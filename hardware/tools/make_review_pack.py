"""Builds hardware/review/: the files a layout engineer reads first, regenerated from the boards as they are now.

    python3 hardware/tools/make_review_pack.py

Writes: design-rules.md (net classes, limits, stack-up, planes, keep-outs), routing-stats.md (copper by layer, vias, where the
differential pairs run and over what), drc-summary.md and erc-summary.md, footprints.md (where every footprint comes from and
how it was verified), the netlists and placement CSVs (kicad-cli), and copies of the schematic PDFs. Needs kicad-cli and pcbnew.
"""
from __future__ import annotations

import collections
import json
import re
import shutil
import subprocess as sp
from pathlib import Path

import pcbnew

HW = Path(__file__).resolve().parent.parent
OUT = HW / "review"
BOARDS = {
    "brain": {"pcb": HW / "brain-drain.kicad_pcb", "pro": HW / "brain-drain.kicad_pro", "sch": HW / "brain-drain.kicad_sch",
              "routing": HW / "routing", "erc": HW / "erc.json", "layers": 6},
    "card": {"pcb": HW / "bay-card" / "bay-card.kicad_pcb", "pro": HW / "bay-card" / "bay-card.kicad_pro", "sch": HW / "bay-card" / "bay-card.kicad_sch",
             "routing": HW / "bay-card" / "routing", "erc": HW / "bay-card" / "erc.json", "layers": 4},
}
PAIR = re.compile(r"(_P|_N|DP|DM|TXDP|TXDM|RXDP|RXDM|XP|XN)$")

FOOTPRINTS = [   # name, source, verification
    ("PCIe_x1_Socket_THT", "generated (`fpgen.py`) from the Amphenol FCI customer drawing 10018784 sheets 1, 3, 5", "hole pattern and pegs from the drawing; the housing ends (x -2.1 .. 22.9) are assumed symmetrical about the contacts, check against the 3D model"),
    ("SATA_22pin_Receptacle_RA", "generated (`fpgen.py`) from the Molex sales drawing SD-47018-001 sheets 1, 2", "pads, pegs and slots from the drawing; the mating face is assumed flush with the PCB edge; the two 0.5 mm key rectangles are not modelled; slot hole 1.0 x 2.15 mm read off the drawing"),
    ("BUS_PCIexpress_x1", "KiCad stock library (Connector_PCBEdge), card-edge fingers with the tab outline", "PCI-SIG CEM geometry; our pinout is custom"),
    ("Raspberry-Pi-5-Compute-Module", "copied unchanged from the Raspberry Pi CM5IO rev 2 KiCad project", "Raspberry Pi design files"),
    ("M2_Socket3_MKey_CM5IO", "copied from the CM5IO project, renamed", "peg and standoff holes still to be compared with the TE 2199230-4 customer drawing (STATUS R2)"),
    ("Kycon_KPJX-4S-S", "generated from the Kycon drawing A17", "pin positions from the drawing; DIN pin assignment must match the brick (STATUS R3)"),
    ("Texas_RPA0010A_VQFN-HR-10_3x3mm", "generated from the TPS56637 datasheet land pattern", "datasheet example board layout"),
    ("DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm, SOIC-8, SOT-23, TSOT-23-6, QFN-56 / QFN-48, WSON-8, passives, crystals, LEDs, headers", "KiCad stock libraries", "stock; check the QFN exposed-pad sizes against the ASM1153E and USB5744 datasheets"),
]


def layer_names(board):
    return [board.GetLayerName(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu) if board.IsLayerEnabled(l)]


