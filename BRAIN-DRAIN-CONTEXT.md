# BRAIN-DRAIN-CONTEXT.md

What the project is and where everything is, as of 2026-09-26 (decisions C1 to C30). Read this first to get oriented.
How we keep the repository consistent is in [AGENT.md](AGENT.md); local Claude Code settings are in [CLAUDE.md](CLAUDE.md).
Deeper documents: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (the design), [docs/STATUS.md](docs/STATUS.md) (what is done and open),
[docs/DECISIONS.md](docs/DECISIONS.md) (every decision), [docs/LAYOUT-REVIEW.md](docs/LAYOUT-REVIEW.md) (hand-off to a board engineer).

## The product

A standalone, portable disk sanitizer that follows NIST SP 800-88 Rev. 2 (Clear and Purge) for ATA and NVMe media. Up to **eight**
SATA drives (four bay cards fitted in version 1) plus an **M.2 NVMe bay 9** are wiped at once. A Raspberry Pi **CM5** (wireless,
2 GB RAM, 16 GB eMMC) runs the Python service. A 128 x 64 OLED shows per-drive progress, the CM5 makes a Wi-Fi access point with a QR
code and a phone page, and every drive gets a JSON sanitization certificate. Drives lie loose on the bench and connect with SATA
extension cables that rise through windows in the lid. There is no rack, dock or backplane. Power is one 12 V brick into a 4-pin DIN jack.

Not in scope: physical destruction, degaussing, signed or PKI certificates, Ethernet, touchscreen, wiping the CM5's own eMMC (forbidden).

## The design as built

| Part | What it is |
|---|---|
| **Brain board** | 150 x 122 mm, six layers (C26). CM5 on the right edge with its antenna outside, two USB5744 hubs, eight PCIe x1 bay slots along the rear edge (custom bay pinout, no PCIe signalling), M.2 socket, DIN 12 V, USB-C, microSD, 5 V and 3.3 V buck converters, service headers, lid switch, DIP switch, OLED header. Top silkscreen carries the logo, name, revision and repository URL. |
| **Bay card** | 45 x 46 mm, four layers (C27). ASM1153E USB 3.0 to SATA bridge, P-FET switches for 12 V and 5 V with resettable fuses, Molex 22-pin SATA receptacle on the top edge, PCIe x1 edge fingers. It stands upright in a slot and overhangs the brain's rear edge by 15.3 mm. One design, up to eight cards. |
| **Enclosure** | OpenSCAD tray and lid hinged at the rear with a snap latch, about 157 x 145 x 62 mm. Eight receptacle windows, OLED window, DIP slot, LED holes and a CM5 grille in the lid. A comb of ribs under the lid and grooved blocks in the tray hold the cards (C30). The logo and name are engraved in the lid. |
| **Software** | `software/braindrain`: engine, NIST policy, safety fence, host overwrite and firmware Sanitize wrappers, verification, certificates, per-bay state machine, Wi-Fi access point, OLED and GPIO drivers (untested on hardware), simulator. 74 tests. |

Power: about 9.5 A typical for eight drives, so a 150 to 180 W, 12 V brick is needed for eight bays and 120 W covers four. The 12 V brick is
not chosen yet (B3); its DIN pinout decides how the jack is wired.

## State

- Schematics: two projects, ERC clean (card has 2 harmless library-copy warnings).
- Boards: both routed by the unattended flow, 0 open connections, 0 DRC errors, all differential pairs length-matched end to end.
  **No board designer has reviewed them, nothing is simulated, and the pair geometry is still set for a four-layer stack-up.**
- Enclosure: STLs export clean, nothing printed yet. Renders of everything are in `docs/img/renders/`.
- Nothing has run on real hardware. The first bench day is 2026-09-26 (`docs/saturday-bench-plan.md`).
- Open: 12 V brick datasheet (B3), layout review items A1 to A14, OLED size (D5), option B with bridges in the cables (D6), M.2 footprint check (R2).

