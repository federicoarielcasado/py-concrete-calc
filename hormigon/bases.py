"""
Bases de fundación de hormigón armado — CIRSOC 201-2005, cap. 15.

Alcance:
  - Bases aisladas centradas: cuadradas y rectangulares.
  - Dimensionado de la planta desde la carga de servicio P_s y la presión
    admisible del suelo q_adm.
  - Determinación automática del espesor h_f por punzonamiento (art. 11.12)
    y corte unidireccional (art. 11.3).
  - Armadura de flexión en ambas direcciones (art. 15.4.2).
  - Distribución de armadura transversal para bases rectangulares (art. 15.4.4.2).
  - φ = 0.75 para corte/punzonamiento (art. 9.3.2.3).
  - φ = 0.90 para flexión (sección controlada por tracción).

Hipótesis:
  - Base sobre suelo con presión de contacto uniforme (q_neta = Pu / A).
  - Columna rectangular de dimensiones bc × hc.
  - Armadura inferior paralela a los ejes; recubrimiento mínimo 75 mm (suelo).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion
from hormigon.corte import PHI_CORTE

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_REC_DEFAULT = 0.075   # recubrimiento mínimo para fundaciones [m]
_H_F_MIN     = 0.25    # espesor mínimo práctico [m]
_PASO_D      = 0.005   # paso de iteración para d [m]


# ---------------------------------------------------------------------------
# Capacidad al punzonamiento (art. 11.12.2.1)
# ---------------------------------------------------------------------------

def Vc_punzonamiento(
    hormigon:       Hormigon,
    bc:             float,   # m — dimensión de columna paralela a L
    hc:             float,   # m — dimensión de columna paralela a B
    d:              float,   # m — altura útil de la base
    tipo_columna:   str = "interior",  # "interior" | "borde" | "esquina"
) -> float:
    """
    Resistencia nominal al punzonamiento Vc [kN] (art. 11.12.2.1).

    bo: perímetro de la sección crítica a d/2 de la columna.
    Vc = min(Vc_1, Vc_2, Vc_3) × 1000 [kN].
    """
    fc   = hormigon.fc
    sqfc = math.sqrt(fc)
    bo   = 2.0 * (bc + d) + 2.0 * (hc + d)      # [m]
    beta = max(bc, hc) / max(min(bc, hc), 1e-9)   # relación de lados de la columna

    alpha_s = {"interior": 40.0, "borde": 30.0, "esquina": 20.0}.get(tipo_columna, 40.0)

    Vc1 = (0.17 + 0.34 / beta) * sqfc * bo * d * 1000.0
    Vc2 = (0.083 * alpha_s * d / bo + 0.17) * sqfc * bo * d * 1000.0
    Vc3 = 0.33 * sqfc * bo * d * 1000.0

    return min(Vc1, Vc2, Vc3)


# ---------------------------------------------------------------------------
# Objetos resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoBase:
    """Resultado completo del diseño de una base centrada."""

    # ---- Geometría ----
    B:    float    # m — lado (dirección de bc)
    L:    float    # m — lado (dirección de hc); L ≥ B
    h_f:  float    # m — espesor
    d:    float    # m — altura útil

    # ---- Columna ----
    bc:   float    # m
    hc:   float    # m

    # ---- Cargas ----
    Pu:     float   # kN — axial mayorada
    P_s:    float   # kN — axial de servicio (para q_adm)
    q_adm:  float   # kN/m²
    q_neta: float   # kN/m² (Pu / A_base)

    # ---- Verificación de suelo ----
    q_servicio: float    # kN/m² (P_s / A_base)
    verifica_suelo: bool

    # ---- Punzonamiento ----
    bo:           float   # m
    Vu_punch:     float   # kN
    Vc_punch:     float   # kN
    phi_Vc_punch: float   # kN
    verifica_punch: bool

    # ---- Corte unidireccional ----
    Vu_1way_L:   float   # kN (dirección L, normalmente la más crítica)
    Vu_1way_B:   float   # kN (dirección B)
    phi_Vc_1way_L: float
    phi_Vc_1way_B: float
    verifica_1way: bool

    # ---- Flexión dirección L ----
    l_v_L:    float   # m — voladizo en L
    Mu_L:     float   # kNm
    As_L:     float   # cm² total sobre ancho B
    As_L_m:   float   # cm²/m
    phi_Mn_L: float   # kNm
    verifica_flex_L: bool

    # ---- Flexión dirección B ----
    l_v_B:    float
    Mu_B:     float
    As_B:     float   # cm² total sobre ancho L
    As_B_m:   float   # cm²/m
    phi_Mn_B: float
    verifica_flex_B: bool

    # ---- Distribución transversal (base rectangular, art. 15.4.4.2) ----
    gamma_s:       float   # fracción de As_B en la banda central
    As_banda_B:    float   # cm² en banda central de ancho B
    As_lateral_B:  float   # cm² en cada franja lateral

    @property
    def verifica(self) -> bool:
        return (
            self.verifica_suelo
            and self.verifica_punch
            and self.verifica_1way
            and self.verifica_flex_L
            and self.verifica_flex_B
        )

    def mostrar(self) -> None:
        print(f"{'Base centrada':=^60}")
        print(f"  {'Columna':<28}: {self.bc*100:.0f} × {self.hc*100:.0f} cm")
        print(f"  {'Planta adoptada':<28}: {self.B:.2f} × {self.L:.2f} m")
        print(f"  {'Espesor h_f':<28}: {self.h_f*100:.0f} cm  |  d={self.d*100:.1f} cm")
        print(f"  {'Pu':<28}: {self.Pu:.1f} kN")
        print(f"  {'q_neta (mayorada)':<28}: {self.q_neta:.1f} kN/m²")
        q_ok = "✓" if self.verifica_suelo else "✗"
        print(f"  {'q servicio':<28}: {self.q_servicio:.1f} kN/m²  "
              f"(q_adm={self.q_adm:.0f})  {q_ok}")
        print()
        p_ok = "✓" if self.verifica_punch else "✗"
        print(f"  {'Punzonamiento (bo='f'{self.bo:.2f}m)':<28}: "
              f"Vu={self.Vu_punch:.1f} kN  φVc={self.phi_Vc_punch:.1f} kN  {p_ok}")
        v_ok = "✓" if self.verifica_1way else "✗"
        print(f"  {'Corte 1-dir (L)':<28}: "
              f"Vu={self.Vu_1way_L:.1f} kN  φVc={self.phi_Vc_1way_L:.1f} kN  {v_ok}")
        print()
        fl_ok = "✓" if self.verifica_flex_L else "✗"
        print(f"  {'Flexión dir-L':<28}: "
              f"Mu={self.Mu_L:.1f} kNm  As={self.As_L:.1f}cm²  "
              f"({self.As_L_m:.2f}cm²/m)  {fl_ok}")
        fb_ok = "✓" if self.verifica_flex_B else "✗"
        print(f"  {'Flexión dir-B':<28}: "
              f"Mu={self.Mu_B:.1f} kNm  As={self.As_B:.1f}cm²  "
              f"({self.As_B_m:.2f}cm²/m)  {fb_ok}")
        if self.L > self.B + 1e-6:
            print(f"  {'Banda central (γs={self.gamma_s:.2f})':<28}: "
                  f"As_banda={self.As_banda_B:.1f}cm²  "
                  f"As_lateral={self.As_lateral_B:.1f}cm² (c/franja)")
        print()
        ok = "✓ VERIFICA" if self.verifica else "✗ NO VERIFICA"
        print(f"  {ok}")


# ---------------------------------------------------------------------------
# Lógica interna
# ---------------------------------------------------------------------------

def _calcular_con_d(
    bc: float, hc: float, B: float, L: float, d: float,
    Pu: float, P_s: float, q_adm: float,
    hormigon: Hormigon, acero: Acero, recubrimiento: float,
) -> ResultadoBase:
    """Calcula todos los resultados para una geometría (B, L, d) dada."""
    h_f    = d + recubrimiento
    q_neta = Pu / (B * L)
    A_base = B * L

    # ---- Verificación de presión de suelo ----
    q_serv = P_s / A_base
    ver_suelo = q_serv <= q_adm + 1e-6

    # ---- Punzonamiento ----
    bo       = 2.0 * (bc + d) + 2.0 * (hc + d)
    Vc_p     = Vc_punzonamiento(hormigon, bc, hc, d)
    phi_Vc_p = PHI_CORTE * Vc_p

    # Área de la sección crítica al punzonamiento, sin exceder el área de la base
    A_punch = min((bc + d) * (hc + d), A_base)
    Vu_punch = max(0.0, Pu - q_neta * A_punch)
    ver_punch = phi_Vc_p >= Vu_punch - 1e-6

    # ---- Corte unidireccional ----
    sqfc  = math.sqrt(hormigon.fc)

    # dirección L: ancho de sección = B, voladizo - d
    brazo_L = L / 2.0 - hc / 2.0 - d
    Vu_1L   = max(0.0, q_neta * B * brazo_L) if brazo_L > 0 else 0.0
    phi_Vc_1L = PHI_CORTE * sqfc / 6.0 * B * d * 1000.0

    # dirección B: ancho de sección = L, voladizo - d
    brazo_B = B / 2.0 - bc / 2.0 - d
    Vu_1B   = max(0.0, q_neta * L * brazo_B) if brazo_B > 0 else 0.0
    phi_Vc_1B = PHI_CORTE * sqfc / 6.0 * L * d * 1000.0

    ver_1way = (phi_Vc_1L >= Vu_1L - 1e-6) and (phi_Vc_1B >= Vu_1B - 1e-6)

    # ---- Flexión dirección L ----
    l_v_L = (L - hc) / 2.0
    Mu_L  = q_neta * B * l_v_L ** 2 / 2.0
    sec_L = SeccionRectangular(
        b=B, h=h_f, recubrimiento=recubrimiento,
        hormigon=hormigon, acero=acero,
    )
    r_L      = dimensionar_flexion(sec_L, Mu=Mu_L)
    As_L     = r_L.As           # cm² total
    As_L_m   = As_L / B        # cm²/m
    phi_Mn_L = r_L.phi_Mn
    ver_flex_L = r_L.verifica

    # ---- Flexión dirección B ----
    l_v_B = (B - bc) / 2.0
    Mu_B  = q_neta * L * l_v_B ** 2 / 2.0
    sec_B = SeccionRectangular(
        b=L, h=h_f, recubrimiento=recubrimiento,
        hormigon=hormigon, acero=acero,
    )
    r_B      = dimensionar_flexion(sec_B, Mu=Mu_B)
    As_B     = r_B.As           # cm² total
    As_B_m   = As_B / L        # cm²/m
    phi_Mn_B = r_B.phi_Mn
    ver_flex_B = r_B.verifica

    # ---- Distribución transversal (art. 15.4.4.2) ----
    beta_losa = L / max(B, 1e-9)
    gamma_s   = 2.0 / (beta_losa + 1.0)   # fracción en la banda central
    As_banda  = gamma_s * As_B
    As_lat    = (1.0 - gamma_s) * As_B / 2.0   # cada franja lateral

    return ResultadoBase(
        B=B, L=L, h_f=h_f, d=d,
        bc=bc, hc=hc,
        Pu=Pu, P_s=P_s, q_adm=q_adm, q_neta=q_neta,
        q_servicio=q_serv, verifica_suelo=ver_suelo,
        bo=bo, Vu_punch=Vu_punch, Vc_punch=Vc_p, phi_Vc_punch=phi_Vc_p,
        verifica_punch=ver_punch,
        Vu_1way_L=Vu_1L, Vu_1way_B=Vu_1B,
        phi_Vc_1way_L=phi_Vc_1L, phi_Vc_1way_B=phi_Vc_1B,
        verifica_1way=ver_1way,
        l_v_L=l_v_L, Mu_L=Mu_L, As_L=As_L, As_L_m=As_L_m, phi_Mn_L=phi_Mn_L,
        verifica_flex_L=ver_flex_L,
        l_v_B=l_v_B, Mu_B=Mu_B, As_B=As_B, As_B_m=As_B_m, phi_Mn_B=phi_Mn_B,
        verifica_flex_B=ver_flex_B,
        gamma_s=gamma_s, As_banda_B=As_banda, As_lateral_B=As_lat,
    )


def _d_minimo_shear(
    bc: float, hc: float, B: float, L: float,
    Pu: float, hormigon: Hormigon, recubrimiento: float,
) -> float:
    """
    Encuentra el d mínimo que satisface punzonamiento y corte unidireccional,
    iterando de d=_PASO_D hasta un límite práctico.
    """
    q_neta = Pu / (B * L)

    for n in range(1, 400):
        d = n * _PASO_D
        if d + recubrimiento > min(B, L) / 2.0:
            break

        # Punzonamiento
        A_punch  = min((bc + d) * (hc + d), B * L)
        Vu_punch = max(0.0, Pu - q_neta * A_punch)
        phi_Vc_p = PHI_CORTE * Vc_punzonamiento(hormigon, bc, hc, d)
        if phi_Vc_p < Vu_punch - 1e-6:
            continue

        # Corte unidireccional (dir L y B)
        sqfc = math.sqrt(hormigon.fc)
        brazo_L  = L / 2.0 - hc / 2.0 - d
        Vu_1L    = max(0.0, q_neta * B * brazo_L) if brazo_L > 0 else 0.0
        phi_Vc_1L = PHI_CORTE * sqfc / 6.0 * B * d * 1000.0
        if phi_Vc_1L < Vu_1L - 1e-6:
            continue

        brazo_B  = B / 2.0 - bc / 2.0 - d
        Vu_1B    = max(0.0, q_neta * L * brazo_B) if brazo_B > 0 else 0.0
        phi_Vc_1B = PHI_CORTE * sqfc / 6.0 * L * d * 1000.0
        if phi_Vc_1B < Vu_1B - 1e-6:
            continue

        return d

    # Sin solución en el rango (sección inadecuada): devolver d grande para señalarlo
    return 0.90


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def dimensionar_base_centrada(
    bc:            float,
    hc:            float,
    Pu:            float,
    P_s:           float,
    q_adm:         float,
    hormigon:      Hormigon,
    acero:         Acero,
    h_f:           Optional[float] = None,
    recubrimiento: float = _REC_DEFAULT,
    cuadrada:      bool  = True,
    L_B_ratio:     float = 1.0,
) -> ResultadoBase:
    """
    Diseña una base aislada centrada.

    bc, hc:       dimensiones de la columna [m]
    Pu:           carga axial mayorada [kN]
    P_s:          carga de servicio (sin mayorar) [kN]  ← para dimensionar la planta
    q_adm:        presión admisible neta del suelo [kN/m²]
    h_f:          espesor de la base [m]; si None, se determina automáticamente
    cuadrada:     True → base cuadrada (B=L); False → rectangular según L_B_ratio
    L_B_ratio:    L/B para base rectangular (≥ 1)
    """
    # ---- Plan: dimensiones de la base ----
    A_req = P_s / q_adm   # m²

    if cuadrada:
        lado = max(math.sqrt(A_req), max(bc, hc) + 0.30)
        # Redondear hacia arriba al múltiplo de 0.05m más próximo
        lado = math.ceil(lado / 0.05) * 0.05
        B_calc, L_calc = lado, lado
    else:
        ratio = max(L_B_ratio, 1.0)
        # B × L = B × ratio·B = A_req → B = √(A_req/ratio)
        B_calc = max(math.sqrt(A_req / ratio), bc + 0.30)
        B_calc = math.ceil(B_calc / 0.05) * 0.05
        L_calc = math.ceil(B_calc * ratio / 0.05) * 0.05
        L_calc = max(L_calc, hc + 0.30)

    # Asegurar L ≥ B
    B_calc, L_calc = min(B_calc, L_calc), max(B_calc, L_calc)

    # ---- Espesor ----
    if h_f is None:
        d_calc = _d_minimo_shear(bc, hc, B_calc, L_calc, Pu, hormigon, recubrimiento)
        d_calc = max(d_calc, 0.15)
        h_f_calc = d_calc + recubrimiento
        # Redondear h_f hacia arriba al múltiplo de 0.05m
        h_f_calc = max(math.ceil(h_f_calc / 0.05) * 0.05, _H_F_MIN)
        d_use = h_f_calc - recubrimiento
    else:
        h_f_calc = max(h_f, _H_F_MIN)
        d_use    = h_f_calc - recubrimiento

    return _calcular_con_d(
        bc=bc, hc=hc, B=B_calc, L=L_calc, d=d_use,
        Pu=Pu, P_s=P_s, q_adm=q_adm,
        hormigon=hormigon, acero=acero, recubrimiento=recubrimiento,
    )


def verificar_base_centrada(
    bc:            float,
    hc:            float,
    B:             float,
    L:             float,
    h_f:           float,
    Pu:            float,
    P_s:           float,
    q_adm:         float,
    hormigon:      Hormigon,
    acero:         Acero,
    recubrimiento: float = _REC_DEFAULT,
) -> ResultadoBase:
    """
    Verifica una base centrada con geometría completamente especificada.
    """
    B_use, L_use = min(B, L), max(B, L)
    d = max(h_f, _H_F_MIN) - recubrimiento
    return _calcular_con_d(
        bc=bc, hc=hc, B=B_use, L=L_use, d=d,
        Pu=Pu, P_s=P_s, q_adm=q_adm,
        hormigon=hormigon, acero=acero, recubrimiento=recubrimiento,
    )
