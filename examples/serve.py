"""Servidor local con API de consulta orbital.

Uso:
  python examples/serve.py
  Abrir http://localhost:8000/query.html

Endpoints:
  /api/query?norad=25544&norbits=3&step=1&start=2026-11-16T00:00
      -> JSON con la trayectoria proyectada (lat/lon) y metadatos.
"""
import os
import sys
import json
import ssl
import urllib.request
import urllib.parse

STATIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "orbitas_rt", "data", "tracking_stations.json")
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta

# Aliases: nombres comunes -> términos de búsqueda en CelesTrak
NAME_ALIASES = {
    "ssot": "SSOT",
    "suchai": "SUCHAI",
    "fasat": "FASAT",
    "fasat charlie": "SSOT",
    "fasat c": "SSOT",
    "fasat bravo": "FASAT B",
    "fasat b": "FASAT B",
    "fasat alpha": "FASAT",
    "fasat delta": "FASAT",
    "lemu": "LEMU NGE",
    "iss": "ISS",
    "zarya": "ISS",
    "starlink": "STARLINK",
    "starship": "STARSHIP",
}

# Grupos curados: nombre de grupo -> lista de NORAD_CAT_ID
CURATED_GROUPS = {
    "chile": [69911, 25395, 38011, 60532, 52192, 52191, 52188, 42788],
    "argentina": [37673, 40272, 40941, 39153, 39440, 20442],
    "brasil": [40336, 44883, 47699],
}

# Grupos por búsqueda de texto: nombre de grupo -> lista de términos de búsqueda
GROUPS = {
    "fasat": ["FASAT"],
    "suchai": ["SUCHAI"],
    "starlink": ["STARLINK"],
    "iss": ["ISS"],
    "starship": ["STARSHIP"],
    "lemu": ["LEMU NGE"],
    "ssot": ["SSOT"],
    "galileo": ["GALILEO"],
    "sentinel": ["SENTINEL"],
    "tiangong": ["TIANGONG"],
    "beidou": ["BEIDOU"],
    "gps": ["GPS"],
    "glonass": ["GLONASS"],
    "goes": ["GOES"],
    "europa": ["GALILEO", "SENTINEL", "ENVISAT"],
    "china": ["CSS", "BEIDOU", "GAOFEN"],
    "rusia": ["GLONASS", "SOYUZ", "PROGRESS"],
    "usa": ["GPS", "GOES", "STARLINK"],
}

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sgp4.api import Satrec, jday
from sgp4 import omm
from orbitas_rt.tle import fetch_gp
from orbitas_rt.horizons import fetch_vectors

ROOT = os.path.join(os.path.dirname(__file__), "output")
PORT = 8000


def fetch_gp_by_norad(norad):
    ctx = ssl._create_unverified_context()
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%d&FORMAT=json" % norad
    try:
        data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=20).read().decode())
        return data[0] if data else None
    except Exception:
        return None


def search_satellites(name):
    ctx = ssl._create_unverified_context()
    key = name.strip().lower()
    results = []
    seen = set()
    is_group = False
    terms = []

    if key in CURATED_GROUPS:
        is_group = True
        terms = ["curated: %s" % key]
        for norad in CURATED_GROUPS[key]:
            d = fetch_gp_by_norad(norad)
            if d and d.get("NORAD_CAT_ID") not in seen:
                seen.add(d.get("NORAD_CAT_ID"))
                results.append({
                    "name": d.get("OBJECT_NAME"),
                    "norad": d.get("NORAD_CAT_ID"),
                    "inc": d.get("INCLINATION"),
                    "epoch": d.get("EPOCH"),
                })
    elif key in GROUPS:
        is_group = True
        terms = GROUPS[key]
        for term in terms:
            url = "https://celestrak.org/NORAD/elements/gp.php?NAME=%s&FORMAT=json" % urllib.parse.quote(term)
            try:
                data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=20).read().decode())
            except Exception:
                continue
            for d in data:
                norad = d.get("NORAD_CAT_ID")
                if norad in seen:
                    continue
                seen.add(norad)
                results.append({
                    "name": d.get("OBJECT_NAME"),
                    "norad": norad,
                    "inc": d.get("INCLINATION"),
                    "epoch": d.get("EPOCH"),
                })
    else:
        term = NAME_ALIASES.get(key, name.strip())
        terms = [term]
        url = "https://celestrak.org/NORAD/elements/gp.php?NAME=%s&FORMAT=json" % urllib.parse.quote(term)
        try:
            data = json.loads(urllib.request.urlopen(url, context=ctx, timeout=20).read().decode())
        except Exception as e:
            return {"error": str(e), "results": []}
        for d in data[:20]:
            norad = d.get("NORAD_CAT_ID")
            if norad in seen:
                continue
            seen.add(norad)
            results.append({
                "name": d.get("OBJECT_NAME"),
                "norad": norad,
                "inc": d.get("INCLINATION"),
                "epoch": d.get("EPOCH"),
            })

    return {"query": name.strip(), "group": is_group, "terms": terms, "results": results[:50]}


