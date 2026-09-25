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
| Bay 9 M.2 slot controller (bay 5 before C24) | yes, `tests/test_m2_bay.py` | no | simulated lid switch/PEDET | GPIO paths untested |
| Eight bays, two-column OLED layout, bay-card ports | yes, `tests/test_display.py`, `tests/test_config.py` | no | | slots 5–8 unpopulated in v1 |
| Certificates + crash recovery | yes | no | | schema v1 |
| Bench tool (`bench.py`) | yes, `tests/test_bench.py` | **planned 2026-09-26** | fake hdparm/smartctl | |
| Config file, headless HAL, setup-bay | yes, `tests/test_config.py` | no | | |
| Wi-Fi manager (`wifi.py`): AP, join, fallback, resets, key | yes, `tests/test_wifi.py` | no | simulated backend | nmcli backend written from the NetworkManager docs, untested |
| Phone page (`webui.py`): status, certificates, zip, join, reset, key check | yes, `tests/test_webui.py` | no | real HTTP on a local port | one intermittent failure seen once in a timing-based join test; passed 5/5 afterwards |
| Service mode (DIP 110): no wipe, Wi-Fi reset at boot, factory with DIP 8 | yes, `tests/test_service_mode.py` | no | | |
| Wi-Fi QR frame on the OLED | yes (matrix size, layout) | no | `docs/img/oled-wifi.png` from the real renderer | luma drawing untested |
| Real GPIO HAL (`hal/gpio.py`) | no | no | needs the carrier board | libgpiod v2 API from docs |
| OLED driver (`hal/oled.py`) | no | no | needs the panel | |
| systemd unit + install script | no | **planned 2026-09-26** | Raspberry Pi OS Lite on a Pi 5 | |

## Hardware (`hardware/`)

| Item | Tested | Validated | Conditions | Notes |
|---|---|---|---|---|
| Netlist (`design.py`) pin coverage | yes, `design.py` check | no | every pin assigned or NC | |
| Schematic ERC | yes: brain 0 findings, card 2 harmless library-copy warnings | no | kicad-cli 9.0.8 | `hardware/review/erc-summary.md` |
| Board DRC, brain (six layers) | yes: 0 errors, 0 unconnected, silkscreen and dangling-stub warnings | no | kicad-cli 9.0.8, `check_place.py` 0 problems | `hardware/review/drc-summary.md`; no independent review |
| Board DRC, bay card | yes: 0 errors, 0 unconnected | no | same | |
| Differential-pair matching | yes: 44 + 8 pairs under 0.15 mm end to end | no | `route.py pairs` | no impedance calculation, no simulation; segment-level mismatch up to 6 mm |
| Symbols from datasheet tables | yes | no | CM5 datasheet, USB5744 DS00001855M, ASM1153E Rev 0.4 | |
| FET pin tables (AON7403, AO4407A) | yes, read against the datasheets | no | AOS datasheets | S 1-3, G 4, D 5-8 (+ EP) |
| Footprints: PCIe x1 socket, SATA receptacle, KPJX-4S-S, RPA0010A | generated from vendor drawings | no | Amphenol 10018784, Molex SD-47018-001, Kycon, TI | Molex face position and socket housing ends assumed |
| Footprints: CM5 module, M.2 socket | copied from CM5IO rev 2 | no | Raspberry Pi design files | M.2 pegs vs TE drawing pending (R2) |
| Generated BOM | yes, every part mapped | no | `gen_bom.py` | `verify` lines need a stock and rating check |
| USB-SATA bridge Sanitize passthrough | | **planned 2026-09-26** | ASM1153E dock | closes C12 with evidence |
| Signal integrity, power integrity, thermal | no | no | | nothing simulated |

## Enclosure (`enclosure/`)

| Item | Tested | Validated | Conditions | Notes |
|---|---|---|---|---|
| Tray / hinged lid / bezel STL export (v2 box) | yes, OpenSCAD 2021.01 | no | no warnings | no print yet |
| Hinge, latch, lid-open scene | yes | no | renders in `docs/img/renders/` | hinge pin fit and latch force need a print |
| Cutout fit against real connectors | no | no | | first print |
