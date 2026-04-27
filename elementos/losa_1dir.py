"""
Wrapper para losa continua en 1 dirección.

Clase:
  Losa1Dir — calcula wu a partir de cargas características y llama a losas.py.

Unidades: kN y metros.
"""
from __future__ import annotations

from hormigon.cargas import wu_DL
from hormigon.losas import ResultadoLosa1Dir, calcular_losa_1dir, calcular_losa_simple
from hormigon.materiales import Acero, Hormigon


class Losa1Dir:
    """
    Losa en 1 dirección — método de coeficientes (art. 8.3.3) o tramo simple.

    Para n_tramos ≥ 2 usa el método de coeficientes.
    Para n_tramos = 1 calcula como viga simplemente apoyada (Mu = wu·ln²/8).
    """

    def __init__(
        self,
        h:             float,
        recubrimiento: float,
        hormigon:      Hormigon,
        acero:         Acero,
        wD:            float,
        wL:            float,
        ln:            float,
        n_tramos:      int = 2,
        extremo:       str = 'libre',
    ):
        """
        h             : espesor adoptado de la losa [m]
        recubrimiento : distancia a la armadura principal [m]
        hormigon      : objeto Hormigon
        acero         : objeto Acero
        wD, wL        : carga muerta y viva [kN/m²]
        ln            : luz libre del tramo [m]
        n_tramos      : número de tramos (1 = tramo simple, ≥ 2 = coeficientes)
        extremo       : condición del extremo discontinuo:
                        'libre'   → apoyo sin restricción
                        'viga'    → empotrado a viga de borde
                        'columna' → empotrado a columna
        """
        self.h             = h
        self.recubrimiento = recubrimiento
        self.hormigon      = hormigon
        self.acero         = acero
        self.wu            = wu_DL(wD, wL)
        self.ln            = ln
        self.n_tramos      = n_tramos
        self.extremo       = extremo

    def calcular(self) -> ResultadoLosa1Dir:
        """Realiza el cálculo y retorna el resultado completo."""
        if self.n_tramos == 1:
            return calcular_losa_simple(
                h=self.h,
                recubrimiento=self.recubrimiento,
                hormigon=self.hormigon,
                acero=self.acero,
                wu=self.wu,
                ln=self.ln,
            )
        return calcular_losa_1dir(
            h=self.h,
            recubrimiento=self.recubrimiento,
            hormigon=self.hormigon,
            acero=self.acero,
            wu=self.wu,
            ln=self.ln,
            n_tramos=self.n_tramos,
            extremo=self.extremo,
        )
