"""
Tests para elementos/ — wrappers de elementos estructurales tipificados.
Verifican cálculo correcto y generación de gráficos sin error.
"""
import pytest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular, SeccionT

from elementos.viga import VigaSimple, VigaVoladizo, VigaContinua
from elementos.columna import Columna
from elementos.losa_1dir import Losa1Dir

H25  = Hormigon(fc=25)
H30  = Hormigon(fc=30)
A420 = Acero(fy=420)

SEC_30x60 = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                                hormigon=H30, acero=A420)
SEC_40x40 = SeccionRectangular(b=0.40, h=0.40, recubrimiento=0.05,
                                hormigon=H30, acero=A420)


@pytest.fixture(autouse=True)
def cerrar_figuras():
    yield
    plt.close('all')


# ── VigaSimple ────────────────────────────────────────────────────────────────

def test_viga_simple_Mu():
    r = VigaSimple(SEC_30x60, L=6.0, wD=10.0, wL=8.0).calcular()
    wu_esperado = max(1.4 * 10, 1.2 * 10 + 1.6 * 8)
    Mu_esperado = wu_esperado * 6.0**2 / 8.0
    assert abs(r.Mu - Mu_esperado) < 0.01


def test_viga_simple_wu_directo():
    r = VigaSimple(SEC_30x60, L=5.0, wU=30.0).calcular()
    assert abs(r.wu - 30.0) < 1e-9
    assert abs(r.Mu - 30.0 * 25.0 / 8.0) < 0.01


def test_viga_simple_verifica():
    r = VigaSimple(SEC_30x60, L=5.0, wD=8.0, wL=6.0).calcular()
    assert r.resultado_flex.verifica


def test_viga_simple_arrays_longitud():
    r = VigaSimple(SEC_30x60, L=4.0, wU=20.0).calcular()
    assert len(r.x) == len(r.M_x) == len(r.V_x)
    assert r.x[0] == pytest.approx(0.0)
    assert r.x[-1] == pytest.approx(4.0)


def test_viga_simple_M_simetrico():
    r = VigaSimple(SEC_30x60, L=6.0, wU=30.0).calcular()
    # M es simétrico respecto al centro para carga uniforme
    import numpy as np
    assert abs(r.M_x[0]) < 1e-9
    assert abs(r.M_x[-1]) < 1e-9
    idx_mid = len(r.x) // 2
    Mu_esperado = 30.0 * 6.0**2 / 8.0
    assert abs(r.M_x[idx_mid] - Mu_esperado) < 0.5


def test_viga_simple_V_antisimetrico():
    r = VigaSimple(SEC_30x60, L=6.0, wU=30.0).calcular()
    assert r.V_x[0] > 0        # cortante positivo en apoyo izquierdo
    assert r.V_x[-1] < 0       # cortante negativo en apoyo derecho


def test_viga_simple_graficar():
    r = VigaSimple(SEC_30x60, L=6.0, wD=10.0, wL=8.0).calcular()
    fig = r.graficar()
    assert fig is not None


# ── VigaVoladizo ──────────────────────────────────────────────────────────────

def test_voladizo_Mu_uniforme():
    r = VigaVoladizo(SEC_30x60, L=3.0, wU=20.0).calcular()
    assert abs(r.Mu - 20.0 * 9.0 / 2.0) < 0.01


def test_voladizo_Mu_concentrada():
    r = VigaVoladizo(SEC_30x60, L=2.0, PU=50.0).calcular()
    assert abs(r.Mu - 50.0 * 2.0) < 0.01


def test_voladizo_Mu_combinada():
    r = VigaVoladizo(SEC_30x60, L=2.0, wU=10.0, PU=20.0).calcular()
    Mu_esp = 10.0 * 4.0 / 2.0 + 20.0 * 2.0
    assert abs(r.Mu - Mu_esp) < 0.01


def test_voladizo_verifica():
    r = VigaVoladizo(SEC_30x60, L=2.5, wD=8.0, wL=5.0).calcular()
    assert r.resultado_flex.verifica


def test_voladizo_M_negativo_en_empotramiento():
    r = VigaVoladizo(SEC_30x60, L=3.0, wU=20.0).calcular()
    # Momento en el empotramiento (x=0) debe ser el más negativo
    assert r.M_x[0] < 0
    assert abs(r.M_x[-1]) < 0.1   # libre: M ≈ 0


def test_voladizo_graficar():
    r = VigaVoladizo(SEC_30x60, L=2.5, wU=25.0).calcular()
    fig = r.graficar()
    assert fig is not None


# ── VigaContinua ──────────────────────────────────────────────────────────────

def test_continua_2_tramos():
    r = VigaContinua(SEC_30x60, ln=5.0, wD=10.0, wL=8.0, n_tramos=2).calcular()
    assert len(r.secciones) >= 3      # pos_ext, neg_ext, neg_1er_int


def test_continua_3_tramos():
    r = VigaContinua(SEC_30x60, ln=5.0, wD=10.0, wL=8.0, n_tramos=3).calcular()
    assert len(r.secciones) >= 4      # pos_ext, pos_int, neg_ext, neg_1er_int


def test_continua_4_tramos():
    r = VigaContinua(SEC_30x60, ln=5.0, wD=10.0, wL=8.0, n_tramos=4).calcular()
    # pos_ext, pos_int, neg_ext, neg_1er_int, neg_int
    assert len(r.secciones) == 5


