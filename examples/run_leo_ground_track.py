"""Genera una huella en tierra (ground track) para una órbita LEO.

Ejemplo: órbita tipo ISS (400 km, inclinación 51.6°) durante 3 órbitas.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt.viz import ground_track, ground_track_ortho, leo_ground_track

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

lat, lon, t = leo_ground_track(altitude_km=400.0, inclination_deg=51.6,
                                n_orbits=3, dt_s=30.0)

path = os.path.join(out, "leo_ground_track.png")
ground_track(lat, lon, "Huella en tierra - LEO 400 km, inc 51.6° (3 órbitas)",
             path)
print(f"Guardado: {path}  ({len(t)} puntos)")

path2 = os.path.join(out, "leo_ground_track_ortho.png")
ground_track_ortho(lat, lon, "Huella en tierra - LEO 400 km, inc 51.6° (3 órbitas)",
                   path2, subsolar_lon=30.0)
print(f"Guardado: {path2}")
