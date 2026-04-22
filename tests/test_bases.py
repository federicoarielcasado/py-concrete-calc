"""
Tests de bases aisladas centradas — CIRSOC 201-2005, cap. 15.

Cubren:
  - Vc_punzonamiento: tres fórmulas art. 11.12.2.1 para columna cuadrada y rectangular
  - dimensionar_base_centrada: determinación de planta, espesor, armadura y verificaciones
  - verificar_base_centrada: con geometría completamente especificada
  - Consistencia interna: φVc ≥ Vu, φMn ≥ Mu en todos los diseños automáticos
"""
import math
import pytest

from hormigon.materiales import Hormigon, Acero
from hormigon.bases import (
    Vc_punzonamiento,
    dimensionar_base_centrada,
    verificar_base_centrada,
    ResultadoBase,
    PHI_CORTE,
)

H25  = Hormigon(fc=25)
H30  = Hormigon(fc=30)
H20  = Hormigon(fc=20)
ADN420 = Acero(fy=420)


# ---------------------------------------------------------------------------
# Vc_punzonamiento
# ---------------------------------------------------------------------------

class TestVcPunzonamiento:
    def test_columna_cuadrada_Vc3_gobierna(self):
        # Para bc=hc (βc=1): Vc1=0.51·√fc·bo·d·1000, Vc3=0.33 → Vc3 es mínimo
        d  = 0.40
        bc = hc = 0.30
        bo = 2 * (bc + d) + 2 * (hc + d)
        esperado = 0.33 * math.sqrt(25) * bo * d * 1000.0
        assert Vc_punzonamiento(H25, bc, hc, d) == pytest.approx(esperado, rel=1e-9)

    def test_columna_rectangular_reduce_Vc1(self):
        # βc > 1 → Vc1 < Vc_cuadrada; puede gobernar sobre Vc3
        Vc_sq   = Vc_punzonamiento(H25, bc=0.30, hc=0.30, d=0.40)
        Vc_rect = Vc_punzonamiento(H25, bc=0.60, hc=0.30, d=0.40)
        # βc=2 → Vc1 = (0.17+0.17)*√25*bo_rect*d → puede ser < Vc3
        # En todo caso: Vc_rect ≠ Vc_sq (distinto bo y distinto βc)
        assert Vc_rect != pytest.approx(Vc_sq)

    def test_crece_con_d(self):
        for d1, d2 in [(0.20, 0.40), (0.30, 0.50)]:
            assert Vc_punzonamiento(H25, 0.30, 0.30, d2) > Vc_punzonamiento(H25, 0.30, 0.30, d1)

    def test_crece_con_fc(self):
        assert Vc_punzonamiento(H30, 0.30, 0.30, 0.40) > Vc_punzonamiento(H20, 0.30, 0.30, 0.40)

    def test_tipo_interior_alpha40(self):
        d  = 0.30
        bc = hc = 0.25
        bo = 2 * (bc + d) + 2 * (hc + d)
        # Vc2 interior (αs=40)
        Vc2 = (0.083 * 40.0 * d / bo + 0.17) * math.sqrt(25) * bo * d * 1000.0
        Vc3 = 0.33 * math.sqrt(25) * bo * d * 1000.0
        esperado = min(Vc2, Vc3)   # Vc1 > Vc3 para βc=1
        assert Vc_punzonamiento(H25, bc, hc, d, "interior") == pytest.approx(esperado, rel=1e-9)

    def test_positivo(self):
        assert Vc_punzonamiento(H25, 0.30, 0.30, 0.40) > 0


# ---------------------------------------------------------------------------
# dimensionar_base_centrada — cuadrada
# ---------------------------------------------------------------------------

