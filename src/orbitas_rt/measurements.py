"""Fuentes de medición para estimación orbital.

Tres métodos (como pidió el usuario):
  1. SatNOGS: red abierta de estaciones de tierra (Doppler/observaciones).
  2. GNSS a bordo: posición del satélite si transmite su GPS (simulado aquí).
  3. Óptico: astrometría de observadores (simulado aquí).

Cada fuente devuelve la última medición disponible (posición + tiempo) para
que el EKF la use como corrección.
"""
from __future__ import annotations

import ssl
import json
import urllib.request
from datetime import datetime, timezone, timedelta

import numpy as np


def _now():
    return datetime.now(timezone.utc)


class Measurement:
    """Una medición de posición."""
    def __init__(self, lat, lon, alt, timestamp, method, noise_m=0.0):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.timestamp = timestamp  # datetime UTC
        self.method = method
        self.noise_m = noise_m

    def age_seconds(self, now=None):
        now = now or _now()
        return (now - self.timestamp).total_seconds()

    def to_dict(self):
        return {
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "noise_m": self.noise_m,
            "age_s": self.age_seconds(),
        }


class SatNOGSSource:
    """Fuente SatNOGS: consulta la API pública de observaciones.

    SatNOGS mide Doppler (range-rate), no posición directa. Aquí usamos la
    observación más reciente para obtener el tiempo de la última medición y
    una posición aproximada (TLE en ese instante). En un sistema real se haría
    orbit determination con las observaciones Doppler.
    """
    API = "https://network.satnogs.org/api/observations/"

    def __init__(self, norad_cat_id, timeout=15):
        self.norad = norad_cat_id
        self.timeout = timeout
        self._ctx = ssl._create_unverified_context()

    def latest(self):
        # Consultar observaciones recientes para este satélite
        url = "%s?satellite__norad_cat_id=%d&ordering=-end" % (self.API, self.norad)
        try:
            data = json.loads(urllib.request.urlopen(url, context=self._ctx,
                                                     timeout=self.timeout).read().decode())
        except Exception:
            return None
        if not data:
            return None
        now = _now()
        # buscar la observación completada más reciente (no futura)
        for obs in data:
            try:
                ts = datetime.fromisoformat(obs["end"].replace("Z", "+00:00"))
            except Exception:
                continue
            if ts <= now and obs.get("status") not in ("future", "scheduled"):
                return Measurement(lat=None, lon=None, alt=None, timestamp=ts,
                                   method="SatNOGS (Doppler)", noise_m=1000.0)
        # si no hay completadas, devolver None
        return None


class SimulatedGNSSSource:
    """Fuente GNSS a bordo (simulada): posición con ruido pequeño (~10 m)."""
    def __init__(self, noise_m=10.0):
        self.noise_m = noise_m

    def latest(self, true_lat, true_lon, true_alt):
        # simula una medición GPS reciente
        rng = np.random.default_rng()
        noise_deg = self.noise_m / 111000.0
        lat = true_lat + rng.normal(0, noise_deg)
        lon = true_lon + rng.normal(0, noise_deg)
        alt = true_alt + rng.normal(0, self.noise_m)
        return Measurement(lat=lat, lon=lon, alt=alt, timestamp=_now(),
                           method="GNSS a bordo (simulado)", noise_m=self.noise_m)


class SimulatedOpticalSource:
    """Fuente óptica (simulada): astrometría con ruido mayor (~1 km)."""
    def __init__(self, noise_m=1000.0):
        self.noise_m = noise_m

    def latest(self, true_lat, true_lon, true_alt):
        rng = np.random.default_rng()
        noise_deg = self.noise_m / 111000.0
        lat = true_lat + rng.normal(0, noise_deg)
        lon = true_lon + rng.normal(0, noise_deg)
        alt = true_alt + rng.normal(0, self.noise_m)
        return Measurement(lat=lat, lon=lon, alt=alt, timestamp=_now(),
                           method="Óptico (simulado)", noise_m=self.noise_m)


def quality_from_age(age_s):
    """Clasifica la calidad de la estimación según la antigüedad de la última medición."""
    if age_s is None:
        return "sin datos", "#999999"
    a = abs(age_s)
    if a < 60:
        return "buena", "#2ca02c"
    if a < 300:
        return "moderada", "#ff7f0e"
    if a < 1800:
        return "degradada", "#d62728"
    return "mala (sin medicion reciente)", "#8b0000"