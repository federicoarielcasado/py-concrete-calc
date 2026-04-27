"""
Tests para hormigon/losas.py — calcular_losa_2dir (DDM, art. 13.6).
Todos los valores esperados son calculables a mano.
"""
import pytest

from hormigon.materiales import Acero, Hormigon
from hormigon.losas import calcular_losa_2dir, h_minimo_2dir, _DDM_FACTORES

H25  = Hormigon(fc=25)
A420 = Acero(fy=420)


# ---------------------------------------------------------------------------
# Parámetros geometricos base
# ---------------------------------------------------------------------------

LA, LB = 4.0, 5.0
H, REC = 0.14, 0.02
WU = 10.0   # kN/m²


@pytest.fixture
def resultado_int():
    return calcular_losa_2dir(LA, LB, H, REC, H25, A420, wu=WU,
                               tipo_a='int', tipo_b='int')


@pytest.fixture
def resultado_ext_emp():
    return calcular_losa_2dir(LA, LB, H, REC, H25, A420, wu=WU,
                               tipo_a='ext_empotrado', tipo_b='ext_empotrado')


# ---------------------------------------------------------------------------
# Geometría y propiedades
# ---------------------------------------------------------------------------

def test_m_relacion_aspecto(resultado_int):
    assert resultado_int.m == pytest.approx(LA / LB)


def test_d_a_d_b(resultado_int):
    assert resultado_int.d_a == pytest.approx(H - REC)
    assert resultado_int.d_b == pytest.approx(H - REC - 0.02)


def test_h_minimo_int():
    assert h_minimo_2dir(LA, 'int') == pytest.approx(LA / 33)


def test_h_minimo_borde():
    assert h_minimo_2dir(LA, 'borde') == pytest.approx(LA / 36)


def test_verifica_h(resultado_int):
    # h=0.14 >= la/33 = 4.0/33 ≈ 0.121 → debe verificar
    assert resultado_int.verifica_h is True


# ---------------------------------------------------------------------------
# Momentos — tramo interior (tipo='int')
# ---------------------------------------------------------------------------

def test_momentos_dir_a_int(resultado_int):
    """M+ = 0.35*M0, M- = 0.65*M0 para tramo interior dir a."""
    M0_a = WU * LA**2 / 8.0
    f_pos, f_neg_int, _ = _DDM_FACTORES['int']

    secs = {s.nombre: s for s in resultado_int.secciones}
    assert secs['M+ centro tramo (a (corta))'].Mu == pytest.approx(f_pos * M0_a, rel=1e-6)
    assert secs['M- apoyo int. (a (corta))'].Mu   == pytest.approx(f_neg_int * M0_a, rel=1e-6)


def test_momentos_dir_b_int(resultado_int):
    """M+ = 0.35*M0, M- = 0.65*M0 para tramo interior dir b."""
    M0_b = WU * LB**2 / 8.0
    f_pos, f_neg_int, _ = _DDM_FACTORES['int']

    secs = {s.nombre: s for s in resultado_int.secciones}
    assert secs['M+ centro tramo (b (larga))'].Mu == pytest.approx(f_pos * M0_b, rel=1e-6)
    assert secs['M- apoyo int. (b (larga))'].Mu   == pytest.approx(f_neg_int * M0_b, rel=1e-6)


def test_ext_libre_sin_momento_neg_ext():
    """Para tipo='ext_libre', f_neg_ext=0 → la seccion M- ext no aparece."""
    r = calcular_losa_2dir(LA, LB, H, REC, H25, A420, wu=WU,
                            tipo_a='ext_libre', tipo_b='int')
    nombres_a = [s.nombre for s in r.secciones if s.direccion == 'a']
    assert not any('apoyo ext.' in n for n in nombres_a)


# ---------------------------------------------------------------------------
# Momentos — tramo ext_empotrado
# ---------------------------------------------------------------------------

def test_momentos_ext_empotrado(resultado_ext_emp):
    """M+ = 0.52*M0, M-_int = 0.70*M0, M-_ext = 0.26*M0."""
    M0_a = WU * LA**2 / 8.0
    f_pos, f_neg_int, f_neg_ext = _DDM_FACTORES['ext_empotrado']

    secs = {s.nombre: s for s in resultado_ext_emp.secciones}
    assert secs['M+ centro tramo (a (corta))'].Mu    == pytest.approx(f_pos * M0_a, rel=1e-6)
    assert secs['M- apoyo int. (a (corta))'].Mu      == pytest.approx(f_neg_int * M0_a, rel=1e-6)
    assert secs['M- apoyo ext. (a (corta))'].Mu      == pytest.approx(f_neg_ext * M0_a, rel=1e-6)


# ---------------------------------------------------------------------------
# Armado: As > 0 y phiMn >= Mu
# ---------------------------------------------------------------------------

def test_armado_verifica(resultado_int):
    """Todas las secciones con Mu > 0 deben verificar (phiMn >= Mu)."""
    for s in resultado_int.secciones:
        if s.Mu > 1e-6:
            assert s.verifica, f"Seccion '{s.nombre}' no verifica (Mu={s.Mu:.2f}, phiMn={s.phi_Mn:.2f})"
            assert s.As > 0


def test_armado_mayor_carga_mayor_as():
    """A mayor wu, mayor As negativo requerido (wu=25 supera claramente el As mínimo)."""
    r_low  = calcular_losa_2dir(LA, LB, H, REC, H25, A420, wu=5.0,  tipo_a='int')
    r_high = calcular_losa_2dir(LA, LB, H, REC, H25, A420, wu=25.0, tipo_a='int')
    As_low  = next(s.As for s in r_low.secciones  if 'M- apoyo int. (a' in s.nombre)
    As_high = next(s.As for s in r_high.secciones if 'M- apoyo int. (a' in s.nombre)
    assert As_high > As_low


# ---------------------------------------------------------------------------
# Losa cuadrada: ambas direcciones tienen el mismo M0
# ---------------------------------------------------------------------------

def test_losa_cuadrada_m0_iguales():
    r = calcular_losa_2dir(5.0, 5.0, H, REC, H25, A420, wu=WU,
                            tipo_a='int', tipo_b='int')
    secs = {s.nombre: s for s in r.secciones}
    Mu_a = secs['M+ centro tramo (a (corta))'].Mu
    Mu_b = secs['M+ centro tramo (b (larga))'].Mu
    assert Mu_a == pytest.approx(Mu_b, rel=1e-6)


# ---------------------------------------------------------------------------
# Temperatura y retracción
# ---------------------------------------------------------------------------

def test_temperatura_positivo(resultado_int):
    assert resultado_int.As_temp > 0
    assert resultado_int.s_temp_max > 0


# ---------------------------------------------------------------------------
# Validaciones de entrada
# ---------------------------------------------------------------------------

def test_error_la_mayor_lb():
    """Si la > lb se debe levantar ValueError."""
    with pytest.raises(ValueError, match="la="):
        calcular_losa_2dir(6.0, 4.0, H, REC, H25, A420, wu=WU)


def test_error_m_menor_05():
    """Si la/lb < 0.5 la losa es casi unidireccional."""
    with pytest.raises(ValueError, match="m = la/lb"):
        calcular_losa_2dir(2.0, 5.0, H, REC, H25, A420, wu=WU)


def test_error_tipo_invalido():
    with pytest.raises(ValueError, match="invalido"):
        calcular_losa_2dir(LA, LB, H, REC, H25, A420, wu=WU, tipo_a='malo')
