"""
Tests de losas en 1 dirección — CIRSOC 201-2005, art. 8.3.3 y 9.5.2.1.

Cubren:
  - h_minimo: condiciones de borde, número de tramos
  - As_temperatura: coeficientes por fy
  - s_max_principal / s_max_temperatura: límites de separación
  - calcular_losa_1dir: momentos por coeficientes, armado, corte, temperatura
  - calcular_losa_simple: tramo único simplemente apoyado
  - Consistencia con flexion.py (φMn ≥ Mu en todas las secciones)
"""
import math
import pytest

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion
from hormigon.corte import Vc_simplificado, PHI_CORTE
from hormigon.losas import (
    h_minimo,
    As_temperatura,
    s_max_principal,
    s_max_temperatura,
    calcular_losa_1dir,
    calcular_losa_simple,
)

H20  = Hormigon(fc=20)
H25  = Hormigon(fc=25)
H30  = Hormigon(fc=30)
ADN420 = Acero(fy=420)
AM500  = Acero(fy=500)


# ---------------------------------------------------------------------------
# h_minimo
# ---------------------------------------------------------------------------

class TestHMinimo:
    def test_libre_2_tramos(self):
        # extremo libre → ln/20
        assert h_minimo(4.0, "libre", 2) == pytest.approx(4.0 / 20, rel=1e-9)

    def test_empotrado_viga(self):
        assert h_minimo(4.0, "viga", 2) == pytest.approx(4.0 / 24, rel=1e-9)

    def test_empotrado_columna(self):
        assert h_minimo(4.0, "columna", 3) == pytest.approx(4.0 / 24, rel=1e-9)

    def test_mas_de_2_tramos_governa_ext(self):
        # Interior: ln/28 = 0.1429; Exterior libre: ln/20 = 0.2 → ext governa
        h = h_minimo(4.0, "libre", 3)
        assert h == pytest.approx(4.0 / 20, rel=1e-9)

    def test_interior_no_governa_libre(self):
        # Con extremo libre: ln/20 > ln/28 siempre
        assert h_minimo(5.0, "libre", 4) == pytest.approx(5.0 / 20, rel=1e-9)

    def test_crece_con_ln(self):
        assert h_minimo(6.0) > h_minimo(4.0)


# ---------------------------------------------------------------------------
# As_temperatura
# ---------------------------------------------------------------------------

class TestAsTemperatura:
    def test_fy_420(self):
        # ρ=0.0018, h=0.12m → 0.0018*0.12*1e4 = 2.16 cm²/m
        assert As_temperatura(0.12, ADN420) == pytest.approx(2.16, rel=1e-9)

    def test_fy_500(self):
        # ρ = max(0.0018*420/500, 0.0014) = max(0.001512, 0.0014) = 0.001512
        rho = max(0.0018 * 420 / 500, 0.0014)
        assert As_temperatura(0.12, AM500) == pytest.approx(rho * 0.12 * 1e4, rel=1e-9)

    def test_fy_500_menor_que_420(self):
        # AM500 debería dar menos acero de temp que ADN420
        assert As_temperatura(0.12, AM500) < As_temperatura(0.12, ADN420)

    def test_proporcional_a_h(self):
        r1 = As_temperatura(0.10, ADN420)
        r2 = As_temperatura(0.20, ADN420)
        assert r2 == pytest.approx(2 * r1, rel=1e-9)


# ---------------------------------------------------------------------------
# s_max
# ---------------------------------------------------------------------------

class TestSMax:
    def test_principal_3h_o_450(self):
        assert s_max_principal(0.10) == pytest.approx(min(0.30, 0.45), rel=1e-9)
        assert s_max_principal(0.20) == pytest.approx(min(0.60, 0.45), rel=1e-9)

    def test_temperatura_5h_o_450(self):
        assert s_max_temperatura(0.08) == pytest.approx(min(0.40, 0.45), rel=1e-9)
        assert s_max_temperatura(0.10) == pytest.approx(min(0.50, 0.45), rel=1e-9)

    def test_principal_tope_045(self):
        assert s_max_principal(0.30) == pytest.approx(0.45, rel=1e-9)

    def test_temperatura_tope_045(self):
        assert s_max_temperatura(0.10) == pytest.approx(0.45, rel=1e-9)


# ---------------------------------------------------------------------------
# calcular_losa_1dir — 2 tramos, extremo libre
# ---------------------------------------------------------------------------

