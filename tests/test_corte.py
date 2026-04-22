"""
Tests de corte validados contra el Ejemplo 3.I del CIRSOC 201-2005.
Tolerancia: 2% en resultados numéricos principales.

Datos Ej 3.I: H-20, bw=0.20m, h=0.60m, d≈0.575m, ADN420, Vu=174.6 kN
Resultados esperados: Vc≈85.8kN, Vs_req≈147kN, Av/s≈609mm²/m, s_max≈0.29m
"""
import math
import pytest

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular, SeccionT
from hormigon.corte import (
    Vc_simplificado,
    Vc_afinado,
    Vs_estribos,
    Vs_barras_dobladas,
    Avs_minimo,
    s_maximo,
    Vn_maximo,
    calcular_corte,
    calcular_corte_variantes,
    PHI_CORTE,
)

H20 = Hormigon(fc=20)
H25 = Hormigon(fc=25)
H30 = Hormigon(fc=30)
ADN420 = Acero(fy=420)


# ---------------------------------------------------------------------------
# Funciones elementales
# ---------------------------------------------------------------------------

class TestVcSimplificado:
    def test_sin_axial(self):
        # √20/6 * 0.20 * 0.575 * 1000 = 85.72 kN
        Vc = Vc_simplificado(H20, bw=0.20, d=0.575)
        assert Vc == pytest.approx(math.sqrt(20) / 6 * 0.20 * 0.575 * 1000, rel=1e-9)

    def test_valor_numerico(self):
        Vc = Vc_simplificado(H20, bw=0.20, d=0.575)
        assert Vc == pytest.approx(85.7, rel=0.01)

    def test_con_compresion(self):
        # Nu=120 kN, Ag=0.20*0.60=0.12 m² → sigma=1 MPa → factor=1+1/14=1.0714
        Ag = 0.20 * 0.60
        Vc_base = math.sqrt(20) / 6 * 0.20 * 0.575 * 1000
        sigma = 120.0 / (Ag * 1000.0)     # MPa
        esperado = Vc_base * (1.0 + sigma / 14.0)
        assert Vc_simplificado(H20, bw=0.20, d=0.575, Nu=120.0, Ag=Ag) == pytest.approx(esperado, rel=1e-9)

    def test_con_traccion_reduce_Vc(self):
        Vc_puro = Vc_simplificado(H20, bw=0.20, d=0.575)
        Ag = 0.20 * 0.60
        Vc_trac = Vc_simplificado(H20, bw=0.20, d=0.575, Nu=-80.0, Ag=Ag)
        assert Vc_trac < Vc_puro

    def test_traccion_grande_vc_nulo(self):
        # Nu muy negativo → factor → 0 → Vc ≥ 0
        Ag = 0.20 * 0.60
        Vc = Vc_simplificado(H20, bw=0.20, d=0.575, Nu=-100_000.0, Ag=Ag)
        assert Vc == pytest.approx(0.0, abs=1e-6)

    def test_proporcional_bwd(self):
        Vc1 = Vc_simplificado(H25, bw=0.30, d=0.50)
        Vc2 = Vc_simplificado(H25, bw=0.60, d=0.50)
        assert Vc2 == pytest.approx(2 * Vc1, rel=1e-9)


class TestVsEstribos:
    def test_valor_numerico(self):
        # Avs=609 mm²/m, fyt=420, d=0.575
        Vs = Vs_estribos(609.0, fyt=420.0, d=0.575)
        assert Vs == pytest.approx(147.0, rel=0.01)

    def test_unidades(self):
        # Con Avs/s=1000 mm²/m, fyt=200 MPa, d=1.0 m → Vs=200 kN
        assert Vs_estribos(1000.0, fyt=200.0, d=1.0) == pytest.approx(200.0, rel=1e-9)


class TestVsBarrasDobladas:
    def test_45_grados(self):
        # Av=2cm², fy=420, α=45° → 2/1e4*420e3*sin(45°)
        esperado = 2.0 / 1e4 * 420.0 * 1000.0 * math.sin(math.radians(45))
        assert Vs_barras_dobladas(2.0, fy=420.0, alpha_deg=45.0) == pytest.approx(esperado, rel=1e-9)

    def test_90_grados(self):
        esperado = 2.0 / 1e4 * 420.0 * 1000.0
        assert Vs_barras_dobladas(2.0, fy=420.0, alpha_deg=90.0) == pytest.approx(esperado, rel=1e-9)

    def test_angulo_invalido_menos_de_30(self):
        assert Vs_barras_dobladas(2.0, fy=420.0, alpha_deg=20.0) == pytest.approx(0.0)


