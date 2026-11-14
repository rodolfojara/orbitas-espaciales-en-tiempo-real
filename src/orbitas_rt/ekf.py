"""Filtro de Kalman extendido (EKF) para estado [x, y, vx, vy].

Ciclo:
    predict(t)  -> propaga estado y covarianza hasta el tiempo t con el modelo
    update(z)   -> corrige con una medición z = [altitud (m), rapidez (m/s)]

Si no llegan mediciones, solo se llama a predict(): la estimación sigue
avanzando y la covarianza P crece. Esa covarianza es la incertidumbre que se
dibuja como elipse en los gráficos.
"""
from __future__ import annotations

import numpy as np

from .dynamics import RE, VehicleParams, deriv, rk4_step


class EKF:
    def __init__(
        self,
        t0: float,
        x0: np.ndarray,
        P0: np.ndarray,
        params: VehicleParams,
        q_burn: float = 1.5,
        q_coast: float = 2.0,
        max_step: float = 0.5,
    ):
        """
        q_burn / q_coast: densidad espectral del ruido de aceleración
        (m/s^2 por raíz de segundo) durante el encendido y fuera de él. Modela
        lo que el modelo NO sabe: variaciones de empuje, viento, cabeceo real.
        """
        self.t = float(t0)
        self.x = np.asarray(x0, dtype=float).copy()
        self.P = np.asarray(P0, dtype=float).copy()
        self.params = params
        self.q_burn = q_burn
        self.q_coast = q_coast
        self.max_step = max_step

    # -- propagación ----------------------------------------------------------
    def _jacobian(self, t: float, x: np.ndarray) -> np.ndarray:
        eps = np.array([1.0, 1.0, 0.01, 0.01])
        A = np.zeros((4, 4))
        for i in range(4):
            dx = np.zeros(4)
            dx[i] = eps[i]
            fp = deriv(t, x + dx, self.params)
            fm = deriv(t, x - dx, self.params)
            A[:, i] = (fp - fm) / (2 * eps[i])
        return A

    def predict(self, t: float) -> None:
        if t < self.t - 1e-9:
            raise ValueError("predict solo avanza en el tiempo")
        while self.t < t - 1e-9:
            dt = min(self.max_step, t - self.t)
            A = self._jacobian(self.t, self.x)
            Adt = A * dt
            Phi = np.eye(4) + Adt + 0.5 * Adt @ Adt
            q = self.q_burn if self.t <= self.params.burn_time else self.q_coast
            Q = np.zeros((4, 4))
            Q[2, 2] = Q[3, 3] = q**2 * dt
            Q[0, 0] = Q[1, 1] = 0.25 * q**2 * dt**3  # acople vel->pos
            self.x = rk4_step(self.t, self.x, dt, self.params)
            self.P = Phi @ self.P @ Phi.T + Q
            self.t += dt

    # -- corrección -----------------------------------------------------------
    @staticmethod
    def h(x: np.ndarray) -> np.ndarray:
        return np.array([np.hypot(x[0], x[1]) - RE, np.hypot(x[2], x[3])])

    @staticmethod
    def H(x: np.ndarray) -> np.ndarray:
        rn = np.hypot(x[0], x[1])
        vn = max(np.hypot(x[2], x[3]), 1e-6)
        return np.array([
            [x[0] / rn, x[1] / rn, 0.0, 0.0],
            [0.0, 0.0, x[2] / vn, x[3] / vn],
        ])

    def update(self, z: np.ndarray, R: np.ndarray) -> None:
        H = self.H(self.x)
        y = np.asarray(z, dtype=float) - self.h(self.x)
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I_KH = np.eye(4) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T  # forma de Joseph
        self.P = 0.5 * (self.P + self.P.T)

    # -- salidas en marco local (adelante / arriba) -------------------------------
    def local_position_cov(self) -> np.ndarray:
        """Covarianza 2x2 de la posición en ejes (adelante, arriba), en m^2."""
        up = self.x[:2] / np.hypot(*self.x[:2])
        east = np.array([up[1], -up[0]])
        T = np.vstack([east, up])
        return T @ self.P[:2, :2] @ T.T
