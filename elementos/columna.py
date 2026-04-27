"""
Wrapper para columna con flexocompresión — P + M simultáneos.

Clase:
  Columna — dados Pu y Mu, diseña o verifica Ast a partir del diagrama P-M.

Unidades: kN y metros.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from hormigon.columnas import (
    DiagramaInteraccion,
    PHI_ESTRIBO,
    PHI_ZUNCHADA,
    RHO_MAX,
    RHO_MIN,
    diagrama_interaccion,
)
from hormigon.materiales import BARRAS, DIAMETROS


@dataclass
class ResultadoColumnaFlexoCompresion:
    """Resultado de diseño/verificación de columna con P + M."""
    Pu:      float   # kN — solicitación axial de diseño
    Mu:      float   # kNm — momento de diseño
    Ast:     float   # cm² — área de armadura total
    rho_g:   float   # Ast / Ag
    tipo:    str     # "estribos" | "zunchada"
    diagrama: DiagramaInteraccion
    verifica: bool

    # Barras adoptadas (opcionales)
    phi_barra: Optional[int]  = None
    n_barras:  Optional[int]  = None
    Ast_real:  Optional[float] = None

    def adoptar(self, phi: int, n_barras: int) -> ResultadoColumnaFlexoCompresion:
        """Registra la elección de barras (phi en mm, n barras)."""
        self.phi_barra = phi
        self.n_barras  = n_barras
        self.Ast_real  = n_barras * BARRAS[phi]
        return self

    def mostrar(self) -> None:
        check = 'OK verifica' if self.verifica else 'NO verifica'
        print(f"{'Pu':<28}: {self.Pu:.1f} kN")
        print(f"{'Mu':<28}: {self.Mu:.1f} kNm")
        print(f"{'Ast calc':<28}: {self.Ast:.2f} cm2")
        print(f"{'rho_g':<28}: {self.rho_g:.4f}  [{RHO_MIN:.2f}-{RHO_MAX:.2f}]")
        print(f"{'Verificación P-M':<28}: {check}")
        if self.Ast_real is not None:
            print(f"{'Adoptado':<28}: {self.n_barras}phi{self.phi_barra}  "
                  f"Ast_real={self.Ast_real:.2f} cm2")

    def graficar(self):
        """Diagrama de interacción con el punto de demanda (Pu, Mu)."""
        from graficos.diagramas import graficar_interaccion_PM
        return graficar_interaccion_PM(self.diagrama, Pu=self.Pu, Mu=self.Mu)


class Columna:
    """
    Columna corta con flexocompresión (Pu, Mu).

    El diseño encuentra la mínima Ast tal que (Pu, Mu) quede dentro del
    diagrama de interacción φP-φM.
    """

    def __init__(
        self,
        seccion,
        Pu: float,
        Mu: float,
        Ast: Optional[float] = None,
        tipo: str = 'estribos',
    ):
        """
        seccion : SeccionRectangular
        Pu      : carga axial mayorada [kN]
        Mu      : momento mayorado [kNm]
        Ast     : armadura total [cm²] — si se da, sólo verifica; si es None, diseña
        tipo    : 'estribos' (φ=0.65) | 'zunchada' (φ=0.70)
        """
        if not hasattr(seccion, 'b'):
            raise TypeError(
                "Columna solo acepta SeccionRectangular. "
                "Sección circular: pendiente de implementación."
            )
        self.seccion = seccion
        self.Pu      = Pu
        self.Mu      = Mu
        self._Ast    = Ast
        self.tipo    = tipo

    def calcular(self) -> ResultadoColumnaFlexoCompresion:
        if self._Ast is not None:
            return self._verificar(self._Ast)
        return self._disenar()

    def _verificar(self, Ast: float) -> ResultadoColumnaFlexoCompresion:
        diag   = diagrama_interaccion(self.seccion, Ast, self.tipo)
        Ag     = self.seccion.Ag
        rho_g  = (Ast / 1e4) / Ag
        return ResultadoColumnaFlexoCompresion(
            Pu=self.Pu, Mu=self.Mu, Ast=Ast, rho_g=rho_g,
            tipo=self.tipo, diagrama=diag,
            verifica=diag.contiene(self.Pu, self.Mu),
        )

    def _disenar(self) -> ResultadoColumnaFlexoCompresion:
        """
        Búsqueda binaria del mínimo Ast tal que (Pu, Mu) ∈ diagrama.

        Intervalo: [ρ_min·Ag, ρ_max·Ag].
        """
        Ag      = self.seccion.Ag
        Ast_min = RHO_MIN * Ag * 1e4   # cm²
        Ast_max = RHO_MAX * Ag * 1e4   # cm²

        # Verificar si ρ_max alcanza
        diag_max = diagrama_interaccion(self.seccion, Ast_max, self.tipo)
        if not diag_max.contiene(self.Pu, self.Mu):
            raise ValueError(
                f"La sección es insuficiente: (Pu={self.Pu:.0f} kN, "
                f"Mu={self.Mu:.0f} kNm) no está dentro del diagrama "
                f"con ρg_max = {RHO_MAX:.0%}. Aumente la sección."
            )

        # Búsqueda binaria (tolerancia 0.05 cm²)
        lo, hi = Ast_min, Ast_max
        for _ in range(40):
            mid  = (lo + hi) / 2.0
            diag = diagrama_interaccion(self.seccion, mid, self.tipo)
            if diag.contiene(self.Pu, self.Mu):
                hi = mid
            else:
                lo = mid
            if hi - lo < 0.05:
                break

        Ast   = hi
        diag  = diagrama_interaccion(self.seccion, Ast, self.tipo)
        rho_g = (Ast / 1e4) / Ag
        return ResultadoColumnaFlexoCompresion(
            Pu=self.Pu, Mu=self.Mu, Ast=Ast, rho_g=rho_g,
            tipo=self.tipo, diagrama=diag,
            verifica=True,
        )
