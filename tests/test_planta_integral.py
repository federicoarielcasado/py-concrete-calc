"""
Tests de integración para elementos/planta.py.
Verifica que dimensionar_viga, dimensionar_columna y dimensionar_losa
funcionan de extremo a extremo sobre una planta estructural real.
"""
import pytest

from hormigon.materiales import Acero, Hormigon
from hormigon.modelo import (
    ColumnaEsquema,
    Grilla,
    PanelLosa,
    PlantaEstructural,
    VigaEsquema,
)
from hormigon.secciones import SeccionRectangular
from elementos.planta import (
    dimensionar_columna,
    dimensionar_losa,
    dimensionar_planta,
    dimensionar_viga,
)
from elementos.viga import ResultadoViga, ResultadoVigaContinua
from elementos.columna import ResultadoColumnaFlexoCompresion
from hormigon.losas import ResultadoLosa2Dir

H25  = Hormigon(fc=25)
A420 = Acero(fy=420)
SEC_VIGA = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.06,
                               hormigon=H25, acero=A420)
SEC_COL  = SeccionRectangular(b=0.30, h=0.30, recubrimiento=0.06,
                               hormigon=H25, acero=A420)


# ---------------------------------------------------------------------------
# Fixture: planta 2×1 con vigas y columnas (igual que ej_planta_simple.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def planta_2x1():
    """2 vanos en x (5.0+5.0m) × 1 vano en y (4.5m), losas 2dir."""
    grilla = Grilla(ejes_x=[0.0, 5.0, 10.0], ejes_y=[0.0, 4.5])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420, gamma_conc=25.0)

    for i in range(grilla.nx):
        p.agregar_losa(PanelLosa(
            id=f'L{i}', i=i, j=0, h=0.14, tipo='2dir',
            wD=1.5, wL=2.0,
            tipo_a='ext_empotrado', tipo_b='ext_empotrado',
        ))

    for j_eje in range(len(grilla.ejes_y)):
        p.agregar_viga(VigaEsquema(
            id=f'Vx{j_eje}', dir='x', idx=j_eje,
            desde=0, hasta=grilla.nx,
            seccion=SEC_VIGA, extremo='columna',
        ))

    for i_eje in range(len(grilla.ejes_x)):
        p.agregar_viga(VigaEsquema(
            id=f'Vy{i_eje}', dir='y', idx=i_eje,
            desde=0, hasta=grilla.ny,
            seccion=SEC_VIGA, extremo='columna',
        ))

    k = 0
    for iy in range(len(grilla.ejes_y)):
        for ix in range(len(grilla.ejes_x)):
            p.agregar_columna(ColumnaEsquema(
                id=f'C{k}', ix=ix, iy=iy,
                seccion=SEC_COL, h_entrepiso=3.0,
            ))
            k += 1

    return p


# ---------------------------------------------------------------------------
# Fixture: planta 1×1 simple para tests de vigas simples
# ---------------------------------------------------------------------------

@pytest.fixture
def planta_1x1():
    grilla = Grilla(ejes_x=[0.0, 4.0], ejes_y=[0.0, 5.0])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420, gamma_conc=25.0)
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='1dir',
                              dir_1dir='y', wD=2.0, wL=3.0))
    p.agregar_viga(VigaEsquema('Vy0', dir='y', idx=0,
                                desde=0, hasta=1, seccion=SEC_VIGA))
    p.agregar_columna(ColumnaEsquema('C0', ix=0, iy=0,
                                      seccion=SEC_COL, h_entrepiso=3.0))
    p.agregar_columna(ColumnaEsquema('C1', ix=0, iy=1,
                                      seccion=SEC_COL, h_entrepiso=3.0))
    return p


# ---------------------------------------------------------------------------
# dimensionar_viga
# ---------------------------------------------------------------------------

def test_dimensionar_viga_simple_tipo(planta_1x1):
    r = dimensionar_viga('Vy0', planta_1x1)
    assert isinstance(r, ResultadoViga)


