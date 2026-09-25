# hardware: the brain board and the bay card

Two KiCad 9 projects, both **generated** from `tools/design.py` (see [../docs/LAYOUT-REVIEW.md](../docs/LAYOUT-REVIEW.md) for how, and for what a
layout engineer must check). Design intent: [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) section 3. Parts: [../docs/BOM.md](../docs/BOM.md).
Regenerate and route commands: [../docs/USAGE.md](../docs/USAGE.md).

| | Brain board | Bay card |
|---|---|---|
| Project | `brain-drain.kicad_pro` | `bay-card/bay-card.kicad_pro` |
| Size, layers | 150 x 122 mm, 6 layers (F sig, In1 GND, In2 sig, In3 sig, In4 power, B sig), 1.6 mm, ENIG | 45 x 46 mm, 4 layers (F sig, In1 GND, In2 power, B sig), 1.6 mm, ENIG, finger tab |
| Contents | CM5 wireless, two USB5744 hubs, eight PCIe x1 bay slots, M.2 socket, 12 V input and bucks, OLED and DIP headers, LEDs, microSD, USB-C | ASM1153E bridge, two P-FET power switches with PTC fuses, SATA 22-pin receptacle, PCIe x1 fingers |
| Schematic sheets | `power-input`, `power-bucks`, `cm5`, `usb3-hub-A`, `usb3-hub-B`, `bay-slots`, `m2-nvme` | `bridge`, `bay-switch`, `edge` |
| Status | routed: 0 open connections, 0 DRC errors, 44 pairs matched | routed: 0 open connections, 0 DRC errors, 8 pairs matched |

![brain](../docs/img/renders/brain-iso-rear.png)
![card](../docs/img/renders/card-iso.png)

More views and the assembled unit: [../docs/RENDERS.md](../docs/RENDERS.md). KiCad's own 3D views are in `renders/`, one image per layer in
`renders/layers/` (F.Cu, In1 to In4, B.Cu, assembly-top, assembly-bottom, mask), schematic sheets in `renders/schematic/`.

## Layout of this directory

```
hardware/
  brain-drain.kicad_pro / .kicad_sch / .kicad_pcb   the brain (generated; the PCB also carries the routing)
  sheets/*.kicad_sch                                7 brain sheets (generated)
  bay-card/                                         the bay card project, same layout: .kicad_pro/.sch/.pcb, sheets/, routing/, renders/
  CONNECTIONS.md, bay-card/CONNECTIONS.md           net-by-net connection lists (generated)
  lib/brain-drain.kicad_sym, lib/brain-drain.pretty custom symbols and footprints (see lib/brain-drain.pretty/README.md for origins)
  review/                                           generated review pack: design rules, stack-up, planes, keep-outs, routing statistics,
                                                    DRC / ERC summaries, footprint provenance, netlists, placement CSV, schematic PDFs
  routing/, bay-card/routing/                       Specctra DSN/SES for freerouting, drc.json, open.md, pairs.md, chain.log
  renders/, bay-card/renders/                       KiCad 3D views, per-layer PNGs, schematic PNGs and PDFs
  bom/                                              brain-drain-bom.csv, bay-card-bom.csv (generated)
  ref/                                              pin tables (CSV), DOWNLOADS.md; ref/datasheets/ is gitignored
  tools/                                            the generators and the routing pipeline, listed in ../docs/LAYOUT-REVIEW.md section 6
  fab/                                              fab/<date>/ order packs (gitignored)
```

## Board rules

* Design rules follow the Raspberry Pi CM5IO reference: 0.13 mm tracks, 0.125 mm clearance, 0.45/0.2 mm vias, 0.3 mm copper to the board edge,
  0.2 mm hole clearance; power nets 0.3 mm tracks with 0.6/0.3 mm vias; 0.3/0.15 mm vias for the 0.4 mm-pitch QFN supply pins only (D8, confirm
  with the fab). They are written into each project file by `route.py prepare`; the table is in `review/design-rules.md`.
* Differential pairs: 90 ohm (USB 3, SATA, USB 2), 85 ohm (PCIe). The class `DiffPair90` is 0.147 mm / 0.253 mm gap, **carried over from a four-layer
  design and not yet recalculated for the six-layer stack-up**. Pairs are length-matched end to end (across the series capacitors) to 0.15 mm.
* CM5 antenna strip: no copper on any layer and no parts (rule area `keepout_CM5_antenna`); keep-outs around the CM5's four standoff holes.
* CM5 boot-order straps: eMMC/SD only. All bay power switches default **off** (10 k pull-down on `BAY_EN`, on the card).
* Input: 4-pin DIN (Kycon KPJX-4S-S); the pin assignment must match the chosen brick.

## Before fabrication

See [../docs/LAYOUT-REVIEW.md](../docs/LAYOUT-REVIEW.md) (priority items and the sign-off checklist) and [../docs/STATUS.md](../docs/STATUS.md) R2, R3, R10, R25 to R30:
the stack-up and pair geometry, the M.2 footprint against the TE drawing, the Molex face position, the DIN pinout from the chosen brick, test points, fiducials
and ESD, the card panel.

## Bench validation that does not need these boards

Any Linux box plus an ASM1153E-based USB dock answers the risky questions: does `hdparm --sanitize-*` pass through, does the bridge survive a long SECURITY ERASE,
does `--sanitize-status` report progress. A Pi 5 with two docks is the exact software test bed for this topology. Do this first
([../docs/saturday-bench-plan.md](../docs/saturday-bench-plan.md)).
