# Decisions log

Open items block layout or software structure. Closed items record what was
chosen and why, so nobody re-litigates them later.

## Open

| # | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| D2 | 12 V input connector | high-current barrel 5.5×2.5 vs 4-pin DIN (both footprints on board, populate one) | DIN, because 12 V/10 A bricks ship with it; barrel if a ≥8 A jack is confirmed | BOM, enclosure cutout |
| D3 | USB→SATA bridge | ASM1153E vs ASM235CM | ASM1153E unless stock is bad | schematic |
| D5 | OLED | 0.96"/1.3" 4-pin I2C vs 2.42" SSD1309 | 0.96"/1.3" for v1 | enclosure |
| D10 | Optional M.2 NVMe bay on the free PCIe Gen3 x1 | populate in v1 / footprint only / omit | footprint only (DNP) in v1; enables native `nvme sanitize` later | layout, enclosure door |
| D7 | Bay LEDs | 3 mm TH through panel vs 0603 + light pipes | 3 mm TH | layout, enclosure |
| D8 | Build order | software-sim first / schematic first / enclosure first | software-sim first (ARCHITECTURE §8) | everything |

## Closed

| # | Decision | Chosen | Why | Date |
|---|---|---|---|---|
| C1 | Drive pigtail | Off-the-shelf 22-pin SATA M-F extension; board has backplane-style 22-pin receptacles | no custom cable, drive end is native | 2026-09-21 |
| C2 | Staggered spin-up | Mandatory, per-bay P-FET switches on 12 V and 5 V from GPIO | halves peak input current; also gives unfreeze/reset | 2026-09-21 |
| C3 | Two 5 V bucks | separate 5V_SYS and 5V_HDD, same TPS56637 | keep spin-up ripple off the CM4 rail | 2026-09-21 |
| C4 | RTC on board | PCF85063AT + CR2032 | certificates need timestamps off-network | 2026-09-21 |
| C5 | Default wipe policy | HDD: 1-pass zeros + full verify (Clear). SSD: Sanitize crypto-scramble then block-erase (Purge). Multi-pass only as explicit legacy modes | NIST 800-88 Rev. 2 | 2026-09-21 |
| C6 | Enclosure tool | OpenSCAD with params generated from KiCad | ubiquitous, easy to diff | 2026-09-21 |
| C7 (was D9) | Compute module | **CM5** | $10 over CM4 at equal RAM/eMMC; 2× native USB 3.0 so four HDDs run at native speed; PCIe Gen3 x1 left free; on-module RTC | 2026-09-22 |
| C8 (was D1, D4) | USB 3 topology | CM5 USB 3.0 port → VL817 hub → 2× ASM1153E, twice. No PCIe xHCI | ~400 MB/s per pair of bays, no firmware loading, uses the originally requested VL817 | 2026-09-22 |
| C9 (was D6) | Module size | CM5002016 (2 GB, 16 GB eMMC) for production; CM5002000 Lite via microSD for dev | service needs < 1 GB; eMMC can't fall out mid-job; same carrier serves both | 2026-09-22 |
