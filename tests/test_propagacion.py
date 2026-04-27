"""
Tests para hormigon/modelo.py y hormigon/propagacion.py.
Todos los valores esperados son calculables a mano.
"""
import pytest

from hormigon.cargas import wu_DL
from hormigon.materiales import Acero, Hormigon
from hormigon.modelo import (
    ColumnaEsquema,
    Grilla,
    PanelLosa,
    PlantaEstructural,
    VigaEsquema,
)
from hormigon.propagacion import (
    calcular_carga_columna,
    calcular_carga_viga,
    propagar,
)
from hormigon.secciones import SeccionRectangular

# ---------------------------------------------------------------------------
# Materiales y secciones comunes
# ---------------------------------------------------------------------------

H25  = Hormigon(fc=25)
A420 = Acero(fy=420)
SEC_VIGA = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.06,
                               hormigon=H25, acero=A420)
SEC_COL  = SeccionRectangular(b=0.30, h=0.30, recubrimiento=0.06,
                               hormigon=H25, acero=A420)
GAMMA = 25.0


# ---------------------------------------------------------------------------
# Planta 1×1 vano — losa 1dir
# ---------------------------------------------------------------------------

@pytest.fixture
def planta_1x1_1dir():
    """
    Planta 1 vano en x (4.0m) × 1 vano en y (5.0m).
    Losa 1dir que vana en x → cargas van a Vy0, Vy1.
    """
    grilla = Grilla(ejes_x=[0.0, 4.0], ejes_y=[0.0, 5.0])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420, gamma_conc=GAMMA)
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='1dir',
                              dir_1dir='x', wD=2.0, wL=3.0))
    for idx in range(2):
        p.agregar_viga(VigaEsquema(f'Vx{idx}', dir='x', idx=idx,
                                    desde=0, hasta=1, seccion=SEC_VIGA))
        p.agregar_viga(VigaEsquema(f'Vy{idx}', dir='y', idx=idx,
                                    desde=0, hasta=1, seccion=SEC_VIGA))
    for iy in range(2):
        for ix in range(2):
            p.agregar_columna(ColumnaEsquema(f'C{iy*2+ix}', ix=ix, iy=iy,
                                              seccion=SEC_COL, h_entrepiso=3.0))
    return p


# ── Cargas sobre vigas ────────────────────────────────────────────────────────

def test_1dir_Vy_recibe_carga_losa(planta_1x1_1dir):
    """Vy0 y Vy1 reciben w_losa * lx/2 de la losa 1dir."""
    wD_losa = 0.14 * GAMMA + 2.0        # 5.5 kN/m²
    q_wD = wD_losa * 4.0 / 2            # 11.0 kN/m
    q_wL = 3.0 * 4.0 / 2               # 6.0 kN/m
    pp   = 0.25 * 0.50 * GAMMA         # 3.125 kN/m

    for vid in ('Vy0', 'Vy1'):
        cv = calcular_carga_viga(vid, planta_1x1_1dir)
        assert cv.wD == pytest.approx(pp + q_wD, rel=1e-3)
        assert cv.wL == pytest.approx(q_wL, rel=1e-3)
        assert cv.wu == pytest.approx(wu_DL(cv.wD, cv.wL), rel=1e-6)


def test_1dir_Vx_solo_autopeso(planta_1x1_1dir):
    """Vx0 y Vx1 no reciben carga de la losa (1dir vana en x → carga a Vy)."""
    pp = 0.25 * 0.50 * GAMMA
    for vid in ('Vx0', 'Vx1'):
        cv = calcular_carga_viga(vid, planta_1x1_1dir)
        assert cv.wD == pytest.approx(pp, rel=1e-3)
        assert cv.wL == pytest.approx(0.0, abs=1e-9)


def test_viga_1tramo_n_tramos_spans(planta_1x1_1dir):
    cv = calcular_carga_viga('Vy0', planta_1x1_1dir)
    assert cv.n_tramos == 1
    assert len(cv.spans) == 1
    assert cv.spans[0] == pytest.approx(5.0)


# ── Simetría y valor exacto de columna ───────────────────────────────────────

def test_1dir_columnas_simetria(planta_1x1_1dir):
    """Las 4 columnas deben tener exactamente el mismo Pu."""
    prop = propagar(planta_1x1_1dir)
    vals = [cc.Pu for cc in prop.cargas_columnas.values()]
    assert max(vals) == pytest.approx(min(vals), rel=1e-6)


