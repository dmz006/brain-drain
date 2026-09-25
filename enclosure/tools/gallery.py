"""Renders every documentation image of the boards, the assembled electronics, the case and the complete unit.

    python3 enclosure/tools/gallery.py [boards|electronics|case|unit|all]

Output goes to docs/img/renders/. Needs: the enclosure STLs (make -C enclosure), the routed boards, pcbnew, numpy, Pillow.
The scenes are composed here from the STLs of the case and the board models of hardware/tools/board_model.py.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hardware" / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import board_model as bm      # noqa: E402
from render3d import load, render, transform    # noqa: E402

OUT = ROOT / "docs" / "img" / "renders"
STL = ROOT / "enclosure" / "stl"
CASE = {"tray": (64, 68, 78), "lid": (86, 92, 104), "cable": (196, 46, 46), "drive": (150, 154, 162), "brick": (34, 34, 38),
        "ssd": (44, 70, 128), "cable_dark": (60, 60, 64)}


def params() -> dict:
    """Numeric assignments of enclosure/params.scad and board.scad (in order, so later lines can use earlier ones)."""
    env: dict = {"pow": pow}
    for name in ("board.scad", "params.scad"):
        for line in (ROOT / "enclosure" / name).read_text().splitlines():
            m = re.match(r"^\s*([a-z_0-9]+)\s*=\s*([^;\[]+?);", line)
            if m and "include" not in line:
                try:
                    env[m.group(1)] = eval(m.group(2), {"__builtins__": {}}, env)
                except Exception:      # noqa: BLE001
                    pass
    env["tray_height"] = env["floor_t"] + env["below_board"] + env["board_t"] + env["above_board"]
    env["z_board_top"] = env["floor_t"] + env["below_board"] + env["board_t"]
    return env


P = params()


# ------------------------------------------------------------------ meshes
def colored(model: dict) -> list:
    return [(t, bm.COLORS[g]) for g, t in model["groups"].items()]


def m2_ssd() -> np.ndarray:
    """A 2280 M.2 module lying in the socket, reaching toward the middle of the board (front-left of the brain)."""
    # socket J50 at KiCad (14, 108) rotated 90: the module runs toward +x_kicad, 80 x 22 mm, 4.2..5.9 mm above the board
    W = 150.0
    x_k0, x_k1, y_c = 12.0, 92.0, 108.0
    return bm.box(W - x_k1, y_c - 11.0, 4.2, W - x_k0, y_c + 11.0, 5.9)


def brain_parts(ssd=False) -> list:
    return colored(bm.model("brain")) + ([(m2_ssd(), CASE["ssd"])] if ssd else [])


def electronics(populated=(0, 1, 2, 3), ssd=True) -> list:
    """The brain with bay cards standing in the given slots (0-7), in the brain's right-handed frame."""
    brain = bm.model("brain")
    card = bm.model("card")
    Wb, Wc = brain["size"][0], card["size"][0]
    parts = colored(brain)
    if ssd:
        parts.append((m2_ssd(), CASE["ssd"]))
    for n in populated:
        slot_x = 12.0 + 14.5 * n
        for g, t in card["groups"].items():
            parts.append((bm.place_card(t, Wc, Wb, slot_x), bm.COLORS[g]))
    return parts


def at_board(parts, dz=0.0):
    """Move board-frame parts into the tray frame (inside the case)."""
    off = (P["wall"] + P["clear"], P["wall"] + P["clear"] + P["rear_ext"], P["z_board_top"] + dz)
    return [(transform(t, None, off), c) for t, c in parts]


def lid_closed(t):
    v = t.copy()
    v[..., 1] = P["outer_h"] - t[..., 1]
    v[..., 2] = P["tray_height"] + P["lid_t"] - t[..., 2]
    return v


def lid_open(t, angle=72.0, dz=0.0):
    v = lid_closed(t)
    yh, zh = -P["hinge_knuckle_d"] / 2, P["tray_height"]
    y, z = v[..., 1] - yh, v[..., 2] - zh
    a = math.radians(angle)
    out = v.copy()
    out[..., 1] = yh + y * math.cos(a) - z * math.sin(a)
    out[..., 2] = zh + y * math.sin(a) + z * math.cos(a) + dz
    return out


def brick():
    """12 V desktop brick, 170 x 70 x 38, at the far end of the power cable."""
    return bm.box(0, 0, 0, 170, 70, 38)


# ------------------------------------------------------------------ image sets
def boards():
    OUT.mkdir(parents=True, exist_ok=True)
    b = brain_parts()
    render(b, OUT / "brain-top.png", az=180, el=90, caption="Brain board, top side (150 x 122 mm, 6 layers): eight bay slots at the rear, CM5 on the right edge")
    render(b, OUT / "brain-iso-front.png", az=145, el=38, caption="Brain board from the front left")
    render(b, OUT / "brain-iso-rear.png", az=-35, el=36, caption="Brain board from the rear: the eight PCIe x1 bay slots")
    render(b, OUT / "brain-bottom.png", az=0, el=-90, caption="Brain board, bottom side: hub bypass capacitors, CR2032 holder, service headers")
    c = colored(bm.model("card"))
    render(c, OUT / "card-front.png", az=180, el=90, caption="Bay card, component side (45 x 46 mm, 4 layers): SATA receptacle on the top edge, PCIe x1 fingers below")
    render(c, OUT / "card-iso.png", az=150, el=38, caption="Bay card from the front")
    render(c, OUT / "card-back.png", az=0, el=-90, caption="Bay card, back side: gold fingers on both sides")


