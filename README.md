# py-concrete-calc

**py-concrete-calc** es una librería Python y aplicación de escritorio para el diseño y verificación de elementos de hormigón armado según **CIRSOC 201-2005** (equivalente argentino del ACI 318).

Cubre el programa completo de Estructuras de Hormigón en UTN FRA: propiedades de secciones y combinaciones de cargas, flexión, corte, torsión, columnas, losas, bases, anclajes y modelos biela-tirante. La librería de cálculo funciona de forma completamente offline y puede usarse de forma independiente (scripts, tests, notebooks) o a través de la interfaz de escritorio PyQt6 actualmente en desarrollo.

## Módulos

| Módulo | Contenido |
|---|---|
| `materiales.py` | `Hormigon` y `Acero` con propiedades derivadas (β₁, f\*c, Es) |
| `secciones.py` | Secciones rectangular, T, L y circular; ancho efectivo de alas (art. 8.10) |
| `cargas.py` | Combinaciones de acciones art. 9.2.1; método de los coeficientes art. 8.3.3 |
| `flexion.py` | Flexión simple: dimensionado y verificación; armadura simple y doble; φ variable según modo de rotura |
| `corte.py` | Corte: Vc, Vs, estribado y envolvente φVn |
| `torsion.py` | Torsión combinada con corte; armadura transversal At/s y longitudinal Al (art. 11.6) |
| `columnas.py` | Columnas cortas y esbeltas; diagrama de interacción P-M; estribadas y zunchadas |
| `losas.py` | Losas en una dirección por método de coeficientes (art. 8.3.3); punzonamiento |
| `bases.py` | Bases centradas aisladas; flexión, corte unidireccional y punzonamiento (art. 15) |
| `tirantes.py` | Elementos en tracción pura; control de fisuras (art. 10.6.4) |
| `anclajes.py` | Longitudes de desarrollo y empalme en tracción y compresión; ganchos estándar (art. 12) |
| `bielas.py` | Método biela-tirante (art. 10.7); factores de eficiencia de bielas y nudos; ménsulas cortas |

## Características principales

- **Cobertura completa del CIRSOC 201-2005** para los elementos del programa de UTN FRA
- **Sistema de variantes**: las funciones de dimensionado devuelven todas las combinaciones de armadura válidas ordenadas por mínima área de acero
- **Trazabilidad total**: cada objeto resultado almacena todos los valores intermedios (As, φMn, Vc, At/s, etc.)
- **487 tests automatizados** validados contra los ejemplos resueltos del CIRSOC con tolerancia ≤ 1%
- **Arquitectura en capas**: la librería de cálculo es completamente independiente de la interfaz gráfica

## Instalación

Requiere Python 3.12+.

```bash
git clone https://github.com/federicoarielcasado/py-concrete-calc.git
cd py-concrete-calc
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m pytest                                  # 487 tests
```

## Uso

```python
from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion

h25  = Hormigon(fc=25)
a420 = Acero(fy=420)
sec  = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.04, hormigon=h25, acero=a420)

# Solución única
resultado = dimensionar_flexion(seccion=sec, Mu=180)
print(resultado.As)       # cm²
print(resultado.phi_Mn)   # kNm

# Todas las combinaciones válidas rankeadas por mínima As
rset = dimensionar_flexion(seccion=sec, Mu=180, variantes=True)
rset.mostrar()
```

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Librería de cálculo | Python 3.12, NumPy, SciPy |
| Interfaz de escritorio *(en desarrollo)* | PyQt6, Matplotlib (embebido), Plotly (3D vía QWebEngineView) |
| Tests | pytest |

## Tests

487 tests automatizados cubriendo los 12 módulos de cálculo, cada uno validado contra los ejemplos resueltos del CIRSOC 201-2005.

```bash
python -m pytest -v
```

## Estructura del proyecto

```
hormigon/       # Librería de cálculo — sin dependencia de la UI
elementos/      # Wrappers de elementos tipificados: viga, columna, losa   [WIP]
graficos/       # Visualización: secciones 2D, diagramas, modelo 3D        [WIP]
app/            # Interfaz de escritorio PyQt6                              [WIP]
tests/          # Tests unitarios por módulo
ejemplos/       # Scripts que replican los ejemplos resueltos del CIRSOC
```

## Estado

Librería de cálculo completa (12 módulos, 487 tests). Interfaz de escritorio y capa de visualización en desarrollo.

**Autor**: Federico Ariel Casado — UTN FRA  
**Reglamento**: CIRSOC 201-2005  
**Licencia**: Privada
