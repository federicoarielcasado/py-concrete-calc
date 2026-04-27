"""
Flexión simple — dimensionado y verificación (CIRSOC 201-2005, cap. 2).

Hipótesis:
  - Secciones controladas por tracción: εs ≥ 0.005 → φ = 0.90.
  - Bloque rectangular de tensiones (art. 10.2.7).
  - El hormigón no resiste tracciones (art. 10.2.5).
  - Adherencia perfecta acero–hormigón.

Unidades internas: kN y metros; tensiones en MPa (se convierten a kN/m² donde se
necesita operar con las otras unidades: 1 MPa = 1000 kN/m²).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from hormigon.materiales import Acero, Hormigon, BARRAS, DIAMETROS
from hormigon.secciones import SeccionRectangular, SeccionT


# ---------------------------------------------------------------------------
# Utilidades de cálculo
# ---------------------------------------------------------------------------

def phi_flexion(epsilon_s: float, epsilon_y: float, espiral: bool = False) -> float:
    """
    Coeficiente φ para flexión según tipo de rotura (art. 9.3.2.1).

    phi_min = 0.70 para espiral / 0.65 para estribos.
    """
    phi_min = 0.70 if espiral else 0.65
    if epsilon_s >= 0.005:
        return 0.90
    if epsilon_s <= epsilon_y:
        return phi_min
    return phi_min + (0.90 - phi_min) * (epsilon_s - epsilon_y) / (0.005 - epsilon_y)


def tipo_rotura(epsilon_s: float, epsilon_y: float) -> str:
    if epsilon_s >= 0.005:
        return "tracción"
    if epsilon_s <= epsilon_y:
        return "compresión"
    return "transición"


def ka_min(hormigon: Hormigon) -> float:
    """
    ka mínimo = As_min·fy/(fsc·b·d) — art. 10.5.1.

    Combina los dos criterios del reglamento (mayor de los dos).
    """
    fsc = hormigon.fsc
    fc = hormigon.fc
    return max(1.4 / fsc, 1.0 / (3.4 * math.sqrt(fc)))


def ka_max(hormigon: Hormigon) -> float:
    """ka máximo para φ = 0.90 (εs ≥ 0.005, c/d ≤ 0.375)."""
    return 0.375 * hormigon.beta1


def _tension_acero_comprimido(c: float, d_prima: float, acero: Acero) -> float:
    """
    Tensión en la armadura comprimida [MPa] a partir de la posición del eje neutro c [m].
    """
    if c <= d_prima:
        return 0.0
    eps_prima = 0.003 * (c - d_prima) / c
    return min(acero.fy, acero.Es * eps_prima)


def _ka_from_mn(mn: float) -> float:
    """ka = 1 – √(1 – 2·mn) ; mn = Mn/(fsc·b·d²)."""
    discriminant = 1.0 - 2.0 * mn
    if discriminant < 0:
        raise ValueError(
            f"mn = {mn:.4f} excede el máximo posible (≥ 0.5). "
            "La sección es insuficiente — aumente b o h."
        )
    return 1.0 - math.sqrt(discriminant)


# ---------------------------------------------------------------------------
# Objetos resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoFlexion:
    """Resultado completo de un cálculo de flexión simple."""

    # Solicitación
    Mu: float                        # [kNm]

    # Intermedios
    Mn: float                        # [kNm]  Mn = Mu / φ
    mn: float                        # adimensional
    ka: float                        # a/d (adimensional)
    ka_min: float                    # límite inferior
    ka_max: float                    # límite superior (εs ≥ 0.005)
    c: float                         # profundidad del eje neutro [m]
    a: float                         # profundidad del bloque de tensiones [m]
    epsilon_s: float                 # deformación en acero más traccionado

    # φ y resultado resistente
    phi: float
    phi_Mn: float                    # [kNm]
    verifica: bool
    tipo: str                        # "tracción" / "transición" / "compresión"

    # Armaduras de cálculo
    As: float                        # [cm²] — armadura traccionada calculada
    As_prima: float = 0.0            # [cm²] — armadura comprimida (0 si no se necesita)
    fs_prima: float = 0.0            # [MPa] — tensión en As'

    # Armadura adoptada (se llena al llamar a adoptar())
    phi_adoptado: Optional[int] = None
    n_barras: Optional[int] = None
    As_adoptada: Optional[float] = None    # [cm²]
    phi_adoptado_prima: Optional[int] = None
    n_barras_prima: Optional[int] = None
    As_adoptada_prima: Optional[float] = None

    def adoptar(self, phi: int, n: int, phi_prima: int = 0, n_prima: int = 0) -> ResultadoFlexion:
        """
        Registra la armadura adoptada. phi y phi_prima son diámetros en mm.
        Retorna self para encadenamiento.
        """
        self.phi_adoptado = phi
        self.n_barras = n
        self.As_adoptada = n * BARRAS[phi]
        if phi_prima and n_prima:
            self.phi_adoptado_prima = phi_prima
            self.n_barras_prima = n_prima
            self.As_adoptada_prima = n_prima * BARRAS[phi_prima]
        return self

    def graficar(self, seccion=None):
        """Dibuja la sección con la armadura. Requiere `seccion` como argumento."""
        from graficos.seccion_2d import graficar_seccion
        return graficar_seccion(seccion, resultado_flex=self)

    def mostrar(self) -> None:
        print(f"{'Mu':25s}: {self.Mu:10.2f} kNm")
        print(f"{'φ':25s}: {self.phi:.2f}  ({self.tipo})")
        print(f"{'Mn = Mu/φ':25s}: {self.Mn:10.2f} kNm")
        print(f"{'φ·Mn':25s}: {self.phi_Mn:10.2f} kNm  {'✓ verifica' if self.verifica else '✗ NO verifica'}")
        print(f"{'a (bloque tensiones)':25s}: {self.a*100:10.2f} cm")
        print(f"{'c (eje neutro)':25s}: {self.c*100:10.2f} cm")
        print(f"{'εs (acero)':25s}: {self.epsilon_s:.5f}")
        print(f"{'As calculada':25s}: {self.As:10.2f} cm²")
        if self.As_prima > 0:
            print(f"{'As\' comprimida':25s}: {self.As_prima:10.2f} cm²  (f's = {self.fs_prima:.0f} MPa)")
        if self.As_adoptada is not None:
            print(f"{'Armado tracción':25s}: {self.n_barras}φ{self.phi_adoptado} = {self.As_adoptada:.2f} cm²")
        if self.As_adoptada_prima is not None:
            print(f"{'Armado compresión':25s}: {self.n_barras_prima}φ{self.phi_adoptado_prima} = {self.As_adoptada_prima:.2f} cm²")


@dataclass
class VarianteFlexion:
    """Una combinación de barras válida para la armadura de tracción."""
    phi: int                   # diámetro [mm]
    n: int                     # número de barras
    As: float                  # área total [cm²]
    phi_Mn: float              # resistencia efectiva con esta armadura [kNm]
    Mu: float                  # solicitación de diseño [kNm]
    separacion: float          # separación libre entre barras [mm]
    capas: int = 1             # número de filas (1 o 2)
    rank: int = 0              # posición en el ranking (1 = más económica)

    @property
    def verifica(self) -> bool:
        return self.phi_Mn >= self.Mu

    def __str__(self) -> str:
        return (
            f"[{self.rank}] {self.n}φ{self.phi:2d}  As={self.As:.2f} cm²  "
            f"φMn={self.phi_Mn:.1f} kNm  s={self.separacion:.0f} mm"
        )


@dataclass
class ResultadoSetFlexion:
    """Conjunto de variantes válidas rankeadas por economía (mínima As)."""
    Mu: float
    As_requerida: float               # [cm²]
    variantes: list[VarianteFlexion] = field(default_factory=list)

    def graficar(self, n_mostrar: int = 8):
        """Gráfico comparativo de variantes rankeadas."""
        from graficos.diagramas import graficar_variantes_flexion
        return graficar_variantes_flexion(self, n_mostrar=n_mostrar)

    def mostrar(self) -> None:
        print(f"Mu = {self.Mu:.1f} kNm  |  As requerida = {self.As_requerida:.2f} cm²\n")
        print(f"{'Rank':<5} {'Barras':<10} {'As [cm²]':<10} {'φMn [kNm]':<12} {'s libre [mm]':<14}")
        print("-" * 53)
        for v in self.variantes:
            print(
                f"[{v.rank}]   {v.n}φ{v.phi:<6}  {v.As:<10.2f}  {v.phi_Mn:<12.1f}  {v.separacion:.0f}"
            )

    def adoptar(self, rank: int) -> VarianteFlexion:
        """Retorna la variante con el rank indicado."""
        for v in self.variantes:
            if v.rank == rank:
                return v
        raise ValueError(f"No existe variante con rank {rank}")


# ---------------------------------------------------------------------------
# Lógica principal — sección rectangular
# ---------------------------------------------------------------------------

def _dimensionar_rect_core(
    b: float, d: float, d_prima: float,
    hormigon: Hormigon, acero: Acero,
    Mu: float,
) -> dict:
    """
    Núcleo del dimensionado rectangular. Retorna dict con todos los valores
    intermedios. b y d en [m], Mu en [kNm].
    """
    fsc = hormigon.fsc         # [MPa]
    fy = acero.fy              # [MPa]
    beta1 = hormigon.beta1
    epsilon_u = hormigon.epsilon_u
    epsilon_y = acero.epsilon_y

    _ka_min = ka_min(hormigon)
    _ka_max = ka_max(hormigon)

    # Mn = Mu / φ_asumido. Se asume φ = 0.90 (sección controlada por tracción).
    phi_asumido = 0.90
    Mn = Mu / phi_asumido      # [kNm]

    # mn adimensional (fsc en kN/m² = fsc_MPa * 1000)
    fsc_kN = fsc * 1000.0
    mn = Mn / (fsc_kN * b * d ** 2)

    ka_calc = _ka_from_mn(mn)

    # Determinar región y armadura
    As_prima = 0.0
    fs_prima = 0.0

    if ka_calc <= _ka_min:
        # Cuantía mínima gobierna
        ka_usado = _ka_min
    elif ka_calc <= _ka_max:
        # Armadura simple
        ka_usado = ka_calc
    else:
        # Doble armadura
        ka_usado = _ka_max
        Mc = fsc_kN * b * d ** 2 * _ka_max * (1.0 - _ka_max / 2.0)   # [kNm]
        delta_Mn = Mn - Mc                                              # [kNm]

        c_max = _ka_max / beta1 * d
        fs_prima = _tension_acero_comprimido(c_max, d_prima, acero)     # [MPa]

        # As' = ΔMn / (f's · (d – d')) — conversión: [kNm / (MPa * m)] = [kNm / (kN/m² * 1000 * m)]
        As_prima_m2 = delta_Mn / (fs_prima * 1000.0 * (d - d_prima))   # [m²]
        As_prima = As_prima_m2 * 1e4                                     # [cm²]

    # Armadura de tracción
    a = ka_usado * d
    c = a / beta1
    epsilon_s = epsilon_u * (d - c) / c
    phi = phi_flexion(epsilon_s, epsilon_y)

    # As traccionada: de equilibrio T = C_hormigon + C_acero_comprimido
    As_m2 = fsc * 1000.0 * b * a / (fy * 1000.0)   # [m²]
    if As_prima > 0:
        As_m2 += As_prima / 1e4 * (fs_prima / fy)
    As = As_m2 * 1e4                                 # [cm²]

    phi_Mn = phi * fsc_kN * b * d ** 2 * ka_usado * (1.0 - ka_usado / 2.0)
    if As_prima > 0:
        phi_Mn = phi * (Mc + delta_Mn)

    return dict(
        Mn=Mn, mn=mn, ka=ka_usado, ka_min=_ka_min, ka_max=_ka_max,
        c=c, a=a, epsilon_s=epsilon_s, phi=phi, phi_Mn=phi_Mn,
        verifica=(phi_Mn >= Mu - 1e-9),
        tipo=tipo_rotura(epsilon_s, epsilon_y),
        As=As, As_prima=As_prima, fs_prima=fs_prima,
    )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def dimensionar_flexion(
    seccion: SeccionRectangular | SeccionT,
    Mu: float,
    d_prima: float | None = None,
) -> ResultadoFlexion:
    """
    Dimensiona la armadura de flexión simple dado Mu [kNm].

    Para secciones T, verifica si el eje neutro cae en el ala o en el alma
    y calcula en consecuencia.

    d_prima: distancia fibra comprimida → centroide As' [m].
             Si es None usa seccion.d_prima (o seccion.recubrimiento).
    """
    hormigon = seccion.hormigon
    acero = seccion.acero
    d = seccion.d

    if d_prima is None:
        d_prima = seccion.d_prima if hasattr(seccion, "d_prima") else seccion.recubrimiento

    if isinstance(seccion, SeccionT):
        return _dimensionar_T(seccion, Mu, d_prima)

    # Sección rectangular
    b = seccion.b
    r = _dimensionar_rect_core(b, d, d_prima, hormigon, acero, Mu)
    return ResultadoFlexion(Mu=Mu, **r)


def _dimensionar_T(
    seccion: SeccionT,
    Mu: float,
    d_prima: float,
) -> ResultadoFlexion:
    """Dimensionado para sección T. Detecta si NA está en ala o alma."""
    hormigon = seccion.hormigon
    acero = seccion.acero
    fsc = hormigon.fsc
    fy = acero.fy
    d = seccion.d
    bw = seccion.bw
    b = seccion.b_ala
    h_ala = seccion.h_ala

    _ka_min_val = ka_min(hormigon)
    _ka_max_val = ka_max(hormigon)

    # Paso 1: asumir NA en ala, calcular como rectangular con b = b_ala
    r = _dimensionar_rect_core(b, d, d_prima, hormigon, acero, Mu)

    ka_calculado = r["ka"]
    a_calculado = ka_calculado * d

    if a_calculado <= h_ala:
        # NA en ala: resultado ya es válido
        return ResultadoFlexion(Mu=Mu, **r)

    # NA en alma: separar contribución del ala y del alma
    fsc_kN = fsc * 1000.0
    fy_kN = fy * 1000.0

    Mn = Mu / 0.90   # [kNm], asumimos φ = 0.90

    # Aporte del ala (voladizos a ambos lados del alma)
    b_vuelo = b - bw
    Mnf = fsc_kN * b_vuelo * h_ala * (d - h_ala / 2.0)   # [kNm]
    Asf_m2 = fsc_kN * b_vuelo * h_ala / fy_kN             # [m²]
    Asf = Asf_m2 * 1e4                                      # [cm²]

    # Momento restante para el alma
    Mnw = Mn - Mnf   # [kNm]

    # Calcular ka del alma (sección rectangular de ancho bw)
    mn_w = Mnw / (fsc_kN * bw * d ** 2)
    ka_w = _ka_from_mn(mn_w)

    As_prima = 0.0
    fs_prima = 0.0

    if ka_w <= _ka_max_val:
        ka_usado = ka_w
    else:
        # Doble armadura en el alma
        ka_usado = _ka_max_val
        Mc_w = fsc_kN * bw * d ** 2 * _ka_max_val * (1.0 - _ka_max_val / 2.0)
        delta_Mn = Mnw - Mc_w
        c_max = _ka_max_val / hormigon.beta1 * d
        fs_prima = _tension_acero_comprimido(c_max, d_prima, acero)
        As_prima_m2 = delta_Mn / (fs_prima * 1000.0 * (d - d_prima))
        As_prima = As_prima_m2 * 1e4

    a_w = ka_usado * d
    c = a_w / hormigon.beta1
    epsilon_s = 0.003 * (d - c) / c
    phi = phi_flexion(epsilon_s, acero.epsilon_y)

    # As traccionada total = ala + alma
    As_alma_m2 = fsc_kN * bw * a_w / fy_kN
    if As_prima > 0:
        As_alma_m2 += As_prima / 1e4 * (fs_prima / fy)
    As_total = (Asf + As_alma_m2 * 1e4)

    # As mínima para T se verifica sobre bw
    As_min_m2 = _ka_min_val * (fsc_kN * bw * d / fy_kN)
    As_total = max(As_total, As_min_m2 * 1e4)

    phi_Mn = phi * (Mnf + fsc_kN * bw * d ** 2 * ka_usado * (1.0 - ka_usado / 2.0))

    # ka representativo para el resultado (a total / d, informativo)
    a_total_equiv = (Asf / 1e4 + As_alma_m2) * fy_kN / (fsc_kN * b)

    return ResultadoFlexion(
        Mu=Mu,
        Mn=Mn,
        mn=mn_w,
        ka=a_total_equiv / d,
        ka_min=_ka_min_val,
        ka_max=_ka_max_val,
        c=c,
        a=a_w,
        epsilon_s=epsilon_s,
        phi=phi,
        phi_Mn=phi_Mn,
        verifica=(phi_Mn >= Mu - 1e-9),
        tipo=tipo_rotura(epsilon_s, acero.epsilon_y),
        As=As_total,
        As_prima=As_prima,
        fs_prima=fs_prima,
    )


def verificar_flexion(
    seccion: SeccionRectangular | SeccionT,
    As: float,
    As_prima: float = 0.0,
    d_prima: float | None = None,
) -> ResultadoFlexion:
    """
    Dado As [cm²] (y opcionalmente As' [cm²]), calcula φMn.

    Itera para encontrar la posición del eje neutro cuando hay armadura comprimida.
    """
    hormigon = seccion.hormigon
    acero = seccion.acero
    d = seccion.d
    beta1 = hormigon.beta1
    fsc = hormigon.fsc
    fy = acero.fy
    fsc_kN = fsc * 1000.0
    fy_kN = fy * 1000.0
    epsilon_u = hormigon.epsilon_u

    if d_prima is None:
        d_prima = seccion.d_prima if hasattr(seccion, "d_prima") else seccion.recubrimiento

    # Ancho efectivo para la zona comprimida
    if isinstance(seccion, SeccionT):
        b = seccion.b_ala
        bw = seccion.bw
        h_ala = seccion.h_ala
    else:
        b = seccion.b
        bw = seccion.b
        h_ala = None

    As_m2 = As / 1e4
    As_prima_m2 = As_prima / 1e4

    if As_prima == 0.0:
        # Armadura simple — sin iteración
        a = As_m2 * fy_kN / (fsc_kN * b)
        if h_ala is not None and a > h_ala:
            # NA en alma — calcular a en alma con la parte del ala restada
            Cf = fsc_kN * (b - bw) * h_ala
            a = (As_m2 * fy_kN - Cf) / (fsc_kN * bw) + h_ala
        c = a / beta1
        epsilon_s = epsilon_u * (d - c) / c
        phi = phi_flexion(epsilon_s, acero.epsilon_y)
        fs_prima = 0.0
    else:
        # Armadura doble — iterar sobre posición del eje neutro
        c = (As_m2 - As_prima_m2) * fy_kN / (fsc_kN * b) / beta1
        for _ in range(20):
            a = beta1 * c
            fs_prima = _tension_acero_comprimido(c, d_prima, acero)
            T = As_m2 * fy_kN
            C_conc = fsc_kN * b * a
            C_acero = As_prima_m2 * (fs_prima - fsc) * 1000.0  # descuento el hormigón
            c_new = (T - C_acero) / (fsc_kN * b * beta1)
            if abs(c_new - c) < 1e-7:
                break
            c = c_new
        a = beta1 * c
        epsilon_s = epsilon_u * (d - c) / c
        phi = phi_flexion(epsilon_s, acero.epsilon_y)

    # Mn
    if isinstance(seccion, SeccionT) and (beta1 * c) > h_ala:
        a_eff = beta1 * c
        Mn = (
            fsc_kN * (b - bw) * h_ala * (d - h_ala / 2.0)
            + fsc_kN * bw * a_eff * (d - a_eff / 2.0)
        )
        if As_prima > 0:
            Mn += As_prima_m2 * (fs_prima - fsc) * 1000.0 * (d - d_prima)
    else:
        Mn = fsc_kN * b * a * (d - a / 2.0)
        if As_prima > 0:
            Mn += As_prima_m2 * (fs_prima - fsc) * 1000.0 * (d - d_prima)

    phi_Mn = phi * Mn
    _ka_min_val = ka_min(hormigon)
    _ka_max_val = ka_max(hormigon)
    ka_eff = a / d

    return ResultadoFlexion(
        Mu=phi_Mn,    # en verificación Mu ← φMn calculado
        Mn=Mn,
        mn=Mn / (fsc_kN * b * d ** 2),
        ka=ka_eff,
        ka_min=_ka_min_val,
        ka_max=_ka_max_val,
        c=c,
        a=a,
        epsilon_s=epsilon_s,
        phi=phi,
        phi_Mn=phi_Mn,
        verifica=True,
        tipo=tipo_rotura(epsilon_s, acero.epsilon_y),
        As=As,
        As_prima=As_prima,
        fs_prima=fs_prima if As_prima > 0 else 0.0,
    )


# ---------------------------------------------------------------------------
# Sistema de variantes
# ---------------------------------------------------------------------------

def _separacion_libre(n: int, phi_mm: int, b_m: float, recub_m: float, phi_estribo_mm: int = 8) -> float:
    """
    Separación libre entre barras en una capa [mm].
    Asume recubrimiento mecánico = recub_m, de donde el nominal es aprox.
    recub_m - phi_estribo/2000 - phi_mm/2000.
    """
    b_mm = b_m * 1000.0
    # Ancho disponible para barras: b - 2*(recub - estribo)
    recub_nominal_mm = recub_m * 1000.0 - phi_estribo_mm - phi_mm / 2.0
    ancho_barras = b_mm - 2.0 * (recub_nominal_mm + phi_estribo_mm)
    if n <= 1:
        return ancho_barras - phi_mm
    return (ancho_barras - n * phi_mm) / (n - 1)


def _separacion_minima(phi_mm: int, dmax_agregado_mm: int = 20) -> float:
    """Separación mínima libre entre barras [mm] (art. 7.6.1)."""
    return max(25.0, phi_mm, 4.0 / 3.0 * dmax_agregado_mm)


def dimensionar_flexion_variantes(
    seccion: SeccionRectangular | SeccionT,
    Mu: float,
    d_prima: float | None = None,
    phi_estribo_mm: int = 8,
    dmax_agregado_mm: int = 20,
) -> ResultadoSetFlexion:
    """
    Retorna todas las combinaciones de barras válidas, rankeadas por As ascendente.

    Solo válido para secciones rectangulares (en la dimensión de tracción).
    Para secciones T usa bw para la separación.
    """
    # Obtener la solución base (As requerida)
    res_base = dimensionar_flexion(seccion, Mu, d_prima)
    As_req = res_base.As

    b = seccion.bw if isinstance(seccion, SeccionT) else seccion.b
    recub = seccion.recubrimiento
    sep_min = _separacion_minima(max(DIAMETROS), dmax_agregado_mm)

    variantes: list[VarianteFlexion] = []

    for phi in DIAMETROS:
        area_barra = BARRAS[phi]   # [cm²]
        n_min = math.ceil(As_req / area_barra)
        if n_min < 2:
            n_min = 2

        sep_min_phi = _separacion_minima(phi, dmax_agregado_mm)

        for n in range(n_min, n_min + 4):   # explorar hasta 3 alternativas por diámetro
            As_var = n * area_barra
            sep = _separacion_libre(n, phi, b, recub, phi_estribo_mm)
            if sep < sep_min_phi:
                # No cabe en una capa — intentar 2 capas (n en 2 filas)
                n1 = math.ceil(n / 2)
                n2 = n - n1
                sep = _separacion_libre(max(n1, n2), phi, b, recub, phi_estribo_mm)
                capas = 2
            else:
                capas = 1

            if sep < sep_min_phi:
                break   # ninguna configuración de este φ cabe

            # Verificar con la sección real (puede diferir de seccion si d cambia en 2 capas)
            res_v = verificar_flexion(seccion, As_var, d_prima=d_prima)

            variantes.append(VarianteFlexion(
                phi=phi, n=n, As=As_var,
                phi_Mn=res_v.phi_Mn,
                Mu=Mu,
                separacion=sep,
                capas=capas,
            ))

    # Filtrar y rankear
    validas = [v for v in variantes if v.verifica and v.As >= As_req]
    validas.sort(key=lambda v: (v.As, v.phi))
    for i, v in enumerate(validas, 1):
        v.rank = i

    return ResultadoSetFlexion(
        Mu=Mu,
        As_requerida=As_req,
        variantes=validas,
    )
