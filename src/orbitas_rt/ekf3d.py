"""Filtro de Kalman extendido 3D (EKF) para estado orbital ECI.

Estado: x = [rx, ry, rz, vx, vy, vz] (m, m/s).
Medición: posición 3D (m) con ruido R (m).
Propagación: gravedad + J2 (orbit3d), con ruido de proceso (aceleración).
"""
from __future__ import annotations

import numpy as np

from .orbit3d import accel, rk4_step, RE


class EKF3D:
    def __init__(self, x0, P0, q_accel=0.5, max_step=10.0):
        self.x = np.asarray(x0, dtype=float).copy()
        self.P = np.asarray(P0, dtype=float).copy()
        self.q = q_accel
        self.max_step = max_step
        self.t = 0.0

    def _jacobian(self, x):
        eps = np.array([1.0, 1.0, 1.0, 0.01, 0.01, 0.01])
        A = np.zeros((6, 6))
        for i in range(6):
            dx = np.zeros(6)
            dx[i] = eps[i]
            # deriv = [v, a(r)]
            def f(state):
                r = state[:3]
                v = state[3:]
                return np.concatenate([v, accel(r)])
            fp = f(x + dx)
            fm = f(x - dx)
            A[:, i] = (fp - fm) / (2 * eps[i])
        return A

    def predict(self, dt):
        if dt <= 0:
            return
        nsub = max(1, int(np.ceil(dt / self.max_step)))
        h = dt / nsub
        for _ in range(nsub):
            A = self._jacobian(self.x)
            Adt = A * h
            Phi = np.eye(6) + Adt + 0.5 * Adt @ Adt
            Q = np.zeros((6, 6))
            # ruido de aceleración en velocidad, acoplado a posición
            Q[3:, 3:] = np.eye(3) * (self.q ** 2 * h)
            Q[:3, :3] = np.eye(3) * (self.q ** 2 * h ** 3 / 4.0)
            Q[:3, 3:] = np.eye(3) * (self.q ** 2 * h ** 2 / 2.0)
            Q[3:, :3] = Q[:3, 3:].T
            r, v = self.x[:3], self.x[3:]
            r2, v2 = rk4_step(r, v, h)
            self.x = np.concatenate([r2, v2])
            self.P = Phi @ self.P @ Phi.T + Q
        self.t += dt

    def update(self, z, R):
        z = np.asarray(z, dtype=float)
        R = np.asarray(R, dtype=float)
        H = np.eye(3, 6)  # medimos posición
        y = z - self.x[:3]
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I = np.eye(6) - K @ H
        self.P = I @ self.P @ I.T + K @ R @ K.T
        self.P = 0.5 * (self.P + self.P.T)

    def position_eci(self):
        return self.x[:3].copy()

    def latlonalt(self, t_s=None):
        from .orbit3d import eci_to_geodetic
        if t_s is None:
            t_s = self.t
        lat, lon, alt = eci_to_geodetic(self.x[:3], t_s)
        return float(lat), float(lon), float(alt)