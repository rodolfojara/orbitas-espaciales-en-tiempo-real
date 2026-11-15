"""Órbitas REALES de satélites chilenos (CelesTrak TLE + SGP4).

Satélites:
  - SUCHAI-4  (NORAD 69911, lanzado 2026, CubeSat U. de Chile)
  - FASAT B   (NORAD 25395, FASAT-Bravo, 1998)
  - SSOT      (NORAD 38011, Sistema Satelital de Observación de la Tierra, 2011)
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

from sgp4.api import Satrec
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

for s in sats:
    catnr = s["catnr"]
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%d&FORMAT=json" % catnr
    data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=30).read().decode())
    d = data[0]
    print("Satélite:", d["OBJECT_NAME"], "NORAD", d["NORAD_CAT_ID"],
          "Inc:", d["INCLINATION"], "Epoch:", d["EPOCH"][:16])

    sat = Satrec()
    omm.initialize(sat, d)

    epoch = datetime.fromisoformat(d["EPOCH"].replace("Z", "+00:00"))
    # período orbital
    mm = d["MEAN_MOTION"]
    period_min = 1440.0 / mm
    total_min = period_min * 2  # 2 órbitas
    step_min = 1.0
    times = np.arange(0, total_min, step_min)

    lats, lons = [], []
    from orbitas_rt.orbit3d import eci_to_geodetic
    for dt in times:
        from sgp4.api import jday
        jd = None
        # convert epoch + dt to julian
        t = epoch + __import__("datetime").timedelta(minutes=float(dt))
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute,
                      t.second + t.microsecond / 1e6)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            continue
        lat, lon, alt = eci_to_geodetic(np.array(r) * 1000.0, dt * 60.0)
        lats.append(lat)
        lons.append(lon)

    lats = np.array(lats)
    lons = np.array(lons)
    all_lats.append(lats)
    all_lons.append(lons)
    colors.append(s["color"])
    labels.append(s["name"])

    # PNG individual
    path = os.path.join(out, "chile_%s.png" % s["name"].replace(" ", "_").lower())
    ground_track(lats, lons, "Satélite chileno: %s (real, CelesTrak)" % s["name"],
                 path, color=s["color"],
                 subsolar_lon=subsolar_lon, subsolar_lat=subsolar_lat)
    print("  Guardado:", path)

# --- Mapa combinado (todas las órbitas) ---
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.set_facecolor("#dbe9f4")
ex = np.linspace(-180, 180, 361)
ax.plot(ex, 90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
ax.plot(ex, -90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
from orbitas_rt.viz import draw_world_map
draw_world_map(ax, "plate", color="#3a6b4a", lw=0.5, alpha=0.7)

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
        ax.plot(xs, ys, color=c, lw=1.2, alpha=0.8, zorder=2, label=lab)
    ax.scatter([lons[0]], [lats[0]], color=c, s=40, zorder=4)

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

# Mapa web
points_all = []
for lats, lons in zip(all_lats, all_lons):
    points_all.append([[float(la), float(lo)] for la, lo in zip(lats, lons)])

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
          background: rgba(255,255,255,0.9); padding: 10px 14px; border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 13px; }
  .legend { position: absolute; bottom: 20px; left: 20px; z-index: 1000;
            background: rgba(255,255,255,0.9); padding: 8px 12px; border-radius: 8px;
            font-size: 12px; }
</style>
</head>
<body>
<div id="map"></div>
<div class="info">
  <b>Satélites chilenos (reales)</b><br/>
  Datos: CelesTrak TLE + SGP4<br/>
  2 órbitas cada uno
</div>
<div class="legend">
  <span style="color:#d62728">●</span> SUCHAI-4<br/>
  <span style="color:#1f77b4">●</span> FASAT B<br/>
  <span style="color:#2ca02c">●</span> SSOT
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const tracks = __TRACKS__;
  const colors = ['#d62728', '#1f77b4', '#2ca02c'];
  const names = ['SUCHAI-4', 'FASAT B', 'SSOT'];
  const map = L.map('map', {
    maxBounds: [[-90, -180], [90, 180]],
    maxBoundsViscosity: 1.0,
    worldCopyJump: false
  }).setView([-20, -70], 3);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 8, noWrap: true, attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ'
  }).addTo(map);
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
    L.circleMarker(pts[0], {radius: 5, color: colors[idx]}).addTo(map).bindPopup(names[idx] + ' (inicio)');
  });
  map.fitBounds(group.getBounds());
</script>
</body>
</html>
"""
html = html.replace("__TRACKS__", json.dumps(points_all))
path_html = os.path.join(out, "chile_satellites.html")
with open(path_html, "w", encoding="utf-8") as f:
    f.write(html)
print("Guardado:", path_html)
print()
print("Satélites chilenos (reales): SUCHAI-4, FASAT B, SSOT")