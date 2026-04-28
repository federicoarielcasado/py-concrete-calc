"""
Definición de temas visuales de la aplicación.

Cada tema hereda la estructura Win98 (biseles, tipografía, layouts)
pero cambia la paleta de acento, el sidebar y los colores del panel CRT.

Temas disponibles:
  BM — Black Mesa    (HL1, naranja HEV)
  BS — Blue Shift    (expansión Blue Shift, azul seguridad)
  OF — Opposing Force (expansión OpFor, verde militar)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tema:
    nombre:     str
    codigo:     str   # 2 letras para el botón del sidebar

    # ── Base ──────────────────────────────────────────────────────────────
    fondo_base:    str   # fondo general de widgets
    fondo_marcos:  str   # frames y contenedores secundarios (ligeramente más oscuro)

    # ── Sidebar ───────────────────────────────────────────────────────────
    sidebar_fondo:  str
    sidebar_logo:   str   # color del texto "CIRSOC 201-2005"

    # ── Botones de módulo (sidebar) ───────────────────────────────────────
    btn_mod_normal: str
    btn_mod_light:  str   # borde claro (arriba / izquierda)
    btn_mod_dark:   str   # borde oscuro (abajo / derecha)

    # ── Botón de acción principal ─────────────────────────────────────────
    btn_act_normal: str
    btn_act_light:  str
    btn_act_dark:   str
    btn_act_texto:  str

    # ── Barra de título del módulo ────────────────────────────────────────
    titulo_fondo:   str
    titulo_texto:   str

    # ── Status bar ────────────────────────────────────────────────────────
    status_fondo:   str
    status_texto:   str

    # ── Panel CRT (colores HTML, no QSS) ──────────────────────────────────
    crt_fondo:      str
    crt_verde:      str   # texto normal / resultado OK
    crt_ambar:      str   # encabezados / advertencias
    crt_rojo:       str   # errores / alertas
    crt_gris:       str   # separadores / texto inactivo


# ── BLACK MESA ────────────────────────────────────────────────────────────────
# HEV suit amber, dark ops corridors. The classic.

BLACK_MESA = Tema(
    nombre    = 'Black Mesa',
    codigo    = 'BM',
    fondo_base    = '#C0C0C0',
    fondo_marcos  = '#A8A8A8',
    sidebar_fondo = '#404040',
    sidebar_logo  = '#FFA500',
    btn_mod_normal = '#CC7722',
    btn_mod_light  = '#FFCC88',
    btn_mod_dark   = '#884400',
    btn_act_normal = '#D08000',
    btn_act_light  = '#FFD080',
    btn_act_dark   = '#805000',
    btn_act_texto  = '#000000',
    titulo_fondo   = '#000080',
    titulo_texto   = '#FFFFFF',
    status_fondo   = '#404040',
    status_texto   = '#00CC00',
    crt_fondo  = '#000000',
    crt_verde  = '#00FF00',
    crt_ambar  = '#FFAA00',
    crt_rojo   = '#FF3C3C',
    crt_gris   = '#606060',
)

# ── BLUE SHIFT ────────────────────────────────────────────────────────────────
# Barney Calhoun, security blues. Lambda Complex access terminals.

BLUE_SHIFT = Tema(
    nombre    = 'Blue Shift',
    codigo    = 'BS',
    fondo_base    = '#C4C8CC',
    fondo_marcos  = '#ACBAC4',
    sidebar_fondo = '#1A2A40',
    sidebar_logo  = '#66AAFF',
    btn_mod_normal = '#2A5599',
    btn_mod_light  = '#88AADD',
    btn_mod_dark   = '#112255',
    btn_act_normal = '#1A44AA',
    btn_act_light  = '#6699DD',
    btn_act_dark   = '#0A2266',
    btn_act_texto  = '#FFFFFF',
    titulo_fondo   = '#102060',
    titulo_texto   = '#AACCFF',
    status_fondo   = '#1A2A40',
    status_texto   = '#00AADD',
    crt_fondo  = '#000811',
    crt_verde  = '#00CCFF',
    crt_ambar  = '#FFCC44',
    crt_rojo   = '#FF4444',
    crt_gris   = '#334455',
)

# ── OPPOSING FORCE ────────────────────────────────────────────────────────────
# Adrian Shephard, HECU. Field terminals. Military olive drab.

OPPOSING_FORCE = Tema(
    nombre    = 'Opposing Force',
    codigo    = 'OF',
    fondo_base    = '#B4BCA0',
    fondo_marcos  = '#9EA898',
    sidebar_fondo = '#1E2A14',
    sidebar_logo  = '#AABB88',
    btn_mod_normal = '#4A5E30',
    btn_mod_light  = '#889966',
    btn_mod_dark   = '#243018',
    btn_act_normal = '#3A5020',
    btn_act_light  = '#708050',
    btn_act_dark   = '#1A2810',
    btn_act_texto  = '#CCDDAA',
    titulo_fondo   = '#1A2A0A',
    titulo_texto   = '#AACCAA',
    status_fondo   = '#1E2A14',
    status_texto   = '#88CC44',
    crt_fondo  = '#000800',
    crt_verde  = '#88FF44',
    crt_ambar  = '#FFDD44',
    crt_rojo   = '#FF4422',
    crt_gris   = '#445533',
)

TEMAS: dict[str, Tema] = {
    'BM': BLACK_MESA,
    'BS': BLUE_SHIFT,
    'OF': OPPOSING_FORCE,
}

# ── Estado global ─────────────────────────────────────────────────────────────

_tema_activo: Tema = BLACK_MESA


def get_tema() -> Tema:
    return _tema_activo


def set_tema(codigo: str) -> Tema:
    global _tema_activo
    _tema_activo = TEMAS[codigo]
    return _tema_activo
