"""
MÓDULO-07 / BASES AISLADAS CENTRADAS  —  Cap. 15 CIRSOC 201-2005
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QCheckBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_crt import PanelCRT
from app.widgets.selector_materiales import SelectorMateriales


class VentanaBases(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('MÓDULO-07 / BASES AISLADAS CENTRADAS  —  CAP. 15')
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

        # Columna
        grp_col = QGroupBox('COLUMNA')
        form_col = QFormLayout(grp_col)
        form_col.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_bc  = QLineEdit('0.40')
        self.entrada_bc.setToolTip(
            '<b>bc</b> — ancho de la sección de la columna [m]<br>'
            'Dimensión paralela al eje X de la base'
        )
        self.entrada_hc  = QLineEdit('0.40')
        self.entrada_hc.setToolTip(
            '<b>hc</b> — altura de la sección de la columna [m]<br>'
            'Dimensión paralela al eje Y de la base'
        )
        form_col.addRow('bc [m]:', self.entrada_bc)
        form_col.addRow('hc [m]:', self.entrada_hc)
        lay.addWidget(grp_col)

        # Cargas
        grp_car = QGroupBox('CARGAS Y SUELO')
        form_car = QFormLayout(grp_car)
        form_car.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_Pu    = QLineEdit('1200')
        self.entrada_Pu.setToolTip(
            '<b>Pu</b> — carga axial última mayorada [kN]<br>'
            'Combinación art. 9.2.1: Pu = 1.4·PD + 1.7·PL<br>'
            'Para diseño de la armadura de la base'
        )
        self.entrada_Ps    = QLineEdit('850')
        self.entrada_Ps.setToolTip(
            '<b>P_s</b> — carga de servicio sin mayorar [kN]<br>'
            'P_s = PD + PL<br>'
            'Para verificar presión real sobre el suelo: q = P_s / A_base ≤ q_adm'
        )
        self.entrada_qadm  = QLineEdit('150')
        self.entrada_qadm.setToolTip(
            '<b>q_adm</b> — presión admisible del suelo [kN/m²]<br>'
            'Dato del estudio geotécnico. Valores orientativos:<br>'
            'Arcilla media: 75–150, Arena densa: 200–400, Roca: 500+ kN/m²'
        )
        self.entrada_rec   = QLineEdit('0.075')
        self.entrada_rec.setToolTip(
            '<b>rec</b> — recubrimiento en base [m]<br>'
            'Mínimo CIRSOC art. 7.7.1: 0.075 m (contacto con suelo sin encofrado)<br>'
            'Con capa de limpieza: 0.050 m'
        )
        form_car.addRow('Pu [kN]:', self.entrada_Pu)
        form_car.addRow('P_s [kN]:', self.entrada_Ps)
        form_car.addRow('q_adm [kN/m²]:', self.entrada_qadm)
        form_car.addRow('rec [m]:', self.entrada_rec)
        lay.addWidget(grp_car)

        # Opciones de geometría
        grp_opt = QGroupBox('GEOMETRÍA DE LA BASE')
        form_opt = QFormLayout(grp_opt)
        form_opt.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.chk_cuadrada = QCheckBox('Base cuadrada')
        self.chk_cuadrada.setChecked(True)
        self.chk_cuadrada.setToolTip(
            'Base cuadrada: B = L — la más económica con carga centrada sin momento<br>'
            'Desmarcar para ingresar relación L/B en base rectangular'
        )
        self.chk_cuadrada.stateChanged.connect(self._toggle_ratio)
        self.spin_ratio = QDoubleSpinBox()
        self.spin_ratio.setRange(1.0, 3.0)
        self.spin_ratio.setSingleStep(0.1)
        self.spin_ratio.setValue(1.5)
        self.spin_ratio.setEnabled(False)
        self.spin_ratio.setToolTip(
            '<b>L/B ratio</b> — relación largo/ancho de la base rectangular<br>'
            'Activar desmarcando "Base cuadrada". Típico: 1.2–2.0'
        )
        form_opt.addRow('', self.chk_cuadrada)
        form_opt.addRow('L/B ratio:', self.spin_ratio)
        lay.addWidget(grp_opt)

        self.btn_calc = QPushButton('EJECUTAR PROTOCOLO B-07')
        self.btn_calc.setObjectName('btn_calcular')
        self.btn_calc.clicked.connect(self._ejecutar)
        lay.addWidget(self.btn_calc)

        lay.addStretch()
        return w

    def _panel_resultados(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(4)

        self.crt = PanelCRT()
        self.crt.setFixedHeight(220)
        self.crt.mostrar_bienvenida('B-07 BASES CENTRADAS')
        lay.addWidget(self.crt)

        self.canvas = CanvasMatplotlib()
        lay.addWidget(self.canvas, stretch=1)
        return w

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'bc':       self.entrada_bc.text(),   'hc':    self.entrada_hc.text(),
            'Pu':       self.entrada_Pu.text(),   'Ps':    self.entrada_Ps.text(),
            'qadm':     self.entrada_qadm.text(), 'rec':   self.entrada_rec.text(),
            'cuadrada': self.chk_cuadrada.isChecked(),
            'ratio':    self.spin_ratio.value(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.entrada_bc.setText(d.get('bc', '0.40'))
        self.entrada_hc.setText(d.get('hc', '0.40'))
        self.entrada_Pu.setText(d.get('Pu', '1200'))
        self.entrada_Ps.setText(d.get('Ps', '850'))
        self.entrada_qadm.setText(d.get('qadm', '150'))
        self.entrada_rec.setText(d.get('rec', '0.075'))
        self.chk_cuadrada.setChecked(d.get('cuadrada', True))
        self.spin_ratio.setValue(d.get('ratio', 1.5))

    def _toggle_ratio(self, state: int) -> None:
        self.spin_ratio.setEnabled(state == 0)

    def _ejecutar(self) -> None:
        from hormigon.bases import dimensionar_base_centrada
        try:
            horm     = self.sel_mat.get_hormigon()
            acer     = self.sel_mat.get_acero()
            bc       = float(self.entrada_bc.text().replace(',', '.'))
            hc       = float(self.entrada_hc.text().replace(',', '.'))
            Pu       = float(self.entrada_Pu.text().replace(',', '.'))
            Ps       = float(self.entrada_Ps.text().replace(',', '.'))
            q_adm    = float(self.entrada_qadm.text().replace(',', '.'))
            rec      = float(self.entrada_rec.text().replace(',', '.'))
            cuadrada = self.chk_cuadrada.isChecked()
            ratio    = self.spin_ratio.value()

            r = dimensionar_base_centrada(
                bc=bc, hc=hc, Pu=Pu, P_s=Ps, q_adm=q_adm,
                hormigon=horm, acero=acer,
                recubrimiento=rec,
                cuadrada=cuadrada,
                L_B_ratio=ratio,
            )
            self._resultado = r
            self.crt.mostrar_resultado_base(r)
            self._actualizar_canvas(r)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _actualizar_canvas(self, r) -> None:
        from graficos import graficar_base
        self.canvas.mostrar_figura(graficar_base(r))