class TestAvsMinimo:
    def test_H20_ADN420(self):
        # op1=0.33*200/420*1000=157.1; op2=√20/16*200/420*1000=133.1 → max=157.1
        Avs = Avs_minimo(H20, ADN420, bw=0.20)
        assert Avs == pytest.approx(157.1, rel=0.01)

    def test_siempre_positivo(self):
        for fc in [20, 25, 30, 35]:
            Avs = Avs_minimo(Hormigon(fc=fc), ADN420, bw=0.25)
            assert Avs > 0

    def test_aumenta_con_bw(self):
        Avs1 = Avs_minimo(H25, ADN420, bw=0.20)
        Avs2 = Avs_minimo(H25, ADN420, bw=0.30)
        assert Avs2 > Avs1


class TestSMaximo:
    def test_Vs_bajo_da_d_sobre_2(self):
        # Vs pequeño → Vs ≤ √fc/3*bw*d*1000 → s_max = min(d/2, 0.40)
        d = 0.575
        bw = 0.20
        Vs_bajo = 50.0   # kN (muy por debajo del límite)
        s = s_maximo(H20, bw=bw, d=d, Vs=Vs_bajo)
        assert s == pytest.approx(min(d / 2, 0.40), rel=1e-9)

    def test_Vs_alto_da_d_sobre_4(self):
        # Vs muy alto → s_max = min(d/4, 0.20)
        d = 0.575
        bw = 0.20
        Vs_alto = 500.0   # kN (muy por encima del límite)
        s = s_maximo(H20, bw=bw, d=d, Vs=Vs_alto)
        assert s == pytest.approx(min(d / 4, 0.20), rel=1e-9)

    def test_tope_absoluto_040(self):
        # d muy grande → s_max acotado en 0.40m
        d = 1.50
        s = s_maximo(H25, bw=0.30, d=d, Vs=10.0)
        assert s <= 0.401

    def test_tope_absoluto_020(self):
        d = 1.50
        s = s_maximo(H25, bw=0.30, d=d, Vs=1000.0)
        assert s <= 0.201


class TestVnMaximo:
    def test_sin_axial(self):
        # 5 * √20/6 * 0.20 * 0.575 * 1000 = 5 * 85.72 = 428.6 kN
        Vn_max = Vn_maximo(H20, bw=0.20, d=0.575)
        assert Vn_max == pytest.approx(5 * math.sqrt(20) / 6 * 0.20 * 0.575 * 1000, rel=1e-9)

    def test_valor_numerico(self):
        assert Vn_maximo(H20, bw=0.20, d=0.575) == pytest.approx(428.6, rel=0.01)


# ---------------------------------------------------------------------------
# Ejemplo 3.I — viga rectangular H-20, bw=0.20m, h=0.60m, ADN420
# Vu = 174.6 kN
# ---------------------------------------------------------------------------

class TestEjemplo3I:
    """CIRSOC Ejemplo 3.I: sección rectangular, Vu=174.6 kN."""

    @pytest.fixture
    def sec(self):
        # d = 0.60 - 0.025 = 0.575 m
        return SeccionRectangular(
            b=0.20, h=0.60, recubrimiento=0.025,
            hormigon=H20, acero=ADN420,
        )

    @pytest.fixture
    def res(self, sec):
        return calcular_corte(sec, Vu=174.6)

    def test_d(self, sec):
        assert sec.d == pytest.approx(0.575, abs=1e-9)

    def test_Vc(self, res):
        assert res.Vc == pytest.approx(85.7, rel=0.01)

    def test_Vs_requerido(self, res):
        assert res.Vs_requerido == pytest.approx(147.0, rel=0.02)

    def test_Avs_calculado(self, res):
        assert res.Avs_calculado == pytest.approx(609.0, rel=0.02)

    def test_Avs_minimo(self, res):
        assert res.Avs_minimo == pytest.approx(157.1, rel=0.02)

    def test_Avs_adoptado_es_calculado(self, res):
        # Calculado > mínimo → adoptado = calculado
        assert res.Avs_adoptado == pytest.approx(res.Avs_calculado, rel=1e-9)

    def test_s_maximo(self, res):
        # Vs ≤ √fc/3·bw·d·1000 → s = min(d/2, 0.40) = 0.2875 m
        assert res.s_maximo == pytest.approx(0.2875, rel=0.01)

    def test_phi_Vn_verifica(self, res):
        assert res.phi_Vn >= 174.6
        assert res.verifica_resistencia

    def test_Vn_max_ok(self, res):
        assert res.verifica_Vn_max

    def test_phi_corte(self):
        assert PHI_CORTE == pytest.approx(0.75)

    def test_phi_Vn_consiste_con_Vn(self, res):
        assert res.phi_Vn == pytest.approx(PHI_CORTE * res.Vn, rel=1e-9)

    def test_Vn_es_Vc_mas_Vs_eff(self, res):
        Vs_eff = res.Avs_adoptado / 1e6 * ADN420.fy * 1000.0 * 0.575
        assert res.Vn == pytest.approx(res.Vc + Vs_eff, rel=1e-9)


# ---------------------------------------------------------------------------
# Adoptar
# ---------------------------------------------------------------------------

