"""
Tests para graficos/modelo_3d.py.
Verifica que la figura se genera sin errores y contiene las trazas esperadas.
"""
import pytest

from hormigon.materiales import Acero, Hormigon
from hormigon.modelo import (
    ColumnaEsquema, Grilla, PanelLosa, PlantaEstructural, VigaEsquema,
)
from hormigon.propagacion import propagar
from hormigon.secciones import SeccionRectangular
from graficos.modelo_3d import visualizar_planta_3d

H25  = Hormigon(fc=25)
A420 = Acero(fy=420)
SEC  = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.06, hormigon=H25, acero=A420)
SEC_COL = SeccionRectangular(b=0.30, h=0.30, recubrimiento=0.06, hormigon=H25, acero=A420)


@pytest.fixture
def planta_simple():
    grilla = Grilla(ejes_x=[0.0, 5.0], ejes_y=[0.0, 4.5])
    p = PlantaEstructural(grilla=grilla, hormigon=H25, acero=A420)
    p.agregar_losa(PanelLosa('L0', i=0, j=0, h=0.14, tipo='2dir', wD=1.5, wL=2.0))
    p.agregar_viga(VigaEsquema('Vx0', dir='x', idx=0, desde=0, hasta=1, seccion=SEC))
    p.agregar_viga(VigaEsquema('Vx1', dir='x', idx=1, desde=0, hasta=1, seccion=SEC))
    p.agregar_viga(VigaEsquema('Vy0', dir='y', idx=0, desde=0, hasta=1, seccion=SEC))
    p.agregar_viga(VigaEsquema('Vy1', dir='y', idx=1, desde=0, hasta=1, seccion=SEC))
    for iy in range(2):
        for ix in range(2):
            p.agregar_columna(ColumnaEsquema(
                f'C{iy*2+ix}', ix=ix, iy=iy, seccion=SEC_COL, h_entrepiso=3.0,
            ))
    return p


def test_genera_figura(planta_simple):
    import plotly.graph_objects as go
    fig = visualizar_planta_3d(planta_simple)
    assert isinstance(fig, go.Figure)


def test_traces_no_vacio(planta_simple):
    fig = visualizar_planta_3d(planta_simple)
    assert len(fig.data) > 0


def test_legend_grupos(planta_simple):
    """Deben aparecer los grupos Columnas, Vigas y Losas en la leyenda."""
    fig = visualizar_planta_3d(planta_simple)
    names = {t.name for t in fig.data if getattr(t, 'showlegend', False)}
    assert 'Columnas' in names
    assert 'Vigas'    in names
    assert 'Losas'    in names


def test_con_propagacion(planta_simple):
    """Con propagación no debe haber errores y debe haber más traces (etiquetas)."""
    prop = propagar(planta_simple)
    fig_sin = visualizar_planta_3d(planta_simple, propagacion=None)
    fig_con = visualizar_planta_3d(planta_simple, propagacion=prop)
    assert len(fig_con.data) > len(fig_sin.data)


def test_sin_ids(planta_simple):
    """mostrar_ids=False reduce el número de traces."""
    fig_con_id = visualizar_planta_3d(planta_simple, mostrar_ids=True)
    fig_sin_id = visualizar_planta_3d(planta_simple, mostrar_ids=False)
    assert len(fig_sin_id.data) < len(fig_con_id.data)


def test_titulo(planta_simple):
    fig = visualizar_planta_3d(planta_simple, titulo='Test titulo')
    assert fig.layout.title.text == 'Test titulo'
