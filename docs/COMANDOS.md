# Referencia de comandos

Guía corta en el [README](../README.md). Aquí está el catálogo completo.

## Instalación

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e .            # paquete + dependencias + comando orbitas-rt
python tests/test_basic.py  # o: pytest
```

Si solo quieres correr ejemplos sin instalar el paquete: `pip install -r requirements.txt`
(el comando `orbitas-rt` no queda instalado en ese caso).

## Demostración del filtro

```bash
python examples/run_demo.py
```

Regenera `examples/output/trajectory.png`, `time_series.png`, `uncertainty.png`
y `track.csv`. En rojo, los tramos donde se simula que se cae la transmisión.

Ejemplo de `examples/output/track.csv` (`señal = NO` → solo propagación del modelo):

| T+ (s) | lat | lon | dist. (km) | alt. (km) | vel. (km/s) | ±σ dist. (km) | señal |
|---:|---:|---:|---:|---:|---:|---:|:--:|
| 0 | 25.9970 | -97.1570 | 0.00 | 0.00 | 0.000 | 0.01 | NO |
| 120 | 25.9893 | -97.0755 | 8.19 | 10.44 | 0.195 | 0.10 | sí |
| 300 | 25.8785 | -95.9564 | 120.78 | 49.67 | 1.694 | 0.10 | NO |
| 360 | 25.7306 | -94.5831 | 259.23 | 76.38 | 3.120 | 0.42 | NO |
| 420 | 25.4542 | -92.2922 | 491.02 | 108.03 | 4.823 | 1.15 | NO |
| 500 | 24.7746 | -87.6124 | 968.18 | 153.01 | 7.392 | 0.61 | sí |
| 900 | 18.1043 | -61.3280 | 3782.63 | 277.09 | 7.237 | 0.76 | NO |
| 1000 | 15.8926 | -55.2341 | 4475.66 | 279.98 | 7.234 | 2.26 | NO |
| 1150 | 12.2647 | -46.3301 | 5517.06 | 262.92 | 7.255 | 6.09 | NO |
| 1300 | 8.2629 | -37.4741 | 6583.10 | 228.41 | 7.358 | 3.11 | sí |
| 1700 | -2.9979 | -14.6469 | 9407.29 | 33.15 | 2.973 | 9.72 | NO |
| 1863 | -3.2938 | -14.0514 | 9481.14 | 0.07 | 0.091 | 3.26 | sí |

`examples/output/track.geojson` se puede abrir directamente en GitHub (se dibuja sobre un mapa).

### Con tus propias mediciones

CSV con columnas `t_s, altitude_km, speed_kmh` (ver `examples/data/measurements.csv`):

```bash
orbitas-rt track mis_mediciones.csv --out salida/ --extra 120
```

`--extra` propaga el estimado N segundos después de la última medición: es el caso
"se cortó la transmisión".

### OCR experimental

`src/orbitas_rt/ocr.py` intenta leer los números directamente del video del
webcast. Es experimental y no está probado contra un webcast real.

## Visualizaciones orbitales

### Órbita terrestre (datos reales)

```bash
python examples/run_leo_ground_track.py     # huella en tierra + vista ortográfica
python examples/run_web_ground_track.py     # mapa Leaflet autocontenido
python examples/run_real_starlink.py        # Starlink real desplegado por Starship Flight 15
python examples/run_chile_satellites.py     # SUCHAI-4, FASAT B, SSOT/FASAT-C, LEMU NGE
python examples/run_orbit3d.py              # modelo 3D con J2 y rotación terrestre (GMST)
```

### Trayectorias ilustrativas (NO son datos reales)

```bash
python examples/run_starship_track.py       # órbita LEO + arco suborbital del booster
python examples/run_starship_reentry.py     # reentrada y aproximación desde el Golfo
```

> B22 no fue capturado: abortó la aproximación y se estrelló en el Golfo.
> Ship 42 fue capturada en Starbase. Estos scripts son ilustrativos.

### Cislunar, Marcio y espacio profundo (JPL Horizons, datos reales)

```bash
python examples/run_lunar.py --list
python examples/run_lunar.py --sc -85       # LRO; -1024 Artemis II, -1176 CAPSTONE

python examples/run_mars.py --list
python examples/run_mars.py --sc -74        # MRO, crucero heliocéntrico
python examples/run_mars.py --sc -74 --center mars   # órbita marcocéntrica

python examples/run_deep_space.py --list
python examples/run_deep_space.py --sc -98  # New Horizons; -31 Voyager 1

python examples/run_lost_objects.py --list
python examples/run_lost_objects.py --sc -399080     # Apollo 8 S-IVB

python examples/run_escapade.py             # diagrama Tierra-L2 / Tierra-Marte
```

Ver [COORDINADAS.md](COORDINADAS.md) para saber qué marco se usa en cada caso.

### Determinación de órbitas

```bash
python examples/run_od.py                   # mínimos cuadrados, Gauss-Newton
```

## Servidor local y páginas web

```bash
python examples/serve.py                    # o doble clic en examples/serve.bat
```

Páginas:

| URL | Qué muestra |
|---|---|
| `http://localhost:8000/` | índice |
| `/dashboard.html` | panel unificado |
| `/query.html` | consulta por NORAD, órbitas, paso y fecha |
| `/tracking_stations.html` | estaciones con filtros por operador, región, tipo y función |
| `/lunar_map.html`, `/mars_map.html` | mapas canvas cislunar y marciano |
| `/live_track.html` | seguimiento "en vivo" |

APIs: `/api/lookup`, `/api/deep_search`, `/api/knowledge_base`, `/api/horizons`,
`/api/lunar`, `/api/query`, `/api/search`, `/api/groups`, `/api/stations`.

### Seguimiento en vivo

```bash
python examples/run_live_track.py --method gnss        # o satnogs / optical
python examples/run_live_track.py --auto --method satnogs
```

Muestra posición TLE, EKF estimada, última medición real y su antigüedad.
SatNOGS es real pero limitado; GNSS y óptico son simulados y están marcados como tal.

## Fuentes de datos

```bash
orbitas-rt sources --mission starship
```

- Documento legible: [SOURCES.md](SOURCES.md)
- Fuente editable: `src/orbitas_rt/sources.json`
- Cada fuente indica si está `verificada` (con fecha) o `sin verificar`.

Opcional: [Space-Track.org](SPACETRACK_SETUP.md) con cuenta gratuita y variables
`SPACETRACK_USER` / `SPACETRACK_PASS`. Si no están configuradas, se desactiva sin romper.

Estaciones y organismos: [TRACKING_ORGANIZATIONS.md](TRACKING_ORGANIZATIONS.md).
Incluye las correcciones históricas (Peldehue/Colina, SSOT = FASAT-Charlie, etc.).

## Limitaciones del modelo del filtro

- Altitud y rapidez no bastan para fijar la distancia recorrida; se infiere con el
  modelo, con un error de unos pocos km que no se elimina del todo.
- Modelo 2D simplificado: sin rotación terrestre, viento, sustentación ni vuelo
  no coplanar. Una nave real maniobra.
- Si el overlay da velocidad respecto de la superficie y el modelo usa inercial,
  hay un sesgo de hasta ~0.4 km/s en el ecuador.
- El perfil de vuelo suborbital es inventado: sustituye `VehicleParams` por el
  perfil publicado de la misión real.
- Una maniobra no anunciada durante un corte no se puede predecir; solo se corrige
  cuando vuelven las mediciones.
