"""
Visualización 3D interactiva del esquema de planta estructural — Plotly.

Función principal:
    visualizar_planta_3d(planta, propagacion=None) → plotly.graph_objects.Figure

Muestra:
  - Columnas como prismas verticales
  - Vigas como prismas a nivel de losa
  - Losas como planos semitransparentes
  - Etiquetas con ID y Pu/wu cuando se pasa resultado de propagación
"""
from __future__ import annotations

from hormigon.modelo import PlantaEstructural
from hormigon.propagacion import ResultadoPropagacion


# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------

_C_COL_FACE  = 'rgba(44, 62, 80, 0.82)'
_C_COL_EDGE  = 'rgba(20, 30, 40, 1.0)'
_C_VIG_FACE  = 'rgba(130, 84, 44, 0.78)'
_C_VIG_EDGE  = 'rgba(80, 50, 20, 1.0)'
_C_LOS_FACE  = 'rgba(189, 195, 199, 0.22)'
_C_LOS_EDGE  = 'rgba(120, 130, 140, 0.55)'
_C_TEXT_COL  = '#e74c3c'
_C_TEXT_VIG  = '#1a6fa8'


# ---------------------------------------------------------------------------
# Primitivas
# ---------------------------------------------------------------------------

def _box(x0, x1, y0, y1, z0, z1,
         color_face, color_edge,
         name='', group='', showlegend=False):
    """
    Devuelve [mesh_trace, edge_trace] para un paralelepípedo.
    """
    import plotly.graph_objects as go

    vx = [x0, x1, x1, x0, x0, x1, x1, x0]
    vy = [y0, y0, y1, y1, y0, y0, y1, y1]
    vz = [z0, z0, z0, z0, z1, z1, z1, z1]

    # 12 triángulos — 6 caras × 2
    ii = [0, 0,  4, 4,  0, 0,  1, 1,  2, 2,  3, 3]
    jj = [1, 2,  5, 6,  1, 5,  2, 6,  3, 7,  0, 4]
    kk = [2, 3,  6, 7,  5, 4,  6, 5,  7, 6,  4, 7]

    # opacity from rgba string
    try:
        opacity = float(color_face.split(',')[-1].rstrip(')').strip())
    except (ValueError, IndexError):
        opacity = 0.8

    mesh = go.Mesh3d(
        x=vx, y=vy, z=vz,
        i=ii, j=jj, k=kk,
        color=color_face,
        opacity=opacity,
        flatshading=True,
        name=name,
        legendgroup=group,
        showlegend=showlegend,
        hovertext=name,
        hoverinfo='text',
    )

    # 12 aristas
    segs = [
        (0, 1), (1, 2), (2, 3), (3, 0),    # cara inferior
        (4, 5), (5, 6), (6, 7), (7, 4),    # cara superior
        (0, 4), (1, 5), (2, 6), (3, 7),    # pilares
    ]
    xs, ys, zs = [], [], []
    for a, b_ in segs:
        xs += [vx[a], vx[b_], None]
        ys += [vy[a], vy[b_], None]
        zs += [vz[a], vz[b_], None]

    edges = go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode='lines',
        line=dict(color=color_edge, width=2),
        name=name,
        legendgroup=group,
        showlegend=False,
        hoverinfo='skip',
    )

    return [mesh, edges]


