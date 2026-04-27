"""
Ejemplo de uso del modelador de planta estructural.

Esquema:
    Planta 2 vanos en x (5.0 + 5.0 m) × 1 vano en y (4.5 m)
    6 columnas (3 × 2), 3 vigas en x (una por cada fila y), 2 vigas en y (bordes)
    2 losas 2dir en los paneles

    Eje Y
    |
    4.5 ─  C3──V1x──C4──V1x──C5
           |        |        |
          V1y      V2y      V3y   ← vigas en y
           |        |        |
    0.0 ─  C0──V0x──C1──V0x──C2
           0.0      5.0     10.0 ── Eje X
"""
from hormigon.materiales import Acero, Hormigon
from hormigon.modelo import (
    ColumnaEsquema,
    Grilla,
    PanelLosa,
    PlantaEstructural,
    VigaEsquema,
)
from hormigon.secciones import SeccionRectangular
from elementos.planta import dimensionar_columna, dimensionar_losa, dimensionar_viga
from hormigon.propagacion import propagar

# ── Materiales ────────────────────────────────────────────────────────────────
h25  = Hormigon(fc=25)
a420 = Acero(fy=420)

# ── Secciones ─────────────────────────────────────────────────────────────────
sec_viga = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.06,
                               hormigon=h25, acero=a420)
sec_col  = SeccionRectangular(b=0.30, h=0.30, recubrimiento=0.06,
                               hormigon=h25, acero=a420)

# ── Grilla ────────────────────────────────────────────────────────────────────
grilla = Grilla(ejes_x=[0.0, 5.0, 10.0], ejes_y=[0.0, 4.5])

# ── Planta ────────────────────────────────────────────────────────────────────
planta = PlantaEstructural(grilla=grilla, hormigon=h25, acero=a420)

# Losas 2dir, h=0.14m, piso terminado 1.5 kN/m², uso vivienda 2.0 kN/m²
# Planta de 2 vanos en x y 1 vano en y → todos los paneles son de borde
# con vigas en los 4 lados (ext_empotrado = borde con restriccion de viga)
for i in range(grilla.nx):
    planta.agregar_losa(PanelLosa(
        id=f'L{i}', i=i, j=0,
        h=0.14, tipo='2dir',
        wD=1.5, wL=2.0,
        tipo_a='ext_empotrado',   # vano extremo en x (viga en cada borde)
        tipo_b='ext_empotrado',   # vano extremo en y
    ))

# Vigas en x: una abajo (j=0) y una arriba (j=1)
for j_eje in range(len(grilla.ejes_y)):
    planta.agregar_viga(VigaEsquema(
        id=f'Vx{j_eje}', dir='x', idx=j_eje,
        desde=0, hasta=grilla.nx,
        seccion=sec_viga, extremo='columna',
    ))

# Vigas en y en los 3 ejes verticales
for i_eje in range(len(grilla.ejes_x)):
    planta.agregar_viga(VigaEsquema(
        id=f'Vy{i_eje}', dir='y', idx=i_eje,
        desde=0, hasta=grilla.ny,
        seccion=sec_viga, extremo='columna',
    ))

# Columnas en las 6 intersecciones
k = 0
for iy in range(len(grilla.ejes_y)):
    for ix in range(len(grilla.ejes_x)):
        planta.agregar_columna(ColumnaEsquema(
            id=f'C{k}', ix=ix, iy=iy,
            seccion=sec_col, h_entrepiso=3.0,
        ))
        k += 1

# ── Propagar y mostrar ─────────────────────────────────────────────────────────
prop = propagar(planta)
print("=" * 60)
print("PROPAGACIÓN DE CARGAS")
print("=" * 60)
prop.mostrar()

# ── Diseño de un elemento ─────────────────────────────────────────────────────
print()
print("=" * 60)
print("DISEÑO — Viga Vx0 (inferior, continua 2 tramos)")
print("=" * 60)
r_viga = dimensionar_viga('Vx0', planta, carga=prop.cargas_vigas['Vx0'])
r_viga.mostrar()

print()
print("=" * 60)
print("DISEÑO — Columna C0 (esquina inferior izquierda)")
print("=" * 60)
r_col = dimensionar_columna('C0', planta, carga=prop.cargas_columnas['C0'])
r_col.mostrar()

print()
print("=" * 60)
print("DISEÑO — Losa L0 (panel izquierdo, 2dir)")
print("=" * 60)
try:
    r_losa = dimensionar_losa('L0', planta)
    r_losa.mostrar()
except NotImplementedError as e:
    print(f"[Pendiente] {e}")
