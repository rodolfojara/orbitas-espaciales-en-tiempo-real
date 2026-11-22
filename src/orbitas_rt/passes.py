"""Predicción de pases de satélites sobre estaciones de tierra.

Calcula AOS (Acquisition of Signal), LOS (Loss of Signal),
elevación, azimut y footprint para una estación dada.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np

from .frames import eci_to_geodetic, geodetic_to_ecef
from .timeutils import utc_to_jd, gmst


def _elevation_azimuth(r_sat_eci, station_lat, station_lon, station_alt, t):
    """Calcula elevación y azimut del satélite visto desde la estación."""
    # Posición de la estación en ECEF
    st_ecef = geodetic_to_ecef(station_lat, station_lon, station_alt)
    # Satélite ECI -> ECEF
    from .frames import eci_to_ecef
    sat_ecef = eci_to_ecef(r_sat_eci, t)
    # Vector de la estación al satélite
    diff = sat_ecef - st_ecef
    # Rotar a ENU (East-North-Up)
    lat_r = math.radians(station_lat)
    lon_r = math.radians(station_lon)
    R = np.array([
        [-math.sin(lon_r), math.cos(lon_r), 0],
        [-math.sin(lat_r) * math.cos(lon_r), -math.sin(lat_r) * math.sin(lon_r), math.cos(lat_r)],
        [math.cos(lat_r) * math.cos(lon_r), math.cos(lat_r) * math.sin(lon_r), math.sin(lat_r)],
    ])
    enu = R @ diff
    e, n, u = enu
    # Elevación
    horiz = math.sqrt(e * e + n * n)
    el = math.degrees(math.atan2(u, horiz))
    # Azimut
    az = math.degrees(math.atan2(e, n)) % 360
    # Rango
    rng = math.sqrt(e * e + n * n + u * u)
    return el, az, rng


def predict_passes(sat_func, station_lat, station_lon, station_alt,
                   start, end, step_s=10.0, min_el=0.0):
    """Predice pases de un satélite sobre una estación.

    sat_func: función(t_utc) -> r_eci (m) (posición ECI del satélite).
    Devuelve lista de dicts con AOS, LOS, max_elevation, duration.
    """
    t = start
    passes = []
    in_pass = False
    aos_time = None
    max_el = 0.0
    max_el_time = None

    while t <= end:
        r_sat = sat_func(t)
        el, az, rng = _elevation_azimuth(r_sat, station_lat, station_lon, station_alt, t)
        if el >= min_el:
            if not in_pass:
                in_pass = True
                aos_time = t
                max_el = el
                max_el_time = t
            else:
                if el > max_el:
                    max_el = el
                    max_el_time = t
        else:
            if in_pass:
                in_pass = False
                passes.append({
                    "aos": aos_time,
                    "los": t,
                    "max_elevation": max_el,
                    "max_el_time": max_el_time,
                    "duration_s": (t - aos_time).total_seconds(),
                })
        t += timedelta(seconds=step_s)

    # Si el pase sigue al final
    if in_pass:
        passes.append({
            "aos": aos_time,
            "los": end,
            "max_elevation": max_el,
            "max_el_time": max_el_time,
            "duration_s": (end - aos_time).total_seconds(),
        })

    return passes


def footprint_radius(altitude_km):
    """Radio del footprint (km) para una altitud dada (línea de vista)."""
    R = 6371.0
    # cos(central_angle) = R / (R + h)
    import math
    cos_angle = R / (R + altitude_km)
    angle = math.acos(cos_angle)
    return R * angle  # km en la superficie


def is_visible(sat_func, station_lat, station_lon, station_alt, t, min_el=0.0):
    """¿Es visible el satélite desde la estación en el tiempo t?"""
    r_sat = sat_func(t)
    el, az, rng = _elevation_azimuth(r_sat, station_lat, station_lon, station_alt, t)
    return el >= min_el, el, az, rng