"""Trayectorias ilustrativas de Starship sobre el mapa mundial.

IMPORTANTE: no son datos reales. Starship no ha realizado (a la fecha) un vuelo
orbital completo de 10 órbitas. Estas trayectorias son ilustrativas, generadas
con el modelo orbital del proyecto, para mostrar cómo se verían en el mapa.

Genera:
  - examples/output/starship_orbital.png / .html  (trayectoria orbital, ~10 órbitas LEO)
  - examples/output/starship_booster.png         (arco suborbital del booster, ~8 min)
"""
import os
import sys
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt.viz import (ground_track, ground_track_ortho,
                            leo_ground_track, solar_subsolar_lon, solar_declination)

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

subsolar_lon = solar_subsolar_lon()
subsolar_lat = solar_declination()

# --- 1) Trayectoria orbital ilustrativa: ~10 órbitas LEO a ~200 km ---
lat_o, lon_o, t_o = leo_ground_track(altitude_km=200.0, inclination_deg=28.5,
                                     raan_deg=0.0,
                                     n_orbits=10, dt_s=60.0)

path = os.path.join(out, "starship_orbital.png")
ground_track(lat_o, lon_o, "Starship orbital (ilustrativo, ~10 órbitas LEO, ~200 km)",
             path, subsolar_lon=subsolar_lon, subsolar_lat=subsolar_lat)
print(f"Guardado: {path}")

path2 = os.path.join(out, "starship_orbital_ortho.png")
ground_track_ortho(lat_o, lon_o, "Starship orbital (ilustrativo, ~10 órbitas LEO)",
                   path2, subsolar_lon=subsolar_lon, subsolar_lat=subsolar_lat)
print(f"Guardado: {path2}")

# Mapa web orbital
points_o = [[float(la), float(lo)] for la, lo in zip(lat_o, lon_o)]
segments_o = []
cur = [points_o[0]]
for i in range(1, len(points_o)):
    if abs(points_o[i][1] - points_o[i-1][1]) > 180:
        segments_o.append(cur); cur = [points_o[i]]
    else:
        cur.append(points_o[i])
segments_o.append(cur)

# imagen día/noche
N = 360
lons = np.linspace(-180, 180, N)
slat = np.radians(subsolar_lat)
slon = np.radians(subsolar_lon)
lats2 = np.linspace(-90, 90, N // 2)
LON2, LAT2 = np.meshgrid(lons, lats2)
cosz2 = (np.sin(slat) * np.sin(np.radians(LAT2)) +
         np.cos(slat) * np.cos(np.radians(LAT2)) *
         np.cos(np.radians(LON2) - slon))
cosz2 = np.clip(cosz2, -1.0, 1.0)
zenith2 = np.arccos(cosz2)
night2 = zenith2 > (np.pi / 2)
darkness2 = np.clip((zenith2 - np.pi / 2) / (np.pi / 2), 0.0, 1.0)
gray2 = 0.72 - 0.48 * darkness2
alpha2 = np.where(night2, 0.30 + 0.45 * darkness2, 0.0)
rgba2 = np.zeros((N // 2, N, 4))
rgba2[..., 0] = gray2
rgba2[..., 1] = gray2
rgba2[..., 2] = gray2 + 0.02
rgba2[..., 3] = alpha2
fig, ax = plt.subplots(figsize=(8, 4))
ax.imshow(rgba2, extent=[-180, 180, -90, 90], origin="lower", aspect="auto")
ax.axis("off")
fig.tight_layout(pad=0)
fig.savefig(os.path.join(out, "starship_orbital_daynight.png"), dpi=90, transparent=True)
plt.close(fig)

html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Starship orbital (ilustrativo)</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  body { margin: 0; font-family: sans-serif; }
  #map { height: 100vh; width: 100%; }
  .info { position: absolute; top: 10px; right: 10px; z-index: 1000;
          background: rgba(255,255,255,0.9); padding: 10px 14px; border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 13px; }
</style>
</head>
<body>
<div id="map"></div>
<div class="info">
  <b>Starship orbital (ilustrativo)</b><br/>
  ~10 órbitas LEO, ~200 km<br/>
  Lanzamiento desde Starbase (ilustrativo)<br/>
  Puntos: __N__<br/>
  <small>No son datos reales.</small>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const points = __POINTS__;
  const segments = [];
  let cur = [points[0]];
  for (let i = 1; i < points.length; i++) {
    if (Math.abs(points[i][1] - points[i-1][1]) > 180) {
      segments.push(cur); cur = [points[i]];
    } else {
      cur.push(points[i]);
    }
  }
  segments.push(cur);
  const map = L.map('map', {
    maxBounds: [[-90, -180], [90, 180]],
    maxBoundsViscosity: 1.0,
    worldCopyJump: false
  }).setView([10, -60], 3);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 8, noWrap: true, attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ'
  }).addTo(map);
  L.imageOverlay('starship_orbital_daynight.png', [[-90, -180], [90, 180]], {opacity: 0.85, interactive: false}).addTo(map);
  const group = L.featureGroup().addTo(map);
  segments.forEach(seg => {
    if (seg.length < 2) return;
    L.polyline(seg, {color: '#d62728', weight: 2, opacity: 0.85}).addTo(group);
  });
  L.circleMarker(points[0], {radius: 7, color: 'green'}).addTo(map).bindPopup('Despegue (Starbase)');
  L.circleMarker(points[points.length-1], {radius: 7, color: 'red'}).addTo(map).bindPopup('Fin de simulación');
  map.fitBounds(group.getBounds());
</script>
</body>
</html>
"""
html = html.replace("__N__", str(len(points_o)))
html = html.replace("__POINTS__", json.dumps(points_o))
path_html = os.path.join(out, "starship_orbital.html")
with open(path_html, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Guardado: {path_html}")

# --- 2) Arco suborbital del booster: ~8 min, aterrizaje cerca del pad ---
# Aproximación: trayectoria balística corta (no usa el sim suborbital largo).
# Generamos un arco simple: lat/lon a lo largo de una elipse corta.
t_b = np.linspace(0, 480, 120)  # 8 min
# downrange en km, pico ~100 km, aterrizaje ~5 km del pad
down = 120 * (1 - np.cos(np.pi * t_b / 480))  # 0..240 km ida, vuelta? simplificado
# mejor: arco que vuelve al pad
down = 80 * np.sin(np.pi * t_b / 480)  # 0 -> 80 km -> 0
# lat/lon desde Starbase con azimut 96° (como geo.py)
from orbitas_rt.geo import destination, STARBASE, DEFAULT_AZIMUTH_DEG
lat_b, lon_b = destination(STARBASE[0], STARBASE[1], DEFAULT_AZIMUTH_DEG, down * 1000.0)
path_b = os.path.join(out, "starship_booster.png")
ground_track(lat_b, lon_b, "Super Heavy booster (ilustrativo, ~8 min, aterrizaje cerca del pad)",
             path_b, subsolar_lon=subsolar_lon, subsolar_lat=subsolar_lat)
print(f"Guardado: {path_b}")

print()
print("NOTA: trayectorias ilustrativas, no datos reales de Starship.")