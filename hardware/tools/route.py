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

import os
import subprocess
import sys
from pathlib import Path

import pcbnew

import design

import project as _project

PRJ = _project.current()
HW = PRJ.dir
PCB = PRJ.pcb
DSN = PRJ.routing / f"{PRJ.name}.dsn"
SES = PRJ.routing / f"{PRJ.name}.ses"
JAR = next(iter(sorted((HW / "tools" / "freerouting").glob("freerouting-2.1.0.jar"))), None)

MM = pcbnew.FromMM

POWER_NETS = {"+12V", "5V_SYS", "5V_HDD", "+3V3", "3V3_M2", "3V3_M2_SW", "+1V2", "VIN_12V_RAW", "VIN_12V_FUSED", "GND", "SD_VDD"}
BAY_SHEETS = {"bridge", "bay-switch"}   # on the bay card; the brain has no bay sheets any more (C24)


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
MIN_RULES = {"min_clearance": 0.125, "min_track_width": 0.1, "min_via_diameter": 0.3, "min_through_hole_diameter": 0.15,
             "min_via_annular_width": 0.075, "min_hole_clearance": 0.2, "min_copper_edge_clearance": 0.3}   # 0.3/0.15 vias: D8, QFN dog-bones only; verify hole-to-copper 0.2 with the fab


