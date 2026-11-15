"""Genera una visualización web (Leaflet) de la huella en tierra.

Produce examples/output/ground_track.html, un archivo autocontenido que carga
Leaflet desde CDN y dibuja la trayectoria sobre un mapa base (OpenStreetMap).
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt.orbit3d import orbit_ground_track

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

lat, lon, alt, t = orbit_ground_track(a_km=6871.0, e=0.0, i_deg=51.6,
                                      raan_deg=0.0, argp_deg=0.0,
                                      n_orbits=3, dt_s=60.0)

# Puntos para Leaflet: [lat, lon]
points = [[float(la), float(lo)] for la, lo in zip(lat, lon)]

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
  const map = L.map('map').setView([0, 0], 2);
  // Proveedor de tiles que funciona abriendo el HTML localmente (file://).
  // OpenStreetMap bloquea las peticiones sin Referer; Esri no.
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 8, attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ'
  }).addTo(map);
  const poly = L.polyline(points, {color: '#d62728', weight: 2, opacity: 0.8}).addTo(map);
  L.circleMarker(points[0], {radius: 6, color: 'green'}).addTo(map).bindPopup('Inicio');
  L.circleMarker(points[points.length-1], {radius: 6, color: 'red'}).addTo(map).bindPopup('Fin');
  map.fitBounds(poly.getBounds());
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
