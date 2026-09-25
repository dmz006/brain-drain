"""Bill of materials generated from the two designs (the schematics' source of truth is tools/design.py).

    python3 hardware/tools/gen_bom.py          # writes hardware/bom/*.csv and the tables in docs/BOM.md

Every part of both boards is grouped by (symbol, value, footprint). Vendor part numbers and prices come from the PARTS
table below: a manufacturer part number where the design names one, a generic description ("generic: ...") where any
equivalent part works, and a `verify` status where the family is chosen but the orderable number still has to be checked
against the datasheet and stock on the day of the order. Prices are rough 2026 single-unit to quantity-10 USD (LCSC,
Digi-Key, Mouser) for budgeting, not quotes.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design    # noqa: E402

HW = Path(__file__).resolve().parent.parent
DOC = HW.parent / "docs" / "BOM.md"

# (symbol regex, value regex) -> manufacturer, part number, description, USD each, status ("" = fine, "verify" = check before ordering)
PARTS = [
    (r"^Battery_Cell$", r".*", "Keystone", "1060", "CR2032 SMD holder (cell bought separately, about 0.5)", 0.9, "verify"),
    (r"^CM5$", r".*", "Raspberry Pi", "CM5102016", "Compute Module 5, wireless, 2 GB RAM, 16 GB eMMC (the schematic value field still reads CM5002016)", 97.0, "verify"),
    (r"^C$", r"^33p$", "generic", "", "33 pF C0G 50 V 0402 (crystal load)", 0.01, ""),
    (r"^C$", r"^100n( \d+V)?$", "generic", "", "100 nF X7R 16 V or better, 0402", 0.01, ""),
    (r"^C$", r"^1n$", "generic", "", "1 nF C0G 50 V 0402", 0.01, ""),
    (r"^C$", r"^10n$", "generic", "", "10 nF X7R 25 V 0402 (SATA AC coupling)", 0.01, ""),
    (r"^C$", r"^22p$", "generic", "", "22 pF C0G 50 V 0402 (crystal load)", 0.01, ""),
    (r"^C$", r"^1u 10V$", "generic", "", "1 uF X5R 10 V 0402", 0.02, ""),
    (r"^C$", r"^2\.2u$", "generic", "", "2.2 uF X5R 10 V 0603", 0.03, ""),
    (r"^C$", r"^4\.7u 10V$", "generic", "", "4.7 uF X5R 10 V 0603", 0.04, ""),
    (r"^C$", r"^10u 10V$", "generic", "", "10 uF X5R 10 V 0805", 0.05, ""),
    (r"^C$", r"^22u 10V$", "generic", "", "22 uF X5R 10 V 0805", 0.08, ""),
    (r"^C$", r"^10u 25V$", "generic", "", "10 uF X5R 25 V 1210 (input and 5 V bulk)", 0.12, ""),
    (r"^C_Polarized$", r".*", "generic", "", "680 uF 25 V low-ESR aluminium polymer or electrolytic, 10 x 10.5 mm SMD (spin-up bulk)", 0.9, "verify"),
    (r"^R$", r"^0R", "generic", "", "0 ohm 0402 (option link, cap DNP alternative)", 0.005, ""),
    (r"^R$", r".*", "generic", "", "resistor 1 %, thick film (value as listed)", 0.005, ""),
    (r"^LED$", r".*", "generic", "", "3 mm through-hole LED, colour as listed, 2 V forward, about 5 mA", 0.1, ""),
    (r"^D_TVS$", r".*", "Littelfuse", "SMBJ15A", "TVS diode 15 V standoff, SMB", 0.35, ""),
    (r"^D_Zener$", r".*", "generic", "", "12 V 0.5 W zener, SOD-123 (BZT52C12 class)", 0.05, ""),
    (r"^Fuse$", r".*", "Littelfuse", "0453010.MR", "NANO2 10 A slow-blow fuse", 0.8, ""),
    (r"^BAY_SLOT$", r".*", "Amphenol FCI", "10018783-10100TLF", "PCI Express x1 vertical through-hole socket, 36 contacts (custom bay pinout, no PCIe signalling)", 1.0, "verify"),
    (r"^DIN4_KPJX$", r".*", "Kycon", "KPJX-4S-S", "4-pin mini-DIN power jack, shielded, 7.5 A per pin", 1.5, ""),
    (r"^Micro_SD_Card$", r".*", "Hirose", "DM3AT-SF-PEJM5", "microSD push-push socket", 1.0, "verify"),
    (r"^Conn_01x0[1-9]$", r".*", "generic", "", "2.54 mm pin header, vertical, count as listed", 0.1, ""),
    (r"^USB_C_Receptacle", r".*", "GCT", "USB4085-GF-A", "USB-C 16-pin receptacle, USB 2.0 only", 1.0, ""),
    (r"^M2_MKEY$", r".*", "TE Connectivity", "2199230-4", "M.2 M-key socket, 4.2 mm, for a 2280 module", 1.2, ""),
    (r"^L$", r"^2\.2u 8A$", "generic", "", "2.2 uH, 8 A saturation, shielded, 6 x 6 mm (TPS56637 reference design class)", 0.6, "verify"),
    (r"^L$", r"^4\.7u 3A$", "generic", "", "4.7 uH, 3 A, shielded, 4 x 4 mm (AP63203 class)", 0.35, "verify"),
    (r"^L$", r"^4\.7u 1A$", "generic", "", "4.7 uH, 1 A, 4 x 4 mm (ASM1153E internal core switcher)", 0.3, "verify"),
    (r"^PMOS_SSSGDDDD$", r".*", "Alpha & Omega", "AO4407A", "P-MOSFET -30 V, SO-8: S 1-3, G 4, D 5-8 (reverse-polarity protection)", 0.8, ""),
    (r"^PMOS_SSSGDDDD_EP$", r".*", "Alpha & Omega", "AON7403", "P-MOSFET -30 V, DFN 3x3-8: S 1-3, G 4, D 5-8 + EP (bay 12 V and 5 V switches)", 0.8, ""),
    (r"^2N7002$", r".*", "generic", "", "N-MOSFET 60 V 2N7002, SOT-23 (gate driver)", 0.05, ""),
    (r"^SW_DIP_x08$", r".*", "generic", "", "8-position piano DIP switch, 2.54 mm pitch, 7.62 mm row", 1.0, "verify"),
    (r"^SW_Push$", r".*", "generic", "", "6 mm tactile switch used as the lid switch", 0.2, ""),
    (r"^USB5744$", r".*", "Microchip", "USB5744/2G", "USB 3.2 Gen 1 four-port hub, VQFN-56 7 x 7", 2.44, ""),
    (r"^TPS56637$", r".*", "Texas Instruments", "TPS56637RPAR", "6 A step-down converter, VQFN-HR 3 x 3", 1.9, ""),
    (r"^AP63203WU$", r".*", "Diodes Inc.", "AP63203WU-7", "2 A step-down converter, TSOT-26, 3.3 V", 0.5, ""),
    (r"^AP2112K-1\.2$", r".*", "Diodes Inc.", "AP2112K-1.2TRG1", "600 mA LDO, 1.2 V, SOT-25 (hub core)", 0.3, ""),
    (r"^TPS22965$", r".*", "Texas Instruments", "TPS22965DSGR", "load switch, 4 A, WSON-8 2 x 2", 0.5, ""),
    (r"^Crystal_GND24$", r"^25MHz", "generic", "", "25 MHz crystal, 3.2 x 2.5 mm, CL 20 pF (hub clock)", 0.3, ""),
    (r"^Crystal_GND24$", r"^30MHz", "generic", "", "30 MHz crystal, 3.2 x 2.5 mm, CL 16 pF (bridge default clock strap)", 0.3, ""),
    (r"^Polyfuse$", r"^3A", "generic", "", "PTC resettable fuse 1812, 3 A hold (bay 12 V), 15 V or better", 0.3, "verify"),
    (r"^Polyfuse$", r"^2A", "generic", "", "PTC resettable fuse 1812, 2 A hold (bay 5 V), 6 V or better", 0.3, "verify"),
    (r"^BAY_EDGE$", r".*", "(board)", "", "PCI Express x1 card-edge fingers on the card itself, ENIG, chamfered tab", 0.0, ""),
    (r"^SATA22$", r".*", "Molex", "47018-4001", "SATA 22-pin (7+15) host receptacle, top mount, PCB-edge type, tape and reel with cap", 1.5, "verify"),
    (r"^ASM1153E$", r".*", "ASMedia", "ASM1153E", "USB 3.0 to SATA 6G bridge, QFN-48 6 x 6, SAT passthrough", 3.0, "verify"),
]
OFF_BOARD = [   # (item, qty per unit, USD each, note)
    ("Raspberry Pi CM5 cooler (passive)", 1, 6.0, "presses on the CM5; lid grille above it"),
    ("OLED module 0.96 in 128x64 I2C (SSD1306)", 1, 3.0, "4-wire lead to J41, clamped by the printed bezel"),
    ("SATA 22-pin male-to-female extension cable, 0.5 m", 4, 3.5, "one per populated bay; eight if all slots are used"),
    ("12 V brick with matching 4-pin DIN, 120 W (four bays)", 1, 30.0, "150-180 W with eight bays; DIN pin table decides the J21 wiring (STATUS R3)"),
    ("Heat-set inserts M2.5, feet, screws, hinge pin", 1, 4.0, "enclosure hardware"),
    ("Enclosure print, PETG or ASA, about 350 g", 1, 9.0, "home printer; 35-60 from a print service"),
    ("M.2 NVMe SSD 2280 (user's own, not part of the unit)", 0, 0.0, "the M.2 bay is optional"),
]


def lookup(sym: str, value: str):
    for s, v, mfr, mpn, desc, usd, status in PARTS:
        if re.match(s, sym) and re.match(v, value):
            return mfr, mpn, desc, usd, status
    return "?", "", f"UNMAPPED {sym} {value}", 0.0, "verify"


def natural(ref: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", ref)]


def group(project: str):
    d = design.build(project)
    g = defaultdict(list)
    for c in d.comps.values():
        g[(c.lib_id.split(":")[-1], c.value, c.footprint.split(":")[-1])].append(c.ref)
    rows = []
    for (sym, value, fp), refs in g.items():
        refs.sort(key=natural)
        mfr, mpn, desc, usd, status = lookup(sym, value)
        rows.append({"refs": ",".join(refs), "qty": len(refs), "value": value, "footprint": fp, "manufacturer": mfr, "mpn": mpn,
                     "description": desc, "usd_each": usd, "usd_total": round(usd * len(refs), 3), "status": status, "_first": natural(refs[0])})
    rows.sort(key=lambda r: r["_first"])
    for r in rows:
        del r["_first"]
    return rows


def write_csv(rows, path):
    fields = ["refs", "qty", "value", "footprint", "manufacturer", "mpn", "description", "usd_each", "usd_total", "status"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def md_table(rows):
    out = ["| Refs | Qty | Value | Footprint | Part | Description | ~USD | Check |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        part = (f"{r['manufacturer']} {r['mpn']}".strip() if r["mpn"] else r["manufacturer"])
        refs = r["refs"] if len(r["refs"]) < 60 else r["refs"][:57] + "..."
        out.append(f"| {refs} | {r['qty']} | {r['value']} | {r['footprint']} | {part} | {r['description']} | {r['usd_total']:.2f} | {r['status']} |")
    return "\n".join(out)


def main():
    brain, card = group("brain"), group("card")
    (HW / "bom").mkdir(exist_ok=True)
    write_csv(brain, HW / "bom" / "brain-drain-bom.csv")
    write_csv(card, HW / "bom" / "bay-card-bom.csv")
    b_total = sum(r["usd_total"] for r in brain)
    c_total = sum(r["usd_total"] for r in card)
    n_parts_b = sum(r["qty"] for r in brain); n_parts_c = sum(r["qty"] for r in card)
    off = sum(q * p for _, q, p, _ in OFF_BOARD)
    text = f"""<!-- GENERATED by hardware/tools/gen_bom.py from hardware/tools/design.py: do not edit between the markers -->

