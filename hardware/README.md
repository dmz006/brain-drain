# hardware — CM5 carrier board

KiCad 9 project (not yet created). See `../docs/ARCHITECTURE.md` §3 for the
design and `../docs/BOM.md` for parts.

## Planned layout

```
hardware/
  brain-drain.kicad_pro
  brain-drain.kicad_sch          # root: sheet instances
  sheets/cm5.kicad_sch           # DF40 connectors, microSD, GbE, USB-C, UART, nRPIBOOT, RTC cell, fan
  sheets/usb3-hub.kicad_sch      # VL817 + crystal + LDO (2 instances, one per CM5 USB 3 port)
  sheets/bridge.kicad_sch        # ASM1153E + crystal + LDO + SATA coupling (4 instances)
  sheets/bay-switch.kicad_sch    # P-FET 12 V / 5 V switch + PTCs (4 instances)
  sheets/power-input.kicad_sch   # jack(s), fuse, TVS, reverse polarity, bulk
  sheets/power-bucks.kicad_sch   # 2× TPS56637, AP63203
  sheets/ui.kicad_sch            # DIP, OLED header, LEDs, buzzer, RTC fallback (DNP)
  sheets/m2-nvme.kicad_sch       # optional M.2 M-key on PCIe Gen3 x1 (DNP, D10)
  brain-drain.kicad_pcb
  lib/                           # project symbols/footprints (VL817, ASM1153E, DF40, SATA 22)
  bom/brain-drain-bom.csv        # canonical BOM (edit here, BOM.md is derived)
  fab/                           # gerbers, drill, pos, assembly BOM exports
```

## Board rules

* 4-layer, 1.6 mm, JLC04161H-7628 stackup, ENIG.
* Diff pairs: USB 3 SS and SATA at 90 Ω, PCIe Gen3 at 85 Ω, USB 2.0 at 90 Ω.
  Intra-pair length match ±0.15 mm. Keep SS/SATA/PCIe pairs on outer layers
  over solid GND, no layer changes without a stitching via.
* CM5 boot-order straps: eMMC/SD only; USB and NVMe boot disabled.
* All bay power switches default **off** (10 k pull-down on each BAY_EN).
* Both input-jack footprints (barrel J20, DIN J21) on the board; populate one.

## Before layout

Close decisions D2, D3, D7 and D10 in `../docs/DECISIONS.md`.

## Bench validation that does not need this board

Any Linux box + an ASM1153E-based USB dock answers the risky questions:
does `hdparm --sanitize-*` pass through, does the bridge survive a long
SECURITY ERASE, does `--sanitize-status` report progress. A Pi 5 with two docks is the exact
software test bed for this topology. Do this first.
