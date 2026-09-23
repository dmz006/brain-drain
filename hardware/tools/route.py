"""Routing pipeline on KiCad's pcbnew API (KiCad 9):

  python3 tools/route.py prepare   net classes, diff-pair rules, copper zones -> brain-drain.kicad_pcb
  python3 tools/route.py dsn       export Specctra DSN (full and "lite": no diff pairs, no bay nets)
  python3 tools/route.py import    import the freerouting session, strip bay-net tracks, fill zones, DRC
  python3 tools/route.py fanout    via + stub beside every SMD pad on a net that has a copper plane
  python3 tools/route.py all       prepare + fanout + dsn + freerouting + import

Bay nets (anything touching the bridge-* and bay-switch-* sheets) are removed
after import: their routing is redone once the real SATA footprint lands.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pcbnew

import design

HW = Path(__file__).resolve().parent.parent
PCB = HW / "brain-drain.kicad_pcb"
DSN = HW / "routing" / "brain-drain.dsn"
SES = HW / "routing" / "brain-drain.ses"
JAR = next(iter(sorted((HW / "tools" / "freerouting").glob("freerouting-2.1.0.jar"))), None)

MM = pcbnew.FromMM

POWER_NETS = {"+12V", "5V_SYS", "5V_HDD", "+3V3", "3V3_M2", "3V3_M2_SW", "+1V2", "VIN_12V_RAW", "VIN_12V_FUSED", "GND", "SD_VDD"}
BAY_SHEETS = {f"bridge-{i}" for i in range(1, 5)} | {f"bay-switch-{i}" for i in range(1, 5)}


def bay_nets(d: design.Design) -> set[str]:
    out = set()
    for net, pins in d.nets.items():
        if any(d.sheet_of_pin(r, n) in BAY_SHEETS for r, n in pins):
            out.add(net)
    return out - POWER_NETS


def diff_pair_nets(d: design.Design) -> set[str]:
    out = set()
    for net in d.nets:
        if net.endswith(("_P", "_N", "DP", "DM", "TXDP", "TXDM", "RXDP", "RXDM", "_TXP", "_TXN", "_RXP", "_RXN", "XP", "XN")):
            out.add(net)
    return out


# Rules follow the Raspberry Pi CM5IO reference design (0.13 mm tracks, 0.125 mm clearance, 0.45/0.2 mm
# vias, 90 ohm pairs 0.147/0.253) so the 0.4 mm-pitch CM5 connector and the 0.5 mm M.2 socket can escape.
# name: (track width, clearance, diff-pair gap or None, via diameter, via drill) in mm
NETCLASSES = {
    "Default": (0.13, 0.125, None, 0.45, 0.2),
    "Power": (0.3, 0.125, None, 0.6, 0.3),         # 0.3: a 0.5 track cannot leave a 0.65 mm-pitch DFN pin; planes carry the current
    "DiffPair90": (0.147, 0.125, 0.253, 0.45, 0.2),   # of two classes, the router only knows its own
    "Bay": (0.2, 0.125, None, 0.45, 0.2),
}
MIN_RULES = {"min_clearance": 0.125, "min_track_width": 0.1, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2,
             "min_via_annular_width": 0.1, "min_copper_edge_clearance": 0.3}


def write_project_netclasses(assignments: dict[str, str]) -> None:
    """Net classes live in the .kicad_pro, not the board: kicad-cli DRC and the DSN export read them from
    there, and gen_sch.py rewrites the project. So prepare() writes them into the project file itself."""
    import json
    pro = HW / "brain-drain.kicad_pro"
    data = json.loads(pro.read_text()) if pro.exists() else {}
    classes = []
    for name, (w, c, gap, vd, vh) in NETCLASSES.items():
        entry = {"name": name, "clearance": c, "track_width": w, "via_diameter": vd, "via_drill": vh,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "bus_width": 12, "wire_width": 6,
                 "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                 "priority": 2147483647 if name == "Default" else list(NETCLASSES).index(name)}
        if gap:
            entry["diff_pair_width"] = w; entry["diff_pair_gap"] = gap; entry["diff_pair_via_gap"] = 0.25
        classes.append(entry)
    data["net_settings"] = {"classes": classes, "meta": {"version": 4},
                            "netclass_assignments": None,
                            "netclass_patterns": [{"netclass": cls, "pattern": net} for net, cls in sorted(assignments.items())]}
    rules = data.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
    rules.update(MIN_RULES)
    pro.write_text(json.dumps(data, indent=2) + "\n")
    print(f"project net classes written: {len(classes)} classes, {len(assignments)} patterns; min rules {MIN_RULES}")


def prepare(board: pcbnew.BOARD, d: design.Design) -> None:
    ds = board.GetDesignSettings()
    ds.m_SolderMaskMinWidth = 0
    ds.m_SolderMaskExpansion = MM(0.05)
    bays = bay_nets(d)
    pairs = diff_pair_nets(d)
    assignments = {}
    for net in d.nets:
        if net in POWER_NETS or net.startswith(("12V_BAY", "5V_BAY")):
            assignments[net] = "Power"
        elif net in pairs:
            assignments[net] = "DiffPair90"
        elif net in bays:
            assignments[net] = "Bay"
    import json
    pro = HW / "brain-drain.kicad_pro"
    have = {c.get("name") for c in json.loads(pro.read_text()).get("net_settings", {}).get("classes", [])} if pro.exists() else set()
    if set(NETCLASSES) <= have:
        # the board was loaded with the classes from the project: touching them again through the API
        # corrupts NET_SETTINGS (zone filler bad_alloc, untyped SWIG proxies), so only refresh the file
        write_project_netclasses(assignments)
        print(f"net classes come from the project file ({len(assignments)} patterns)")
        return _zones(board, d)
    ncs = ds.m_NetSettings  # NET_SETTINGS
    # net classes
    w, c, _, vd, vh = NETCLASSES["Default"]
    nc_default = ncs.GetDefaultNetclass()
    nc_default.SetTrackWidth(MM(w)); nc_default.SetClearance(MM(c))
    nc_default.SetViaDiameter(MM(vd)); nc_default.SetViaDrill(MM(vh))
    for name, (width, clearance, gap, vd, vh) in NETCLASSES.items():
        if name == "Default":
            continue
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(MM(width)); nc.SetClearance(MM(clearance))
        nc.SetViaDiameter(MM(vd)); nc.SetViaDrill(MM(vh))
        if gap:
            nc.SetDiffPairWidth(MM(width)); nc.SetDiffPairGap(MM(gap))
        ncs.SetNetclass(name, nc)
    ds.m_MinClearance = MM(MIN_RULES["min_clearance"]); ds.m_TrackMinWidth = MM(MIN_RULES["min_track_width"])
    ds.m_ViasMinSize = MM(MIN_RULES["min_via_diameter"]); ds.m_MinThroughDrill = MM(MIN_RULES["min_through_hole_diameter"])
    for net, cls in assignments.items():
        ncs.SetNetclassPatternAssignment(net, cls)
    write_project_netclasses(assignments)
    print(f"net classes set through the API; {len(assignments)} nets assigned")
    return _zones(board, d)


def _zones(board: pcbnew.BOARD, d: design.Design) -> None:
    codes = {n: board.FindNet(n).GetNetCode() for n in ("GND", "5V_SYS", "5V_HDD", "+3V3", "+12V")}
    # copper zones: GND on In1, power islands on In2, GND on B.Cu. Only on a board that has none yet
    # (gen_pcb.py writes none): removing filled zones that fanout vias connect to corrupts the
    # Python bindings for the rest of the process, so prepare() never deletes zones.
    if any(not z.GetIsRuleArea() for z in board.Zones()):
        print("zones already present; net classes refreshed, zones left as they are")
        return
    import gen_pcb
    ox, oy = gen_pcb.ORIGIN
    W, H = gen_pcb.BOARD_W, gen_pcb.BOARD_H
    def zone(net_name, layer, rect, priority=0):
        net = codes[net_name]
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNetCode(net)
        z.SetAssignedPriority(priority)
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        if len(rect) == 4:   # rectangle
            x0, y0, x1, y1 = rect
            rect = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pts = [pcbnew.VECTOR2I(MM(ox + x), MM(oy + y)) for x, y in rect]   # polygon
        outline = z.Outline()
        outline.RemoveAllContours()
        outline.NewOutline()
        for p in pts:
            outline.Append(p.x, p.y)
        z.SetZoneName(f"{net_name}_{pcbnew.LayerName(layer)}")
        board.Add(z)
        return z

    zone("GND", pcbnew.In1_Cu, (0, 0, W, H))
    zone("GND", pcbnew.B_Cu, (0, 0, W, H))
    # In2 power islands for the 150x112 layout (gen_pcb.py REGIONS); a higher priority island wins overlaps
    zone("5V_SYS", pcbnew.In2_Cu, [(0, 0), (126, 0), (126, 38), (150, 38), (150, 62), (100, 62), (100, 80), (56, 80), (56, 112), (0, 112), (0, 38)], 1)
    zone("5V_HDD", pcbnew.In2_Cu, (0, 9, 126, 23), 2)          # bay switch blocks
    zone("+3V3", pcbnew.In2_Cu, (8, 82, 56, 112), 2)           # hub corner
    zone("+12V", pcbnew.In2_Cu, (56, 39, 100, 80), 3)          # buck column, input block, bulk caps
    # CM5 antenna strip: no copper on any layer, nothing routed (CM5 datasheet 4.1.2)
    ax0, ay0, ax1, ay1 = gen_pcb.ANTENNA_STRIP
    ka = pcbnew.ZONE(board)
    ka.SetIsRuleArea(True); ka.SetDoNotAllowTracks(True); ka.SetDoNotAllowVias(True)
    ka.SetDoNotAllowCopperPour(True); ka.SetDoNotAllowPads(False); ka.SetDoNotAllowFootprints(True)   # the CM5 standoff holes sit in the strip
    ka.SetLayer(pcbnew.F_Cu); ka.SetLayerSet(pcbnew.LSET.AllCuMask(4))
    o = ka.Outline(); o.RemoveAllContours(); o.NewOutline()
    for x, y in ((ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1)):
        o.Append(MM(ox + x), MM(oy + y))
    ka.SetZoneName("keepout_CM5_antenna")
    board.Add(ka)
    # keep-out areas (no tracks / vias) around the CM5 mounting holes: the DSN export carries no
    # hole clearance, so without these the autorouter runs traces under the standoffs
    m1 = next((f for f in board.GetFootprints() if f.GetReference() == "M1"), None)
    if m1 is not None:
        for pad in m1.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = pad.GetPosition()
                z = pcbnew.ZONE(board)
                z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
                z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
                z.SetLayer(pcbnew.F_Cu); z.SetLayerSet(pcbnew.LSET.AllCuMask(4))
                import math
                r = MM(1.35 + 1.7)   # hole radius + the footprint's 1.7 mm hole clearance
                o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
                for k in range(24):
                    a = 2 * math.pi * k / 24
                    o.Append(int(c.x + r * math.cos(a)), int(c.y + r * math.sin(a)))
                z.SetZoneName("keepout_CM5_hole")
                board.Add(z)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print("zones and keep-outs created and filled")


class Occupancy:
    """Geometry-aware collision check for fanout vias and stubs: pads by their bounding box, tracks by
    segment distance (a diagonal track's bounding box would block a whole square), vias by centre."""

    def __init__(self, board: pcbnew.BOARD, clearance: float = 0.125):
        self.clr = MM(clearance)
        self.boxes = [pad.GetBoundingBox() for f in board.GetFootprints() for pad in f.Pads()]
        self.segs = []   # (SEG, half width)
        self.vias = []   # (x, y, radius)
        for t in board.GetTracks():
            self.add(t)

    def add(self, t) -> None:
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); self.vias.append((int(p.x), int(p.y), t.GetWidth(pcbnew.F_Cu) // 2))
        else:
            self.segs.append((pcbnew.SEG(t.GetStart(), t.GetEnd()), t.GetWidth() // 2))

    def add_box(self, box) -> None:
        self.boxes.append(box)

    def point_free(self, x: int, y: int, r: int, own) -> bool:
        """A disc of radius r at (x, y) clears everything except copper that touches one of `own`."""
        pt = pcbnew.VECTOR2I(x, y)
        for b in self.boxes:
            if b.Intersects(pcbnew.BOX2I(pcbnew.VECTOR2I(x - r - self.clr, y - r - self.clr), pcbnew.VECTOR2I(2 * (r + self.clr), 2 * (r + self.clr)))):
                if not any(b.Contains(pcbnew.VECTOR2I(*o)) for o in own):
                    return False
        for seg, hw in self.segs:
            if seg.Distance(pt) < r + hw + self.clr:
                if not any(seg.Distance(pcbnew.VECTOR2I(*o)) <= hw + 10 for o in own):
                    return False
        for vx, vy, vr in self.vias:
            if (vx - x) ** 2 + (vy - y) ** 2 < (r + vr + self.clr) ** 2:
                if not any((vx - o[0]) ** 2 + (vy - o[1]) ** 2 <= (vr + 10) ** 2 for o in own):
                    return False
        return True

    def path_free(self, p1, p2, hw: int, own) -> bool:
        n = max(2, int(((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5 / MM(0.1)))
        return all(self.point_free(p1[0] + (p2[0] - p1[0]) * k // n, p1[1] + (p2[1] - p1[1]) * k // n, hw, own) for k in range(n + 1))


def fanout(board: pcbnew.BOARD) -> None:
    """Drop a via and a short stub next to every open SMD pad of a small part (8 pads or fewer) whose net
    has a copper zone, so the inner/back planes reach it. Tries 8 directions at 4 distances with a
    geometry-aware collision check; skips the pad (reported) when nothing fits."""
    import math
    zones_by_net = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        zones_by_net.setdefault(z.GetNetname(), []).append(z)
    open_pads = open_pads_from_drc(board)
    done_pads = connected_pads(board) if open_pads is None else None
    via_d, via_drill, stub_w = MM(0.45), MM(0.2), MM(0.13)
    occ = Occupancy(board)
    placed = skipped = 0
    for f in board.GetFootprints():
        fc = f.GetPosition()
        if len(list(f.Pads())) > 8:
            continue   # ICs and connectors: fanout_big / fanout_conn
        layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        for pad in f.Pads():
            net = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or net not in zones_by_net:
                continue
            key = (f.GetReference(), str(pad.GetNumber()))
            if (open_pads is not None and key not in open_pads) or (open_pads is None and key in done_pads):
                continue
            if not any(z.Outline().Contains(pad.GetPosition()) for z in zones_by_net[net]):
                continue
            ppos = pad.GetPosition(); px, py = int(ppos.x), int(ppos.y)
            half = max(pad_size(pad)) / 2
            base = math.atan2(py - int(fc.y), px - int(fc.x))
            done = False
            for extra in (0.35, 0.75, 1.15, 1.6):
                dist = half + via_d / 2 + MM(extra)
                for k in (0, 1, -1, 2, 0.5, -0.5, 1.5, -1.5):
                    a = base + k * math.pi / 2
                    vx, vy = int(px + dist * math.cos(a)), int(py + dist * math.sin(a))
                    if not occ.point_free(vx, vy, via_d // 2, [(px, py)]) or not occ.path_free((px, py), (vx, vy), stub_w // 2, [(px, py)]):
                        continue
                    if not any(z.Outline().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]):
                        continue
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(via_d); v.SetDrill(via_drill)
                    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    v.SetNetCode(pad.GetNetCode()); board.Add(v); occ.add(v)
                    tr = pcbnew.PCB_TRACK(board)
                    tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                    tr.SetWidth(stub_w); tr.SetLayer(layer)
                    tr.SetNetCode(pad.GetNetCode()); board.Add(tr); occ.add(tr)
                    placed += 1; done = True
                    break
                if done:
                    break
            if not done:
                skipped += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"fanout: {placed} vias placed, {skipped} pads skipped (no free spot)")


def connected_pads(board: pcbnew.BOARD) -> set:
    """(reference, pad number) of every pad that DRC would call connected: pads touching a track, a via or
    a filled zone of their net. Uses the board connectivity after a zone fill."""
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    plane_nets = {z.GetNetname() for z in board.Zones() if not z.GetIsRuleArea()}
    out = set()
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetCode() <= 0:
                continue
            tht = pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            if len(conn.GetConnectedTracks(pad)) or (tht and pad.GetNetname() in plane_nets):
                out.add((f.GetReference(), pad.GetNumber()))
    return out


def fanout_big(board: pcbnew.BOARD, dogbones: bool = False) -> None:
    """Plane vias for the parts the first fanout skips (more than 8 pads): vias inside the exposed pads
    of the QFNs (always safe: the pad is the only copper there). The dog-bone variant for connector pins
    is kept behind a flag: on 0.4/0.5 mm pitch it collides with neighbours far too often (464 clearance
    errors in a dry run), and the router does that job with real geometry checks."""
    import math
    zones_by_net = {}
    for z in board.Zones():
        if not z.GetIsRuleArea():
            zones_by_net.setdefault(z.GetNetname(), []).append(z)
    done_pads = connected_pads(board)
    via_d, via_drill, stub_w = MM(0.6), MM(0.3), MM(0.25)
    occupied = [pad.GetBoundingBox() for f in board.GetFootprints() for pad in f.Pads()]
    occupied += [t.GetBoundingBox() for t in board.GetTracks()]

    def free(vx, vy, own_pad):
        box = pcbnew.BOX2I(pcbnew.VECTOR2I(vx - via_d // 2 - MM(0.15), vy - via_d // 2 - MM(0.15)),
                           pcbnew.VECTOR2I(via_d + 2 * MM(0.15), via_d + 2 * MM(0.15)))
        return not any(o.Intersects(box) and not o.Contains(pcbnew.VECTOR2I(*own_pad)) for o in occupied)

    def add_via(vx, vy, net, layer):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(via_d); v.SetDrill(via_drill)
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(net); board.Add(v); occupied.append(v.GetBoundingBox())
        return v

    placed = skipped = 0
    for f in board.GetFootprints():
        pads = list(f.Pads())
        if len(pads) <= 8:
            continue
        layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        fc = f.GetPosition(); fcx, fcy = int(fc.x), int(fc.y)
        for i, pad in enumerate(pads):
            net = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or net not in zones_by_net:
                continue
            if (f.GetReference(), pad.GetNumber()) in done_pads:
                continue
            if not any(z.Outline().Contains(pad.GetPosition()) for z in zones_by_net[net]):
                continue
            ppos = pad.GetPosition(); px, py = int(ppos.x), int(ppos.y)
            sz = pad.GetSize(); sx, sy = int(sz.x), int(sz.y)
            sx, sy = pad_size(pad)
            if min(sx, sy) >= MM(1.2):   # exposed pad (or a quarter of a split one): vias inside it, 1 mm grid
                nx, ny = max(1, int((sx - MM(1.0)) // MM(1.0))), max(1, int((sy - MM(1.0)) // MM(1.0)))
                nx, ny = min(nx, 3), min(ny, 3)
                for ix in range(nx):
                    for iy in range(ny):
                        vx = px - (nx - 1) * MM(0.5) + ix * MM(1.0)
                        vy = py - (ny - 1) * MM(0.5) + iy * MM(1.0)
                        add_via(int(vx), int(vy), pad.GetNetCode(), layer); placed += 1
                continue
            if not dogbones:
                skipped += 1
                continue
            base = math.atan2(py - fcy, px - fcx)
            half = max(sx, sy) / 2
            ok = False
            for k, dist_mm in ((0, 0.9), (0, 1.6), (2, 0.9), (2, 1.6), (1, 1.0), (-1, 1.0)):
                if i % 2 == 1 and k in (0, 2):   # stagger neighbours: odd pads try the far spot first
                    dist_mm = 2.5 - dist_mm
                a = base + k * math.pi / 2
                dist = half + via_d / 2 + MM(dist_mm)
                vx, vy = int(px + dist * math.cos(a)), int(py + dist * math.sin(a))
                if not free(vx, vy, (px, py)):
                    continue
                if not any(z.Outline().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]):
                    continue
                add_via(vx, vy, pad.GetNetCode(), layer)
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                tr.SetWidth(stub_w); tr.SetLayer(layer); tr.SetNetCode(pad.GetNetCode()); board.Add(tr)
                occupied.append(tr.GetBoundingBox())
                placed += 1; ok = True
                break
            if not ok:
                skipped += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"fanout_big: {placed} vias placed, {skipped} plane pads skipped (no free spot)")


def export_dsn(board: pcbnew.BOARD) -> None:
    DSN.parent.mkdir(exist_ok=True)
    ok = pcbnew.ExportSpecctraDSN(board, str(DSN))
    print("DSN export", "ok" if ok else "FAILED", DSN.relative_to(HW))


LITE_DSN = HW / "routing" / "brain-drain-lite.dsn"
LITE_SES = HW / "routing" / "brain-drain-lite.ses"


MAX_PASSES = 60   # freerouting 2.1.0 stops at pass 999 (hard-coded) and ignores -mp: start_pass_no in the DSN bounds a run


def bound_passes(text: str, max_passes: int = MAX_PASSES) -> str:
    """Insert (autoroute_settings (start_pass_no 999-max)) into the structure section. Kept for reference:
    the headless job flow of 2.1.0 ignores it (passes still count from 1), so runs are bounded only by
    the router's own history exhaustion, about 600 passes after its last improvement."""
    start = max(1, 999 - max_passes)
    i = text.index("(structure")
    j = text.index("\n", i)
    return text[:j + 1] + f"    (autoroute_settings (start_pass_no {start}))\n" + text[j + 1:]


def filter_dsn(d: design.Design, drop: set[str] | None = None) -> None:
    """Write a DSN containing only the single-ended, non-bay nets: power, control, GPIO, I2C.

    Differential pairs and the four bay sheets are left for hand routing, so the
    autorouter gets a problem it can finish. Textual filter: the DSN's
    (string_quote ") directive defeats a generic s-expression parser."""
    text = DSN.read_text()
    skip = drop if drop is not None else (
        bay_nets(d) | diff_pair_nets(d) | POWER_NETS | {n for n in d.nets if n.startswith(('12V_BAY', '5V_BAY'))})

    def block_end(i):  # index just past the balanced block starting at text[i] == "("
        depth = 0; j = i; inq = False
        while j < len(text):
            c = text[j]
            if c == '"':
                inq = not inq
            elif not inq:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        return j + 1
            j += 1
        return j

    def name_at(i):  # token after "(net " or "(class "
        j = i
        while text[j] not in " \n":
            j += 1
        j += 1
        if text[j] == '"':
            k = text.index('"', j + 1); return text[j + 1:k]
        k = j
        while text[k] not in " \n)":
            k += 1
        return text[j:k]

    out = []; pos = 0; kept = dropped = 0
    import re
    for m in re.finditer(r"\n(\s*)\((net|class) ", text):
        i = m.start() + 1 + len(m.group(1))
        if i < pos:
            continue
        j = block_end(i)
        kind = m.group(2)
        if kind == "net":
            if name_at(i) in skip:
                out.append(text[pos:m.start() + 1]); pos = j; dropped += 1
                # swallow the newline that followed the block
                if pos < len(text) and text[pos] == "\n":
                    pos += 1
            else:
                kept += 1
        else:
            blk = text[i:j]
            for name in skip:
                blk = re.sub(r'(?<=[\s(])"?' + re.escape(name) + r'"?(?=[\s)])', "", blk)
            out.append(text[pos:i]); out.append(blk); pos = j
    out.append(text[pos:])
    LITE_DSN.write_text("".join(out))
    print(f"lite DSN: kept {kept} nets, dropped {dropped} (diff pairs, bay nets, power nets carried by zones) -> {LITE_DSN.relative_to(HW)}")


def run_freerouting(passes: int = 30, ignore_classes: tuple[str, ...] = ()) -> int:
    """Route the lite DSN (single-ended, non-bay nets). The optimizer loops forever without -oit;
    -mp is ignored by 2.1.0 but kept for newer builds."""
    import os
    # BD_ROUTER=2.4.1 picks the newer jar (needs Java 25; honours -mp and writes its session on the cap, but
    # each pass takes minutes and it leaves some clearance violations for the DRC cleanup); default 2.1.0
    ver = os.environ.get("BD_ROUTER", "2.1.0")
    jar = HW / "tools" / "freerouting" / f"freerouting-{ver}.jar"
    java = "/usr/lib/jvm/java-25-openjdk-amd64/bin/java" if ver != "2.1.0" else "java"
    passes = int(os.environ.get("BD_PASSES", passes))
    if not jar.exists():
        print(f"no {jar.name} in tools/freerouting/"); return 1
    LITE_SES.unlink(missing_ok=True)
    cmd = [java, "-Djava.awt.headless=true", "-jar", str(jar), "-de", str(LITE_DSN), "-do", str(LITE_SES),
           "-mp", str(passes), "-oit", "2"]
    if ignore_classes:   # route only the other classes; nets are never dropped from a DSN that has their wiring
        cmd += ["-inc", ",".join(ignore_classes)]
    print(" ".join(cmd))
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=6 * 3600, stdin=subprocess.DEVNULL)
    (HW / "routing" / "freerouting-lite.log").write_text(cp.stdout + cp.stderr)
    print("freerouting rc", cp.returncode, "->", LITE_SES.exists())
    return cp.returncode


def import_ses(board: pcbnew.BOARD, d: design.Design) -> None:
    ses = LITE_SES if LITE_SES.exists() else SES
    ok = pcbnew.ImportSpecctraSES(board, str(ses))
    print("SES import", "ok" if ok else "FAILED")
    for t in board.GetTracks():   # routes were locked for the export so the router kept them; free them again
        t.SetLocked(False)
    # the DSN carries no rule areas, so the router may cross the CM5 standoff and antenna keep-outs:
    # drop those segments and report their nets for hand routing
    areas = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
    cleared = {}
    for t in list(board.GetTracks()):
        hit = False
        for z in areas:
            outline = z.Outline()
            if t.GetClass() == "PCB_VIA":
                hit = outline.Collide(t.GetPosition(), t.GetWidth(pcbnew.F_Cu) // 2)
            else:
                hit = outline.Collide(pcbnew.SEG(t.GetStart(), t.GetEnd()), t.GetWidth() // 2)
            if hit:
                break
        if hit:
            cleared[t.GetNetname()] = cleared.get(t.GetNetname(), 0) + 1
            board.Remove(t)
    if cleared:
        print(f"removed {sum(cleared.values())} segments/vias crossing keep-outs; hand-route: {', '.join(sorted(cleared))}")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def stats(board: pcbnew.BOARD) -> None:
    tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    length = sum(t.GetLength() for t in tracks) / 1e6
    print(f"tracks {len(tracks)} ({length:.0f} mm), vias {len(vias)}, zones {len(board.Zones())}")


def lock_routes(board: pcbnew.BOARD) -> int:
    """Existing tracks and vias export as (type fix) so freerouting builds on them instead of ripping them up."""
    n = 0
    for t in board.GetTracks():
        t.SetLocked(True); n += 1
    return n


def stage(board: pcbnew.BOARD, d: design.Design, drop: set[str], label: str, ignore_classes: tuple[str, ...] = ()) -> int:
    """One incremental router run: lock what is routed, export, drop `drop` from the DSN (only nets that
    have no wiring yet: freerouting rejects wires of unknown nets), optionally ignore whole net classes,
    route, import."""
    prepare(board, d)   # classes and rules into this process's board and the project file
    print(f"== stage {label}: {lock_routes(board)} existing segments locked")
    export_dsn(board)
    filter_dsn(d, drop)
    rc = run_freerouting(ignore_classes=ignore_classes)
    if rc != 0:
        return rc
    import_ses(board, d)
    return 0


def pair_report(board: pcbnew.BOARD, d: design.Design) -> None:
    """Differential pairs: routed length per side (tracks + 0.6 mm per via) and the mismatch."""
    lengths = {}; vias = {}
    for t in board.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            vias[n] = vias.get(n, 0) + 1
        else:
            lengths[n] = lengths.get(n, 0) + t.GetLength() / 1e6
    pairs = []
    for net in sorted(diff_pair_nets(d)):
        for p, n in (("_P", "_N"), ("DP", "DM"), ("XP", "XN")):
            if net.endswith(p):
                other = net[: -len(p)] + n
                if other in d.nets:
                    pairs.append((net, other))
    lines = ["# Differential pairs after autorouting", "", "| pair | P mm | N mm | mismatch mm | vias P/N | note |", "|---|---|---|---|---|---|"]
    bad = 0
    for a, b in pairs:
        la, lb = lengths.get(a, 0.0), lengths.get(b, 0.0)
        mm = abs(la - lb)
        note = "" if (la and lb) else "UNROUTED"
        if la and lb and mm > 0.15:
            note = "match > 0.15 mm"; bad += 1
        lines.append(f"| {a} / {b} | {la:.2f} | {lb:.2f} | {mm:.2f} | {vias.get(a, 0)}/{vias.get(b, 0)} | {note} |")
    (HW / "routing" / "pairs.md").write_text("\n".join(lines) + "\n")
    print(f"pairs: {len(pairs)}, {bad} beyond the 0.15 mm match, report routing/pairs.md")


def pad_size(p) -> tuple[int, int]:
    """Pad size as seen on the board: KiCad stores it unrotated, the orientation turns it."""
    s = p.GetSize()
    if int(round(p.GetOrientationDegrees())) % 180 == 90:
        return int(s.y), int(s.x)
    return int(s.x), int(s.y)


def open_pads_from_drc(board: pcbnew.BOARD) -> set | None:
    """(reference, pad) pairs DRC lists as unconnected, when routing/drc.json is newer than the board
    file; None when there is no current report (then every pad without a track counts as open)."""
    import json, re
    rep = Path(str(PCB).replace(".kicad_pcb", "-drc.json")) if not (HW / "routing" / "drc.json").exists() else HW / "routing" / "drc.json"
    if not rep.exists() or rep.stat().st_mtime < PCB.stat().st_mtime - 1:
        return None
    out = set()
    for it in json.loads(rep.read_text()).get("unconnected_items", []):
        for i in it["items"]:
            m = re.match(r"(?:PTH )?[Pp]ad (\S+) \[.*?\] of (\w+)", i["description"])
            if m:
                out.add((m.group(2), m.group(1)))
    return out


def fanout_conn(board: pcbnew.BOARD) -> None:
    import math
    """Row-fitted fanout for every fine-pitch part with 20+ SMD pads (CM5 connector, M.2 socket, SATA
    receptacles, QFN hubs and bridges). Per row of pads, adjacent same-net pins are bridged pad-to-pad
    so they need one connection; plane-net groups get one via (in the gap between paired rows, else
    outward, staggered); QFN ground pins next to an exposed pad of the same net are tied straight into
    it. Non-plane groups (bay 12 V / 5 V pins, M.2 3.3 V pins) are only bridged, the router does the rest.
    Only pads that are still unconnected are touched; every via is collision-checked."""
    zones_by_net = {}
    for z in board.Zones():
        if not z.GetIsRuleArea():
            zones_by_net.setdefault(z.GetNetname(), []).append(z)
    open_pads = open_pads_from_drc(board)
    done_pads = connected_pads(board) if open_pads is None else None

    def is_open(ref, num):
        return ((ref, num) in open_pads) if open_pads is not None else ((ref, num) not in done_pads)

    via_d, via_drill, stub_w = MM(0.45), MM(0.2), MM(0.13)
    occ = Occupancy(board)
    placed = skipped = bridged = tied = 0

    def free(vx, vy, own):
        return occ.point_free(vx, vy, via_d // 2, own)

    def path_free(p1, p2, own):
        return occ.path_free(p1, p2, stub_w // 2, own)

    def track(p1, p2, net, layer):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pcbnew.VECTOR2I(*p1)); tr.SetEnd(pcbnew.VECTOR2I(*p2))
        tr.SetWidth(stub_w); tr.SetLayer(layer); tr.SetNetCode(net); board.Add(tr); occ.add(tr)

    def add_via(px, py, vx, vy, net, layer):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(via_d); v.SetDrill(via_drill)
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net); board.Add(v); occ.add(v)
        track((px, py), (vx, vy), net, layer)

    for f in board.GetFootprints():
        ref = f.GetReference()
        pads = [p for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        if len(pads) < 20:
            continue
        layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        fcx, fcy = f.GetPosition().x, f.GetPosition().y
        eps = [p for p in pads if min(pad_size(p)) >= MM(1.2) or not str(p.GetNumber())]   # exposed pads, incl. split ones
        if eps and ref.startswith("U"):
            continue   # QFNs: a via ring outside 0.4 mm pin rows blocks the neighbours' escapes; the router does these
        ep_keys = {(str(e.GetNumber()), int(e.GetPosition().x), int(e.GetPosition().y)) for e in eps}
        # rows: pads with the same orientation sharing the coordinate along their long axis
        rows = {}
        for p in pads:
            if (str(p.GetNumber()), int(p.GetPosition().x), int(p.GetPosition().y)) in ep_keys:
                continue
            sx_, sy_ = pad_size(p); along_x = sx_ < sy_   # pad longer in y -> its row runs along x
            pos = p.GetPosition()
            key = (along_x, int(round((pos.y if along_x else pos.x) / 1e4)))
            rows.setdefault(key, []).append(p)
        rows = {k: sorted(v, key=lambda p: p.GetPosition().x if k[0] else p.GetPosition().y) for k, v in rows.items() if len(v) >= 6}
        for (along_x, k), row in rows.items():
            partners = [kk for (ax, kk) in rows if ax == along_x and kk != k]
            partner = min(partners, key=lambda kk: abs(kk - k)) if partners else None
            gap = abs(partner - k) * 1e4 if partner is not None else 0
            pad_len = max(pad_size(row[0]))
            pos0 = row[0].GetPosition()
            coord = pos0.y if along_x else pos0.x
            centre = fcy if along_x else fcx
            inward = 1 if centre > coord else -1
            d_in = pad_len / 2 + MM(0.13) + via_d / 2 + MM(0.05)
            dists = []
            if partner is not None and gap and gap / 2 > d_in + via_d / 2 + MM(0.2):
                dists.append(inward * d_in)
            dists += [-inward * d_in, inward * (d_in + MM(0.6)), -inward * (d_in + MM(0.6))]
            # the exposed pad this row faces, if any (QFN): its edge nearest the row
            ep = None
            for e in eps:
                epos = e.GetPosition(); ex, ey = pad_size(e)
                edge = (epos.y - inward * ey / 2) if along_x else (epos.x - inward * ex / 2)
                if abs(edge - coord) < pad_len / 2 + MM(0.8):
                    ep = (e, edge)
            i = 0
            while i < len(row):
                p = row[i]; net = p.GetNetname()
                if not net or not is_open(ref, str(p.GetNumber())):
                    i += 1; continue
                j = i
                while j + 1 < len(row) and row[j + 1].GetNetname() == net:
                    j += 1
                group = row[i:j + 1]
                mid = group[len(group) // 2]
                mp = mid.GetPosition(); mx, my = int(mp.x), int(mp.y)
                own = [(int(g.GetPosition().x), int(g.GetPosition().y)) for g in group]
                for g in group:   # bridge the group pad-to-pad (same net, adjacent pads)
                    if g is not mid:
                        gp = g.GetPosition(); q = (int(gp.x), int(gp.y))
                        if path_free(q, (mx, my), own):
                            track(q, (mx, my), mid.GetNetCode(), layer); bridged += 1
                span_ok = False
                if ep is not None:
                    e = ep[0]; epos = e.GetPosition(); ex, ey = pad_size(e)
                    span_ok = (abs(mx - epos.x) <= ex / 2) if along_x else (abs(my - epos.y) <= ey / 2)
                if ep is not None and ep[0].GetNetname() == net and span_ok:
                    # tie into the exposed pad: straight inward from the group's middle pin to just inside its edge
                    e, edge = ep
                    inside = int(edge + inward * MM(0.25))
                    end = (mx, inside) if along_x else (inside, my)
                    epos = e.GetPosition()
                    if path_free((mx, my), end, own + [(int(epos.x), int(epos.y))]):
                        track((mx, my), end, mid.GetNetCode(), layer); tied += 1
                        i = j + 1; continue
                if net not in zones_by_net:
                    i = j + 1; continue   # bridged only; the router connects the group
                ok = False
                for dd in dists:
                    vx, vy = (mx, my + int(dd)) if along_x else (mx + int(dd), my)
                    if not free(vx, vy, own) or not path_free((mx, my), (vx, vy), own):
                        continue
                    if not any(z.Outline().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]):
                        continue
                    add_via(mx, my, vx, vy, mid.GetNetCode(), layer); placed += 1; ok = True
                    break
                if not ok:
                    skipped += len(group)
                i = j + 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"fanout_conn: {placed} vias, {bridged} pad-to-pad links, {tied} pins tied into exposed pads, {skipped} plane pins left for the router")


def drc_clean(board: pcbnew.BOARD, rounds: int = 3) -> int:
    """Remove tracks and vias that DRC flags in clearance, short, crossing or edge-clearance errors (the
    newer router leaves a few), refill, repeat. Pads and zones are never touched. Returns errors left."""
    import json
    import subprocess as sp
    rep = HW / "routing" / "drc.json"
    left = 0
    for r in range(rounds):
        pcbnew.SaveBoard(str(PCB), board)
        sp.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(rep), str(PCB)], capture_output=True)
        j = json.loads(rep.read_text())
        bad = [x for x in j["violations"] if x["type"] in ("clearance", "shorting_items", "tracks_crossing", "copper_edge_clearance", "items_not_allowed")]
        left = len(bad)
        if not bad:
            break
        spots = set()
        for x in bad:
            for i in x["items"]:
                if i["description"].startswith(("Track", "Via")) and "pos" in i:
                    spots.add((round(i["pos"]["x"], 3), round(i["pos"]["y"], 3), i["description"].startswith("Via")))
        doomed = []
        for t in board.GetTracks():
            is_via = t.GetClass() == "PCB_VIA"
            pts = [t.GetPosition()] if is_via else [t.GetStart(), t.GetEnd()]
            for q in pts:
                if (round(q.x / 1e6, 3), round(q.y / 1e6, 3), is_via) in spots:
                    doomed.append(t); break
        for t in doomed:
            board.Remove(t)
        print(f"drc_clean round {r + 1}: {len(bad)} errors, removed {len(doomed)} tracks/vias")
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(PCB), board)
    print(f"drc_clean: {left} copper errors left")
    return left


def main(cmd: str) -> int:
    d = design.build()
    board = pcbnew.LoadBoard(str(PCB))
    if cmd in ("prepare", "all"):
        prepare(board, d)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd in ("fanout", "all"):
        fanout(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "dsn":
        prepare(board, d)   # the export reads the classes from this process's board, so set them again
    if cmd in ("dsn", "all"):
        export_dsn(board)
        filter_dsn(d)
    if cmd == "all":
        if run_freerouting() != 0:
            return 1
    if cmd in ("import", "all"):
        import_ses(board, d)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "stage1":   # the single-ended signal nets (no planes, bays or pairs)
        lite = bay_nets(d) | diff_pair_nets(d) | POWER_NETS | {n for n in d.nets if n.startswith(("12V_BAY", "5V_BAY"))}
        if stage(board, d, lite, "1 (signals)"):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "stage2":   # everything single-ended: planes, bridge rails, bay power and control
        if stage(board, d, diff_pair_nets(d), "2 (single-ended, planes, bays)"):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "stage3":   # the differential pairs alone: the other classes are ignored, their copper stays
        if stage(board, d, set(), "3 (differential pairs)", ignore_classes=("kicad_default", "Bay", "Power")):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
        pair_report(board, d)
    if cmd == "drc-clean":
        drc_clean(board)
    if cmd == "fanout-big":
        fanout_big(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "fanout-conn":
        fanout_conn(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "pairs":
        pair_report(board, d)
    stats(board)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
