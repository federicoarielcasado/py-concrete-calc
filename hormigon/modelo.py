"""
Modelo estructural de planta para hormigón armado.

Define la geometría del esquema y las propiedades de los elementos.
La propagación de cargas está en propagacion.py.
La API de diseño de elementos está en elementos/planta.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular


@dataclass
class Grilla:
    """
    Grilla ortogonal de ejes estructurales.

    ejes_x : coordenadas de ejes verticales (columnas) en x [m]
    ejes_y : coordenadas de ejes horizontales (columnas) en y [m]

    Ejemplo — planta 3×2 vanos:
        Grilla(ejes_x=[0.0, 5.0, 10.0, 15.0], ejes_y=[0.0, 4.5, 9.0])
    """
    ejes_x: list[float]
    ejes_y: list[float]

    def lx(self, i: int) -> float:
        """Ancho del panel i en dirección x [m]."""
        return self.ejes_x[i + 1] - self.ejes_x[i]

    def ly(self, j: int) -> float:
        """Altura del panel j en dirección y [m]."""
        return self.ejes_y[j + 1] - self.ejes_y[j]

    @property
    def nx(self) -> int:
        """Número de vanos en x."""
        return len(self.ejes_x) - 1

    @property
    def ny(self) -> int:
        """Número de vanos en y."""
        return len(self.ejes_y) - 1


@dataclass
class PanelLosa:
    """
    Panel de losa entre los ejes i, i+1 (en x) y j, j+1 (en y).

    i, j           : índices del panel en la grilla (0-based)
    h              : espesor de losa [m]
    tipo           : '1dir' | '2dir'
    dir_1dir       : 'x' | 'y' — dirección de la armadura principal (solo para tipo='1dir')
    wD             : carga muerta SUPERIMPUESTA [kN/m²] (sin peso propio de la losa)
    wL             : carga viva [kN/m²]
    n_tramos       : número de tramos continuos (para diseño por coeficientes)
    extremo        : condición del apoyo exterior discontinuo ('libre'|'viga'|'columna')
    recubrimiento  : distancia al centroide de la armadura principal [m]
    """
    id:            str
    i:             int
    j:             int
    h:             float
    tipo:          str
    dir_1dir:      str   = 'x'
    wD:            float = 0.0
    wL:            float = 0.0
    n_tramos:      int   = 2
    extremo:       str   = 'libre'
    recubrimiento: float = 0.02
    # Solo para tipo='2dir': condicion de tramo en cada direccion
    tipo_a:        str   = 'int'   # 'int' | 'ext_libre' | 'ext_empotrado'
    tipo_b:        str   = 'int'


@dataclass
class VigaEsquema:
    """
    Viga ubicada sobre un eje de la grilla.

    dir    : 'x' → la viga corre en dirección x (horizontal en planta)
             'y' → la viga corre en dirección y (vertical en planta)
    idx    : índice del eje que contiene la viga
             si dir='x': la viga está en y = ejes_y[idx]
             si dir='y': la viga está en x = ejes_x[idx]
    desde  : índice de la columna de arranque (en la dirección perpendicular)
    hasta  : índice de la columna de llegada
    extremo: condición del apoyo exterior discontinuo para art. 8.3.3
             ('libre' | 'viga' | 'columna')
    """
    id:      str
    dir:     str
    idx:     int
    desde:   int
    hasta:   int
    seccion: SeccionRectangular
    extremo: str = 'libre'

    @property
    def n_tramos(self) -> int:
        return self.hasta - self.desde


@dataclass
class ColumnaEsquema:
    """
    Columna en el nodo (ix, iy) de la grilla.

    ix, iy      : índices en ejes_x y ejes_y
    tipo        : 'estribos' | 'zunchada'
    h_entrepiso : altura libre del fuste [m]
    """
    id:          str
    ix:          int
    iy:          int
    seccion:     SeccionRectangular
    tipo:        str   = 'estribos'
    h_entrepiso: float = 3.0


@dataclass
class PlantaEstructural:
    """
    Esquema estructural completo de un piso.

    gamma_conc : peso específico del hormigón [kN/m³] (default: 25)
    """
    grilla:     Grilla
    hormigon:   Hormigon
    acero:      Acero
    losas:      dict[str, PanelLosa]      = field(default_factory=dict)
    vigas:      dict[str, VigaEsquema]    = field(default_factory=dict)
    columnas:   dict[str, ColumnaEsquema] = field(default_factory=dict)
    gamma_conc: float = 25.0

    def agregar_losa(self, losa: PanelLosa) -> PlantaEstructural:
        self.losas[losa.id] = losa
        return self

    def agregar_viga(self, viga: VigaEsquema) -> PlantaEstructural:
        self.vigas[viga.id] = viga
        return self

    def agregar_columna(self, col: ColumnaEsquema) -> PlantaEstructural:
        self.columnas[col.id] = col
        return self
