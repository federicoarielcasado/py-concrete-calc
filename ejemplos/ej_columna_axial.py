"""
Columna corta — carga axial pura
CIRSOC 201-2005, cap. 5 — columnas con estribos

Enunciado:
  Dimensionar la armadura longitudinal de una columna cuadrada:
    f'c = 25 MPa,  fy = 420 MPa (ADN 420)
    b = 40 cm,  h = 40 cm,  recubrimiento mecánico = 5 cm
    Pu = 1800 kN  (carga axial de diseño, sin excentricidad significativa)

La carga axial pura usa φ = 0.65 y k = 0.80 para columnas con estribos.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from hormigon.columnas import (
    dimensionar_columna,
    dimensionar_columna_variantes,
    verificar_columna,
)

# ── Datos ─────────────────────────────────────────────────────────────────────
H25    = Hormigon(fc=25)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.40, h=0.40,
    recubrimiento=0.05,
    hormigon=H25, acero=ADN420,
)

Pu = 1800.0   # kN

# ── Dimensionado ──────────────────────────────────────────────────────────────
print("=" * 60)
print("COLUMNA AXIAL — Dimensionado con estribos")
print("=" * 60)

r = dimensionar_columna(sec, Pu=Pu, tipo='estribos')
r.mostrar()

# ── Verificar con armadura adoptada ───────────────────────────────────────────
# Adoptar 8φ16 = 8 × 2.011 = 16.09 cm²
Ast_adop = 8 * 2.011   # cm²
print("\n" + "─" * 60)
print(f"Verificación con 8φ16 = {Ast_adop:.2f} cm²:")
print("─" * 60)
rv = verificar_columna(sec, Pu=Pu, Ast=Ast_adop, tipo='estribos')
rv.mostrar()

# ── Variantes ─────────────────────────────────────────────────────────────────
print("\n" + "─" * 60)
print("Variantes válidas (rankeadas por mínima Ast):")
print("─" * 60)
rset = dimensionar_columna_variantes(sec, Pu=Pu, tipo='estribos')
rset.mostrar()

plt.show()   # no se genera gráfico automático; placeholder para extensión futura
