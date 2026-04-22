"""
Tests de flexión simple validados contra los Ejemplos del CIRSOC 201-2005, Parte 1.
Tolerancia: 1% en resultados numéricos principales.
"""
import pytest
from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular, SeccionT, ancho_eficaz_T
from hormigon.flexion import (
    dimensionar_flexion,
    verificar_flexion,
    dimensionar_flexion_variantes,
    ka_min,
    ka_max,
    phi_flexion,
)

# ---------------------------------------------------------------------------
# Materiales usados en los ejemplos
# ---------------------------------------------------------------------------
H25 = Hormigon(fc=25)
H30 = Hormigon(fc=30)
H20 = Hormigon(fc=20)
ADN420 = Acero(fy=420)
AM500 = Acero(fy=500)

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

class TestUtilidades:
    def test_ka_min_fc25(self):
        # 1.4 / (0.85*25) = 0.06588 ; 1/(3.4*sqrt(25)) = 0.05882 → max = 0.06588
        assert ka_min(H25) == pytest.approx(0.06588, abs=0.0001)

    def test_ka_min_fc35(self):
        # 1.4/(0.85*35)=0.04706 ; 1/(3.4*sqrt(35))=0.04969 → max = 0.04969
        assert ka_min(H35 := Hormigon(fc=35)) == pytest.approx(0.04969, abs=0.0001)

    def test_ka_max_fc25(self):
        # 0.375 * 0.85 = 0.31875
        assert ka_max(H25) == pytest.approx(0.31875, abs=1e-6)

    def test_ka_max_fc30(self):
        # 0.375 * beta1(30) = 0.375 * 0.8357 = 0.31339
        assert ka_max(H30) == pytest.approx(0.375 * H30.beta1, rel=1e-6)

    def test_phi_traccion(self):
        assert phi_flexion(0.005, 420/200000) == pytest.approx(0.90)
        assert phi_flexion(0.010, 420/200000) == pytest.approx(0.90)

    def test_phi_compresion_estribos(self):
        assert phi_flexion(0.001, 420/200000) == pytest.approx(0.65)

    def test_phi_transicion(self):
        eps_y = 420 / 200_000
        eps_s = (0.005 + eps_y) / 2  # punto medio
        phi_esperado = 0.65 + 0.25 * (eps_s - eps_y) / (0.005 - eps_y)
        assert phi_flexion(eps_s, eps_y) == pytest.approx(phi_esperado, rel=1e-6)


# ---------------------------------------------------------------------------
# Ejemplo 2.I.1 — sección rectangular, armadura simple (CIRSOC Parte 1 p.17)
# f'c=25, fy=420, b=0.12, h=0.40, recub_mec=0.034 m, Mu=52 kNm
# Resultado esperado: As ≈ 4.15 cm²
# ---------------------------------------------------------------------------

class TestEjemplo2I1:
    """Sección rectangular, Mu=52 kNm — armadura simple."""

    @pytest.fixture
    def sec(self):
        # d = 0.40 - 0.02 - 0.006 - 0.008 = 0.366 m
        return SeccionRectangular(
            b=0.12, h=0.40, recubrimiento=0.034,
            hormigon=H25, acero=ADN420,
        )

    def test_d(self, sec):
        assert sec.d == pytest.approx(0.366, abs=1e-9)

    def test_As_calculada(self, sec):
        r = dimensionar_flexion(sec, Mu=52)
        assert r.As == pytest.approx(4.15, rel=0.01)

    def test_phi_es_090(self, sec):
        r = dimensionar_flexion(sec, Mu=52)
        assert r.phi == pytest.approx(0.90, abs=1e-6)

    def test_ka(self, sec):
        r = dimensionar_flexion(sec, Mu=52)
        assert r.ka == pytest.approx(0.18655, abs=0.001)

    def test_phi_Mn_ge_Mu(self, sec):
        r = dimensionar_flexion(sec, Mu=52)
        assert r.phi_Mn >= 52.0
        assert r.verifica

    def test_tipo_traccion(self, sec):
        r = dimensionar_flexion(sec, Mu=52)
        assert r.tipo == "tracción"


