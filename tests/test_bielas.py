"""Tests para hormigon/bielas.py — CIRSOC 201-2005 art. 10.7."""
import math
import pytest

from hormigon.materiales import Hormigon, Acero
from hormigon.bielas import (
    Nodo,
    Biela,
    Tirante,
    beta_n,
    verificar_nudo,
    ModeloBielaTirante,
    dimensionar_mensula,
    PHI_BT,
)


# ---------------------------------------------------------------------------
# Materiales comunes
# ---------------------------------------------------------------------------

@pytest.fixture
def h25():
    return Hormigon(fc=25)

@pytest.fixture
def h30():
    return Hormigon(fc=30)

@pytest.fixture
def adn420():
    return Acero(fy=420)


# ---------------------------------------------------------------------------
# Nodo
# ---------------------------------------------------------------------------

class TestNodo:
    def test_atributos(self):
        n = Nodo("A", x=1.0, y=2.0)
        assert n.nombre == "A"
        assert abs(n.x - 1.0) < 1e-9
        assert abs(n.y - 2.0) < 1e-9

    def test_coordenadas_cero(self):
        n = Nodo("O", x=0.0, y=0.0)
        assert abs(n.x) < 1e-9


# ---------------------------------------------------------------------------
# Biela
# ---------------------------------------------------------------------------

class TestBiela:
    def test_area(self):
        b = Biela("A", "B", fuerza=200.0, ancho_mm=150.0, espesor_mm=300.0)
        assert abs(b.area_mm2 - 45000.0) < 1e-9

    def test_tension(self):
        # 200 kN / (150×300 mm²) = 200000 N / 45000 mm² ≈ 4.444 MPa
        b = Biela("A", "B", fuerza=200.0, ancho_mm=150.0, espesor_mm=300.0)
        assert abs(b.tension_mpa() - 200000.0 / 45000.0) < 1e-6

    def test_fce_prismatica(self, h25):
        b = Biela("A", "B", fuerza=100.0, ancho_mm=200.0, espesor_mm=300.0, beta_s=1.0)
        assert abs(b.fce(h25) - 0.85 * 1.0 * 25.0) < 1e-9

    def test_fce_abanico_sin_refuerzo(self, h25):
        b = Biela("A", "B", fuerza=100.0, ancho_mm=200.0, espesor_mm=300.0, beta_s=0.60)
        assert abs(b.fce(h25) - 0.85 * 0.60 * 25.0) < 1e-9

    def test_phi_fce(self, h25):
        b = Biela("A", "B", fuerza=100.0, ancho_mm=200.0, espesor_mm=300.0, beta_s=1.0)
        assert abs(b.phi_fce(h25) - PHI_BT * b.fce(h25)) < 1e-9

    def test_verifica_ok(self, h25):
        # Tensión pequeña → verifica
        b = Biela("A", "B", fuerza=10.0, ancho_mm=400.0, espesor_mm=400.0, beta_s=1.0)
        assert b.verifica(h25) is True

    def test_no_verifica_tension_grande(self, h25):
        # Tensión muy grande → no verifica
        b = Biela("A", "B", fuerza=10000.0, ancho_mm=100.0, espesor_mm=100.0, beta_s=0.40)
        assert b.verifica(h25) is False

    def test_beta_s_default_1(self):
        b = Biela("A", "B", fuerza=100.0, ancho_mm=200.0, espesor_mm=300.0)
        assert abs(b.beta_s - 1.0) < 1e-9

    def test_mayor_fuerza_mayor_tension(self, h25):
        b1 = Biela("A", "B", fuerza=100.0, ancho_mm=200.0, espesor_mm=300.0)
        b2 = Biela("A", "B", fuerza=200.0, ancho_mm=200.0, espesor_mm=300.0)
        assert b2.tension_mpa() > b1.tension_mpa()

    def test_mayor_area_menor_tension(self, h25):
        b1 = Biela("A", "B", fuerza=200.0, ancho_mm=200.0, espesor_mm=200.0)
        b2 = Biela("A", "B", fuerza=200.0, ancho_mm=400.0, espesor_mm=200.0)
        assert b2.tension_mpa() < b1.tension_mpa()


# ---------------------------------------------------------------------------
# Tirante
# ---------------------------------------------------------------------------

