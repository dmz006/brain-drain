# Renders and drawings

Everything here is generated. Board and assembly views come from a proxy 3D model (`hardware/tools/board_model.py`: the outline extruded
to 1.6 mm plus a box for every part body, sized from the courtyards and a height table), so they show layout and fit, not exact
component shapes. The case is the real OpenSCAD geometry. Regenerate all of it with:

```
cd hardware && for p in brain card; do BD_PROJECT=$p sh tools/render_board.sh; done   # KiCad 3D views, per-layer images, schematic PNGs
cd ../enclosure && make && make renders                                              # STLs, then docs/img/renders/*.png
software/.venv/bin/python docs/tools/diagrams.py                                     # block diagram, lid plan, wall panel, bay flow
```

## Boards, one at a time

| Brain board, rear (slots) | Brain board, from above |
|---|---|
| ![](img/renders/brain-iso-rear.png) | ![](img/renders/brain-top.png) |

| Brain board, front left | Brain board, bottom side |
|---|---|
| ![](img/renders/brain-iso-front.png) | ![](img/renders/brain-bottom.png) |

| Bay card, component side | Bay card, 3D | Bay card, back |
|---|---|---|
| ![](img/renders/card-front.png) | ![](img/renders/card-iso.png) | ![](img/renders/card-back.png) |

KiCad's own 3D views (bare copper, no part bodies) and the layer images:

| Brain, KiCad 3D | Brain, F.Cu | Brain, In3.Cu |
|---|---|---|
| ![](../hardware/renders/board-3d-iso.png) | ![](../hardware/renders/layers/F.Cu.png) | ![](../hardware/renders/layers/In3.Cu.png) |

All layers: `hardware/renders/layers/` (F.Cu, In1 to In4, B.Cu, assembly-top, assembly-bottom, mask) and `hardware/bay-card/renders/layers/`;
schematic sheets: `hardware/renders/schematic/`; PDFs: `hardware/review/*-schematic.pdf`.

## The assembled electronics

| Brain with four bay cards, from the rear left | From the front left |
|---|---|
| ![](img/renders/electronics-iso.png) | ![](img/renders/electronics-iso-front.png) |

| Plan view (cards overhang the rear edge by 15 mm) | Side view (card top 48.9 mm above the board) |
|---|---|
| ![](img/renders/electronics-top.png) | ![](img/renders/electronics-side.png) |

![all eight slots populated](img/renders/electronics-full8.png)

## The case

| Tray | Lid, outside |
|---|---|
| ![](img/renders/case-tray-iso.png) | ![](img/renders/case-lid-outside.png) |

| Lid, inside (printed face down) | Tray from above |
|---|---|
| ![](img/renders/case-lid-inside.png) | ![](img/renders/case-tray-top.png) |

Lid artwork (engraved logo and name) and the comb ribs seen through the windows:

![](img/renders/case-lid-artwork.png)

| Closed, from the rear left | Closed, from the front right |
|---|---|
| ![](img/renders/case-closed-iso.png) | ![](img/renders/case-closed-front.png) |

Plan drawing with dimensions, windows and holes: ![lid plan](img/lid-plan.png)

OLED bezel: ![](img/renders/case-bezel.png)

## The unit with the electronics inside

| Lid open, from the front | Lid removed |
|---|---|
| ![](img/renders/unit-open-front.png) | ![](img/renders/unit-no-lid.png) |

![exploded](img/renders/unit-exploded.png)

![cut-away](img/renders/unit-cutaway.png)

## The complete system

The unit, four drives on 0.5 m 22-pin cables rising through the lid windows, and the 12 V brick on the DIN cable.

![](img/renders/system-iso.png)

| From above | From the front right |
|---|---|
| ![](img/renders/system-top.png) | ![](img/renders/system-front.png) |

![lid open](img/renders/system-open.png)

## Diagrams

| | |
|---|---|
| ![system](img/system-block.png) | ![bay flow](img/bay-flow.png) |
| ![left panel](img/left-panel.png) | ![oled](img/oled-wifi.png) |
