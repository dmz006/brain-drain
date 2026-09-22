"""Headless STL preview: painter's-algorithm render to PNG (numpy + Pillow only).

    python3 tools/stl_preview.py OUT.png [--view iso|top|bottom|front|left|iso2] [--width 1600] FILE[:R,G,B] ...

Several STLs render into one scene, each with its own colour, depth-sorted together.
"""
from __future__ import annotations

import re
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw


def load(path):
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        v = np.array([list(map(float, m.groups())) for m in re.finditer(rb"vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)", data)])
        return v.reshape(-1, 3, 3)
    n = struct.unpack("<I", data[80:84])[0]
    arr = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return arr["v"].reshape(-1, 3, 3).astype(float)


def rot(view):
    def rx(a): a = np.radians(a); return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    def rz(a): a = np.radians(a); return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    return {
        "top": np.eye(3),
        "bottom": np.diag([1, -1, -1.0]),
        "iso": rx(60) @ rz(-30),
        "iso2": rx(60) @ rz(35),
        "front": rx(90),                # looking at the +y (front, vents) face
        "rear": rx(90) @ rz(180),       # looking at the -y (rear, cables) face
        "left": rx(90) @ rz(90),
    }[view]


def render(parts, out, view="iso", width=1600):
    R = rot(view)
    tris = np.concatenate([p for p, _ in parts]); cols = np.concatenate([np.repeat([c], len(p), axis=0) for p, c in parts])
    p = tris @ R.T
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    nn = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    light = np.array([0.35, -0.45, 0.82]); light /= np.linalg.norm(light)   # from above and slightly in front of the tilted views
    shade = 0.3 + 0.7 * np.clip(nn @ light, 0, 1)
    order = np.argsort(p[:, :, 2].mean(1))
    xy = p[:, :, :2]
    lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
    height = int(width * (hi[1] - lo[1] + 1e-9) / (hi[0] - lo[0] + 1e-9)) + 40
    scale = (width - 40) / (hi[0] - lo[0] + 1e-9)
    img = Image.new("RGB", (width, height), (238, 240, 236))
    d = ImageDraw.Draw(img)
    for i in order:
        if nn[i, 2] <= 0:
            continue
        pts = [(20 + (x - lo[0]) * scale, height - 20 - (y - lo[1]) * scale) for x, y in xy[i]]
        c = tuple(int(min(255, ch * shade[i])) for ch in cols[i])
        d.polygon(pts, fill=c)
    img.save(out)
    print("wrote", out, f"{width}x{height}", "scale", round(scale, 2), "px/mm")


if __name__ == "__main__":
    args = sys.argv[1:]
    out = args.pop(0)
    view = "iso"; width = 1600
    if "--view" in args:
        i = args.index("--view"); view = args[i + 1]; del args[i:i + 2]
    if "--width" in args:
        i = args.index("--width"); width = int(args[i + 1]); del args[i:i + 2]
    parts = []
    for a in args:
        path, _, col = a.partition(":")
        color = tuple(int(x) for x in col.split(",")) if col else (225, 215, 190)
        parts.append((load(path), color))
    render(parts, out, view, width)
