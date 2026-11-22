"""Cliente para Space-Track.org (catálogo oficial del DoD de EE.UU.).

Requiere cuenta gratuita en https://www.space-track.org/
Credenciales por variables de entorno:
  SPACETRACK_USER  (email de la cuenta)
  SPACETRACK_PASS  (contraseña)

Si no están configuradas, el módulo se desactiva silenciosamente.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

SPACETRACK_BASE = "https://www.space-track.org"
LOGIN_URL = SPACETRACK_BASE + "/ajaxauth/login"
QUERY_URL = SPACETRACK_BASE + "/basicspacedata/query"


def is_configured():
    """Verifica si las credenciales de Space-Track están configuradas."""
    return bool(os.environ.get("SPACETRACK_USER") and os.environ.get("SPACETRACK_PASS"))


def _login():
    """Autentica en Space-Track y devuelve un opener con cookies."""
    user = os.environ.get("SPACETRACK_USER")
    passw = os.environ.get("SPACETRACK_PASS")
    if not user or not passw:
        return None
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    data = urllib.parse.urlencode({"identity": user, "password": passw}).encode()
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(LOGIN_URL, data=data)
        opener.open(req, context=ctx, timeout=30)
    except Exception:
        return None
    return opener


def query_gp(norad_cat_id=None, name=None, limit=10):
    """Consulta GP (General Perturbations) data de Space-Track.

    Devuelve lista de dicts con los mismos campos que CelesTrak GP.
    """
    opener = _login()
    if opener is None:
        return [], "Credenciales no configuradas (SPACETRACK_USER/PASS)"

    ctx = ssl._create_unverified_context()
    # Construir query
    parts = ["class/gp"]
    if norad_cat_id is not None:
        parts.append("NORAD_CAT_ID/%d" % norad_cat_id)
    if name:
        parts.append("OBJECT_NAME/~~%s" % name)
    parts.append("orderby/EPOCH desc")
    parts.append("limit/%d" % limit)
    parts.append("format/json")

    url = QUERY_URL + "/" + "/".join(parts)
    try:
        req = urllib.request.Request(url)
        resp = opener.open(req, context=ctx, timeout=30)
        data = json.loads(resp.read().decode())
    except Exception as e:
        return [], str(e)

    # Normalizar a formato CelesTrak-compatible
    results = []
    for d in (data if isinstance(data, list) else [data]):
        results.append({
            "source": "spacetrack",
            "name": d.get("OBJECT_NAME"),
            "norad": d.get("NORAD_CAT_ID"),
            "inc": d.get("INCLINATION"),
            "ecc": d.get("ECCENTRICITY"),
            "mm": d.get("MEAN_MOTION"),
            "epoch": d.get("EPOCH"),
            "country": d.get("COUNTRY_CODE"),
            "launch": d.get("LAUNCH_DATE"),
            "rcs_size": d.get("RCS_SIZE"),
            "object_type": d.get("OBJECT_TYPE"),
            "valid": True,
            "issues": [],
        })
    return results, None


def search_by_name(name, limit=10):
    """Busca satélites por nombre en Space-Track."""
    return query_gp(name=name, limit=limit)


def search_by_norad(norad, limit=5):
    """Busca un satélite por NORAD_CAT_ID en Space-Track."""
    return query_gp(norad_cat_id=norad, limit=limit)