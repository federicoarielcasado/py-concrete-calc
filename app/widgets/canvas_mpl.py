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
        self._btn_export = QPushButton('↓  EXPORTAR FIGURA')
        self._btn_export.setFixedHeight(22)
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

        fig.patch.set_facecolor('#C0C0C0')

        self._figura = fig
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._layout.addWidget(self._canvas)
        self._canvas.draw()
        self._btn_export.setEnabled(True)

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
            self._figura.savefig(path, bbox_inches='tight', dpi=150)
