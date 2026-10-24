"""
Propagación de cargas gravitacionales en la planta estructural.

Flujo:
    losa → viga (carga distribuida equivalente)
    viga → columna (reacciones en apoyos)

Distribución de carga de losa a vigas
--------------------------------------
• Losas 1 dirección (dir_1dir='x' o 'y'):
    La carga va íntegramente a las vigas perpendiculares al vano.
    Carga por metro de viga = wu · l_vano / 2  [kN/m]

• Losas 2 direcciones (método de líneas a 45°):
    la = lado corto, lb = lado largo, m = la/lb
    La carga real sobre la viga es triangular (lado corto) o trapezoidal
    (lado largo). Se reemplaza por una carga uniforme equivalente, distinta
    según el efecto que se quiere reproducir:

                          momento (diseño de la viga)   corte (reacciones)
      triangular           q = w · la / 3                 q = w · la / 4
      trapezoidal          q = w · la · (3 − m²) / 6      q = w · la · (2 − m) / 4

    Las equivalentes de corte suman exactamente la carga de la losa
    (2·w·la²/4 + 2·w·la·(2·lb − la)/4 = w·la·lb); las de momento la superan
    y solo se usan para dimensionar la viga a flexión.

Reacciones sobre columnas
--------------------------
Art. 8.3.3 (corte en vigas continuas), con la carga equivalente de corte:
    Apoyo exterior:                     R = w · ln / 2
    Primer apoyo interior (tramo extremo): 1.15 · w · ln / 2
    Demás apoyos interiores:            w · ln / 2   (por cada vano adyacente)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from hormigon.cargas import wu_DL
from hormigon.modelo import (
    ColumnaEsquema,
    PanelLosa,
    PlantaEstructural,
    VigaEsquema,
)


# ---------------------------------------------------------------------------
# Objetos resultado
# ---------------------------------------------------------------------------

@dataclass
class CargaViga:
    """Cargas de diseño sobre una viga de la planta."""
    id:            str
    n_tramos:      int
    ln_disenio:    float         # luz libre representativa para VigaContinua [m]
    spans:         list[float]   # luces individuales por vano [m]
    wD:            float         # carga muerta promedio ponderada [kN/m]
    wL:            float         # carga viva promedio ponderada [kN/m]
    wu:            float         # carga mayorada promedio [kN/m]
    wu_por_tramo:  list[float]   # wu por cada vano (equivalente de momento)
    corte_por_tramo: list[tuple[float, float]] = field(default_factory=list)
                                 # (wD, wL) por vano, equivalente de corte [kN/m]
    detalle:       dict = field(default_factory=dict)


@dataclass
class CargaColumna:
    """Cargas de diseño sobre una columna de la planta."""
    id:      str
    Pu:      float   # carga axial mayorada [kN]
    Mu:      float   # momento de diseño [kNm]
    detalle: dict = field(default_factory=dict)


@dataclass
class ResultadoPropagacion:
    """Resultado de propagar las cargas en toda la planta."""
    cargas_vigas:    dict[str, CargaViga]
    cargas_columnas: dict[str, CargaColumna]

    def mostrar(self) -> None:
        print("--- Cargas sobre vigas ------------------------------")
        print(f"{'ID':<8} {'n':>3} {'ln [m]':>8} {'wD [kN/m]':>11} "
              f"{'wL [kN/m]':>11} {'wu [kN/m]':>11}")
        print("-" * 56)
        for cv in self.cargas_vigas.values():
            print(f"  {cv.id:<6} {cv.n_tramos:>3} {cv.ln_disenio:>8.2f} "
                  f"{cv.wD:>11.2f} {cv.wL:>11.2f} {cv.wu:>11.2f}")
        print()
        print("--- Cargas sobre columnas ---------------------------")
        print(f"{'ID':<8} {'Pu [kN]':>10} {'Mu [kNm]':>10}")
        print("-" * 32)
        for cc in self.cargas_columnas.values():
            print(f"  {cc.id:<6} {cc.Pu:>10.1f} {cc.Mu:>10.2f}")


# ---------------------------------------------------------------------------
# Lógica interna
# ---------------------------------------------------------------------------

def _wD_losa(losa: PanelLosa, gamma_conc: float) -> float:
    """Carga muerta total de la losa [kN/m²]: peso propio + superimpuesto."""
    return losa.h * gamma_conc + losa.wD


def _cargas_borde_1dir(
    losa: PanelLosa,
    lx: float,
    ly: float,
    gamma_conc: float,
    efecto: str = 'momento',
) -> dict[str, tuple[float, float]]:
    """
    Cargas (wD, wL) [kN/m] sobre cada borde de una losa 1-dirección.

    Claves del dict:
      'x_neg' → borde en y = ejes_y[j]   (cara inferior del panel)
      'x_pos' → borde en y = ejes_y[j+1] (cara superior)
      'y_neg' → borde en x = ejes_x[i]   (cara izquierda)
      'y_pos' → borde en x = ejes_x[i+1] (cara derecha)
    """
    wD_total = _wD_losa(losa, gamma_conc)
    wL = losa.wL

    if losa.dir_1dir == 'x':
        # Vano en x → reacciones en las vigas de borde en y (dir='y')
        q_wD = wD_total * lx / 2
        q_wL = wL * lx / 2
        return {
            'y_neg': (q_wD, q_wL),
            'y_pos': (q_wD, q_wL),
            'x_neg': (0.0, 0.0),
            'x_pos': (0.0, 0.0),
        }
    else:
        # Vano en y → reacciones en las vigas de borde en x (dir='x')
        q_wD = wD_total * ly / 2
        q_wL = wL * ly / 2
        return {
            'x_neg': (q_wD, q_wL),
            'x_pos': (q_wD, q_wL),
            'y_neg': (0.0, 0.0),
            'y_pos': (0.0, 0.0),
        }


def _cargas_borde_2dir(
    losa: PanelLosa,
    lx: float,
    ly: float,
    gamma_conc: float,
    efecto: str = 'momento',
) -> dict[str, tuple[float, float]]:
    """
    Cargas uniformes equivalentes (wD, wL) [kN/m] sobre cada borde de una
    losa 2-direcciones (líneas a 45°; la = lado corto, lb = lado largo, m = la/lb).

    efecto='momento': triangular w·la/3, trapezoidal w·la·(3−m²)/6
    efecto='corte':   triangular w·la/4, trapezoidal w·la·(2−m)/4
    """
    wD_total = _wD_losa(losa, gamma_conc)
    wL = losa.wL

    la = min(lx, ly)
    lb = max(lx, ly)
    m = la / lb

    if efecto == 'corte':
        f_tri, f_trap = la / 4, la * (2 - m) / 4
    else:
        f_tri, f_trap = la / 3, la * (3 - m ** 2) / 6

    q_tri_D,  q_tri_L  = wD_total * f_tri,  wL * f_tri
    q_trap_D, q_trap_L = wD_total * f_trap, wL * f_trap

    # La carga triangular va a los bordes del lado corto (longitud la) y la
    # trapezoidal a los del lado largo. Bordes 'x_*': vigas en x, longitud lx;
    # bordes 'y_*': vigas en y, longitud ly.
    if lx <= ly:
        # Lado corto paralelo a x → vigas en x (longitud lx = la): triangular
        return {
            'x_neg': (q_tri_D,  q_tri_L),
            'x_pos': (q_tri_D,  q_tri_L),
            'y_neg': (q_trap_D, q_trap_L),
            'y_pos': (q_trap_D, q_trap_L),
        }
    else:
        # Lado corto paralelo a y → vigas en y (longitud ly = la): triangular
        return {
            'y_neg': (q_tri_D,  q_tri_L),
            'y_pos': (q_tri_D,  q_tri_L),
            'x_neg': (q_trap_D, q_trap_L),
            'x_pos': (q_trap_D, q_trap_L),
        }


def _carga_tramo(
    viga: VigaEsquema,
    k: int,
    planta: PlantaEstructural,
    efecto: str = 'momento',
) -> tuple[float, float]:
    """
    Retorna (wD, wL) [kN/m] del tramo k de la viga (0-based).

    El tramo k va de la columna (desde+k) a la columna (desde+k+1).
    Incluye autopeso + contribuciones de los paneles adyacentes a ESE tramo.
    Cada panel contribuye a un único tramo de la viga (el que tiene a su lado).
    """
    g = planta.grilla
    sec = viga.seccion
    wD = sec.b * sec.h * planta.gamma_conc
    wL = 0.0

    if viga.dir == 'x':
        # Tramo k: entre ejes_x[desde+k] y ejes_x[desde+k+1], a y=ejes_y[idx]
        i_panel = viga.desde + k
        for losa in planta.losas.values():
            if losa.i != i_panel:
                continue
            lx = g.lx(losa.i)
            ly = g.ly(losa.j)
            fn = _cargas_borde_1dir if losa.tipo == '1dir' else _cargas_borde_2dir
            cargas = fn(losa, lx, ly, planta.gamma_conc, efecto)
            if losa.j == viga.idx:          # panel abajo del tramo
                wD += cargas['x_neg'][0]
                wL += cargas['x_neg'][1]
            elif losa.j == viga.idx - 1:    # panel arriba del tramo
                wD += cargas['x_pos'][0]
                wL += cargas['x_pos'][1]
    else:
        # Tramo k: entre ejes_y[desde+k] y ejes_y[desde+k+1], a x=ejes_x[idx]
        j_panel = viga.desde + k
        for losa in planta.losas.values():
            if losa.j != j_panel:
                continue
            lx = g.lx(losa.i)
            ly = g.ly(losa.j)
            fn = _cargas_borde_1dir if losa.tipo == '1dir' else _cargas_borde_2dir
            cargas = fn(losa, lx, ly, planta.gamma_conc, efecto)
            if losa.i == viga.idx:          # panel a la izquierda
                wD += cargas['y_neg'][0]
                wL += cargas['y_neg'][1]
            elif losa.i == viga.idx - 1:    # panel a la derecha
                wD += cargas['y_pos'][0]
                wL += cargas['y_pos'][1]

    return wD, wL


def _reaccion_caracteristica(
    viga: VigaEsquema,
    nodo_perp: int,
    cv: CargaViga,
) -> tuple[float, float]:
    """
    Retorna (R_D, R_L) [kN] — reacciones características en el nodo.

    Usa la carga equivalente de corte de cada vano adyacente y el art. 8.3.3:
      apoyo exterior                    : w · ln / 2
      tramo extremo en el 1.er apoyo int.: 1.15 · w · ln / 2
      demás tramos en apoyos interiores : w · ln / 2
    """
    pos = nodo_perp - viga.desde  # posición local (0 = extremo inicial)
    spans = cv.spans
    n = len(spans)

    def aporte(k: int, interior: bool) -> tuple[float, float]:
        wD, wL = cv.corte_por_tramo[k]
        extremo = k in (0, n - 1)
        f = 1.15 if (interior and extremo) else 1.0
        return f * wD * spans[k] / 2, f * wL * spans[k] / 2

    if pos == 0:
        return aporte(0, interior=False)
    if pos == n:
        return aporte(n - 1, interior=False)
    D_i, L_i = aporte(pos - 1, interior=True)
    D_d, L_d = aporte(pos, interior=True)
    return D_i + D_d, L_i + L_d


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def calcular_carga_viga(
    viga_id: str,
    planta: PlantaEstructural,
) -> CargaViga:
    """
    Calcula las cargas de diseño sobre la viga.

    Computa la carga por tramo (cada panel contribuye solo al tramo adyacente)
    y luego promedia ponderando por longitud para obtener el wu único que
    requiere el método de coeficientes (art. 8.3.3).
    """
    viga = planta.vigas[viga_id]
    g = planta.grilla

    if viga.dir == 'x':
        spans = [g.lx(i) for i in range(viga.desde, viga.hasta)]
    else:
        spans = [g.ly(j) for j in range(viga.desde, viga.hasta)]

    n = len(spans)
    cargas_tramos = [_carga_tramo(viga, k, planta) for k in range(n)]
    cargas_corte  = [_carga_tramo(viga, k, planta, 'corte') for k in range(n)]
    wu_tramos = [wu_DL(wD, wL) for wD, wL in cargas_tramos]

    # Promedio ponderado por longitud de tramo
    total_len = sum(spans)
    wD_avg = sum(wD * l for (wD, _), l in zip(cargas_tramos, spans)) / total_len
    wL_avg = sum(wL * l for (_, wL), l in zip(cargas_tramos, spans)) / total_len
    wu_avg = wu_DL(wD_avg, wL_avg)

    ln_disenio = total_len / n

    detalle: dict = {
        f'tramo_{k}': {'wD': wD, 'wL': wL, 'wu': wu_tramos[k], 'ln': spans[k]}
        for k, (wD, wL) in enumerate(cargas_tramos)
    }

    return CargaViga(
        id=viga_id,
        n_tramos=n,
        ln_disenio=ln_disenio,
        spans=spans,
        wD=wD_avg,
        wL=wL_avg,
        wu=wu_avg,
        wu_por_tramo=wu_tramos,
        corte_por_tramo=cargas_corte,
        detalle=detalle,
    )


def calcular_carga_columna(
    col_id: str,
    planta: PlantaEstructural,
    _cache_vigas: dict[str, CargaViga] | None = None,
) -> CargaColumna:
    """
    Calcula la carga axial sobre la columna sumando reacciones de las vigas
    que llegan a su nodo.

    _cache_vigas: resultado previo de calcular_carga_viga para cada viga
                  (evita recalcular en propagación completa).
    """
    col = planta.columnas[col_id]

    # Peso propio del fuste
    sec = col.seccion
    wD_col = sec.b * sec.h * planta.gamma_conc * col.h_entrepiso
    detalle: dict = {'pp_columna': wD_col}

    total_D = wD_col
    total_L = 0.0

    for viga_id, viga in planta.vigas.items():
        if viga.dir == 'x':
            if col.iy != viga.idx:
                continue
            nodo_perp = col.ix
        else:
            if col.ix != viga.idx:
                continue
            nodo_perp = col.iy

        if not (viga.desde <= nodo_perp <= viga.hasta):
            continue

        if _cache_vigas is not None and viga_id in _cache_vigas:
            cv = _cache_vigas[viga_id]
        else:
            cv = calcular_carga_viga(viga_id, planta)

        R_D, R_L = _reaccion_caracteristica(viga, nodo_perp, cv)
        total_D += R_D
        total_L += R_L
        detalle[f'R_{viga_id}'] = wu_DL(R_D, R_L)

    Pu = wu_DL(total_D, total_L)

    # Excentricidad mínima: e_min = max(20 mm, h_col/20)
    e_min = max(0.02, col.seccion.h / 20)
    Mu = Pu * e_min

    return CargaColumna(id=col_id, Pu=Pu, Mu=Mu, detalle=detalle)


def propagar(planta: PlantaEstructural) -> ResultadoPropagacion:
    """Propaga las cargas en toda la planta y retorna los resultados."""
    cache: dict[str, CargaViga] = {}
    for viga_id in planta.vigas:
        cache[viga_id] = calcular_carga_viga(viga_id, planta)

    cargas_col = {}
    for col_id in planta.columnas:
        cargas_col[col_id] = calcular_carga_columna(col_id, planta, _cache_vigas=cache)

    return ResultadoPropagacion(cargas_vigas=cache, cargas_columnas=cargas_col)
