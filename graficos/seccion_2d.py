"""
Sección transversal 2D con armaduras — matplotlib.

Función principal:
  graficar_seccion(seccion, resultado_flex=None, resultado_corte=None, titulo=None)
  → matplotlib.figure.Figure
"""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import Circle, Rectangle

# ── Paleta ────────────────────────────────────────────────────────────────────
_C_HORM   = '#DCDCDC'
_C_BLOQUE = '#4472C4'
_C_BT     = '#C00000'   # barras traccionadas
_C_BC     = '#FF8C00'   # barras comprimidas
_C_EST    = '#404040'   # estribos
_C_NA     = '#0055AA'   # eje neutro


# ── Helpers de dibujo ─────────────────────────────────────────────────────────

def _xposiciones(n: int, x_min: float, x_max: float) -> list[float]:
    if n <= 1:
        return [(x_min + x_max) / 2]
    return [x_min + i * (x_max - x_min) / (n - 1) for i in range(n)]


def _dibujar_barras(ax, n: int, phi_mm: float, y: float,
                    x_min: float, x_max: float, color: str):
    r = phi_mm / 2000.0
    for x in _xposiciones(n, x_min + r, x_max - r):
        ax.add_patch(Circle((x, y), r, facecolor=color,
                            edgecolor='black', linewidth=0.5, zorder=5))


def _dibujar_estribo_rect(ax, x0: float, y0: float, ancho: float, alto: float,
                           phi_mm: float, color: str):
    r = phi_mm / 2000.0
    ax.add_patch(Rectangle(
        (x0 - r, y0 - r), ancho + 2*r, alto + 2*r,
        linewidth=max(0.8, phi_mm / 10),
        edgecolor=color, facecolor='none', zorder=3,
    ))


def _cota_h(ax, x1: float, x2: float, y: float, texto: str, fs: float = 7):
    dy = min(abs(x2 - x1) * 0.12, 0.014)
    ax.annotate('', xy=(x2, y - dy), xytext=(x1, y - dy),
                arrowprops=dict(arrowstyle='<->', color='#333', lw=0.8))
    ax.text((x1 + x2) / 2, y - dy - dy * 0.4,
            texto, ha='center', va='top', fontsize=fs, color='#333')


def _cota_v(ax, y1: float, y2: float, x: float, texto: str, fs: float = 7):
    dx = min(abs(y2 - y1) * 0.10, 0.012)
    x_ = x + dx
    ax.annotate('', xy=(x_, y2), xytext=(x_, y1),
                arrowprops=dict(arrowstyle='<->', color='#444', lw=0.8))
    ax.text(x_ + dx * 0.5, (y1 + y2) / 2,
            texto, ha='left', va='center', fontsize=fs, color='#444', rotation=90)


def _panel_info(ax, lines: list[tuple[str, str]]):
    ax.axis('off')
    n_real = sum(1 for k, _ in lines if k != '---')
    dy = min(0.072, 0.92 / max(n_real, 1))
    y = 0.97
    for k, v in lines:
        if y < 0.02:
            break
        if k == '---':
            ax.plot([0.02, 0.98], [y, y], color='#CCC', linewidth=0.5,
                    transform=ax.transAxes)
            y -= dy * 0.4
            continue
        ax.text(0.03, y, k, ha='left', va='top', fontsize=8,
                transform=ax.transAxes, color='#555')
        if v:
            ax.text(0.40, y, v, ha='left', va='top', fontsize=8,
                    transform=ax.transAxes, color='black', fontweight='bold')
        y -= dy


