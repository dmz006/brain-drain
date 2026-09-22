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

### Fixed
- Board generator: pad angles now follow footprint rotation (KiCad stores them absolute), which
  removed the overlapping pads on every rotated fine-pitch part; region packer with capacity checks
  and a spill area; DIN jack pads shorter than their pitch; M.2 footprint mask margins removed;
  USB-C moved to the left wall; DRC now reports 0 errors before routing.

### Dependencies
- Python: pyudev; dev: pytest, ruff, pillow, numpy, cairosvg; hw: gpiod, luma.oled, smbus2.
- Tools (not vendored): KiCad 9.0.8, OpenSCAD 2021.01, freerouting 2.1.0 jar (downloaded into `hardware/tools/freerouting/`, gitignored), Java 21.
