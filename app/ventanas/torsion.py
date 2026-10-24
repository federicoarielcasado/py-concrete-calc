"""
MÓDULO-06 / TORSIÓN  —  Art. 11.6 CIRSOC 201-2005
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_resultados import PanelResultados
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.selector_seccion import SelectorSeccion
from app.widgets.entradas import con_scroll, instalar_validadores, validar_campos


class VentanaTorsion(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._setup_ui()
        instalar_validadores(self)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('T-06  ·  Torsión — corte y torsión combinados')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        sub = QLabel(
            'Usar cuando: Tu > Tu_min — torsión no despreciable combinada con corte (art. 11.6)  ·  '
            'Complementa C-02  ·  Datos: Tu, Vu, sección'
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
        self.entrada_Tu    = QLineEdit('25.0')
        self.entrada_Tu.setToolTip(
            '<b>Tu</b> — torsión última mayorada [kN·m]<br>'
            'Verificar si Tu > Tu,min antes de armar (art. 11.6.1):<br>'
            "<i>Tu,min = φ·(√f'c/12)·(Acp²/pcp)</i>"
        )
        self.entrada_Vu    = QLineEdit('80.0')
        self.entrada_Vu.setToolTip(
            '<b>Vu</b> — cortante último mayorado [kN]<br>'
            'En la misma sección donde actúa la torsión'
        )
        self.entrada_c_est = QLineEdit('0.04')
        self.entrada_c_est.setToolTip(
            '<b>c_estribo</b> — recubrimiento al eje del estribo cerrado [m]<br>'
            'c = rec_hormigón + d_estribo/2<br>'
            'Típico: 0.04 m (interior), 0.05 m (exterior/húmedo)'
        )
        self.combo_theta   = QComboBox()
        self.combo_theta.addItems(['45', '30', '35', '40', '50', '55', '60'])
        self.combo_theta.setToolTip(
            '<b>θ</b> — ángulo de las bielas comprimidas [°]<br>'
            'Rango permitido CIRSOC art. 11.6: 30°–60°<br>'
            'θ = 45° es el más conservador y habitual<br>'
            '<i>Menor θ → más armadura transversal y menos longitudinal</i>'
        )
        self.chk_equilibrio = QCheckBox('Torsión de equilibrio')
        self.chk_equilibrio.setChecked(True)
        self.chk_equilibrio.setToolTip(
            '<b>Tipo de torsión — CIRSOC art. 11.6.2</b><br>'
            'MARCADO — equilibrio: la torsión es necesaria para el equilibrio<br>'
            '→ diseñar para Tu completo, no se puede redistribuir<br>'
            'DESMARCADO — compatibilidad: puede reducirse a Tu,min (art. 11.6.2.2)'
        )
        form.addRow('Tu [kNm]:', self.entrada_Tu)
        form.addRow('Vu [kN]:', self.entrada_Vu)
        form.addRow('c_estribo [m]:', self.entrada_c_est)
        form.addRow('θ [°]:', self.combo_theta)
        form.addRow('', self.chk_equilibrio)
        lay.addWidget(grp)

        self.btn_calc = QPushButton('Calcular')
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

        self.panel_res = PanelResultados()
        self.panel_res.mostrar_bienvenida('T-06 · TORSIÓN')
        lay.addWidget(self.panel_res)

        self.canvas = CanvasMatplotlib()
        lay.addWidget(self.canvas, stretch=1)
        return w

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'seccion':    self.sel_sec.get_datos(),
            'Tu':         self.entrada_Tu.text(),
            'Vu':         self.entrada_Vu.text(),
            'c_est':      self.entrada_c_est.text(),
            'theta':      self.combo_theta.currentText(),
            'equilibrio': self.chk_equilibrio.isChecked(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.sel_sec.set_datos(d.get('seccion', {}))
        self.entrada_Tu.setText(d.get('Tu', '25.0'))
        self.entrada_Vu.setText(d.get('Vu', '80.0'))
        self.entrada_c_est.setText(d.get('c_est', '0.04'))
        self.combo_theta.setCurrentText(d.get('theta', '45'))
        self.chk_equilibrio.setChecked(d.get('equilibrio', True))

    def _ejecutar(self) -> None:
        if not validar_campos(self):
            return
        from hormigon.torsion import calcular_torsion
        try:
            horm   = self.sel_mat.get_hormigon()
            acer   = self.sel_mat.get_acero()
            sec    = self.sel_sec.get_seccion(horm, acer)
            Tu     = float(self.entrada_Tu.text().replace(',', '.'))
            Vu     = float(self.entrada_Vu.text().replace(',', '.'))
            c_est  = float(self.entrada_c_est.text().replace(',', '.'))
            theta  = float(self.combo_theta.currentText())
            equil  = self.chk_equilibrio.isChecked()

            r = calcular_torsion(
                seccion=sec, Tu=Tu, Vu=Vu,
                c_est=c_est, theta_deg=theta, equilibrio=equil,
            )
            self._resultado = r
            self.panel_res.mostrar_resultado_torsion(r)
            self._actualizar_canvas(r)

        except Exception as e:
            self.panel_res.mostrar_error(str(e))

    def _actualizar_canvas(self, r) -> None:
        from graficos import graficar_torsion
        self.canvas.mostrar_figura(graficar_torsion(r))
