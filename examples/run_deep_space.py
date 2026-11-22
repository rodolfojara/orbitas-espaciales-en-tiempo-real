"""Trayectorias de naves en espacio profundo (heliocéntricas) usando JPL Horizons.

Muestra la órbita de naves que han salido más allá de la Luna, en coordenadas
heliocéntricas (AU), con las órbitas de los planetas de referencia.

Uso:
  python examples/run_deep_space.py --list
  python examples/run_deep_space.py --sc -98   # New Horizons
  python examples/run_deep_space.py --sc -31    # Voyager 1
"""
import os
import sys
import argparse
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orbitas_rt.horizons import fetch_vectors

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

# Cargar registro de naves
reg_path = os.path.join(os.path.dirname(__file__), "..", "src", "orbitas_rt", "data", "deep_space.json")
with open(reg_path, encoding="utf-8") as f:
    registry = json.load(f)
SPACECRAFT = {str(s["id"]): s["name"] for s in registry}

parser = argparse.ArgumentParser()
parser.add_argument("--sc", default="-98", help="Horizons ID de la nave (default New Horizons)")
parser.add_argument("--start", default="2026-01-01", help="fecha inicio YYYY-MM-DD")
parser.add_argument("--stop", default="2026-01-31", help="fecha fin YYYY-MM-DD")
parser.add_argument("--list", action="store_true", help="Listar naves disponibles")
args = parser.parse_args()

if args.list:
    print("Naves en espacio profundo disponibles en Horizons (%d):" % len(SPACECRAFT))
    for k, v in sorted(SPACECRAFT.items(), key=lambda x: x[1]):
        info = next((s for s in registry if str(s["id"]) == k), {})
        print("  %s  %-35s  %s  (%s)" % (k.rjust(7), v, info.get("target", ""), info.get("status", "")))
    sys.exit(0)

START = args.start
STOP = args.stop
STEP = "1 d"

sc_id = args.sc
sc_info = next((s for s in registry if str(s["id"]) == sc_id), {})
sc_name = sc_info.get("name", "sc_%s" % sc_id)

print("Descargando efemérides de Horizons...")
t_sc, r_sc, v_sc = fetch_vectors(sc_id, START, STOP, step=STEP,
                                  center="@sun", frame="ECLIPTIC", units="AU-D")

# Planetas de referencia
t_e, r_e, _ = fetch_vectors("399", START, STOP, step=STEP,
                              center="@sun", frame="ECLIPTIC", units="AU-D")
t_m, r_m, _ = fetch_vectors("499", START, STOP, step=STEP,
                              center="@sun", frame="ECLIPTIC", units="AU-D")

fig, ax = plt.subplots(figsize=(9, 9))
ax.set_facecolor("#0b1020")
ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
# Órbitas planetarias
for a, c, lbl in [(1.0, "dodgerblue", "Tierra"), (1.5237, "orangered", "Marte")]:
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(a * np.cos(th), a * np.sin(th), color=c, lw=0.8, alpha=0.3, label="órbita %s" % lbl)
# Tierra y Marte
ax.plot(r_e[:, 0], r_e[:, 1], color="dodgerblue", lw=1.0, alpha=0.6)
ax.scatter([r_e[-1, 0]], [r_e[-1, 1]], color="dodgerblue", s=40, zorder=4, label="Tierra (actual)")
ax.plot(r_m[:, 0], r_m[:, 1], color="orangered", lw=1.0, alpha=0.6)
ax.scatter([r_m[-1, 0]], [r_m[-1, 1]], color="orangered", s=40, zorder=4, label="Marte (actual)")
# Nave
ax.plot(r_sc[:, 0], r_sc[:, 1], color="#ff5555", lw=2.0, label=sc_name)
ax.scatter([r_sc[0, 0]], [r_sc[0, 1]], color="#00ff88", s=50, zorder=4, label="inicio")
ax.scatter([r_sc[-1, 0]], [r_sc[-1, 1]], color="#ff5555", marker="*", s=80, zorder=4, label="fin (actual)")

ax.set_aspect("equal")
# Auto-scale based on spacecraft distance
maxr = max(np.max(np.abs(r_sc)), 2.0)
ax.set_xlim(-maxr * 1.1, maxr * 1.1)
ax.set_ylim(-maxr * 1.1, maxr * 1.1)
ax.set_xlabel("x (AU, eclíptica)")
ax.set_ylabel("y (AU, eclíptica)")
ax.set_title("Trayectoria espacio profundo: %s (Horizons, real)" % sc_name)
ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
fig.tight_layout()
path = os.path.join(out, "deep_space_%s.png" % sc_name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_"))
fig.savefig(path, dpi=140, facecolor="#0b1020")
plt.close(fig)
print("Guardado:", path)
print("%s: %d puntos" % (sc_name, len(r_sc)))