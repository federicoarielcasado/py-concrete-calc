"""
Losas de hormigón armado en 1 dirección — CIRSOC 201-2005.

Método de los coeficientes (art. 8.3.3): aplicable cuando hay ≥ 2 tramos,
cargas uniformes y relación de luces adyacentes ≤ 1.20.

Alcance:
  - Espesores mínimos para control de deflexiones (art. 9.5.2.1).
  - Momentos y cortantes por coeficientes (art. 8.3.3).
  - Armadura principal (flexión) en cada sección crítica.
  - Armadura de temperatura y retracción (art. 7.12).
  - Separación máxima de barras (art. 7.6.5 y 7.12.2.2).
  - Verificación de corte sin estribos (art. 11.3).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion
from hormigon.corte import Vc_simplificado, PHI_CORTE


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def h_minimo(ln: float, extremo: str = "libre", n_tramos: int = 2) -> float:
    """
    Espesor mínimo de losa en 1 dirección para control de deflexiones (art. 9.5.2.1).

    ln:      luz libre del tramo [m]
    extremo: condición del extremo discontinuo —
             "libre"   → sin restricción (apoyo simple)
             "viga"    → empotrado a viga
             "columna" → empotrado a columna
    n_tramos: cantidad de tramos (≥ 2 para el método de coeficientes)
    """
    # Tramos extremos
    if extremo == "libre":
        h_ext = ln / 20.0
    else:   # empotrado a viga o columna
        h_ext = ln / 24.0

    # Tramos interiores
    h_int = ln / 28.0 if n_tramos > 2 else 0.0

    return max(h_ext, h_int)


def As_temperatura(h: float, acero: Acero) -> float:
    """
    Área de armadura de temperatura y retracción por metro de ancho [cm²/m] (art. 7.12.2.1).

    Coeficiente ρ_temp:
      fy ≤ 420 MPa → ρ = 0.0018
      fy > 420 MPa → ρ = max(0.0018 · 420 / fy, 0.0014)
    """
    fy = acero.fy
    if fy <= 420.0:
        rho_t = 0.0018
    else:
        rho_t = max(0.0018 * 420.0 / fy, 0.0014)
    return rho_t * h * 1e4   # [cm²/m]  (b=1m)


def s_max_principal(h: float) -> float:
    """Separación máxima de barras de armadura principal [m] (art. 7.6.5)."""
    return min(3.0 * h, 0.45)


def s_max_temperatura(h: float) -> float:
    """Separación máxima de barras de temperatura [m] (art. 7.12.2.2)."""
    return min(5.0 * h, 0.45)


# ---------------------------------------------------------------------------
# Coeficientes de momento — art. 8.3.3
# ---------------------------------------------------------------------------

def _coef_Mu(wu: float, ln: float) -> dict[str, float]:
    """Términos wu·ln² / C para cada tipo de sección (ver _secciones_criticas)."""
    return {k: wu * ln ** 2 / v for k, v in {
        "pos_ext_libre":     11,
        "pos_ext_empotrado": 14,
        "pos_int":           16,
        "neg_ext_viga":      24,
        "neg_ext_columna":   16,
        "neg_1er_int_2":      9,
        "neg_1er_int_mas":   10,
        "neg_int":           11,
    }.items()}


# ---------------------------------------------------------------------------
# Objetos resultado
# ---------------------------------------------------------------------------

@dataclass
class SeccionLosa:
    """Resultado de armado en una sección crítica de la losa (franja de 1 m)."""
    nombre:   str
    Mu:       float   # kNm/m — momento de diseño
    As:       float   # cm²/m — armadura calculada
    s_max:    float   # m     — separación máxima permitida
    phi_Mn:   float   # kNm/m — resistencia de diseño
    verifica: bool


@dataclass
class ResultadoLosa1Dir:
    """Resultado completo del diseño de una losa en 1 dirección."""

    # Geometría e inputs
    h:        float   # m — espesor adoptado
    d:        float   # m — altura útil
    ln:       float   # m — luz libre
    wu:       float   # kN/m² — carga mayorada
    n_tramos: int
    extremo:  str     # "libre" | "viga" | "columna"

    # Control de espesor
    h_min:        float
    verifica_h:   bool

    # Secciones de flexión
    secciones: list[SeccionLosa]

    # Temperatura y retracción
    As_temp:    float   # cm²/m
    s_temp_max: float   # m

    # Corte (φVc por metro de ancho)
    phi_Vc:        float   # kN/m
    Vu_max:        float   # kN/m
    verifica_corte: bool

    def mostrar(self) -> None:
        print(f"{'Espesor h':<30}: {self.h*100:.0f} cm  "
              f"(h_min={self.h_min*100:.1f} cm  {'✓' if self.verifica_h else '✗'})")
        print(f"{'Altura útil d':<30}: {self.d*100:.1f} cm")
        print(f"{'Carga mayorada wu':<30}: {self.wu:.2f} kN/m²")
        print(f"{'Luz libre ln':<30}: {self.ln:.2f} m")
        print()
        print(f"{'Sección':<30} {'Mu [kNm/m]':>12} {'As [cm²/m]':>12} "
              f"{'s_max [cm]':>11} {'φMn [kNm/m]':>12}  OK")
        print("-" * 82)
        for s in self.secciones:
            ok = "✓" if s.verifica else "✗"
            print(
                f"  {s.nombre:<28} {s.Mu:>12.2f} {s.As:>12.2f} "
                f"{s.s_max*100:>11.0f} {s.phi_Mn:>12.2f}  {ok}"
            )
        print()
        print(f"{'Armadura temperatura':<30}: {self.As_temp:.2f} cm²/m  "
              f"s_max={self.s_temp_max*100:.0f} cm")
        print()
        ok_v = "✓" if self.verifica_corte else "✗"
        print(f"{'φVc':<30}: {self.phi_Vc:.1f} kN/m")
        print(f"{'Vu_max':<30}: {self.Vu_max:.1f} kN/m  {ok_v}")


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_losa_1dir(
    h:            float,
    recubrimiento: float,
    hormigon:     Hormigon,
    acero:        Acero,
    wu:           float,
    ln:           float,
    n_tramos:     int = 2,
    extremo:      str = "libre",
) -> ResultadoLosa1Dir:
    """
    Diseña la armadura de una losa en 1 dirección por el método de los coeficientes.

    h:             espesor adoptado [m]
    recubrimiento: distancia al centroide de la armadura principal [m]
    wu:            carga mayorada total [kN/m²]
    ln:            luz libre del tramo [m]
    n_tramos:      número de tramos (≥ 2 para aplicar art. 8.3.3)
    extremo:       condición del apoyo exterior discontinuo:
                   "libre"   → sin restricción
                   "viga"    → empotrado a viga de borde
                   "columna" → empotrado a columna

    Retorna ResultadoLosa1Dir con todas las secciones críticas diseñadas.
    """
    if n_tramos < 2:
        raise ValueError(
            "El método de coeficientes (art. 8.3.3) requiere n_tramos ≥ 2. "
            "Para tramo único, calcule Mu directamente y use dimensionar_flexion()."
        )

    d = h - recubrimiento

    # Sección franja de 1m — se reutiliza para todas las secciones
    sec = SeccionRectangular(
        b=1.0, h=h, recubrimiento=recubrimiento,
        hormigon=hormigon, acero=acero,
    )
    s_max_p = s_max_principal(h)

    # Espesor mínimo
    h_min = h_minimo(ln, extremo, n_tramos)

    # Momentos por coeficientes
    C = _coef_Mu(wu, ln)

    def _dim(nombre: str, Mu: float) -> SeccionLosa:
        if Mu < 1e-6:
            return SeccionLosa(nombre=nombre, Mu=0.0, As=0.0,
                               s_max=s_max_p, phi_Mn=0.0, verifica=True)
        r = dimensionar_flexion(sec, Mu=Mu)
        return SeccionLosa(
            nombre=nombre,
            Mu=Mu,
            As=r.As,
            s_max=s_max_p,
            phi_Mn=r.phi_Mn,
            verifica=r.verifica,
        )

    secciones: list[SeccionLosa] = []

    # --- Momento positivo en tramo extremo ---
    if extremo == "libre":
        secciones.append(_dim("Tramo ext. M+ (centro)", C["pos_ext_libre"]))
    else:
        secciones.append(_dim("Tramo ext. M+ (centro)", C["pos_ext_empotrado"]))

    # --- Momento positivo en tramos interiores ---
    if n_tramos > 2:
        secciones.append(_dim("Tramo int. M+ (centro)", C["pos_int"]))

    # --- Momento negativo en el apoyo exterior ---
    if extremo == "libre":
        secciones.append(_dim("Apoyo ext. M- (libre)", 0.0))
    elif extremo == "viga":
        secciones.append(_dim("Apoyo ext. M- (viga)", C["neg_ext_viga"]))
    else:
        secciones.append(_dim("Apoyo ext. M- (columna)", C["neg_ext_columna"]))

    # --- Momento negativo en la cara exterior del 1° apoyo interior ---
    if n_tramos == 2:
        secciones.append(_dim("1° apoyo int. M- (cara ext.)", C["neg_1er_int_2"]))
    else:
        secciones.append(_dim("1° apoyo int. M- (cara ext.)", C["neg_1er_int_mas"]))

    # --- Momento negativo en apoyos interiores centrales ---
    if n_tramos > 3:
        secciones.append(_dim("Apoyos int. M-", C["neg_int"]))

    # --- Armadura de temperatura ---
    As_temp  = As_temperatura(h, acero)
    s_t_max  = s_max_temperatura(h)

    # --- Corte: sección crítica a distancia d del apoyo ---
    # Vu máximo en cara del primer apoyo interior (art. 8.3.3)
    Vu_max = 1.15 * wu * ln / 2.0   # kN/m

    # φVc por metro de ancho (b=1 m)
    Vc     = Vc_simplificado(hormigon, bw=1.0, d=d)
    phi_Vc = PHI_CORTE * Vc

    return ResultadoLosa1Dir(
        h=h, d=d, ln=ln, wu=wu, n_tramos=n_tramos, extremo=extremo,
        h_min=h_min, verifica_h=(h >= h_min - 1e-9),
        secciones=secciones,
        As_temp=As_temp, s_temp_max=s_t_max,
        phi_Vc=phi_Vc, Vu_max=Vu_max, verifica_corte=(phi_Vc >= Vu_max),
    )


# ---------------------------------------------------------------------------
# Losa en tramo simple (sin método de coeficientes)
# ---------------------------------------------------------------------------

def calcular_losa_simple(
    h:             float,
    recubrimiento: float,
    hormigon:      Hormigon,
    acero:         Acero,
    wu:            float,
    ln:            float,
) -> ResultadoLosa1Dir:
    """
    Losa en 1 dirección de un solo tramo simplemente apoyado.

    Mu = wu·ln²/8 (viga simplemente apoyada).
    """
    d = h - recubrimiento
    sec = SeccionRectangular(
        b=1.0, h=h, recubrimiento=recubrimiento,
        hormigon=hormigon, acero=acero,
    )
    s_max_p = s_max_principal(h)
    h_min   = ln / 20.0   # art. 9.5.2.1, simplemente apoyada

    Mu = wu * ln ** 2 / 8.0
    r  = dimensionar_flexion(sec, Mu=Mu)
    sec_losa = SeccionLosa(
        nombre="Tramo simple M+ (centro)",
        Mu=Mu, As=r.As, s_max=s_max_p,
        phi_Mn=r.phi_Mn, verifica=r.verifica,
    )

    As_temp = As_temperatura(h, acero)
    s_t_max = s_max_temperatura(h)

    Vu_max  = wu * ln / 2.0
    Vc      = Vc_simplificado(hormigon, bw=1.0, d=d)
    phi_Vc  = PHI_CORTE * Vc

    return ResultadoLosa1Dir(
        h=h, d=d, ln=ln, wu=wu, n_tramos=1, extremo="libre",
        h_min=h_min, verifica_h=(h >= h_min - 1e-9),
        secciones=[sec_losa],
        As_temp=As_temp, s_temp_max=s_t_max,
        phi_Vc=phi_Vc, Vu_max=Vu_max, verifica_corte=(phi_Vc >= Vu_max),
    )
