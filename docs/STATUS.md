# Status

Last updated 2026-09-23 (v2 outline, wireless). One line per workstream, then the remaining and
blocked lists with stable ids (never reused).

| Workstream | State | Evidence |
|---|---|---|
| Design docs | complete for v2; decisions C1–C23 closed, D5 (OLED size) and D6 (option B, bridges in the cables) open; fabrication vendors and cost estimate written | `ARCHITECTURE.md`, `DECISIONS.md`, `FABRICATION.md`, `decisions/2026-09-23-portable-brain.md` |
| Schematic | generated, **0 ERC errors**, 13 warnings (9 lib-cache notes on 2N7002, 4 placeholder SATA footprints) | `hardware/renders/schematic/` |
| Board | **v2 outline 136 × 100 mm (C21–C23)**: four SATA receptacles on the rear edge at 28.9 mm pitch; DIN / USB-C / microSD / fan header on the right wall; the left edge is the CM5 wireless antenna edge (8 mm copper-free strip, nothing metal within 10 mm); CM5 landscape at the left, hubs and buck column to its right; M.2 socket front-left with the 2280 module lying along the front under the hinged lid (its small passives sit under the SSD); lid microswitch rear-right; CR2032 holder and the two service headers on the bottom. No Ethernet, no buzzer. 299 footprints placed with nets, `check_place.py` clean, net classes, copper zones (GND on In1 and B.Cu; 5V_SYS, 5V_HDD, +3V3 and +12V islands on In2), CM5 hole and antenna keep-outs. **DRC 0 errors, 0 tracks**: routing to be rerun on this outline (R16) | `hardware/renders/board-top.png`, `board-3d-iso.png`, `board-3d-bottom.png` |
| Footprints | DIN, TPS56637 generated from drawings; CM5 and M.2 copied from the CM5IO design files; **SATA 22-pin is a placeholder** | `hardware/lib/brain-drain.pretty/README.md` |
| Software | engine, policy, fence, overwrite/verify, firmware wrappers, certificates, bay 5, bench tool, Pi deployment; **Wi-Fi access point with an ephemeral key and QR code on the OLED, phone page (status, certificates, log, join a network, Wi-Fi / factory reset), DIP service mode**; **74 tests pass**; firmware, GPIO, OLED and nmcli paths untested on hardware | `docs/testing-tracker.md` |
| Enclosure | v2 "brain box" about 143 × 107 × 32 mm: tray with cutouts on the rear (cables) and right (power, USB-C, microSD) walls, vents on the antenna side and the front, a lid hinged along the rear edge with a snap latch at the front that opens for the M.2 SSD; lid has the OLED window over the SSD, DIP slot, 8 LED holes and a convection grille over the passive cooler. STLs export clean; renders of the closed unit on the bench and of the lid open; not printed | `enclosure/renders/` |

## Remaining work (R)

