"""
Columnas de hormigón armado — CIRSOC 201-2005, cap. 5–6.

Alcance:
  - Columnas cortas (sin mayoración por esbeltez).
  - Con estribos rectangulares: φ=0.65, Pn_max=0.80·Pn_0  (art. 10.3.5).
  - Zunchadas:                  φ=0.70, Pn_max=0.85·Pn_0  (art. 10.3.6).
  - Cuantía longitudinal: 0.01 ≤ ρg ≤ 0.08 (art. 10.9.1).
  - Diagrama de interacción P-M para secciones rectangulares (armadura simétrica).
  - φ variable a lo largo del diagrama (art. 9.3.2): transición tracción ↔ compresión.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS
from hormigon.secciones import SeccionRectangular, SeccionCircular

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PHI_ESTRIBO  = 0.65   # factor de reducción, columna con estribos
PHI_ZUNCHADA = 0.70   # ídem, zunchada
K_ESTRIBO    = 0.80   # factor de excentricidad mínima (art. 10.3.5)
K_ZUNCHADA   = 0.85   # ídem (art. 10.3.6)
RHO_MIN      = 0.01   # cuantía longitudinal mínima (art. 10.9.1)
RHO_MAX      = 0.08   # cuantía longitudinal máxima (art. 10.9.1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def phi_columna(epsilon_t: float, epsilon_y: float,
                tipo: str = "estribos") -> float:
    """
    Factor φ según la deformación de la armadura más alejada (art. 9.3.2).

    epsilon_t : deformación unitaria de tracción (positivo = tracción)
    """
    phi_c = PHI_ESTRIBO if tipo == "estribos" else PHI_ZUNCHADA
    if epsilon_t <= epsilon_y:
        return phi_c
    elif epsilon_t >= 0.005:
        return 0.90
    else:
        return phi_c + (0.90 - phi_c) * (epsilon_t - epsilon_y) / (0.005 - epsilon_y)


def _Pn0(hormigon: Hormigon, acero: Acero,
         Ag: float, Ast_m2: float) -> float:
    """
    Resistencia nominal a compresión pura Pn_0 [kN] (sin factor de excentricidad).

    Pn_0 = 0.85·f'c·(Ag − Ast) + fy·Ast
    """
    return (hormigon.fsc * (Ag - Ast_m2) + acero.fy * Ast_m2) * 1000.0


# ---------------------------------------------------------------------------
# Resultado de columna corta — carga axial pura
# ---------------------------------------------------------------------------

@dataclass
class ResultadoColumna:
    """Resultado de dimensionado o verificación de columna corta (Pu axial)."""

    Pu:    float   # kN — solicitación
    tipo:  str     # "estribos" | "zunchada"

    Pn_0:    float   # kN — compresión pura (sin factor excentricidad)
    Pn_max:  float   # kN — k · Pn_0
    phi_Pn:  float   # kN — φ · Pn_max

    Ast:   float   # cm² — calculada (dimensionado) o dada (verificación)
    rho_g: float   # Ast / Ag

    rho_min: float = RHO_MIN
    rho_max: float = RHO_MAX

    verifica_cuantia_min: bool = True
    verifica_cuantia_max: bool = True
    verifica:             bool = True   # φPn ≥ Pu

    # Adoptado (tras llamar a adoptar())
    phi_barra: Optional[int]   = None
    n_barras:  Optional[int]   = None
    Ast_real:  Optional[float] = None   # cm²

    def adoptar(self, phi: int, n_barras: int) -> ResultadoColumna:
        """Registra la elección de barras: n barras de diámetro phi [mm]."""
        self.phi_barra = phi
        self.n_barras  = n_barras
        self.Ast_real  = n_barras * BARRAS[phi]
        return self

    def mostrar(self) -> None:
        k   = K_ESTRIBO   if self.tipo == "estribos" else K_ZUNCHADA
        phi = PHI_ESTRIBO if self.tipo == "estribos" else PHI_ZUNCHADA
        print(f"{'Tipo':<25}: {self.tipo}")
        print(f"{'Pu':<25}: {self.Pu:.1f} kN")
        print(f"{'Pn_0':<25}: {self.Pn_0:.1f} kN")
        print(f"{'Pn_max (k=' + str(k) + ')':<25}: {self.Pn_max:.1f} kN")
        v = "✓" if self.verifica else "✗"
        print(f"{'φ·Pn (φ=' + str(phi) + ')':<25}: {self.phi_Pn:.1f} kN  {v}")
        print(f"{'Ast':<25}: {self.Ast:.2f} cm²")
        cuantia_ok = self.verifica_cuantia_min and self.verifica_cuantia_max
        print(
            f"{'ρg':<25}: {self.rho_g:.4f}  [{self.rho_min:.2f}–{self.rho_max:.2f}]  "
            f"{'✓' if cuantia_ok else '✗'}"
        )
        if self.Ast_real is not None:
            print(
                f"{'Adoptado':<25}: {self.n_barras}φ{self.phi_barra}  "
                f"Ast_real={self.Ast_real:.2f} cm²"
            )


# ---------------------------------------------------------------------------
# API pública — axial puro
# ---------------------------------------------------------------------------

def dimensionar_columna(
    seccion: SeccionRectangular | SeccionCircular,
    Pu: float,
    tipo: str = "estribos",
) -> ResultadoColumna:
    """
    Calcula la armadura longitudinal necesaria para Pu [kN].

    Pu = φ · k · [0.85·f'c·(Ag − Ast) + fy·Ast]
    Si el resultado < ρ_min → gobierna mínimo; si > ρ_max → sección insuficiente.
    """
    hormigon = seccion.hormigon
    acero    = seccion.acero
    Ag       = seccion.Ag           # m²

    phi = PHI_ESTRIBO if tipo == "estribos" else PHI_ZUNCHADA
    k   = K_ESTRIBO   if tipo == "estribos" else K_ZUNCHADA

    fsc = hormigon.fsc   # MPa
    fy  = acero.fy       # MPa

    # Despejando Ast [m²]:
    # Pu/(φ·k·1000) = fsc·Ag + (fy - fsc)·Ast
    denom  = (fy - fsc) * 1000.0                 # kN/m²
    lhs    = Pu / (phi * k) - fsc * Ag * 1000.0  # kN
    Ast_m2 = lhs / denom if abs(denom) > 1e-9 else 0.0

    Ast_min_m2 = RHO_MIN * Ag
    Ast_max_m2 = RHO_MAX * Ag

    seccion_insuficiente = Ast_m2 > Ast_max_m2 + 1e-9
    Ast_m2 = max(Ast_min_m2, min(Ast_m2, Ast_max_m2))

    Ast_cm2 = Ast_m2 * 1e4
    rho_g   = Ast_m2 / Ag

    Pn_0   = _Pn0(hormigon, acero, Ag, Ast_m2)
    Pn_max = k * Pn_0
    phi_Pn = phi * Pn_max

    return ResultadoColumna(
        Pu=Pu, tipo=tipo,
        Pn_0=Pn_0, Pn_max=Pn_max, phi_Pn=phi_Pn,
        Ast=Ast_cm2, rho_g=rho_g,
        verifica_cuantia_min=rho_g >= RHO_MIN - 1e-9,
        verifica_cuantia_max=not seccion_insuficiente,
        verifica=phi_Pn >= Pu,
    )


def verificar_columna(
    seccion: SeccionRectangular | SeccionCircular,
    Pu: float,
    Ast: float,
    tipo: str = "estribos",
) -> ResultadoColumna:
    """
    Verifica φPn ≥ Pu dado Ast [cm²].
    """
    hormigon = seccion.hormigon
    acero    = seccion.acero
    Ag       = seccion.Ag

    phi = PHI_ESTRIBO if tipo == "estribos" else PHI_ZUNCHADA
    k   = K_ESTRIBO   if tipo == "estribos" else K_ZUNCHADA

    Ast_m2 = Ast / 1e4
    rho_g  = Ast_m2 / Ag

    Pn_0   = _Pn0(hormigon, acero, Ag, Ast_m2)
    Pn_max = k * Pn_0
    phi_Pn = phi * Pn_max

    return ResultadoColumna(
        Pu=Pu, tipo=tipo,
        Pn_0=Pn_0, Pn_max=Pn_max, phi_Pn=phi_Pn,
        Ast=Ast, rho_g=rho_g,
        verifica_cuantia_min=rho_g >= RHO_MIN - 1e-9,
        verifica_cuantia_max=rho_g <= RHO_MAX + 1e-9,
        verifica=phi_Pn >= Pu,
    )


# ---------------------------------------------------------------------------
# Variantes — combinaciones de barras
# ---------------------------------------------------------------------------

@dataclass
class VarianteColumna:
    phi:      int     # diámetro de barra [mm]
    n_barras: int
    Ast:      float   # cm²
    rho_g:    float
    phi_Pn:   float   # kN
    Pu:       float   # kN
    rank:     int = 0

    @property
    def verifica(self) -> bool:
        return self.phi_Pn >= self.Pu

    def __str__(self) -> str:
        return (
            f"[{self.rank}] {self.n_barras}φ{self.phi}  "
            f"Ast={self.Ast:.2f}cm²  ρg={self.rho_g:.4f}  φPn={self.phi_Pn:.1f}kN"
        )


@dataclass
class ResultadoSetColumna:
    """Variantes de armado rankeadas por mínima Ast (más económica)."""
    Pu:            float
    Ast_requerida: float   # cm²
    variantes:     list[VarianteColumna] = field(default_factory=list)

    def mostrar(self) -> None:
        print(
            f"Pu = {self.Pu:.1f} kN  |  Ast requerida = {self.Ast_requerida:.2f} cm²\n"
        )
        print(f"{'Rank':<5} {'Barras':<16} {'Ast [cm²]':<12} {'ρg':<10} {'φPn [kN]'}")
        print("-" * 58)
        for v in self.variantes:
            print(
                f"[{v.rank}]   {v.n_barras}φ{v.phi:<11}  {v.Ast:<12.2f}  "
                f"{v.rho_g:<10.4f}  {v.phi_Pn:.1f}"
            )

    def adoptar(self, rank: int) -> VarianteColumna:
        for v in self.variantes:
            if v.rank == rank:
                return v
        raise ValueError(f"No existe variante con rank {rank}")


def dimensionar_columna_variantes(
    seccion: SeccionRectangular | SeccionCircular,
    Pu: float,
    tipo: str = "estribos",
    n_barras_rango: range = range(4, 25),
) -> ResultadoSetColumna:
    """
    Genera todas las combinaciones de barras que verifican, rankeadas por mínima Ast.
    """
    res_base = dimensionar_columna(seccion, Pu, tipo)
    Ast_req  = res_base.Ast   # cm²
    Ag       = seccion.Ag

    phi_col = PHI_ESTRIBO if tipo == "estribos" else PHI_ZUNCHADA
    k       = K_ESTRIBO   if tipo == "estribos" else K_ZUNCHADA

    variantes: list[VarianteColumna] = []

    for phi_d in DIAMETROS:
        area_barra = BARRAS[phi_d]   # cm²
        for n in n_barras_rango:
            Ast    = n * area_barra
            Ast_m2 = Ast / 1e4
            rho_g  = Ast_m2 / Ag

            if rho_g < RHO_MIN - 1e-9 or rho_g > RHO_MAX + 1e-9:
                continue
            if Ast < Ast_req - 1e-6:
                continue

            Pn_0   = _Pn0(seccion.hormigon, seccion.acero, Ag, Ast_m2)
            phi_Pn = phi_col * k * Pn_0

            v = VarianteColumna(
                phi=phi_d, n_barras=n, Ast=Ast, rho_g=rho_g,
                phi_Pn=phi_Pn, Pu=Pu,
            )
            if v.verifica:
                variantes.append(v)

    # Eliminar duplicados exactos
    seen   = set()
    unicas = []
    for v in variantes:
        key = (v.phi, v.n_barras)
        if key not in seen:
            seen.add(key)
            unicas.append(v)

    unicas.sort(key=lambda v: (v.Ast, v.phi))
    for i, v in enumerate(unicas, 1):
        v.rank = i

    return ResultadoSetColumna(Pu=Pu, Ast_requerida=Ast_req, variantes=unicas)


# ---------------------------------------------------------------------------
# Diagrama de interacción P-M — sección rectangular simétrica
# ---------------------------------------------------------------------------

@dataclass
class PuntoPM:
    """Un punto de la curva de interacción P-M."""
    Pn:        float   # kN  (positivo = compresión)
    Mn:        float   # kNm
    epsilon_t: float   # deformación en la armadura más alejada (tracción positiva)
    phi:       float   # factor φ en ese punto
    phi_Pn:    float   # kN
    phi_Mn:    float   # kNm


@dataclass
class DiagramaInteraccion:
    """Curva de interacción P-M con φ variable."""
    puntos:      list[PuntoPM]
    Pn_0:        float   # kN — compresión pura
    phi_Pn_max:  float   # kN — φ·k·Pn_0 (techo del diagrama de diseño)
    Pn_bal:      float   # kN — punto de balance
    Mn_bal:      float   # kNm
    phi_Pn_bal:  float
    phi_Mn_bal:  float
    tipo: str

    def contiene(self, Pu: float, Mu: float) -> bool:
        """
        True si el punto (Pu, Mu) cae dentro del diagrama de diseño.

        Interpola linealmente entre puntos adyacentes, respetando el techo φPn_max.
        """
        if Pu > self.phi_Pn_max + 1e-6:
            return False

        # Ordenar puntos de mayor a menor phi_Pn
        pts = sorted(self.puntos, key=lambda p: -p.phi_Pn)

        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            if p2.phi_Pn <= Pu <= p1.phi_Pn + 1e-6:
                if abs(p1.phi_Pn - p2.phi_Pn) < 1e-9:
                    Mu_cap = max(p1.phi_Mn, p2.phi_Mn)
                else:
                    t = (Pu - p1.phi_Pn) / (p2.phi_Pn - p1.phi_Pn)
                    Mu_cap = p1.phi_Mn + t * (p2.phi_Mn - p1.phi_Mn)
                return Mu <= Mu_cap + 1e-6

        return False


def diagrama_interaccion(
    seccion: SeccionRectangular,
    Ast: float,
    tipo: str = "estribos",
    n_puntos: int = 80,
) -> DiagramaInteraccion:
    """
    Genera el diagrama de interacción P-M para una sección rectangular con
    armadura simétrica (As' = As = Ast/2).

    Ast: área total de armadura longitudinal [cm²]
    """
    if not isinstance(seccion, SeccionRectangular):
        raise TypeError(
            "diagrama_interaccion solo implementado para SeccionRectangular. "
            "Sección circular: pendiente."
        )

    hormigon = seccion.hormigon
    acero    = seccion.acero

    b    = seccion.b
    h    = seccion.h
    d    = seccion.d
    d_pr = (seccion.recubrimiento_prima
            if seccion.recubrimiento_prima is not None
            else seccion.recubrimiento)
    Ag   = seccion.Ag

    phi_c  = PHI_ESTRIBO if tipo == "estribos" else PHI_ZUNCHADA
    k      = K_ESTRIBO   if tipo == "estribos" else K_ZUNCHADA
    beta1  = hormigon.beta1
    fsc    = hormigon.fsc        # MPa
    fy     = acero.fy            # MPa
    Es     = acero.Es            # MPa
    eps_cu = hormigon.epsilon_u
    eps_y  = acero.epsilon_y

    Ast_m2      = Ast / 1e4
    As_m2       = Ast_m2 / 2    # capa traccionada
    As_prima_m2 = Ast_m2 / 2    # capa comprimida

    Pn_0       = _Pn0(hormigon, acero, Ag, Ast_m2)
    phi_Pn_max = phi_c * k * Pn_0

    # Valores clave de c
    c_bal = eps_cu * d / (eps_cu + eps_y)
    c_005 = eps_cu * d / (eps_cu + 0.005)

    # Rango de c: de muy grande (compresión pura) a muy pequeño (tracción pura)
    c_max = 500.0 * h
    c_min = 1e-4 * h

    c_log = np.logspace(math.log10(c_min), math.log10(c_max), n_puntos)[::-1]
    c_key = np.array([c_bal * 3, c_bal * 1.5, c_bal, c_005 * 1.5, c_005, c_005 * 0.5])
    c_all = np.unique(np.concatenate([c_log, c_key]))[::-1]

    puntos: list[PuntoPM] = []

    for c in c_all:
        a = min(beta1 * c, h)

        # Deformaciones (signo: positivo = compresión)
        eps_s_pr = eps_cu * (c - d_pr) / c
        eps_s    = eps_cu * (c - d) / c

        # Tensiones [MPa], acotadas a fy
        f_s_pr = max(-fy, min(fy, eps_s_pr * Es))
        f_s    = max(-fy, min(fy, eps_s    * Es))

        # Fuerzas [kN] — se descuenta el hormigón bajo el bloque de compresión
        Cc     = fsc * 1000.0 * a * b
        Cs_pr  = As_prima_m2 * (f_s_pr - (fsc if d_pr < a else 0.0)) * 1000.0
        T      = As_m2       * (f_s    - (fsc if d    < a else 0.0)) * 1000.0

        Pn = Cc + Cs_pr + T
        Mn = abs(
            Cc    * (h / 2 - a / 2)   +
            Cs_pr * (h / 2 - d_pr)    +
            T     * (h / 2 - d)
        )

        eps_t = max(0.0, -eps_s)   # tracción positiva (para φ)
        phi   = phi_columna(eps_t, eps_y, tipo)

        phi_Pn = min(phi * Pn, phi_Pn_max)
        phi_Mn = phi * Mn

        puntos.append(PuntoPM(
            Pn=Pn, Mn=Mn, epsilon_t=eps_t,
            phi=phi, phi_Pn=phi_Pn, phi_Mn=phi_Mn,
        ))

    # Punto de tracción pura
    Pn_ten = -Ast_m2 * fy * 1000.0
    puntos.append(PuntoPM(
        Pn=Pn_ten, Mn=0.0, epsilon_t=1.0,
        phi=0.90, phi_Pn=0.90 * Pn_ten, phi_Mn=0.0,
    ))

    # Punto de balance (c = c_bal)
    a_bal    = beta1 * c_bal
    eps_s_pr_b = eps_cu * (c_bal - d_pr) / c_bal
    f_s_pr_b   = max(-fy, min(fy, eps_s_pr_b * Es))
    Cc_b     = fsc * 1000.0 * a_bal * b
    Cs_pr_b  = As_prima_m2 * (f_s_pr_b - (fsc if d_pr < a_bal else 0.0)) * 1000.0
    T_b      = As_m2       * (-fy - (fsc if d < a_bal else 0.0)) * 1000.0
    Pn_bal   = Cc_b + Cs_pr_b + T_b
    Mn_bal   = abs(
        Cc_b    * (h / 2 - a_bal / 2) +
        Cs_pr_b * (h / 2 - d_pr)      +
        T_b     * (h / 2 - d)
    )
    phi_bal = phi_columna(eps_y, eps_y, tipo)   # = phi_c

    return DiagramaInteraccion(
        puntos=puntos,
        Pn_0=Pn_0,
        phi_Pn_max=phi_Pn_max,
        Pn_bal=Pn_bal,
        Mn_bal=Mn_bal,
        phi_Pn_bal=phi_bal * Pn_bal,
        phi_Mn_bal=phi_bal * Mn_bal,
        tipo=tipo,
    )
