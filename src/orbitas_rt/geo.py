"""Conversión de distancia recorrida (downrange) a latitud/longitud.

Se asume un círculo máximo (gran círculo) desde el sitio de lanzamiento con un
azimut inicial fijo. Es una aproximación: sin rotación terrestre ni curvatura
lateral de la trayectoria real.
"""
from __future__ import annotations

import numpy as np

from .dynamics import RE

# Valores de ejemplo (Starbase, Texas). Cámbialos para otra misión.
STARBASE = (25.9970, -97.1570)
DEFAULT_AZIMUTH_DEG = 96.0


def destination(lat0_deg: float, lon0_deg: float, azimuth_deg: float, distance_m):
    lat0, lon0, az = np.radians([lat0_deg, lon0_deg, azimuth_deg])
    d = np.asarray(distance_m, dtype=float) / RE
    lat = np.arcsin(np.sin(lat0) * np.cos(d) + np.cos(lat0) * np.sin(d) * np.cos(az))
    lon = lon0 + np.arctan2(
        np.sin(az) * np.sin(d) * np.cos(lat0),
        np.cos(d) - np.sin(lat0) * np.sin(lat),
    )
    lon = (lon + np.pi) % (2 * np.pi) - np.pi
    return np.degrees(lat), np.degrees(lon)