def test_1dir_columna_Pu_exacto(planta_1x1_1dir):
    """
    Pu de C0 calculado a mano:
      wD_Vx = 3.125,     wL_Vx = 0
      wD_Vy = 14.125,    wL_Vy = 6.0
      R_Vx = wD_Vx * 4.0/2 = 6.25 (D)
      R_Vy = wD_Vy * 5.0/2 = 35.3125 (D),  wL_Vy * 5.0/2 = 15.0 (L)
      pp_col = 0.30*0.30*25*3.0 = 6.75 (D)
      Pu = wu_DL(6.75 + 6.25 + 35.3125, 15.0)
    """
    wD_Vx = 0.25 * 0.50 * GAMMA
    wD_Vy = wD_Vx + (0.14 * GAMMA + 2.0) * 4.0 / 2
    wL_Vy = 3.0 * 4.0 / 2
    pp_col = 0.30 * 0.30 * GAMMA * 3.0
    D_total = pp_col + wD_Vx * 4.0 / 2 + wD_Vy * 5.0 / 2
    L_total = wL_Vy * 5.0 / 2
    Pu_esp = wu_DL(D_total, L_total)

    cc = calcular_carga_columna('C0', planta_1x1_1dir)
    assert cc.Pu == pytest.approx(Pu_esp, rel=1e-4)


# ---------------------------------------------------------------------------
# Planta 1×1 vano — losa 2dir (45°)
# ---------------------------------------------------------------------------

@pytest.fixture
def planta_1x1_2dir():
    """Planta 1×1, losa 2dir 4.0m×5.0m."""
    grilla = Grilla(ejes_x=[0.0, 4.0], ejes_y=[0.0, 5.0])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420, gamma_conc=GAMMA)
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='2dir', wD=2.0, wL=3.0))
    for idx in range(2):
        p.agregar_viga(VigaEsquema(f'Vx{idx}', dir='x', idx=idx,
                                    desde=0, hasta=1, seccion=SEC_VIGA))
        p.agregar_viga(VigaEsquema(f'Vy{idx}', dir='y', idx=idx,
                                    desde=0, hasta=1, seccion=SEC_VIGA))
    for iy in range(2):
        for ix in range(2):
            p.agregar_columna(ColumnaEsquema(f'C{iy*2+ix}', ix=ix, iy=iy,
                                              seccion=SEC_COL, h_entrepiso=3.0))
    return p


def test_2dir_Vy_carga_triangular(planta_1x1_2dir):
    """
    Panel 4.0×5.0: lx=4.0 < ly=5.0 → vigas en y (dir corta) reciben carga
    triangular: q = w*la/3.
    """
    wD_losa = 0.14 * GAMMA + 2.0
    la, pp = 4.0, 0.25 * 0.50 * GAMMA
    q_tri_wD = wD_losa * la / 3
    q_tri_wL = 3.0 * la / 3

    for vid in ('Vy0', 'Vy1'):
        cv = calcular_carga_viga(vid, planta_1x1_2dir)
        assert cv.wD == pytest.approx(pp + q_tri_wD, rel=1e-3)
        assert cv.wL == pytest.approx(q_tri_wL, rel=1e-3)


def test_2dir_Vx_carga_trapezoidal(planta_1x1_2dir):
    """
    Las vigas en x (dir larga) reciben carga trapezoidal: q = w*la*(3-m²)/6.
    la=4.0, lb=5.0, m=0.8.
    """
    wD_losa = 0.14 * GAMMA + 2.0
    la, lb = 4.0, 5.0
    m = la / lb
    pp = 0.25 * 0.50 * GAMMA
    q_trap_wD = wD_losa * la * (3 - m**2) / 6
    q_trap_wL = 3.0 * la * (3 - m**2) / 6

    for vid in ('Vx0', 'Vx1'):
        cv = calcular_carga_viga(vid, planta_1x1_2dir)
        assert cv.wD == pytest.approx(pp + q_trap_wD, rel=1e-3)
        assert cv.wL == pytest.approx(q_trap_wL, rel=1e-3)


