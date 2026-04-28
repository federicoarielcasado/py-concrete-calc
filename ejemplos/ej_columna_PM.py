"""
Columna corta — flexocompresión (P + M)
CIRSOC 201-2005, cap. 5 — diagrama de interacción

Enunciado:
  Diseñar la armadura de una columna rectangular sometida a carga excéntrica:
    f'c = 30 MPa,  fy = 420 MPa (ADN 420)
    b = 35 cm,  h = 55 cm,  recubrimiento mecánico = 6 cm
    Pu = 1200 kN,  Mu = 180 kNm

Se utiliza el diagrama de interacción φP-φM para encontrar la mínima Ast
que encierre el punto de demanda (Pu, Mu).
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from hormigon.columnas import diagrama_interaccion
from elementos.columna import Columna

# ── Datos ─────────────────────────────────────────────────────────────────────
H30    = Hormigon(fc=30)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.35, h=0.55,
    recubrimiento=0.06,
    hormigon=H30, acero=ADN420,
)

Pu = 1200.0   # kN
Mu =  180.0   # kNm

# ── Diseño ────────────────────────────────────────────────────────────────────
print("=" * 60)
print("COLUMNA P+M — Diseño por diagrama de interacción")
print("=" * 60)

col = Columna(sec, Pu=Pu, Mu=Mu, tipo='estribos')
r   = col.calcular()
r.mostrar()

# ── Adoptar barras comerciales ─────────────────────────────────────────────────
# Buscar combinación que supere r.Ast con distribución práctica (múltiplo de 4 ≥ 4)
print("\n" + "─" * 60)
print("Barras adoptadas:")
r.adoptar(phi=20, n_barras=8)   # 8φ20 = 8 × 3.14 = 25.13 cm²
r.mostrar()

# ── Diagrama de interacción con demanda ───────────────────────────────────────
print("\n" + "─" * 60)
print("Diagrama de interacción con armadura calculada:")
print("─" * 60)
diag = r.diagrama
print(f"  φPn_max  = {diag.phi_Pn_max:.1f} kN")
print(f"  φPn_bal  = {diag.phi_Pn_bal:.1f} kN")
print(f"  φMn_bal  = {diag.phi_Mn_bal:.1f} kNm")
print(f"  φPn_0    = {diag.phi_Pn_0:.1f} kN   (tracción pura)")

fig = r.graficar()
fig.suptitle("Columna P+M — Diagrama de interacción φP-φM", fontsize=10)

plt.show()
