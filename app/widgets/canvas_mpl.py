"""
Widget que embebe una figura matplotlib dentro de un QWidget PyQt6.

Uso:
    canvas = CanvasMatplotlib(parent)
    canvas.mostrar_figura(fig)   # fig: matplotlib.figure.Figure
    canvas.limpiar()
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QPushButton


class CanvasMatplotlib(QWidget):
    """Contenedor para figuras matplotlib embebidas en Qt."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Área de dibujo
        self._area = QWidget()
        self._layout = QVBoxLayout(self._area)
        self._layout.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._area, stretch=1)

        # Botón de exportación
        self._btn_export = QPushButton('Exportar figura')
        self._btn_export.setToolTip('Guardar la figura como PDF, PNG o SVG (siempre en colores claros)')
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._exportar)
        outer.addWidget(self._btn_export)

        self._canvas = None
        self._figura = None

    def mostrar_figura(self, fig) -> None:
        """Muestra una figura matplotlib. Elimina la anterior para liberar memoria."""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

        self._limpiar_canvas()

        from app.themes import get_tema
        from app.widgets.tema_figuras import aplicar_tema_figura
        aplicar_tema_figura(fig, get_tema())

        self._figura = fig
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._layout.addWidget(self._canvas)
        self._canvas.draw()
        self._btn_export.setEnabled(True)

    def aplicar_tema(self) -> None:
        """Re-colorea la figura actual según el tema activo."""
        if self._figura is None:
            return
        from app.themes import get_tema
        from app.widgets.tema_figuras import aplicar_tema_figura
        aplicar_tema_figura(self._figura, get_tema())
        self._canvas.draw_idle()

    def figura_png(self, dpi: int = 150) -> bytes | None:
        """PNG de la figura actual en colores claros (para la memoria de cálculo)."""
        if self._figura is None:
            return None
        import io
        from app.widgets.tema_figuras import con_tema_claro
        buf = io.BytesIO()
        with con_tema_claro(self._figura):
            self._figura.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                                 facecolor='white')
        self._canvas.draw_idle()
        return buf.getvalue()

    def limpiar(self) -> None:
        """Elimina el canvas actual y cierra la figura."""
        self._limpiar_canvas()
        self._btn_export.setEnabled(False)

    def _limpiar_canvas(self) -> None:
        if self._canvas is not None:
            self._layout.removeWidget(self._canvas)
            self._canvas.setParent(None)  # type: ignore[arg-type]
            self._canvas.deleteLater()
            self._canvas = None

        if self._figura is not None:
            import matplotlib.pyplot as plt
            plt.close(self._figura)
            self._figura = None

    def _exportar(self) -> None:
        if self._figura is None:
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, 'Exportar figura', '',
            'PDF (*.pdf);;PNG (*.png);;SVG (*.svg)',
        )
        if path:
            from app.widgets.tema_figuras import con_tema_claro
            with con_tema_claro(self._figura):
                self._figura.savefig(path, bbox_inches='tight', dpi=150, facecolor='white')
            self._canvas.draw_idle()
