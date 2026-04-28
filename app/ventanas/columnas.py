"""
MÓDULO-03 / COLUMNA P+M
Diseño por diagrama de interacción.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QSpinBox,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_crt import PanelCRT
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.selector_seccion import SelectorSeccion


class VentanaColumnas(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._seccion   = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('MÓDULO-03 / COLUMNA  —  FLEXOCOMPRESIÓN P+M')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        content = QWidget()
        hl = QHBoxLayout(content)
        hl.setContentsMargins(8, 8, 8, 8)
        hl.setSpacing(0)
        hl.addWidget(self._panel_entrada())

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        hl.addWidget(sep)

        hl.addWidget(self._panel_resultados(), stretch=1)
        root.addWidget(content, stretch=1)

    def _panel_entrada(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(330)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(6)

        self.sel_mat = SelectorMateriales()
        lay.addWidget(self.sel_mat)

        # Para columnas usamos siempre sección rectangular
        self.sel_sec = SelectorSeccion()
        lay.addWidget(self.sel_sec)

        grp = QGroupBox('SOLICITACIÓN')
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_Pu = QLineEdit('800')
        self.entrada_Pu.setToolTip(
            '<b>Pu</b> — carga axial última mayorada [kN]<br>'
            'Del análisis de la estructura con cargas mayoradas (art. 9.2.1)<br>'
            '<i>Estimación: Pu ≈ N° pisos × carga_piso × área_tributaria</i>'
        )
        self.entrada_Mu = QLineEdit('100')
        self.entrada_Mu.setToolTip(
            '<b>Mu</b> — momento flector último mayorado [kN·m]<br>'
            'Del análisis estructural. Si Mu = 0, usar excentricidad mínima:<br>'
            '<i>e_min = 0.015·h o 15 mm (art. 10.3.6.3)</i>'
        )
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(['ESTRIBOS  (φ = 0.65)', 'ZUNCHADA  (φ = 0.70)'])
        self.combo_tipo.setToolTip(
            '<b>Tipo de armadura transversal</b><br>'
            'ESTRIBOS: φ = 0.65 — columnas rectangulares o circulares con estribos<br>'
            'ZUNCHADA: φ = 0.70 — columnas circulares con espiral continua<br>'
            '<i>CIRSOC art. 10.3.6</i>'
        )
        form.addRow('Pu [kN]:', self.entrada_Pu)
        form.addRow('Mu [kNm]:', self.entrada_Mu)
        form.addRow('TIPO:', self.combo_tipo)
        lay.addWidget(grp)

        # Adopción manual de barras
        grp_adop = QGroupBox('ADOPCIÓN DE BARRAS')
        form_adop = QFormLayout(grp_adop)
        form_adop.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.combo_phi_adop = QComboBox()
        self.combo_phi_adop.addItems(
            ['φ12', 'φ14', 'φ16', 'φ20', 'φ22', 'φ25', 'φ28', 'φ32']
        )
        self.combo_phi_adop.setCurrentText('φ20')
        self.combo_phi_adop.setToolTip(
            '<b>Diámetro de barra longitudinal</b><br>'
            'Mínimo CIRSOC: φ12. Usual en columnas: φ16–φ25<br>'
            'Elegir según As requerida y separación disponible'
        )
        self.spin_n_adop = QSpinBox()
        self.spin_n_adop.setRange(4, 24)
        self.spin_n_adop.setValue(8)
        self.spin_n_adop.setSingleStep(2)
        self.spin_n_adop.setToolTip(
            '<b>Número de barras longitudinales</b><br>'
            'Mínimo: 4 barras (sección rectangular), 6 (circular)<br>'
            'As_adoptada = N° barras × área_barra'
        )
        form_adop.addRow('Diámetro:', self.combo_phi_adop)
        form_adop.addRow('N° barras:', self.spin_n_adop)
        lay.addWidget(grp_adop)

        self.btn_calc = QPushButton('DISEÑAR COLUMNA P-03')
        self.btn_calc.setObjectName('btn_calcular')
        self.btn_calc.clicked.connect(self._ejecutar)
        lay.addWidget(self.btn_calc)

        self.btn_adoptar = QPushButton('REGISTRAR CONFIGURACIÓN')
        self.btn_adoptar.setEnabled(False)
        self.btn_adoptar.clicked.connect(self._adoptar)
        lay.addWidget(self.btn_adoptar)

        lay.addStretch()
        return w

    def _panel_resultados(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(4)

        self.crt = PanelCRT()
        self.crt.setFixedHeight(190)
        self.crt.mostrar_bienvenida('P-03 COLUMNA P+M')
        lay.addWidget(self.crt)

        self.canvas = CanvasMatplotlib()
        lay.addWidget(self.canvas, stretch=1)
        return w

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'seccion':    self.sel_sec.get_datos(),
            'Pu':         self.entrada_Pu.text(),
            'Mu':         self.entrada_Mu.text(),
            'tipo':       self.combo_tipo.currentIndex(),
            'phi_adop':   self.combo_phi_adop.currentText(),
            'n_adop':     self.spin_n_adop.value(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.sel_sec.set_datos(d.get('seccion', {}))
        self.entrada_Pu.setText(d.get('Pu', '800'))
        self.entrada_Mu.setText(d.get('Mu', '100'))
        self.combo_tipo.setCurrentIndex(d.get('tipo', 0))
        self.combo_phi_adop.setCurrentText(d.get('phi_adop', 'φ20'))
        self.spin_n_adop.setValue(d.get('n_adop', 8))

    def _ejecutar(self) -> None:
        from elementos.columna import Columna
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            Pu   = float(self.entrada_Pu.text().replace(',', '.'))
            Mu   = float(self.entrada_Mu.text().replace(',', '.'))
            tipo = 'estribos' if self.combo_tipo.currentIndex() == 0 else 'zunchada'

            r = Columna(sec, Pu=Pu, Mu=Mu, tipo=tipo).calcular()
            self._resultado = r
            self._seccion   = sec

            self.crt.mostrar_resultado_columna(r)
            self._actualizar_canvas(r)
            self.btn_adoptar.setEnabled(True)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _adoptar(self) -> None:
        if self._resultado is None:
            return
        phi_str = self.combo_phi_adop.currentText().replace('φ', '')
        phi     = int(phi_str)
        n       = self.spin_n_adop.value()
        self._resultado.adoptar(phi=phi, n_barras=n)
        self.crt.mostrar_resultado_columna(self._resultado)
        self._actualizar_canvas(self._resultado)

    def _actualizar_canvas(self, r) -> None:
        from graficos import graficar_interaccion_PM
        fig = graficar_interaccion_PM(r.diagrama, Pu=r.Pu, Mu=r.Mu)
        self.canvas.mostrar_figura(fig)
