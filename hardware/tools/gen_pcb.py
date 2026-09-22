"""Generate hardware/brain-drain.kicad_pcb: outline (C19), mounting holes, every footprint
placed in its region with nets attached, ready for routing in the GUI.

The layout is a starting arrangement, not a finished placement: connectors sit on
the rear edge at their final pitch, ICs sit in their region, passives are gridded
next to their sheet's ICs. Re-running overwrites the file; keep hand placement by
editing tools/placement.json (positions keyed by reference) — the generator reads it
and honours any reference it finds there.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import design
import kifp
import kilib
import sexp
from sexp import Str, new_uuid

HW = Path(__file__).resolve().parent.parent
OUT = HW / "brain-drain.kicad_pcb"
PLACEMENT = HW / "tools" / "placement.json"

BOARD_W, BOARD_H = 180.0, 110.0
ORIGIN = (20.0, 20.0)  # board top-left on the sheet
CORNER_R = 3.0
HOLES = [(4, 4), (BOARD_W - 4, 4), (4, BOARD_H - 4), (BOARD_W - 4, BOARD_H - 4)]  # CM5 brings its own four

# Regions (x0, y0, x1, y1) in board mm, y down from the rear edge (rear edge = y 0).
REGIONS = {
    "power-input": (0, 0, 22, 45),
    "power-bucks": (0, 45, 40, 80),
    "cm5": (100, 28, 120, 85),
    "usb3-hub-A": (60, 18, 90, 40),
    "usb3-hub-B": (120, 40, 150, 62),
    "bridge-1": (60, 8, 88, 18), "bridge-2": (90, 8, 118, 18), "bridge-3": (120, 8, 148, 18), "bridge-4": (150, 8, 178, 18),
    "bay-switch-1": (60, 18, 88, 27), "bay-switch-2": (90, 18, 118, 27), "bay-switch-3": (120, 18, 148, 27), "bay-switch-4": (150, 18, 178, 27),
    "m2-nvme": (120, 62, 178, 108),
}
# Fixed anchors: reference -> (x, y, rotation) in board mm
FIXED = {
    "J21": (12.0, 0.0, 0),            # DIN jack: face on the rear edge
    "J4": (34.0, 6.0, 0),             # RJ45
    "J5": (50.0, 3.0, 0),             # USB-C
    "J7": (56.0, 12.0, 90),           # UART header
    "J6": (52.0, 12.0, 90),           # nRPIBOOT
    "J10": (74.0, 3.0, 0), "J11": (104.0, 3.0, 0), "J12": (134.0, 3.0, 0), "J13": (164.0, 3.0, 0),   # SATA, 30 mm pitch
    "M1": (62.0, 80.0, 0),           # CM5: footprint origin is mounting hole MH1; module spans x 58.5-98.5, y 28.5-83.5
    "J50": (140.0, 97.0, 270),        # M.2 socket; the footprint extends toward local +y, rotated so the module runs toward -x
    "J3": (6.0, 92.0, 90),            # microSD on the left edge
    "J41": (100.0, 104.0, 0), "SW1": (60.0, 104.0, 0), "J40": (30.0, 100.0, 0),
    "D1": (110.0, 106.0, 0), "D2": (114.0, 106.0, 0), "D3": (118.0, 106.0, 0),
    "D10": (74.0, 24.0, 0), "D11": (104.0, 24.0, 0), "D12": (134.0, 24.0, 0), "D13": (164.0, 24.0, 0),
    "D50": (122.0, 106.0, 0), "SW3": (176.0, 90.0, 0), "BZ1": (20.0, 92.0, 0), "BT1": (48.0, 92.0, 0),
    "C20": (8.0, 30.0, 0), "C21": (16.0, 30.0, 0),
}
LAYERS = [(0, "F.Cu", "signal"), (1, "In1.Cu", "power"), (2, "In2.Cu", "power"), (31, "B.Cu", "signal"),
          (32, "B.Adhes", "user"), (33, "F.Adhes", "user"), (34, "B.Paste", "user"), (35, "F.Paste", "user"),
          (36, "B.SilkS", "user"), (37, "F.SilkS", "user"), (38, "B.Mask", "user"), (39, "F.Mask", "user"),
          (40, "Dwgs.User", "user"), (41, "Cmts.User", "user"), (44, "Edge.Cuts", "user"), (45, "Margin", "user"),
          (46, "B.CrtYd", "user"), (47, "F.CrtYd", "user"), (48, "B.Fab", "user"), (49, "F.Fab", "user")]

PLACEHOLDER_SIZES = {"brain-drain:SATA_22pin_Receptacle_RA": (27.5, 8.0)}


def footprint_node(comp: design.Comp):
    fp = comp.footprint
    try:
        node = kifp.load(fp)
    except (FileNotFoundError, ValueError):
        w, h = PLACEHOLDER_SIZES.get(fp, (5.0, 5.0))
        node = kifp.placeholder(fp, w, h, [p.number for p in comp.sym().pins])
    import copy
    node = copy.deepcopy(node)
    node[1] = Str(fp)
    return node


def set_props(node, comp: design.Comp, x, y, rot, nets: dict[str, int], pin_net):
    # position
    for i, c in enumerate(node):
        if isinstance(c, list) and c and c[0] == "at":
            node[i] = ["at", sexp.fmt(x), sexp.fmt(y), rot]
            break
    else:
        node.insert(4, ["at", sexp.fmt(x), sexp.fmt(y), rot])
    # reference / value
    for c in node:
        if isinstance(c, list) and c and c[0] == "property":
            if str(c[1]) == "Reference":
                c[2] = Str(comp.ref)
            elif str(c[1]) == "Value":
                c[2] = Str(comp.value)
    node.insert(4, ["uuid", Str(new_uuid())])
    # pad nets
    for p in sexp.find_all(node, "pad"):
        num = str(p[1])
        net = pin_net.get((comp.ref, num))
        for i, c in enumerate(list(p)):
            if isinstance(c, list) and c and c[0] == "net":
                p.remove(c)
        if net and num:
            p.append(["net", nets[net], Str(net)])
    return node


def main():
    sexp._counter[0] = 5000000
    d = design.build()
    pin_net = d.pin_net()
    net_names = sorted(d.nets)
    nets = {n: i + 1 for i, n in enumerate(net_names)}
    saved = json.loads(PLACEMENT.read_text()) if PLACEMENT.exists() else {}
    ox, oy = ORIGIN
    body = []
    # outline with rounded corners
    r = CORNER_R
    W, H = BOARD_W, BOARD_H
    segs = [((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r))]
    for (x1, y1), (x2, y2) in segs:
        body.append(["gr_line", ["start", sexp.fmt(ox + x1), sexp.fmt(oy + y1)], ["end", sexp.fmt(ox + x2), sexp.fmt(oy + y2)],
                     ["stroke", ["width", 0.1], ["type", "default"]], ["layer", Str("Edge.Cuts")], ["uuid", Str(new_uuid())]])
    for (cx, cy), (sx, sy), (ex, ey) in [((r, r), (r, 0), (0, r)), ((W - r, r), (W, r), (W - r, 0)),
                                         ((W - r, H - r), (W - r, H), (W, H - r)), ((r, H - r), (0, H - r), (r, H))]:
        body.append(["gr_arc", ["start", sexp.fmt(ox + sx), sexp.fmt(oy + sy)],
                     ["mid", sexp.fmt(ox + cx + (sx - cx) * 0.7071 + (ex - cx) * 0.7071), sexp.fmt(oy + cy + (sy - cy) * 0.7071 + (ey - cy) * 0.7071)],
                     ["end", sexp.fmt(ox + ex), sexp.fmt(oy + ey)], ["stroke", ["width", 0.1], ["type", "default"]],
                     ["layer", Str("Edge.Cuts")], ["uuid", Str(new_uuid())]])
    body.append(["gr_text", Str("brain-drain carrier v0  180x110  rear edge = top"), ["at", sexp.fmt(ox + 2), sexp.fmt(oy - 3), 0],
                 ["layer", Str("Cmts.User")], ["uuid", Str(new_uuid())], ["effects", ["font", ["size", 2, 2], ["thickness", 0.3]]]])
    # mounting holes
    for i, (hx, hy) in enumerate(HOLES, start=1):
        node = kifp.load("MountingHole:MountingHole_2.7mm_M2.5")
        import copy
        node = copy.deepcopy(node); node[1] = Str("MountingHole:MountingHole_2.7mm_M2.5")
        hc = design.Comp(f"H{i}", "MountingHole:MountingHole_2.7mm_M2.5", "M2.5", "cm5")
        body.append(set_props(node, hc, ox + hx, oy + hy, 0, nets, {}))
    # footprints
    cursors = {}
    placed = 0
    for comp in d.comps.values():
        node = footprint_node(comp)
        fx0, fy0, fx1, fy1 = kifp.bbox(node)
        w, h = (fx1 - fx0) + 1.0, (fy1 - fy0) + 1.0
        if comp.ref in saved:
            x, y, rot = saved[comp.ref]
        elif comp.ref in FIXED:
            x, y, rot = FIXED[comp.ref]
        else:
            rx0, ry0, rx1, ry1 = REGIONS[comp.sheet]
            cx, cy, rowh = cursors.get(comp.sheet, (rx0 + 1, ry0 + 1, 0.0))
            if cx + w > rx1 and cx > rx0 + 1:
                cx, cy, rowh = rx0 + 1, cy + rowh + 0.5, 0.0
            x, y, rot = cx + w / 2, cy + h / 2, 0
            cursors[comp.sheet] = (cx + w + 0.5, cy, max(rowh, h))
        body.append(set_props(node, comp, ox + x, oy + y, rot, nets, pin_net))
        placed += 1
    layers = ["layers"] + [[i, Str(n), k] for i, n, k in LAYERS]
    pcb = ["kicad_pcb", ["version", 20241229], ["generator", Str("brain-drain-gen_pcb")], ["generator_version", Str("9.0")],
           ["general", ["thickness", 1.6], ["legacy_teardrops", "no"]], ["paper", Str("A3")], layers,
           ["setup", ["pad_to_mask_clearance", 0], ["allow_soldermask_bridges_in_footprints", "no"],
            ["pcbplotparams", ["layerselection", "0x00000000_00000000_55555555_5755555555"], ["plot_on_all_layers_selection", "0x00000000_00000000_00000000_00000000"]]],
           ["net", 0, Str("")]] + [["net", i, Str(n)] for n, i in nets.items()] + body + [["embedded_fonts", "no"]]
    OUT.write_text(sexp.emit(pcb) + "\n")
    missing = sorted({c.footprint for c in d.comps.values() if not kifp.exists(c.footprint)})
    print(f"wrote {OUT.name}: {placed} footprints, {len(nets)} nets; placeholders for: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    sys.exit(main())
