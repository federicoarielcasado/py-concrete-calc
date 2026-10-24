"""
MÓDULO-04 / LOSA
Losas en 1 dirección (art. 8.3.3) y 2 direcciones (DDM art. 13.6).
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QSpinBox,
    QStackedWidget,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_resultados import PanelResultados
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.entradas import con_scroll, instalar_validadores, validar_campos


class VentanaLosas(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._setup_ui()
        instalar_validadores(self)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('L-04  ·  Losas en 1 y 2 direcciones')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        sub = QLabel(
            'Usar para: losas en 1 dir. (coef. art. 8.3.3) o 2 dir. DDM (art. 13.6)  ·  '
            'Alimenta: V-05 con la carga distribuida sobre las vigas de borde'
        )
        sub.setObjectName('modulo_subtitulo')
        root.addWidget(sub)

        content = QWidget()
        hl = QHBoxLayout(content)
        hl.setContentsMargins(8, 8, 8, 8)
        hl.setSpacing(0)
        hl.addWidget(con_scroll(self._panel_entrada()))

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        hl.addWidget(sep)

        hl.addWidget(self._panel_resultados(), stretch=1)
        root.addWidget(content, stretch=1)

    # ── Panel de entrada ──────────────────────────────────────────────────────

    def _panel_entrada(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(330)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(6)

        self.sel_mat = SelectorMateriales()
        lay.addWidget(self.sel_mat)

        # Selector de tipo de losa
        grp_tipo = QGroupBox('TIPO DE LOSA')
        form_tipo = QFormLayout(grp_tipo)
        form_tipo.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.combo_tipo_losa = QComboBox()
        self.combo_tipo_losa.addItems(['1 DIRECCIÓN', '2 DIRECCIONES'])
        self.combo_tipo_losa.setToolTip(
            '<b>Tipo de losa</b><br>'
            '1 DIRECCIÓN: trabaja principalmente en una dirección (la/lb &lt; 0.5)<br>'
            'Método de coeficientes art. 8.3.3<br>'
            '2 DIRECCIONES: trabaja en ambas direcciones (la/lb ≥ 0.5)<br>'
            'Método Directo DDM art. 13.6'
        )
        self.combo_tipo_losa.currentIndexChanged.connect(self._cambiar_tipo_losa)
        form_tipo.addRow('Tipo:', self.combo_tipo_losa)
        lay.addWidget(grp_tipo)

        # Stack: campos según tipo
        self._stack_tipo = QStackedWidget()
        self._stack_tipo.addWidget(self._panel_1dir())
        self._stack_tipo.addWidget(self._panel_2dir())
        lay.addWidget(self._stack_tipo)

        self.btn_calc = QPushButton('Calcular')
        self.btn_calc.setObjectName('btn_calcular')
        self.btn_calc.clicked.connect(self._ejecutar)
        lay.addWidget(self.btn_calc)

        lay.addStretch()
        return w

    def _panel_1dir(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        grp_geo = QGroupBox('GEOMETRÍA')
        form_geo = QFormLayout(grp_geo)
        form_geo.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_h = QLineEdit('0.20')
        self.entrada_h.setToolTip(
            '<b>h</b> — espesor total de la losa [m]<br>'
            'Mínimo por deflexiones (tabla 9.5a):<br>'
            'ln/28 (un extremo cont.), ln/24 (dos cont.), ln/20 (voladizo)<br>'
            'Adoptar múltiplo de 0.01 m — típico: 0.10–0.25 m'
        )
        self.entrada_rec = QLineEdit('0.025')
        self.entrada_rec.setToolTip(
            '<b>rec</b> — recubrimiento mecánico hasta eje de armadura [m]<br>'
            'Mínimo CIRSOC art. 7.7: 0.019 m (interior), 0.025 m (exterior)<br>'
            '<i>rec = rec_hormigón + d_barra/2 ≈ 0.020–0.030 m</i>'
        )
        self.entrada_ln = QLineEdit('4.00')
        self.entrada_ln.setToolTip(
            '<b>ln</b> — luz libre entre caras de apoyos [m]<br>'
            'Art. 8.3.3: todos los tramos deben tener longitudes aproximadamente iguales<br>'
            'Diferencia admitida: ±20% respecto al tramo mayor'
        )
        form_geo.addRow('h [m]:', self.entrada_h)
        form_geo.addRow('rec [m]:', self.entrada_rec)
        form_geo.addRow('ln [m]:', self.entrada_ln)
        lay.addWidget(grp_geo)

        grp_car = QGroupBox('CARGAS Y CONFIGURACIÓN')
        form_car = QFormLayout(grp_car)
        form_car.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_wD = QLineEdit('5.0')
        self.entrada_wD.setToolTip(
            '<b>wD</b> — carga muerta superficial de servicio [kN/m²] — sin mayorar<br>'
            'Incluye: peso propio losa (25·h kN/m²) + piso terminado + tabiques<br>'
            '<i>Piso terminado ≈ 1.5–2.5 kN/m². Tabiques livianos ≈ 1.0 kN/m²</i>'
        )
        self.entrada_wL = QLineEdit('3.0')
        self.entrada_wL.setToolTip(
            '<b>wL</b> — carga viva superficial de servicio [kN/m²] — sin mayorar<br>'
            'CIRSOC tabla C4.2: vivienda=2.0, oficinas=2.4, depósito=4.8 kN/m²<br>'
            '<i>El programa aplica 1.4·wD + 1.7·wL internamente</i>'
        )
        self.spin_tramos = QSpinBox()
        self.spin_tramos.setRange(1, 10)
        self.spin_tramos.setValue(3)
        self.spin_tramos.setToolTip(
            '<b>N° tramos</b><br>'
            'Art. 8.3.3: se requieren ≥ 2 tramos para usar el método de coeficientes<br>'
            '1 tramo = losa simplemente apoyada o voladizo'
        )
        self.combo_extremo = QComboBox()
        self.combo_extremo.addItems(['libre', 'viga', 'columna'])
        self.combo_extremo.setToolTip(
            '<b>Extremo exterior</b> — condición del apoyo en el borde (art. 8.3.3)<br>'
            'libre: sin restricción al giro (apoyo simple)<br>'
            'viga: monolítico con viga de borde (restricción parcial)<br>'
            'columna: monolítico con columna (mayor restricción)'
        )
        form_car.addRow('wD [kN/m²]:', self.entrada_wD)
        form_car.addRow('wL [kN/m²]:', self.entrada_wL)
        form_car.addRow('N° tramos:', self.spin_tramos)
        form_car.addRow('Extremo:', self.combo_extremo)
        lay.addWidget(grp_car)
        return w

    def _panel_2dir(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        grp_geo = QGroupBox('GEOMETRÍA')
        form_geo = QFormLayout(grp_geo)
        form_geo.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.e2_la = QLineEdit('4.0')
        self.e2_la.setToolTip(
            '<b>la</b> — vano corto (dirección a) [m]<br>'
            'Debe ser la ≤ lb. Condición 2 dir.: m = la/lb ≥ 0.5<br>'
            '<i>Si m &lt; 0.5 usar losa 1 dirección</i>'
        )
        self.e2_lb = QLineEdit('5.0')
        self.e2_lb.setToolTip('<b>lb</b> — vano largo (dirección b) [m] — lb ≥ la')
        self.e2_h = QLineEdit('0.18')
        self.e2_h.setToolTip(
            '<b>h</b> — espesor total de la losa [m]<br>'
            'Mínimo CIRSOC art. 9.5.3: h ≥ la/33 (panel interior)<br>'
            'Típico: 0.12–0.25 m'
        )
        self.e2_rec = QLineEdit('0.025')
        self.e2_rec.setToolTip(
            '<b>rec</b> — recubrimiento mecánico a la armadura exterior [m]<br>'
            'La armadura de la dir. corta va en la capa inferior (d_a mayor)<br>'
            'La armadura de la dir. larga va en la capa superior (d_b = d_a − 20 mm aprox.)'
        )
        form_geo.addRow('la [m]:', self.e2_la)
        form_geo.addRow('lb [m]:', self.e2_lb)
        form_geo.addRow('h [m]:', self.e2_h)
        form_geo.addRow('rec [m]:', self.e2_rec)
        lay.addWidget(grp_geo)

        grp_car = QGroupBox('CARGAS')
        form_car = QFormLayout(grp_car)
        form_car.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.e2_wD = QLineEdit('5.0')
        self.e2_wD.setToolTip(
            '<b>wD</b> — carga muerta superficial de servicio [kN/m²] — sin mayorar<br>'
            'Incluye: peso propio losa (25·h) + piso terminado + tabiques'
        )
        self.e2_wL = QLineEdit('3.0')
        self.e2_wL.setToolTip(
            '<b>wL</b> — carga viva superficial de servicio [kN/m²] — sin mayorar<br>'
            '<i>El programa aplica wu = 1.4·wD + 1.7·wL internamente</i>'
        )
        form_car.addRow('wD [kN/m²]:', self.e2_wD)
        form_car.addRow('wL [kN/m²]:', self.e2_wL)
        lay.addWidget(grp_car)

        grp_borde = QGroupBox('CONDICIÓN DE BORDE')
        form_borde = QFormLayout(grp_borde)
        form_borde.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.combo_tipo_a = QComboBox()
        self.combo_tipo_a.addItems(['int', 'ext_libre', 'ext_empotrado'])
        self.combo_tipo_a.setToolTip(
            '<b>Condición del tramo — dirección a (corta)</b><br>'
            'int: tramo interior (ambos extremos continuos)<br>'
            'ext_libre: extremo sin restricción al giro (apoyo simple)<br>'
            'ext_empotrado: extremo con viga o muro (restricción alta)'
        )
        self.combo_tipo_b = QComboBox()
        self.combo_tipo_b.addItems(['int', 'ext_libre', 'ext_empotrado'])
        self.combo_tipo_b.setToolTip(
            '<b>Condición del tramo — dirección b (larga)</b><br>'
            'int: tramo interior (ambos extremos continuos)<br>'
            'ext_libre: extremo sin restricción al giro<br>'
            'ext_empotrado: extremo con viga o muro'
        )
        form_borde.addRow('Dir. a (corta):', self.combo_tipo_a)
        form_borde.addRow('Dir. b (larga):', self.combo_tipo_b)
        lay.addWidget(grp_borde)
        return w

    # ── Panel de resultados ───────────────────────────────────────────────────

    def _panel_resultados(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 0, 0, 0)
        lay.setSpacing(4)

        self.panel_res = PanelResultados()
        self.panel_res.mostrar_bienvenida('L-04 · LOSAS')
        lay.addWidget(self.panel_res)

        self.canvas = CanvasMatplotlib()
        lay.addWidget(self.canvas, stretch=1)
        return w

    # ── Lógica ────────────────────────────────────────────────────────────────

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'tipo_losa':  self.combo_tipo_losa.currentIndex(),
            'h':    self.entrada_h.text(),   'rec':  self.entrada_rec.text(),
            'ln':   self.entrada_ln.text(),  'wD':   self.entrada_wD.text(),
            'wL':   self.entrada_wL.text(),  'tramos': self.spin_tramos.value(),
            'extremo': self.combo_extremo.currentText(),
            'la':    self.e2_la.text(),   'lb':    self.e2_lb.text(),
            'h2':    self.e2_h.text(),    'rec2':  self.e2_rec.text(),
            'wD2':   self.e2_wD.text(),   'wL2':   self.e2_wL.text(),
            'tipo_a': self.combo_tipo_a.currentText(),
            'tipo_b': self.combo_tipo_b.currentText(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.combo_tipo_losa.setCurrentIndex(d.get('tipo_losa', 0))
        self.entrada_h.setText(d.get('h', '0.20'))
        self.entrada_rec.setText(d.get('rec', '0.025'))
        self.entrada_ln.setText(d.get('ln', '4.00'))
        self.entrada_wD.setText(d.get('wD', '5.0'))
        self.entrada_wL.setText(d.get('wL', '3.0'))
        self.spin_tramos.setValue(d.get('tramos', 3))
        self.combo_extremo.setCurrentText(d.get('extremo', 'libre'))
        self.e2_la.setText(d.get('la', '4.0'))
        self.e2_lb.setText(d.get('lb', '5.0'))
        self.e2_h.setText(d.get('h2', '0.18'))
        self.e2_rec.setText(d.get('rec2', '0.025'))
        self.e2_wD.setText(d.get('wD2', '5.0'))
        self.e2_wL.setText(d.get('wL2', '3.0'))
        self.combo_tipo_a.setCurrentText(d.get('tipo_a', 'int'))
        self.combo_tipo_b.setCurrentText(d.get('tipo_b', 'int'))

    def _cambiar_tipo_losa(self, idx: int) -> None:
        self._stack_tipo.setCurrentIndex(idx)

    def _ejecutar(self) -> None:
        if not validar_campos(self):
            return
        if self.combo_tipo_losa.currentIndex() == 0:
            self._ejecutar_1dir()
        else:
            self._ejecutar_2dir()

    def _ejecutar_1dir(self) -> None:
        from elementos.losa_1dir import Losa1Dir
        try:
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()
            h    = float(self.entrada_h.text().replace(',', '.'))
            rec  = float(self.entrada_rec.text().replace(',', '.'))
            ln   = float(self.entrada_ln.text().replace(',', '.'))
            wD   = float(self.entrada_wD.text().replace(',', '.'))
            wL   = float(self.entrada_wL.text().replace(',', '.'))
            n    = self.spin_tramos.value()
            ext  = self.combo_extremo.currentText()

            r = Losa1Dir(
                h=h, recubrimiento=rec, hormigon=horm, acero=acer,
                wD=wD, wL=wL, ln=ln, n_tramos=n, extremo=ext,
            ).calcular()
            self._resultado = r
            self.panel_res.mostrar_resultado_losa(r)
            from graficos import graficar_losa_1dir
            self.canvas.mostrar_figura(graficar_losa_1dir(r))

        except Exception as e:
            self.panel_res.mostrar_error(str(e))

    def _ejecutar_2dir(self) -> None:
        from hormigon.losas import calcular_losa_2dir
        try:
            horm   = self.sel_mat.get_hormigon()
            acer   = self.sel_mat.get_acero()
            la     = float(self.e2_la.text().replace(',', '.'))
            lb     = float(self.e2_lb.text().replace(',', '.'))
            h      = float(self.e2_h.text().replace(',', '.'))
            rec    = float(self.e2_rec.text().replace(',', '.'))
            wD     = float(self.e2_wD.text().replace(',', '.'))
            wL     = float(self.e2_wL.text().replace(',', '.'))
            tipo_a = self.combo_tipo_a.currentText()
            tipo_b = self.combo_tipo_b.currentText()

            wu = 1.4 * wD + 1.7 * wL

            r = calcular_losa_2dir(
                la=la, lb=lb, h=h, recubrimiento=rec,
                hormigon=horm, acero=acer,
                wu=wu, tipo_a=tipo_a, tipo_b=tipo_b,
            )
            self._resultado = r
            self.panel_res.mostrar_resultado_losa_2dir(r)
            from graficos import graficar_losa_2dir
            self.canvas.mostrar_figura(graficar_losa_2dir(r))

        except Exception as e:
            self.panel_res.mostrar_error(str(e))