class TestTirante:
    def test_As_req_formula(self, adn420):
        # As = Tu / (φ × fy × 1000) × 1e4 [cm²]
        Tu = 150.0
        t = Tirante("A", "B", fuerza=Tu, acero=adn420)
        expected = Tu / (PHI_BT * 420.0 * 1000.0) * 1e4
        assert abs(t.As_req - expected) < 1e-9

    def test_As_req_positivo(self, adn420):
        t = Tirante("A", "B", fuerza=200.0, acero=adn420)
        assert t.As_req > 0

    def test_verifica_As_suficiente(self, adn420):
        t = Tirante("A", "B", fuerza=150.0, acero=adn420)
        assert t.verifica_As(t.As_req * 1.1) is True

    def test_no_verifica_As_insuficiente(self, adn420):
        t = Tirante("A", "B", fuerza=150.0, acero=adn420)
        assert t.verifica_As(t.As_req * 0.5) is False

    def test_mayor_fuerza_mayor_As(self, adn420):
        t1 = Tirante("A", "B", fuerza=100.0, acero=adn420)
        t2 = Tirante("A", "B", fuerza=300.0, acero=adn420)
        assert t2.As_req > t1.As_req

    def test_mayor_fy_menor_As(self):
        a420 = Acero(fy=420)
        a500 = Acero(fy=500)
        t420 = Tirante("A", "B", fuerza=200.0, acero=a420)
        t500 = Tirante("A", "B", fuerza=200.0, acero=a500)
        assert t500.As_req < t420.As_req


# ---------------------------------------------------------------------------
# beta_n
# ---------------------------------------------------------------------------

class TestBetaN:
    def test_CCC(self):
        assert abs(beta_n("CCC") - 1.00) < 1e-9

    def test_CCT(self):
        assert abs(beta_n("CCT") - 0.80) < 1e-9

    def test_CTT(self):
        assert abs(beta_n("CTT") - 0.60) < 1e-9

    def test_case_insensitive(self):
        assert abs(beta_n("cct") - 0.80) < 1e-9
        assert abs(beta_n("Ccc") - 1.00) < 1e-9

    def test_invalido_error(self):
        with pytest.raises(ValueError):
            beta_n("TTT")

    def test_invalido_vacio(self):
        with pytest.raises(ValueError):
            beta_n("")


# ---------------------------------------------------------------------------
# verificar_nudo
# ---------------------------------------------------------------------------

class TestVerificarNudo:
    def test_nudo_CCC_verifica_pequena_tension(self, h25):
        v = verificar_nudo("N1", "CCC", h25, fuerza_kN=50.0, area_nudo_mm2=100000.0)
        assert v.verifica is True

    def test_nudo_CTT_no_verifica_tension_grande(self, h25):
        # σ = 500000 N / 1000 mm² = 500 MPa >> φ×fnn
        v = verificar_nudo("N2", "CTT", h25, fuerza_kN=500.0, area_nudo_mm2=1000.0)
        assert v.verifica is False

    def test_phi_fnn_CCC(self, h25):
        v = verificar_nudo("N1", "CCC", h25, fuerza_kN=10.0, area_nudo_mm2=50000.0)
        assert abs(v.phi_fnn_mpa - PHI_BT * 0.85 * 1.00 * 25.0) < 1e-9

    def test_phi_fnn_CCT(self, h25):
        v = verificar_nudo("N1", "CCT", h25, fuerza_kN=10.0, area_nudo_mm2=50000.0)
        assert abs(v.phi_fnn_mpa - PHI_BT * 0.85 * 0.80 * 25.0) < 1e-9

    def test_phi_fnn_CTT(self, h25):
        v = verificar_nudo("N1", "CTT", h25, fuerza_kN=10.0, area_nudo_mm2=50000.0)
        assert abs(v.phi_fnn_mpa - PHI_BT * 0.85 * 0.60 * 25.0) < 1e-9

    def test_tension_formula(self, h25):
        v = verificar_nudo("N1", "CCT", h25, fuerza_kN=200.0, area_nudo_mm2=80000.0)
        expected = 200.0 * 1000.0 / 80000.0
        assert abs(v.tension_mpa - expected) < 1e-9

    def test_nombre_almacenado(self, h25):
        v = verificar_nudo("NodoX", "CCC", h25, fuerza_kN=10.0, area_nudo_mm2=10000.0)
        assert v.nombre == "NodoX"

    def test_tipo_almacenado(self, h25):
        v = verificar_nudo("N1", "CCT", h25, fuerza_kN=10.0, area_nudo_mm2=10000.0)
        assert v.tipo == "CCT"

    def test_mayor_fc_mayor_resistencia(self, h25, h30):
        v25 = verificar_nudo("N1", "CCC", h25, fuerza_kN=10.0, area_nudo_mm2=10000.0)
        v30 = verificar_nudo("N1", "CCC", h30, fuerza_kN=10.0, area_nudo_mm2=10000.0)
        assert v30.phi_fnn_mpa > v25.phi_fnn_mpa


# ---------------------------------------------------------------------------
# ModeloBielaTirante
# ---------------------------------------------------------------------------

