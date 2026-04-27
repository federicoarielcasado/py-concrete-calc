"""
MÓDULO-09 / PLANTA  —  Modelado y propagación de cargas de planta estructural
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QSplitter,
)
from PyQt6.QtCore import Qt

from app.widgets.panel_crt import PanelCRT
from app.widgets.visor_3d import VisorPlotly3D
from app.widgets.selector_materiales import SelectorMateriales


class VentanaPlanta(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._planta = None
        self._propagacion = None
        self._setup_ui()

    # ── Construcción ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('MÓDULO-09 / PLANTA  —  MODELADO Y PROPAGACIÓN DE CARGAS')
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
        w.setFixedWidth(320)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(6)

        self.sel_mat = SelectorMateriales()
        lay.addWidget(self.sel_mat)

        lay.addWidget(self._grp_grilla())
        lay.addWidget(self._grp_losas())
        lay.addWidget(self._grp_secciones())
        lay.addWidget(self._grp_columnas())

        self.btn_modelar = QPushButton('EJECUTAR PROTOCOLO E-09')
        self.btn_modelar.setObjectName('btn_calcular')
        self.btn_modelar.clicked.connect(self._ejecutar)
        lay.addWidget(self.btn_modelar)

        self.btn_3d = QPushButton('ACTUALIZAR VISTA 3D')
        self.btn_3d.clicked.connect(self._actualizar_3d)
        self.btn_3d.setEnabled(False)
        lay.addWidget(self.btn_3d)

        lay.addStretch()
        return w

    def _grp_grilla(self) -> QGroupBox:
        grp = QGroupBox('GRILLA')
        f = QFormLayout(grp)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_ejes_x = QLineEdit('0, 5, 10')
        self.txt_ejes_y = QLineEdit('0, 4.5')
        f.addRow('Ejes X [m]:', self.txt_ejes_x)
        f.addRow('Ejes Y [m]:', self.txt_ejes_y)
        return grp

    def _grp_losas(self) -> QGroupBox:
        grp = QGroupBox('LOSAS (uniforme en toda la planta)')
        f = QFormLayout(grp)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.combo_tipo_losa = QComboBox()
        self.combo_tipo_losa.addItems(['2dir', '1dir'])
        self.txt_h_losa  = QLineEdit('0.14')
        self.txt_wD_losa = QLineEdit('1.5')
        self.txt_wL_losa = QLineEdit('2.0')
        self.combo_cond  = QComboBox()
        self.combo_cond.addItems(['ext_empotrado', 'ext_libre', 'int'])
        f.addRow('Tipo:', self.combo_tipo_losa)
        f.addRow('h [m]:', self.txt_h_losa)
        f.addRow('wD [kN/m²]:', self.txt_wD_losa)
        f.addRow('wL [kN/m²]:', self.txt_wL_losa)
        f.addRow('Condición borde:', self.combo_cond)
        return grp

    def _grp_secciones(self) -> QGroupBox:
        grp = QGroupBox('SECCIONES')
        f = QFormLayout(grp)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        lbl_v = QLabel('— VIGAS —')
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f.addRow(lbl_v)
        self.txt_bv  = QLineEdit('0.25')
        self.txt_hv  = QLineEdit('0.50')
        self.txt_rv  = QLineEdit('0.06')
        f.addRow('b [m]:', self.txt_bv)
        f.addRow('h [m]:', self.txt_hv)
        f.addRow('rec [m]:', self.txt_rv)

        lbl_c = QLabel('— COLUMNAS —')
        lbl_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f.addRow(lbl_c)
        self.txt_bc  = QLineEdit('0.30')
        self.txt_hc  = QLineEdit('0.30')
        self.txt_rc  = QLineEdit('0.06')
        f.addRow('b [m]:', self.txt_bc)
        f.addRow('h [m]:', self.txt_hc)
        f.addRow('rec [m]:', self.txt_rc)
        return grp

    def _grp_columnas(self) -> QGroupBox:
        grp = QGroupBox('COLUMNAS')
        f = QFormLayout(grp)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_h_entrepiso = QLineEdit('3.0')
        self.combo_tipo_col  = QComboBox()
        self.combo_tipo_col.addItems(['estribos', 'zunchada'])
        f.addRow('H entrepiso [m]:', self.txt_h_entrepiso)
        f.addRow('Tipo:', self.combo_tipo_col)
        return grp

    def _panel_resultados(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(4)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.visor = VisorPlotly3D()
        splitter.addWidget(self.visor)

        self.crt = PanelCRT()
        self.crt.mostrar_bienvenida('E-09 PLANTA')
        splitter.addWidget(self.crt)

        splitter.setSizes([480, 220])
        lay.addWidget(splitter, stretch=1)
        return w

    # ── Ejecución ────────────────────────────────────────────────────────────

    def _ejecutar(self) -> None:
        try:
            planta = self._construir_planta()
            self._planta = planta

            from hormigon.propagacion import propagar
            self._propagacion = propagar(planta)

            self.crt.mostrar_resultado_propagacion(self._propagacion)
            self._actualizar_3d()
            self.btn_3d.setEnabled(True)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _construir_planta(self):
        from hormigon.modelo import (
            ColumnaEsquema, Grilla, PanelLosa,
            PlantaEstructural, VigaEsquema,
        )
        from hormigon.secciones import SeccionRectangular

        horm = self.sel_mat.get_hormigon()
        acer = self.sel_mat.get_acero()

        def _f(txt): return float(txt.text().replace(',', '.'))
        def _lista(txt):
            return [float(v.strip()) for v in txt.text().split(',')]

        ejes_x = _lista(self.txt_ejes_x)
        ejes_y = _lista(self.txt_ejes_y)
        grilla = Grilla(ejes_x=ejes_x, ejes_y=ejes_y)

        sec_v = SeccionRectangular(
            b=_f(self.txt_bv), h=_f(self.txt_hv),
            recubrimiento=_f(self.txt_rv),
            hormigon=horm, acero=acer,
        )
        sec_c = SeccionRectangular(
            b=_f(self.txt_bc), h=_f(self.txt_hc),
            recubrimiento=_f(self.txt_rc),
            hormigon=horm, acero=acer,
        )

        tipo_losa = self.combo_tipo_losa.currentText()
        h_losa    = _f(self.txt_h_losa)
        wD_losa   = _f(self.txt_wD_losa)
        wL_losa   = _f(self.txt_wL_losa)
        cond      = self.combo_cond.currentText()
        h_entre   = _f(self.txt_h_entrepiso)
        tipo_col  = self.combo_tipo_col.currentText()

        planta = PlantaEstructural(grilla=grilla, hormigon=horm, acero=acer)

        for j in range(grilla.ny):
            for i in range(grilla.nx):
                planta.agregar_losa(PanelLosa(
                    id=f'L{j*grilla.nx+i}', i=i, j=j,
                    h=h_losa, tipo=tipo_losa,
                    wD=wD_losa, wL=wL_losa,
                    tipo_a=cond, tipo_b=cond,
                ))

        for j_eje in range(len(ejes_y)):
            planta.agregar_viga(VigaEsquema(
                id=f'Vx{j_eje}', dir='x', idx=j_eje,
                desde=0, hasta=grilla.nx,
                seccion=sec_v, extremo='columna',
            ))

        for i_eje in range(len(ejes_x)):
            planta.agregar_viga(VigaEsquema(
                id=f'Vy{i_eje}', dir='y', idx=i_eje,
                desde=0, hasta=grilla.ny,
                seccion=sec_v, extremo='columna',
            ))

        k = 0
        for iy in range(len(ejes_y)):
            for ix in range(len(ejes_x)):
                planta.agregar_columna(ColumnaEsquema(
                    id=f'C{k}', ix=ix, iy=iy,
                    seccion=sec_c, h_entrepiso=h_entre,
                    tipo=tipo_col,
                ))
                k += 1

        return planta

    def _actualizar_3d(self) -> None:
        if self._planta is None:
            return
        from graficos.modelo_3d import visualizar_planta_3d
        fig = visualizar_planta_3d(
            self._planta,
            propagacion=self._propagacion,
            titulo='Planta Estructural',
        )
        self.visor.mostrar_figura(fig)
