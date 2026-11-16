"""Trayectorias marcianas (heliocéntricas) usando JPL Horizons.

Muestra la órbita de naves alrededor del Sol en coordenadas heliocéntricas (AU),
con las órbitas de Tierra y Marte de referencia.

Naves disponibles en Horizons (ID):
  -3    Mars Orbiter Mission (MOM/Mangalyaan)
  -41   Mars Express (MEX)
  -53   Mars Odyssey
  -62   EMM (Hope, EAU)
  -65   MarCO-A
  -66   MarCO-B
  -74   Mars Reconnaissance Orbiter (MRO)
  -76   Mars Science Laboratory (Curiosity)
  -84   Phoenix
  -143  ExoMars 2016 (TGO)
  -168  Mars2020 (Perseverance)
  -189  InSight
  -202  MAVEN
  -253  Opportunity (MER-B)
  -254  Spirit (MER-A)
  -530  Mars Pathfinder
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orbitas_rt.horizons import fetch_vectors

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--sc", default="-74", help="Horizons ID de la nave (default MRO)")
parser.add_argument("--start", default="2026-01-01", help="fecha inicio YYYY-MM-DD")
parser.add_argument("--stop", default="2026-01-31", help="fecha fin YYYY-MM-DD")
parser.add_argument("--list", action="store_true", help="Listar naves disponibles")
args = parser.parse_args()

SPACECRAFT = {
    "-3": "MOM (Mangalyaan)",
    "-41": "Mars Express",
    "-53": "Mars Odyssey",
    "-62": "EMM (Hope)",
    "-65": "MarCO-A",
    "-66": "MarCO-B",
    "-74": "MRO",
    "-76": "MSL (Curiosity)",
    "-84": "Phoenix",
    "-143": "ExoMars TGO",
    "-168": "Mars2020 (Perseverance)",
    "-189": "InSight",
    "-202": "MAVEN",
    "-253": "Opportunity",
    "-254": "Spirit",
    "-530": "Mars Pathfinder",
}

if args.list:
    print("Naves marcianas disponibles en Horizons (%d):" % len(SPACECRAFT))
    for k, v in sorted(SPACECRAFT.items(), key=lambda x: x[1]):
        print("  %s  %s" % (k.rjust(7), v))
    sys.exit(0)

START = args.start
STOP = args.stop
STEP = "1 d"

sc_id = args.sc
sc_name = SPACECRAFT.get(sc_id, "sc_%s" % sc_id)

print("Descargando efemérides marcianas de Horizons...")
# Tierra y Marte (heliocéntrico)
t_earth, r_earth, _ = fetch_vectors("399", START, STOP, step=STEP,
                                     center="@sun", frame="ECLIPTIC", units="AU-D")
t_mars, r_mars, _ = fetch_vectors("499", START, STOP, step=STEP,
                                   center="@sun", frame="ECLIPTIC", units="AU-D")
# Nave
t_sc, r_sc, _ = fetch_vectors(sc_id, START, STOP, step=STEP,
                               center="@sun", frame="ECLIPTIC", units="AU-D")

fig, ax = plt.subplots(figsize=(9, 9))
ax.set_facecolor("#0b1020")
ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
# Órbitas planetarias
for a, c, lbl in [(1.0, "dodgerblue", "Tierra"), (1.5237, "orangered", "Marte")]:
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(a * np.cos(th), a * np.sin(th), color=c, lw=1.0, alpha=0.4, label="órbita %s" % lbl)
# Tierra y Marte (posiciones)
ax.plot(r_earth[:, 0], r_earth[:, 1], color="dodgerblue", lw=1.2, alpha=0.7, label="Tierra")
ax.scatter([r_earth[-1, 0]], [r_earth[-1, 1]], color="dodgerblue", s=40, zorder=4)
ax.plot(r_mars[:, 0], r_mars[:, 1], color="orangered", lw=1.2, alpha=0.7, label="Marte")
ax.scatter([r_mars[-1, 0]], [r_mars[-1, 1]], color="orangered", s=40, zorder=4)
# Nave
ax.plot(r_sc[:, 0], r_sc[:, 1], color="#ff5555", lw=2.0, label=sc_name)
ax.scatter([r_sc[0, 0]], [r_sc[0, 1]], color="#00ff88", s=50, zorder=4, label="inicio")
ax.scatter([r_sc[-1, 0]], [r_sc[-1, 1]], color="#ff5555", marker="*", s=80, zorder=4, label="fin (actual)")

ax.set_aspect("equal")
ax.set_xlim(-2.2, 2.2)
ax.set_ylim(-2.2, 2.2)
ax.set_xlabel("x (AU, eclíptica)")
ax.set_ylabel("y (AU, eclíptica)")
ax.set_title("Trayectoria marciana: %s (Horizons, real)" % sc_name)
ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
fig.tight_layout()
path = os.path.join(out, "mars_%s.png" % sc_name.replace(" ", "_").replace("(", "").replace(")", ""))
fig.savefig(path, dpi=140, facecolor="#0b1020")
plt.close(fig)
print("Guardado:", path)
print("%s: %d puntos" % (sc_name, len(r_sc)))