def electronics_images():
    OUT.mkdir(parents=True, exist_ok=True)
    e = electronics()
    render(e, OUT / "electronics-iso.png", az=-38, el=30, caption="Brain with four bay cards fitted (slots 1-4), M.2 SSD in the front left socket")
    render(e, OUT / "electronics-iso-front.png", az=145, el=32, caption="Same, from the front left: cards stand in the slots, the LEDs sit in front of them")
    render(e, OUT / "electronics-top.png", az=180, el=90, caption="Plan view: the 45 mm cards overhang the rear edge of the brain by 15 mm")
    render(e, OUT / "electronics-side.png", az=90, el=0, caption="Side view: card top edge 48.9 mm above the board, receptacles facing the next slot")
    full = electronics(populated=range(8))
    render(full, OUT / "electronics-full8.png", az=-38, el=30, caption="Fully expanded: eight bay cards")


def case_images():
    OUT.mkdir(parents=True, exist_ok=True)
    tray = load(STL / "tray.stl"); lid = load(STL / "lid.stl")
    render([(tray, CASE["tray"])], OUT / "case-tray-iso.png", az=-38, el=34, caption="Tray: standoffs for the brain, vent slots on the right and rear, connector cutouts on the left wall")
    render([(tray, CASE["tray"])], OUT / "case-tray-top.png", az=180, el=90, caption="Tray from above (rear at the top): 16 mm extra depth behind the board for the card overhang")
    render([(lid_closed(lid), CASE["lid"])], OUT / "case-lid-outside.png", az=-38, el=34, caption="Lid, outside: eight receptacle windows, LED holes, OLED window, DIP slot, CM5 grille")
    lid_flat = lid.copy()
    render([(lid_flat, CASE["lid"])], OUT / "case-lid-inside.png", az=0, el=90, caption="Lid, inside (printed face down)")
    bezel = load(STL / "bezel.stl")
    render([(bezel, (46, 46, 52))], OUT / "case-bezel.png", az=-30, el=38, width=1200, caption="OLED bezel: clamps the 0.96 inch module under the lid window")
    unit = [(tray, CASE["tray"]), (lid_closed(lid), CASE["lid"])]
    render(unit, OUT / "case-closed-iso.png", az=-38, el=30, caption="Closed unit from the rear left")
    render(unit, OUT / "case-closed-front.png", az=145, el=30, caption="Closed unit from the front right: latch and vents")
    render(unit, OUT / "case-closed-top.png", az=180, el=90, caption="Closed unit from above")
    o = electronics()
    opened = [(tray, CASE["tray"]), (lid_open(lid), CASE["lid"])] + at_board(o)
    render(opened, OUT / "unit-open.png", az=-32, el=26, caption="Lid open: brain and four bay cards inside the tray", width=1900)
    render(opened, OUT / "unit-open-front.png", az=150, el=30, caption="Lid open, from the front", width=1900)
    render([(tray, CASE["tray"])] + at_board(o), OUT / "unit-no-lid.png", az=-38, el=36, caption="Lid removed")
    exploded = [(tray, CASE["tray"])] + at_board(o, dz=38) + [(lid_closed(lid) + np.array([0, 0, 120]), CASE["lid"])]
    render(exploded, OUT / "unit-exploded.png", az=-32, el=22, caption="Exploded: tray, brain with cards, lid", width=1900)
    render([(tray, CASE["tray"]), (lid_closed(lid), CASE["lid"])] + at_board(o), OUT / "unit-cutaway.png", az=150, el=26,
           clip=(1, P["outer_h"] * 0.55, True), caption="Cut-away through the unit behind the middle (front part removed): cards, sockets and the rear overhang", width=1900)


def unit_images():
    OUT.mkdir(parents=True, exist_ok=True)
    tray = load(STL / "tray.stl"); lid = load(STL / "lid.stl")
    cables = load(STL / "scene_cables.stl"); drives = load(STL / "scene_drives.stl")
    o = electronics()
    # brick where the power cable ends
    end = np.array([P["outer_w"] + 240, P["wall"] + P["clear"] + P["rear_ext"] + 75 + 120, 4.0])
    br = transform(brick(), None, end + np.array([-10, -35, 0]))
    scene = [(tray, CASE["tray"]), (lid_closed(lid), CASE["lid"]), (cables, CASE["cable"]), (drives, CASE["drive"]), (br, CASE["brick"])]
    render(scene, OUT / "system-iso.png", az=-38, el=32, width=2000, shadow_parts=[0, 3, 4], caption="Complete system: unit, four drives on 0.5 m 22-pin cables, 12 V brick")
    render(scene, OUT / "system-top.png", az=180, el=90, width=2000, shadow_parts=[0, 3, 4], caption="Complete system from above")
    render(scene, OUT / "system-front.png", az=145, el=30, width=2000, shadow_parts=[0, 3, 4], caption="Complete system from the front right")
    inside = [(tray, CASE["tray"]), (lid_open(lid), CASE["lid"]), (cables, CASE["cable"]), (drives, CASE["drive"]), (br, CASE["brick"])] + at_board(o)
    render(inside, OUT / "system-open.png", az=-32, el=30, width=2000, shadow_parts=[0, 3, 4], caption="Complete system with the lid open")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("boards", "all"):
        boards()
    if which in ("electronics", "all"):
        electronics_images()
    if which in ("case", "all"):
        case_images()
    if which in ("unit", "all"):
        unit_images()
