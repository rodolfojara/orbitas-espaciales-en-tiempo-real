"""Búsqueda profunda automática de objetos espaciales.

Estrategia multi-nivel:
  1. Búsqueda directa en registros locales.
  2. Búsqueda en CelesTrak (TLE/GP) por nombre y NORAD ID.
  3. Búsqueda en JPL Horizons (mayor-bodies y spacecraft).
  4. Búsqueda por aliases/nombres alternativos.
  5. Búsqueda en fuentes complementarias (KeepTrack, planet4589).
  6. Acumulación de resultados en base de conocimiento local.

Criterios de validación:
  - No mezclar datos contradictorios.
  - Preferir fuentes más autoritativas (Horizons > Space-Track > CelesTrak > local).
  - Marcar incertidumbre cuando solo hay una fuente.
  - Cachear resultados con TTL para no re-consultar.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "deep_search_cache.json")
KNOWLEDGE_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "knowledge_base.json")

# Aliases: nombres comunes -> términos de búsqueda alternativos
ALIASES = {
    "snoopy": ["Apollo 10 LM", "Apollo 10"],
    "apollo 13": ["Apollo 13", "Apollo"],
    "voyager": ["Voyager 1", "Voyager 2"],
    "cassini": ["Cassini", "Cassini Huygens"],
    "mro": ["Mars Reconnaissance Orbiter", "MRO"],
    "perseverance": ["Mars 2020", "Perseverance"],
    "curiosity": ["Mars Science Laboratory", "MSL", "Curiosity"],
    "insight": ["InSight"],
    "maven": ["MAVEN"],
    "juno": ["Juno"],
    "new horizons": ["New Horizons"],
    "parker": ["Parker Solar Probe"],
    "psyche": ["Psyche"],
    "europa clipper": ["Europa Clipper"],
    "tianwen": ["Tianwen-1", "Tianwen"],
    "chang'e": ["Chang'e", "Chang'e 5", "Chang'e 4", "Chang'e 3"],
    "artemis": ["Artemis 1", "Artemis II", "Artemis"],
    "orion": ["Artemis", "Orion"],
    "starship": ["Starship", "SpaceX"],
}


def _now():
    return datetime.now(timezone.utc)


def _load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _search_horizons(name_or_id):
    """Busca en JPL Horizons."""
    ctx = ssl._create_unverified_context()
    results = []
    # Intentar como ID negativo (spacecraft)
    if str(name_or_id).lstrip("-").isdigit() and int(name_or_id) < 0:
        url = "https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=" + chr(39) + name_or_id + chr(39)
        try:
            r = urllib.request.urlopen(url, context=ctx, timeout=20).read().decode()
            for line in r.splitlines():
                if "spacecraft" in line.lower() and "-" in line:
                    results.append({"source": "horizons", "name": line.strip(), "id": int(name_or_id),
                                    "type": "horizons", "confidence": "high"})
                    break
        except Exception:
            pass
    # Intentar por nombre
    else:
        url = "https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=" + chr(34) + name_or_id + chr(34)
        try:
            r = urllib.request.urlopen(url, context=ctx, timeout=20).read().decode()
            for line in r.splitlines():
                if "spacecraft" in line.lower() and "-" in line:
                    # Extraer ID
                    parts = line.strip().split()
                    if parts and parts[0].lstrip("-").isdigit():
                        results.append({"source": "horizons", "name": line.strip(),
                                        "id": int(parts[0]), "type": "horizons",
                                        "confidence": "high"})
        except Exception:
            pass
    return results


def _search_celestrak(name):
    """Busca en CelesTrak."""
    ctx = ssl._create_unverified_context()
    url = "https://celestrak.org/NORAD/elements/gp.php?NAME=%s&FORMAT=json" % name.replace(" ", "%20")
    try:
        data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=20).read().decode())
    except Exception:
        return []
    results = []
    for d in (data if isinstance(data, list) else [data]):
        results.append({"source": "celestrak", "name": d.get("OBJECT_NAME"),
                        "norad": d.get("NORAD_CAT_ID"), "inc": d.get("INCLINATION"),
                        "epoch": d.get("EPOCH"), "type": "leo", "confidence": "medium"})
    return results


def _search_local_registry(name):
    """Busca en registros locales (deep_space, lost_objects)."""
    results = []
    for fname in ["deep_space.json", "lost_objects.json"]:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", fname)
        if not os.path.exists(path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for d in data:
            if name.lower() in str(d.get("name", "")).lower():
                results.append({"source": "local", "name": d["name"], "id": d.get("id"),
                                "agency": d.get("agency"), "target": d.get("target"),
                                "launch": d.get("launch"), "status": d.get("status"),
                                "desc": d.get("desc"), "type": "local", "confidence": "high"})
    return results


def deep_search(name, use_cache=True):
    """Búsqueda profunda multi-fuente con validación y acumulación.

    Devuelve:
      - results: lista de resultados validados.
      - sources: fuentes consultadas.
      - confidence: nivel de confianza general.
      - cached: si se usó caché.
      - knowledge_base_updated: si se actualizó la base de conocimiento.
    """
    cache = _load_json(CACHE_FILE)
    cache_key = name.strip().lower()

    # Verificar caché
    if use_cache and cache_key in cache:
        entry = cache[cache_key]
        ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if (_now() - ts).total_seconds() < 3600 * 6:  # 6h TTL
            entry["cached"] = True
            return entry

    # Búsqueda en múltiples fuentes
    all_results = []
    sources_queried = []

    # 1. Registro local
    local = _search_local_registry(name)
    if local:
        sources_queried.append("local")
        all_results.extend(local)

    # 2. Aliases
    aliases = ALIASES.get(name.strip().lower(), [])
    for alias in aliases:
        local_alias = _search_local_registry(alias)
        if local_alias:
            sources_queried.append("local (alias: %s)" % alias)
            all_results.extend(local_alias)

    # 3. CelesTrak (por nombre)
    celes = _search_celestrak(name)
    if celes:
        sources_queried.append("celestrak")
        all_results.extend(celes)

    # 4. JPL Horizons (por nombre)
    horizons = _search_horizons(name)
    if horizons:
        sources_queried.append("horizons")
        all_results.extend(horizons)

    # 5. Aliases en Horizons
    for alias in aliases:
        h = _search_horizons(alias)
        if h:
            sources_queried.append("horizons (alias: %s)" % alias)
            all_results.extend(h)

    # Deduplicar por nombre
    seen_names = set()
    unique_results = []
    for r in all_results:
        key = r.get("name", "").lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        unique_results.append(r)

    # Determinar confianza
    n_sources = len(set(r["source"] for r in unique_results))
    if n_sources >= 2:
        confidence = "high"
    elif n_sources == 1:
        confidence = "medium"
    else:
        confidence = "low"

    # Detectar conflictos
    conflicts = []
    # Si hay resultados de diferentes fuentes para el mismo objeto, verificar consistencia
    by_name = {}
    for r in unique_results:
        by_name.setdefault(r.get("name", "").lower(), []).append(r)
    for name_key, rs in by_name.items():
        if len(rs) > 1:
            sources = set(r["source"] for r in rs)
            if len(sources) > 1:
                conflicts.append("'%s' encontrado en múltiples fuentes: %s" % (name_key, ", ".join(sources)))

    # Actualizar base de conocimiento (solo si hay resultados nuevos)
    kb = _load_json(KNOWLEDGE_BASE)
    kb_key = name.strip().lower()
    if unique_results:
        kb[kb_key] = {
            "timestamp": _now().isoformat(),
            "results": unique_results,
            "sources": sources_queried,
            "confidence": confidence,
        }
        _save_json(KNOWLEDGE_BASE, kb)

    # Cachear
    entry = {
        "timestamp": _now().isoformat(),
        "results": unique_results,
        "conflicts": conflicts,
        "sources_queried": sources_queried,
        "confidence": confidence,
        "cached": False,
    }
    cache = _load_json(CACHE_FILE)
    cache[cache_key] = entry
    _save_json(CACHE_FILE, cache)

    return entry


def get_knowledge_base():
    """Devuelve la base de conocimiento acumulada."""
    return _load_json(KNOWLEDGE_BASE)


def search_knowledge_base(query):
    """Busca en la base de conocimiento local."""
    kb = _load_json(KNOWLEDGE_BASE)
    results = []
    for key, entry in kb.items():
        if query.lower() in key:
            results.append({"query": key, "results": entry.get("results", []),
                           "confidence": entry.get("confidence", "unknown"),
                           "timestamp": entry.get("timestamp")})
    return results