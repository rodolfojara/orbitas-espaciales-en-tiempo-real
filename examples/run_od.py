"""Determinación de órbitas (OD) por mínimos cuadrados en batch.

Demuestra el módulo od.py: refina un estado orbital inicial usando un conjunto
de mediciones de posición simuladas.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np

from orbitas_rt.od import batch_least_squares
from orbitas_rt.orbit3d import rk4_step, eci_to_geodetic

out = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out, exist_ok=True)

# Órbita inicial: LEO a 500 km, inclinación 45°
r0 = np.array([6871000.0, 0.0, 0.0])
v0 = np.array([0.0, 7600.0, 0.0])
x0 = np.concatenate([r0, v0])

# Generar mediciones (con ruido) en t = 0, 60, 120, ..., 600 s
t_meas = np.arange(0, 601, 60, dtype=float)
meas = np.zeros((len(t_meas), 3))
for i, ti in enumerate(t_meas):
    r, v = r0.copy(), v0.copy()
    nsub = max(1, int(abs(ti) / 10.0))
    h = ti / nsub if nsub > 0 else 0
    for _ in range(nsub):
        r, v = rk4_step(r, v, h)
    meas[i] = r + np.random.normal(0, 100.0, 3)  # ruido 100 m

print("Estado inicial: r=%.1f km, v=%.1f m/s" % (np.linalg.norm(r0)/1000, np.linalg.norm(v0)))
print("Mediciones: %d puntos con ruido 100 m" % len(t_meas))

# OD
x_est, resid, history = batch_least_squares(meas, t_meas, x0, max_iter=10, tol=1.0)

print()
print("Estado estimado: r=%.3f km, v=%.3f m/s" % (np.linalg.norm(x_est[:3])/1000, np.linalg.norm(x_est[3:])))
print("Error en posición: %.1f m" % np.linalg.norm(x_est[:3] - r0))
print("Error en velocidad: %.3f m/s" % np.linalg.norm(x_est[3:] - v0))
print("RMS residuo: %.1f m" % np.sqrt(np.mean(resid**2)))
print("Iteraciones: %d" % len(history))
for it, cost in history:
    print("  iter %d: RMS=%.2f m" % (it, cost))