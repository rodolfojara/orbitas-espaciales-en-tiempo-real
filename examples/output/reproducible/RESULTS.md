# Resultados de la demo reproducible

Generado por `python examples/run_reproducible_demo.py`.
Los valores son una **simulación ilustrativa**, no un vuelo real.

## Entrada

- Archivo: `measurements.csv`
- SHA-256: `8dc27eb2ba414c9d2b4815ea3a9842c419441cf5cb0d11d11bf38260b3dd20e9`
- Mediciones: 1320
- Columnas: `t_s, altitude_km, speed_kmh` (altitud entera en km, rapidez entera en km/h)

Primeras 3 filas:

```csv
t_s,altitude_km,speed_kmh
1.0,0.0,15.0
2.0,0.0,51.0
3.0,0.0,57.0
```

Últimas 3 filas:

```csv
t_s,altitude_km,speed_kmh
1861.0,0.0,345.0
1862.0,0.0,333.0
1863.0,0.0,328.0
```

## Resultados (puntos de control)

| t (s) | altitud estimada (km) | velocidad (km/s) | σ altitud (km) | ¿hubo medición? |
|---:|---:|---:|---:|:--:|
| 0 | 0.000 | 0.0000 | 0.010 | no |
| 120 | 10.439 | 0.1953 | 0.070 | sí |
| 300 | 49.675 | 1.6942 | 0.115 | no |
| 420 | 108.027 | 4.8234 | 1.485 | no |
| 850 | 271.359 | 7.2446 | 0.130 | no |
| 950 | 279.961 | 7.2339 | 1.530 | no |
| 1000 | 279.980 | 7.2339 | 2.579 | no |
| 1150 | 262.919 | 7.2551 | 6.742 | no |
| 1300 | 228.407 | 7.3585 | 0.123 | sí |
| 1580 | 102.273 | 7.5161 | 0.130 | no |
| 1700 | 33.150 | 2.9726 | 1.087 | no |
| 1863 | 0.071 | 0.0909 | 0.040 | sí |

## Métricas

- Error máximo de altitud contra la verdad simulada: **2.572 km**
- Máxima σ de altitud sin medición: **6.742 km**
- Estimación final (T+1983 s): **-10.154 km**, **0.0851 km/s**

> La propagación extra de 120 s continúa después del contacto con el suelo;
> la altitud negativa es un artefacto del modelo (no detiene la nave en tierra).

## Verificar

```bash
python examples/run_reproducible_demo.py --check
```

Compara 69 valores contra `examples/data/reproducible_demo_expected.json`.
Devuelve `PASS` si la entrada y los resultados siguen siendo los mismos.
