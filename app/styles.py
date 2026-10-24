"""
Hoja de estilos QSS parametrizada por tema (Claro / Oscuro).

Uso:
    from app.styles import get_stylesheet
    from app.themes import get_tema
    app.setStyle('Fusion')
    app.setStyleSheet(get_stylesheet(get_tema()))
"""
from __future__ import annotations

import os

from app.themes import Tema

_RECURSOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recursos').replace(os.sep, '/')

_FUENTE      = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
_FUENTE_MONO = '"Cascadia Mono", Consolas, "Courier New", monospace'


def get_stylesheet(t: Tema) -> str:
    variante = 'oscuro' if t.oscuro else 'claro'
    abajo  = f'{_RECURSOS}/flecha_abajo_{variante}.svg'
    arriba = f'{_RECURSOS}/flecha_arriba_{variante}.svg'
    return f"""
/* ── Base ──────────────────────────────────────────────────────────────────── */

QMainWindow, QDialog {{
    background-color: {t.fondo};
}}

QWidget {{
    background-color: {t.fondo};
    color: {t.texto};
    font-family: {_FUENTE};
    font-size: 12px;
}}

QToolTip {{
    background-color: {t.superficie};
    color: {t.texto};
    border: 1px solid {t.borde};
    padding: 6px;
}}

/* ── Barra lateral ──────────────────────────────────────────────────────────── */

QWidget#sidebar {{
    background-color: {t.sidebar_fondo};
}}

QLabel#sidebar_logo {{
    background-color: transparent;
    color: {t.sidebar_texto};
    font-size: 11px;
    font-weight: 600;
    padding: 6px 0 2px 0;
}}

QWidget#sidebar_sep {{
    background-color: {t.sidebar_hover};
    max-height: 1px;
    min-height: 1px;
}}

QPushButton#btn_modulo {{
    background-color: transparent;
    color: {t.sidebar_texto};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    font-size: 11px;
    font-weight: 600;
    text-align: left;
    padding: 6px 10px;
    min-height: 0;
}}

QPushButton#btn_modulo:hover {{
    background-color: {t.sidebar_hover};
    color: #FFFFFF;
}}

QPushButton#btn_modulo:checked {{
    background-color: {t.sidebar_hover};
    color: #FFFFFF;
    border-left: 3px solid {t.acento};
}}

QPushButton#btn_tema {{
    background-color: transparent;
    color: {t.sidebar_texto};
    border: 1px solid {t.sidebar_hover};
    border-radius: 4px;
    font-size: 10px;
    padding: 3px 0;
    min-height: 0;
}}

QPushButton#btn_tema:hover {{
    background-color: {t.sidebar_hover};
}}

QPushButton#btn_tema:checked {{
    background-color: {t.acento};
    border-color: {t.acento};
    color: {t.acento_texto};
}}

/* ── Barra de estado ────────────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {t.superficie};
    border-top: 1px solid {t.borde};
    min-height: 22px;
}}

QStatusBar::item {{
    border: none;
}}

QLabel#status_label {{
    background-color: transparent;
    color: {t.texto_suave};
    font-size: 11px;
    padding: 2px 6px;
}}

/* ── Encabezado de módulo ───────────────────────────────────────────────────── */

QLabel#modulo_titulo {{
    background-color: {t.superficie};
    color: {t.texto};
    font-size: 16px;
    font-weight: 600;
    padding: 10px 14px 0 14px;
}}

QLabel#modulo_subtitulo {{
    background-color: {t.superficie};
    color: {t.texto_suave};
    font-size: 11px;
    padding: 2px 14px 10px 14px;
    border-bottom: 1px solid {t.borde};
}}

/* ── Grupos ─────────────────────────────────────────────────────────────────── */

QGroupBox {{
    background-color: {t.superficie};
    border: 1px solid {t.borde};
    border-radius: 6px;
    margin-top: 16px;
    padding: 6px 4px 4px 4px;
    font-size: 11px;
    font-weight: 600;
    color: {t.texto_suave};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background-color: transparent;
    color: {t.texto_suave};
}}

QGroupBox QWidget {{
    background-color: {t.superficie};
}}

QGroupBox QLabel, QCheckBox {{
    background-color: transparent;
    font-weight: normal;
    color: {t.texto};
}}

/* ── Campos ─────────────────────────────────────────────────────────────────── */

QLineEdit, QAbstractSpinBox, QComboBox {{
    background-color: {t.superficie};
    color: {t.texto};
    border: 1px solid {t.borde};
    border-radius: 4px;
    padding: 3px 6px;
    min-height: 20px;
    selection-background-color: {t.acento};
    selection-color: {t.acento_texto};
}}

QLineEdit {{
    font-family: {_FUENTE_MONO};
}}

QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus {{
    border: 1px solid {t.acento};
}}

QLineEdit[error="true"] {{
    border: 2px solid {t.error};
}}

QLineEdit:disabled, QAbstractSpinBox:disabled, QComboBox:disabled {{
    color: {t.texto_suave};
    background-color: {t.superficie_alt};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: url({abajo});
    width: 10px;
    height: 6px;
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {t.superficie};
    color: {t.texto};
    border: 1px solid {t.borde};
    selection-background-color: {t.acento};
    selection-color: {t.acento_texto};
    outline: none;
}}

QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
    width: 16px;
    border: none;
    background-color: transparent;
}}

QAbstractSpinBox::up-arrow {{
    image: url({arriba});
    width: 8px;
    height: 5px;
}}

QAbstractSpinBox::down-arrow {{
    image: url({abajo});
    width: 8px;
    height: 5px;
}}

/* ── Botones ────────────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {t.superficie};
    color: {t.texto};
    border: 1px solid {t.borde};
    border-radius: 4px;
    padding: 5px 14px;
    min-height: 18px;
}}

QPushButton:hover {{
    background-color: {t.superficie_alt};
    border-color: {t.acento};
}}

QPushButton:pressed {{
    background-color: {t.borde};
}}

QPushButton:disabled {{
    color: {t.texto_suave};
    background-color: {t.superficie_alt};
    border-color: {t.borde};
}}

QPushButton#btn_calcular {{
    background-color: {t.acento};
    color: {t.acento_texto};
    border: 1px solid {t.acento};
    font-weight: 600;
    min-height: 24px;
}}

QPushButton#btn_calcular:hover {{
    background-color: {t.acento_hover};
    border-color: {t.acento_hover};
}}

QPushButton#btn_calcular:disabled {{
    background-color: {t.superficie_alt};
    color: {t.texto_suave};
    border-color: {t.borde};
}}

/* ── Panel de resultados ────────────────────────────────────────────────────── */

QTextEdit#panel_resultados {{
    background-color: {t.res_fondo};
    color: {t.res_texto};
    border: 1px solid {t.borde};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {t.acento};
    selection-color: {t.acento_texto};
}}

/* ── Tablas ─────────────────────────────────────────────────────────────────── */

QTableWidget {{
    background-color: {t.superficie};
    alternate-background-color: {t.superficie_alt};
    color: {t.texto};
    gridline-color: {t.borde};
    border: 1px solid {t.borde};
    border-radius: 6px;
    font-family: {_FUENTE_MONO};
    font-size: 11px;
    selection-background-color: {t.acento};
    selection-color: {t.acento_texto};
}}

QTableWidget::item {{
    padding: 2px 4px;
}}

QHeaderView::section {{
    background-color: {t.superficie_alt};
    color: {t.texto_suave};
    border: none;
    border-bottom: 1px solid {t.borde};
    border-right: 1px solid {t.borde};
    padding: 4px 6px;
    font-weight: 600;
    font-size: 11px;
}}

QTableCornerButton::section {{
    background-color: {t.superficie_alt};
    border: none;
}}

/* ── Barras de desplazamiento ───────────────────────────────────────────────── */

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {t.borde};
    border-radius: 3px;
    min-height: 24px;
    min-width: 24px;
}}

QScrollBar::handle:hover {{
    background-color: {t.texto_suave};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

/* ── Divisores y separadores ────────────────────────────────────────────────── */

QSplitter::handle {{
    background-color: {t.fondo};
}}

QSplitter::handle:horizontal {{ width: 6px; }}
QSplitter::handle:vertical   {{ height: 6px; }}

QFrame[frameShape="5"] {{
    border: none;
    background-color: {t.borde};
    max-width: 1px;
    min-width: 1px;
}}

QFrame[frameShape="4"] {{
    border: none;
    background-color: {t.borde};
    max-height: 1px;
    min-height: 1px;
}}
"""