class TestLosa2TramosLibre:
    @pytest.fixture
    def res(self):
        return calcular_losa_1dir(
            h=0.12, recubrimiento=0.020,
            hormigon=H25, acero=ADN420,
            wu=8.0, ln=4.0,
            n_tramos=2, extremo="libre",
        )

    def test_d_correcto(self, res):
        assert res.d == pytest.approx(0.12 - 0.020, abs=1e-9)

    def test_h_min_ln_sobre_20(self, res):
        assert res.h_min == pytest.approx(4.0 / 20, rel=1e-9)

    def test_verifica_h(self, res):
        # h=0.12 ≥ h_min=0.20? No → no verifica (sección subescalada intencional)
        assert res.verifica_h == (0.12 >= 4.0 / 20 - 1e-9)

    def test_hay_secciones(self, res):
        assert len(res.secciones) >= 3

    def test_todas_secciones_verifican(self, res):
        for s in res.secciones:
            if s.Mu > 0:
                assert s.verifica, f"Sección {s.nombre} no verifica"

    def test_phi_Mn_ge_Mu_en_todas(self, res):
        for s in res.secciones:
            if s.Mu > 0:
                assert s.phi_Mn >= s.Mu - 1e-6

    def test_As_positivo_donde_hay_momento(self, res):
        for s in res.secciones:
            if s.Mu > 0:
                assert s.As > 0

    def test_momento_positivo_ext_libre(self, res):
        # Mu = wu·ln²/11 = 8*16/11 = 11.636 kNm/m
        Mu_esp = 8.0 * 4.0 ** 2 / 11.0
        s = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M+" in s.nombre)
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_momento_negativo_1er_apoyo_2tramos(self, res):
        # 2 tramos → Mu = wu·ln²/9 = 8*16/9 = 14.222 kNm/m
        Mu_esp = 8.0 * 4.0 ** 2 / 9.0
        s = next(s for s in res.secciones if "1°" in s.nombre or "1er" in s.nombre.lower() or "apoyo int" in s.nombre.lower())
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_apoyo_ext_libre_Mu_cero(self, res):
        s = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M-" in s.nombre)
        assert s.Mu == pytest.approx(0.0, abs=1e-9)

    def test_As_temp(self, res):
        assert res.As_temp == pytest.approx(0.0018 * 0.12 * 1e4, rel=1e-9)

    def test_s_temp_max(self, res):
        assert res.s_temp_max == pytest.approx(min(5 * 0.12, 0.45), rel=1e-9)

    def test_phi_Vc_formula(self, res):
        Vc_esp = Vc_simplificado(H25, bw=1.0, d=res.d)
        assert res.phi_Vc == pytest.approx(PHI_CORTE * Vc_esp, rel=1e-9)

    def test_Vu_max_formula(self, res):
        assert res.Vu_max == pytest.approx(1.15 * 8.0 * 4.0 / 2.0, rel=1e-9)


# ---------------------------------------------------------------------------
# calcular_losa_1dir — 3 tramos, extremo empotrado a viga
# ---------------------------------------------------------------------------

class TestLosa3TramosViga:
    @pytest.fixture
    def res(self):
        return calcular_losa_1dir(
            h=0.15, recubrimiento=0.025,
            hormigon=H25, acero=ADN420,
            wu=10.0, ln=5.0,
            n_tramos=3, extremo="viga",
        )

    def test_h_min_ln_sobre_24(self, res):
        assert res.h_min == pytest.approx(5.0 / 24, rel=1e-9)

    def test_momento_positivo_ext_empotrado(self, res):
        Mu_esp = 10.0 * 5.0 ** 2 / 14.0
        s = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M+" in s.nombre)
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_momento_positivo_interior(self, res):
        Mu_esp = 10.0 * 5.0 ** 2 / 16.0
        s = next(s for s in res.secciones if "int" in s.nombre.lower() and "M+" in s.nombre)
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_momento_negativo_1er_apoyo_3tramos(self, res):
        # > 2 tramos → /10
        Mu_esp = 10.0 * 5.0 ** 2 / 10.0
        s = next(s for s in res.secciones if "1°" in s.nombre or "apoyo int" in s.nombre.lower())
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_momento_apoyo_ext_viga(self, res):
        Mu_esp = 10.0 * 5.0 ** 2 / 24.0
        s = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M-" in s.nombre)
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_todas_secciones_verifican(self, res):
        for s in res.secciones:
            if s.Mu > 0:
                assert s.verifica


# ---------------------------------------------------------------------------
# calcular_losa_1dir — 4 tramos, extremo columna
# ---------------------------------------------------------------------------

