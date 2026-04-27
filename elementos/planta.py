"""
API de alto nivel para diseño de elementos a partir de un esquema estructural.

Uso:
    from elementos.planta import dimensionar_viga, dimensionar_columna, dimensionar_losa

    r = dimensionar_viga('V1', planta)
    r.mostrar()

    r = dimensionar_columna('C3', planta)
    r.mostrar()

    r = dimensionar_losa('L2', planta)
    r.mostrar()
"""
from __future__ import annotations

from hormigon.cargas import wu_DL
from hormigon.modelo import PlantaEstructural
from hormigon.propagacion import (
    CargaColumna,
    CargaViga,
    ResultadoPropagacion,
    calcular_carga_columna,
    calcular_carga_viga,
    propagar,
)


# ---------------------------------------------------------------------------
# Diseño de vigas
# ---------------------------------------------------------------------------

def dimensionar_viga(
    viga_id: str,
    planta: PlantaEstructural,
    carga: CargaViga | None = None,
):
    """
    Dimensiona la viga viga_id según las cargas propagadas desde la planta.

    Si ya se calculó la propagación completa, pasar carga=resultado.cargas_vigas[id]
    para evitar recalcular.

    Retorna ResultadoViga (1 tramo) o ResultadoVigaContinua (≥ 2 tramos).
    """
    from elementos.viga import VigaContinua, VigaSimple

    if carga is None:
        carga = calcular_carga_viga(viga_id, planta)

    viga = planta.vigas[viga_id]

    if carga.n_tramos == 1:
        obj = VigaSimple(
            seccion=viga.seccion,
            L=carga.ln_disenio,
            wU=carga.wu,
        )
    else:
        obj = VigaContinua(
            seccion=viga.seccion,
            ln=carga.ln_disenio,
            wD=carga.wD,
            wL=carga.wL,
            n_tramos=carga.n_tramos,
            extremo=viga.extremo,
        )
    return obj.calcular()


# ---------------------------------------------------------------------------
# Diseño de columnas
# ---------------------------------------------------------------------------

def dimensionar_columna(
    col_id: str,
    planta: PlantaEstructural,
    carga: CargaColumna | None = None,
):
    """
    Dimensiona la columna col_id según las cargas propagadas desde la planta.

    Retorna ResultadoColumnaFlexoCompresion.
    """
    from elementos.columna import Columna

    if carga is None:
        carga = calcular_carga_columna(col_id, planta)

    col = planta.columnas[col_id]
    obj = Columna(
        seccion=col.seccion,
        Pu=carga.Pu,
        Mu=carga.Mu,
        tipo=col.tipo,
    )
    return obj.calcular()


# ---------------------------------------------------------------------------
# Diseño de losas
# ---------------------------------------------------------------------------

def dimensionar_losa(losa_id: str, planta: PlantaEstructural):
    """
    Dimensiona la losa losa_id.

    Para losas 1dir: retorna ResultadoLosa1Dir.
    Para losas 2dir: pendiente de implementación.
    """
    from elementos.losa_1dir import Losa1Dir

    losa = planta.losas[losa_id]
    g = planta.grilla

    wD_total = losa.h * planta.gamma_conc + losa.wD

    if losa.tipo == '1dir':
        ln = g.lx(losa.i) if losa.dir_1dir == 'x' else g.ly(losa.j)
        obj = Losa1Dir(
            h=losa.h,
            recubrimiento=losa.recubrimiento,
            hormigon=planta.hormigon,
            acero=planta.acero,
            wD=wD_total,
            wL=losa.wL,
            ln=ln,
            n_tramos=losa.n_tramos,
            extremo=losa.extremo,
        )
        return obj.calcular()

    elif losa.tipo == '2dir':
        from hormigon.losas import calcular_losa_2dir
        la = min(g.lx(losa.i), g.ly(losa.j))
        lb = max(g.lx(losa.i), g.ly(losa.j))
        obj = calcular_losa_2dir(
            la=la,
            lb=lb,
            h=losa.h,
            recubrimiento=losa.recubrimiento,
            hormigon=planta.hormigon,
            acero=planta.acero,
            wu=wu_DL(wD_total, losa.wL),
            tipo_a=losa.tipo_a,
            tipo_b=losa.tipo_b,
        )
        return obj
    else:
        raise ValueError(f"tipo de losa desconocido: {losa.tipo!r}")


# ---------------------------------------------------------------------------
# Diseño completo de la planta
# ---------------------------------------------------------------------------

def dimensionar_planta(planta: PlantaEstructural) -> dict:
    """
    Propaga cargas y dimensiona todos los elementos de la planta.

    Retorna un dict con claves:
      'propagacion' : ResultadoPropagacion
      'vigas'       : dict[id, resultado]
      'columnas'    : dict[id, resultado]
      'losas'       : dict[id, resultado]
    """
    prop = propagar(planta)

    resultados_vigas = {
        vid: dimensionar_viga(vid, planta, carga=prop.cargas_vigas[vid])
        for vid in planta.vigas
    }
    resultados_columnas = {
        cid: dimensionar_columna(cid, planta, carga=prop.cargas_columnas[cid])
        for cid in planta.columnas
    }
    resultados_losas = {}
    for lid in planta.losas:
        try:
            resultados_losas[lid] = dimensionar_losa(lid, planta)
        except NotImplementedError as e:
            resultados_losas[lid] = str(e)

    return {
        'propagacion': prop,
        'vigas':       resultados_vigas,
        'columnas':    resultados_columnas,
        'losas':       resultados_losas,
    }