## Brain board ({n_parts_b} parts, about ${b_total:.0f} of parts without the board itself)

{md_table(brain)}

## Bay card ({n_parts_c} parts, about ${c_total:.2f} of parts per card without the board)

{md_table(card)}

## Off-board items per unit

| Item | Qty | ~USD each | Note |
|---|---|---|---|
""" + "\n".join(f"| {i} | {q} | {p:.2f} | {n} |" for i, q, p, n in OFF_BOARD) + f"""

## Roll-up per unit (four bay cards fitted)

| | ~USD |
|---|---|
| Brain board parts (without PCB) | {b_total:.0f} |
| Four bay cards, parts (without PCB) | {4 * c_total:.0f} |
| Off-board items | {off:.0f} |
| **Parts and accessories** | **{b_total + 4 * c_total + off:.0f}** |

Boards and assembly are priced in [FABRICATION.md](FABRICATION.md). `Check = verify` marks a part whose family is chosen but whose
orderable number, footprint or rating must be confirmed against the datasheet and stock before the order.
<!-- END GENERATED -->
"""
    head = ("# brain-drain: bill of materials\n\nQuantities are per board; the unit has one brain board and four to eight bay cards. Machine-readable copies: "
            "`hardware/bom/brain-drain-bom.csv` and `hardware/bom/bay-card-bom.csv` (both regenerated by `python3 hardware/tools/gen_bom.py`).\n"
            "Vendors and prices are budgeting figures from 2026 (LCSC, Digi-Key, Mouser), not quotes.\n\n")
    DOC.write_text(head + text)
    unmapped = [r for r in brain + card if r["manufacturer"] == "?"]
    print(f"brain {n_parts_b} parts ${b_total:.0f}, card {n_parts_c} parts ${c_total:.2f}, unit ${b_total + 4 * c_total + off:.0f}; unmapped: {len(unmapped)}")


if __name__ == "__main__":
    main()
