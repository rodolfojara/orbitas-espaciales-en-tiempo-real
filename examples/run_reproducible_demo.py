"""Demostración reproducible: entrada fija -> resultados verificables.

Uso:
  python examples/run_reproducible_demo.py              # genera resultados
  python examples/run_reproducible_demo.py --check      # compara con la referencia
  python examples/run_reproducible_demo.py --save-expected  # regenera la referencia

Entrada fija: examples/data/measurements.csv (1320 mediciones, semilla 42).
Salida: examples/output/reproducible/
  results.csv, summary.json, RESULTS.md, time_series.png
Referencia: examples/data/reproducible_demo_expected.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from orbitas_rt import plotting, sim  # noqa: E402

DEFAULT_INPUT = os.path.join(HERE, "data", "measurements.csv")
DEFAULT_OUT = os.path.join(HERE, "output", "reproducible")
DEFAULT_EXPECTED = os.path.join(HERE, "data", "reproducible_demo_expected.json")
CHECKPOINTS = (0, 120, 300, 420, 850, 950, 1000, 1150, 1300, 1580, 1700, 1863)
EXTRA_S = 120.0
TOL = 0.01


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build(input_path):
    """Corre el filtro sobre la entrada fija. La verdad simulada es solo referencia."""
    meas = sim.read_measurements(input_path)
    scenario = sim.Scenario()
    truth = sim.simulate_truth(scenario.truth, surprise=scenario.surprise_burn)
    t_end = max(m[0] for m in meas) + EXTRA_S
    res = sim.run_tracker(meas, t_end, scenario.nominal, truth)
    return meas, scenario, res


def summarise(input_path, meas, res):
    """Resume los resultados con números redondeados y estables."""
    n = len(res["t_s"])
    checkpoints = []
    for t in CHECKPOINTS:
        i = min(int(t), n - 1)
        checkpoints.append({
            "t_s": t,
            "altitude_km": round(float(res["altitude_km"][i]), 3),
            "speed_kms": round(float(res["speed_kms"][i]), 4),
            "sigma_alt_km": round(float(res["sigma_alt_km"][i]), 3),
            "measured": int(res["measured"][i]),
        })
    truth_alt = res["truth_altitude_km"]
    m = min(n, len(truth_alt))  # la verdad llega hasta la última medición; el filtro propaga 120 s más
    err = np.abs(res["altitude_km"][:m] - truth_alt[:m])
    sin_med = res["measured"] == 0
    return {
        "input_file": os.path.basename(input_path),
        "input_sha256": sha256(input_path),
        "n_measurements": len(meas),
        "n_estimates": n,
        "t_end_s": round(float(res["t_s"][-1]), 1),
        "checkpoints": checkpoints,
        "metrics": {
            "max_altitude_error_km": round(float(np.nanmax(err)), 3),
            "max_sigma_alt_during_dropout_km": round(float(np.max(res["sigma_alt_km"][sin_med])), 3),
            "final_altitude_km": round(float(res["altitude_km"][-1]), 3),
            "final_speed_kms": round(float(res["speed_kms"][-1]), 4),
        },
    }


def compare(expected, actual, path="", diffs=None):
    """Compara dos resúmenes; los números usan TOL para evitar ruido de plataforma."""
    if diffs is None:
        diffs = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            diffs.append("%s: claves distintas %s vs %s" % (path, sorted(expected), sorted(actual)))
            return diffs
        for k in expected:
            compare(expected[k], actual[k], "%s.%s" % (path, k) if path else k, diffs)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append("%s: longitud %d vs %d" % (path, len(expected), len(actual)))
        else:
            for i, (a, b) in enumerate(zip(expected, actual)):
                compare(a, b, "%s[%d]" % (path, i), diffs)
    elif isinstance(expected, bool) or isinstance(actual, bool):
        if expected != actual:
            diffs.append("%s: %r vs %r" % (path, expected, actual))
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if abs(float(expected) - float(actual)) > TOL:
            diffs.append("%s: esperado %s, obtenido %s" % (path, expected, actual))
    elif expected != actual:
        diffs.append("%s: %r vs %r" % (path, expected, actual))
    return diffs


def leaf_count(obj):
    if isinstance(obj, dict):
        return sum(leaf_count(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(leaf_count(v) for v in obj)
    return 1


def render_results(summary, meas):
    lines = [
        "# Resultados de la demo reproducible",
        "",
        "Generado por `python examples/run_reproducible_demo.py`.",
        "Los valores son una **simulación ilustrativa**, no un vuelo real.",
        "",
        "## Entrada",
        "",
        "- Archivo: `%s`" % summary["input_file"],
        "- SHA-256: `%s`" % summary["input_sha256"],
        "- Mediciones: %d" % summary["n_measurements"],
        "- Columnas: `t_s, altitude_km, speed_kmh` (altitud entera en km, rapidez entera en km/h)",
        "",
        "Primeras 3 filas:",
        "",
        "```csv",
        "t_s,altitude_km,speed_kmh",
    ]
    for row in meas[:3]:
        lines.append(",".join(str(x) for x in row))
    lines += ["```", "", "Últimas 3 filas:", "", "```csv", "t_s,altitude_km,speed_kmh"]
    for row in meas[-3:]:
        lines.append(",".join(str(x) for x in row))
    lines += [
        "```",
        "",
        "## Resultados (puntos de control)",
        "",
        "| t (s) | altitud estimada (km) | velocidad (km/s) | σ altitud (km) | ¿hubo medición? |",
        "|---:|---:|---:|---:|:--:|",
    ]
    for c in summary["checkpoints"]:
        lines.append("| %d | %.3f | %.4f | %.3f | %s |" %
                     (c["t_s"], c["altitude_km"], c["speed_kms"], c["sigma_alt_km"],
                      "sí" if c["measured"] else "no"))
    m = summary["metrics"]
    lines += [
        "",
        "## Métricas",
        "",
        "- Error máximo de altitud contra la verdad simulada: **%.3f km**" % m["max_altitude_error_km"],
        "- Máxima σ de altitud sin medición: **%.3f km**" % m["max_sigma_alt_during_dropout_km"],
        "- Estimación final (T+%.0f s): **%.3f km**, **%.4f km/s**" %
        (summary["t_end_s"], m["final_altitude_km"], m["final_speed_kms"]),
    ]
    if m["final_altitude_km"] < 0:
        lines += [
            "",
            "> La propagación extra de 120 s continúa después del contacto con el suelo;",
            "> la altitud negativa es un artefacto del modelo (no detiene la nave en tierra).",
        ]
    lines += [
        "",
        "## Verificar",
        "",
        "```bash",
        "python examples/run_reproducible_demo.py --check",
        "```",
        "",
        "Compara %d valores contra `examples/data/reproducible_demo_expected.json`." % leaf_count(summary),
        "Devuelve `PASS` si la entrada y los resultados siguen siendo los mismos.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=DEFAULT_INPUT, help="CSV de mediciones de entrada")
    ap.add_argument("--out", default=DEFAULT_OUT, help="directorio de resultados")
    ap.add_argument("--expected", default=DEFAULT_EXPECTED, help="JSON de referencia")
    ap.add_argument("--check", action="store_true", help="compara con la referencia y sale con 0/1")
    ap.add_argument("--save-expected", action="store_true", help="escribe la referencia actual")
    args = ap.parse_args(argv)

    meas, scenario, res = build(args.input)
    summary = summarise(args.input, meas, res)

    os.makedirs(args.out, exist_ok=True)
    sim.write_track_csv(os.path.join(args.out, "results.csv"), res)
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open(os.path.join(args.out, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write(render_results(summary, meas))
    plotting.plot_time_series(res, scenario.dropouts, os.path.join(args.out, "time_series.png"))

    if args.save_expected:
        with open(args.expected, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print("Referencia guardada:", args.expected)
        return

    if args.check:
        if not os.path.exists(args.expected):
            raise SystemExit("No existe %s; genérala una vez con --save-expected" % args.expected)
        with open(args.expected, encoding="utf-8") as f:
            expected = json.load(f)
        diffs = compare(expected, summary)
        total = leaf_count(expected)
        if diffs:
            print("FAIL: %d/%d valores distintos (tolerancia %.3g)" % (len(diffs), total, TOL))
            for d in diffs[:20]:
                print("  -", d)
            raise SystemExit(1)
        print("PASS: %d/%d valores idénticos (tolerancia %.3g)" % (total, total, TOL))
        print("Resultados en:", args.out)
        return

    print("Resultados generados en:", args.out)
    print("Verificar con: python examples/run_reproducible_demo.py --check")


if __name__ == "__main__":
    main()
