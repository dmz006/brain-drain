# Fabrication: getting boards made and assembled

The owner wants the board fabricated **and fully assembled** (every SMD part and
every connector) by a small-run service, with at most minimal soldering at home
(the OLED lead, heat-set inserts, the CM5 itself which just presses on). This
page lists who can do that for a 4-layer 150 × 112 mm board in quantities of
2–10, what it costs, and what the design needs before the order can be placed.

Prices are estimates from the vendors' public calculators and 2025–2026 price
lists; they move with copper, exchange rates and the day's promotion, so get a
live quote from the design files before deciding.

## What the board needs from the fab

| Item | Requirement | Why |
|---|---|---|
| Layers, size | 4 layers, 150 × 112 mm, 1.6 mm, ENIG | USB 3 / SATA / PCIe pairs on outer layers over solid ground; ENIG for the 0.4 mm connectors |
| Stack-up | vendor's standard 4-layer with controlled impedance (JLC04161H-7628 or equal) | 90 Ω differential pairs without a custom stack-up fee |
| Minimum features | 0.13 mm track / 0.125 mm space, 0.2 mm drill in a 0.45 mm via (the Raspberry Pi CM5IO rules); power vias 0.6/0.3 | set by the CM5's 0.4 mm connectors and the 0.5 mm M.2 socket; every vendor above quotes these as standard 4-layer capability |
| Fine pitch | 0.4 mm pitch (Hirose DF40 for the CM5, QFN-48 / QFN-56 at 0.4–0.5 mm) | needs stencil + reflow, not hand soldering; every vendor below handles it |
| Through-hole | SATA receptacles (SMT with pegs), DIN jack, DIP switch, LEDs, headers, M.2 standoff | ask for **through-hole assembly** too, or these come loose in a bag |
| Bottom side | CR2032 holder and two headers | double-sided assembly adds a setup fee; or move them to the top before ordering |
| Parts sourcing | vendor-stocked passives; the CM5, USB5744, ASM1153E, TPS56637, connectors as consigned or "global sourcing" parts | ASM1153E is not in most in-house catalogues; JLCPCB has it (LCSC C2762919) |

The CM5 module and its cooler are bought separately and pressed on at home.

## Vendors that assemble small runs

| Vendor | Where | Small-run assembly | Notes | Link |
|---|---|---|---|---|
| **JLCPCB** | China | yes, from 2 pcs, SMT + through-hole, single or double side | cheapest by far; huge in-house parts catalogue (LCSC) including the ASM1153E and USB5744; 4-layer impedance stack-ups are standard; "Economic" vs "Standard" assembly tiers | https://jlcpcb.com/capabilities/pcb-assembly-capabilities |
| **PCBWay** | China | yes, from 1 pc, full turnkey or consigned parts | more flexible on odd parts and on special requests; quotes by e-mail for anything the calculator does not cover | https://www.pcbway.com/pcb-assembly.html |
| **Seeed Fusion** | China | yes, from 1 pc, turnkey | Open Parts Library for common parts; good documentation for first-time assembly orders | https://www.seeedstudio.com/fusion_pcb.html |
| **Eurocircuits** | Belgium / Germany | yes, "PCB + assembly" from 1 pc | EU pricing (roughly 3–5× China) but EU lead times, no customs, strong DFM checks | https://www.eurocircuits.com/pcb-assembly/ |
| **Aisler** | Germany | yes, small batches | simple upload-and-go, EU; assembly catalogue is narrower, consigned parts possible | https://aisler.net/ |
| **MacroFab** | USA | yes, prototypes from 1 pc | US production, good for a US owner who wants no import paperwork; pricier than Asia | https://macrofab.com/ |
| **Screaming Circuits** | USA | yes, quick-turn prototypes | assembly only (they source boards too); strong on fine pitch and odd connectors | https://www.screamingcircuits.com/ |
| OSH Park | USA | **no assembly** | listed only because it is the usual prototype fab; bare boards only, so not a fit for this project | https://oshpark.com/ |

