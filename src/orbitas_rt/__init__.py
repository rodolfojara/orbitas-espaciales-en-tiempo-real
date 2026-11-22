"""orbitas_rt: estimación de trayectoria en tiempo real con filtro de Kalman extendido."""
from .dynamics import VehicleParams, MU, RE, deriv, rk4_step
from .ekf import EKF
from .ekf3d import EKF3D
from .timeutils import utc_to_jd, jd_to_utc, gmst, RE as RE_TIME
from .frames import eci_to_geodetic, eci_to_ecef, ecef_to_geodetic, geodetic_to_ecef
from .passes import predict_passes, footprint_radius, is_visible
from .od import batch_least_squares

__all__ = ["VehicleParams", "MU", "RE", "deriv", "rk4_step", "EKF", "EKF3D",
           "utc_to_jd", "jd_to_utc", "gmst", "eci_to_geodetic", "eci_to_ecef",
           "ecef_to_geodetic", "geodetic_to_ecef", "predict_passes",
           "footprint_radius", "is_visible", "batch_least_squares"]
__version__ = "0.1.0"
