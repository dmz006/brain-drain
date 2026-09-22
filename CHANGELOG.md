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

### Changed
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
