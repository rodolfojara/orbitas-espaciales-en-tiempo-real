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
        # Verificar frescura del TLE (epoch dentro de los últimos 30 días)
        try:
            epoch = datetime.fromisoformat(d.get("EPOCH", "").replace("Z", "+00:00"))
            if epoch.tzinfo is None:
                epoch = epoch.replace(tzinfo=timezone.utc)
            age_days = (_now() - epoch).total_seconds() / 86400.0
            if age_days > 30:
                issues.append("TLE antiguo: %.0f días" % age_days)
        except Exception:
            pass
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


# KeepTrack API: requiere registro (https://keeptrack.space). Documentado como fuente futura.
# Cuando se obtenga una API key, implementar _search_keeptrack() aquí.


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

    # 2. CelesTrak (fuente principal de TLE/GP)
    celes_results, err = _search_celestrak(name)
    if celes_results:
        sources_queried.append("celestrak")
        all_results.extend(celes_results)
    elif err:
        sources_queried.append("celestrak (error: %s)" % err)

    # 3. Space-Track.org (catálogo oficial, requiere cuenta gratuita)
    from .spacetrack import is_configured, search_by_name, search_by_norad
    if is_configured():
        if name.strip().lstrip("-").isdigit():
            st_results, err = search_by_norad(int(name.strip()))
        else:
            st_results, err = search_by_name(name.strip())
        if st_results:
            sources_queried.append("spacetrack")
            # Validar resultados de Space-Track
            for r in st_results:
                issues = _validate_orbital({"INCLINATION": r.get("inc"), "ECCENTRICITY": r.get("ecc"),
                                            "MEAN_MOTION": r.get("mm")})
                # Verificar frescura
                if r.get("epoch"):
                    try:
                        epoch = datetime.fromisoformat(r["epoch"].replace("Z", "+00:00"))
                        if epoch.tzinfo is None:
                            epoch = epoch.replace(tzinfo=timezone.utc)
                        age_days = (_now() - epoch).total_seconds() / 86400.0
                        if age_days > 30:
                            issues.append("TLE antiguo: %.0f días" % age_days)
                    except Exception:
                        pass
                r["valid"] = len(issues) == 0
                r["issues"] = issues
            all_results.extend(st_results)
        elif err:
            sources_queried.append("spacetrack (error: %s)" % err)
    else:
        sources_queried.append("spacetrack (no configurado - ver docs)")

    # Validar y filtrar
    valid_results = [r for r in all_results if r.get("valid", True)]
    invalid_results = [r for r in all_results if not r.get("valid", True)]

    # Cross-referencia: detectar conflictos reales
    conflicts = []
    by_norad = {}
    for r in valid_results:
        norad = r.get("norad") or r.get("id")
        if norad is not None:
            by_norad.setdefault(norad, []).append(r)
    for norad, rs in by_norad.items():
        if len(rs) > 1:
            sources = set(r["source"] for r in rs)
            if len(sources) > 1:
                incs = [r.get("inc") for r in rs if r.get("inc") is not None]
                if len(incs) > 1:
                    if max(incs) - min(incs) > 0.5:
                        conflicts.append("NORAD %s: inclinación difiere entre fuentes (%.2f vs %.2f)" % (norad, min(incs), max(incs)))

    # Cross-referencia con registro local: validar consistencia
    local_results = [r for r in valid_results if r["source"] == "local"]
    celes_results = [r for r in valid_results if r["source"] == "celestrak"]
    for lr in local_results:
        # buscar en CelesTrak por nombre similar
        for cr in celes_results:
            if lr.get("name", "").lower() in str(cr.get("name", "")).lower() or \
               str(cr.get("name", "")).lower() in lr.get("name", "").lower():
                # verificar si la inclinación es consistente
                if lr.get("inc") is not None and cr.get("inc") is not None:
                    if abs(float(lr["inc"]) - float(cr["inc"])) > 1.0:
                        conflicts.append("Posible inconsistencia para %s: inc local=%.2f vs celestrak=%.2f" % (
                            lr["name"], float(lr["inc"]), float(cr["inc"])))

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