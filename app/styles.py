"""
Hoja de estilos QSS parametrizada por tema.

Uso:
    from app.styles import get_stylesheet
    from app.themes import get_tema
    app.setStyleSheet(get_stylesheet(get_tema()))
"""
from __future__ import annotations

from app.themes import Tema


def _lighten(hex_color: str, amount: int = 20) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'#{min(255,r+amount):02X}{min(255,g+amount):02X}{min(255,b+amount):02X}'


def _darken(hex_color: str, amount: int = 20) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'#{max(0,r-amount):02X}{max(0,g-amount):02X}{max(0,b-amount):02X}'


def get_stylesheet(t: Tema) -> str:
    sep_color       = _lighten(t.sidebar_fondo, 30)
    btn_mod_hover   = _lighten(t.btn_mod_normal, 24)
    btn_mod_pressed = _darken(t.btn_mod_normal, 30)
    btn_act_hover   = _lighten(t.btn_act_normal, 16)

    return f"""
/* ── Base ──────────────────────────────────────────────────────────────────── */

QMainWindow, QDialog {{
    background-color: {t.fondo_base};
}}

QWidget {{
    background-color: {t.fondo_base};
    font-family: "Tahoma", "MS Sans Serif", sans-serif;
    font-size: 11px;
    color: #000000;
}}

/* ── Sidebar ────────────────────────────────────────────────────────────────── */

QWidget#sidebar {{
    background-color: {t.sidebar_fondo};
    border-right: 2px solid #202020;
}}

QLabel#sidebar_logo {{
    background-color: transparent;
    color: {t.sidebar_logo};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10px;
    font-weight: bold;
    padding: 4px 0;
}}

QWidget#sidebar_sep {{
    background-color: {sep_color};
    max-height: 1px;
    min-height: 1px;
}}

QPushButton#btn_modulo {{
    background-color: {t.btn_mod_normal};
    color: #000000;
    font-family: "Tahoma", sans-serif;
    font-size: 9px;
    font-weight: bold;
    border: 2px solid;
    border-top-color:    {t.btn_mod_light};
    border-left-color:   {t.btn_mod_light};
    border-right-color:  {t.btn_mod_dark};
    border-bottom-color: {t.btn_mod_dark};
}}

QPushButton#btn_modulo:hover {{
    background-color: {btn_mod_hover};
}}

QPushButton#btn_modulo:pressed,
QPushButton#btn_modulo:checked {{
    background-color: {btn_mod_pressed};
    border-top-color:    {t.btn_mod_dark};
    border-left-color:   {t.btn_mod_dark};
    border-right-color:  {t.btn_mod_light};
    border-bottom-color: {t.btn_mod_light};
    padding-top: 3px;
    padding-left: 3px;
}}

/* ── Botones de tema (sidebar) ──────────────────────────────────────────────── */

QPushButton#btn_tema {{
    background-color: {t.btn_mod_normal};
    color: {t.btn_act_texto};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 8px;
    font-weight: bold;
    border: 2px solid;
    border-top-color:    {t.btn_mod_light};
    border-left-color:   {t.btn_mod_light};
    border-right-color:  {t.btn_mod_dark};
    border-bottom-color: {t.btn_mod_dark};
    padding: 0;
}}

QPushButton#btn_tema:hover {{
    background-color: {btn_mod_hover};
}}

QPushButton#btn_tema:pressed {{
    border-top-color:    {t.btn_mod_dark};
    border-left-color:   {t.btn_mod_dark};
    border-right-color:  {t.btn_mod_light};
    border-bottom-color: {t.btn_mod_light};
}}

/* ── Status bar ─────────────────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {t.status_fondo};
    color: {t.status_texto};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10px;
    border-top: 2px solid #202020;
    min-height: 22px;
}}

QStatusBar::item {{
    border: none;
}}

QLabel#status_label {{
    background-color: transparent;
    color: {t.status_texto};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10px;
    padding: 2px 6px;
}}

/* ── Título de módulo ───────────────────────────────────────────────────────── */

QLabel#modulo_titulo {{
    background-color: {t.titulo_fondo};
    color: {t.titulo_texto};
    font-family: "Tahoma", sans-serif;
    font-size: 12px;
    font-weight: bold;
    padding: 5px 10px;
    border-bottom: 2px solid #000040;
}}

/* ── GroupBox ───────────────────────────────────────────────────────────────── */

QGroupBox {{
    background-color: {t.fondo_base};
    border: 2px groove #808080;
    margin-top: 14px;
    font-weight: bold;
    font-size: 10px;
    color: #000000;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background-color: {t.fondo_base};
}}

/* ── LineEdit ───────────────────────────────────────────────────────────────── */

QLineEdit {{
    background-color: #FFFFFF;
    border: 2px solid;
    border-top-color:    #808080;
    border-left-color:   #808080;
    border-right-color:  #DFDFDF;
    border-bottom-color: #DFDFDF;
    padding: 2px 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    color: #000000;
    selection-background-color: #000080;
    selection-color: #FFFFFF;
}}

QLineEdit:focus {{
    border-top-color:    #000080;
    border-left-color:   #000080;
    border-right-color:  #A0A0FF;
    border-bottom-color: #A0A0FF;
}}

QLineEdit:read-only {{
    background-color: #D4D0C8;
    color: #606060;
}}

QLineEdit:disabled {{
    background-color: #D4D0C8;
    color: #808080;
}}

/* ── ComboBox ───────────────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {t.fondo_base};
    border: 2px solid;
    border-top-color:    #FFFFFF;
    border-left-color:   #FFFFFF;
    border-right-color:  #808080;
    border-bottom-color: #808080;
    padding: 2px 4px;
    min-height: 20px;
    font-family: "Tahoma", sans-serif;
    font-size: 11px;
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
    background-color: {t.fondo_base};
    border-left: 1px solid #808080;
}}

QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #000000;
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    border: 2px solid #000000;
    selection-background-color: {t.titulo_fondo};
    selection-color: {t.titulo_texto};
    font-family: "Tahoma", sans-serif;
    font-size: 11px;
}}

/* ── QPushButton general ────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {t.fondo_base};
    border: 2px solid;
    border-top-color:    #FFFFFF;
    border-left-color:   #FFFFFF;
    border-right-color:  #808080;
    border-bottom-color: #808080;
    padding: 3px 14px;
    min-height: 22px;
    color: #000000;
    font-family: "Tahoma", sans-serif;
    font-size: 11px;
}}

QPushButton:hover {{
    background-color: #D4D0C8;
}}

QPushButton:pressed {{
    border-top-color:    #808080;
    border-left-color:   #808080;
    border-right-color:  #FFFFFF;
    border-bottom-color: #FFFFFF;
    padding: 4px 13px 2px 15px;
}}

QPushButton:disabled {{
    color: #808080;
    border-top-color:    #DFDFDF;
    border-left-color:   #DFDFDF;
    border-right-color:  #A0A0A0;
    border-bottom-color: #A0A0A0;
}}

/* ── Botón de acción principal ──────────────────────────────────────────────── */

QPushButton#btn_calcular {{
    background-color: {t.btn_act_normal};
    color: {t.btn_act_texto};
    font-weight: bold;
    min-height: 28px;
    border-top-color:    {t.btn_act_light};
    border-left-color:   {t.btn_act_light};
    border-right-color:  {t.btn_act_dark};
    border-bottom-color: {t.btn_act_dark};
}}

QPushButton#btn_calcular:hover {{
    background-color: {btn_act_hover};
}}

QPushButton#btn_calcular:pressed {{
    border-top-color:    {t.btn_act_dark};
    border-left-color:   {t.btn_act_dark};
    border-right-color:  {t.btn_act_light};
    border-bottom-color: {t.btn_act_light};
}}

/* ── Panel CRT ──────────────────────────────────────────────────────────────── */

QTextEdit#panel_crt {{
    background-color: {t.crt_fondo};
    color: {t.crt_verde};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    border: 2px solid;
    border-top-color:    #808080;
    border-left-color:   #808080;
    border-right-color:  #DFDFDF;
    border-bottom-color: #DFDFDF;
    padding: 4px;
    selection-background-color: #003300;
    selection-color: {t.crt_verde};
}}

/* ── QTableWidget ───────────────────────────────────────────────────────────── */

QTableWidget {{
    background-color: #FFFFFF;
    gridline-color: #C0C0C0;
    border: 2px solid;
    border-top-color:    #808080;
    border-left-color:   #808080;
    border-right-color:  #DFDFDF;
    border-bottom-color: #DFDFDF;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10px;
    selection-background-color: {t.titulo_fondo};
    selection-color: {t.titulo_texto};
    alternate-background-color: #F0F0F0;
}}

QTableWidget::item {{
    padding: 2px 4px;
}}

QHeaderView::section {{
    background-color: {t.fondo_base};
    border: 2px solid;
    border-top-color:    #FFFFFF;
    border-left-color:   #FFFFFF;
    border-right-color:  #808080;
    border-bottom-color: #808080;
    padding: 2px 6px;
    font-weight: bold;
    font-size: 10px;
    font-family: "Tahoma", sans-serif;
}}

/* ── ScrollBar ──────────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background-color: {t.fondo_base};
    width: 17px;
    border: 1px solid #808080;
}}

QScrollBar::handle:vertical {{
    background-color: {t.fondo_base};
    border: 2px solid;
    border-top-color:    #FFFFFF;
    border-left-color:   #FFFFFF;
    border-right-color:  #808080;
    border-bottom-color: #808080;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background-color: {t.fondo_base};
    height: 17px;
    border: 2px solid;
    border-top-color:    #FFFFFF;
    border-left-color:   #FFFFFF;
    border-right-color:  #808080;
    border-bottom-color: #808080;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background-color: {t.fondo_marcos};
}}

QScrollBar:horizontal {{
    background-color: {t.fondo_base};
    height: 17px;
    border: 1px solid #808080;
}}

QScrollBar::handle:horizontal {{
    background-color: {t.fondo_base};
    border: 2px solid;
    border-top-color:    #FFFFFF;
    border-left-color:   #FFFFFF;
    border-right-color:  #808080;
    border-bottom-color: #808080;
    min-width: 20px;
}}

/* ── Splitter ───────────────────────────────────────────────────────────────── */

QSplitter::handle:horizontal {{
    background-color: {t.fondo_base};
    border-left: 1px solid #808080;
    border-right: 1px solid #FFFFFF;
    width: 4px;
}}

QSplitter::handle:vertical {{
    background-color: {t.fondo_base};
    border-top: 1px solid #808080;
    border-bottom: 1px solid #FFFFFF;
    height: 4px;
}}

/* ── Separadores QFrame ─────────────────────────────────────────────────────── */

QFrame[frameShape="5"] {{
    border: none;
    border-left: 1px solid #808080;
    border-right: 1px solid #FFFFFF;
    max-width: 3px;
    min-width: 3px;
}}

QFrame[frameShape="4"] {{
    border: none;
    border-top: 1px solid #808080;
    border-bottom: 1px solid #FFFFFF;
    max-height: 3px;
    min-height: 3px;
}}

/* ── Labels de estado ───────────────────────────────────────────────────────── */

QLabel#lbl_nominal {{
    color: #007700;
    font-weight: bold;
    background-color: transparent;
}}

QLabel#lbl_alerta {{
    color: #CC0000;
    font-weight: bold;
    background-color: transparent;
}}
"""
