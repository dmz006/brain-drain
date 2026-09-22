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

BOARD_W, BOARD_H = 136.0, 100.0   # C22: brain box with a hinged lid, no Ethernet, CM5 antenna on the left edge
ORIGIN = (20.0, 20.0)  # board top-left on the sheet
CORNER_R = 3.0
# Two board holes plus the CM5's four standoffs and the M.2 standoff. The rear-right corner holds the
# lid switch, the front-left the M.2 socket and the front-right the DIN jack, so the holes are
# rear-left and front-centre-right (between the DIP switch and the DIN).
HOLES = [(4, 4), (113, BOARD_H - 4)]

# Regions (x0, y0, x1, y1) in board mm, y down from the rear edge (rear edge = y 0).
# Regions are sized so the parts fit (checked at generation time; ~1.6x the summed part area).
# Rows from the rear: SATA receptacles y 0-9 at 28.9 mm pitch, bridges 9-22.5, bay switches 22.5-32.5.
# CM5 (landscape, antenna edge on the LEFT board edge) x 0-55, y 34-74; hubs x 56-79; bucks and input
# x 80-116; right wall (x = 136): USB-C, microSD, fan header, DIN 12 V. M.2 socket front-left, the 2280
# module lies along the front (x 8-95, y 75.5-98.5) under the hinged lid. Front-right: DIP switch.
ANTENNA_STRIP = (0, 33, 8, 75)   # no copper on any layer, no parts on either side (CM5 datasheet 4.1.2)
BAY_PITCH = 28.9   # 27.94 mm pad span + 0.7 mm pad + 0.15 mm clearance
BAY_X0 = 22.0
REGIONS = {
    "power-input": (101, 34, 116, 53),
    "power-bucks": (80, 34, 99, 69),
    "cm5": (57.5, 78, 70, 96),          # CM5-sheet passives (SD switch, LED resistors) UNDER the SSD too (all < 1.5 mm)
    "usb3-hub-A": (66, 34, 79, 52),     # hub QFN anchored at (61, 43); passives pack to its right
    "usb3-hub-B": (66, 54, 79, 72),     # hub QFN anchored at (61, 63)
    "m2-nvme": (24, 78, 40, 96),        # M.2 switch and 0402/0603 passives UNDER the SSD (max 1.5 mm tall; L51 is fixed elsewhere)
    # the packed regions under the SSD sit between the socket's 2242/2260/2280 standoff holes (x 42.3, 54.3, 72.3, 92.3)
}
for _b in range(4):
    _x = BAY_X0 + _b * BAY_PITCH
    REGIONS[f"bridge-{_b + 1}"] = (_x - 1, 9.3, _x + 13.5, 22.5)       # right of the bridge QFN at (_x - 6, 15.5)
    REGIONS[f"bay-switch-{_b + 1}"] = (_x - 8, 22.5, _x + 15, 32.5)   # right of the bay LED at (_x - 12, 27.5)
SPILL = (74, 78, 90, 96)   # under the SSD: anything that does not fit its region lands here and is reported
# Fixed anchors: reference -> (x, y, rotation) in board mm
FIXED = {
    "M1": (3.5, 37.5, 270),           # CM5 landscape, MH1 (antenna) edge on the left board edge: module x 0-55, y 34-74
    "U1": (61.0, 43.0, 90), "U2": (61.0, 63.0, 90),   # hubs: rot 90 turns the upstream pins toward the CM5
    "J21": (135.7, 90.5, 270),        # DIN jack on the RIGHT wall (face +x), body x 118-136, y 82-99: all cables leave rear/right
    "J5": (126.8, 45.0, 90),          # USB-C on the RIGHT wall (face +x)
    "J3": (127.0, 62.0, 90),          # microSD on the RIGHT wall, card entry +x
    "J40": (126.6, 75.5, 0),          # fan header (kept for an optional fan; passive cooler by default)
    "SW1": (99.1, 79.0, 0),           # DIP under a lid slot, x 95.5-108.7, y 76.6-99.2
    "J41": (72.0, 73.5, 90),          # OLED header between the hubs and the M.2 module
    "L51": (92.0, 72.0, 0),           # M.2 3.3 V inductor (1.8 mm tall: not under the SSD)
    "C20": (108.5, 59.5, 0), "C21": (108.5, 71.0, 0),   # 12 V bulk caps below the input block
    "J50": (14.0, 87.0, 90),          # M.2 socket front-left, module runs toward +x under the lid
    "D50": (3.5, 79.0, 0),            # M.2 LED and the three status LEDs down the left edge
    "D1": (3.5, 84.0, 0), "D2": (3.5, 89.0, 0), "D3": (3.5, 94.0, 0),
    "SW3": (129.9, 16.0, 90),         # lid microswitch, rear-right corner under the lid edge
    # bottom side under the CM5 module, clear of its connector pads (x 13.5-36.5) and the antenna strip
    "BT1": (28.0, 58.0, 0),           # CR2032 holder (post-process flip)
    "J6": (48.5, 46.0, 0), "J7": (48.5, 58.0, 0),     # nRPIBOOT and UART headers, bottom side (service only)
}
for _b in range(4):
    _x = BAY_X0 + _b * BAY_PITCH
    FIXED[f"J1{_b}"] = (_x, 4.5, 0)                 # SATA 22-pin receptacle on the rear edge
    # bridges: QFN-48 pins 25-36 (SATA) on the right side at rot 0 -> rot 90 turns them to face the rear
    # receptacle; USB pins (13-24, bottom) then face right, toward the hubs
    FIXED[f"U1{_b}"] = (_x - 6, 15.5, 90)
    FIXED[f"D1{_b}"] = (_x - 12, 27.5, 0)           # bay LED at the start of the bay switch row
