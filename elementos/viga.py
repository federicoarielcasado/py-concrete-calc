"""
Wrappers para vigas de hormigón armado.

Clases:
  VigaSimple    — viga isostática con carga uniforme
  VigaVoladizo  — voladizo con carga uniforme y/o concentrada en extremo libre
  VigaContinua  — viga continua por método de coeficientes (art. 8.3.3)

Unidades: kN y metros; kNm para momentos.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from hormigon.cargas import wu_DL
from hormigon.corte import ResultadoCorte, calcular_corte
from hormigon.flexion import ResultadoFlexion, dimensionar_flexion


# ── Resultado común (viga isostática) ─────────────────────────────────────────

@dataclass
class ResultadoViga:
    """Resultado de VigaSimple o VigaVoladizo."""
    tipo:    str       # "simple" | "voladizo"
    L:       float     # luz [m]
    wu:      float     # carga mayorada distribuida [kN/m]
    Mu:      float     # momento de diseño [kNm]
    Vu:      float     # corte de diseño en la sección crítica [kN]
    x:       np.ndarray   # posiciones a lo largo de la luz [m]
    M_x:     np.ndarray   # M(x) [kNm]
    V_x:     np.ndarray   # V(x) [kN]
    resultado_flex:  ResultadoFlexion
    resultado_corte: ResultadoCorte
    seccion: object

    def mostrar(self) -> None:
        tipo_str = {'simple': 'Viga simple', 'voladizo': 'Viga en voladizo'}[self.tipo]
        print(f"{'Tipo':<28}: {tipo_str}")
        print(f"{'Luz L':<28}: {self.L:.2f} m")
        print(f"{'wu':<28}: {self.wu:.2f} kN/m")
        print(f"{'Mu (diseño)':<28}: {self.Mu:.2f} kNm")
        print(f"{'Vu (diseño)':<28}: {self.Vu:.2f} kN")
        print()
        print("--- Flexion -----------------------------------------")
        self.resultado_flex.mostrar()
        print()
        print("--- Corte -------------------------------------------")
        self.resultado_corte.mostrar()

    def graficar(self):
        """M y V a lo largo de la luz + sección transversal."""
        from graficos.diagramas import graficar_viga
        return graficar_viga(self)

    def graficar_3d(self):
        """Visualización 3D interactiva con barras y estribos (Plotly)."""
        from graficos.elemento_3d import visualizar_viga_3d
        return visualizar_viga_3d(self)


# ── Resultado viga continua ───────────────────────────────────────────────────

@dataclass
class SeccionCriticaViga:
    """Sección crítica de diseño en una viga continua."""
    nombre:         str
    Mu:             float              # kNm (valor absoluto)
    signo:          str                # "positivo" | "negativo"
    resultado_flex: ResultadoFlexion


@dataclass
class ResultadoVigaContinua:
    """Resultado de VigaContinua (método de coeficientes, art. 8.3.3)."""
    ln:       float
    wu:       float
    n_tramos: int
    extremo:  str
    secciones: list[SeccionCriticaViga] = field(default_factory=list)
    Vu_ext:   float = 0.0   # kN — corte en apoyos exteriores
    Vu_1er_int: float = 0.0 # kN — corte en primer apoyo interior
    resultado_corte_ext: Optional[ResultadoCorte] = None
    resultado_corte_int: Optional[ResultadoCorte] = None

    def mostrar(self) -> None:
        print(f"{'ln':<28}: {self.ln:.2f} m")
        print(f"{'wu':<28}: {self.wu:.2f} kN/m")
        print(f"{'n_tramos':<28}: {self.n_tramos}")
        print(f"{'extremo':<28}: {self.extremo}")
        print()
        print(f"{'Seccion':<35} {'Mu [kNm]':>10} {'As [cm2]':>10} {'phiMn [kNm]':>13}  OK")
        print("-" * 72)
        for s in self.secciones:
            ok = "OK" if s.resultado_flex.verifica else "NO"
            rf = s.resultado_flex
            print(f"  {s.nombre:<33} {s.Mu:>10.2f} {rf.As:>10.2f} {rf.phi_Mn:>11.2f}  {ok}")
        print()
        print(f"{'Vu apoyo exterior':<28}: {self.Vu_ext:.2f} kN")
        print(f"{'Vu primer apoyo interior':<28}: {self.Vu_1er_int:.2f} kN")
        if self.resultado_corte_ext:
            check = 'OK' if self.resultado_corte_ext.verifica_resistencia else 'NO'
            print(f"{'phiVn (apoyo ext.)':<28}: {self.resultado_corte_ext.phi_Vn:.2f} kN  {check}")
        if self.resultado_corte_int:
            check = 'OK' if self.resultado_corte_int.verifica_resistencia else 'NO'
            print(f"{'phiVn (1er apoyo int.)':<28}: {self.resultado_corte_int.phi_Vn:.2f} kN  {check}")

    def graficar(self):
        """Tabla de secciones críticas con φMn vs Mu."""
        from graficos.diagramas import graficar_viga_continua
        return graficar_viga_continua(self)


# ── VigaSimple ────────────────────────────────────────────────────────────────

class VigaSimple:
    """
    Viga isostática simplemente apoyada con carga uniforme.

    La sección crítica de corte se toma a distancia d del apoyo.
    """

    def __init__(
        self,
        seccion,
        L: float,
        wD: float = 0.0,
        wL: float = 0.0,
        wU: Optional[float] = None,
    ):
        """
        seccion : SeccionRectangular o SeccionT
        L       : luz libre entre apoyos [m]
        wD, wL  : cargas permanente y viva [kN/m]
        wU      : carga mayorada directa (omite wD y wL si se da)
        """
        self.seccion = seccion
        self.L       = L
        self.wu      = wU if wU is not None else wu_DL(wD, wL)

    def calcular(self) -> ResultadoViga:
        L, wu = self.L, self.wu
        Mu = wu * L ** 2 / 8.0

        # Corte en la sección crítica (d desde la cara del apoyo)
        d  = self.seccion.d
        Vu = wu * (L / 2.0 - d)
        Vu = max(Vu, 0.0)   # no puede ser negativo

        r_flex  = dimensionar_flexion(self.seccion, Mu)
        r_corte = calcular_corte(self.seccion, Vu)

        n   = 120
        x   = np.linspace(0.0, L, n)
        M_x = wu * x * (L - x) / 2.0
        V_x = wu * L / 2.0 - wu * x

        return ResultadoViga(
            tipo='simple', L=L, wu=wu, Mu=Mu, Vu=Vu,
            x=x, M_x=M_x, V_x=V_x,
            resultado_flex=r_flex, resultado_corte=r_corte,
            seccion=self.seccion,
        )


# ── VigaVoladizo ──────────────────────────────────────────────────────────────

class VigaVoladizo:
    """
    Viga en voladizo con carga uniforme y/o concentrada en el extremo libre.

    El empotramiento está en x = 0.
    """

    def __init__(
        self,
        seccion,
        L: float,
        wD: float = 0.0,
        wL: float = 0.0,
        PD: float = 0.0,
        PL: float = 0.0,
        wU: Optional[float] = None,
        PU: Optional[float] = None,
    ):
        """
        L       : longitud del voladizo [m]
        wD, wL  : carga uniforme muerta/viva [kN/m]
        PD, PL  : carga concentrada muerta/viva en el extremo libre [kN]
        wU, PU  : cargas mayoradas directas (si se dan, anulan wD/wL y PD/PL)
        """
        self.seccion = seccion
        self.L  = L
        self.wu = wU if wU is not None else wu_DL(wD, wL)
        self.Pu = PU if PU is not None else (1.2 * PD + 1.6 * PL)

    def calcular(self) -> ResultadoViga:
        L, wu, Pu = self.L, self.wu, self.Pu

        Mu = wu * L ** 2 / 2.0 + Pu * L
        Vu = wu * L + Pu

        r_flex  = dimensionar_flexion(self.seccion, Mu)
        r_corte = calcular_corte(self.seccion, Vu)

        n     = 120
        x     = np.linspace(0.0, L, n)
        xL    = L - x                         # distancia al extremo libre
        M_x   = -(wu * xL ** 2 / 2.0 + Pu * xL)   # negativo: tensión en fibra superior
        V_x   = wu * xL + Pu

        return ResultadoViga(
            tipo='voladizo', L=L, wu=wu, Mu=Mu, Vu=Vu,
            x=x, M_x=M_x, V_x=V_x,
            resultado_flex=r_flex, resultado_corte=r_corte,
            seccion=self.seccion,
        )


# ── VigaContinua ──────────────────────────────────────────────────────────────

class VigaContinua:
    """
    Viga continua con carga uniforme — método de coeficientes (art. 8.3.3).

    Condiciones de aplicabilidad:
      - ≥ 2 tramos, cargas uniformes, secciones prismáticas.
      - Variación de carga viva ≤ 3/4 de la carga muerta.
      - Luces adyacentes sin diferencia mayor al 20%.
    """

    def __init__(
        self,
        seccion,
        ln: float,
        wD: float,
        wL: float,
        n_tramos: int = 2,
        extremo:  str = 'libre',
    ):
        """
        seccion  : SeccionRectangular o SeccionT
        ln       : luz libre entre caras de apoyo [m]
        wD, wL   : carga uniforme muerta/viva [kN/m]
        n_tramos : número de tramos (≥ 2)
        extremo  : condición del extremo discontinuo:
                   'libre'   → apoyo simple (no integral con columna)
                   'viga'    → empotrado a viga de borde
                   'columna' → empotrado a columna
        """
        if n_tramos < 2:
            raise ValueError("VigaContinua requiere n_tramos ≥ 2.")
        self.seccion  = seccion
        self.ln       = ln
        self.wu       = wu_DL(wD, wL)
        self.n_tramos = n_tramos
        self.extremo  = extremo

    # Selección de coeficientes según art. 8.3.3
    def _coeficientes(self) -> dict[str, float]:
        n, ext = self.n_tramos, self.extremo
        c: dict[str, float] = {}

        # Momentos positivos
        c['pos_ext'] = 1 / 14        # tramo extremo
        if n > 2:
            c['pos_int'] = 1 / 16    # tramos interiores

        # Momento negativo en apoyo exterior
        if ext == 'libre':
            c['neg_ext'] = 1 / 24
        elif n == 2:
            c['neg_ext'] = 1 / 16    # 2 tramos, apoyo empotrado
        else:
            c['neg_ext'] = 1 / 14    # >2 tramos, apoyo empotrado

        # Momento negativo en primer apoyo interior
        c['neg_1er_int'] = 1 / 9 if n == 2 else 1 / 10

        # Momento negativo en apoyos interiores restantes
        if n > 3:
            c['neg_int'] = 1 / 11

        return c

    def calcular(self) -> ResultadoVigaContinua:
        wu, ln = self.wu, self.ln
        coef   = self._coeficientes()
        sec    = self.seccion

        def _dim(nombre: str, C: float, signo: str) -> SeccionCriticaViga:
            Mu = abs(C) * wu * ln ** 2
            return SeccionCriticaViga(
                nombre=nombre,
                Mu=Mu,
                signo=signo,
                resultado_flex=dimensionar_flexion(sec, Mu),
            )

        secciones: list[SeccionCriticaViga] = []

        secciones.append(_dim('Tramo ext.  M+ (centro)',   coef['pos_ext'],    'positivo'))
        if 'pos_int' in coef:
            secciones.append(_dim('Tramo int.  M+ (centro)',   coef['pos_int'],    'positivo'))
        secciones.append(_dim('Apoyo ext.  M- (cara int.)', coef['neg_ext'],   'negativo'))
        secciones.append(_dim('1° apoyo int. M- (cara ext.)', coef['neg_1er_int'], 'negativo'))
        if 'neg_int' in coef:
            secciones.append(_dim('Apoyos int. M-',            coef['neg_int'],    'negativo'))

        # Cortes
        Vu_ext     = wu * ln / 2.0
        Vu_1er_int = 1.15 * wu * ln / 2.0

        r_corte_ext = calcular_corte(sec, Vu_ext)
        r_corte_int = calcular_corte(sec, Vu_1er_int)

        return ResultadoVigaContinua(
            ln=ln, wu=wu,
            n_tramos=self.n_tramos,
            extremo=self.extremo,
            secciones=secciones,
            Vu_ext=Vu_ext,
            Vu_1er_int=Vu_1er_int,
            resultado_corte_ext=r_corte_ext,
            resultado_corte_int=r_corte_int,
        )
