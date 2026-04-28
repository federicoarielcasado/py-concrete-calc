"""
Flexión simple — sección rectangular con armadura doble
CIRSOC 201-2005, Ejemplo 2.I.3

Enunciado:
  Dimensionar la armadura de una viga rectangular con:
    f'c = 25 MPa,  fy = 420 MPa (ADN 420)
    b = 12 cm,  h = 40 cm,  recubrimiento mecánico = 3.4 cm
    Mu = 100 kNm

  El momento es suficientemente grande como para requerir armadura comprimida (As').

Resultados esperados (CIRSOC):
  As ≈ 8.47 cm²,  As' ≈ 1.39 cm²,  φ = 0.90 (controlada por tracción)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion

# ── Datos ─────────────────────────────────────────────────────────────────────
H25    = Hormigon(fc=25)
ADN420 = Acero(fy=420)

sec = SeccionRectangular(
    b=0.12, h=0.40,
    recubrimiento=0.034,
    hormigon=H25, acero=ADN420,
)

Mu = 100.0   # kNm

# ── Dimensionado ──────────────────────────────────────────────────────────────
print("=" * 60)
print("EJEMPLO 2.I.3 — Flexión simple, armadura doble")
print("=" * 60)

r = dimensionar_flexion(sec, Mu=Mu)
r.mostrar()

# ── Adoptar armadura comercial ─────────────────────────────────────────────────
# Tracción: 3φ20 = 3 × 3.14 = 9.42 cm²  (cubre As = 8.47 cm²)  ✓
# Compresión: 2φ10 = 2 × 0.785 = 1.57 cm²  (cubre As' = 1.39 cm²)  ✓
r.adoptar(phi=20, n=3, phi_prima=10, n_prima=2)
print(f"\nArmadura tracción  adoptada: {r.n_barras}φ{r.phi_adoptado}  = {r.As_adoptada:.2f} cm²")
print(f"Armadura compresión adoptada: {r.n_barras_prima}φ{r.phi_adoptado_prima} = {r.As_adoptada_prima:.2f} cm²")

# ── Gráfico de la sección ──────────────────────────────────────────────────────
fig = r.graficar(seccion=sec)
fig.suptitle("Ej 2.I.3 — Sección con armadura doble adoptada", fontsize=10)

plt.show()
