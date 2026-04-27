"""
Canvas interactivo de planta estructural — QGraphicsScene / QGraphicsView.

Flujo:
  - Drag sobre area vacia   → nuevo panel de losa
  - Drag sobre panel        → mover (snap a grilla)
  - Doble clic sobre panel  → dialogo de propiedades
  - Tecla Delete            → elimina panel seleccionado
  - Drag derecho / scroll   → pan y zoom
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsLineItem,
    QDialog, QWidget, QVBoxLayout, QFormLayout, QGroupBox, QGridLayout,
    QLabel, QDoubleSpinBox, QComboBox, QCheckBox, QDialogButtonBox,
    QRubberBand,
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont

# ── Constantes ────────────────────────────────────────────────────────────────

SCALE  = 80      # px / metro
SNAP_M = 1.0     # paso de grilla en metros

_C_GRID       = QColor(70,  70,  70,  40)
_C_GRID_MAJ   = QColor(90,  90,  90,  90)
_C_PANEL_FILL = QColor(100, 140, 200, 38)
_C_PANEL_SEL  = QColor(120, 190, 255, 70)
_C_EDGE_LIBRE = QColor(120, 120, 140, 80)
_C_EDGE_VIGA  = QColor(150,  90,  35, 255)
_C_VIGA       = QColor(160, 100,  40, 220)
_C_COL_FILL   = QColor( 44,  62,  80, 230)
_C_LABEL      = QColor(210, 225, 255)


def _snap(px: float) -> float:
    step = SNAP_M * SCALE
    return round(px / step) * step


def _to_m(px: float) -> float:
    return round(px / SCALE, 4)


def _merge_segs(segs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Fusiona segmentos 1D solapados o adyacentes (coordenadas px)."""
    if not segs:
        return []
    out = [min(segs, key=lambda s: s[0])]
    for a, b in sorted(segs)[1:]:
        if a <= out[-1][1] + 2:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _merge_segs_m(segs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Fusiona segmentos 1D solapados o adyacentes (coordenadas metros)."""
    if not segs:
        return []
    out = [min(segs, key=lambda s: s[0])]
    for a, b in sorted(segs)[1:]:
        if a <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


# ── Propiedades del panel ─────────────────────────────────────────────────────

@dataclass
class PanelProps:
    h:        float = 0.14
    tipo:     str   = '2dir'
    wD:       float = 1.5
    wL:       float = 2.0
    dir_1dir: str   = 'x'
    edge_n:   bool  = True
    edge_s:   bool  = True
    edge_e:   bool  = True
    edge_w:   bool  = True


# ── Items graficos ────────────────────────────────────────────────────────────

class PanelItem(QGraphicsRectItem):
    """Panel de losa arrastrable con indicadores de borde."""

    def __init__(self, x0: float, y0: float, x1: float, y1: float,
                 props: PanelProps, panel_id: str):
        super().__init__(0, 0, x1 - x0, y1 - y0)
        self.setPos(x0, y0)
        self.props    = props
        self.panel_id = panel_id
        self.setFlags(
            self.GraphicsItemFlag.ItemIsMovable |
            self.GraphicsItemFlag.ItemIsSelectable |
            self.GraphicsItemFlag.ItemSendsGeometryChanges,
        )
        self.setPen(QPen(Qt.GlobalColor.transparent))
        self.setZValue(1)

    # ── Geometria en metros ───────────────────────────────────────────────────

    def x0_m(self) -> float: return _to_m(self.pos().x())
    def y0_m(self) -> float: return _to_m(self.pos().y())
    def x1_m(self) -> float: return _to_m(self.pos().x() + self.rect().width())
    def y1_m(self) -> float: return _to_m(self.pos().y() + self.rect().height())

    def rect_scene(self) -> QRectF:
        return QRectF(self.pos().x(), self.pos().y(),
                      self.rect().width(), self.rect().height())

    # ── Interaccion ───────────────────────────────────────────────────────────

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemPositionChange:
            return QPointF(_snap(value.x()), _snap(value.y()))
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            sc = self.scene()
            if sc:
                sc.reconstruir()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        dlg = DialogPanel(self.props)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.props = dlg.get_props()
            self.update()
            if self.scene():
                self.scene().reconstruir()

    # ── Dibujo ────────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, option, widget=None):
        r = self.rect()
        painter.fillRect(r, _C_PANEL_SEL if self.isSelected() else _C_PANEL_FILL)

        ew = 5
        for has_viga, p0, p1 in [
            (self.props.edge_n, r.topLeft(),    r.topRight()),
            (self.props.edge_s, r.bottomLeft(), r.bottomRight()),
            (self.props.edge_w, r.topLeft(),    r.bottomLeft()),
            (self.props.edge_e, r.topRight(),   r.bottomRight()),
        ]:
            pen = QPen(_C_EDGE_VIGA, ew) if has_viga else QPen(_C_EDGE_LIBRE, 1)
            painter.setPen(pen)
            painter.drawLine(p0, p1)

        painter.setPen(QPen(_C_LABEL))
        painter.setFont(QFont('Consolas', 8))
        lx = round(self.rect().width()  / SCALE, 2)
        ly = round(self.rect().height() / SCALE, 2)
        txt = (f'{self.panel_id}\n'
               f'{self.props.tipo}  h={self.props.h*100:.0f}cm\n'
               f'{lx}m × {ly}m\n'
               f'wD={self.props.wD}  wL={self.props.wL}')
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, txt)


class VigaItem(QGraphicsLineItem):
    def __init__(self, x0, y0, x1, y1):
        super().__init__(x0, y0, x1, y1)
        self.setPen(QPen(_C_VIGA, 4))
        self.setZValue(2)


class ColumnaItem(QGraphicsRectItem):
    def __init__(self, x: float, y: float, sz: float = 14):
        h = sz / 2
        super().__init__(-h, -h, sz, sz)
        self.setPos(x, y)
        self.setBrush(QBrush(_C_COL_FILL))
        self.setPen(QPen(QColor(20, 30, 40), 1.5))
        self.setZValue(3)


# ── Dialogo de propiedades ────────────────────────────────────────────────────

class DialogPanel(QDialog):
    def __init__(self, props: PanelProps, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Propiedades del panel')
        self.setFixedWidth(280)
        self._p = props
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)

        grp = QGroupBox('Losa')
        f = QFormLayout(grp)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.spn_h = QDoubleSpinBox()
        self.spn_h.setRange(5, 50); self.spn_h.setSuffix(' cm')
        self.spn_h.setDecimals(0); self.spn_h.setValue(self._p.h * 100)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(['2dir', '1dir'])
        self.cmb_tipo.setCurrentText(self._p.tipo)
        self.cmb_tipo.currentTextChanged.connect(
            lambda t: self._wgt_dir.setVisible(t == '1dir'))

        self.spn_wD = QDoubleSpinBox()
        self.spn_wD.setRange(0, 50); self.spn_wD.setSuffix(' kN/m2')
        self.spn_wD.setDecimals(2); self.spn_wD.setValue(self._p.wD)

        self.spn_wL = QDoubleSpinBox()
        self.spn_wL.setRange(0, 50); self.spn_wL.setSuffix(' kN/m2')
        self.spn_wL.setDecimals(2); self.spn_wL.setValue(self._p.wL)

        self.cmb_dir = QComboBox()
        self.cmb_dir.addItems(['x', 'y'])
        self.cmb_dir.setCurrentText(self._p.dir_1dir)
        self._wgt_dir = QWidget()
        dhl = QFormLayout(self._wgt_dir)
        dhl.setContentsMargins(0, 0, 0, 0)
        dhl.addRow('Dir armadura:', self.cmb_dir)
        self._wgt_dir.setVisible(self._p.tipo == '1dir')

        f.addRow('h:', self.spn_h)
        f.addRow('Tipo:', self.cmb_tipo)
        f.addRow('wD:', self.spn_wD)
        f.addRow('wL:', self.spn_wL)
        f.addRow(self._wgt_dir)
        lay.addWidget(grp)

        grp_e = QGroupBox('Bordes con viga')
        g = QGridLayout(grp_e)
        g.setSpacing(4)
        self.chk_n = QCheckBox('Norte'); self.chk_n.setChecked(self._p.edge_n)
        self.chk_s = QCheckBox('Sur');   self.chk_s.setChecked(self._p.edge_s)
        self.chk_e = QCheckBox('Este');  self.chk_e.setChecked(self._p.edge_e)
        self.chk_w = QCheckBox('Oeste'); self.chk_w.setChecked(self._p.edge_w)
        g.addWidget(self.chk_n, 0, 1, Qt.AlignmentFlag.AlignCenter)
        g.addWidget(self.chk_w, 1, 0)
        g.addWidget(QLabel('panel'), 1, 1, Qt.AlignmentFlag.AlignCenter)
        g.addWidget(self.chk_e, 1, 2)
        g.addWidget(self.chk_s, 2, 1, Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(grp_e)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_props(self) -> PanelProps:
        return PanelProps(
            h=self.spn_h.value() / 100,
            tipo=self.cmb_tipo.currentText(),
            wD=self.spn_wD.value(),
            wL=self.spn_wL.value(),
            dir_1dir=self.cmb_dir.currentText(),
            edge_n=self.chk_n.isChecked(),
            edge_s=self.chk_s.isChecked(),
            edge_e=self.chk_e.isChecked(),
            edge_w=self.chk_w.isChecked(),
        )


# ── Escena ────────────────────────────────────────────────────────────────────

class PlantaScene(QGraphicsScene):
    modelo_listo = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-200, -200, 3000, 2500)
        self._panels:  list[PanelItem]   = []
        self._vigas:   list[VigaItem]    = []
        self._cols:    list[ColumnaItem] = []
        self._counter: int = 0

    def agregar_panel(self, x0: float, y0: float, x1: float, y1: float,
                      props: PanelProps | None = None) -> PanelItem:
        pid   = f'L{self._counter}'
        self._counter += 1
        item  = PanelItem(x0, y0, x1, y1, props or PanelProps(), pid)
        self.addItem(item)
        self._panels.append(item)
        self.reconstruir()
        return item

    def eliminar_seleccionados(self):
        for item in list(self.selectedItems()):
            if isinstance(item, PanelItem):
                self.removeItem(item)
                self._panels.remove(item)
        self.reconstruir()

    # ── Reconstruccion de vigas y columnas ────────────────────────────────────

    def reconstruir(self):
        for it in self._vigas + self._cols:
            self.removeItem(it)
        self._vigas.clear()
        self._cols.clear()

        h_beams: dict[float, list] = {}
        v_beams: dict[float, list] = {}

        for p in self._panels:
            r  = p.rect_scene()
            x0 = r.x();          y0 = r.y()
            x1 = r.x() + r.width(); y1 = r.y() + r.height()
            if p.props.edge_n: h_beams.setdefault(y0, []).append((x0, x1))
            if p.props.edge_s: h_beams.setdefault(y1, []).append((x0, x1))
            if p.props.edge_w: v_beams.setdefault(x0, []).append((y0, y1))
            if p.props.edge_e: v_beams.setdefault(x1, []).append((y0, y1))

        mh = {y: _merge_segs(s) for y, s in h_beams.items()}
        mv = {x: _merge_segs(s) for x, s in v_beams.items()}

        for y, segs in mh.items():
            for x0, x1 in segs:
                it = VigaItem(x0, y, x1, y)
                self.addItem(it); self._vigas.append(it)

        for x, segs in mv.items():
            for y0, y1 in segs:
                it = VigaItem(x, y0, x, y1)
                self.addItem(it); self._vigas.append(it)

        # Columnas en extremos de vigas e intersecciones
        col_pts: set[tuple[float, float]] = set()
        for y, segs in mh.items():
            for x0, x1 in segs:
                col_pts.add((_snap(x0), _snap(y)))
                col_pts.add((_snap(x1), _snap(y)))
        for x, segs in mv.items():
            for y0, y1 in segs:
                col_pts.add((_snap(x), _snap(y0)))
                col_pts.add((_snap(x), _snap(y1)))
        for y, h_segs in mh.items():
            for x, v_segs in mv.items():
                xs, ys = _snap(x), _snap(y)
                for x0, x1 in h_segs:
                    for y0, y1 in v_segs:
                        if x0 - 1 <= xs <= x1 + 1 and y0 - 1 <= ys <= y1 + 1:
                            col_pts.add((xs, ys))

        for cx, cy in col_pts:
            it = ColumnaItem(cx, cy)
            self.addItem(it); self._cols.append(it)

        self.modelo_listo.emit()

    # ── Fondo de grilla ───────────────────────────────────────────────────────

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        step  = SNAP_M * SCALE
        major = step * 5

        x = int(rect.left()  / step) * step
        while x <= rect.right():
            maj = abs(round(x / major) * major - x) < 0.5
            painter.setPen(QPen(_C_GRID_MAJ if maj else _C_GRID, 0.5))
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += step

        y = int(rect.top() / step) * step
        while y <= rect.bottom():
            maj = abs(round(y / major) * major - y) < 0.5
            painter.setPen(QPen(_C_GRID_MAJ if maj else _C_GRID, 0.5))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += step

    # ── Conversion a PlantaEstructural ───────────────────────────────────────

    def to_planta_estructural(self, hormigon, acero, sec_viga, sec_col,
                               h_entrepiso: float):
        if not self._panels:
            return None

        from hormigon.modelo import (
            ColumnaEsquema, Grilla, PanelLosa, PlantaEstructural, VigaEsquema,
        )

        xs = set()
        ys = set()
        for p in self._panels:
            xs.add(p.x0_m()); xs.add(p.x1_m())
            ys.add(p.y0_m()); ys.add(p.y1_m())

        ejes_x = sorted(xs)
        ejes_y = sorted(ys)
        xi = {x: i for i, x in enumerate(ejes_x)}
        yj = {y: j for j, y in enumerate(ejes_y)}

        grilla = Grilla(ejes_x=ejes_x, ejes_y=ejes_y)
        planta = PlantaEstructural(grilla=grilla, hormigon=hormigon, acero=acero)

        for p in self._panels:
            i = xi.get(p.x0_m()); j = yj.get(p.y0_m())
            if i is None or j is None:
                continue
            pr = p.props
            planta.agregar_losa(PanelLosa(
                id=p.panel_id, i=i, j=j,
                h=pr.h, tipo=pr.tipo,
                wD=pr.wD, wL=pr.wL,
                dir_1dir=pr.dir_1dir,
                tipo_a='ext_empotrado',
                tipo_b='ext_empotrado',
            ))

        # Recolectar segmentos de vigas desde paneles
        h_segs: dict[float, list] = {}
        v_segs: dict[float, list] = {}
        for p in self._panels:
            r  = p.rect_scene()
            x0 = r.x();          y0 = r.y()
            x1 = r.x() + r.width(); y1 = r.y() + r.height()
            if p.props.edge_n: h_segs.setdefault(y0, []).append((x0, x1))
            if p.props.edge_s: h_segs.setdefault(y1, []).append((x0, x1))
            if p.props.edge_w: v_segs.setdefault(x0, []).append((y0, y1))
            if p.props.edge_e: v_segs.setdefault(x1, []).append((y0, y1))

        vid_set: set[str] = set()

        for y_px, segs in h_segs.items():
            y_m = _to_m(y_px)
            j   = yj.get(y_m)
            if j is None:
                continue
            for xa_px, xb_px in _merge_segs(segs):
                i0 = xi.get(_to_m(xa_px)); i1 = xi.get(_to_m(xb_px))
                if i0 is None or i1 is None or i0 == i1:
                    continue
                vid = f'Vx_{j}_{i0}_{i1}'
                if vid not in vid_set:
                    vid_set.add(vid)
                    planta.agregar_viga(VigaEsquema(
                        id=vid, dir='x', idx=j,
                        desde=i0, hasta=i1,
                        seccion=sec_viga, extremo='columna',
                    ))

        for x_px, segs in v_segs.items():
            x_m = _to_m(x_px)
            i   = xi.get(x_m)
            if i is None:
                continue
            for ya_px, yb_px in _merge_segs(segs):
                j0 = yj.get(_to_m(ya_px)); j1 = yj.get(_to_m(yb_px))
                if j0 is None or j1 is None or j0 == j1:
                    continue
                vid = f'Vy_{i}_{j0}_{j1}'
                if vid not in vid_set:
                    vid_set.add(vid)
                    planta.agregar_viga(VigaEsquema(
                        id=vid, dir='y', idx=i,
                        desde=j0, hasta=j1,
                        seccion=sec_viga, extremo='columna',
                    ))

        # Recompute column positions from panel corners in meters (not from
        # ColumnaItem pixel positions, which can be misplaced by _snap rounding).
        h_beam_m: dict[float, list[tuple[float, float]]] = {}
        v_beam_m: dict[float, list[tuple[float, float]]] = {}
        for p in self._panels:
            x0m, x1m = p.x0_m(), p.x1_m()
            y0m, y1m = p.y0_m(), p.y1_m()
            if p.props.edge_n: h_beam_m.setdefault(y0m, []).append((x0m, x1m))
            if p.props.edge_s: h_beam_m.setdefault(y1m, []).append((x0m, x1m))
            if p.props.edge_w: v_beam_m.setdefault(x0m, []).append((y0m, y1m))
            if p.props.edge_e: v_beam_m.setdefault(x1m, []).append((y0m, y1m))

        col_pts_m: set[tuple[float, float]] = set()
        for y_m, segs in h_beam_m.items():
            for x0, x1 in _merge_segs_m(segs):
                col_pts_m.add((x0, y_m))
                col_pts_m.add((x1, y_m))
        for x_m, segs in v_beam_m.items():
            for y0, y1 in _merge_segs_m(segs):
                col_pts_m.add((x_m, y0))
                col_pts_m.add((x_m, y1))

        col_added: set[tuple[int, int]] = set()
        for x_m, y_m in sorted(col_pts_m):
            ix = xi.get(x_m); iy = yj.get(y_m)
            if ix is None or iy is None:
                continue
            key = (ix, iy)
            if key not in col_added:
                col_added.add(key)
                planta.agregar_columna(ColumnaEsquema(
                    id=f'C{len(col_added)-1}',
                    ix=ix, iy=iy,
                    seccion=sec_col,
                    h_entrepiso=h_entrepiso,
                ))

        return planta


# ── Vista ─────────────────────────────────────────────────────────────────────

class PlantaView(QGraphicsView):

    def __init__(self, scene: PlantaScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setStyleSheet('background: #1a1a1a;')

        self._drawing   = False
        self._panning   = False
        self._draw_start_view  = None
        self._draw_start_scene = None
        self._pan_start = None
        self._rubber: QRubberBand | None = None
        self._default_props = PanelProps()

    def set_default_props(self, props: PanelProps):
        self._default_props = props

    # ── Zoom ─────────────────────────────────────────────────────────────────

    def wheelEvent(self, event):
        f = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(f, f)

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning   = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            sc_pos = self.mapToScene(event.pos())
            item   = self.scene().itemAt(sc_pos, self.transform())
            if not isinstance(item, PanelItem):
                self._drawing          = True
                self._draw_start_view  = event.pos()
                self._draw_start_scene = sc_pos
                if self._rubber is None:
                    self._rubber = QRubberBand(
                        QRubberBand.Shape.Rectangle, self.viewport())
                self._rubber.setGeometry(QRect(event.pos(), QSize()))
                self._rubber.show()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_start is not None:
            d = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - d.y())
            return
        if self._drawing and self._rubber:
            self._rubber.setGeometry(
                QRect(self._draw_start_view, event.pos()).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if event.button() == Qt.MouseButton.LeftButton and self._drawing:
            self._drawing = False
            if self._rubber:
                self._rubber.hide()
            end = self.mapToScene(event.pos())
            step = SNAP_M * SCALE
            x0 = _snap(min(self._draw_start_scene.x(), end.x()))
            y0 = _snap(min(self._draw_start_scene.y(), end.y()))
            x1 = _snap(max(self._draw_start_scene.x(), end.x()))
            y1 = _snap(max(self._draw_start_scene.y(), end.y()))
            if (x1 - x0) >= step and (y1 - y0) >= step:
                from dataclasses import replace
                self.scene().agregar_panel(
                    x0, y0, x1, y1,
                    replace(self._default_props),
                )
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.scene().eliminar_seleccionados()
        else:
            super().keyPressEvent(event)
