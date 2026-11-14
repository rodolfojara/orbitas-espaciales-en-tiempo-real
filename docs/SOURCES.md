# Fuentes de datos

Actualizado: 2026-11-14. Este archivo se genera desde `src/orbitas_rt/sources.json` (`orbitas-rt sources --markdown docs/SOURCES.md`). Para agregar o corregir una fuente, edita el JSON, no este archivo.

**Estado de cada fuente**

- `verificada`: la existencia y el uso descrito se confirmaron con una búsqueda web el día indicado en 'checked'.
- `sin verificar`: viene de conocimiento previo; confirmar URL, formato y condiciones antes de depender de ella.

## Resumen

| Fuente | Misión | Entrega | Acceso | Estado |
|---|---|---|---|---|
| [Overlay del webcast oficial de SpaceX (altitud, velocidad, T+)](#webcast_overlay) | starship | altitud, rapidez | gratis, solo video | sin verificar |
| [Spaceflight Now - Starship live tracker / Orbital Tracker](#spaceflightnow_tracker) | starship | altitud, rapidez | gratis, página web | verificada (2026-11-14) |
| [FAA / avisos a navegantes (NOTAM, avisos marítimos) y zonas de peligro del vuelo](#faa_notam_hazard_areas) | starship | corredor y ventana nominal del vuelo, zona de reentrada y amerizaje | gratis | sin verificar |
| [Perfil de vuelo publicado por SpaceX (cronología de eventos por T+)](#spacex_flight_profile) | starship | eventos nominales (separación, apagado, reentrada) con tiempo T+ | gratis | sin verificar |
| [Cámaras públicas y observadores (transmisiones de terceros, cámaras del sitio de lanzamiento)](#visual_cross_check) | starship | confirmación visual de eventos (despegue, separación, anomalías) | gratis, varía según el canal | sin verificar |
| [JPL Horizons (efemérides y vectores de estado)](#jpl_horizons) | artemis, deep_space | estado completo (posición y velocidad), efemérides pasadas y predichas | gratis, sin registro | verificada (2026-11-14) |
| [NASA AROW (Artemis Real-time Orbit Website)](#nasa_arow) | artemis | posición, velocidad | gratis, sitio web y app de NASA | verificada (2026-11-14) |
| [Relé comunitario de AROW (artemis.cdnspace.ca)](#community_arow_relay) | artemis | telemetría tipo AROW (posición y velocidad), estado de antenas DSN | gratis, API abierta mantenida por la comunidad | verificada (2026-11-14) |
| [NASA DSN Now (Red de Espacio Profundo)](#dsn_now) | artemis, deep_space | qué antenas se comunican con cada nave, detalles de la señal | gratis | verificada (2026-11-14) |
| [Seguimiento Doppler por radioaficionados (AMSAT, SatNOGS)](#amateur_doppler) | artemis, deep_space, leo | velocidad radial (por efecto Doppler), telemetría de balizas | gratis la información | verificada (2026-11-14) |
| [Kernels SPICE de NAIF (trayectorias reconstruidas)](#naif_spice) | artemis, deep_space | trayectoria reconstruida con alta precisión, orientación y marcos de referencia | gratis | sin verificar |
| [CelesTrak (elementos orbitales TLE/OMM)](#celestrak) | leo | elementos orbitales para propagar con SGP4 | gratis, sin registro | sin verificar |
| [Space-Track.org (catálogo oficial del Departamento de Defensa de EE.UU.)](#space_track) | leo | elementos orbitales oficiales (GP/TLE) de objetos en órbita | gratis, requiere registro y aceptar condiciones de uso | sin verificar |

## Vuelo suborbital (Starship)

<a id="webcast_overlay"></a>
### Overlay del webcast oficial de SpaceX (altitud, velocidad, T+)

- **URL:** https://www.spacex.com/launches/
- **Qué entrega:** altitud, rapidez, tiempo T+
- **Latencia:** ~1 s (mientras dure la transmisión)
- **Acceso:** gratis, solo video; requiere leer los números (OCR) o transcribirlos a mano
- **Estado:** sin verificar
- **Uso en el proyecto:** Entrada principal del filtro (medición [altitud, rapidez]). Módulo experimental: orbitas_rt.ocr

**Pros**

- Es la fuente oficial y la que ya usa el modelo del proyecto (altitud y rapidez)
- Cadencia de ~1 Hz, suficiente para el filtro
- No necesita equipo ni cuenta

**Contras**

- Se pierde justo cuando se cae la transmisión (el problema que queremos resolver)
- Solo altitud y rapidez: no entrega posición, así que la distancia recorrida se infiere con el modelo
- Los valores son enteros (km, km/h) y el OCR puede equivocarse
- No está documentado si la velocidad es respecto de la superficie o inercial

<a id="spaceflightnow_tracker"></a>
### Spaceflight Now - Starship live tracker / Orbital Tracker

- **URL:** https://spaceflightnow.com/tracker/
- **Qué entrega:** altitud, rapidez, tiempo, traza sobre el mapa (ground track)
- **Latencia:** sin documentar
- **Acceso:** gratis, página web; no se encontró API pública documentada
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Solo contraste manual por ahora

**Pros**

- Ya muestra altitud, rapidez, tiempo y traza (voladas y predichas) en un mapa
- Sirve como referencia independiente para comparar con la estimación propia

**Contras**

- Es de terceros: no se sabe de dónde saca los datos (probablemente la misma telemetría del webcast)
- Si el webcast deja de informar, es probable que ellos también
- Sin API documentada: usarla en el filtro implicaría raspar la página, que puede cambiar o estar prohibido

<a id="faa_notam_hazard_areas"></a>
### FAA / avisos a navegantes (NOTAM, avisos marítimos) y zonas de peligro del vuelo

- **URL:** https://www.faa.gov/space
- **Qué entrega:** corredor y ventana nominal del vuelo, zona de reentrada y amerizaje
- **Latencia:** previa al vuelo (estático)
- **Acceso:** gratis
- **Estado:** sin verificar
- **Uso en el proyecto:** Define la trayectoria nominal y el acimut (geo.py) en lugar de los valores de ejemplo

**Pros**

- Entregan la ruta y las zonas de reentrada planificadas, con anticipación
- Permiten construir la trayectoria nominal por tiempo T+ (referencia cuando no hay datos)

**Contras**

- No son tiempo real: dicen dónde debería ir, no dónde está
- Las zonas son anchas y no dan altitud ni velocidad por instante
- Cambian si se reprograma el vuelo

<a id="spacex_flight_profile"></a>
### Perfil de vuelo publicado por SpaceX (cronología de eventos por T+)

- **URL:** https://www.spacex.com/launches/
- **Qué entrega:** eventos nominales (separación, apagado, reentrada) con tiempo T+
- **Latencia:** previa al vuelo (estático)
- **Acceso:** gratis
- **Estado:** sin verificar
- **Uso en el proyecto:** Ajuste de parámetros del modelo nominal

**Pros**

- Da hitos de tiempo para calibrar VehicleParams (duración del encendido, etc.)
- Útil para saber cuándo esperar un apagón de comunicaciones

**Contras**

- Nominal: no refleja anomalías ni cambios de último minuto
- Sin valores numéricos suficientes para un modelo de empuje fino

<a id="visual_cross_check"></a>
### Cámaras públicas y observadores (transmisiones de terceros, cámaras del sitio de lanzamiento)

- **Qué entrega:** confirmación visual de eventos (despegue, separación, anomalías)
- **Latencia:** tiempo real, manual
- **Acceso:** gratis, varía según el canal
- **Estado:** sin verificar
- **Uso en el proyecto:** Ancla de tiempo (T+0) y verificación humana

**Pros**

- Independiente del webcast oficial
- Sirve para fijar el instante T+0 y confirmar si hubo una anomalía

**Contras**

- No entrega coordenadas ni cifras; es manual
- Disponible solo cerca del sitio y solo durante parte del vuelo


## Artemis y misiones lunares

<a id="jpl_horizons"></a>
### JPL Horizons (efemérides y vectores de estado)

- **URL:** https://ssd.jpl.nasa.gov/horizons/
- **Qué entrega:** estado completo (posición y velocidad), efemérides pasadas y predichas
- **Latencia:** bajo demanda; depende de cuándo NASA/JPL publique la trayectoria de la misión
- **Acceso:** gratis, sin registro; interfaz web y API
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Estado inicial y verdad de referencia para el modo espacio profundo (en la hoja de ruta)

**Pros**

- Fuente oficial de la trayectoria de Orion: en Artemis II se usó para reconstruir su trayectoria real
- Entrega el estado completo, que es justo el estado inicial que necesita el propagador
- También cubre sondas, planetas y la Luna para el modelo de N cuerpos

**Contras**

- Una misión solo aparece cuando JPL la publica: para Artemis III aún no hay efemérides (la misión no ha volado)
- Predicho y reconstruido difieren; tras una maniobra el dato se actualiza con retraso
- Hay que respetar las condiciones de uso de la API (límite de consultas sin documentar aquí)

<a id="nasa_arow"></a>
### NASA AROW (Artemis Real-time Orbit Website)

- **URL:** https://www.nasa.gov/trackartemis
- **Qué entrega:** posición, velocidad, distancia a la Tierra y a la Luna, tiempo de misión, vectores de estado y archivo de efemérides descargable
- **Latencia:** casi tiempo real; se alimenta de los datos que Orion envía a Houston
- **Acceso:** gratis, sitio web y app de NASA
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Vectores de estado para reinicializar el filtro tras un corte

**Pros**

- Oficial; muestra velocidad, distancia y tiempo de misión
- NASA ha publicado vectores de estado y una efeméride descargable en misiones Artemis
- Se alimenta de la telemetría real de la nave

**Contras**

- Es una interfaz web: no se encontró una API oficial documentada
- Depende del enlace de datos con Houston: si la nave no transmite, tampoco hay datos
- Los vectores de estado se publican en momentos puntuales, no de forma continua

<a id="community_arow_relay"></a>
### Relé comunitario de AROW (artemis.cdnspace.ca)

- **URL:** https://artemis.cdnspace.ca
- **Qué entrega:** telemetría tipo AROW (posición y velocidad), estado de antenas DSN
- **Latencia:** ~1 s (flujo SSE); respaldo por consulta cada 5 s
- **Acceso:** gratis, API abierta mantenida por la comunidad
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Candidata para el modo 'en vivo', siempre con Horizons como respaldo

**Pros**

- Entrega los datos en un formato fácil de consumir por programa (flujo continuo)
- Otros trackers de aficionados lo usan como fuente primaria con respaldo en Horizons

**Contras**

- No es oficial ni está afiliado a NASA: puede cambiar o desaparecer sin aviso
- La existencia y descripción vienen de la página de otro tracker aficionado; no la probé directamente
- No hay garantía de exactitud ni de continuidad

<a id="dsn_now"></a>
### NASA DSN Now (Red de Espacio Profundo)

- **URL:** https://eyes.nasa.gov/dsn/dsn.html
- **Qué entrega:** qué antenas se comunican con cada nave, detalles de la señal, tiempo de luz de ida y vuelta (round-trip light time)
- **Latencia:** se actualiza cada ~5 a 60 s según la fuente (XML de NASA: ~60 s)
- **Acceso:** gratis; datos en XML en eyes.nasa.gov/dsn/data/dsn.xml
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Medición de rango para espacio profundo (hoja de ruta)

**Pros**

- El tiempo de luz de ida y vuelta equivale a una medición de distancia (rango) a la nave: sirve como medición adicional para el filtro
- Confirma si hay enlace activo con la nave en este momento
- Oficial y gratuito

**Contras**

- Solo cubre naves que usan la DSN (no LEO ni Starship)
- Actualización lenta comparada con 1 Hz
- El formato XML no tiene garantía de estabilidad

<a id="amateur_doppler"></a>
### Seguimiento Doppler por radioaficionados (AMSAT, SatNOGS)

- **URL:** https://www.amsat.org
- **Qué entrega:** velocidad radial (por efecto Doppler), telemetría de balizas
- **Latencia:** tiempo real, con equipo propio o de la red
- **Acceso:** gratis la información; recibir señales requiere antena y receptor SDR
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Medición de velocidad radial para cubesats y misiones lunares (hoja de ruta)

**Pros**

- Medición física independiente de NASA y de cualquier webcast
- En Artemis I se siguieron balizas de 70 cm de un cubesat con herramientas como Horizons (según AMSAT)

**Contras**

- Solo funciona si la nave o un cubesat acompañante transmite en bandas de aficionados
- Requiere equipo, ubicación con visibilidad y conocimiento técnico
- Orion y Starship no emiten señales que un aficionado pueda usar como balizas

<a id="naif_spice"></a>
### Kernels SPICE de NAIF (trayectorias reconstruidas)

- **URL:** https://naif.jpl.nasa.gov/naif/
- **Qué entrega:** trayectoria reconstruida con alta precisión, orientación y marcos de referencia
- **Latencia:** posterior a la misión (o por tramos)
- **Acceso:** gratis; se leen con spiceypy
- **Estado:** sin verificar
- **Uso en el proyecto:** Validación post-vuelo del modo espacio profundo

**Pros**

- La trayectoria más precisa que existe tras la misión
- Sirve para validar el filtro con datos reales después del vuelo

**Contras**

- No sirve en tiempo real
- Hay que descargar y administrar kernels grandes


## Espacio profundo

<a id="jpl_horizons"></a>
### JPL Horizons (efemérides y vectores de estado)

- **URL:** https://ssd.jpl.nasa.gov/horizons/
- **Qué entrega:** estado completo (posición y velocidad), efemérides pasadas y predichas
- **Latencia:** bajo demanda; depende de cuándo NASA/JPL publique la trayectoria de la misión
- **Acceso:** gratis, sin registro; interfaz web y API
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Estado inicial y verdad de referencia para el modo espacio profundo (en la hoja de ruta)

**Pros**

- Fuente oficial de la trayectoria de Orion: en Artemis II se usó para reconstruir su trayectoria real
- Entrega el estado completo, que es justo el estado inicial que necesita el propagador
- También cubre sondas, planetas y la Luna para el modelo de N cuerpos

**Contras**

- Una misión solo aparece cuando JPL la publica: para Artemis III aún no hay efemérides (la misión no ha volado)
- Predicho y reconstruido difieren; tras una maniobra el dato se actualiza con retraso
- Hay que respetar las condiciones de uso de la API (límite de consultas sin documentar aquí)

<a id="dsn_now"></a>
### NASA DSN Now (Red de Espacio Profundo)

- **URL:** https://eyes.nasa.gov/dsn/dsn.html
- **Qué entrega:** qué antenas se comunican con cada nave, detalles de la señal, tiempo de luz de ida y vuelta (round-trip light time)
- **Latencia:** se actualiza cada ~5 a 60 s según la fuente (XML de NASA: ~60 s)
- **Acceso:** gratis; datos en XML en eyes.nasa.gov/dsn/data/dsn.xml
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Medición de rango para espacio profundo (hoja de ruta)

**Pros**

- El tiempo de luz de ida y vuelta equivale a una medición de distancia (rango) a la nave: sirve como medición adicional para el filtro
- Confirma si hay enlace activo con la nave en este momento
- Oficial y gratuito

**Contras**

- Solo cubre naves que usan la DSN (no LEO ni Starship)
- Actualización lenta comparada con 1 Hz
- El formato XML no tiene garantía de estabilidad

<a id="amateur_doppler"></a>
### Seguimiento Doppler por radioaficionados (AMSAT, SatNOGS)

- **URL:** https://www.amsat.org
- **Qué entrega:** velocidad radial (por efecto Doppler), telemetría de balizas
- **Latencia:** tiempo real, con equipo propio o de la red
- **Acceso:** gratis la información; recibir señales requiere antena y receptor SDR
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Medición de velocidad radial para cubesats y misiones lunares (hoja de ruta)

**Pros**

- Medición física independiente de NASA y de cualquier webcast
- En Artemis I se siguieron balizas de 70 cm de un cubesat con herramientas como Horizons (según AMSAT)

**Contras**

- Solo funciona si la nave o un cubesat acompañante transmite en bandas de aficionados
- Requiere equipo, ubicación con visibilidad y conocimiento técnico
- Orion y Starship no emiten señales que un aficionado pueda usar como balizas

<a id="naif_spice"></a>
### Kernels SPICE de NAIF (trayectorias reconstruidas)

- **URL:** https://naif.jpl.nasa.gov/naif/
- **Qué entrega:** trayectoria reconstruida con alta precisión, orientación y marcos de referencia
- **Latencia:** posterior a la misión (o por tramos)
- **Acceso:** gratis; se leen con spiceypy
- **Estado:** sin verificar
- **Uso en el proyecto:** Validación post-vuelo del modo espacio profundo

**Pros**

- La trayectoria más precisa que existe tras la misión
- Sirve para validar el filtro con datos reales después del vuelo

**Contras**

- No sirve en tiempo real
- Hay que descargar y administrar kernels grandes


## Órbita terrestre baja (LEO)

<a id="amateur_doppler"></a>
### Seguimiento Doppler por radioaficionados (AMSAT, SatNOGS)

- **URL:** https://www.amsat.org
- **Qué entrega:** velocidad radial (por efecto Doppler), telemetría de balizas
- **Latencia:** tiempo real, con equipo propio o de la red
- **Acceso:** gratis la información; recibir señales requiere antena y receptor SDR
- **Estado:** verificada (revisada el 2026-11-14)
- **Uso en el proyecto:** Medición de velocidad radial para cubesats y misiones lunares (hoja de ruta)

**Pros**

- Medición física independiente de NASA y de cualquier webcast
- En Artemis I se siguieron balizas de 70 cm de un cubesat con herramientas como Horizons (según AMSAT)

**Contras**

- Solo funciona si la nave o un cubesat acompañante transmite en bandas de aficionados
- Requiere equipo, ubicación con visibilidad y conocimiento técnico
- Orion y Starship no emiten señales que un aficionado pueda usar como balizas

<a id="celestrak"></a>
### CelesTrak (elementos orbitales TLE/OMM)

- **URL:** https://celestrak.org
- **Qué entrega:** elementos orbitales para propagar con SGP4
- **Latencia:** se actualizan cada cierto tiempo (horas a días)
- **Acceso:** gratis, sin registro
- **Estado:** sin verificar
- **Uso en el proyecto:** Fuera del alcance actual; útil si se agrega el modo LEO

**Pros**

- Muy fácil de usar con skyfield, sgp4 o satellite.js
- Cubre ISS, Starlink, cubesats y la mayoría de objetos en órbita terrestre

**Contras**

- Solo órbita terrestre: no sirve para vuelos suborbitales ni para el espacio profundo
- La precisión es del orden de kilómetros y empeora con la antigüedad del TLE
- No refleja maniobras recientes

<a id="space_track"></a>
### Space-Track.org (catálogo oficial del Departamento de Defensa de EE.UU.)

- **URL:** https://www.space-track.org
- **Qué entrega:** elementos orbitales oficiales (GP/TLE) de objetos en órbita
- **Latencia:** se actualiza varias veces al día
- **Acceso:** gratis, requiere registro y aceptar condiciones de uso
- **Estado:** sin verificar
- **Uso en el proyecto:** Fuera del alcance actual (modo LEO)

**Pros**

- Fuente primaria del catálogo, con historial
- Buena cobertura de objetos en órbita

**Contras**

- Requiere cuenta y respetar límites de consultas
- Solo órbita terrestre

## Cómo combinarlas

Ninguna fuente alcanza sola. Orden sugerido de prioridad según la misión:

1. **Starship:** overlay del webcast (medición) → trayectoria nominal de FAA/SpaceX (referencia cuando se corta) → contraste visual/Spaceflight Now.
2. **Artemis / espacio profundo:** estado inicial de Horizons o AROW → propagación de N cuerpos → mediciones de rango (DSN Now) y Doppler (radioaficionados) cuando existan.
3. **LEO:** TLE de CelesTrak o Space-Track con SGP4.

Regla general: cada fuente debe entrar al filtro como una **medición con su propio ruido**, y el sistema debe poder seguir funcionando (solo propagando) si todas fallan.
