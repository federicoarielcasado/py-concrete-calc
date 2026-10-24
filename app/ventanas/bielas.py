"""
MÓDULO-08 / MÉNSULA CORTA  —  Biela-Tirante Art. 10.7 + 11.9
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_mpl import CanvasMatplotlib
from app.widgets.panel_resultados import PanelResultados
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.entradas import con_scroll, instalar_validadores, validar_campos


class VentanaBielas(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._resultado = None
        self._setup_ui()
        instalar_validadores(self)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('M-08  ·  Ménsula corta — biela-tirante')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        sub = QLabel(
            'Usar para: ménsulas cortas con a/d < 1 por método de bielas y tirantes (art. 10.7 + 11.9)  ·  '
            'Elemento especial — independiente del flujo principal de diseño'
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

        grp = QGroupBox('GEOMETRÍA DE LA MÉNSULA')
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_b   = QLineEdit('300')
        self.entrada_b.setToolTip(
            '<b>b</b> — ancho de la sección de la ménsula [mm]<br>'
            '<i>ATENCIÓN: este campo está en MILÍMETROS (no metros)</i><br>'
            'Rango típico: 200–600 mm'
        )
        self.entrada_d   = QLineEdit('0.40')
        self.entrada_d.setToolTip(
            '<b>d</b> — altura efectiva de la ménsula [m]<br>'
            'd = h − rec (distancia de la fibra comprimida al eje del tirante principal)'
        )
        self.entrada_a   = QLineEdit('0.20')
        self.entrada_a.setToolTip(
            '<b>a</b> — distancia de la carga al borde de la columna [m]<br>'
            'Ménsula corta si a/d < 1 (CIRSOC art. 11.9)<br>'
            'Típico: a ≤ d para que aplique el método de bielas y tirantes'
        )
        form.addRow('b [mm]:', self.entrada_b)
        form.addRow('d [m]:', self.entrada_d)
        form.addRow('a [m]:', self.entrada_a)
        lay.addWidget(grp)

        grp2 = QGroupBox('SOLICITACIÓN')
        form2 = QFormLayout(grp2)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.entrada_Vu   = QLineEdit('150.0')
        self.entrada_Vu.setToolTip(
            '<b>Vu</b> — cortante último mayorado [kN]<br>'
            'Fuerza vertical de la viga o carga que apoya sobre la ménsula'
        )
        self.entrada_Nu   = QLineEdit('0.0')
        self.entrada_Nu.setToolTip(
            '<b>Nu</b> — fuerza horizontal mayorada [kN]<br>'
            'CIRSOC art. 11.9.3.4: Nu ≥ 0.2·Vu salvo que se garantice deslizamiento libre<br>'
            'Positivo si tracción (la viga se aleja de la columna)'
        )
        self.combo_betas  = QComboBox()
        self.combo_betas.addItems([
            '0.60 — botella sin refuerzo',
            '0.75 — botella con refuerzo',
            '1.00 — prismática',
            '0.40 — con tracción',
        ])
        self.combo_betas.setToolTip(
            '<b>β_s</b> — factor de resistencia de la biela (art. 10.7.2.1)<br>'
            '0.60 — biela en botella sin refuerzo transversal (caso más frecuente)<br>'
            '0.75 — biela en botella con armadura de confinamiento<br>'
            '1.00 — biela prismática (compresión uniforme)<br>'
            '0.40 — zona con tracción transversal significativa'
        )
        form2.addRow('Vu [kN]:', self.entrada_Vu)
        form2.addRow('Nu [kN]:', self.entrada_Nu)
        form2.addRow('β_s biela:', self.combo_betas)
        lay.addWidget(grp2)

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
        self.panel_res.mostrar_bienvenida('M-08 · MÉNSULA CORTA')
        lay.addWidget(self.panel_res)

        self.canvas = CanvasMatplotlib()
        lay.addWidget(self.canvas, stretch=1)
        return w

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'b':    self.entrada_b.text(),
            'd':    self.entrada_d.text(),
            'a':    self.entrada_a.text(),
            'Vu':   self.entrada_Vu.text(),
            'Nu':   self.entrada_Nu.text(),
            'betas': self.combo_betas.currentIndex(),
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        self.entrada_b.setText(d.get('b', '300'))
        self.entrada_d.setText(d.get('d', '0.40'))
        self.entrada_a.setText(d.get('a', '0.20'))
        self.entrada_Vu.setText(d.get('Vu', '150.0'))
        self.entrada_Nu.setText(d.get('Nu', '0.0'))
        self.combo_betas.setCurrentIndex(d.get('betas', 0))

    def _ejecutar(self) -> None:
        if not validar_campos(self):
            return
        from hormigon.bielas import dimensionar_mensula
        try:
            horm  = self.sel_mat.get_hormigon()
            acer  = self.sel_mat.get_acero()
            b_mm  = float(self.entrada_b.text().replace(',', '.'))
            d     = float(self.entrada_d.text().replace(',', '.'))
            a     = float(self.entrada_a.text().replace(',', '.'))
            Vu    = float(self.entrada_Vu.text().replace(',', '.'))
            Nu    = float(self.entrada_Nu.text().replace(',', '.'))
            beta_s_vals = [0.60, 0.75, 1.00, 0.40]
            beta_s = beta_s_vals[self.combo_betas.currentIndex()]

            r = dimensionar_mensula(
                Vu=Vu, a=a, b_mm=b_mm, d=d,
                hormigon=horm, acero=acer,
                Nu=Nu, beta_s=beta_s,
            )
            self._resultado = r
            self.panel_res.mostrar_resultado_mensula(r)
            self._actualizar_canvas(r)

        except Exception as e:
            self.panel_res.mostrar_error(str(e))

    def _actualizar_canvas(self, r) -> None:
        from graficos import graficar_mensula
        self.canvas.mostrar_figura(graficar_mensula(r))
