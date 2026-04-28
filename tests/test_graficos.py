"""
Tests de humo para graficos/ — verifican que las figuras se generan sin error.
No comprueban el contenido visual, solo que el código no lanza excepciones.
"""
import pytest
import matplotlib
matplotlib.use('Agg')   # sin ventana, para CI y pytest
import matplotlib.pyplot as plt

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular, SeccionT, SeccionCircular
from hormigon.flexion import dimensionar_flexion, dimensionar_flexion_variantes
from hormigon.corte import calcular_corte, calcular_corte_variantes
from hormigon.columnas import diagrama_interaccion
from graficos import (
    graficar_seccion,
    graficar_interaccion_PM,
    graficar_variantes_flexion,
    graficar_variantes_corte,
    visualizar_elemento_3d,
    visualizar_viga_3d,
)
from elementos.viga import VigaSimple

H30  = Hormigon(fc=30)
A420 = Acero(fy=420)


@pytest.fixture(autouse=True)
def cerrar_figuras():
    yield
    plt.close('all')


# ── seccion_2d ────────────────────────────────────────────────────────────────

def test_seccion_rect_sin_resultado():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    fig = graficar_seccion(sec)
    assert fig is not None


def test_seccion_rect_con_flexion_calculada():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    r = dimensionar_flexion(sec, Mu=180)
    fig = graficar_seccion(sec, resultado_flex=r)
    assert fig is not None


def test_seccion_rect_con_flexion_adoptada():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    r = dimensionar_flexion(sec, Mu=180)
    r.adoptar(phi=20, n=4)
    fig = graficar_seccion(sec, resultado_flex=r)
    assert fig is not None


def test_seccion_rect_con_corte_adoptado():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    rc = calcular_corte(sec, Vu=120)
    rc.adoptar(phi=8, n_ramas=2, s=0.15)
    fig = graficar_seccion(sec, resultado_corte=rc)
    assert fig is not None


def test_seccion_rect_flex_y_corte():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    r  = dimensionar_flexion(sec, Mu=180)
    rc = calcular_corte(sec, Vu=120)
    fig = graficar_seccion(sec, resultado_flex=r, resultado_corte=rc)
    assert fig is not None


def test_seccion_T_con_flexion():
    sec = SeccionT(bw=0.25, h=0.55, b_ala=0.80, h_ala=0.12,
                   recubrimiento=0.05, hormigon=H30, acero=A420)
    r = dimensionar_flexion(sec, Mu=200)
    fig = graficar_seccion(sec, resultado_flex=r)
    assert fig is not None


def test_seccion_circular():
    sec = SeccionCircular(D=0.40, recubrimiento=0.05,
                          hormigon=H30, acero=A420)
    fig = graficar_seccion(sec)
    assert fig is not None


def test_seccion_sin_seccion_lanza_error():
    with pytest.raises(ValueError):
        graficar_seccion(None)


# ── Método graficar() en objetos resultado ────────────────────────────────────

def test_resultado_flexion_graficar():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    r = dimensionar_flexion(sec, Mu=150)
    fig = r.graficar(seccion=sec)
    assert fig is not None


def test_resultado_set_flexion_graficar():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    rset = dimensionar_flexion_variantes(sec, Mu=150)
    fig = rset.graficar()
    assert fig is not None


def test_resultado_corte_graficar():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    rc = calcular_corte(sec, Vu=100)
    fig = rc.graficar(seccion=sec)
    assert fig is not None


def test_resultado_set_corte_graficar():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    rset = calcular_corte_variantes(sec, Vu=100)
    fig = rset.graficar()
    assert fig is not None


# ── diagramas ─────────────────────────────────────────────────────────────────

def test_interaccion_PM_sin_demanda():
    sec  = SeccionRectangular(b=0.40, h=0.40, recubrimiento=0.05,
                               hormigon=H30, acero=A420)
    diag = diagrama_interaccion(sec, Ast=20.0)
    fig  = graficar_interaccion_PM(diag)
    assert fig is not None


def test_interaccion_PM_con_demanda_dentro():
    sec  = SeccionRectangular(b=0.40, h=0.40, recubrimiento=0.05,
                               hormigon=H30, acero=A420)
    diag = diagrama_interaccion(sec, Ast=20.0)
    fig  = graficar_interaccion_PM(diag, Pu=500, Mu=80)
    assert fig is not None


def test_interaccion_PM_con_demanda_fuera():
    sec  = SeccionRectangular(b=0.40, h=0.40, recubrimiento=0.05,
                               hormigon=H30, acero=A420)
    diag = diagrama_interaccion(sec, Ast=20.0)
    fig  = graficar_interaccion_PM(diag, Pu=200, Mu=500)
    assert fig is not None


def test_interaccion_PM_metodo_graficar():
    sec  = SeccionRectangular(b=0.40, h=0.40, recubrimiento=0.05,
                               hormigon=H30, acero=A420)
    diag = diagrama_interaccion(sec, Ast=20.0)
    fig  = diag.graficar(Pu=600, Mu=100)
    assert fig is not None


def test_variantes_flexion_graf():
    sec  = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                               hormigon=H30, acero=A420)
    rset = dimensionar_flexion_variantes(sec, Mu=180)
    fig  = graficar_variantes_flexion(rset)
    assert fig is not None


def test_variantes_corte_graf():
    sec  = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                               hormigon=H30, acero=A420)
    rset = calcular_corte_variantes(sec, Vu=120)
    fig  = graficar_variantes_corte(rset)
    assert fig is not None


# ── elemento_3d ───────────────────────────────────────────────────────────────

def test_visualizar_elemento_3d_basico():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    fig = visualizar_elemento_3d(sec, L=5.0, n_inf=3, phi_inf_mm=16)
    assert fig is not None
    assert len(fig.data) >= 3   # caras + aristas + barras + estribos


def test_visualizar_elemento_3d_con_barras_sup():
    sec = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    fig = visualizar_elemento_3d(sec, L=4.0,
                                  n_inf=4, phi_inf_mm=20,
                                  n_sup=2, phi_sup_mm=12)
    assert fig is not None


def test_visualizar_viga_3d_desde_resultado():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    r   = VigaSimple(sec, L=6.0, wD=10.0, wL=8.0).calcular()
    r.resultado_flex.adoptar(phi=20, n=3)
    fig = visualizar_viga_3d(r)
    assert fig is not None


def test_graficar_3d_metodo_resultado_viga():
    sec = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.05,
                              hormigon=H30, acero=A420)
    r   = VigaSimple(sec, L=5.0, wU=25.0).calcular()
    fig = r.graficar_3d()
    assert fig is not None


def test_visualizar_elemento_3d_titulo_personalizado():
    sec = SeccionRectangular(b=0.40, h=0.80, recubrimiento=0.06,
                              hormigon=H30, acero=A420)
    fig = visualizar_elemento_3d(sec, L=8.0, titulo='Viga principal piso 3')
    assert 'Viga principal piso 3' in fig.layout.title.text
