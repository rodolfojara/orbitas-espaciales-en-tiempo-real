"""Cliente mínimo para JPL Horizons (efemérides vectoriales).

Permite obtener posiciones/velocidades de cuerpos del sistema solar y sondas
espaciales, para visualizar órbitas y trayectorias (LEO, translunar, interplanetario).

Uso:
    from orbitas_rt.horizons import fetch_vectors
    t, r, v = fetch_vectors("-9", "2026-11-14", "2027-09-01", step="5 d",
                            center="@sun", frame="ECLIPTIC")
"""
from __future__ import annotations

import re
import ssl
import urllib.request
from datetime import datetime

import numpy as np


HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def _ctx():
    ctx = ssl._create_unverified_context()
    return ctx


def fetch_vectors(command, start, stop, step="1 d", center="@sun",
                  frame="ECLIPTIC", units="AU-D"):
    """Devuelve (t_jd, r (N,3) AU, v (N,3) AU/d) para el cuerpo `command`.

    command: id Horizons (ej. "-9" ESCAPADE-Blue, "399" Tierra, "499" Marte, "10" Sol).
    start/stop: 'YYYY-MM-DD'.
    """
    step_enc = step.replace(" ", "%20")
    q = (
        f"COMMAND={command}&EPHEM_TYPE=VECTORS"
        f"&START_TIME=%22{start}%22&STOP_TIME=%22{stop}%22&STEP_SIZE=%22{step_enc}%22"
        f"&CENTER=%22{center}%22&REF_PLANE={frame}&OUT_UNITS={units}&format=json"
    )
    url = HORIZONS_URL + "?" + q
    with urllib.request.urlopen(url, context=_ctx(), timeout=60) as resp:
        data = resp.read().decode("utf-8", errors="replace")
    # Horizons devuelve JSON con campo "result" (texto). Extraemos bloques.
    import json
    try:
        obj = json.loads(data)
        text = obj.get("result", data)
    except Exception:
        text = data

    soe = text.find("$$SOE")
    eoe = text.find("$$EOE")
    if soe < 0 or eoe < 0:
        raise RuntimeError("Horizons no devolvió datos vectoriales:\n" + text[:1000])
    block = text[soe:eoe]

    # Parseo: cada entrada empieza con "JD = ..." o línea con fecha.
    # Formato estándar: línea "JD = ... = A.D. ..." luego " X = ... Y = ... Z = ..."
    # y " VX= ... VY= ... VZ= ..."
    t_list, r_list, v_list = [], [], []
    lines = block.splitlines()
    i = 0
    current_t = None
    while i < len(lines):
        line = lines[i].strip()
        m = re.search(r"(\d+\.\d+)\s*=\s*A\.D\.", line)
        if m:
            current_t = float(m.group(1))
            i += 1
            continue
        m = re.search(r"X\s*=\s*([+-]?\d\.\d+E[+-]?\d+)\s+Y\s*=\s*([+-]?\d\.\d+E[+-]?\d+)\s+Z\s*=\s*([+-]?\d\.\d+E[+-]?\d+)", line)
        if m and current_t is not None:
            r = [float(m.group(1)), float(m.group(2)), float(m.group(3))]
            # siguiente línea contiene VX, VY, VZ
            if i + 1 < len(lines):
                m2 = re.search(r"VX\s*=\s*([+-]?\d\.\d+E[+-]?\d+)\s+VY\s*=\s*([+-]?\d\.\d+E[+-]?\d+)\s+VZ\s*=\s*([+-]?\d\.\d+E[+-]?\d+)", lines[i + 1])
                if m2:
                    v = [float(m2.group(1)), float(m2.group(2)), float(m2.group(3))]
                    t_list.append(current_t)
                    r_list.append(r)
                    v_list.append(v)
            i += 2
            continue
        i += 1

    if not t_list:
        raise RuntimeError("No se pudieron parsear vectores de Horizons.")
    t = np.array(t_list)
    r = np.array(r_list)
    v = np.array(v_list)
    # convertir JD a fecha legible
    return t, r, v


def jd_to_date(jd):
    # conversión aproximada JD -> datetime (UTC/TDB, suficiente para etiquetas)
    # usando algoritmo estándar
    jd = jd + 0.5
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
    day = B - D - int(30.6001 * E) + F
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
    # fracción de día -> hora
    frac = day - int(day)
    day_i = int(day)
    hour = int(frac * 24)
    minute = int((frac * 24 - hour) * 60)
    try:
        return datetime(year, month, day_i, hour, minute)
    except ValueError:
        return None
