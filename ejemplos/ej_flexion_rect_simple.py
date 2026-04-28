"""
Flexión simple — sección rectangular con armadura simple
CIRSOC 201-2005, Ejemplo 2.I.1 (pág. 17)

Enunciado:
  Dimensionar la armadura de una viga rectangular con:
    f'c = 25 MPa,  fy = 420 MPa (ADN 420)
    b = 12 cm,  h = 40 cm,  recubrimiento mecánico = 3.4 cm
    Mu = 52 kNm

Resultados esperados (CIRSOC):
  As ≈ 4.15 cm²,  φ = 0.90 (controlada por tracción)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion, dimensionar_flexion_variantes

# ── Datos ─────────────────────────────────────────────────────────────────────
H25    = Hormigon(fc=25)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.12, h=0.40,
    recubrimiento=0.034,   # rec. mecánico = cc + ø_estribo + ø_long/2
    hormigon=H25, acero=ADN420,
)

Mu = 52.0   # kNm

# ── Dimensionado ──────────────────────────────────────────────────────────────
print("=" * 60)
print("EJEMPLO 2.I.1 — Flexión simple, armadura simple")
print("=" * 60)

r = dimensionar_flexion(sec, Mu=Mu)
r.mostrar()

# ── Adoptar armadura comercial ─────────────────────────────────────────────────
# Elegir 2φ16 = 2 × 2.011 = 4.02 cm²  (algo menos que 4.15 cm², no verifica)
# Mejor: 3φ14 = 3 × 1.539 = 4.62 cm²  ✓
r.adoptar(phi=14, n=3)
print(f"\nArmadura adoptada: {r.n_barras}φ{r.phi_adoptado} = {r.As_adoptada:.2f} cm²")

# ── Variantes ─────────────────────────────────────────────────────────────────
print("\n" + "─" * 60)
print("Variantes válidas (rankeadas por mínima As):")
print("─" * 60)
rset = dimensionar_flexion_variantes(sec, Mu=Mu)
rset.mostrar()

# ── Gráficos ──────────────────────────────────────────────────────────────────
fig1 = r.graficar(seccion=sec)
fig1.suptitle("Ej 2.I.1 — Sección con armadura adoptada", fontsize=10)

fig2 = rset.graficar()

plt.show()
