"""
Diagramas de diseño — matplotlib.

Funciones:
  graficar_interaccion_PM(diagrama, Pu=None, Mu=None, titulo=None) → Figure
  graficar_variantes_flexion(rset, n_mostrar=8)                     → Figure
  graficar_variantes_corte(rset, n_mostrar=8)                       → Figure
  graficar_viga(resultado_viga)                                      → Figure
  graficar_viga_continua(resultado)                                  → Figure
"""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ── Diagrama de interacción P-M ───────────────────────────────────────────────

def graficar_interaccion_PM(
    diagrama,
    Pu: Optional[float] = None,
    Mu: Optional[float] = None,
    titulo: Optional[str] = None,
) -> plt.Figure:
    """
    Dibuja el diagrama de interacción P-M.

    diagrama : DiagramaInteraccion (de hormigon.columnas).
    Pu, Mu   : Punto de demanda [kN, kNm] — si se dan, se marca con verificación.
    """
    pts = diagrama.puntos

    # Curva nominal y de diseño
    Mn_nom  = [p.Mn     for p in pts]
    Pn_nom  = [p.Pn     for p in pts]
    Mn_dis  = [p.phi_Mn for p in pts]
    Pn_dis  = [p.phi_Pn for p in pts]

    fig, ax = plt.subplots(figsize=(6.5, 7.5), layout='constrained')

    # Nominal
    ax.plot(Mn_nom, Pn_nom, color='#AAAAAA', lw=1.2, ls='--',
            label='Curva nominal (Pn, Mn)')

    # Diseño
    ax.plot(Mn_dis, Pn_dis, color='#1F4E79', lw=2.0,
            label='Curva de diseño (φPn, φMn)')

    # Techo φPn_max
    phi_Pn_max = diagrama.phi_Pn_max
    ax.axhline(phi_Pn_max, color='#1F4E79', lw=1.0, ls=':',
               label=f'φPn_max = {phi_Pn_max:.0f} kN')

    # Punto de balance
    ax.plot(diagrama.phi_Mn_bal, diagrama.phi_Pn_bal,
            's', color='#2E75B6', markersize=7, zorder=5,
            label=(f'Balance  φMb={diagrama.phi_Mn_bal:.0f} kNm  '
                   f'φPb={diagrama.phi_Pn_bal:.0f} kN'))

    # Eje horizontal (Pn = 0)
    ax.axhline(0, color='#666', lw=0.6)

    # Punto de demanda
    if Pu is not None and Mu is not None:
        dentro = diagrama.contiene(Pu, Mu)
        color_pt = '#00B050' if dentro else '#C00000'
        check    = '✓' if dentro else '✗'
        ax.plot(Mu, Pu, 'o', color=color_pt, markersize=9, zorder=6,
                label=f'Demanda ({Mu:.0f} kNm, {Pu:.0f} kN)  {check}')
        ax.annotate(f'({Mu:.0f}, {Pu:.0f})', (Mu, Pu), xytext=(7, 7),
                    textcoords='offset points', fontsize=7.5, color=color_pt,
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1))

    # Límite entre zonas: por encima de φPb controla compresión; por debajo, tracción/transición
    ax.plot([0, diagrama.phi_Mn_bal], [diagrama.phi_Pn_bal] * 2, color='#999', lw=0.8, ls='--',
            label='φPb: límite compresión / tracción')

    ax.set_xlabel('φMn  [kNm]', fontsize=9)
    ax.set_ylabel('φPn  [kN]', fontsize=9)
    ax.set_title(titulo or f'Diagrama de interacción P-M  ({diagrama.tipo})',
                 fontsize=10)
    ax.legend(fontsize=7.5, loc='upper right')
    ax.grid(True, alpha=0.25)
    ax.tick_params(labelsize=8)

    return fig


# ── Variantes de flexión ──────────────────────────────────────────────────────

