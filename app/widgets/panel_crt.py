"""
PanelCRT — panel de resultados estilo terminal CRT.

Fondo negro, texto coloreado según tema activo, fuente monoespaciada.
Los colores se leen del tema en cada renderizado.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont

_FONT       = 'font-family:Consolas,"Courier New",monospace; font-size:11px;'
_BODY_CLOSE = '</body>'


def _ln(texto: str, color: str) -> str:
    texto_esc = (texto
                 .replace('&', '&amp;')
                 .replace('<', '&lt;')
                 .replace('>', '&gt;'))
    return f'<span style="color:{color}; {_FONT}">{texto_esc}</span><br>'


class PanelCRT(QTextEdit):
    """Terminal CRT embebida en Qt — solo lectura, HTML colored."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('panel_crt')
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 10))

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _t(self):
        from app.themes import get_tema
        return get_tema()

    def _body_open(self) -> str:
        return f'<body style="background-color:{self._t().crt_fondo}; margin:6px;">'

    def _sep(self) -> str:
        return _ln('─' * 52, self._t().crt_gris)

    # ── Métodos de presentación ──────────────────────────────────────────────

    def limpiar(self) -> None:
        self.setHtml(self._body_open() + _BODY_CLOSE)

    def mostrar_bienvenida(self, modulo: str) -> None:
        t = self._t()
        html = (
            self._body_open()
            + _ln('> SISTEMA DE CÁLCULO ESTRUCTURAL // CIRSOC 201-2005', t.crt_ambar)
            + _ln(f'> MÓDULO: {modulo}', t.crt_verde)
            + self._sep()
            + _ln('> Ingrese los parámetros y ejecute el protocolo.', t.crt_gris)
            + _BODY_CLOSE
        )
        self.setHtml(html)

    def mostrar_error(self, mensaje: str) -> None:
        t = self._t()
        html = (
            self._body_open()
            + _ln('> ERROR DE PROTOCOLO', t.crt_rojo)
            + self._sep()
            + _ln(f'> {mensaje}', t.crt_ambar)
            + _BODY_CLOSE
        )
        self.setHtml(html)

    def mostrar_resultado_flexion(self, r) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO F-01 EJECUTADO', t.crt_ambar),
            None,
            (f'>  Mu ........................... {r.Mu:>10.2f} kNm', t.crt_verde),
            (f'>  φ ............................ {r.phi:>10.2f}  ({r.tipo.upper()})', t.crt_verde),
            (f'>  Mn = Mu/φ ................... {r.Mn:>10.2f} kNm', t.crt_verde),
            (f'>  φ·Mn ........................ {r.phi_Mn:>10.2f} kNm', t.crt_verde),
            (f'>  a (bloque tensiones) ......... {r.a*100:>10.2f} cm', t.crt_verde),
            (f'>  c (eje neutro) ............... {r.c*100:>10.2f} cm', t.crt_verde),
            (f'>  εs (acero) .................. {r.epsilon_s:>10.5f}', t.crt_verde),
            (f'>  As calculada ................. {r.As:>10.2f} cm²', t.crt_verde),
        ]
        if r.As_prima > 0:
            lineas.append(
                (f">  As' comprimida ............... {r.As_prima:>10.2f} cm²", t.crt_ambar)
            )
        if r.As_adoptada is not None:
            lineas.append(None)
            lineas.append(
                (f'>  ARMADO: {r.n_barras}φ{r.phi_adoptado} = {r.As_adoptada:.2f} cm²', t.crt_ambar)
            )
        lineas.append(None)
        lineas.append(
            ('> ESTADO: NOMINAL', t.crt_verde) if r.verifica
            else ('> ALERTA — CAPACIDAD INSUFICIENTE', t.crt_rojo)
        )
        self._renderizar(lineas)

    def mostrar_resultado_corte(self, r) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO C-02 EJECUTADO', t.crt_ambar),
            None,
            (f'>  Vu ........................... {r.Vu:>10.2f} kN', t.crt_verde),
            (f'>  Vc (hormigón) ................ {r.Vc:>10.2f} kN', t.crt_verde),
            (f'>  Vs requerido ................. {r.Vs_requerido:>10.2f} kN', t.crt_verde),
            (f'>  φ·Vn ........................ {r.phi_Vn:>10.2f} kN', t.crt_verde),
            (f'>  Vn_max ...................... {r.Vn_max:>10.2f} kN', t.crt_verde),
            (f'>  Av/s calculado ............... {r.Avs_calculado:>10.1f} mm²/m', t.crt_verde),
            (f'>  Av/s mínimo .................. {r.Avs_minimo:>10.1f} mm²/m', t.crt_verde),
            (f'>  Av/s adoptado ................ {r.Avs_adoptado:>10.1f} mm²/m', t.crt_verde),
            (f'>  s máximo ..................... {r.s_maximo*100:>10.1f} cm', t.crt_verde),
        ]
        lineas.append(None)
        if r.verifica_resistencia and r.verifica_Vn_max:
            lineas.append(('> ESTADO: NOMINAL', t.crt_verde))
        else:
            msg = ('RESISTENCIA INSUFICIENTE' if not r.verifica_resistencia
                   else 'Vn SUPERA EL MÁXIMO — AMPLIAR SECCIÓN')
            lineas.append((f'> ALERTA — {msg}', t.crt_rojo))
        self._renderizar(lineas)

    def mostrar_resultado_columna(self, r) -> None:
        from hormigon.columnas import RHO_MIN, RHO_MAX
        t = self._t()
        lineas = [
            ('> PROTOCOLO P-03 EJECUTADO', t.crt_ambar),
            None,
            (f'>  Pu ........................... {r.Pu:>10.1f} kN', t.crt_verde),
            (f'>  Mu ........................... {r.Mu:>10.1f} kNm', t.crt_verde),
            (f'>  Ast calculada ................ {r.Ast:>10.2f} cm²', t.crt_verde),
            (f'>  ρg ........................... {r.rho_g:>10.4f}', t.crt_verde),
            (f'>  Rango ρg: [{RHO_MIN:.2f} — {RHO_MAX:.2f}]', t.crt_gris),
        ]
        if r.Ast_real is not None:
            lineas.append(None)
            lineas.append(
                (f'>  ADOPTADO: {r.n_barras}φ{r.phi_barra}  = {r.Ast_real:.2f} cm²', t.crt_ambar)
            )
        lineas.append(None)
        lineas.append(
            ('> ESTADO: NOMINAL', t.crt_verde) if r.verifica
            else ('> ALERTA — DEMANDA FUERA DEL DIAGRAMA P-M', t.crt_rojo)
        )
        self._renderizar(lineas)

    def mostrar_resultado_viga(self, r) -> None:
        t = self._t()
        tipo_str = 'Viga simple' if r.tipo == 'simple' else 'Viga en voladizo'
        rf = r.resultado_flex
        rc = r.resultado_corte
        lineas = [
            (f'> PROTOCOLO V-05 EJECUTADO — {tipo_str.upper()}', t.crt_ambar),
            None,
            (f'>  L  .......................... {r.L:>10.2f} m', t.crt_verde),
            (f'>  wu .......................... {r.wu:>10.2f} kN/m', t.crt_verde),
            (f'>  Mu .......................... {r.Mu:>10.2f} kNm', t.crt_verde),
            (f'>  Vu .......................... {r.Vu:>10.2f} kN', t.crt_verde),
            None,
            (f'>  As calculada ................ {rf.As:>10.2f} cm²', t.crt_verde),
            (f'>  φ·Mn ........................ {rf.phi_Mn:>10.2f} kNm', t.crt_verde),
            (f'>  Av/s adoptado ............... {rc.Avs_adoptado:>10.1f} mm²/m', t.crt_verde),
            (f'>  s máximo .................... {rc.s_maximo*100:>10.1f} cm', t.crt_verde),
            None,
            ('> ESTADO: NOMINAL', t.crt_verde) if (rf.verifica and rc.verifica_resistencia)
            else ('> ALERTA — VERIFICAR SECCIÓN', t.crt_rojo),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_viga_continua(self, r) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO V-05c EJECUTADO — VIGA CONTINUA', t.crt_ambar),
            None,
            (f'>  ln .......................... {r.ln:>10.2f} m', t.crt_verde),
            (f'>  wu .......................... {r.wu:>10.2f} kN/m', t.crt_verde),
            (f'>  n_tramos .................... {r.n_tramos:>10d}', t.crt_verde),
            (f'>  extremo ..................... {r.extremo:>10s}', t.crt_verde),
            None,
        ]
        for s in r.secciones:
            rf = s.resultado_flex
            ok = '✓' if rf.verifica else '✗'
            lineas.append(
                (f'>  {s.nombre[:28]:<28} {rf.As:>6.2f} cm²  {ok}', t.crt_verde)
            )
        lineas.append(None)
        todas_ok = all(s.resultado_flex.verifica for s in r.secciones)
        lineas.append(
            ('> ESTADO: NOMINAL', t.crt_verde) if todas_ok
            else ('> ALERTA — VERIFICAR SECCIONES', t.crt_rojo)
        )
        self._renderizar(lineas)

    def mostrar_resultado_losa(self, r) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO L-04 EJECUTADO — LOSA 1 DIRECCIÓN', t.crt_ambar),
            None,
            (f'>  h ........................... {r.h*100:>9.0f} cm', t.crt_verde),
            (f'>  h_min ....................... {r.h_min*100:>9.1f} cm  {"✓" if r.verifica_h else "✗"}', t.crt_verde),
            (f'>  d ........................... {r.d*100:>9.1f} cm', t.crt_verde),
            (f'>  wu .......................... {r.wu:>9.2f} kN/m²', t.crt_verde),
            None,
        ]
        for s in r.secciones:
            if s.Mu < 1e-6:
                continue
            ok = '✓' if s.verifica else '✗'
            lineas.append(
                (f'>  {s.nombre[:28]:<28} As={s.As:>5.2f}cm²  {ok}', t.crt_verde)
            )
        lineas += [
            None,
            (f'>  As temperatura .............. {r.As_temp:>9.2f} cm²/m', t.crt_verde),
            (f'>  Vu_max / φVc ................ {r.Vu_max:>5.1f} / {r.phi_Vc:>5.1f} kN/m  {"✓" if r.verifica_corte else "✗"}', t.crt_verde),
            None,
            ('> ESTADO: NOMINAL', t.crt_verde) if r.verifica_h and r.verifica_corte
            else ('> ALERTA — VERIFICAR', t.crt_rojo),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_torsion(self, r) -> None:
        t = self._t()
        if r.despreciable:
            lineas = [
                ('> PROTOCOLO T-06 EJECUTADO', t.crt_ambar),
                None,
                (f'>  Tu .......................... {r.Tu:>10.2f} kNm', t.crt_verde),
                (f'>  Tu_umbral ................... {r.Tu_umbral:>10.2f} kNm', t.crt_verde),
                None,
                ('>  Tu < Tu_umbral — TORSIÓN DESPRECIABLE', t.crt_verde),
                None,
                ('> ESTADO: NOMINAL', t.crt_verde),
            ]
        else:
            ok_comb = '✓' if r.verifica_combinado else '✗'
            lineas = [
                ('> PROTOCOLO T-06 EJECUTADO', t.crt_ambar),
                None,
                (f'>  Tu .......................... {r.Tu:>10.2f} kNm', t.crt_verde),
                (f'>  Tu_umbral ................... {r.Tu_umbral:>10.2f} kNm', t.crt_verde),
                (f'>  τ_combinado / τ_límite ...... {r.tau_combinado:.3f} / {r.tau_limite:.3f} MPa  {ok_comb}', t.crt_verde),
                None,
                (f'>  At/s (torsión) .............. {r.At_s:>10.0f} mm²/m', t.crt_verde),
                (f'>  Av/s (corte/rama) ........... {r.Av_s:>10.0f} mm²/m', t.crt_verde),
                (f'>  Avt/s total/rama ............ {r.Avt_s:>10.0f} mm²/m', t.crt_verde),
                (f'>  Al longitudinal ............. {r.Al:>10.2f} cm²', t.crt_verde),
                (f'>  Al_min ...................... {r.Al_min:>10.2f} cm²', t.crt_verde),
                None,
                ('> ESTADO: NOMINAL', t.crt_verde) if r.verifica
                else ('> ALERTA — VERIFICAR SECCIÓN', t.crt_rojo),
            ]
        self._renderizar(lineas)

    def mostrar_resultado_base(self, r) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO B-07 EJECUTADO — BASE CENTRADA', t.crt_ambar),
            None,
            (f'>  Planta ...................... {r.B:.2f} × {r.L:.2f} m', t.crt_verde),
            (f'>  h_f ......................... {r.h_f*100:>9.0f} cm  d={r.d*100:.1f} cm', t.crt_verde),
            (f'>  q_serv / q_adm .............. {r.q_servicio:.1f} / {r.q_adm:.0f} kN/m²  {"✓" if r.verifica_suelo else "✗"}', t.crt_verde),
            None,
            (f'>  Punzonamiento Vu/φVc ......... {r.Vu_punch:.1f} / {r.phi_Vc_punch:.1f} kN  {"✓" if r.verifica_punch else "✗"}', t.crt_verde),
            (f'>  Corte 1-dir (L) Vu/φVc ...... {r.Vu_1way_L:.1f} / {r.phi_Vc_1way_L:.1f} kN  {"✓" if r.verifica_1way else "✗"}', t.crt_verde),
            None,
            (f'>  As dir-L .................... {r.As_L:>9.2f} cm²  ({r.As_L_m:.2f} cm²/m)', t.crt_verde),
            (f'>  As dir-B .................... {r.As_B:>9.2f} cm²  ({r.As_B_m:.2f} cm²/m)', t.crt_verde),
            None,
            ('> ESTADO: NOMINAL', t.crt_verde) if r.verifica
            else ('> ALERTA — NO VERIFICA', t.crt_rojo),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_mensula(self, r) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO M-08 EJECUTADO — MÉNSULA CORTA', t.crt_ambar),
            None,
            (f'>  Vu .......................... {r.Vu:>10.1f} kN', t.crt_verde),
            (f'>  a / d ....................... {r.a:.3f} / {r.d:.3f} m  (a/d={r.a/r.d:.3f})', t.crt_verde),
            (f'>  θ biela ..................... {r.theta_deg:>10.1f}°', t.crt_verde),
            None,
            (f'>  F biela ..................... {r.F_biela:>10.1f} kN', t.crt_verde),
            (f'>  F tirante principal ......... {r.F_tirante_principal:>10.1f} kN', t.crt_verde),
            (f'>  As principal ................ {r.As_principal:>10.2f} cm²', t.crt_verde),
            (f'>  As total .................... {r.As_total:>10.2f} cm²', t.crt_verde),
            None,
            (f'>  σ biela / φ·fce ............. {r.sigma_biela:.2f} / {r.phi_fce:.2f} MPa  {"✓" if r.verifica_biela else "✗"}', t.crt_verde),
            None,
            ('> ESTADO: NOMINAL', t.crt_verde) if r.verifica
            else ('> ALERTA — BIELA NO VERIFICA', t.crt_rojo),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_propagacion(self, prop) -> None:
        t = self._t()
        lineas = [
            ('> PROTOCOLO E-09 EJECUTADO — PROPAGACIÓN DE CARGAS', t.crt_ambar),
            None,
            ('> VIGAS', t.crt_ambar),
        ]
        for vid, cv in prop.cargas_vigas.items():
            lineas.append(
                (f'>  {vid:<8}  wD={cv.wD:>7.2f}  wL={cv.wL:>6.2f}  '
                 f'wu={cv.wu:>7.2f} kN/m', t.crt_verde)
            )
        lineas.append(None)
        lineas.append(('> COLUMNAS', t.crt_ambar))
        for cid, cc in prop.cargas_columnas.items():
            lineas.append(
                (f'>  {cid:<8}  Pu={cc.Pu:>8.1f} kN  '
                 f'Mu={cc.Mu:>7.2f} kNm', t.crt_verde)
            )
        self._renderizar(lineas)

    # ── Interno ──────────────────────────────────────────────────────────────

    def _renderizar(self, lineas) -> None:
        partes = [self._body_open()]
        for item in lineas:
            if item is None:
                partes.append(self._sep())
            else:
                texto, color = item
                partes.append(_ln(texto, color))
        partes.append(_BODY_CLOSE)
        self.setHtml(''.join(partes))
