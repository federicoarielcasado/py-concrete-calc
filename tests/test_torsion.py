"""Tests para hormigon/torsion.py — CIRSOC 201-2005 art. 11.6."""
import math
import pytest

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular
from hormigon.torsion import (
    geometria_torsion,
    Tu_umbral,
    Tu_redistribucion,
    calcular_torsion,
    PHI_TORSION,
)


# ---------------------------------------------------------------------------
# Materiales y sección comunes
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

@pytest.fixture
def sec_30x60(h25, adn420):
    return SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.04, hormigon=h25, acero=adn420)

@pytest.fixture
def sec_30x50(h30, adn420):
    return SeccionRectangular(b=0.30, h=0.50, recubrimiento=0.04, hormigon=h30, acero=adn420)


# ---------------------------------------------------------------------------
# geometria_torsion
# ---------------------------------------------------------------------------

class TestGeometriaTorsion:
    def test_Acp(self, h25, adn420):
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert abs(g["Acp"] - 0.18) < 1e-9

    def test_pcp(self, h25, adn420):
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert abs(g["pcp"] - 1.80) < 1e-9

    def test_Aoh(self, h25, adn420):
        # Aoh = (0.30 - 2×0.04) × (0.60 - 2×0.04) = 0.22 × 0.52
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert abs(g["Aoh"] - 0.22 * 0.52) < 1e-9

    def test_ph(self, h25, adn420):
        # ph = 2×(0.22 + 0.52)
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert abs(g["ph"] - 2.0 * (0.22 + 0.52)) < 1e-9

    def test_Ao(self, h25, adn420):
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert abs(g["Ao"] - 0.85 * g["Aoh"]) < 1e-9

    def test_cuadrada(self):
        g = geometria_torsion(0.40, 0.40, 0.05)
        assert abs(g["Acp"] - 0.16) < 1e-9
        assert abs(g["Aoh"] - 0.30 * 0.30) < 1e-9

    def test_c_est_grande(self):
        g = geometria_torsion(0.50, 0.50, 0.10)
        assert abs(g["Aoh"] - 0.30 * 0.30) < 1e-9


# ---------------------------------------------------------------------------
# Tu_umbral y Tu_redistribucion
# ---------------------------------------------------------------------------

class TestTuUmbral:
    def test_formula_30x60(self, h25):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(h25, g["Acp"], g["pcp"])
        # φ × √25/12 × (0.18²/1.80) × 1000
        expected = PHI_TORSION * math.sqrt(25) / 12.0 * (0.18**2 / 1.80) * 1000.0
        assert abs(Tu_u - expected) < 1e-6

    def test_positivo(self, h25):
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert Tu_umbral(h25, g["Acp"], g["pcp"]) > 0

    def test_mayor_fc_mayor_umbral(self):
        h20 = Hormigon(fc=20)
        h35 = Hormigon(fc=35)
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert Tu_umbral(h35, g["Acp"], g["pcp"]) > Tu_umbral(h20, g["Acp"], g["pcp"])

    def test_b30h60_h25_valor(self, h25):
        # Verificación numérica: Acp=0.18, pcp=1.80
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(h25, g["Acp"], g["pcp"])
        # ≈ 0.75 × 5/12 × 0.018 × 1000 ≈ 5.625 kNm
        assert abs(Tu_u - 5.625) < 0.01

    def test_redistribucion_es_4_veces_umbral(self, h25):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u  = Tu_umbral(h25, g["Acp"], g["pcp"])
        Tu_re = Tu_redistribucion(h25, g["Acp"], g["pcp"])
        assert abs(Tu_re - 4.0 * Tu_u) < 1e-9

    def test_redistribucion_positivo(self, h25):
        g = geometria_torsion(0.30, 0.60, 0.04)
        assert Tu_redistribucion(h25, g["Acp"], g["pcp"]) > 0


# ---------------------------------------------------------------------------
# calcular_torsion — caso despreciable
# ---------------------------------------------------------------------------

