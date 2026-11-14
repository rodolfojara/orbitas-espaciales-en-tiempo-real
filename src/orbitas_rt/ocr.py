"""EXPERIMENTAL / SIN PROBAR CONTRA UN WEBCAST REAL.

Lee altitud y velocidad del overlay de un video y escribe un CSV compatible con
`orbitas-rt track`. Requiere:  pip install opencv-python easyocr

Debes indicar las regiones (x, y, ancho, alto) del overlay donde aparecen la
altitud y la velocidad, y las unidades que muestra el overlay.

    python -m orbitas_rt.ocr video.mp4 --alt-roi 120,980,200,60 --speed-roi 120,1040,260,60 \
        --t0 12.0 --out mediciones.csv

`--t0` es el segundo del video que corresponde a T+0 (despegue).
IMPORTANTE: si el overlay muestra velocidad respecto de la superficie y el
modelo usa velocidad inercial, hay un desfase sistemático que hay que corregir.
"""
from __future__ import annotations

import argparse
import csv
import re


def _digits(text: str):
    m = re.search(r"\d[\d,\.]*", text)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def main():
    import cv2  # import diferido: dependencias opcionales
    import easyocr

    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--alt-roi", required=True)
    ap.add_argument("--speed-roi", required=True)
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--step", type=float, default=1.0, help="segundos entre lecturas")
    ap.add_argument("--out", default="mediciones.csv")
    a = ap.parse_args()

    reader = easyocr.Reader(["en"], gpu=False)
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    roi_a = [int(v) for v in a.alt_roi.split(",")]
    roi_v = [int(v) for v in a.speed_roi.split(",")]

    def read(frame, roi):
        x, y, w, h = roi
        crop = frame[y:y + h, x:x + w]
        txt = " ".join(reader.readtext(crop, allowlist="0123456789,.", detail=0))
        return _digits(txt)

    rows, n, last = [], 0, -1e9
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t_video = n / fps
        n += 1
        t = t_video - a.t0
        if t < 0 or t - last < a.step:
            continue
        last = t
        alt, v = read(frame, roi_a), read(frame, roi_v)
        if alt is not None and v is not None:
            rows.append((round(t, 2), alt, v))
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t_s", "altitude_km", "speed_kmh"])
        w.writerows(rows)
    print(f"{len(rows)} lecturas -> {a.out}")


if __name__ == "__main__":
    main()
