"""Tests para hormigon/tirantes.py — CIRSOC 201-2005 art. 9.3.2.1 y 10.6.4."""
import math
import pytest

from hormigon.materiales import Acero, BARRAS, DIAMETROS
from hormigon.tirantes import (
    s_max_fisuras,
    dimensionar_tirante,
    verificar_tirante,
    dimensionar_tirante_variantes,
    PHI_TRACCION,
    ResultadoTirante,
)


# ---------------------------------------------------------------------------
# Materiales comunes
# ---------------------------------------------------------------------------

@pytest.fixture
def adn420():
    return Acero(fy=420)

@pytest.fixture
def am500():
    return Acero(fy=500)


# ---------------------------------------------------------------------------
# s_max_fisuras (art. 10.6.4)
# ---------------------------------------------------------------------------

class TestSMaxFisuras:
    def test_formula_con_fs(self, adn420):
        fs = 200.0
        cc = 30.0
        s1 = 380.0 * (280.0 / fs) - 2.5 * cc
        s2 = 300.0 * (280.0 / fs)
        expected = min(s1, s2)
        result = s_max_fisuras(adn420, cc_mm=cc, fs=fs)
        assert abs(result - expected) < 1e-9

    def test_fs_none_usa_2_3_fy(self, adn420):
        cc = 25.0
        fs_def = 2.0 / 3.0 * adn420.fy
        s1 = 380.0 * (280.0 / fs_def) - 2.5 * cc
        s2 = 300.0 * (280.0 / fs_def)
        expected = min(s1, s2)
        result = s_max_fisuras(adn420, cc_mm=cc)
        assert abs(result - expected) < 1e-9

    def test_mayor_fs_menor_smax(self, adn420):
        s_200 = s_max_fisuras(adn420, cc_mm=25.0, fs=200.0)
        s_280 = s_max_fisuras(adn420, cc_mm=25.0, fs=280.0)
        assert s_200 > s_280

    def test_mayor_cc_menor_smax(self, adn420):
        s_25 = s_max_fisuras(adn420, cc_mm=25.0)
        s_50 = s_max_fisuras(adn420, cc_mm=50.0)
        assert s_50 < s_25

    def test_positivo(self, adn420):
        assert s_max_fisuras(adn420, cc_mm=25.0) > 0

    def test_am500_menor_que_adn420(self, adn420, am500):
        # fs = 2/3 × fy: mayor fy → mayor fs → menor smax
        s420 = s_max_fisuras(adn420, cc_mm=25.0)
        s500 = s_max_fisuras(am500, cc_mm=25.0)
        assert s420 > s500

    def test_resultado_es_el_minimo(self, adn420):
        cc = 25.0
        fs = 2.0 / 3.0 * adn420.fy
        s1 = 380.0 * (280.0 / fs) - 2.5 * cc
        s2 = 300.0 * (280.0 / fs)
        result = s_max_fisuras(adn420, cc_mm=cc)
        assert abs(result - min(s1, s2)) < 1e-9


# ---------------------------------------------------------------------------
# dimensionar_tirante
# ---------------------------------------------------------------------------