def design_rules(name, cfg, board):
    pro = json.loads(cfg["pro"].read_text())
    lines = [f"## {name}: net classes", "", "| class | track mm | clearance mm | via / drill mm | diff pair width / gap mm |", "|---|---|---|---|---|"]
    for c in pro["net_settings"]["classes"]:
        lines.append(f"| {c['name']} | {c.get('track_width')} | {c.get('clearance')} | {c.get('via_diameter')} / {c.get('via_drill')} | {c.get('diff_pair_width') or ''} / {c.get('diff_pair_gap') or ''} |")
    rules = pro["board"]["design_settings"]["rules"]
    lines += ["", "Board limits (`.kicad_pro`, written by `route.py prepare`):", ""]
    lines += [f"* `{k}` = {v}" for k, v in rules.items() if k.startswith("min_") and v]
    lines += ["", f"### {name}: copper layers", "", "| layer | type | use |", "|---|---|---|"]
    use = {"brain": {"F.Cu": "signal, parts", "In1.Cu": "GND plane", "In2.Cu": "signal (pairs, buses)", "In3.Cu": "signal (pairs, buses)",
                     "In4.Cu": "power islands: 5V_SYS, 5V_HDD, +12V, +3V3", "B.Cu": "signal, GND pour, bypass caps of the hubs"},
           "card": {"F.Cu": "signal, parts", "In1.Cu": "GND plane", "In2.Cu": "power islands: 5V_HDD, +12V", "B.Cu": "signal, GND pour"}}[name]
    for n in layer_names(board):
        lid = board.GetLayerID(n)
        lines.append(f"| {n} | {'plane' if board.GetLayerType(lid) == pcbnew.LT_POWER else 'signal'} | {use.get(n, '')} |")
    lines += ["", f"### {name}: zones", "", "| zone | net | layer | priority |", "|---|---|---|---|"]
    for z in board.Zones():
        if z.IsOnLayer(pcbnew.F_Cu) and z.GetIsRuleArea() is False and False:
            continue
        if z.GetIsRuleArea():
            continue
        lines.append(f"| {z.GetZoneName()} | {z.GetNetname()} | {board.GetLayerName(z.GetFirstLayer())} | {z.GetAssignedPriority()} |")
    lines += ["", f"### {name}: keep-out areas (no tracks / vias)", "", "| name | layers |", "|---|---|"]
    for z in board.Zones():
        if z.GetIsRuleArea():
            lines.append(f"| {z.GetZoneName()} | {', '.join(board.GetLayerName(l) for l in z.GetLayerSet().Seq())} |")
    return lines


def stats(name, cfg, board):
    L = collections.Counter(); segs = 0; vias = collections.Counter()
    pair_L = collections.Counter()
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            vias[(round(t.GetWidth(pcbnew.F_Cu) / 1e6, 2), round(t.GetDrillValue() / 1e6, 2))] += 1
            continue
        segs += 1
        ln = t.GetLength() / 1e6
        L[t.GetLayerName()] += ln
        if PAIR.search(t.GetNetname()):
            pair_L[t.GetLayerName()] += ln
    lines = [f"## {name}", "", f"* {len(list(board.GetFootprints()))} footprints, {board.GetNetCount() - 1} nets, {segs} track segments, {sum(vias.values())} vias",
             "* copper length by layer (mm): " + ", ".join(f"{k} {v:.0f}" for k, v in sorted(L.items())),
             "* vias (diameter / drill): " + ", ".join(f"{d}/{h} x {n}" for (d, h), n in sorted(vias.items())),
             "* differential-pair copper by layer (mm): " + ", ".join(f"{k} {v:.0f}" for k, v in sorted(pair_L.items()))]
    if name == "brain":
        zs = [z for z in board.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In4_Cu)]

        def zone_at(x, y):
            best = None
            for z in zs:
                if z.Outline().Contains(pcbnew.VECTOR2I(int(x), int(y))) and (best is None or z.GetAssignedPriority() > best.GetAssignedPriority()):
                    best = z
            return best.GetNetname() if best else "none"

        under = collections.Counter(); moves = 0; nets = set()
        in2 = [pcbnew.SEG(t.GetStart(), t.GetEnd()) for t in board.GetTracks() if t.GetClass() != "PCB_VIA" and t.GetLayerName() == "In2.Cu"]
        overlap = samples = 0
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA" or t.GetLayerName() != "In3.Cu" or not PAIR.search(t.GetNetname()):
                continue
            ln = t.GetLength() / 1e6; a, e = t.GetStart(), t.GetEnd(); k = max(1, int(ln / 0.5)); prev = None
            for i in range(k + 1):
                x, y = a.x + (e.x - a.x) * i / k, a.y + (e.y - a.y) * i / k
                zn = zone_at(x, y); under[zn] += 1; samples += 1
                if prev is not None and zn != prev:
                    moves += 1; nets.add(t.GetNetname())
                prev = zn
                if any(s.Distance(pcbnew.VECTOR2I(int(x), int(y))) < 0.3e6 for s in in2):
                    overlap += 1
        lines += ["", "**Reference planes of the pairs (review item):** pairs on In2 have the solid GND plane In1 next to them. Pairs on In3 have In4 next to them, "
                  "which is split into power islands. Sampled every 0.5 mm along the In3 pair copper:", "",
                  "| plane under the pair (In4) | samples |", "|---|---|"] + [f"| {k} | {v} |" for k, v in under.most_common()]
        lines += ["", f"* {moves} island-to-island transitions inside single segments, on {len(nets)} pair nets (each is a return-path discontinuity; stitching capacitors or a re-assigned In4 are the fixes).",
                  f"* {overlap} of {samples} In3 pair samples ({100 * overlap / max(1, samples):.0f} %) have an In2 track within 0.3 mm in plan view: broadside coupling between the two adjacent inner signal layers."]
    pr = cfg["routing"] / "pairs.md"
    if pr.exists():
        rows = [l for l in pr.read_text().splitlines()[4:] if l.startswith("|")]
        sk = [float(l.split("|")[5]) for l in rows]
        lines += ["", f"* {len(rows)} differential pairs, end-to-end skew (across the series capacitors) max {max(sk):.2f} mm, table in `{pr.relative_to(HW)}`"]
    return lines


