"""3D proxy model of a board for the documentation renders: the board outline extruded to 1.6 mm plus a box for every
part body, coloured by kind. It is a visual aid (sizes come from the courtyards and a height table), not a mechanical
model; the real 3D models of the vendors' connectors (STEP files in hardware/ref/datasheets) are not used here.

Frame of the returned meshes ("right-handed board frame", the same frame the enclosure is modelled in):
    X = board width - x_kicad   (KiCad's top view has x right and y down, which is left-handed; mirroring x makes it
                                 right-handed, and it is exactly how the tray is modelled, see enclosure/README.md)
    Y = y_kicad                 (distance from the rear edge)
    Z = up, 0 at the top surface of the board; the substrate is z = -1.6 .. 0, bottom-side parts hang below it
Origin is the top-left corner of the board outline in KiCad's view.

    python3 hardware/tools/board_model.py [brain|card]      # prints a summary
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pcbnew

HW = Path(__file__).resolve().parent.parent
BOARDS = {"brain": HW / "brain-drain.kicad_pcb", "card": HW / "bay-card" / "bay-card.kicad_pcb"}
T = 1.6   # board thickness

# footprint name fragment -> (height above the board surface in mm, group). First match wins.
HEIGHTS = [
    ("PCIe_x1_Socket", 11.25, "connector"),          # Amphenol FCI 10018783, drawing 10018784
    ("SATA_22pin", 9.5, "connector"),                # Molex 47018-4001, drawing SD-47018-001 (9.5 REF)
    ("Kycon_KPJX", 11.0, "connector"),
    ("M2_Socket", 4.2, "connector"),                 # TE 2199230-4
    ("USB_C_Receptacle", 3.2, "connector"),
    ("microSD", 1.9, "connector"),
    ("PinHeader", 8.5, "connector"),
    ("FanPinHeader", 8.5, "connector"),
    ("SW_DIP", 7.5, "connector"),
    ("SW_PUSH", 5.0, "connector"),
    ("BatteryHolder", 5.2, "connector"),
    ("BUS_PCIexpress", 0.0, "connector"),            # card-edge fingers: no body
    ("CP_Elec", 10.5, "passive_tall"),
    ("LED_D3.0", 5.0, "led"),
    ("QFN", 0.9, "ic"), ("DFN", 0.9, "ic"), ("SOIC", 1.75, "ic"), ("SOT-23", 1.2, "ic"), ("TSOT", 0.9, "ic"),
    ("Texas_", 1.0, "ic"), ("Crystal", 0.9, "ic"),
    ("L_Taiyo-Yuden_NR-40", 1.8, "passive"), ("L_Taiyo-Yuden_NR-60", 3.0, "passive"),
    ("Fuse_", 2.0, "passive"), ("D_SMB", 2.3, "ic"), ("D_SOD", 1.1, "ic"),
    ("C_1210", 2.0, "passive"), ("C_0805", 1.3, "passive"), ("C_0603", 0.9, "passive"), ("C_0402", 0.55, "passive"),
    ("R_0603", 0.5, "resistor"), ("R_0402", 0.35, "resistor"),
]
COLORS = {                                       # RGB for the renderer
    "pcb": (36, 112, 62), "ic": (38, 38, 42), "passive": (196, 168, 120), "passive_tall": (60, 60, 66),
    "resistor": (44, 44, 48), "connector": (74, 78, 88), "led": (60, 120, 230), "module": (28, 96, 60),
    "cooler": (170, 174, 180), "gold": (214, 176, 70), "black": (28, 28, 30),
}


# ------------------------------------------------------------------ geometry helpers (right-handed, outward normals)
def box(x0, y0, z0, x1, y1, z1):
    """12 triangles of an axis-aligned box, counter-clockwise seen from outside."""
    p = lambda x, y, z: (x, y, z)
    v = [p(x0, y0, z0), p(x1, y0, z0), p(x1, y1, z0), p(x0, y1, z0), p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]   # bottom, top, -y, +x, +y, -x
    out = []
    for a, b, c, d in quads:
        out += [(v[a], v[b], v[c]), (v[a], v[c], v[d])]
    return np.array(out, dtype=float)


def _area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def triangulate(poly):
    """Ear clipping of a simple polygon (list of (x, y)); returns triangles as index triples, counter-clockwise."""
    n = len(poly)
    idx = list(range(n))
    if _area(poly) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        clipped = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                px, py = poly[j]
                d1 = (b[0] - a[0]) * (py - a[1]) - (b[1] - a[1]) * (px - a[0])
                d2 = (c[0] - b[0]) * (py - b[1]) - (c[1] - b[1]) * (px - b[0])
                d3 = (a[0] - c[0]) * (py - c[1]) - (a[1] - c[1]) * (px - c[0])
                if d1 >= 0 and d2 >= 0 and d3 >= 0:
                    inside = True
                    break
            if not inside:
                tris.append((i0, i1, i2)); idx.pop(k); clipped = True
                break
        if not clipped:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


def prism(poly, z0, z1):
    """Extrude a polygon (any orientation) between z0 and z1 with outward normals."""
    pts = list(poly)
    if _area(pts) < 0:
        pts.reverse()
    tris = []
    for a, b, c in triangulate(pts):
        tris.append(((*pts[a], z1), (*pts[b], z1), (*pts[c], z1)))
        tris.append(((*pts[a], z0), (*pts[c], z0), (*pts[b], z0)))
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        tris.append(((*p, z0), (*q, z0), (*q, z1)))
        tris.append(((*p, z0), (*q, z1), (*p, z1)))
    return np.array(tris, dtype=float)


def _rotated(x, y, rot):
    a = math.radians(rot)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


# ------------------------------------------------------------------ the model
def model(kind: str) -> dict:
    """Returns {"groups": {name: (N,3,3) triangles}, "size": (W, H)} for the brain or the card."""
    board = pcbnew.LoadBoard(str(BOARDS[kind]))
    poly = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(poly)
    ol = poly.COutline(0)
    pts = [(ol.CPoint(i).x / 1e6, ol.CPoint(i).y / 1e6) for i in range(ol.PointCount())]
    ox, oy = min(p[0] for p in pts), min(p[1] for p in pts)
    W = max(p[0] for p in pts) - ox
    H = max(p[1] for p in pts) - oy
    to_frame = lambda x, y: (W - (x - ox), y - oy)             # KiCad mm -> right-handed board frame
    outline = [to_frame(x, y) for x, y in pts]
    groups: dict[str, list] = {"pcb": [prism(outline, -T, 0.0)]}

    def add(group, arr):
        groups.setdefault(group, []).append(arr)

    for f in board.GetFootprints():
        name = str(f.GetFPID().GetLibItemName())
        flipped = f.IsFlipped()
        rot = f.GetOrientationDegrees()
        pos = f.GetPosition()
        if name.startswith("MountingHole"):
            cx, cy = to_frame(pos.x / 1e6, pos.y / 1e6)
            add("black", box(cx - 1.35, cy - 1.35, 0.01, cx + 1.35, cy + 1.35, 0.05))
            continue
        if name.startswith("Raspberry-Pi-5"):
            # module 55 x 40 centred 16.5 / -24 from the MH1 origin; on two 4 mm connectors; passive cooler on top
            dx, dy = _rotated(16.5, -24.0, rot)
            cx, cy = pos.x / 1e6 + dx, pos.y / 1e6 + dy
            w, h = (40.0, 55.0) if int(round(rot)) % 180 == 90 else (55.0, 40.0)
            X, Y = to_frame(cx, cy)
            add("module", box(X - w / 2, Y - h / 2, 4.0, X + w / 2, Y + h / 2, 5.6))
            add("connector", box(X - w / 2 + 2, Y - h / 2 + 2, 0.0, X + w / 2 - 2, Y - h / 2 + 8, 4.0))
            add("cooler", box(X - 16, Y - 12, 5.6, X + 16, Y + 12, 11.6))
            continue
        h, group = next(((hh, g) for frag, hh, g in HEIGHTS if frag in name), (1.0, "ic"))
        crt = f.GetCourtyard(pcbnew.B_CrtYd if flipped else pcbnew.F_CrtYd)
        bb = crt.BBox() if crt.OutlineCount() else f.GetBoundingBox(False)
        x0, y0, x1, y1 = bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6
        if h <= 0:
            continue
        if group == "led":
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            x0, x1, y0, y1 = cx - 1.5, cx + 1.5, cy - 1.5, cy + 1.5
        elif name.startswith(("PCIe", "SATA", "Kycon", "M2_", "SW_", "PinHeader", "FanPin", "USB_C", "microSD", "Battery", "CP_Elec")):
            x0, y0, x1, y1 = x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25
        else:
            x0, y0, x1, y1 = x0 + 0.1, y0 + 0.1, x1 - 0.1, y1 - 0.1
        (X0, Y0), (X1, Y1) = to_frame(x0, y0), to_frame(x1, y1)
        X0, X1 = sorted((X0, X1)); Y0, Y1 = sorted((Y0, Y1))
        if flipped:
            add(group, box(X0, Y0, -T - h, X1, Y1, -T))
        else:
            add(group, box(X0, Y0, 0.0, X1, Y1, h))
    # gold pads of the card-edge fingers, both sides
    if kind == "card":
        for f in board.GetFootprints():
            if str(f.GetFPID().GetLibItemName()).startswith("BUS_PCIexpress"):
                for p in f.Pads():
                    c = p.GetPosition(); s = p.GetSize()
                    cx, cy = to_frame(c.x / 1e6, c.y / 1e6)
                    z0, z1 = (0.0, 0.03) if p.IsOnLayer(pcbnew.F_Cu) else (-T - 0.03, -T)
                    add("gold", box(cx - s.x / 2e6, cy - s.y / 2e6, z0, cx + s.x / 2e6, cy + s.y / 2e6, z1))
    return {"groups": {k: np.concatenate(v) for k, v in groups.items()}, "size": (W, H)}


def place_card(mesh: np.ndarray, card_w: float, brain_w: float, slot_x: float) -> np.ndarray:
    """Card frame (right-handed, from model('card')) -> the brain's right-handed frame, standing in the slot whose
    contact centre is at KiCad x = slot_x (mm from the brain's left edge): the card's front (component) face looks
    toward +x of KiCad, its fingers A1 end 6 mm behind the front edge at the slot's first contact (y = 23.7), its top edge
    48.85 mm above the board, tab 8.4 mm down into the socket."""
    out = mesh.copy()
    Xc, Yc, Zc = mesh[..., 0], mesh[..., 1], mesh[..., 2]
    x_c = card_w - Xc                      # back to KiCad-like card coordinates
    out[..., 0] = brain_w - (slot_x + 0.8 + Zc)
    out[..., 1] = 29.7 - x_c
    out[..., 2] = 48.85 - Yc
    return out


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "brain"
    m = model(kind)
    print(kind, "size", m["size"], {k: len(v) for k, v in m["groups"].items()})
