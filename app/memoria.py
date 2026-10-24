"""
Memoria de cálculo en PDF del módulo activo.

Arma un documento con:
  1. Encabezado (módulo, fecha, reglamento)
  2. Datos de entrada — leídos de los formularios visibles de la ventana
  3. Resultados — el informe del panel de resultados
  4. Referencias normativas del módulo
  5. Figura del módulo (siempre en colores claros)

Se imprime con QTextDocument → QPdfWriter, sin dependencias adicionales.
"""
from __future__ import annotations

import re
from datetime import date
from html import escape

from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QMarginsF, QSizeF, QUrl
from PyQt6.QtGui import QImage, QPageLayout, QPageSize, QPdfWriter, QTextDocument
from PyQt6.QtWidgets import (
    QAbstractSpinBox, QCheckBox, QComboBox, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QWidget,
)

_NOMBRES = {
    'F-01': 'Flexión simple',
    'C-02': 'Corte — diseño de estribos',
    'P-03': 'Columna — flexocompresión',
    'L-04': 'Losas',
    'V-05': 'Vigas',
    'T-06': 'Torsión y corte combinados',
    'B-07': 'Base aislada centrada',
    'M-08': 'Ménsula corta — biela-tirante',
    'E-09': 'Planta estructural — propagación de cargas',
}

_REFERENCIAS = {
    'F-01': ['art. 9.3.2 — Factores de reducción de resistencia φ',
             'art. 10.2 — Hipótesis de diseño (bloque rectangular de tensiones)',
             'art. 10.3 — Secciones controladas por tracción / compresión',
             'art. 10.5 — Armadura mínima en elementos flexionados'],
    'C-02': ['art. 9.3.2 — Factor φ para corte',
             'art. 11.3 — Resistencia al corte del hormigón Vc',
             'art. 11.5 — Armadura de corte: Vs, separación máxima y armadura mínima'],
    'P-03': ['art. 9.3.2 — Factor φ según deformación del acero',
             'art. 10.2 y 10.3 — Hipótesis y diagrama de interacción P-M',
             'art. 10.3.6 — Resistencia máxima a compresión axial',
             'art. 10.9 — Límites de la armadura longitudinal (ρg)'],
    'L-04': ['art. 8.3.3 — Método de los coeficientes',
             'art. 9.5 — Espesor mínimo de losas',
             'art. 7.12 — Armadura de contracción y temperatura',
             'art. 13.6 — Método directo para losas en dos direcciones'],
    'V-05': ['art. 8.3.3 — Momentos y cortes por coeficientes (vigas continuas)',
             'art. 10.5 — Armadura mínima de flexión',
             'art. 11.5 — Armadura de corte'],
    'T-06': ['art. 11.6 — Torsión: umbral, armadura transversal At/s y longitudinal Al'],
    'B-07': ['cap. 15 — Zapatas',
             'art. 11.12 — Punzonamiento (corte en dos direcciones)'],
    'M-08': ['art. 11.9 — Ménsulas cortas (cuantía mínima 11.9.5, estribos horizontales 11.9.4)',
             'Modelo de bielas y tirantes para regiones de discontinuidad'],
    'E-09': ['art. 9.2.1 — Combinaciones de cargas (U = 1.2 D + 1.6 L)',
             'Distribución de cargas de losas a vigas por áreas tributarias'],
}

_PUNTEADO = re.compile(r'^(\S.*?) \.+ (.*)$')


def sin_resultados(ventana: QWidget) -> bool:
    panel = getattr(ventana, 'panel_res', None)
    return panel is None or not panel.tiene_resultado()


# ── Datos de entrada ──────────────────────────────────────────────────────────

def _valor(widget: QWidget) -> str | None:
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QAbstractSpinBox):
        return widget.text()
    if isinstance(widget, QCheckBox):
        return f'{widget.text()}: {"sí" if widget.isChecked() else "no"}'
    partes = [_valor(w) for w in widget.findChildren(QWidget)
              if isinstance(w, (QLineEdit, QComboBox, QAbstractSpinBox, QCheckBox))
              and w.isVisibleTo(widget)]
    partes = [p for p in partes if p]
    return '  '.join(partes) if partes else None


def _datos_entrada(ventana: QWidget) -> list[tuple[str, list[tuple[str, str]]]]:
    """[(título del grupo, [(etiqueta, valor), ...]), ...] en orden de pantalla."""
    grupos = []
    for form in ventana.findChildren(QFormLayout):
        cont = form.parentWidget()
        if cont is None or not cont.isVisibleTo(ventana):
            continue
        grupo = cont
        while grupo is not None and grupo is not ventana and not isinstance(grupo, QGroupBox):
            grupo = grupo.parentWidget()
        titulo = grupo.title() if isinstance(grupo, QGroupBox) else 'Datos'
        if 'ENVIAR' in titulo.upper():
            continue
        filas = []
        for i in range(form.rowCount()):
            item_span = form.itemAt(i, QFormLayout.ItemRole.SpanningRole)
            if item_span is not None and isinstance(item_span.widget(), QLabel):
                filas.append((item_span.widget().text().strip('— ').capitalize(), None))
                continue
            item_lbl = form.itemAt(i, QFormLayout.ItemRole.LabelRole)
            item_cmp = form.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if item_cmp is None or item_cmp.widget() is None:
                continue
            campo = item_cmp.widget()
            if not campo.isVisibleTo(ventana) or isinstance(campo, QLabel):
                continue
            etiqueta = ''
            if item_lbl is not None and isinstance(item_lbl.widget(), QLabel):
                etiqueta = item_lbl.widget().text().rstrip(':').strip()
            valor = _valor(campo)
            if valor:
                filas.append((etiqueta, valor))
        if filas:
            y = cont.mapTo(ventana, cont.rect().topLeft()).y()
            grupos.append((y, titulo, filas))
    grupos.sort(key=lambda g: g[0])
    # Formularios del mismo grupo (p. ej. tipo de sección + dimensiones) van juntos
    unidos: list[tuple[str, list]] = []
    for _, titulo, filas in grupos:
        if unidos and unidos[-1][0] == titulo:
            unidos[-1][1].extend(filas)
        else:
            unidos.append((titulo, list(filas)))
    return unidos


