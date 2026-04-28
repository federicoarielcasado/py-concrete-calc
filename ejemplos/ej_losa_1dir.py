"""
Losa en 1 dirección — método de coeficientes
CIRSOC 201-2005, art. 8.3.3

Enunciado:
  Diseñar una losa continua en 1 dirección con 3 tramos iguales:
    f'c = 21 MPa,  fy = 420 MPa (ADN 420)
    Espesor adoptado h = 15 cm,  recubrimiento = 2.5 cm
    wD = 3.5 kN/m²  (incluye peso propio de la losa)
    wL = 2.0 kN/m²
    ln = 4.0 m  (luz libre entre caras de vigas de apoyo)
    Extremo discontinuo: sin restricción (apoyo libre)

El método de coeficientes (art. 8.3.3) aplica cuando:
  - ≥ 2 tramos de igual luz (o diferencia ≤ 20%)
  - Carga viva ≤ 3/4 de la carga muerta  (2.0 ≤ 0.75 × 3.5 = 2.625  ✓)
  - Carga uniforme
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.losas import h_minimo
from elementos.losa_1dir import Losa1Dir

# ── Datos ─────────────────────────────────────────────────────────────────────
H21    = Hormigon(fc=21)
ADN420 = Acero(fy=420)

h  = 0.22    # m — espesor adoptado (h_min = ln/20 = 0.20 m)
ln = 4.0     # m — luz libre

# ── Control de espesor mínimo ─────────────────────────────────────────────────
h_min = h_minimo(ln, extremo='libre', n_tramos=3)
print(f"Espesor mínimo reglamentario:  h_min = {h_min*100:.1f} cm")
print(f"Espesor adoptado:              h     = {h*100:.0f} cm  "
      f"{'✓' if h >= h_min else '✗ INSUFICIENTE'}\n")

# ── Cálculo ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("LOSA 1 DIRECCIÓN — Método de coeficientes (3 tramos, ext. libre)")
print("=" * 65)

losa = Losa1Dir(
    h=h, recubrimiento=0.025,
    hormigon=H21, acero=ADN420,
    wD=3.5, wL=2.0,
    ln=ln, n_tramos=3,
    extremo='libre',
)
r = losa.calcular()
r.mostrar()

plt.show()
