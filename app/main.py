"""
Punto de entrada de la interfaz de escritorio.
Ejecutar con:  python app/main.py
"""
import sys
import os

# Asegurar que la raíz del proyecto esté en el path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# WebEngine debe importarse ANTES de QApplication (requisito de Qt6 en Windows)
os.environ.setdefault('QTWEBENGINE_DISABLE_SANDBOX', '1')
try:
    from PyQt6 import QtWebEngineWidgets as _qwew  # noqa: F401
except Exception:
    pass

import matplotlib
matplotlib.use('QtAgg')

import matplotlib as mpl
# Las figuras se crean siempre con esta base clara; el tema oscuro se aplica
# después sobre la figura ya dibujada (app.widgets.tema_figuras).
mpl.rcParams.update({
    'figure.facecolor':  '#FFFFFF',
    'axes.facecolor':    '#FAFBFC',
    'axes.edgecolor':    '#8A96A3',
    'axes.labelcolor':   '#1F2933',
    'text.color':        '#1F2933',
    'xtick.color':       '#1F2933',
    'ytick.color':       '#1F2933',
    'grid.color':        '#D9DEE4',
    # DejaVu Sans como respaldo para glifos que Segoe UI no tiene (✓, ✗, ▲)
    'font.family':       ['Segoe UI', 'DejaVu Sans'],
    'font.size':         9,
    'figure.autolayout': True,
})

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget,
    QStatusBar, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.styles import get_stylesheet
from app.themes import get_tema, set_tema, TEMAS


