"""
Secciones transversales de hormigón armado.

Convención de recubrimiento:
  `recubrimiento` = distancia desde la fibra extrema hasta el centroide
  de la primera fila de armadura traccionada [m].
  Equivale al recubrimiento mecánico total (nominal + estribo + φ_long/2).
  Para la armadura comprimida se usa `recubrimiento_prima` con el mismo criterio.
"""
from __future__ import annotations

import math
from hormigon.materiales import Hormigon, Acero


# ---------------------------------------------------------------------------
# Funciones para el ancho efectivo de alas (art. 8.10)
# ---------------------------------------------------------------------------

def ancho_eficaz_T(bw: float, h_ala: float, ln: float, dist_entre_vigas: float) -> float:
    """
    Ancho efectivo del ala para viga T con losa en ambos lados (art. 8.10.2).

    bw:               ancho del alma [m]
    h_ala:            espesor del ala (losa) [m]
    ln:               luz libre de la viga [m]
    dist_entre_vigas: distancia entre ejes de vigas adyacentes [m]
    """
    vuelo = min(ln / 8.0, 8.0 * h_ala, (dist_entre_vigas - bw) / 2.0)
    return bw + 2.0 * vuelo


def ancho_eficaz_L(bw: float, h_ala: float, ln: float, dist_libre_siguiente: float) -> float:
    """
    Ancho efectivo del ala para viga L con losa en un solo lado (art. 8.10.3).

    dist_libre_siguiente: distancia libre hasta el alma de la viga adyacente [m]
    """
    vuelo = min(ln / 12.0, 6.0 * h_ala, dist_libre_siguiente / 2.0)
    return bw + vuelo


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------

class SeccionRectangular:
    """Sección transversal rectangular."""

    def __init__(
        self,
        b: float,
        h: float,
        recubrimiento: float,
        hormigon: Hormigon,
        acero: Acero,
        recubrimiento_prima: float | None = None,
    ):
        """
        b:                 ancho [m]
        h:                 altura total [m]
        recubrimiento:     distancia fibra extrema traccionada → centroide As [m]
        recubrimiento_prima: distancia fibra extrema comprimida → centroide As' [m]
                           Si es None se usa el mismo valor que recubrimiento.
        """
        if b <= 0 or h <= 0:
            raise ValueError("b y h deben ser positivos")
        if recubrimiento <= 0 or recubrimiento >= h:
            raise ValueError("recubrimiento debe estar entre 0 y h")
        self.b = b
        self.h = h
        self.recubrimiento = recubrimiento
        self.recubrimiento_prima = recubrimiento_prima if recubrimiento_prima is not None else recubrimiento
        self.hormigon = hormigon
        self.acero = acero

    @property
    def d(self) -> float:
        """Altura útil hacia la armadura traccionada [m]."""
        return self.h - self.recubrimiento

    @property
    def d_prima(self) -> float:
        """Distancia de la fibra comprimida al centroide de la armadura comprimida [m]."""
        return self.recubrimiento_prima

    @property
    def Ag(self) -> float:
        """Área bruta de la sección [m²]."""
        return self.b * self.h

    def __repr__(self) -> str:
        return (
            f"SeccionRectangular(b={self.b} m, h={self.h} m, d={self.d:.4f} m, "
            f"{self.hormigon}, {self.acero})"
        )


class SeccionT:
    """
    Sección transversal en T o en L.

    El ala ya tiene el ancho efectivo incorporado (b_ala = b_ef).
    Para calcular b_ef usar ancho_eficaz_T() o ancho_eficaz_L().
    """

    def __init__(
        self,
        bw: float,
        h: float,
        b_ala: float,
        h_ala: float,
        recubrimiento: float,
        hormigon: Hormigon,
        acero: Acero,
        recubrimiento_prima: float | None = None,
    ):
        """
        bw:            ancho del alma [m]
        h:             altura total de la viga (incluye el ala) [m]
        b_ala:         ancho efectivo del ala [m]
        h_ala:         espesor del ala (losa) [m]
        recubrimiento: distancia fibra extrema traccionada → centroide As [m]
        """
        if bw <= 0 or h <= 0 or b_ala <= 0 or h_ala <= 0:
            raise ValueError("Dimensiones deben ser positivas")
        if b_ala < bw:
            raise ValueError("b_ala debe ser mayor o igual a bw")
        if h_ala >= h:
            raise ValueError("h_ala debe ser menor que h")
        if recubrimiento <= 0 or recubrimiento >= h:
            raise ValueError("recubrimiento debe estar entre 0 y h")
        self.bw = bw
        self.h = h
        self.b_ala = b_ala
        self.h_ala = h_ala
        self.recubrimiento = recubrimiento
        self.recubrimiento_prima = recubrimiento_prima if recubrimiento_prima is not None else recubrimiento
        self.hormigon = hormigon
        self.acero = acero

    @property
    def d(self) -> float:
        """Altura útil hacia la armadura traccionada [m]."""
        return self.h - self.recubrimiento

    @property
    def d_prima(self) -> float:
        return self.recubrimiento_prima

    @property
    def Ag(self) -> float:
        """Área bruta de la sección [m²]."""
        return self.bw * (self.h - self.h_ala) + self.b_ala * self.h_ala

    @property
    def hw(self) -> float:
        """Altura del alma (por debajo del ala) [m]."""
        return self.h - self.h_ala

    def __repr__(self) -> str:
        return (
            f"SeccionT(bw={self.bw} m, h={self.h} m, b_ala={self.b_ala} m, "
            f"h_ala={self.h_ala} m, d={self.d:.4f} m)"
        )


class SeccionCircular:
    """Sección transversal circular — principalmente para columnas."""

    def __init__(
        self,
        D: float,
        recubrimiento: float,
        hormigon: Hormigon,
        acero: Acero,
    ):
        """
        D:             diámetro exterior [m]
        recubrimiento: distancia de la fibra extrema al centroide de la armadura [m]
        """
        if D <= 0:
            raise ValueError("D debe ser positivo")
        if recubrimiento <= 0 or recubrimiento >= D / 2:
            raise ValueError("recubrimiento debe estar entre 0 y D/2")
        self.D = D
        self.recubrimiento = recubrimiento
        self.hormigon = hormigon
        self.acero = acero

    @property
    def Ag(self) -> float:
        """Área bruta [m²]."""
        return math.pi * self.D ** 2 / 4.0

    @property
    def d(self) -> float:
        """Altura útil (para flexión simple) [m]."""
        return self.D - self.recubrimiento

    @property
    def Dc(self) -> float:
        """Diámetro del núcleo (para cálculo de espiral/zuncho) [m]."""
        return self.D - 2.0 * self.recubrimiento

    @property
    def Ach(self) -> float:
        """Área del núcleo (hasta cara exterior del espiral) [m²]."""
        return math.pi * self.Dc ** 2 / 4.0

    def __repr__(self) -> str:
        return (
            f"SeccionCircular(D={self.D} m, recubrimiento={self.recubrimiento} m, "
            f"Ag={self.Ag:.4f} m²)"
        )
