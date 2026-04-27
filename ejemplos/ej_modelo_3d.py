"""
Visualización 3D del esquema de planta estructural.

Genera la figura interactiva Plotly y la guarda como HTML
(se puede abrir en cualquier navegador).

Planta: 2 vanos en x (5+5 m) × 1 vano en y (4.5 m), losas 2dir.
"""
from hormigon.materiales import Acero, Hormigon
from hormigon.modelo import (
    ColumnaEsquema, Grilla, PanelLosa, PlantaEstructural, VigaEsquema,
)
from hormigon.propagacion import propagar
from hormigon.secciones import SeccionRectangular
from graficos.modelo_3d import visualizar_planta_3d

h25  = Hormigon(fc=25)
a420 = Acero(fy=420)
sec_viga = SeccionRectangular(b=0.25, h=0.50, recubrimiento=0.06, hormigon=h25, acero=a420)
sec_col  = SeccionRectangular(b=0.30, h=0.30, recubrimiento=0.06, hormigon=h25, acero=a420)

grilla = Grilla(ejes_x=[0.0, 5.0, 10.0], ejes_y=[0.0, 4.5])
planta = PlantaEstructural(grilla=grilla, hormigon=h25, acero=a420)

for i in range(grilla.nx):
    planta.agregar_losa(PanelLosa(
        id=f'L{i}', i=i, j=0, h=0.14, tipo='2dir',
        wD=1.5, wL=2.0, tipo_a='ext_empotrado', tipo_b='ext_empotrado',
    ))

for j_eje in range(len(grilla.ejes_y)):
    planta.agregar_viga(VigaEsquema(
        id=f'Vx{j_eje}', dir='x', idx=j_eje,
        desde=0, hasta=grilla.nx,
        seccion=sec_viga, extremo='columna',
    ))

for i_eje in range(len(grilla.ejes_x)):
    planta.agregar_viga(VigaEsquema(
        id=f'Vy{i_eje}', dir='y', idx=i_eje,
        desde=0, hasta=grilla.ny,
        seccion=sec_viga, extremo='columna',
    ))

k = 0
for iy in range(len(grilla.ejes_y)):
    for ix in range(len(grilla.ejes_x)):
        planta.agregar_columna(ColumnaEsquema(
            id=f'C{k}', ix=ix, iy=iy,
            seccion=sec_col, h_entrepiso=3.0,
        ))
        k += 1

prop = propagar(planta)
fig = visualizar_planta_3d(planta, propagacion=prop, titulo='Planta 2x1 — 2dir')

fig.write_html('planta_3d.html')
print("Figura guardada en planta_3d.html")
fig.show()