def _lineas_info_flex(sec, rf, rc) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    if hasattr(sec, 'b'):
        lines.append(('Sección', f"{sec.b*100:.0f} × {sec.h*100:.0f} cm"))
    elif hasattr(sec, 'bw'):
        lines.append(('Sección T', f"bw={sec.bw*100:.0f}  b_ala={sec.b_ala*100:.0f}  h={sec.h*100:.0f} cm"))
    else:
        lines.append(('Sección', f"D={sec.D*100:.0f} cm"))
    if hasattr(sec, 'hormigon'):
        lines.append(("f'c", f"{sec.hormigon.fc} MPa"))
        lines.append(('fy',  f"{sec.acero.fy} MPa"))
    if rf is not None:
        lines.append(('---', ''))
        lines.append(('Mu',      f"{rf.Mu:.1f} kNm"))
        lines.append(('φ',       f"{rf.phi:.2f}"))
        lines.append(('Rotura',  f"{rf.tipo}"))
        check = '✓' if rf.verifica else '✗'
        lines.append(('φ·Mn',    f"{rf.phi_Mn:.1f} kNm  {check}"))
        lines.append(('a',       f"{rf.a*100:.2f} cm"))
        lines.append(('c',       f"{rf.c*100:.2f} cm"))
        lines.append(('εs',      f"{rf.epsilon_s:.5f}"))
        lines.append(('As calc', f"{rf.As:.2f} cm²"))
        if rf.As_prima > 0:
            lines.append(("As' calc", f"{rf.As_prima:.2f} cm²"))
        if rf.As_adoptada is not None:
            lines.append(('Adoptado',
                          f"{rf.n_barras}φ{rf.phi_adoptado} = {rf.As_adoptada:.2f} cm²"))
        if rf.As_adoptada_prima is not None:
            lines.append(("Adoptado'",
                          f"{rf.n_barras_prima}φ{rf.phi_adoptado_prima} = {rf.As_adoptada_prima:.2f} cm²"))
    if rc is not None:
        lines.append(('---', ''))
        lines.append(('Vu',    f"{rc.Vu:.1f} kN"))
        check = '✓' if rc.verifica_resistencia else '✗'
        lines.append(('φ·Vn',  f"{rc.phi_Vn:.1f} kN  {check}"))
        lines.append(('s_max', f"{rc.s_maximo*100:.0f} cm"))
        if rc.s_adoptado is not None:
            lines.append(('Estribos',
                          f"{rc.n_ramas}φ{rc.phi_estribo} c/{rc.s_adoptado*100:.0f} cm"))
    return lines


def _titulo(fig, rf, rc, titulo):
    if titulo:
        fig.suptitle(titulo, fontsize=10, fontweight='bold')
        return
    partes = []
    if rf:
        partes.append(f"Mu = {rf.Mu:.0f} kNm")
    if rc:
        partes.append(f"Vu = {rc.Vu:.0f} kN")
    fig.suptitle('  |  '.join(partes) if partes else 'Sección transversal',
                 fontsize=10)


# ── API pública ───────────────────────────────────────────────────────────────

def graficar_seccion(
    seccion,
    resultado_flex=None,
    resultado_corte=None,
    titulo: Optional[str] = None,
) -> plt.Figure:
    """
    Dibuja la sección transversal con armaduras y dimensiones.

    seccion         : SeccionRectangular, SeccionT o SeccionCircular.
    resultado_flex  : ResultadoFlexion (opcional) — muestra As, eje neutro y bloque.
    resultado_corte : ResultadoCorte   (opcional) — muestra diámetro del estribo.
    Retorna la Figure de matplotlib (usar plt.show() para visualizar).
    """
    if seccion is None:
        raise ValueError("seccion es obligatorio. Pasá la sección como primer argumento.")
    from hormigon.secciones import SeccionT, SeccionCircular
    if isinstance(seccion, SeccionCircular):
        return _fig_circ(seccion, resultado_flex, titulo)
    if isinstance(seccion, SeccionT):
        return _fig_T(seccion, resultado_flex, resultado_corte, titulo)
    return _fig_rect(seccion, resultado_flex, resultado_corte, titulo)


# ── Sección rectangular ───────────────────────────────────────────────────────

def _fig_rect(sec, rf, rc, titulo) -> plt.Figure:
    b       = sec.b
    h       = sec.h
    recub   = sec.recubrimiento
    recub_p = getattr(sec, 'recubrimiento_prima', recub)

    phi_est = 8.0
    if rc is not None and rc.phi_estribo:
        phi_est = float(rc.phi_estribo)
    est_inset = recub * 0.45          # distancia desde cara a eje del estribo
    x_bar_min = est_inset + phi_est / 2000.0
    x_bar_max = b - x_bar_min

    fig, (ax, ax_info) = plt.subplots(
        1, 2, figsize=(8, 5.5),
        gridspec_kw={'width_ratios': [3, 2.2]},
    )
    ax.set_aspect('equal')
    ax.axis('off')

    # Hormigón
    ax.add_patch(Rectangle((0, 0), b, h, linewidth=1.5,
                            edgecolor='black', facecolor=_C_HORM, zorder=1))

    # Bloque de tensiones + eje neutro
    if rf is not None:
        a, c = rf.a, rf.c
        ax.add_patch(Rectangle((0, h - a), b, a, linewidth=0,
                                facecolor=_C_BLOQUE, alpha=0.45, zorder=2))
        y_NA = h - c
        ax.plot([0, b], [y_NA, y_NA], color=_C_NA, lw=1.2, ls='--', zorder=6)
        ax.text(b * 1.02, y_NA,
                f' N.A.\n c={c*100:.1f}cm',
                va='center', fontsize=7, color=_C_NA)

    # Estribo
    _dibujar_estribo_rect(ax, est_inset, est_inset,
                          b - 2*est_inset, h - 2*est_inset, phi_est, _C_EST)

    # Barras traccionadas
    y_t = recub
    if rf is not None and rf.As_adoptada is not None:
        _dibujar_barras(ax, rf.n_barras, rf.phi_adoptado,
                        y_t, x_bar_min, x_bar_max, _C_BT)
    elif rf is not None:
        ax.text(b / 2, y_t, f'As\n{rf.As:.2f}cm²',
                ha='center', va='center', fontsize=6.5,
                color=_C_BT, fontweight='bold')

    # Barras comprimidas
    y_c = h - recub_p
    if rf is not None and rf.As_prima > 0:
        if rf.As_adoptada_prima is not None:
            _dibujar_barras(ax, rf.n_barras_prima, rf.phi_adoptado_prima,
                            y_c, x_bar_min, x_bar_max, _C_BC)
        else:
            ax.text(b / 2, y_c, f"As'\n{rf.As_prima:.2f}cm²",
                    ha='center', va='center', fontsize=6.5,
                    color=_C_BC, fontweight='bold')

    # Cotas
    _cota_h(ax, 0, b, 0, f'b = {b*100:.0f} cm')
    _cota_v(ax, 0, h, b, f'h = {h*100:.0f} cm')
    _cota_v(ax, recub, h, b + b * 0.25, f'd = {sec.d*100:.0f} cm')

    margin_x = b * 0.22
    margin_y = h * 0.18
    ax.set_xlim(-margin_x, b + b * 0.80)
    ax.set_ylim(-margin_y * 1.5, h + margin_y)

    _panel_info(ax_info, _lineas_info_flex(sec, rf, rc))
    _titulo(fig, rf, rc, titulo)
    fig.tight_layout()
    return fig


