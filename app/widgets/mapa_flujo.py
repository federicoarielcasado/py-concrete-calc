"""
Diálogo con el mapa de flujo de diseño estructural.
Muestra cuándo usar cada módulo y cómo se vinculan entre sí.
"""
from __future__ import annotations
import math

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from app.widgets.tema_figuras import FIJO, aplicar_tema_figura
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt


# ── Datos de nodos ────────────────────────────────────────────────────────────
#   key: (cx, cy, título, descripción, color_fondo, color_texto, ancho, alto)
_NODOS: dict[str, tuple] = {
    'E09': (6.0, 5.35, 'E-09 / PLANTA',
            'Punto de partida — modelar la planta\ny propagar cargas gravitacionales',
            '#1F5FAD', '#FFFFFF', 3.1, 0.80),

    'L04': (2.0, 3.75, 'L-04 / LOSA',
            'Losas en 1 dir. (coef. art. 8.3.3)\no 2 dir. DDM (art. 13.6)',
            '#2E7D5B', '#FFFFFF', 2.9, 0.75),

    'V05': (6.0, 3.75, 'V-05 / VIGA',
            'Simple / voladizo / continua\nArmadura longitudinal + estribos',
            '#2E7D5B', '#FFFFFF', 2.9, 0.75),

    'P03': (10.0, 3.75, 'P-03 / COLUMNA',
            'Flexocompresión P+M\nDiagrama de interacción',
            '#2E7D5B', '#FFFFFF', 2.9, 0.75),

    'F01': (1.2, 2.0, 'F-01 / FLEXIÓN',
            'Mu → As (dimensionado)\nAs → φMn (verificación)',
            '#B0661E', '#FFFFFF', 2.2, 0.70),

    'C02': (3.6, 2.0, 'C-02 / CORTE',
            'Estribos para resistir Vu\n(art. 11.5)',
            '#B0661E', '#FFFFFF', 2.2, 0.70),

    'T06': (6.0, 2.0, 'T-06 / TORSIÓN',
            'Tu + Vu combinados\n(art. 11.6)',
            '#B0661E', '#FFFFFF', 2.2, 0.70),

    'B07': (10.0, 2.0, 'B-07 / BASES',
            'Zapata centrada (cap. 15)\nRecibe Pu de P-03',
            '#6B4FA0', '#FFFFFF', 2.2, 0.70),

    'M08': (11.8, 5.35, 'M-08 / MÉNSULA',
            'Bielas y tirantes, a/d < 1\n(art. 10.7 + 11.9)',
            '#5B6775', '#FFFFFF', 2.3, 0.70),
}

# ── Aristas: (origen, destino, etiqueta, curvatura) ──────────────────────────
_ARISTAS = [
    ('E09', 'L04', 'geometría / cargas',  0.0),
    ('E09', 'V05', 'cargas vigas',         0.0),
    ('E09', 'P03', 'Pu, Mu',              0.0),
    ('L04', 'V05', 'carga dist.',          0.0),
    ('V05', 'P03', 'reacciones',          0.0),
    ('V05', 'F01', 'Mu',                  0.1),
    ('V05', 'C02', 'Vu',                  0.05),
    ('V05', 'T06', 'Tu, Vu',             -0.05),
    ('P03', 'B07', 'Pu',                  0.0),
]

_LEYENDA = [
    ('#1F5FAD', 'E-09 — Modelo global de planta (punto de partida)'),
    ('#2E7D5B', 'Elementos estructurales principales'),
    ('#B0661E', 'Módulos de detalle de sección'),
    ('#6B4FA0', 'Fundaciones'),
    ('#5B6775', 'Elementos especiales'),
]