def test_dimensionar_viga_continua_tipo(planta_2x1):
    r = dimensionar_viga('Vx0', planta_2x1)
    assert isinstance(r, ResultadoVigaContinua)


def test_dimensionar_viga_continua_n_tramos(planta_2x1):
    r = dimensionar_viga('Vx0', planta_2x1)
    assert r.n_tramos == 2


def test_dimensionar_viga_acepta_carga_precalculada(planta_2x1):
    """Pasar la carga precalculada da el mismo resultado que calcularlo internamente."""
    from hormigon.propagacion import calcular_carga_viga
    carga = calcular_carga_viga('Vx0', planta_2x1)
    r1 = dimensionar_viga('Vx0', planta_2x1)
    r2 = dimensionar_viga('Vx0', planta_2x1, carga=carga)
    assert r1.wu == pytest.approx(r2.wu, rel=1e-9)


# ---------------------------------------------------------------------------
# dimensionar_columna
# ---------------------------------------------------------------------------

def test_dimensionar_columna_tipo(planta_2x1):
    r = dimensionar_columna('C0', planta_2x1)
    assert isinstance(r, ResultadoColumnaFlexoCompresion)


def test_dimensionar_columna_Pu_positivo(planta_2x1):
    r = dimensionar_columna('C0', planta_2x1)
    assert r.Pu > 0


def test_dimensionar_columna_verifica(planta_2x1):
    """Con la sección 30×30 las columnas de un entrepiso de carga normal deben verificar."""
    r = dimensionar_columna('C0', planta_2x1)
    assert r.verifica


def test_columnas_borde_menor_central(planta_2x1):
    """Columnas interiores reciben más carga que las de esquina."""
    from hormigon.propagacion import calcular_carga_columna
    Pu_esquina  = calcular_carga_columna('C0', planta_2x1).Pu
    Pu_interior = calcular_carga_columna('C1', planta_2x1).Pu  # ix=1, iy=0 (borde inferior)
    # C1 está en el eje x central y recibe vigas de 2 paneles → mayor Pu
    assert Pu_interior > Pu_esquina


# ---------------------------------------------------------------------------
# dimensionar_losa
# ---------------------------------------------------------------------------

def test_dimensionar_losa_1dir(planta_1x1):
    from hormigon.losas import ResultadoLosa1Dir
    r = dimensionar_losa('L0', planta_1x1)
    assert isinstance(r, ResultadoLosa1Dir)


def test_dimensionar_losa_2dir_tipo(planta_2x1):
    r = dimensionar_losa('L0', planta_2x1)
    assert isinstance(r, ResultadoLosa2Dir)


def test_dimensionar_losa_2dir_verifica(planta_2x1):
    r = dimensionar_losa('L0', planta_2x1)
    assert all(s.verifica for s in r.secciones)


# ---------------------------------------------------------------------------
# dimensionar_planta (integración completa)
# ---------------------------------------------------------------------------

def test_dimensionar_planta_estructura(planta_2x1):
    res = dimensionar_planta(planta_2x1)
    assert 'propagacion' in res
    assert 'vigas' in res
    assert 'columnas' in res
    assert 'losas' in res


def test_dimensionar_planta_cubre_todos_los_elementos(planta_2x1):
    res = dimensionar_planta(planta_2x1)
    assert set(res['vigas'].keys())   == set(planta_2x1.vigas.keys())
    assert set(res['columnas'].keys()) == set(planta_2x1.columnas.keys())
    assert set(res['losas'].keys())    == set(planta_2x1.losas.keys())


def test_dimensionar_planta_vigas_continuas(planta_2x1):
    res = dimensionar_planta(planta_2x1)
    assert isinstance(res['vigas']['Vx0'], ResultadoVigaContinua)
    assert isinstance(res['vigas']['Vx1'], ResultadoVigaContinua)
