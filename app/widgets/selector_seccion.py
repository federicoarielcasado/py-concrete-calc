"""
SelectorSeccion — QGroupBox con campos para sección transversal.

Soporta RECTANGULAR y T / L.
Expone:
    get_seccion(hormigon, acero) -> SeccionRectangular | SeccionT
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QLineEdit,
    QWidget, QVBoxLayout, QStackedWidget,
)
from PyQt6.QtCore import Qt

from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular, SeccionT


def _campo(default: str, placeholder: str = '') -> QLineEdit:
    e = QLineEdit(default)
    if placeholder:
        e.setPlaceholderText(placeholder)
    return e


class SelectorSeccion(QGroupBox):
    """Selector de tipo y geometría de sección transversal."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__('SECCIÓN', parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Tipo de sección
        fila_tipo = QWidget()
        fl = QFormLayout(fila_tipo)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._combo = QComboBox()
        self._combo.addItems(['RECTANGULAR', 'T / L'])
        self._combo.setToolTip(
            '<b>Tipo de sección transversal</b><br>'
            'RECTANGULAR: vigas aisladas, columnas, losas<br>'
            'T / L: viga solidaria con losa — usar ancho efectivo del ala (art. 8.10)'
        )
        self._combo.currentIndexChanged.connect(lambda i: self._stack.setCurrentIndex(i))
        fl.addRow('Tipo:', self._combo)
        layout.addWidget(fila_tipo)

        # Stack por tipo
        self._stack = QStackedWidget()

        # — Página RECTANGULAR —
        w_rect = QWidget()
        fr = QFormLayout(w_rect)
        fr.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        fr.setSpacing(3)
        self.b   = _campo('0.30', 'm')
        self.h   = _campo('0.60', 'm')
        self.rec = _campo('0.05', 'm')
        self.b.setToolTip(
            '<b>b</b> — ancho de la sección rectangular [m]<br>'
            'Rango típico: 0.20–0.40 m para vigas<br>'
            'Adoptar múltiplo de 0.05 m por razones constructivas'
        )
        self.h.setToolTip(
            '<b>h</b> — altura total de la sección [m]<br>'
            'Regla práctica: h ≈ L/12 (viga simple), h ≈ L/10 (continua)<br>'
            'Rango típico: 0.30–0.80 m para vigas'
        )
        self.rec.setToolTip(
            '<b>rec</b> — recubrimiento mecánico hasta eje de armadura [m]<br>'
            'Mínimos CIRSOC art. 7.7: 0.019 m (normal), 0.038 m (exterior)<br>'
            'Con estribo: rec ≈ rec_hormigón + d_estribo + d_barra/2 ≈ 0.04–0.06 m'
        )
        fr.addRow('b [m]:', self.b)
        fr.addRow('h [m]:', self.h)
        fr.addRow('rec [m]:', self.rec)
        self._stack.addWidget(w_rect)

        # — Página T / L —
        w_T = QWidget()
        ft = QFormLayout(w_T)
        ft.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        ft.setSpacing(3)
        self.bw     = _campo('0.25', 'm')
        self.h_T    = _campo('0.60', 'm')
        self.b_ala  = _campo('0.90', 'm')
        self.h_ala  = _campo('0.12', 'm')
        self.rec_T  = _campo('0.06', 'm')
        self.bw.setToolTip(
            '<b>bw</b> — ancho del alma para sección T o L [m]<br>'
            'Rango típico: 0.20–0.35 m'
        )
        self.h_T.setToolTip(
            '<b>h</b> — altura total de la sección T/L [m]<br>'
            'Incluye el espesor del ala (h_ala)'
        )
        self.b_ala.setToolTip(
            '<b>b_ala</b> — ancho efectivo del ala [m]<br>'
            'CIRSOC art. 8.10: mín{ L/4 ; bw + 16·h_ala ; distancia entre vigas }<br>'
            'Para viga L: mín{ L/12 + bw ; bw + 6·h_ala ; semiDistancia entre vigas }'
        )
        self.h_ala.setToolTip(
            '<b>h_ala</b> — espesor del ala [m]<br>'
            'Generalmente igual al espesor de la losa colaborante'
        )
        self.rec_T.setToolTip(
            '<b>rec</b> — recubrimiento mecánico hasta eje de armadura [m]<br>'
            'Mínimos CIRSOC art. 7.7: 0.019 m (normal), 0.038 m (exterior)<br>'
            'Típico en vigas T: 0.05–0.07 m'
        )
        ft.addRow('bw [m]:', self.bw)
        ft.addRow('h [m]:', self.h_T)
        ft.addRow('b_ala [m]:', self.b_ala)
        ft.addRow('h_ala [m]:', self.h_ala)
        ft.addRow('rec [m]:', self.rec_T)
        self._stack.addWidget(w_T)

        layout.addWidget(self._stack)

    def get_datos(self) -> dict:
        tipo = self._combo.currentIndex()
        d: dict = {'tipo': tipo}
        if tipo == 0:
            d.update({'b': self.b.text(), 'h': self.h.text(), 'rec': self.rec.text()})
        else:
            d.update({'bw': self.bw.text(), 'h': self.h_T.text(),
                      'b_ala': self.b_ala.text(), 'h_ala': self.h_ala.text(),
                      'rec': self.rec_T.text()})
        return d

    def set_datos(self, d: dict) -> None:
        tipo = d.get('tipo', 0)
        self._combo.setCurrentIndex(tipo)
        if tipo == 0:
            self.b.setText(d.get('b', '0.30'))
            self.h.setText(d.get('h', '0.60'))
            self.rec.setText(d.get('rec', '0.05'))
        else:
            self.bw.setText(d.get('bw', '0.25'))
            self.h_T.setText(d.get('h', '0.60'))
            self.b_ala.setText(d.get('b_ala', '0.90'))
            self.h_ala.setText(d.get('h_ala', '0.12'))
            self.rec_T.setText(d.get('rec', '0.06'))

    def get_seccion(self, hormigon: Hormigon, acero: Acero):
        """Devuelve la sección configurada. Lanza ValueError si hay datos inválidos."""
        try:
            tipo = self._combo.currentIndex()
            if tipo == 0:
                return SeccionRectangular(
                    b=float(self.b.text()),
                    h=float(self.h.text()),
                    recubrimiento=float(self.rec.text()),
                    hormigon=hormigon,
                    acero=acero,
                )
            else:
                return SeccionT(
                    bw=float(self.bw.text()),
                    h=float(self.h_T.text()),
                    b_ala=float(self.b_ala.text()),
                    h_ala=float(self.h_ala.text()),
                    recubrimiento=float(self.rec_T.text()),
                    hormigon=hormigon,
                    acero=acero,
                )
        except (ValueError, TypeError) as e:
            raise ValueError(f'Datos de sección inválidos: {e}') from e
