"""Registro de fuentes de datos (sources.json) con sus pros y contras.

    from orbitas_rt.sources import load_sources, by_mission
    for s in by_mission("starship"): print(s["name"], s["status"])

El JSON es la única fuente de verdad; docs/SOURCES.md se genera con
    orbitas-rt sources --markdown docs/SOURCES.md
"""
from __future__ import annotations

import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json")

MISSION_TITLES = {
    "starship": "Vuelo suborbital (Starship)",
    "artemis": "Artemis y misiones lunares",
    "deep_space": "Espacio profundo",
    "leo": "Órbita terrestre baja (LEO)",
}


def load(path: str = PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_sources(path: str = PATH) -> list:
    return load(path)["sources"]


def by_mission(mission: str, path: str = PATH) -> list:
    return [s for s in load_sources(path) if mission in s["missions"]]


def validate(sources: list) -> list:
    """Devuelve una lista de problemas (vacía si todo está bien)."""
    req = ["id", "name", "url", "missions", "measures", "latency", "access",
           "pros", "cons", "use_in_project", "status", "checked"]
    errs, seen = [], set()
    for s in sources:
        for k in req:
            if k not in s:
                errs.append(f"{s.get('id', '?')}: falta el campo '{k}'")
        if s.get("id") in seen:
            errs.append(f"id repetido: {s['id']}")
        seen.add(s.get("id"))
        if s.get("status") == "verificada" and not s.get("checked"):
            errs.append(f"{s['id']}: 'verificada' requiere fecha en 'checked'")
        if not s.get("pros") or not s.get("cons"):
            errs.append(f"{s['id']}: debe tener al menos un pro y un contra")
    return errs


def _bullets(items) -> str:
    return "\n".join(f"- {x}" for x in items)


def to_markdown(data: dict | None = None) -> str:
    data = data or load()
    srcs = data["sources"]
    out = [
        "# Fuentes de datos",
        "",
        f"Actualizado: {data['meta']['updated']}. Este archivo se genera desde "
        "`src/orbitas_rt/sources.json` (`orbitas-rt sources --markdown docs/SOURCES.md`). "
        "Para agregar o corregir una fuente, edita el JSON, no este archivo.",
        "",
        "**Estado de cada fuente**",
        "",
    ]
    for k, v in data["meta"]["legend"].items():
        out.append(f"- `{k}`: {v}.")
    out += ["", "## Resumen", "",
            "| Fuente | Misión | Entrega | Acceso | Estado |",
            "|---|---|---|---|---|"]
    for s in srcs:
        miss = ", ".join(s["missions"])
        est = s["status"] + (f" ({s['checked']})" if s["checked"] else "")
        out.append(f"| [{s['name']}](#{s['id']}) | {miss} | {', '.join(s['measures'][:2])} | "
                   f"{s['access'].split(';')[0]} | {est} |")
    for mission, title in MISSION_TITLES.items():
        group = [s for s in srcs if mission in s["missions"]]
        if not group:
            continue
        out += ["", f"## {title}", ""]
        for s in group:
            out += [f'<a id="{s["id"]}"></a>', f"### {s['name']}", ""]
            if s["url"]:
                out.append(f"- **URL:** {s['url']}")
            out += [
                f"- **Qué entrega:** {', '.join(s['measures'])}",
                f"- **Latencia:** {s['latency']}",
                f"- **Acceso:** {s['access']}",
                f"- **Estado:** {s['status']}" + (f" (revisada el {s['checked']})" if s["checked"] else ""),
                f"- **Uso en el proyecto:** {s['use_in_project']}",
                "",
                "**Pros**", "", _bullets(s["pros"]), "",
                "**Contras**", "", _bullets(s["cons"]), "",
            ]
    out += [
        "## Cómo combinarlas",
        "",
        "Ninguna fuente alcanza sola. Orden sugerido de prioridad según la misión:",
        "",
        "1. **Starship:** overlay del webcast (medición) → trayectoria nominal de FAA/SpaceX "
        "(referencia cuando se corta) → contraste visual/Spaceflight Now.",
        "2. **Artemis / espacio profundo:** estado inicial de Horizons o AROW → propagación de N cuerpos → "
        "mediciones de rango (DSN Now) y Doppler (radioaficionados) cuando existan.",
        "3. **LEO:** TLE de CelesTrak o Space-Track con SGP4.",
        "",
        "Regla general: cada fuente debe entrar al filtro como una **medición con su propio ruido**, "
        "y el sistema debe poder seguir funcionando (solo propagando) si todas fallan.",
        "",
    ]
    return "\n".join(out)
