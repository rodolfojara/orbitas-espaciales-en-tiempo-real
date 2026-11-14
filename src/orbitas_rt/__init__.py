"""orbitas_rt: estimación de trayectoria en tiempo real con filtro de Kalman extendido."""
from .dynamics import VehicleParams, MU, RE, deriv, rk4_step
from .ekf import EKF

__all__ = ["VehicleParams", "MU", "RE", "deriv", "rk4_step", "EKF"]
__version__ = "0.1.0"
