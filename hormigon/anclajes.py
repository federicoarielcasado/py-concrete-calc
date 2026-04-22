"""
Anclajes y empalmes por adherencia — CIRSOC 201-2005, cap. 9 (art. 12).

Alcance:
  - Longitud de desarrollo en tracción: expresión general (art. 12.2.3).
  - Longitud de desarrollo en compresión (art. 12.3.2).
  - Longitud de desarrollo con gancho estándar en tracción (art. 12.5).
  - Empalmes por traslape: Clase A y Clase B (art. 12.15).
  - Longitudes mínimas absolutas.

Unidades: metros y MPa.
Factores de modificación por defecto: barras no recubiertas (ψe=1.0),
  hormigón de peso normal (λ=1.0), condición de colado inferior (ψt=1.0).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS


# ---------------------------------------------------------------------------
# Factores de modificación
# ---------------------------------------------------------------------------

def psi_t(barra_superior: bool) -> float:
    """ψt — factor de posición de colado (art. 12.2.4)."""
    return 1.3 if barra_superior else 1.0


def psi_e(recubierta_epoxi: bool) -> float:
    """ψe — factor de recubrimiento epóxico (art. 12.2.4)."""
    return 1.5 if recubierta_epoxi else 1.0


def psi_s(db_mm: float) -> float:
    """ψs — factor de tamaño de barra (art. 12.2.4)."""
    return 0.8 if db_mm <= 19.0 else 1.0


# ---------------------------------------------------------------------------
# Longitud de desarrollo en tracción (art. 12.2.3)
# ---------------------------------------------------------------------------

def ld_traccion(
    db_mm:            float,
    hormigon:         Hormigon,
    acero:            Acero,
    cb_mm:            float   = None,
    Ktr:              float   = 0.0,
    barra_superior:   bool    = False,
    recubierta_epoxi: bool    = False,
    lambda_horm:      float   = 1.0,
) -> float:
    """
    Longitud de desarrollo en tracción [m] (art. 12.2.3).

    db_mm:  diámetro de barra [mm]
    cb_mm:  recubrimiento al centro de la barra o semiespaciado entre barras [mm];
            si None, se usa 40mm (valor conservador)
    Ktr:    índice de armadura transversal = 40·Atr/(s·n) [mm];
            0 = conservador (sin contar estribos)
    lambda_horm: factor de peso del hormigón (1.0 normal, 0.75 leve)

    Retorna ld [m] ≥ max(300mm, 8db).
    """
    fy  = acero.fy
    fc  = hormigon.fc

    if cb_mm is None:
        cb_mm = 40.0   # valor conservador típico

    psi_t_v = psi_t(barra_superior)
    psi_e_v = psi_e(recubierta_epoxi)
    psi_s_v = psi_s(db_mm)

    # Producto ψt·ψe ≤ 1.7 (art. 12.2.4)
    psi_te = min(psi_t_v * psi_e_v, 1.7)

    # Cociente (cb + Ktr)/db, acotado a 2.5
    ratio = min((cb_mm + Ktr) / db_mm, 2.5)

    # Fórmula general (art. 12.2.3) — resultado en mm
    ld_mm = (3.0 * fy * psi_te * psi_s_v) / (40.0 * lambda_horm * math.sqrt(fc) * ratio) * db_mm

    # Mínimos absolutos
    ld_mm = max(ld_mm, 300.0, 8.0 * db_mm)

    return ld_mm / 1000.0   # m


# ---------------------------------------------------------------------------
# Longitud de desarrollo en compresión (art. 12.3.2)
# ---------------------------------------------------------------------------

def ldc_compresion(
    db_mm:        float,
    hormigon:     Hormigon,
    acero:        Acero,
    lambda_horm:  float = 1.0,
) -> float:
    """
    Longitud de desarrollo en compresión [m] (art. 12.3.2).

    ldc = max(0.24 × fy × db / (λ·√f'c), 0.044 × fy × db) ≥ 200mm
    """
    fy = acero.fy
    fc = hormigon.fc

    ldc1 = 0.24 * fy * db_mm / (lambda_horm * math.sqrt(fc))
    ldc2 = 0.044 * fy * db_mm
    ldc_mm = max(ldc1, ldc2, 200.0)

    return ldc_mm / 1000.0   # m


# ---------------------------------------------------------------------------
# Gancho estándar en tracción (art. 12.5)
# ---------------------------------------------------------------------------

def ldh_gancho(
    db_mm:            float,
    hormigon:         Hormigon,
    acero:            Acero,
    recubierta_epoxi: bool  = False,
    lambda_horm:      float = 1.0,
) -> float:
    """
    Longitud de desarrollo con gancho estándar en tracción [m] (art. 12.5.2).

    ldh = 0.24 × ψe × fy × db / (λ × √f'c) ≥ max(8db, 150mm)

    Aplica reducción por recubrimiento lateral ≥ 60mm y/o confinamiento
    (esas reducciones se pueden aplicar externamente multiplicando por el factor).
    """
    fy  = acero.fy
    fc  = hormigon.fc
    psi = psi_e(recubierta_epoxi)

    ldh_mm = 0.24 * psi * fy * db_mm / (lambda_horm * math.sqrt(fc))
    ldh_mm = max(ldh_mm, 8.0 * db_mm, 150.0)

    return ldh_mm / 1000.0   # m


# ---------------------------------------------------------------------------
# Empalmes por traslape en tracción (art. 12.15)
# ---------------------------------------------------------------------------

def ls_traslape(
    db_mm:            float,
    hormigon:         Hormigon,
    acero:            Acero,
    clase:            str   = "B",
    cb_mm:            float = None,
    Ktr:              float = 0.0,
    barra_superior:   bool  = False,
    recubierta_epoxi: bool  = False,
    lambda_horm:      float = 1.0,
) -> float:
    """
    Longitud de traslape por empalme en tracción [m] (art. 12.15.1).

    clase: "A" → ls = 1.0 × ld  |  "B" → ls = 1.3 × ld  (default = B)

    Clase A: As_prov/As_req ≥ 2 Y ≤ 50% de las barras empalman en la zona.
    Clase B: todos los demás casos.
    """
    ld = ld_traccion(
        db_mm=db_mm, hormigon=hormigon, acero=acero,
        cb_mm=cb_mm, Ktr=Ktr,
        barra_superior=barra_superior,
        recubierta_epoxi=recubierta_epoxi,
        lambda_horm=lambda_horm,
    )
    factor = 1.0 if clase.upper() == "A" else 1.3
    return max(factor * ld, 0.30)   # m, mínimo 300mm


# ---------------------------------------------------------------------------
# Tabla de longitudes para todas las barras comerciales
# ---------------------------------------------------------------------------

@dataclass
class TablaAnclajes:
    """Longitudes de desarrollo/empalme para todas las barras comerciales."""
    hormigon:    Hormigon
    acero:       Acero
    barra_sup:   bool  = False
    cb_mm_fijo:  float = 50.0    # recubrimiento al centro de barra [mm]
    Ktr:         float = 0.0
    lambda_horm: float = 1.0

    def ld(self, db_mm: float) -> float:
        return ld_traccion(db_mm, self.hormigon, self.acero,
                           cb_mm=self.cb_mm_fijo, Ktr=self.Ktr,
                           barra_superior=self.barra_sup,
                           lambda_horm=self.lambda_horm)

    def ldc(self, db_mm: float) -> float:
        return ldc_compresion(db_mm, self.hormigon, self.acero, self.lambda_horm)

    def ldh(self, db_mm: float) -> float:
        return ldh_gancho(db_mm, self.hormigon, self.acero,
                          lambda_horm=self.lambda_horm)

    def ls_B(self, db_mm: float) -> float:
        return ls_traslape(db_mm, self.hormigon, self.acero, "B",
                           cb_mm=self.cb_mm_fijo, Ktr=self.Ktr,
                           barra_superior=self.barra_sup,
                           lambda_horm=self.lambda_horm)

    def mostrar(self) -> None:
        print(f"{'φ[mm]':>7} {'ld[m]':>8} {'ldc[m]':>8} {'ldh[m]':>8} {'ls_B[m]':>9}")
        print("-" * 45)
        for d in DIAMETROS:
            print(
                f"{d:>7}  {self.ld(d):>7.2f}  {self.ldc(d):>7.2f}  "
                f"{self.ldh(d):>7.2f}  {self.ls_B(d):>8.2f}"
            )