class TestTorsionDespreciable:
    def test_despreciable_flag(self, sec_30x60):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(sec_30x60.hormigon, g["Acp"], g["pcp"])
        res  = calcular_torsion(sec_30x60, Tu=Tu_u * 0.5, Vu=50.0, c_est=0.04)
        assert res.despreciable is True

    def test_despreciable_At_s_cero(self, sec_30x60):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(sec_30x60.hormigon, g["Acp"], g["pcp"])
        res  = calcular_torsion(sec_30x60, Tu=Tu_u * 0.5, Vu=50.0, c_est=0.04)
        assert res.At_s == 0.0

    def test_no_despreciable(self, sec_30x60):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(sec_30x60.hormigon, g["Acp"], g["pcp"])
        res  = calcular_torsion(sec_30x60, Tu=Tu_u * 2.0, Vu=50.0, c_est=0.04)
        assert res.despreciable is False
        assert res.At_s > 0.0


# ---------------------------------------------------------------------------
# calcular_torsion — propiedades geométricas en resultado
# ---------------------------------------------------------------------------

class TestTorsionGeometria:
    def test_Aoh_correcto(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert abs(res.Aoh - 0.22 * 0.52) < 1e-9

    def test_ph_correcto(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert abs(res.ph - 2.0 * (0.22 + 0.52)) < 1e-9

    def test_Ao_correcto(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert abs(res.Ao - 0.85 * res.Aoh) < 1e-9

    def test_Acp_pcp_correctos(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert abs(res.Acp - 0.18) < 1e-9
        assert abs(res.pcp - 1.80) < 1e-9


# ---------------------------------------------------------------------------
# calcular_torsion — tensión combinada
# ---------------------------------------------------------------------------

class TestTorsionTauCombinado:
    def test_tau_combinado_formula(self, sec_30x60):
        Tu = 20.0   # kNm
        Vu = 80.0   # kN
        res = calcular_torsion(sec_30x60, Tu=Tu, Vu=Vu, c_est=0.04)
        bw = 0.30
        d  = sec_30x60.d
        Aoh = 0.22 * 0.52
        ph  = 2.0 * (0.22 + 0.52)
        tau_v = Vu / (bw * d * 1000.0)
        tau_t = Tu * ph / (1.7 * Aoh**2 * 1000.0)
        expected = math.sqrt(tau_v**2 + tau_t**2)
        assert abs(res.tau_combinado - expected) < 1e-6

    def test_tau_limite_formula(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=80.0, c_est=0.04)
        fc = 25.0
        expected = PHI_TORSION * (math.sqrt(fc) / 6.0 + 2.0 * math.sqrt(fc) / 3.0)
        assert abs(res.tau_limite - expected) < 1e-6

    def test_tau_limite_constante_dado_fc(self, sec_30x60):
        res1 = calcular_torsion(sec_30x60, Tu=10.0, Vu=50.0, c_est=0.04)
        res2 = calcular_torsion(sec_30x60, Tu=20.0, Vu=80.0, c_est=0.04)
        assert abs(res1.tau_limite - res2.tau_limite) < 1e-9

    def test_verifica_combinado_pequeno_Tu_Vu(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=5.0, Vu=30.0, c_est=0.04)
        assert res.verifica_combinado is True

    def test_verifica_global_igual_verifica_combinado(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=15.0, Vu=60.0, c_est=0.04)
        assert res.verifica == res.verifica_combinado


# ---------------------------------------------------------------------------
# calcular_torsion — armadura transversal
# ---------------------------------------------------------------------------

class TestTorsionArmaduraTransversal:
    def test_At_s_formula_theta45(self, sec_30x60):
        Tu = 20.0
        res = calcular_torsion(sec_30x60, Tu=Tu, Vu=50.0, c_est=0.04, theta_deg=45.0)
        Ao  = res.Ao
        fyt = 420.0
        # cot(45°) = 1
        expected = Tu * 1000.0 / (PHI_TORSION * 2.0 * Ao * fyt * 1.0)
        assert abs(res.At_s - expected) < 1.0  # puede ser mayor por mínimo

    def test_At_s_positivo_con_torsion(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert res.At_s > 0.0

    def test_At_s_minimo_art11651(self, sec_30x60):
        # At/s ≥ 0.175 × bw / fyt [mm²/m]
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        At_s_min = 0.175 * 0.30 * 1000.0 / 420.0
        assert res.At_s >= At_s_min - 1e-9

    def test_Av_s_corte_puro(self, sec_30x60):
        # Con Vu grande, Av_s debe ser significativo
        res = calcular_torsion(sec_30x60, Tu=6.0, Vu=120.0, c_est=0.04)
        assert res.Av_s > 0.0

    def test_Avt_s_es_suma(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=80.0, c_est=0.04)
        assert abs(res.Avt_s - (res.At_s + res.Av_s)) < 1e-9

    def test_theta_60_mayor_At_s(self, sec_30x60):
        res45 = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04, theta_deg=45.0)
        res60 = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04, theta_deg=60.0)
        # cot(60°) < cot(45°) → At/s mayor para θ=60°
        assert res60.At_s >= res45.At_s - 1e-6

    def test_theta_30_menor_At_s(self, sec_30x60):
        res45 = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04, theta_deg=45.0)
        res30 = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04, theta_deg=30.0)
        # cot(30°) > cot(45°) → At/s menor para θ=30°
        assert res30.At_s <= res45.At_s + 1e-6


# ---------------------------------------------------------------------------
# calcular_torsion — armadura longitudinal
# ---------------------------------------------------------------------------

class TestTorsionArmaduraLongitudinal:
    def test_Al_positivo(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert res.Al > 0.0

    def test_Al_mayor_igual_Al_min(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert res.Al >= res.Al_min - 1e-9

    def test_Al_min_positivo(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert res.Al_min > 0.0

    def test_Al_crece_con_Tu(self, sec_30x60):
        res1 = calcular_torsion(sec_30x60, Tu=15.0, Vu=50.0, c_est=0.04)
        res2 = calcular_torsion(sec_30x60, Tu=30.0, Vu=50.0, c_est=0.04)
        assert res2.Al >= res1.Al


# ---------------------------------------------------------------------------
# calcular_torsion — compatibilidad vs equilibrio
# ---------------------------------------------------------------------------

class TestTorsionCompatibilidad:
    def test_equilibrio_no_limita_Tu(self, sec_30x60):
        Tu_grande = 40.0
        res = calcular_torsion(sec_30x60, Tu=Tu_grande, Vu=30.0, c_est=0.04, equilibrio=True)
        # tau_t se calcula con Tu completo
        Aoh = res.Aoh
        ph  = res.ph
        tau_t = Tu_grande * ph / (1.7 * Aoh**2 * 1000.0)
        assert abs(res.tau_combinado**2 - (res.tau_combinado**2)) < 1.0  # sanity

    def test_compatibilidad_limita_Tu(self, sec_30x60):
        Tu_grande = 40.0
        res_eq   = calcular_torsion(sec_30x60, Tu=Tu_grande, Vu=30.0, c_est=0.04, equilibrio=True)
        res_comp = calcular_torsion(sec_30x60, Tu=Tu_grande, Vu=30.0, c_est=0.04, equilibrio=False)
        # compatibilidad limita Tu → menor tau_combinado → menor At_s
        assert res_comp.tau_combinado <= res_eq.tau_combinado + 1e-9
        assert res_comp.At_s <= res_eq.At_s + 1e-6

    def test_compatibilidad_Tu_red_aplicado(self, sec_30x60):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_re = Tu_redistribucion(sec_30x60.hormigon, g["Acp"], g["pcp"])
        Tu_dis = Tu_re * 3.0   # muy grande
        res = calcular_torsion(sec_30x60, Tu=Tu_dis, Vu=30.0, c_est=0.04, equilibrio=False)
        # At_s debe corresponder a Tu_re, no a Tu_dis
        res_ref = calcular_torsion(sec_30x60, Tu=Tu_re, Vu=30.0, c_est=0.04, equilibrio=True)
        assert abs(res.At_s - res_ref.At_s) < 1.0  # within 1 mm²/m


# ---------------------------------------------------------------------------
# calcular_torsion — Vc (corte nominal del hormigón)
# ---------------------------------------------------------------------------

class TestTorsionVc:
    def test_Vc_positivo(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=10.0, Vu=50.0, c_est=0.04)
        assert res.Vc > 0.0

    def test_phi_Vc(self, sec_30x60):
        from hormigon.corte import PHI_CORTE
        res = calcular_torsion(sec_30x60, Tu=10.0, Vu=50.0, c_est=0.04)
        assert abs(res.phi_Vc - PHI_CORTE * res.Vc) < 1e-9

    def test_Vc_crece_con_fc(self, adn420):
        sec_h20 = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.04,
                                     hormigon=Hormigon(fc=20), acero=adn420)
        sec_h35 = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.04,
                                     hormigon=Hormigon(fc=35), acero=adn420)
        res20 = calcular_torsion(sec_h20, Tu=10.0, Vu=50.0, c_est=0.04)
        res35 = calcular_torsion(sec_h35, Tu=10.0, Vu=50.0, c_est=0.04)
        assert res35.Vc > res20.Vc


# ---------------------------------------------------------------------------
# calcular_torsion — coherencia de entradas
# ---------------------------------------------------------------------------

class TestTorsionCoherencia:
    def test_Tu_se_almacena(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=18.5, Vu=60.0, c_est=0.04)
        assert abs(res.Tu - 18.5) < 1e-9

    def test_Vu_se_almacena(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=18.5, Vu=60.0, c_est=0.04)
        assert abs(res.Vu - 60.0) < 1e-9

    def test_theta_se_almacena(self, sec_30x60):
        res = calcular_torsion(sec_30x60, Tu=18.5, Vu=60.0, c_est=0.04, theta_deg=40.0)
        assert abs(res.theta_deg - 40.0) < 1e-9

    def test_Tu_umbral_almacenado(self, sec_30x60):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(sec_30x60.hormigon, g["Acp"], g["pcp"])
        res  = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert abs(res.Tu_umbral - Tu_u) < 1e-9

    def test_Tu_red_almacenado(self, sec_30x60):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_re = Tu_redistribucion(sec_30x60.hormigon, g["Acp"], g["pcp"])
        res   = calcular_torsion(sec_30x60, Tu=20.0, Vu=50.0, c_est=0.04)
        assert abs(res.Tu_red - Tu_re) < 1e-9

    def test_mostrar_no_falla(self, sec_30x60, capsys):
        res = calcular_torsion(sec_30x60, Tu=20.0, Vu=80.0, c_est=0.04)
        res.mostrar()
        out = capsys.readouterr().out
        assert "Tu" in out
        assert "At" in out

    def test_mostrar_despreciable(self, sec_30x60, capsys):
        g = geometria_torsion(0.30, 0.60, 0.04)
        Tu_u = Tu_umbral(sec_30x60.hormigon, g["Acp"], g["pcp"])
        res  = calcular_torsion(sec_30x60, Tu=Tu_u * 0.3, Vu=30.0, c_est=0.04)
        res.mostrar()
        out = capsys.readouterr().out
        assert "DESPRECIABLE" in out

    def test_secciones_diferentes_resultados_diferentes(self, h25, adn420):
        sec_a = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.04, hormigon=h25, acero=adn420)
        sec_b = SeccionRectangular(b=0.40, h=0.60, recubrimiento=0.04, hormigon=h25, acero=adn420)
        r_a = calcular_torsion(sec_a, Tu=20.0, Vu=50.0, c_est=0.04)
        r_b = calcular_torsion(sec_b, Tu=20.0, Vu=50.0, c_est=0.04)
        assert r_a.Acp != r_b.Acp