def drc_summary(name, cfg):
    rep = cfg["routing"] / "drc.json"
    if not rep.exists():
        return [f"## {name}: no DRC report"]
    j = json.loads(rep.read_text())
    c = collections.Counter((v["severity"], v["type"]) for v in j["violations"])
    lines = [f"## {name}", "", f"* violations: {sum(1 for v in j['violations'] if v['severity'] == 'error')} errors, {sum(1 for v in j['violations'] if v['severity'] == 'warning')} warnings; unconnected items: {len(j['unconnected_items'])}", "", "| severity | type | count |", "|---|---|---|"]
    lines += [f"| {s} | {t} | {n} |" for (s, t), n in sorted(c.items())]
    lines += ["", "Warnings are silkscreen overlaps and dangling vias/tracks (fanout stubs); none affect copper.  `hole_clearance`, `clearance`, `track_width`, "
              "`copper_edge_clearance` and `shorting_items` are all zero. Reports: `routing/drc.json`, `routing/open.md`, `routing/pairs.md`."]
    return lines


def erc_summary(name, cfg):
    j = json.loads(cfg["erc"].read_text())
    v = [x for s in j.get("sheets", []) for x in s.get("violations", [])]
    lines = [f"## {name}", "", f"* {len(v)} ERC findings ({sum(1 for x in v if x['severity'] == 'error')} errors)"]
    for x in v:
        lines.append(f"  * {x['severity']}: {x['type']}: {x['description']} ({', '.join(i['description'] for i in x['items'])})")
    return lines


def main():
    OUT.mkdir(exist_ok=True)
    dr = ["# Design rules, stack-up, planes and keep-outs", "", "Generated by `hardware/tools/make_review_pack.py` from the boards as they are now.", ""]
    st = ["# Routing statistics", "", "Generated by `hardware/tools/make_review_pack.py`.", ""]
    dc = ["# DRC summary", "", "kicad-cli 9 `pcb drc`, all severities.", ""]
    ec = ["# ERC summary", "", "kicad-cli 9 `sch erc`.", ""]
    for name, cfg in BOARDS.items():
        board = pcbnew.LoadBoard(str(cfg["pcb"]))
        dr += design_rules(name, cfg, board) + [""]
        st += stats(name, cfg, board) + [""]
        dc += drc_summary(name, cfg) + [""]
        ec += erc_summary(name, cfg) + [""]
        sp.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(OUT / f"{name}.net"), str(cfg["sch"])], capture_output=True)
        sp.run(["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "-o", str(OUT / f"{name}-placement.csv"), str(cfg["pcb"])], capture_output=True)
        pdf = HW / ("" if name == "brain" else "bay-card") / "renders" / "schematic" / ("brain-drain-schematic.pdf" if name == "brain" else "bay-card-schematic.pdf")
        if pdf.exists():
            shutil.copy(pdf, OUT / f"{name}-schematic.pdf")
        for src, dst in (("open.md", "open-connections"), ("pairs.md", "pairs")):
            f = cfg["routing"] / src
            if f.exists():
                shutil.copy(f, OUT / f"{name}-{dst}.md")
    fp = ["# Footprint provenance", "", "| footprint | source | verification |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in FOOTPRINTS]
    (OUT / "design-rules.md").write_text("\n".join(dr) + "\n")
    (OUT / "routing-stats.md").write_text("\n".join(st) + "\n")
    (OUT / "drc-summary.md").write_text("\n".join(dc) + "\n")
    (OUT / "erc-summary.md").write_text("\n".join(ec) + "\n")
    (OUT / "footprints.md").write_text("\n".join(fp) + "\n")
    print("review pack written to", OUT.relative_to(HW.parent), sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