## Repository map

| Path | Contents |
|---|---|
| `software/` | Python package `braindrain`, tests, deploy files for the Pi, bench and mockup tools. Own venv in `software/.venv` (pytest, ruff, cairosvg). |
| `hardware/` | KiCad projects: brain (`brain-drain.*`) and `bay-card/`. `tools/` holds every generator (below). `ref/` datasheet pin tables (vendor PDFs are gitignored). `lib/` generated footprints. `sheets/` generated schematic sheets. `routing/` routing logs and reports. `renders/` board images. `review/` generated engineer pack. `bom/` generated BOM CSVs. `fab/` fabrication output. |
| `enclosure/` | `params.scad` (all dimensions), `shell.scad` (tray, lid, comb, supports, artwork), `board.scad` and `logo.scad` (generated), `refinements.scad` (bezel, feet), `scene.scad`, `tools/` (converter, renderers, fit check), `stl/` (output). |
| `docs/` | Architecture, status, decisions, layout review, renders, BOM, fabrication, usage, testing tracker, history, briefs in `decisions/`, images in `img/`, diagram generator in `tools/`. |

## Generators and commands (all run from the repository root)

| Task | Command |
|---|---|
| Schematic and netlist | `BD_PROJECT=brain\|card python3 hardware/tools/gen_sch.py` (source of truth `hardware/tools/design.py`) |
| Placement | `python3 hardware/tools/gen_pcb.py`, `check_place.py` |
| Route a board | `sh hardware/tools/route_full.sh` (hours; run in the background; `BD_PROJECT` selects the board) |
| Branding on the silkscreen | `python3 hardware/tools/branding.py [brain\|card]` (revision constant `REV` lives here) |
| BOM | `python3 hardware/tools/gen_bom.py` |
| Engineer pack | `python3 hardware/tools/make_review_pack.py` |
| Board renders | `sh hardware/tools/render_board.sh` (and with `BD_PROJECT=card`) |
| Fabrication files | `sh hardware/tools/export_fab.sh` |
| Enclosure | `make -C enclosure` (STLs), `make -C enclosure renders` (all images), `python3 enclosure/tools/check_fit.py` |
| Diagrams | `software/.venv/bin/python docs/tools/diagrams.py` |
| Software | `cd software && .venv/bin/python -m pytest -q` and `ruff check .` |

Use the system `python3` for anything that imports `pcbnew` (KiCad 9.0.8) and `software/.venv` for tests, ruff and cairosvg.

## Conventions worth knowing

- **Frames.** KiCad's top view has x to the right, y down, and the rear edge at the top. The enclosure frame is right-handed and mirrors x
  (`enclosure/tools/kicad_to_scad.py`). The lid is modelled upside down with local y measured from the front; use `lby()` in `shell.scad`.
- **Board coordinates** in the docs are millimetres from the board's top-left corner; the KiCad file itself starts at (19.95, 19.95).
- **Copper stack** of the brain: F.Cu signal, In1 GND, In2 and In3 signal, In4 power islands (5V_SYS, 5V_HDD, +12V, +3V3), B.Cu signal and GND.
  The card: F.Cu, In1 GND, In2 power islands (5V_HDD, +12V), B.Cu.
- **Card in the enclosure frame:** the card slab is centred 5.4 mm behind the window centre, the receptacle housing runs 9.5 mm toward the next slot.
- **Footprints** are stock KiCad, generated from vendor drawings (`fpgen.py`), or copied from Raspberry Pi's CM5IO project. Sources are in `hardware/review/footprints.md`.
- **pcbnew scripting:** each edit in a fresh process; the Python proxies go stale after `Remove()` or a second `LoadBoard`.

## People and process

The owner makes every decision and answers one question at a time. Closed decisions are `C<n>`, open ones `D<n>`, remaining work `R<n>`,
blocked items `B<n>`; numbers are never reused. Licence: Polyform Noncommercial (C20). Public repository: github.com/dmz006/brain-drain.
