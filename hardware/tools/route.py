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
    "Power": (0.5, 0.13, None, 0.6, 0.3),
    "DiffPair90": (0.147, 0.13, 0.253, 0.45, 0.2),
    "Bay": (0.2, 0.13, None, 0.45, 0.2),
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
    # net codes first: after the net-class edits below, pcbnew's Python net lookups come back untyped
    codes = {n: board.FindNet(n).GetNetCode() for n in ("GND", "5V_SYS", "5V_HDD", "+3V3", "+12V")}
    ds = board.GetDesignSettings()
    ds.m_SolderMaskMinWidth = 0
    ds.m_SolderMaskExpansion = MM(0.05)
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
    for net, cls in assignments.items():
        ncs.SetNetclassPatternAssignment(net, cls)
    write_project_netclasses(assignments)
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
    # In2 power islands for the 136x100 layout (gen_pcb.py REGIONS): one contiguous polygon per rail,
    # built from rectangles; a higher priority island wins where they overlap.
    # 5V_SYS: bridge row, a link past bay 1's switch region, the CM5 and the M.2/front band
    zone("5V_SYS", pcbnew.In2_Cu, [(0, 0), (124, 0), (124, 22), (14, 22), (14, 33), (56, 33), (56, 75), (100, 75), (100, H), (0, H)], 1)
    zone("5V_HDD", pcbnew.In2_Cu, (14, 22, 124, 33), 1)      # bay switch row
    zone("+3V3", pcbnew.In2_Cu, (56, 33, 80, 75), 2)         # hubs column
    zone("+12V", pcbnew.In2_Cu, (80, 33, W, 82), 3)          # bucks, input block, bulk caps, right wall column
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
    print(f"net classes set; {len(assignments)} nets assigned ({sum(v == 'Bay' for v in assignments.values())} bay, "
          f"{sum(v == 'DiffPair90' for v in assignments.values())} diff-pair); zones filled")


def fanout(board: pcbnew.BOARD) -> None:
    """Drop a via and a short stub next to every SMD pad whose net has a copper zone, so the
    inner/back planes reach the top-side parts. Tries four directions and skips a pad if all
    collide with existing copper (reported)."""
    zones_by_net = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        zones_by_net.setdefault(z.GetNetname(), []).append(z)
    via_d, via_drill, stub_w = MM(0.6), MM(0.3), MM(0.3)
    occupied = []  # bounding boxes of pads and vias on F.Cu (coarse collision check)
    for f in board.GetFootprints():
        for pad in f.Pads():
            occupied.append(pad.GetBoundingBox())
    for t in board.GetTracks():
        occupied.append(t.GetBoundingBox())
    placed = skipped = 0
    for f in board.GetFootprints():
        fc = f.GetPosition()
        if len(list(f.Pads())) > 8:
            continue   # ICs and connectors with fine pitch: a stub between 0.4 mm pads shorts them; the router vias these itself
        for pad in f.Pads():
            net = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or net not in zones_by_net:
                continue
            if not any(z.Outline().Contains(pad.GetPosition()) for z in zones_by_net[net]):   # polygon, not bbox: the 5V island is L-shaped
                continue
            ppos = pad.GetPosition(); px, py = int(ppos.x), int(ppos.y)   # plain ints: SWIG hands back mutable refs
            sz = pad.GetSize(); half = max(int(sz.x), int(sz.y)) / 2
            dist = half + via_d / 2 + MM(0.35)
            import math
            base = math.atan2(py - int(fc.y), px - int(fc.x))
            done = False
            for k in (0, 1, -1, 2):
                a = base + k * math.pi / 2
                vx, vy = int(px + dist * math.cos(a)), int(py + dist * math.sin(a))
                box = pcbnew.BOX2I(pcbnew.VECTOR2I(vx - via_d // 2 - MM(0.15), vy - via_d // 2 - MM(0.15)),
                                   pcbnew.VECTOR2I(via_d + 2 * MM(0.15), via_d + 2 * MM(0.15)))
                if any(o.Intersects(box) and not o.Contains(pcbnew.VECTOR2I(px, py)) for o in occupied):
                    continue
                if not any(z.Outline().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]):
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(via_d); v.SetDrill(via_drill)
                v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNetCode(pad.GetNetCode()); board.Add(v)
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                tr.SetWidth(stub_w); tr.SetLayer(pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu)
                tr.SetNetCode(pad.GetNetCode()); board.Add(tr)
                occupied.append(v.GetBoundingBox()); occupied.append(tr.GetBoundingBox())
                placed += 1; done = True
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
            if min(sx, sy) >= MM(1.8):   # exposed pad: vias inside it, 1 mm grid, 0.5 mm inset
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


def run_freerouting(passes: int = 30) -> int:
    """Route the lite DSN (single-ended, non-bay nets). The optimizer loops forever without -oit;
    -mp is ignored by 2.1.0 but kept for newer builds."""
    if JAR is None:
        print("no freerouting jar in tools/freerouting/"); return 1
    LITE_SES.unlink(missing_ok=True)
    cmd = ["java", "-Djava.awt.headless=true", "-jar", str(JAR), "-de", str(LITE_DSN), "-do", str(LITE_SES),
           "-mp", str(passes), "-oit", "2"]
    print(" ".join(cmd))
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=7200, stdin=subprocess.DEVNULL)
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


def stage(board: pcbnew.BOARD, d: design.Design, drop: set[str], label: str) -> int:
    """One incremental router run: lock what is routed, export, drop `drop` from the DSN, route, import."""
    prepare(board, d)   # classes and rules into this process's board and the project file
    print(f"== stage {label}: {lock_routes(board)} existing segments locked")
    export_dsn(board)
    filter_dsn(d, drop)
    rc = run_freerouting()
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
    if cmd == "stage2":   # everything single-ended: planes, bridge rails, bay power and control
        if stage(board, d, diff_pair_nets(d), "2 (single-ended, planes, bays)"):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "stage3":   # the differential pairs
        if stage(board, d, set(), "3 (differential pairs)"):
            return 1
        pcbnew.SaveBoard(str(PCB), board)
        pair_report(board, d)
    if cmd == "fanout-big":
        fanout_big(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd == "pairs":
        pair_report(board, d)
    stats(board)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