class VentanaPrincipal(QMainWindow):

    _MODULOS = [
        ('F-01', 'Flexión'),
        ('C-02', 'Corte'),
        ('P-03', 'Columna'),
        ('L-04', 'Losa'),
        ('V-05', 'Viga'),
        ('T-06', 'Torsión'),
        ('B-07', 'Bases'),
        ('M-08', 'Ménsula'),
        ('E-09', 'Planta'),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle('py-concrete-calc  —  Hormigón armado CIRSOC 201-2005')
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self._modulo_activo = 'F-01 Flexión'
        self._conversor  = None
        self._mapa_flujo = None
        self._setup_ui()

    # ── Construcción ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        hl = QHBoxLayout(central)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        hl.addWidget(self._crear_sidebar())

        self.stack = QStackedWidget()
        hl.addWidget(self.stack, 1)

        self._cargar_ventanas()
        self._setup_statusbar()

        # Activar primer módulo
        self._botones[0].setChecked(True)

    def _boton_sidebar(self, texto: str, tip: str, accion) -> QPushButton:
        btn = QPushButton(texto)
        btn.setObjectName('btn_modulo')
        btn.setToolTip(tip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(accion)
        return btn

    def _separador(self) -> QWidget:
        sep = QWidget()
        sep.setObjectName('sidebar_sep')
        sep.setFixedHeight(1)
        return sep

    def _crear_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setObjectName('sidebar')
        sb.setFixedWidth(150)

        lay = QVBoxLayout(sb)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(1)

        logo = QLabel('py-concrete-calc\nCIRSOC 201-2005')
        logo.setObjectName('sidebar_logo')
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)
        lay.addSpacing(6)
        lay.addWidget(self._separador())
        lay.addSpacing(6)

        _TIPS = [
            'F-01 FLEXIÓN\nDimensionar As ante Mu o verificar φMn\nComplementar siempre con C-02',
            'C-02 CORTE\nDiseñar estribos ante Vu (art. 11.5)\nUsar junto a F-01 en diseño de vigas',
            'P-03 COLUMNA\nFlexocompresión P+M, diagrama interacción\nRecibe Pu/Mu de V-05 o E-09 → alimenta B-07',
            'L-04 LOSA\n1 dir. (coef. art. 8.3.3) o 2 dir. DDM\nAlimenta V-05 con carga sobre vigas de borde',
            'V-05 VIGA\nSimple / voladizo / continua\nRecibe cargas de L-04 o E-09 → alimenta P-03',
            'T-06 TORSIÓN\nTu + Vu combinados (art. 11.6)\nUsar cuando Tu > Tu_min, complementa C-02',
            'B-07 BASES\nZapata aislada centrada (cap. 15)\nRecibe Pu de P-03 + datos de suelo',
            'M-08 MÉNSULA\nBielas y tirantes, a/d < 1 (art. 11.9)\nElemento especial, independiente del flujo',
            'E-09 PLANTA\nModelar la planta + propagar cargas\nPunto de partida → alimenta V-05 y P-03',
        ]

        self._botones: list[QPushButton] = []
        for i, (codigo, nombre) in enumerate(self._MODULOS):
            btn = self._boton_sidebar(f'{codigo}    {nombre}', _TIPS[i],
                                      lambda _chk, idx=i: self._cambiar_modulo(idx))
            btn.setCheckable(True)
            lay.addWidget(btn)
            self._botones.append(btn)

        lay.addStretch()
        lay.addWidget(self._separador())
        lay.addSpacing(4)

        lay.addWidget(self._boton_sidebar(
            'Mapa de flujo', 'Cuándo usar cada módulo y cómo se vinculan',
            self._abrir_mapa_flujo))
        lay.addWidget(self._boton_sidebar(
            'Conversor de unidades',
            'kgf ↔ kN, tf ↔ kN, kgf·m ↔ kN·m,\nkgf/cm² ↔ MPa, kgf/m² ↔ kN/m², ...',
            self._abrir_conversor))
        lay.addWidget(self._boton_sidebar(
            'Memoria de cálculo PDF',
            'Exportar datos, resultados, referencias y figura\ndel módulo actual a un PDF',
            self._exportar_memoria))
        lay.addWidget(self._boton_sidebar(
            'Guardar sesión', 'Guardar los datos de todos los módulos en un archivo JSON',
            self._guardar_sesion))
        lay.addWidget(self._boton_sidebar(
            'Abrir sesión', 'Restaurar los datos de una sesión guardada (JSON)',
            self._abrir_sesion))

        lay.addSpacing(6)
        lay.addWidget(self._separador())
        lay.addSpacing(8)

        tema_row = QWidget()
        tema_row.setObjectName('sidebar')
        tema_hl = QHBoxLayout(tema_row)
        tema_hl.setContentsMargins(10, 0, 10, 0)
        tema_hl.setSpacing(4)

        tema_activo = get_tema().codigo
        self._btns_tema: dict[str, QPushButton] = {}
        for codigo, tema in TEMAS.items():
            btn = QPushButton(tema.nombre)
            btn.setObjectName('btn_tema')
            btn.setCheckable(True)
            btn.setChecked(codigo == tema_activo)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _chk, c=codigo: self._cambiar_tema(c))
            tema_hl.addWidget(btn)
            self._btns_tema[codigo] = btn

        lay.addWidget(tema_row)
        return sb

    def _cargar_ventanas(self) -> None:
        from app.ventanas.flexion  import VentanaFlexion
        from app.ventanas.corte    import VentanaCorte
        from app.ventanas.columnas import VentanaColumnas
        from app.ventanas.losas    import VentanaLosas
        from app.ventanas.viga     import VentanaViga
        from app.ventanas.torsion  import VentanaTorsion
        from app.ventanas.bases    import VentanaBases
        from app.ventanas.bielas   import VentanaBielas
        from app.ventanas.planta_canvas import VentanaPlantaCanvas

        for VClass in (VentanaFlexion, VentanaCorte, VentanaColumnas,
                       VentanaLosas, VentanaViga, VentanaTorsion,
                       VentanaBases, VentanaBielas, VentanaPlantaCanvas):
            self.stack.addWidget(VClass())

    def _setup_statusbar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._lbl_status = QLabel()
        self._lbl_status.setObjectName('status_label')
        sb.addWidget(self._lbl_status)
        self._actualizar_status('Listo')

    # ── Navegación ───────────────────────────────────────────────────────────

    def _cambiar_modulo(self, idx: int) -> None:
        for i, btn in enumerate(self._botones):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        codigo, nombre = self._MODULOS[idx]
        self._modulo_activo = f'{codigo} {nombre}'
        self._actualizar_status('Listo')

    def _guardar_sesion(self) -> None:
        import json
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar sesión', '', 'JSON (*.json)'
        )
        if not path:
            return
        estados = {}
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if w is not None and hasattr(w, 'get_estado'):
                estados[str(i)] = w.get_estado()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(estados, f, indent=2, ensure_ascii=False)
        self._actualizar_status('Sesión guardada')

    def _abrir_sesion(self) -> None:
        import json
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, 'Abrir sesión', '', 'JSON (*.json)'
        )
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as f:
                estados = json.load(f)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, 'Abrir sesión', f'No se pudo leer el archivo:\n{e}')
            return
        fallidos = []
        for idx_str, estado in estados.items():
            w = self.stack.widget(int(idx_str))
            if w is not None and hasattr(w, 'set_estado'):
                try:
                    w.set_estado(estado)
                except Exception:
                    fallidos.append(self._MODULOS[int(idx_str)][0])
        if fallidos:
            QMessageBox.warning(
                self, 'Abrir sesión',
                'Algunos módulos no se pudieron restaurar: ' + ', '.join(fallidos))
        self._actualizar_status('Sesión cargada')

    def _exportar_memoria(self) -> None:
        from PyQt6.QtWidgets import QFileDialog
        from app.memoria import generar_memoria, sin_resultados

        idx = self.stack.currentIndex()
        codigo, nombre = self._MODULOS[idx]
        ventana = self.stack.currentWidget()
        if sin_resultados(ventana):
            QMessageBox.information(
                self, 'Memoria de cálculo',
                f'Primero calcule el módulo {codigo} para generar su memoria.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Exportar memoria de cálculo',
            f'memoria_{codigo}_{nombre.lower()}.pdf', 'PDF (*.pdf)')
        if not path:
            return
        generar_memoria(ventana, codigo, path)
        self._actualizar_status(f'Memoria exportada: {os.path.basename(path)}')

    def _abrir_mapa_flujo(self) -> None:
        if self._mapa_flujo is None:
            from app.widgets.mapa_flujo import MapaFlujo
            self._mapa_flujo = MapaFlujo(self)
        if self._mapa_flujo.isVisible():
            self._mapa_flujo.raise_()
            self._mapa_flujo.activateWindow()
        else:
            self._mapa_flujo.show()

    def _abrir_conversor(self) -> None:
        if self._conversor is None:
            from app.widgets.conversor_unidades import ConversorUnidades
            self._conversor = ConversorUnidades(self)
        if self._conversor.isVisible():
            self._conversor.raise_()
            self._conversor.activateWindow()
        else:
            self._conversor.show()

    def _cambiar_tema(self, codigo: str) -> None:
        tema = set_tema(codigo)
        QApplication.instance().setStyleSheet(get_stylesheet(tema))
        for c, btn in self._btns_tema.items():
            btn.setChecked(c == codigo)

        # Componentes que dibujan con colores propios (no QSS)
        from app.widgets.panel_resultados import PanelResultados
        from app.widgets.canvas_mpl import CanvasMatplotlib
        from app.widgets.visor_3d import VisorPlotly3D
        from app.widgets.canvas_planta import PlantaView
        for w in self.findChildren(PanelResultados):
            w.refrescar()
        for clase in (CanvasMatplotlib, VisorPlotly3D, PlantaView):
            for w in self.findChildren(clase):
                w.aplicar_tema()
        if self._mapa_flujo is not None:
            self._mapa_flujo.aplicar_tema()
        self._actualizar_status(f'Tema {tema.nombre.lower()}')

    def _actualizar_status(self, estado: str) -> None:
        self._lbl_status.setText(
            f'{self._modulo_activo}   ·   CIRSOC 201-2005   ·   {estado}'
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(get_stylesheet(get_tema()))
    app.setFont(QFont('Segoe UI', 9))

    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
