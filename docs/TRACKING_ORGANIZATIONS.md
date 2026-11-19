# Organismos y redes de rastreo de satélites y objetos espaciales

Documento de referencia sobre las organizaciones que rastrean objetos en órbita,
sus instrumentos, procedimientos y fuentes de datos. Complementa el mapa de
estaciones (`examples/output/tracking_stations.html`).

---

## 1. Organismos oficiales de rastreo

### NASA Deep Space Network (DSN)
- **Operador**: NASA / JPL
- **Estaciones**: Goldstone (California), Madrid (España), Canberra (Australia)
- **Instrumentos**: Antenas de 34 m y 70 m, banda S/X/Ka
- **Procedimiento**: Ranging (medición de distancia) + Doppler (velocidad radial) + VLBI (interferometría). Tracking continuo de naves interplanetarias.
- **Historia**: Operativa desde 1963 (proyecto Apollo). Red global para espacio profundo.
- **Datos públicos**: JPL Horizons (efemérides), DSN Now (estado en tiempo real).

### ESA ESTRACK
- **Operador**: ESA
- **Estaciones**: Cebreros (España), Malargüe (Argentina), New Norcia (Australia), Kourou (Guayana), Santa Maria (Azores), Kiruna (Suecia), Redu (Bélgica), Maspalomas (Canarias)
- **Instrumentos**: Antenas de 15 m (LEO) y 35 m (espacio profundo), banda S/X/Ka
- **Procedimiento**: Ranging, Doppler, telemetría. Red global para misiones ESA.
- **Historia**: Desarrollada desde los años 70. Malargüe (2012) es la estación más nueva.
- **Datos públicos**: ESA SSA (Space Situational Awareness).

### Roscosmos
- **Operador**: Agencia Espacial Rusa
- **Estaciones**: Medvezhy Ozera (cerca de Moscú), Ussuriysk, Evpatoria (Crimea)
- **Instrumentos**: Antenas parabólicas, radar
- **Procedimiento**: Rastreo de satélites y naves (Soyuz, Progress, ISS). Red heredada de la URSS.
- **Historia**: Red de la era soviética, modernizada parcialmente.