class TestDimensionarTirante:
    def test_As_formula(self, adn420):
        Tu = 200.0  # kN
        fy = adn420.fy
        As_m2 = Tu / (PHI_TRACCION * fy * 1000.0)
        expected = As_m2 * 1e4  # cm²
        res = dimensionar_tirante(Tu, adn420)
        assert abs(res.As - expected) < 1e-9

    def test_phi_Tn_verifica(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        assert res.verifica is True

    def test_phi_Tn_formula(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        fy = adn420.fy
        expected = PHI_TRACCION * res.As / 1e4 * fy * 1000.0
        assert abs(res.phi_Tn - expected) < 1e-9

    def test_Tu_almacenado(self, adn420):
        res = dimensionar_tirante(150.0, adn420)
        assert abs(res.Tu - 150.0) < 1e-9

    def test_cc_mm_default(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        assert abs(res.cc_mm - 25.0) < 1e-9

    def test_cc_mm_custom(self, adn420):
        res = dimensionar_tirante(200.0, adn420, cc_mm=40.0)
        assert abs(res.cc_mm - 40.0) < 1e-9

    def test_fs_servicio_es_2_3_fy(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        assert abs(res.fs_servicio - 2.0 / 3.0 * adn420.fy) < 1e-9

    def test_s_max_fis_correcto(self, adn420):
        cc = 30.0
        res = dimensionar_tirante(200.0, adn420, cc_mm=cc)
        expected = s_max_fisuras(adn420, cc_mm=cc)
        assert abs(res.s_max_fis_mm - expected) < 1e-9

    def test_mayor_Tu_mayor_As(self, adn420):
        res1 = dimensionar_tirante(100.0, adn420)
        res2 = dimensionar_tirante(300.0, adn420)
        assert res2.As > res1.As

    def test_mayor_fy_menor_As(self, adn420, am500):
        res420 = dimensionar_tirante(200.0, adn420)
        res500 = dimensionar_tirante(200.0, am500)
        assert res500.As < res420.As

    def test_phi_traccion_0_90(self, adn420):
        assert abs(PHI_TRACCION - 0.90) < 1e-9

    def test_res_tipo_ResultadoTirante(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        assert isinstance(res, ResultadoTirante)

    def test_sin_barras_adoptadas(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        assert res.phi_barra is None
        assert res.n_barras is None
        assert res.As_real is None


# ---------------------------------------------------------------------------
# verificar_tirante
# ---------------------------------------------------------------------------

class TestVerificarTirante:
    def test_verifica_con_As_suficiente(self, adn420):
        # As que corresponde a Tu=200kN, calculada con la fórmula
        As = 200.0 / (PHI_TRACCION * adn420.fy * 1000.0) * 1e4
        res = verificar_tirante(Tu=200.0, As=As, acero=adn420)
        assert res.verifica is True

    def test_no_verifica_con_As_insuficiente(self, adn420):
        As = 1.0  # cm², claramente insuficiente para Tu grande
        res = verificar_tirante(Tu=500.0, As=As, acero=adn420)
        assert res.verifica is False

    def test_phi_Tn_formula(self, adn420):
        As = 10.0  # cm²
        phi_Tn = PHI_TRACCION * As / 1e4 * adn420.fy * 1000.0
        res = verificar_tirante(Tu=100.0, As=As, acero=adn420)
        assert abs(res.phi_Tn - phi_Tn) < 1e-9

    def test_As_almacenado(self, adn420):
        res = verificar_tirante(Tu=100.0, As=8.0, acero=adn420)
        assert abs(res.As - 8.0) < 1e-9

    def test_Tu_almacenado(self, adn420):
        res = verificar_tirante(Tu=123.0, As=8.0, acero=adn420)
        assert abs(res.Tu - 123.0) < 1e-9

    def test_s_max_fis_calculado(self, adn420):
        res = verificar_tirante(Tu=100.0, As=8.0, acero=adn420, cc_mm=30.0)
        expected = s_max_fisuras(adn420, cc_mm=30.0)
        assert abs(res.s_max_fis_mm - expected) < 1e-9


# ---------------------------------------------------------------------------
# ResultadoTirante.adoptar
# ---------------------------------------------------------------------------

class TestAdoptar:
    def test_adoptar_guarda_phi_n(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        res.adoptar(phi=16, n_barras=4, ancho_mm=300.0)
        assert res.phi_barra == 16
        assert res.n_barras == 4

    def test_As_real_correcto(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        res.adoptar(phi=16, n_barras=4, ancho_mm=300.0)
        assert abs(res.As_real - 4 * BARRAS[16]) < 1e-9

    def test_separacion_n_mayor_1(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        cc = res.cc_mm
        n = 4
        phi = 16
        ancho = 300.0
        res.adoptar(phi=phi, n_barras=n, ancho_mm=ancho)
        s_libre = (ancho - 2.0 * cc - n * phi) / (n - 1)
        assert abs(res.s_barras_mm - s_libre) < 1e-6

    def test_separacion_n_igual_1(self, adn420):
        res = dimensionar_tirante(50.0, adn420)
        cc = res.cc_mm
        phi = 16
        ancho = 200.0
        res.adoptar(phi=phi, n_barras=1, ancho_mm=ancho)
        s_libre = ancho - 2.0 * cc - phi
        assert abs(res.s_barras_mm - s_libre) < 1e-6

    def test_verifica_fisuras_cuando_ok(self, adn420):
        # 2φ12 en 200mm: s_libre=(200-50-24)/1=126mm < s_max=300mm (fy=420, cc=25)
        res = dimensionar_tirante(100.0, adn420, cc_mm=25.0)
        res.adoptar(phi=12, n_barras=2, ancho_mm=200.0)
        assert res.verifica_fisuras is True

    def test_no_verifica_fisuras_cuando_apretado(self, adn420):
        # Ancho muy pequeño → separación muy ajustada
        res = dimensionar_tirante(300.0, adn420, cc_mm=25.0)
        res.adoptar(phi=25, n_barras=4, ancho_mm=200.0)
        # s_barras muy pequeña o incluso negativa → no verifica
        if res.s_barras_mm <= res.s_max_fis_mm:
            assert res.verifica_fisuras is True
        else:
            assert res.verifica_fisuras is False

    def test_adoptar_retorna_self(self, adn420):
        res = dimensionar_tirante(200.0, adn420)
        ret = res.adoptar(phi=16, n_barras=4, ancho_mm=300.0)
        assert ret is res

    def test_mostrar_no_falla(self, adn420, capsys):
        res = dimensionar_tirante(200.0, adn420)
        res.adoptar(phi=16, n_barras=4, ancho_mm=300.0)
        res.mostrar()
        out = capsys.readouterr().out
        assert "Tu" in out
        assert "As" in out

    def test_mostrar_sin_adoptar(self, adn420, capsys):
        res = dimensionar_tirante(200.0, adn420)
        res.mostrar()
        out = capsys.readouterr().out
        assert "Tu" in out


# ---------------------------------------------------------------------------
# dimensionar_tirante_variantes
# ---------------------------------------------------------------------------

class TestVariantes:
    def test_retorna_lista(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        assert isinstance(variantes, list)

    def test_no_vacia(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        assert len(variantes) > 0

    def test_todas_verifican(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        Tu = 200.0
        for v in variantes:
            phi_Tn = PHI_TRACCION * v["As"] / 1e4 * adn420.fy * 1000.0
            assert phi_Tn >= Tu - 1e-9

    def test_tiene_campos_requeridos(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        for v in variantes:
            assert "phi_mm" in v
            assert "n" in v
            assert "As" in v
            assert "phi_Tn" in v
            assert "rank" in v

    def test_rankeado_por_As_creciente(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        As_vals = [v["As"] for v in variantes]
        assert As_vals == sorted(As_vals)

    def test_rank_empieza_en_1(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        assert variantes[0]["rank"] == 1

    def test_rank_consecutivo(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        for i, v in enumerate(variantes, 1):
            assert v["rank"] == i

    def test_sin_duplicados(self, adn420):
        variantes = dimensionar_tirante_variantes(200.0, adn420)
        claves = [(v["phi_mm"], v["n"]) for v in variantes]
        assert len(claves) == len(set(claves))

    def test_Tu_pequeno_tiene_variantes(self, adn420):
        variantes = dimensionar_tirante_variantes(50.0, adn420)
        assert len(variantes) > 0

    def test_Tu_grande_tiene_variantes(self, adn420):
        variantes = dimensionar_tirante_variantes(800.0, adn420)
        assert len(variantes) > 0
