"""Visualizaciones orbitales.

Dos familias:
  * Huella en tierra (ground track): para órbita baja/media (LEO/MEO). Proyecta la
    órbita sobre la superficie terrestre (lat/lon del punto sub-satélite).
  * Diagrama interplanetario: para órbita alta / Tierra-Luna / Tierra-L2 / Tierra-Marte.
    Muestra las órbitas de los planetas y la trayectoria del objeto en coordenadas
    heliocéntricas (eclíptica).
"""
from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


RE_KM = 6371.0
MU_KM3_S2 = 3.986004418e5  # km^3/s^2 (Tierra)
OMEGA_EARTH_RAD_S = 7.2921159e-5  # rotación terrestre


def _wrap_lon(lon):
    return (lon + 180.0) % 360.0 - 180.0


def ground_track(lat_deg, lon_deg, title, path, color="#1f77b4", show_earth=True):
    """Dibuja una huella en tierra (lat/lon) sobre un mapa equirectangular simple.

    lat_deg, lon_deg: arrays en grados.
    """
    lat = np.asarray(lat_deg, dtype=float)
    lon = np.asarray(lon_deg, dtype=float)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    if show_earth:
        # Fondo "océano" + contorno terrestre simplificado (elipse)
        ax.set_facecolor("#dbe9f4")
        theta = np.linspace(0, 2 * np.pi, 361)
        pass
        # Dibujo de la esfera terrestre como óvalo (aproximación)
        ex = np.linspace(-180, 180, 361)
        # contorno superior/inferior (círculo en proyección equirectangular es elipse)
        ax.plot(ex, 90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
        ax.plot(ex, -90 * np.ones_like(ex), color="#2a6f3b", lw=0.6, alpha=0.4)
    # Línea de la huella, coloreada por tiempo (índice)
    sc = ax.scatter(lon, lat, c=np.arange(len(lon)), cmap="viridis", s=6, zorder=3)
    ax.plot(lon, lat, color=color, lw=1.0, alpha=0.6, zorder=2)
    # marcar inicio y fin
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


def leo_ground_track(altitude_km=400.0, inclination_deg=51.6, n_orbits=3,
                    dt_s=30.0, raan_deg=0.0, arglat0_deg=0.0):
    """Genera (lat, lon) del punto sub-satélite para una órbita circular LEO.

    Devuelve (lat_deg array, lon_deg array, t_s array).
    """
    a = RE_KM + altitude_km
    # período orbital (s)
    T = 2 * np.pi * np.sqrt(a ** 3 / MU_KM3_S2)
    n = 2 * np.pi / T  # rad/s movimiento medio
    i = np.radians(inclination_deg)
    Omega = np.radians(raan_deg)
    u0 = np.radians(arglat0_deg)

    t_end = n_orbits * T
    t = np.arange(0.0, t_end, dt_s)
    u = u0 + n * t  # argumento de latitud

    # posición ECI (km)
    x = a * (np.cos(Omega) * np.cos(u) - np.sin(Omega) * np.sin(u) * np.cos(i))
    y = a * (np.sin(Omega) * np.cos(u) + np.cos(Omega) * np.sin(u) * np.cos(i))
    z = a * (np.sin(i) * np.sin(u))

    r = np.sqrt(x * x + y * y + z * z)
    lat = np.degrees(np.arcsin(np.clip(z / r, -1, 1)))
    lon_eci = np.degrees(np.arctan2(y, x))
    # rotación terrestre: lon geográfica = lon_eci - omega_E * t (deg)
    lon_geo = _wrap_lon(lon_eci - np.degrees(OMEGA_EARTH_RAD_S * t))
    return lat, lon_geo, t


def interplanetary(bodies, trajectory=None, title="Diagrama interplanetario (eclíptica)",
                   path="interplanetary.png", xlim=None, ylim=None):
    """Dibuja órbitas planetarias y una trayectoria en coordenadas heliocéntricas (AU).

    bodies: lista de dict con keys: name, r (N,2) o (N,3) array en AU (x,y), color, marker.
           Si se pasa una órbita circular, r puede ser un escalar (radio AU) -> se dibuja círculo.
    trajectory: dict opcional con keys: name, r (N,2/3), color.
    """
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#0b1020")
    # Sol
    ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
    # Órbitas planetarias (círculos) si se dan como radio escalar
    for b in bodies:
        if np.isscalar(b.get("a")):
            a = b["a"]
            th = np.linspace(0, 2 * np.pi, 361)
            ax.plot(a * np.cos(th), a * np.sin(th), color=b.get("color", "gray"),
                    lw=1.0, alpha=0.6, label=b["name"])
            # posición actual si se da r
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
        # Esfera terrestre
        u = np.linspace(0, 2 * np.pi, 40)
        v = np.linspace(0, np.pi, 20)
        xs = RE_KM * np.outer(np.cos(u), np.sin(v))
        ys = RE_KM * np.outer(np.sin(u), np.sin(v))
        zs = RE_KM * np.outer(np.ones_like(u), np.cos(v))
        ax.plot_surface(xs, ys, zs, color="#2a6f9b", alpha=0.25, linewidth=0)
    ax.plot(r[:, 0], r[:, 1], r[:, 2], color="#ff5555", lw=1.5, label="órbita")
    ax.scatter([r[0, 0]], [r[0, 1]], [r[0, 2]], color="green", s=40, label="inicio")
    ax.scatter([r[-1, 0]], [r[-1, 1]], [r[-1, 2]], color="red", s=40, label="fin")
    # ejes
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
