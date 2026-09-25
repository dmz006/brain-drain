# Status

Last updated 2026-09-25. One line per workstream, then the remaining and blocked lists with stable ids (never reused).
For the engineer taking over the boards, start with [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md).

| Workstream | State | Evidence |
|---|---|---|
| Design docs | complete for the current design: brain board plus bay cards (C24), six layers (C26), 45 mm card (C27); decisions C1 to C27 closed, D5 (OLED size) and D6 (option B, bridges in the cables) open | [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md), [FABRICATION.md](FABRICATION.md), [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md) |
| Schematic | two projects generated from one netlist source (`BD_PROJECT=brain\|card`): brain 0 ERC findings, bay card 2 harmless library-copy warnings | `hardware/review/*-schematic.pdf`, `hardware/renders/schematic/` |
| Boards | **Brain 150 x 122 mm, six layers; bay card 45 x 46 mm, four layers.** Both routed by the unattended flow: 0 open connections, 0 DRC errors, all 44 + 8 differential pairs length-matched end to end. Connector footprints (PCIe x1 slot, SATA receptacle) come from the vendor drawings. **Never reviewed by a board designer; nothing simulated; pair geometry still set for a four-layer stack-up.** Details and risks in the review guide | `hardware/review/`, `hardware/routing/`, `hardware/bay-card/routing/`, `hardware/renders/layers/` |
| Footprints | DIN, TPS56637, PCIe x1 socket, SATA receptacle generated from drawings; CM5 and M.2 copied from the CM5IO project (the M.2 not yet compared with the TE drawing) | `hardware/review/footprints.md` |
| BOM | generated from the designs, vendor part numbers where known, `verify` flags where the orderable number must be checked | [BOM.md](BOM.md), `hardware/bom/*.csv` |
| Software | engine, policy, fence, overwrite/verify, firmware wrappers, certificates, eight bays plus the M.2 bay (bay 9), bench tool, Pi deployment, Wi-Fi access point with QR code and phone page, DIP service mode; **74 tests pass, ruff clean**; firmware, GPIO, OLED and nmcli paths untested on hardware | [testing-tracker.md](testing-tracker.md) |
| Enclosure | box about 157 x 145 x 62 mm: tray 16 mm deeper behind the board for the card overhang, lid hinged at the rear with a snap latch at the front, eight receptacle windows, OLED window, DIP slot, LED holes, CM5 grille; STLs export clean; not printed | `enclosure/`, [RENDERS.md](RENDERS.md) |
| Renders | boards one by one, the electronics assembled, the case, the unit open, exploded, cut-away and the complete system, plus per-layer PCB images | [RENDERS.md](RENDERS.md), `docs/img/renders/` |

## Remaining work (R)

