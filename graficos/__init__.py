"""
Capa de visualización — matplotlib y plotly.

Importaciones rápidas:
  from graficos import graficar_seccion, graficar_interaccion_PM
  from graficos import visualizar_elemento_3d, visualizar_viga_3d
"""
from graficos.seccion_2d import graficar_seccion
from graficos.diagramas import (
    graficar_interaccion_PM,
    graficar_variantes_flexion,
    graficar_variantes_corte,
    graficar_viga,
    graficar_viga_continua,
    graficar_losa_1dir,
    graficar_losa_2dir,
    graficar_torsion,
    graficar_base,
    graficar_mensula,
)
from graficos.elemento_3d import visualizar_elemento_3d, visualizar_viga_3d

__all__ = [
    "graficar_seccion",
    "graficar_interaccion_PM",
    "graficar_variantes_flexion",
    "graficar_variantes_corte",
    "graficar_viga",
    "graficar_viga_continua",
    "graficar_losa_1dir",
    "graficar_losa_2dir",
    "graficar_torsion",
    "graficar_base",
    "graficar_mensula",
    "visualizar_elemento_3d",
    "visualizar_viga_3d",
]