class TestModeloBielaTirante:
    def _modelo_simple(self, adn420, h25):
        """Modelo triangular simple: A-B biela, A-C tirante."""
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=1.0)
        m.agregar_nodo("B", x=1.0, y=0.0)
        m.agregar_nodo("C", x=1.0, y=1.0)
        m.agregar_biela("A", "B", fuerza=200.0, ancho_mm=200.0, espesor_mm=300.0, beta_s=0.60)
        m.agregar_tirante("A", "C", fuerza=150.0, acero=adn420)
        return m

    def test_nodos_agregados(self, adn420, h25):
        m = self._modelo_simple(adn420, h25)
        assert "A" in m.nodos
        assert "B" in m.nodos

    def test_longitud_entre_nodos(self, adn420, h25):
        m = self._modelo_simple(adn420, h25)
        l = m.longitud("A", "B")
        assert abs(l - math.sqrt(2.0)) < 1e-9

    def test_longitud_horizontal(self, adn420, h25):
        m = self._modelo_simple(adn420, h25)
        assert abs(m.longitud("A", "C") - 1.0) < 1e-9

    def test_verificar_devuelve_resultado(self, adn420, h25):
        m = self._modelo_simple(adn420, h25)
        res = m.verificar(h25)
        assert res is not None

    def test_resultado_tiene_bielas_y_tirantes(self, adn420, h25):
        m = self._modelo_simple(adn420, h25)
        res = m.verificar(h25)
        assert len(res.res_bielas) == 1
        assert len(res.res_tirantes) == 1

    def test_biela_pequena_verifica(self, adn420, h25):
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=0.0)
        m.agregar_nodo("B", x=1.0, y=0.0)
        m.agregar_biela("A", "B", fuerza=10.0, ancho_mm=500.0, espesor_mm=500.0, beta_s=1.0)
        res = m.verificar(h25)
        assert res.verifica is True

    def test_biela_grande_no_verifica(self, adn420, h25):
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=0.0)
        m.agregar_nodo("B", x=1.0, y=0.0)
        m.agregar_biela("A", "B", fuerza=50000.0, ancho_mm=10.0, espesor_mm=10.0, beta_s=0.40)
        res = m.verificar(h25)
        assert res.verifica is False

    def test_resultado_tirante_As(self, adn420, h25):
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=0.0)
        m.agregar_nodo("B", x=1.0, y=0.0)
        m.agregar_tirante("A", "B", fuerza=200.0, acero=adn420)
        res = m.verificar(h25)
        expected_As = 200.0 / (PHI_BT * 420.0 * 1000.0) * 1e4
        assert abs(res.res_tirantes[0].As_req - expected_As) < 1e-9

    def test_sin_bielas_verifica(self, adn420, h25):
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=0.0)
        m.agregar_tirante("A", "A", fuerza=100.0, acero=adn420)
        res = m.verificar(h25)
        assert res.verifica is True  # sin bielas → no hay nada que no verifique

    def test_mostrar_no_falla(self, adn420, h25, capsys):
        m = self._modelo_simple(adn420, h25)
        res = m.verificar(h25)
        res.mostrar()
        out = capsys.readouterr().out
        assert "BIELAS" in out
        assert "TIRANTES" in out

    def test_multiples_bielas(self, adn420, h25):
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=0.0)
        m.agregar_nodo("B", x=1.0, y=0.0)
        m.agregar_nodo("C", x=2.0, y=0.0)
        m.agregar_biela("A", "B", fuerza=10.0, ancho_mm=300.0, espesor_mm=300.0)
        m.agregar_biela("B", "C", fuerza=10.0, ancho_mm=300.0, espesor_mm=300.0)
        res = m.verificar(h25)
        assert len(res.res_bielas) == 2


# ---------------------------------------------------------------------------
# dimensionar_mensula
# ---------------------------------------------------------------------------

