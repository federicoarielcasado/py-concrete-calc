"""
Método Bielas y Tirantes (strut-and-tie) — CIRSOC 201-2005, art. 10.7.

Alcance:
  - Regiones con discontinuidades (D-regions): ménsulas cortas, zonas bajo
    cargas concentradas, apoyos directos, zonas de anclaje, etc.
  - Modelo de celosía equivalente: bielas comprimidas + tirantes de acero.
  - Dimensionado de tirantes: As = Tu / (φ × fy).
  - Verificación de tensiones en bielas: σ ≤ fce = 0.85 × β_s × f'c.
  - Verificación de tensiones en nudos: σ ≤ fnn = 0.85 × β_n × f'c.

Convenciones de unidades: kN y metros; MPa para tensiones.

Factores β_s (art. 10.7.3.2):
  - Biela prismática (no atravesada por armadura de tracción): β_s = 1.00
  - Biela en abanico o botella con refuerzo transversal:        β_s = 0.75
  - Biela en abanico o botella sin refuerzo transversal:        β_s = 0.60
  - Biela con armadura longitudinal de tracción en su interior: β_s = 0.40

Factores β_n (art. 10.7.4.2):
  - Nudo C-C-C (solo bielas comprimidas):                β_n = 1.00
  - Nudo C-C-T (una tracción entrante):                  β_n = 0.80
  - Nudo C-T-T (dos o más tracciones entrantes):         β_n = 0.60

φ = 0.75 para toda la verificación biela-tirante (art. 9.3.2.6).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from hormigon.materiales import Acero, Hormigon

PHI_BT = 0.75   # factor φ global para biela-tirante (art. 9.3.2.6)


# ---------------------------------------------------------------------------
# Nodo del modelo (punto de aplicación de fuerza o intersección de miembros)
# ---------------------------------------------------------------------------

@dataclass
class Nodo:
    """Coordenadas 2D de un nodo en el modelo biela-tirante [m]."""
    nombre: str
    x: float   # m
    y: float   # m


# ---------------------------------------------------------------------------
# Miembro: biela o tirante
# ---------------------------------------------------------------------------

@dataclass
class Biela:
    """
    Biela comprimida definida por dos nodos y el ancho de la zona de apoyo.

    nodo_a, nodo_b: nombres de los nodos extremos
    fuerza:         fuerza axial de compresión [kN] (valor positivo)
    ancho_mm:       ancho de la biela en la sección crítica [mm]
    espesor_mm:     espesor del elemento (profundidad fuera del plano) [mm]
    beta_s:         factor de eficiencia de la biela (art. 10.7.3.2)
    """
    nodo_a:      str
    nodo_b:      str
    fuerza:      float   # kN
    ancho_mm:    float   # mm — ancho en sección crítica
    espesor_mm:  float   # mm — espesor fuera del plano
    beta_s:      float = 1.00

    @property
    def area_mm2(self) -> float:
        return self.ancho_mm * self.espesor_mm

    def tension_mpa(self) -> float:
        """Tensión de compresión actuante [MPa]."""
        return self.fuerza * 1000.0 / self.area_mm2   # kN → N

    def fce(self, hormigon: Hormigon) -> float:
        """Resistencia efectiva de la biela fce = 0.85 × β_s × f'c [MPa]."""
        return 0.85 * self.beta_s * hormigon.fc

    def phi_fce(self, hormigon: Hormigon) -> float:
        return PHI_BT * self.fce(hormigon)

    def verifica(self, hormigon: Hormigon) -> bool:
        return self.tension_mpa() <= self.phi_fce(hormigon) + 1e-9


@dataclass
class Tirante:
    """
    Tirante de acero definido por dos nodos.

    nodo_a, nodo_b: nombres de los nodos extremos
    fuerza:         fuerza axial de tracción [kN]
    acero:          material del acero
    """
    nodo_a:  str
    nodo_b:  str
    fuerza:  float   # kN
    acero:   Acero

    @property
    def As_req(self) -> float:
        """Área de acero requerida [cm²]."""
        return self.fuerza / (PHI_BT * self.acero.fy * 1000.0) * 1e4

    def verifica_As(self, As_prov: float) -> bool:
        """Verifica que el área provista As_prov [cm²] sea suficiente."""
        return As_prov >= self.As_req - 1e-9


