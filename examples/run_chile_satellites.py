"""Órbitas REALES de satélites chilenos (CelesTrak TLE + SGP4).

Satélites actualmente catalogados:
  - SUCHAI-4  (NORAD 69911, lanzado 2026, CubeSat U. de Chile)
  - FASAT B   (NORAD 25395, FASAT-Bravo, 1998)
  - SSOT      (NORAD 38011, Sistema Satelital de Observación de la Tierra, 2011)

Historial (fuentes públicas):
  SUCHAI:
    - SUCHAI-1 (2017, NORAD 42788): reentró oct-2023.
    - SUCHAI-2 (2022, Transporter-4): reentró.
    - SUCHAI-3 (2022, Transporter-4): reentró.
    - SUCHAI-4 (2026, Transporter-17): en órbita.
    - PlantSat (2022): reentró.
  FASAT:
    - FASAT-Alfa (1995): no se separó del portador, nunca operó.
    - FASAT-Bravo (1998): dejó de transmitir ~2014. TLE aún disponible.
    - FASAT-Charlie (2001): sigue operativo (según FACH).
    - FASAT-Delta (2011): falló, desautorizado por la FACH ~2026.
  SSOT (2011): en órbita, observación terrestre.
"""
import os
import sys
import json
import ssl
import urllib.request
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sgp4.api import Satrec, jday
from sgp4 import omm
from orbitas_rt.viz import (ground_track, ground_track_ortho,
                            solar_subsolar_lon, solar_declination)

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

ctx = ssl._create_unverified_context()

sats = [
    {"catnr": 69911, "name": "SUCHAI-4", "color": "#d62728"},
    {"catnr": 25395, "name": "FASAT B", "color": "#1f77b4"},
    {"catnr": 38011, "name": "SSOT", "color": "#2ca02c"},
]

subsolar_lon = solar_subsolar_lon()
subsolar_lat = solar_declination()

all_lats = []
all_lons = []
colors = []
labels = []
altitudes = []
current_pos = []

for s in sats:
    catnr = s["catnr"]
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%d&FORMAT=json" % catnr
    data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=30).read().decode())
    d = data[0]
    print("Satélite:", d["OBJECT_NAME"], "NORAD", d["NORAD_CAT_ID"],
          "Inc:", d["INCLINATION"], "Epoch:", d["EPOCH"][:16])

    sat = Satrec()
    omm.initialize(sat, d)

    # altitud orbital aproximada
    mm = d["MEAN_MOTION"]  # rev/día
    n = mm * 2 * np.pi / 86400.0  # rad/s
    mu = 3.986004418e14
    a = (mu / (n * n)) ** (1.0 / 3.0)  # m
    alt_km = a / 1000.0 - 6371.0
    altitudes.append(alt_km)
    print("  Altitud orbital: %.0f km" % alt_km)

    epoch = datetime.fromisoformat(d["EPOCH"].replace("Z", "+00:00"))
    period_min = 1440.0 / mm
    total_min = period_min * 2
    step_min = 1.0
    times = np.arange(0, total_min, step_min)

    lats, lons = [], []
    for dt in times:
        t = epoch + __import__("datetime").timedelta(minutes=float(dt))
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute,
                      t.second + t.microsecond / 1e6)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            continue
        from orbitas_rt.orbit3d import eci_to_geodetic
        lat, lon, alt = eci_to_geodetic(np.array(r) * 1000.0, dt * 60.0)
        lats.append(lat)
        lons.append(lon)

    lats = np.array(lats)
    lons = np.array(lons)
    all_lats.append(lats)
    all_lons.append(lons)
    colors.append(s["color"])
    labels.append(s["name"])
    # posición actual = primer punto (época TLE ≈ ahora)
    current_pos.append((float(lats[0]), float(lons[0])))

    path = os.path.join(out, "chile_%s.png" % s["name"].replace(" ", "_").lower())
    ground_track(lats, lons, "Satélite chileno: %s (real, CelesTrak) - alt ~%.0f km" % (s["name"], alt_km),
                 path, color=s["color"],
                 subsolar_lon=subsolar_lon, subsolar_lat=subsolar_lat)
    print("  Guardado:", path)

