"""Placement sanity check: every footprint courtyard inside the outline, no courtyard overlaps
between fixed parts (packed parts are checked against fixed parts too). Run after gen_pcb.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pcbnew

HW = Path(__file__).resolve().parent.parent
PCB = HW / "brain-drain.kicad_pcb"


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    bb = board.GetBoardEdgesBoundingBox()
    ox, oy = bb.GetX(), bb.GetY()
    boxes = []
    for f in board.GetFootprints():
        ref = f.GetReference()
        cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        box = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False)
        pads = list(f.Pads())
        tht = [p for p in pads if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)]
        if tht and len(tht) == len(pads):
            boxes.append((ref, box, None))   # None: through-hole part, clashes with both sides
        else:
            boxes.append((ref, box, f.IsFlipped()))
            for p in tht:   # mixed part (CM5 with its standoff holes): each hole clashes with both sides
                boxes.append((f"{ref}:{p.GetNumber() or 'hole'}", p.GetBoundingBox(), None))
    bad = 0
    for ref, box, flipped in boxes:
        if not bb.Contains(box):
            x0, y0 = (box.GetX() - ox) / 1e6, (box.GetY() - oy) / 1e6
            print(f"OUTSIDE {ref}: x {x0:.1f}-{x0 + box.GetWidth() / 1e6:.1f} y {y0:.1f}-{y0 + box.GetHeight() / 1e6:.1f}")
            bad += 1
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (r1, b1, f1), (r2, b2, f2) = boxes[i], boxes[j]
            if (f1 is not None and f2 is not None and f1 != f2) or r1.startswith("H") and r2.startswith("H") \
                    or r1.split(":")[0] == r2.split(":")[0]:
                continue
            if b1.Intersects(b2):
                inter = b1.Intersect(b2)
                if inter.GetWidth() > 50000 and inter.GetHeight() > 50000:   # ignore < 0.05 mm touches
                    print(f"OVERLAP {r1} x {r2}: {inter.GetWidth() / 1e6:.2f} x {inter.GetHeight() / 1e6:.2f} mm")
                    bad += 1
    if "-v" in sys.argv:
        for ref, box, flipped in sorted(boxes, key=lambda t: t[0]):
            x0, y0 = (box.GetX() - ox) / 1e6, (box.GetY() - oy) / 1e6
            print(f"{ref:6s} {'B' if flipped else 'F'} x {x0:6.1f}-{x0 + box.GetWidth() / 1e6:6.1f}  y {y0:6.1f}-{y0 + box.GetHeight() / 1e6:6.1f}")
    print(f"check_place: {len(boxes)} footprints, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
