"""
Temas visuales de la aplicación: Claro y Oscuro.

Cada tema define la paleta de la interfaz Qt (QSS), del panel de resultados,
de las figuras matplotlib, del visor 3D y del lienzo de planta (E-09).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tema:
    nombre: str
    codigo: str
    oscuro: bool

    # ── Interfaz ──────────────────────────────────────────────────────────
    fondo:          str   # fondo general de la ventana
    superficie:     str   # grupos, campos, tablas
    superficie_alt: str   # filas alternas, hover
    borde:          str
    texto:          str
    texto_suave:    str   # subtítulos, etiquetas secundarias
    acento:         str   # botón principal, selección, foco
    acento_hover:   str
    acento_texto:   str
    error:          str   # borde de campos inválidos

    # ── Barra lateral ─────────────────────────────────────────────────────
    sidebar_fondo:  str
    sidebar_texto:  str
    sidebar_hover:  str

    # ── Panel de resultados ───────────────────────────────────────────────
    res_fondo:   str
    res_texto:   str
    res_titulo:  str
    res_ok:      str
    res_alerta:  str
    res_tenue:   str

    # ── Figuras (matplotlib / plotly) ─────────────────────────────────────
    fig_fondo:   str
    fig_ejes:    str
    fig_texto:   str
    fig_grilla:  str

    # ── Lienzo de planta (E-09) ───────────────────────────────────────────
    plano_fondo:   str
    plano_grilla:  tuple[int, int, int, int]
    plano_mayor:   tuple[int, int, int, int]
    plano_panel:   tuple[int, int, int, int]
    plano_sel:     tuple[int, int, int, int]
    plano_rotulo:  str


CLARO = Tema(
    nombre='Claro', codigo='CLARO', oscuro=False,

    fondo='#F2F4F7', superficie='#FFFFFF', superficie_alt='#F6F8FA',
    borde='#D3D9E0', texto='#1F2933', texto_suave='#5B6775',
    acento='#1F5FAD', acento_hover='#2B6FC2', acento_texto='#FFFFFF',
    error='#D64545',

    sidebar_fondo='#1F2B3A', sidebar_texto='#C5CFDA', sidebar_hover='#2C3B4E',

    res_fondo='#FAFBFC', res_texto='#1F2933', res_titulo='#1F5FAD',
    res_ok='#1E8A4C', res_alerta='#C62828', res_tenue='#8A96A3',

    fig_fondo='#FFFFFF', fig_ejes='#FAFBFC', fig_texto='#1F2933', fig_grilla='#D9DEE4',

    plano_fondo='#FFFFFF',
    plano_grilla=(31, 41, 51, 28), plano_mayor=(31, 41, 51, 70),
    plano_panel=(31, 95, 173, 30), plano_sel=(31, 95, 173, 70),
    plano_rotulo='#24435F',
)

OSCURO = Tema(
    nombre='Oscuro', codigo='OSCURO', oscuro=True,

    fondo='#15191F', superficie='#1E242C', superficie_alt='#252C35',
    borde='#36404B', texto='#E3E8EE', texto_suave='#9AA5B1',
    acento='#3D7FD1', acento_hover='#5193E0', acento_texto='#FFFFFF',
    error='#FF6B6B',

    sidebar_fondo='#0F1318', sidebar_texto='#AEB8C4', sidebar_hover='#1D242D',

    res_fondo='#11151B', res_texto='#D7DEE6', res_titulo='#6FA8F0',
    res_ok='#4CC38A', res_alerta='#FF6B6B', res_tenue='#6B7785',

    fig_fondo='#1E242C', fig_ejes='#1A1F26', fig_texto='#D7DEE6', fig_grilla='#39424D',

    plano_fondo='#161B21',
    plano_grilla=(150, 160, 175, 40), plano_mayor=(150, 160, 175, 95),
    plano_panel=(100, 150, 220, 40), plano_sel=(120, 190, 255, 80),
    plano_rotulo='#D2E1F5',
)

TEMAS: dict[str, Tema] = {t.codigo: t for t in (CLARO, OSCURO)}

# ── Estado global ─────────────────────────────────────────────────────────────

_tema_activo: Tema = CLARO


def get_tema() -> Tema:
    return _tema_activo


def set_tema(codigo: str) -> Tema:
    global _tema_activo
    _tema_activo = TEMAS[codigo]
    return _tema_activo
