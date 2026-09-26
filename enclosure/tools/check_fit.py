"""Clearance check of the bay-card retention (lid comb ribs and tray overhang blocks) against the placed cards.

    python3 tools/check_fit.py

Reads the slot windows from board.scad and the constants from params.scad, places every card with the same routine the renders use
(hardware/tools/board_model.py) and reports the smallest gap between each rib or block and the card, its receptacle housing and
the neighbouring cards. Exit code 1 when anything touches or the plug path (receptacle width, straight up) is blocked.
"""
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hardware" / "tools"))
import board_model as bm  # noqa: E402

ENC = ROOT / "enclosure"


def num(name, text):
    return float(re.search(r"^" + name + r"\s*=\s*(-?[\d.]+)", text, re.M).group(1))


def main():
    P = (ENC / "params.scad").read_text()
    slots = sorted(float(m.group(1)) for m in re.finditer(r'"slot",\s*([\d.]+),', (ENC / "board.scad").read_text()))
    c = {k: num(k, P) for k in ("card_off", "card_t", "comb_gap", "comb_depth", "card_over", "card_shoulder_z", "support_w", "support_groove", "support_groove_d", "support_gap", "above_board")}
    cy = re.search(r"comb_y\s*=\s*\[(-?[\d.]+),\s*(-?[\d.]+)\]", P)
    y0, y1 = float(cy.group(1)), float(cy.group(2))
    hous_front, pitch = 4.9, 14.5
    slab_back = c["card_off"] + c["card_t"] / 2
    rib_w = pitch - hous_front - slab_back - 2 * c["comb_gap"]
    ribs = [(w + slab_back + c["comb_gap"], w + slab_back + c["comb_gap"] + rib_w) for w in slots]
    w0 = slots[0]
    ribs.append((w0 - hous_front - c["comb_gap"] - rib_w, w0 - hous_front - c["comb_gap"]))
    z_lo = c["above_board"] - c["comb_depth"]                    # rib tip above the board top
    card = bm.model("card"); brain = bm.model("brain")
    Wb, Wc = brain["size"][0], card["size"][0]
    bad = 0; worst = 99.0
    for w in slots:
        contact_kicad = Wb - (w + c["card_off"])
        boxes = {}
        for g, t in card["groups"].items():
            p = bm.place_card(t, Wc, Wb, contact_kicad).reshape(-1, 3)
            boxes[g] = (p.min(0), p.max(0))
        # x extent of everything on the card, and the housing alone
        cx0 = min(b[0][0] for b in boxes.values()); cx1 = max(b[1][0] for b in boxes.values())
        hx0, hx1 = boxes["connector"][0][0], boxes["connector"][1][0]
        for r0, r1 in ribs:
            # ribs that lie within this card's neighbourhood only
            if r1 < cx0 - pitch or r0 > cx1 + pitch:
                continue
            gap = max(r0 - cx1, cx0 - r1) if (r1 < cx0 or r0 > cx1) else -min(r1 - cx0, cx1 - r0)
            worst = min(worst, gap)
            if gap < 0.25:
                bad += 1
                print(f"  rib x {r0:.2f}..{r1:.2f} touches card at {w:.1f}: x extent {cx0:.2f}..{cx1:.2f} (gap {gap:.2f})")
        # plug path: the receptacle housing's x range must be free of ribs
        for r0, r1 in ribs:
            if r0 < hx1 and r1 > hx0:
                bad += 1; print(f"  rib {r0:.2f}..{r1:.2f} blocks the plug path {hx0:.2f}..{hx1:.2f}")
    print(f"comb: {len(ribs)} ribs {rib_w:.2f} mm wide, y {y0}..{y1}, tip {z_lo:.1f} mm above the board (card top 48.9); smallest gap to any card {worst:.2f} mm")
    # support blocks: card shoulder sits over the groove
    z_groove_floor = c["card_shoulder_z"] - c["support_gap"]
    print(f"supports: {len(slots)} blocks {c['support_w']} wide, groove {c['support_groove']} x {c['support_groove_d']} deep, shoulder {c['support_gap']} mm above the groove floor "
          f"(z {z_groove_floor:.2f} above the board), card slab {c['card_t']} in a {c['support_groove']} groove -> {(c['support_groove'] - c['card_t']) / 2:.2f} mm each side")
    print("OK" if not bad else f"{bad} problems")
    return 1 if bad else 0


sys.exit(main())
