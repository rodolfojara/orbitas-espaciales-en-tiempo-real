"""Visualiza la situación actual de ESCAPADE (Blue/Gold) rumbo a Marte.

Datos reales vía JPL Horizons (requiere conexión a internet).
ESCAPADE está en L2 Tierra-Sol y ejecuta su inyección trans-Marte en nov-2026.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt.horizons import fetch_vectors
from orbitas_rt.viz import interplanetary

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

START = "2026-11-14"
STOP = "2027-09-01"
STEP = "5 d"

print("Descargando efemérides de Horizons...")
t_b, r_b, v_b = fetch_vectors("-9", START, STOP, step=STEP, center="@sun",
                               frame="ECLIPTIC", units="AU-D")
t_g, r_g, v_g = fetch_vectors("-10", START, STOP, step=STEP, center="@sun",
                               frame="ECLIPTIC", units="AU-D")
t_e, r_e, _ = fetch_vectors("399", START, STOP, step=STEP, center="@sun",
                            frame="ECLIPTIC", units="AU-D")
t_m, r_m, _ = fetch_vectors("499", START, STOP, step=STEP, center="@sun",
                            frame="ECLIPTIC", units="AU-D")

# Órbitas planetarias como círculos (semiejes mayores)
bodies = [
    {"name": "Tierra (órbita)", "a": 1.0, "color": "dodgerblue"},
    {"name": "Marte (órbita)", "a": 1.5237, "color": "orangered"},
    {"name": "Tierra (actual)", "r": r_e, "color": "dodgerblue"},
    {"name": "Marte (actual)", "r": r_m, "color": "orangered"},
]

path = os.path.join(out, "escapade_mars_transfer.png")
interplanetary(
    bodies,
    trajectory={"name": "ESCAPADE-Blue", "r": r_b, "color": "#00ff88"},
    title="ESCAPADE rumbo a Marte (datos reales Horizons, nov-2026 → sep-2027)",
    path=path,
)
print(f"Guardado: {path}")

# Segunda imagen: ambas sondas
path2 = os.path.join(out, "escapade_both.png")
# reutilizamos interplanetary con una trayectoria combinada (Blue) y agregamos Gold manualmente
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9, 9))
ax.set_facecolor("#0b1020")
ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
for a, c, lbl in [(1.0, "dodgerblue", "órbita Tierra"), (1.5237, "orangered", "órbita Marte")]:
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(a * np.cos(th), a * np.sin(th), color=c, lw=1.0, alpha=0.5, label=lbl)
ax.plot(r_b[:, 0], r_b[:, 1], color="#00ff88", lw=2, label="ESCAPADE-Blue")
ax.plot(r_g[:, 0], r_g[:, 1], color="#ff88ff", lw=2, label="ESCAPADE-Gold")
ax.scatter([r_b[0, 0]], [r_b[0, 1]], color="#00ff88", s=50)
ax.scatter([r_b[-1, 0]], [r_b[-1, 1]], color="#00ff88", marker="*", s=80)
ax.scatter([r_g[-1, 0]], [r_g[-1, 1]], color="#ff88ff", marker="*", s=80)
ax.scatter([r_e[-1, 0]], [r_e[-1, 1]], color="dodgerblue", s=40, label="Tierra (actual)")
ax.scatter([r_m[-1, 0]], [r_m[-1, 1]], color="orangered", s=40, label="Marte (actual)")
ax.set_aspect("equal")
ax.set_xlim(-2.2, 2.2)
ax.set_ylim(-2.2, 2.2)
ax.set_xlabel("x (AU)")
ax.set_ylabel("y (AU)")
ax.set_title("ESCAPADE-Blue y Gold rumbo a Marte (Horizons, real)")
ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
fig.tight_layout()
fig.savefig(path2, dpi=140, facecolor="#0b1020")
plt.close(fig)
print(f"Guardado: {path2}")
print(f"Blue: {len(r_b)} puntos, Gold: {len(r_g)} puntos")
