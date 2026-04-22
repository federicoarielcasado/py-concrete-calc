"""
Torsión en secciones de hormigón armado — CIRSOC 201-2005, art. 11.6.

Hipótesis:
  - Secciones no pretensadas, rectangulares.
  - θ = 45° (art. 11.6.3.6 permite 30°–60°; se usa el valor simplificado).
  - Aoh y ph referidos al eje del estribo más exterior.
  - φ = 0.75 para torsión y combinación corte + torsión (art. 9.3.2.3).

Unidades: kN, metros, MPa (las tensiones se convierten internamente).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from hormigon.materiales import Acero, Hormigon
from hormigon.secciones import SeccionRectangular
from hormigon.corte import Vc_simplificado, PHI_CORTE

PHI_TORSION = 0.75


# ---------------------------------------------------------------------------
# Propiedades geométricas de torsión
# ---------------------------------------------------------------------------

def geometria_torsion(
    b: float,
    h: float,
    c_est: float,
) -> dict[str, float]:
    """
    Propiedades geométricas de la sección para torsión.

    b, h:   dimensiones brutas [m]
    c_est:  recubrimiento al eje del estribo (exterior de la sección) [m]

    Retorna dict con: Acp, pcp, Aoh, ph, Ao.
    """
    Acp = b * h
    pcp = 2.0 * (b + h)
    Aoh = (b - 2.0 * c_est) * (h - 2.0 * c_est)
    ph  = 2.0 * ((b - 2.0 * c_est) + (h - 2.0 * c_est))
    Ao  = 0.85 * Aoh
    return {"Acp": Acp, "pcp": pcp, "Aoh": Aoh, "ph": ph, "Ao": Ao}


# ---------------------------------------------------------------------------
# Umbrales de torsión (art. 11.6.1 y 11.6.2.2)
# ---------------------------------------------------------------------------

def Tu_umbral(
    hormigon: Hormigon,
    Acp:      float,
    pcp:      float,
) -> float:
    """
    Tu mínimo bajo el cual se puede ignorar la torsión (art. 11.6.1) [kNm].

    Tu_umbral = φ × (√f'c / 12) × (Acp² / pcp) × 1000
    """
    return PHI_TORSION * math.sqrt(hormigon.fc) / 12.0 * Acp ** 2 / pcp * 1000.0


def Tu_redistribucion(
    hormigon: Hormigon,
    Acp:      float,
    pcp:      float,
) -> float:
    """
    Tu máximo a usar cuando la torsión es de compatibilidad (art. 11.6.2.2) [kNm].

    Tu_red = φ × (√f'c / 3) × (Acp² / pcp) × 1000  = 4 × Tu_umbral
    """
    return PHI_TORSION * math.sqrt(hormigon.fc) / 3.0 * Acp ** 2 / pcp * 1000.0


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoTorsion:
    """Resultado del diseño de armadura de torsión + corte combinados."""

    # Solicitaciones
    Tu: float   # kNm
    Vu: float   # kN

    # Propiedades geométricas
    Acp: float
    pcp: float
    Aoh: float
    ph:  float
    Ao:  float

    # Umbrales
    Tu_umbral:    float   # kNm — mínimo a partir del cual es necesaria armadura
    Tu_red:       float   # kNm — máximo para torsión de compatibilidad
    despreciable: bool    # True si Tu < Tu_umbral

    # Resistencia del hormigón al corte
    Vc: float        # kN
    phi_Vc: float    # kN

    # Comprobación combinada corte + torsión (art. 11.6.3.1)
    tau_combinado: float   # MPa — lado izquierdo de la desigualdad
    tau_limite:    float   # MPa — lado derecho (φ × (Vc/bw·d + 2√f'c/3))
    verifica_combinado: bool

    # Armadura transversal por torsión
    At_s: float       # mm²/m  Av_torsion / s (por rama del estribo)
    Av_s: float       # mm²/m  Av_corte / s  (por rama, para 2 ramas)
    Avt_s: float      # mm²/m  At_s + Av_s  (total requerido por rama)
    theta_deg: float  # grados

    # Armadura longitudinal por torsión (art. 11.6.3.7)
    Al: float        # cm²  total en la sección
    Al_min: float    # cm²  mínimo reglamentario

    # Verificación final
    verifica: bool

    def mostrar(self) -> None:
        print(f"{'Tu':30s}: {self.Tu:.2f} kNm  "
              f"(umbral={self.Tu_umbral:.2f}  "
              f"{'→ DESPRECIABLE' if self.despreciable else '→ DISEÑAR'})")
        print(f"{'Vu':30s}: {self.Vu:.1f} kN")
        print(f"{'Aoh':30s}: {self.Aoh*1e4:.0f} cm²  ph={self.ph*100:.0f} cm")
        print(f"{'Corte+torsión':30s}: {self.tau_combinado:.3f} MPa  "
              f"≤ {self.tau_limite:.3f} MPa  {'✓' if self.verifica_combinado else '✗'}")
        print(f"{'At/s (torsión)':30s}: {self.At_s:.0f} mm²/m")
        print(f"{'Av/s (corte, c/rama)':30s}: {self.Av_s:.0f} mm²/m")
        print(f"{'Avt/s total/rama':30s}: {self.Avt_s:.0f} mm²/m")
        print(f"{'Al longitudinal':30s}: {self.Al:.2f} cm²  (mín={self.Al_min:.2f})")


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_torsion(
    seccion:    SeccionRectangular,
    Tu:         float,
    Vu:         float,
    c_est:      float,
    theta_deg:  float = 45.0,
    equilibrio: bool  = True,
) -> ResultadoTorsion:
    """
    Dimensiona la armadura de torsión + corte combinados.

    seccion:    sección rectangular (se usan b, h, hormigon, acero)
    Tu:         torsión de diseño [kNm]
    Vu:         corte de diseño [kN]
    c_est:      recubrimiento al centroide del estribo (ext. → eje) [m]
    theta_deg:  ángulo de bielas comprimidas [°] (30–60; default 45°)
    equilibrio: True = torsión de equilibrio (no se redistribuye);
                False = compatibilidad (se limita Tu a Tu_red)
    """
    b  = seccion.b
    h  = seccion.h
    d  = seccion.d
    bw = b
    hormigon = seccion.hormigon
    acero    = seccion.acero
    fc       = hormigon.fc
    fyt      = acero.fy
    fy       = acero.fy

    geom = geometria_torsion(b, h, c_est)
    Acp  = geom["Acp"]
    pcp  = geom["pcp"]
    Aoh  = geom["Aoh"]
    ph   = geom["ph"]
    Ao   = geom["Ao"]

    Tu_umb  = Tu_umbral(hormigon, Acp, pcp)
    Tu_red  = Tu_redistribucion(hormigon, Acp, pcp)
    desp    = Tu < Tu_umb

    # Si es de compatibilidad, limitar Tu
    Tu_dis = Tu if equilibrio else min(Tu, Tu_red)

    # Vc nominal
    Vc    = Vc_simplificado(hormigon, bw, d)
    phi_Vc = PHI_CORTE * Vc

    # ---- Comprobación combinada corte + torsión (art. 11.6.3.1) ----
    # τ_v [MPa]
    tau_v  = Vu / (bw * d * 1000.0)
    # τ_t [MPa]: Tu × ph / (1.7 × Aoh²) / 1000
    tau_t  = Tu_dis * ph / (1.7 * Aoh ** 2 * 1000.0)
    tau_iz = math.sqrt(tau_v ** 2 + tau_t ** 2)

    # Límite derecho: φ(Vc/(bw·d) + 2√f'c/3) [MPa]
    tau_lim = PHI_TORSION * (math.sqrt(fc) / 6.0 + 2.0 * math.sqrt(fc) / 3.0)
    ver_comb = tau_iz <= tau_lim + 1e-9

    theta_rad = math.radians(theta_deg)
    cot_theta = math.cos(theta_rad) / math.sin(theta_rad)

    # ---- Armadura transversal por torsión ----
    # At/s [mm²/m] = Tu_dis × 1000 / (φ × 2 × Ao × fyt × cot(θ))
    # (deducción en la docstring del módulo)
    if not desp:
        At_s = Tu_dis * 1000.0 / (PHI_TORSION * 2.0 * Ao * fyt * cot_theta)
    else:
        At_s = 0.0

    # ---- Av/s por corte (por rama, 2 ramas) ----
    Vn_req = max(0.0, Vu / PHI_CORTE - Vc)
    Av_s   = Vn_req * 1e6 / (fyt * 1000.0 * d) / 2.0 if d > 0 else 0.0  # por rama

    # Total por rama (estribos cerrados)
    Avt_s = At_s + Av_s

    # Mínimo (art. 11.6.5.2): At/s ≥ 0.175 × bw / fyt
    At_s_min = 0.175 * bw * 1000.0 / fyt   # [mm²/m]
    At_s_use = max(At_s, At_s_min) if not desp else 0.0

    # ---- Armadura longitudinal (art. 11.6.3.7) ----
    # Al [cm²] = (At/s) [mm²/m] × ph [m] × (fyt/fy) / 100  (de mm² → cm²)
    Al = At_s_use * ph * (fyt / fy) / 100.0

    # Al mínimo (art. 11.6.5.3)
    At_s_lim = max(At_s_use, 0.175 * bw * 1000.0 / fyt)
    Al_min   = max(
        (0.42 * math.sqrt(fc) * Acp * 1e4 / fy) - At_s_lim * ph * fyt / (fy * 100.0),
        0.42 * math.sqrt(fc) * Acp * 1e4 / fy * 0.2,   # piso: 20% del primer término
    )
    Al       = max(Al, Al_min)

    return ResultadoTorsion(
        Tu=Tu, Vu=Vu,
        Acp=Acp, pcp=pcp, Aoh=Aoh, ph=ph, Ao=Ao,
        Tu_umbral=Tu_umb, Tu_red=Tu_red, despreciable=desp,
        Vc=Vc, phi_Vc=phi_Vc,
        tau_combinado=tau_iz, tau_limite=tau_lim, verifica_combinado=ver_comb,
        At_s=At_s_use, Av_s=Av_s, Avt_s=Avt_s,
        theta_deg=theta_deg,
        Al=Al, Al_min=Al_min,
        verifica=ver_comb,
    )