def test_continua_Vu_1er_int_mayor():
    r = VigaContinua(SEC_30x60, ln=6.0, wD=8.0, wL=6.0).calcular()
    assert r.Vu_1er_int > r.Vu_ext


def test_continua_Vu_relacion():
    r = VigaContinua(SEC_30x60, ln=6.0, wD=10.0, wL=8.0).calcular()
    # 1er apoyo interior ≈ 1.15 × apoyo exterior
    assert abs(r.Vu_1er_int / r.Vu_ext - 1.15) < 1e-9


def test_continua_n_tramos_minimo():
    with pytest.raises(ValueError):
        VigaContinua(SEC_30x60, ln=5.0, wD=10.0, wL=8.0, n_tramos=1)


def test_continua_extremo_libre_neg_menor():
    r_libre   = VigaContinua(SEC_30x60, ln=5.0, wD=10.0, wL=8.0,
                              n_tramos=3, extremo='libre').calcular()
    r_empotr  = VigaContinua(SEC_30x60, ln=5.0, wD=10.0, wL=8.0,
                              n_tramos=3, extremo='viga').calcular()
    # Momento negativo en apoyo exterior es mayor con extremo empotrado
    Mneg_libre  = next(s.Mu for s in r_libre.secciones  if 'ext' in s.nombre and 'M-' in s.nombre)
    Mneg_empotr = next(s.Mu for s in r_empotr.secciones if 'ext' in s.nombre and 'M-' in s.nombre)
    assert Mneg_empotr > Mneg_libre


def test_continua_graficar():
    r = VigaContinua(SEC_30x60, ln=5.0, wD=8.0, wL=6.0).calcular()
    fig = r.graficar()
    assert fig is not None


# ── Columna ───────────────────────────────────────────────────────────────────

def test_columna_disena_Ast():
    c = Columna(SEC_40x40, Pu=800.0, Mu=100.0)
    r = c.calcular()
    from hormigon.columnas import RHO_MIN, RHO_MAX
    assert RHO_MIN * SEC_40x40.Ag <= r.Ast / 1e4 <= RHO_MAX * SEC_40x40.Ag + 1e-6
    assert r.verifica


def test_columna_verifica_con_Ast():
    # Generar diagrama y tomar un punto interno como demanda
    from hormigon.columnas import diagrama_interaccion
    diag = diagrama_interaccion(SEC_40x40, Ast=20.0)
    Pu = diag.phi_Pn_bal * 0.5
    Mu = diag.phi_Mn_bal * 0.5
    c = Columna(SEC_40x40, Pu=Pu, Mu=Mu, Ast=20.0)
    r = c.calcular()
    assert r.verifica


def test_columna_falla_cuando_insuficiente():
    # Sección muy pequeña, demanda enorme
    sec_chica = SeccionRectangular(b=0.20, h=0.20, recubrimiento=0.05,
                                   hormigon=H30, acero=A420)
    c = Columna(sec_chica, Pu=5000.0, Mu=500.0)
    with pytest.raises(ValueError):
        c.calcular()


def test_columna_graficar():
    r = Columna(SEC_40x40, Pu=600.0, Mu=80.0).calcular()
    fig = r.graficar()
    assert fig is not None


def test_columna_adoptar():
    r = Columna(SEC_40x40, Pu=600.0, Mu=80.0).calcular()
    r.adoptar(phi=20, n_barras=8)
    assert r.Ast_real is not None
    assert r.n_barras == 8


# ── Losa1Dir ──────────────────────────────────────────────────────────────────

def test_losa_1dir_calcular():
    losa = Losa1Dir(h=0.14, recubrimiento=0.025, hormigon=H25, acero=A420,
                    wD=3.5, wL=2.0, ln=4.0, n_tramos=3)
    r = losa.calcular()
    assert r.h == pytest.approx(0.14)
    assert r.ln == pytest.approx(4.0)
    assert len(r.secciones) >= 3


def test_losa_1dir_wu_correcto():
    losa = Losa1Dir(h=0.12, recubrimiento=0.020, hormigon=H25, acero=A420,
                    wD=4.0, wL=3.0, ln=3.5, n_tramos=2)
    r = losa.calcular()
    from hormigon.cargas import wu_DL
    assert abs(r.wu - wu_DL(4.0, 3.0)) < 1e-9


def test_losa_1dir_tramo_simple():
    losa = Losa1Dir(h=0.12, recubrimiento=0.020, hormigon=H25, acero=A420,
                    wD=3.0, wL=2.0, ln=3.0, n_tramos=1)
    r = losa.calcular()
    assert len(r.secciones) == 1
    from hormigon.cargas import wu_DL
    wu = wu_DL(3.0, 2.0)
    Mu_esp = wu * 3.0**2 / 8.0
    assert abs(r.secciones[0].Mu - Mu_esp) < 0.01


def test_losa_1dir_todas_verifican():
    losa = Losa1Dir(h=0.18, recubrimiento=0.025, hormigon=H30, acero=A420,
                    wD=5.0, wL=4.0, ln=5.0, n_tramos=3)
    r = losa.calcular()
    for s in r.secciones:
        if s.Mu > 0:
            assert s.verifica, f"No verifica: {s.nombre}"


def test_losa_1dir_n_tramos_invalido():
    losa = Losa1Dir(h=0.12, recubrimiento=0.020, hormigon=H25, acero=A420,
                    wD=3.0, wL=2.0, ln=3.0, n_tramos=0)
    with pytest.raises(ValueError):
        losa.calcular()
