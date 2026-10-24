# Notas de desarrollo

Contexto para retomar el proyecto en otra computadora o en una sesión nueva: cómo está armado, qué se decidió y por qué, y qué queda pendiente. El README describe el proyecto hacia afuera; este documento es para quien lo desarrolla.

## Puesta en marcha

```bash
git clone https://github.com/federicoarielcasado/py-concrete-calc.git
cd py-concrete-calc
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt

python app/main.py                  # aplicación de escritorio
python -m pytest                    # 598 tests (no necesitan PyQt)
python -m ejemplos.ej_viga_continua # ejemplos: siempre como módulo, desde la raíz
python scripts/generar_capturas.py  # regenera docs/capturas/ (~60 s, abre la app)
```

- El repositorio es privado: en una máquina nueva hace falta iniciar sesión en GitHub.
- **El historial se reescribió en octubre de 2026** para quitar un archivo. Una copia clonada antes de esa fecha no es compatible: hay que clonar de nuevo (o `git fetch` + `git reset --hard origin/main`), nunca `git pull`.
- CI: `.github/workflows/tests.yml` corre pytest en cada push (Ubuntu, sin PyQt, `MPLBACKEND=Agg`).

## Arquitectura

```
hormigon/    Librería de cálculo pura (sin UI). Cada función devuelve un objeto
             resultado con todos los valores intermedios.
elementos/   Elementos tipificados que combinan módulos (viga, columna, losa, planta).
graficos/    Figuras matplotlib (2D) y plotly (3D). No conocen la UI.
app/         Interfaz PyQt6: una ventana por módulo en app/ventanas/, widgets
             reutilizables en app/widgets/, temas, estilos y memoria PDF.
tests/       pytest; valores esperados calculables a mano o de ejemplos CIRSOC.
scripts/     Herramientas de desarrollo (capturas).
```

Flujo típico de una ventana: `validar_campos()` → leer entradas → función de `hormigon/` o `elementos/` → `panel_res.mostrar_resultado_*()` → figura de `graficos/` en `CanvasMatplotlib`.

### Convenciones

