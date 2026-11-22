"""Transformaciones de marco de referencia para mecánica orbital.

Centraliza conversiones entre:
  ECI (Earth-Centered Inertial), ECEF (Earth-Fixed),
  geodésico (lat/lon/alt), heliocéntrico (AU).

Usa el módulo timeutils para GMST real (IAU 2006).
"""
from __future__ import annotations

import math
from datetime import datetime

import numpy as np

from .timeutils import gmst_from_dt, RE
from .orbit3d import MU, RE as RE3D


def eci_to_ecef(r_eci, dt):
    """ECI (m) -> ECEF (m) usando GMST real."""
    r = np.asarray(r_eci, dtype=float)
    theta = gmst_from_dt(dt if isinstance(dt, datetime) else None) if False else None
    # gmst needs jd; compute from dt
    from .timeutils import utc_to_jd, gmst
    if isinstance(dt, datetime):
        jd = utc_to_jd(dt)
    else:
        jd = float(dt)
    theta = gmst(jd)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    R = np.array([[cos_t, sin_t, 0],
                  [-sin_t, cos_t, 0],
                  [0, 0, 1]])
    if r.ndim == 1:
        return R @ r
    return (R @ r.T).T


def ecef_to_eci(r_ecef, dt):
    """ECEF (m) -> ECI (m)."""
    from .timeutils import utc_to_jd, gmst
    if isinstance(dt, datetime):
        jd = utc_to_jd(dt)
    else:
        jd = float(dt)
    theta = gmst(jd)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    R = np.array([[cos_t, -sin_t, 0],
                  [sin_t, cos_t, 0],
                  [0, 0, 1]])
    r = np.asarray(r_ecef, dtype=float)
    if r.ndim == 1:
        return R @ r
    return (R @ r.T).T


def eci_to_geodetic(r_eci, dt):
    """ECI (m) -> (lat_deg, lon_deg, alt_m) con GMST real."""
    r_ecef = eci_to_ecef(r_eci, dt)
    r = np.asarray(r_ecef, dtype=float)
    single = (r.ndim == 1)
    if single:
        r = r[np.newaxis, :]
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    rr = np.sqrt(x * x + y * y + z * z)
    lat = np.degrees(np.arcsin(np.clip(z / rr, -1, 1)))
    lon = np.degrees(np.arctan2(y, x))
    alt = rr - RE
    if single:
        return float(lat[0]), float(lon[0]), float(alt[0])
    return lat, lon, alt


def geodetic_to_ecef(lat_deg, lon_deg, alt_m):
    """(lat, lon, alt) -> ECEF (m)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r = RE + alt_m
    x = r * math.cos(lat) * math.cos(lon)
    y = r * math.cos(lat) * math.sin(lon)
    z = r * math.sin(lat)
    return np.array([x, y, z])


def ecef_to_geodetic(r_ecef):
    """ECEF (m) -> (lat_deg, lon_deg, alt_m)."""
    r = np.asarray(r_ecef, dtype=float)
    single = (r.ndim == 1)
    if single:
        r = r[np.newaxis, :]
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    rr = np.sqrt(x * x + y * y + z * z)
    lat = np.degrees(np.arcsin(np.clip(z / rr, -1, 1)))
    lon = np.degrees(np.arctan2(y, x))
    alt = rr - RE
    if single:
        return float(lat[0]), float(lon[0]), float(alt[0])
    return lat, lon, alt


def eci_to_heliocentric(r_eci_km, jd):
    """ECI (km) -> heliocéntrico (km) aproximado.

    Para conversiones precisas, usar JPL Horizons o SPICE.
    Esta es una aproximación: suma la posición de la Tierra respecto al Sol.
    """
    # Posición de la Tierra respecto al Sol (aproximación circular)
    # En realidad debería usar Horizons; esto es solo para estimación
    from .timeutils import gmst
    # Earth orbital angle (approx)
    d = jd - 2451545.0
    earth_lon = math.radians(100.464 + 0.985647 * d)  # ecliptic longitude of Earth
    r_earth_sun = np.array([math.cos(earth_lon), math.sin(earth_lon), 0.0]) * 1.496e8  # km
    r = np.asarray(r_eci_km, dtype=float)
    if r.ndim == 1:
        return r + r_earth_sun
    return r + r_earth_sun[np.newaxis, :]