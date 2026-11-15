"""Visualizaciones orbitales.

Dos familias:
  * Huella en tierra (ground track): para órbita baja/media (LEO/MEO). Proyecta la
    órbita sobre la superficie terrestre (lat/lon del punto sub-satélite).
  * Diagrama interplanetario: para órbita alta / Tierra-Luna / Tierra-L2 / Tierra-Marte.
    Muestra las órbitas de los planetas y la trayectoria del objeto en coordenadas
    heliocéntricas (eclíptica).
"""
from __future__ import annotations

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

_WORLD_GEOJSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "data", "world_countries.geojson")


def _load_world():
    if not os.path.exists(_WORLD_GEOJSON):
        return None
    with open(_WORLD_GEOJSON, encoding="utf-8") as f:
        return json.load(f)


def draw_world_map(ax, projection="plate", color="#4a7c59", lw=0.4, alpha=0.6):
    """Dibuja las costas del mundo a partir del GeoJSON incluido."""
    data = _load_world()
    if data is None:
        return
    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        polys = []
        if gtype == "Polygon":
            polys = [coords]
        elif gtype == "MultiPolygon":
            polys = coords
        for poly in polys:
            for ring in poly:
                xs = [p[0] for p in ring]
                ys = [p[1] for p in ring]
                if projection == "plate":
                    ax.plot(xs, ys, color=color, lw=lw, alpha=alpha, zorder=2)
                elif projection == "ortho":
                    # convertir lon/lat a coords ortográficas (centro 0,0)
                    lons = np.array(xs, dtype=float)
                    lats = np.array(ys, dtype=float)
                    rr = np.cos(np.radians(lats))
                    X = rr * np.sin(np.radians(lons))
                    Y = np.sin(np.radians(lats))
                    Z = rr * np.cos(np.radians(lons))
                    visible = Z > 0
                    # dibujar solo segmentos visibles
                    seg_x, seg_y = [], []
                    for i in range(len(X)):
                        if visible[i]:
                            seg_x.append(X[i])
                            seg_y.append(Y[i])
                        else:
                            if len(seg_x) > 1:
                                ax.plot(seg_x, seg_y, color=color, lw=lw, alpha=alpha, zorder=2)
                            seg_x, seg_y = [], []
                    if len(seg_x) > 1:
                        ax.plot(seg_x, seg_y, color=color, lw=lw, alpha=alpha, zorder=2)

RE_KM = 6371.0
MU_KM3_S2 = 3.986004418e5  # km^3/s^2 (Tierra)
OMEGA_EARTH_RAD_S = 7.2921159e-5  # rotación terrestre


def _wrap_lon(lon):
    return (lon + 180.0) % 360.0 - 180.0


