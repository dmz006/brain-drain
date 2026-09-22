# Decisions log

Open items block layout or software structure. Closed items record what was
chosen and why, so nobody re-litigates them later.

## Open

| # | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| D5 | OLED | 0.96"/1.3" 4-pin I2C vs 2.42" SSD1309 | 0.96"/1.3" for v1 | enclosure |
| D6 | Option B: bridges move into the cables | board = CM5 + hubs + 4× USB-A + switched 12 V/5 V outputs, about 90 × 70 mm; commercial USB 3 to SATA cables | parked by the owner on 2026-09-23 as a later study; A (C21) is being built | nothing now |
| D8 | Build order | software-sim first / schematic first / enclosure first | software-sim first (ARCHITECTURE §8) | everything |

## Closed

| # | Decision | Chosen | Why | Date |
|---|---|---|---|---|
| C1 | Drive pigtail | Off-the-shelf 22-pin SATA M-F extension; board has backplane-style 22-pin receptacles | no custom cable, drive end is native | 2026-09-21 |
| C2 | Staggered spin-up | Mandatory, per-bay P-FET switches on 12 V and 5 V from GPIO | halves peak input current; also gives unfreeze/reset | 2026-09-21 |
| C3 | Two 5 V bucks | separate 5V_SYS and 5V_HDD, same TPS56637 | keep spin-up ripple off the CM5 rail | 2026-09-21 |
| C4 | RTC on board | PCF85063AT + CR2032 | certificates need timestamps off-network | 2026-09-21 |
| C5 | Default wipe policy | HDD: 1-pass zeros + full verify (Clear). SSD: Sanitize crypto-scramble then block-erase (Purge). Multi-pass only as explicit legacy modes | NIST 800-88 Rev. 2 | 2026-09-21 |
| C6 | Enclosure tool | OpenSCAD with params generated from KiCad | ubiquitous, easy to diff | 2026-09-21 |
| C7 (was D9) | Compute module | **CM5** | $10 over CM4 at equal RAM/eMMC; 2× native USB 3.0 so four HDDs run at native speed; PCIe Gen3 x1 left free; on-module RTC | 2026-09-22 |
| C8 (was D1, D4) | USB 3 topology | CM5 USB 3.0 port → VL817 hub → 2× ASM1153E, twice. No PCIe xHCI | ~400 MB/s per pair of bays, no firmware loading, uses the originally requested VL817 | 2026-09-22 |
| C9 (was D6) | Module size | CM5002016 (2 GB, 16 GB eMMC) for production; CM5002000 Lite via microSD for dev | service needs < 1 GB; eMMC can't fall out mid-job; same carrier serves both | 2026-09-22 |
| C10 | User interaction | No Start button. A drive is wiped as soon as it is detected (after a 5 s grace countdown); unplugging aborts; DIP is the only control | single-purpose appliance, keep it simple | 2026-09-22 |
| C11 | USB 3.0 hub | **Microchip USB5744**, one per CM5 USB 3.0 port | same 4-port 5 Gbit/s spec as VL817; fully public datasheet; smallest and cheapest; JLCPCB-assembled; +1 LDO for 1.2 V core | 2026-09-23 |
| C12 (was D3) | USB→SATA bridge | **ASMedia ASM1153E** | dmz's call: Linux track record (UASP+TRIM, no quirks) over the public-datasheet rule; datasheet from a mirror copy, kept locally in hardware/ref/datasheets (not committed) | 2026-09-23 |
| C13 (was D2) | 12 V input | **4-pin DIN Kycon KPJX-4S-S only**; barrel footprint dropped | barrels are 5 A rated, design peak is 7.4 A; DIN is 7.5 A/pin and what 12 V/10 A bricks ship with. Brick must be chosen before layout to match DIN pin assignment | 2026-09-23 |
| C14 (was D7) | Panel LEDs | **3 mm through-hole**, 6 off | cheapest, tolerant of enclosure error, bay LEDs blink with real disk activity | 2026-09-23 |
| C15 (was D10) | M.2 NVMe bay | **Populated in v1**: M.2 M-key on PCIe Gen3 x1, switched 3V3, enclosure access door | dmz's call: NVMe wipes from day one; accepts door + PCIe rescan software as v1 work | 2026-09-23 |
| C16 | Schematic workflow | **Generated**: `hardware/tools/design.py` is the source of truth; `gen_sch.py` regenerates the KiCad sheets and `gen_connections.py` the connection list on every change; placement is tidied in the GUI only once the netlist settles | ERC on every edit, repeated bay sheets cannot drift, connection list always in sync | 2026-09-23 |
| C17 | SATA bay receptacle | **Molex 47018-4001**, right-angle SMT 22-pin host receptacle | industry standard, precise sales drawing SD-47018-001, easy small-quantity sourcing | 2026-09-23 |
| C18 | M.2 socket | **TE 2199230-4**, 4.2 mm M-key | most common small-run M.2 socket, stocked at distributors and JLCPCB | 2026-09-23 |
| C19 | Board outline | **Option A: 180 × 110 mm**, all cables on the rear edge (DIN, RJ45, USB-C/UART, 4× SATA), CM5 centred, M.2 along the front with its door on a side wall | one enclosure wall with cutouts, single cable exit, M.2 door away from cables, fits a 220 mm print bed | 2026-09-23 |
| C20 | Licence | **Polyform Noncommercial 1.0.0** for hardware, software and enclosure | matches the owner's datawatch project; source-available, noncommercial | 2026-09-23 |
| C21 | Portable "brain box" (supersedes C19) | **Option A**: bridges stay on the board, drives on 22-pin cables, no rack or chassis. Board **150 × 98 mm**: 4× SATA on the rear at 28.9 mm pitch, DIN / RJ45 / USB-C on the left wall, microSD + M.2 SSD slot on the front wall, CM5 landscape centre, hubs and bucks in the right column, M.2 vertical along the right edge, CR2032 and buzzer on the bottom. Enclosure about 157 × 105 × 39 mm | owner wants the unit, brick and cables in a backpack and drives loose on the bench; A keeps every chosen part (ASM1153E, per-bay power, allow-list, M.2) and only the outline and enclosure change. Option B (D6) parked for later. Brief: `decisions/2026-09-23-portable-brain.md` | 2026-09-23 |
