import math
import pytest
from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import (
    SeccionRectangular,
    SeccionT,
    SeccionCircular,
    ancho_eficaz_T,
    ancho_eficaz_L,
)

H30 = Hormigon(fc=30)
ADN420 = Acero(fy=420)


class TestSeccionRectangular:
    def test_d(self):
        sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.03, hormigon=H30, acero=ADN420)
        assert sec.d == pytest.approx(0.57)

    def test_Ag(self):
        sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.03, hormigon=H30, acero=ADN420)
        assert sec.Ag == pytest.approx(0.18)

    def test_d_prima_default(self):
        sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.03, hormigon=H30, acero=ADN420)
        assert sec.d_prima == pytest.approx(0.03)

    def test_d_prima_custom(self):
        sec = SeccionRectangular(
            b=0.30, h=0.60, recubrimiento=0.03,
            hormigon=H30, acero=ADN420,
            recubrimiento_prima=0.04,
        )
        assert sec.d_prima == pytest.approx(0.04)

    def test_b_invalido(self):
        with pytest.raises(ValueError):
            SeccionRectangular(b=0, h=0.60, recubrimiento=0.03, hormigon=H30, acero=ADN420)

    def test_recubrimiento_invalido(self):
        with pytest.raises(ValueError):
            SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.60, hormigon=H30, acero=ADN420)


class TestSeccionT:
    def test_d(self):
        sec = SeccionT(bw=0.25, h=0.60, b_ala=1.20, h_ala=0.12,
                       recubrimiento=0.03, hormigon=H30, acero=ADN420)
        assert sec.d == pytest.approx(0.57)

    def test_Ag(self):
        # alma: 0.25*(0.60-0.12) + ala: 1.20*0.12 = 0.12 + 0.144 = 0.264
        sec = SeccionT(bw=0.25, h=0.60, b_ala=1.20, h_ala=0.12,
                       recubrimiento=0.03, hormigon=H30, acero=ADN420)
        assert sec.Ag == pytest.approx(0.264)

    def test_hw(self):
        sec = SeccionT(bw=0.25, h=0.60, b_ala=1.20, h_ala=0.12,
                       recubrimiento=0.03, hormigon=H30, acero=ADN420)
        assert sec.hw == pytest.approx(0.48)

    def test_b_ala_menor_bw_invalido(self):
        with pytest.raises(ValueError):
            SeccionT(bw=0.30, h=0.60, b_ala=0.20, h_ala=0.12,
                     recubrimiento=0.03, hormigon=H30, acero=ADN420)


class TestAnchoEficaz:
    def test_ancho_eficaz_T_controlado_por_ln(self):
        # vuelo = min(6/8=0.75, 8*0.20=1.60, (3.0-0.25)/2=1.375) = 0.75
        bef = ancho_eficaz_T(bw=0.25, h_ala=0.20, ln=6.0, dist_entre_vigas=3.0)
        assert bef == pytest.approx(0.25 + 2 * 0.75)

    def test_ancho_eficaz_T_controlado_por_hala(self):
        # vuelo = min(20/8=2.50, 8*0.10=0.80, (5.0-0.30)/2=2.35) = 0.80
        bef = ancho_eficaz_T(bw=0.30, h_ala=0.10, ln=20.0, dist_entre_vigas=5.0)
        assert bef == pytest.approx(0.30 + 2 * 0.80)

    def test_ancho_eficaz_T_controlado_por_distancia(self):
        # vuelo = min(30/8=3.75, 8*0.30=2.40, (3.0-0.25)/2=1.375) = 1.375
        bef = ancho_eficaz_T(bw=0.25, h_ala=0.30, ln=30.0, dist_entre_vigas=3.0)
        assert bef == pytest.approx(0.25 + 2 * 1.375)

    def test_ancho_eficaz_L(self):
        # vuelo = min(6/12=0.50, 6*0.12=0.72, 1.75/2=0.875) = 0.50
        bef = ancho_eficaz_L(bw=0.25, h_ala=0.12, ln=6.0, dist_libre_siguiente=1.75)
        assert bef == pytest.approx(0.75)


class TestSeccionCircular:
    def test_Ag(self):
        sec = SeccionCircular(D=0.40, recubrimiento=0.04, hormigon=H30, acero=ADN420)
        assert sec.Ag == pytest.approx(math.pi * 0.40 ** 2 / 4, rel=1e-9)

    def test_d(self):
        sec = SeccionCircular(D=0.40, recubrimiento=0.04, hormigon=H30, acero=ADN420)
        assert sec.d == pytest.approx(0.36)

    def test_Dc(self):
        sec = SeccionCircular(D=0.40, recubrimiento=0.04, hormigon=H30, acero=ADN420)
        assert sec.Dc == pytest.approx(0.32)

    def test_Ach(self):
        sec = SeccionCircular(D=0.40, recubrimiento=0.04, hormigon=H30, acero=ADN420)
        assert sec.Ach == pytest.approx(math.pi * 0.32 ** 2 / 4, rel=1e-9)

    def test_recubrimiento_invalido(self):
        with pytest.raises(ValueError):
            SeccionCircular(D=0.40, recubrimiento=0.25, hormigon=H30, acero=ADN420)
