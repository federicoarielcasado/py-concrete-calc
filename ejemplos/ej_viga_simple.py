"""
Viga simplemente apoyada — dimensionado completo
CIRSOC 201-2005, cap. 2 (flexión) + cap. 3 (corte)

Enunciado:
  Dimensionar una viga rectangular isostática:
    f'c = 25 MPa,  fy = 420 MPa (ADN 420)
    b = 30 cm,  h = 65 cm,  recubrimiento mecánico = 6 cm
    Luz L = 7.0 m
    Carga muerta distribuida wD = 15 kN/m  (incluye peso propio)
    Carga viva distribuida    wL = 12 kN/m

Combina el dimensionado de flexión y corte en un único objeto resultado.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from elementos.viga import VigaSimple

# ── Datos ─────────────────────────────────────────────────────────────────────
H25    = Hormigon(fc=25)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.30, h=0.65,
    recubrimiento=0.06,
    hormigon=H25, acero=ADN420,
)

# ── Cálculo ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("VIGA SIMPLE — Flexión + Corte")
print("=" * 60)

viga = VigaSimple(sec, L=7.0, wD=15.0, wL=12.0)
r    = viga.calcular()
r.mostrar()

# ── Adoptar armaduras ─────────────────────────────────────────────────────────
print("\n" + "─" * 60)
print("Adopción de armaduras:")

r.resultado_flex.adoptar(phi=20, n=4)
print(f"  Tracción : {r.resultado_flex.n_barras}φ{r.resultado_flex.phi_adoptado}"
      f" = {r.resultado_flex.As_adoptada:.2f} cm²  "
      f"(requerida {r.resultado_flex.As:.2f} cm²)")

print(f"  Estribos : Avs = {r.resultado_corte.Avs_adoptado:.0f} mm²/m  "
      f"(s_max = {r.resultado_corte.s_maximo*100:.0f} cm)")

# ── Gráficos ──────────────────────────────────────────────────────────────────
fig = r.graficar()
fig.suptitle("Viga simple — Esquema, M(x) y V(x)", fontsize=10)

plt.show()
