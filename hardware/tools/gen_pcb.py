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

import project as _project

PRJ = _project.current()
OUT = PRJ.pcb
PLACEMENT = PRJ.dir / "placement.json"
ORIGIN = (20.0, 20.0)  # board top-left on the sheet
CORNER_R = 3.0


def layout_brain():
    """Brain board v4 (C24): eight bay slots along the rear edge, the CM5 on the RIGHT edge with its antenna
    edge out (so the CM5's USB 3 / PCIe row faces the hubs behind the slots), DIN / USB-C / microSD on the
    LEFT wall, M.2 socket front-left with the module lying along the front, bucks in the middle."""
    W, H = 150.0, 122.0
    L = dict(BOARD_W=W, BOARD_H=H, HOLES=[(4, 4), (4, H - 4), (140, H - 4), (140, 4)],
             ANTENNA_STRIP=(142, 57, 150, 100), SLOT_PITCH=14.5, SLOT_X0=12.0)
    R = {
        "bay-slots": (122, 8, 136, 30),      # the eight LED resistors (LEDs and slots are fixed)
        "usb3-hub-A": (45, 37, 60, 52),      # hub QFN anchored at (38, 44); passives to its right
        "usb3-hub-B": (103, 37, 118, 52),    # hub QFN anchored at (96, 44)
        "power-bucks": (58, 57, 78, 93),
        "power-input": (80, 57, 93, 75),
        "cm5": (118, 100, 128, 122),         # CM5-sheet passives (SD switch, LED resistors)
        "m2-nvme": (58, 100, 68.5, 120),     # M.2 switch and 0402/0603 passives UNDER the SSD, between standoff holes
    }
    F = {
        "M1": (146.5, 95.0, 90),          # CM5 landscape on the right edge: module x 95-150, y 58.5-98.5, antenna edge at x = 150
        "U1": (38.0, 44.0, 0), "U2": (96.0, 44.0, 0),   # hubs right behind their four slots
        "J21": (0.3, 75.0, 90),           # DIN jack on the LEFT wall (face -x), body x 0-18, y 66-84
        "J5": (9.2, 58.0, 270),           # USB-C on the LEFT wall
        "J3": (12.0, 44.5, 270),          # microSD on the LEFT wall, card entry -x
        "J40": (132.0, 108.0, 0),         # fan header (optional fan)
        "SW1": (108.0, 101.1, 0),         # DIP under a lid slot, x 101.4-114.6, y 98.7-121.3
        "J41": (60.0, 96.5, 90),          # OLED header between the bucks and the SSD
        "L51": (97.0, 102.0, 0),          # M.2 3.3 V inductor (1.8 mm tall: not under the SSD)
        "C20": (86.5, 82.0, 0), "C21": (86.5, 94.0, 0),   # 12 V bulk caps below the input block
        "J50": (14.0, 108.0, 90),         # M.2 socket front-left, module runs toward +x under the lid (x 8-95)
        "D50": (3.5, 95.0, 0),            # M.2 LED and the three status LEDs down the left edge, front
        "D1": (3.5, 100.0, 0), "D2": (3.5, 105.0, 0), "D3": (3.5, 110.0, 0),
        "SW3": (143.9, 40.0, 90),         # lid microswitch, right-rear under the lid edge
        "BT1": (120.0, 78.0, 0),          # CR2032 holder on the BOTTOM under the CM5 (post-process flip)
        "J6": (100.0, 66.0, 0), "J7": (100.0, 78.0, 0),   # nRPIBOOT and UART headers, bottom side under the CM5
    }
    for n in range(8):
        x = L["SLOT_X0"] + n * L["SLOT_PITCH"]
        F[f"J1{n}"] = (x, 23.7, 90)        # bay slot n+1: socket length along y (card plane front-to-back), y 1-27
        F[f"D1{n}"] = (x, 32.0, 90)        # bay LED right in front of its slot
    L.update(REGIONS=R, FIXED=F, SPILL=(76, 100, 88, 120), BOTTOM={"BT1", "J6", "J7"},
             LABEL=f"brain-drain brain v4  {W:.0f}x{H:.0f}  rear edge = top")
    return L