### CNSA (China National Space Administration)
- **Operador**: CNSA
- **Estaciones**: Kashgar, Jiamusi, Kashi (espacio profundo); Neuquén (Argentina, acuerdo bilateral); Swakopmund (Namibia)
- **Instrumentos**: Antenas de 35 m (espacio profundo), 18 m (LEO)
- **Procedimiento**: Rastreo de misiones lunares y marcianas (Chang'e, Tianwen). Red en expansión global.
- **Historia**: Desarrollada desde 2000s. Neuquén (2018) es la primera estación en el hemisferio sur.
- **Nota**: La estación de Neuquén es operada por CNSA en territorio argentino (acuerdo bilateral), no por CONAE.

### CONAE (Comisión Nacional de Actividades Espaciales, Argentina)
- **Operador**: CONAE
- **Estaciones**: Córdoba (Centro Espacial Teófilo Tabanera), Falda del Carmen, Malargüe (CETT)
- **Instrumentos**: Antenas de seguimiento, centro de control
- **Procedimiento**: Seguimiento de satélites argentinos (SAOCOM, ARSAT). Recepción de datos.
- **Historia**: Desarrollada desde los 90s. Centro Espacial Teófilo Tabanera (CETT) en Córdoba.

### SSC (Swedish Space Corporation)
- **Operador**: SSC
- **Estaciones**: Kiruna (Suecia), Dongara (Australia), South Point (Hawaii), North Pole (Alaska), Santiago/Peldehue (Chile), etc.
- **Instrumentos**: Antenas de diversos tamaños
- **Procedimiento**: Servicios comerciales de seguimiento y telemetría (TT&C) para satélites LEO.
- **Historia**: Fundada en 1972. Red global de estaciones.
- **Nota sobre Peldehue**: Construida por NASA ~1965 (acuerdo con gobierno chileno). Traspasada a la Universidad de Chile (unidad independiente). Luego vendida a SSC (~2000s). La FACH no tuvo relación con esta estación.

### KSAT (Kongsberg Satellite Services)
- **Operador**: KSAT (Noruega)
- **Estaciones**: Svalbard (Noruega), Troll (Antártida), Inuvik (Canadá), Punta Arenas (Chile), Antofagasta (Chile), etc.
- **Instrumentos**: Antenas de diversos tamaños
- **Procedimiento**: Servicios comerciales de TT&C y downlink para satélites LEO/MEO. Red polar global.
- **Historia**: Fundada en 2002 (fusión de Kongsberg y Telenor).

### INTA (Instituto Nacional de Técnica Aeroespacial, España)
- **Operador**: INTA
- **Estaciones**: Maspalomas (Gran Canaria, España), Torrejón (Madrid, España)
- **Nota**: INTA NO tiene estación en Santiago de Chile. Las estaciones INTA están en España.
- **Instrumentos**: Antenas de seguimiento
- **Procedimiento**: Seguimiento de satélites, telemetría.

### ISRO (Indian Space Research Organisation)
- **Estaciones**: Sriharikota, Bangalore, etc.
- **Instrumentos**: Red de seguimiento y comando (ISTRAC)
- **Procedimiento**: Seguimiento de satélites y lanzamientos indios.

### JAXA (Japan Aerospace Exploration Agency)
- **Estaciones**: Tanegashima, Uchinoura, etc.
- **Instrumentos**: Red de seguimiento y comando
- **Procedimiento**: Seguimiento de satélites y misiones lunares (SLIM, Hayabusa).

### KARI (Korea Aerospace Research Institute)
- **Estaciones**: Naro Space Center, Daejeon
- **Instrumentos**: Red de seguimiento y comando (KGSN)
- **Procedimiento**: Seguimiento de satélites coreanos (Danuri/KPLO). Usa estaciones propias + acuerdos con NASA (DSN) para misiones lunares.

### ISRO (Indian Space Research Organisation) — cómo obtiene datos
- **Red propia**: ISTRAC (Indian Space Research Organisation Telemetry, Tracking and Command Network). Estaciones en Sriharikota, Bangalore, Lucknow, Mauritius, Brunei, Indonesia, etc.
- **Instrumentos**: Antenas de 18m y 32m, radar, telemetría.
- **Procedimiento**: Seguimiento de satélites y lanzamientos indios. Para misiones interplanetarias (Chandrayaan, Mangalyaan) usa DSN de NASA (acuerdo) + estaciones propias.
- **Historia**: Desarrollada desde los 70s. Red global con estaciones en varios países.

### JAXA (Japan Aerospace Exploration Agency) — cómo obtiene datos
- **Red propia**: JAXA Tracking Network. Estaciones en Tsukuba, Uchinoura, Tanegashima, Okinawa, etc.
- **Instrumentos**: Antenas de 10m, 20m, 34m, 64m (Usuda). Radar.
- **Procedimiento**: Seguimiento de satélites y misiones lunares/marcianas (Hayabusa, SLIM, MMX). Para espacio profundo usa Usuda Deep Space Center (64m) + acuerdos con NASA DSN y ESA ESTRACK.
- **Historia**: Desarrollada desde los 60s (NASDA, ISAS). Usuda es la estación de espacio profundo japonesa.
- **Nota**: SLIM (2023) y Hayabusa2 usaron la red JAXA + DSN de NASA.

### KARI — cómo obtiene datos
- **Red propia**: KGSN (Korea Ground Station Network). Estaciones en Naro, Daejeon.
- **Procedimiento**: Seguimiento de satélites coreanos. Para Danuri/KPLO (misión lunar) usa DSN de NASA (acuerdo) + estaciones propias.
- **Historia**: Desarrollada desde los 2000s. Danuri es la primera misión lunar coreana.

### Nota sobre agencias medianas
Las agencias de tamaño medio (ISRO, JAXA, KARI, CONAE, etc.) **no tienen redes globales completas**. Para misiones interplanetarias o lunares, dependen de:
1. **Acuerdos con NASA DSN** (Goldstone, Madrid, Canberra) — el más común.
2. **Acuerdos con ESA ESTRACK** (Cebreros, Malargüe, New Norcia).
3. **Estaciones propias** para LEO/MEO.
4. **Redes comerciales** (KSAT, SSC) para seguimiento rutinario.

---

## 2. Redes de rastreo abiertas / ciudadanas

### SatNOGS (Satellite Networked Open Ground Station)
- **Operador**: Libre Space Foundation (comunidad open source)
- **Estaciones**: Red global de estaciones de radioaficionados y voluntarios
- **Instrumentos**: Antenas VHF/UHF, SDR (Software Defined Radio)
- **Procedimiento**: Recepción de señales de satélites, medición de Doppler, decodificación de telemetría. Datos públicos.
- **Historia**: Fundada en 2014. Red más grande de estaciones de tierra abiertas.
- **Datos**: API pública (https://network.satnogs.org/api/)

### SeeSat-L
- **Operador**: Comunidad de observadores de satélites
- **Instrumentos**: Telescopios, cámaras, observación visual
- **Procedimiento**: Reportes de pasos de satélites (flash, posición, brillo). Astrometría amateur.
- **Historia**: Lista de correo desde los 90s. Observadores en todo el mundo.

### Heavens-Above
- **Operador**: Chris Peat (individual)
- **Instrumentos**: Base de datos de TLE + cálculos de pasos
- **Procedimiento**: Predicción de pasos visibles de satélites.
- **Historia**: Uno de los sitios más usados por aficionados desde 1998.

---

## 3. Observación complementaria del cielo

### Meteoritos y bólidos
- **American Meteor Society (AMS)**: red de observadores de meteoros y bólidos. Reportes de fireballs.
- **International Meteor Organization (IMO)**: red global de observación de meteoros.
- **CAMS (Cameras for All-sky Meteor Surveillance)**: red de cámaras de todo el cielo para detección de meteoros.
- **Instrumentos**: Cámaras de todo el cielo, espectrógrafos, radares meteor.

### Rayos cósmicos
- **Pierre Auger Observatory**: Observatorio de rayos cósmicos en Malargüe, Argentina. Detecta rayos cósmicos de ultra-alta energía.
- **IceCube**: Observatorio de neutrinos en el Polo Sur.
- **AMS-02**: Espectrómetro magnético en la ISS (rayos cósmicos).
- **Instrumentos**: Detectores de partículas, tanques de agua Cherenkov, telescopios de fluorescencia.

### Observación astronómica general
- **ESO (European Southern Observatory)**: Observatorios en Chile (Paranal, La Silla, ALMA). Observación del cielo profundo.
- **ALMA**: Radiotelescopio en el desierto de Atacama (Chile).
- **VLT (Very Large Telescope)**: Paranal, Chile.
- **Instrumentos**: Telescopios ópticos/infrarrojos, radiotelescopios, interferómetros.

### Satélites de observación terrestre
- **Sentinel (ESA)**: constelación de observación terrestre.
- **Landsat (NASA/USGS)**: observación terrestre desde 1972.
- **Planet (Planet Labs)**: constelación de microsatélites de observación.

---

## 4. Notas sobre la fiabilidad de las fuentes

- **Agencias oficiales** (NASA, ESA, etc.) dependen de sus gobiernos y pueden tener sesgos o restricciones en la publicación de datos.
- **Redes ciudadanas** (SatNOGS, SeeSat) suelen ser más transparentes y rápidas en reportar anomalías.
- **La mejor aproximación** combina múltiples fuentes: TLE (estado inicial) + mediciones (corrección) + efemérides (referencia).
- **Tu proyecto** ya implementa esta idea con el EKF 3D + fuentes de medición.

---

## 5. Referencias

- NASA DSN: https://eyes.nasa.gov/dsn/dsn.html
- ESA ESTRACK: https://www.esa.int/Enabling_Support/Operations/ESTRACK
- SatNOGS: https://satnogs.org/
- SeeSat-L: https://www.satobs.org/
- Heavens-Above: https://www.heavens-above.com/
- Pierre Auger: https://www.auger.org/
- ESO: https://www.eso.org/