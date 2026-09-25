"""Headless 3D renderer for the documentation images (numpy + Pillow, no GPU, no display).

Painter's algorithm over triangles with two-light Lambert shading, 2x supersampling, a soft ground shadow and an
optional caption. Meshes are (N, 3, 3) arrays of triangles in a right-handed frame with z up, outward normals
counter-clockwise (what OpenSCAD writes and hardware/tools/board_model.py builds).

    from render3d import render, load
    render([(load("stl/tray.stl"), (60, 64, 72))], "out.png", az=-30, el=35, caption="tray")

View: `az` turns the scene about z (0 = looking toward +y from the -y side, the rear of the unit), `el` is the
camera elevation above the horizon (90 = plan view). With az = 180, el = 90 a board is seen as KiCad shows it
(rear edge at the top, x to the right).
"""
from __future__ import annotations

import re
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def load(path):
    """Binary or ASCII STL -> (N, 3, 3) float array."""
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        v = np.array([list(map(float, m.groups())) for m in re.finditer(rb"vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)", data)])
        return v.reshape(-1, 3, 3)
    n = struct.unpack("<I", data[80:84])[0]
    arr = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return arr["v"].reshape(-1, 3, 3).astype(float)


def rx(a):
    a = np.radians(a)
    return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])


def rz(a):
    a = np.radians(a)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


def view_matrix(az, el):
    """World -> camera: camera looks down -z', image x = x', image up = y'."""
    return rx(el - 90) @ rz(az)


def subdivide(tris, max_edge=10.0, rounds=5):
    """Split large triangles so the per-triangle depth sort has no big faces that cover small parts."""
    for _ in range(rounds):
        e = np.max(np.linalg.norm(tris - np.roll(tris, -1, axis=1), axis=2), axis=1)
        big = e > max_edge
        if not big.any():
            break
        t = tris[big]
        m01, m12, m20 = (t[:, 0] + t[:, 1]) / 2, (t[:, 1] + t[:, 2]) / 2, (t[:, 2] + t[:, 0]) / 2
        quads = [np.stack([t[:, 0], m01, m20], 1), np.stack([m01, t[:, 1], m12], 1),
                 np.stack([m20, m12, t[:, 2]], 1), np.stack([m01, m12, m20], 1)]
        tris = np.concatenate([tris[~big]] + quads)
    return tris


def clip_mesh(tris, axis, value, keep_below=True):
    """Cut a triangle mesh at the plane coordinate[axis] == value, keeping the side below (or above) it; triangles that
    cross the plane are split (Sutherland-Hodgman). The cut is left open (no cap)."""
    sign = 1.0 if keep_below else -1.0
    d = sign * (tris[:, :, axis] - value)               # <= 0: kept side
    inside = d <= 0
    n_in = inside.sum(axis=1)
    keep = tris[n_in == 3]
    out = [keep]
    for tri, di in zip(tris[(n_in > 0) & (n_in < 3)], d[(n_in > 0) & (n_in < 3)]):
        poly = []
        for k in range(3):
            a, b = tri[k], tri[(k + 1) % 3]
            da, db = di[k], di[(k + 1) % 3]
            if da <= 0:
                poly.append(a)
            if (da <= 0) != (db <= 0):
                t = da / (da - db)
                poly.append(a + t * (b - a))
        for k in range(1, len(poly) - 1):
            out.append(np.array([[poly[0], poly[k], poly[k + 1]]]))
    return np.concatenate(out) if len(out) > 1 else keep


def _font(size):
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Regular.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def transform(tris, matrix=None, offset=(0, 0, 0)):
    out = tris if matrix is None else tris @ np.asarray(matrix).T
    return out + np.asarray(offset, dtype=float)


def render(parts, out, az=-30.0, el=35.0, width=1800, ss=2, caption=None, shadow=True, clip=None, max_edge=10.0, shadow_parts=None):
    """parts: [(triangles, (r, g, b)), ...]. clip: optional (axis, value, keep_below) dropping triangles whose centroid
    is beyond a plane (cut-away views)."""
    R = view_matrix(az, el)
    tris_l, cols_l = [], []
    for t, c in parts:
        if clip is not None:
            axis, val, keep_below = clip
            t = clip_mesh(t, axis, val, keep_below)
        if len(t) == 0:
            continue
        t = subdivide(t, max_edge)
        tris_l.append(t); cols_l.append(np.repeat([c], len(t), axis=0))
    tris = np.concatenate(tris_l); cols = np.concatenate(cols_l).astype(float)
    p = tris @ R.T
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    nn = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
    key = np.array([-0.45, 0.55, 0.70]); key /= np.linalg.norm(key)
    fill = np.array([0.65, 0.15, 0.45]); fill /= np.linalg.norm(fill)
    shade = 0.32 + 0.62 * np.clip(nn @ key, 0, 1) + 0.22 * np.clip(nn @ fill, 0, 1)
    wz = tris[:, :, 2].mean(1)
    shade = shade * (1.0 + 0.010 * np.clip(wz, 0, 18) * (nn[:, 2] > 0.5))   # taller top faces a little brighter: depth cue in plan views
    order = np.argsort(p[:, :, 2].mean(1))
    xy = p[:, :, :2]
    lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
    pad = 0.04 * max(hi - lo) + 1.0
    lo, hi = lo - pad, hi + pad + np.array([0.0, 0.0])
    W = int(width * ss); scale = W / (hi[0] - lo[0])
    H = int((hi[1] - lo[1]) * scale) + int(28 * ss if caption else 0)
    base = Image.new("RGB", (W, H))
    bd = ImageDraw.Draw(base)
    for y in range(H):   # soft studio background
        t = y / max(1, H - 1)
        c = tuple(int(v) for v in (244 - 22 * t, 245 - 22 * t, 248 - 20 * t))
        bd.line([(0, y), (W, y)], fill=c)
    top_px = H - (int(28 * ss) if caption else 0)
    if shadow:
        wp = tris.reshape(-1, 3)
        zmin = wp[:, 2].min()
        sh = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(sh)
        sel = [parts[i][0] for i in shadow_parts] if shadow_parts is not None else [wp.reshape(-1, 3, 3)]
        for t in sel:
            q = t.reshape(-1, 3)
            x0, y0 = q[:, 0].min(), q[:, 1].min(); x1, y1 = q[:, 0].max(), q[:, 1].max()
            corners = np.array([[x0, y0, zmin], [x1, y0, zmin], [x1, y1, zmin], [x0, y1, zmin]]) @ R.T
            sd.polygon([((c[0] - lo[0]) * scale, top_px - (c[1] - lo[1]) * scale) for c in corners], fill=95)
        sh = sh.filter(ImageFilter.GaussianBlur(radius=8 * ss))
        base = Image.composite(Image.new("RGB", (W, H), (120, 122, 130)), base, sh)
    d = ImageDraw.Draw(base)
    top = H - (int(28 * ss) if caption else 0)
    for i in order:
        if nn[i, 2] <= 0:
            continue
        pts = [((x - lo[0]) * scale, top - (y - lo[1]) * scale) for x, y in xy[i]]
        c = tuple(int(min(255, ch * shade[i])) for ch in cols[i])
        d.polygon(pts, fill=c, outline=c)
    img = base.resize((W // ss, H // ss), Image.LANCZOS)
    if caption:
        ImageDraw.Draw(img).text((14, img.size[1] - 24), caption, fill=(50, 56, 66), font=_font(15))
    img.save(out)
    print("wrote", out, f"{img.size[0]}x{img.size[1]}")
    return img
