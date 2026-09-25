<p align="center"><img src="docs/img/logo.png" alt="brain-drain" width="720"></p>

# brain-drain

A standalone disk sanitizer: plug a drive in, it gets wiped to NIST SP 800-88 Rev. 2 and you get a certificate. No buttons, no
screen to poke at, no PC. A Raspberry Pi Compute Module 5 on a custom carrier board, plug-in bay cards (one per drive, up to eight, four
in version 1), an M.2 NVMe bay, a Python service and a 3D-printed enclosure that fits a backpack.

> **Status: design complete enough for layout review, nothing fabricated yet.** Both boards are routed with 0 DRC errors in KiCad, the
> software has 74 passing tests and the enclosure exports clean STLs. The boards have not been reviewed by a board designer and nothing has
> been simulated; the first bench test with a real drive is scheduled for 2026-09-26. See [docs/STATUS.md](docs/STATUS.md).
> **Handing this to an engineer? Start with [docs/LAYOUT-REVIEW.md](docs/LAYOUT-REVIEW.md).**

<p align="center"><img src="docs/img/renders/system-iso.png" alt="the complete system: the unit, four drives on 22-pin cables and the 12 V brick" width="900"></p>
<p align="center"><img src="docs/img/renders/unit-open-front.png" alt="lid open: the brain board with four bay cards standing in their slots" width="520"> <img src="docs/img/renders/electronics-iso.png" alt="the assembled electronics" width="640"></p>

## What it does

* Up to eight SATA bays as plug-in cards (four fitted), each a USB 3 bridge
  with its own switched power. Drives are not docked: each bay is a 0.5 m
  22-pin SATA cable (data + power) that rises through the lid and plugs straight
  onto a bare 3.5" or 2.5" drive lying on the bench. Plus an M.2 NVMe bay under
  the lid (bay 9). Each bay is independent.
* Set the policy on an 8-way DIP switch. Plug a drive in: it is identified,
  wiped, verified and reported. Unplug it: the job aborts. That is the whole UI.
* Methods follow NIST 800-88 Rev. 2: single-pass overwrite with full
  verification for magnetic drives, firmware Sanitize (crypto or block erase)
  for SSDs and NVMe, legacy 3-pass and 7-pass available for those who insist.
* A JSON certificate per drive per job: what was attempted, what worked, how it
  was verified, and which tier (Clear / Purge) is honestly claimed.
* A 128×64 OLED shows per-bay progress and ETA. When idle it shows a QR code:
  scan it with a phone to join the unit's Wi-Fi, open the address, and you get
  the status page, the certificates to download, the log, and the option to
  join the unit to your own network. A key on the screen authorises changes.
  DIP mode 110 resets Wi-Fi (or everything, with DIP 8) without a network.

<p align="center"><img src="docs/img/oled-wifi.png" alt="OLED idle: Wi-Fi QR code" width="420"> <img src="docs/img/oled-running.png" alt="OLED while running" width="420"></p>

## Use cases

* IT refresh: wiping a pile of decommissioned laptop and desktop drives
  unattended, four at a time, with paperwork for each.
* Reselling or donating hardware where a Purge-level record is wanted.
* Small MSPs and repair shops that need a repeatable wipe without dedicating a PC.

## The hardware

| ![brain](docs/img/renders/brain-iso-rear.png) | ![card](docs/img/renders/card-iso.png) |
|---|---|
| **Brain board**, 150 x 122 mm, six layers: CM5 wireless, two USB5744 hubs, eight PCIe-x1-style bay slots, M.2 socket, 12 V input and bucks, OLED, DIP switch | **Bay card**, 45 x 46 mm, four layers: ASM1153E USB 3 to SATA bridge, per-bay 12 V / 5 V power switch, SATA receptacle, PCIe x1 fingers |

More views, the case, the assembled unit, an exploded view, a cut-away and the complete system: [docs/RENDERS.md](docs/RENDERS.md).

## Repository layout

| Directory | Workstream | State |
|---|---|---|
| [`hardware/`](hardware/README.md) | KiCad 9 projects for the brain board and the bay card, generated from one netlist source; review pack, per-layer images, BOM | schematic clean; both boards routed, 0 open connections, 0 DRC errors, all differential pairs matched; **unreviewed, unsimulated, not fabricated** |
| [`software/`](software/README.md) | `braindrain` Python service, simulator, bench tool, Wi-Fi access point + phone page, Pi deployment | 74 tests, ready for the first bench |
| [`enclosure/`](enclosure/README.md) | OpenSCAD case, about 157 x 145 x 62 mm: tray, hinged lid with eight cable windows and a snap latch, OLED bezel; render gallery script | STLs export, renders done, not printed |
| [`docs/`](docs/README.md) | architecture, review guide, BOM, decisions, status, usage, diagrams, renders | |

## Quick start

```
# simulate the appliance on any Linux box
cd software && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
braindrain simulate --grace 2            # terminal 1
braindrain sim-plug 1 --size 1G --prefill # terminal 2: a drive appears in bay 1 and is wiped

# regenerate a board from its source and route it unattended (BD_PROJECT=brain or card; see docs/USAGE.md)
cd hardware && python3 tools/symgen.py && BD_PROJECT=card python3 tools/gen_sch.py && BD_PROJECT=card sh tools/route_full.sh

# export the enclosure and render every image
cd enclosure && make && make renders
```

More in [docs/USAGE.md](docs/USAGE.md).

## Documentation

* **For the layout engineer: [Layout and design review guide](docs/LAYOUT-REVIEW.md)** · generated review data in [`hardware/review/`](hardware/review/)
* [Architecture](docs/ARCHITECTURE.md) · [System block diagram](docs/img/system-block.png) · [Renders and drawings](docs/RENDERS.md)
* [Bill of materials](docs/BOM.md) · [Fabrication and assembly vendors, cost estimate](docs/FABRICATION.md) · [Decisions](docs/DECISIONS.md)
* [Status and remaining work](docs/STATUS.md) · [Testing tracker](docs/testing-tracker.md)
* [Usage and regeneration](docs/USAGE.md) · [Bench plan for 2026-09-26](docs/saturday-bench-plan.md)
* [AGENT.md](AGENT.md) rules for agents and contributors · [CONTRIBUTING](CONTRIBUTING.md) · [CHANGELOG](CHANGELOG.md)

## Safety

This device destroys data by design. The software's safety fence only ever
targets whole disks behind an allow-listed USB bridge on a configured bay port,
or the M.2 slot, and never anything mounted or holding the root filesystem.
Treat every drive that touches a bay as gone.

## Licence

[Polyform Noncommercial 1.0.0](LICENSE): you may use, modify and share this
project for noncommercial purposes. Commercial use needs permission from the
author. Applies to the hardware sources, the software and the enclosure alike.