def propagate(norad, norbits, step_min, start_dt):
    gp = fetch_gp(norad)
    sat = Satrec()
    omm.initialize(sat, gp)
    name = gp["OBJECT_NAME"]

    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)

    period_min = 1440.0 / gp["MEAN_MOTION"]
    total_min = norbits * period_min
    n_steps = int(total_min / step_min) + 1

    pts = []
    for i in range(n_steps):
        t = start_dt + timedelta(minutes=i * step_min)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute,
                      t.second + t.microsecond / 1e6)
        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            continue
        # ECI -> geodetic
        gmst = 0  # simplified; use OMEGA_EARTH * seconds
        from orbitas_rt.orbit3d import eci_to_geodetic
        dt_s = (t - start_dt).total_seconds()
        lat, lon, alt = eci_to_geodetic(__import__("numpy").array(r) * 1000.0, dt_s)
        pts.append({"lat": float(lat), "lon": float(lon), "alt": float(alt), "t": t.isoformat()})

    # subsolar for day/night
    utc_h = start_dt.hour + start_dt.minute / 60.0
    subsolar_lon = 180.0 - utc_h * 15.0
    doy = start_dt.timetuple().tm_yday
    subsolar_lat = -23.44 * __import__("numpy").cos(2 * __import__("numpy").pi * (doy + 10) / 365.25)

    return {
        "sat": name,
        "norad": norad,
        "norbits": norbits,
        "step_min": step_min,
        "start": start_dt.isoformat(),
        "period_min": period_min,
        "points": pts,
        "subsolar_lon": subsolar_lon,
        "subsolar_lat": float(subsolar_lat),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/horizons":
            params = parse_qs(parsed.query)
            target = params.get("target", ["-85"])[0]
            start = params.get("start", ["2026-11-15"])[0]
            stop = params.get("stop", ["2026-11-18"])[0]
            step = params.get("step", ["1 d"])[0]
            center = params.get("center", ["@sun"])[0]
            try:
                t, r, v = fetch_vectors(target, start, stop, step=step, center=center,
                                        frame="ECLIPTIC", units="AU-D")
                traj = [[float(x), float(y)] for x, y in zip(r[:, 0], r[:, 1])]
                result = {"target": target, "traj": traj, "n": len(traj)}
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed.path == "/api/lunar":
            params = parse_qs(parsed.query)
            sc = params.get("sc", ["-85"])[0]
            start = params.get("start", ["2026-11-15"])[0]
            stop = params.get("stop", ["2026-11-18"])[0]
            step = params.get("step", ["4 h"])[0]
            try:
                t_moon, r_moon, v_moon = fetch_vectors("301", start, stop, step=step,
                                                        center="399", frame="ECLIPTIC", units="KM-S")
                t_sc, r_sc, v_sc = fetch_vectors(sc, start, stop, step=step,
                                                  center="399", frame="ECLIPTIC", units="KM-S")
                result = {
                    "sc": sc,
                    "moon": [[float(x), float(y)] for x, y in zip(r_moon[:, 0], r_moon[:, 1])],
                    "sc_traj": [[float(x), float(y)] for x, y in zip(r_sc[:, 0], r_sc[:, 1])],
                    "start": r_sc[0].tolist() if len(r_sc) else [],
                    "end": r_sc[-1].tolist() if len(r_sc) else [],
                }
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed.path == "/api/stations":
            with open(STATIONS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/groups":
            body = json.dumps({"groups": sorted(set(list(GROUPS.keys()) + list(CURATED_GROUPS.keys())))}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            name = params.get("name", [""])[0]
            result = search_satellites(name)
            body = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/query":
            params = parse_qs(parsed.query)
            try:
                norad = int(params.get("norad", ["25544"])[0])
                norbits = int(params.get("norbits", ["3"])[0])
                step = float(params.get("step", ["1"])[0])
                start_str = params.get("start", [None])[0]
                start_dt = datetime.fromisoformat(start_str) if start_str else None
                result = propagate(norad, norbits, step, start_dt)
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            super().do_GET()


if __name__ == "__main__":
    os.chdir(ROOT)
    httpd = HTTPServer(("0.0.0.0", PORT), Handler)
    print("Servidor en http://localhost:%d" % PORT)
    print("Abrir http://localhost:%d/query.html" % PORT)
    httpd.serve_forever()