Recommendation for the first run: **JLCPCB** (5 boards, 2 assembled), because the
ASM1153E and USB5744 are in their catalogue, 4-layer impedance control is
standard, and a 2-piece assembly order is routine. Keep PCBWay as the fallback
for consigned parts if a JLCPCB part goes out of stock.

## Estimated cost for the first run

Two assembled units plus three bare spares, at JLCPCB-class pricing.

| Item | Estimate (USD) | Basis |
|---|---|---|
| 5 × bare 4-layer 150 × 112 mm, ENIG, impedance stack-up | 70–100 | calculator: 4-layer, 112 × 150 mm, ENIG, 5 pcs |
| Assembly setup + stencil, both sides | 50–80 | SMT setup fee, through-hole setup, extended-parts fees (a few dollars per unique part) |
| Assembly labour, 2 boards, ~300 placements each | 30–60 | per-joint pricing, 0402 heavy |
| Board-mounted parts, per board | 55–70 | BOM section B–F: hubs 2 × 2.44, bridges 4 × 3, bucks, switches, PTCs, crystals, connectors, passives |
| Shipping and import (DHL to the US) | 35–60 | 2 assembled + 3 bare, 1–2 kg |
| **Subtotal, 2 assembled + 3 bare** | **~290–450** | |
| CM5 wireless, 2 GB / 16 GB eMMC, per unit | 60–70 | Raspberry Pi list price; Lite (no eMMC) about 10 less, wireless adds 5 |
| CM5 passive cooler, per unit | 6 | |
| OLED module, CR2032, heat-set inserts, feet, per unit | 8 | |
| 4 × SATA 22-pin extension cables 0.5 m | 12–20 | off-the-shelf |
| 12 V / 10 A brick with matching 4-pin DIN | 25–35 | choose before the DIN pinout is fixed (B3) |
| Enclosure print (PETG/ASA, ~200 g) | 5–8 | home printer; 25–40 from a print service |
| **Per finished unit, on top of the board run** | **~120–150** | |

So the first two working units land at roughly **$530–750 all in**, or about
**$265–375 each**, with three spare bare boards. A second run of five assembled
boards would be about $450–600 for the boards and $120–150 per unit on top.

## Before the order can go in

| # | Gate | Status |
|---|---|---|
| 1 | Routing finished and DRC-clean (STATUS R4, R22, D7, D8) | 83 % autorouted, copper DRC-clean; the QFN supply pins (D8) and pair matching remain |
| 2 | SATA receptacle footprint from the Molex drawing (R1, B1) | placeholder |
| 3 | M.2 socket peg check (R2, B2) | pending |
| 4 | DIN pinout matched to the chosen brick (R3, B3) | pending |
| 5 | Vendor part numbers on every BOM line, checked against stock the day of ordering | BOM has families, not all orderable numbers |
| 6 | Gerbers, drill, pick-and-place and BOM exports from `kicad-cli`, plus the assembly drawings | `hardware/tools/export_fab.sh` writes `hardware/fab/<date>/` (gitignored) |
| 7 | Bench evidence that the ASM1153E passes Sanitize through (Saturday plan) | 2026-09-26 |

## Ordering checklist (JLCPCB flow)

1. `sh hardware/tools/export_fab.sh`: gerber + drill zip, placement CSV, BOM CSV, assembly PDFs, an errors-only DRC report. Add LCSC numbers to the BOM lines first (gate 5).
2. Upload the zip, pick 4 layers, 1.6 mm, ENIG, the impedance stack-up, 5 pcs.
3. Tick "PCB assembly", 2 pcs, both sides, standard tier; upload BOM + placement.
4. In the parts matcher, confirm every line; for anything out of stock choose an
   equivalent or mark DNP and note it in `docs/BOM.md`.
5. Review the placement preview (rotations of polarised parts and the QFNs).
6. Order; expect 2–3 weeks to the door.

What still gets soldered at home: nothing on the board. Press the CM5 on, screw
the cooler, fit the OLED lead to J41, heat-set the inserts, close the lid.
