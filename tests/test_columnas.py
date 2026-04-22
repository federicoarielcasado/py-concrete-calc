"""
Tests de columnas cortas — CIRSOC 201-2005, cap. 5.

Cubren:
  - phi_columna: transición compresión / tracción
  - dimensionar_columna: cuantía mínima y calculada, estribos y zunchada
  - verificar_columna: φPn, verificación, cuantías
  - dimensionar_columna_variantes: sistema de variantes
  - diagrama_interaccion: puntos clave (compresión pura, balance, tracción pura)
  - DiagramaInteraccion.contiene: check P-M
"""
import math
import pytest

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular
from hormigon.columnas import (
    phi_columna,
    dimensionar_columna,
    verificar_columna,
    dimensionar_columna_variantes,
    diagrama_interaccion,
    PHI_ESTRIBO,
    PHI_ZUNCHADA,
    K_ESTRIBO,
    K_ZUNCHADA,
    RHO_MIN,
    RHO_MAX,
    _Pn0,
)

H25  = Hormigon(fc=25)
H30  = Hormigon(fc=30)
ADN420 = Acero(fy=420)
AM500  = Acero(fy=500)


# ---------------------------------------------------------------------------
# phi_columna
# ---------------------------------------------------------------------------

class TestPhiColumna:
    def test_compresion_estribos(self):
        eps_y = ADN420.epsilon_y
        assert phi_columna(0.0, eps_y, "estribos") == pytest.approx(PHI_ESTRIBO)
        assert phi_columna(eps_y, eps_y, "estribos") == pytest.approx(PHI_ESTRIBO)

    def test_compresion_zunchada(self):
        eps_y = ADN420.epsilon_y
        assert phi_columna(0.0, eps_y, "zunchada") == pytest.approx(PHI_ZUNCHADA)

    def test_traccion(self):
        eps_y = ADN420.epsilon_y
        assert phi_columna(0.005, eps_y) == pytest.approx(0.90)
        assert phi_columna(0.010, eps_y) == pytest.approx(0.90)

    def test_transicion_estribos(self):
        eps_y = ADN420.epsilon_y
        eps_mid = (eps_y + 0.005) / 2
        esperado = PHI_ESTRIBO + (0.90 - PHI_ESTRIBO) * (eps_mid - eps_y) / (0.005 - eps_y)
        assert phi_columna(eps_mid, eps_y, "estribos") == pytest.approx(esperado, rel=1e-9)

    def test_transicion_zunchada(self):
        eps_y = ADN420.epsilon_y
        eps_mid = (eps_y + 0.005) / 2
        esperado = PHI_ZUNCHADA + (0.90 - PHI_ZUNCHADA) * (eps_mid - eps_y) / (0.005 - eps_y)
        assert phi_columna(eps_mid, eps_y, "zunchada") == pytest.approx(esperado, rel=1e-9)

    def test_monotono_creciente(self):
        eps_y = ADN420.epsilon_y
        epsilons = [0.0, eps_y, (eps_y + 0.005) / 2, 0.005, 0.010]
        phis = [phi_columna(e, eps_y) for e in epsilons]
        assert phis == sorted(phis)


# ---------------------------------------------------------------------------
# _Pn0
# ---------------------------------------------------------------------------

class TestPn0:
    def test_formula_analitica(self):
        Ag     = 0.30 * 0.30    # m²
        Ast_m2 = 12.0 / 1e4     # cm² → m²
        esperado = (H25.fsc * (Ag - Ast_m2) + ADN420.fy * Ast_m2) * 1000.0
        assert _Pn0(H25, ADN420, Ag, Ast_m2) == pytest.approx(esperado, rel=1e-9)

    def test_sin_acero(self):
        Ag = 0.30 * 0.30
        Pn_solo = H25.fsc * Ag * 1000.0
        assert _Pn0(H25, ADN420, Ag, 0.0) == pytest.approx(Pn_solo, rel=1e-9)


# ---------------------------------------------------------------------------
# dimensionar_columna — cuantía mínima y calculada
# ---------------------------------------------------------------------------

