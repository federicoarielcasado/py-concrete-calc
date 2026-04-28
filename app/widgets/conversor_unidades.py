"""
Conversor de unidades para ejercicios CIRSOC.
Cubre las conversiones más comunes al transcribir datos de libros y apuntes.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

# factor_a_base: multiplicar para obtener la unidad base de cada categoría
_CATEGORIAS: dict[str, dict[str, float]] = {
    'Fuerza  [kN]': {
        'kN':   1.0,
        'N':    0.001,
        'kgf':  0.00980665,
        'tf':   9.80665,
    },
    'Momento  [kN·m]': {
        'kN·m':   1.0,
        'N·m':    0.001,
        'kgf·m':  0.00980665,
        'tf·m':   9.80665,
        'kgf·cm': 0.0000980665,
    },
    'Carga dist.  [kN/m]': {
        'kN/m':  1.0,
        'N/m':   0.001,
        'kgf/m': 0.00980665,
        'tf/m':  9.80665,
    },
    'Presión  [kN/m²]': {
        'kN/m²':  1.0,
        'N/m²':   0.001,
        'kgf/m²': 0.00980665,
        'tf/m²':  9.80665,
        'kgf/cm²': 98.0665,
    },
    'Tensión  [MPa]': {
        'MPa':     1.0,
        'N/mm²':   1.0,
        'kgf/cm²': 0.0980665,
        'ksi':     6.89476,
    },
    'Longitud  [m]': {
        'm':  1.0,
        'cm': 0.01,
        'mm': 0.001,
        'ft': 0.3048,
        'in': 0.0254,
    },
    'Área  [cm²]': {
        'cm²': 1.0,
        'mm²': 0.01,
        'm²':  10000.0,
        'in²': 6.4516,
    },
}


class ConversorUnidades(QDialog):
    """Conversor flotante no modal. Se mantiene abierto mientras se trabaja."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle('CONVERSOR DE UNIDADES')
        self.setFixedWidth(300)
        self.setModal(False)
        self._ultimo: float = 0.0
        self._setup_ui()
        self._cambiar_categoria(0)

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        grp_cat = QGroupBox('CATEGORÍA')
        fl_cat = QFormLayout(grp_cat)
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(list(_CATEGORIAS.keys()))
        self.combo_cat.currentIndexChanged.connect(self._cambiar_categoria)
        fl_cat.addRow('', self.combo_cat)
        lay.addWidget(grp_cat)

        grp_in = QGroupBox('DE')
        fl_in = QFormLayout(grp_in)
        fl_in.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.edit_valor = QLineEdit('1')
        self.edit_valor.setValidator(QDoubleValidator(-1e15, 1e15, 8))
        self.edit_valor.textChanged.connect(self._recalcular)
        self.combo_desde = QComboBox()
        self.combo_desde.currentIndexChanged.connect(self._recalcular)
        fl_in.addRow('Valor:', self.edit_valor)
        fl_in.addRow('Unidad:', self.combo_desde)
        lay.addWidget(grp_in)

        btn_inv = QPushButton('⇅  INVERTIR SENTIDO')
        btn_inv.clicked.connect(self._invertir)
        lay.addWidget(btn_inv)

        grp_out = QGroupBox('A')
        fl_out = QFormLayout(grp_out)
        fl_out.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.combo_hasta = QComboBox()
        self.combo_hasta.currentIndexChanged.connect(self._recalcular)
        self.lbl_resultado = QLabel('—')
        self.lbl_resultado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.lbl_resultado.font()
        font.setPointSize(13)
        font.setBold(True)
        self.lbl_resultado.setFont(font)
        fl_out.addRow('Unidad:', self.combo_hasta)
        fl_out.addRow('=', self.lbl_resultado)
        lay.addWidget(grp_out)

        btn_copiar = QPushButton('COPIAR NÚMERO AL PORTAPAPELES')
        btn_copiar.clicked.connect(self._copiar)
        lay.addWidget(btn_copiar)

    def _cambiar_categoria(self, _idx: int) -> None:
        cat = self.combo_cat.currentText()
        unidades = list(_CATEGORIAS[cat].keys())
        for combo in (self.combo_desde, self.combo_hasta):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(unidades)
            combo.blockSignals(False)
        if len(unidades) > 1:
            self.combo_hasta.setCurrentIndex(1)
        self._recalcular()

    def _recalcular(self) -> None:
        try:
            valor = float(self.edit_valor.text().replace(',', '.'))
        except ValueError:
            self.lbl_resultado.setText('—')
            return
        cat = self.combo_cat.currentText()
        factores = _CATEGORIAS[cat]
        desde = self.combo_desde.currentText()
        hasta = self.combo_hasta.currentText()
        if not desde or not hasta:
            return
        resultado = valor * factores[desde] / factores[hasta]
        self._ultimo = resultado
        self.lbl_resultado.setText(f'{resultado:.6g} {hasta}')

    def _invertir(self) -> None:
        desde = self.combo_desde.currentText()
        hasta = self.combo_hasta.currentText()
        self.combo_desde.blockSignals(True)
        self.combo_hasta.blockSignals(True)
        self.combo_desde.setCurrentText(hasta)
        self.combo_hasta.setCurrentText(desde)
        self.combo_desde.blockSignals(False)
        self.combo_hasta.blockSignals(False)
        self._recalcular()

    def _copiar(self) -> None:
        QApplication.clipboard().setText(f'{self._ultimo:.6g}')
