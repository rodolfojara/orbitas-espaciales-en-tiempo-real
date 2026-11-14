"""Modelo 3D con rotación terrestre: órbita inclinada con J2 + ground track.

Genera:
  - examples/output/orbit3d.png       : órbita 3D en ECI
  - examples/output/orbit3d_ground.png : huella en tierra (lat/lon) considerando rotación terrestre
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from orbitas_rt.orbit3d import orbit_ground_track, propagate, keplerian_to_eci
from orbitas_rt.viz import ground_track, plot_orbit_3d

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

# Órbita: 500 km, inclinación 45°, ligeramente excéntrica
a_km = 6871.0
lat, lon, alt, t = orbit_ground_track(a_km=a_km, e=0.01, i_deg=45.0,
                                      raan_deg=30.0, argp_deg=10.0,
                                      n_orbits=2, dt_s=60.0)

# Órbita 3D en ECI
r0, v0 = keplerian_to_eci(a_km * 1000.0, 0.01, 45.0, 30.0, 10.0, 0.0)
rs, _ = propagate(r0, v0, t)
plot_orbit_3d(rs, "Órbita 3D en ECI (500 km, inc 45°, J2)", os.path.join(out, "orbit3d.png"))
ground_track(lat, lon, "Huella en tierra 3D+rotación terrestre (2 órbitas)", os.path.join(out, "orbit3d_ground.png"))
print(f"Guardado: orbit3d.png, orbit3d_ground.png  ({len(t)} puntos)")
print(f"Altitud media: {alt.mean()/1e3:.1f} km")
