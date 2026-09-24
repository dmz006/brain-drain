"""Close the small gaps the autorouter leaves: DRC 'unconnected' pairs of copper items on the same net.

Every open connection DRC lists joins two items of one net (pad, track end or via) that the router could
not reach: a pin of a plane net, a rail split by a fanout via, a short link between two decoupling caps.
This is a small grid router for exactly that job. For each pair, shortest first, it
  1. rasterises the copper around the gap on both outer layers (0.1 mm cells, obstacles inflated by their
     size + clearance + half the new track's width; the net's own copper is passable),
  2. runs A* over (cell, layer) with 8 directions and vias between F.Cu and B.Cu,
  3. writes the tracks (straight runs merged) and vias, and stamps them into the obstacle lists so the next
     gap sees them.
Widths are tried from the net's class width downwards (0.3, 0.2, 0.13 mm for Power nets). Pairs, whose
length is tuned, are not touched here. Pure Python: pcbnew is used only to read the board once and to add
the copper at the end.
"""
from __future__ import annotations

import heapq
import json
import math
import re
import subprocess as sp
from array import array

import pcbnew

MM = pcbnew.FromMM
RES = MM(0.1)          # grid cell, nm
CLR = 0.125            # mm copper clearance
EDGE_CLR = 0.3         # mm copper to board edge
MARGIN = 6.0           # mm searched around the two anchors
VIA = {"power": (0.6, 0.3), "signal": (0.45, 0.2)}
POWERISH = ("+12V", "5V_", "+5V", "+3V3", "3V3", "+1V2", "VDD", "12V_BAY", "5V_BAY", "GND", "VIN")
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
ITEM = re.compile(r"^(?:PTH pad|Pad|Track|Via) ")


