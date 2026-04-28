"""
MÓDULO-09 / PLANTA  —  Editor visual con drag & drop
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QPushButton, QDoubleSpinBox, QComboBox, QFrame,
    QSplitter,
)
from PyQt6.QtCore import Qt

from app.widgets.canvas_planta import PlantaScene, PlantaView, PanelProps
from app.widgets.panel_crt import PanelCRT
from app.widgets.visor_3d import VisorPlotly3D
from app.widgets.selector_materiales import SelectorMateriales

# Mapas fc → nombre de combo y fy → nombre de combo
_FC_NOMBRES = {17: 'H17', 21: 'H21', 25: 'H25', 30: 'H30', 35: 'H35', 40: 'H40'}
_FY_NOMBRES = {420: 'ADN 420', 500: 'AM 500N'}


def _mat_datos(hormigon, acero) -> dict:
    """Serializa materiales al formato de SelectorMateriales.set_datos()."""
    fc, fy = hormigon.fc, acero.fy
    d = {
        'hormigon': _FC_NOMBRES.get(fc, 'Personalizado'),
        'acero':    _FY_NOMBRES.get(fy, 'Personalizado'),
    }
    if d['hormigon'] == 'Personalizado':
        d['fc'] = str(fc)
    if d['acero'] == 'Personalizado':
        d['fy'] = str(fy)
    return d


def _sec_datos(sec) -> dict:
    """Serializa SeccionRectangular al formato de SelectorSeccion.set_datos()."""
    return {
        'tipo': 0,
        'b':   str(sec.b),
        'h':   str(sec.h),
        'rec': str(sec.recubrimiento),
    }


class VentanaPlantaCanvas(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._planta      = None
        self._propagacion = None
        self._setup_ui()

    # ── Construccion ─────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('MÓDULO-09 / PLANTA  —  EDITOR VISUAL DE PLANTA ESTRUCTURAL')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        body = QWidget()
        hl = QHBoxLayout(body)
        hl.setContentsMargins(4, 4, 4, 4)
        hl.setSpacing(4)

        hl.addWidget(self._panel_izq(), 0)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        hl.addWidget(sep)

        self._scene = PlantaScene()
        self._view  = PlantaView(self._scene)
        self._scene.modelo_listo.connect(self._on_modelo_listo)
        hl.addWidget(self._view, 1)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine)
        hl.addWidget(sep2)

        hl.addWidget(self._panel_der(), 0)

        root.addWidget(body, 1)
        root.addWidget(self._barra_inferior())

    # ── Panel izquierdo: configuracion ───────────────────────────────────────

    def _panel_izq(self) -> QWidget:
        w = QWidget(); w.setFixedWidth(210)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 4, 0)
        lay.setSpacing(6)

        self.sel_mat = SelectorMateriales()
        lay.addWidget(self.sel_mat)

        grp_l = QGroupBox('LOSA (nuevo panel)')
        f = QFormLayout(grp_l)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.spn_h_def  = QDoubleSpinBox()
        self.spn_h_def.setRange(5, 50); self.spn_h_def.setValue(14)
        self.spn_h_def.setSuffix(' cm'); self.spn_h_def.setDecimals(0)

        self.cmb_tipo   = QComboBox(); self.cmb_tipo.addItems(['2dir', '1dir'])
        self.spn_wD_def = QDoubleSpinBox()
        self.spn_wD_def.setRange(0, 50); self.spn_wD_def.setValue(1.5)
        self.spn_wD_def.setSuffix(' kN/m2'); self.spn_wD_def.setDecimals(2)
        self.spn_wL_def = QDoubleSpinBox()
        self.spn_wL_def.setRange(0, 50); self.spn_wL_def.setValue(2.0)
        self.spn_wL_def.setSuffix(' kN/m2'); self.spn_wL_def.setDecimals(2)

        f.addRow('h:', self.spn_h_def)
        f.addRow('Tipo:', self.cmb_tipo)
        f.addRow('wD:', self.spn_wD_def)
        f.addRow('wL:', self.spn_wL_def)

        for w_ in (self.spn_h_def, self.spn_wD_def, self.spn_wL_def):
            w_.valueChanged.connect(self._sync_defaults)
        self.cmb_tipo.currentTextChanged.connect(self._sync_defaults)

        lay.addWidget(grp_l)

        grp_s = QGroupBox('SECCIONES')
        fs = QFormLayout(grp_s)
        fs.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        lv = QLabel('— VIGAS —'); lv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fs.addRow(lv)
        self.spn_bv = QDoubleSpinBox(); self.spn_bv.setRange(0.1,1.0); self.spn_bv.setValue(0.25); self.spn_bv.setSuffix(' m')
        self.spn_hv = QDoubleSpinBox(); self.spn_hv.setRange(0.1,2.0); self.spn_hv.setValue(0.50); self.spn_hv.setSuffix(' m')
        fs.addRow('b:', self.spn_bv); fs.addRow('h:', self.spn_hv)

        lc = QLabel('— COLUMNAS —'); lc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fs.addRow(lc)
        self.spn_bc = QDoubleSpinBox(); self.spn_bc.setRange(0.1,1.0); self.spn_bc.setValue(0.30); self.spn_bc.setSuffix(' m')
        self.spn_hc = QDoubleSpinBox(); self.spn_hc.setRange(0.1,1.0); self.spn_hc.setValue(0.30); self.spn_hc.setSuffix(' m')
        self.spn_he = QDoubleSpinBox(); self.spn_he.setRange(2.0,12.0); self.spn_he.setValue(3.0); self.spn_he.setSuffix(' m')
        fs.addRow('b:', self.spn_bc); fs.addRow('h:', self.spn_hc)
        fs.addRow('H piso:', self.spn_he)

        lay.addWidget(grp_s)
        lay.addStretch()
        return w

    # ── Panel derecho: resultados + envío ─────────────────────────────────────

    def _panel_der(self) -> QWidget:
        w = QWidget(); w.setFixedWidth(310)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 0, 0, 0)
        lay.setSpacing(4)

        spl = QSplitter(Qt.Orientation.Vertical)
        self.visor = VisorPlotly3D()
        self.crt   = PanelCRT()
        self.crt.mostrar_bienvenida('E-09 PLANTA')
        spl.addWidget(self.visor)
        spl.addWidget(self.crt)
        spl.setSizes([370, 180])

        lay.addWidget(spl, 1)
        lay.addWidget(self._panel_enviar())
        return w

    def _panel_enviar(self) -> QWidget:
        grp = QGroupBox('ENVIAR A MÓDULO')
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(4)

        self.combo_env_tipo = QComboBox()
        self.combo_env_tipo.addItems(['VIGA', 'COLUMNA'])
        self.combo_env_tipo.setToolTip(
            'VIGA → abre el elemento en V-05 como viga continua\n'
            'COLUMNA → abre el elemento en P-03 con Pu y Mu propagados'
        )
        self.combo_env_tipo.currentIndexChanged.connect(self._actualizar_ids)

        self.combo_env_id = QComboBox()
        self.combo_env_id.setToolTip('ID del elemento — disponible después de PROPAGAR CARGAS')

        btn_env = QPushButton('ABRIR EN MÓDULO  →')
        btn_env.setObjectName('btn_calcular')
        btn_env.setToolTip(
            'Pre-llena el módulo de cálculo con los datos del elemento seleccionado\n'
            'y cambia a ese módulo automáticamente'
        )
        btn_env.clicked.connect(self._enviar_a_modulo)

        form.addRow('Tipo:', self.combo_env_tipo)
        form.addRow('ID:', self.combo_env_id)
        form.addRow('', btn_env)
        return grp

    # ── Barra inferior ────────────────────────────────────────────────────────

    def _barra_inferior(self) -> QWidget:
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(8, 3, 8, 3)

        hint = QLabel(
            'Drag: nueva losa  |  Drag sobre losa: mover  |  '
            'Dbl-click: propiedades  |  Supr: eliminar  |  '
            'Drag derecho: paneo  |  Scroll: zoom'
        )
        hint.setObjectName('status_label')
        hl.addWidget(hint, 1)

        self._lbl_conteo = QLabel('0 paneles  0 vigas  0 columnas')
        self._lbl_conteo.setObjectName('status_label')
        hl.addWidget(self._lbl_conteo)

        self.btn_prop = QPushButton('PROPAGAR CARGAS  [E-09]')
        self.btn_prop.setObjectName('btn_calcular')
        self.btn_prop.clicked.connect(self._ejecutar)
        hl.addWidget(self.btn_prop)

        return w

    # ── Señales y logica ──────────────────────────────────────────────────────

    def _on_modelo_listo(self):
        np = len(self._scene._panels)
        nv = len(self._scene._vigas)
        nc = len(self._scene._cols)
        self._lbl_conteo.setText(
            f'{np} panel{"es" if np!=1 else ""}  '
            f'{nv} viga{"s" if nv!=1 else ""}  '
            f'{nc} columna{"s" if nc!=1 else ""}')

    def _sync_defaults(self):
        self._view.set_default_props(PanelProps(
            h=self.spn_h_def.value() / 100,
            tipo=self.cmb_tipo.currentText(),
            wD=self.spn_wD_def.value(),
            wL=self.spn_wL_def.value(),
        ))

    def _ejecutar(self):
        try:
            self._sync_defaults()
            horm = self.sel_mat.get_hormigon()
            acer = self.sel_mat.get_acero()

            from hormigon.secciones import SeccionRectangular
            sec_v = SeccionRectangular(
                b=self.spn_bv.value(), h=self.spn_hv.value(),
                recubrimiento=0.06, hormigon=horm, acero=acer)
            sec_c = SeccionRectangular(
                b=self.spn_bc.value(), h=self.spn_hc.value(),
                recubrimiento=0.06, hormigon=horm, acero=acer)

            planta = self._scene.to_planta_estructural(
                horm, acer, sec_v, sec_c, self.spn_he.value())

            if planta is None:
                self.crt.mostrar_error('No hay paneles en la planta.')
                return
            if not planta.columnas:
                self.crt.mostrar_error(
                    'Sin columnas — asignar vigas en los bordes de las losas.')
                return

            from hormigon.propagacion import propagar
            self._planta      = planta
            self._propagacion = propagar(planta)

            self.crt.mostrar_resultado_propagacion(self._propagacion)
            self._actualizar_ids()

            from graficos.modelo_3d import visualizar_planta_3d
            fig = visualizar_planta_3d(
                planta, propagacion=self._propagacion,
                titulo='Planta Estructural')
            self.visor.mostrar_figura(fig)

        except Exception as e:
            import traceback
            self.crt.mostrar_error(
                f'{type(e).__name__}: {e}\n{traceback.format_exc()[-300:]}')

    # ── Envío a módulos ───────────────────────────────────────────────────────

    def _actualizar_ids(self):
        """Rellena el combo de IDs según el tipo de elemento y la propagación actual."""
        self.combo_env_id.clear()
        if self._propagacion is None:
            return
        tipo = self.combo_env_tipo.currentText()
        if tipo == 'VIGA':
            ids = sorted(self._propagacion.cargas_vigas.keys())
        else:
            ids = sorted(self._propagacion.cargas_columnas.keys())
        self.combo_env_id.addItems(ids)

    def _enviar_a_modulo(self):
        """Pre-llena el módulo de cálculo correspondiente y cambia de pestaña."""
        if self._propagacion is None or self._planta is None:
            self.crt.mostrar_error('Primero ejecutar PROPAGAR CARGAS.')
            return

        tipo    = self.combo_env_tipo.currentText()
        elem_id = self.combo_env_id.currentText()
        if not elem_id:
            return

        main = self.window()  # VentanaPrincipal

        if tipo == 'VIGA':
            cv   = self._propagacion.cargas_vigas.get(elem_id)
            viga = self._planta.vigas.get(elem_id)
            if cv is None or viga is None:
                return

            estado = {
                'materiales': _mat_datos(self._planta.hormigon, self._planta.acero),
                'seccion':    _sec_datos(viga.seccion),
                'tipo': 2,  # CONTINUA
                'c_ln':  str(round(cv.ln_disenio, 3)),
                'c_wD':  str(round(cv.wD, 3)),
                'c_wL':  str(round(cv.wL, 3)),
                'c_n':   cv.n_tramos,
                'c_ext': viga.extremo,
                # Valores por defecto para los otros tipos (no usados)
                's_L': '6.0', 's_wD': str(round(cv.wD, 3)), 's_wL': str(round(cv.wL, 3)),
                'v_L': '2.0', 'v_wD': '10.0', 'v_wL': '8.0', 'v_PD': '0.0', 'v_PL': '0.0',
            }
            main.stack.widget(4).set_estado(estado)   # VentanaViga (índice 4)
            main._cambiar_modulo(4)

        elif tipo == 'COLUMNA':
            cc  = self._propagacion.cargas_columnas.get(elem_id)
            col = self._planta.columnas.get(elem_id)
            if cc is None or col is None:
                return

            estado = {
                'materiales': _mat_datos(self._planta.hormigon, self._planta.acero),
                'seccion':    _sec_datos(col.seccion),
                'Pu':   str(round(cc.Pu, 1)),
                'Mu':   str(round(cc.Mu, 2)),
                'tipo': 0 if col.tipo == 'estribos' else 1,
                'phi_adop': 'φ20',
                'n_adop': 8,
            }
            main.stack.widget(2).set_estado(estado)   # VentanaColumnas (índice 2)
            main._cambiar_modulo(2)
