"""
MÓDULO-01 / FLEXIÓN SIMPLE
Dimensionado de armadura de flexión con sección rectangular o T.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_crt import PanelCRT
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.selector_seccion import SelectorSeccion


class VentanaFlexion(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._seccion   = None
        self._setup_ui()

    # ── Construcción de la UI ────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Título
        titulo = QLabel('MÓDULO-01 / FLEXIÓN SIMPLE')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        # Contenido
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

        # Solicitación
        grp = QGroupBox('SOLICITACIÓN')
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_Mu = QLineEdit('52')
        self.entrada_Mu.setToolTip(
            '<b>Mu</b> — momento último mayorado [kN·m]<br>'
            'Del análisis con cargas mayoradas (art. 9.2.1)<br>'
            'Combinación usual: Mu = 1.4·MD + 1.7·ML<br>'
            '<i>Viga simple, carga uniforme: Mu = wu·L²/8</i>'
        )
        form.addRow('Mu [kNm]:', self.entrada_Mu)
        lay.addWidget(grp)

        # Botones
        self.btn_calc = QPushButton('EJECUTAR PROTOCOLO F-01')
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

        # CRT
        self.crt = PanelCRT()
        self.crt.setFixedHeight(190)
        self.crt.mostrar_bienvenida('F-01 FLEXIÓN SIMPLE')
        lay.addWidget(self.crt)

        # Canvas + tabla
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

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(['RK', 'CONFIG', 'As [cm²]', 'φMn [kNm]', 'sep [mm]'])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemDoubleClicked.connect(self._adoptar_variante)
        lay.addWidget(self.tabla)

        self.btn_adoptar = QPushButton('REGISTRAR CONFIGURACIÓN')
        self.btn_adoptar.setEnabled(False)
        self.btn_adoptar.clicked.connect(self._adoptar_seleccion)
        lay.addWidget(self.btn_adoptar)
        return w

    # ── Lógica ───────────────────────────────────────────────────────────────

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'seccion':    self.sel_sec.get_datos(),
            'Mu':         self.entrada_Mu.text(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.sel_sec.set_datos(d.get('seccion', {}))
        self.entrada_Mu.setText(d.get('Mu', '52'))

    def _ejecutar(self) -> None:
        from hormigon.flexion import dimensionar_flexion
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            Mu   = float(self.entrada_Mu.text().replace(',', '.'))

            r = dimensionar_flexion(sec, Mu=Mu)
            self._resultado = r
            self._seccion   = sec

            self.crt.mostrar_resultado_flexion(r)
            self._actualizar_canvas(sec, r)
            self.btn_var.setEnabled(True)
            self.tabla.setRowCount(0)
            self.btn_adoptar.setEnabled(False)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _ver_variantes(self) -> None:
        from hormigon.flexion import dimensionar_flexion_variantes
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            Mu   = float(self.entrada_Mu.text().replace(',', '.'))

            rset = dimensionar_flexion_variantes(sec, Mu=Mu)
            self._rset = rset
            self._llenar_tabla(rset.variantes)
            self.btn_adoptar.setEnabled(True)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _actualizar_canvas(self, sec, r) -> None:
        from graficos import graficar_seccion
        fig = graficar_seccion(sec, resultado_flex=r)
        self.canvas.mostrar_figura(fig)

    def _llenar_tabla(self, variantes) -> None:
        self.tabla.setRowCount(len(variantes))
        for i, v in enumerate(variantes):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(v.rank)))
            self.tabla.setItem(i, 1, QTableWidgetItem(f'{v.n}φ{v.phi}'))
            self.tabla.setItem(i, 2, QTableWidgetItem(f'{v.As:.2f}'))
            self.tabla.setItem(i, 3, QTableWidgetItem(f'{v.phi_Mn:.1f}'))
            self.tabla.setItem(i, 4, QTableWidgetItem(f'{v.separacion:.0f}'))
        self.tabla.resizeColumnsToContents()

    def _adoptar_variante(self, item) -> None:
        self._adoptar_seleccion()

    def _adoptar_seleccion(self) -> None:
        if self._resultado is None:
            return
        row = self.tabla.currentRow()
        if row < 0:
            return
        v = self._rset.variantes[row]
        self._resultado.adoptar(phi=v.phi, n=v.n)
        self.crt.mostrar_resultado_flexion(self._resultado)
        self._actualizar_canvas(self._seccion, self._resultado)
