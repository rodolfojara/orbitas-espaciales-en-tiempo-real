"""Gráficos de ejemplo (matplotlib, sin pandas)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _shade(ax, dropouts, label=True):
    for i, (a, b) in enumerate(dropouts):
        ax.axvspan(a, b, color="#f4c7c3", alpha=0.6, lw=0,
                   label="sin señal (solo propagación)" if (label and i == 0) else None)


def plot_trajectory(res, dropouts, path):
    """Altitud vs distancia recorrida: verdad, estimación y puntos medidos."""
    t = res["t_s"]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    if "truth_altitude_km" in res:
        n = len(res["truth_altitude_km"])
        ax.plot(res["truth_downrange_km"], res["truth_altitude_km"], color="#444", lw=4,
                alpha=0.25, label="verdad simulada")
    ax.plot(res["downrange_km"], res["altitude_km"], color="#1f77b4", lw=1.6, label="estimación EKF")
    meas = res["measured"] == 1
    ax.plot(res["downrange_km"][meas], res["altitude_km"][meas], ".", ms=1.5, color="#2ca02c",
            label="instantes con medición")
    for i, (a, b) in enumerate(dropouts):
        m = (t >= a) & (t <= b)
        ax.plot(res["downrange_km"][m], res["altitude_km"][m], color="#d62728", lw=3,
                label="tramos sin señal" if i == 0 else None)
    for tm in (0, 500, 1000, 1500, 1800):
        i = int(np.argmin(np.abs(t - tm)))
        ax.annotate(f"T+{tm}s", (res["downrange_km"][i], res["altitude_km"][i]),
                    textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8)
    ax.set_xlabel("distancia recorrida sobre la superficie (km)")
    ax.set_ylabel("altitud (km)")
    ax.set_title("Trayectoria estimada (simulación de ejemplo, no son datos reales)")
    ax.set_ylim(0, 1.12 * float(np.max(res["altitude_km"])))
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_time_series(res, dropouts, path):
    """Altitud y rapidez vs tiempo, con banda de incertidumbre ±2σ."""
    t = res["t_s"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.2), sharex=True)
    for ax in (a1, a2):
        _shade(ax, dropouts, label=(ax is a1))
    alt, sa = res["altitude_km"], res["sigma_alt_km"]
    a1.fill_between(t, alt - 2 * sa, alt + 2 * sa, color="#1f77b4", alpha=0.25, label="±2σ")
    a1.plot(t, alt, color="#1f77b4", label="estimación")
    if "truth_altitude_km" in res:
        a1.plot(t[: len(res["truth_altitude_km"])], res["truth_altitude_km"], "--", color="#444",
                lw=1, label="verdad simulada")
    a1.set_ylabel("altitud (km)")
    a1.grid(alpha=0.3)
    a1.legend(fontsize=8, loc="upper left")
    a2.plot(t, res["speed_kms"], color="#ff7f0e")
    a2.set_ylabel("rapidez (km/s)")
    a2.set_xlabel("tiempo desde el despegue T+ (s)")
    a2.grid(alpha=0.3)
    fig.suptitle("Posición-tiempo: altitud y rapidez estimadas")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_uncertainty(res, dropouts, path):
    """Error real vs incertidumbre estimada (distancia recorrida)."""
    t = res["t_s"]
    n = len(res.get("truth_downrange_km", []))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    _shade(ax, dropouts)
    ax.plot(t, 2 * res["sigma_down_km"], color="#1f77b4", label="2σ estimada por el filtro")
    if n:
        err = np.abs(res["downrange_km"][:n] - res["truth_downrange_km"][:n])
        ax.plot(t[:n], err, color="#d62728", lw=1, label="|error real| (conocido solo en la simulación)")
    ax.set_yscale("log")
    ax.set_xlabel("tiempo desde el despegue T+ (s)")
    ax.set_ylabel("distancia recorrida: error (km)")
    ax.set_title("La incertidumbre crece sin mediciones y se corrige al volver la señal")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
