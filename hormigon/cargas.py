"""
Resistencia requerida — combinaciones y mayoración de acciones (art. 9.2.1).
Coeficientes simplificados para vigas y losas (art. 8.3.3).
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Combinaciones generales (art. 9.2.1, ecs. 9-1 a 9-6)
# ---------------------------------------------------------------------------

def combinaciones(
    D: float = 0.0,
    L: float = 0.0,
    Lr: float = 0.0,
    S: float = 0.0,
    R: float = 0.0,
    W: float = 0.0,
    E: float = 0.0,
) -> dict[str, float]:
    """
    Calcula la resistencia requerida U según todas las combinaciones del art. 9.2.1.

    Parámetros (cargas características, en las unidades del usuario):
      D  — carga permanente (muerta)
      L  — carga de uso (viva)
      Lr — carga de uso en cubiertas
      S  — carga de nieve
      R  — carga de lluvia
      W  — acción del viento
      E  — acción sísmica

    Retorna un diccionario {nombre_combinacion: U}.
    """
    Lr_S_R = max(Lr, S, R)  # mayor de las tres para ec. 9-3 y 9-4

    combos = {
        "9-1":  1.4 * D,
        "9-2":  1.2 * D + 1.6 * L + 0.5 * Lr_S_R,
        "9-3a": 1.2 * D + 1.6 * Lr_S_R + 1.0 * L,
        "9-3b": 1.2 * D + 1.6 * Lr_S_R + 0.8 * W,
        "9-4a": 1.2 * D + 1.6 * W + 1.0 * L + 0.5 * Lr_S_R,
        "9-4b": 0.9 * D + 1.6 * W,
        "9-5a": 1.2 * D + 1.0 * E + 1.0 * L + 0.2 * S,
        "9-5b": 0.9 * D + 1.0 * E,
    }
    return combos


def U_max(
    D: float = 0.0,
    L: float = 0.0,
    Lr: float = 0.0,
    S: float = 0.0,
    R: float = 0.0,
    W: float = 0.0,
    E: float = 0.0,
) -> float:
    """Retorna la máxima resistencia requerida U entre todas las combinaciones."""
    return max(combinaciones(D=D, L=L, Lr=Lr, S=S, R=R, W=W, E=E).values())


# ---------------------------------------------------------------------------
# Coeficientes para vigas y losas (art. 8.3.3)
# Se aplican a w_u = 1.2·w_D + 1.6·w_L sobre cargas uniformes.
# Válido cuando: 2 tramos mínimo, ≥2 vanos, variación de carga viva ≤ 3/4 carga muerta,
# cargas uniformes, secciones prismáticas.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoeficienteMomento:
    """Coeficiente C_m para M_u = C_m · w_u · l_n²."""
    descripcion: str
    C_m: float          # positivo = tensión en traccionado inferior


@dataclass(frozen=True)
class CoeficienteCorte:
    """Coeficiente C_v para V_u = C_v · w_u · l_n."""
    descripcion: str
    C_v: float


# Coeficientes de momento (art. 8.3.3) — M_u = C_m · w_u · l_n²
# Nota: l_n = luz libre entre caras de apoyo [m], w_u en kN/m.
MOMENTOS_VIGAS = [
    CoeficienteMomento("Momento neg. exterior — 2 tramos, apoyo discontinuo empotrado", -1/16),
    CoeficienteMomento("Momento neg. exterior — más de 2 tramos, apoyo discontinuo empotrado", -1/14),
    CoeficienteMomento("Momento neg. exterior — apoyo discontinuo libre (no integral con columna)", -1/24),
    CoeficienteMomento("Momento positivo — tramo extremo", +1/14),
    CoeficienteMomento("Momento positivo — tramo interior", +1/16),
    CoeficienteMomento("Momento neg. interior — primer apoyo interior, 2 tramos", -1/9),
    CoeficienteMomento("Momento neg. interior — primer apoyo interior, >2 tramos", -1/10),
    CoeficienteMomento("Momento neg. — apoyos interiores restantes", -1/11),
    CoeficienteMomento("Momento neg. — cara de columnas de borde (viga continua en columna)", -1/16),
]

# Igual que vigas pero con coeficiente positivo distinto para el tramo extremo
MOMENTOS_LOSAS_1DIR = [
    CoeficienteMomento("Momento neg. exterior — apoyo discontinuo empotrado", -1/16),
    CoeficienteMomento("Momento neg. exterior — apoyo discontinuo libre", -1/24),
    CoeficienteMomento("Momento positivo — tramo extremo", +1/14),
    CoeficienteMomento("Momento positivo — tramo interior", +1/16),
    CoeficienteMomento("Momento neg. interior — primer apoyo interior, 2 tramos", -1/9),
    CoeficienteMomento("Momento neg. interior — primer apoyo interior, >2 tramos", -1/10),
    CoeficienteMomento("Momento neg. — apoyos interiores restantes", -1/11),
]

# Coeficientes de corte (art. 8.3.3) — V_u = C_v · w_u · l_n
CORTES_VIGAS = [
    CoeficienteCorte("Corte en primer apoyo interior — 2 tramos", 1.15 / 2),
    CoeficienteCorte("Corte en primer apoyo interior — >2 tramos", 1.15 / 2),
    CoeficienteCorte("Corte en apoyos exteriores e interiores restantes", 1.0 / 2),
]


def momento_ultimo(C_m: float, wu: float, ln: float) -> float:
    """M_u = C_m · w_u · l_n²  [kNm] (wu en kN/m, ln en m)."""
    return C_m * wu * ln ** 2


def corte_ultimo(C_v: float, wu: float, ln: float) -> float:
    """V_u = C_v · w_u · l_n  [kN]."""
    return C_v * wu * ln


# ---------------------------------------------------------------------------
# Carga mayorada para la combinación más común (D + L)
# ---------------------------------------------------------------------------

def wu_DL(wD: float, wL: float) -> float:
    """
    Carga mayorada para la combinación D + L (la más usual en vigas/losas).

    Retorna max(1.4·wD, 1.2·wD + 1.6·wL).

    wD, wL en kN/m (viga) o kN/m² (losa) — las unidades se conservan.
    """
    return max(1.4 * wD, 1.2 * wD + 1.6 * wL)


# ---------------------------------------------------------------------------
# Resultado de combinaciones (para trazabilidad)
# ---------------------------------------------------------------------------

@dataclass
class ResultadoCombinaciones:
    """Resultado de evaluar todas las combinaciones de acciones."""
    combos: dict[str, float]

    @property
    def U(self) -> float:
        """Máxima resistencia requerida."""
        return max(self.combos.values())

    @property
    def combo_gobernante(self) -> str:
        """Nombre de la combinación que produce el mayor U."""
        return max(self.combos, key=self.combos.__getitem__)

    def mostrar(self) -> None:
        print(f"{'Combinación':<10} {'U':>12}")
        print("-" * 24)
        for nombre, valor in self.combos.items():
            marca = " ← gobierna" if nombre == self.combo_gobernante else ""
            print(f"{nombre:<10} {valor:>12.3f}{marca}")


def evaluar_combinaciones(
    D: float = 0.0,
    L: float = 0.0,
    Lr: float = 0.0,
    S: float = 0.0,
    R: float = 0.0,
    W: float = 0.0,
    E: float = 0.0,
) -> ResultadoCombinaciones:
    """Evalúa todas las combinaciones y retorna un ResultadoCombinaciones."""
    return ResultadoCombinaciones(
        combos=combinaciones(D=D, L=L, Lr=Lr, S=S, R=R, W=W, E=E)
    )
