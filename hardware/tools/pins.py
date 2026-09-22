"""Pin tables from hardware/ref/*.csv."""

from __future__ import annotations

import csv
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "ref"


def _rows(name):
    with open(REF / name, newline="") as f:
        return list(csv.DictReader(f))


def cm5():
    """{pin: (signal, description)} for all 200 pins."""
    return {int(r["pin"]): (r["signal"], r["description"]) for r in _rows("cm5-pinout.csv")}


def usb5744():
    return {r["pin"]: (r["name"], r["buffer"]) for r in _rows("usb5744-pinout.csv")}


def asm1153e():
    return {int(r["pin"]): (r["name"], r["type"], r["description"]) for r in _rows("asm1153e-pinout.csv")}


def m2_mkey():
    return {int(r["pin"]): r["signal"] for r in _rows("m2-mkey-pinout.csv")}
