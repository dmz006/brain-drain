"""Generate project footprints into hardware/lib/brain-drain.pretty.

Sources:
  Kycon_KPJX-4S-S   Kycon drawing KPJX-4S-S rev A17 (2022), "Recommended PCB Layout, bottom view"
  Texas_RPA0010A    TI TPS56637 datasheet, RPA0010A "Example board layout", pad rectangles measured
                    from the drawing at 228 px/mm with the 0.5 mm pin pitch as the scale reference
"""

from __future__ import annotations

import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "lib" / "brain-drain.pretty"


def u():
    return str(uuid.uuid4())


def header(name, descr, tags, attr):
    return [f'(footprint "{name}"', "\t(version 20241229)", '\t(generator "brain-drain-fpgen")', '\t(generator_version "9.0")',
            '\t(layer "F.Cu")', f'\t(descr "{descr}")', f'\t(tags "{tags}")', f"\t(attr {attr})"]


def text(kind, val, x, y, layer, size=1.0, hide=False):
    return (f'\t(property "{kind}" "{val}" (at {x} {y} 0) (layer "{layer}"){" (hide yes)" if hide else ""} '
            f'(uuid "{u()}") (effects (font (size {size} {size}) (thickness 0.15))))')


def line(x1, y1, x2, y2, layer, w=0.12):
    return f'\t(fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{u()}"))'


def rect(x1, y1, x2, y2, layer, w=0.05):
    return f'\t(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{u()}"))'


def circle(cx, cy, r, layer, w=0.12):
    return f'\t(fp_circle (center {cx} {cy}) (end {cx + r} {cy}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{u()}"))'


def smd(num, x, y, w, h, shape="roundrect", rr=0.25):
    extra = f" (roundrect_rratio {rr})" if shape == "roundrect" else ""
    return (f'\t(pad "{num}" smd {shape} (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask"){extra} '
            f'(uuid "{u()}"))')


def tht(num, x, y, dw, dh, pw, ph, shape="oval"):
    drill = f"(drill {dw})" if dh is None else f"(drill oval {dw} {dh})"
    return (f'\t(pad "{num}" thru_hole {shape} (at {x} {y}) (size {pw} {ph}) {drill} (layers "*.Cu" "*.Mask") '
            f'(remove_unused_layers no) (uuid "{u()}"))')


def npth(x, y, dw, dh=None):
    drill = f"(drill {dw})" if dh is None else f"(drill oval {dw} {dh})"
    size = f"(size {dw} {dw})" if dh is None else f"(size {dw} {dh})"
    return f'\t(pad "" np_thru_hole {"circle" if dh is None else "oval"} (at {x} {y}) {size} {drill} (layers "*.Cu" "*.Mask") (uuid "{u()}"))'


def write(name, lines):
    (OUT / f"{name}.kicad_mod").write_text("\n".join(lines + [")"]) + "\n")
    print("wrote", name)


def kycon_kpjx_4s_s():
    """Origin: the jack's front face line (Kycon 'reference' line), +y into the board (away from the panel).
    Kycon's layout is a BOTTOM view; x is mirrored here for the top view."""
    n = "Kycon_KPJX-4S-S"
    L = header(n, "Kycon KPJX-4S-S 4-pin DIN power jack, shielded, right angle, 7.5 A per pin (Kycon drawing A17)",
               "din power jack kycon kpjx", "through_hole")
    L.append(text("Reference", "REF**", 0, -2.5, "F.SilkS"))
    L.append(text("Value", n, 0, 19.5, "F.Fab"))
    L.append(text("Footprint", "", 0, 0, "F.Fab", hide=True))
    L.append(text("Datasheet", "https://www.kycon.com/Pub_Eng_Draw/KPJX-4S-S.pdf", 0, 0, "F.Fab", hide=True))
    L.append(text("Description", "", 0, 0, "F.Fab", hide=True))
    # signal pins: 0.6 x 2.7 rectangular legs -> oval drill 0.8 x 2.9, pad 1.5 x 3.3 (pitch is 3.65 mm)
    for num, x, y in ((1, 2.90, 14.65), (2, -2.90, 14.65), (3, 2.90, 11.00), (4, -2.90, 11.00)):
        L.append(tht(num, x, y, 0.8, 2.9, 1.5, 3.3))
    # shield: two 0.6 x 2.7 tabs at the rear corners and two round 1.7 mm legs
    for x, y in ((7.80, 16.00), (-7.80, 16.00)):
        L.append(tht(5, x, y, 0.8, 2.9, 1.5, 3.3))
    for x, y in ((2.50, 7.50), (-2.50, 7.50)):
        L.append(tht(5, x, y, 1.7, None, 2.5, 2.5, "circle"))
    # plastic locating pegs 2.2 mm and the 2.2 x 1.0 slot
    L.append(npth(7.80, 7.50, 2.3)); L.append(npth(-7.80, 7.50, 2.3))
    L.append(npth(0, 5.50, 1.1, 2.3))
    # body: 16.0 wide, 17.4 deep from the face line; rear of body at y = 17.4
    L.append(rect(-8.0, 0, 8.0, 17.4, "F.Fab", 0.1))
    L.append(rect(-8.3, -0.3, 8.3, 17.7, "F.CrtYd", 0.05))
    L.append(line(-8.0, 17.4, 8.0, 17.4, "F.SilkS")); L.append(line(-8.0, 0.0, -8.0, 17.4, "F.SilkS")); L.append(line(8.0, 0.0, 8.0, 17.4, "F.SilkS"))
    L.append(line(-8.0, 0.0, -1.5, 0.0, "F.SilkS")); L.append(line(1.5, 0.0, 8.0, 0.0, "F.SilkS"))
    L.append(text("User", "face / board edge", 0, -1.0, "F.Fab", 0.7))
    write(n, L)


