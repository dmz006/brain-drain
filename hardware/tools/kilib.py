"""Access to symbol definitions and pin geometry from the project library and KiCad's stock libraries."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import sexp

STOCK = Path(os.environ.get("KICAD9_SYMBOL_DIR", "/usr/share/kicad/symbols"))
PROJECT_LIB = Path(__file__).resolve().parent.parent / "lib" / "brain-drain.kicad_sym"


@dataclass
class PinGeo:
    number: str
    name: str
    etype: str
    x: float  # symbol coords, +y up, connection point
    y: float
    angle: int
    length: float
    unit: int


@dataclass
class SymDef:
    lib: str
    name: str
    node: list  # parsed s-expression, name already prefixed "lib:name"
    pins: list[PinGeo]
    is_power: bool

    @property
    def lib_id(self):
        return f"{self.lib}:{self.name}"

    def units(self) -> list[int]:
        us = sorted({p.unit for p in self.pins if p.unit})
        return us or [1]

    def pins_of_unit(self, unit: int) -> list[PinGeo]:
        return [p for p in self.pins if p.unit in (0, unit)]

    def bbox(self, unit: int):
        """(xmin, ymin, xmax, ymax) in symbol coords including pin ends."""
        xs, ys = [], []
        for c in _walk_graphics(self.node, unit):
            xs.extend(c[0]); ys.extend(c[1])
        for p in self.pins_of_unit(unit):
            xs.append(p.x); ys.append(p.y)
        if not xs:
            return (-2.54, -2.54, 2.54, 2.54)
        return (min(xs), min(ys), max(xs), max(ys))


def _walk_graphics(node, unit):
    out = []
    for sub in sexp.find_all(node, "symbol"):
        nm = str(sub[1])
        try:
            u = int(nm.rsplit("_", 2)[1])
        except (IndexError, ValueError):
            continue
        if u not in (0, unit):
            continue
        for g in sub:
            if not isinstance(g, list):
                continue
            if g[0] in ("rectangle",):
                s, e = sexp.find(g, "start"), sexp.find(g, "end")
                out.append(([float(s[1]), float(e[1])], [float(s[2]), float(e[2])]))
            elif g[0] == "polyline":
                pts = sexp.find(g, "pts")
                xs = [float(p[1]) for p in pts[1:]]; ys = [float(p[2]) for p in pts[1:]]
                out.append((xs, ys))
            elif g[0] == "circle":
                c = sexp.find(g, "center"); r = float(sexp.find(g, "radius")[1])
                out.append(([float(c[1]) - r, float(c[1]) + r], [float(c[2]) - r, float(c[2]) + r]))
    return out


@lru_cache(maxsize=None)
def _lib_nodes(path: str):
    tree = sexp.parse(Path(path).read_text())[0]
    return {str(s[1]): s for s in sexp.find_all(tree, "symbol")}


def _resolve(lib: str, name: str):
    path = str(PROJECT_LIB) if lib == "brain-drain" else str(STOCK / f"{lib}.kicad_sym")
    nodes = _lib_nodes(path)
    if name not in nodes:
        raise KeyError(f"{lib}:{name} not found in {path}")
    node = nodes[name]
    ext = sexp.find(node, "extends")
    if ext:
        parent = _resolve(lib, str(ext[1]))
        # flatten: parent body with child's properties
        import copy
        merged = copy.deepcopy(parent.node)
        merged[1] = sexp.Str(name)
        child_props = {str(p[1]): p for p in sexp.find_all(node, "property")}
        for i, c in enumerate(merged):
            if isinstance(c, list) and c and c[0] == "property" and str(c[1]) in child_props:
                merged[i] = child_props[str(c[1])]
        # rename unit sub-symbols to the child name
        for sub in sexp.find_all(merged, "symbol"):
            sub[1] = sexp.Str(str(sub[1]).replace(parent.name, name, 1))
        node = merged
    import copy
    node = copy.deepcopy(node)
    return SymDef(lib, name, node, _pins(node), sexp.find(node, "power") is not None)


def _pins(node) -> list[PinGeo]:
    out = []
    for sub in sexp.find_all(node, "symbol"):
        nm = str(sub[1])
        try:
            unit = int(nm.rsplit("_", 2)[1])
        except (IndexError, ValueError):
            unit = 0
        for p in sexp.find_all(sub, "pin"):
            at = sexp.find(p, "at")
            out.append(PinGeo(
                number=str(sexp.find(p, "number")[1]), name=str(sexp.find(p, "name")[1]), etype=str(p[1]),
                x=float(at[1]), y=float(at[2]), angle=int(float(at[3])) if len(at) > 3 else 0,
                length=float(sexp.find(p, "length")[1]), unit=unit))
    return out


@lru_cache(maxsize=None)
def get(lib_id: str) -> SymDef:
    lib, name = lib_id.split(":", 1)
    return _resolve(lib, name)


def embedded_node(sd: SymDef):
    """Symbol node as it must appear in a schematic's lib_symbols (name prefixed with lib)."""
    import copy
    n = copy.deepcopy(sd.node)
    n[1] = sexp.Str(sd.lib_id)
    return n
