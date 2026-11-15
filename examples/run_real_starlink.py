"""Trayectoria REAL de un Starlink desplegado por Starship Flight 15.

Datos reales obtenidos de CelesTrak (TLE/GP) y propagados con SGP4.
Demuestra el uso de fuentes reales (CelesTrak) mencionadas al inicio.
"""
import os
import sys
import json
import ssl
import urllib.request
from datetime import datetime, timedelta

import numpy as np
import matplotlib
matplotlib.use("Agg")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sgp4.api import Satrec, jday
from orbitas_rt.viz import ground_track, ground_track_ortho, solar_subsolar_lon, solar_declination

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

# --- 1) Obtener TLE real de CelesTrak ---
ctx = ssl._create_unverified_context()
catnr = 101252  # STARLINK-38485, desplegado por Flight 15 (epoch 2026-11-14)
url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%d&FORMAT=json" % catnr
data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=30).read().decode())
d = data[0]
print("Satélite:", d["OBJECT_NAME"], "NORAD", d["NORAD_CAT_ID"])
print("Epoch:", d["EPOCH"], "Inc:", d["INCLINATION"], "RAAN:", d["RA_OF_ASC_NODE"])

# Construir Satrec desde los elementos GP (OMM) usando sgp4.omm
from sgp4.api import Satrec
from sgp4 import omm
sat = Satrec()
omm.initialize(sat, d)
print("Satrec inicializado desde GP/OMM")

# --- 2) Propagar con SGP4 ---
# Período orbital aproximado
mm = d["MEAN_MOTION"]  # rev/día
period_min = 1440.0 / mm
print("Período orbital: %.1f min" % period_min)
n_orbits = 3
total_min = period_min * n_orbits
# Tiempo inicial = epoch
epoch = datetime.fromisoformat(d["EPOCH"].replace("Z", "+00:00"))
# propagar cada minuto
step_min = 1.0
times = np.arange(0, total_min, step_min)
jd0, fr0 = jday(epoch.year, epoch.month, epoch.day, epoch.hour, epoch.minute,
                 epoch.second + epoch.microsecond / 1e6)

lats, lons = [], []
for dt in times:
    jd = jd0 + dt / 1440.0
    fr = fr0
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        continue
    # r en km, TEME. Convertir a geodésico con GMST.
    # GMST aproximado: theta = 15.04107 * (jd - 2451545.0) ... usar simplificado con OMEGA_EARTH
    # Usamos la conversión del proyecto (ECI -> geodésico) con t en segundos desde epoch
    from orbitas_rt.orbit3d import eci_to_geodetic
    lat, lon, alt = eci_to_geodetic(np.array(r) * 1000.0, dt * 60.0)
    # eci_to_geodetic usa t_s desde epoch con GMST = OMEGA_EARTH * t; aproximación ok
    lats.append(lat)
    lons.append(lon)

lats = np.array(lats)
lons = np.array(lons)

# --- 3) Dibujar ---
path = os.path.join(out, "real_starlink.png")
ground_track(lats, lons, "Starlink-38485 (real, CelesTrak TLE, SGP4) - 3 órbitas",
             path, subsolar_lon=solar_subsolar_lon(), subsolar_lat=solar_declination())
print(f"Guardado: {path}")

path2 = os.path.join(out, "real_starlink_ortho.png")
ground_track_ortho(lats, lons, "Starlink-38485 (real, CelesTrak TLE, SGP4)",
                   path2, subsolar_lon=solar_subsolar_lon(), subsolar_lat=solar_declination())
print(f"Guardado: {path2}")

print()
print("NOTA: este satélite (STARLINK-38485) fue desplegado por Starship Flight 15.")
print("Es un satélite real en órbita LEO (~70° inc, ~550 km).")