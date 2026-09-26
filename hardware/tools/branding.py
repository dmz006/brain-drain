"""Silkscreen branding on the top (F.SilkS) of the boards: the octopus-brain logo, the name and the repository URL, so someone
who opens the lid can read what the board is and where its files live.

    python3 tools/branding.py brain    # hardware/brain-drain.kicad_pcb
    python3 tools/branding.py card     # hardware/bay-card/bay-card.kicad_pcb
    python3 tools/branding.py brain --dry     # only report where it would go

Finds the largest free area itself (no footprint, reference designator, via or board edge inside the block), draws the logo
as 0.15 mm silk lines from docs/img/logo.svg (via logo_geom.py), and puts everything in one group called "branding" so a
second run replaces the first. Silk does not touch copper, so this can run on an already routed board (route_full.sh runs it
after routing). Nothing under the CM5 module, the M.2 SSD or the front strip is used because those are covered when the lid opens.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logo_geom  # noqa: E402

HW = Path(__file__).resolve().parent.parent
BOARDS = {"brain": HW / "brain-drain.kicad_pcb", "card": HW / "bay-card" / "bay-card.kicad_pcb"}
URL = "github.com/dmz006/brain-drain"
NAME = "BRAIN-DRAIN"
LW = 0.2             # silk line width (typical fab minimum is 0.15; stay above it)
LW_BOLD = 0.3        # tentacles
NM = 1e6
CELL = 0.5
GROUP = "branding"
REV = "1.0"          # board revision printed on the silkscreen and set in the KiCad title block; bump it when the fab files change

TITLES = {"brain": "brain board", "card": "bay card"}


def mm(v):
    return int(round(v * NM))


def P(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


class Sil:
    def __init__(self, board):
        self.b = board
        self.group = pcbnew.PCB_GROUP(board)
        self.group.SetName(GROUP)
        board.Add(self.group)
        self.n = 0

    def _add(self, item):
        item.SetLayer(pcbnew.F_SilkS)
        self.b.Add(item)
        self.group.AddItem(item)
        self.n += 1

    def line(self, a, b, w=LW):
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetWidth(mm(w))
        self._add(s)

    def poly(self, pts, closed=False, w=LW):
        for i in range(len(pts) - 1):
            self.line(pts[i], pts[i + 1], w)
        if closed:
            self.line(pts[-1], pts[0], w)

    def dot(self, c, r):   # filled circle
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetStart(P(*c)); s.SetEnd(P(c[0] + r, c[1])); s.SetWidth(mm(LW)); s.SetFilled(True)
        self._add(s)

    def text(self, s, x, y, h, thick, align="center"):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s); t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(thick))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER if align == "center" else pcbnew.GR_TEXT_H_ALIGN_LEFT)
        t.SetPosition(P(x, y))
        self._add(t)
        return t


def remove_old(board):
    for g in list(board.Groups()):
        if g.GetName() == GROUP:
            for it in list(g.GetItems()):
                board.Remove(it)
            board.Remove(g)


def occupancy(board, keepout_y_from=None):
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetX() / NM, bb.GetY() / NM, bb.GetRight() / NM, bb.GetBottom() / NM
    nx, ny = int((x1 - x0) / CELL) + 1, int((y1 - y0) / CELL) + 1
    g = np.zeros((ny, nx), bool)

    def mark(a, b, c, d, m=0.0):
        i0 = max(0, int((a - x0 - m) / CELL)); i1 = min(nx, int((c - x0 + m) / CELL) + 1)
        j0 = max(0, int((b - y0 - m) / CELL)); j1 = min(ny, int((d - y0 + m) / CELL) + 1)
        g[j0:j1, i0:i1] = True

    for fp in board.GetFootprints():
        r = fp.GetBoundingBox(False)
        mark(r.GetX() / NM, r.GetY() / NM, r.GetRight() / NM, r.GetBottom() / NM, 0.5)
        for t in (fp.Reference(), fp.Value()):
            if t.IsVisible():
                r = t.GetBoundingBox(); mark(r.GetX() / NM, r.GetY() / NM, r.GetRight() / NM, r.GetBottom() / NM, 0.3)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition(); d = t.GetWidth(pcbnew.F_Cu) / NM / 2 + 0.5
            mark(p.x / NM - d, p.y / NM - d, p.x / NM + d, p.y / NM + d)
    for d in board.GetDrawings():        # anything already drawn on the top silk or the fab layers of the board itself
        if d.GetLayer() in (pcbnew.F_SilkS,) and d.GetParentGroup() is None:
            r = d.GetBoundingBox(); mark(r.GetX() / NM, r.GetY() / NM, r.GetRight() / NM, r.GetBottom() / NM, 0.5)
    mark(x0, y0, x1, y0 + 2.5); mark(x0, y1 - 2.5, x1, y1); mark(x0, y0, x0 + 2.5, y1); mark(x1 - 2.5, y0, x1, y1)
    if keepout_y_from is not None:
        mark(x0, y0 + keepout_y_from, x1, y1)
    return g, (x0, y0, x1, y1)


def free_spots(g, w, h):
    """All top-left grid indices (j, i) where a w x h mm rectangle is free."""
    cw, ch = int(math.ceil(w / CELL)), int(math.ceil(h / CELL))
    integral = np.pad(g.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    s = integral[ch:, cw:] - integral[:-ch, cw:] - integral[ch:, :-cw] + integral[:-ch, :-cw]
    return np.argwhere(s == 0)


def find_free(g, org, w, h, prefer):
    """Top-left of the free w x h rectangle (mm) nearest to `prefer`, or None."""
    spots = free_spots(g, w, h)
    if not len(spots):
        return None
    xy = np.stack([org[0] + spots[:, 1] * CELL + w / 2, org[1] + spots[:, 0] * CELL + h / 2], 1)
    k = int(np.argmin(np.hypot(xy[:, 0] - prefer[0], xy[:, 1] - prefer[1])))
    return org[0] + spots[k, 1] * CELL, org[1] + spots[k, 0] * CELL


def simple_bbox(lg):
    xs = [p[0] for t in lg.tentacles for p in t]; ys = [p[1] for t in lg.tentacles for p in t]
    bx, by, rx, ry = lg.brain
    return (min(xs), by - ry, max(xs), max(ys + [by + ry]))


def draw_logo(sil, lg, ox, oy, scale):
    """Simplified line-art for silkscreen (no drive icons, few folds, single-line tentacles), top-left at (ox, oy);
    scale is mm per logo unit. Every stroke is at least 0.2 mm and every gap at least 0.6 mm at the sizes used (35 mm and up)."""
    x0, y0, _, _ = simple_bbox(lg)

    def T(p):
        return ((p[0] - x0) * scale + ox, (p[1] - y0) * scale + oy)

    bx, by, rx, ry = lg.brain
    sil.poly([T((bx + rx * math.cos(a), by + ry * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 73)], w=LW_BOLD)
    sil.poly([T(p) for p in lg.gyri[0]], w=LW_BOLD)                       # the fissure
    for f in lg.gyri[1:7]:                                                # the six long folds (skip the short top and side ones)
        sil.poly([T(p) for p in f], w=LW)
    for (cx, cy, erx, ery, px, py, pr) in lg.eyes:
        sil.poly([T((cx + erx * math.cos(a), cy + ery * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 25)], w=LW)
        sil.dot(T((px, py)), pr * scale * 1.1)
    for t in lg.tentacles:                                                # one bold line each, from under the brain to the tip
        run = [p for p in t if ((p[0] - bx) / (rx + 6)) ** 2 + ((p[1] - by) / (ry + 6)) ** 2 >= 1]
        if len(run) > 1:
            sil.poly([T(q) for q in run], w=LW_BOLD)
            sil.dot(T(run[-1]), 0.5)                                       # a round tip, like the suction end of the drawing


def mark_rect(g, org, x, y, w, h):
    x0, y0, _, _ = org
    i0, i1 = int((x - x0) / CELL), int((x + w - x0) / CELL) + 1
    j0, j1 = int((y - y0) / CELL), int((y + h - y0) / CELL) + 1
    g[max(j0, 0):j1, max(i0, 0):i1] = True


def text_blocks(kind):
    """Independent text blocks, each a list of (text, height mm, stroke mm), so they can sit in different free spots."""
    if kind == "brain":
        return [[(NAME, 2.6, 0.4), ("eight-bay disk sanitizer", 1.2, 0.18)],
                [(f"brain board  rev {REV}", 1.2, 0.22), (URL, 1.3, 0.2)]]
    return [[(NAME, 1.6, 0.3), (f"card rev {REV}", 1.2, 0.18)]]


def block_size(lines, width):
    return width, sum(h for _, h, _ in lines) + 0.6 * (len(lines) - 1) + 1.0


def brand(kind: str, dry: bool = False) -> str:
    """The logo as big as the free space allows (with every text block also placed), each text block in the free spot nearest the logo."""
    path = BOARDS[kind]
    board = pcbnew.LoadBoard(str(path))
    lg = logo_geom.load()
    sb = simple_bbox(lg); ar = (sb[3] - sb[1]) / (sb[2] - sb[0])
    g, org = occupancy(board, keepout_y_from=(board.GetBoardEdgesBoundingBox().GetHeight() / NM - 26) if kind == "brain" else None)
    centre = ((org[0] + org[2]) / 2, (org[1] + org[3]) / 2)
    prefer = (centre[0] - 30, centre[1]) if kind == "brain" else centre
    widths = {"brain": 31.0, "card": 13.0}[kind]
    blocks = [(lines, *block_size(lines, widths if kind == "card" or k == 1 else 27.0)) for k, lines in enumerate(text_blocks(kind))]

    def place_blocks(gg, ref):
        spots, dist = [], 0.0
        for lines, bw, bh in sorted(blocks, key=lambda b: -b[1] * b[2]):
            t = find_free(gg, org, bw + 1, bh + 1, ref)
            if t is None:
                return None, 0
            mark_rect(gg, org, t[0] - 1, t[1] - 1, bw + 3, bh + 3)
            spots.append((lines, bw, bh, t)); dist += math.hypot(t[0] + bw / 2 - ref[0], t[1] + bh / 2 - ref[1])
        return spots, dist

    best = None
    if kind == "brain":
        for W in (64, 60, 56, 52, 48, 44, 40, 36, 32, 30, 28, 26, 24):
            lw, lh = W + 1, W * ar + 1
            for j, i in free_spots(g, lw, lh)[::3]:
                lx, ly = org[0] + i * CELL, org[1] + j * CELL
                gg = g.copy(); mark_rect(gg, org, lx - 1, ly - 1, lw + 2, lh + 2)
                spots, d = place_blocks(gg, (lx + lw / 2, ly + lh / 2))
                if spots is None:
                    continue
                d += 0.15 * math.hypot(lx - prefer[0], ly - prefer[1])
                if best is None or d < best[0]:
                    best = (d, (W, (lx, ly)), spots)
            if best:
                break
    else:
        spots, _ = place_blocks(g.copy(), prefer)
        if spots:
            best = (0, None, spots)
    if best is None:
        return f"{kind}: no free area found, nothing drawn"
    _, logo, spots = best
    where = "; ".join(f"text {bw:.0f} x {bh:.1f} mm at ({t[0] - org[0]:.1f}, {t[1] - org[1]:.1f})" for _, bw, bh, t in spots)
    head = f"{kind}: logo {'%d mm wide at (%.1f, %.1f)' % (logo[0], logo[1][0] - org[0], logo[1][1] - org[1]) if logo else 'none'}; {where}"
    if dry:
        return head
    sil = Sil(board)
    if logo:
        W, (lx, ly) = logo
        draw_logo(sil, lg, lx + 0.5, ly + 0.5, W / (sb[2] - sb[0]))
    smallest = 9.0
    for lines, bw, bh, (x, y) in spots:
        cx = x + 0.5 + bw / 2; yy = y + 0.5
        for text, h, thick in lines:
            t = sil.text(text, cx, yy + h / 2, h, thick)
            while t.GetBoundingBox().GetWidth() / NM > bw:
                h *= 0.97; t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h)))
            smallest = min(smallest, h)
            yy += h + 0.6
    board.GetTitleBlock().SetRevision(REV)
    board.Save(str(path))
    return head + f"; {sil.n} silk items, smallest text {smallest:.2f} mm high"


def strip(kind: str) -> None:
    """Remove an earlier branding group and save. Runs in its own process: pcbnew's Python proxies go stale after Remove()."""
    board = pcbnew.LoadBoard(str(BOARDS[kind]))
    if any(g.GetName() == GROUP for g in board.Groups()):
        remove_old(board)
        board.Save(str(BOARDS[kind]))


if __name__ == "__main__":
    import subprocess
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--strip" in sys.argv:
        for k in args:
            strip(k)
        sys.exit(0)
    kinds = args or ["brain", "card"]
    for k in kinds:
        if "--dry" not in sys.argv:
            subprocess.run([sys.executable, __file__, k, "--strip"], check=True, stderr=subprocess.DEVNULL)
        print(brand(k, dry="--dry" in sys.argv))
