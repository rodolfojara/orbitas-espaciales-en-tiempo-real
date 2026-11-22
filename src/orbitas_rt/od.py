"""Determinación de órbitas (Orbit Determination) por mínimos cuadrados en batch.

Refina un estado orbital inicial usando un conjunto de mediciones de posición.
Usa propagación numérica (gravedad + J2) y Gauss-Newton iterativo.

Concepto:
  x0 (estado inicial) -> propagar a tiempos de medición -> residuos -> Jacobiano -> corrección
  Iterar hasta convergencia.
"""
from __future__ import annotations

import numpy as np

from .orbit3d import propagate, rk4_step


def batch_least_squares(measurements, t_meas, x0, max_iter=10, tol=1e-6):
    """Determinación de órbitas por mínimos cuadrados en batch.

    Args:
        measurements: array (N, 3) de posiciones medidas (m, ECI) en los tiempos t_meas.
        t_meas: array (N,) de tiempos (s) relativos a t0.
        x0: estado inicial [rx, ry, rz, vx, vy, vz] (m, m/s).
        max_iter: número máximo de iteraciones.
        tol: tolerancia de convergencia (norma del residuo).

    Returns:
        x_est: estado estimado (6,).
        residuals: residuos finales (N, 3).
        history: lista de (iter, cost).
    """
    x = np.asarray(x0, dtype=float).copy()
    meas = np.asarray(measurements, dtype=float)
    t = np.asarray(t_meas, dtype=float)
    N = len(t)

    history = []
    for it in range(max_iter):
        # Propagar estado a cada tiempo de medición
        # (propagar desde t=0 a cada t_i)
        predicted = np.zeros((N, 3))
        for i in range(N):
            # propagar de 0 a t[i]
            dt = t[i]
            if dt == 0:
                predicted[i] = x[:3]
            else:
                r0, v0 = x[:3], x[3:]
                # propagar con sub-pasos
                nsub = max(1, int(np.ceil(abs(dt) / 10.0)))
                h = dt / nsub
                r, v = r0.copy(), v0.copy()
                for _ in range(nsub):
                    r, v = rk4_step(r, v, h)
                predicted[i] = r

        # Residuos
        resid = (meas - predicted).ravel()  # (3N,)
        cost = np.sqrt(np.mean(resid ** 2))
        history.append((it, cost))

        if cost < tol:
            break

        # Jacobiano numérico: d(predicted)/d(x0)
        eps = np.array([1.0, 1.0, 1.0, 0.01, 0.01, 0.01])
        J = np.zeros((3 * N, 6))
        for j in range(6):
            dx = np.zeros(6)
            dx[j] = eps[j]
            # propagar con x+dx
            pred_p = np.zeros((N, 3))
            for i in range(N):
                r0, v0 = (x + dx)[:3], (x + dx)[3:]
                dt = t[i]
                if dt == 0:
                    pred_p[i] = r0
                else:
                    nsub = max(1, int(np.ceil(abs(dt) / 10.0)))
                    h = dt / nsub
                    r, v = r0.copy(), v0.copy()
                    for _ in range(nsub):
                        r, v = rk4_step(r, v, h)
                    pred_p[i] = r
            # propagar con x-dx
            pred_m = np.zeros((N, 3))
            for i in range(N):
                r0, v0 = (x - dx)[:3], (x - dx)[3:]
                dt = t[i]
                if dt == 0:
                    pred_m[i] = r0
                else:
                    nsub = max(1, int(np.ceil(abs(dt) / 10.0)))
                    h = dt / nsub
                    r, v = r0.copy(), v0.copy()
                    for _ in range(nsub):
                        r, v = rk4_step(r, v, h)
                    pred_m[i] = r
            J[:, j] = ((pred_p - pred_m).ravel()) / (2 * eps[j])

        # Gauss-Newton update
        try:
            delta = np.linalg.lstsq(J, resid, rcond=None)[0]
        except np.linalg.LinAlgError:
            break
        x = x + delta

    # residuos finales
    predicted = np.zeros((N, 3))
    for i in range(N):
        r0, v0 = x[:3], x[3:]
        dt = t[i]
        if dt == 0:
            predicted[i] = r0
        else:
            nsub = max(1, int(np.ceil(abs(dt) / 10.0)))
            h = dt / nsub
            r, v = r0.copy(), v0.copy()
            for _ in range(nsub):
                r, v = rk4_step(r, v, h)
            predicted[i] = r
    resid = meas - predicted

    return x, resid, history


def covariance_from_residuals(residuals, J):
    """Estima la covarianza del estado a partir de los residuos."""
    resid = residuals.ravel()
    sigma = np.std(resid)
    try:
        P = sigma ** 2 * np.linalg.inv(J.T @ J)
    except np.linalg.LinAlgError:
        P = np.eye(6) * sigma ** 2
    return P, sigma