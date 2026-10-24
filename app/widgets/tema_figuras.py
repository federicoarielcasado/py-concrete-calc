"""
Adaptación de figuras matplotlib al tema activo.

Las figuras de `graficos/` se generan siempre sobre fondo claro. Para el tema
oscuro se recorren sus artistas y se transforman los colores:
  - grises (fondos, texto, ejes, bordes, celdas de tablas) → se invierte su
    luminosidad dentro del rango fondo/texto del tema;
  - colores saturados oscuros → se aclaran para mantener el contraste.
Los colores originales se guardan en cada artista, así que volver al tema
claro restaura la figura exacta.
"""
from __future__ import annotations

import colorsys

from matplotlib.colors import to_rgba, to_hex
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
from matplotlib.collections import Collection
from matplotlib.table import Table

_ATTR = '_colores_tema_claro'
FIJO = 'color_fijo'   # gid de artistas que conservan su color en ambos temas


def _lum(hex_color: str) -> float:
    r, g, b, _ = to_rgba(hex_color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _transformar(color, tema):
    """Color del tema claro → color equivalente en el tema oscuro."""
    r, g, b, a = to_rgba(color)
    if a == 0:
        return (r, g, b, a)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if max(r, g, b) - min(r, g, b) < 0.10:          # gris: invertir dentro del rango
        fondo, texto = _lum(tema.fig_ejes), _lum(tema.fig_texto)
        nl = fondo + (1.0 - l) * (texto - fondo)
        nr, ng, nb = colorsys.hls_to_rgb(h, nl, s)
        return (nr, ng, nb, a)
    if l < 0.45:                                     # saturado oscuro: aclarar
        nr, ng, nb = colorsys.hls_to_rgb(h, min(0.62, l + 0.28), s)
        return (nr, ng, nb, a)
    return (r, g, b, a)


def _artistas(fig: Figure):
    vistos = set()
    for a in fig.findobj():
        if id(a) in vistos:
            continue
        vistos.add(id(a))
        yield a
        if isinstance(a, Text) and a.get_bbox_patch() is not None:
            yield a.get_bbox_patch()
        if isinstance(a, Table):
            for celda in a.get_celld().values():
                yield celda
                yield celda.get_text()


def _guardar(a, props: dict) -> dict:
    if not hasattr(a, _ATTR):
        setattr(a, _ATTR, props)
    return getattr(a, _ATTR)


def aplicar_tema_figura(fig: Figure, tema) -> None:
    """Aplica `tema` a la figura (idempotente: parte siempre de los colores claros)."""
    oscuro = tema.oscuro

    def tr(c):
        # Un color totalmente transparente se repone como 'none': si el artista
        # tiene alpha propio (p. ej. bbox de un texto), set_*color lo haría visible.
        if to_rgba(c)[3] == 0:
            return 'none'
        return _transformar(c, tema) if oscuro else c

    for a in _artistas(fig):
        if a.get_gid() == FIJO:
            continue
        try:
            if isinstance(a, Text):
                o = _guardar(a, {'color': a.get_color()})
                a.set_color(tr(o['color']))
            elif isinstance(a, Line2D):
                o = _guardar(a, {'color': a.get_color(),
                                 'mec': a.get_markeredgecolor(),
                                 'mfc': a.get_markerfacecolor()})
                a.set_color(tr(o['color']))
                a.set_markeredgecolor(tr(o['mec']))
                a.set_markerfacecolor(tr(o['mfc']))
            elif isinstance(a, Patch):
                o = _guardar(a, {'fc': a.get_facecolor(), 'ec': a.get_edgecolor()})
                a.set_facecolor(tr(o['fc']))
                a.set_edgecolor(tr(o['ec']))
            elif isinstance(a, Collection):
                o = _guardar(a, {'fc': a.get_facecolor().copy(),
                                 'ec': a.get_edgecolor().copy()})
                a.set_facecolor([tr(c) for c in o['fc']] if len(o['fc']) else o['fc'])
                a.set_edgecolor([tr(c) for c in o['ec']] if len(o['ec']) else o['ec'])
        except (ValueError, TypeError):
            continue

    # Fondos de figura y ejes con los colores exactos del tema
    fig.patch.set_facecolor(tema.fig_fondo)
    for ax in fig.axes:
        o = _guardar(ax.patch, {'fc': ax.patch.get_facecolor(), 'ec': ax.patch.get_edgecolor()})
        if to_hex(o['fc']) in ('#ffffff', '#fafbfc'):
            ax.patch.set_facecolor(tema.fig_ejes)


def con_tema_claro(fig: Figure):
    """Context manager: deja la figura en colores claros (para exportar / imprimir)."""
    from contextlib import contextmanager
    from app.themes import CLARO, get_tema

    @contextmanager
    def _cm():
        aplicar_tema_figura(fig, CLARO)
        try:
            yield fig
        finally:
            aplicar_tema_figura(fig, get_tema())
    return _cm()
