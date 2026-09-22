# hardware — CM4 carrier board

KiCad 9 project (not yet created). See `../docs/ARCHITECTURE.md` §3 for the
design and `../docs/BOM.md` for parts.

## Planned layout

```
hardware/
  brain-drain.kicad_pro
  brain-drain.kicad_sch          # root: sheet instances
  sheets/cm4.kicad_sch           # DF40 connectors, eMMC/SD, GbE, USB-C, UART, nRPIBOOT
  sheets/usb3-host.kicad_sch     # VL805, crystal, SPI flash (DNP), PCIe coupling
  sheets/bridge.kicad_sch        # ASM1153E + crystal + LDO + SATA coupling (4 instances)
  sheets/bay-switch.kicad_sch    # P-FET 12 V / 5 V switch + PTCs (4 instances)
  sheets/power-input.kicad_sch   # jack(s), fuse, TVS, reverse polarity, bulk
  sheets/power-bucks.kicad_sch   # 2× TPS56637, AP63203
  sheets/ui.kicad_sch            # DIP, button, OLED header, LEDs, buzzer, RTC, fan
  brain-drain.kicad_pcb
  lib/                           # project symbols/footprints (VL805, ASM1153E, DF40, SATA 22)
  bom/brain-drain-bom.csv        # canonical BOM (edit here, BOM.md is derived)
  fab/                           # gerbers, drill, pos, assembly BOM exports
```

## Board rules

* 4-layer, 1.6 mm, JLC04161H-7628 stackup, ENIG.
* Diff pairs: USB 3 SS, PCIe, SATA at 90 Ω; USB 2.0 at 90 Ω. Intra-pair
  length match ±0.15 mm. Keep SS/PCIe/SATA pairs on outer layers over solid
  GND, no layer changes without a stitching via.
* All bay power switches default **off** (10 k pull-down on each BAY_EN).
* Both input-jack footprints (barrel J20, DIN J21) on the board; populate one.

## Before layout

Close decisions D1–D4 and D7 in `../docs/DECISIONS.md`.

## Bench validation that does not need this board

Any Linux box + an ASM1153E-based USB dock answers the risky questions:
does `hdparm --sanitize-*` pass through, does the bridge survive a long
SECURITY ERASE, does `--sanitize-status` report progress. Do this first.
