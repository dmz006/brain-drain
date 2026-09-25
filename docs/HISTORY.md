# Project history

Short session log so a reader (or an agent) knows how the repository got here.
Details are in `DECISIONS.md`, `CHANGELOG.md` and the git log.

| Date | What happened |
|---|---|
| 2026-09-21 | Repo scaffolded: architecture, BOM, decisions. Found that the CM4 has no native USB 3; proposed a PCIe xHCI, then moved the design to the CM5 (C7) after pricing showed a $10 gap. |
| 2026-09-22 | Software first: engine, policy, fence, overwrite/verify, certificates, simulator (45 tests). UX simplified to "plug in = wipe, unplug = abort", no button (C10). Decision brief on hub, bridge, input connector, LEDs, M.2; owner chose USB5744, ASM1153E, 4-pin DIN, 3 mm LEDs, populated M.2 (C11–C15). |
| 2026-09-23 | Schematic generated from a single netlist (0 ERC errors), footprints from vendor drawings, board outline A (C19), placement generator. Bay 5 software, bench tool, Pi deployment for the 2026-09-26 bench. Enclosure v1 and refinements. CM5IO reference design files used to fix the CM5 footprint, M.2 footprint and several control-pin details. Docs, diagrams, renders, logo, AGENT.md; autoroute pass on non-bay nets. Later the same day the owner redirected the product to a portable box with drives on cables (no rack): options A/B/C briefed, A chosen, B parked (C21, D6); board re-laid out at 150 × 98 mm, enclosure v1 box, renders redone. Then, same session: passive cooler, keep the M.2 but open the lid for it, drop Ethernet, drop the buzzer, Wi-Fi access point with a QR code on the OLED and a phone page with join/reset (C22–C23); board v2 at 136 × 100 mm with the antenna edge, hinged-lid enclosure, fabrication vendor page. |

| 2026-09-23 (evening) | Portable "brain box" (C21–C23): cabled drives, no Ethernet, no buzzer, Wi-Fi AP with a QR code and a phone page, hinged lid. Staged autorouting reached 83 % on the monolithic v3 board; D8 small vias applied. Then the split into a brain and plug-in bay cards (C24, eight slots, four fitted) with a second KiCad project, eight-bay software and a taller enclosure; routing chains launched on both boards. |
| 2026-09-24 to 25 | Routing brought to completion: pairs routed first, a grid gap router, a length tuner, bottom-side hub bypass caps, six layers for the brain (C26), real footprints from the Amphenol and Molex drawings and the 45 mm card with a 15 mm rear overhang (C27), end-to-end pair matching. Both boards 0 open connections and 0 DRC errors. Enclosure x-mirror bug found and fixed. Full render gallery, generated BOM and review pack, and the engineer hand-off guide written. |

Rules of engagement that shaped the work: the owner makes every decision
(interview style, one question at a time); every pin comes from a datasheet
table saved in the repo; generated files are never hand-edited.
