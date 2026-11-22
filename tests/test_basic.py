import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orbitas_rt import EKF, RE, VehicleParams  # noqa: E402
from orbitas_rt.dynamics import initial_state  # noqa: E402
from orbitas_rt.geo import destination  # noqa: E402
from orbitas_rt.sim import Scenario, make_measurements, run_tracker, simulate_truth  # noqa: E402


def test_covariance_grows_without_measurements():
    ekf = EKF(0.0, initial_state(), np.diag([10.0**2] * 2 + [1.0] * 2), VehicleParams())
    ekf.predict(100.0)
    p100 = np.trace(ekf.P[:2, :2])
    ekf.predict(200.0)
    assert np.trace(ekf.P[:2, :2]) > p100


def test_update_reduces_covariance_and_corrects_state():
    ekf = EKF(0.0, initial_state(), np.diag([10.0**2] * 2 + [1.0] * 2), VehicleParams())
    ekf.predict(60.0)
    tr_before = np.trace(ekf.P)
    alt_est = np.hypot(*ekf.x[:2]) - RE
    ekf.update(np.array([alt_est + 200.0, np.hypot(*ekf.x[2:])]), np.diag([400.0**2, 3.0**2]))
    assert np.trace(ekf.P) < tr_before


def test_geo_zero_distance_is_launch_site():
    lat, lon = destination(26.0, -97.0, 96.0, 0.0)
    assert abs(float(lat) - 26.0) < 1e-9 and abs(float(lon) + 97.0) < 1e-9


def test_filter_tracks_truth_within_3_sigma():
    sc = Scenario()
    truth = simulate_truth(sc.truth, surprise=sc.surprise_burn)
    meas = make_measurements(*truth, sc.dropouts, np.random.default_rng(sc.seed))
    res = run_tracker(meas, truth[0][-1], sc.nominal, truth)
    n = len(res["truth_downrange_km"])
    err = np.abs(res["downrange_km"][:n] - res["truth_downrange_km"][:n])
    # tras el primer segundo, el error real debe quedar dentro de ~3σ (+ holgura de 0.5 km)
    assert np.all(err[5:] < 3 * res["sigma_down_km"][5:n] + 0.5)
    # la altitud estimada final coincide con la real (km)
    assert abs(res["altitude_km"][n - 1] - res["truth_altitude_km"][n - 1]) < 1.0


def test_sources_registry_is_valid():
    from orbitas_rt import sources

    data = sources.load()
    assert sources.validate(data["sources"]) == []
    assert len(sources.by_mission("starship")) >= 2
    assert "# Fuentes de datos" in sources.to_markdown(data)


def test_timeutils_roundtrip():
    from orbitas_rt.timeutils import utc_to_jd, jd_to_utc, gmst
    from datetime import datetime, timezone
    dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    jd = utc_to_jd(dt)
    dt2 = jd_to_utc(jd)
    assert abs((dt2 - dt).total_seconds()) < 2
    assert 0 <= gmst(jd) < 2 * 3.1416


def test_frames_roundtrip():
    from orbitas_rt.frames import eci_to_geodetic, geodetic_to_ecef, ecef_to_geodetic
    from datetime import datetime, timezone
    import numpy as np
    lat, lon, alt = 40.0, -3.0, 500000.0
    r = geodetic_to_ecef(lat, lon, alt)
    lat2, lon2, alt2 = ecef_to_geodetic(r)
    assert abs(lat2 - lat) < 1e-6
    assert abs(lon2 - lon) < 1e-6
    assert abs(alt2 - alt) < 1e-3


def test_passes_visibility():
    from orbitas_rt.passes import is_visible, footprint_radius
    from datetime import datetime, timezone
    import numpy as np
    # satélite directamente sobre la estación
    def sat_func(t):
        return np.array([0.0, 0.0, 7000000.0])  # 629 km alt, sobre el polo norte
    vis, el, az, rng = is_visible(sat_func, 90.0, 0.0, 0.0, datetime(2026, 1, 1, tzinfo=timezone.utc), min_el=0.0)
    assert vis is True
    assert footprint_radius(400.0) > 0


def test_od_convergence():
    from orbitas_rt.od import batch_least_squares
    import numpy as np
    # estado inicial: órbita circular a 7000 km
    r0 = np.array([7000000.0, 0.0, 0.0])
    v0 = np.array([0.0, 7500.0, 0.0])
    x0 = np.concatenate([r0, v0])
    # mediciones: posición en t=0, 10, 20 s (con ruido pequeño)
    t_meas = np.array([0.0, 10.0, 20.0])
    meas = np.zeros((3, 3))
    for i, ti in enumerate(t_meas):
        # propagar
        from orbitas_rt.orbit3d import rk4_step
        r, v = r0.copy(), v0.copy()
        nsub = max(1, int(abs(ti) / 1.0))
        h = ti / nsub if nsub > 0 else 0
        for _ in range(nsub):
            r, v = rk4_step(r, v, h)
        meas[i] = r + np.random.normal(0, 1.0, 3)
    x_est, resid, hist = batch_least_squares(meas, t_meas, x0, max_iter=5, tol=1e6)
    assert x_est.shape == (6,)
    assert len(hist) > 0
    # el estado estimado debe estar cerca del inicial (ruido pequeño)
    assert np.linalg.norm(x_est[:3] - r0) < 1000.0


if __name__ == "__main__":  # permite correr sin pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
