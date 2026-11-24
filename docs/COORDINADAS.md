# Marcos de referencia: de la TLE al espacio profundo

La visualización cambia de **marco de referencia** (y de fuente) según la escala
de la misión. La lat/lon sobre el mapa terrestre solo tiene sentido mientras el
objeto sigue ligado a la Tierra. Para todo lo demás usamos **vectores de estado
de JPL Horizons** y cambiamos el origen del mapa.

## Tabla de marcos por régimen

| Régimen | Fuente | Origen / centro | Plano | Unidades | Visualización |
|---|---|---|---|---|---|
| LEO/MEO | CelesTrak GP + SGP4 | Tierra (ECI → ECEF) | TEME/ECI | km → lat/lon/alt | Leaflet sobre mapa terrestre |
| Translunar, L1/L2, NRHO | JPL Horizons | `center="399"` (Tierra) | `ECLIPTIC` | `KM-S` | canvas geocéntrico: Tierra al centro, Luna y nave |
| Viaje a Marte, espacio profundo | JPL Horizons | `center="@sun"` | `ECLIPTIC` | `AU-D` | canvas heliocéntrico: Sol al centro, órbitas Tierra/Marte |
| Órbita marciana | JPL Horizons | `center="499"` (Marte) | `ECLIPTIC` | `KM-S` | canvas marcocéntrico: Marte al centro, órbitas de referencia |
| Etapas "perdidas" (Apollo S-IVB, Centaur…) | JPL Horizons | `center="@sun"` | `ECLIPTIC` | `AU-D` | igual al caso heliocéntrico |

`ECLIPTIC` es la eclíptica J2000: un plano **inercial**, fijo respecto al Sol.
En cambio el marco TEME de una TLE gira con la Tierra.

## 1. Órbita terrestre (TLE + SGP4)

El TLE no es una posición: son elementos orbitales con época (inclinación,
RAAN, excentricidad, argumento del periapsis, anomalía media, movimiento medio).
El flujo es:

```
TLE (GP)  →  SGP4  →  vector ECI  →  GMST  →  ECEF  →  lat/lon/alt
```

- `orbit3d.py` / `tle.py`: propagación SGP4.
- `frames.py: eci_to_ecef()` usa el GMST real (IAU 2006, en `timeutils.py`).
- `frames.py: eci_to_geodetic()` entrega la lat/lon del **punto sub-satélite**,
  que es lo que se dibuja sobre el mapa Leaflet.
- El terminador día/noche se calcula aparte con la hora UTC:
  `subsolar_lon = 180 − hora_UTC · 15`.

```bash
python examples/run_leo_ground_track.py
```

## 2. Translunar, L1/L2 y cislunar

```python
fetch_vectors(id, inicio, fin, step="4 h",
              center="399", frame="ECLIPTIC", units="KM-S")
```

Devuelve `(x, y, z)` y `(vx, vy, vz)` en km relativos a la Tierra. La Luna se
pide con ID `301`, también relativa a `399`. En el canvas va la Tierra en el
origen, la órbita lunar de referencia (~384.400 km) y la trayectoria de la nave.

Cubre LRO, CAPSTONE, Artemis II, el módulo lunar Snoopy y cualquier objeto en
L1/L2 (para JWST/SOHO solo hay que escalar el canvas a ~1,5 × 10⁶ km).

**La lat/lon terrestre pierde sentido aquí**: el objeto ya no está "sobre" un
punto de la Tierra de forma útil, así que se dibuja el vector de estado, no su
proyección.

```bash
python examples/run_lunar.py --list
python examples/run_lunar.py --sc -1024   # Artemis II
```

## 3. Crucero a Marte y espacio profundo

```python
fetch_vectors(id, inicio, fin, step="1 d",
              center="@sun", frame="ECLIPTIC", units="AU-D")
```

Vectores en UA y velocidades en UA/día, con el Sol en el origen. Se dibujan las
órbitas de Tierra (1 UA) y Marte (1,5237 UA) como referencia. Es el esquema de
New Horizons, Voyager y de las etapas de cohete "perdidas".

```bash
python examples/run_mars.py --sc -168                # Perseverance, crucero heliocéntrico
python examples/run_deep_space.py --sc -98           # New Horizons
python examples/run_lost_objects.py --sc -399080     # Apollo 8 S-IVB
```

## 4. Órbita alrededor de Marte

Cuando la nave ya llegó, el análogo al caso lunar es cambiar el centro a Marte
(ID Horizons `499`) y trabajar en km:

```bash
python examples/run_mars.py --sc -74 --center mars   # MRO orbitando Marte
```

El canvas muestra Marte en el centro, su radio (~3.390 km), la órbita
areostática (~20.428 km) y las órbitas de Phobos (~9.376 km) y Deimos
(~23.463 km). El paso por defecto baja a 5 minutos porque un orbitador marciano
tiene un período de ~2 h: con `1 d` se perdería la órbita por aliasing.

Para sondas en superficie (Curiosity, Perseverance, InSight, Phoenix, MER), la
traza circular de radio ~3.390 km corresponde a la **rotación de Marte**, no a
una órbita. El script lo advierte en la salida.

## 5. Conversión local heliocéntrica (aproximación)

`frames.py: eci_to_heliocentric()` suma una posición circular aproximada de la
Tierra. Está marcada como estimación en el código; para valores reales siempre
se prefiere pedir el vector directamente a Horizons con `center="@sun"`.

## Regla mnemotécnica

> Si el objeto **comparte órbita con la Tierra** → TLE + SGP4 + lat/lon sobre el mapa.
> Si **se alejó pero se mide desde la Tierra** → vectores geocéntricos (`@399`, km).
> Si **se mide desde el Sol** → vectores heliocéntricos (`@sun`, UA).
> Si **ya orbita otro cuerpo** → vectores relativos a ese cuerpo (`@499`, km).

Horizons devuelve los tiempos como fecha juliana (JD, escala TDB);
`horizons.py: jd_to_date()` la convierte a fecha legible para las etiquetas.
