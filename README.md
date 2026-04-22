# py-concrete-calc

**py-concrete-calc** is a Python library and desktop application for structural design and verification of reinforced concrete elements following **CIRSOC 201-2005** (Argentine equivalent of ACI 318).

Covers the full reinforced concrete curriculum at UTN FRA — from cross-section properties and load combinations through flexure, shear, torsion, columns, slabs, footings, anchorage, and strut-and-tie models. The calculation library runs entirely offline and can be used standalone (scripts, tests, notebooks) or through the PyQt6 desktop interface currently in development.

## Modules

| Module | Content |
|---|---|
| `materiales.py` | `Hormigon` and `Acero` with derived properties (β₁, f\*c, Es) |
| `secciones.py` | Rectangular, T, L and circular sections; effective flange width (art. 8.10) |
| `cargas.py` | Load combinations art. 9.2.1; coefficient method art. 8.3.3 |
| `flexion.py` | Flexure: design and verification; single and double reinforcement; φ variable by failure mode |
| `corte.py` | Shear: Vc, Vs, stirrup spacing and φVn envelope |
| `torsion.py` | Torsion + shear interaction; transverse At/s and longitudinal Al (art. 11.6) |
| `columnas.py` | Short and slender columns; P-M interaction diagram; tied and spiral |
| `losas.py` | One-way slabs by coefficient method (art. 8.3.3); two-way punching shear |
| `bases.py` | Centered isolated footings; flexure, one-way shear and punching (art. 15) |
| `tirantes.py` | Pure tension members; crack control (art. 10.6.4) |
| `anclajes.py` | Development and lap-splice lengths in tension and compression; standard hooks (art. 12) |
| `bielas.py` | Strut-and-tie model (art. 10.7); strut/node efficiency factors; corbel design |

## Key Features

- **Complete CIRSOC 201-2005 coverage** for the main element types taught at UTN FRA
- **Variant ranking**: design functions return all valid reinforcement combinations sorted by minimum steel area
- **Traceability**: every result object stores all intermediate values (As, φMn, Vc, At/s, etc.)
- **487 automated tests** validated against CIRSOC worked examples with ≤ 1% tolerance
- **Two-layer architecture**: calculation library is fully independent of the desktop UI

## Installation

Requires Python 3.12+.

```bash
git clone https://github.com/federicoarielcasado/py-concrete-calc.git
cd py-concrete-calc
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m pytest                                  # 487 tests
```

## Usage

```python
from hormigon.materiales import Hormigon, Acero
from hormigon.secciones import SeccionRectangular
from hormigon.flexion import dimensionar_flexion

h25  = Hormigon(fc=25)
a420 = Acero(fy=420)
sec  = SeccionRectangular(b=0.30, h=0.60, recubrimiento=0.04, hormigon=h25, acero=a420)

# Single result
resultado = dimensionar_flexion(seccion=sec, Mu=180)
print(resultado.As)       # cm²
print(resultado.phi_Mn)   # kNm

# All valid reinforcement combinations ranked by minimum steel
rset = dimensionar_flexion(seccion=sec, Mu=180, variantes=True)
rset.mostrar()
```

## Technology Stack

| Layer | Technology |
|---|---|
| Calculation library | Python 3.12, NumPy, SciPy |
| Desktop interface *(in development)* | PyQt6, Matplotlib (embedded), Plotly (3D via QWebEngineView) |
| Testing | pytest |

## Testing

487 automated tests covering all 12 calculation modules, each validated against CIRSOC 201-2005 worked examples.

```bash
python -m pytest -v
```

## Architecture

```
hormigon/       # Calculation library — no UI dependency
elementos/      # Typed element wrappers: viga, columna, losa       [WIP]
graficos/       # Visualization: 2D sections, diagrams, 3D model    [WIP]
app/            # PyQt6 desktop interface                            [WIP]
tests/          # Unit tests per module
ejemplos/       # Scripts replicating CIRSOC worked examples
```

## Status

Core calculation library complete (12 modules, 487 tests). Desktop interface and visualization layer in development.

**Author**: Federico Ariel Casado — UTN FRA  
**Standard**: CIRSOC 201-2005  
**License**: Private
