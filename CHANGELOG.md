# Changelog

All notable changes to brain-drain. Format follows Keep a Changelog; versions
are software versions (`software/pyproject.toml`), hardware and enclosure
revisions are noted in the entries.

## [Unreleased]

### Added
- Architecture, BOM, decisions log (C1–C19) and decision briefs.
- `braindrain` sanitizer service: engine, NIST 800-88 Rev. 2 policy, safety
  fence, host overwrite and firmware wrappers, verification, certificates,
  simulation mode, bay 5 M.2 slot controller, bench tool, headless Pi
  deployment (61 tests).
- Generated KiCad 9 schematic (14 sheets, 0 ERC errors) and board (180 × 110 mm,
  307 footprints, net classes, copper zones) from `hardware/tools/design.py`;
  symbol and footprint generators; routing pipeline via freerouting.
- Parametric OpenSCAD enclosure: tray, lid, hinged door, OLED bezel, drive rack.
- Documentation set, diagrams, renders, logo.

### Added
- **Wireless (C22):** Wi-Fi access point with an ephemeral key and a QR code on the OLED, the
  phone page (`webui.py`: status, certificates, log, join a network, Wi-Fi / factory reset with the
  key), `wifi.py` (nmcli backend, simulated backend), DIP service mode 110, `braindrain wifi-reset`.
  13 new tests (74 total). Dependency: `qrcode`.
- `docs/FABRICATION.md`: small-run assembly vendors, cost estimate, order gates and checklist.

### Added
- **Six-layer brain (C26, 2026-09-24):** F sig / In1 GND / In2 sig / In3 sig / In4 power / B sig. Full unattended flow: 2 connections open (was 10 on four layers), 0 DRC errors, all 44 pairs routed, 43 matched; flow time 85 minutes (was 3.5 hours). The gap router routes on every signal layer.
- **Bottom-side bypass caps (2026-09-24):** the ten supply bypass capacitors of each USB hub are generated on the bottom in two rows around the chip. Open supply pins went from 25 to none; the brain now has 10 open (8 pair ends, the fan tach, one inner-plane island), 43 of 44 pairs matched, DRC 0 copper errors. `gapclose.py` also has an experimental rip-up mode (`BD_RIPUP=1`) that crosses other nets at a price and removes what it crosses; it did not converge (open count went 10, 21, 29, 25 over three rounds) and is off by default.
- **Pairs-first routing and gap closer (2026-09-24):** `tools/route_full.sh` regenerates the board and routes the differential pairs first on the empty board (`stage0`, `BD_PAIRS_FIRST=1`) so their escapes from the 0.4 mm-pitch pins are free; single-ended stages route around them. `route.py close-gaps` (`tools/gapclose.py`) is a small grid A* router (0.1 mm cells, both outer layers, vias, adaptive search window, pair sides hug their partner) that closes what the autorouter leaves; every route is DRC-checked and removed whole if flagged. `route.py rip-pairs` and `tools/reroute_pairs.sh` handle pairs the tuner cannot fix. Results: card 1 open, 0 DRC errors, 8/8 pairs matched; brain 9 open (was 43), 0 copper errors, 41/44 pairs matched.
- `tools/pcbfix.py`: generated boards carried duplicate pad UUIDs (363 on the brain), so DRC reported the wrong slot pad; they are now made unique at generation.
- **Length tuner (`route.py tune`, 2026-09-24):** meanders the shorter side of every routed differential pair (rectangular bumps 0.5 mm wide, up to 4 mm tall, layer-aware collision checks, keep-outs respected, last bump cut to the exact remainder). Skew now counts 0.6 mm per via. Bay card: 5 of 8 pairs matched to under 0.01 mm; brain: 26 pairs tuned, 10 left (sides unrouted or more than 40 mm apart). No new DRC errors on either board. Part of `route_chain.sh`.

### Fixed
- **P-FET pin-out (2026-09-23):** Q20 (AO4407A, SO-8) and the bay cards' Q1 / Q2 (DFN 3x3) used the
  generic three-pin `Q_PMOS_GSD` symbol, which put gate, source and drain on pads 1, 2 and 3; on these
  8-pin power packages pads 1–3 are all source, 4 is the gate and 5–8 (plus the exposed pad) the drain.
  New library symbols `PMOS_SSSGDDDD` / `PMOS_SSSGDDDD_EP` carry the real numbering; `route.py
  update-nets` re-syncs the pad nets on the routed boards and the router finishes the moved pins.
- `gen_sch.py` wiped the board design rules (0.3 mm via, 0.15 mm hole) from the project file on every
  run; it now keeps them, and both projects have them again.

