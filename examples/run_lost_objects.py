"""Objetos 'perdidos' en espacio profundo (etapas de cohetes, impactores, etc.).

Estos objetos salieron más allá de la Luna pero no son satélites activos.
Incluye etapas de cohetes Apollo, Centaur, boosters, etc.

Uso:
  python examples/run_lost_objects.py --list
  python examples/run_lost_objects.py --sc -399080   # Apollo 8 S-IVB
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

reg_path = os.path.join(os.path.dirname(__file__), "..", "src", "orbitas_rt", "data", "lost_objects.json")
with open(reg_path, encoding="utf-8") as f:
    registry = json.load(f)
OBJECTS = {str(o["id"]): o for o in registry}

parser = argparse.ArgumentParser()
parser.add_argument("--sc", default="-399080", help="Horizons ID del objeto (default Apollo 8 S-IVB)")
parser.add_argument("--start", default="2026-01-01", help="fecha inicio YYYY-MM-DD")
parser.add_argument("--stop", default="2026-01-31", help="fecha fin YYYY-MM-DD")
parser.add_argument("--list", action="store_true", help="Listar objetos disponibles")
args = parser.parse_args()

if args.list:
    print("Objetos perdidos en espacio profundo (%d):" % len(OBJECTS))
    for k, v in sorted(OBJECTS.items(), key=lambda x: x[1]["name"]):
        print("  %s  %-35s  %s  (%s)" % (k.rjust(8), v["name"], v["type"], v["status"]))
    sys.exit(0)

START = args.start
STOP = args.stop
STEP = "1 d"

obj_id = args.sc
obj_info = OBJECTS.get(obj_id, {"name": "obj_%s" % obj_id, "type": "unknown", "status": "unknown"})
obj_name = obj_info["name"]

print("Descargando efemérides de Horizons...")
t_sc, r_sc, v_sc = fetch_vectors(obj_id, START, STOP, step=STEP,
                                  center="@sun", frame="ECLIPTIC", units="AU-D")

# Tierra
t_e, r_e, _ = fetch_vectors("399", START, STOP, step=STEP,
                              center="@sun", frame="ECLIPTIC", units="AU-D")

fig, ax = plt.subplots(figsize=(9, 9))
ax.set_facecolor("#0b1020")
ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
th = np.linspace(0, 2 * np.pi, 361)
ax.plot(1.0 * np.cos(th), 1.0 * np.sin(th), color="dodgerblue", lw=0.8, alpha=0.3, label="órbita Tierra")
ax.plot(r_e[:, 0], r_e[:, 1], color="dodgerblue", lw=1.0, alpha=0.6)
ax.scatter([r_e[-1, 0]], [r_e[-1, 1]], color="dodgerblue", s=40, zorder=4, label="Tierra (actual)")
ax.plot(r_sc[:, 0], r_sc[:, 1], color="#ff5555", lw=2.0, label=obj_name)
ax.scatter([r_sc[0, 0]], [r_sc[0, 1]], color="#00ff88", s=50, zorder=4, label="inicio")
ax.scatter([r_sc[-1, 0]], [r_sc[-1, 1]], color="#ff5555", marker="*", s=80, zorder=4, label="fin (actual)")

ax.set_aspect("equal")
maxr = max(np.max(np.abs(r_sc)), 2.0)
ax.set_xlim(-maxr * 1.1, maxr * 1.1)
ax.set_ylim(-maxr * 1.1, maxr * 1.1)
ax.set_xlabel("x (AU, eclíptica)")
ax.set_ylabel("y (AU, eclíptica)")
ax.set_title("Objeto perdido: %s (Horizons, real)" % obj_name)
ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
fig.tight_layout()
path = os.path.join(out, "lost_%s.png" % obj_name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_"))
fig.savefig(path, dpi=140, facecolor="#0b1020")
plt.close(fig)
print("Guardado:", path)
print("%s: %d puntos | %s" % (obj_name, len(r_sc), obj_info.get("status", "")))