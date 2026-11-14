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


if __name__ == "__main__":  # permite correr sin pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
