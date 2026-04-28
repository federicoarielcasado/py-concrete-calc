"""
Visualización 3D interactiva de elementos de hormigón armado — Plotly.

Función principal:
  visualizar_elemento_3d(seccion, L, ...)  →  plotly.graph_objects.Figure

La figura muestra:
  - Prisma de hormigón con caras semitransparentes
  - Barras longitudinales (inferiores y superiores)
  - Estribos a separación constante
  - Ejes y cotas

Integración con elementos/:
  resultado_viga.graficar_3d()  →  llama a visualizar_elemento_3d()
"""
from __future__ import annotations

import math
import numpy as np


# ── Colores ────────────────────────────────────────────────────────────────────

_C_HORMIGON_FACE  = 'rgba(210, 200, 180, 0.18)'
_C_HORMIGON_EDGE  = 'rgba(100, 90, 70, 0.70)'
_C_BARRA_INF      = '#c0392b'   # rojo — armadura traccionada
_C_BARRA_SUP      = '#e67e22'   # naranja — armadura comprimida
_C_ESTRIBO        = '#2980b9'   # azul


# ── Utilidades de geometría ────────────────────────────────────────────────────

def _segmentos(pts_lista, color, width=3, name='', showlegend=False):
    """
    Convierte una lista de pares [(x0,y0,z0),(x1,y1,z1), ...] en un único
    Scatter3d con breaks None entre cada segmento.
    """
    import plotly.graph_objects as go
    xs, ys, zs = [], [], []
    for p0, p1 in pts_lista:
        xs += [p0[0], p1[0], None]
        ys += [p0[1], p1[1], None]
        zs += [p0[2], p1[2], None]
    return go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode='lines',
        line=dict(color=color, width=width),
        name=name,
        showlegend=showlegend,
        hoverinfo='skip',
    )


def _aristas_prisma(b, h, L):
    """12 aristas del prisma de hormigón (vértices en x=0..b, y=0..h, z=0..L)."""
    v = [
        (0, 0, 0), (b, 0, 0), (b, h, 0), (0, h, 0),   # cara frontal
        (0, 0, L), (b, 0, L), (b, h, L), (0, h, L),   # cara trasera
    ]
    aristas = [
        # cara frontal
        (v[0], v[1]), (v[1], v[2]), (v[2], v[3]), (v[3], v[0]),
        # cara trasera
        (v[4], v[5]), (v[5], v[6]), (v[6], v[7]), (v[7], v[4]),
        # longitudinales
        (v[0], v[4]), (v[1], v[5]), (v[2], v[6]), (v[3], v[7]),
    ]
    return aristas


def _caras_prisma(b, h, L):
    """Mesh3d semitransparente del prisma."""
    import plotly.graph_objects as go
    x = [0, b, b, 0, 0, b, b, 0]
    y = [0, 0, h, h, 0, 0, h, h]
    z = [0, 0, 0, 0, L, L, L, L]
    # 6 caras × 2 triángulos = 12 triángulos
    i = [0, 0, 4, 4, 1, 1, 0, 0, 3, 3, 2, 2]
    j = [1, 3, 5, 7, 2, 5, 4, 3, 7, 2, 6, 5]
    k = [2, 4, 6, 3, 6, 4, 7, 7, 4, 6, 5, 1]
    # corregir cara bottom / top
    i = [0, 2, 4, 6, 0, 1, 1, 2, 3, 3, 0, 4]
    j = [1, 3, 5, 7, 4, 5, 2, 6, 7, 2, 3, 7]
    k = [2, 0, 6, 4, 1, 4, 6, 5, 2, 6, 7, 3]
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=_C_HORMIGON_FACE,
        flatshading=True,
        showlegend=False,
        hoverinfo='skip',
        opacity=0.18,
        name='Hormigón',
    )


def _posiciones_barras_inf(b, h, recub, n):
    """
    Devuelve las posiciones (x, y) de n barras en la cara traccionada (inferior).
    Las barras se distribuyen uniformemente entre recubrimientos laterales.
    """
    y = recub
    if n == 1:
        return [(b / 2.0, y)]
    xs = np.linspace(recub, b - recub, n)
    return [(float(x), y) for x in xs]


def _posiciones_barras_sup(b, h, recub, n):
    """Posiciones de n barras en la cara comprimida (superior)."""
    y = h - recub
    if n == 1:
        return [(b / 2.0, y)]
    xs = np.linspace(recub, b - recub, n)
    return [(float(x), y) for x in xs]


def _traza_barras(posiciones_xy, L, color, name, phi_m):
    """Líneas longitudinales para un conjunto de barras."""
    segs = [((x, y, 0.0), (x, y, L)) for x, y in posiciones_xy]
    return _segmentos(segs, color=color, width=max(2, int(phi_m * 200)), name=name, showlegend=True)


def _traza_estribos(b, h, recub, phi_estribo_m, s, L):
    """
    Marcos rectangulares de estribo a separación s a lo largo de L.

    El centro del estribo queda a recub de cada cara.
    """
    segs = []
    xc = recub
    yc = recub
    xd = b - recub
    yd = h - recub

    z0 = recub
    while z0 <= L - recub + 1e-9:
        z = min(z0, L - recub)
        corners = [
            (xc, yc, z), (xd, yc, z),
            (xd, yd, z), (xc, yd, z),
            (xc, yc, z),   # cierre
        ]
        for i in range(len(corners) - 1):
            segs.append((corners[i], corners[i + 1]))
        z0 += s

    return _segmentos(segs, color=_C_ESTRIBO, width=2,
                      name=f'Estribos  (s={s*100:.0f} cm)', showlegend=True)


