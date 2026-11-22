"""Búsqueda multi-fuente de naves espaciales.

Estrategia de búsqueda (en orden):
  1. Registro local (deep_space.json, lunar, etc.) — instantáneo.
  2. JPL Horizons (efemérides) — si está disponible.
  3. CelesTrak (TLE/GP) — para satélites en órbita terrestre.
  4. Búsqueda por nombre en CelesTrak (si no se encuentra por ID).

Devuelve información básica + efemérides si están disponibles.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from datetime import datetime

REGISTRY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load_json(name):
    path = os.path.join(REGISTRY_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def search_local(name_or_id):
    """Busca en los registros locales (deep_space, etc.)."""
    results = []
    # deep_space
    for s in _load_json("deep_space.json"):
        if (str(name_or_id).lower() in str(s.get("name", "")).lower() or
            str(name_or_id) == str(s.get("id", ""))):
            results.append({"source": "local", "name": s["name"], "id": s["id"],
                           "agency": s.get("agency"), "target": s.get("target"),
                           "launch": s.get("launch"), "status": s.get("status"),
                           "desc": s.get("desc"), "type": "deep_space"})
    return results


def search_horizons(name_or_id):
    """Busca en JPL Horizons."""
    ctx = ssl._create_unverified_context()
    url = "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND=%s" % urllib.parse.quote(str(name_or_id)) if False else str(name_or_id)
    # Horizons search
    try:
        if str(name_or_id).lstrip("-").isdigit():
            url = "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND=%27%s%27" % name_or_id
        else:
            url = "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND=%22%s%22" % name_or_id
        r = urllib.request.urlopen(url, context=ctx, timeout=20).read().decode()
        import re
        # Check if it found a spacecraft
        if "spacecraft" in r.lower() or "Matching" in r:
            # Extract name
            for line in r.splitlines():
                if "spacecraft" in line.lower():
                    return [{"source": "horizons", "name": line.strip(), "id": name_or_id,
                             "type": "horizons", "raw": r[:500]}]
    except Exception:
        pass
    return []


def search_celestrak(name_or_id):
    """Busca en CelesTrak (TLE/GP)."""
    ctx = ssl._create_unverified_context()
    # Try by name
    if not str(name_or_id).lstrip("-").isdigit() or int(name_or_id) > 0:
        url = "https://celestrak.org/NORAD/elements/gp.php?NAME=%s&FORMAT=json" % urllib.parse.quote(str(name_or_id))
    else:
        url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%s&FORMAT=json" % name_or_id
    try:
        data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=20).read().decode())
        results = []
        for d in (data if isinstance(data, list) else [data]):
            results.append({"source": "celestrak", "name": d.get("OBJECT_NAME"),
                           "id": d.get("NORAD_CAT_ID"), "type": "leo",
                           "inc": d.get("INCLINATION"), "epoch": d.get("EPOCH"),
                           "norad": d.get("NORAD_CAT_ID")})
        return results
    except Exception:
        return []


def lookup(name_or_id):
    """Búsqueda multi-fuente. Devuelve lista de resultados combinados."""
    results = []
    # 1. Local
    results.extend(search_local(name_or_id))
    # 2. CelesTrak (por nombre o NORAD)
    results.extend(search_celestrak(name_or_id))
    # 3. Horizons (si es un ID negativo o nombre conocido)
    if str(name_or_id).lstrip("-").isdigit() and int(name_or_id) < 0:
        results.extend(search_horizons(name_or_id))
    return results


# Need urllib.parse
import urllib.parse