- Unidades: kN y m en todo el proyecto; MPa para tensiones; As en cm².
- Nombres según la notación del CIRSOC (Mu, Vu, As, phi_Mn, f'c → `fc`...).
- Combinación de cargas: siempre `hormigon.cargas.wu_DL()` = máx(1.4·D ; 1.2·D + 1.6·L), art. 9.2.1. No escribir factores sueltos (ver "Decisiones").
- Variantes de armado: ordenadas por economía (menor área o menor Av/s).
- Commits en español, en infinitivo ("Agregar…", "Corregir…"), sin líneas de co-autoría.

## Interfaz

| Pieza | Dónde | Notas |
|---|---|---|
| Temas Claro / Oscuro | `app/themes.py`, `app/styles.py` | Un `Tema` (dataclass) genera el QSS y los colores de todo lo que no usa QSS. Base de estilo `Fusion`. |
| Figuras en el tema | `app/widgets/tema_figuras.py` | Las figuras se crean siempre en claro; el oscuro se aplica después invirtiendo grises y aclarando colores oscuros. Guarda los colores originales, así que cambiar de tema es reversible. Artistas con `gid='color_fijo'` no se tocan. Exportar figura y la memoria PDF usan siempre los colores claros. |
| Panel de resultados | `app/widgets/panel_resultados.py` | Recibe `[(texto, color) \| None]`; `None` separa bloques, que se reparten en dos columnas. Recuerda la última llamada para redibujar al cambiar de tema; `lineas` alimenta la memoria PDF. |
| Validación | `app/widgets/entradas.py` | Validador numérico en los `QLineEdit`, chequeo antes de calcular (vacío, no numérico, dimensión ≤ 0, negativo salvo Nu) y scroll de los paneles de datos. |
| Memoria PDF | `app/memoria.py` | Genérica para cualquier ventana: lee los `QFormLayout` visibles, el panel de resultados y la figura. QTextDocument → QPdfWriter, sin dependencias extra. Referencias normativas por módulo en `_REFERENCIAS`. |
| Visor 3D | `app/widgets/visor_3d.py` | plotly.js embebido (sin CDN, funciona offline). Supera el límite de 2 MB de `setHtml`, por eso se escribe a un archivo temporal y se usa `load()`. No llamar `setHtml` justo antes de un `load()` (compiten). |
| Lienzo E-09 | `app/widgets/canvas_planta.py` | Escala `SCALE = 80 px/m`, grilla de 1 m. Vigas y columnas se generan solas desde los paneles. |

Detalle útil para capturas automáticas: `QWidget.grab()` de la ventana no incluye el contenido de `QWebEngineView` ni los tooltips; `scripts/generar_capturas.py` los captura aparte y los superpone.

## Modelo de planta (E-09) y propagación de cargas

**Construcción** (`canvas_planta.py`):
1. El usuario dibuja paños rectangulares (o usa *Cargar ejemplo*: 3×2 paños, 14 × 9 m).
2. Cada borde de paño marcado "con viga" genera una viga; bordes colineales se unen en vigas continuas.
3. `puntos_columna_m()` ubica una columna en cada extremo de viga **y en cada eje de la grilla que la cruza** (incluye cruces entre vigas). La usan tanto el dibujo como el modelo, para que coincidan.
4. `to_planta_estructural()` arma el `PlantaEstructural` de `hormigon/modelo.py`.

**Propagación** (`hormigon/propagacion.py`):

| Paso | Regla |
|---|---|
| Losa | D = h·25 kN/m³ + wD superpuesta; L = wL |
| Losa 1 dir. → viga | w·l/2 a las vigas perpendiculares a la luz |
| Losa 2 dir. → viga | Líneas a 45°: triangular sobre el **lado corto**, trapezoidal sobre el **largo** |
| Equivalente para **momento** (diseño de la viga) | triangular w·la/3; trapezoidal w·la·(3−m²)/6 |
| Equivalente para **corte** (reacciones) | triangular w·la/4; trapezoidal w·la·(2−m)/4 (suman exactamente w·la·lb) |
| Viga → columna | art. 8.3.3: w·ln/2; 1.15·w·ln/2 solo para el tramo extremo en el primer apoyo interior |
| Columna | Pu = suma de reacciones + peso propio, mayorado con `wu_DL`; Mu = Pu·e_mín, e_mín = máx(20 mm ; h/20) |

**Control de equilibrio**: ΣPu de columnas ≥ carga total mayorada, con un excedente explicado solo por el factor 1.15 (≈ +5 % en el ejemplo). Lo verifica `tests/test_propagacion.py::test_equilibrio_planta_3x2`.

**Simplificaciones conocidas** (conviene mencionarlas si se presenta el proyecto):
- Un solo nivel: las columnas no acumulan pisos.
- Paños rectangulares sobre grilla de 1 m; secciones de vigas y columnas únicas para toda la planta.
- Mu de columnas por excentricidad mínima, no por análisis de pórtico; sin viento ni sismo.
- Reacciones por coeficientes del art. 8.3.3, no por resolución de la viga continua.

## Decisiones y correcciones (octubre 2026)

- **Estética**: se reemplazó el tema retro (Win98 / terminal CRT, textos tipo "EJECUTAR PROTOCOLO") por temas Claro y Oscuro con textos neutros ("Calcular", "✓ VERIFICA").
- **C-02**: variantes de estribos ordenadas por menor Av/s (antes, por mayor separación).
- **M-08**: se agregó la cuantía mínima de ménsulas (art. 11.9.5) y los estribos horizontales Ah (art. 11.9.4).
- **Factores de carga**: L-04 en 2 direcciones calculaba con 1.4·D + 1.7·L (ACI viejo) y varios tooltips citaban esa combinación; todo pasa ahora por `wu_DL`.
- **E-09**, cuatro errores corregidos con un balance de cargas:
  1. no había columnas en los cruces interiores de vigas → se perdía ~9 % de la carga;
  2. las reacciones usaban la equivalente de momento → +33 %;
  3. triangular y trapezoidal estaban asignadas al revés (los tests viejos tenían el mismo error);
  4. el factor 1.15 se aplicaba en todos los apoyos interiores.
- **Planta en la sesión JSON**: E-09 guarda y restaura sus paneles.
- **Repositorio**: el archivo de instrucciones local para asistentes de código no se versiona (`.gitignore`); el historial se reescribió para quitarlo.

## Diagnóstico de E-09: casos límite

Balance de cargas (carga total mayorada vs. ΣPu de columnas) sobre casos que el editor permite dibujar. Un excedente de +4 a +6 % es esperable (factor 1.15 del art. 8.3.3); un déficit indica carga perdida.

| Caso | ΣPu vs. total |
|---|---|
| Grilla regular, 2 paños 5 × 4 m | +4.1 % ✓ |
| Planta en L | +5.7 % ✓ |
| Losa con un borde sin viga | −8.5 % |
| Paño de 6 × 6 junto a dos paños de 4 × 3 | −24.7 % |
| Paños superpuestos | −30.8 % |
| Paños desfasados (no alineados) | −40.7 % |
| Losa en 1 dirección sin vigas en su dirección de apoyo | −67.9 % |

Causas:
- `PanelLosa` se ubica por la celda `(i, j)` de su esquina y el modelo toma `lx = grilla.lx(i)`, `ly = grilla.ly(j)`: supone que cada losa ocupa **una sola celda**. El editor permite rectángulos libres; si un paño abarca varias celdas, sus dimensiones y su carga se toman mal.
- `_carga_tramo` solo carga vigas existentes: la parte de la losa que corresponde a un borde sin viga no se transfiere a ningún lado.
- El editor no valida superposiciones ni apoyos.

Plan de trabajo (también en el README):
- **A. Robustez:** losas multi-celda con dimensiones reales y reparto a los tramos de viga que tocan; redistribución de bordes libres; validaciones en el editor; control de equilibrio visible en E-09 (y un test por cada caso de la tabla).
- **B. Nuevos casos:** voladizos; cargas lineales y puntuales; varios niveles con enlace E-09 → B-07; secciones por elemento y vigas sobre vigas.
- **C. Largo plazo:** vigas continuas por rigidez, losas no rectangulares, aberturas, viento y sismo.

## Pendientes

Alcance del curso aún no cubierto:
- Columnas esbeltas (art. 10.10–10.12) y secciones circulares en columnas.
- Bases medianeras y de esquina.
- Losas en 2 direcciones por Pórtico Equivalente (art. 13.7); punzonamiento en losas sin vigas.
- Pantallas para anclajes y tirantes (la librería ya los tiene).
- `elementos/planta.py::dimensionar_losa` todavía no dimensiona losas en 2 direcciones.

Mejoras posibles (además del plan de E-09 de la sección anterior):
- Rótulos del lienzo E-09 más legibles con poco zoom.
- Ejecutable para Windows (PyInstaller; pesado por QtWebEngine).
- Los archivos temporales del visor 3D no se borran al cerrar.
