"""Trayectorias marcianas usando JPL Horizons.

Dos marcos de referencia:
  --center sun  (default): heliocéntrico, UA, plano eclíptico. Ideal para el
                crucero Tierra->Marte y naves en órbita solar.
  --center mars: marciano (center=499), km relativos a Marte, plano eclíptico.
                Ideal para naves ya orbitando Marte.

Uso:
  python examples/run_mars.py --list
  python examples/run_mars.py --sc -74                # MRO, crucero heliocéntrico
  python examples/run_mars.py --sc -74 --center mars  # MRO orbitando Marte
  python examples/run_mars.py --sc -168 --center mars # Perseverance en superficie
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
parser.add_argument("--center", choices=["sun", "mars"], default="sun",
                    help="origen del mapa: heliocéntrico (default) o marciano")
parser.add_argument("--start", default=None, help="fecha inicio YYYY-MM-DD (default 2026-01-01)")
parser.add_argument("--stop", default=None,
                    help="fecha fin (default 2026-01-31 con sun, 2026-01-02 con mars)")
parser.add_argument("--step", default=None,
                    help="paso Horizons (default '1 d' con sun, '5 m' con mars)")
parser.add_argument("--list", action="store_true", help="Listar naves disponibles")
args = parser.parse_args()

# Naves en superficie: en marco marciano trazan un círculo por la rotación del planeta.
LANDED = {"-84", "-76", "-168", "-189", "-253", "-254"}

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
        print("  %s  %s" % (k.rjust(5), v))
    sys.exit(0)

if args.center == "mars":
    START = args.start or "2026-01-01"
    STOP = args.stop or "2026-01-02"
    STEP = args.step or "5 m"
    CENTER = "499"
    UNITS = "KM-S"
else:
    START = args.start or "2026-01-01"
    STOP = args.stop or "2026-01-31"
    STEP = args.step or "1 d"
    CENTER = "@sun"
    UNITS = "AU-D"

sc_id = args.sc
sc_name = SPACECRAFT.get(sc_id, "sc_%s" % sc_id)

print("Descargando efemérides de Horizons...")
t_sc, r_sc, v_sc = fetch_vectors(sc_id, START, STOP, step=STEP,
                                  center=CENTER, frame="ECLIPTIC", units=UNITS)

if args.center == "mars":
    # Vista marcocéntrica: Marte en el origen, referencias en km.
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#0b1020")
    R_MARS = 3389.5
    ax.add_patch(plt.Circle((0, 0), R_MARS, color="orangered", alpha=0.45, zorder=3))
    ax.scatter([0], [0], color="orangered", s=25, zorder=4, label="Marte (centro)")
    for a, c, lbl in [(9376, "#aaaaaa", "Phobos"),
                      (20428, "#777777", "areostática"),
                      (23463, "#cccccc", "Deimos")]:
        th = np.linspace(0, 2 * np.pi, 361)
        ax.plot(a * np.cos(th), a * np.sin(th), color=c, lw=0.8, ls=":", alpha=0.5,
                label="órbita %s" % lbl)
    ax.plot(r_sc[:, 0], r_sc[:, 1], color="#ff5555", lw=2.0, label=sc_name)
    ax.scatter([r_sc[0, 0]], [r_sc[0, 1]], color="#00ff88", s=50, zorder=4, label="inicio")
    ax.scatter([r_sc[-1, 0]], [r_sc[-1, 1]], color="#ff5555", marker="*", s=80,
               zorder=4, label="fin (actual)")
    ax.set_aspect("equal")
    maxr = max(float(np.max(np.abs(r_sc))), 26000.0) * 1.1
    ax.set_xlim(-maxr, maxr)
    ax.set_ylim(-maxr, maxr)
    ax.set_xlabel("x (km, eclíptica, relativa a Marte)")
    ax.set_ylabel("y (km, eclíptica, relativa a Marte)")
    ax.set_title("Órbita marciana (marcocéntrica): %s (Horizons, real)" % sc_name)
    suffix = "mars_centered_%s.png"
else:
    # Vista heliocéntrica: Sol en el origen, órbitas de Tierra y Marte.
    t_earth, r_earth, _ = fetch_vectors("399", START, STOP, step=STEP,
                                        center=CENTER, frame="ECLIPTIC", units=UNITS)
    t_mars, r_mars, _ = fetch_vectors("499", START, STOP, step=STEP,
                                      center=CENTER, frame="ECLIPTIC", units=UNITS)
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#0b1020")
    ax.scatter([0], [0], color="#ffd24d", s=200, zorder=5, label="Sol")
    for a, c, lbl in [(1.0, "dodgerblue", "Tierra"), (1.5237, "orangered", "Marte")]:
        th = np.linspace(0, 2 * np.pi, 361)
        ax.plot(a * np.cos(th), a * np.sin(th), color=c, lw=0.8, alpha=0.4,
                label="órbita %s" % lbl)
    ax.plot(r_earth[:, 0], r_earth[:, 1], color="dodgerblue", lw=1.2, alpha=0.7, label="Tierra")
    ax.scatter([r_earth[-1, 0]], [r_earth[-1, 1]], color="dodgerblue", s=40, zorder=4)
    ax.plot(r_mars[:, 0], r_mars[:, 1], color="orangered", lw=1.2, alpha=0.7, label="Marte")
    ax.scatter([r_mars[-1, 0]], [r_mars[-1, 1]], color="orangered", s=40, zorder=4)
    ax.plot(r_sc[:, 0], r_sc[:, 1], color="#ff5555", lw=2.0, label=sc_name)
    ax.scatter([r_sc[0, 0]], [r_sc[0, 1]], color="#00ff88", s=50, zorder=4, label="inicio")
    ax.scatter([r_sc[-1, 0]], [r_sc[-1, 1]], color="#ff5555", marker="*", s=80,
               zorder=4, label="fin (actual)")
    ax.set_aspect("equal")
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.2, 2.2)
    ax.set_xlabel("x (UA, eclíptica)")
    ax.set_ylabel("y (UA, eclíptica)")
    ax.set_title("Trayectoria marciana (heliocéntrica): %s (Horizons, real)" % sc_name)
    suffix = "mars_%s.png"

ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
fig.tight_layout()
fname = suffix % sc_name.replace(" ", "_").replace("(", "").replace(")", "")
path = os.path.join(out, fname)
fig.savefig(path, dpi=140, facecolor="#0b1020")
plt.close(fig)
print("Guardado:", path)
print("%s: %d puntos | centro=%s | paso=%s" % (sc_name, len(r_sc), CENTER, STEP))
if args.center == "mars" and sc_id in LANDED:
    print("Nota: %s está en la superficie; el círculo de radio ~3390 km es la rotación "
          "de Marte, no una órbita." % sc_name)
