"""Modo 'en vivo': seguimiento en tiempo real con TLE + EKF 3D.

Demuestra la idea del usuario: combinar TLE (estado inicial) con mediciones
para obtener una estimación mejor que el TLE puro, actualizada cada segundo.

Métodos de medición (seleccionables con --method):
  satnogs  : SatNOGS (Doppler, red abierta) — usa última observación real
  gnss     : GNSS a bordo simulado (ruido ~10 m)
  optical  : Astrometría simulada (ruido ~1 km)

Uso:
  python examples/run_live_track.py --method gnss
  # en otra terminal: cd examples/output && python -m http.server 8000
  # abrir http://localhost:8000/live_track.html
"""
import os
import sys
import json
import ssl
import time
import argparse
import urllib.request
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sgp4.api import Satrec, jday
from sgp4 import omm
from orbitas_rt.tle import fetch_gp
from orbitas_rt.ekf3d import EKF3D
from orbitas_rt.orbit3d import eci_to_geodetic
from orbitas_rt.measurements import (SimulatedGNSSSource, SimulatedOpticalSource,
                                    SatNOGSSource, quality_from_age)

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--catnr", type=int, default=25544, help="NORAD_CAT_ID (default ISS)")
parser.add_argument("--method", choices=["satnogs", "gnss", "optical"], default="gnss")
parser.add_argument("--duration", type=int, default=120, help="segundos")
parser.add_argument("--auto", action="store_true", help="Elegir satélite con obs SatNOGS recientes")
args = parser.parse_args()

if args.auto:
    from orbitas_rt.measurements import find_satellites_with_recent_obs
    cands = find_satellites_with_recent_obs(hours=24, limit=10)
    if cands:
        print("Satélites con observaciones SatNOGS recientes:")
        for norad, tx, ts, tle in cands[:10]:
            print("  NORAD %s  obs_end=%s  %s" % (norad, ts.isoformat(), tx))
        args.catnr = cands[0][0]
        print("Usando NORAD %d" % args.catnr)
    else:
        print("No se encontraron observaciones recientes; usando default.")

ctx = ssl._create_unverified_context()
gp = fetch_gp(args.catnr)
print("Satélite:", gp["OBJECT_NAME"], "NORAD", gp["NORAD_CAT_ID"])
print("Epoch TLE:", gp["EPOCH"])
print("Método de medición:", args.method)

sat = Satrec()
omm.initialize(sat, gp)

t0 = datetime.fromisoformat(gp["EPOCH"].replace("Z", "+00:00"))
if t0.tzinfo is None:
    t0 = t0.replace(tzinfo=timezone.utc)

jd0, fr0 = jday(t0.year, t0.month, t0.day, t0.hour, t0.minute,
                 t0.second + t0.microsecond / 1e6)
e0, r0, v0 = sat.sgp4(jd0, fr0)
r0 = np.array(r0) * 1000.0
v0 = np.array(v0) * 1000.0

P0 = np.diag([1000.0**2] * 3 + [10.0**2] * 3)
ekf = EKF3D(np.concatenate([r0, v0]), P0, q_accel=0.5)

# Fuente de medición
if args.method == "satnogs":
    meas_source = SatNOGSSource(args.catnr)
elif args.method == "optical":
    meas_source = SimulatedOpticalSource(noise_m=1000.0)
else:
    meas_source = SimulatedGNSSSource(noise_m=10.0)

R_MEAS = np.diag([500.0**2] * 3)

print("Corriendo modo en vivo por %d s..." % args.duration)
last_meas = None
last_meas_time = None