class TestLosa4TramosColumna:
    @pytest.fixture
    def res(self):
        return calcular_losa_1dir(
            h=0.18, recubrimiento=0.030,
            hormigon=H30, acero=ADN420,
            wu=12.0, ln=6.0,
            n_tramos=4, extremo="columna",
        )

    def test_momento_apoyo_ext_columna(self, res):
        Mu_esp = 12.0 * 6.0 ** 2 / 16.0
        s = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M-" in s.nombre)
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_hay_apoyos_int_intermedios(self, res):
        # n_tramos > 3 → debe haber sección de apoyos interiores intermedios
        nombres = [s.nombre for s in res.secciones]
        assert any("poyos int" in n for n in nombres)

    def test_momento_apoyo_int_intermedio(self, res):
        Mu_esp = 12.0 * 6.0 ** 2 / 11.0
        s = next(s for s in res.secciones if "poyos int" in s.nombre and "°" not in s.nombre)
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_todas_secciones_verifican(self, res):
        for s in res.secciones:
            if s.Mu > 0:
                assert s.verifica

    def test_s_max_principal_correcto(self, res):
        for s in res.secciones:
            if s.Mu > 0:
                assert s.s_max == pytest.approx(min(3 * 0.18, 0.45), rel=1e-9)


# ---------------------------------------------------------------------------
# Validar error para tramo único
# ---------------------------------------------------------------------------

class TestNTramosMinimo:
    def test_n_tramos_1_lanza(self):
        with pytest.raises(ValueError, match="n_tramos"):
            calcular_losa_1dir(
                h=0.12, recubrimiento=0.020,
                hormigon=H25, acero=ADN420,
                wu=8.0, ln=4.0,
                n_tramos=1,
            )


# ---------------------------------------------------------------------------
# calcular_losa_simple
# ---------------------------------------------------------------------------

class TestLosaSimple:
    @pytest.fixture
    def res(self):
        return calcular_losa_simple(
            h=0.12, recubrimiento=0.020,
            hormigon=H25, acero=ADN420,
            wu=6.0, ln=3.0,
        )

    def test_Mu_formula(self, res):
        Mu_esp = 6.0 * 3.0 ** 2 / 8.0
        s = res.secciones[0]
        assert s.Mu == pytest.approx(Mu_esp, rel=1e-9)

    def test_h_min_ln_sobre_20(self, res):
        assert res.h_min == pytest.approx(3.0 / 20, rel=1e-9)

    def test_Vu_formula(self, res):
        assert res.Vu_max == pytest.approx(6.0 * 3.0 / 2.0, rel=1e-9)

    def test_phi_Mn_ge_Mu(self, res):
        assert res.secciones[0].phi_Mn >= res.secciones[0].Mu - 1e-6

    def test_verifica_corte_o_no(self, res):
        # Solo verificamos que el campo es booleano consistente
        assert res.verifica_corte == (res.phi_Vc >= res.Vu_max)

    def test_n_tramos_es_1(self, res):
        assert res.n_tramos == 1


# ---------------------------------------------------------------------------
# Consistencia con flexion.py
# ---------------------------------------------------------------------------

class TestConsistenciaConFlexion:
    def test_As_igual_a_dimensionar_flexion(self):
        h = 0.14
        rec = 0.022
        wu = 9.0
        ln = 4.5
        Mu = wu * ln ** 2 / 11.0

        sec  = SeccionRectangular(b=1.0, h=h, recubrimiento=rec, hormigon=H25, acero=ADN420)
        r_fl = dimensionar_flexion(sec, Mu=Mu)

        res  = calcular_losa_1dir(h=h, recubrimiento=rec, hormigon=H25, acero=ADN420,
                                   wu=wu, ln=ln, n_tramos=2, extremo="libre")
        s_ext = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M+" in s.nombre)

        assert s_ext.As == pytest.approx(r_fl.As, rel=1e-9)

    def test_phi_Mn_consistente(self):
        h = 0.14
        rec = 0.022
        wu = 9.0
        ln = 4.5
        Mu = wu * ln ** 2 / 11.0

        sec  = SeccionRectangular(b=1.0, h=h, recubrimiento=rec, hormigon=H25, acero=ADN420)
        r_fl = dimensionar_flexion(sec, Mu=Mu)

        res  = calcular_losa_1dir(h=h, recubrimiento=rec, hormigon=H25, acero=ADN420,
                                   wu=wu, ln=ln, n_tramos=2, extremo="libre")
        s_ext = next(s for s in res.secciones if "ext" in s.nombre.lower() and "M+" in s.nombre)

        assert s_ext.phi_Mn == pytest.approx(r_fl.phi_Mn, rel=1e-9)

    def test_mostrar_no_falla(self, capsys):
        res = calcular_losa_1dir(
            h=0.15, recubrimiento=0.025,
            hormigon=H25, acero=ADN420,
            wu=10.0, ln=5.0,
            n_tramos=3, extremo="viga",
        )
        res.mostrar()
        captured = capsys.readouterr()
        assert "wu" in captured.out.lower() or "Wu" in captured.out
