"""Simulador de "verdad" + mediciones tipo overlay del webcast + corrida del filtro."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field

import numpy as np

from .dynamics import VehicleParams, altitude, downrange, initial_state, rk4_step, speed
from .ekf import EKF
from .geo import DEFAULT_AZIMUTH_DEG, STARBASE, destination

# Ruido de medición asumido por el filtro (el overlay entrega enteros: km y km/h)
SIGMA_ALT_M = 400.0
SIGMA_SPEED_MS = 3.0


@dataclass
class Scenario:
    nominal: VehicleParams = field(default_factory=VehicleParams)
    # "Realidad": parámetros ligeramente distintos al modelo del filtro.
    truth: VehicleParams = field(
        default_factory=lambda: VehicleParams().perturbed(
            a0=16.05, a1=34.1, pitch_final_deg=89.1, beta=500.0
        )
    )
    # Ventanas sin señal (s): corte en ascenso, corte en coast y apagón de reentrada.
    dropouts: tuple = ((300.0, 420.0), (850.0, 1150.0), (1580.0, 1700.0))
    # Encendido NO anunciado en la "verdad": (t_inicio, t_fin, aceleración m/s^2 en la dirección de la velocidad)
    surprise_burn: tuple = (950.0, 980.0, 2.0)
    seed: int = 42


def simulate_truth(params: VehicleParams, dt: float = 0.5, t_max: float = 7000.0, surprise=None):
    """Integra la trayectoria "real". Devuelve t (1 s) y estados (N, 4).

    `surprise` = (t0, t1, a) añade un empuje no modelado a lo largo de la velocidad.
    """
    extra = None
    if surprise is not None:
        t0_, t1_, a_ = surprise

        def extra(t, s):
            if t0_ <= t <= t1_:
                return a_ * s[2:] / max(np.hypot(*s[2:]), 1e-6)
            return np.zeros(2)
    s = initial_state()
    t = 0.0
    ts, ss = [0.0], [s.copy()]
    next_out = 1.0
    while t < t_max:
        s = rk4_step(t, s, dt, params, extra)
        t += dt
        if t >= next_out - 1e-9:
            ts.append(round(t, 6))
            ss.append(s.copy())
            next_out += 1.0
        if altitude(s) < 0 and t > params.burn_time:
            break
    return np.array(ts), np.array(ss)


def in_dropout(t: float, dropouts) -> bool:
    return any(a <= t <= b for a, b in dropouts)


def make_measurements(t, states, dropouts, rng):
    """Lee altitud (km, entero) y rapidez (km/h, entero) como en un overlay."""
    rows = []
    for ti, si in zip(t, states):
        if ti == 0.0 or in_dropout(ti, dropouts):
            continue
        alt_km = round((altitude(si) + rng.normal(0, 200.0)) / 1000.0)
        v_kmh = round((speed(si) + rng.normal(0, 2.0)) * 3.6)
        rows.append((float(ti), int(alt_km), int(v_kmh)))
    return rows


def write_measurements(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t_s", "altitude_km", "speed_kmh"])
        w.writerows(rows)


def read_measurements(path):
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            out.append((float(r["t_s"]), float(r["altitude_km"]), float(r["speed_kmh"])))
    return out


def run_tracker(meas, t_end, params: VehicleParams, truth=None,
                site=STARBASE, azimuth_deg=DEFAULT_AZIMUTH_DEG):
    """Corre el EKF sobre mediciones (t, alt_km, speed_kmh). Devuelve dict de arrays."""
    meas_by_t = {round(t, 6): (a, v) for t, a, v in meas}
    P0 = np.diag([10.0**2, 10.0**2, 1.0, 1.0])
    ekf = EKF(0.0, initial_state(), P0, params)
    R = np.diag([SIGMA_ALT_M**2, SIGMA_SPEED_MS**2])

    cols = {k: [] for k in
            ["t_s", "downrange_km", "altitude_km", "speed_kms",
             "sigma_down_km", "sigma_alt_km", "measured"]}
    covs = []
    grid = np.arange(0.0, t_end + 1e-9, 1.0)
    for t in grid:
        if t > 0:
            ekf.predict(float(t))
            m = meas_by_t.get(round(float(t), 6))
            if m is not None:
                z = np.array([m[0] * 1000.0, m[1] / 3.6])
                ekf.update(z, R)
        C = ekf.local_position_cov()
        cols["t_s"].append(t)
        cols["downrange_km"].append(downrange(ekf.x) / 1e3)
        cols["altitude_km"].append(altitude(ekf.x) / 1e3)
        cols["speed_kms"].append(speed(ekf.x) / 1e3)
        cols["sigma_down_km"].append(np.sqrt(C[0, 0]) / 1e3)
        cols["sigma_alt_km"].append(np.sqrt(C[1, 1]) / 1e3)
        cols["measured"].append(1 if round(float(t), 6) in meas_by_t else 0)
        covs.append(C / 1e6)  # km^2
    out = {k: np.array(v) for k, v in cols.items()}
    out["cov_km2"] = np.array(covs)
    lat, lon = destination(site[0], site[1], azimuth_deg, out["downrange_km"] * 1e3)
    out["lat"], out["lon"] = lat, lon
    if truth is not None:
        tt, ts = truth
        n = min(len(tt), len(grid))
        out["truth_downrange_km"] = np.array([downrange(s) / 1e3 for s in ts[:n]])
        out["truth_altitude_km"] = np.array([altitude(s) / 1e3 for s in ts[:n]])
        tl, tn = destination(site[0], site[1], azimuth_deg, out["truth_downrange_km"] * 1e3)
        out["truth_lat"], out["truth_lon"] = tl, tn
    return out


def write_track_csv(path, res):
    n = len(res["t_s"])
    has_truth = "truth_altitude_km" in res
    head = ["t_s", "lat", "lon", "downrange_km", "altitude_km", "speed_kms",
            "sigma_down_km", "sigma_alt_km", "measured"]
    if has_truth:
        head += ["truth_downrange_km", "truth_altitude_km"]
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(head)
        for i in range(n):
            row = [f"{res['t_s'][i]:.0f}", f"{res['lat'][i]:.4f}", f"{res['lon'][i]:.4f}",
                   f"{res['downrange_km'][i]:.2f}", f"{res['altitude_km'][i]:.2f}",
                   f"{res['speed_kms'][i]:.3f}", f"{res['sigma_down_km'][i]:.2f}",
                   f"{res['sigma_alt_km'][i]:.2f}", int(res["measured"][i])]
            if has_truth:
                if i < len(res["truth_altitude_km"]):
                    row += [f"{res['truth_downrange_km'][i]:.2f}", f"{res['truth_altitude_km'][i]:.2f}"]
                else:
                    row += ["", ""]
            w.writerow(row)


def write_geojson(path, res):
    import json
    feats = [{
        "type": "Feature",
        "properties": {"name": "estimada (EKF)", "stroke": "#d62728"},
        "geometry": {"type": "LineString",
                     "coordinates": [[float(lo), float(la)] for la, lo in zip(res["lat"], res["lon"])]},
    }]
    if "truth_lat" in res:
        feats.append({
            "type": "Feature",
            "properties": {"name": "verdad simulada", "stroke": "#555555"},
            "geometry": {"type": "LineString",
                         "coordinates": [[float(lo), float(la)]
                                         for la, lo in zip(res["truth_lat"], res["truth_lon"])]},
        })
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