for i in range(args.duration):
    now = datetime.now(timezone.utc)
    dt_from_epoch = (now - t0).total_seconds()

    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute,
                  now.second + now.microsecond / 1e6)
    e, r_sgp, v_sgp = sat.sgp4(jd, fr)
    if e != 0:
        print("SGP4 error", e)
        time.sleep(1)
        continue
    r_true = np.array(r_sgp) * 1000.0
    lat_tle, lon_tle, alt_tle = eci_to_geodetic(r_true, dt_from_epoch)

    # Obtener medición según el método
    meas_eci = None
    meas_time = None
    meas_lat = meas_lon = meas_alt = lat_tle, lon_tle, alt_tle
    if args.method == "gnss":
        m = meas_source.latest(lat_tle, lon_tle, alt_tle)
        meas_lat, meas_lon, meas_alt = m.lat, m.lon, m.alt
        meas_eci = r_true + np.random.normal(0, meas_source.noise_m, 3)
        meas_time = now
    elif args.method == "optical":
        m = meas_source.latest(lat_tle, lon_tle, alt_tle)
        meas_lat, meas_lon, meas_alt = m.lat, m.lon, m.alt
        meas_eci = r_true + np.random.normal(0, meas_source.noise_m, 3)
        meas_time = now
    else:  # satnogs
        m = meas_source.latest()
        if m is not None and m.lat is None:
            ts = m.timestamp
            dt_m = (ts - t0).total_seconds()
            jd_m, fr_m = jday(ts.year, ts.month, ts.day, ts.hour, ts.minute,
                              ts.second + ts.microsecond / 1e6)
            e_m, r_m, v_m = sat.sgp4(jd_m, fr_m)
            if e_m == 0:
                meas_eci = np.array(r_m) * 1000.0
                meas_time = ts
                mla, mlo, mal = eci_to_geodetic(meas_eci, dt_m)
                meas_lat, meas_lon, meas_alt = mla, mlo, mal
        if meas_eci is None:
            # Sin observación SatNOGS reciente: usar medición simulada
            meas_eci = r_true + np.random.normal(0, 500.0, 3)
            meas_time = now
            meas_lat, meas_lon, meas_alt = lat_tle, lon_tle, alt_tle
            if i == 0:
                print("  (SatNOGS: sin observaciones completadas recientes, usando simulación)")

    if meas_eci is not None:
        last_meas = meas_eci
        last_meas_time = meas_time

    # EKF: predecir 1 s, luego actualizar con la medición (si es reciente)
    ekf.predict(1.0)
    if last_meas is not None and last_meas_time is not None:
        age = (now - last_meas_time).total_seconds()
        # solo actualizar si la medición es reciente (no más de 5 min)
        if 0 <= age < 300:
            ekf.update(last_meas, R_MEAS)

    lat_ekf, lon_ekf, alt_ekf = ekf.latlonalt(dt_from_epoch)
    lat_meas, lon_meas, alt_meas = eci_to_geodetic(last_meas, dt_from_epoch) if last_meas is not None else (meas_lat, meas_lon, meas_alt)

    # calidad
    if last_meas_time is not None:
        age_s = (now - last_meas_time).total_seconds()
    else:
        age_s = None
    quality, qcolor = quality_from_age(age_s)

    # método de la última medición
    if args.method == "satnogs":
        method_name = "SatNOGS (Doppler)"
    elif args.method == "optical":
        method_name = "Óptico (simulado)"
    else:
        method_name = "GNSS a bordo (simulado)"

    payload = {
        "t": now.isoformat(),
        "elapsed": i + 1,
        "method": method_name,
        "tle": {"lat": lat_tle, "lon": lon_tle, "alt": alt_tle},
        "ekf": {"lat": lat_ekf, "lon": lon_ekf, "alt": alt_ekf},
        "meas": {"lat": lat_meas, "lon": lon_meas, "alt": alt_meas},
        "last_meas_time": last_meas_time.isoformat() if last_meas_time else None,
        "age_s": age_s,
        "quality": quality,
        "qcolor": qcolor,
        "sat": gp["OBJECT_NAME"],
    }
    with open(os.path.join(out, "live_position.json"), "w") as f:
        json.dump(payload, f)

    if i % 10 == 0 or i == args.duration - 1:
        print("  t=%3d  TLE=%.2f,%.2f  EKF=%.2f,%.2f  age=%s %s" % (
            i + 1, lat_tle, lon_tle, lat_ekf, lon_ekf,
            ("%.0f" % age_s) if age_s is not None else "-", quality))

    time.sleep(1.0)

print("Listo. live_position.json actualizado cada segundo.")