import math
import pytest
from hormigon.materiales import Hormigon, Acero, BARRAS, DIAMETROS


class TestHormigon:
    def test_beta1_fc_menor_28(self):
        assert Hormigon(fc=20).beta1 == pytest.approx(0.85)
        assert Hormigon(fc=25).beta1 == pytest.approx(0.85)

    def test_beta1_fc_igual_28(self):
        assert Hormigon(fc=28).beta1 == pytest.approx(0.85)

    def test_beta1_fc30(self):
        # 0.85 - 0.05*(30-28)/7 = 0.83571...
        assert Hormigon(fc=30).beta1 == pytest.approx(0.8357, abs=0.0001)

    def test_beta1_fc35(self):
        # 0.85 - 0.05*(35-28)/7 = 0.80
        assert Hormigon(fc=35).beta1 == pytest.approx(0.80, abs=1e-9)

    def test_beta1_fc40(self):
        # 0.85 - 0.05*(40-28)/7 = 0.7643
        assert Hormigon(fc=40).beta1 == pytest.approx(0.7643, abs=0.0001)

    def test_beta1_minimo_065(self):
        # f'c muy alto → clamped a 0.65
        assert Hormigon(fc=70).beta1 == pytest.approx(0.65)
        assert Hormigon(fc=100).beta1 == pytest.approx(0.65)

    def test_fsc(self):
        assert Hormigon(fc=30).fsc == pytest.approx(25.5)
        assert Hormigon(fc=25).fsc == pytest.approx(21.25)

    def test_Ec_formula(self):
        h = Hormigon(fc=30, wc=2400)
        expected = 2400 ** 1.5 * 0.043 * math.sqrt(30)
        assert h.Ec == pytest.approx(expected, rel=1e-9)

    def test_epsilon_u(self):
        assert Hormigon(fc=30).epsilon_u == 0.003

    def test_fc_invalido(self):
        with pytest.raises(ValueError):
            Hormigon(fc=0)
        with pytest.raises(ValueError):
            Hormigon(fc=-5)


class TestAcero:
    def test_epsilon_y_adn420(self):
        a = Acero(fy=420)
        assert a.epsilon_y == pytest.approx(420 / 200_000, rel=1e-9)

    def test_Es_constante_clase(self):
        assert Acero.Es == 200_000.0

    def test_Es_no_cambia_entre_instancias(self):
        a1 = Acero(fy=420)
        a2 = Acero(fy=500)
        assert a1.Es == a2.Es == 200_000.0

    def test_fy_invalido(self):
        with pytest.raises(ValueError):
            Acero(fy=0)
        with pytest.raises(ValueError):
            Acero(fy=-420)


class TestBarras:
    def test_diametros_presentes(self):
        for phi in [6, 8, 10, 12, 16, 20, 25, 32]:
            assert phi in BARRAS

    def test_area_phi16(self):
        # π*(16mm)²/4 = 201.06 mm² = 2.0106 cm²
        assert BARRAS[16] == pytest.approx(2.011, abs=0.001)

    def test_area_phi25(self):
        # π*(25mm)²/4 = 490.87 mm² = 4.9087 cm²
        assert BARRAS[25] == pytest.approx(4.909, abs=0.001)

    def test_diametros_ordenados(self):
        assert DIAMETROS == sorted(DIAMETROS)