### Changed
- **Brain + bay cards (C24, D9 option A, 2026-09-23):** the design is split into a brain board
  (150 × 122 mm: CM5 on the right edge, two hubs with all four downstream ports, eight PCIe-x1
  bay slots along the rear with the bay LEDs, M.2 bay 9, DIN / USB-C / microSD on the left wall)
  and one bay-card design (40 × 46 mm: ASM1153E, switched 12 V / 5 V with PTC fuses, SATA 22-pin
  receptacle on top, PCIe-x1 fingers). Four cards fitted in v1, slots 5–8 for expansion. Second
  KiCad project `hardware/bay-card/` from the same generators (`BD_PROJECT=brain|card`, `project.py`);
  slot pinout in `symgen.SLOT_PINS`; placeholder socket footprint. Software: eight bays (bay ports
  1-1.1..1-1.4 and 2-1.1..2-1.4, BAY_EN GPIOs 5,6,12,13,7,8,9,10), M.2 is bay 9, two-column OLED
  layout above five bays. Enclosure: 50 mm above the board, eight lid windows for the card
  receptacles, left-wall cutouts, vents on the right and rear; about 157 × 129 × 62 mm. Docs, BOM
  (card table), fabrication (two boards, panelised cards) and cost table updated.
- D8 applied: 0.3 / 0.15 mm dog-bone vias on the QFN supply pins (`fanout_qfn`); unattended routing
  chain `tools/route_chain.sh` (stage 2 → stage 3 → DRC clean → fanouts → reports → renders).
- Board v3 (D7 option B): 150 × 112 mm, 2.5 mm around every QFN, hubs under the CM5 USB 3 pins, M.2
  front-right; pipeline rerun: 733 / 884 connections (83 %), 3300 segments, 738 vias, DRC copper-clean,
  21 of 48 pairs routed (unmatched). The connector fanout no longer touches QFNs (its via ring blocked
  the neighbouring pins); D8 proposes 0.3/0.15 mm vias for the QFN supply pins as the next lever.
- Staged autorouting completed as far as the tools go (2026-09-23): 719 / 884 connections (81 %), 3175
  segments, 658 vias, DRC copper-clean. Tooling: staged runs with locked routes (`stage1/2/3`), `-inc`
  class ignoring, `BD_ROUTER=2.4.1` / `BD_PASSES` for the newer bounded router, `drc-clean`, geometry-aware
  fanout collision checks (`Occupancy`), row-fitted connector fanout with orientation-correct pad sizes,
  exposed-pad ties, DRC-driven open-pad detection, `pair_report`, `open_report`. What remains is listed in
  `hardware/routing/open.md` and `pairs.md` and decision D7.
- Routing rerun on the v2 outline: all 75 single-ended signal nets routed (930 segments, 214 vias); the
  fanout now checks the plane polygon, not its bounding box; `route.py prepare` writes the net classes
  into the project file (their only home) and `gen_sch.py` preserves them; session import strips
  anything crossing a keep-out; board renders cropped to the outline; schematic renders regenerated by
  the same script.
- **v2 outline (C22–C23):** 136 × 100 mm, no Ethernet (magjack and CM5 PHY pins dropped), no
  buzzer, passive CM5 cooler (fan header kept), CM5 wireless with its antenna edge on the left
  board edge and a copper-free strip under it; DIN / USB-C / microSD on the right wall; the M.2
  lies along the front under a lid hinged along the rear with a snap latch (lid microswitch is the
  bay-5 door). Enclosure about 143 × 107 × 32 mm; scene render of the lid open. Wall panel
  diagrams now rear and right.
- **Portable "brain box" (C21, 2026-09-23):** the board is re-laid out at 150 × 98 mm with the four
  SATA receptacles on the rear edge, DIN / RJ45 / USB-C on the left wall, microSD and the M.2 SSD
  slot on the front wall, the CM5 in landscape, CR2032 holder and buzzer on the bottom side. The
  enclosure is a closed box of about 157 × 105 × 39 mm with an M.2 slot door on the front; the drive
  rack is removed, drives lie loose on 22-pin cables. Placement is checked by `check_place.py`;
  board renders come from `render_board.sh`. The v0 autoroute was discarded with the outline (R16).
- Enclosure preview renderer: camera matrices fixed (world up is up, viewer above the cable side),
  large triangles subdivided so the painter's sort no longer draws walls over the lid.
- Option B (bridges in the cables, ~90 × 70 mm board) recorded as D6 for a later study.

### Fixed
- Board generator: pad angles now follow footprint rotation (KiCad stores them absolute), which
  removed the overlapping pads on every rotated fine-pitch part; region packer with capacity checks
  and a spill area; DIN jack pads shorter than their pitch; M.2 footprint mask margins removed;
  USB-C moved to the left wall; DRC now reports 0 errors before routing.
- Routing: freerouting 2.1.0 (Java 21) on the single-ended non-bay nets: 71 nets, 630 segments, 68 vias imported; tracks that crossed the CM5 standoff clearance were removed and circular keep-outs added for future runs.

### Dependencies
- Python: pyudev; dev: pytest, ruff, pillow, numpy, cairosvg; hw: gpiod, luma.oled, smbus2.
- Tools (not vendored): KiCad 9.0.8, OpenSCAD 2021.01, freerouting 2.1.0 jar (downloaded into `hardware/tools/freerouting/`, gitignored), Java 21.
