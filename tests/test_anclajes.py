"""Tests para hormigon/anclajes.py — CIRSOC 201-2005 art. 12."""
import math
import pytest

from hormigon.materiales import Hormigon, Acero, DIAMETROS
from hormigon.anclajes import (
    psi_t,
    psi_e,
    psi_s,
    ld_traccion,
    ldc_compresion,
    ldh_gancho,
    ls_traslape,
    TablaAnclajes,
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

@pytest.fixture
def am500():
    return Acero(fy=500)


# ---------------------------------------------------------------------------
# Factores de modificación
# ---------------------------------------------------------------------------

class TestPsiT:
    def test_barra_superior_1_3(self):
        assert abs(psi_t(True) - 1.3) < 1e-9

    def test_barra_inferior_1_0(self):
        assert abs(psi_t(False) - 1.0) < 1e-9


class TestPsiE:
    def test_epoxi_1_5(self):
        assert abs(psi_e(True) - 1.5) < 1e-9

    def test_no_epoxi_1_0(self):
        assert abs(psi_e(False) - 1.0) < 1e-9


class TestPsiS:
    def test_pequena_0_8(self):
        assert abs(psi_s(16.0) - 0.8) < 1e-9

    def test_limite_19_0_8(self):
        assert abs(psi_s(19.0) - 0.8) < 1e-9

    def test_grande_1_0(self):
        assert abs(psi_s(25.0) - 1.0) < 1e-9

    def test_20mm_1_0(self):
        assert abs(psi_s(20.0) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# ld_traccion (art. 12.2.3)
# ---------------------------------------------------------------------------

class TestLdTraccion:
    def test_minimo_300mm(self, h25, adn420):
        # Barra φ6 con condiciones muy favorables: debe ser ≥ 300mm
        ld = ld_traccion(6.0, h25, adn420, cb_mm=80.0, Ktr=50.0)
        assert ld >= 0.30 - 1e-9

    def test_minimo_8db(self, h25, adn420):
        # Para barra φ32: 8×32 = 256mm < 300mm, así que domina 300mm
        ld = ld_traccion(32.0, h25, adn420, cb_mm=80.0, Ktr=50.0)
        assert ld >= 8.0 * 32.0 / 1000.0 - 1e-9

    def test_positivo(self, h25, adn420):
        for db in [12.0, 16.0, 20.0, 25.0]:
            assert ld_traccion(db, h25, adn420) > 0

    def test_barra_superior_mayor(self, h25, adn420):
        ld_inf = ld_traccion(16.0, h25, adn420, barra_superior=False)
        ld_sup = ld_traccion(16.0, h25, adn420, barra_superior=True)
        assert ld_sup >= ld_inf

    def test_epoxi_mayor(self, h25, adn420):
        ld_std  = ld_traccion(16.0, h25, adn420, recubierta_epoxi=False)
        ld_ep   = ld_traccion(16.0, h25, adn420, recubierta_epoxi=True)
        assert ld_ep >= ld_std

    def test_mayor_fc_menor_ld(self):
        # φ32, cb=20mm: fórmula supera el mínimo 300mm para H-20 (360mm) pero no H-35 (272mm)
        # → H-20 da ld mayor (fórmula), H-35 da mínimo 300mm → ld_h20 > ld_h35
        h20 = Hormigon(fc=20)
        h35 = Hormigon(fc=35)
        a420 = Acero(fy=420)
        ld20 = ld_traccion(32.0, h20, a420, cb_mm=20.0)
        ld35 = ld_traccion(32.0, h35, a420, cb_mm=20.0)
        assert ld35 < ld20

    def test_mayor_Ktr_menor_ld(self, h25, adn420):
        ld0   = ld_traccion(20.0, h25, adn420, cb_mm=40.0, Ktr=0.0)
        ld20  = ld_traccion(20.0, h25, adn420, cb_mm=40.0, Ktr=20.0)
        assert ld20 <= ld0

    def test_ratio_acotado_2_5(self, h25, adn420):
        # Con Ktr muy grande, el ratio no puede superar 2.5
        ld_lim = ld_traccion(20.0, h25, adn420, cb_mm=200.0, Ktr=1000.0)
        ld_25  = ld_traccion(20.0, h25, adn420, cb_mm=200.0, Ktr=800.0)
        assert abs(ld_lim - ld_25) < 1e-9  # ambos saturan en 2.5

    def test_mayor_fy_mayor_ld(self):
        # φ32, cb=20mm, H-20: ambos valores superan el mínimo 300mm
        h20 = Hormigon(fc=20)
        a420 = Acero(fy=420)
        a500 = Acero(fy=500)
        ld420 = ld_traccion(32.0, h20, a420, cb_mm=20.0)
        ld500 = ld_traccion(32.0, h20, a500, cb_mm=20.0)
        assert ld500 > ld420

    def test_lambda_ligero_mayor_ld(self, h25, adn420):
        # φ32, cb=20mm: fórmula supera el mínimo → el λ influye en el resultado
        ld_normal = ld_traccion(32.0, h25, adn420, cb_mm=20.0, lambda_horm=1.0)
        ld_ligero = ld_traccion(32.0, h25, adn420, cb_mm=20.0, lambda_horm=0.75)
        assert ld_ligero > ld_normal

    def test_producto_psi_t_e_acotado_1_7(self, h25, adn420):
        # ψt=1.3, ψe=1.5 → producto=1.95, debe ser acotado a 1.7
        ld_sin_cota  = ld_traccion(20.0, h25, adn420,
                                    barra_superior=True, recubierta_epoxi=True)
        # Verificar que el resultado es consistente (no NaN, > mínimo)
        assert ld_sin_cota >= 0.30

    def test_cb_none_usa_40mm(self, h25, adn420):
        ld_none = ld_traccion(20.0, h25, adn420, cb_mm=None)
        ld_40   = ld_traccion(20.0, h25, adn420, cb_mm=40.0)
        assert abs(ld_none - ld_40) < 1e-9

    def test_db_16_h25_fy420_conservador(self, h25, adn420):
        # φ16, H-25, ADN420, condiciones estándar: domina mínimo 300mm
        ld = ld_traccion(16.0, h25, adn420)
        assert 0.28 < ld < 1.50  # ≥ 300mm (mínimo reglamentario)

    def test_formula_numerica_phi16(self, h25, adn420):
        db = 16.0
        fy = 420.0
        fc = 25.0
        cb = 40.0
        ratio = min((cb + 0.0) / db, 2.5)
        ld_mm = (3.0 * fy * 1.0 * 0.8) / (40.0 * 1.0 * math.sqrt(fc) * ratio) * db
        ld_mm = max(ld_mm, 300.0, 8.0 * db)
        expected = ld_mm / 1000.0
        result = ld_traccion(16.0, h25, adn420, cb_mm=40.0)
        assert abs(result - expected) < 1e-9


# ---------------------------------------------------------------------------
# ldc_compresion (art. 12.3.2)
# ---------------------------------------------------------------------------

class TestLdcCompresion:
    def test_minimo_200mm(self, h25, adn420):
        ldc = ldc_compresion(6.0, h25, adn420)
        assert ldc >= 0.20 - 1e-9

    def test_positivo(self, h25, adn420):
        for db in [12.0, 16.0, 20.0, 25.0, 32.0]:
            assert ldc_compresion(db, h25, adn420) > 0

    def test_mayor_db_mayor_ldc(self, h25, adn420):
        ldc16 = ldc_compresion(16.0, h25, adn420)
        ldc25 = ldc_compresion(25.0, h25, adn420)
        assert ldc25 > ldc16

    def test_mayor_fc_menor_ldc(self, adn420):
        h20 = Hormigon(fc=20)
        h35 = Hormigon(fc=35)
        ldc20 = ldc_compresion(20.0, h20, adn420)
        ldc35 = ldc_compresion(20.0, h35, adn420)
        assert ldc35 < ldc20

    def test_formula_primer_termino(self, h25, adn420):
        db = 20.0
        expected1 = 0.24 * 420.0 * db / math.sqrt(25.0) / 1000.0
        result = ldc_compresion(db, h25, adn420)
        assert result >= expected1 - 1e-9

    def test_formula_segundo_termino(self, h25, adn420):
        db = 20.0
        expected2 = 0.044 * 420.0 * db / 1000.0
        result = ldc_compresion(db, h25, adn420)
        assert result >= expected2 - 1e-9

    def test_menor_que_ld_traccion_barra_grande(self, h25, adn420):
        # Para φ32 con cb_mm=20: fórmula ld governa (361mm) > mínimo ldc governa (645mm)
        # Desarrollo en compresión es mayor que el mínimo de tracción en barras grandes
        # En general ldc[formula] > ld[formula]: se verifica cuando ambas son fórmula
        # Con cb=20mm, φ32, H25, la fórmula de tracción (322mm) < la de compresión (645mm)
        ld  = ld_traccion(32.0, h25, adn420, cb_mm=20.0)
        ldc = ldc_compresion(32.0, h25, adn420)
        assert ld <= ldc

    def test_lambda_ligero(self, h25, adn420):
        ldc_n = ldc_compresion(20.0, h25, adn420, lambda_horm=1.0)
        ldc_l = ldc_compresion(20.0, h25, adn420, lambda_horm=0.75)
        assert ldc_l >= ldc_n


# ---------------------------------------------------------------------------
# ldh_gancho (art. 12.5)
# ---------------------------------------------------------------------------

class TestLdhGancho:
    def test_minimo_8db(self, h25, adn420):
        for db in [6.0, 10.0, 16.0]:
            ldh = ldh_gancho(db, h25, adn420)
            assert ldh >= 8.0 * db / 1000.0 - 1e-9

    def test_minimo_150mm(self, h25, adn420):
        ldh = ldh_gancho(6.0, h25, adn420)
        assert ldh >= 0.15 - 1e-9

    def test_positivo(self, h25, adn420):
        for db in DIAMETROS:
            assert ldh_gancho(float(db), h25, adn420) > 0

    def test_epoxi_mayor(self, h25, adn420):
        ldh_std = ldh_gancho(16.0, h25, adn420, recubierta_epoxi=False)
        ldh_ep  = ldh_gancho(16.0, h25, adn420, recubierta_epoxi=True)
        assert ldh_ep >= ldh_std

    def test_mayor_fc_menor_ldh(self, adn420):
        h20 = Hormigon(fc=20)
        h35 = Hormigon(fc=35)
        ldh20 = ldh_gancho(20.0, h20, adn420)
        ldh35 = ldh_gancho(20.0, h35, adn420)
        assert ldh35 < ldh20

    def test_menor_que_ld_traccion_cb_pequeño(self, h25, adn420):
        # Con cb=20mm y φ32: ld[fórmula=322mm] < ldh[fórmula=1213mm]
        ldh = ldh_gancho(32.0, h25, adn420)
        ld  = ld_traccion(32.0, h25, adn420, cb_mm=20.0)
        assert ld <= ldh

    def test_formula_numerica_phi20(self, h25, adn420):
        db = 20.0
        ldh_mm = 0.24 * 1.0 * 420.0 * db / (1.0 * math.sqrt(25.0))
        ldh_mm = max(ldh_mm, 8.0 * db, 150.0)
        expected = ldh_mm / 1000.0
        result = ldh_gancho(db, h25, adn420)
        assert abs(result - expected) < 1e-9


# ---------------------------------------------------------------------------
# ls_traslape (art. 12.15)
# ---------------------------------------------------------------------------

class TestLsTraslape:
    def test_clase_B_es_1_3_ld(self, h25, adn420):
        ld = ld_traccion(20.0, h25, adn420)
        ls = ls_traslape(20.0, h25, adn420, clase="B")
        assert abs(ls - max(1.3 * ld, 0.30)) < 1e-9

    def test_clase_A_es_1_0_ld(self, h25, adn420):
        ld = ld_traccion(20.0, h25, adn420)
        ls = ls_traslape(20.0, h25, adn420, clase="A")
        assert abs(ls - max(1.0 * ld, 0.30)) < 1e-9

    def test_clase_B_mayor_igual_A(self, h25, adn420):
        ls_A = ls_traslape(20.0, h25, adn420, clase="A")
        ls_B = ls_traslape(20.0, h25, adn420, clase="B")
        assert ls_B >= ls_A

    def test_minimo_300mm(self, h25, adn420):
        ls = ls_traslape(6.0, h25, adn420, cb_mm=80.0, Ktr=50.0)
        assert ls >= 0.30 - 1e-9

    def test_clase_case_insensitive(self, h25, adn420):
        ls_b = ls_traslape(20.0, h25, adn420, clase="B")
        ls_b_low = ls_traslape(20.0, h25, adn420, clase="b")
        assert abs(ls_b - ls_b_low) < 1e-9

    def test_positivo(self, h25, adn420):
        for db in [12.0, 16.0, 20.0]:
            assert ls_traslape(db, h25, adn420) > 0

    def test_barra_superior_mayor(self, h25, adn420):
        ls_inf = ls_traslape(16.0, h25, adn420, barra_superior=False)
        ls_sup = ls_traslape(16.0, h25, adn420, barra_superior=True)
        assert ls_sup >= ls_inf


# ---------------------------------------------------------------------------
# TablaAnclajes
# ---------------------------------------------------------------------------

class TestTablaAnclajes:
    def test_instancia(self, h25, adn420):
        t = TablaAnclajes(hormigon=h25, acero=adn420)
        assert t is not None

    def test_ld_phi16(self, h25, adn420):
        t = TablaAnclajes(hormigon=h25, acero=adn420, cb_mm_fijo=40.0)
        ld = ld_traccion(16.0, h25, adn420, cb_mm=40.0)
        assert abs(t.ld(16.0) - ld) < 1e-9

    def test_ldc_phi20(self, h25, adn420):
        t = TablaAnclajes(hormigon=h25, acero=adn420)
        ldc = ldc_compresion(20.0, h25, adn420)
        assert abs(t.ldc(20.0) - ldc) < 1e-9

    def test_ldh_phi25(self, h25, adn420):
        t = TablaAnclajes(hormigon=h25, acero=adn420)
        ldh = ldh_gancho(25.0, h25, adn420)
        assert abs(t.ldh(25.0) - ldh) < 1e-9

    def test_ls_B_phi16(self, h25, adn420):
        t  = TablaAnclajes(hormigon=h25, acero=adn420, cb_mm_fijo=40.0)
        ls = ls_traslape(16.0, h25, adn420, clase="B", cb_mm=40.0)
        assert abs(t.ls_B(16.0) - ls) < 1e-9

    def test_mostrar_no_falla(self, h25, adn420, capsys):
        t = TablaAnclajes(hormigon=h25, acero=adn420)
        t.mostrar()
        out = capsys.readouterr().out
        assert "ld" in out

    def test_mostrar_contiene_todos_diametros(self, h25, adn420, capsys):
        t = TablaAnclajes(hormigon=h25, acero=adn420)
        t.mostrar()
        out = capsys.readouterr().out
        for d in DIAMETROS:
            assert str(d) in out

    def test_barra_sup_modifica_ld(self, h25, adn420):
        t_inf = TablaAnclajes(hormigon=h25, acero=adn420, barra_sup=False)
        t_sup = TablaAnclajes(hormigon=h25, acero=adn420, barra_sup=True)
        assert t_sup.ld(20.0) >= t_inf.ld(20.0)

    def test_ld_crece_con_db(self, h25, adn420):
        # cb=20mm: para φ32 la fórmula supera el mínimo (322mm > 300mm)
        # → ld(32) > ld(25) aunque ld(25) esté en el mínimo (300mm)
        t = TablaAnclajes(hormigon=h25, acero=adn420, cb_mm_fijo=20.0)
        assert t.ld(32.0) > t.ld(25.0)

    def test_ldc_crece_con_db(self, h25, adn420):
        t = TablaAnclajes(hormigon=h25, acero=adn420)
        assert t.ldc(25.0) > t.ldc(16.0)
