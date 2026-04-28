"""
MÓDULO-02 / CORTE
Dimensionado de estribos para resistencia a corte.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame, QHeaderView, QAbstractItemView, QSpinBox,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_crt import PanelCRT
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.selector_seccion import SelectorSeccion


class VentanaCorte(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._seccion   = None
        self._rset      = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('MÓDULO-02 / CORTE  —  DISEÑO DE ESTRIBOS')
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

        self.sel_sec = SelectorSeccion()
        lay.addWidget(self.sel_sec)

        grp = QGroupBox('SOLICITACIÓN')
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_Vu = QLineEdit('120')
        self.entrada_Vu.setToolTip(
            '<b>Vu</b> — cortante último mayorado [kN]<br>'
            'CIRSOC art. 11.1.3: tomarlo a distancia d del borde del apoyo<br>'
            '<i>Viga simple, carga uniforme: Vu = wu·L/2 − wu·d</i>'
        )
        self.entrada_Nu = QLineEdit('0')
        self.entrada_Nu.setToolTip(
            '<b>Nu</b> — fuerza axial mayorada [kN]<br>'
            'Positivo si compresión. Para vigas convencionales: Nu = 0<br>'
            'Afecta a Vc según art. 11.3.1.2'
        )
        self.spin_ramas = QSpinBox()
        self.spin_ramas.setRange(1, 6)
        self.spin_ramas.setValue(2)
        self.spin_ramas.setToolTip(
            '<b>Ramas del estribo</b><br>'
            'Estribo simple (U): 2 ramas<br>'
            'Estribo doble o con patilla interior: 4 ramas<br>'
            '<i>Más ramas → menor diámetro o mayor separación</i>'
        )
        form.addRow('Vu [kN]:', self.entrada_Vu)
        form.addRow('Nu [kN]:', self.entrada_Nu)
        form.addRow('Ramas estribo:', self.spin_ramas)
        lay.addWidget(grp)

        self.btn_calc = QPushButton('EJECUTAR PROTOCOLO C-02')
        self.btn_calc.setObjectName('btn_calcular')
        self.btn_calc.clicked.connect(self._ejecutar)
        lay.addWidget(self.btn_calc)

        self.btn_var = QPushButton('VER VARIANTES')
        self.btn_var.setEnabled(False)
        self.btn_var.clicked.connect(self._ver_variantes)
        lay.addWidget(self.btn_var)

        lay.addStretch()
        return w

    def _panel_resultados(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(4)

        self.crt = PanelCRT()
        self.crt.setFixedHeight(190)
        self.crt.mostrar_bienvenida('C-02 CORTE')
        lay.addWidget(self.crt)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = CanvasMatplotlib()
        splitter.addWidget(self.canvas)
        splitter.addWidget(self._panel_tabla())
        splitter.setSizes([380, 390])
        lay.addWidget(splitter, stretch=1)
        return w

    def _panel_tabla(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(['RK', 'ESTRIBO', 'Av/s [mm²/m]', 's [cm]'])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemDoubleClicked.connect(self._adoptar_seleccion)
        lay.addWidget(self.tabla)

        self.btn_adoptar = QPushButton('REGISTRAR CONFIGURACIÓN')
        self.btn_adoptar.setEnabled(False)
        self.btn_adoptar.clicked.connect(self._adoptar_seleccion)
        lay.addWidget(self.btn_adoptar)
        return w

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'seccion':    self.sel_sec.get_datos(),
            'Vu':         self.entrada_Vu.text(),
            'Nu':         self.entrada_Nu.text(),
            'ramas':      self.spin_ramas.value(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.sel_sec.set_datos(d.get('seccion', {}))
        self.entrada_Vu.setText(d.get('Vu', '120'))
        self.entrada_Nu.setText(d.get('Nu', '0'))
        self.spin_ramas.setValue(d.get('ramas', 2))

    def _ejecutar(self) -> None:
        from hormigon.corte import calcular_corte
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            Vu   = float(self.entrada_Vu.text().replace(',', '.'))
            Nu   = float(self.entrada_Nu.text().replace(',', '.'))

            r = calcular_corte(sec, Vu=Vu, Nu=Nu)
            self._resultado = r
            self._seccion   = sec

            self.crt.mostrar_resultado_corte(r)
            self._actualizar_canvas(sec, r)
            self.btn_var.setEnabled(True)
            self.tabla.setRowCount(0)
            self.btn_adoptar.setEnabled(False)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _ver_variantes(self) -> None:
        from hormigon.corte import calcular_corte_variantes
        try:
            horm  = self.sel_mat.get_hormigon()
            acer  = self.sel_mat.get_acero()
            sec   = self.sel_sec.get_seccion(horm, acer)
            Vu    = float(self.entrada_Vu.text().replace(',', '.'))
            Nu    = float(self.entrada_Nu.text().replace(',', '.'))
            ramas = self.spin_ramas.value()

            rset = calcular_corte_variantes(sec, Vu=Vu, Nu=Nu, n_ramas=ramas)
            self._rset = rset
            self._llenar_tabla(rset.variantes)
            self.btn_adoptar.setEnabled(True)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _actualizar_canvas(self, sec, r) -> None:
        from graficos import graficar_seccion
        fig = graficar_seccion(sec, resultado_corte=r)
        self.canvas.mostrar_figura(fig)

    def _llenar_tabla(self, variantes) -> None:
        self.tabla.setRowCount(len(variantes))
        for i, v in enumerate(variantes):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(v.rank)))
            self.tabla.setItem(i, 1, QTableWidgetItem(f'{v.n_ramas}φ{v.phi}'))
            self.tabla.setItem(i, 2, QTableWidgetItem(f'{v.Avs:.0f}'))
            self.tabla.setItem(i, 3, QTableWidgetItem(f'{v.s*100:.1f}'))
        self.tabla.resizeColumnsToContents()

    def _adoptar_seleccion(self) -> None:
        if self._resultado is None:
            return
        row = self.tabla.currentRow()
        if row < 0 or self._rset is None:
            return
        v = self._rset.variantes[row]
        self._resultado.adoptar(phi=v.phi, n_ramas=v.n_ramas, s=v.s)
        self.crt.mostrar_resultado_corte(self._resultado)
        self._actualizar_canvas(self._seccion, self._resultado)