BOTTOM = {"BT1", "J6", "J7"}   # footprints flipped to B.Cu after generation (pcbnew post-process)
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
    # pad nets; pad angles are stored absolute in KiCad files, so add the footprint rotation
    for p in sexp.find_all(node, "pad"):
        num = str(p[1])
        at = sexp.find(p, "at")
        if at is not None and rot:
            ang = float(at[3]) if len(at) > 3 else 0.0
            while len(at) > 3:
                at.pop()
            at.append(sexp.fmt((ang + rot) % 360))
        net = pin_net.get((comp.ref, num))
        for i, c in enumerate(list(p)):
            if isinstance(c, list) and c and c[0] == "net":
                p.remove(c)
        if net and num:
            p.append(["net", nets[net], Str(net)])
    return node


def flip_bottom():
    """Move the BOTTOM set to B.Cu (mirrors pads and layers; pcbnew does it right, the emitter does not)."""
    if not BOTTOM:
        return
    import pcbnew
    board = pcbnew.LoadBoard(str(OUT))
    for ref in BOTTOM:
        f = board.FindFootprintByReference(ref)
        if f and not f.IsFlipped():
            f.Flip(f.GetPosition(), False)
    pcbnew.SaveBoard(str(OUT), board)


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
    body.append(["gr_text", Str("brain-drain carrier v2  136x100  rear edge = top"), ["at", sexp.fmt(ox + 2), sexp.fmt(oy - 3), 0],
                 ["layer", Str("Cmts.User")], ["uuid", Str(new_uuid())], ["effects", ["font", ["size", 2, 2], ["thickness", 0.3]]]])
    # mounting holes
    for i, (hx, hy) in enumerate(HOLES, start=1):
        node = kifp.load("MountingHole:MountingHole_2.7mm_M2.5")
        import copy
        node = copy.deepcopy(node); node[1] = Str("MountingHole:MountingHole_2.7mm_M2.5")
        hc = design.Comp(f"H{i}", "MountingHole:MountingHole_2.7mm_M2.5", "M2.5", "cm5")
        body.append(set_props(node, hc, ox + hx, oy + hy, 0, nets, {}))
    # footprints
    placed = 0
    spilled = []
    # group the free parts per region, largest first, and shelf-pack them
    groups: dict[str, list] = {}
    fixed_items = []
    GAP = 0.4
    for comp in d.comps.values():
        node = footprint_node(comp)
        fx0, fy0, fx1, fy1 = kifp.bbox(node)
        w, h = (fx1 - fx0) + GAP, (fy1 - fy0) + GAP
        if comp.ref in saved or comp.ref in FIXED:
            fixed_items.append((comp, node, fx0, fy0))
        else:
            groups.setdefault(comp.sheet, []).append((comp, node, w, h, fx0, fy0))
    for comp, node, fx0, fy0 in fixed_items:
        x, y, rot = saved.get(comp.ref, FIXED.get(comp.ref))
        body.append(set_props(node, comp, ox + x, oy + y, rot, nets, pin_net)); placed += 1
    spill_cursor = [SPILL[0], SPILL[1], 0.0]
    for sheet, items in groups.items():
        items.sort(key=lambda t: (-t[3], -t[2], t[0].ref))
        rx0, ry0, rx1, ry1 = REGIONS[sheet]
        cx, cy, rowh = rx0, ry0, 0.0
        for comp, node, w, h, fx0, fy0 in items:
            if cx + w > rx1 and cx > rx0:
                cx, cy, rowh = rx0, cy + rowh, 0.0
            if cy + h > ry1:  # region full: spill
                sx, sy, srowh = spill_cursor
                if sx + w > SPILL[2]:
                    sx, sy, srowh = SPILL[0], sy + srowh, 0.0
                x, y = sx - fx0, sy - fy0
                spill_cursor = [sx + w, sy, max(srowh, h)]
                spilled.append((comp.ref, sheet))
            else:
                x, y = cx - fx0, cy - fy0   # place so the footprint's bbox corner sits at the cursor
                cx, rowh = cx + w, max(rowh, h)
            body.append(set_props(node, comp, ox + x, oy + y, 0, nets, pin_net)); placed += 1
    if spilled:
        print(f"WARNING: {len(spilled)} parts did not fit their region and were placed in the spill area: "
              + ", ".join(f"{r}({s})" for r, s in spilled[:20]))
    layers = ["layers"] + [[i, Str(n), k] for i, n, k in LAYERS]
    pcb = ["kicad_pcb", ["version", 20241229], ["generator", Str("brain-drain-gen_pcb")], ["generator_version", Str("9.0")],
           ["general", ["thickness", 1.6], ["legacy_teardrops", "no"]], ["paper", Str("A3")], layers,
           ["setup", ["pad_to_mask_clearance", 0], ["allow_soldermask_bridges_in_footprints", "no"],
            ["pcbplotparams", ["layerselection", "0x00000000_00000000_55555555_5755555555"], ["plot_on_all_layers_selection", "0x00000000_00000000_00000000_00000000"]]],
           ["net", 0, Str("")]] + [["net", i, Str(n)] for n, i in nets.items()] + body + [["embedded_fonts", "no"]]
    OUT.write_text(sexp.emit(pcb) + "\n")
    flip_bottom()
    missing = sorted({c.footprint for c in d.comps.values() if not kifp.exists(c.footprint)})
    print(f"wrote {OUT.name}: {placed} footprints, {len(nets)} nets; placeholders for: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    sys.exit(main())
