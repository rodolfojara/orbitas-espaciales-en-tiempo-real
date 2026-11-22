"""Utilidades de tiempo para mecánica orbital.

Centraliza conversiones entre sistemas de tiempo:
  UTC, TDB (Barycentric Dynamical Time), JD (Julian Date),
  MJD (Modified Julian Date), GMST (Greenwich Mean Sidereal Time).

Usa aproximaciones estándar (suficientes para visualización y estimación).
Para misiones de alta precisión, usar SPICE kernels.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

import numpy as np

# Constantes
J2000 = 2451545.0  # JD del 2000-01-01 12:00 TT
OMEGA_EARTH = 7.2921159e-5  # rad/s (rotación terrestre)
RE = 6371000.0  # m (radio terrestre)


def utc_to_jd(dt: datetime) -> float:
    """Convierte datetime UTC a Julian Date."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Algoritmo estándar
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0 +
                  dt.microsecond / 1e6 / 3600.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return jd


def jd_to_utc(jd: float) -> datetime:
    """Convierte Julian Date a datetime UTC (aproximado)."""
    jd += 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E)
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
    # fracción de día
    frac = F
    hour = int(frac * 24)
    minute = int((frac * 24 - hour) * 60)
    second = int(((frac * 24 - hour) * 60 - minute) * 60)
    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    except ValueError:
        return datetime(year, month, max(1, day), tzinfo=timezone.utc)


def utc_to_mjd(dt: datetime) -> float:
    """Modified Julian Date."""
    return utc_to_jd(dt) - 2400000.5


def mjd_to_utc(mjd: float) -> datetime:
    return jd_to_utc(mjd + 2400000.5)


def utc_to_tdb(dt: datetime) -> float:
    """Aproximación TDB - UTC (segundos). TDB ≈ TT - 32.184s."""
    # TDB-UTC ≈ TT-UTC + (TDB-TT). TT-UTC = 32.184 + (leap seconds).
    # Aproximación simple: ignorar leap seconds y variación TDB-TT (< 2 ms).
    return utc_to_jd(dt)  # devuelve JD en TDB (aprox)


def gmst(jd: float) -> float:
    """Greenwich Mean Sidereal Time (radianes) para un JD (IAU 2006 simplificado).

    Usa la fórmula de la IAU 2006 (aproximación de primer orden).
    """
    # Días desde J2000
    d = jd - J2000
    # GMST en grados (fórmula de la IAU 2006)
    gmst_deg = (280.46061837 + 360.98564736629 * d +
                0.000387933 * d * d / 3600.0)
    gmst_deg = gmst_deg % 360.0
    return math.radians(gmst_deg)


def gmst_from_dt(dt: datetime) -> float:
    """GMST (rad) para un datetime UTC."""
    return gmst(utc_to_jd(dt))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def jd_now() -> float:
    return utc_to_jd(now_utc())