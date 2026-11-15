"""Dibuja la trayectoria suborbital simulada de Starship (S42) sobre mapas.

Usa la simulación del proyecto (no son datos reales de ningún vuelo) y genera:
  - examples/output/starship_track.png        (proyección plana)
  - examples/output/starship_track_ortho.png  (globo)
  - examples/output/starship_track.html       (mapa web interactivo)
"""
import os
import sys
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt import sim
from orbitas_rt.viz import ground_track, ground_track_ortho

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

# Simulación de ejemplo (S42 ficticio)
sc = sim.Scenario()
truth = sim.simulate_truth(sc.truth, surprise=sc.surprise_burn)
rng = np.random.default_rng(sc.seed)
meas = sim.make_measurements(*truth, sc.dropouts, rng)
res = sim.run_tracker(meas, truth[0][-1], sc.nominal, truth)

lat = res["lat"]
lon = res["lon"]

# PNG planar
path = os.path.join(out, "starship_track.png")
ground_track(lat, lon, "Trayectoria suborbital simulada - Starship (S42)",
             path, subsolar_lon=None, subsolar_lat=None)
print(f"Guardado: {path}")

# PNG globo
path2 = os.path.join(out, "starship_track_ortho.png")
ground_track_ortho(lat, lon, "Trayectoria suborbital simulada - Starship (S42)",
                   path2, subsolar_lon=None, subsolar_lat=None)
print(f"Guardado: {path2}")

# Mapa web (Leaflet)
points = [[float(la), float(lo)] for la, lo in zip(lat, lon)]

# imagen día/noche
import datetime as _dt
from orbitas_rt.viz import solar_subsolar_lon, solar_declination
subsolar_lon = solar_subsolar_lon()
subsolar_lat = solar_declination()
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
fig.savefig(os.path.join(out, "starship_daynight.png"), dpi=90, transparent=True)
plt.close(fig)

html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Starship (S42) - trayectoria suborbital</title>
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
  <b>Starship (S42) - trayectoria suborbital simulada</b><br/>
  Lanzamiento desde Starbase, Texas<br/>
  Puntos: __N__<br/>
  <small>Simulación ilustrativa, no datos reales.</small>
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
  L.imageOverlay('starship_daynight.png', [[-90, -180], [90, 180]], {opacity: 0.85, interactive: false}).addTo(map);
  const group = L.featureGroup().addTo(map);
  segments.forEach(seg => {
    if (seg.length < 2) return;
    L.polyline(seg, {color: '#d62728', weight: 2.5, opacity: 0.9}).addTo(group);
  });
  L.circleMarker(points[0], {radius: 7, color: 'green'}).addTo(map).bindPopup('Despegue (Starbase)');
  L.circleMarker(points[points.length-1], {radius: 7, color: 'red'}).addTo(map).bindPopup('Aterrizaje');
  map.fitBounds(group.getBounds());
</script>
</body>
</html>
"""
html = html.replace("__N__", str(len(points)))
html = html.replace("__POINTS__", json.dumps(points))

path_html = os.path.join(out, "starship_track.html")
with open(path_html, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Guardado: {path_html}")
print("Abre starship_track.html en el navegador (o via serve.bat).")