class TestDimensionarColumna:
    @pytest.fixture
    def sec_30x30(self):
        return SeccionRectangular(
            b=0.30, h=0.30, recubrimiento=0.035,
            hormigon=H25, acero=ADN420,
        )

    @pytest.fixture
    def sec_40x40(self):
        return SeccionRectangular(
            b=0.40, h=0.40, recubrimiento=0.04,
            hormigon=H25, acero=ADN420,
        )

    def test_minimo_gobierna_Pu_bajo(self, sec_30x30):
        # Con Pu pequeño, el Ast calculado es negativo → rige mínimo
        res = dimensionar_columna(sec_30x30, Pu=200.0)
        Ag = sec_30x30.Ag
        assert res.rho_g == pytest.approx(RHO_MIN, rel=0.01)
        assert res.Ast == pytest.approx(RHO_MIN * Ag * 1e4, rel=0.01)

    def test_calculado_gobierna_Pu_alto(self, sec_40x40):
        # Con Pu más exigente, el cálculo supera el mínimo
        # φ·k = 0.65*0.80 = 0.52
        # Pu = 0.52 * [fsc*(Ag-Ast) + fy*Ast] * 1000
        # Elegimos Pu tal que ρg ≈ 0.03 (mayor que ρ_min=0.01)
        Ag  = sec_40x40.Ag   # 0.16 m²
        fsc = H25.fsc         # MPa
        fy  = ADN420.fy       # MPa
        rho_obj = 0.03
        Ast_m2_obj = rho_obj * Ag
        Pu_obj = PHI_ESTRIBO * K_ESTRIBO * (
            fsc * (Ag - Ast_m2_obj) + fy * Ast_m2_obj
        ) * 1000.0
        res = dimensionar_columna(sec_40x40, Pu=Pu_obj)
        assert res.rho_g == pytest.approx(rho_obj, rel=0.01)
        assert res.Ast == pytest.approx(rho_obj * Ag * 1e4, rel=0.01)

    def test_phi_Pn_mayor_o_igual_Pu(self, sec_30x30):
        for Pu in [200, 500, 800, 1000]:
            res = dimensionar_columna(sec_30x30, Pu=float(Pu))
            assert res.phi_Pn >= Pu - 1e-6

    def test_verifica_True(self, sec_30x30):
        res = dimensionar_columna(sec_30x30, Pu=400.0)
        assert res.verifica

    def test_tipo_estribos_phi_065(self, sec_30x30):
        res = dimensionar_columna(sec_30x30, Pu=400.0, tipo="estribos")
        k   = K_ESTRIBO
        assert res.phi_Pn == pytest.approx(PHI_ESTRIBO * k * res.Pn_0, rel=1e-6)

    def test_tipo_zunchada_phi_070(self, sec_30x30):
        res = dimensionar_columna(sec_30x30, Pu=400.0, tipo="zunchada")
        k   = K_ZUNCHADA
        assert res.phi_Pn == pytest.approx(PHI_ZUNCHADA * k * res.Pn_0, rel=1e-6)

    def test_rho_dentro_limites(self, sec_30x30):
        res = dimensionar_columna(sec_30x30, Pu=600.0)
        assert RHO_MIN - 1e-9 <= res.rho_g <= RHO_MAX + 1e-9

    def test_seccion_insuficiente_flagea(self, sec_30x30):
        # Pu mayor que la capacidad con ρ_max
        Ag     = sec_30x30.Ag
        fsc    = H25.fsc
        fy     = ADN420.fy
        Ast_max_m2 = RHO_MAX * Ag
        phi_Pn_max = PHI_ESTRIBO * K_ESTRIBO * (
            fsc * (Ag - Ast_max_m2) + fy * Ast_max_m2
        ) * 1000.0
        Pu_exceso = phi_Pn_max * 1.2
        res = dimensionar_columna(sec_30x30, Pu=Pu_exceso)
        assert not res.verifica_cuantia_max

    def test_cuantia_min_ok_cuando_minimo_gobierna(self, sec_30x30):
        res = dimensionar_columna(sec_30x30, Pu=100.0)
        assert res.verifica_cuantia_min


# ---------------------------------------------------------------------------
# verificar_columna
# ---------------------------------------------------------------------------