# ---------------------------------------------------------------------------
# Verificación de nudo (art. 10.7.4)
# ---------------------------------------------------------------------------

@dataclass
class VerificacionNudo:
    """Resultado de verificación de un nudo."""
    nombre:       str
    tipo:         str    # "CCC", "CCT", "CTT"
    beta_n:       float
    tension_mpa:  float  # MPa actuante en la cara más cargada
    phi_fnn_mpa:  float  # φ × 0.85 × β_n × f'c [MPa]
    verifica:     bool


def beta_n(tipo_nudo: str) -> float:
    """
    Factor β_n según tipo de nudo (art. 10.7.4.2).

    tipo_nudo: "CCC", "CCT" o "CTT"
    """
    tipos = {"CCC": 1.00, "CCT": 0.80, "CTT": 0.60}
    t = tipo_nudo.upper()
    if t not in tipos:
        raise ValueError(f"tipo_nudo debe ser 'CCC', 'CCT' o 'CTT'; se recibió '{tipo_nudo}'")
    return tipos[t]


def verificar_nudo(
    nombre:      str,
    tipo:        str,
    hormigon:    Hormigon,
    fuerza_kN:   float,
    area_nudo_mm2: float,
) -> VerificacionNudo:
    """
    Verifica la tensión en un nudo.

    fuerza_kN:     fuerza mayor que entra al nudo [kN]
    area_nudo_mm2: área de la cara del nudo perpendicular a la fuerza [mm²]
    """
    bn  = beta_n(tipo)
    fnn = 0.85 * bn * hormigon.fc          # MPa
    phi_fnn = PHI_BT * fnn                 # MPa
    sigma   = fuerza_kN * 1000.0 / area_nudo_mm2   # MPa
    return VerificacionNudo(
        nombre=nombre, tipo=tipo, beta_n=bn,
        tension_mpa=sigma, phi_fnn_mpa=phi_fnn,
        verifica=(sigma <= phi_fnn + 1e-9),
    )


# ---------------------------------------------------------------------------
# Modelo completo biela-tirante
# ---------------------------------------------------------------------------

@dataclass
class ModeloBielaTirante:
    """
    Colección de nodos, bielas y tirantes que forman el modelo.

    Uso:
        m = ModeloBielaTirante()
        m.agregar_nodo("A", x=0.0, y=0.0)
        m.agregar_nodo("B", x=1.0, y=0.5)
        m.agregar_biela("A", "B", fuerza=200.0, ancho_mm=150, espesor_mm=300)
        m.agregar_tirante("A", "C", fuerza=100.0, acero=acero)
        res = m.verificar(hormigon)
    """
    nodos:    dict[str, Nodo]    = field(default_factory=dict)
    bielas:   list[Biela]        = field(default_factory=list)
    tirantes: list[Tirante]      = field(default_factory=list)

    def agregar_nodo(self, nombre: str, x: float, y: float) -> None:
        self.nodos[nombre] = Nodo(nombre=nombre, x=x, y=y)

    def agregar_biela(
        self,
        nodo_a: str,
        nodo_b: str,
        fuerza: float,
        ancho_mm: float,
        espesor_mm: float,
        beta_s: float = 1.00,
    ) -> None:
        self.bielas.append(Biela(
            nodo_a=nodo_a, nodo_b=nodo_b,
            fuerza=fuerza, ancho_mm=ancho_mm, espesor_mm=espesor_mm,
            beta_s=beta_s,
        ))

    def agregar_tirante(
        self,
        nodo_a: str,
        nodo_b: str,
        fuerza: float,
        acero:  Acero,
    ) -> None:
        self.tirantes.append(Tirante(
            nodo_a=nodo_a, nodo_b=nodo_b,
            fuerza=fuerza, acero=acero,
        ))

    def longitud(self, nodo_a: str, nodo_b: str) -> float:
        """Longitud entre dos nodos [m]."""
        na = self.nodos[nodo_a]
        nb = self.nodos[nodo_b]
        return math.sqrt((nb.x - na.x) ** 2 + (nb.y - na.y) ** 2)

    def verificar(self, hormigon: Hormigon) -> ResultadoModeloBT:
        res_bielas   = [
            ResultadoBiela(
                nodo_a=b.nodo_a, nodo_b=b.nodo_b,
                fuerza=b.fuerza, beta_s=b.beta_s,
                tension_mpa=b.tension_mpa(),
                fce_mpa=b.fce(hormigon),
                phi_fce_mpa=b.phi_fce(hormigon),
                verifica=b.verifica(hormigon),
            )
            for b in self.bielas
        ]
        res_tirantes = [
            ResultadoTiranteBT(
                nodo_a=t.nodo_a, nodo_b=t.nodo_b,
                fuerza=t.fuerza, As_req=t.As_req,
            )
            for t in self.tirantes
        ]
        verifica_global = all(r.verifica for r in res_bielas)
        return ResultadoModeloBT(
            res_bielas=res_bielas,
            res_tirantes=res_tirantes,
            verifica=verifica_global,
        )


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------