def write_project_netclasses(assignments: dict[str, str]) -> None:
    """Net classes live in the .kicad_pro, not the board: kicad-cli DRC and the DSN export read them from
    there, and gen_sch.py rewrites the project. So prepare() writes them into the project file itself."""
    import json
    pro = PRJ.pro
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
    pro = PRJ.pro
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
    codes = {n: board.FindNet(n).GetNetCode() for n in ("GND", "5V_SYS", "5V_HDD", "+3V3", "+12V") if board.FindNet(n) is not None}
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
    if PRJ.key == "card":
        # bay card: 12 V and 5 V islands on In2 under the switch block, the rest of In2 is 5 V for the bridge
        zone("5V_HDD", pcbnew.In2_Cu, (0, 0, W, H), 1)
        zone("+12V", pcbnew.In2_Cu, (0, 29, 18, 37.5), 2)
    else:
        # brain v4 (150x122, gen_pcb.layout_brain): 5V_SYS almost everywhere on In2, 5V_HDD behind the slots,
        # +3V3 around the hubs, +12V under the bucks / input block. A higher priority island wins overlaps.
        zone("5V_SYS", pcbnew.In2_Cu, (0, 0, W, H), 1)
        zone("5V_HDD", pcbnew.In2_Cu, (0, 0, 122, 30), 2)          # slot row: card 5 V through the slots
        zone("+12V", pcbnew.In2_Cu, [(0, 0), (12, 0), (12, 30), (58, 30), (58, 35), (0, 35)], 3)   # unused corner + strip feeding the slot row
        zone("+12V", pcbnew.In2_Cu, (56, 55, 95, 100), 3)          # bucks, input block, bulk caps
        zone("+3V3", pcbnew.In2_Cu, (30, 35, 122, 55), 2)          # hub band
    if gen_pcb.ANTENNA_STRIP:
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
        self.box_layers = [{L for L in (pcbnew.F_Cu, pcbnew.B_Cu) if pad.IsOnLayer(L)} for f in board.GetFootprints() for pad in f.Pads()]
        self.segs = []   # (SEG, half width, net code, layer)
        self.vias = []   # (x, y, radius, net code)
        for t in board.GetTracks():
            self.add(t)
        # board edges (board drawings and footprint-owned outlines such as a card-edge tab with its key notch)
        self.edge_clr = int(board.GetDesignSettings().m_CopperEdgeClearance)
        self.edges = [d.GetEffectiveShape() for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
        for f in board.GetFootprints():
            self.edges += [g.GetEffectiveShape() for g in f.GraphicalItems() if g.GetLayer() == pcbnew.Edge_Cuts]

    def add(self, t) -> None:
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); self.vias.append((int(p.x), int(p.y), t.GetWidth(pcbnew.F_Cu) // 2, t.GetNetCode()))
        else:
            self.segs.append((pcbnew.SEG(t.GetStart(), t.GetEnd()), t.GetWidth() // 2, t.GetNetCode(), t.GetLayer()))

    def remove_track(self, a, b, netcode: int, layer) -> None:
        """Forget one straight track (given by its ends) so a replacement can be checked against the rest."""
        self.segs = [s for s in self.segs if not (s[2] == netcode and s[3] == layer and
                     {(int(s[0].A.x), int(s[0].A.y)), (int(s[0].B.x), int(s[0].B.y))} == {(int(a[0]), int(a[1])), (int(b[0]), int(b[1]))})]

    def drop_net(self, netcode: int) -> None:
        self.segs = [s for s in self.segs if s[2] != netcode]
        self.vias = [v for v in self.vias if v[3] != netcode]

    def blockers(self, x: int, y: int, r: int, own) -> set | None:
        """Net codes of the tracks / vias that block a disc at (x, y); None when a pad or the board edge
        blocks it (nothing to rip up)."""
        pt = pcbnew.VECTOR2I(x, y)
        if any(e.Collide(pt, r + self.edge_clr) for e in self.edges):
            return None
        for b in self.boxes:
            if b.Intersects(pcbnew.BOX2I(pcbnew.VECTOR2I(x - r - self.clr, y - r - self.clr), pcbnew.VECTOR2I(2 * (r + self.clr), 2 * (r + self.clr)))):
                if not any(b.Contains(pcbnew.VECTOR2I(*o)) for o in own):
                    return None
        out = set()
        for seg, hw, net, _layer in self.segs:
            if seg.Distance(pt) < r + hw + self.clr and not any(seg.Distance(pcbnew.VECTOR2I(*o)) <= hw + 10 for o in own):
                out.add(net)
        for vx, vy, vr, net in self.vias:
            if (vx - x) ** 2 + (vy - y) ** 2 < (r + vr + self.clr) ** 2 and not any((vx - o[0]) ** 2 + (vy - o[1]) ** 2 <= (vr + 10) ** 2 for o in own):
                out.add(net)
        return out

    def add_box(self, box) -> None:
        self.boxes.append(box)
        self.box_layers.append(None)

    def point_free(self, x: int, y: int, r: int, own, layer=None) -> bool:
        """A disc of radius r at (x, y) clears everything except copper that touches one of `own`. With
        `layer`, tracks and SMD pads on the other copper layer are ignored (vias and through-hole pads count)."""
        pt = pcbnew.VECTOR2I(x, y)
        if any(e.Collide(pt, r + self.edge_clr) for e in self.edges):
            return False
        for b, bl in zip(self.boxes, self.box_layers):
            if layer is not None and bl and layer not in bl:
                continue
            if b.Intersects(pcbnew.BOX2I(pcbnew.VECTOR2I(x - r - self.clr, y - r - self.clr), pcbnew.VECTOR2I(2 * (r + self.clr), 2 * (r + self.clr)))):
                if not any(b.Contains(pcbnew.VECTOR2I(*o)) for o in own):
                    return False
        for seg, hw, _net, sl in self.segs:
            if layer is not None and sl != layer:
                continue
            if seg.Distance(pt) < r + hw + self.clr:
                if not any(seg.Distance(pcbnew.VECTOR2I(*o)) <= hw + 10 for o in own):
                    return False
        for vx, vy, vr, _net in self.vias:
            if (vx - x) ** 2 + (vy - y) ** 2 < (r + vr + self.clr) ** 2:
                if not any((vx - o[0]) ** 2 + (vy - o[1]) ** 2 <= (vr + 10) ** 2 for o in own):
                    return False
        return True

    def path_free(self, p1, p2, hw: int, own, layer=None) -> bool:
        n = max(2, int(((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5 / MM(0.1)))
        return all(self.point_free(p1[0] + (p2[0] - p1[0]) * k // n, p1[1] + (p2[1] - p1[1]) * k // n, hw, own, layer) for k in range(n + 1))


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
    open_pads = open_pads_from_drc(board)
    done_pads = connected_pads(board) if open_pads is None else None
    via_d, via_drill, stub_w = MM(0.6), MM(0.3), MM(0.25)
    occupied = [pad.GetBoundingBox() for f in board.GetFootprints() for pad in f.Pads()]
    occupied += [t.GetBoundingBox() for t in board.GetTracks()]
    occ = Occupancy(board)   # for the long-pad branch (card-edge fingers)
    long_vias = [(int(t.GetPosition().x), int(t.GetPosition().y), t.GetNetCode()) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]

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
            if pad.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN) or net not in zones_by_net:
                continue
            key = (f.GetReference(), str(pad.GetNumber()))
            sx, sy = pad_size(pad)
            long_pad = max(sx, sy) >= MM(3.0) and min(sx, sy) < MM(1.2)
            if not long_pad and ((open_pads is not None and key not in open_pads) or (open_pads is None and key in done_pads)):
                continue
            if not any(z.Outline().Contains(pad.GetPosition()) for z in zones_by_net[net]):
                continue
            ppos = pad.GetPosition(); px, py = int(ppos.x), int(ppos.y)
            if long_pad:
                # long pad (card-edge finger): one via in line with the pad beyond its inner end, where the
                # neighbours at 1 mm pitch are clear, shared by the A- and B-side fingers of that position
                # (opposite layers), each with a stub on its own layer. A via the router already put there
                # is reused; a finger whose layer has no stub to the via gets one.
                along_x = sx > sy
                half = max(sx, sy) / 2
                pad_layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
                reach = half + via_d / 2 + MM(2.6)
                near = [(x, y) for x, y, nc in long_vias if nc == pad.GetNetCode() and abs(x - px) <= MM(0.7) and abs(y - py) <= reach] if not along_x else \
                       [(x, y) for x, y, nc in long_vias if nc == pad.GetNetCode() and abs(y - py) <= MM(0.7) and abs(x - px) <= reach]
                ok = False
                if near:
                    vx, vy = min(near, key=lambda q: (q[0] - px) ** 2 + (q[1] - py) ** 2)
                    has_stub = any(t.GetClass() != "PCB_VIA" and t.GetLayer() == pad_layer and t.GetNetCode() == pad.GetNetCode()
                                   and pcbnew.SEG(t.GetStart(), t.GetEnd()).Distance(pcbnew.VECTOR2I(vx, vy)) < MM(0.05)
                                   and pcbnew.SEG(t.GetStart(), t.GetEnd()).Distance(pcbnew.VECTOR2I(px, py)) < min(sx, sy) for t in board.GetTracks())
                    if has_stub:
                        continue
                    if occ.path_free((px, py), (vx, vy), stub_w // 2, [(px, py), (vx, vy)]):
                        tr = pcbnew.PCB_TRACK(board)
                        tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                        tr.SetWidth(stub_w); tr.SetLayer(pad_layer); tr.SetNetCode(pad.GetNetCode()); board.Add(tr)
                        occupied.append(tr.GetBoundingBox()); occ.add(tr)
                        placed += 1; ok = True
                else:
                    for sign in (-1, 1):
                        for extra, side in ((0.3, 0), (0.8, 0), (1.4, 0), (0.8, 0.6), (0.8, -0.6), (1.6, 0.6), (1.6, -0.6), (2.4, 0), (2.4, 0.6), (2.4, -0.6)):
                            dist = int(half + via_d / 2 + MM(extra))
                            vx, vy = (px + sign * dist, py + int(MM(side))) if along_x else (px + int(MM(side)), py + sign * dist)
                            if not occ.point_free(vx, vy, via_d // 2, [(px, py)]) or not occ.path_free((px, py), (vx, vy), stub_w // 2, [(px, py)]):
                                continue
                            if not any(z.Outline().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]):
                                continue
                            v = add_via(vx, vy, pad.GetNetCode(), pad_layer); occ.add(v)
                            long_vias.append((vx, vy, pad.GetNetCode()))
                            twins = [q for q in pads if q.GetNetCode() == pad.GetNetCode()
                                     and abs(int(q.GetPosition().x) - px) < MM(0.05) and abs(int(q.GetPosition().y) - py) < MM(0.05)]
                            for q in twins:
                                ql = pcbnew.F_Cu if q.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
                                tr = pcbnew.PCB_TRACK(board)
                                tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                                tr.SetWidth(stub_w); tr.SetLayer(ql); tr.SetNetCode(q.GetNetCode()); board.Add(tr)
                                occupied.append(tr.GetBoundingBox()); occ.add(tr)
                            placed += 1; ok = True
                            break
                        if ok:
                            break
                if not ok:
                    skipped += 1
                continue
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


LITE_DSN = PRJ.routing / f"{PRJ.name}-lite.dsn"
LITE_SES = PRJ.routing / f"{PRJ.name}-lite.ses"


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
    jar = _project.HW / "tools" / "freerouting" / f"freerouting-{ver}.jar"
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
    (PRJ.routing / "freerouting-lite.log").write_text(cp.stdout + cp.stderr)
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
    try:
        _stats(board)
    except Exception as e:  # noqa: BLE001 - untyped SWIG proxies after heavy edits; the board is already saved
        print("stats skipped:", e)


def _stats(board: pcbnew.BOARD) -> None:
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


VIA_LEN = 0.6   # mm of electrical length counted per via in a pair


def pairs_of(d: design.Design) -> list[tuple[str, str]]:
    pairs = []
    for net in sorted(diff_pair_nets(d)):
        for p, n in (("_P", "_N"), ("DP", "DM"), ("XP", "XN")):
            if net.endswith(p):
                other = net[: -len(p)] + n
                if other in d.nets:
                    pairs.append((net, other))
    return pairs


def net_lengths(board: pcbnew.BOARD) -> tuple[dict, dict]:
    """(length in mm per net: tracks + VIA_LEN per via, via count per net)."""
    lengths = {}; vias = {}
    for t in board.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            vias[n] = vias.get(n, 0) + 1
            lengths[n] = lengths.get(n, 0) + VIA_LEN
        else:
            lengths[n] = lengths.get(n, 0) + t.GetLength() / 1e6
    return lengths, vias


def pair_report(board: pcbnew.BOARD, d: design.Design) -> None:
    """Differential pairs: routed length per side (tracks + VIA_LEN per via) and the mismatch."""
    lengths, vias = net_lengths(board)
    pairs = pairs_of(d)
    lines = ["# Differential pairs after autorouting", "", "| pair | P mm | N mm | mismatch mm | vias P/N | note |", "|---|---|---|---|---|---|"]
    bad = 0
    for a, b in pairs:
        la, lb = lengths.get(a, 0.0), lengths.get(b, 0.0)
        mm = abs(la - lb)
        note = "" if (la and lb) else "UNROUTED"
        if la and lb and mm > 0.15:
            note = "match > 0.15 mm"; bad += 1
        lines.append(f"| {a} / {b} | {la:.2f} | {lb:.2f} | {mm:.2f} | {vias.get(a, 0)}/{vias.get(b, 0)} | {note} |")
    (PRJ.routing / "pairs.md").write_text("\n".join(lines) + "\n")
    print(f"pairs: {len(pairs)}, {bad} beyond the 0.15 mm match, report routing/pairs.md")


def rip_bad_pairs(board: pcbnew.BOARD, d: design.Design, tol: float = 0.15, min_gap: float = 0.0) -> list[str]:
    """Remove every track and via of both nets of each pair the tuner cannot fix: a side that is not
    routed, or a mismatch beyond `tol` (called after `tune`, so what is left is detour, not tuning room).
    Returns the pair names; the router then routes them again with the rest of the copper locked."""
    lengths, _v = net_lengths(board)
    doomed_nets, names = set(), []
    for a, b in pairs_of(d):
        la, lb = lengths.get(a, 0.0), lengths.get(b, 0.0)
        if not (la and lb) or abs(la - lb) > tol:
            doomed_nets.update((a, b)); names.append(f"{a}/{b}")
    victims = [t for t in board.GetTracks() if t.GetNetname() in doomed_nets]
    for t in victims:
        board.Remove(t)
    print(f"rip_pairs: {len(names)} pairs, {len(victims)} tracks/vias removed: {', '.join(names)}")
    return names


def tune_pairs(board: pcbnew.BOARD, d: design.Design, tol: float = 0.1, max_extra: float = 40.0) -> None:
    """Length-match every routed differential pair by adding rectangular meanders to the shorter side.

    A bump of height h adds exactly 2h of track. Bumps are 0.5 mm wide with 0.5 mm between them (edge gap
    0.35 mm, well above the 0.125 mm clearance), sit on the outer side of the shorter net's longest straight
    segments, and grow as tall as the free space allows (up to 4 mm); the last bump is cut to the exact
    remainder. Everything is checked with the layer-aware Occupancy (tracks, pads, vias, board edge) and the
    keep-out rule areas; a pair that cannot be completed is left alone and listed. Skew is measured as the
    pair report does: track length plus VIA_LEN per via."""
    import math
    lengths, _vias = net_lengths(board)
    occ = Occupancy(board)
    keepouts = [z for z in board.Zones() if z.GetIsRuleArea()]
    tracks = [t for t in board.GetTracks() if t.GetClass() != "PCB_VIA"]
    by_net = {}
    for t in tracks:
        a, b = t.GetStart(), t.GetEnd()
        by_net.setdefault(t.GetNetname(), []).append(
            (t, (int(a.x), int(a.y)), (int(b.x), int(b.y)), t.GetLayer(), t.GetWidth(), t.GetNetCode(), t.GetLength()))
    A_W = MM(0.5)      # bump width and gap between bumps
    MARGIN = MM(0.45)  # straight run kept at each end of a segment
    H_MAX, H_MIN, STEP = MM(4.0), MM(0.1), MM(0.1)

    def in_keepout(pt, layer) -> bool:
        return any(z.IsOnLayer(layer) and z.Outline().Contains(pcbnew.VECTOR2I(int(pt[0]), int(pt[1]))) for z in keepouts)

    def plan(seg, side, need_mm):
        """Bump heights (nm) along one segment on one side, or [] ; returns (list of (x0, h), extra in mm)."""
        _t, A, B, layer, width, _nc, length = seg
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        if L < 2 * MARGIN + 2 * A_W:
            return [], 0.0
        ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
        nx, ny = -uy * side, ux * side

        def pt(sx, ty):
            return (int(A[0] + ux * sx + nx * ty), int(A[1] + uy * sx + ny * ty))

        bumps, extra = [], 0.0
        x0 = MARGIN
        while x0 + A_W <= L - MARGIN and need_mm - extra >= tol:
            want = max(H_MIN, min(H_MAX, int(MM((need_mm - extra) / 2))))
            h = 0
            hh = want
            while hh >= H_MIN:
                quad = [pt(x0, 0), pt(x0, hh), pt(x0 + A_W, hh), pt(x0 + A_W, 0)]
                if (all(occ.path_free(quad[i], quad[i + 1], width // 2, [], layer) for i in range(3))
                        and not any(in_keepout(q, layer) for q in quad)):
                    h = hh
                    break
                hh -= STEP
            if h:
                bumps.append((x0, h)); extra += 2 * h / 1e6
                x0 += 2 * A_W
            else:
                x0 += MM(0.25)   # nothing fits here: slide along
        return bumps, extra

    done = failed = 0
    notes = []
    for a, b in pairs_of(d):
        la, lb = lengths.get(a, 0.0), lengths.get(b, 0.0)
        if not (la and lb):
            continue
        need = abs(la - lb)
        if need < tol:
            continue
        short = a if la < lb else b
        if need > max_extra:
            notes.append(f"{a}/{b}: {need:.1f} mm apart, more than {max_extra:.0f} mm; reroute the long side")
            failed += 1
            continue
        segs = sorted(by_net.get(short, []), key=lambda s: -s[6])[:8]
        chosen = []   # (seg, side, bumps)
        got = 0.0
        for seg in segs:
            if need - got < tol:
                break
            # both sides on the seg's occupancy (the original track itself removed while planning)
            occ.remove_track(seg[1], seg[2], seg[5], seg[3])
            best = max(((plan(seg, sd, need - got), sd) for sd in (1, -1)), key=lambda r: r[0][1])
            (bumps, extra), side = best
            occ.add(seg[0])   # put the original back until the pair is settled
            if bumps:
                chosen.append((seg, side, bumps)); got += extra
        if need - got >= tol:
            notes.append(f"{a}/{b}: needs {need:.2f} mm, room for {got:.2f} mm; left as routed")
            failed += 1
            continue
        for seg, side, bumps in chosen:
            t, A, B, layer, width, nc, _len = seg
            L = math.hypot(B[0] - A[0], B[1] - A[1])
            ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
            nx, ny = -uy * side, ux * side

            def pt(sx, ty, A=A, ux=ux, uy=uy, nx=nx, ny=ny):
                return (int(A[0] + ux * sx + nx * ty), int(A[1] + uy * sx + ny * ty))

            poly = [A]
            for x0, h in bumps:
                poly += [pt(x0, 0), pt(x0, h), pt(x0 + A_W, h), pt(x0 + A_W, 0)]
            poly.append(B)
            occ.remove_track(A, B, nc, layer)
            board.Remove(t)
            for q0, q1 in zip(poly, poly[1:]):
                if q0 == q1:
                    continue
                nt = pcbnew.PCB_TRACK(board)
                nt.SetStart(pcbnew.VECTOR2I(*q0)); nt.SetEnd(pcbnew.VECTOR2I(*q1))
                nt.SetWidth(width); nt.SetLayer(layer); nt.SetNetCode(nc)
                board.Add(nt); occ.add(nt)
        done += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"tune: {done} pairs meandered, {failed} left as routed")
    for n in notes:
        print("tune note:", n)


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
    rep = PRJ.routing / "drc.json"
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


def fanout_qfn(board: pcbnew.BOARD, ripup: bool = False) -> None:
    """D8: dog-bone vias of 0.3/0.15 mm on the 0.4-0.65 mm-pitch QFN / DFN pins (bridges, hubs, the DFN P-FETs), for every
    pin on a net with three or more pads that is not a differential pair. Vias sit on two lines outside
    the pin row (0.75 and 1.35 mm from the pad centre), alternating by pin index so no two vias are
    closer than 0.8 mm along the row and the signal pins between them can still escape. Plane pins land
    on their plane; rail pins (VCCO, VDD_CORE, +1V2...) get a B.Cu escape for the router. Only pins DRC
    lists as open are touched."""
    import math
    open_pads = open_pads_from_drc(board)
    done_pads = connected_pads(board) if open_pads is None else None

    def is_open(ref, num):
        return ((ref, num) in open_pads) if open_pads is not None else ((ref, num) not in done_pads)

    pads_per_net = {}
    pair_nets = set()
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() > 0:
                pads_per_net[p.GetNetname()] = pads_per_net.get(p.GetNetname(), 0) + 1
    for n in pads_per_net:
        if n.endswith(("_P", "_N", "DP", "DM", "TXDP", "TXDM", "RXDP", "RXDM", "_TXP", "_TXN", "_RXP", "_RXN", "XP", "XN")):
            pair_nets.add(n)
    zones_by_net = {}
    for z in board.Zones():
        if not z.GetIsRuleArea():
            zones_by_net.setdefault(z.GetNetname(), []).append(z)
    via_d, via_drill, stub_w = MM(0.3), MM(0.15), MM(0.13)
    occ = Occupancy(board)
    placed = skipped = 0
    ripped = set()   # simple nets (a track between two or three pads, no pair) removed so a plane pin can escape; the router redoes them
    netinfo = board.GetNetInfo()

    def rip(netcodes) -> bool:
        """Remove every track and via of the given nets when all are simple point-to-point nets."""
        names = [netinfo.GetNetItem(n).GetNetname() for n in netcodes]
        if not netcodes or any(n in pair_nets or pads_per_net.get(n, 0) > 6 or n in zones_by_net for n in names):
            return False
        for t in [t for t in board.GetTracks() if t.GetNetCode() in netcodes]:
            board.Remove(t)
        for n in netcodes:
            occ.drop_net(n)
        ripped.update(names)
        return True

    for f in board.GetFootprints():
        ref = f.GetReference()
        pads = [p for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        eps = [p for p in pads if min(pad_size(p)) >= MM(1.2) or not str(p.GetNumber())]
        if not (ref.startswith(("U", "Q")) and eps and len(pads) >= 8):
            continue   # QFNs and DFNs with an exposed pad only
        layer = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
        fcx, fcy = f.GetPosition().x, f.GetPosition().y
        ep_keys = {(str(e.GetNumber()), int(e.GetPosition().x), int(e.GetPosition().y)) for e in eps}
        rows = {}
        for p in pads:
            if (str(p.GetNumber()), int(p.GetPosition().x), int(p.GetPosition().y)) in ep_keys:
                continue
            sx_, sy_ = pad_size(p); along_x = sx_ < sy_
            pos = p.GetPosition()
            rows.setdefault((along_x, int(round((pos.y if along_x else pos.x) / 1e4))), []).append(p)
        for (along_x, k), row in rows.items():
            if len(row) < 4:
                continue
            row.sort(key=lambda p: p.GetPosition().x if along_x else p.GetPosition().y)
            pos0 = row[0].GetPosition()
            coord = pos0.y if along_x else pos0.x
            centre = fcy if along_x else fcx
            outward = -1 if centre > coord else 1
            pad_len = max(pad_size(row[0]))
            d1 = pad_len / 2 + MM(0.125) + via_d / 2 + MM(0.05)
            d2 = d1 + MM(0.6)
            for i, p in enumerate(row):
                net = p.GetNetname()
                if not net or net in pair_nets or pads_per_net.get(net, 0) < 3:
                    continue
                if not is_open(ref, str(p.GetNumber())):
                    continue
                pp = p.GetPosition(); px, py = int(pp.x), int(pp.y)

                def spot(dd):
                    return (px, py + int(outward * dd)) if along_x else (px + int(outward * dd), py)

                def fits(vx, vy):
                    if not occ.point_free(vx, vy, via_d // 2, [(px, py)]) or not occ.path_free((px, py), (vx, vy), stub_w // 2, [(px, py)]):
                        return False
                    return not (net in zones_by_net and not any(z.Outline().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]))

                order = (d1, d2) if i % 2 == 0 else (d2, d1)
                found = next((spot(dd) for dd in order if fits(*spot(dd))), None)
                if found is None:   # rip up a simple net sitting on the closest spot, then look again
                    blk = occ.blockers(*spot(d1), via_d // 2, [(px, py)])
                    if ripup and blk and p.GetNetCode() not in blk and rip(blk):
                        found = next((spot(dd) for dd in order if fits(*spot(dd))), None)
                if found is None:
                    skipped += 1
                    continue
                vx, vy = found
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(via_d); v.SetDrill(via_drill)
                v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNetCode(p.GetNetCode()); board.Add(v); occ.add(v)
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                tr.SetWidth(stub_w); tr.SetLayer(layer); tr.SetNetCode(p.GetNetCode()); board.Add(tr); occ.add(tr)
                placed += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"fanout_qfn: {placed} small vias placed, {skipped} QFN pins skipped (no free spot)" + (f", ripped up for the router: {sorted(ripped)}" if ripped else ""))


def drc_clean(board: pcbnew.BOARD, rounds: int = 3) -> int:
    """Remove tracks and vias that DRC flags in clearance, short, crossing or edge-clearance errors (the
    newer router leaves a few), refill, repeat. Pads and zones are never touched. Returns errors left."""
    import json
    import subprocess as sp
    rep = PRJ.routing / "drc.json"
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


def update_nets(board: pcbnew.BOARD, d: design.Design) -> int:
    """Re-sync the pad nets of an already routed board from the design (after a pin-mapping fix such as
    the 8-pin P-FET symbols) without regenerating the board: pads get their new net, copper of another
    net that lands on a re-netted pad is removed, and whatever of the touched nets is then left without
    a pad (the rest of an old route) is removed too. The router finishes the re-netted pins afterwards.
    All geometry is read into plain Python first: after the first pad edit this KiCad build hands back
    untyped SWIG proxies for everything else."""
    want = d.pin_net()
    nets = board.GetNetInfo()
    tracks = []   # (proxy, is_via, netcode, layer, (x, y) ends)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition(); tracks.append((t, True, t.GetNetCode(), None, [(int(pos.x), int(pos.y))]))
        else:
            a, b = t.GetStart(), t.GetEnd()
            tracks.append((t, False, t.GetNetCode(), t.GetLayer(), [(int(a.x), int(a.y)), (int(b.x), int(b.y))]))
    pads = []     # (proxy, ref, number, netname, netcode, box, layers)
    for f in board.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            box = (int(bb.GetLeft()), int(bb.GetTop()), int(bb.GetRight()), int(bb.GetBottom()))
            layers = {L for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu) if p.IsOnLayer(L)}
            pads.append((p, f.GetReference(), str(p.GetNumber()), p.GetNetname(), p.GetNetCode(), box, layers))
    codes = {}
    for _p, ref, num, netname, _c, _b, _l in pads:
        new = want.get((ref, num), "")
        if new and new != netname and new not in codes:
            item = nets.GetNetItem(new)
            if item is None:
                board.Add(pcbnew.NETINFO_ITEM(board, new)); item = nets.GetNetItem(new)
            codes[new] = item.GetNetCode()

    def inside(box, pt):
        return box[0] <= pt[0] <= box[2] and box[1] <= pt[1] <= box[3]

    changed = []   # (pad tuple, new code)
    for pt in pads:
        new = want.get((pt[1], pt[2]), "")
        if new != pt[3]:
            changed.append((pt, codes[new] if new else 0))
    if not changed:
        print("update_nets: nothing to change")
        return 0
    touched = {c for pt, new in changed for c in (pt[4], new) if c}
    removed = set()
    # 1) copper of another net sitting on a re-netted pad
    for pt, new in changed:
        for i, (t, is_via, net, layer, ends) in enumerate(tracks):
            if net == new or i in removed:
                continue
            if any(inside(pt[5], e) for e in ends) and (is_via or layer in pt[6]):
                removed.add(i)
    # new pad nets and layers for step 2
    newcode = {id(pt[0]): new for pt, new in changed}
    pad_net = [(newcode.get(id(pt[0]), pt[4]), pt[5], pt[6]) for pt in pads]
    # 2) pieces of the touched nets that no longer reach any pad (union-find on coincident ends)
    for code in touched:
        idx = [i for i, tr in enumerate(tracks) if tr[2] == code and i not in removed]
        parent = {i: i for i in idx}

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i

        pts = {}
        for i in idx:
            for e in tracks[i][4]:
                k = (e[0] // 1000, e[1] // 1000)
                if k in pts:
                    parent[find(i)] = find(pts[k])
                else:
                    pts[k] = i
        cpads = [(box, layers) for c, box, layers in pad_net if c == code]
        has_pad = set()
        for i in idx:
            _t, is_via, _n, layer, ends = tracks[i]
            if any(inside(box, e) and (is_via or layer in layers) for e in ends for box, layers in cpads):
                has_pad.add(find(i))
        removed.update(i for i in idx if find(i) not in has_pad)
    # mutate last
    for pt, new in changed:
        pt[0].SetNetCode(new)
    for i in removed:
        board.Remove(tracks[i][0])
    print(f"update_nets: {len(changed)} pads re-netted ({', '.join(sorted({pt[1] for pt, _ in changed}))}), {len(removed)} copper items removed")
    return len(changed)


def main(cmd: str) -> int:
    d = design.build(PRJ.key)
    board = pcbnew.LoadBoard(str(PCB))
    if cmd == "update-nets":
        update_nets(board, d)
        pcbnew.SaveBoard(str(PCB), board)
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
    pairs_first = os.environ.get("BD_PAIRS_FIRST") == "1"   # pairs are routed first on the empty board (stage0); later stages keep them
    if cmd == "stage0":   # differential pairs alone, first: the other classes are ignored
        if stage(board, d, set(), "0 (pairs first)", ignore_classes=("kicad_default", "Bay", "Power")):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
        pair_report(board, d)
    if cmd == "stage1":   # the single-ended signal nets (no planes, bays or pairs)
        lite = bay_nets(d) | diff_pair_nets(d) | POWER_NETS | {n for n in d.nets if n.startswith(("12V_BAY", "5V_BAY"))}
        if pairs_first:
            lite -= diff_pair_nets(d)
        if stage(board, d, lite, "1 (signals)", ignore_classes=("DiffPair90",) if pairs_first else ()):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "stage2":   # everything single-ended: planes, bridge rails, bay power and control
        if stage(board, d, set() if pairs_first else diff_pair_nets(d), "2 (single-ended, planes, bays)",
                 ignore_classes=("DiffPair90",) if pairs_first else ()):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "stage3":   # the differential pairs alone: the other classes are ignored, their copper stays
        if stage(board, d, set(), "3 (differential pairs)", ignore_classes=("kicad_default", "Bay", "Power")):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
        pair_report(board, d)
    if cmd == "fanout-qfn":
        fanout_qfn(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "fanout-qfn-rip":   # before a routing stage only: may rip up simple nets for the router to redo
        fanout_qfn(board, ripup=True)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "drc-clean":
        drc_clean(board)
    if cmd == "fanout-big":
        fanout_big(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "fanout-conn":
        fanout_conn(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "rip-pairs":   # tools/reroute_pairs.sh: rip, then stage3 / drc-clean / tune in fresh processes
        rip_bad_pairs(board, d)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "tune":
        tune_pairs(board, d)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd in ("pairs", "tune"):
        pair_report(board, d)
    stats(board)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
