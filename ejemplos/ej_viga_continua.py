"""
Viga continua — método de coeficientes
CIRSOC 201-2005, art. 8.3.3

Enunciado:
  Dimensionar las secciones críticas de una viga continua de 3 tramos iguales:
    f'c = 25 MPa,  fy = 420 MPa (ADN 420)
    b = 30 cm,  h = 60 cm,  recubrimiento mecánico = 5 cm
    ln = 5.50 m  (luz libre entre caras de columnas)
    wD = 18 kN/m  (incluye peso propio de viga)
    wL = 12 kN/m
    Extremo discontinuo: apoyo libre (sin restricción)

El método de coeficientes (art. 8.3.3) requiere:
  - ≥ 2 tramos, cargas uniformes, secciones prismáticas
  - wL ≤ 3/4 · wD  (12 ≤ 0.75 × 18 = 13.5 kN/m  ✓)
  - Luces adyacentes sin diferencia > 20%

Secciones de diseño (momentos):
  M+ ext = wu·ln²/14    M+ int = wu·ln²/16
  M– ext = wu·ln²/24    M– 1°int = wu·ln²/10    M– int = wu·ln²/11

Cortantes de diseño:
  Vu ext = wu·ln/2      Vu 1°int = 1.15·wu·ln/2
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from elementos.viga import VigaContinua

# ── Datos ─────────────────────────────────────────────────────────────────────
H25    = Hormigon(fc=25)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.30, h=0.60,
    recubrimiento=0.05,
    hormigon=H25, acero=ADN420,
)

# ── Cálculo ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("VIGA CONTINUA 3 TRAMOS — Método de coeficientes (art. 8.3.3)")
print("=" * 65)

viga = VigaContinua(sec, ln=5.50, wD=18.0, wL=12.0, n_tramos=3, extremo='libre')
r    = viga.calcular()
r.mostrar()

# ── Resumen de armaduras por sección ──────────────────────────────────────────
print("\n" + "─" * 65)
print("Resumen de armaduras calculadas por sección:")
print("─" * 65)
for s in r.secciones:
    rf = s.resultado_flex
    signo = "M+" if s.signo == "positivo" else "M-"
    print(f"  {s.nombre:<35}  {signo}  As = {rf.As:.2f} cm²")

# ── Gráfico ───────────────────────────────────────────────────────────────────
fig = r.graficar()
fig.suptitle("Viga continua 3 tramos — Secciones críticas φMn vs Mu", fontsize=10)

plt.show()
