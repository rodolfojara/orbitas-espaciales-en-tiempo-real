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
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sgp4.api import Satrec, jday
from sgp4 import omm
from orbitas_rt.tle import fetch_gp

ROOT = os.path.join(os.path.dirname(__file__), "output")
PORT = 8000


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
        if parsed.path == "/api/query":
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