# ── Sección T ─────────────────────────────────────────────────────────────────

def _fig_T(sec, rf, rc, titulo) -> plt.Figure:
    b_ala = sec.b_ala
    h_ala = sec.h_ala
    bw    = sec.bw
    h     = sec.h
    hw    = sec.hw            # altura del alma (por debajo del ala)
    recub   = sec.recubrimiento
    recub_p = getattr(sec, 'recubrimiento_prima', recub)

    x_ws  = (b_ala - bw) / 2  # offset x del alma respecto al origen del ala

    phi_est = 8.0
    if rc is not None and rc.phi_estribo:
        phi_est = float(rc.phi_estribo)
    est_inset = recub * 0.45
    x_bar_min = x_ws + est_inset + phi_est / 2000.0
    x_bar_max = x_ws + bw - (est_inset + phi_est / 2000.0)

    fig, (ax, ax_info) = plt.subplots(
        1, 2, figsize=(8.5, 5.5),
        gridspec_kw={'width_ratios': [3, 2.2]},
    )
    ax.set_aspect('equal')
    ax.axis('off')

    # Ala
    ax.add_patch(Rectangle((0, hw), b_ala, h_ala, linewidth=1.5,
                            edgecolor='black', facecolor=_C_HORM, zorder=1))
    # Alma
    ax.add_patch(Rectangle((x_ws, 0), bw, hw, linewidth=1.5,
                            edgecolor='black', facecolor=_C_HORM, zorder=1))

    # Bloque de tensiones + eje neutro
    if rf is not None:
        a, c = rf.a, rf.c
        y_NA  = h - c
        if a <= h_ala:
            ax.add_patch(Rectangle((0, h - a), b_ala, a, linewidth=0,
                                    facecolor=_C_BLOQUE, alpha=0.45, zorder=2))
        else:
            ax.add_patch(Rectangle((0, hw), b_ala, h_ala, linewidth=0,
                                    facecolor=_C_BLOQUE, alpha=0.45, zorder=2))
            ax.add_patch(Rectangle((x_ws, h - a), bw, a - h_ala, linewidth=0,
                                    facecolor=_C_BLOQUE, alpha=0.45, zorder=2))
        x_na0 = 0 if y_NA >= hw else x_ws
        x_na1 = b_ala if y_NA >= hw else x_ws + bw
        ax.plot([x_na0, x_na1], [y_NA, y_NA], color=_C_NA, lw=1.2, ls='--', zorder=6)
        ax.text(b_ala * 1.02, y_NA,
                f' N.A.\n c={c*100:.1f}cm',
                va='center', fontsize=7, color=_C_NA)

    # Estribo en el alma
    _dibujar_estribo_rect(ax, x_ws + est_inset, est_inset,
                          bw - 2*est_inset, hw - 2*est_inset, phi_est, _C_EST)

    # Barras traccionadas (fondo del alma)
    y_t = recub
    if rf is not None and rf.As_adoptada is not None:
        _dibujar_barras(ax, rf.n_barras, rf.phi_adoptado,
                        y_t, x_bar_min, x_bar_max, _C_BT)
    elif rf is not None:
        ax.text(x_ws + bw / 2, y_t, f'As\n{rf.As:.2f}cm²',
                ha='center', va='center', fontsize=6.5,
                color=_C_BT, fontweight='bold')

    # Barras comprimidas (parte superior del ala)
    y_c  = h - recub_p
    xc_min = est_inset + phi_est / 2000.0
    xc_max = b_ala - xc_min
    if rf is not None and rf.As_prima > 0:
        if rf.As_adoptada_prima is not None:
            _dibujar_barras(ax, rf.n_barras_prima, rf.phi_adoptado_prima,
                            y_c, xc_min, xc_max, _C_BC)
        else:
            ax.text(b_ala / 2, y_c, f"As'\n{rf.As_prima:.2f}cm²",
                    ha='center', va='center', fontsize=6.5,
                    color=_C_BC, fontweight='bold')

    # Cotas
    _cota_h(ax, 0, b_ala, 0, f'b_ala = {b_ala*100:.0f} cm')
    _cota_h(ax, x_ws, x_ws + bw, 0, f'bw = {bw*100:.0f} cm')
    _cota_v(ax, 0, h, b_ala, f'h = {h*100:.0f} cm')
    _cota_v(ax, hw, h, b_ala + b_ala * 0.20, f'h_ala = {h_ala*100:.0f} cm')
    _cota_v(ax, recub, h, b_ala + b_ala * 0.40, f'd = {sec.d*100:.0f} cm')

    margin_x = b_ala * 0.20
    margin_y = h * 0.18
    ax.set_xlim(-margin_x, b_ala + b_ala * 0.90)
    ax.set_ylim(-margin_y * 1.5, h + margin_y)

    _panel_info(ax_info, _lineas_info_flex(sec, rf, rc))
    _titulo(fig, rf, rc, titulo)
    fig.tight_layout()
    return fig