| id | Item | Depends on | Notes |
|---|---|---|---|
| R1 | SATA 22-pin footprint from Molex drawing SD-47018-001 | B1 | then regenerate board, reroute the four bays |
| R2 | Verify the M.2 socket footprint pegs against the TE 2199230-4 drawing | B2 | footprint currently from CM5IO (different vendor, same land pattern) |
| R3 | Wire the DIN jack pins to the chosen 12 V brick's pinout | B3 | `design.py` J21 note |
| R4 | Finish routing in the KiCad GUI after R16: hand-route whatever the router leaves, power vias for the IC and connector pins the fanout skips, then USB 3 / SATA / PCIe pairs with length matching | R16, R1 | net classes, zones and CM5 hole keep-outs are set by `route.py prepare`. Autorouting was tried on 2026-09-23 with freerouting 2.1.0: the full board stalled at 646 unrouted after 35 passes, a reduced net set at 443 (logs in `hardware/routing/*-attempt.log`, gitignored). Likely causes: ground/power pins routed as tracks instead of via zones, tight 0.15 mm pair rules, placeholder SATA pads, auto-placement overlaps. After the placement fix (pad rotation bug, packer capacity checks) freerouting routed all but one signal connection in 15 passes; its optimizer loops forever without `-oit`, so run it with `-oit 2` |
| R5 | Bench: bridge Sanitize / Security Erase passthrough, hot-plug behaviour, hdparm status parser fixture | Saturday 2026-09-26 | closes C12 with evidence; may reorder `policy.py` chains |
| R6 | Identify the ASM1153E LED GPIO (assumed GPIO0) | first board | |
| R7 | Confirm USB5744 port-disable strap resistor value and crystal load caps | datasheet re-read | notes in `CONNECTIONS.md` |
| R8 | (closed: magjack removed, C22) | — | |
| R9 | Real HAL bring-up: GPIO (libgpiod v2), OLED, bay power, M.2 door/PEDET | first board | code written, untested |
| R10 | Fabrication: gerbers, JLCPCB 4-layer + SMT quote, order 5 | R4 | |
| R11 | First enclosure print and fit check (DIN round face, SATA latch clearance, lid fit) | R10 or board dimensions | |
| R12 | Certificate export to USB stick / HTTP push | — | schema v1 written locally only |
| R13 | OLED size decision D5 | owner | 0.96" assumed in the bezel |
| R14 | GitHub Actions: pytest + ruff, ERC on push, STL export | after first push | |
| R15 | Software: real udev watcher tested with a dock (`sim/udev.py`) | R5 | |
| R16 | Rerun the routing pipeline on the v1 outline: `route.py fanout`, `dsn`, freerouting with `-oit 2` on the lite DSN, `import`, strip keep-out crossings, DRC | — | the v0 run proved the flow (all but one signal connection in 15 passes); the DSN carries the In2 planes so power nets can be tried with them |
| R17 | Enclosure fit review of the v2 box: DIN round face on the right wall, hinge knuckle clearance and pin, latch snap force, OLED lead length from J41 to the window over the SSD, lid switch travel | R11 | |
| R18 | Option B study (D6): bridges in the cables, board shrinks to about 90 × 70 mm | owner | `decisions/2026-09-23-portable-brain.md` |
| R19 | Wireless bring-up on the Pi: nmcli hotspot + shared IPv4, join, resets; confirm `dtparam=ant1` and the antenna strip on the first board | first board | `software/braindrain/wifi.py`, simulated only |
| R20 | Fabrication order pack: gerbers, drill, placement and BOM exports with vendor part numbers (`FABRICATION.md` gates 5–6) | R4, R1–R3 | JLCPCB first, PCBWay fallback |

## Blocked on external input (B)

| id | Item | Who | Where |
|---|---|---|---|
| B1 | Molex 47018-4001 sales drawing | owner downloads | `hardware/ref/DOWNLOADS.md` |
| B2 | TE 2199230-4 customer drawing | owner downloads | same |
| B3 | 12 V / 10 A brick selection and its DIN pinout | owner chooses | same |
| B4 | Bench results 2026-09-26 (JSON under `hardware/ref/bench/`) | bench day | `docs/saturday-bench-plan.md` |
| B5 | Repository visibility and GitHub auth | owner decides; licence chosen (Polyform Noncommercial, C20) | needed before the first push |

## What is verified vs. assumed

Verified from documents: every CM5, USB5744 and ASM1153E pin; Kycon, TI and
Raspberry Pi footprint geometry; CM5 mechanical positions and the antenna edge
(CM5IO reference board puts the MH1 edge flush with its board edge); part prices (Sept 2026).

Assumed until the bench or the first board: bridge firmware behaviour under
Sanitize, the hdparm status text format, the LED GPIO, crystal load capacitors,
all enclosure clearances, the nmcli hotspot flow, and everything in `hal/gpio.py`
and `hal/oled.py`.
