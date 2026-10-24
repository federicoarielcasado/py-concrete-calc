"""
PanelResultados — informe de resultados de cada módulo.

Texto monoespaciado con los colores del tema activo. Los bloques separados por
`None` se reparten en dos columnas para aprovechar el ancho, y la altura del
panel se ajusta al contenido. El último informe se guarda para volver a
dibujarlo al cambiar de tema y para la memoria de cálculo en PDF.
"""
from __future__ import annotations

import re
from html import escape

from PyQt6.QtWidgets import QTextEdit, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

_FUENTE = "font-family:'Cascadia Mono',Consolas,'Courier New',monospace; font-size:12px;"
_ANCHO_ETIQUETA = 26
_PUNTEADO = re.compile(r'^(\S.*?) \.+ (.*)$')
_ALTURA_MAX = 300


def _alinear(texto: str) -> str:
    """'Mu ...... 52.00 kNm' → etiqueta con puntos hasta un ancho fijo."""
    m = _PUNTEADO.match(texto)
    if not m:
        return texto
    etiqueta, valor = m.groups()
    relleno = max(2, _ANCHO_ETIQUETA - len(etiqueta) - 1)
    return f'{etiqueta} {"." * relleno} {valor.strip()}'


class PanelResultados(QTextEdit):
    """Panel de solo lectura con el informe de resultados."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('panel_resultados')
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 10))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._ultimo: tuple | None = None      # (método, args) para re-dibujar
        self.lineas: list | None = None        # último informe (texto, color) o None

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _t(self):
        from app.themes import get_tema
        return get_tema()

    # ── API general ──────────────────────────────────────────────────────────

    def refrescar(self) -> None:
        """Vuelve a dibujar el último contenido con los colores del tema activo."""
        if self._ultimo is not None:
            metodo, args = self._ultimo
            metodo(*args)

    def tiene_resultado(self) -> bool:
        return self.lineas is not None

    def limpiar(self) -> None:
        self.lineas = None
        self._ultimo = None
        self._renderizar([], guardar=False)

    def mostrar_bienvenida(self, modulo: str) -> None:
        self._ultimo = (self.mostrar_bienvenida, (modulo,))
        t = self._t()
        self.lineas = None
        self._renderizar([
            (modulo, t.res_titulo),
            ('Ingrese los datos y presione Calcular.', t.res_tenue),
        ], guardar=False)

    def mostrar_error(self, mensaje: str) -> None:
        self._ultimo = (self.mostrar_error, (mensaje,))
        t = self._t()
        self.lineas = None
        self._renderizar([
            ('✗ NO SE PUDO CALCULAR', t.res_alerta),
            (mensaje, t.res_texto),
        ], guardar=False)

    def mostrar_resultado_flexion(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_flexion, (r,))
        t = self._t()
        lineas = [
            ('F-01 · FLEXIÓN SIMPLE', t.res_titulo),
            None,
            (f'Mu ........................... {r.Mu:>10.2f} kNm', t.res_texto),
            (f'φ ............................ {r.phi:>10.2f}  ({r.tipo.upper()})', t.res_texto),
            (f'Mn = Mu/φ ................... {r.Mn:>10.2f} kNm', t.res_texto),
            (f'φ·Mn ........................ {r.phi_Mn:>10.2f} kNm', t.res_texto),
            (f'a (bloque tensiones) ......... {r.a*100:>10.2f} cm', t.res_texto),
            (f'c (eje neutro) ............... {r.c*100:>10.2f} cm', t.res_texto),
            (f'εs (acero) .................. {r.epsilon_s:>10.5f}', t.res_texto),
            (f'As calculada ................. {r.As:>10.2f} cm²', t.res_texto),
        ]
        if r.As_prima > 0:
            lineas.append(
                (f"As' comprimida ............... {r.As_prima:>10.2f} cm²", t.res_titulo)
            )
        if r.As_adoptada is not None:
            lineas.append(None)
            lineas.append(
                (f'ARMADO: {r.n_barras}φ{r.phi_adoptado} = {r.As_adoptada:.2f} cm²', t.res_titulo)
            )
        lineas.append(None)
        lineas.append(
            ('✓ VERIFICA', t.res_ok) if r.verifica
            else ('✗ NO VERIFICA — CAPACIDAD INSUFICIENTE', t.res_alerta)
        )
        self._renderizar(lineas)

    def mostrar_resultado_corte(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_corte, (r,))
        t = self._t()
        lineas = [
            ('C-02 · CORTE', t.res_titulo),
            None,
            (f'Vu ........................... {r.Vu:>10.2f} kN', t.res_texto),
            (f'Vc (hormigón) ................ {r.Vc:>10.2f} kN', t.res_texto),
            (f'Vs requerido ................. {r.Vs_requerido:>10.2f} kN', t.res_texto),
            (f'φ·Vn ........................ {r.phi_Vn:>10.2f} kN', t.res_texto),
            (f'Vn_max ...................... {r.Vn_max:>10.2f} kN', t.res_texto),
            (f'Av/s calculado ............... {r.Avs_calculado:>10.1f} mm²/m', t.res_texto),
            (f'Av/s mínimo .................. {r.Avs_minimo:>10.1f} mm²/m', t.res_texto),
            (f'Av/s adoptado ................ {r.Avs_adoptado:>10.1f} mm²/m', t.res_texto),
            (f's máximo ..................... {r.s_maximo*100:>10.1f} cm', t.res_texto),
        ]
        lineas.append(None)
        if r.verifica_resistencia and r.verifica_Vn_max:
            lineas.append(('✓ VERIFICA', t.res_ok))
        else:
            msg = ('RESISTENCIA INSUFICIENTE' if not r.verifica_resistencia
                   else 'Vn SUPERA EL MÁXIMO — AMPLIAR SECCIÓN')
            lineas.append((f'✗ NO VERIFICA — {msg}', t.res_alerta))
        self._renderizar(lineas)

    def mostrar_resultado_columna(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_columna, (r,))
        from hormigon.columnas import RHO_MIN, RHO_MAX
        t = self._t()
        lineas = [
            ('P-03 · COLUMNA — FLEXOCOMPRESIÓN', t.res_titulo),
            None,
            (f'Pu ........................... {r.Pu:>10.1f} kN', t.res_texto),
            (f'Mu ........................... {r.Mu:>10.1f} kNm', t.res_texto),
            (f'Ast calculada ................ {r.Ast:>10.2f} cm²', t.res_texto),
            (f'ρg ........................... {r.rho_g:>10.4f}', t.res_texto),
            (f'Rango ρg: [{RHO_MIN:.2f} — {RHO_MAX:.2f}]', t.res_tenue),
        ]
        if r.Ast_real is not None:
            lineas.append(None)
            lineas.append(
                (f'ADOPTADO: {r.n_barras}φ{r.phi_barra}  = {r.Ast_real:.2f} cm²', t.res_titulo)
            )
        lineas.append(None)
        lineas.append(
            ('✓ VERIFICA', t.res_ok) if r.verifica
            else ('✗ NO VERIFICA — DEMANDA FUERA DEL DIAGRAMA P-M', t.res_alerta)
        )
        self._renderizar(lineas)

    def mostrar_resultado_viga(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_viga, (r,))
        t = self._t()
        tipo_str = 'Viga simple' if r.tipo == 'simple' else 'Viga en voladizo'
        rf = r.resultado_flex
        rc = r.resultado_corte
        lineas = [
            (f'V-05 · {tipo_str.upper()}', t.res_titulo),
            None,
            (f'L  .......................... {r.L:>10.2f} m', t.res_texto),
            (f'wu .......................... {r.wu:>10.2f} kN/m', t.res_texto),
            (f'Mu .......................... {r.Mu:>10.2f} kNm', t.res_texto),
            (f'Vu .......................... {r.Vu:>10.2f} kN', t.res_texto),
            None,
            (f'As calculada ................ {rf.As:>10.2f} cm²', t.res_texto),
            (f'φ·Mn ........................ {rf.phi_Mn:>10.2f} kNm', t.res_texto),
            (f'Av/s adoptado ............... {rc.Avs_adoptado:>10.1f} mm²/m', t.res_texto),
            (f's máximo .................... {rc.s_maximo*100:>10.1f} cm', t.res_texto),
            None,
            ('✓ VERIFICA', t.res_ok) if (rf.verifica and rc.verifica_resistencia)
            else ('✗ NO VERIFICA — REVISAR SECCIÓN', t.res_alerta),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_viga_continua(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_viga_continua, (r,))
        t = self._t()
        lineas = [
            ('V-05 · VIGA CONTINUA', t.res_titulo),
            None,
            (f'ln .......................... {r.ln:>10.2f} m', t.res_texto),
            (f'wu .......................... {r.wu:>10.2f} kN/m', t.res_texto),
            (f'n_tramos .................... {r.n_tramos:>10d}', t.res_texto),
            (f'extremo ..................... {r.extremo:>10s}', t.res_texto),
            None,
        ]
        for s in r.secciones:
            rf = s.resultado_flex
            ok = '✓' if rf.verifica else '✗'
            lineas.append(
                (f'{s.nombre[:28]:<28} {rf.As:>6.2f} cm²  {ok}', t.res_texto)
            )
        lineas.append(None)
        todas_ok = all(s.resultado_flex.verifica for s in r.secciones)
        lineas.append(
            ('✓ VERIFICA', t.res_ok) if todas_ok
            else ('✗ NO VERIFICA — REVISAR SECCIONES', t.res_alerta)
        )
        self._renderizar(lineas)

    def mostrar_resultado_losa(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_losa, (r,))
        t = self._t()
        lineas = [
            ('L-04 · LOSA EN 1 DIRECCIÓN', t.res_titulo),
            None,
            (f'h ........................... {r.h*100:>9.0f} cm', t.res_texto),
            (f'h_min ....................... {r.h_min*100:>9.1f} cm  {"✓" if r.verifica_h else "✗"}', t.res_texto),
            (f'd ........................... {r.d*100:>9.1f} cm', t.res_texto),
            (f'wu .......................... {r.wu:>9.2f} kN/m²', t.res_texto),
            None,
        ]
        for s in r.secciones:
            if s.Mu < 1e-6:
                continue
            ok = '✓' if s.verifica else '✗'
            lineas.append(
                (f'{s.nombre[:28]:<28} As={s.As:>5.2f}cm²  {ok}', t.res_texto)
            )
        lineas += [
            None,
            (f'As temperatura .............. {r.As_temp:>9.2f} cm²/m', t.res_texto),
            (f'Vu_max / φVc ................ {r.Vu_max:>5.1f} / {r.phi_Vc:>5.1f} kN/m  {"✓" if r.verifica_corte else "✗"}', t.res_texto),
            None,
            ('✓ VERIFICA', t.res_ok) if r.verifica_h and r.verifica_corte
            else ('✗ NO VERIFICA', t.res_alerta),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_losa_2dir(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_losa_2dir, (r,))
        t = self._t()
        ok_h = '✓' if r.verifica_h else '✗'
        lineas = [
            ('L-04 · LOSA EN 2 DIRECCIONES (MÉTODO DIRECTO)', t.res_titulo),
            None,
            (f'la (vano corto) ............. {r.la:>9.2f} m', t.res_texto),
            (f'lb (vano largo) ............. {r.lb:>9.2f} m', t.res_texto),
            (f'm = la/lb ................... {r.m:>9.3f}', t.res_texto),
            (f'h adoptado .................. {r.h*100:>9.0f} cm', t.res_texto),
            (f'h_min (la/33) ............... {r.h_min*100:>9.1f} cm  {ok_h}', t.res_texto),
            (f'd_a (dir. corta) ............ {r.d_a*100:>9.1f} cm', t.res_texto),
            (f'd_b (dir. larga) ............ {r.d_b*100:>9.1f} cm', t.res_texto),
            (f'wu .......................... {r.wu:>9.2f} kN/m²', t.res_texto),
            None,
        ]
        for s in r.secciones:
            if s.Mu < 1e-6:
                continue
            ok = '✓' if s.verifica else '✗'
            lineas.append(
                (f'[{s.direccion}] {s.nombre[:26]:<26} As={s.As:>5.2f}cm²  {ok}', t.res_texto)
            )
        lineas += [
            None,
            (f'As temperatura .............. {r.As_temp:>9.2f} cm²/m', t.res_texto),
            None,
            ('✓ VERIFICA', t.res_ok) if r.verifica_h
            else ('✗ NO VERIFICA — REVISAR ESPESOR h', t.res_alerta),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_torsion(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_torsion, (r,))
        t = self._t()
        if r.despreciable:
            lineas = [
                ('T-06 · TORSIÓN + CORTE', t.res_titulo),
                None,
                (f'Tu .......................... {r.Tu:>10.2f} kNm', t.res_texto),
                (f'Tu_umbral ................... {r.Tu_umbral:>10.2f} kNm', t.res_texto),
                None,
                ('Tu < Tu_umbral — TORSIÓN DESPRECIABLE', t.res_texto),
                None,
                ('✓ VERIFICA', t.res_ok),
            ]
        else:
            ok_comb = '✓' if r.verifica_combinado else '✗'
            lineas = [
                ('T-06 · TORSIÓN + CORTE', t.res_titulo),
                None,
                (f'Tu .......................... {r.Tu:>10.2f} kNm', t.res_texto),
                (f'Tu_umbral ................... {r.Tu_umbral:>10.2f} kNm', t.res_texto),
                (f'τ_combinado / τ_límite ...... {r.tau_combinado:.3f} / {r.tau_limite:.3f} MPa  {ok_comb}', t.res_texto),
                None,
                (f'At/s (torsión) .............. {r.At_s:>10.0f} mm²/m', t.res_texto),
                (f'Av/s (corte/rama) ........... {r.Av_s:>10.0f} mm²/m', t.res_texto),
                (f'Avt/s total/rama ............ {r.Avt_s:>10.0f} mm²/m', t.res_texto),
                (f'Al longitudinal ............. {r.Al:>10.2f} cm²', t.res_texto),
                (f'Al_min ...................... {r.Al_min:>10.2f} cm²', t.res_texto),
                None,
                ('✓ VERIFICA', t.res_ok) if r.verifica
                else ('✗ NO VERIFICA — REVISAR SECCIÓN', t.res_alerta),
            ]
        self._renderizar(lineas)

    def mostrar_resultado_base(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_base, (r,))
        t = self._t()
        lineas = [
            ('B-07 · BASE AISLADA CENTRADA', t.res_titulo),
            None,
            (f'Planta ...................... {r.B:.2f} × {r.L:.2f} m', t.res_texto),
            (f'h_f ......................... {r.h_f*100:>9.0f} cm  d={r.d*100:.1f} cm', t.res_texto),
            (f'q_serv / q_adm .............. {r.q_servicio:.1f} / {r.q_adm:.0f} kN/m²  {"✓" if r.verifica_suelo else "✗"}', t.res_texto),
            None,
            (f'Punzonamiento Vu/φVc ......... {r.Vu_punch:.1f} / {r.phi_Vc_punch:.1f} kN  {"✓" if r.verifica_punch else "✗"}', t.res_texto),
            (f'Corte 1-dir (L) Vu/φVc ...... {r.Vu_1way_L:.1f} / {r.phi_Vc_1way_L:.1f} kN  {"✓" if r.verifica_1way else "✗"}', t.res_texto),
            None,
            (f'As dir-L .................... {r.As_L:>9.2f} cm²  ({r.As_L_m:.2f} cm²/m)', t.res_texto),
            (f'As dir-B .................... {r.As_B:>9.2f} cm²  ({r.As_B_m:.2f} cm²/m)', t.res_texto),
            None,
            ('✓ VERIFICA', t.res_ok) if r.verifica
            else ('✗ NO VERIFICA', t.res_alerta),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_mensula(self, r) -> None:
        self._ultimo = (self.mostrar_resultado_mensula, (r,))
        t = self._t()
        lineas = [
            ('M-08 · MÉNSULA CORTA (BIELA-TIRANTE)', t.res_titulo),
            None,
            (f'Vu .......................... {r.Vu:>10.1f} kN', t.res_texto),
            (f'a / d ....................... {r.a:.3f} / {r.d:.3f} m  (a/d={r.a/r.d:.3f})', t.res_texto),
            (f'θ biela ..................... {r.theta_deg:>10.1f}°', t.res_texto),
            (f'F biela ..................... {r.F_biela:>10.1f} kN', t.res_texto),
            (f'F tirante principal ......... {r.F_tirante_principal:>10.1f} kN', t.res_texto),
            (f'As principal ................ {r.As_principal:>10.2f} cm²', t.res_texto),
            *([(f'As total (+ Nu) ............ {r.As_total:>10.2f} cm²', t.res_texto)]
              if r.Nu > 0 else []),
            (f'As mín (art. 11.9.5) ........ {r.As_min:>10.2f} cm²', t.res_texto),
            (f'As a disponer ............... {r.As_adoptar:>10.2f} cm²', t.res_titulo),
            (f'Ah estribos horiz. (11.9.4) . {r.Ah:>10.2f} cm²', t.res_texto),
            None,
            (f'σ biela / φ·fce ............. {r.sigma_biela:.2f} / {r.phi_fce:.2f} MPa  {"✓" if r.verifica_biela else "✗"}', t.res_texto),
            None,
            ('✓ VERIFICA', t.res_ok) if r.verifica
            else ('✗ NO VERIFICA — BIELA NO VERIFICA', t.res_alerta),
        ]
        self._renderizar(lineas)

    def mostrar_resultado_propagacion(self, prop) -> None:
        self._ultimo = (self.mostrar_resultado_propagacion, (prop,))
        t = self._t()
        lineas = [
            ('E-09 · PROPAGACIÓN DE CARGAS', t.res_titulo),
            None,
            (f'VIGAS ({len(prop.cargas_vigas)})            wu [kN/m]', t.res_titulo),
        ]
        for vid, cv in prop.cargas_vigas.items():
            lineas.append((f'{vid:<12} {cv.wu:>10.2f}', t.res_texto))
        lineas.append(None)
        lineas.append((f'COLUMNAS ({len(prop.cargas_columnas)})   Pu [kN]  Mu [kNm]', t.res_titulo))
        for cid, cc in prop.cargas_columnas.items():
            lineas.append((f'{cid:<9} {cc.Pu:>9.1f} {cc.Mu:>8.2f}', t.res_texto))
        self._renderizar(lineas)

    # ── Interno ──────────────────────────────────────────────────────────────

    def _renderizar(self, lineas, guardar: bool = True) -> None:
        """
        lineas: [título, None, bloque..., None, bloque..., None, estado]
        Cada elemento es (texto, color) o None (separador de bloques).
        """
        t = self._t()
        if guardar:
            self.lineas = lineas

        items = [x for x in lineas]
        titulo = items.pop(0) if items and items[0] is not None else None
        estado = None
        if items and items[-1] is not None and items[-1][0][:1] in '✓✗':
            estado = items.pop()

        bloques, actual = [], []
        for it in items:
            if it is None:
                if actual:
                    bloques.append(actual)
                actual = []
            else:
                actual.append(it)
        if actual:
            bloques.append(actual)

        def html_linea(it, negrita=False):
            texto, color = it
            peso = 'font-weight:600;' if negrita else ''
            return (f'<div style="color:{color}; {peso} white-space:pre-wrap;">'
                    f'{escape(_alinear(texto))}</div>')

        def html_columna(bls):
            partes = []
            for i, b in enumerate(bls):
                if i:
                    partes.append('<div style="font-size:6px;">&nbsp;</div>')
                partes += [html_linea(x) for x in b]
            return ''.join(partes)

        # Reparto en dos columnas, respetando el orden de los bloques
        total = sum(len(b) for b in bloques)
        col1, col2, acum = [], [], 0
        for b in bloques:
            if acum < total / 2 or not col1:
                col1.append(b)
                acum += len(b)
            else:
                col2.append(b)
        if len(bloques) == 1 or total <= 6:
            col1, col2 = bloques, []

        html = [f'<body style="background-color:{t.res_fondo}; {_FUENTE}">']
        if titulo:
            html.append(html_linea(titulo, negrita=True))
            html.append(f'<hr style="background-color:{t.res_tenue};">')
        html.append('<table width="100%" cellspacing="0" cellpadding="0"><tr>')
        html.append(f'<td valign="top">{html_columna(col1)}</td>')
        if col2:
            html.append('<td width="28"></td>')
            html.append(f'<td valign="top">{html_columna(col2)}</td>')
        html.append('</tr></table>')
        if estado:
            html.append('<div style="font-size:6px;">&nbsp;</div>')
            html.append(html_linea(estado, negrita=True))
        html.append('</body>')
        self.setHtml(''.join(html))
        self._ajustar_altura()

    def _ajustar_altura(self) -> None:
        doc = self.document()
        doc.setTextWidth(max(self.viewport().width(), 300))
        alto = int(doc.size().height()) + 2 * self.frameWidth() + 8
        self.setFixedHeight(min(max(alto, 70), _ALTURA_MAX))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._ajustar_altura()
