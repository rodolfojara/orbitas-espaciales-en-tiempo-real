"""Trayectorias lunares (cislunar) usando JPL Horizons.

Muestra la órbita de naves alrededor de la Tierra-Luna en coordenadas
geocéntricas (km), con la órbita lunar de referencia.

Naves disponibles en Horizons (ID):
  -85  LRO (Lunar Reconnaissance Orbiter)
  -155 Danuri (KPLO)
  -1024 Artemis II (Orion)
  -1176 CAPSTONE
  -164 Lunar Flashlight
  -240 SLIM (JAXA)
  -86  Chandrayaan-1
  -152 Chandrayaan-2 (Orbiter)
  -158 Chandrayaan-3 (Lander)
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

parser = argparse.ArgumentParser()
parser.add_argument("--sc", default="-85", help="Horizons ID de la nave (default LRO)")
parser.add_argument("--start", default="2026-11-15", help="fecha inicio YYYY-MM-DD")
parser.add_argument("--stop", default="2026-11-18", help="fecha fin YYYY-MM-DD")
args = parser.parse_args()

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

START = args.start
STOP = args.stop
STEP = "4 h"

SPACECRAFT = {
    "-85": "LRO",
    "-155": "Danuri",
    "-1024": "Artemis II",
    "-1176": "CAPSTONE",
    "-164": "Lunar Flashlight",
    "-240": "SLIM",
    "-86": "Chandrayaan-1",
    "-152": "Chandrayaan-2",
    "-158": "Chandrayaan-3",
    "-169": "Chandrayaan-3 Orbiter",
}

sc_id = args.sc
sc_name = SPACECRAFT.get(sc_id, "sc_%s" % sc_id)

print("Descargando efemérides lunares de Horizons...")
# Luna (relativa a Tierra, center=399)
t_moon, r_moon, v_moon = fetch_vectors("301", START, STOP, step=STEP,
                                        center="399", frame="ECLIPTIC", units="KM-S")
# Nave (relativa a Tierra)
t_sc, r_sc, v_sc = fetch_vectors(sc_id, START, STOP, step=STEP,
                                  center="399", frame="ECLIPTIC", units="KM-S")

# Dibujar: Tierra en origen, órbita lunar, nave
fig, ax = plt.subplots(figsize=(9, 9))
ax.set_facecolor("#0b1020")
ax.scatter([0], [0], color="#4da6ff", s=200, zorder=5, label="Tierra")
# Órbita lunar (círculo ~384400 km)
theta = np.linspace(0, 2 * np.pi, 361)
ax.plot(384400 * np.cos(theta), 384400 * np.sin(theta), color="#aaaaaa",
        lw=0.8, alpha=0.4, label="órbita lunar (ref)")
# Luna
ax.plot(r_moon[:, 0], r_moon[:, 1], color="#cccccc", lw=1.0, alpha=0.6, label="Luna")
ax.scatter([r_moon[-1, 0]], [r_moon[-1, 1]], color="#ffffff", s=60, zorder=4, label="Luna (actual)")
# Nave
ax.plot(r_sc[:, 0], r_sc[:, 1], color="#ff5555", lw=2.0, label=sc_name)
ax.scatter([r_sc[0, 0]], [r_sc[0, 1]], color="#00ff88", s=50, zorder=4, label="inicio")
ax.scatter([r_sc[-1, 0]], [r_sc[-1, 1]], color="#ff5555", marker="*", s=80, zorder=4, label="fin (actual)")

ax.set_aspect("equal")
ax.set_xlim(-420000, 420000)
ax.set_ylim(-420000, 420000)
ax.set_xlabel("x (km, eclíptica)")
ax.set_ylabel("y (km, eclíptica)")
ax.set_title("Trayectoria cislunar: %s (Horizons, real)" % sc_name)
ax.grid(alpha=0.2, linestyle=":")
ax.legend(fontsize=8, loc="upper right", facecolor="#1a1f33", labelcolor="white")
fig.tight_layout()
path = os.path.join(out, "lunar_%s.png" % sc_name.replace(" ", "_").replace("(", "").replace(")", ""))
fig.savefig(path, dpi=140, facecolor="#0b1020")
plt.close(fig)
print("Guardado:", path)
print("%s: %d puntos" % (sc_name, len(r_sc)))