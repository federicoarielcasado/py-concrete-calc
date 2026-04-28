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
mpl.rcParams.update({
    'figure.facecolor':  '#C0C0C0',
    'axes.facecolor':    '#EBEBEB',
    'axes.edgecolor':    '#404040',
    'axes.labelcolor':   '#000000',
    'text.color':        '#000000',
    'xtick.color':       '#000000',
    'ytick.color':       '#000000',
    'grid.color':        '#C8C8C8',
    'font.family':       'monospace',
    'font.size':         9,
    'figure.autolayout': True,
})

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget,
    QStatusBar, QLabel,
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from app.styles import get_stylesheet
from app.themes import get_tema, set_tema, TEMAS


class VentanaPrincipal(QMainWindow):

    _MODULOS = [
        ('F-01', 'FLEXIÓN'),
        ('C-02', 'CORTE'),
        ('P-03', 'COLUMNA'),
        ('L-04', 'LOSA'),
        ('V-05', 'VIGA'),
        ('T-06', 'TORSIÓN'),
        ('B-07', 'BASES'),
        ('M-08', 'MÉNSULA'),
        ('E-09', 'PLANTA'),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SIST. CÁLCULO ESTRUCTURAL  //  CIRSOC 201-2005')
        self.setFixedSize(1280, 800)
        self._modulo_activo = 'F-01 FLEXIÓN'
        self._conversor = None
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
        hl.addWidget(self.stack)

        self._cargar_ventanas()
        self._setup_statusbar()

        # Activar primer módulo
        self._botones[0].setChecked(True)

    def _crear_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setObjectName('sidebar')
        sb.setFixedWidth(100)

        lay = QVBoxLayout(sb)
        lay.setContentsMargins(8, 10, 8, 8)
        lay.setSpacing(4)

        logo = QLabel('CIRSOC\n201-2005')
        logo.setObjectName('sidebar_logo')
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)

        sep = QWidget()
        sep.setObjectName('sidebar_sep')
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(6)

        self._botones: list[QPushButton] = []
        for i, (codigo, nombre) in enumerate(self._MODULOS):
            btn = QPushButton(f'{codigo}\n{nombre}')
            btn.setObjectName('btn_modulo')
            btn.setCheckable(True)
            btn.setFixedSize(84, 68)
            btn.clicked.connect(lambda _checked, idx=i: self._cambiar_modulo(idx))
            lay.addWidget(btn)
            self._botones.append(btn)

        lay.addStretch()

        # ── Conversor de unidades ────────────────────────────────────────────
        sep_conv = QWidget()
        sep_conv.setObjectName('sidebar_sep')
        sep_conv.setFixedHeight(1)
        lay.addWidget(sep_conv)
        lay.addSpacing(4)

        btn_conv = QPushButton('⇄\nUNIDADES')
        btn_conv.setObjectName('btn_modulo')
        btn_conv.setFixedSize(84, 36)
        btn_conv.setToolTip(
            'Conversor de unidades\n'
            'kgf ↔ kN, tf ↔ kN, kgf·m ↔ kN·m,\n'
            'kgf/cm² ↔ MPa, kgf/m² ↔ kN/m², ...'
        )
        btn_conv.clicked.connect(self._abrir_conversor)
        lay.addWidget(btn_conv)
        lay.addSpacing(2)

        btn_guardar = QPushButton('↓ GUARDAR')
        btn_guardar.setObjectName('btn_modulo')
        btn_guardar.setFixedSize(84, 24)
        btn_guardar.setToolTip('Guardar todos los inputs de la sesión en un archivo JSON')
        btn_guardar.clicked.connect(self._guardar_sesion)
        lay.addWidget(btn_guardar)

        btn_abrir = QPushButton('↑ ABRIR')
        btn_abrir.setObjectName('btn_modulo')
        btn_abrir.setFixedSize(84, 24)
        btn_abrir.setToolTip('Restaurar los inputs de una sesión guardada (JSON)')
        btn_abrir.clicked.connect(self._abrir_sesion)
        lay.addWidget(btn_abrir)
        lay.addSpacing(2)

        # ── Selector de tema ─────────────────────────────────────────────────
        sep2 = QWidget()
        sep2.setObjectName('sidebar_sep')
        sep2.setFixedHeight(1)
        lay.addWidget(sep2)
        lay.addSpacing(4)

        lbl = QLabel('TEMA')
        lbl.setObjectName('sidebar_logo')
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)
        lay.addSpacing(2)

        tema_row = QWidget()
        tema_row.setObjectName('sidebar')
        tema_hl = QHBoxLayout(tema_row)
        tema_hl.setContentsMargins(0, 0, 0, 0)
        tema_hl.setSpacing(2)

        tema_activo = get_tema().codigo
        self._btns_tema: list[QPushButton] = []
        for codigo in TEMAS:
            btn = QPushButton(codigo)
            btn.setObjectName('btn_tema')
            btn.setCheckable(True)
            btn.setChecked(codigo == tema_activo)
            btn.setFixedSize(26, 22)
            btn.clicked.connect(lambda _chk, c=codigo: self._cambiar_tema(c))
            tema_hl.addWidget(btn)
            self._btns_tema.append(btn)

        lay.addWidget(tema_row)
        lay.addSpacing(4)

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
        sb.setObjectName('status_bar')
        self.setStatusBar(sb)
        self._lbl_status = QLabel()
        self._lbl_status.setObjectName('status_label')
        sb.addWidget(self._lbl_status)
        self._actualizar_status('LISTO')

    # ── Navegación ───────────────────────────────────────────────────────────

    def _cambiar_modulo(self, idx: int) -> None:
        for i, btn in enumerate(self._botones):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        codigo, nombre = self._MODULOS[idx]
        self._modulo_activo = f'{codigo} {nombre}'
        self._actualizar_status('LISTO')

    def _guardar_sesion(self) -> None:
        import json
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar sesión', '', 'JSON (*.json)'
        )
        if not path:
            return
        estados = {}
        for i in range(8):
            w = self.stack.widget(i)
            if w is not None and hasattr(w, 'get_estado'):
                estados[str(i)] = w.get_estado()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(estados, f, indent=2, ensure_ascii=False)
        self._actualizar_status('SESIÓN GUARDADA')

    def _abrir_sesion(self) -> None:
        import json
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, 'Abrir sesión', '', 'JSON (*.json)'
        )
        if not path:
            return
        with open(path, encoding='utf-8') as f:
            estados = json.load(f)
        for idx_str, estado in estados.items():
            w = self.stack.widget(int(idx_str))
            if w is not None and hasattr(w, 'set_estado'):
                try:
                    w.set_estado(estado)
                except Exception:
                    pass
        self._actualizar_status('SESIÓN CARGADA')

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
        for btn in self._btns_tema:
            btn.setChecked(btn.text() == codigo)
        self._actualizar_status(f'TEMA: {tema.nombre.upper()}')

    def _actualizar_status(self, estado: str) -> None:
        hora = QDateTime.currentDateTime().toString('hh:mm:ss')
        self._lbl_status.setText(
            f'[{self._modulo_activo}]  //  CIRSOC 201-2005  //  {hora}  //  {estado}'
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet(get_tema()))
    app.setFont(QFont('Tahoma', 9))

    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
