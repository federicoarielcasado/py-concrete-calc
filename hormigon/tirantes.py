"""
Tirantes (elementos en tracción pura) — CIRSOC 201-2005.

Alcance:
  - Elementos cargados axialmente en tracción (tiras, tirantes de pórtico,
    elementos de tracción en modelos biela-tirante).
  - Resistencia nominal: φTn = φ × As × fy  (φ = 0.90, art. 9.3.2.1).
  - Control de fisuras (art. 10.6.4): separación máxima de barras.
  - Armadura mínima por tracción directa (art. 10.9.1 no aplica;
    se usa criterio de cuantía mínima ρ ≥ As_min / Ag).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS

PHI_TRACCION = 0.90


# ---------------------------------------------------------------------------
# Control de fisuras (art. 10.6.4)
# ---------------------------------------------------------------------------

def s_max_fisuras(
    acero:  Acero,
    cc_mm:  float,
    fs:     float = None,
) -> float:
    """
    Separación máxima de barras para control de fisuras [mm] (art. 10.6.4).

    cc_mm: recubrimiento libre (exterior de barra a cara de hormigón) [mm]
    fs:    tensión de servicio en el acero [MPa]; si None, se usa 2/3 × fy

    s ≤ min(380×(280/fs) - 2.5·cc, 300×(280/fs)) [mm]
    """
    if fs is None:
        fs = 2.0 / 3.0 * acero.fy
    s1 = 380.0 * (280.0 / fs) - 2.5 * cc_mm
    s2 = 300.0 * (280.0 / fs)
    return min(s1, s2)


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoTirante:
    """Resultado del dimensionado o verificación de un tirante."""

    Tu:      float   # kN — tracción de diseño
    As:      float   # cm² — área de armadura calculada
    phi_Tn:  float   # kN — resistencia de diseño
    verifica: bool   # φTn ≥ Tu

    # Control de fisuras
    cc_mm:        float          # mm — recubrimiento libre
    s_max_fis_mm: float          # mm — separación máxima para control de fisuras
    fs_servicio:  float          # MPa — tensión de servicio (2/3 fy por defecto)

    # Adoptado
    phi_barra:   Optional[int]   = None
    n_barras:    Optional[int]   = None
    As_real:     Optional[float] = None   # cm²
    s_barras_mm: Optional[float] = None   # mm — separación real (para verificar fisuras)
    verifica_fisuras: Optional[bool] = None

    def adoptar(self, phi: int, n_barras: int, ancho_mm: float) -> ResultadoTirante:
        """
        Registra la armadura adoptada y verifica la separación para fisuras.

        ancho_mm: ancho total del elemento [mm] (para calcular la separación)
        """
        self.phi_barra = phi
        self.n_barras  = n_barras
        self.As_real   = n_barras * BARRAS[phi]
        db_mm          = float(phi)
        # s libre = (ancho - 2·cc - n·db) / (n-1) para n>1
        if n_barras > 1:
            s_total = ancho_mm - 2.0 * self.cc_mm - n_barras * db_mm
            self.s_barras_mm = s_total / (n_barras - 1)
        else:
            self.s_barras_mm = ancho_mm - 2.0 * self.cc_mm - db_mm
        self.verifica_fisuras = self.s_barras_mm <= self.s_max_fis_mm + 1e-6
        return self

    def mostrar(self) -> None:
        ok = "✓" if self.verifica else "✗"
        print(f"{'Tu':<30}: {self.Tu:.1f} kN")
        print(f"{'As calculada':<30}: {self.As:.2f} cm²")
        print(f"{'φ·Tn':<30}: {self.phi_Tn:.1f} kN  {ok}")
        print(f"{'s_max fisuras':<30}: {self.s_max_fis_mm:.0f} mm  "
              f"(fs={self.fs_servicio:.0f} MPa, cc={self.cc_mm:.0f} mm)")
        if self.s_barras_mm is not None:
            ok_f = "✓" if self.verifica_fisuras else "✗"
            print(f"{'s_adoptada':<30}: {self.s_barras_mm:.0f} mm  {ok_f}")
        if self.As_real is not None:
            print(f"{'Adoptado':<30}: {self.n_barras}φ{self.phi_barra}  "
                  f"As_real={self.As_real:.2f} cm²")


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def dimensionar_tirante(
    Tu:   float,
    acero: Acero,
    cc_mm: float = 25.0,
) -> ResultadoTirante:
    """
    Dimensiona la armadura de un tirante para Tu [kN].

    Tu:    tracción de diseño (mayorada) [kN]
    acero: acero longitudinal
    cc_mm: recubrimiento libre a la cara de la barra [mm]
    """
    fy = acero.fy
    As_m2 = Tu / (PHI_TRACCION * fy * 1000.0)   # m²
    As_cm2 = As_m2 * 1e4                          # cm²
    phi_Tn = PHI_TRACCION * As_cm2 / 1e4 * fy * 1000.0  # kN

    fs_serv    = 2.0 / 3.0 * fy
    s_max_fis  = s_max_fisuras(acero, cc_mm, fs_serv)

    return ResultadoTirante(
        Tu=Tu, As=As_cm2, phi_Tn=phi_Tn, verifica=(phi_Tn >= Tu - 1e-9),
        cc_mm=cc_mm, s_max_fis_mm=s_max_fis, fs_servicio=fs_serv,
    )


def verificar_tirante(
    Tu:    float,
    As:    float,
    acero: Acero,
    cc_mm: float = 25.0,
) -> ResultadoTirante:
    """
    Verifica un tirante con área de acero dada As [cm²].
    """
    fy     = acero.fy
    phi_Tn = PHI_TRACCION * As / 1e4 * fy * 1000.0

    fs_serv   = 2.0 / 3.0 * fy
    s_max_fis = s_max_fisuras(acero, cc_mm, fs_serv)

    return ResultadoTirante(
        Tu=Tu, As=As, phi_Tn=phi_Tn, verifica=(phi_Tn >= Tu - 1e-9),
        cc_mm=cc_mm, s_max_fis_mm=s_max_fis, fs_servicio=fs_serv,
    )


def dimensionar_tirante_variantes(
    Tu:    float,
    acero: Acero,
    cc_mm: float = 25.0,
) -> list[dict]:
    """
    Retorna todas las combinaciones de barras que verifican φTn ≥ Tu,
    rankeadas por mínima As (economía).

    Cada item: {"rank", "phi_mm", "n", "As", "phi_Tn"}
    """
    base = dimensionar_tirante(Tu, acero, cc_mm)
    As_req = base.As

    variantes = []
    for phi_d in DIAMETROS:
        area = BARRAS[phi_d]
        n_min = math.ceil(As_req / area)
        for n in range(max(1, n_min), n_min + 6):
            As_tot = n * area
            phi_Tn = PHI_TRACCION * As_tot / 1e4 * acero.fy * 1000.0
            if phi_Tn >= Tu - 1e-9:
                variantes.append({
                    "phi_mm": phi_d, "n": n,
                    "As": As_tot, "phi_Tn": phi_Tn,
                })

    # Eliminar duplicados As idénticas, rankear por mínima As
    seen = set()
    unicas = []
    for v in variantes:
        key = (v["phi_mm"], v["n"])
        if key not in seen:
            seen.add(key)
            unicas.append(v)

    unicas.sort(key=lambda v: (v["As"], v["phi_mm"]))
    for i, v in enumerate(unicas, 1):
        v["rank"] = i

    return unicas
