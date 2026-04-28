"""
MÓDULO-05 / VIGA  —  Simple, Voladizo, Continua
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QSpinBox,
    QStackedWidget,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_crt import PanelCRT
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.selector_seccion import SelectorSeccion


class VentanaViga(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('MÓDULO-05 / VIGA  —  SIMPLE / VOLADIZO / CONTINUA')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        sub = QLabel(
            'Usar para: diseñar vigas con armadura longitudinal y estribos  ·  '
            'Recibe: cargas de L-04 o E-09  ·  Alimenta: P-03 con las reacciones de apoyo'
        )
        sub.setObjectName('modulo_subtitulo')
        root.addWidget(sub)

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

        # Tipo de viga
        grp_tipo = QGroupBox('TIPO')
        form_tipo = QFormLayout(grp_tipo)
        form_tipo.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(['SIMPLE', 'VOLADIZO', 'CONTINUA'])
        self.combo_tipo.setToolTip(
            '<b>Esquema estático de la viga</b><br>'
            'SIMPLE: dos apoyos — Mu_max = wu·L²/8<br>'
            'VOLADIZO: empotramiento + extremo libre — Mu_max = wu·L²/2<br>'
            'CONTINUA: método de coeficientes art. 8.3.3 (≥ 2 tramos)'
        )
        self.combo_tipo.currentIndexChanged.connect(self._cambiar_tipo)
        form_tipo.addRow('Viga:', self.combo_tipo)
        lay.addWidget(grp_tipo)

        # Parámetros — apilados por tipo
        self._stack = QStackedWidget()
        self._stack.addWidget(self._panel_simple())
        self._stack.addWidget(self._panel_voladizo())
        self._stack.addWidget(self._panel_continua())
        lay.addWidget(self._stack)

        self.btn_calc = QPushButton('EJECUTAR PROTOCOLO V-05')
        self.btn_calc.setObjectName('btn_calcular')
        self.btn_calc.clicked.connect(self._ejecutar)
        lay.addWidget(self.btn_calc)

        lay.addStretch()
        return w

    def _panel_simple(self) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.s_L  = QLineEdit('6.0')
        self.s_L.setToolTip(
            '<b>L</b> — luz entre ejes de apoyo [m]<br>'
            'Para cálculo de momentos: usar luz libre + d_apoyo/2 en cada extremo'
        )
        self.s_wD = QLineEdit('20.0')
        self.s_wD.setToolTip(
            '<b>wD</b> — carga muerta distribuida de servicio [kN/m] — sin mayorar<br>'
            'Incluye: peso propio viga (b·h·25 kN/m³) + losa + revoques + tabiques'
        )
        self.s_wL = QLineEdit('15.0')
        self.s_wL.setToolTip(
            '<b>wL</b> — carga viva distribuida de servicio [kN/m] — sin mayorar<br>'
            '<i>El programa aplica wu = 1.4·wD + 1.7·wL internamente</i>'
        )
        f.addRow('L [m]:', self.s_L)
        f.addRow('wD [kN/m]:', self.s_wD)
        f.addRow('wL [kN/m]:', self.s_wL)
        return w

    def _panel_voladizo(self) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.v_L  = QLineEdit('2.0')
        self.v_L.setToolTip('<b>L</b> — longitud del voladizo desde el eje del apoyo [m]')
        self.v_wD = QLineEdit('10.0')
        self.v_wD.setToolTip('<b>wD</b> — carga muerta distribuida de servicio [kN/m] — sin mayorar')
        self.v_wL = QLineEdit('8.0')
        self.v_wL.setToolTip('<b>wL</b> — carga viva distribuida de servicio [kN/m] — sin mayorar')
        self.v_PD = QLineEdit('0.0')
        self.v_PD.setToolTip('<b>PD</b> — carga puntual muerta en extremo libre [kN] — sin mayorar')
        self.v_PL = QLineEdit('0.0')
        self.v_PL.setToolTip('<b>PL</b> — carga puntual viva en extremo libre [kN] — sin mayorar')
        f.addRow('L [m]:', self.v_L)
        f.addRow('wD [kN/m]:', self.v_wD)
        f.addRow('wL [kN/m]:', self.v_wL)
        f.addRow('PD [kN]:', self.v_PD)
        f.addRow('PL [kN]:', self.v_PL)
        return w

    def _panel_continua(self) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.c_ln  = QLineEdit('5.0')
        self.c_ln.setToolTip(
            '<b>ln</b> — luz libre entre caras de apoyos [m]<br>'
            'Art. 8.3.3: todos los tramos deben tener longitudes aproximadamente iguales'
        )
        self.c_wD  = QLineEdit('20.0')
        self.c_wD.setToolTip('<b>wD</b> — carga muerta distribuida de servicio [kN/m] — sin mayorar')
        self.c_wL  = QLineEdit('15.0')
        self.c_wL.setToolTip('<b>wL</b> — carga viva distribuida de servicio [kN/m] — sin mayorar')
        self.c_n   = QSpinBox()
        self.c_n.setRange(2, 10)
        self.c_n.setValue(3)
        self.c_n.setToolTip(
            '<b>N° tramos</b><br>'
            'Mínimo 2 tramos para aplicar el método de coeficientes (art. 8.3.3)'
        )
        self.c_ext = QComboBox()
        self.c_ext.addItems(['libre', 'viga', 'columna'])
        self.c_ext.setToolTip(
            '<b>Extremo exterior</b> — condición de apoyo en el borde<br>'
            'libre: sin restricción al giro (apoyo simple)<br>'
            'viga: monolítico con viga de borde<br>'
            'columna: monolítico con columna (mayor momento negativo en apoyo)'
        )
        f.addRow('ln [m]:', self.c_ln)
        f.addRow('wD [kN/m]:', self.c_wD)
        f.addRow('wL [kN/m]:', self.c_wL)
        f.addRow('N° tramos:', self.c_n)
        f.addRow('Extremo:', self.c_ext)
        return w

    def _panel_resultados(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(4)

        self.crt = PanelCRT()
        self.crt.setFixedHeight(200)
        self.crt.mostrar_bienvenida('V-05 VIGA')
        lay.addWidget(self.crt)

        self.canvas = CanvasMatplotlib()
        lay.addWidget(self.canvas, stretch=1)
        return w

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'seccion':    self.sel_sec.get_datos(),
            'tipo':       self.combo_tipo.currentIndex(),
            's_L':  self.s_L.text(),  's_wD': self.s_wD.text(), 's_wL': self.s_wL.text(),
            'v_L':  self.v_L.text(),  'v_wD': self.v_wD.text(), 'v_wL': self.v_wL.text(),
            'v_PD': self.v_PD.text(), 'v_PL': self.v_PL.text(),
            'c_ln': self.c_ln.text(), 'c_wD': self.c_wD.text(), 'c_wL': self.c_wL.text(),
            'c_n':  self.c_n.value(), 'c_ext': self.c_ext.currentText(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.sel_sec.set_datos(d.get('seccion', {}))
        self.combo_tipo.setCurrentIndex(d.get('tipo', 0))
        self.s_L.setText(d.get('s_L', '6.0'));  self.s_wD.setText(d.get('s_wD', '20.0'))
        self.s_wL.setText(d.get('s_wL', '15.0'))
        self.v_L.setText(d.get('v_L', '2.0'));  self.v_wD.setText(d.get('v_wD', '10.0'))
        self.v_wL.setText(d.get('v_wL', '8.0'))
        self.v_PD.setText(d.get('v_PD', '0.0')); self.v_PL.setText(d.get('v_PL', '0.0'))
        self.c_ln.setText(d.get('c_ln', '5.0')); self.c_wD.setText(d.get('c_wD', '20.0'))
        self.c_wL.setText(d.get('c_wL', '15.0')); self.c_n.setValue(d.get('c_n', 3))
        self.c_ext.setCurrentText(d.get('c_ext', 'libre'))

    def _cambiar_tipo(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)

    def _ejecutar(self) -> None:
        idx = self.combo_tipo.currentIndex()
        if idx == 0:
            self._ejecutar_simple()
        elif idx == 1:
            self._ejecutar_voladizo()
        else:
            self._ejecutar_continua()

    def _ejecutar_simple(self) -> None:
        from elementos.viga import VigaSimple
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            L    = float(self.s_L.text().replace(',', '.'))
            wD   = float(self.s_wD.text().replace(',', '.'))
            wL   = float(self.s_wL.text().replace(',', '.'))

            r = VigaSimple(sec, L=L, wD=wD, wL=wL).calcular()
            self._resultado = r
            self.crt.mostrar_resultado_viga(r)
            self._actualizar_canvas_iso(r)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _ejecutar_voladizo(self) -> None:
        from elementos.viga import VigaVoladizo
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            L    = float(self.v_L.text().replace(',', '.'))
            wD   = float(self.v_wD.text().replace(',', '.'))
            wL   = float(self.v_wL.text().replace(',', '.'))
            PD   = float(self.v_PD.text().replace(',', '.'))
            PL   = float(self.v_PL.text().replace(',', '.'))

            r = VigaVoladizo(sec, L=L, wD=wD, wL=wL, PD=PD, PL=PL).calcular()
            self._resultado = r
            self.crt.mostrar_resultado_viga(r)
            self._actualizar_canvas_iso(r)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _ejecutar_continua(self) -> None:
        from elementos.viga import VigaContinua
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            sec  = self.sel_sec.get_seccion(horm, acer)
            ln   = float(self.c_ln.text().replace(',', '.'))
            wD   = float(self.c_wD.text().replace(',', '.'))
            wL   = float(self.c_wL.text().replace(',', '.'))
            n    = self.c_n.value()
            ext  = self.c_ext.currentText()

            r = VigaContinua(sec, ln=ln, wD=wD, wL=wL, n_tramos=n, extremo=ext).calcular()
            self._resultado = r
            self.crt.mostrar_resultado_viga_continua(r)
            self._actualizar_canvas_continua(r)

        except Exception as e:
            self.crt.mostrar_error(str(e))

    def _actualizar_canvas_iso(self, r) -> None:
        from graficos import graficar_viga
        self.canvas.mostrar_figura(graficar_viga(r))

    def _actualizar_canvas_continua(self, r) -> None:
        from graficos import graficar_viga_continua
        self.canvas.mostrar_figura(graficar_viga_continua(r))
