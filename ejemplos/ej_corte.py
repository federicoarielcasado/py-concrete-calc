"""
Corte — viga rectangular
CIRSOC 201-2005, Ejemplo 3.I

Enunciado:
  Diseñar el refuerzo transversal (estribos) de una viga rectangular:
    f'c = 20 MPa,  fy = 420 MPa (ADN 420)
    b = 20 cm,  h = 60 cm,  recubrimiento mecánico = 3.4 cm
    Vu = 174.6 kN  (corte mayorado en la sección crítica)

Resultados esperados (CIRSOC):
  Vc ≈ 85.7 kN,  Avs ≈ 609 mm²/m,  φVn ≥ Vu
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from hormigon.corte import calcular_corte, calcular_corte_variantes

# ── Datos ─────────────────────────────────────────────────────────────────────
H20    = Hormigon(fc=20)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.20, h=0.60,
    recubrimiento=0.034,
    hormigon=H20, acero=ADN420,
)

Vu = 174.6   # kN

# ── Dimensionado ──────────────────────────────────────────────────────────────
print("=" * 60)
print("EJEMPLO 3.I — Corte, estribos verticales")
print("=" * 60)

r = calcular_corte(sec, Vu=Vu)
r.mostrar()

# ── Variantes de estribado ────────────────────────────────────────────────────
print("\n" + "─" * 60)
print("Variantes válidas (rankeadas por mayor separación):")
print("─" * 60)
rset = calcular_corte_variantes(sec, Vu=Vu, n_ramas=2)
rset.mostrar()

# ── Gráfico ───────────────────────────────────────────────────────────────────
fig = rset.graficar()
fig.suptitle("Ej 3.I — Variantes de estribado", fontsize=10)

plt.show()