def ground_track(lat_deg, lon_deg, title, path, color="#1f77b4", show_earth=True,
                 daynight=True, subsolar_lon=0.0, subsolar_lat=0.0):
    """Dibuja una huella en tierra (lat/lon) sobre un mapa equirectangular simple.

    lat_deg, lon_deg: arrays en grados. La polilínea se corta en los saltos de
    antimeridiano (|Δlon|>180) para evitar rectas espurias. Si daynight=True,
    sombrea el hemisferio nocturno con un degradado gris.
    """
    lat = np.asarray(lat_deg, dtype=float)
    lon = np.asarray(lon_deg, dtype=float)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    if show_earth:
        ax.set_facecolor("#dbe9f4")
        ex = np.linspace(-180, 180, 361)
        ax.plot(ex, 90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
        ax.plot(ex, -90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
        draw_world_map(ax, "plate", color="#3a6b4a", lw=0.5, alpha=0.7)

    if daynight:
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
        gray = 0.75 - 0.55 * darkness
        alpha = np.where(night, 0.35 + 0.50 * darkness, 0.0)
        rgba = np.zeros((N, N, 4))
        rgba[..., 0] = gray
        rgba[..., 1] = gray
        rgba[..., 2] = gray + 0.05
        rgba[..., 3] = alpha
        ax.imshow(rgba, extent=[-180, 180, -90, 90], origin="lower", zorder=1, aspect="auto")

    sc = ax.scatter(lon, lat, c=np.arange(len(lon)), cmap="viridis", s=6, zorder=4)
    # cortar en saltos de antimeridiano
    segs = []
    cur = [(lon[0], lat[0])]
    for i in range(1, len(lon)):
        if abs(lon[i] - lon[i - 1]) > 180.0:
            segs.append(cur)
            cur = [(lon[i], lat[i])]
        else:
            cur.append((lon[i], lat[i]))
    segs.append(cur)
    for seg in segs:
        if len(seg) < 2:
            continue
        xs, ys = zip(*seg)
        ax.plot(xs, ys, color=color, lw=1.0, alpha=0.6, zorder=2)
    ax.scatter([lon[0]], [lat[0]], color="green", s=60, zorder=4, label="inicio")
    ax.scatter([lon[-1]], [lat[-1]], color="red", s=60, zorder=4, label="fin")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("longitud (deg)")
    ax.set_ylabel("latitud (deg)")
    ax.set_title(title)
    ax.grid(alpha=0.3, linestyle=":")
    ax.legend(fontsize=8, loc="upper right")
    cbar = fig.colorbar(sc, ax=ax, pad=0.01)
    cbar.set_label("paso (índice temporal)")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def ground_track_ortho(lat_deg, lon_deg, title, path, color="#1f77b4",
                      subsolar_lon=0.0, subsolar_lat=0.0, daynight=True):
    """Huella en tierra en proyección ortográfica (globo), sin distorsión planar.

    Evita la distorsión de la proyección plana; muestra el hemisferio visible
    centrado en (0,0). Si daynight=True, sombrea el hemisferio nocturno con un
    degradado gris (no negro total).
    """
    lat = np.asarray(lat_deg, dtype=float)
    lon = np.asarray(lon_deg, dtype=float)
    lat0, lon0 = 0.0, 0.0
    c = (np.sin(np.radians(lat0)) * np.sin(np.radians(lat)) +
         np.cos(np.radians(lat0)) * np.cos(np.radians(lat)) *
         np.cos(np.radians(lon - lon0)))
    visible = c > 0
    x = np.cos(np.radians(lat)) * np.sin(np.radians(lon - lon0))
    y = (np.sin(np.radians(lat)) * np.cos(np.radians(lat0)) -
         np.cos(np.radians(lat)) * np.sin(np.radians(lat0)) *
         np.cos(np.radians(lon - lon0)))
    fig, ax = plt.subplots(figsize=(7, 7))
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(np.cos(th), np.sin(th), color="#2a6f3b", lw=1.2)
    ax.fill(np.cos(th), np.sin(th), color="#dbe9f4", alpha=0.4)
    draw_world_map(ax, "ortho", color="#3a6b4a", lw=0.4, alpha=0.6)

    # Sombreado día/noche con degradado (solo en el disco visible)
    if daynight:
        N = 500
        xs = np.linspace(-1.0, 1.0, N)
        ys = np.linspace(-1.0, 1.0, N)
        X, Y = np.meshgrid(xs, ys)
        R2 = X * X + Y * Y
        mask = R2 <= 1.0
        Z = np.sqrt(np.clip(1.0 - R2, 0.0, 1.0))
        slat = np.radians(subsolar_lat)
        slon = np.radians(subsolar_lon)
        S = np.array([np.cos(slat) * np.cos(slon),
                      np.cos(slat) * np.sin(slon),
                      np.sin(slat)])
        cosz = X * S[0] + Y * S[1] + Z * S[2]
        cosz = np.clip(cosz, -1.0, 1.0)
        zenith = np.arccos(cosz)
        night = zenith > (np.pi / 2)
        darkness = np.clip((zenith - np.pi / 2) / (np.pi / 2), 0.0, 1.0)
        gray = 0.75 - 0.55 * darkness
        alpha = np.where(night, 0.35 + 0.50 * darkness, 0.0)
        rgba = np.zeros((N, N, 4))
        rgba[..., 0] = gray
        rgba[..., 1] = gray
        rgba[..., 2] = gray + 0.05
        rgba[..., 3] = alpha
        rgba[~mask, 3] = 0.0
        ax.imshow(rgba, extent=[-1, 1, -1, 1], origin="lower", zorder=2)

    xs = x[visible]
    ys = y[visible]
    ax.scatter(xs, ys, c=np.arange(len(xs)), cmap="viridis", s=6, zorder=4)
    for i in range(1, len(lat)):
        if not (visible[i] and visible[i - 1]):
            continue
        ax.plot([x[i - 1], x[i]], [y[i - 1], y[i]], color=color, lw=1.0, alpha=0.6, zorder=4)
    vis_idx = np.where(visible)[0]
    if len(vis_idx) > 0:
        ax.scatter([x[vis_idx[0]]], [y[vis_idx[0]]], color="green", s=60, zorder=5, label="inicio")
        ax.scatter([x[vis_idx[-1]]], [y[vis_idx[-1]]], color="red", s=60, zorder=5, label="fin")
    ax.set_aspect("equal")
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title + " (proyección ortográfica)")
    ax.grid(alpha=0.2, linestyle=":")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def leo_ground_track(altitude_km=400.0, inclination_deg=51.6, n_orbits=3,
                    dt_s=30.0, raan_deg=0.0, arglat0_deg=0.0):
    """Genera (lat, lon) del punto sub-satélite para una órbita circular LEO.

    Devuelve (lat_deg array, lon_deg array, t_s array).
    """
    a = RE_KM + altitude_km
    T = 2 * np.pi * np.sqrt(a ** 3 / MU_KM3_S2)
    n = 2 * np.pi / T
    i = np.radians(inclination_deg)
    Omega = np.radians(raan_deg)
    u0 = np.radians(arglat0_deg)

    t_end = n_orbits * T
    t = np.arange(0.0, t_end, dt_s)
    u = u0 + n * t

    x = a * (np.cos(Omega) * np.cos(u) - np.sin(Omega) * np.sin(u) * np.cos(i))
    y = a * (np.sin(Omega) * np.cos(u) + np.cos(Omega) * np.sin(u) * np.cos(i))
    z = a * (np.sin(i) * np.sin(u))

    r = np.sqrt(x * x + y * y + z * z)
    lat = np.degrees(np.arcsin(np.clip(z / r, -1, 1)))
    lon_eci = np.degrees(np.arctan2(y, x))
    lon_geo = _wrap_lon(lon_eci - np.degrees(OMEGA_EARTH_RAD_S * t))
    return lat, lon_geo, t


def interplanetary(bodies, trajectory=None, title="Diagrama interplanetario (eclíptica)",
                   path="interplanetary.png", xlim=None, ylim=None):
    """Dibuja órbitas planetarias y una trayectoria en coordenadas heliocéntricas (AU).

    bodies: lista de dict con keys: name, a (radio escalar AU) o r (N,2/3).
    trajectory: dict opcional con keys: name, r (N,2/3), color.
    """
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#0b1020")
    ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
    for b in bodies:
        if np.isscalar(b.get("a")):
            a = b["a"]
            th = np.linspace(0, 2 * np.pi, 361)
            ax.plot(a * np.cos(th), a * np.sin(th), color=b.get("color", "gray"),
                    lw=1.0, alpha=0.6, label=b["name"])
            if "r" in b and not np.isscalar(b["r"]):
                rr = np.asarray(b["r"])
                if rr.ndim == 2:
                    ax.scatter([rr[-1, 0]], [rr[-1, 1]], color=b.get("color", "gray"),
                               s=40, zorder=4)
        else:
            rr = np.asarray(b["r"])
            if rr.ndim == 2 and rr.shape[1] >= 2:
                ax.plot(rr[:, 0], rr[:, 1], color=b.get("color", "gray"), lw=1.2,
                        label=b["name"])
                ax.scatter([rr[-1, 0]], [rr[-1, 1]], color=b.get("color", "gray"), s=40, zorder=4)
    if trajectory is not None:
        tr = np.asarray(trajectory["r"])
        ax.plot(tr[:, 0], tr[:, 1], color=trajectory.get("color", "#ff5555"), lw=2.0,
                label=trajectory.get("name", "trayectoria"))
        ax.scatter([tr[0, 0]], [tr[0, 1]], color=trajectory.get("color", "#ff5555"),
                   marker="o", s=50, zorder=4, label="inicio")
        ax.scatter([tr[-1, 0]], [tr[-1, 1]], color=trajectory.get("color", "#ff5555"),
                   marker="*", s=80, zorder=4, label="fin")
    ax.set_aspect("equal")
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)
    else:
        ax.set_xlim(-2.2, 2.2)
        ax.set_ylim(-2.2, 2.2)
    ax.set_xlabel("x (AU, eclíptica)")
    ax.set_ylabel("y (AU, eclíptica)")
    ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
    ax.tick_params(colors="white")
    for sp in ax.spines.values():
        sp.set_color("gray")
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor="#0b1020")
    plt.close(fig)


