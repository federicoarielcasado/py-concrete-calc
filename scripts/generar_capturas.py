"""
Genera las capturas de la aplicación que usa el README (docs/capturas/).

Recorre un escenario de demostración: calcula cada módulo, arma la planta de
ejemplo en E-09, propaga cargas, envía una viga y una columna a sus módulos,
exporta una memoria PDF y repite algunas pantallas en tema oscuro.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python scripts/generar_capturas.py               # → docs/capturas/
    python scripts/generar_capturas.py --salida otra/carpeta

Notas:
  - Abre la ventana de la aplicación unos 60 s; no hace falta interactuar.
  - Las vistas QWebEngineView (Plotly 3D) y los tooltips no aparecen en
    QWidget.grab() de la ventana: se capturan aparte y se pegan en su lugar.
  - Termina con código 1 si algún módulo mostró un error.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import app.main as m  # noqa: E402  (configura matplotlib y WebEngine antes de Qt)
from PyQt6.QtCore import QPoint, QSize, QTimer  # noqa: E402
from PyQt6.QtGui import QFont, QPainter  # noqa: E402
from PyQt6.QtPdf import QPdfDocument  # noqa: E402
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: E402
from PyQt6.QtWidgets import QApplication, QToolTip, QWidget  # noqa: E402

from app.memoria import generar_memoria  # noqa: E402
from app.widgets.panel_resultados import PanelResultados  # noqa: E402

args = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
args.add_argument('--salida', default=os.path.join(RAIZ, 'docs', 'capturas'),
                  help='carpeta destino (por defecto docs/capturas)')
SALIDA = args.parse_args().salida
os.makedirs(SALIDA, exist_ok=True)

# Cualquier error mostrado por un módulo o excepción no capturada se registra
errores: list[str] = []
_mostrar_error = PanelResultados.mostrar_error
PanelResultados.mostrar_error = lambda self, msg: (errores.append(msg), _mostrar_error(self, msg))[1]
sys.excepthook = lambda *a: errores.append(''.join(traceback.format_exception(*a)))

app = QApplication(sys.argv)
app.setStyle('Fusion')
app.setStyleSheet(m.get_stylesheet(m.get_tema()))
app.setFont(QFont('Segoe UI', 9))
win = m.VentanaPrincipal()
win.show()


# ── Utilidades ────────────────────────────────────────────────────────────────

def pump(seg: float = 0.3) -> None:
    """Procesa eventos de Qt durante `seg` segundos."""
    fin = time.time() + seg
    while time.time() < fin:
        app.processEvents()
        time.sleep(0.01)


def _componer(widget: QWidget, tip: QWidget | None = None):
    pix = widget.grab()
    p = QPainter(pix)
    for v in widget.findChildren(QWebEngineView):
        if v.isVisibleTo(widget) and v.width() > 0:
            p.drawPixmap(v.mapTo(widget, QPoint(0, 0)), v.grab())
    if tip is not None:
        p.drawPixmap(widget.mapFromGlobal(tip.mapToGlobal(QPoint(0, 0))), tip.grab())
    p.end()
    return pix


def capturar(widget: QWidget, nombre: str) -> None:
    _componer(widget).save(os.path.join(SALIDA, nombre))
    print('  ', nombre, flush=True)


def capturar_tooltip(nombre: str, sobre: QWidget, pos: QPoint, texto: str) -> None:
    """Muestra el tooltip real de Qt en `pos` (coordenadas de `sobre`) y lo captura con la ventana."""
    QToolTip.showText(sobre.mapToGlobal(pos), texto, sobre)
    pump(0.6)
    tip = next((w for w in QApplication.topLevelWidgets()
                if w.metaObject().className() == 'QTipLabel' and w.isVisible()), None)
    _componer(win, tip).save(os.path.join(SALIDA, nombre))
    QToolTip.hideText()
    pump(0.2)
    print('  ', nombre, flush=True)


def esperar_plotly(view: QWebEngineView, max_seg: float = 25) -> bool:
    """Espera a que Plotly haya dibujado (existe .main-svg) y 1.5 s más para WebGL."""
    listo = {'ok': False}
    fin = time.time() + max_seg
    while time.time() < fin and not listo['ok']:
        view.page().runJavaScript("!!document.querySelector('.main-svg')",
                                  lambda r: listo.__setitem__('ok', bool(r)))
        pump(0.5)
    pump(1.5)
    if not listo['ok']:
        errores.append('La vista 3D no terminó de cargar')
    return listo['ok']


def ir(idx: int):
    win._cambiar_modulo(idx)
    pump(0.3)
    return win.stack.widget(idx)


def adoptar_primera(w) -> None:
    w.tabla.selectRow(0)
    w.btn_adoptar.click()


# ── Escenario ─────────────────────────────────────────────────────────────────

def escenario() -> None:
    try:
        # F-01 Flexión: Mu = 180 kNm, variantes y adopción de la primera
        w = ir(0)
        w.entrada_Mu.setText('180')
        w.btn_calc.click(); w.btn_var.click(); pump()
        adoptar_primera(w); pump()
        capturar(win, '01_flexion.png')

        # Memoria de cálculo PDF de F-01 (página 1 como imagen)
        ruta_pdf = os.path.join(tempfile.gettempdir(), 'memoria_F-01.pdf')
        generar_memoria(w, 'F-01', ruta_pdf)
        pdf = QPdfDocument(None)
        pdf.load(ruta_pdf)
        pdf.render(0, QSize(1240, 1754)).save(os.path.join(SALIDA, '17_memoria_pdf.png'))
        print('   17_memoria_pdf.png', flush=True)

        # C-02 Corte
        w = ir(1)
        w.btn_calc.click(); w.btn_var.click(); pump()
        adoptar_primera(w); pump()
        capturar(win, '02_corte.png')

        # P-03 Columna
        w = ir(2)
        w.btn_calc.click(); pump()
        capturar(win, '03_columna_PM.png')

        # L-04 Losa en 1 y 2 direcciones
        w = ir(3)
        w.combo_tipo_losa.setCurrentIndex(0); w.btn_calc.click(); pump()
        capturar(win, '04_losa_1dir.png')
        w.combo_tipo_losa.setCurrentIndex(1); w.btn_calc.click(); pump()
        capturar(win, '05_losa_2dir.png')

        # V-05 Viga simple
        w = ir(4)
        w.combo_tipo.setCurrentIndex(0); w.btn_calc.click(); pump()
        capturar(win, '06_viga_simple.png')

        # T-06, B-07, M-08
        w = ir(5); w.btn_calc.click(); pump(); capturar(win, '07_torsion.png')
        w = ir(6); w.btn_calc.click(); pump(); capturar(win, '08_base.png')
        w = ir(7); w.btn_calc.click(); pump(); capturar(win, '09_mensula.png')

        # E-09 Planta: ejemplo (se carga al abrir) + propagación + 3D
        w = ir(8)
        w.btn_prop.click()
        esperar_plotly(w.visor._view)
        capturar(win, '10_planta_propagacion.png')

        # Tooltips sobre la planta: columna más cargada y una losa interior
        sc, vista = w._scene, w._view
        prop = w._propagacion.cargas_columnas
        col = max((c for c in sc._cols if c.elem_id), key=lambda c: prop[c.elem_id].Pu)
        capturar_tooltip('18_tooltip_columna.png', vista.viewport(),
                         vista.mapFromScene(col.scenePos()), col.toolTip())
        losa = sc._panels[min(4, len(sc._panels) - 1)]
        capturar_tooltip('19_tooltip_losa.png', vista.viewport(),
                         vista.mapFromScene(losa.sceneBoundingRect().center()), losa.toolTip())

        w._ver_3d_ampliado()
        esperar_plotly(w._dlg_3d.visor._view)
        capturar(w._dlg_3d, '11_planta_3d.png')
        w._dlg_3d.hide()

        # E-09 → V-05 (viga continua interior) y → P-03 (columna más cargada)
        w.combo_env_tipo.setCurrentText('VIGA'); w._actualizar_ids()
        w.combo_env_id.setCurrentIndex(1)
        w._enviar_a_modulo(); pump()
        win.stack.widget(4).btn_calc.click(); pump()
        capturar(win, '12_planta_a_viga_continua.png')

        ir(8)
        w.combo_env_tipo.setCurrentText('COLUMNA'); w._actualizar_ids()
        w.combo_env_id.setCurrentText(col.elem_id)
        w._enviar_a_modulo(); pump()
        win.stack.widget(2).btn_calc.click(); pump()
        capturar(win, '13_planta_a_columna.png')

        # Mapa de flujo y conversor de unidades
        win._abrir_mapa_flujo(); pump(0.8)
        capturar(win._mapa_flujo, '14_mapa_flujo.png'); win._mapa_flujo.hide()
        win._abrir_conversor(); pump()
        capturar(win._conversor, '15_conversor.png'); win._conversor.hide()

        # Tema oscuro: pantallas representativas
        win._cambiar_tema('OSCURO'); pump(0.5)
        for idx, nombre in ((0, 'flexion'), (3, 'losa_2dir'), (2, 'columna_PM')):
            ir(idx); pump(0.5)
            capturar(win, f'20_oscuro_{nombre}.png')
        w = ir(8)
        esperar_plotly(w.visor._view)
        capturar(win, '20_oscuro_planta.png')
        win._cambiar_tema('CLARO'); pump()
    except Exception:
        errores.append(traceback.format_exc())

    print('errores:', errores or 'ninguno', flush=True)
    app.exit(1 if errores else 0)


QTimer.singleShot(800, escenario)
sys.exit(app.exec())