class TestVerificarColumna:
    @pytest.fixture
    def sec(self):
        return SeccionRectangular(
            b=0.35, h=0.35, recubrimiento=0.035,
            hormigon=H30, acero=ADN420,
        )

    def test_phi_Pn_formula(self, sec):
        Ast    = 16.0   # cm²
        Ag     = sec.Ag
        Ast_m2 = Ast / 1e4
        Pn_0   = _Pn0(H30, ADN420, Ag, Ast_m2)
        esperado = PHI_ESTRIBO * K_ESTRIBO * Pn_0
        res = verificar_columna(sec, Pu=0.0, Ast=Ast)
        assert res.phi_Pn == pytest.approx(esperado, rel=1e-9)

    def test_verifica_True(self, sec):
        res = verificar_columna(sec, Pu=1000.0, Ast=20.0)
        assert res.verifica

    def test_verifica_False_Pu_grande(self, sec):
        res = verificar_columna(sec, Pu=9999.0, Ast=10.0)
        assert not res.verifica

    def test_rho_g_correcto(self, sec):
        Ast = 12.0
        res = verificar_columna(sec, Pu=500.0, Ast=Ast)
        assert res.rho_g == pytest.approx(Ast / 1e4 / sec.Ag, rel=1e-9)

    def test_cuantia_min_violada(self, sec):
        # Ast muy pequeño
        Ast_min_cm2 = RHO_MIN * sec.Ag * 1e4
        res = verificar_columna(sec, Pu=0.0, Ast=Ast_min_cm2 * 0.5)
        assert not res.verifica_cuantia_min

    def test_cuantia_max_violada(self, sec):
        Ast_max_cm2 = RHO_MAX * sec.Ag * 1e4
        res = verificar_columna(sec, Pu=0.0, Ast=Ast_max_cm2 * 1.5)
        assert not res.verifica_cuantia_max

    def test_consistencia_dimensionar_verificar(self):
        sec = SeccionRectangular(
            b=0.40, h=0.40, recubrimiento=0.04,
            hormigon=H25, acero=ADN420,
        )
        Pu = 1500.0
        r_dim = dimensionar_columna(sec, Pu=Pu)
        r_ver = verificar_columna(sec, Pu=Pu, Ast=r_dim.Ast)
        assert r_ver.phi_Pn == pytest.approx(r_dim.phi_Pn, rel=1e-9)
        assert r_ver.verifica


# ---------------------------------------------------------------------------
# Adoptar
# ---------------------------------------------------------------------------

class TestAdoptar:
    def test_adoptar_registra_valores(self):
        sec = SeccionRectangular(
            b=0.30, h=0.30, recubrimiento=0.035,
            hormigon=H25, acero=ADN420,
        )
        res = dimensionar_columna(sec, Pu=500.0)
        res.adoptar(phi=16, n_barras=8)
        assert res.phi_barra == 16
        assert res.n_barras == 8
        from hormigon.materiales import BARRAS
        assert res.Ast_real == pytest.approx(8 * BARRAS[16], rel=1e-9)

    def test_mostrar_no_falla(self, capsys):
        sec = SeccionRectangular(
            b=0.30, h=0.30, recubrimiento=0.035,
            hormigon=H25, acero=ADN420,
        )
        res = dimensionar_columna(sec, Pu=400.0)
        res.adoptar(phi=12, n_barras=8)
        res.mostrar()
        captured = capsys.readouterr()
        assert "Pu" in captured.out


# ---------------------------------------------------------------------------
# Variantes
# ---------------------------------------------------------------------------

class TestVariantesColumna:
    @pytest.fixture
    def rset(self):
        sec = SeccionRectangular(
            b=0.35, h=0.35, recubrimiento=0.035,
            hormigon=H25, acero=ADN420,
        )
        return dimensionar_columna_variantes(sec, Pu=1200.0)

    def test_hay_variantes(self, rset):
        assert len(rset.variantes) > 0

    def test_todas_verifican(self, rset):
        for v in rset.variantes:
            assert v.verifica

    def test_ast_supera_requerido(self, rset):
        for v in rset.variantes:
            assert v.Ast >= rset.Ast_requerida - 1e-6

    def test_cuantias_dentro_limites(self, rset):
        for v in rset.variantes:
            assert RHO_MIN - 1e-9 <= v.rho_g <= RHO_MAX + 1e-9

    def test_rankeadas_por_Ast(self, rset):
        areas = [v.Ast for v in rset.variantes]
        assert areas == sorted(areas)

    def test_rank_1_es_minima_Ast(self, rset):
        v1 = rset.adoptar(1)
        assert v1.Ast == min(v.Ast for v in rset.variantes)

    def test_adoptar_invalido_lanza(self, rset):
        with pytest.raises(ValueError):
            rset.adoptar(9999)


# ---------------------------------------------------------------------------
# Diagrama de interacción
# ---------------------------------------------------------------------------

