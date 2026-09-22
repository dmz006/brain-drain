# Status

Last updated 2026-09-23. One line per workstream, then the remaining and
blocked lists with stable ids (never reused).

| Workstream | State | Evidence |
|---|---|---|
| Design docs | complete for v0; decisions C1–C19 closed, D5 (OLED size) open | `ARCHITECTURE.md`, `DECISIONS.md` |
| Schematic | generated, **0 ERC errors**, 13 warnings (9 lib-cache notes on 2N7002, 4 placeholder SATA footprints) | `hardware/renders/schematic/` |
| Board | 180 × 110 mm, 307 footprints placed with nets, net classes, copper zones (GND on In1 and B.Cu, +12V / 5V_SYS / 5V_HDD / +3V3 islands on In2), hole keep-outs. **Autorouted signal nets: 71 nets, 630 segments, 68 vias, 3.8 m** (freerouting on the single-ended, non-bay nets). DRC: 1 error (starved_thermal 1), warnings are silkscreen and zone-island notes. Left for the KiCad GUI: I2C1_SCL, I2C1_SDA, DIP1, DIP2, DIP4, DIP8, SD_CMD, M2_PEDET, ETH_nLED3 (cleared where the router crossed the CM5 standoff keep-outs), all USB 3 / SATA / PCIe pairs, the bay sheets, and power vias for SMD pads | `hardware/renders/board-top.png`, `board-3d-top.png` |
| Footprints | DIN, TPS56637 generated from drawings; CM5 and M.2 copied from the CM5IO design files; **SATA 22-pin is a placeholder** | `hardware/lib/brain-drain.pretty/README.md` |
| Software | engine, policy, fence, overwrite/verify, firmware wrappers, certificates, bay 5, bench tool, Pi deployment; **61 tests pass**; firmware paths untested on hardware | `docs/testing-tracker.md` |
| Enclosure | tray, lid, blank and hinged doors, OLED bezel, feet, drive rack; STLs export clean; not printed | `enclosure/renders/` |

## Remaining work (R)

| id | Item | Depends on | Notes |
|---|---|---|---|
| R1 | SATA 22-pin footprint from Molex drawing SD-47018-001 | B1 | then regenerate board, reroute the four bays |
| R2 | Verify the M.2 socket footprint pegs against the TE 2199230-4 drawing | B2 | footprint currently from CM5IO (different vendor, same land pattern) |
| R3 | Wire the DIN jack pins to the chosen 12 V brick's pinout | B3 | `design.py` J21 note |
| R4 | Finish routing in the KiCad GUI: the 71 autorouted signal nets are in; hand-route I2C1_SCL, I2C1_SDA, DIP1, DIP2, DIP4, DIP8, SD_CMD, M2_PEDET, ETH_nLED3, power vias for SMD pads, then USB 3 / SATA / PCIe pairs with length matching, and clear the one starved-thermal note on J5 | R1 | net classes, zones and CM5 hole keep-outs are set by `route.py prepare`. Autorouting was tried on 2026-09-23 with freerouting 2.1.0: the full board stalled at 646 unrouted after 35 passes, a reduced net set at 443 (logs in `hardware/routing/*-attempt.log`, gitignored). Likely causes: ground/power pins routed as tracks instead of via zones, tight 0.15 mm pair rules, placeholder SATA pads, auto-placement overlaps. After the placement fix (pad rotation bug, packer capacity checks) freerouting routed all but one signal connection in 15 passes; its optimizer loops forever without `-oit`, so run it with `-oit 2` |
| R5 | Bench: bridge Sanitize / Security Erase passthrough, hot-plug behaviour, hdparm status parser fixture | Saturday 2026-09-26 | closes C12 with evidence; may reorder `policy.py` chains |
| R6 | Identify the ASM1153E LED GPIO (assumed GPIO0) | first board | |
| R7 | Confirm USB5744 port-disable strap resistor value and crystal load caps | datasheet re-read | notes in `CONNECTIONS.md` |
| R8 | Magjack pair order and LED polarity against the UDE drawing | drawing | |
| R9 | Real HAL bring-up: GPIO (libgpiod v2), OLED, bay power, M.2 door/PEDET | first board | code written, untested |
| R10 | Fabrication: gerbers, JLCPCB 4-layer + SMT quote, order 5 | R4 | |
| R11 | First enclosure print and fit check (DIN round face, SATA latch clearance, lid fit) | R10 or board dimensions | |
| R12 | Certificate export to USB stick / HTTP push | — | schema v1 written locally only |
| R13 | OLED size decision D5 | owner | 0.96" assumed in the bezel |
| R14 | GitHub Actions: pytest + ruff, ERC on push, STL export | after first push | |
| R15 | Software: real udev watcher tested with a dock (`sim/udev.py`) | R5 | |

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
Raspberry Pi footprint geometry; CM5 mechanical positions; part prices (Sept 2026).

Assumed until the bench or the first board: bridge firmware behaviour under
Sanitize, the hdparm status text format, the LED GPIO, crystal load capacitors,
magjack pin order, all enclosure clearances, and everything in `hal/gpio.py`
and `hal/oled.py`.
