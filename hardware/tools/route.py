"""Routing pipeline on KiCad's pcbnew API (KiCad 9):

  python3 tools/route.py prepare   net classes, diff-pair rules, copper zones -> brain-drain.kicad_pcb
  python3 tools/route.py dsn       export Specctra DSN for freerouting
  python3 tools/route.py import    import the freerouting session, strip bay-net tracks, fill zones, DRC
  python3 tools/route.py all       prepare + dsn + freerouting + import

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
    ncs = ds.m_NetSettings  # NET_SETTINGS
    # net classes
    nc_default = ncs.GetDefaultNetclass()
    nc_default.SetTrackWidth(MM(0.2)); nc_default.SetClearance(MM(0.15))
    nc_default.SetViaDiameter(MM(0.6)); nc_default.SetViaDrill(MM(0.3))
    for name, width, clearance, gap in (("Power", 0.6, 0.2, 0.0), ("DiffPair90", 0.15, 0.15, 0.15), ("Bay", 0.25, 0.15, 0.0)):
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
    ox, oy = 20.0, 20.0
    W, H = 180.0, 110.0

    def zone(net_name, layer, rect, priority=0):
        net = board.GetNetcodeFromNetname(net_name)
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNetCode(net)
        z.SetAssignedPriority(priority)
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        x0, y0, x1, y1 = rect
        pts = [pcbnew.VECTOR2I(MM(ox + x0), MM(oy + y0)), pcbnew.VECTOR2I(MM(ox + x1), MM(oy + y0)),
               pcbnew.VECTOR2I(MM(ox + x1), MM(oy + y1)), pcbnew.VECTOR2I(MM(ox + x0), MM(oy + y1))]
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
    zone("+12V", pcbnew.In2_Cu, (0, 0, 42, 82), 1)          # input, bucks, bay switch feed
    zone("5V_SYS", pcbnew.In2_Cu, (42, 28, 180, 110), 1)    # CM5, hubs, bridges (VBUS/VCCIN), M.2 power parts
    zone("5V_HDD", pcbnew.In2_Cu, (42, 0, 180, 28), 1)      # bay switch row
    zone("+3V3", pcbnew.In2_Cu, (100, 28, 180, 62), 2)      # hub B / M.2 region, higher priority island
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print(f"net classes set; {len(assignments)} nets assigned ({sum(v == 'Bay' for v in assignments.values())} bay, "
          f"{sum(v == 'DiffPair90' for v in assignments.values())} diff-pair); zones filled")


def export_dsn(board: pcbnew.BOARD) -> None:
    DSN.parent.mkdir(exist_ok=True)
    ok = pcbnew.ExportSpecctraDSN(board, str(DSN))
    print("DSN export", "ok" if ok else "FAILED", DSN.relative_to(HW))


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
    ok = pcbnew.ImportSpecctraSES(board, str(SES))
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
    if cmd in ("dsn", "all"):
        export_dsn(board)
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