class TestDiagramaInteraccion:
    @pytest.fixture
    def sec(self):
        return SeccionRectangular(
            b=0.30, h=0.50, recubrimiento=0.05,
            hormigon=H25, acero=ADN420,
            recubrimiento_prima=0.05,
        )

    @pytest.fixture
    def diag(self, sec):
        return diagrama_interaccion(sec, Ast=20.0)

    def test_hay_puntos(self, diag):
        assert len(diag.puntos) > 10

    def test_Pn0_correcto(self, diag, sec):
        Ast_m2 = 20.0 / 1e4
        esperado = _Pn0(H25, ADN420, sec.Ag, Ast_m2)
        assert diag.Pn_0 == pytest.approx(esperado, rel=1e-9)

    def test_phi_Pn_max_correcto(self, diag):
        assert diag.phi_Pn_max == pytest.approx(
            PHI_ESTRIBO * K_ESTRIBO * diag.Pn_0, rel=1e-9
        )

    def test_todos_phi_Pn_acotados(self, diag):
        for p in diag.puntos:
            assert p.phi_Pn <= diag.phi_Pn_max + 1e-6

    def test_Mn_puro_compresion_cero(self, diag):
        # El punto con mayor Pn debe tener M ≈ 0 (sección simétrica)
        p_max = max(diag.puntos, key=lambda p: p.Pn)
        assert p_max.Mn == pytest.approx(0.0, abs=0.5)   # ≤ 0.5 kNm

    def test_balance_Pn_positivo(self, diag):
        # El punto de balance tiene P de compresión
        assert diag.Pn_bal > 0

    def test_balance_Mn_mayor_que_cero(self, diag):
        assert diag.Mn_bal > 0

    def test_balance_phi_es_phi_c(self, diag):
        # En el punto de balance, ε_t = ε_y → φ = φ_c
        assert diag.phi_Pn_bal == pytest.approx(
            PHI_ESTRIBO * diag.Pn_bal, rel=0.01
        )

    def test_traccion_pura_Pn_negativo(self, diag):
        p_ten = min(diag.puntos, key=lambda p: p.Pn)
        assert p_ten.Pn < 0

    def test_traccion_pura_Mn_cero(self, diag):
        p_ten = min(diag.puntos, key=lambda p: p.Pn)
        assert p_ten.Mn == pytest.approx(0.0, abs=0.1)

    def test_traccion_pura_formula(self, diag):
        Ast_m2 = 20.0 / 1e4
        Pn_ten = -Ast_m2 * ADN420.fy * 1000.0
        p_ten  = min(diag.puntos, key=lambda p: p.Pn)
        assert p_ten.Pn == pytest.approx(Pn_ten, rel=0.01)

    def test_phi_traccion_es_090(self, diag):
        p_ten = min(diag.puntos, key=lambda p: p.Pn)
        assert p_ten.phi == pytest.approx(0.90)

    def test_phi_Mn_igual_phi_por_Mn(self, diag):
        for p in diag.puntos:
            assert p.phi_Mn == pytest.approx(p.phi * p.Mn, rel=1e-9)

    def test_tipo_incorrecto_lanza(self):
        from hormigon.secciones import SeccionCircular
        sec_circ = SeccionCircular(D=0.40, recubrimiento=0.05, hormigon=H25, acero=ADN420)
        with pytest.raises(TypeError):
            diagrama_interaccion(sec_circ, Ast=15.0)


# ---------------------------------------------------------------------------
# DiagramaInteraccion.contiene
# ---------------------------------------------------------------------------

class TestContiene:
    @pytest.fixture
    def diag(self):
        sec = SeccionRectangular(
            b=0.30, h=0.50, recubrimiento=0.05,
            hormigon=H25, acero=ADN420,
            recubrimiento_prima=0.05,
        )
        return diagrama_interaccion(sec, Ast=24.0)

    def test_origen_dentro(self, diag):
        assert diag.contiene(0.0, 0.0)

    def test_Pu_mayor_phi_Pn_max_fuera(self, diag):
        assert not diag.contiene(diag.phi_Pn_max * 1.1, 0.0)

    def test_Pu_negativo_dentro(self, diag):
        # Un poco de tracción con M=0 debe estar dentro
        assert diag.contiene(diag.phi_Pn_bal * 0.01, 0.0)

    def test_punto_balance_dentro(self, diag):
        # Punto de balance (con margen) debe estar dentro
        assert diag.contiene(diag.phi_Pn_bal, diag.phi_Mn_bal * 0.95)

    def test_punto_lejano_fuera(self, diag):
        # Mu muy alto → fuera
        assert not diag.contiene(100.0, 9999.0)

    def test_consistencia_dimensionar_y_diagrama(self):
        sec = SeccionRectangular(
            b=0.35, h=0.35, recubrimiento=0.04,
            hormigon=H25, acero=ADN420,
            recubrimiento_prima=0.04,
        )
        Pu = 1000.0
        res = dimensionar_columna(sec, Pu=Pu)
        diag = diagrama_interaccion(sec, Ast=res.Ast)
        # Para Mu=0, el punto (Pu, 0) debe estar dentro
        assert diag.contiene(Pu, 0.0)
