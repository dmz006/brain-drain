# Fabrication: getting boards made and assembled

The owner wants the board fabricated **and fully assembled** (every SMD part and
every connector) by a small-run service, with at most minimal soldering at home
(the OLED lead, heat-set inserts, the CM5 itself which just presses on). This
page lists who can do that for the two boards of C24, a 4-layer 150 × 122 mm
brain and a 45 × 46 mm bay card (four per unit, panelised), in quantities of
2–10, what it costs, and what the design needs before the order can be placed.

Prices are estimates from the vendors' public calculators and 2025–2026 price
lists; they move with copper, exchange rates and the day's promotion, so get a
live quote from the design files before deciding.

## What the board needs from the fab

| Item | Requirement | Why |
|---|---|---|
| Layers, size | brain: 6 layers, 150 × 122 mm, 1.6 mm, ENIG; bay card: 4 layers, 45 × 46 mm, 1.6 mm, ENIG, panel of 8–16 with the finger tab and key notch routed | USB 3 / SATA / PCIe pairs on outer layers over solid ground; ENIG for the 0.4 mm connectors |
| Stack-up | brain: vendor's standard 6-layer with controlled impedance (JLC06161H-series or equal; recalculate the pair widths with their calculator, the design's 0.147 / 0.253 mm were set for four layers); card: standard 4-layer (JLC04161H-7628) | 90 Ω differential pairs without a custom stack-up fee |
| Minimum features | 0.13 mm track / 0.125 mm space, 0.2 mm drill in a 0.45 mm via (the Raspberry Pi CM5IO rules); power vias 0.6/0.3 | set by the CM5's 0.4 mm connectors and the 0.5 mm M.2 socket; every vendor above quotes these as standard 4-layer capability |
| Fine pitch | 0.4 mm pitch (Hirose DF40 for the CM5, QFN-48 / QFN-56 at 0.4–0.5 mm) | needs stencil + reflow, not hand soldering; every vendor below handles it |
| Through-hole | brain: eight PCIe x1 sockets, DIN jack, DIP switch, LEDs, headers, M.2 standoff; card: the SATA receptacle (SMT with pegs) | ask for **through-hole assembly** too, or these come loose in a bag |
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

Two assembled units (each one brain and four bay cards) plus three bare brain boards and spare cards, at JLCPCB-class pricing. Part costs
come from the generated [BOM.md](BOM.md); board and assembly prices are the vendors' public calculators, not quotes.

| Item | Estimate (USD) | Basis |
|---|---|---|
| 5 x bare brain, 6-layer 150 x 122 mm, ENIG, impedance stack-up | 150-230 | calculator: 6-layer, 122 x 150 mm, ENIG, 5 pcs (four layers would be 70-100) |
| Bay-card panel, 4-layer 45 x 46 mm, 16 cards (8 for the two units, 8 spare or expansion) | 40-70 | panel of 16, tab routed, ENIG |
| Assembly setup and stencil, brain, both sides | 50-80 | SMT and through-hole setup, extended-parts fees |
| Assembly setup and stencil, card (a second job) | 40-70 | |
| Assembly labour: 2 brains (about 330 placements each) and 8 cards (about 40 each) | 60-110 | per-joint pricing, 0402 heavy |
| Board-mounted parts: 2 brains without the CM5 (about $37 each) and 8 cards (about $8 each) | 140 | BOM.md |
| Shipping and import (DHL to the US) | 40-70 | 2 assembled brains, 8 cards, 3 bare brains, 1-2 kg |
| **Subtotal, boards, assembly and board parts** | **~520-770** | |
| CM5 wireless, 2 GB / 16 GB eMMC, per unit | 97 | Raspberry Pi list price (also counted in the BOM roll-up) |
| CM5 cooler, OLED module, heat-set inserts, feet, per unit | 13 | |
| 4 x SATA 22-pin extension cables 0.5 m | 14 | off-the-shelf |
| 12 V / 10 A brick with matching 4-pin DIN | 25-35 | choose before the DIN pinout is fixed (B3); 150-180 W for eight bays |
| Enclosure print (PETG/ASA, about 350 g) | 9 | home printer; 35-60 from a print service |
| **Per finished unit, on top of the board run** | **~160-170** | |

So the first two working units land at roughly **$850-1100 all in**, or about **$425-550 each**, with three spare bare brains and eight spare cards.
A second run of five assembled units would be about $450-650 for the boards plus $160-170 per unit on top. Eight fitted bays add four cards
(about $16 each with parts and board) and four cables, plus the 150-180 W brick and heavier input parts (STATUS R23).

## Before the order can go in

| # | Gate | Status |
|---|---|---|
| 1 | Routing finished and DRC-clean | done 2026-09-25: 0 open connections, 0 DRC errors on both boards, pairs matched; **not yet reviewed by a board engineer** (STATUS R25 to R29) |
| 2 | Stack-up chosen with the fab and the pair geometry recalculated for it | open, R26: the pair class was set for a four-layer stack-up |
| 3 | SATA receptacle and PCIe slot footprints from the vendor drawings | done 2026-09-25; the Molex mating face and the socket housing ends to check against the 3D models (R28) |
| 4 | M.2 socket peg check against the TE drawing | open, R2 (drawing received) |
| 5 | DIN pinout matched to the chosen brick | open, R3, B3 |
| 6 | Vendor part numbers on every BOM line, checked against stock the day of ordering | BOM generated; lines marked `verify` remain |
| 7 | Gerbers, drill, pick-and-place and BOM exports from `kicad-cli`, plus the assembly drawings | `BD_PROJECT=brain\|card sh hardware/tools/export_fab.sh` writes `hardware/fab/<date>/<board>/` (gitignored); run it after the engineer's changes |
| 8 | Fab DFM check on the gerbers (0.3/0.15 mm vias, 0.4 mm QFN dog-bones, hole-to-hole, edge clearance) | open |
| 9 | Test points, fiducials, panel drawing for the card, silkscreen cleaned | open, R29 |
| 10 | Bench evidence that the ASM1153E passes Sanitize through | 2026-09-26 |

## Ordering checklist (JLCPCB flow)

1. `BD_PROJECT=brain sh hardware/tools/export_fab.sh` and again with `BD_PROJECT=card`: gerber + drill zip, placement CSV, BOM CSV, assembly PDFs, an errors-only DRC report. Add LCSC numbers to the BOM lines first (gate 6).
2. Upload the zip, pick 6 layers (brain) or 4 layers (card), 1.6 mm, ENIG, the impedance stack-up, 5 pcs.
3. Tick "PCB assembly", 2 pcs, both sides, standard tier; upload BOM + placement.
4. In the parts matcher, confirm every line; for anything out of stock choose an
   equivalent or mark DNP and note it in `docs/BOM.md`.
5. Review the placement preview (rotations of polarised parts and the QFNs).
6. Order; expect 2–3 weeks to the door.

What still gets soldered at home: nothing on the board. Press the CM5 on, screw
the cooler, fit the OLED lead to J41, heat-set the inserts, close the lid.