class TestDimensionarMensula:
    def test_resultado_no_nulo(self, h25, adn420):
        res = dimensionar_mensula(Vu=150.0, a=0.20, b_mm=300.0, d=0.40,
                                   hormigon=h25, acero=adn420)
        assert res is not None

    def test_theta_formula(self, h25, adn420):
        a = 0.20
        d = 0.40
        res = dimensionar_mensula(Vu=150.0, a=a, b_mm=300.0, d=d,
                                   hormigon=h25, acero=adn420)
        expected_deg = math.degrees(math.atan2(d, a))
        assert abs(res.theta_deg - expected_deg) < 1e-6

    def test_F_biela_formula(self, h25, adn420):
        Vu = 150.0
        a = 0.20
        d = 0.40
        res = dimensionar_mensula(Vu=Vu, a=a, b_mm=300.0, d=d,
                                   hormigon=h25, acero=adn420)
        theta = math.atan2(d, a)
        expected = Vu / math.sin(theta)
        assert abs(res.F_biela - expected) < 1e-6

    def test_F_tirante_formula(self, h25, adn420):
        Vu = 150.0
        a = 0.20
        d = 0.40
        res = dimensionar_mensula(Vu=Vu, a=a, b_mm=300.0, d=d,
                                   hormigon=h25, acero=adn420)
        # F_tirante = Vu × a / d
        expected = Vu * a / d
        assert abs(res.F_tirante_principal - expected) < 1e-6

    def test_As_principal_formula(self, h25, adn420):
        Vu = 150.0
        a = 0.20
        d = 0.40
        res = dimensionar_mensula(Vu=Vu, a=a, b_mm=300.0, d=d,
                                   hormigon=h25, acero=adn420)
        F_tir = Vu * a / d
        expected = F_tir / (PHI_BT * 420.0 * 1000.0) * 1e4
        assert abs(res.As_principal - expected) < 1e-9

    def test_As_total_con_Nu(self, h25, adn420):
        Nu = 30.0
        res = dimensionar_mensula(Vu=150.0, a=0.20, b_mm=300.0, d=0.40,
                                   hormigon=h25, acero=adn420, Nu=Nu)
        As_nu = Nu / (PHI_BT * 420.0 * 1000.0) * 1e4
        assert abs(res.As_total - (res.As_principal + As_nu)) < 1e-9

    def test_As_total_sin_Nu(self, h25, adn420):
        res = dimensionar_mensula(Vu=150.0, a=0.20, b_mm=300.0, d=0.40,
                                   hormigon=h25, acero=adn420)
        assert abs(res.As_total - res.As_principal) < 1e-9

    def test_mayor_Vu_mayor_As(self, h25, adn420):
        r1 = dimensionar_mensula(Vu=100.0, a=0.20, b_mm=300.0, d=0.40,
                                  hormigon=h25, acero=adn420)
        r2 = dimensionar_mensula(Vu=200.0, a=0.20, b_mm=300.0, d=0.40,
                                  hormigon=h25, acero=adn420)
        assert r2.As_principal > r1.As_principal

    def test_mayor_a_mayor_tirante(self, h25, adn420):
        # Mayor excentricidad → mayor brazo → mayor F_tirante
        r1 = dimensionar_mensula(Vu=150.0, a=0.15, b_mm=300.0, d=0.40,
                                  hormigon=h25, acero=adn420)
        r2 = dimensionar_mensula(Vu=150.0, a=0.30, b_mm=300.0, d=0.40,
                                  hormigon=h25, acero=adn420)
        assert r2.F_tirante_principal > r1.F_tirante_principal

    def test_error_a_mayor_d(self, h25, adn420):
        with pytest.raises(ValueError):
            dimensionar_mensula(Vu=150.0, a=0.50, b_mm=300.0, d=0.30,
                                hormigon=h25, acero=adn420)

    def test_error_a_cero(self, h25, adn420):
        with pytest.raises((ValueError, ZeroDivisionError)):
            dimensionar_mensula(Vu=150.0, a=0.0, b_mm=300.0, d=0.40,
                                hormigon=h25, acero=adn420)

    def test_verifica_biela_tension_ok(self, h25, adn420):
        # Sección grande, fuerza pequeña → verifica
        res = dimensionar_mensula(Vu=50.0, a=0.15, b_mm=500.0, d=0.50,
                                   hormigon=h25, acero=adn420,
                                   ancho_biela_mm=250.0)
        assert res.verifica_biela is True

    def test_verifica_biela_tension_excesiva(self, h25, adn420):
        # Fuerza grande, sección pequeña → no verifica
        res = dimensionar_mensula(Vu=2000.0, a=0.20, b_mm=100.0, d=0.40,
                                   hormigon=h25, acero=adn420,
                                   ancho_biela_mm=10.0)
        assert res.verifica_biela is False

    def test_phi_BT_es_0_75(self):
        assert abs(PHI_BT - 0.75) < 1e-9

    def test_almacena_Vu_Nu_a_d(self, h25, adn420):
        res = dimensionar_mensula(Vu=150.0, a=0.20, b_mm=300.0, d=0.40,
                                   hormigon=h25, acero=adn420, Nu=20.0)
        assert abs(res.Vu - 150.0) < 1e-9
        assert abs(res.Nu - 20.0) < 1e-9
        assert abs(res.a - 0.20) < 1e-9
        assert abs(res.d - 0.40) < 1e-9

    def test_mostrar_no_falla(self, h25, adn420, capsys):
        res = dimensionar_mensula(Vu=150.0, a=0.20, b_mm=300.0, d=0.40,
                                   hormigon=h25, acero=adn420)
        res.mostrar()
        out = capsys.readouterr().out
        assert "Vu" in out
        assert "As" in out

    def test_verifica_global_igual_verifica_biela(self, h25, adn420):
        res = dimensionar_mensula(Vu=150.0, a=0.20, b_mm=300.0, d=0.40,
                                   hormigon=h25, acero=adn420)
        assert res.verifica == res.verifica_biela