# ---------------------------------------------------------------------------
# Ejemplo 2.I.2 — cuantía mínima gobierna (Mu=16 kNm)
# Resultado esperado: As ≈ 1.46 cm² (mínimo)
# ---------------------------------------------------------------------------

class TestEjemplo2I2:
    @pytest.fixture
    def sec(self):
        return SeccionRectangular(
            b=0.12, h=0.40, recubrimiento=0.034,
            hormigon=H25, acero=ADN420,
        )

    def test_ka_es_ka_min(self, sec):
        r = dimensionar_flexion(sec, Mu=16)
        assert r.ka == pytest.approx(ka_min(H25), rel=0.01)

    def test_As_minima(self, sec):
        r = dimensionar_flexion(sec, Mu=16)
        # As_min = ka_min * fsc * b * d / fy → aprox 1.46 cm²
        assert r.As == pytest.approx(1.46, rel=0.02)


# ---------------------------------------------------------------------------
# Ejemplo 2.I.3 — doble armadura (Mu=100 kNm, d'=0.03 m)
# Resultados esperados: As ≈ 8.47 cm², As' ≈ 1.39 cm²
# ---------------------------------------------------------------------------

class TestEjemplo2I3:
    @pytest.fixture
    def sec(self):
        return SeccionRectangular(
            b=0.12, h=0.40, recubrimiento=0.034,
            hormigon=H25, acero=ADN420,
            recubrimiento_prima=0.03,
        )

    def test_As_doble(self, sec):
        r = dimensionar_flexion(sec, Mu=100)
        assert r.As == pytest.approx(8.47, rel=0.02)

    def test_As_prima(self, sec):
        r = dimensionar_flexion(sec, Mu=100)
        assert r.As_prima == pytest.approx(1.39, rel=0.02)

    def test_fs_prima_igual_fy(self, sec):
        # ε's = 0.0023 > εy = 0.0021 → f's = fy = 420 MPa
        r = dimensionar_flexion(sec, Mu=100)
        assert r.fs_prima == pytest.approx(420.0, rel=0.01)

    def test_phi_Mn_ge_Mu(self, sec):
        r = dimensionar_flexion(sec, Mu=100)
        assert r.phi_Mn >= 100.0


# ---------------------------------------------------------------------------
# Ejemplo 2.I.5 — losa 1 dir., malla AM 500 N, doble armadura
# f'c=20, fy=500, b=1.00, h=0.09, recub=0.026 m (cc=0.02, d_b/2=0.006)
# Mu=17.1 kNm → As' > 0
# ---------------------------------------------------------------------------

class TestEjemplo2I5:
    @pytest.fixture
    def sec(self):
        # d = 0.09 - 0.02 - 0.006 = 0.064 m
        return SeccionRectangular(
            b=1.00, h=0.09, recubrimiento=0.026,
            hormigon=H20, acero=AM500,
            recubrimiento_prima=0.023,
        )

    def test_d(self, sec):
        assert sec.d == pytest.approx(0.064, abs=1e-9)

    def test_doble_armadura(self, sec):
        r = dimensionar_flexion(sec, Mu=17.1)
        assert r.As_prima > 0


# ---------------------------------------------------------------------------
# Verificación — dado As, calcular φMn
# ---------------------------------------------------------------------------