def layout_card():
    """Bay card (C24): 40 x 40 mm, fingers on the bottom edge (into the brain's slot), the 22-pin SATA
    receptacle on the top edge (cables leave upward at the rear of the box), bridge QFN behind the
    receptacle's data pads, switch block below."""
    # The finger footprint carries its own Edge.Cuts: a 20.3 mm-wide tab that sticks out 8.4 mm below the
    # main body (edge at footprint y +3.45, main body edge at y -4.95, key notch between contacts 11/12).
    W, H = 40.0, 46.0
    J1 = (10.0, 42.55)                    # fingers: tab bottom at y 46, main body edge at y 37.6
    L = dict(BOARD_W=W, BOARD_H=H, HOLES=[], ANTENNA_STRIP=None,
             TAB=(J1[0] - 0.65, J1[0] + 19.65, J1[1] - 4.95))
    R = {"bridge": (2, 19.5, 38, 28), "bay-switch": (2, 29, 38, 36.5), "edge": (2, 37, 8, 37.5)}
    F = {
        "J2": (20.0, 4.5, 0),             # SATA 22-pin receptacle on the top edge (cable leaves upward)
        "U1": (28.0, 14.0, 90),           # bridge: SATA pins face the receptacle's data pads (its right end)
        "J1": (J1[0], J1[1], 0),          # PCIe x1 fingers, contacts x 10-29
    }
    L.update(REGIONS=R, FIXED=F, SPILL=(2, 12, 18, 19), BOTTOM=set(), LABEL=f"brain-drain bay card v1  {W:.0f}x{H:.0f}")
    return L


LAYOUT = layout_card() if PRJ.key == "card" else layout_brain()
BOARD_W, BOARD_H, HOLES, REGIONS, FIXED, SPILL, BOTTOM = (LAYOUT[k] for k in ("BOARD_W", "BOARD_H", "HOLES", "REGIONS", "FIXED", "SPILL", "BOTTOM"))
ANTENNA_STRIP = LAYOUT["ANTENNA_STRIP"]
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
    import pcbfix
    print("duplicate UUIDs replaced:", pcbfix.uniquify_uuids(OUT))


def main():
    sexp._counter[0] = 5000000
    d = design.build(PRJ.key)
    pin_net = d.pin_net()
    net_names = sorted(d.nets)
    nets = {n: i + 1 for i, n in enumerate(net_names)}
    saved = json.loads(PLACEMENT.read_text()) if PLACEMENT.exists() else {}
    ox, oy = ORIGIN
    body = []
    # outline with rounded corners
    r = CORNER_R
    W, H = BOARD_W, BOARD_H
    tab = LAYOUT.get("TAB")
    if tab:   # main body ends at the tab line; the finger footprint draws the tab's own edge
        tx0, tx1, ty = tab
        segs = [((r, 0), (W - r, 0)), ((W, r), (W, ty)), ((W, ty), (tx1, ty)), ((tx0, ty), (0, ty)), ((0, ty), (0, r))]
    else:
        segs = [((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r))]
    for (x1, y1), (x2, y2) in segs:
        body.append(["gr_line", ["start", sexp.fmt(ox + x1), sexp.fmt(oy + y1)], ["end", sexp.fmt(ox + x2), sexp.fmt(oy + y2)],
                     ["stroke", ["width", 0.1], ["type", "default"]], ["layer", Str("Edge.Cuts")], ["uuid", Str(new_uuid())]])
    corners = [((r, r), (r, 0), (0, r)), ((W - r, r), (W, r), (W - r, 0))]
    if not tab:
        corners += [((W - r, H - r), (W - r, H), (W, H - r)), ((r, H - r), (0, H - r), (r, H))]
    for (cx, cy), (sx, sy), (ex, ey) in corners:
        body.append(["gr_arc", ["start", sexp.fmt(ox + sx), sexp.fmt(oy + sy)],
                     ["mid", sexp.fmt(ox + cx + (sx - cx) * 0.7071 + (ex - cx) * 0.7071), sexp.fmt(oy + cy + (sy - cy) * 0.7071 + (ey - cy) * 0.7071)],
                     ["end", sexp.fmt(ox + ex), sexp.fmt(oy + ey)], ["stroke", ["width", 0.1], ["type", "default"]],
                     ["layer", Str("Edge.Cuts")], ["uuid", Str(new_uuid())]])
    body.append(["gr_text", Str(LAYOUT["LABEL"]), ["at", sexp.fmt(ox + 2), sexp.fmt(oy - 3), 0],
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