# ── Función principal ──────────────────────────────────────────────────────────

def visualizar_elemento_3d(
    seccion,
    L: float,
    n_inf:        int   = 3,
    phi_inf_mm:   int   = 16,
    n_sup:        int   = 0,
    phi_sup_mm:   int   = 0,
    s_estribo:    float = 0.20,
    phi_estribo_mm: int = 8,
    titulo:       str | None = None,
) -> 'plotly.graph_objects.Figure':
    """
    Visualización 3D interactiva de una viga o columna rectangular.

    Parámetros
    ----------
    seccion        : SeccionRectangular
    L              : longitud del elemento [m]
    n_inf          : número de barras en la cara traccionada (inferior)
    phi_inf_mm     : diámetro de barra inferior [mm]
    n_sup          : número de barras en la cara comprimida (superior); 0 = sin armadura sup.
    phi_sup_mm     : diámetro de barra superior [mm]
    s_estribo      : separación entre estribos [m]
    phi_estribo_mm : diámetro del estribo [mm]
    titulo         : título del gráfico

    Retorna
    -------
    plotly.graph_objects.Figure
    """
    import plotly.graph_objects as go

    b    = seccion.b
    h    = seccion.h
    recub = seccion.recubrimiento

    traces = []

    # Caras semitransparentes del hormigón
    traces.append(_caras_prisma(b, h, L))

    # Aristas del prisma
    traces.append(_segmentos(
        _aristas_prisma(b, h, L),
        color=_C_HORMIGON_EDGE, width=2,
        name='Sección', showlegend=False,
    ))

    # Barras inferiores (traccionadas)
    if n_inf > 0:
        pos_inf = _posiciones_barras_inf(b, h, recub, n_inf)
        traces.append(_traza_barras(
            pos_inf, L,
            color=_C_BARRA_INF,
            name=f'{n_inf}φ{phi_inf_mm}  (tracción)',
            phi_m=phi_inf_mm / 1000,
        ))

    # Barras superiores (comprimidas)
    if n_sup > 0:
        pos_sup = _posiciones_barras_sup(b, h, recub, n_sup)
        traces.append(_traza_barras(
            pos_sup, L,
            color=_C_BARRA_SUP,
            name=f'{n_sup}φ{phi_sup_mm}  (compresión)',
            phi_m=phi_sup_mm / 1000,
        ))

    # Estribos
    traces.append(_traza_estribos(
        b, h, recub,
        phi_estribo_m=phi_estribo_mm / 1000,
        s=s_estribo,
        L=L,
    ))

    # Layout
    titulo = titulo or f'Elemento  {b*100:.0f}×{h*100:.0f} cm  L={L:.2f} m'
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=titulo, x=0.5, font=dict(size=13)),
        scene=dict(
            xaxis=dict(title='x [m]', range=[-0.05*b, 1.05*b]),
            yaxis=dict(title='y [m]', range=[-0.05*h, 1.05*h]),
            zaxis=dict(title='z [m]', range=[-0.05*L, 1.05*L]),
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=1.2, z=0.8)),
        ),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor='rgba(255,255,255,0.7)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


# ── Wrapper desde ResultadoViga ────────────────────────────────────────────────

def visualizar_viga_3d(resultado) -> 'plotly.graph_objects.Figure':
    """
    Genera la visualización 3D a partir de un ResultadoViga.

    Extrae automáticamente la armadura adoptada (si se llamó a adoptar())
    o usa la calculada. La separación de estribos se toma del s_maximo.
    """
    from hormigon.materiales import BARRAS

    sec   = resultado.seccion
    L     = resultado.L
    rf    = resultado.resultado_flex
    rc    = resultado.resultado_corte

    # Barras inferiores
    if rf.phi_adoptado is not None:
        n_inf       = rf.n_barras
        phi_inf_mm  = rf.phi_adoptado
    else:
        # Estimar combinación de barras a partir de As calculada
        n_inf, phi_inf_mm = _estimar_barras(rf.As)

    # Barras superiores (armadura comprimida si hay)
    n_sup, phi_sup_mm = 0, 0
    if rf.As_prima > 0:
        if rf.phi_adoptado_prima is not None:
            n_sup      = rf.n_barras_prima
            phi_sup_mm = rf.phi_adoptado_prima
        else:
            n_sup, phi_sup_mm = _estimar_barras(rf.As_prima)

    # Estribo: elegir φ8 y s = s_maximo
    s_est = rc.s_maximo if rc.s_maximo < L else min(0.20, L / 3.0)

    titulo = (f'Viga {sec.b*100:.0f}×{sec.h*100:.0f} cm  '
              f'L={L:.1f} m  |  '
              f'wu={resultado.wu:.1f} kN/m')

    return visualizar_elemento_3d(
        seccion=sec, L=L,
        n_inf=n_inf, phi_inf_mm=phi_inf_mm,
        n_sup=n_sup, phi_sup_mm=phi_sup_mm,
        s_estribo=s_est,
        titulo=titulo,
    )


def _estimar_barras(As_cm2: float) -> tuple[int, int]:
    """Devuelve (n, phi_mm) que cubre As_cm2 con mínima As sobrante."""
    from hormigon.materiales import BARRAS, DIAMETROS
    mejor = (4, 12)
    mejor_exceso = 1e9
    for phi in DIAMETROS:
        a = BARRAS[phi]
        n = math.ceil(As_cm2 / a)
        n = max(2, min(n, 8))
        exceso = n * a - As_cm2
        if exceso >= 0 and exceso < mejor_exceso:
            mejor_exceso = exceso
            mejor = (n, phi)
    return mejor