class TestVerificacion:
    def test_phi_Mn_ejemplo2I1(self):
        sec = SeccionRectangular(
            b=0.12, h=0.40, recubrimiento=0.034,
            hormigon=H25, acero=ADN420,
        )
        # 3φ12 = 3*1.131 = 3.393 cm² < As_calc=4.15 → φMn < Mu=52
        r = verificar_flexion(sec, As=4.15)
        # φMn debe ser ≥ 52 kNm
        assert r.phi_Mn >= 51.5   # tolerancia 1%

    def test_verificacion_simple_rect(self):
        sec = SeccionRectangular(
            b=0.30, h=0.60, recubrimiento=0.03,
            hormigon=H30, acero=ADN420,
        )
        # As = 10 cm² — verificar que devuelve φMn coherente
        r = verificar_flexion(sec, As=10.0)
        assert r.phi_Mn > 0
        assert r.epsilon_s > 0

    def test_consistencia_dimensionar_verificar(self):
        sec = SeccionRectangular(
            b=0.25, h=0.55, recubrimiento=0.035,
            hormigon=H30, acero=ADN420,
        )
        Mu = 150.0
        r_dim = dimensionar_flexion(sec, Mu=Mu)
        r_ver = verificar_flexion(sec, As=r_dim.As)
        # φMn(verificado) ≈ φMn(dimensionado)
        assert r_ver.phi_Mn == pytest.approx(r_dim.phi_Mn, rel=0.01)


# ---------------------------------------------------------------------------
# Sección T — eje neutro en ala (comportamiento rectangular)
# ---------------------------------------------------------------------------

class TestSeccionT:
    @pytest.fixture
    def sec_T_ala(self):
        # T con ala grande → NA en ala para momentos moderados
        bef = ancho_eficaz_T(bw=0.25, h_ala=0.12, ln=6.0, dist_entre_vigas=2.5)
        return SeccionT(
            bw=0.25, h=0.60, b_ala=bef, h_ala=0.12,
            recubrimiento=0.035, hormigon=H30, acero=ADN420,
        )

    def test_NA_en_ala_As_positivo(self, sec_T_ala):
        r = dimensionar_flexion(sec_T_ala, Mu=100)
        assert r.As > 0
        assert r.phi_Mn >= 100

    def test_seccion_T_alma(self):
        # T con Mu grande → NA pasa al alma
        sec = SeccionT(
            bw=0.25, h=0.65, b_ala=1.20, h_ala=0.12,
            recubrimiento=0.035, hormigon=H30, acero=ADN420,
        )
        r = dimensionar_flexion(sec, Mu=400)
        assert r.As > 0
        assert r.phi_Mn >= 400

    def test_consistencia_T_dimensionar_verificar(self):
        bef = ancho_eficaz_T(bw=0.25, h_ala=0.12, ln=6.0, dist_entre_vigas=2.5)
        sec = SeccionT(
            bw=0.25, h=0.60, b_ala=bef, h_ala=0.12,
            recubrimiento=0.035, hormigon=H30, acero=ADN420,
        )
        Mu = 200.0
        r_dim = dimensionar_flexion(sec, Mu=Mu)
        r_ver = verificar_flexion(sec, As=r_dim.As)
        assert r_ver.phi_Mn == pytest.approx(r_dim.phi_Mn, rel=0.02)


# ---------------------------------------------------------------------------
# Sistema de variantes
# ---------------------------------------------------------------------------

class TestVariantes:
    def test_variantes_devuelve_soluciones_validas(self):
        sec = SeccionRectangular(
            b=0.30, h=0.60, recubrimiento=0.035,
            hormigon=H30, acero=ADN420,
        )
        rset = dimensionar_flexion_variantes(sec, Mu=150)
        assert len(rset.variantes) > 0
        for v in rset.variantes:
            assert v.verifica
            assert v.As >= rset.As_requerida

    def test_variantes_rankeadas_por_As(self):
        sec = SeccionRectangular(
            b=0.30, h=0.60, recubrimiento=0.035,
            hormigon=H30, acero=ADN420,
        )
        rset = dimensionar_flexion_variantes(sec, Mu=150)
        areas = [v.As for v in rset.variantes]
        assert areas == sorted(areas)

    def test_variantes_rank_1_es_minima(self):
        sec = SeccionRectangular(
            b=0.30, h=0.60, recubrimiento=0.035,
            hormigon=H30, acero=ADN420,
        )
        rset = dimensionar_flexion_variantes(sec, Mu=150)
        v1 = rset.adoptar(1)
        assert v1.As == min(v.As for v in rset.variantes)