class Obstacles:
    """Everything that is copper on the two outer layers, as plain Python data."""

    def __init__(self, board):
        self.pads = []      # (l, t, r, b, layers, net, nm-rect)
        self.tracks = []    # (ax, ay, bx, by, halfw, layer, net, pcbnew object)
        self.vias = []      # (x, y, r, net, pcbnew object)
        self.edges = []     # pcbnew shapes on Edge.Cuts
        self.keepouts = []  # (polygon outline, bbox)
        for f in board.GetFootprints():
            for p in f.Pads():
                bb = p.GetBoundingBox()
                layers = {L for L in LAYERS if p.IsOnLayer(L)}
                if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    layers = set(LAYERS)
                self.pads.append((int(bb.GetLeft()), int(bb.GetTop()), int(bb.GetRight()), int(bb.GetBottom()), layers, p.GetNetCode()))
            self.edges += [g.GetEffectiveShape() for g in f.GraphicalItems() if g.GetLayer() == pcbnew.Edge_Cuts]
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                pos = t.GetPosition(); self.vias.append((int(pos.x), int(pos.y), t.GetWidth(pcbnew.F_Cu) // 2, t.GetNetCode(), t))
            else:
                a, b = t.GetStart(), t.GetEnd()
                self.tracks.append((int(a.x), int(a.y), int(b.x), int(b.y), t.GetWidth() // 2, t.GetLayer(), t.GetNetCode(), t))
        self.edges += [d.GetEffectiveShape() for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
        for z in board.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
                bb = z.GetBoundingBox()
                self.keepouts.append((z, z.GetLayerSet(), int(bb.GetLeft()), int(bb.GetTop()), int(bb.GetRight()), int(bb.GetBottom())))


class Window:
    """Blocked-cell maps for both layers around one gap. owner[layer][cell]: 0 free, -1 blocked, n net code."""

    def __init__(self, obs: Obstacles, x0: int, y0: int, x1: int, y1: int, net: int, w_mm: float, via_r_mm: float, partner: int = 0):
        self.x0, self.y0 = x0, y0
        self.W = (x1 - x0) // RES + 2
        self.H = (y1 - y0) // RES + 2
        self.net = net
        self.w = MM(w_mm)
        self.own = {L: array("i", [0]) * (self.W * self.H) for L in LAYERS}
        infl = MM(CLR + w_mm / 2)
        self._build(obs, x0, y0, x1, y1, infl)
        # a via needs more room than a track: cells within this many cells of anything else block it
        self.via_cells = max(1, int(math.ceil((via_r_mm - w_mm / 2) / 0.1)))
        # cells close to the partner net's copper are cheaper: a pair's second side hugs the first
        self.near = {L: bytearray(self.W * self.H) for L in LAYERS}
        if partner:
            reach = 0.55 / 0.1
            for ax, ay, bx, by, hw, layer, pn, _obj in obs.tracks:
                if pn != partner or layer not in self.near:
                    continue
                if max(ax, bx) < x0 - MM(1) or min(ax, bx) > x1 + MM(1) or max(ay, by) < y0 - MM(1) or min(ay, by) > y1 + MM(1):
                    continue
                n = max(1, int(math.hypot(bx - ax, by - ay) / (RES * 0.5)))
                for k in range(n + 1):
                    cx, cy = self._cell(ax + (bx - ax) * k / n, ay + (by - ay) * k / n)
                    for jj in range(max(0, int(cy - reach)), min(self.H, int(cy + reach) + 1)):
                        for ii in range(max(0, int(cx - reach)), min(self.W, int(cx + reach) + 1)):
                            if (ii + 0.5 - cx) ** 2 + (jj + 0.5 - cy) ** 2 <= reach * reach:
                                self.near[layer][jj * self.W + ii] = 1

    def _stamp(self, layer, cx: float, cy: float, r: float, net: int) -> None:
        """Stamp a disc (cell units) around (cx, cy) with owner `net`."""
        arr = self.own[layer]
        i0, i1 = max(0, int(cx - r)), min(self.W - 1, int(cx + r) + 1)
        j0, j1 = max(0, int(cy - r)), min(self.H - 1, int(cy + r) + 1)
        r2 = r * r
        for j in range(j0, j1 + 1):
            dy = j + 0.5 - cy
            row = j * self.W
            for i in range(i0, i1 + 1):
                dx = i + 0.5 - cx
                if dx * dx + dy * dy <= r2:
                    k = row + i
                    cur = arr[k]
                    if cur == 0:
                        arr[k] = net
                    elif cur != net:
                        arr[k] = -1

    def _stamp_box(self, layer, l: float, t: float, r: float, b: float, net: int) -> None:
        arr = self.own[layer]
        i0, i1 = max(0, int(l)), min(self.W - 1, int(r) + 1)
        j0, j1 = max(0, int(t)), min(self.H - 1, int(b) + 1)
        for j in range(j0, j1 + 1):
            row = j * self.W
            for i in range(i0, i1 + 1):
                k = row + i
                cur = arr[k]
                if cur == 0:
                    arr[k] = net
                elif cur != net:
                    arr[k] = -1

    def _cell(self, x: int, y: int) -> tuple[float, float]:
        return (x - self.x0) / RES, (y - self.y0) / RES

    def _build(self, obs: Obstacles, x0, y0, x1, y1, infl) -> None:
        pad = infl / RES
        for l, t, r, b, layers, net in obs.pads:
            if r < x0 - infl or l > x1 + infl or b < y0 - infl or t > y1 + infl:
                continue
            (cl, ct), (cr, cb) = self._cell(l, t), self._cell(r, b)
            for L in layers:
                self._stamp_box(L, cl - pad, ct - pad, cr + pad, cb + pad, net if net else -1)
        for x, y, r, net, _obj in obs.vias:
            if x < x0 - infl - r or x > x1 + infl + r or y < y0 - infl - r or y > y1 + infl + r:
                continue
            cx, cy = self._cell(x, y)
            for L in LAYERS:
                self._stamp(L, cx, cy, (r + infl) / RES, net)
        for ax, ay, bx, by, hw, layer, net, _obj in obs.tracks:
            if max(ax, bx) < x0 - infl - hw or min(ax, bx) > x1 + infl + hw or max(ay, by) < y0 - infl - hw or min(ay, by) > y1 + infl + hw:
                continue
            if layer not in self.own:
                continue
            n = max(1, int(math.hypot(bx - ax, by - ay) / (RES * 0.5)))
            for k in range(n + 1):
                cx, cy = self._cell(ax + (bx - ax) * k / n, ay + (by - ay) * k / n)
                self._stamp(layer, cx, cy, (hw + infl) / RES, net)
        # board edge and keep-out areas block everybody
        band = MM(EDGE_CLR) + self.w // 2
        win = pcbnew.BOX2I(pcbnew.VECTOR2I(x0, y0), pcbnew.VECTOR2I(x1 - x0, y1 - y0))
        for e in obs.edges:
            bb = e.BBox()
            if not win.Intersects(bb.Inflate(band + RES)):
                continue
            for j in range(self.H):
                for i in range(self.W):
                    if e.Collide(pcbnew.VECTOR2I(int(self.x0 + (i + 0.5) * RES), int(self.y0 + (j + 0.5) * RES)), band):
                        for L in LAYERS:
                            self.own[L][j * self.W + i] = -1
        for z, layers, l, t, r, b in obs.keepouts:
            if r < x0 or l > x1 or b < y0 or t > y1:
                continue
            outline = z.Outline()
            for L in LAYERS:
                if not z.IsOnLayer(L):
                    continue
                for j in range(self.H):
                    for i in range(self.W):
                        if outline.Collide(pcbnew.VECTOR2I(int(self.x0 + (i + 0.5) * RES), int(self.y0 + (j + 0.5) * RES)), MM(EDGE_CLR)):
                            self.own[L][j * self.W + i] = -1

    def free(self, layer, i: int, j: int) -> bool:
        if not (0 <= i < self.W and 0 <= j < self.H):
            return False
        v = self.own[layer][j * self.W + i]
        return v == 0 or v == self.net

    def step_cost(self, layer, i: int, j: int, rip):
        """None: blocked. 0: free. With `rip` ({net code: cost}): another net's copper can be crossed at that cost."""
        if not (0 <= i < self.W and 0 <= j < self.H):
            return None
        v = self.own[layer][j * self.W + i]
        if v == 0 or v == self.net:
            return 0.0
        if rip is None or v < 0:
            return None
        return rip.get(v, 60.0)

    def via_ok(self, i: int, j: int) -> bool:
        n = self.via_cells
        for L in LAYERS:
            for dj in range(-n, n + 1):
                for di in range(-n, n + 1):
                    if di * di + dj * dj <= n * n and not self.free(L, i + di, j + dj):
                        return False
        return True


def astar(win: Window, starts, goals, via_cost: float = 12.0, max_nodes: int = 2500000, weight: float = 1.6, rip=None):
    """starts / goals: sets of (i, j, layer). Returns the list of (i, j, layer) from a start to a goal or None."""
    if not goals:
        return None
    gl = list(goals)

    def h(i, j):
        return min(max(abs(i - gi), abs(j - gj)) + 0.414 * min(abs(i - gi), abs(j - gj)) for gi, gj, _ in gl)

    heap = []
    best = {}
    parent = {}
    for s in starts:
        best[s] = 0.0
        heapq.heappush(heap, (weight * h(s[0], s[1]), 0.0, s))
    nodes = 0
    dirs = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while heap and nodes < max_nodes:
        _f, g, cur = heapq.heappop(heap)
        if g > best.get(cur, 1e18) + 1e-9:
            continue
        nodes += 1
        if cur in goals:
            path = [cur]
            while cur in parent:
                cur = parent[cur]; path.append(cur)
            return path[::-1]
        i, j, L = cur
        for di, dj, c in dirs:
            ni, nj = i + di, j + dj
            extra = win.step_cost(L, ni, nj, rip)
            if extra is None:
                continue
            if di and dj and (win.step_cost(L, i + di, j, rip) is None or win.step_cost(L, i, j + dj, rip) is None):
                continue   # no corner cutting
            nxt = (ni, nj, L)
            ng = g + (c * 0.6 if win.near[L][nj * win.W + ni] else c) + extra
            if ng < best.get(nxt, 1e18):
                best[nxt] = ng; parent[nxt] = cur
                heapq.heappush(heap, (ng + weight * h(ni, nj), ng, nxt))
        other = pcbnew.B_Cu if L == pcbnew.F_Cu else pcbnew.F_Cu
        nxt = (i, j, other)
        if win.free(other, i, j) and win.via_ok(i, j):
            ng = g + via_cost
            if ng < best.get(nxt, 1e18):
                best[nxt] = ng; parent[nxt] = cur
                heapq.heappush(heap, (ng + weight * h(i, j), ng, nxt))
    return None


def _anchors(board, item, pads_by_key, tracks_by_net):
    """(x, y, layers) anchor points of a DRC item, or []."""
    desc, pos = item["description"], item["pos"]
    px, py = int(pos["x"] * 1e6), int(pos["y"] * 1e6)
    m = re.match(r"(?:PTH pad|Pad) (\S+) \[.*?\] of (\w+)", desc)
    if m:
        pad = pads_by_key.get((m.group(2), m.group(1)))
        if pad is None:
            return []
        x, y, layers = pad
        return [(x, y, layers)]
    if desc.startswith("Via"):
        return [(px, py, set(LAYERS))]
    m = re.match(r"Track \[(.*?)\] on (\S+?), length ([\d.]+) mm", desc)
    if m:
        net, lname, length = m.group(1), m.group(2), float(m.group(3))
        cands = []
        for (ax, ay, bx, by, layer_name, ln) in tracks_by_net.get(net, []):
            if layer_name == lname and abs(ln - length) < 0.001:
                d = min(math.hypot(px - ax, py - ay), math.hypot(px - bx, py - by), math.hypot(px - (ax + bx) / 2, py - (ay + by) / 2))
                cands.append((d, ax, ay, bx, by))
        if not cands:
            return []
        d, ax, ay, bx, by = min(cands)
        layer = pcbnew.F_Cu if lname == "F.Cu" else pcbnew.B_Cu
        return [(ax, ay, {layer}), (bx, by, {layer})]
    return []


def close_gaps(board, d, routing_dir, pcb_path, skip_nets=frozenset(), max_len: float = 45.0, partner_of=None, ripup: bool = False, pair_names=frozenset()) -> int:
    """Route every DRC-unconnected pair of one net. Returns the number of gaps closed."""
    rep = routing_dir / "drc.json"
    pcbnew.SaveBoard(str(pcb_path), board)
    sp.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "-o", str(rep), str(pcb_path)], capture_output=True)
    unconn = json.loads(rep.read_text()).get("unconnected_items", [])
    obs = Obstacles(board)
    nets = board.GetNetInfo()
    pads_by_key = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            pos = p.GetPosition()
            layers = set(LAYERS) if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else {L for L in LAYERS if p.IsOnLayer(L)}
            pads_by_key[(f.GetReference(), str(p.GetNumber()))] = (int(pos.x), int(pos.y), layers)
    tracks_by_net = {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            a, b = t.GetStart(), t.GetEnd()
            tracks_by_net.setdefault(t.GetNetname(), []).append((int(a.x), int(a.y), int(b.x), int(b.y), t.GetLayerName(), t.GetLength() / 1e6))

    jobs = []
    for u in unconn:
        its = u["items"]
        if len(its) != 2 or not all(ITEM.match(i["description"]) for i in its):
            continue
        mnet = re.search(r"\[(.*?)\]", its[0]["description"])
        if not mnet:
            continue
        net = mnet.group(1)
        if net in skip_nets:
            continue
        other = re.search(r"\[(.*?)\]", its[1]["description"])
        if not other or other.group(1) != net:   # never join two different nets
            continue
        a1, a2 = _anchors(board, its[0], pads_by_key, tracks_by_net), _anchors(board, its[1], pads_by_key, tracks_by_net)
        if not a1 or not a2:
            continue
        best = min(((math.hypot(p[0] - q[0], p[1] - q[1]), p, q) for p in a1 for q in a2), key=lambda r: r[0])
        jobs.append((best[0], net, a1, a2))
    jobs.sort(key=lambda j: j[0])

    closed = failed = 0
    log = []
    made = []   # (net, [created tracks / vias]) per closed gap
    for dist, net, a1, a2 in jobs:
        if dist / 1e6 > max_len:
            failed += 1; log.append(f"{net}: {dist / 1e6:.1f} mm apart, too far"); continue
        code = nets.GetNetItem(net).GetNetCode()
        power = net.startswith(POWERISH) or any(k in net for k in ("GND", "12V", "5V", "3V3", "1V2"))
        widths = (0.3, 0.2, 0.13) if power else (0.13,)
        via_d, via_drill = VIA["power" if power else "signal"]
        done = False
        # try the closest anchor pairs first
        pairs = sorted(((math.hypot(p[0] - q[0], p[1] - q[1]), p, q) for p in a1 for q in a2), key=lambda r: r[0])[:4]
        for w, margin in [(w, m) for m in (MARGIN, 18.0) for w in widths]:
            for _d, p, q in pairs:
                x0 = min(p[0], q[0]) - MM(margin); x1 = max(p[0], q[0]) + MM(margin)
                y0 = min(p[1], q[1]) - MM(margin); y1 = max(p[1], q[1]) + MM(margin)
                pn = partner_of.get(net) if partner_of else None
                win = Window(obs, x0, y0, x1, y1, code, w, via_d / 2, nets.GetNetItem(pn).GetNetCode() if pn else 0)

                def cells(a):
                    ci, cj = int((a[0] - win.x0) // RES), int((a[1] - win.y0) // RES)
                    return {(ci + di, cj + dj, L) for L in a[2] for di in (-1, 0, 1) for dj in (-1, 0, 1) if win.free(L, ci + di, cj + dj)}

                path = astar(win, cells(p), cells(q))
                victims = []
                if not path and ripup:
                    # negotiate: cross other nets' copper at a price, take their crossed segments out, and let
                    # the next round reconnect them around the new route
                    costs = {}
                    for _ax, _ay, _bx, _by, _hw, _ly, nn, _o in obs.tracks:
                        if nn != code and nn not in costs:
                            nm = nets.GetNetItem(nn).GetNetname() if nets.GetNetItem(nn) else ""
                            costs[nn] = 150.0 if nm in pair_names else 70.0
                    path = astar(win, cells(p), cells(q), rip=costs)
                    if path:
                        victims = "rip"
                if not path:
                    continue
                created = _emit(board, obs, win, path, p, q, code, w, via_d, via_drill)
                made.append((net, created))
                if victims == "rip":
                    ripped = _rip_crossed(board, obs, created, code, w, via_d)
                    log.append(f"{net}: ripped up {ripped} segments/vias of other nets to get through")
                closed += 1; done = True
                break
            if done:
                break
        if not done:
            failed += 1; log.append(f"{net}: no path between ({a1[0][0] / 1e6:.1f}, {a1[0][1] / 1e6:.1f}) and ({a2[0][0] / 1e6:.1f}, {a2[0][1] / 1e6:.1f})")
    # verify: a route that DRC flags is taken out whole (never leave half of it behind), then refill
    keys = []
    for net, items in made:
        ks = set()
        for t in items:
            if t.GetClass() == "PCB_VIA":
                q = t.GetPosition(); ks.add((round(q.x / 1e6, 3), round(q.y / 1e6, 3)))
            else:
                for q in (t.GetStart(), t.GetEnd()):
                    ks.add((round(q.x / 1e6, 3), round(q.y / 1e6, 3)))
        keys.append(ks)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(pcb_path), board)
    sp.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(rep), str(pcb_path)], capture_output=True)
    bad_pos = set()
    kinds = {}
    for v in json.loads(rep.read_text()).get("violations", []):
        if v["type"] in ("clearance", "shorting_items", "tracks_crossing", "copper_edge_clearance", "items_not_allowed", "hole_clearance",
                         "track_width", "via_diameter", "annular_width", "drill_out_of_range", "hole_to_hole", "via_dangling_x"):
            kinds[v["type"]] = kinds.get(v["type"], 0) + 1
            for i in v["items"]:
                if "pos" in i:
                    bad_pos.add((round(i["pos"]["x"], 3), round(i["pos"]["y"], 3)))
    reverted = 0
    for (net, items), ks in zip(made, keys):
        if ks & bad_pos or any(abs(a - b[0]) < 0.6 and abs(c - b[1]) < 0.6 for a, c in ks for b in bad_pos if False):
            for t in items:
                board.Remove(t)
            reverted += 1; closed -= 1; failed += 1
            log.append(f"{net}: route rejected by DRC, removed")
    if reverted:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if kinds:
        print("close_gaps DRC findings on new copper:", kinds)
    print(f"close_gaps: {closed} gaps closed, {failed} left")
    for l in log:
        print("close_gaps note:", l)
    return closed


def _rip_crossed(board, obs, created, code, w, via_d) -> int:
    """Remove the other nets' tracks and vias that the new route violates clearance with (the closest copper
    was priced in the search; this is the exact check)."""
    clr = MM(CLR)
    new_segs = [(pcbnew.SEG(t.GetStart(), t.GetEnd()), t.GetWidth() // 2, t.GetLayer()) for t in created if t.GetClass() != "PCB_VIA"]
    new_vias = [(t.GetPosition(), t.GetWidth(pcbnew.F_Cu) // 2) for t in created if t.GetClass() == "PCB_VIA"]
    gone = 0
    keep_t = []
    for row in obs.tracks:
        ax, ay, bx, by, hw, layer, net, obj = row
        if net == code or obj in created:
            keep_t.append(row); continue
        seg = pcbnew.SEG(pcbnew.VECTOR2I(ax, ay), pcbnew.VECTOR2I(bx, by))
        hit = any(nl == layer and seg.Distance(ns) < hw + nhw + clr for ns, nhw, nl in new_segs)
        if not hit:
            for vp, vr in new_vias:
                if seg.Distance(vp) < hw + vr + clr:
                    hit = True; break
        if hit:
            board.Remove(obj); gone += 1
        else:
            keep_t.append(row)
    obs.tracks = keep_t
    keep_v = []
    for row in obs.vias:
        x, y, r, net, obj = row
        if net == code or obj in created:
            keep_v.append(row); continue
        pt = pcbnew.VECTOR2I(x, y)
        hit = any(ns.Distance(pt) < r + nhw + clr for ns, nhw, _l in new_segs) or any((vp.x - x) ** 2 + (vp.y - y) ** 2 < (r + vr + clr) ** 2 for vp, vr in new_vias)
        if hit:
            board.Remove(obj); gone += 1
        else:
            keep_v.append(row)
    obs.vias = keep_v
    return gone


def _emit(board, obs, win, path, p, q, code, w, via_d, via_drill) -> list:
    """Turn a cell path into tracks and vias; merge straight runs; the first and last points are the exact anchors."""
    pts = []   # (x, y, layer)
    for i, j, L in path:
        pts.append((int(win.x0 + (i + 0.5) * RES), int(win.y0 + (j + 0.5) * RES), L))
    pts[0] = (p[0], p[1], pts[0][2]) if pts[0][2] in p[2] else pts[0]
    pts[-1] = (q[0], q[1], pts[-1][2]) if pts[-1][2] in q[2] else pts[-1]
    created = []
    runs = [[pts[0]]]
    for prev, pt in zip(pts, pts[1:]):
        if pt[2] != prev[2]:   # layer change: a via at the shared cell
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(prev[0], prev[1])); v.SetWidth(MM(via_d)); v.SetDrill(MM(via_drill))
            v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(code)
            board.Add(v); obs.vias.append((prev[0], prev[1], MM(via_d) // 2, code, v)); created.append(v)
            runs.append([pt])
        else:
            runs[-1].append(pt)
    for run in runs:
        # merge collinear points
        simp = [run[0]]
        for k in range(1, len(run) - 1):
            a, b, c = simp[-1], run[k], run[k + 1]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
                simp.append(b)
        simp.append(run[-1])
        for s, e in zip(simp, simp[1:]):
            if (s[0], s[1]) == (e[0], e[1]):
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(s[0], s[1])); t.SetEnd(pcbnew.VECTOR2I(e[0], e[1]))
            t.SetWidth(MM(w)); t.SetLayer(s[2]); t.SetNetCode(code)
            board.Add(t); obs.tracks.append((s[0], s[1], e[0], e[1], MM(w) // 2, s[2], code, t)); created.append(t)
    return created
