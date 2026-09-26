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
LW = 0.15            # silk line width (fab minimum is 0.15)
NM = 1e6
CELL = 0.5
GROUP = "branding"

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

    def dot(self, c, r):
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


def find_free(g, org, w, h, prefer):
    """Top-left of the free w x h rectangle (mm) nearest to `prefer`, or None."""
    x0, y0, _, _ = org
    ny, nx = g.shape
    cw, ch = int(math.ceil(w / CELL)), int(math.ceil(h / CELL))
    integral = np.pad(g.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    best = None
    for j in range(0, ny - ch):
        for i in range(0, nx - cw):
            s = integral[j + ch, i + cw] - integral[j, i + cw] - integral[j + ch, i] + integral[j, i]
            if s == 0:
                cx, cy = x0 + i * CELL + w / 2, y0 + j * CELL + h / 2
                d = math.hypot(cx - prefer[0], cy - prefer[1])
                if best is None or d < best[0]:
                    best = (d, x0 + i * CELL, y0 + j * CELL)
    return None if best is None else best[1:]


def draw_logo(sil, lg, ox, oy, scale):
    """Line-art of the octopus with its top-left at (ox, oy); scale is mm per logo unit."""
    x0, y0, _, _ = lg.bbox

    def T(p):
        return ((p[0] - x0) * scale + ox, (p[1] - y0) * scale + oy)

    bx, by, rx, ry = lg.brain

    def inside_brain(p):
        return ((p[0] - bx) / (rx + 6)) ** 2 + ((p[1] - by) / (ry + 6)) ** 2 < 1
    # brain outline
    sil.poly([T((bx + rx * math.cos(a), by + ry * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 73)], closed=False)
    for f in lg.gyri:
        sil.poly([T(p) for p in f])
    for (cx, cy, erx, ery, px, py, pr) in lg.eyes:
        sil.poly([T((cx + erx * math.cos(a), cy + ery * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 25)])
        sil.dot(T((px, py)), pr * scale)
    # tentacles: two edges, dropped where they run inside the brain, with a round tip
    hw = lg.tentacle_w / 2
    for t in lg.tentacles:
        left, right = [], []
        for i, p in enumerate(t):
            a = t[max(i - 1, 0)]; b = t[min(i + 1, len(t) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dy) or 1
            nx_, ny_ = -dy / n * hw, dx / n * hw
            left.append((p[0] + nx_, p[1] + ny_)); right.append((p[0] - nx_, p[1] - ny_))
        for edge in (left, right):
            run = []
            for p in edge:
                if inside_brain(p):
                    if len(run) > 1:
                        sil.poly([T(q) for q in run])
                    run = []
                else:
                    run.append(p)
            if len(run) > 1:
                sil.poly([T(q) for q in run])
        # round tip at the far end (the end away from the brain)
        e = t[-1] if not inside_brain(t[-1]) else t[0]
        k = t.index(e); o = t[k - 1] if k else t[1]
        ang = math.atan2(e[1] - o[1], e[0] - o[0])
        sil.poly([T((e[0] + hw * math.cos(ang + a), e[1] + hw * math.sin(ang + a))) for a in np.linspace(-math.pi / 2, math.pi / 2, 9)])
    for (hx, hy) in lg.hdds:
        sil.poly([T((hx, hy)), T((hx + 92, hy)), T((hx + 92, hy + 60)), T((hx, hy + 60))], closed=True)
        c = (hx + 34, hy + 30)
        sil.poly([T((c[0] + 20 * math.cos(a), c[1] + 20 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 17)])
        sil.line(T(c), T((hx + 62, hy + 50)))
        for k in (14, 26, 38):
            sil.line(T((hx + 60, hy + k + 3)), T((hx + 82, hy + k + 3)))


def mark_rect(g, org, x, y, w, h):
    x0, y0, _, _ = org
    i0, i1 = int((x - x0) / CELL), int((x + w - x0) / CELL) + 1
    j0, j1 = int((y - y0) / CELL), int((y + h - y0) / CELL) + 1
    g[max(j0, 0):j1, max(i0, 0):i1] = True


def brand(kind: str, dry: bool = False) -> str:
    """Two blocks, each placed in the largest free spot nearest the board's middle: the logo, then the text lines beside it."""
    path = BOARDS[kind]
    board = pcbnew.LoadBoard(str(path))
    remove_old(board)
    lg = logo_geom.load()
    ar = (lg.bbox[3] - lg.bbox[1]) / (lg.bbox[2] - lg.bbox[0])
    g, org = occupancy(board, keepout_y_from=(board.GetBoardEdgesBoundingBox().GetHeight() / NM - 26) if kind == "brain" else None)
    centre = ((org[0] + org[2]) / 2, (org[1] + org[3]) / 2)
    prefer = (centre[0] - 30, centre[1]) if kind == "brain" else centre
    lines_w = 30.0 if kind == "brain" else 13.0
    lines_h = 3.6 + 1.6 + 1.9 + 0.5 if kind == "brain" else 1.8 + 0.7 + 1.3 + 0.5     # the card is full: name and "bay card" only

    def place(order):
        gg = g.copy(); logo = None; text = None
        for what in order:
            if what == "logo" and kind == "brain":
                ref = (text[0] + lines_w / 2, text[1] + lines_h / 2) if text else prefer
                for W in (44, 40, 36, 32, 28, 24, 20):
                    spot = find_free(gg, org, W + 1, W * ar + 1, ref)
                    if spot:
                        logo = (W, spot); mark_rect(gg, org, spot[0] - 1, spot[1] - 1, W + 3, W * ar + 3); break
            elif what == "text":
                ref = (logo[1][0] + logo[0] / 2, logo[1][1] + logo[0] * ar / 2) if logo else prefer
                text = find_free(gg, org, lines_w + 1, lines_h + 1, ref)
                if text:
                    mark_rect(gg, org, text[0] - 1, text[1] - 1, lines_w + 3, lines_h + 3)
        return logo, text

    best = None
    for order in (("logo", "text"), ("text", "logo")):
        logo, text = place(order)
        if text is None or (kind == "brain" and logo is None):
            continue
        d = 0 if kind != "brain" else math.hypot(logo[1][0] + logo[0] / 2 - text[0] - lines_w / 2, logo[1][1] + logo[0] * ar / 2 - text[1] - lines_h / 2)
        score = d - (logo[0] * 0.8 if logo else 0)          # prefer a big logo, close to the text
        if best is None or score < best[0]:
            best = (score, logo, text)
    if best is None:
        return f"{kind}: no free area found, nothing drawn"
    _, logo, spot = best
    if dry:
        return (f"{kind}: logo {'%d mm at (%.1f, %.1f)' % (logo[0], logo[1][0] - org[0], logo[1][1] - org[1]) if logo else 'none'}; "
                f"text block {lines_w:.0f} x {lines_h:.1f} mm at ({spot[0] - org[0]:.1f}, {spot[1] - org[1]:.1f}) from the board corner")
    sil = Sil(board)
    if logo:
        W, (lx, ly) = logo
        draw_logo(sil, lg, lx + 0.5, ly + 0.5, W / (lg.bbox[2] - lg.bbox[0]))
    x, y = spot; bw = lines_w
    cx = x + 0.5 + bw / 2; yy = y + 0.5
    ht = 3.0 if kind == "brain" else 1.6
    t = sil.text(NAME, cx, yy + ht / 2, ht, 0.4 if kind == "brain" else 0.3)
    while t.GetBoundingBox().GetWidth() / NM > bw:
        ht *= 0.94; t.SetTextSize(pcbnew.VECTOR2I(mm(ht), mm(ht)))
    yy += ht + 0.9
    hs = 1.3
    t2 = sil.text("four-bay disk sanitizer" if kind == "brain" else "bay card", cx, yy + hs / 2, hs, 0.18)
    while t2.GetBoundingBox().GetWidth() / NM > bw:
        hs *= 0.94; t2.SetTextSize(pcbnew.VECTOR2I(mm(hs), mm(hs)))
    yy += hs + 0.7
    hu = 0.0
    if kind == "brain":
        hu = 1.5
        t3 = sil.text(URL, cx, yy + hu / 2, hu, 0.2)
        while t3.GetBoundingBox().GetWidth() / NM > bw:
            hu *= 0.97; t3.SetTextSize(pcbnew.VECTOR2I(mm(hu), mm(hu)))
    board.Save(str(path))
    return (f"{kind}: branding written, logo {'%d mm wide' % logo[0] if logo else 'not placed'}, text block at "
            f"({spot[0] - org[0]:.1f}, {spot[1] - org[1]:.1f}) mm from the board corner, {sil.n} silk items, URL {hu:.2f} mm high")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    kinds = args or ["brain", "card"]
    for k in kinds:
        print(brand(k, dry="--dry" in sys.argv))