@dataclass
class ResultadoBiela:
    nodo_a:      str
    nodo_b:      str
    fuerza:      float    # kN
    beta_s:      float
    tension_mpa: float    # MPa actuante
    fce_mpa:     float    # MPa resistencia nominal
    phi_fce_mpa: float    # MPa resistencia de diseño
    verifica:    bool


@dataclass
class ResultadoTiranteBT:
    nodo_a:  str
    nodo_b:  str
    fuerza:  float   # kN
    As_req:  float   # cm²


@dataclass
class ResultadoModeloBT:
    res_bielas:   list[ResultadoBiela]
    res_tirantes: list[ResultadoTiranteBT]
    verifica:     bool

    def mostrar(self) -> None:
        print("=== BIELAS ===")
        print(f"{'A-B':<12} {'F[kN]':>8} {'β_s':>5} {'σ[MPa]':>9} {'φfce[MPa]':>10} {'OK':>4}")
        print("-" * 52)
        for b in self.res_bielas:
            ok = "✓" if b.verifica else "✗"
            print(f"{b.nodo_a}-{b.nodo_b:<10} {b.fuerza:>8.1f} {b.beta_s:>5.2f} "
                  f"{b.tension_mpa:>9.2f} {b.phi_fce_mpa:>10.2f} {ok:>4}")
        print("\n=== TIRANTES ===")
        print(f"{'A-B':<12} {'F[kN]':>8} {'As[cm²]':>9}")
        print("-" * 32)
        for t in self.res_tirantes:
            print(f"{t.nodo_a}-{t.nodo_b:<10} {t.fuerza:>8.1f} {t.As_req:>9.2f}")
        print(f"\nVerificación global: {'✓' if self.verifica else '✗'}")


# ---------------------------------------------------------------------------
# API de alto nivel: ménsula corta (art. 11.9 + 10.7)
# ---------------------------------------------------------------------------

@dataclass
class ResultadoMensulaCorta:
    """Resultado del dimensionado de ménsula corta por biela-tirante."""
    Vu:      float   # kN  — cortante de diseño
    Nu:      float   # kN  — tracción horizontal (0 si no hay)
    a:       float   # m   — excentricidad de la carga
    d:       float   # m   — peralte efectivo

    # Fuerzas en el modelo
    F_tirante_principal: float   # kN  — tirante horizontal superior
    F_tirante_tension:   float   # kN  — componente Nu (si aplica)
    F_biela:             float   # kN  — biela diagonal comprimida
    theta_deg:           float   # grados — inclinación de la biela

    # Armadura
    As_principal: float   # cm²  — armadura principal (tirante horizontal)
    As_total:     float   # cm²  — As_principal + Nu/(φ×fy)

    # Verificación de biela
    sigma_biela:  float   # MPa actuante
    phi_fce:      float   # MPa resistencia
    verifica_biela: bool

    verifica: bool

    def mostrar(self) -> None:
        print(f"{'Vu':30s}: {self.Vu:.1f} kN")
        print(f"{'Nu':30s}: {self.Nu:.1f} kN")
        print(f"{'a/d':30s}: {self.a/self.d:.3f}")
        print(f"{'θ biela':30s}: {self.theta_deg:.1f}°")
        print(f"{'F biela':30s}: {self.F_biela:.1f} kN")
        print(f"{'F tirante principal':30s}: {self.F_tirante_principal:.1f} kN")
        print(f"{'As principal':30s}: {self.As_principal:.2f} cm²")
        print(f"{'As total':30s}: {self.As_total:.2f} cm²")
        print(f"{'σ biela / φ·fce':30s}: {self.sigma_biela:.2f} / {self.phi_fce:.2f} MPa  "
              f"{'✓' if self.verifica_biela else '✗'}")


