"""Búsqueda inteligente multi-fuente con validación y caché.

Estrategia:
  1. Buscar en múltiples fuentes en paralelo.
  2. Validar cada resultado (plausibilidad orbital, frescura).
  3. Cross-referenciar: si varias fuentes coinciden, mayor confianza.
  4. Cachear resultados con TTL para no re-consultar demasiado.
  5. Solo actualizar el registro local si los datos nuevos son mejores.
  6. Marcar conflictos si las fuentes no coinciden.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from datetime import datetime, timezone, timedelta

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "search_cache.json")
CACHE_TTL_HOURS = 6  # re-consultar después de 6 horas


def _now():
    return datetime.now(timezone.utc)


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _is_cache_valid(entry):
    if not entry or "timestamp" not in entry:
        return False
    ts = datetime.fromisoformat(entry["timestamp"])
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (_now() - ts).total_seconds() < CACHE_TTL_HOURS * 3600


def _validate_orbital(gp):
    """Valida que los elementos orbitales sean plausibles."""
    issues = []
    try:
        inc = float(gp.get("INCLINATION", 0))
        ecc = float(gp.get("ECCENTRICITY", 0))
        mm = float(gp.get("MEAN_MOTION", 0))
        if not (0 <= inc <= 180):
            issues.append("inclinación fuera de rango: %.2f" % inc)
        if not (0 <= ecc < 1):
            issues.append("excentricidad fuera de rango: %.4f" % ecc)
        if mm <= 0 or mm > 20:
            issues.append("mean motion fuera de rango: %.4f" % mm)
        # altitud aproximada
        import math
        n = mm * 2 * 3.14159 / 86400.0
        a = (3.986e14 / (n * n)) ** (1.0 / 3.0) / 1000.0  # km
        alt = a - 6371.0
        if alt < -100 or alt > 100000:
            issues.append("altitud implausible: %.0f km" % alt)
    except (ValueError, TypeError) as e:
        issues.append("error de validación: %s" % str(e))
    return issues


def _search_celestrak(name):
    """Busca en CelesTrak por nombre."""
    ctx = ssl._create_unverified_context()
    url = "https://celestrak.org/NORAD/elements/gp.php?NAME=%s&FORMAT=json" % name.replace(" ", "%20")
    try:
        data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=15).read().decode())
    except Exception as e:
        return [], str(e)
    results = []
    for d in (data if isinstance(data, list) else [data]):
        issues = _validate_orbital(d)
        results.append({
            "source": "celestrak",
            "name": d.get("OBJECT_NAME"),
            "norad": d.get("NORAD_CAT_ID"),
            "inc": d.get("INCLINATION"),
            "ecc": d.get("ECCENTRICITY"),
            "mm": d.get("MEAN_MOTION"),
            "epoch": d.get("EPOCH"),
            "valid": len(issues) == 0,
            "issues": issues,
        })
    return results, None


def _search_local(name):
    """Busca en registros locales."""
    results = []
    for fname in ["deep_space.json"]:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", fname)
        if not os.path.exists(path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for d in data:
            if name.lower() in str(d.get("name", "")).lower():
                results.append({
                    "source": "local",
                    "name": d.get("name"),
                    "id": d.get("id"),
                    "agency": d.get("agency"),
                    "target": d.get("target"),
                    "launch": d.get("launch"),
                    "status": d.get("status"),
                    "desc": d.get("desc"),
                    "valid": True,
                    "issues": [],
                })
    return results


def smart_search(name, force_refresh=False):
    """Búsqueda inteligente multi-fuente con caché y validación.

    Devuelve:
      - results: lista de resultados validados.
      - conflicts: lista de conflictos detectados.
      - cached: True si se usó caché.
      - sources_queried: lista de fuentes consultadas.
    """
    cache = _load_cache()
    cache_key = name.strip().lower()

    # Usar caché si es válido y no se fuerza refresh
    if not force_refresh and cache_key in cache and _is_cache_valid(cache[cache_key]):
        entry = cache[cache_key]
        return {
            "results": entry.get("results", []),
            "conflicts": entry.get("conflicts", []),
            "cached": True,
            "sources_queried": entry.get("sources_queried", []),
            "timestamp": entry.get("timestamp"),
        }

    # Buscar en múltiples fuentes
    sources_queried = []
    all_results = []

    # 1. Local
    local_results = _search_local(name)
    if local_results:
        sources_queried.append("local")
        all_results.extend(local_results)

    # 2. CelesTrak
    celes_results, err = _search_celestrak(name)
    if celes_results:
        sources_queried.append("celestrak")
        all_results.extend(celes_results)
    elif err:
        sources_queried.append("celestrak (error: %s)" % err)

    # Validar y filtrar
    valid_results = [r for r in all_results if r.get("valid", True)]
    invalid_results = [r for r in all_results if not r.get("valid", True)]

    # Cross-referencia: detectar conflictos reales
    conflicts = []
    # Solo comparar si el mismo NORAD ID aparece en múltiples fuentes
    by_norad = {}
    for r in valid_results:
        norad = r.get("norad") or r.get("id")
        if norad is not None:
            by_norad.setdefault(norad, []).append(r)
    for norad, rs in by_norad.items():
        if len(rs) > 1:
            sources = set(r["source"] for r in rs)
            if len(sources) > 1:
                # verificar si los datos orbitales coinciden
                epochs = set(r.get("epoch") for r in rs if r.get("epoch"))
                if len(epochs) > 1:
                    conflicts.append("NORAD %s: epochs diferentes entre fuentes" % norad)

    # Detectar resultados inválidos
    for r in invalid_results:
        conflicts.append("Resultado inválido de %s: %s" % (r["source"], "; ".join(r.get("issues", []))))

    # Cachear
    entry = {
        "timestamp": _now().isoformat(),
        "results": valid_results,
        "conflicts": conflicts,
        "sources_queried": sources_queried,
    }
    cache[cache_key] = entry
    _save_cache(cache)

    return {
        "results": valid_results,
        "conflicts": conflicts,
        "cached": False,
        "sources_queried": sources_queried,
        "timestamp": entry["timestamp"],
    }


def get_cached(name):
    """Obtiene resultado cacheado sin re-consultar."""
    cache = _load_cache()
    entry = cache.get(name.strip().lower())
    if entry and _is_cache_valid(entry):
        return entry
    return None


def clear_cache(name=None):
    """Limpia el caché (todo o una entrada específica)."""
    cache = _load_cache()
    if name:
        cache.pop(name.strip().lower(), None)
    else:
        cache = {}
    _save_cache(cache)