def texas_rpa0010a(fingers):
    """TI RPA0010A (TPS56637) land pattern. Coordinates in mm, KiCad y-down (drawing y-up negated)."""
    n = "Texas_RPA0010A_VQFN-HR-10_3x3mm"
    L = header(n, "TI VQFN-HR 10-pin HotRod 3x3 mm (RPA0010A), land pattern from TPS56637 datasheet example board layout",
               "vqfn hotrod rpa0010a tps56637", "smd")
    L.append(text("Reference", "REF**", 0, -2.5, "F.SilkS"))
    L.append(text("Value", n, 0, 2.7, "F.Fab"))
    L.append(text("Footprint", "", 0, 0, "F.Fab", hide=True))
    L.append(text("Datasheet", "https://www.ti.com/lit/ds/symlink/tps56637.pdf", 0, 0, "F.Fab", hide=True))
    L.append(text("Description", "", 0, 0, "F.Fab", hide=True))
    # pins 1-4: 0.65 x 0.25 at x = -1.40, rows +0.75 .. -0.75 (drawing y up)
    for i, yy in enumerate((0.75, 0.25, -0.25, -0.75), start=1):
        L.append(smd(i, -1.40, -yy, 0.65, 0.25))
    L.append(smd(5, -0.93, 1.40, 0.25, 0.60))       # bottom-left
    L.append(smd(10, -0.93, -1.40, 0.25, 0.60))     # top-left
    L.append(smd(7, 0.87, 1.40, 0.25, 0.60))        # BOOT bottom-right
    L.append(smd(6, -0.20, -0.65, 0.40, 2.10))      # SW: x -0.40..0, y +1.71..-0.41 (drawing) -> center (-0.2, +0.65)
    L.append(smd(9, 0.37, 0.85, 0.25, 1.70))        # PGND: y 0..-1.7 (drawing) -> center +0.85 down
    # VIN pad 8: body plus fingers toward the right
    L.append(smd(8, 0.95, -0.65, 0.40, 2.10))       # body x +0.75..+1.15
    for y0, y1 in fingers:                          # drawing-y ranges of the fingers
        L.append(smd(8, 1.43, -(y0 + y1) / 2, 0.56, round(y0 - y1, 2)))
    L.append(rect(-1.5, -1.5, 1.5, 1.5, "F.Fab", 0.1))
    L.append(rect(-2.0, -2.0, 2.0, 2.0, "F.CrtYd", 0.05))
    L.append(circle(-1.9, -1.9, 0.15, "F.SilkS", 0.2))  # pin 1 marker top-left (pin 1 is the upper of the left column)
    write(n, L)


if __name__ == "__main__":
    import json
    import sys
    OUT.mkdir(exist_ok=True)
    kycon_kpjx_4s_s()
    fingers = json.loads(sys.argv[1]) if len(sys.argv) > 1 else [(0.50, 0.25), (0.0, -0.25), (-0.50, -0.75)]
    texas_rpa0010a(fingers)
