"""Genera una visualización web (Leaflet) de la huella en tierra.

Produce examples/output/ground_track.html, un archivo autocontenido que carga
Leaflet desde CDN y dibuja la trayectoria sobre un mapa base (OpenStreetMap).
"""
import os
import sys
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt.orbit3d import orbit_ground_track

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

lat, lon, alt, t = orbit_ground_track(a_km=6871.0, e=0.0, i_deg=51.6,
                                      raan_deg=0.0, argp_deg=0.0,
                                      n_orbits=3, dt_s=60.0)

# Puntos para Leaflet: [lat, lon]
points = [[float(la), float(lo)] for la, lo in zip(lat, lon)]

# Generar imagen día/noche (equirectangular) para overlay en el mapa web
subsolar_lon = 30.0
subsolar_lat = 0.0
N = 360
lons = np.linspace(-180, 180, N)
lats = np.linspace(-90, 90, N)
LON, LAT = np.meshgrid(lons, lats)
slat = np.radians(subsolar_lat)
slon = np.radians(subsolar_lon)
cosz = (np.sin(slat) * np.sin(np.radians(LAT)) +
        np.cos(slat) * np.cos(np.radians(LAT)) *
        np.cos(np.radians(LON) - slon))
cosz = np.clip(cosz, -1.0, 1.0)
zenith = np.arccos(cosz)
night = zenith > (np.pi / 2)
darkness = np.clip((zenith - np.pi / 2) / (np.pi / 2), 0.0, 1.0)
gray = 0.85 - 0.45 * darkness
alpha = np.where(night, 0.12 + 0.38 * darkness, 0.0)
rgba = np.zeros((N // 2, N, 4))
# resize lats to N//2
lats2 = np.linspace(-90, 90, N // 2)
LON2, LAT2 = np.meshgrid(lons, lats2)
cosz2 = (np.sin(slat) * np.sin(np.radians(LAT2)) +
         np.cos(slat) * np.cos(np.radians(LAT2)) *
         np.cos(np.radians(LON2) - slon))
cosz2 = np.clip(cosz2, -1.0, 1.0)
zenith2 = np.arccos(cosz2)
night2 = zenith2 > (np.pi / 2)
darkness2 = np.clip((zenith2 - np.pi / 2) / (np.pi / 2), 0.0, 1.0)
gray2 = 0.75 - 0.55 * darkness2
alpha2 = np.where(night2, 0.35 + 0.50 * darkness2, 0.0)
rgba2 = np.zeros((N // 2, N, 4))
rgba2[..., 0] = gray2
rgba2[..., 1] = gray2
rgba2[..., 2] = gray2 + 0.05
rgba2[..., 3] = alpha2
fig, ax = plt.subplots(figsize=(8, 4))
ax.imshow(rgba2, extent=[-180, 180, -90, 90], origin="lower", aspect="auto")
ax.axis("off")
fig.tight_layout(pad=0)
fig.savefig(os.path.join(out, "daynight.png"), dpi=90, transparent=True)
plt.close(fig)

html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Huella en tierra - LEO</title>
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
  <b>Huella en tierra - LEO</b><br/>
  Altitud ~500 km, inc. 51.6°<br/>
  3 órbitas, rotación terrestre incluida<br/>
  Puntos: __N__<br/>
  <small>Si el mapa base se bloquea, sirve la carpeta con<br/>
  <code>python -m http.server 8000</code></small>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const points = __POINTS__;
  // Cortar la polilínea en los saltos de antimeridiano (|Δlon|>180)
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
  const map = L.map('map').setView([0, 0], 2);
  // Proveedor de tiles que funciona abriendo el HTML localmente (file://).
  // OpenStreetMap bloquea las peticiones sin Referer; Esri no.
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 8, attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ'
  }).addTo(map);
  // Sombreado día/noche (degradado)
  L.imageOverlay('daynight.png', [[-90, -180], [90, 180]], {opacity: 0.85, interactive: false}).addTo(map);
  const group = L.featureGroup().addTo(map);
  segments.forEach(seg => {
    if (seg.length < 2) return;
    L.polyline(seg, {color: '#d62728', weight: 2, opacity: 0.8}).addTo(group);
  });
  L.circleMarker(points[0], {radius: 6, color: 'green'}).addTo(map).bindPopup('Inicio');
  L.circleMarker(points[points.length-1], {radius: 6, color: 'red'}).addTo(map).bindPopup('Fin');
  map.fitBounds(group.getBounds());
</script>
</body>
</html>
"""
html = html.replace("__N__", str(len(points)))
html = html.replace("__POINTS__", json.dumps(points))

path = os.path.join(out, "ground_track.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Guardado: {path}")
print("Ábrelo en un navegador (doble clic) para ver el mapa interactivo.")
print("Si el mapa base aparece bloqueado, sirve la carpeta con un servidor local:")
print("  cd examples/output && python -m http.server 8000")
print("  y abre http://localhost:8000/ground_track.html")
