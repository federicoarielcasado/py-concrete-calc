"""
SelectorMateriales — QGroupBox con selección de hormigón y acero.

Expone:
    get_hormigon() -> Hormigon
    get_acero()    -> Acero
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QLineEdit, QWidget, QHBoxLayout,
)
from PyQt6.QtCore import Qt

from hormigon.materiales import Hormigon, Acero

_HORMIGONES: dict[str, float | None] = {
    'H17': 17, 'H21': 21, 'H25': 25, 'H30': 30,
    'H35': 35, 'H40': 40, 'Personalizado': None,
}
_ACEROS: dict[str, float | None] = {
    'ADN 420': 420, 'AM 500N': 500, 'Personalizado': None,
}


class SelectorMateriales(QGroupBox):
    """Selector de hormigón y acero con opciones predefinidas o personalizadas."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__('MATERIALES', parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        form = QFormLayout(self)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(4)

        # Hormigón
        self._combo_horm = QComboBox()
        self._combo_horm.addItems(list(_HORMIGONES.keys()))
        self._combo_horm.setCurrentText('H25')
        self._combo_horm.setToolTip(
            "<b>Hormigón</b> — resistencia característica f'c<br>"
            "H17=17 MPa, H21=21, H25=25, H30=30, H35=35, H40=40 MPa<br>"
            "El más usado en obra es <b>H25</b>. Módulo: E = 4700·√f'c MPa<br>"
            "<i>CIRSOC art. 5.1 y art. 8.5.1</i>"
        )
        self._campo_fc = QLineEdit('25')
        self._campo_fc.setFixedWidth(60)
        self._campo_fc.setPlaceholderText('MPa')
        self._campo_fc.setToolTip("f'c personalizado [MPa] — resistencia característica a compresión")
        self._campo_fc.hide()
        self._combo_horm.currentTextChanged.connect(self._cambiar_hormigon)

        hw = QWidget()
        hl = QHBoxLayout(hw)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(4)
        hl.addWidget(self._combo_horm)
        hl.addWidget(self._campo_fc)
        form.addRow("Hormigón:", hw)

        # Acero
        self._combo_acero = QComboBox()
        self._combo_acero.addItems(list(_ACEROS.keys()))
        self._combo_acero.setCurrentText('ADN 420')
        self._combo_acero.setToolTip(
            '<b>Acero</b> — tensión de fluencia fy<br>'
            'ADN 420: fy = 420 MPa — barras corrugadas, el más común en Argentina<br>'
            'AM 500N: fy = 500 MPa — barras microaleadas<br>'
            '<i>Es = 200 000 MPa para todos los tipos (art. 8.5.2)</i>'
        )
        self._campo_fy = QLineEdit('420')
        self._campo_fy.setFixedWidth(60)
        self._campo_fy.setPlaceholderText('MPa')
        self._campo_fy.setToolTip('fy personalizado [MPa] — tensión de fluencia del acero')
        self._campo_fy.hide()
        self._combo_acero.currentTextChanged.connect(self._cambiar_acero)

        aw = QWidget()
        al = QHBoxLayout(aw)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(4)
        al.addWidget(self._combo_acero)
        al.addWidget(self._campo_fy)
        form.addRow("Acero:", aw)

    def _cambiar_hormigon(self, nombre: str) -> None:
        self._campo_fc.setVisible(nombre == 'Personalizado')

    def _cambiar_acero(self, nombre: str) -> None:
        self._campo_fy.setVisible(nombre == 'Personalizado')

    def get_datos(self) -> dict:
        d = {'hormigon': self._combo_horm.currentText(),
             'acero':    self._combo_acero.currentText()}
        if d['hormigon'] == 'Personalizado':
            d['fc'] = self._campo_fc.text()
        if d['acero'] == 'Personalizado':
            d['fy'] = self._campo_fy.text()
        return d

    def set_datos(self, d: dict) -> None:
        self._combo_horm.setCurrentText(d.get('hormigon', 'H25'))
        if 'fc' in d:
            self._campo_fc.setText(d['fc'])
        self._combo_acero.setCurrentText(d.get('acero', 'ADN 420'))
        if 'fy' in d:
            self._campo_fy.setText(d['fy'])

    def get_hormigon(self) -> Hormigon:
        nombre = self._combo_horm.currentText()
        if nombre == 'Personalizado':
            try:
                fc = float(self._campo_fc.text().replace(',', '.'))
            except ValueError:
                raise ValueError("f'c personalizado inválido — ingrese un número.")
        else:
            fc = _HORMIGONES[nombre]
        return Hormigon(fc=fc)

    def get_acero(self) -> Acero:
        nombre = self._combo_acero.currentText()
        if nombre == 'Personalizado':
            try:
                fy = float(self._campo_fy.text().replace(',', '.'))
            except ValueError:
                raise ValueError("fy personalizado inválido — ingrese un número.")
        else:
            fy = _ACEROS[nombre]
        return Acero(fy=fy)