def _texto(x, y, z, txt, color, size=11, name='', group='', showlegend=False):
    import plotly.graph_objects as go
    return go.Scatter3d(
        x=[x], y=[y], z=[z],
        mode='text',
        text=[txt],
        textfont=dict(color=color, size=size),
        name=name,
        legendgroup=group,
        showlegend=showlegend,
        hoverinfo='skip',
    )


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def visualizar_planta_3d(
    planta: PlantaEstructural,
    propagacion: ResultadoPropagacion | None = None,
    mostrar_ids: bool = True,
    mostrar_cargas: bool = True,
    titulo: str = 'Planta Estructural 3D',
) -> 'plotly.graph_objects.Figure':
    """
    Genera una figura Plotly 3D con el esquema estructural de la planta.

    planta      : PlantaEstructural con grilla, vigas, columnas y losas
    propagacion : resultado de propagar(planta); agrega etiquetas Pu/wu
    mostrar_ids : dibuja el ID de cada elemento
    mostrar_cargas : dibuja Pu en columnas y wu en vigas (requiere propagacion)
    """
    import plotly.graph_objects as go

    g = planta.grilla
    traces = []

    # z de referencia = máxima altura de entrepiso
    h_piso = max(
        (col.h_entrepiso for col in planta.columnas.values()),
        default=3.0,
    )

    # ── Columnas ────────────────────────────────────────────────────────────
    first_col = True
    for col in planta.columnas.values():
        xc = g.ejes_x[col.ix]
        yc = g.ejes_y[col.iy]
        bx = col.seccion.b / 2
        by = col.seccion.h / 2
        traces += _box(
            xc - bx, xc + bx,
            yc - by, yc + by,
            0.0, col.h_entrepiso,
            _C_COL_FACE, _C_COL_EDGE,
            name='Columnas', group='col',
            showlegend=first_col,
        )
        first_col = False

        rotulo = []
        if mostrar_ids:
            rotulo.append(col.id)
        if mostrar_cargas and propagacion and col.id in propagacion.cargas_columnas:
            rotulo.append(f'Pu={propagacion.cargas_columnas[col.id].Pu:.0f} kN')
        if rotulo:
            traces.append(_texto(
                xc, yc, col.h_entrepiso + 0.35,
                '<br>'.join(rotulo),
                color=_C_TEXT_COL, size=10,
                group='col_id',
            ))

    # ── Vigas ────────────────────────────────────────────────────────────────
    first_viga = True
    for viga in planta.vigas.values():
        bv = viga.seccion.b
        hv = viga.seccion.h
        z_top = h_piso
        z_bot = h_piso - hv

        if viga.dir == 'x':
            x0 = g.ejes_x[viga.desde]
            x1 = g.ejes_x[viga.hasta]
            yc = g.ejes_y[viga.idx]
            y0, y1 = yc - bv / 2, yc + bv / 2
            xm, ym = (x0 + x1) / 2, yc
            # rótulo en el centro del primer tramo (evita choques en cruces de vigas)
            xr, yr = (x0 + g.ejes_x[viga.desde + 1]) / 2, yc
        else:   # dir == 'y'
            y0 = g.ejes_y[viga.desde]
            y1 = g.ejes_y[viga.hasta]
            xc = g.ejes_x[viga.idx]
            x0, x1 = xc - bv / 2, xc + bv / 2
            xm, ym = xc, (y0 + y1) / 2
            xr, yr = xc, (y0 + g.ejes_y[viga.desde + 1]) / 2

        traces += _box(
            x0, x1, y0, y1, z_bot, z_top,
            _C_VIG_FACE, _C_VIG_EDGE,
            name='Vigas', group='vig',
            showlegend=first_viga,
        )
        first_viga = False

        rotulo = []
        if mostrar_ids:
            rotulo.append(viga.id)
        if mostrar_cargas and propagacion and viga.id in propagacion.cargas_vigas:
            rotulo.append(f'wu={propagacion.cargas_vigas[viga.id].wu:.1f} kN/m')
        if rotulo:
            traces.append(_texto(
                xr, yr, z_top + 0.15,
                '<br>'.join(rotulo),
                color=_C_TEXT_VIG, size=9,
                group='vig_id',
            ))

    # ── Losas ────────────────────────────────────────────────────────────────
    first_losa = True
    for losa in planta.losas.values():
        x0 = g.ejes_x[losa.i]
        x1 = g.ejes_x[losa.i + 1]
        y0 = g.ejes_y[losa.j]
        y1 = g.ejes_y[losa.j + 1]
        z_bot = h_piso - losa.h
        z_top = h_piso

        traces += _box(
            x0, x1, y0, y1, z_bot, z_top,
            _C_LOS_FACE, _C_LOS_EDGE,
            name='Losas', group='los',
            showlegend=first_losa,
        )
        first_losa = False

        if mostrar_ids:
            xm = (x0 + x1) / 2
            ym = (y0 + y1) / 2
            traces.append(_texto(
                xm, ym, z_top + 0.05,
                losa.id,
                color='#555', size=9,
                group='los_id',
            ))

    # ── Layout ───────────────────────────────────────────────────────────────
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=titulo,
        scene=dict(
            xaxis=dict(title='X [m]', showgrid=True),
            yaxis=dict(title='Y [m]', showgrid=True),
            zaxis=dict(title='Z [m]', showgrid=True),
            aspectmode='data',
        ),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor='rgba(255,255,255,0.7)',
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    return fig
