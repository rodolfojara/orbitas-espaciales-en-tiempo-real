"""Utilidades para trabajar con TLE (Two-Line Element sets).

Permite obtener el estado inicial (ECI) de un satélite a partir de un TLE,
usando SGP4, para alimentar el EKF u otras estimaciones.
"""
from __future__ import annotations

import ssl
import urllib.request
from datetime import datetime, timezone

import numpy as np
from sgp4.api import Satrec, jday
from sgp4 import omm

RE = 6371000.0  # m


def fetch_gp(catnr):
    """Obtiene el GP (OMM) JSON de CelesTrak para un NORAD_CAT_ID."""
    ctx = ssl._create_unverified_context()
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%d&FORMAT=json" % catnr
    import json
    data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=30).read().decode())
    return data[0]


def gp_to_satrec(gp):
    sat = Satrec()
    omm.initialize(sat, gp)
    return sat


def state_at(sat, dt_utc=None):
    """Devuelve (r_eci_m, v_eci_m_s) en ECI para el instante dt_utc (UTC).

    Si dt_utc es None, usa el tiempo actual (UTC).
    """
    if dt_utc is None:
        dt_utc = datetime.now(timezone.utc)
    jd, fr = jday(dt_utc.year, dt_utc.month, dt_utc.day,
                   dt_utc.hour, dt_utc.minute,
                   dt_utc.second + dt_utc.microsecond / 1e6)
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        raise RuntimeError("SGP4 error code %d" % e)
    return np.array(r) * 1000.0, np.array(v) * 1000.0  # km->m, km/s->m/s (sgp4 v is km/s)


def gp_to_initial_state(gp, t0=None):
    """Convierte un GP en estado EKF-compatible.

    Devuelve (t0_utc, x0 [x,y,z,vx,vy,vz] en ECI m/m/s, sat).
    El EKF del proyecto es 2D; aquí devolvemos estado 3D para uso futuro.
    """
    sat = gp_to_satrec(gp)
    if t0 is None:
        t0 = datetime.fromisoformat(gp["EPOCH"].replace("Z", "+00:00"))
    r, v = state_at(sat, t0)
    return t0, np.concatenate([r, v]), sat