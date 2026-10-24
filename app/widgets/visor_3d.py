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


def _con_tema(fig, tema):
    """Copia de la figura con plantilla y colores del tema (None = claro)."""
    import plotly.graph_objects as go
    f = go.Figure(fig)
    if tema is None or not tema.oscuro:
        f.update_layout(template='plotly_white')
        return f
    f.update_layout(
        template='plotly_dark',
        paper_bgcolor=tema.fig_fondo,
        font_color=tema.fig_texto,
        legend_bgcolor='rgba(0,0,0,0)',
    )
    return f


class VisorPlotly3D(QWidget):
    """Widget que muestra una figura Plotly 3D incrustada."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._fig = None
        self._html_tmp: str | None = None

        self._view = _intentar_crear_webview()

        if self._view is not None:
            self._view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            self._layout.addWidget(self._view)
            # Fondo del tema sin navegar (un setHtml acá competiría con el primer load())
            self._fondo_pagina()
        else:
            lbl = QLabel(
                'Vista 3D integrada no disponible.\n'
                'Usar el botón para abrir la figura en el navegador.'
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName('panel_resultados')
            self._layout.addWidget(lbl)

            self._btn_abrir = QPushButton('Abrir en el navegador')
            self._btn_abrir.setObjectName('btn_calcular')
            self._btn_abrir.setEnabled(False)
            self._btn_abrir.clicked.connect(self._abrir_en_navegador)
            self._layout.addWidget(self._btn_abrir)

    # ── API pública ──────────────────────────────────────────────────────────

    def mostrar_figura(self, fig) -> None:
        """Muestra la figura Plotly en el visor o habilita el botón del navegador."""
        self._fig = fig

        if self._view is not None:
            # plotly.js va embebido (sin CDN) para que funcione sin internet; como
            # supera el límite de 2 MB de setHtml(), se carga desde un archivo local.
            import os
            import tempfile
            from PyQt6.QtCore import QUrl

            from app.themes import get_tema
            t = get_tema()
            html = _con_tema(fig, t).to_html(
                include_plotlyjs=True,
                full_html=True,
                default_width='100%',
                default_height='100%',
                config={'responsive': True, 'displaylogo': False},
            )
            html = html.replace(
                '<head>',
                '<head><style>html,body,body>div{margin:0;height:100%;overflow:hidden;'
                f'background:{t.fig_fondo};}}</style>', 1)
            self._fondo_pagina()
            if self._html_tmp is None:
                fd, self._html_tmp = tempfile.mkstemp(suffix='.html', prefix='visor_3d_')
                os.close(fd)
            with open(self._html_tmp, 'w', encoding='utf-8') as f:
                f.write(html)
            self._view.load(QUrl.fromLocalFile(self._html_tmp))
        else:
            self._btn_abrir.setEnabled(True)

    def limpiar(self) -> None:
        self._fig = None
        if self._view is not None:
            from app.themes import get_tema
            t = get_tema()
            self._fondo_pagina()
            self._view.setHtml(
                f'<html><body style="margin:0;height:100%;background:{t.fig_fondo};'
                'display:flex;align-items:center;justify-content:center;'
                f'font:12px sans-serif;color:{t.texto_suave};">'
                'Vista 3D &mdash; presione Propagar cargas</body></html>')
        else:
            self._btn_abrir.setEnabled(False)

    def aplicar_tema(self) -> None:
        """Vuelve a dibujar la figura (o el aviso inicial) con el tema activo."""
        if self._view is None:
            return
        if self._fig is not None:
            self.mostrar_figura(self._fig)
        else:
            self.limpiar()

    def _fondo_pagina(self) -> None:
        from PyQt6.QtGui import QColor
        from app.themes import get_tema
        self._view.page().setBackgroundColor(QColor(get_tema().fig_fondo))

    # ── Fallback: navegador externo ──────────────────────────────────────────

    def _abrir_en_navegador(self) -> None:
        if self._fig is None:
            return
        import os
        import tempfile
        import webbrowser

        fd, path = tempfile.mkstemp(suffix='.html', prefix='planta_3d_')
        os.close(fd)
        _con_tema(self._fig, None).write_html(path)
        webbrowser.open(f'file://{path}')
