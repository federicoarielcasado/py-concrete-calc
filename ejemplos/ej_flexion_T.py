"""
Flexión simple — sección en T
CIRSOC 201-2005, cap. 2 — secciones con ala en compresión

Enunciado:
  Dimensionar la armadura de una viga T con:
    f'c = 25 MPa,  fy = 420 MPa (ADN 420)
    bw = 0.25 m,  h = 0.60 m,  h_ala = 0.10 m,  b_ala (efectivo) = 0.60 m
    recubrimiento mecánico = 0.065 m
    Caso A — Mu = 300 kNm  (eje neutro en el ala)
    Caso B — Mu = 620 kNm  (eje neutro en el alma)

La biblioteca detecta automáticamente la posición del eje neutro.
El cruce ala→alma ocurre en Mu ≈ 558 kNm (Mn_ala = 0.85·f'c·b_ala·h_ala·(d−h_ala/2)).
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionT
from hormigon.flexion import dimensionar_flexion

# ── Datos ─────────────────────────────────────────────────────────────────────
H25    = Hormigon(fc=25)
ADN420 = Acero(fy=420)

sec = SeccionT(
    bw=0.25, h=0.60,
    b_ala=0.60, h_ala=0.10,
    recubrimiento=0.065,
    hormigon=H25, acero=ADN420,
)
print(sec)

# ── Caso A — eje neutro en el ala ─────────────────────────────────────────────
Mu_A = 300.0   # kNm

print("\n" + "=" * 60)
print(f"CASO A — Mu = {Mu_A} kNm  (eje neutro en el ala)")
print("=" * 60)

rA = dimensionar_flexion(sec, Mu=Mu_A)
rA.mostrar()

print(f"\n→ a = {rA.a*100:.2f} cm  vs  h_ala = {sec.h_ala*100:.0f} cm  "
      f"→ NA {'en el ala ✓' if rA.a <= sec.h_ala else 'en el ALMA'}")

# ── Caso B — eje neutro en el alma ────────────────────────────────────────────
Mu_B = 620.0   # kNm

print("\n" + "=" * 60)
print(f"CASO B — Mu = {Mu_B} kNm  (eje neutro en el alma)")
print("=" * 60)

rB = dimensionar_flexion(sec, Mu=Mu_B)
rB.mostrar()

print(f"\n→ a = {rB.a*100:.2f} cm  vs  h_ala = {sec.h_ala*100:.0f} cm  "
      f"→ NA {'en el ala' if rB.a <= sec.h_ala else 'en el ALMA ✓'}")

# ── Gráficos ──────────────────────────────────────────────────────────────────
fig1 = rA.graficar(seccion=sec)
fig1.suptitle(f"T — Caso A: Mu={Mu_A} kNm  (NA en ala)", fontsize=10)

fig2 = rB.graficar(seccion=sec)
fig2.suptitle(f"T — Caso B: Mu={Mu_B} kNm  (NA en alma)", fontsize=10)

plt.show()