def test_2dir_losa_cuadrada_triangular_igual_trapezoidal():
    """Para m=1 (cuadrada), q_tri = q_trap = w*la/3."""
    grilla = Grilla(ejes_x=[0.0, 5.0], ejes_y=[0.0, 5.0])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420)
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='2dir', wD=2.0, wL=3.0))
    for idx in range(2):
        p.agregar_viga(VigaEsquema(f'Vx{idx}', dir='x', idx=idx,
                                    desde=0, hasta=1, seccion=SEC_VIGA))
        p.agregar_viga(VigaEsquema(f'Vy{idx}', dir='y', idx=idx,
                                    desde=0, hasta=1, seccion=SEC_VIGA))
    cv_x = calcular_carga_viga('Vx0', p)
    cv_y = calcular_carga_viga('Vy0', p)
    # La contribución de la losa (sin autopeso) debe ser igual en x e y
    pp = 0.25 * 0.50 * 25.0
    assert (cv_x.wD - pp) == pytest.approx((cv_y.wD - pp), rel=1e-6)
    assert cv_x.wL == pytest.approx(cv_y.wL, rel=1e-6)


def test_2dir_columnas_simetria(planta_1x1_2dir):
    """Las 4 columnas deben tener el mismo Pu (planta simétrica)."""
    prop = propagar(planta_1x1_2dir)
    vals = [cc.Pu for cc in prop.cargas_columnas.values()]
    assert max(vals) == pytest.approx(min(vals), rel=1e-6)


# ---------------------------------------------------------------------------
# Vigas multitramo: cada tramo recibe solo su panel adyacente
# ---------------------------------------------------------------------------

def test_multitramo_no_dobla_carga():
    """
    Viga continua de 2 tramos con 2 paneles iguales adyacentes.
    El wu promedio debe ser igual al de una viga de 1 tramo con 1 solo panel.
    """
    grilla = Grilla(ejes_x=[0.0, 5.0, 10.0], ejes_y=[0.0, 4.5])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420, gamma_conc=GAMMA)
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='2dir', wD=1.5, wL=2.0))
    p.agregar_losa(PanelLosa('L1', i=1, j=0, h=0.14, tipo='2dir', wD=1.5, wL=2.0))
    p.agregar_viga(VigaEsquema('Vx_multi', dir='x', idx=0, desde=0, hasta=2, seccion=SEC_VIGA))
    p.agregar_viga(VigaEsquema('Vx_ref',   dir='x', idx=0, desde=0, hasta=1, seccion=SEC_VIGA))

    cv_multi = calcular_carga_viga('Vx_multi', p)
    cv_ref   = calcular_carga_viga('Vx_ref',   p)
    assert cv_multi.wu == pytest.approx(cv_ref.wu, rel=1e-4)


def test_multitramo_paneles_distintos():
    """Viga de 2 tramos con cargas distintas en cada panel → wu promedio ponderado."""
    grilla = Grilla(ejes_x=[0.0, 5.0, 10.0], ejes_y=[0.0, 4.5])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420, gamma_conc=GAMMA)
    # L0: wL=2, L1: wL=4
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='2dir', wD=1.5, wL=2.0))
    p.agregar_losa(PanelLosa('L1', i=1, j=0, h=0.14, tipo='2dir', wD=1.5, wL=4.0))
    p.agregar_viga(VigaEsquema('Vx', dir='x', idx=0, desde=0, hasta=2, seccion=SEC_VIGA))

    cv = calcular_carga_viga('Vx', p)
    # wu_tramo0 (L0) < wu_tramo1 (L1) → wu promedio en el medio
    assert cv.wu_por_tramo[0] < cv.wu_por_tramo[1]
    assert cv.wu_por_tramo[0] < cv.wu < cv.wu_por_tramo[1]


# ---------------------------------------------------------------------------
# Grilla: propiedades geométricas
# ---------------------------------------------------------------------------

def test_grilla_lx_ly():
    g = Grilla(ejes_x=[0.0, 4.0, 9.0], ejes_y=[0.0, 3.0, 7.5])
    assert g.lx(0) == pytest.approx(4.0)
    assert g.lx(1) == pytest.approx(5.0)
    assert g.ly(0) == pytest.approx(3.0)
    assert g.ly(1) == pytest.approx(4.5)
    assert g.nx == 2
    assert g.ny == 2


def test_planta_agregar_fluent():
    """El API fluent (encadenado) funciona correctamente."""
    grilla = Grilla(ejes_x=[0.0, 5.0], ejes_y=[0.0, 5.0])
    sec = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.06, hormigon=H25, acero=A420)
    p = (PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420)
         .agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='1dir', dir_1dir='x', wD=2.0, wL=2.0))
         .agregar_viga(VigaEsquema('V0', dir='x', idx=0, desde=0, hasta=1, seccion=sec)))
    assert 'L0' in p.losas
    assert 'V0' in p.vigas
