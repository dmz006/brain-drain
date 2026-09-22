# Testing tracker

Two levels, per AGENT.md: **Tested** = automated checks pass; **Validated** =
confirmed on real hardware or a real drive, with details. Simulation never sets
Validated.

## Software (`software/braindrain`)

| Interface / module | Tested | Validated | Test conditions | Notes |
|---|---|---|---|---|
| Policy / DIP decoding (`policy.py`) | yes, `tests/test_policy.py` | no | pytest | all 8 modes and flags |
| Safety fence (`devices.classify`) | yes, `tests/test_fence.py` | partial | `braindrain list` on the dev workstation refused the root NVMe and loop devices (2026-09-23) | needs a dock on Saturday |
| Host overwrite + verify (`methods/overwrite.py`, `verify.py`) | yes | no | sparse files, O_DIRECT with buffered fallback | random-pattern phase bug fixed 2026-09-22 |
| Canary verify for firmware wipes | yes | no | simulated firmware | |
| ATA firmware wrappers (`methods/ata.py`) | parser only, `tests/test_parsers.py` | **no** | fixtures written from hdparm 9.65 docs | status-output format must be confirmed on the bench |
| NVMe wrappers (`methods/nvme.py`) | parser only | no | nvme-cli JSON | no native NVMe until the board exists |
| Engine state machine, abort on unplug | yes, `tests/test_engine_sim.py` | no | simulated bays | |
| Bay 5 M.2 slot controller | yes, `tests/test_m2_bay.py` | no | simulated door/PEDET | GPIO paths untested |
| Certificates + crash recovery | yes | no | | schema v1 |
| Bench tool (`bench.py`) | yes, `tests/test_bench.py` | **planned 2026-09-26** | fake hdparm/smartctl | |
| Config file, headless HAL, setup-bay | yes, `tests/test_config.py` | no | | |
| Real GPIO HAL (`hal/gpio.py`) | no | no | needs the carrier board | libgpiod v2 API from docs |
| OLED driver (`hal/oled.py`) | no | no | needs the panel | |
| systemd unit + install script | no | **planned 2026-09-26** | Raspberry Pi OS Lite on a Pi 5 | |

## Hardware (`hardware/`)

| Item | Tested | Validated | Conditions | Notes |
|---|---|---|---|---|
| Netlist (`design.py`) pin coverage | yes, `design.py` check | no | every pin assigned or NC | |
| Schematic ERC | yes, 0 errors | no | kicad-cli 9.0.8 | 9 lib-cache warnings on 2N7002, 4 placeholder footprints |
| Board DRC (v1 outline, unrouted) | yes: 0 errors, silkscreen/isolated-copper warnings | no | kicad-cli 9.0.8, `check_place.py` 0 problems | routing to be rerun on the new outline (R16) |
| Symbols from datasheet tables | yes | no | CM5 datasheet, USB5744 DS00001855M, ASM1153E Rev 0.4 | |
| Footprints: KPJX-4S-S, RPA0010A | generated | no | Kycon drawing, TI land pattern | first board proves them |
| Footprints: CM5 module, M.2 socket | copied from CM5IO rev 2 | no | Raspberry Pi design files | M.2 pegs vs TE drawing pending |
| Footprint: SATA 22-pin | **placeholder** | no | | needs Molex SD-47018-001 |
| USB-SATA bridge Sanitize passthrough | — | **planned 2026-09-26** | ASM1153E dock | closes C12 with evidence |

## Enclosure (`enclosure/`)

| Item | Tested | Validated | Conditions | Notes |
|---|---|---|---|---|
| Tray / lid / door STL export (v1 box) | yes, OpenSCAD 2021.01 | no | no warnings | no print yet |
| Hinged M.2 slot door, bezel, scene | yes | no | renders in `enclosure/renders/` | |
| Cutout fit against real connectors | no | no | | first print |
