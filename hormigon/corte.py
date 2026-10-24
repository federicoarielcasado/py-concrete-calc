"""
Corte en vigas de hormigón armado — CIRSOC 201-2005, cap. 3 (art. 11).

Hipótesis y alcance:
  - Elementos sin pretensado (hormigón armado convencional).
  - Expresiones simplificadas de Vc (art. 11.3.1.1) y opcionalmente la expresión
    afinada (art. 11.3.1.2), que requiere conocer Mu y Nu en la sección.
  - Estribos verticales y barras dobladas (art. 11.5).
  - Estribado mínimo (art. 11.5.6.3) y separación máxima (art. 11.5.5).

φ = 0.75 para corte (art. 9.3.2.3).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS
from hormigon.secciones import SeccionRectangular, SeccionT

PHI_CORTE = 0.75


# ---------------------------------------------------------------------------
# Vc — resistencia del hormigón al corte
# ---------------------------------------------------------------------------

def Vc_simplificado(hormigon: Hormigon, bw: float, d: float, Nu: float = 0.0,
                    Ag: float = 0.0) -> float:
    """
    Resistencia al corte del hormigón — expresión simplificada (art. 11.3.1.1/2/3).

    bw, d:  ancho del alma y altura útil [m]
    Nu:     fuerza axial mayorada [kN] (positivo = compresión, negativo = tracción)
    Ag:     área bruta de la sección [m²] (necesaria solo si Nu ≠ 0)

    Retorna Vc [kN].
    """
    fc = hormigon.fc
    sqrt_fc = math.sqrt(fc)           # [MPa^0.5]
    Vc_base = sqrt_fc / 6.0 * bw * d * 1000.0   # [kN]  (1 MPa·m² = 1000 kN)

    if Nu == 0.0 or Ag == 0.0:
        return Vc_base

    # Nu/Ag en MPa = kN/m² / 1000 → Nu[kN] / (Ag[m²] * 1000)
    sigma_Nu = Nu / (Ag * 1000.0)    # [MPa], positivo = compresión

    if Nu >= 0:
        # Compresión: art. 11.3.1.2
        factor = 1.0 + sigma_Nu / 14.0
    else:
        # Tracción: art. 11.3.1.3
        factor = 1.0 + 0.3 * sigma_Nu  # Nu negativo → factor < 1
        factor = max(factor, 0.0)

    return factor * Vc_base


def Vc_afinado(hormigon: Hormigon, acero: Acero,
               bw: float, d: float,
               Vu: float, Mu: float,
               As: float,
               Nu: float = 0.0, Ag: float = 0.0) -> float:
    """
    Resistencia al corte del hormigón — expresión afinada (art. 11.3.2.1).

    As:    área de armadura longitudinal traccionada [cm²]
    Vu:    corte mayorado en la sección [kN]
    Mu:    momento mayorado en la sección [kNm] (debe ser > 0)
    Nu:    fuerza axial [kN] (+ compresión)

    Retorna Vc [kN].
    """
    fc = hormigon.fc
    fy = acero.fy
    As_m2 = As / 1e4               # [m²]
    rho_w = As_m2 / (bw * d)      # cuantía geométrica

    # Relación Vu·d/Mu — limitada a 1.0 (art. 11.3.2.1)
    ratio = min(1.0, abs(Vu) * d / max(abs(Mu), 1e-9))

    sqrt_fc = math.sqrt(fc)
    # Tensión axial (MPa)
    sigma_Nu = Nu / (Ag * 1000.0) if Ag > 0 else 0.0

    # Fórmula art. 11.3.2.1 (unidades internas: MPa, m → resultado en MPa·m² = MN → x1000 = kN)
    Vc_MPa_m = (
        0.158 * sqrt_fc
        + 17.24 * rho_w * ratio
        + sigma_Nu / 6.0
    )
    Vc = Vc_MPa_m * bw * d * 1000.0   # [kN]

    # Límites (art. 11.3.2.1)
    Vc_min = Vc_simplificado(hormigon, bw, d, Nu, Ag) * 0.85
    Vc_max_formula = (
        0.290 * sqrt_fc + sigma_Nu / 6.0
    ) * bw * d * 1000.0

    return max(Vc_min, min(Vc, Vc_max_formula))


# ---------------------------------------------------------------------------
# Vs — resistencia de la armadura de corte
# ---------------------------------------------------------------------------

def Vs_estribos(Av_sobre_s: float, fyt: float, d: float) -> float:
    """
    Vs para estribos verticales (art. 11.5.7.2).

    Av_sobre_s: Av/s [mm²/m] — sección de estribo por unidad de longitud
    fyt:        tensión de fluencia de estribos [MPa]
    d:          altura útil [m]

    Retorna Vs [kN].
    """
    # Av/s [mm²/m] → [m²/m] = Av/s / 1e6
    # Vs = (Av/s) * fyt * d → [mm²/m * MPa * m] = [mm²·MPa/m·m] = [mm²·N/mm²] = [N] ... unidades
    # Mejor: Av/s [cm²/m] = Av_s_mm/100
    # Vs = (Av/s)[cm²/m] * fyt[kN/cm²] * d[m]
    # fyt [kN/cm²] = fyt_MPa * 0.1
    return (Av_sobre_s / 1e6) * (fyt * 1000.0) * d   # [kN]
    # = (mm²/m) / 1e6 * (MPa * 1000 kN/MN) * m
    # = (m²/m) * (kN/m²) * m = kN ✓


def Vs_barras_dobladas(Av_cm2: float, fy: float, alpha_deg: float = 45.0) -> float:
    """
    Vs para barras dobladas (art. 11.5.7.5).

    Av_cm2:    área total de barras dobladas que cruzan la fisura [cm²]
    fy:        tensión de fluencia [MPa]
    alpha_deg: ángulo de inclinación [°] (mínimo 30° por reglamento)

    Retorna Vs [kN].
    """
    if alpha_deg < 30.0:
        return 0.0
    alpha_rad = math.radians(alpha_deg)
    return Av_cm2 / 1e4 * fy * 1000.0 * math.sin(alpha_rad)   # [kN]


# ---------------------------------------------------------------------------
# Avs mínimo (art. 11.5.6.3)
# ---------------------------------------------------------------------------

def Avs_minimo(hormigon: Hormigon, acero: Acero, bw: float) -> float:
    """
    Sección mínima de estribos por unidad de longitud Av/s [mm²/m] (art. 11.5.6.3).

    bw: ancho del alma [m]
    """
    fc = hormigon.fc
    fyt = acero.fy                      # [MPa]
    bw_mm = bw * 1000.0                 # [mm]

    op1 = 0.33 * bw_mm / fyt * 1000.0  # [mm²/m]  (0.33 MPa^0.5 · bw / fyt → simplificado)
    op2 = math.sqrt(fc) / 16.0 * bw_mm / fyt * 1000.0  # [mm²/m]
    return max(op1, op2)


# ---------------------------------------------------------------------------
# Separación máxima de estribos (art. 11.5.5)
# ---------------------------------------------------------------------------

def s_maximo(hormigon: Hormigon, bw: float, d: float, Vs: float) -> float:
    """
    Separación máxima entre estribos [m] (art. 11.5.5.1 y 11.5.5.3).

    Vs: resistencia de la armadura de corte en la sección [kN]
    """
    fc = hormigon.fc
    limite_Vs = math.sqrt(fc) / 3.0 * bw * d * 1000.0   # [kN]
    if Vs <= limite_Vs:
        return min(d / 2.0, 0.40)
    else:
        return min(d / 4.0, 0.20)


# ---------------------------------------------------------------------------
# Límite de Vn (art. 11.5.7.9)
# ---------------------------------------------------------------------------

def Vn_maximo(hormigon: Hormigon, bw: float, d: float, Nu: float = 0.0,
              Ag: float = 0.0) -> float:
    """
    Resistencia nominal máxima Vn (art. 11.5.7.9 + 11.3.1.x).

    Vn ≤ (5 + Nu/(14·Ag)) · (√f'c/6) · bw · d
    """
    fc = hormigon.fc
    factor_Nu = 0.0
    if Ag > 0.0:
        factor_Nu = (Nu / (Ag * 1000.0)) / 14.0   # Nu/Ag en MPa
    return (5.0 + factor_Nu) * math.sqrt(fc) / 6.0 * bw * d * 1000.0   # [kN]


# ---------------------------------------------------------------------------
# Objetos resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoCorte:
    """Resultado de un cálculo de corte para una sección."""

    # Solicitación
    Vu: float                        # [kN]

    # Resistencias nominales
    Vc: float                        # [kN]
    Vs_requerido: float              # [kN]  Vs = Vn - Vc
    Vn: float                        # [kN]  Vc + Vs_est + Vs_45
    Vn_max: float                    # [kN]  límite art. 11.5.7.9
    phi_Vn: float                    # [kN]

    # Estribado calculado
    Avs_calculado: float             # [mm²/m]  Av/s requerido por Vs
    Avs_minimo: float                # [mm²/m]  mínimo reglamentario
    Avs_adoptado: float              # [mm²/m]  max(calculado, mínimo)
    s_maximo: float                  # [m]

    # Barras dobladas (opcionales)
    Vs_barras: float = 0.0           # [kN]

    # Estribado adoptado (se llena con adoptar())
    phi_estribo: Optional[int] = None   # [mm]
    n_ramas: Optional[int] = None
    s_adoptado: Optional[float] = None  # [m]
    Avs_real: Optional[float] = None    # [mm²/m]

    # Verificaciones
    verifica_resistencia: bool = True
    verifica_Vn_max: bool = True

    def adoptar(self, phi: int, n_ramas: int, s: float) -> ResultadoCorte:
        """
        Registra el estribado adoptado.
        phi: diámetro [mm], s: separación [m].
        """
        self.phi_estribo = phi
        self.n_ramas = n_ramas
        self.s_adoptado = s
        self.Avs_real = n_ramas * BARRAS[phi] * 100.0 / s   # [mm²/m]
        return self

    def graficar(self, seccion=None):
        """Dibuja la sección con el estribado. Requiere `seccion` como argumento."""
        from graficos.seccion_2d import graficar_seccion
        return graficar_seccion(seccion, resultado_corte=self)

    def mostrar(self) -> None:
        print(f"{'Vu':25s}: {self.Vu:10.2f} kN")
        print(f"{'Vc (hormigón)':25s}: {self.Vc:10.2f} kN")
        if self.Vs_barras > 0:
            print(f"{'Vs (barras dobladas)':25s}: {self.Vs_barras:10.2f} kN")
        print(f"{'Vs requerido (estribos)':25s}: {self.Vs_requerido:10.2f} kN")
        print(f"{'φ·Vn':25s}: {self.phi_Vn:10.2f} kN  {'✓' if self.verifica_resistencia else '✗'}")
        print(f"{'Vn_max (art.11.5.7.9)':25s}: {self.Vn_max:10.2f} kN  {'✓' if self.verifica_Vn_max else '✗'}")
        print(f"{'Av/s calculado':25s}: {self.Avs_calculado:10.1f} mm²/m")
        print(f"{'Av/s mínimo':25s}: {self.Avs_minimo:10.1f} mm²/m")
        print(f"{'Av/s adoptado':25s}: {self.Avs_adoptado:10.1f} mm²/m")
        print(f"{'s máximo':25s}: {self.s_maximo*100:10.1f} cm")
        if self.s_adoptado is not None:
            print(
                f"{'Estribado adoptado':25s}: "
                f"{self.n_ramas}φ{self.phi_estribo} c/{self.s_adoptado*100:.0f} cm  "
                f"(Av/s = {self.Avs_real:.0f} mm²/m)"
            )


@dataclass
class VarianteCorte:
    """Una combinación de estribo válida."""
    phi: int             # diámetro [mm]
    n_ramas: int
    s: float             # separación [m]
    Avs: float           # [mm²/m]
    phi_Vn: float        # [kN]
    Vu: float
    rank: int = 0

    @property
    def verifica(self) -> bool:
        return self.phi_Vn >= self.Vu

    def __str__(self) -> str:
        return (
            f"[{self.rank}] {self.n_ramas}φ{self.phi} c/{self.s*100:.0f}cm  "
            f"Av/s={self.Avs:.0f} mm²/m  φVn={self.phi_Vn:.1f} kN"
        )


@dataclass
class ResultadoSetCorte:
    """Variantes de estribado rankeadas por economía (menor Av/s = menos acero por metro)."""
    Vu: float
    Avs_requerido: float
    s_maximo: float
    variantes: list[VarianteCorte] = field(default_factory=list)

    def graficar(self, n_mostrar: int = 8):
        """Gráfico comparativo de variantes de estribado."""
        from graficos.diagramas import graficar_variantes_corte
        return graficar_variantes_corte(self, n_mostrar=n_mostrar)

    def mostrar(self) -> None:
        print(
            f"Vu = {self.Vu:.1f} kN  |  Av/s requerido = {self.Avs_requerido:.0f} mm²/m  "
            f"|  s_max = {self.s_maximo*100:.0f} cm\n"
        )
        print(f"{'Rank':<5} {'Estribo':<14} {'Av/s [mm²/m]':<15} {'s [cm]':<10} {'φVn [kN]'}")
        print("-" * 55)
        for v in self.variantes:
            print(
                f"[{v.rank}]   {v.n_ramas}φ{v.phi:<9}  {v.Avs:<15.0f}  "
                f"{v.s*100:<10.0f}  {v.phi_Vn:.1f}"
            )

    def adoptar(self, rank: int) -> VarianteCorte:
        for v in self.variantes:
            if v.rank == rank:
                return v
        raise ValueError(f"No existe variante con rank {rank}")


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_corte(
    seccion: SeccionRectangular | SeccionT,
    Vu: float,
    Vs_barras: float = 0.0,
    Nu: float = 0.0,
    expresion: str = "simplificada",
    As_long: float = 0.0,
    Mu: float = 0.0,
) -> ResultadoCorte:
    """
    Calcula el estribado necesario para resistir Vu [kN].

    Vu:         corte mayorado en la sección crítica [kN]
    Vs_barras:  aporte de barras dobladas ya calculado [kN] (si las hay)
    Nu:         fuerza axial mayorada [kN] (+ compresión, − tracción)
    expresion:  "simplificada" (art. 11.3.1.1) o "afinada" (art. 11.3.2.1)
    As_long:    armadura longitudinal traccionada [cm²] (solo para expr. afinada)
    Mu:         momento mayorado en la sección [kNm] (solo para expr. afinada)
    """
    hormigon = seccion.hormigon
    acero = seccion.acero
    d = seccion.d

    if isinstance(seccion, SeccionT):
        bw = seccion.bw
        Ag = seccion.Ag
    else:
        bw = seccion.b
        Ag = seccion.Ag

    # Vc
    if expresion == "afinada" and As_long > 0 and Mu > 0:
        Vc = Vc_afinado(hormigon, acero, bw, d, Vu, Mu, As_long, Nu, Ag)
    else:
        Vc = Vc_simplificado(hormigon, bw, d, Nu, Ag)

    # Vn máximo permitido
    vn_max = Vn_maximo(hormigon, bw, d, Nu, Ag)

    # Vn requerido
    Vn_req = Vu / PHI_CORTE

    # Vs requerido por estribos (descontando barras dobladas)
    Vs_req = max(0.0, Vn_req - Vc - Vs_barras)

    # Avs calculado [mm²/m]
    # Vs = Avs/1e6 * fyt*1000 * d → Avs = Vs * 1e6 / (fyt*1000*d) [mm²/m]
    fyt = acero.fy
    Avs_calc = Vs_req * 1e6 / (fyt * 1000.0 * d) if d > 0 else 0.0

    # Avs mínimo
    Avs_min = Avs_minimo(hormigon, acero, bw)

    # Avs adoptado
    Avs_adop = max(Avs_calc, Avs_min)

    # Vs efectivo con el Avs adoptado
    Vs_eff = Avs_adop / 1e6 * fyt * 1000.0 * d
    Vn_eff = Vc + Vs_eff + Vs_barras
    phi_Vn = PHI_CORTE * Vn_eff

    # Separación máxima
    s_max = s_maximo(hormigon, bw, d, Vs_eff)

    verifica_res = phi_Vn >= Vu
    verifica_max = Vn_req <= vn_max

    return ResultadoCorte(
        Vu=Vu,
        Vc=Vc,
        Vs_requerido=Vs_req,
        Vn=Vn_eff,
        Vn_max=vn_max,
        phi_Vn=phi_Vn,
        Avs_calculado=Avs_calc,
        Avs_minimo=Avs_min,
        Avs_adoptado=Avs_adop,
        s_maximo=s_max,
        Vs_barras=Vs_barras,
        verifica_resistencia=verifica_res,
        verifica_Vn_max=verifica_max,
    )


def calcular_corte_variantes(
    seccion: SeccionRectangular | SeccionT,
    Vu: float,
    Vs_barras: float = 0.0,
    Nu: float = 0.0,
    n_ramas: int = 2,
) -> ResultadoSetCorte:
    """
    Retorna variantes de estribado válidas, rankeadas por menor Av/s (menor peso de acero
    por metro de viga); a igual Av/s se prefiere la mayor separación.

    n_ramas: número de ramas del estribo (normalmente 2).
    """
    res = calcular_corte(seccion, Vu, Vs_barras, Nu)
    Avs_req = res.Avs_adoptado
    s_max = res.s_maximo
    d = seccion.d
    bw = seccion.bw if isinstance(seccion, SeccionT) else seccion.b
    hormigon = seccion.hormigon
    acero = seccion.acero
    fyt = acero.fy

    variantes: list[VarianteCorte] = []

    for phi in DIAMETROS:
        area_rama = BARRAS[phi]       # [cm²]
        # s requerido: Avs = n*A_cm2*100/s → s = n*A_cm2*100/Avs_req [m]
        if Avs_req > 0:
            s_req = n_ramas * area_rama * 100.0 / Avs_req   # [m]
        else:
            s_req = s_max

        s_req = min(s_req, s_max)

        # Redondear hacia abajo al cm más próximo
        s_usar = math.floor(s_req * 100) / 100.0

        if s_usar <= 0.05:   # separación mínima práctica 5 cm
            continue

        Avs_real = n_ramas * area_rama * 100.0 / s_usar   # [mm²/m]
        Vs_real = Avs_real / 1e6 * fyt * 1000.0 * d
        Vn_real = res.Vc + Vs_real + Vs_barras
        phi_Vn = PHI_CORTE * Vn_real

        variantes.append(VarianteCorte(
            phi=phi, n_ramas=n_ramas, s=s_usar,
            Avs=Avs_real, phi_Vn=phi_Vn, Vu=Vu,
        ))

    # También probar separaciones redondas (5, 10, 15, 20 cm) para cada diámetro
    for phi in DIAMETROS:
        area_rama = BARRAS[phi]
        for s_cm in [5, 10, 12, 15, 20, 25, 30]:
            s = s_cm / 100.0
            if s > s_max:
                continue
            Avs_real = n_ramas * area_rama * 100.0 / s
            if Avs_real < Avs_req:
                continue
            Vs_real = Avs_real / 1e6 * fyt * 1000.0 * d
            Vn_real = res.Vc + Vs_real + Vs_barras
            phi_Vn = PHI_CORTE * Vn_real
            variantes.append(VarianteCorte(
                phi=phi, n_ramas=n_ramas, s=s,
                Avs=Avs_real, phi_Vn=phi_Vn, Vu=Vu,
            ))

    # Filtrar válidas y eliminar duplicados (phi, s)
    validas = [v for v in variantes if v.verifica and v.s <= s_max]
    seen = set()
    unicas = []
    for v in validas:
        key = (v.phi, v.s)
        if key not in seen:
            seen.add(key)
            unicas.append(v)

    # Rankear por economía: menor Av/s (acero por metro); desempate por mayor separación
    unicas.sort(key=lambda v: (round(v.Avs, 1), -v.s, v.phi))
    for i, v in enumerate(unicas, 1):
        v.rank = i

    return ResultadoSetCorte(
        Vu=Vu,
        Avs_requerido=Avs_req,
        s_maximo=s_max,
        variantes=unicas,
    )
