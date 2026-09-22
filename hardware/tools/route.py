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


def prepare(board: pcbnew.BOARD, d: design.Design) -> None:
    ds = board.GetDesignSettings()
    ds.m_SolderMaskMinWidth = 0
    ds.m_SolderMaskExpansion = MM(0.05)
    ncs = ds.m_NetSettings  # NET_SETTINGS
    # net classes
    nc_default = ncs.GetDefaultNetclass()
    nc_default.SetTrackWidth(MM(0.2)); nc_default.SetClearance(MM(0.15))
    nc_default.SetViaDiameter(MM(0.6)); nc_default.SetViaDrill(MM(0.3))
    for name, width, clearance, gap in (("Power", 0.6, 0.15, 0.0), ("DiffPair90", 0.15, 0.15, 0.15), ("Bay", 0.25, 0.15, 0.0)):
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(MM(width)); nc.SetClearance(MM(clearance))
        nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))
        if gap:
            nc.SetDiffPairWidth(MM(width)); nc.SetDiffPairGap(MM(gap))
        ncs.SetNetclass(name, nc)
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
    # copper zones: GND on In1, power islands on In2, GND on B.Cu
    for z in list(board.Zones()):
        board.Remove(z)
    import gen_pcb
    ox, oy = gen_pcb.ORIGIN
    W, H = gen_pcb.BOARD_W, gen_pcb.BOARD_H
    def zone(net_name, layer, rect, priority=0):
        net = board.GetNetcodeFromNetname(net_name)
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
    # In2 power islands for the 150x98 layout (gen_pcb.py REGIONS): one contiguous polygon per rail,
    # built from rectangles; a higher priority island wins where they overlap.
    # bridge row, a link past bay 1's switch region, CM5 + front band: one L-shaped polygon
    zone("5V_SYS", pcbnew.In2_Cu, [(0, 0), (124, 0), (124, 22), (14, 22), (14, 33), (82, 33), (82, H), (0, H)], 1)
    zone("5V_HDD", pcbnew.In2_Cu, (14, 22, 124, 33), 1)      # bay switch row
    zone("+3V3", pcbnew.In2_Cu, (82, 33, W, H), 2)           # hubs column, M.2 column, right front band
    zone("+12V", pcbnew.In2_Cu, (96, 33, 124, 87), 3)        # buck column carved out of the 3V3 island
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
            if not any(z.GetBoundingBox().Contains(pad.GetPosition()) for z in zones_by_net[net]):
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
                if not any(z.GetBoundingBox().Contains(pcbnew.VECTOR2I(vx, vy)) for z in zones_by_net[net]):
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(via_d); v.SetDrill(via_drill)
                v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNetCode(pad.GetNetCode()); board.Add(v)
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(px, py)); tr.SetEnd(pcbnew.VECTOR2I(vx, vy))
                tr.SetWidth(stub_w); tr.SetLayer(pcbnew.F_Cu)
                tr.SetNetCode(pad.GetNetCode()); board.Add(tr)
                occupied.append(v.GetBoundingBox()); occupied.append(tr.GetBoundingBox())
                placed += 1; done = True
                break
            if not done:
                skipped += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"fanout: {placed} vias placed, {skipped} pads skipped (no free spot)")


def export_dsn(board: pcbnew.BOARD) -> None:
    DSN.parent.mkdir(exist_ok=True)
    ok = pcbnew.ExportSpecctraDSN(board, str(DSN))
    print("DSN export", "ok" if ok else "FAILED", DSN.relative_to(HW))


LITE_DSN = HW / "routing" / "brain-drain-lite.dsn"
LITE_SES = HW / "routing" / "brain-drain-lite.ses"


def filter_dsn(d: design.Design) -> None:
    """Write a DSN containing only the single-ended, non-bay nets: power, control, GPIO, I2C.

    Differential pairs and the four bay sheets are left for hand routing, so the
    autorouter gets a problem it can finish. Textual filter: the DSN's
    (string_quote ") directive defeats a generic s-expression parser."""
    text = DSN.read_text()
    skip = bay_nets(d) | diff_pair_nets(d) | POWER_NETS | {n for n in d.nets if n.startswith(('12V_BAY', '5V_BAY'))}

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
    if JAR is None:
        print("no freerouting jar in tools/freerouting/"); return 1
    cmd = ["java", "-Djava.awt.headless=true", "-jar", str(JAR), "-de", str(DSN), "-do", str(SES), "-mp", str(passes)]
    print(" ".join(cmd))
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, stdin=subprocess.DEVNULL)
    (HW / "routing" / "freerouting.log").write_text(cp.stdout + cp.stderr)
    print("freerouting rc", cp.returncode, "->", SES.exists())
    return cp.returncode


def import_ses(board: pcbnew.BOARD, d: design.Design) -> None:
    ses = LITE_SES if LITE_SES.exists() else SES
    ok = pcbnew.ImportSpecctraSES(board, str(ses))
    print("SES import", "ok" if ok else "FAILED")
    bays = bay_nets(d)
    removed = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() in bays:
            board.Remove(t); removed += 1
    print(f"removed {removed} bay-net track segments/vias (rerouted after the SATA footprint lands)")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def stats(board: pcbnew.BOARD) -> None:
    tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    length = sum(t.GetLength() for t in tracks) / 1e6
    print(f"tracks {len(tracks)} ({length:.0f} mm), vias {len(vias)}, zones {len(board.Zones())}")


def main(cmd: str) -> int:
    d = design.build()
    board = pcbnew.LoadBoard(str(PCB))
    if cmd in ("prepare", "all"):
        prepare(board, d)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd in ("fanout", "all"):
        fanout(board)
        pcbnew.SaveBoard(str(PCB), board)
    if cmd in ("dsn", "all"):
        export_dsn(board)
        filter_dsn(d)
    if cmd == "all":
        if run_freerouting() != 0:
            return 1
    if cmd in ("import", "all"):
        import_ses(board, d)
        pcbnew.SaveBoard(str(PCB), board)
    stats(board)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