class TestDimensionarBaseCuadrada:
    @pytest.fixture
    def res(self):
        return dimensionar_base_centrada(
            bc=0.30, hc=0.30,
            Pu=800.0, P_s=600.0, q_adm=150.0,
            hormigon=H25, acero=ADN420,
        )

    def test_B_igual_L_cuadrada(self, res):
        assert res.B == pytest.approx(res.L, abs=1e-9)

    def test_planta_cubre_P_s(self, res):
        A_min = 600.0 / 150.0
        assert res.B * res.L >= A_min - 1e-6

    def test_q_servicio_le_q_adm(self, res):
        assert res.q_servicio <= res.q_adm + 1e-6
        assert res.verifica_suelo

    def test_q_neta_formula(self, res):
        assert res.q_neta == pytest.approx(res.Pu / (res.B * res.L), rel=1e-9)

    def test_h_f_ge_h_min(self, res):
        from hormigon.bases import _H_F_MIN
        assert res.h_f >= _H_F_MIN - 1e-9

    def test_d_consistente_con_h_f(self, res):
        from hormigon.bases import _REC_DEFAULT
        assert res.d == pytest.approx(res.h_f - _REC_DEFAULT, rel=1e-9)

    def test_verifica_punzonamiento(self, res):
        assert res.phi_Vc_punch >= res.Vu_punch - 1e-6
        assert res.verifica_punch

    def test_verifica_corte_1way(self, res):
        assert res.phi_Vc_1way_L >= res.Vu_1way_L - 1e-6
        assert res.verifica_1way

    def test_verifica_flexion_L(self, res):
        assert res.phi_Mn_L >= res.Mu_L - 1e-6
        assert res.verifica_flex_L

    def test_verifica_flexion_B(self, res):
        assert res.phi_Mn_B >= res.Mu_B - 1e-6
        assert res.verifica_flex_B

    def test_As_L_positivo(self, res):
        assert res.As_L > 0
        assert res.As_L_m > 0

    def test_As_B_positivo(self, res):
        assert res.As_B > 0

    def test_voladizo_L(self, res):
        assert res.l_v_L == pytest.approx((res.L - res.hc) / 2.0, rel=1e-9)

    def test_voladizo_B(self, res):
        assert res.l_v_B == pytest.approx((res.B - res.bc) / 2.0, rel=1e-9)

    def test_Mu_L_formula(self, res):
        Mu_esp = res.q_neta * res.B * res.l_v_L ** 2 / 2.0
        assert res.Mu_L == pytest.approx(Mu_esp, rel=1e-9)

    def test_Mu_B_formula(self, res):
        Mu_esp = res.q_neta * res.L * res.l_v_B ** 2 / 2.0
        assert res.Mu_B == pytest.approx(Mu_esp, rel=1e-9)

    def test_As_L_m_es_As_L_sobre_B(self, res):
        assert res.As_L_m == pytest.approx(res.As_L / res.B, rel=1e-9)

    def test_As_B_m_es_As_B_sobre_L(self, res):
        assert res.As_B_m == pytest.approx(res.As_B / res.L, rel=1e-9)

    def test_gamma_s_cuadrada(self, res):
        # Base cuadrada: L=B → βc=1 → γs = 2/(1+1) = 1.0
        assert res.gamma_s == pytest.approx(1.0, rel=1e-9)

    def test_As_banda_igual_As_B_cuadrada(self, res):
        assert res.As_banda_B == pytest.approx(res.As_B, rel=1e-9)

    def test_bo_formula(self, res):
        bo_esp = 2 * (res.bc + res.d) + 2 * (res.hc + res.d)
        assert res.bo == pytest.approx(bo_esp, rel=1e-9)

    def test_phi_Vc_punch_formula(self, res):
        Vc = Vc_punzonamiento(H25, res.bc, res.hc, res.d)
        assert res.phi_Vc_punch == pytest.approx(PHI_CORTE * Vc, rel=1e-9)

    def test_verifica_global(self, res):
        assert res.verifica

    def test_mostrar_no_falla(self, res, capsys):
        res.mostrar()
        captured = capsys.readouterr()
        assert "Pu" in captured.out or "Base" in captured.out


# ---------------------------------------------------------------------------
# dimensionar_base_centrada — carga alta (estrés de punzonamiento)
# ---------------------------------------------------------------------------

class TestBaseCargaAlta:
    def test_Pu_alto_genera_base_mayor(self):
        res_bajo = dimensionar_base_centrada(
            bc=0.30, hc=0.30,
            Pu=500.0, P_s=380.0, q_adm=120.0,
            hormigon=H25, acero=ADN420,
        )
        res_alto = dimensionar_base_centrada(
            bc=0.30, hc=0.30,
            Pu=1500.0, P_s=1150.0, q_adm=120.0,
            hormigon=H25, acero=ADN420,
        )
        assert res_alto.B >= res_bajo.B
        assert res_alto.As_L >= res_bajo.As_L

    def test_verifica_todo(self):
        res = dimensionar_base_centrada(
            bc=0.40, hc=0.40,
            Pu=2000.0, P_s=1500.0, q_adm=200.0,
            hormigon=H30, acero=ADN420,
        )
        assert res.verifica_punch
        assert res.verifica_1way
        assert res.verifica_flex_L
        assert res.verifica_flex_B


# ---------------------------------------------------------------------------
# dimensionar_base_centrada — rectangular
# ---------------------------------------------------------------------------

class TestBaseCentradaRectangular:
    @pytest.fixture
    def res(self):
        return dimensionar_base_centrada(
            bc=0.30, hc=0.50,
            Pu=1000.0, P_s=750.0, q_adm=150.0,
            hormigon=H25, acero=ADN420,
            cuadrada=False, L_B_ratio=1.5,
        )

    def test_L_ge_B(self, res):
        assert res.L >= res.B - 1e-9

    def test_ratio_aprox_L_B(self, res):
        # El ratio L/B debe ser ≥ 1 (puede ser algo mayor por redondeo)
        assert res.L / res.B >= 1.0 - 1e-6

    def test_gamma_s_menor_1(self, res):
        # Base rectangular → γs < 1
        assert res.gamma_s < 1.0

    def test_gamma_s_formula(self, res):
        beta = res.L / res.B
        assert res.gamma_s == pytest.approx(2.0 / (beta + 1.0), rel=1e-9)

    def test_As_banda_le_As_B(self, res):
        assert res.As_banda_B <= res.As_B + 1e-9

    def test_distribución_suma_As_B(self, res):
        # As_banda + 2*As_lateral = As_B
        total = res.As_banda_B + 2 * res.As_lateral_B
        assert total == pytest.approx(res.As_B, rel=1e-6)

    def test_verifica(self, res):
        assert res.verifica


