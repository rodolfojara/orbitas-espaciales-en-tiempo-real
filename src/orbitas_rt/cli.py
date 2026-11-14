"""Línea de comandos.

    orbitas-rt demo  --out examples/output      # simula, filtra y genera CSV + imágenes
    orbitas-rt track mediciones.csv --out out/  # filtra tus mediciones (t_s, altitude_km, speed_kmh)
    orbitas-rt sources --mission starship       # fuentes de datos con su estado
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from . import plotting, sim


def cmd_demo(args):
    os.makedirs(args.out, exist_ok=True)
    data_dir = os.path.join(os.path.dirname(os.path.abspath(args.out)), "data")
    os.makedirs(data_dir, exist_ok=True)
    sc = sim.Scenario()
    truth = sim.simulate_truth(sc.truth, surprise=sc.surprise_burn)
    rng = np.random.default_rng(sc.seed)
    meas = sim.make_measurements(*truth, sc.dropouts, rng)
    sim.write_measurements(os.path.join(data_dir, "measurements.csv"), meas)
    res = sim.run_tracker(meas, truth[0][-1], sc.nominal, truth)
    sim.write_track_csv(os.path.join(args.out, "track.csv"), res)
    sim.write_geojson(os.path.join(args.out, "track.geojson"), res)
    plotting.plot_trajectory(res, sc.dropouts, os.path.join(args.out, "trajectory.png"))
    plotting.plot_time_series(res, sc.dropouts, os.path.join(args.out, "time_series.png"))
    plotting.plot_uncertainty(res, sc.dropouts, os.path.join(args.out, "uncertainty.png"))
    print(f"Listo: {len(meas)} mediciones, {len(res['t_s'])} estimaciones -> {args.out}")


def cmd_track(args):
    os.makedirs(args.out, exist_ok=True)
    meas = sim.read_measurements(args.measurements)
    t_end = args.t_end if args.t_end else max(m[0] for m in meas) + args.extra
    res = sim.run_tracker(meas, t_end, sim.Scenario().nominal)
    sim.write_track_csv(os.path.join(args.out, "track.csv"), res)
    sim.write_geojson(os.path.join(args.out, "track.geojson"), res)
    plotting.plot_time_series(res, [], os.path.join(args.out, "time_series.png"))
    print(f"Estimación escrita en {args.out}/track.csv")


def cmd_sources(args):
    from . import sources as src

    data = src.load()
    errs = src.validate(data["sources"])
    if errs:
        raise SystemExit("sources.json inválido:\n" + "\n".join(errs))
    if args.markdown:
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown)), exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(src.to_markdown(data))
        print(f"Escrito {args.markdown}")
        return
    items = src.by_mission(args.mission) if args.mission else data["sources"]
    for s in items:
        est = s["status"] + (f" {s['checked']}" if s["checked"] else "")
        print(f"{s['id']:<24} [{', '.join(s['missions'])}]  {est}")
        print(f"   {s['name']}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="orbitas-rt", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="simulación completa de ejemplo")
    d.add_argument("--out", default="examples/output")
    d.set_defaults(func=cmd_demo)
    t = sub.add_parser("track", help="filtrar un CSV de mediciones")
    t.add_argument("measurements")
    t.add_argument("--out", default="out")
    t.add_argument("--t-end", type=float, default=None, help="tiempo final a estimar (s)")
    t.add_argument("--extra", type=float, default=0.0, help="segundos a propagar tras la última medición")
    t.set_defaults(func=cmd_track)
    r = sub.add_parser("sources", help="lista el registro de fuentes de datos")
    r.add_argument("--mission", choices=["starship", "artemis", "deep_space", "leo"])
    r.add_argument("--markdown", metavar="RUTA", help="escribe el registro completo en Markdown")
    r.set_defaults(func=cmd_sources)
    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
