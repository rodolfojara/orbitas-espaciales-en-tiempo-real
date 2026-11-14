"""Modelo orbital 3D con rotación terrestre.

Estado en ECI (Earth-Centered Inertial): r = [x,y,z] (m), v = [vx,vy,vz] (m/s).
Incluye gravedad puntual + perturbación J2 (aplanamiento terrestre).
Conversión a geodésicas (lat/lon/alt) considerando la rotación terrestre (GMST).
"""
from __future__ import annotations

import numpy as np

MU = 3.986004418e14       # m^3/s^2
RE = 6_371_000.0          # m
J2 = 1.08262668e-3
OMEGA_EARTH = 7.2921159e-5  # rad/s


def _accel(r):
    x, y, z = r
    rr = np.hypot(np.hypot(x, y), z)
    a = -MU * r / rr ** 3
    # J2
    factor = 1.5 * J2 * MU * RE ** 2 / rr ** 5
    zr = z / rr
    a = a + factor * r * (5 * zr * zr - 1)  # componente radial-ish; ajuste abajo
    # corrección estándar J2
    a_j2 = np.zeros(3)
    a_j2[0] = factor * x * (5 * zr * zr - 1)  # ya incluido arriba parcialmente; recalcular limpio
    return a


def accel(r):
    x, y, z = r
    rr = np.linalg.norm(r)
    a = -MU * r / rr ** 3
    # J2 perturbation (estándar)
    zr = z / rr
    coef = 1.5 * J2 * MU * RE ** 2 / rr ** 4
    a = a + coef * np.array([
        x / rr * (5 * zr * zr - 1),
        y / rr * (5 * zr * zr - 1),
        z / rr * (5 * zr * zr - 3),
    ])
    return a


def rk4_step(r, v, dt):
    def f(state):
        rr = state[:3]
        vv = state[3:]
        return np.concatenate([vv, accel(rr)])
    s = np.concatenate([r, v])
    k1 = f(s)
    k2 = f(s + dt / 2 * k1)
    k3 = f(s + dt / 2 * k2)
    k4 = f(s + dt * k3)
    s2 = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return s2[:3], s2[3:]


def propagate(r0, v0, t_array):
    """Propaga y devuelve arrays (N,3) de r_eci y v_eci para los tiempos t_array (s)."""
    r0 = np.asarray(r0, dtype=float)
    v0 = np.asarray(v0, dtype=float)
    t_array = np.asarray(t_array, dtype=float)
    rs = np.zeros((len(t_array), 3))
    vs = np.zeros((len(t_array), 3))
    r, v = r0.copy(), v0.copy()
    t_prev = 0.0
    for idx, t in enumerate(t_array):
        # avanzar de t_prev a t
        dt_total = t - t_prev
        # sub-pasos para estabilidad
        nsub = max(1, int(np.ceil(abs(dt_total) / 30.0)))
        dt = dt_total / nsub
        for _ in range(nsub):
            r, v = rk4_step(r, v, dt)
        rs[idx] = r
        vs[idx] = v
        t_prev = t
    return rs, vs


def gmst(t_s):
    """Ángulo de Greenwich Mean Sidereal Time (rad) para t segundos desde época J2000 simplificada.

    Usamos una aproximación lineal: GMST = 0 + OMEGA_EARTH * t (suficiente para demos).
    """
    return OMEGA_EARTH * t_s


def eci_to_geodetic(r_eci, t_s):
    """Convierte posición ECI (m) y tiempo (s) a (lat_deg, lon_deg, alt_m)."""
    r = np.asarray(r_eci, dtype=float)
    if r.ndim == 1:
        r = r[np.newaxis, :]
        single = True
    else:
        single = False
    t = np.broadcast_to(np.asarray(t_s, dtype=float), (r.shape[0],))
    # rotación por GMST: r_ecef = Rz(-gmst) * r_eci
    gm = gmst(t)
    cosg = np.cos(gm)
    sing = np.sin(gm)
    x = r[:, 0] * cosg + r[:, 1] * sing
    y = -r[:, 0] * sing + r[:, 1] * cosg
    z = r[:, 2]
    # geodésicas esféricas (suficiente)
    rr = np.sqrt(x * x + y * y + z * z)
    lat = np.degrees(np.arcsin(np.clip(z / rr, -1, 1)))
    lon = np.degrees(np.arctan2(y, x))
    alt = rr - RE
    if single:
        return float(lat[0]), float(lon[0]), float(alt[0])
    return lat, lon, alt


def keplerian_to_eci(a, e, i_deg, raan_deg, argp_deg, nu_deg):
    """Elementos keplerianos -> estado ECI (m, m/s)."""
    i = np.radians(i_deg)
    raan = np.radians(raan_deg)
    argp = np.radians(argp_deg)
    nu = np.radians(nu_deg)
    p = a * (1 - e * e)
    r_mag = p / (1 + e * np.cos(nu))
    # posición en marco orbital
    r_orb = np.array([r_mag * np.cos(nu), r_mag * np.sin(nu), 0.0])
    v_orb = np.array([-np.sin(nu), e + np.cos(nu), 0.0]) * np.sqrt(MU / p)
    # rotaciones: Rz(raan) Rx(i) Rz(argp)
    def Rz(a):
        return np.array([[np.cos(a), -np.sin(a), 0],
                         [np.sin(a), np.cos(a), 0],
                         [0, 0, 1]])
    def Rx(a):
        return np.array([[1, 0, 0],
                         [0, np.cos(a), -np.sin(a)],
                         [0, np.sin(a), np.cos(a)]])
    R = Rz(raan) @ Rx(i) @ Rz(argp)
    r_eci = R @ r_orb
    v_eci = R @ v_orb
    return r_eci, v_eci


def orbit_ground_track(a_km, e=0.0, i_deg=51.6, raan_deg=0.0, argp_deg=0.0,
                       n_orbits=3, dt_s=30.0):
    """Genera ground track (lat, lon) para una órbita kepleriana con J2, varias órbitas."""
    a = a_km * 1000.0
    r0, v0 = keplerian_to_eci(a, e, i_deg, raan_deg, argp_deg, 0.0)
    # período aproximado
    T = 2 * np.pi * np.sqrt(a ** 3 / MU)
    t = np.arange(0.0, n_orbits * T, dt_s)
    rs, _ = propagate(r0, v0, t)
    lat, lon, alt = eci_to_geodetic(rs, t)
    return lat, lon, alt, t