# ---------------------------------------------------------------------------
# dimensionar_base_centrada — h_f fijo por el usuario
# ---------------------------------------------------------------------------

class TestHfFijo:
    def test_h_f_adoptado_se_respeta(self):
        res = dimensionar_base_centrada(
            bc=0.30, hc=0.30,
            Pu=600.0, P_s=450.0, q_adm=120.0,
            hormigon=H25, acero=ADN420,
            h_f=0.50,
        )
        assert res.h_f == pytest.approx(0.50, rel=1e-9)

    def test_d_consistente_con_h_f_fijo(self):
        from hormigon.bases import _REC_DEFAULT
        res = dimensionar_base_centrada(
            bc=0.30, hc=0.30,
            Pu=600.0, P_s=450.0, q_adm=120.0,
            hormigon=H25, acero=ADN420,
            h_f=0.55,
        )
        assert res.d == pytest.approx(0.55 - _REC_DEFAULT, rel=1e-9)


# ---------------------------------------------------------------------------
# verificar_base_centrada
# ---------------------------------------------------------------------------

class TestVerificarBase:
    @pytest.fixture
    def res_ver(self):
        return verificar_base_centrada(
            bc=0.30, hc=0.30,
            B=1.80, L=1.80, h_f=0.50,
            Pu=800.0, P_s=600.0, q_adm=150.0,
            hormigon=H25, acero=ADN420,
        )

    def test_B_L_respetados(self, res_ver):
        assert res_ver.B == pytest.approx(1.80, rel=1e-9)
        assert res_ver.L == pytest.approx(1.80, rel=1e-9)

    def test_h_f_respetado(self, res_ver):
        assert res_ver.h_f == pytest.approx(0.50, rel=1e-9)

    def test_q_neta_formula(self, res_ver):
        assert res_ver.q_neta == pytest.approx(800.0 / (1.80 * 1.80), rel=1e-9)

    def test_phi_Vc_punch_formula(self, res_ver):
        Vc = Vc_punzonamiento(H25, 0.30, 0.30, res_ver.d)
        assert res_ver.phi_Vc_punch == pytest.approx(PHI_CORTE * Vc, rel=1e-9)

    def test_Mu_L_formula(self, res_ver):
        l_v = (1.80 - 0.30) / 2.0
        q   = res_ver.q_neta
        assert res_ver.Mu_L == pytest.approx(q * 1.80 * l_v ** 2 / 2.0, rel=1e-9)

    def test_phi_Mn_L_ge_Mu_L(self, res_ver):
        assert res_ver.phi_Mn_L >= res_ver.Mu_L - 1e-6

    def test_verifica_shear(self, res_ver):
        assert res_ver.verifica_punch
        assert res_ver.verifica_1way


# ---------------------------------------------------------------------------
# Consistencia dimensionar → verificar
# ---------------------------------------------------------------------------

class TestConsistenciaDimVerif:
    def test_verificar_con_geometria_de_dimensionar(self):
        res_d = dimensionar_base_centrada(
            bc=0.30, hc=0.30,
            Pu=900.0, P_s=680.0, q_adm=160.0,
            hormigon=H25, acero=ADN420,
        )
        res_v = verificar_base_centrada(
            bc=res_d.bc, hc=res_d.hc,
            B=res_d.B, L=res_d.L, h_f=res_d.h_f,
            Pu=res_d.Pu, P_s=res_d.P_s, q_adm=res_d.q_adm,
            hormigon=H25, acero=ADN420,
        )
        assert res_v.q_neta == pytest.approx(res_d.q_neta, rel=1e-9)
        assert res_v.Mu_L   == pytest.approx(res_d.Mu_L,   rel=1e-9)
        assert res_v.As_L   == pytest.approx(res_d.As_L,   rel=1e-9)
        assert res_v.verifica_punch
        assert res_v.verifica_1way

    def test_dimensionar_siempre_verifica(self):
        casos = [
            (0.25, 0.25, 500,  380,  120),
            (0.30, 0.40, 800,  610,  150),
            (0.40, 0.40, 1500, 1150, 180),
            (0.50, 0.50, 2500, 1900, 200),
        ]
        for bc, hc, Pu, Ps, qa in casos:
            res = dimensionar_base_centrada(
                bc=bc, hc=hc,
                Pu=float(Pu), P_s=float(Ps), q_adm=float(qa),
                hormigon=H25, acero=ADN420,
            )
            assert res.verifica_punch, f"Falla punch: bc={bc}, Pu={Pu}"
            assert res.verifica_1way,  f"Falla 1way:  bc={bc}, Pu={Pu}"
            assert res.verifica_flex_L, f"Falla flex L: bc={bc}, Pu={Pu}"