# ── Sección circular (columnas) ───────────────────────────────────────────────

def _fig_circ(sec, rf, titulo) -> plt.Figure:
    from matplotlib.patches import Circle as MCircle

    D    = sec.D
    R    = D / 2
    recub = sec.recubrimiento
    r_bar_ring = R - recub   # radio del círculo que pasa por los centros de barra

    fig, (ax, ax_info) = plt.subplots(
        1, 2, figsize=(7, 5),
        gridspec_kw={'width_ratios': [2.8, 2]},
    )
    ax.set_aspect('equal')
    ax.axis('off')

    # Hormigón
    ax.add_patch(MCircle((R, R), R, linewidth=1.5,
                          edgecolor='black', facecolor=_C_HORM, zorder=1))

    # Anillo de referencia para barras
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(R + r_bar_ring * np.cos(theta),
            R + r_bar_ring * np.sin(theta),
            color='#AAAAAA', lw=0.6, ls=':', zorder=2)

    # Barras (si hay armadura adoptada)
    if rf is not None and rf.As_adoptada is not None:
        n_b   = rf.n_barras
        phi_b = rf.phi_adoptado
        r_b   = phi_b / 2000.0
        for k in range(n_b):
            th = 2 * np.pi * k / n_b + np.pi / 2
            xc = R + r_bar_ring * np.cos(th)
            yc = R + r_bar_ring * np.sin(th)
            ax.add_patch(MCircle((xc, yc), r_b, facecolor=_C_BT,
                                  edgecolor='black', linewidth=0.5, zorder=4))
    elif rf is not None:
        ax.text(R, R, f'As\n{rf.As:.2f}cm²',
                ha='center', va='center', fontsize=8,
                color=_C_BT, fontweight='bold')

    # Cota diámetro
    ax.annotate('', xy=(2*R, R), xytext=(0, R),
                arrowprops=dict(arrowstyle='<->', color='#333', lw=0.8))
    ax.text(R, R - D * 0.07, f'D = {D*100:.0f} cm',
            ha='center', va='top', fontsize=7.5, color='#333')

    margin = D * 0.22
    ax.set_xlim(-margin, 2*R + margin * 2.5)
    ax.set_ylim(-margin, 2*R + margin)

    lines: list[tuple[str, str]] = [('Sección circ.', f'D = {D*100:.0f} cm')]
    if hasattr(sec, 'hormigon'):
        lines.append(("f'c", f"{sec.hormigon.fc} MPa"))
        lines.append(('fy',  f"{sec.acero.fy} MPa"))
    if rf is not None:
        lines.append(('---', ''))
        lines.append(('As calc', f"{rf.As:.2f} cm²"))
        if rf.As_adoptada is not None:
            lines.append(('Adoptado',
                          f"{rf.n_barras}φ{rf.phi_adoptado} = {rf.As_adoptada:.2f} cm²"))
    _panel_info(ax_info, lines)

    if titulo:
        fig.suptitle(titulo, fontsize=10, fontweight='bold')
    fig.tight_layout()
    return fig