def dimensionar_mensula(
    Vu:         float,
    a:          float,
    b_mm:       float,
    d:          float,
    hormigon:   Hormigon,
    acero:      Acero,
    Nu:         float = 0.0,
    beta_s:     float = 0.60,
    ancho_biela_mm: float = None,
) -> ResultadoMensulaCorta:
    """
    Dimensiona una ménsula corta por el método biela-tirante simplificado.

    Vu:       cortante de diseño [kN]
    a:        excentricidad de la carga al eje del apoyo [m]
    b_mm:     ancho de la sección [mm]
    d:        peralte efectivo [m]
    hormigon: material del hormigón
    acero:    material del acero
    Nu:       tracción horizontal de diseño [kN] (default 0)
    beta_s:   factor de eficiencia de la biela (art. 10.7.3.2)
    ancho_biela_mm: ancho de la biela en nudo de compresión [mm];
              si None, se estima como min(d×sin(θ)×1000, b_mm/2)

    Hipótesis del modelo:
      - Nodo A: en el borde superior de la ménsula (donde aplica la carga)
      - Nodo B: en el borde inferior del apoyo (punto de apoyo en columna)
      - Tirante horizontal: de A a B en dirección horizontal
      - Biela diagonal: de A al pie del apoyo en la columna

    θ = arctan(d / a) — ángulo de la biela con la horizontal
    F_biela = Vu / sin(θ)
    F_tirante = Vu / tan(θ) = Vu × a / d
    """
    if a <= 0 or d <= 0:
        raise ValueError("a y d deben ser positivos")
    if a > d:
        raise ValueError("La relación a/d debe ser ≤ 1.0 para ménsula corta")

    theta_rad = math.atan2(d, a)
    theta_deg = math.degrees(theta_rad)

    F_biela    = Vu / math.sin(theta_rad)
    F_tirante  = Vu / math.tan(theta_rad)   # = Vu × a / d

    # Área del tirante principal
    As_princ = F_tirante / (PHI_BT * acero.fy * 1000.0) * 1e4   # cm²

    # Componente Nu (tracción adicional horizontal)
    As_nu    = Nu / (PHI_BT * acero.fy * 1000.0) * 1e4 if Nu > 0 else 0.0
    As_total = As_princ + As_nu

    # Verificación de la biela diagonal
    if ancho_biela_mm is None:
        ancho_biela_mm = min(d * math.sin(theta_rad) * 1000.0, b_mm / 2.0)
    area_biela_mm2 = ancho_biela_mm * b_mm
    sigma_biela = F_biela * 1000.0 / area_biela_mm2   # MPa
    fce         = 0.85 * beta_s * hormigon.fc          # MPa
    phi_fce     = PHI_BT * fce                          # MPa
    ver_biela   = sigma_biela <= phi_fce + 1e-9

    return ResultadoMensulaCorta(
        Vu=Vu, Nu=Nu, a=a, d=d,
        F_tirante_principal=F_tirante,
        F_tirante_tension=Nu,
        F_biela=F_biela,
        theta_deg=theta_deg,
        As_principal=As_princ,
        As_total=As_total,
        sigma_biela=sigma_biela,
        phi_fce=phi_fce,
        verifica_biela=ver_biela,
        verifica=ver_biela,
    )