def _edge_pt(cx: float, cy: float, tx: float, ty: float,
             nw: float, nh: float) -> tuple[float, float]:
    """Punto en el borde de un nodo rectangular en dirección al objetivo."""
    dx, dy = tx - cx, ty - cy
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return cx, cy
    hw, hh = nw / 2, nh / 2
    if abs(dx) < 1e-9:
        return cx, cy + math.copysign(hh, dy)
    if abs(dy) < 1e-9:
        return cx + math.copysign(hw, dx), cy
    sx = hw / abs(dx)
    sy = hh / abs(dy)
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def _crear_figura() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.set_xlim(-0.2, 13.5)
    ax.set_ylim(1.2, 6.2)
    ax.axis('off')

    ax.set_title(
        'Mapa de flujo de diseño  —  CIRSOC 201-2005',
        fontsize=11, fontweight='bold', color='#1F2933',
        pad=6,
    )

    # ── Nodos ─────────────────────────────────────────────────────────────────
    for key, (cx, cy, titulo, desc, fc, tc, nw, nh) in _NODOS.items():
        x0, y0 = cx - nw / 2, cy - nh / 2
        box = FancyBboxPatch(
            (x0, y0), nw, nh,
            boxstyle='round,pad=0.05',
            facecolor=fc, edgecolor='none', linewidth=0,
            zorder=2, gid=FIJO,
        )
        ax.add_patch(box)
        # Título en negrita (línea superior)
        ax.text(cx, cy + nh * 0.15, titulo,
                ha='center', va='center', fontsize=8.5,
                fontweight='bold', color=tc, zorder=3, gid=FIJO)
        # Descripción (línea inferior, más pequeña)
        ax.text(cx, cy - nh * 0.22, desc,
                ha='center', va='center', fontsize=6.2,
                color=tc, zorder=3,
                linespacing=1.3, gid=FIJO)

    # ── Aristas ───────────────────────────────────────────────────────────────
    for src, dst, label, rad in _ARISTAS:
        sx, sy, *_, snw, snh = _NODOS[src]
        dx, dy, *_, dnw, dnh = _NODOS[dst]
        x0, y0 = _edge_pt(sx, sy, dx, dy, snw, snh)
        x1, y1 = _edge_pt(dx, dy, sx, sy, dnw, dnh)

        ax.annotate(
            '', xy=(x1, y1), xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle='->', color='#303030', lw=1.3,
                connectionstyle=f'arc3,rad={rad}',
                mutation_scale=10,
            ),
            zorder=1,
        )

        # Etiqueta de arista
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(mx, my, f' {label} ',
                ha='center', va='center', fontsize=6.5,
                color='#101010', zorder=4,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='#D8D8C8',
                          edgecolor='#A0A0A0', linewidth=0.5, alpha=0.9))

    # ── Nota M-08 (sin flecha al flujo principal) ─────────────────────────────
    ax.annotate(
        'Elemento especial\n(independiente del\nflujo principal)',
        xy=(11.8, 4.95), xytext=(11.8, 4.55),
        ha='center', va='top', fontsize=6, color='#505050',
        arrowprops=dict(arrowstyle='->', color='#808080', lw=0.8),
        zorder=4,
    )

    # ── Leyenda ───────────────────────────────────────────────────────────────
    for i, (color, texto) in enumerate(_LEYENDA):
        x = 0.01 + (i % 3) * 0.34
        y = 0.06 - (i // 3) * 0.055
        patch = FancyBboxPatch((x, y), 0.02, 0.03,
                               boxstyle='round,pad=0.005',
                               facecolor=color, edgecolor='none',
                               linewidth=0.8, transform=fig.transFigure,
                               zorder=5, clip_on=False, gid=FIJO)
        fig.add_artist(patch)
        fig.text(x + 0.032, y + 0.015, texto, va='center',
                 fontsize=6.5, color='#101010')

    fig.tight_layout(rect=[0, 0.10, 1, 1])
    return fig


# ── Diálogo ───────────────────────────────────────────────────────────────────

class MapaFlujo(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Mapa de flujo de diseño  —  CIRSOC 201-2005')
        self.setMinimumSize(1240, 620)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        self._fig = _crear_figura()
        self._canvas = FigureCanvasQTAgg(self._fig)
        lay.addWidget(self._canvas, 1)
        self.aplicar_tema()

        hl = QHBoxLayout()
        lbl = QLabel(
            'E-09 PLANTA es el punto de partida para estructuras completas.  '
            'Los módulos de detalle (F-01, C-02, T-06) pueden usarse también '
            'de forma independiente sobre cualquier sección conocida.'
        )
        lbl.setWordWrap(True)
        lbl.setObjectName('status_label')
        hl.addWidget(lbl, 1)

        btn_cerrar = QPushButton('Cerrar')
        btn_cerrar.setFixedWidth(90)
        btn_cerrar.clicked.connect(self.hide)
        hl.addWidget(btn_cerrar)
        lay.addLayout(hl)

    def aplicar_tema(self) -> None:
        from app.themes import get_tema
        aplicar_tema_figura(self._fig, get_tema())
        self._canvas.draw_idle()