def plot_orbit_3d(r_eci, title, path, show_earth=True):
    """Dibuja una órbita 3D en ECI (r_eci en metros, array (N,3))."""
    r = np.asarray(r_eci, dtype=float) / 1e3  # km
    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")
    if show_earth:
        u = np.linspace(0, 2 * np.pi, 40)
        v = np.linspace(0, np.pi, 20)
        xs = RE_KM * np.outer(np.cos(u), np.sin(v))
        ys = RE_KM * np.outer(np.sin(u), np.sin(v))
        zs = RE_KM * np.outer(np.ones_like(u), np.cos(v))
        ax.plot_surface(xs, ys, zs, color="#2a6f9b", alpha=0.25, linewidth=0)
    ax.plot(r[:, 0], r[:, 1], r[:, 2], color="#ff5555", lw=1.5, label="órbita")
    ax.scatter([r[0, 0]], [r[0, 1]], [r[0, 2]], color="green", s=40, label="inicio")
    ax.scatter([r[-1, 0]], [r[-1, 1]], [r[-1, 2]], color="red", s=40, label="fin")
    maxr = max(np.max(np.abs(r)), RE_KM) * 1.1
    ax.set_xlim(-maxr, maxr)
    ax.set_ylim(-maxr, maxr)
    ax.set_zlim(-maxr, maxr)
    ax.set_xlabel("x (km, ECI)")
    ax.set_ylabel("y (km, ECI)")
    ax.set_zlabel("z (km, ECI)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def circular_orbit_radius_au(a_au):
    return float(a_au)