class TestAdoptar:
    def test_adoptar_registra_valores(self):
        sec = SeccionRectangular(
            b=0.20, h=0.60, recubrimiento=0.025,
            hormigon=H20, acero=ADN420,
        )
        res = calcular_corte(sec, Vu=174.6)
        res.adoptar(phi=8, n_ramas=2, s=0.17)
        assert res.phi_estribo == 8
        assert res.n_ramas == 2
        assert res.s_adoptado == pytest.approx(0.17)
        assert res.Avs_real == pytest.approx(2 * 0.503 * 100 / 0.17, rel=0.01)

    def test_mostrar_no_falla(self):
        sec = SeccionRectangular(
            b=0.25, h=0.55, recubrimiento=0.03,
            hormigon=H25, acero=ADN420,
        )
        res = calcular_corte(sec, Vu=120.0)
        res.adoptar(phi=8, n_ramas=2, s=0.20)
        res.mostrar()   # no debe lanzar excepción


# ---------------------------------------------------------------------------
# Variantes
# ---------------------------------------------------------------------------

class TestVariantes:
    @pytest.fixture
    def rset(self):
        sec = SeccionRectangular(
            b=0.20, h=0.60, recubrimiento=0.025,
            hormigon=H20, acero=ADN420,
        )
        return calcular_corte_variantes(sec, Vu=174.6, n_ramas=2)

    def test_hay_variantes(self, rset):
        assert len(rset.variantes) > 0

    def test_todas_verifican(self, rset):
        for v in rset.variantes:
            assert v.verifica, f"Variante {v} no verifica"

    def test_s_no_excede_s_max(self, rset):
        for v in rset.variantes:
            assert v.s <= rset.s_maximo + 1e-9, f"s={v.s:.3f} > s_max={rset.s_maximo:.3f}"

    def test_rankeadas_por_separacion_descendente(self, rset):
        separaciones = [v.s for v in rset.variantes]
        assert separaciones == sorted(separaciones, reverse=True)

    def test_adoptar_rank_1_existe(self, rset):
        v1 = rset.adoptar(1)
        assert v1.rank == 1

    def test_adoptar_rank_invalido_lanza(self, rset):
        with pytest.raises(ValueError):
            rset.adoptar(9999)

    def test_rank_1_es_mayor_separacion(self, rset):
        v1 = rset.adoptar(1)
        assert v1.s == max(v.s for v in rset.variantes)

    def test_Avs_supera_requerido(self, rset):
        for v in rset.variantes:
            assert v.Avs >= rset.Avs_requerido - 1e-6


# ---------------------------------------------------------------------------
# Sección T — cortante solo toma el alma
# ---------------------------------------------------------------------------

class TestSeccionTCorte:
    def test_Vc_usa_bw(self):
        from hormigon.secciones import SeccionT
        sec_T = SeccionT(
            bw=0.20, h=0.60, b_ala=1.00, h_ala=0.12,
            recubrimiento=0.025, hormigon=H25, acero=ADN420,
        )
        sec_rect = SeccionRectangular(
            b=0.20, h=0.60, recubrimiento=0.025,
            hormigon=H25, acero=ADN420,
        )
        res_T = calcular_corte(sec_T, Vu=120.0)
        res_rect = calcular_corte(sec_rect, Vu=120.0)
        # Vc debe coincidir ya que bw y d son iguales
        assert res_T.Vc == pytest.approx(res_rect.Vc, rel=1e-6)

    def test_variantes_seccion_T(self):
        from hormigon.secciones import SeccionT
        sec_T = SeccionT(
            bw=0.25, h=0.65, b_ala=1.20, h_ala=0.12,
            recubrimiento=0.03, hormigon=H30, acero=ADN420,
        )
        rset = calcular_corte_variantes(sec_T, Vu=200.0, n_ramas=2)
        assert len(rset.variantes) > 0
        for v in rset.variantes:
            assert v.verifica


# ---------------------------------------------------------------------------
# Corte con barras dobladas
# ---------------------------------------------------------------------------

class TestConBarrasDobladas:
    def test_Vs_barras_reduce_Vs_estribo(self):
        sec = SeccionRectangular(
            b=0.25, h=0.60, recubrimiento=0.03,
            hormigon=H25, acero=ADN420,
        )
        res_sin = calcular_corte(sec, Vu=150.0, Vs_barras=0.0)
        Vs_bd = Vs_barras_dobladas(Av_cm2=3.0, fy=420.0, alpha_deg=45.0)
        res_con = calcular_corte(sec, Vu=150.0, Vs_barras=Vs_bd)
        assert res_con.Vs_requerido < res_sin.Vs_requerido

    def test_Vs_barras_mayor_que_Vs_req_da_cero_estribos_calculados(self):
        sec = SeccionRectangular(
            b=0.25, h=0.60, recubrimiento=0.03,
            hormigon=H25, acero=ADN420,
        )
        res = calcular_corte(sec, Vu=40.0, Vs_barras=200.0)
        assert res.Vs_requerido == pytest.approx(0.0, abs=1e-6)
