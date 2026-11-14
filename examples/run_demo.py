"""Ejecuta la demo sin instalar el paquete:  python examples/run_demo.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from orbitas_rt.cli import main  # noqa: E402

main(["demo", "--out", os.path.join(HERE, "output")])
