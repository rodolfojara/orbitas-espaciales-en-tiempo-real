# Pruebas y cobertura

Mapa honesto de qué está verificado automáticamente y qué no.

## Resumen

| Capa | Estado |
|---|---|
| Pruebas unitarias | 9 en `tests/test_basic.py` |
| CI | 2 jobs: matriz Python 3.11/3.12/3.13 + instalación limpia por wheel |
| Demo reproducible | 69 valores de referencia, comprobados en cada push |
| Servidor / API | Solo verificación manual (no hay tests automáticos) |
| Interfaces web | Sin pruebas automáticas |
| Fuentes externas | Sin pruebas automáticas (dependen de red y credenciales) |

Todo se ejecuta con `python tests/test_basic.py` (o `pytest`) y en GitHub Actions
en cada push a `main`.

## Qué sí se valida

### Pruebas unitarias (`tests/test_basic.py`)

| Prueba | Qué comprueba |
|---|---|
| `test_covariance_grows_without_measurements` | La incertidumbre del EKF crece al predecir sin medir. |
| `test_update_reduces_covariance_and_corrects_state` | Una medición reduce la covarianza. |
| `test_geo_zero_distance_is_launch_site` | Distancia cero → lat/lon del sitio de lanzamiento. |
| `test_filter_tracks_truth_within_3_sigma` | En el escenario semilla 42, el error contra la verdad simulada queda dentro de ~3σ y la altitud final coincide a <1 km. |
| `test_sources_registry_is_valid` | `sources.json` pasa validación y tiene fuentes Starship + salida Markdown. |
| `test_timeutils_roundtrip` | JD ↔ UTC y rango del GMST. |
| `test_frames_roundtrip` | geodésico ↔ ECEF con error <1e-6°. |
| `test_passes_visibility` | Satélite en el cenit es visible y el radio de huella es positivo. |
| `test_od_convergence` | La determinación de órbita por mínimos cuadrados converge y queda cerca del estado inicial. |

### Pruebas de integración en CI

- **Instalación editable** (`pip install -e .`): dependencias, tests y dos ejemplos
  (`run_leo_ground_track.py`, `run_orbit3d.py`) generan archivos sin error.
- **Instalación por wheel** (`pip install .` en venv limpio): el paquete se importa
  desde `site-packages`, `sgp4` está presente, los JSON de `data/` viajan en el
  wheel y el entry point `orbitas-rt sources` funciona.
- **Demo reproducible** (`run_reproducible_demo.py --check`): 69 valores
  (SHA-256 de la entrada, 12 puntos de control y 4 métricas) coinciden con la
  referencia con tolerancia 0.01. Se ejecuta en ambos jobs y en Windows se
  verificó manualmente que los archivos son byte-idénticos entre corridas.

> `run_leo_ground_track.py` y `run_orbit3d.py` son *smoke tests*: comprueban que
> el código corre y escribe archivos, **no** que los números sean correctos.

## Qué NO está validado

### Búsqueda y fuentes

- `smart_search.py`: caché TTL de 6 h, frescura del TLE, validación orbital,
  cross-referencia y detección de conflictos no tienen tests.
- `deep_search.py`: aliases, deduplicación, acumulación en `knowledge_base.json`
  y comportamiento sin red no tienen tests.
- `spacetrack.py`: login, búsquedas y manejo de credenciales sin probar; el CI no
  tiene credenciales y la fuente se desactiva.
- `lookup.py` y `horizons.py`: parseo de respuestas reales, IDs que cambian,
  timeouts y errores HTTP no están cubiertos.
- CelesTrak / JPL Horizons: disponibilidad y cambios de formato no se detectan
  en CI; las consultas reales se hicieron a mano durante el desarrollo.

### Servidor y APIs

- Ningún endpoint de `examples/serve.py` tiene test automático. El fallo de
  `/api/lookup` (calculaba la respuesta pero no la enviaba) se encontró y corrigió
  manualmente; hoy podría romperse otra vez sin que el CI lo note.
- No hay tests de `/api/query`, `/api/lunar`, `/api/horizons`, `/api/stations`,
  `/api/groups`, `/api/search`, `/api/deep_search` ni `/api/knowledge_base`.

### Interfaces web

- `dashboard.html`, `query.html`, `tracking_stations.html`, `lunar_map.html`,
  `mars_map.html` y `live_track.html` no se abren en navegador durante el CI.
- El terminador día/noche, el antimeridiano y la proyección ortográfica se
  revisaron visualmente, pero no hay aserciones numéricas sobre esos píxeles.
- Que GitHub Pages compile no implica que los enlaces o el contenido sean
  correctos; los enlaces del README se revisaron una vez de forma manual.

### Datos y catálogos

- `sources.json` es el único registro con validación automática.
- `deep_space.json` (77 naves), `lost_objects.json` (21 objetos) y
  `tracking_stations.json` no tienen validación de esquema ni de duplicados.
- Las correcciones históricas (Peldehue/Colina, SSOT = FASAT-Charlie, B22,
  Ship 42, etc.) están documentadas pero no se comprueban con tests.
- La exactitud de efemérides y metadatos frente a fuentes independientes no está
  verificada; Horizons puede no cubrir misiones soviéticas, chinas o privadas.

### Modelo físico y mediciones

- El EKF solo se prueba en el escenario simulado con semilla 42; no hay tests
  con maniobras reales, sensores reales ni pérdidas de señal distintas de las
  tres ventanas predefinidas.
- GNSS y óptico son simulados y están marcados como tal; SatNOGS es real pero
  limitado y no se consulta en CI.
- `test_od_convergence` usa `np.random.normal` **sin fijar semilla**: el test es
  robusto por la tolerancia de 1 km, pero no es estrictamente reproducible.
- `eci_to_heliocentric()` en `frames.py` es una aproximación y no se valida;
  para valores reales se usa Horizons directo.

### Entorno y otros

- CI corre solo en Ubuntu. Windows se probó manualmente; macOS no se probó.
- Python 3.9/3.10 no están soportados ni testeados (el engine usa 3.11+).
- `ocr.py` es experimental y no tiene pruebas.
- No hay benchmarks de rendimiento ni de memoria.

## Prioridades sugeridas para ampliar

1. Tests de los endpoints de `serve.py` levantando el servidor en un hilo: evita
   regresiones como la de `/api/lookup`.
2. Tests unitarios de `smart_search` y `deep_search` con respuestas HTTP
   simuladas (mockeadas) y caché en directorio temporal.
3. Validación de esquema de los tres JSON de registros (claves obligatorias,
   IDs únicos, fechas plausibles).
4. Test del CLI `track` con un CSV fijo y salida esperada.
5. Smoke test HTTP de las páginas (status 200) sin abrir navegador.
6. Fijar la semilla en `test_od_convergence` para que sea determinista.
