import pytest
from hormigon.cargas import (
    combinaciones,
    U_max,
    wu_DL,
    momento_ultimo,
    corte_ultimo,
    evaluar_combinaciones,
)


class TestCombinaciones:
    def test_solo_D(self):
        # ec. 9-1 gobierna: U = 1.4*D
        assert U_max(D=100) == pytest.approx(140.0)

    def test_DL_tipico(self):
        # 1.4*D = 1.4*50 = 70
        # 1.2*D + 1.6*L = 1.2*50 + 1.6*100 = 60 + 160 = 220 → gobierna
        assert U_max(D=50, L=100) == pytest.approx(220.0)

    def test_ec91_gobierna_con_L_pequeno(self):
        # 1.4*100=140 vs 1.2*100+1.6*5=120+8=128 → ec.9-1
        assert U_max(D=100, L=5) == pytest.approx(140.0)

    def test_combo_gobernante(self):
        res = evaluar_combinaciones(D=50, L=100)
        assert res.combo_gobernante == "9-2"
        assert res.U == pytest.approx(220.0)

    def test_todas_las_claves(self):
        combos = combinaciones(D=10, L=10, Lr=5, S=3, W=8, E=6)
        assert set(combos.keys()) == {"9-1","9-2","9-3a","9-3b","9-4a","9-4b","9-5a","9-5b"}


class TestWuDL:
    def test_wu_DL_ec12_gobierna(self):
        # max(1.4*10, 1.2*10+1.6*20) = max(14, 12+32) = max(14,44) = 44
        assert wu_DL(wD=10, wL=20) == pytest.approx(44.0)

    def test_wu_DL_ec14_gobierna(self):
        # max(1.4*100, 1.2*100+1.6*1) = max(140, 121.6) = 140
        assert wu_DL(wD=100, wL=1) == pytest.approx(140.0)

    def test_wu_DL_iguales(self):
        # max(1.4*10, 1.2*10+1.6*10) = max(14, 28) = 28
        assert wu_DL(wD=10, wL=10) == pytest.approx(28.0)


class TestCoeficientes:
    def test_momento_ultimo(self):
        # M_u = (1/16) * 30 * 4² = 30 kNm
        assert momento_ultimo(C_m=1/16, wu=30, ln=4.0) == pytest.approx(30.0)

    def test_corte_ultimo(self):
        # V_u = (1/2) * 30 * 4 = 60 kN
        assert corte_ultimo(C_v=0.5, wu=30, ln=4.0) == pytest.approx(60.0)

    def test_corte_primer_apoyo_interior(self):
        # V_u = 1.15/2 * wu * ln
        assert corte_ultimo(C_v=1.15/2, wu=40, ln=5.0) == pytest.approx(115.0)


class TestEjemploCIRSOC:
    """Ejemplo 1.I — Parte 1 CIRSOC: combinaciones en tanque elevado."""

    def test_ejemplo_1I(self):
        # Cargas características típicas del ejemplo 1.I
        # Se verifica que ec. 9-2 produce el U mayor
        D, L = 350.0, 200.0   # kN (valores representativos del ejemplo)
        res = evaluar_combinaciones(D=D, L=L)
        u_91 = 1.4 * D
        u_92 = 1.2 * D + 1.6 * L
        assert res.combos["9-1"] == pytest.approx(u_91)
        assert res.combos["9-2"] == pytest.approx(u_92)
        assert res.U == pytest.approx(max(u_91, u_92))