# ── Figura ────────────────────────────────────────────────────────────────────

def _figura_png(ventana: QWidget) -> bytes | None:
    canvas = getattr(ventana, 'canvas', None)
    if canvas is not None and hasattr(canvas, 'figura_png'):
        return canvas.figura_png()
    vista = getattr(ventana, '_view', None)          # E-09: lienzo de planta
    if vista is not None:
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        vista.viewport().grab().save(buf, 'PNG')
        return bytes(ba)
    return None


# ── HTML ──────────────────────────────────────────────────────────────────────

_CSS = """
body  { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1F2933; }
h1    { font-size: 17pt; color: #1F5FAD; margin: 0; }
h2    { font-size: 12pt; color: #1F5FAD; margin-top: 14px; margin-bottom: 4px;
        border-bottom: 1px solid #D3D9E0; }
.sub  { color: #5B6775; font-size: 9pt; }
table.datos td { padding: 2px 8px; border-bottom: 1px solid #E6EAEF; }
td.et { color: #5B6775; }
td.val { font-family: Consolas, 'Courier New', monospace; }
.ok   { color: #1E8A4C; font-weight: bold; }
.mal  { color: #C62828; font-weight: bold; }
.nota { color: #8A96A3; font-size: 8pt; }
"""


def _tabla(filas: list[tuple[str, str | None]]) -> str:
    """Filas (etiqueta, valor); valor None = subtítulo; etiqueta '' = línea preformateada."""
    def fila(e, v):
        if v is None:
            return f'<tr><td colspan="2"><i>{escape(e)}</i></td></tr>'
        if not e:
            return f'<tr><td colspan="2" class="val" style="white-space:pre;">{escape(v)}</td></tr>'
        return f'<tr><td class="et" width="45%">{escape(e)}</td><td class="val">{escape(v)}</td></tr>'
    cuerpo = ''.join(fila(e, v) for e, v in filas)
    return f'<table class="datos" cellspacing="0" width="100%">{cuerpo}</table>'


def _resultados_html(lineas) -> str:
    partes, filas = [], []

    def volcar():
        if filas:
            partes.append(_tabla(filas))
            filas.clear()

    for item in lineas[1:]:                 # el título ya va en el encabezado
        if item is None:
            volcar()
            continue
        texto = item[0]
        if texto[:1] in '✓✗':
            volcar()
            clase = 'ok' if texto.startswith('✓') else 'mal'
            partes.append(f'<p class="{clase}">{escape(texto)}</p>')
            continue
        m = _PUNTEADO.match(texto)
        if m:
            filas.append((m.group(1).strip(), m.group(2).strip()))
        else:
            filas.append(('', texto))
    volcar()
    return ''.join(partes)


def _html(codigo: str, ventana: QWidget, con_figura: bool) -> str:
    panel = ventana.panel_res
    nombre = _NOMBRES.get(codigo, codigo)
    titulo_res = panel.lineas[0][0] if panel.lineas else nombre

    h = [f'<html><head><style>{_CSS}</style></head><body>']
    h.append(f'<h1>Memoria de cálculo — {escape(codigo)} {escape(nombre)}</h1>')
    h.append(f'<p class="sub">{escape(titulo_res)}  ·  Reglamento CIRSOC 201-2005  ·  '
             f'{date.today().strftime("%d/%m/%Y")}  ·  Generado con py-concrete-calc</p>')

    h.append('<h2>1. Datos de entrada</h2>')
    for titulo, filas in _datos_entrada(ventana):
        h.append(f'<p class="sub"><b>{escape(titulo.capitalize())}</b></p>')
        h.append(_tabla(filas))

    h.append('<h2>2. Resultados</h2>')
    h.append(_resultados_html(panel.lineas))

    refs = _REFERENCIAS.get(codigo, [])
    if refs:
        h.append('<h2>3. Referencias normativas (CIRSOC 201-2005)</h2><ul>')
        h += [f'<li>{escape(r)}</li>' for r in refs]
        h.append('</ul>')

    if con_figura:
        h.append('<h2 style="page-break-before: always;">4. Figura</h2>')
        h.append('<p align="center"><img src="figura.png" width="640"></p>')

    h.append('<p class="nota">Documento generado automáticamente. Los resultados deben ser '
             'revisados por un profesional responsable antes de su uso en un proyecto.</p>')
    h.append('</body></html>')
    return ''.join(h)


# ── API ───────────────────────────────────────────────────────────────────────

def generar_memoria(ventana: QWidget, codigo: str, ruta: str) -> None:
    png = _figura_png(ventana)

    doc = QTextDocument()
    doc.setDocumentMargin(0)
    if png:
        img = QImage.fromData(png)
        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl('figura.png'), img)
    doc.setHtml(_html(codigo, ventana, con_figura=bool(png)))

    writer = QPdfWriter(ruta)
    writer.setResolution(96)
    writer.setPageLayout(QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait,
        QMarginsF(18, 18, 18, 18), QPageLayout.Unit.Millimeter))
    writer.setTitle(f'Memoria de cálculo {codigo}')
    writer.setCreator('py-concrete-calc')
    doc.setPageSize(QSizeF(writer.width(), writer.height()))
    doc.print(writer)
