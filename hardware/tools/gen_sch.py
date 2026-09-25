"""Render design.py into KiCad 9 schematic files (label-based) and run ERC.

Output (hardware/):
  brain-drain.kicad_pro, brain-drain.kicad_sch (root with sheet symbols),
  sheets/<name>.kicad_sch, sym-lib-table, erc.json (from kicad-cli)

Every pin gets a short wire stub and a label: a local label when the net stays
on one sheet, a global label when it crosses sheets. Unconnected pins get a
no-connect marker. Power nets that have no driving output get a PWR_FLAG.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys

import design
import kilib
import sexp
from sexp import Str, new_uuid

import project as _project

PRJ = _project.current()
HW = PRJ.dir
PROJECT = PRJ.name
SHEET_DIR = PRJ.sheets
STUB = 5.08
GRID = 1.27
MARGIN_X = 30.0
MARGIN_Y = 25.0
PAPER = "A3"
PAPER_W, PAPER_H = 420.0, 297.0


def snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


# ------------------------------------------------------------------ geometry

def rot_vec(dx, dy, rot):
    """Rotate a schematic-space vector (y down) counter-clockwise (visually) by rot degrees."""
    r = rot % 360
    if r == 0:
        return dx, dy
    if r == 90:
        return dy, -dx
    if r == 180:
        return -dx, -dy
    return -dy, dx


class Placed:
    def __init__(self, comp: design.Comp, unit: int, x: float, y: float):
        self.comp, self.unit, self.x, self.y = comp, unit, x, y
        self.sd = comp.sym()
        self.rot = comp.rotation
        self.uuid = new_uuid()

    def pin_pos(self, p: kilib.PinGeo):
        dx, dy = rot_vec(p.x, -p.y, self.rot)
        return snap(self.x + dx), snap(self.y + dy)

    def pin_outward(self, p: kilib.PinGeo):
        a = math.radians(p.angle)
        ox, oy = -math.cos(a), math.sin(a)  # symbol coords -> schematic y-down
        ox, oy = rot_vec(ox, oy, self.rot)
        return round(ox), round(oy)

    def bbox(self):
        x0, y0, x1, y1 = self.sd.bbox(self.unit)
        corners = [rot_vec(x0, -y0, self.rot), rot_vec(x1, -y1, self.rot), rot_vec(x0, -y1, self.rot), rot_vec(x1, -y0, self.rot)]
        xs = [c[0] for c in corners]; ys = [c[1] for c in corners]
        return self.x + min(xs), self.y + min(ys), self.x + max(xs), self.y + max(ys)


# ------------------------------------------------------------------ emitters

def font(size=1.27, hide=False, justify=None):
    e = ["effects", ["font", ["size", size, size]]]
    if justify:
        e.append(["justify"] + justify)
    if hide:
        e.append(["hide", "yes"])
    return e


def prop(name, value, x, y, rot=0, hide=False, justify=None):
    return ["property", Str(name), Str(value), ["at", sexp.fmt(x), sexp.fmt(y), rot], font(1.27, hide, justify)]


def wire(x1, y1, x2, y2):
    return ["wire", ["pts", ["xy", sexp.fmt(x1), sexp.fmt(y1)], ["xy", sexp.fmt(x2), sexp.fmt(y2)]],
            ["stroke", ["width", 0], ["type", "default"]], ["uuid", Str(new_uuid())]]


def label(text, x, y, rot, is_global):
    just = ["right"] if rot == 180 else ["left"]
    if is_global:
        return ["global_label", Str(text), ["shape", "bidirectional"], ["at", sexp.fmt(x), sexp.fmt(y), rot],
                ["fields_autoplaced", "yes"], font(1.27, justify=just), ["uuid", Str(new_uuid())],
                prop("Intersheetrefs", "${INTERSHEET_REFS}", x, y, 0, hide=True)]
    return ["label", Str(text), ["at", sexp.fmt(x), sexp.fmt(y), rot], font(1.27, justify=just + ["bottom"]),
            ["uuid", Str(new_uuid())]]


def no_connect(x, y):
    return ["no_connect", ["at", sexp.fmt(x), sexp.fmt(y)], ["uuid", Str(new_uuid())]]


def symbol_instance(pl: Placed, root_uuid: str, sheet_uuid: str):
    c, sd = pl.comp, pl.sd
    x0, y0, x1, y1 = pl.bbox()
    node = ["symbol", ["lib_id", Str(sd.lib_id)], ["at", sexp.fmt(pl.x), sexp.fmt(pl.y), pl.rot], ["unit", pl.unit],
            ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "yes" if c.dnp else "no"],
            ["uuid", Str(pl.uuid)],
            prop("Reference", c.ref, x0, y0 - 2.0, justify=["left"]),
            prop("Value", c.value, x0, y1 + 2.5, justify=["left"]),
            prop("Footprint", c.footprint, pl.x, pl.y, hide=True),
            prop("Datasheet", "~", pl.x, pl.y, hide=True),
            prop("Description", c.note or "", pl.x, pl.y, hide=True)]
    for p in sd.pins_of_unit(pl.unit):
        node.append(["pin", Str(p.number), ["uuid", Str(new_uuid())]])
    node.append(["instances", ["project", Str(PROJECT), ["path", Str(f"/{root_uuid}/{sheet_uuid}"),
                                                          ["reference", Str(c.ref)], ["unit", pl.unit]]]])
    return node


def sheet_symbol(name, file, x, y, w, h, root_uuid, page):
    return ["sheet", ["at", sexp.fmt(x), sexp.fmt(y)], ["size", sexp.fmt(w), sexp.fmt(h)], ["exclude_from_sim", "no"],
            ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"],
            ["stroke", ["width", 0.1524], ["type", "solid"]], ["fill", ["color", 0, 0, 0, 0.0]],
            ["uuid", Str(new_uuid())],
            prop("Sheetname", name, x, y - 0.7, justify=["left", "bottom"]),
            prop("Sheetfile", file, x, y + h + 0.7, justify=["left", "top"]),
            ["instances", ["project", Str(PROJECT), ["path", Str(f"/{root_uuid}"), ["page", Str(str(page))]]]]]


def schematic(uuid, paper, title, body, lib_symbols, sheet_instances=None):
    node = ["kicad_sch", ["version", 20250114], ["generator", Str("brain-drain-gen_sch")], ["generator_version", Str("9.0")],
            ["uuid", Str(uuid)], ["paper", Str(paper)],
            ["title_block", ["title", Str(title)], ["rev", Str("v0-generated")], ["company", Str("brain-drain")]],
            ["lib_symbols"] + lib_symbols] + body
    if sheet_instances is not None:
        node.append(["sheet_instances"] + sheet_instances)
    node.append(["embedded_fonts", "no"])
    return sexp.emit(node) + "\n"


# ------------------------------------------------------------------ layout

def place_sheet(d: design.Design, sheet: str) -> list[Placed]:
    """Row-major grid placement of every (component, unit) that belongs to this sheet."""
    items = []
    for c in d.comps.values():
        sd = c.sym()
        for u in sd.units():
            if c.unit_sheets.get(u, c.sheet) == sheet:
                items.append((c, u))
    # big symbols first, then by ref
    def key(cu):
        c, u = cu
        x0, y0, x1, y1 = c.sym().bbox(u)
        return (-(x1 - x0) * (y1 - y0), c.ref, u)
    items.sort(key=key)
    placed = []
    x, y = MARGIN_X, MARGIN_Y
    row_h = 0.0
    for c, u in items:
        pl = Placed(c, u, 0, 0)
        x0, y0, x1, y1 = pl.bbox()
        w = (x1 - x0) + 2 * STUB + 2 * 26.0  # room for labels each side
        h = (y1 - y0) + 12.0
        if x + w > PAPER_W - MARGIN_X and x > MARGIN_X:
            x = MARGIN_X
            y += row_h + 4.0
            row_h = 0.0
        pl.x, pl.y = snap(x - x0 + STUB + 26.0), snap(y - y0 + 6.0)
        placed.append(pl)
        x += w
        row_h = max(row_h, h)
    return placed


def render_sheet(d: design.Design, sheet: str, root_uuid: str, sheet_uuid: str, pin_net, needs_flag):
    sexp._counter[0] = 100000 * (1 + [n for n, _ in d.sheets].index(sheet))
    placed = place_sheet(d, sheet)
    body = []
    libs: dict[str, list] = {}
    for pl in placed:
        libs.setdefault(pl.sd.lib_id, kilib.embedded_node(pl.sd))
        body.append(symbol_instance(pl, root_uuid, sheet_uuid))
        for p in pl.sd.pins_of_unit(pl.unit):
            px, py = pl.pin_pos(p)
            ox, oy = pl.pin_outward(p)
            rp = (pl.comp.ref, p.number)
            net = pin_net.get(rp)
            if net is None:
                body.append(no_connect(px, py))
                continue
            ex, ey = snap(px + ox * STUB), snap(py + oy * STUB)
            body.append(wire(px, py, ex, ey))
            is_global = len(d.net_sheets(net)) > 1 or net in d.pwr_flags
            if ox < 0:
                rot = 180
            elif ox > 0:
                rot = 0
            elif oy < 0:
                rot = 90
            else:
                rot = 270
            body.append(label(net, ex, ey, rot, is_global))
    # PWR_FLAGs for nets assigned to this sheet
    fx, fy = MARGIN_X, PAPER_H - MARGIN_Y - 10
    for net in sorted(needs_flag.get(sheet, [])):
        flag_sd = kilib.get("power:PWR_FLAG")
        libs.setdefault(flag_sd.lib_id, kilib.embedded_node(flag_sd))
        fc = design.Comp(f"#FLG_{net}", "power:PWR_FLAG", "PWR_FLAG", sheet)
        pl = Placed(fc, 1, snap(fx), snap(fy))
        body.append(symbol_instance(pl, root_uuid, sheet_uuid))
        p = flag_sd.pins[0]
        px, py = pl.pin_pos(p)
        body.append(wire(px, py, px, py + STUB))
        body.append(label(net, px, py + STUB, 270, True))
        fx += 22.0
    # notes
    ny = PAPER_H - MARGIN_Y + 4
    for i, n in enumerate(d.notes.get(sheet, [])):
        body.append(["text", Str(n), ["exclude_from_sim", "no"], ["at", sexp.fmt(MARGIN_X), sexp.fmt(ny + i * 4.5), 0],
                     font(1.5, justify=["left", "bottom"]), ["uuid", Str(new_uuid())]])
    desc = dict(d.sheets)[sheet]
    body.insert(0, ["text", Str(f"{sheet}: {desc}"), ["exclude_from_sim", "no"], ["at", sexp.fmt(MARGIN_X), 12, 0],
                    font(3.0, justify=["left", "bottom"]), ["uuid", Str(new_uuid())]])
    return schematic(sheet_uuid, PAPER, f"{PROJECT} — {sheet}", body, list(libs.values())), len(placed)


def assign_flags(d: design.Design) -> dict[str, set[str]]:
    """Which sheet carries the PWR_FLAG for each flagged net (the first sheet the net appears on)."""
    out: dict[str, set[str]] = {}
    order = [s for s, _ in d.sheets]
    for net in d.pwr_flags:
        # a net already driven by a power-output pin must not get a flag (ERC: output vs output)
        driven = any(next(pp for pp in d.comps[r].sym().pins if pp.number == n).etype == "power_out"
                     for r, n in d.nets[net])
        if driven:
            continue
        sheets = d.net_sheets(net)
        first = min(sheets, key=order.index)
        out.setdefault(first, set()).add(net)
    return out


def write_project(root_uuid: str, sheet_uuids: dict[str, str]):
    pro = {
        "board": {"design_settings": {"defaults": {}, "rules": {}}, "layer_presets": [], "viewports": []},
        "boards": [], "cvpcb": {"equivalence_files": []}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.2, "via_diameter": 0.6,
                                      "via_drill": 0.3, "diff_pair_width": 0.2, "diff_pair_gap": 0.25}], "meta": {"version": 4}},
        "pcbnew": {"page_layout_descr_file": ""},
        "schematic": {"drawing": {"default_font": "KiCad Font"}, "legacy_lib_dir": "", "legacy_lib_list": [], "meta": {"version": 1}},
        "sheets": [[root_uuid, "Root"]] + [[u, n] for n, u in sheet_uuids.items()],
        "text_variables": {},
    }
    old = HW / f"{PROJECT}.kicad_pro"
    if old.exists():   # keep the net classes route.py prepare wrote (the project is their only home)
        try:
            prev = json.loads(old.read_text())
            if len(prev.get("net_settings", {}).get("classes", [])) > 1:
                pro["net_settings"] = prev["net_settings"]
            # the board design rules (min via / drill / clearances, written by route.py prepare) live here too
            prev_rules = prev.get("board", {}).get("design_settings", {}).get("rules", {})
            if prev_rules:
                pro["board"]["design_settings"]["rules"] = prev_rules
        except ValueError:
            pass
    old.write_text(json.dumps(pro, indent=2) + "\n")
    used_syms = sorted({c.lib_id.split(":")[0] for c in design.build(PRJ.key).comps.values()} | {"power"})
    rows = [f'  (lib (name "brain-drain")(type "KiCad")(uri "{PRJ.lib_uri}/brain-drain.kicad_sym")(options "")(descr "brain-drain project symbols"))']
    rows += [f'  (lib (name "{n}")(type "KiCad")(uri "${{KICAD9_SYMBOL_DIR}}/{n}.kicad_sym")(options "")(descr ""))'
             for n in used_syms if n != "brain-drain"]
    (HW / "sym-lib-table").write_text("(sym_lib_table\n  (version 7)\n" + "\n".join(rows) + "\n)\n")
    used_fps = sorted({c.footprint.split(":")[0] for c in design.build(PRJ.key).comps.values() if ":" in c.footprint})
    rows = [f'  (lib (name "brain-drain")(type "KiCad")(uri "{PRJ.lib_uri}/brain-drain.pretty")(options "")(descr "brain-drain project footprints"))']
    rows += [f'  (lib (name "{n}")(type "KiCad")(uri "${{KICAD9_FOOTPRINT_DIR}}/{n}.pretty")(options "")(descr ""))'
             for n in used_fps if n != "brain-drain"]
    (HW / "fp-lib-table").write_text("(fp_lib_table\n  (version 7)\n" + "\n".join(rows) + "\n)\n")
    (_project.HW / "lib" / "brain-drain.pretty").mkdir(exist_ok=True)


def main(run_erc=True) -> int:
    d = design.build(PRJ.key)
    missing = d.check()
    if missing:
        print("design has unassigned pins:", missing[:10])
        return 2
    SHEET_DIR.mkdir(exist_ok=True)
    for stale in SHEET_DIR.glob("*.kicad_sch"):   # sheets of an earlier design (e.g. the four on-board bridges before the bay cards)
        if stale.stem not in {n for n, _ in d.sheets}:
            stale.unlink(); print("removed stale sheet", stale.name)
    root_uuid = "0b6a1e2a-0000-4000-8000-000000000001"
    sheet_uuids = {name: f"0b6a1e2a-0000-4000-8000-{i + 2:012d}" for i, (name, _) in enumerate(d.sheets)}
    pin_net = d.pin_net()
    flags = assign_flags(d)
    counts = {}
    for name, _ in d.sheets:
        text, n = render_sheet(d, name, root_uuid, sheet_uuids[name], pin_net, flags)
        (SHEET_DIR / f"{name}.kicad_sch").write_text(text)
        counts[name] = n
    # root sheet: one sheet symbol per sub-sheet
    body = []
    cols = 4
    for i, (name, desc) in enumerate(d.sheets):
        x = MARGIN_X + (i % cols) * 130.0
        y = MARGIN_Y + (i // cols) * 45.0
        body.append(sheet_symbol(name, f"sheets/{name}.kicad_sch", x, y, 110.0, 30.0, root_uuid, i + 2))
        body.append(["text", Str(desc), ["exclude_from_sim", "no"], ["at", sexp.fmt(x + 2), sexp.fmt(y + 8), 0],
                     font(1.4, justify=["left", "top"]), ["uuid", Str(new_uuid())]])
    body.insert(0, ["text", Str(d.title), ["exclude_from_sim", "no"], ["at", sexp.fmt(MARGIN_X), 14, 0],
                    font(4.0, justify=["left", "bottom"]), ["uuid", Str(new_uuid())]])
    (HW / f"{PROJECT}.kicad_sch").write_text(
        schematic(root_uuid, "A3", d.title, body, [], sheet_instances=[["path", Str("/"), ["page", Str("1")]]]))
    write_project(root_uuid, sheet_uuids)
    print(f"wrote {len(d.sheets)} sheets:", ", ".join(f"{k}({v})" for k, v in counts.items()))
    if not run_erc:
        return 0
    rep = HW / "erc.json"
    cp = subprocess.run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "-o", str(rep),
                         str(HW / f"{PROJECT}.kicad_sch")], capture_output=True, text=True)
    print(cp.stdout.strip()[-400:], cp.stderr.strip()[-400:])
    if rep.exists():
        j = json.loads(rep.read_text())
        tot = {}
        for sh in j.get("sheets", []):
            for v in sh.get("violations", []):
                tot[(v["severity"], v["type"])] = tot.get((v["severity"], v["type"]), 0) + 1
        for (sev, typ), n in sorted(tot.items()):
            print(f"  {sev:8s} {typ:32s} {n}")
        print("ERC violations:", sum(tot.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(run_erc="--no-erc" not in sys.argv))
