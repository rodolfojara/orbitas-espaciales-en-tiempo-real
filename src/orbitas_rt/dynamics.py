"""Modelo dinámico plano (2D) de un vehículo cerca de la Tierra.

Marco inercial centrado en la Tierra, plano del vuelo:
    estado s = [x, y, vx, vy]   (metros, m/s)
    el vehículo parte en (0, RE) (la "vertical" inicial es +y).

Fuerzas incluidas:
    * gravedad puntual (mu / r^2)
    * empuje con perfil de aceleración y programa de cabeceo (pitch program)
    * arrastre con atmósfera exponencial y coeficiente balístico constante

Simplificaciones (documentadas en el README): sin rotación terrestre, sin
viento, sin sustentación, vuelo coplanar.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

MU = 3.986004418e14  # m^3/s^2, parámetro gravitacional de la Tierra
RE = 6_371_000.0     # m, radio medio de la Tierra
RHO0 = 1.225         # kg/m^3
H_SCALE = 7200.0     # m, altura de escala de la atmósfera


@dataclass(frozen=True)
class VehicleParams:
    """Parámetros del perfil de vuelo nominal."""

    burn_time: float = 500.0       # s, duración del encendido
    a0: float = 16.0               # m/s^2, aceleración por empuje al inicio
    a1: float = 34.0               # m/s^2, aceleración por empuje al final
    pitch_final_deg: float = 89.0  # grados desde la vertical al final del encendido
    pitch_exp: float = 0.70        # forma del programa de cabeceo
    beta: float = 450.0            # kg/m^2, coeficiente balístico m/(Cd*A)

    def perturbed(self, **kw) -> "VehicleParams":
        return replace(self, **kw)


def thrust_accel(t: float, p: VehicleParams) -> float:
    if t < 0.0 or t > p.burn_time:
        return 0.0
    return p.a0 + (p.a1 - p.a0) * t / p.burn_time


def pitch_angle(t: float, p: VehicleParams) -> float:
    frac = min(max(t / p.burn_time, 0.0), 1.0)
    return np.radians(p.pitch_final_deg) * frac ** p.pitch_exp


def deriv(t: float, s: np.ndarray, p: VehicleParams, extra=None) -> np.ndarray:
    r = s[:2]
    v = s[2:]
    rn = np.hypot(*r)
    up = r / rn
    east = np.array([up[1], -up[0]])
    phi = pitch_angle(t, p)
    thrust_dir = np.cos(phi) * up + np.sin(phi) * east
    h = rn - RE
    rho = RHO0 * np.exp(-max(h, 0.0) / H_SCALE)
    a = -MU * r / rn**3
    a = a + thrust_accel(t, p) * thrust_dir
    a = a - 0.5 * rho * np.hypot(*v) * v / p.beta
    if extra is not None:  # perturbación no modelada (solo se usa en la "verdad" simulada)
        a = a + extra(t, s)
    return np.concatenate([v, a])


def rk4_step(t: float, s: np.ndarray, dt: float, p: VehicleParams, extra=None) -> np.ndarray:
    k1 = deriv(t, s, p, extra)
    k2 = deriv(t + dt / 2, s + dt / 2 * k1, p, extra)
    k3 = deriv(t + dt / 2, s + dt / 2 * k2, p, extra)
    k4 = deriv(t + dt, s + dt * k3, p, extra)
    return s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def initial_state() -> np.ndarray:
    return np.array([0.0, RE, 0.0, 0.0])


# --- utilidades de conversión -------------------------------------------------

def altitude(s: np.ndarray) -> float:
    return float(np.hypot(s[0], s[1]) - RE)


def speed(s: np.ndarray) -> float:
    return float(np.hypot(s[2], s[3]))


def downrange(s: np.ndarray) -> float:
    """Distancia sobre la superficie desde el punto de lanzamiento (m)."""
    return float(RE * np.arctan2(s[0], s[1]))