def graficar_variantes_flexion(rset, n_mostrar: int = 8) -> plt.Figure:
    """
    Gráfico comparativo de variantes de armado en flexión.

    rset : ResultadoSetFlexion (de hormigon.flexion.dimensionar_flexion_variantes).
    """
    variantes = rset.variantes[:n_mostrar]
    if not variantes:
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.text(0.5, 0.5, 'Sin variantes válidas', ha='center', va='center',
                transform=ax.transAxes, fontsize=10)
        ax.axis('off')
        return fig

    labels  = [f'[{v.rank}] {v.n}φ{v.phi}' for v in variantes]
    As_vals = [v.As for v in variantes]

    fig_h = max(3.5, len(variantes) * 0.55 + 1.8)
    fig, (ax_bar, ax_tab) = plt.subplots(
        1, 2, figsize=(9, fig_h),
        gridspec_kw={'width_ratios': [2, 3]},
    )

    # Barras horizontales (ranking de menor a mayor As → mejor arriba)
    bars = ax_bar.barh(labels[::-1], As_vals[::-1],
                       color='#1F6AA5', edgecolor='white', height=0.6)
    ax_bar.axvline(rset.As_requerida, color='#C00000', lw=1.5, ls='--',
                   label=f'As req = {rset.As_requerida:.2f} cm²')
    ax_bar.set_xlabel('As [cm²]', fontsize=8)
    ax_bar.set_title(f'Mu = {rset.Mu:.0f} kNm', fontsize=9)
    ax_bar.legend(fontsize=7.5)
    ax_bar.tick_params(labelsize=7.5)
    for bar, v in zip(bars[::-1], variantes):
        ax_bar.text(bar.get_width() + As_vals[-1] * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{v.As:.2f}', va='center', ha='left', fontsize=7)

    # Tabla comparativa
    ax_tab.axis('off')
    col_headers = ['Rank', 'Barras', 'As [cm²]', 'φMn [kNm]', 's libre [mm]']
    rows = [
        [f'[{v.rank}]', f'{v.n}φ{v.phi}',
         f'{v.As:.2f}', f'{v.phi_Mn:.1f}', f'{v.separacion:.0f}']
        for v in variantes
    ]
    tbl = ax_tab.table(cellText=rows, colLabels=col_headers,
                       loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.30)
    ax_tab.set_title(f'As requerida = {rset.As_requerida:.2f} cm²', fontsize=8.5)

    fig.suptitle(f'Variantes de armado — Mu = {rset.Mu:.0f} kNm', fontsize=10)
    fig.tight_layout()
    return fig


# ── Variantes de corte ────────────────────────────────────────────────────────

def graficar_variantes_corte(rset, n_mostrar: int = 8) -> plt.Figure:
    """
    Gráfico comparativo de variantes de estribado.

    rset : ResultadoSetCorte (de hormigon.corte.calcular_corte_variantes).
    """
    variantes = rset.variantes[:n_mostrar]
    if not variantes:
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.text(0.5, 0.5, 'Sin variantes válidas', ha='center', va='center',
                transform=ax.transAxes, fontsize=10)
        ax.axis('off')
        return fig

    labels   = [f'[{v.rank}] {v.n_ramas}φ{v.phi} c/{v.s*100:.0f}cm' for v in variantes]
    sep_vals = [v.s * 100 for v in variantes]

    fig_h = max(3.5, len(variantes) * 0.55 + 1.8)
    fig, (ax_bar, ax_tab) = plt.subplots(
        1, 2, figsize=(9, fig_h),
        gridspec_kw={'width_ratios': [2, 3]},
    )

    bars = ax_bar.barh(labels[::-1], sep_vals[::-1],
                       color='#2E86AB', edgecolor='white', height=0.6)
    ax_bar.axvline(rset.s_maximo * 100, color='#C00000', lw=1.5, ls='--',
                   label=f's_max = {rset.s_maximo*100:.0f} cm')
    ax_bar.set_xlabel('Separación [cm]', fontsize=8)
    ax_bar.set_title(f'Vu = {rset.Vu:.0f} kN', fontsize=9)
    ax_bar.legend(fontsize=7.5)
    ax_bar.tick_params(labelsize=7.5)
    for bar, v in zip(bars[::-1], variantes):
        ax_bar.text(bar.get_width() + sep_vals[-1] * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{v.s*100:.0f}cm', va='center', ha='left', fontsize=7)

    ax_tab.axis('off')
    col_headers = ['Rank', 'Estribo', 'Av/s [mm²/m]', 's [cm]', 'φVn [kN]']
    rows = [
        [f'[{v.rank}]', f'{v.n_ramas}φ{v.phi}',
         f'{v.Avs:.0f}', f'{v.s*100:.0f}', f'{v.phi_Vn:.1f}']
        for v in variantes
    ]
    tbl = ax_tab.table(cellText=rows, colLabels=col_headers,
                       loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.30)
    ax_tab.set_title(f'Av/s req = {rset.Avs_requerido:.0f} mm²/m', fontsize=8.5)

    fig.suptitle(f'Variantes de estribado — Vu = {rset.Vu:.0f} kN', fontsize=10)
    fig.tight_layout()
    return fig


# ── Diagramas M y V para vigas isostáticas ────────────────────────────────────

def graficar_viga(resultado) -> plt.Figure:
    """
    Figura de tres paneles para VigaSimple o VigaVoladizo:
      • Panel superior  — esquema de carga (elevación)
      • Panel central   — diagrama M(x) [kNm]
      • Panel inferior  — diagrama V(x) [kN]
    """
    import numpy as np
    from matplotlib.patches import FancyArrow, Polygon

    r   = resultado
    L   = r.L
    x   = r.x
    M   = r.M_x
    V   = r.V_x
    wu  = r.wu
    tipo = r.tipo

    fig = plt.figure(figsize=(9, 7), layout='constrained')
    gs  = fig.add_gridspec(3, 1, height_ratios=[1, 2, 2], hspace=0.45)
    ax_esq = fig.add_subplot(gs[0])
    ax_M   = fig.add_subplot(gs[1])
    ax_V   = fig.add_subplot(gs[2])

    # ── Esquema de carga ──────────────────────────────────────────────────────
    ax_esq.set_xlim(-L * 0.12, L * 1.12)
    ax_esq.set_ylim(-0.18, 0.22)
    ax_esq.axis('off')

    # Línea del eje de la viga
    ax_esq.plot([0, L], [0, 0], 'k-', lw=4, solid_capstyle='butt')

    # Apoyo izquierdo
    if tipo == 'voladizo':
        # Empotramiento: rectángulo rayado
        rect = plt.Rectangle((-L * 0.04, -0.08), L * 0.04, 0.08,
                              color='#888', zorder=3)
        ax_esq.add_patch(rect)
        ax_esq.plot([-L * 0.04, 0], [-0.08, -0.08], 'k-', lw=1)
    else:
        # Apoyo simple: triángulo
        tri_L = Polygon([[0, 0], [-L*0.04, -0.10], [L*0.04, -0.10]],
                        closed=True, color='#555', zorder=3)
        ax_esq.add_patch(tri_L)
        ax_esq.plot([-L*0.05, L*0.05], [-0.10, -0.10], 'k-', lw=1.5)

    # Apoyo derecho (solo para viga simple)
    if tipo == 'simple':
        tri_R = Polygon([[L, 0], [L-L*0.04, -0.10], [L+L*0.04, -0.10]],
                        closed=True, color='#555', zorder=3)
        ax_esq.add_patch(tri_R)
        ax_esq.plot([L-L*0.05, L+L*0.05], [-0.10, -0.10], 'k-', lw=1.5)

    # Flechas de carga distribuida
    if wu > 0:
        n_flechas = max(6, int(L / 0.4))
        for xi in np.linspace(0.05 * L, 0.95 * L, n_flechas):
            ax_esq.annotate('', xy=(xi, 0.01), xytext=(xi, 0.16),
                            arrowprops=dict(arrowstyle='->', color='#C00000', lw=1.2))
        # Línea superior
        ax_esq.plot([0.02 * L, 0.98 * L], [0.16, 0.16], color='#C00000', lw=1.2)
        ax_esq.text(L / 2, 0.19, f'wu = {wu:.2f} kN/m',
                    ha='center', va='bottom', fontsize=8, color='#C00000')

    # Cota de luz
    ax_esq.annotate('', xy=(L, -0.14), xytext=(0, -0.14),
                    arrowprops=dict(arrowstyle='<->', color='#333', lw=0.8))
    ax_esq.text(L / 2, -0.17, f'L = {L:.2f} m',
                ha='center', va='top', fontsize=8, color='#333')

    # ── Diagrama M ───────────────────────────────────────────────────────────
    ax_M.axhline(0, color='#666', lw=0.8)
    ax_M.plot(x, M, color='#1F4E79', lw=2.0)
    ax_M.fill_between(x, 0, M,
                      where=(M >= 0), color='#4472C4', alpha=0.25, label='M+')
    ax_M.fill_between(x, 0, M,
                      where=(M < 0),  color='#C00000', alpha=0.20, label='M−')
    # Anotación del valor extremo
    idx_max = int(np.argmax(np.abs(M)))
    ax_M.annotate(f'{M[idx_max]:.1f} kNm',
                  xy=(x[idx_max], M[idx_max]),
                  xytext=(x[idx_max] + L * 0.05, M[idx_max]),
                  fontsize=8, color='#1F4E79',
                  arrowprops=dict(arrowstyle='->', color='#1F4E79', lw=0.8))
    ax_M.set_ylabel('M  [kNm]', fontsize=8)
    ax_M.set_xlim(0, L)
    ax_M.tick_params(labelsize=7.5)
    ax_M.grid(True, alpha=0.25)
    ax_M.legend(fontsize=7.5, loc='best')

    # ── Diagrama V ───────────────────────────────────────────────────────────
    ax_V.axhline(0, color='#666', lw=0.8)
    ax_V.plot(x, V, color='#2E75B6', lw=2.0)
    ax_V.fill_between(x, 0, V,
                      where=(V >= 0), color='#2E75B6', alpha=0.25, label='V+')
    ax_V.fill_between(x, 0, V,
                      where=(V < 0),  color='#FF8C00', alpha=0.20, label='V−')
    # Anotaciones de extremos
    ax_V.annotate(f'{V[0]:.1f} kN', xy=(x[0], V[0]),
                  xytext=(x[0] + L * 0.06, V[0]),
                  fontsize=8, color='#2E75B6',
                  arrowprops=dict(arrowstyle='->', color='#2E75B6', lw=0.8))
    ax_V.annotate(f'{V[-1]:.1f} kN', xy=(x[-1], V[-1]),
                  xytext=(x[-1] - L * 0.06, V[-1]),
                  fontsize=8, color='#2E75B6', ha='right',
                  arrowprops=dict(arrowstyle='->', color='#2E75B6', lw=0.8))
    ax_V.set_xlabel('x  [m]', fontsize=8)
    ax_V.set_ylabel('V  [kN]', fontsize=8)
    ax_V.set_xlim(0, L)
    ax_V.tick_params(labelsize=7.5)
    ax_V.grid(True, alpha=0.25)
    ax_V.legend(fontsize=7.5, loc='best')

    tipo_str = 'Viga simple' if tipo == 'simple' else 'Viga en voladizo'
    rf  = r.resultado_flex
    check = '✓' if rf.verifica else '✗'
    fig.suptitle(
        f'{tipo_str}  —  L={L:.2f} m  wu={wu:.2f} kN/m  '
        f'|  Mu={r.Mu:.1f} kNm  φMn={rf.phi_Mn:.1f} kNm  {check}',
        fontsize=9,
    )
    return fig


# ── Tabla de secciones críticas — viga continua ───────────────────────────────

def _grafico_secciones_criticas(
    titulo: str,
    nombres: list[str],
    Mu: list[float],
    phiMn: list[float],
    colores: list[str],
    unidad: str,
    col_headers: list[str],
    rows: list[list[str]],
    col_widths: list[float],
    leyenda: list[tuple[str, str]],
) -> plt.Figure:
    """
    Figura común para vigas continuas y losas: barras Mu vs φMn por sección
    crítica (arriba) y tabla de resultados a todo el ancho (abajo).
    """
    from matplotlib.patches import Patch

    fig = plt.figure(figsize=(9.5, 6.0))
    fig.set_layout_engine('none')     # la tabla no es compatible con tight_layout
    gs = fig.add_gridspec(2, 1, height_ratios=[1.35, 1], hspace=0.38,
                          left=0.24, right=0.98, top=0.86, bottom=0.03)
    ax_bar = fig.add_subplot(gs[0])
    ax_tab = fig.add_subplot(gs[1])

    # Barras agrupadas (sin superposición); se omiten secciones con Mu = 0
    idx = [k for k, m in enumerate(Mu) if m > 1e-6]
    n = len(idx)
    y = list(range(n))[::-1]          # primera sección arriba
    hb = 0.36
    for yy, k in zip(y, idx):
        ax_bar.barh(yy + hb / 2, Mu[k], height=hb, color=colores[k], alpha=0.85)
        ax_bar.barh(yy - hb / 2, phiMn[k], height=hb, color='#70AD47', alpha=0.85)
        ratio = Mu[k] / phiMn[k] if phiMn[k] > 0 else float('inf')
        ax_bar.text(max(Mu[k], phiMn[k]) * 1.01, yy, f' Mu/φMn = {ratio:.2f}',
                    va='center', fontsize=7.5, color='#222')
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels([nombres[k] for k in idx], fontsize=7.5)
    xmax = max([max(Mu[k], phiMn[k]) for k in idx], default=1.0)
    ax_bar.set_xlim(0, xmax * 1.38)
    ax_bar.set_xlabel(f'Momento [{unidad}]', fontsize=8)
    ax_bar.grid(True, axis='x', alpha=0.3)
    ax_bar.tick_params(labelsize=7.5)
    ax_bar.legend(handles=[Patch(color=c, alpha=0.85, label=l) for l, c in leyenda]
                  + [Patch(color='#70AD47', alpha=0.85, label='φMn')],
                  fontsize=7.5, loc='lower right', bbox_to_anchor=(1.0, 1.0),
                  ncol=len(leyenda) + 1, frameon=False)

    # Tabla
    ax_tab.axis('off')
    tbl = ax_tab.table(cellText=rows, colLabels=col_headers, colWidths=col_widths,
                       cellLoc='center', bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    for (fila, _col), celda in tbl.get_celld().items():
        celda.set_edgecolor('#808080')
        if fila == 0:
            celda.set_facecolor('#D8D8D8')
            celda.set_text_props(weight='bold')
        else:
            celda.set_facecolor('#F4F4F4' if fila % 2 else '#FFFFFF')

    fig.suptitle(titulo, fontsize=9, y=0.975)
    return fig


def graficar_viga_continua(resultado) -> plt.Figure:
    """Secciones críticas de una VigaContinua: Mu vs φMn + tabla de armaduras."""
    r    = resultado
    secs = r.secciones
    rows = [
        [s.nombre,
         '+' if s.signo == 'positivo' else '−',
         f'{s.Mu:.2f}',
         f'{s.resultado_flex.As:.2f}',
         f'{s.resultado_flex.phi_Mn:.2f}',
         '✓' if s.resultado_flex.verifica else '✗']
        for s in secs
    ]
    return _grafico_secciones_criticas(
        titulo=(f'Viga continua — ln={r.ln:.2f} m  wu={r.wu:.2f} kN/m  '
                f'({r.n_tramos} tramos, extremo: {r.extremo})'),
        nombres=[s.nombre for s in secs],
        Mu=[s.Mu for s in secs],
        phiMn=[s.resultado_flex.phi_Mn for s in secs],
        colores=['#4472C4' if s.signo == 'positivo' else '#C00000' for s in secs],
        unidad='kNm',
        col_headers=['Sección', 'M', 'Mu [kNm]', 'As [cm²]', 'φMn [kNm]', 'OK'],
        rows=rows,
        col_widths=[0.40, 0.07, 0.15, 0.14, 0.16, 0.08],
        leyenda=[('Mu (+)', '#4472C4'), ('Mu (−)', '#C00000')],
    )


# ── Losa en 1 dirección ───────────────────────────────────────────────────────

def graficar_losa_1dir(resultado) -> plt.Figure:
    """Secciones críticas de losa 1 dir.: Mu vs φMn + tabla con temperatura y corte."""
    r    = resultado
    secs = r.secciones
    rows = [
        [s.nombre,
         f'{s.Mu:.2f}', f'{s.As:.2f}',
         f'{s.s_max*100:.0f}', f'{s.phi_Mn:.2f}',
         '✓' if s.verifica else '✗']
        for s in secs
    ]
    rows.append(['Armadura de temperatura', '—', f'{r.As_temp:.2f}',
                 f'{r.s_temp_max*100:.0f}', '—', ''])
    rows.append([f'Corte  Vu={r.Vu_max:.1f} / φVc={r.phi_Vc:.1f} kN/m', '—', '—', '—', '—',
                 '✓' if r.verifica_corte else '✗'])
    return _grafico_secciones_criticas(
        titulo=(f'Losa 1 dirección — h={r.h*100:.0f} cm  ln={r.ln:.2f} m  '
                f'wu={r.wu:.2f} kN/m²  ({r.n_tramos} tramos)'),
        nombres=[s.nombre for s in secs],
        Mu=[s.Mu for s in secs],
        phiMn=[s.phi_Mn for s in secs],
        colores=['#4472C4' if 'M+' in s.nombre else '#C00000' for s in secs],
        unidad='kNm/m',
        col_headers=['Sección', 'Mu [kNm/m]', 'As [cm²/m]', 's_max [cm]', 'φMn [kNm/m]', 'OK'],
        rows=rows,
        col_widths=[0.40, 0.13, 0.13, 0.12, 0.14, 0.08],
        leyenda=[('Mu (+)', '#4472C4'), ('Mu (−)', '#C00000')],
    )


# ── Losa 2 direcciones (DDM) ─────────────────────────────────────────────────

def graficar_losa_2dir(resultado) -> plt.Figure:
    """Secciones críticas de losa en 2 direcciones (DDM art. 13.6)."""
    r    = resultado
    secs = [s for s in r.secciones if s.Mu > 1e-6]
    rows = [
        [s.nombre, s.direccion,
         f'{s.Mu:.2f}', f'{s.As:.2f}',
         f'{s.s_max*100:.0f}', f'{s.phi_Mn:.2f}',
         '✓' if s.verifica else '✗']
        for s in secs
    ]
    rows.append(['Armadura de temperatura', '—', '—', f'{r.As_temp:.2f}',
                 f'{r.s_temp_max*100:.0f}', '—', ''])
    return _grafico_secciones_criticas(
        titulo=(f'Losa 2 direcciones DDM — h={r.h*100:.0f} cm  '
                f'la={r.la:.2f} m  lb={r.lb:.2f} m  m={r.m:.2f}  wu={r.wu:.2f} kN/m²'),
        nombres=[s.nombre for s in secs],
        Mu=[s.Mu for s in secs],
        phiMn=[s.phi_Mn for s in secs],
        colores=['#4472C4' if s.direccion == 'a' else '#E87800' for s in secs],
        unidad='kNm/m',
        col_headers=['Sección', 'Dir', 'Mu [kNm/m]', 'As [cm²/m]', 's_max [cm]',
                     'φMn [kNm/m]', 'OK'],
        rows=rows,
        col_widths=[0.36, 0.06, 0.13, 0.12, 0.11, 0.14, 0.08],
        leyenda=[('Mu dir. a (corta)', '#4472C4'), ('Mu dir. b (larga)', '#E87800')],
    )


# ── Torsión + corte combinados ────────────────────────────────────────────────

def graficar_torsion(resultado) -> plt.Figure:
    """Resumen visual del cálculo de torsión + corte."""
    r = resultado
    fig, axes = plt.subplots(1, 2, figsize=(9, 5))

    # Panel izq: barras tensiones vs límites
    ax = axes[0]
    categorias = ['τ combinado\nvs τ límite']
    vals_act = [r.tau_combinado]
    vals_lim = [r.tau_limite]
    x = [0]
    w = 0.35
    ax.bar([xi - w/2 for xi in x], vals_act, w, color='#C00000', alpha=0.75, label='Actuante')
    ax.bar([xi + w/2 for xi in x], vals_lim, w, color='#70AD47', alpha=0.75, label='Límite φ')
    ax.set_xticks(x)
    ax.set_xticklabels(categorias, fontsize=8)
    ax.set_ylabel('Tensión [MPa]', fontsize=8)
    ok_str = '✓' if r.verifica_combinado else '✗'
    ax.set_title(f'Verificación combinada {ok_str}', fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, axis='y', alpha=0.3)
    ax.tick_params(labelsize=7.5)

    # Panel der: tabla de armadura
    ax2 = axes[1]
    ax2.axis('off')
    if r.despreciable:
        ax2.text(0.5, 0.5, 'Tu < Tu_umbral\nTorsión despreciable',
                 ha='center', va='center', transform=ax2.transAxes,
                 fontsize=11, color='#70AD47')
    else:
        rows = [
            ['Tu umbral', f'{r.Tu_umbral:.2f} kNm'],
            ['Tu diseño', f'{r.Tu:.2f} kNm'],
            ['At/s (torsión)', f'{r.At_s:.0f} mm²/m'],
            ['Av/s (corte)', f'{r.Av_s:.0f} mm²/m'],
            ['Avt/s total/rama', f'{r.Avt_s:.0f} mm²/m'],
            ['Al longitudinal', f'{r.Al:.2f} cm²'],
            ['Al mínimo', f'{r.Al_min:.2f} cm²'],
        ]
        tbl = ax2.table(cellText=rows, colLabels=['Parámetro', 'Valor'],
                        loc='center', cellLoc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8.5)
        tbl.scale(1, 1.5)
    ax2.set_title('Armadura requerida', fontsize=9)

    fig.suptitle(
        f'Torsión + Corte — Tu={r.Tu:.2f} kNm  Vu={r.Vu:.1f} kN  '
        f'θ={r.theta_deg:.0f}°',
        fontsize=9,
    )
    fig.tight_layout()
    return fig


# ── Base centrada ─────────────────────────────────────────────────────────────

def graficar_base(resultado) -> plt.Figure:
    """Planta esquemática de la base + tabla de verificaciones."""
    import numpy as np
    r = resultado
    fig, (ax_planta, ax_tab) = plt.subplots(
        1, 2, figsize=(9.5, 5), gridspec_kw={'width_ratios': [1, 1.25]})

    # Planta
    ax = ax_planta
    ax.set_aspect('equal')
    ax.add_patch(plt.Rectangle((0, 0), r.B, r.L, fill=True,
                               facecolor='#DCDCDC', edgecolor='#404040', lw=1.5))
    # Columna
    col_x = (r.B - r.bc) / 2
    col_y = (r.L - r.hc) / 2
    ax.add_patch(plt.Rectangle((col_x, col_y), r.bc, r.hc,
                               facecolor='#888', edgecolor='#222', lw=1.5))
    # Cota B
    ax.annotate('', xy=(r.B, -r.L*0.10), xytext=(0, -r.L*0.10),
                arrowprops=dict(arrowstyle='<->', color='#333', lw=0.8))
    ax.text(r.B/2, -r.L*0.14, f'B = {r.B:.2f} m',
            ha='center', va='top', fontsize=8)
    # Cota L
    ax.annotate('', xy=(r.B + r.B*0.10, r.L), xytext=(r.B + r.B*0.10, 0),
                arrowprops=dict(arrowstyle='<->', color='#333', lw=0.8))
    ax.text(r.B + r.B*0.14, r.L/2, f'L = {r.L:.2f} m',
            ha='left', va='center', fontsize=8, rotation=90)
    ax.set_xlim(-r.B*0.05, r.B*1.30)
    ax.set_ylim(-r.L*0.20, r.L*1.10)
    ax.axis('off')
    ax.set_title(f'Planta  {r.B:.2f}×{r.L:.2f} m  h={r.h_f*100:.0f} cm', fontsize=9)

    # Tabla de verificaciones
    ax2 = ax_tab
    ax2.axis('off')
    rows = [
        ['Suelo',       f'{r.q_servicio:.1f} kN/m²', f'≤ {r.q_adm:.0f}', '✓' if r.verifica_suelo else '✗'],
        ['Punzonamiento', f'Vu={r.Vu_punch:.1f} kN', f'φVc={r.phi_Vc_punch:.1f}', '✓' if r.verifica_punch else '✗'],
        ['Corte 1-dir (L)', f'Vu={r.Vu_1way_L:.1f} kN', f'φVc={r.phi_Vc_1way_L:.1f}', '✓' if r.verifica_1way else '✗'],
        ['Flex. dir-L', f'As={r.As_L:.1f} cm²', f'φMn={r.phi_Mn_L:.1f} kNm', '✓' if r.verifica_flex_L else '✗'],
        ['Flex. dir-B', f'As={r.As_B:.1f} cm²', f'φMn={r.phi_Mn_B:.1f} kNm', '✓' if r.verifica_flex_B else '✗'],
    ]
    tbl = ax2.table(cellText=rows,
                    colLabels=['Verificación', 'Actuante', 'Resistente', 'OK'],
                    colWidths=[0.30, 0.28, 0.32, 0.10],
                    cellLoc='center', bbox=[0, 0.22, 1, 0.56])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    ax2.set_title('Verificaciones', fontsize=9)

    fig.suptitle(
        f'Base centrada — Pu={r.Pu:.0f} kN  columna {r.bc*100:.0f}×{r.hc*100:.0f} cm',
        fontsize=9,
    )
    fig.tight_layout()
    return fig


# ── Ménsula corta (biela-tirante) ─────────────────────────────────────────────

def graficar_mensula(resultado) -> plt.Figure:
    """Esquema del modelo biela-tirante de una ménsula corta."""
    import numpy as np
    r = resultado

    fig, (ax_esq, ax_tab) = plt.subplots(
        1, 2, figsize=(9.5, 5), gridspec_kw={'width_ratios': [1.15, 1]})

    # Esquema geométrico: cara de la columna en x=0, borde inferior de la ménsula en y=0
    ax = ax_esq
    ax.set_aspect('equal')
    ax.axis('off')

    d, a = r.d, r.a
    h  = 1.12 * d                 # altura de la ménsula en la cara
    L  = a + 0.35 * d             # vuelo de la ménsula
    bc = 0.60 * d                 # ancho de columna (esquemático)

    # Columna
    ax.add_patch(plt.Rectangle((-bc, -0.9 * d), bc, h + 1.7 * d,
                               facecolor='#C8C8C8', edgecolor='#404040', lw=1.5))
    # Ménsula (borde inferior inclinado)
    ax.add_patch(plt.Polygon([(0, 0), (L, 0.5 * h), (L, h), (0, h)], closed=True,
                             facecolor='#DCDCDC', edgecolor='#404040', lw=1.5))
    # Placa de apoyo
    ax.add_patch(plt.Rectangle((a - 0.08 * d, h), 0.16 * d, 0.04 * d,
                               facecolor='#404040', edgecolor='#404040'))

    # Tirante: horizontal a la altura d, anclado dentro de la columna
    ax.plot([-0.8 * bc, L - 0.06 * d], [d, d], color='#C00000', lw=2.6, solid_capstyle='butt')
    ax.text(-0.5 * bc, d + 0.07 * d, f'T = {r.F_tirante_principal:.1f} kN',
            ha='center', va='bottom', fontsize=7.5, color='#C00000',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.2))

    # Biela: del nudo de carga al nudo inferior en la cara de la columna
    ax.plot([a, 0], [d, 0], color='#1F4E79', lw=3.0, alpha=0.9)
    ang = np.arctan2(d, a)
    ox, oy = 0.13 * d * np.sin(ang), -0.13 * d * np.cos(ang)
    ax.text(a / 2 + ox, d / 2 + oy,
            f'C = {r.F_biela:.1f} kN\nθ = {r.theta_deg:.1f}°',
            ha='left', va='top', fontsize=7.5, color='#1F4E79',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.2))

    # Nudos
    for x, y in [(a, d), (0, 0)]:
        ax.plot(x, y, 'o', ms=6, color='#222', zorder=5)

    # Carga Vu
    ax.annotate('', xy=(a, h + 0.05 * d), xytext=(a, h + 0.55 * d),
                arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.6))
    ax.text(a + 0.05 * d, h + 0.45 * d, f'Vu = {r.Vu:.1f} kN',
            fontsize=8, color='#333', va='center')

    # Cotas a y d
    yc = h + 0.22 * d
    ax.annotate('', xy=(a, yc), xytext=(0, yc),
                arrowprops=dict(arrowstyle='<->', color='#555', lw=0.8))
    ax.text(a / 2, yc + 0.03 * d, f'a = {a*100:.0f} cm',
            ha='center', va='bottom', fontsize=7.5, color='#555')
    xc = L + 0.15 * d
    ax.annotate('', xy=(xc, d), xytext=(xc, 0),
                arrowprops=dict(arrowstyle='<->', color='#555', lw=0.8))
    ax.text(xc + 0.04 * d, d / 2, f'd = {d*100:.0f} cm',
            ha='left', va='center', fontsize=7.5, color='#555', rotation=90)

    ax.set_xlim(-bc - 0.1 * d, xc + 0.25 * d)
    ax.set_ylim(-0.95 * d, h + 0.85 * d)
    ok_str = '✓' if r.verifica else '✗'
    ax.set_title(f'Modelo biela-tirante  {ok_str}', fontsize=9)

    # Tabla
    ax2 = ax_tab
    ax2.axis('off')
    rows = [
        ['Vu', f'{r.Vu:.1f} kN'],
        ['a/d', f'{r.a/r.d:.3f}'],
        ['θ biela', f'{r.theta_deg:.1f}°'],
        ['F biela', f'{r.F_biela:.1f} kN'],
        ['F tirante', f'{r.F_tirante_principal:.1f} kN'],
        ['As principal', f'{r.As_principal:.2f} cm²'],
        ['As total', f'{r.As_total:.2f} cm²'],
        ['As mín (11.9.5)', f'{r.As_min:.2f} cm²'],
        ['As a disponer', f'{r.As_adoptar:.2f} cm²'],
        ['Ah estribos (11.9.4)', f'{r.Ah:.2f} cm²'],
        ['σ biela', f'{r.sigma_biela:.2f} MPa'],
        ['φ·fce', f'{r.phi_fce:.2f} MPa'],
        ['Biela OK', '✓' if r.verifica_biela else '✗'],
    ]
    tbl = ax2.table(cellText=rows, colLabels=['Parámetro', 'Valor'],
                    loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.35)
    ax2.set_title('Resultados', fontsize=9)

    fig.suptitle(
        f'Ménsula corta — Vu={r.Vu:.1f} kN  a={r.a*100:.0f} cm  d={r.d*100:.0f} cm',
        fontsize=9,
    )
    fig.tight_layout()
    return fig
