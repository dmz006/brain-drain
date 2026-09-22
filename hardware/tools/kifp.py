"""Footprint access: load .kicad_mod from the project library or KiCad's stock libraries."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import sexp

STOCK = Path(os.environ.get("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints"))
PROJECT = Path(__file__).resolve().parent.parent / "lib" / "brain-drain.pretty"


@lru_cache(maxsize=None)
def load(fp_id: str):
    """Parsed footprint node for 'Lib:Name'. Raises FileNotFoundError if missing."""
    lib, name = fp_id.split(":", 1)
    path = (PROJECT if lib == "brain-drain" else STOCK / f"{lib}.pretty") / f"{name}.kicad_mod"
    if not path.exists():
        raise FileNotFoundError(fp_id)
    return sexp.parse(path.read_text())[0]


def exists(fp_id: str) -> bool:
    try:
        load(fp_id)
        return True
    except (FileNotFoundError, ValueError):
        return False


def pads(node):
    return [str(p[1]) for p in sexp.find_all(node, "pad")]


def bbox(node):
    """Rough courtyard/fab bounding box (mm) from pads and courtyard lines."""
    xs, ys = [], []
    for p in sexp.find_all(node, "pad"):
        at = sexp.find(p, "at"); sz = sexp.find(p, "size")
        x, y = float(at[1]), float(at[2]); w, h = float(sz[1]), float(sz[2])
        xs += [x - w / 2, x + w / 2]; ys += [y - h / 2, y + h / 2]
    for tag in ("fp_line", "fp_rect"):
        for l in sexp.find_all(node, tag):
            layer = sexp.find(l, "layer")
            if layer and str(layer[1]) in ("F.CrtYd", "F.Fab", "F.SilkS"):
                s, e = sexp.find(l, "start"), sexp.find(l, "end")
                xs += [float(s[1]), float(e[1])]; ys += [float(s[2]), float(e[2])]
    if not xs:
        return (-1, -1, 1, 1)
    return (min(xs), min(ys), max(xs), max(ys))


def placeholder(fp_id: str, w: float, h: float, pad_numbers: list[str]):
    """A courtyard-only stand-in with pads stacked (no copper geometry known yet)."""
    import uuid
    name = fp_id.split(":", 1)[1]
    lines = [f'(footprint "{fp_id}"', "(version 20241229)", '(generator "brain-drain-placeholder")', '(layer "F.Cu")',
             f'(descr "PLACEHOLDER {name}: outline only, real footprint pending vendor drawing")', "(attr smd)",
             f'(property "Reference" "REF**" (at 0 {-h/2-1.5} 0) (layer "F.SilkS") (uuid "{uuid.uuid4()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'(property "Value" "{name}" (at 0 {h/2+1.5} 0) (layer "F.Fab") (uuid "{uuid.uuid4()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'(fp_rect (start {-w/2} {-h/2}) (end {w/2} {h/2}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{uuid.uuid4()}"))',
             f'(fp_rect (start {-w/2-0.5} {-h/2-0.5}) (end {w/2+0.5} {h/2+0.5}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{uuid.uuid4()}"))',
             f'(fp_text user "PLACEHOLDER" (at 0 0 0) (layer "F.Fab") (uuid "{uuid.uuid4()}") (effects (font (size 1.2 1.2) (thickness 0.2))))']
    n = len(pad_numbers)
    for i, num in enumerate(pad_numbers):
        x = -w / 2 + 1 + (w - 2) * (i / max(n - 1, 1))
        lines.append(f'(pad "{num}" smd rect (at {x:.2f} {h/2 - 1:.2f}) (size 0.3 1) (layers "F.Cu" "F.Mask") (uuid "{uuid.uuid4()}"))')
    lines.append(")")
    return sexp.parse("\n".join(lines))[0]
