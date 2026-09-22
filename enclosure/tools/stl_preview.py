"""Headless STL preview: painter's-algorithm render to PNG (numpy + Pillow only).
    python3 tools/stl_preview.py stl/tray.stl out.png [--view top|iso|bottom]
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


def render(tris, out, view="iso", size=(1600, 1000)):
    if view == "top":
        R = np.eye(3)
    elif view == "bottom":
        R = np.diag([1, -1, -1.0])
    else:  # isometric-ish: tilt 35 deg about x after 30 deg about z
        a, b = np.radians(-30), np.radians(60)
        Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
        R = Rx @ Rz
    p = tris @ R.T
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    nn = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    light = np.array([0.3, 0.5, 0.8]); light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(nn @ light, 0, 1)
    depth = p[:, :, 2].mean(1)
    order = np.argsort(depth)
    xy = p[:, :, :2]
    lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
    scale = min((size[0] - 40) / (hi[0] - lo[0] + 1e-9), (size[1] - 40) / (hi[1] - lo[1] + 1e-9))
    img = Image.new("RGB", size, (245, 245, 240))
    d = ImageDraw.Draw(img)
    for i in order:
        if nn[i, 2] <= 0:
            continue  # back faces
        pts = [(20 + (x - lo[0]) * scale, size[1] - 20 - (y - lo[1]) * scale) for x, y in xy[i]]
        c = int(60 + 170 * shade[i])
        d.polygon(pts, fill=(c, c - 10, c - 30))
    img.save(out)
    print("wrote", out, "scale", round(scale, 2), "px/mm")


if __name__ == "__main__":
    view = sys.argv[sys.argv.index("--view") + 1] if "--view" in sys.argv else "iso"
    render(load(sys.argv[1]), sys.argv[2], view)
