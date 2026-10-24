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
from app.widgets.panel_resultados import PanelResultados
from app.widgets.visor_3d import VisorPlotly3D
from app.widgets.selector_materiales import SelectorMateriales
from app.widgets.entradas import con_scroll

def _figura_compacta(fig):
    """Copia de la figura 3D adaptada al panel lateral (sin título, rótulos chicos)."""
    import plotly.graph_objects as go
    f = go.Figure(fig)
    # Los rótulos no entran en el panel; los valores están en el CRT y en la vista ampliada
    f.update_traces(visible=False, selector=dict(type='scatter3d', mode='text'))
    f.update_layout(
        title=None,
        font=dict(size=9),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation='h', x=0, y=0, font=dict(size=9),
                    bgcolor='rgba(255,255,255,0.6)'),
        scene_camera=dict(eye=dict(x=1.6, y=-2.3, z=1.6)),
        scene=dict(xaxis_title='', yaxis_title='', zaxis_title=''),
    )
    return f


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
        self._fig3d       = None
        self._propagacion = None
        self._setup_ui()

    # ── Construccion ─────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel('E-09  ·  Planta estructural')
        titulo.setObjectName('modulo_titulo')
        root.addWidget(titulo)

        sub = QLabel(
            'Punto de partida para estructuras completas — modelar la planta con drag & drop y propagar '
            'cargas gravitacionales  ·  Alimenta: V-05 y P-03 automáticamente (botón Abrir en módulo)'
        )
        sub.setObjectName('modulo_subtitulo')
        root.addWidget(sub)

        body = QWidget()
        hl = QHBoxLayout(body)
        hl.setContentsMargins(4, 4, 4, 4)
        hl.setSpacing(4)

        self._scene = PlantaScene()
        self._view  = PlantaView(self._scene)
        self._scene.modelo_listo.connect(self._on_modelo_listo)
        self._scene.elemento_activado.connect(self._abrir_elemento)

        hl.addWidget(con_scroll(self._panel_izq()), 0)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        hl.addWidget(sep)

        hl.addWidget(self._view, 1)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine)
        hl.addWidget(sep2)

        hl.addWidget(self._panel_der(), 0)

        root.addWidget(body, 1)
        root.addWidget(self._barra_inferior())

    # ── Panel izquierdo: configuracion ───────────────────────────────────────

    def _panel_izq(self) -> QWidget:
        w = QWidget(); w.setFixedWidth(230)
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

        grp_p = QGroupBox('PLANTA')
        vp = QVBoxLayout(grp_p)
        vp.setSpacing(4)
        btn_ej = QPushButton('Cargar ejemplo')
        btn_ej.setToolTip('Planta de ejemplo: 3 × 2 paños de losa (14 m × 9 m)')
        btn_ej.clicked.connect(self.cargar_ejemplo)
        btn_fit = QPushButton('Encuadrar')
        btn_fit.setToolTip('Ajustar el zoom a toda la planta')
        btn_fit.clicked.connect(self._view.encuadrar)
        btn_clr = QPushButton('Limpiar')
        btn_clr.setToolTip('Borrar todos los paneles')
        btn_clr.clicked.connect(self._limpiar)
        self.btn_3d = QPushButton('Ver 3D ampliado')
        self.btn_3d.setToolTip('Abrir el modelo 3D en una ventana grande (disponible tras PROPAGAR)')
        self.btn_3d.setEnabled(False)
        self.btn_3d.clicked.connect(self._ver_3d_ampliado)
        for b in (btn_ej, btn_fit, btn_clr, self.btn_3d):
            vp.addWidget(b)
        lay.addWidget(grp_p)

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
        self.panel_res   = PanelResultados()
        self.panel_res.mostrar_bienvenida('E-09 · PLANTA ESTRUCTURAL')
        spl.addWidget(self.visor)
        spl.addWidget(self.panel_res)
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
        self.combo_env_id.setToolTip('ID del elemento — disponible después de Propagar cargas')

        btn_env = QPushButton('Abrir en módulo  →')
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
            'Arrastrar: nueva losa  ·  Arrastrar losa: mover  ·  Doble clic: editar / abrir  ·  '
            'Supr: borrar  ·  Botón derecho: desplazar  ·  Rueda: zoom  ·  '
            'Pasar el mouse: ver datos'
        )
        hint.setObjectName('status_label')
        hl.addWidget(hint, 1)

        self._lbl_conteo = QLabel('0 paneles  0 vigas  0 columnas')
        self._lbl_conteo.setObjectName('status_label')
        hl.addWidget(self._lbl_conteo)

        self.btn_prop = QPushButton('Propagar cargas')
        self.btn_prop.setObjectName('btn_calcular')
        self.btn_prop.clicked.connect(self._ejecutar)
        hl.addWidget(self.btn_prop)

        return w

    # ── Planta: ejemplo, limpieza y sesión ───────────────────────────────────

    _EJEMPLO = [  # (x0, y0, x1, y1) en metros
        (0, 0, 5, 4.5), (5, 0, 10, 4.5), (10, 0, 14, 4.5),
        (0, 4.5, 5, 9), (5, 4.5, 10, 9), (10, 4.5, 14, 9),
    ]

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # La primera vez se abre con la planta de ejemplo (la vista ya tiene tamaño)
        if not getattr(self, '_mostrado', False):
            self._mostrado = True
            if not self._scene._panels:
                self.cargar_ejemplo()

    def cargar_ejemplo(self) -> None:
        self._sync_defaults()
        props = self._view._default_props
        self._scene.importar([
            {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'props': vars(props)}
            for x0, y0, x1, y1 in self._EJEMPLO
        ])
        self._invalidar_resultados()
        self._view.encuadrar()

    def _limpiar(self) -> None:
        self._scene.limpiar()
        self._invalidar_resultados()

    def _invalidar_resultados(self) -> None:
        self._planta = None
        self._propagacion = None
        self.combo_env_id.clear()
        self.visor.limpiar()
        self._fig3d = None
        self.btn_3d.setEnabled(False)
        self.panel_res.mostrar_bienvenida('E-09 · PLANTA ESTRUCTURAL')

    def _ver_3d_ampliado(self) -> None:
        if self._fig3d is None:
            return
        from PyQt6.QtWidgets import QDialog
        dlg = getattr(self, '_dlg_3d', None)
        if dlg is None:
            dlg = self._dlg_3d = QDialog(self)
            dlg.setWindowTitle('E-09 / PLANTA  —  MODELO 3D')
            dlg.resize(1100, 720)
            lay = QVBoxLayout(dlg)
            lay.setContentsMargins(0, 0, 0, 0)
            dlg.visor = VisorPlotly3D()
            lay.addWidget(dlg.visor)
        import plotly.graph_objects as go
        fig = go.Figure(self._fig3d)
        fig.update_layout(scene_camera=dict(eye=dict(x=1.25, y=-1.75, z=1.15)))
        dlg.visor.mostrar_figura(fig)
        dlg.show()
        dlg.raise_()

    def get_estado(self) -> dict:
        return {
            'materiales': self.sel_mat.get_datos(),
            'paneles':    self._scene.exportar(),
            'viga':    [self.spn_bv.value(), self.spn_hv.value()],
            'columna': [self.spn_bc.value(), self.spn_hc.value(), self.spn_he.value()],
        }

    def set_estado(self, d: dict) -> None:
        self.sel_mat.set_datos(d.get('materiales', {}))
        bv, hv = d.get('viga', [0.25, 0.50])
        bc, hc, he = d.get('columna', [0.30, 0.30, 3.0])
        self.spn_bv.setValue(bv); self.spn_hv.setValue(hv)
        self.spn_bc.setValue(bc); self.spn_hc.setValue(hc); self.spn_he.setValue(he)
        self._scene.importar(d.get('paneles', []))
        self._invalidar_resultados()
        self._view.encuadrar()

    # ── Señales y logica ──────────────────────────────────────────────────────

    def _on_modelo_listo(self):
        # Cualquier cambio en la planta deja obsoletas las cargas propagadas
        if self._propagacion is not None:
            self._invalidar_resultados()
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
                self.panel_res.mostrar_error('No hay paneles en la planta.')
                return
            if not planta.columnas:
                self.panel_res.mostrar_error(
                    'Sin columnas — asignar vigas en los bordes de las losas.')
                return

            from hormigon.propagacion import propagar
            self._planta      = planta
            self._propagacion = propagar(planta)

            self.panel_res.mostrar_resultado_propagacion(self._propagacion)
            self._scene.asignar_resultados(planta, self._propagacion)
            self._actualizar_ids()

            from graficos.modelo_3d import visualizar_planta_3d
            fig = visualizar_planta_3d(
                planta, propagacion=self._propagacion,
                titulo='Planta Estructural')
            self._fig3d = fig
            self.visor.mostrar_figura(_figura_compacta(fig))
            self.btn_3d.setEnabled(True)

        except Exception as e:
            import traceback
            self.panel_res.mostrar_error(
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

    def _abrir_elemento(self, tipo: str, elem_id: str) -> None:
        """Doble clic sobre una viga o columna del lienzo."""
        self.combo_env_tipo.setCurrentText(tipo)
        self._actualizar_ids()
        self.combo_env_id.setCurrentText(elem_id)
        self._enviar_a_modulo()

    def _enviar_a_modulo(self):
        """Pre-llena el módulo de cálculo correspondiente y cambia de pestaña."""
        if self._propagacion is None or self._planta is None:
            self.panel_res.mostrar_error('Primero presione Propagar cargas.')
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