# --- Mapa combinado ---
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.set_facecolor("#dbe9f4")
ex = np.linspace(-180, 180, 361)
ax.plot(ex, 90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
ax.plot(ex, -90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
from orbitas_rt.viz import draw_world_map
draw_world_map(ax, "plate", color="#3a6b4a", lw=0.5, alpha=0.7)

# día/noche (más oscuro)
N = 400
lons_g = np.linspace(-180, 180, N)
lats_g = np.linspace(-90, 90, N)
LON, LAT = np.meshgrid(lons_g, lats_g)
slat = np.radians(subsolar_lat)
slon = np.radians(subsolar_lon)
cosz = (np.sin(slat) * np.sin(np.radians(LAT)) +
        np.cos(slat) * np.cos(np.radians(LAT)) *
        np.cos(np.radians(LON) - slon))
cosz = np.clip(cosz, -1.0, 1.0)
zenith = np.arccos(cosz)
night = zenith > (np.pi / 2)
darkness = np.clip((zenith - np.pi / 2) / (np.pi / 2), 0.0, 1.0)
gray = 0.60 - 0.45 * darkness
alpha = np.where(night, 0.40 + 0.45 * darkness, 0.0)
rgba = np.zeros((N, N, 4))
rgba[..., 0] = gray
rgba[..., 1] = gray
rgba[..., 2] = gray + 0.02
rgba[..., 3] = alpha
ax.imshow(rgba, extent=[-180, 180, -90, 90], origin="lower", zorder=1, aspect="auto")

for lats, lons, c, lab in zip(all_lats, all_lons, colors, labels):
    segs = []
    cur = [(lons[0], lats[0])]
    for i in range(1, len(lons)):
        if abs(lons[i] - lons[i - 1]) > 180.0:
            segs.append(cur); cur = [(lons[i], lats[i])]
        else:
            cur.append((lons[i], lats[i]))
    segs.append(cur)
    for seg in segs:
        if len(seg) < 2: continue
        xs, ys = zip(*seg)
        ax.plot(xs, ys, color=c, lw=1.2, alpha=0.85, zorder=2, label=lab)

# posición actual
for (la, lo), c, lab in zip(current_pos, colors, labels):
    ax.scatter([lo], [la], color=c, s=80, marker="*", zorder=5, edgecolors="black", linewidths=0.5)

ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.set_xlabel("longitud (deg)")
ax.set_ylabel("latitud (deg)")
ax.set_title("Satélites chilenos (reales, CelesTrak + SGP4): SUCHAI-4, FASAT B, SSOT")
ax.grid(alpha=0.3, linestyle=":")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
path = os.path.join(out, "chile_all.png")
fig.savefig(path, dpi=140)
plt.close(fig)
print("Guardado:", path)

# --- Generar imagen día/noche (más oscura) para el web ---
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
gray2 = 0.60 - 0.45 * darkness2
alpha2 = np.where(night2, 0.40 + 0.45 * darkness2, 0.0)
rgba2 = np.zeros((N // 2, N, 4))
rgba2[..., 0] = gray2
rgba2[..., 1] = gray2
rgba2[..., 2] = gray2 + 0.02
rgba2[..., 3] = alpha2
fig, ax = plt.subplots(figsize=(8, 4))
ax.imshow(rgba2, extent=[-180, 180, -90, 90], origin="lower", aspect="auto")
ax.axis("off")
fig.tight_layout(pad=0)
fig.savefig(os.path.join(out, "chile_daynight.png"), dpi=90, transparent=True)
plt.close(fig)

# --- Mapa web ---
points_all = []
for lats, lons in zip(all_lats, all_lons):
    points_all.append([[float(la), float(lo)] for la, lo in zip(lats, lons)])

# info de altitud y posición actual
info_lines = []
for s, alt, (la, lo) in zip(sats, altitudes, current_pos):
    info_lines.append("%s: alt ~%.0f km, pos actual %.2f, %.2f" % (s["name"], alt, la, lo))

html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Satélites chilenos</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  body { margin: 0; font-family: sans-serif; }
  #map { height: 100vh; width: 100%; }
  .info { position: absolute; top: 10px; right: 10px; z-index: 1000;
          background: rgba(255,255,255,0.92); padding: 10px 14px; border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 12px; max-width: 320px; }
  .legend { position: absolute; bottom: 20px; left: 20px; z-index: 1000;
            background: rgba(255,255,255,0.92); padding: 8px 12px; border-radius: 8px;
            font-size: 12px; }
  .hist { position: absolute; top: 10px; left: 10px; z-index: 1000;
          background: rgba(255,255,255,0.92); padding: 10px 14px; border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 11px; max-width: 340px;
          max-height: 80vh; overflow-y: auto; }
</style>
</head>
<body>
<div id="map"></div>
<div class="info">
  <b>Satélites chilenos (reales)</b><br/>
  Datos: CelesTrak TLE + SGP4<br/>
  2 órbitas cada uno<br/>
  <hr style="margin:4px 0"/>
  __INFO__
</div>
<div class="legend">
  <span style="color:#d62728">●</span> SUCHAI-4 (en órbita)<br/>
  <span style="color:#1f77b4">●</span> FASAT B (sin tx ~2014)<br/>
  <span style="color:#2ca02c">●</span> SSOT (en órbita)<br/>
  <span style="color:gold">★</span> Posición actual
</div>
<div class="hist">
  <b>Historial (fuentes públicas)</b><br/><br/>
  <b>SUCHAI</b><br/>
  • SUCHAI-1 (2017, NORAD 42788): reentró oct-2023.<br/>
  • SUCHAI-2 (2022, Transporter-4): reentró.<br/>
  • SUCHAI-3 (2022, Transporter-4): reentró.<br/>
  • SUCHAI-4 (2026, Transporter-17): en órbita.<br/>
  • PlantSat (2022): reentró.<br/><br/>
  <b>FASAT</b><br/>
  • FASAT-Alfa (1995): no se separó del portador.<br/>
  • FASAT-Bravo (1998): dejó de transmitir ~2014.<br/>
  • FASAT-Charlie (2001): sigue operativo (FACH).<br/>
  • FASAT-Delta (2011): falló, desautorizado ~2026.<br/><br/>
  <b>SSOT</b> (2011): en órbita, obs. terrestre.
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const tracks = __TRACKS__;
  const colors = ['#d62728', '#1f77b4', '#2ca02c'];
  const names = ['SUCHAI-4', 'FASAT B', 'SSOT'];
  const curpos = __CURPOS__;
  const map = L.map('map', {
    maxBounds: [[-90, -180], [90, 180]],
    maxBoundsViscosity: 1.0,
    worldCopyJump: false
  }).setView([-20, -70], 3);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 8, noWrap: true, attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ'
  }).addTo(map);
  L.imageOverlay('chile_daynight.png', [[-90, -180], [90, 180]], {opacity: 0.85, interactive: false}).addTo(map);
  const group = L.featureGroup().addTo(map);
  tracks.forEach((pts, idx) => {
    const segs = [];
    let cur = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      if (Math.abs(pts[i][1] - pts[i-1][1]) > 180) { segs.push(cur); cur = [pts[i]]; }
      else cur.push(pts[i]);
    }
    segs.push(cur);
    segs.forEach(seg => {
      if (seg.length < 2) return;
      L.polyline(seg, {color: colors[idx], weight: 2, opacity: 0.85}).addTo(group);
    });
    L.circleMarker(pts[0], {radius: 4, color: colors[idx], fillColor: colors[idx], fillOpacity: 0.9}).addTo(map);
  });
  // posición actual (estrella dorada)
  curpos.forEach((cp, idx) => {
    L.marker(cp, {icon: L.divIcon({className:'curpos', html:'<div style="color:gold;font-size:18px;">★</div>', iconSize:[18,18]})})
      .addTo(map).bindPopup(names[idx] + ' - posición actual');
  });
  map.fitBounds(group.getBounds());
</script>
</body>
</html>
"""
html = html.replace("__TRACKS__", json.dumps(points_all))
html = html.replace("__CURPOS__", json.dumps(current_pos))
html = html.replace("__INFO__", "<br/>".join(info_lines))
path_html = os.path.join(out, "chile_satellites.html")
with open(path_html, "w", encoding="utf-8") as f:
    f.write(html)
print("Guardado:", path_html)
print()
print("Satélites chilenos (reales): SUCHAI-4, FASAT B, SSOT")
print("Altitudes:", [round(a) for a in altitudes])