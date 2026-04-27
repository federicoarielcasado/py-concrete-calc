"""
VisorPlotly3D — embebe una figura Plotly interactiva en un QWidget.

Usa QWebEngineView si PyQtWebEngine está disponible; de lo contrario
muestra un botón para abrir la figura en el navegador.

Uso:
    visor = VisorPlotly3D()
    visor.mostrar_figura(fig)   # fig: plotly.graph_objects.Figure
    visor.limpiar()
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt

def _intentar_crear_webview():
    """
    Intenta importar e instanciar QWebEngineView.
    Devuelve el widget listo, o None si falla por cualquier motivo.
    Captura ImportError, RuntimeError, OSError, etc. (Windows puede
    lanzar errores distintos de ImportError cuando el sandbox no está
    disponible o falta QtWebEngineProcess.exe).
    """
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        view = QWebEngineView()
        return view
    except Exception:
        return None


class VisorPlotly3D(QWidget):
    """Widget que muestra una figura Plotly 3D incrustada."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._fig = None

        self._view = _intentar_crear_webview()

        if self._view is not None:
            self._view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            self._layout.addWidget(self._view)
        else:
            lbl = QLabel(
                'Vista 3D integrada no disponible.\n'
                'Usar el botón para abrir la figura en el navegador.'
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName('panel_crt')
            self._layout.addWidget(lbl)

            self._btn_abrir = QPushButton('ABRIR EN NAVEGADOR')
            self._btn_abrir.setObjectName('btn_calcular')
            self._btn_abrir.setEnabled(False)
            self._btn_abrir.clicked.connect(self._abrir_en_navegador)
            self._layout.addWidget(self._btn_abrir)

    # ── API pública ──────────────────────────────────────────────────────────

    def mostrar_figura(self, fig) -> None:
        """Muestra la figura Plotly en el visor o habilita el botón del navegador."""
        self._fig = fig

        if self._view is not None:
            html = fig.to_html(
                include_plotlyjs='cdn',
                full_html=True,
                config={'responsive': True},
            )
            self._view.setHtml(html)
        else:
            self._btn_abrir.setEnabled(True)

    def limpiar(self) -> None:
        self._fig = None
        if self._view is not None:
            self._view.setHtml('<html><body style="background:#1a1a1a;"></body></html>')
        else:
            self._btn_abrir.setEnabled(False)

    # ── Fallback: navegador externo ──────────────────────────────────────────

    def _abrir_en_navegador(self) -> None:
        if self._fig is None:
            return
        import os
        import tempfile
        import webbrowser

        fd, path = tempfile.mkstemp(suffix='.html', prefix='planta_3d_')
        os.close(fd)
        self._fig.write_html(path)
        webbrowser.open(f'file://{path}')
