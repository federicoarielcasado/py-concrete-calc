import math

# Catálogo de barras comerciales argentinas: diámetro nominal [mm] → área [cm²]
BARRAS = {
     6:  0.283,
     8:  0.503,
    10:  0.785,
    12:  1.131,
    14:  1.539,
    16:  2.011,
    20:  3.142,
    22:  3.801,
    25:  4.909,
    28:  6.158,
    32:  8.042,
    36: 10.179,
    40: 12.566,
}

DIAMETROS = sorted(BARRAS.keys())


class Hormigon:
    """Hormigón de resistencia f'c según CIRSOC 201-2005."""

    def __init__(self, fc: float, wc: float = 2400.0):
        """
        fc:  f'c [MPa]
        wc:  peso unitario [kg/m³] (2400 = hormigón armado de peso normal)
        """
        if fc <= 0:
            raise ValueError(f"f'c debe ser positivo, se recibió {fc}")
        self.fc = fc
        self.wc = wc

    @property
    def beta1(self) -> float:
        """β₁ del bloque rectangular de tensiones (art. 10.2.7.3)."""
        return min(0.85, max(0.65, 0.85 - 0.05 * (self.fc - 28.0) / 7.0))

    @property
    def fsc(self) -> float:
        """0.85·f'c [MPa] — tensión media en el bloque rectangular."""
        return 0.85 * self.fc

    @property
    def Ec(self) -> float:
        """Módulo de elasticidad [MPa] (art. 8.5.1)."""
        return (self.wc ** 1.5) * 0.043 * math.sqrt(self.fc)

    @property
    def epsilon_u(self) -> float:
        """Deformación unitaria última del hormigón (art. 10.2.3)."""
        return 0.003

    def __repr__(self) -> str:
        return f"Hormigon(fc={self.fc} MPa, β₁={self.beta1:.4f})"


class Acero:
    """Acero de refuerzo según CIRSOC 201-2005."""

    Es: float = 200_000.0  # [MPa] art. 8.5.2 — constante de clase

    def __init__(self, fy: float, tipo: str = "ADN"):
        """
        fy:   tensión de fluencia [MPa]
        tipo: identificador (ADN 420, AM 500 N, etc.)
        """
        if fy <= 0:
            raise ValueError(f"fy debe ser positivo, se recibió {fy}")
        self.fy = fy
        self.tipo = tipo

    @property
    def epsilon_y(self) -> float:
        """Deformación unitaria de fluencia."""
        return self.fy / self.Es

    def __repr__(self) -> str:
        return f"Acero({self.tipo}, fy={self.fy} MPa)"