| id | Item | Depends on | Notes |
|---|---|---|---|
| R1 | (closed 2026-09-25) SATA receptacle and PCIe slot footprints from the Molex and Amphenol drawings | | assumptions left: A3, A4 in the review guide |
| R2 | Compare the M.2 socket footprint (from CM5IO) with the TE 2199230-4 customer drawing | drawing received | `hardware/ref/datasheets/te-2199230-4-drawing.pdf` |
| R3 | Wire the DIN jack pins to the chosen 12 V brick's pinout | B3 | `design.py` J21 note |
| R4 | (closed 2026-09-25) routing: 0 open connections, 0 DRC errors on both boards | | review caveats R25 to R29 |
| R5 | Bench: bridge Sanitize / Security Erase passthrough, hot-plug behaviour, hdparm status parser fixture | bench day 2026-09-26 | closes C12 with evidence; may reorder `policy.py` chains |
| R6 | (obsolete: the bay LED is sunk by the bridge's LED pin through the slot, no GPIO) | | |
| R7 | Confirm USB5744 strap values and crystal load caps against the datasheet | layout engineer | notes in `CONNECTIONS.md` |
| R8 | (closed: magjack removed, C22) | | |
| R9 | Real HAL bring-up: GPIO (libgpiod v2), OLED, bay power, M.2 door / PEDET | first board | code written, untested |
| R10 | Fabrication: gerbers, six-layer and four-layer quote with assembly, order | R25 to R29 | [FABRICATION.md](FABRICATION.md) |
| R11 | First enclosure print and fit check (DIN round face, receptacle windows, card overhang, lid fit) | print | |
| R12 | Certificate export to USB stick / HTTP push | | schema v1 written locally only |
| R13 | OLED size decision D5 | owner | 0.96" assumed in the bezel |
| R14 | GitHub Actions: pytest + ruff, ERC on push, STL export | | |
| R15 | Software: real udev watcher tested with a dock (`sim/udev.py`) | R5 | |
| R16 | (closed 2026-09-23) staged autorouting flow | | superseded by `route_full.sh` |
| R17 | Enclosure fit review: DIN round face, hinge knuckle clearance and pin, latch force, OLED lead length, lid switch travel | R11 | |
| R18 | Option B study (D6): bridges in the cables | owner | `decisions/2026-09-23-portable-brain.md` |
| R19 | Wireless bring-up on the Pi: nmcli hotspot, join, resets; `dtparam=ant1` and the antenna strip | first board | `wifi.py`, simulated only |
| R20 | Fabrication order pack: gerbers, drill, placement, BOM with vendor part numbers | R10 | JLCPCB first, PCBWay fallback |
| R21 | (closed) bay 12 V track width | | planes carry the current; review item 4.3 |
| R22 | (closed 2026-09-25) differential pairs matched end to end | | segment-level mismatch is a review item (4.1) |
| R23 | Eight-bay power: 150 to 180 W brick, larger input fuse, DIN pin paralleling, heavier bulk caps, 5V_HDD buck at its limit; card retention in the enclosure | before slots 5 to 8 are used | ARCHITECTURE 3.5 |
| R24 | (closed 2026-09-25) FET pin tables: AON7403 and AO4407A read against the datasheets | | S 1-3, G 4, D 5-8 confirmed |
| R25 | Layout review by a board engineer of both boards | hand-off | [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md) |
| R26 | Choose the fab's six-layer stack-up and recalculate the pair geometry (90 ohm, 85 ohm PCIe) | R25 | review item 4.1 |
| R27 | Decide the In3 / In4 arrangement: pairs on In3 run over split power islands, In2 / In3 are adjacent signal layers | R25 | review item 4.1 |
| R28 | Check the Molex mating-face position and the socket housing ends against the vendors' 3D models | STEP files received | review items A3, A4 |
| R29 | Add test points, fiducials, ESD protection where wanted, the card panel; clean the silkscreen | R25 | review items 4.5, 4.6 |
| R30 | Correct the CM5 value field (CM5002016 in the schematic, wireless SKU is CM5102016) at the next regeneration | | BOM note |

## Blocked on external input (B)

| id | Item | Who | Where |
|---|---|---|---|
| B1 | (received 2026-09-24) Molex 47018-4001 sales drawing, datasheet and STEP | | `hardware/ref/datasheets/` |
| B2 | (received 2026-09-24) TE 2199230-4 customer drawing | | same; comparison is R2 |
| B3 | 12 V brick selection, datasheet and its DIN pinout | owner chooses | `hardware/ref/DOWNLOADS.md` |
| B4 | Bench results 2026-09-26 (JSON under `hardware/ref/bench/`) | bench day | `docs/saturday-bench-plan.md` |
| B5 | Repository visibility and GitHub auth | owner; licence chosen (Polyform Noncommercial, C20) | done for the public repository |
| B6 | (received) Amphenol FCI 10018784 customer drawing (PCIe x1 socket), AON7403 and AO4407A datasheets | | `hardware/ref/datasheets/` |

## What is verified vs. assumed

Verified from documents: every CM5, USB5744 and ASM1153E pin; the DIN, TPS56637, PCIe x1 socket and SATA receptacle footprint geometry
(vendor drawings); the FET pin tables; CM5 mechanical positions and the antenna edge; the ERC and DRC results (kicad-cli 9.0.8).

Assumed until the bench, the first board or a design review: bridge firmware behaviour under Sanitize, the hdparm status text format,
crystal load capacitors, all enclosure clearances, the nmcli hotspot flow, everything in `hal/gpio.py` and `hal/oled.py`, the signal
integrity of every high-speed link, the power planes' current capacity, and the eight-bay power budget.
