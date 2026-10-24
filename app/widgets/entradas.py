"""
Utilidades para los paneles de entrada de datos.

  - con_scroll(panel):          envuelve el panel izquierdo en un área desplazable.
  - instalar_validadores(w):    los QLineEdit numéricos solo aceptan números.
  - validar_campos(w, panel):   revisa los campos visibles antes de calcular,
                                marca en rojo el inválido y explica el problema.
"""
from __future__ import annotations

import re

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QFormLayout, QFrame, QLineEdit, QScrollArea, QWidget

_NUMERO = QRegularExpression(r'^-?\d*([.,]\d*)?$')
_UNIDAD_LONGITUD = re.compile(r'\[(m|mm|cm)\]')


def con_scroll(panel: QWidget) -> QScrollArea:
    """Área con scroll vertical del mismo ancho que el panel (fijo)."""
    area = QScrollArea()
    area.setWidget(panel)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setFixedWidth(panel.maximumWidth() + 14)
    return area


def instalar_validadores(ventana: QWidget) -> None:
    for campo in ventana.findChildren(QLineEdit):
        if campo.validator() is None and not campo.isReadOnly():
            campo.setValidator(QRegularExpressionValidator(_NUMERO, campo))


def _etiqueta(ventana: QWidget, campo: QLineEdit) -> str:
    for form in ventana.findChildren(QFormLayout):
        lbl = form.labelForField(campo)
        if lbl is not None and hasattr(lbl, 'text'):
            return lbl.text().rstrip(':').strip()
    return campo.toolTip().split('—')[0].replace('<b>', '').replace('</b>', '').strip() or 'Campo'


def _marcar(campo: QLineEdit, error: bool) -> None:
    campo.setProperty('error', error)
    campo.style().unpolish(campo)
    campo.style().polish(campo)
    if error and not campo.property('_limpia_error'):
        campo.setProperty('_limpia_error', True)
        campo.textChanged.connect(lambda _t, c=campo: _marcar(c, False))


def validar_campos(ventana: QWidget, panel=None) -> bool:
    """
    True si todos los campos numéricos visibles son válidos. Si alguno no lo es,
    lo marca, le da el foco y muestra el motivo en el panel de resultados.
    """
    panel = panel or getattr(ventana, 'panel_res', None)
    for campo in ventana.findChildren(QLineEdit):
        if not campo.isVisibleTo(ventana) or not campo.isEnabled() or campo.isReadOnly():
            continue
        if not isinstance(campo.validator(), QRegularExpressionValidator):
            continue
        nombre = _etiqueta(ventana, campo)
        texto = campo.text().strip().replace(',', '.')
        try:
            valor = float(texto)
        except ValueError:
            motivo = 'está vacío' if not texto else 'no es un número válido'
            return _fallar(campo, panel, f'«{nombre}» {motivo}.')
        if _UNIDAD_LONGITUD.search(nombre) and valor <= 0:
            return _fallar(campo, panel, f'«{nombre}» debe ser una dimensión mayor que cero.')
        if valor < 0 and not nombre.startswith('Nu'):
            return _fallar(campo, panel, f'«{nombre}» no puede ser negativo.')
        _marcar(campo, False)
    return True


def _fallar(campo: QLineEdit, panel, mensaje: str) -> bool:
    _marcar(campo, True)
    campo.setFocus()
    campo.selectAll()
    if panel is not None:
        panel.mostrar_error(mensaje)
    return False
