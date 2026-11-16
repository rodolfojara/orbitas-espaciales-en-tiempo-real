"""Modo 'en vivo': seguimiento en tiempo real con TLE + EKF 3D.

Demuestra la idea del usuario: combinar TLE (estado inicial) con mediciones
para obtener una estimación mejor que el TLE puro, actualizada cada segundo.

Uso:
  1. Ejecutar:  python examples/run_live_track.py
  2. Abrir:     http://localhost:8000/live_track.html (via serve.bat)
  El script corre 120 s y escribe live_position.json cada segundo.
"""
import os
import sys
import json
import ssl
import time
import urllib.request
from datetime import datetime, timezone, timedelta

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sgp4.api import Satrec, jday
from sgp4 import omm
from orbitas_rt.tle import fetch_gp
from orbitas_rt.ekf3d import EKF3D
from orbitas_rt.orbit3d import eci_to_geodetic

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

# Satélite a seguir (ISS por defecto; cambia catnr para otro)
CATNR = 25544  # ISS

ctx = ssl._create_unverified_context()
gp = fetch_gp(CATNR)
print("Satélite:", gp["OBJECT_NAME"], "NORAD", gp["NORAD_CAT_ID"])
print("Epoch TLE:", gp["EPOCH"])

sat = Satrec()
omm.initialize(sat, gp)

# Estado inicial desde el TLE (en la época del TLE)
t0 = datetime.fromisoformat(gp["EPOCH"].replace("Z", "+00:00"))
if t0.tzinfo is None:
    t0 = t0.replace(tzinfo=timezone.utc)
r0, v0 = None, None
jd0, fr0 = None, None
# obtener r,v en la época
jd0, fr0 = jday(t0.year, t0.month, t0.day, t0.hour, t0.minute,
                 t0.second + t0.microsecond / 1e6)
e0, r0, v0 = sat.sgp4(jd0, fr0)
r0 = np.array(r0) * 1000.0
v0 = np.array(v0) * 1000.0
print("r0 (km):", [round(x/1000, 1) for x in r0])

# EKF inicializado con el estado del TLE + incertidumbre
P0 = np.diag([1000.0**2]*3 + [10.0**2]*3)  # 1 km pos, 10 m/s vel
ekf = EKF3D(np.concatenate([r0, v0]), P0, q_accel=0.5)

DURATION = 120  # segundos
R_MEAS = np.diag([500.0**2]*3)  # medición de posición con ruido 500 m

print("Corriendo modo en vivo por %d s..." % DURATION)
start = time.time()
for i in range(DURATION):
    now = datetime.now(timezone.utc)
    # tiempo desde la época del TLE (para SGP4)
    dt_from_epoch = (now - t0).total_seconds()
    # posición "real" (SGP4)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute,
                  now.second + now.microsecond / 1e6)
    e, r_sgp, v_sgp = sat.sgp4(jd, fr)
    if e != 0:
        print("SGP4 error", e)
        time.sleep(1)
        continue
    r_true = np.array(r_sgp) * 1000.0
    # medición con ruido
    meas = r_true + np.random.normal(0, 500.0, 3)

    # EKF: predecir 1 s, luego actualizar con la medición
    ekf.predict(1.0)
    ekf.update(meas, R_MEAS)

    # convertir a lat/lon/alt
    lat_tle, lon_tle, alt_tle = eci_to_geodetic(r_true, dt_from_epoch)
    lat_ekf, lon_ekf, alt_ekf = ekf.latlonalt(dt_from_epoch)
    lat_meas, lon_meas, alt_meas = eci_to_geodetic(meas, dt_from_epoch)

    payload = {
        "t": now.isoformat(),
        "elapsed": i + 1,
        "tle": {"lat": lat_tle, "lon": lon_tle, "alt": alt_tle},
        "ekf": {"lat": lat_ekf, "lon": lon_ekf, "alt": alt_ekf},
        "meas": {"lat": lat_meas, "lon": lon_meas, "alt": alt_meas},
        "sat": gp["OBJECT_NAME"],
    }
    with open(os.path.join(out, "live_position.json"), "w") as f:
        json.dump(payload, f)

    if i % 10 == 0 or i == DURATION - 1:
        print("  t=%3d  TLE=%.2f,%.2f  EKF=%.2f,%.2f" % (
            i + 1, lat_tle, lon_tle, lat_ekf, lon_ekf))

    time.sleep(1.0)

print("Listo. live_position.json actualizado cada segundo.")