"""Representación ilustrativa de Starship Flight 15 (Ship 42).

Incluye:
  - Fase orbital: ~15 órbitas LEO (~22.5 h).
  - Reentrada y aproximación: arco desde el punto de deorbit hasta Starbase,
    aproximándose desde el Golfo de México (la torre mira hacia el golfo).
  - Maniobra 'flip and burn' al final para ser capturado por los brazos.

NOTA: ilustrativo. La trayectoria real de reentrada no es pública.
"""
import os
import sys
import json

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt.viz import (ground_track, draw_world_map,
                            leo_ground_track, solar_subsolar_lon, solar_declination)

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

subsolar_lon = solar_subsolar_lon()
subsolar_lat = solar_declination()

# --- 1) Fase orbital (~15 órbitas) ---
lat_o, lon_o, t_o = leo_ground_track(altitude_km=200.0, inclination_deg=28.5,
                                     raan_deg=0.0, n_orbits=15, dt_s=60.0)

# --- 2) Arco de reentrada: deorbit -> Starbase, desde el Golfo ---
# Punto de deorbit (ilustrativo): ~1000 km al este de Starbase
deorbit_lon = -82.0
deorbit_lat = 26.0
starbase_lat, starbase_lon = 25.997, -97.157

# Curva de aproximación: arco que se aproxima desde el sureste (Golfo)
n = 80
frac = np.linspace(0, 1, n)
# Bezier cuadrática: deorbit -> punto de control (sur del Golfo) -> Starbase
ctrl_lat = 22.0   # más al sur (Golfo)
ctrl_lon = -90.0
lat_r = (1 - frac) ** 2 * deorbit_lat + 2 * (1 - frac) * frac * ctrl_lat + frac ** 2 * starbase_lat
lon_r = (1 - frac) ** 2 * deorbit_lon + 2 * (1 - frac) * frac * ctrl_lon + frac ** 2 * starbase_lon

# Concatenar: órbita + reentrada
lat_all = np.concatenate([lat_o, lat_r])
lon_all = np.concatenate([lon_o, lon_r])

# --- 3) Dibujar planar ---
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.set_facecolor("#dbe9f4")
ex = np.linspace(-180, 180, 361)
ax.plot(ex, 90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
ax.plot(ex, -90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
draw_world_map(ax, "plate", color="#3a6b4a", lw=0.5, alpha=0.7)

# día/noche
N = 400
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
gray = 0.72 - 0.48 * darkness
alpha = np.where(night, 0.30 + 0.45 * darkness, 0.0)
rgba = np.zeros((N, N, 4))
rgba[..., 0] = gray
rgba[..., 1] = gray
rgba[..., 2] = gray + 0.02
rgba[..., 3] = alpha
ax.imshow(rgba, extent=[-180, 180, -90, 90], origin="lower", zorder=1, aspect="auto")

# órbita (rojo)
sc = ax.scatter(lon_o, lat_o, c=np.arange(len(lon_o)), cmap="viridis", s=4, zorder=3)
# cortar antimeridiano para la órbita
segs = []
cur = [(lon_o[0], lat_o[0])]
for i in range(1, len(lon_o)):
    if abs(lon_o[i] - lon_o[i - 1]) > 180.0:
        segs.append(cur); cur = [(lon_o[i], lat_o[i])]
    else:
        cur.append((lon_o[i], lat_o[i]))
segs.append(cur)
for seg in segs:
    if len(seg) < 2: continue
    xs, ys = zip(*seg)
    ax.plot(xs, ys, color="#d62728", lw=1.0, alpha=0.7, zorder=2, label="órbita LEO")

# reentrada (azul)
ax.plot(lon_r, lat_r, color="#1f77b4", lw=2.5, alpha=0.9, zorder=4, label="reentrada y aproximación")
ax.scatter([lon_r[0]], [lat_r[0]], color="orange", s=60, zorder=5, label="deorbit")
ax.scatter([starbase_lon], [starbase_lat], color="green", s=100, marker="*", zorder=5, label="Starbase (captura)")
ax.scatter([lon_r[-1]], [lat_r[-1]], color="red", s=60, zorder=5, label="aterrizaje")

ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.set_xlabel("longitud (deg)")
ax.set_ylabel("latitud (deg)")
ax.set_title("Starship Flight 15 (ilustrativo): órbita + reentrada + aproximación desde el Golfo")
ax.grid(alpha=0.3, linestyle=":")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
path = os.path.join(out, "starship_reentry.png")
fig.savefig(path, dpi=140)
plt.close(fig)
print(f"Guardado: {path}")

# Globo
fig, ax = plt.subplots(figsize=(7, 7))
th = np.linspace(0, 2 * np.pi, 361)
ax.plot(np.cos(th), np.sin(th), color="#2a6f3b", lw=1.2)
ax.fill(np.cos(th), np.sin(th), color="#dbe9f4", alpha=0.4)
draw_world_map(ax, "ortho", color="#3a6b4a", lw=0.4, alpha=0.6)

# órbita (proyectar)
def to_ortho(lat, lon):
    x = np.cos(np.radians(lat)) * np.sin(np.radians(lon))
    y = np.sin(np.radians(lat))
    return x, y

xo, yo = to_ortho(lat_o, lon_o)
xr, yr = to_ortho(lat_r, lon_r)
ax.plot(xo, yo, color="#d62728", lw=0.8, alpha=0.6, zorder=2, label="órbita")
ax.plot(xr, yr, color="#1f77b4", lw=2.0, alpha=0.9, zorder=4, label="reentrada")
xs, ys = to_ortho(np.array([starbase_lat]), np.array([starbase_lon]))
ax.scatter(xs, ys, color="green", s=80, marker="*", zorder=5, label="Starbase")
ax.set_aspect("equal")
ax.set_xlim(-1.15, 1.15)
ax.set_ylim(-1.15, 1.15)
ax.set_title("Starship Flight 15 (ilustrativo): globo")
ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
path2 = os.path.join(out, "starship_reentry_ortho.png")
fig.savefig(path2, dpi=140)
plt.close(fig)
print(f"Guardado: {path2}")

print()
print("NOTA: ilustrativo. Trayectoria de reentrada aproximada, no datos reales.")