# Board outline and connector placement — proposal (2026-09-23)

For dmz to decide. Numbers are from the parts chosen so far; the SATA receptacle
and M.2 socket lengths are typical values until their drawings are in hand.

## What has to fit

| Item | Size on the board | Where it wants to be |
|---|---|---|
| CM5 + cooler | 55 × 40 mm, cooler 45 × 40 mm on top, ~15 mm tall | centre, short traces to both hubs and to the M.2 |
| 4× SATA 22-pin receptacle | ~27.5 × 8 mm each, 30 mm pitch → 120 mm of edge | one board edge, pigtails leave the enclosure there |
| 4× ASM1153E + passives | ~15 × 15 mm each | directly behind its receptacle |
| 2× USB5744 + passives | ~15 × 15 mm each | between CM5 and the bridges |
| 4× bay switch (2 P-FETs, 2 PTCs) | ~12 × 12 mm each | between the 12 V rail and its receptacle |
| DIN jack | 16 × 17.4 mm, overhangs the edge by ~4 mm | an edge, near the bucks and bulk caps |
| 2× TPS56637 buck + inductors, AP63203 ×2, 680 µF ×2 | ~30 × 25 mm block | next to the DIN jack |
| RJ45 magjack | 16 × 21 mm | an edge |
| USB-C, UART, nRPIBOOT jumper | 9 mm edge + two headers | an edge, together |
| M.2 2280 + socket | 22 × 80 mm keep-out, socket 22 × 9 mm, 4.2 mm tall | along one edge so the door is in the enclosure wall |
| microSD | 15 × 15 mm, card protrudes 2 mm | an edge, reachable |
| OLED header, DIP, 7 LEDs, buzzer, fan header | small | top face, near the lid |
| Mounting | M2.5 holes, 4 corners + centre | |

## Option A — 180 × 110 mm, everything on the rear edge (recommended)

```
                 rear edge (all cables leave here)
 +-------------------------------------------------------------------------+
 | DIN | RJ45 | USB-C UART |  SATA 1  |  SATA 2  |  SATA 3  |  SATA 4     |
 | bucks, bulk |            | bridge 1 | bridge 2 | bridge 3 | bridge 4    |
 | caps        |  hub A     | switch 1 | switch 2 | switch 3 | switch 4    |
 |             |            +----------+----------+----------+-------------+
 | microSD     |        CM5 + cooler          |  hub B                    |
 |             |                              |                           |
 | M.2 socket ===== M.2 2280 (door on left wall) =====     DIP  OLED LEDs |
 +-------------------------------------------------------------------------+
                 front / lid side
```

* Width: 4 × 30 mm SATA + DIN 16 + RJ45 16 + USB-C/UART 14 + margins ≈ 180 mm.
* Depth: connector row 25 mm + bridge/switch row 30 mm + CM5 row 45 mm + M.2/UI
  row 10 mm ≈ 110 mm.
* Why: one cable face keeps the enclosure simple (one wall with cutouts, the
  rest solid); the drive pigtails and the power brick both come out the back;
  the M.2 door lands on a side wall away from the cables.
* Cost: a long board (180 mm) and the M.2 runs the full front, so the OLED and
  DIP share the front strip with it.

## Option B — 200 × 95 mm, wide and shallow

Same as A but the M.2 lies along the rear behind the SATA row and the front
strip is UI only. Shorter depth suits a slimmer enclosure; the M.2 door ends up
on the rear next to the cables, which is awkward.

## Option C — 150 × 130 mm, power and network on the left side

SATA ×4 alone on the rear (120 mm + margins); DIN, RJ45, USB-C on the left
side; M.2 along the right side. Squarer board, two enclosure walls with
cutouts, shorter high-speed runs from the CM5 to everything. Better for
thermal spread; worse for the enclosure and for the cable exit on two faces.

## Common to all

* 4-layer, 1.6 mm, JLC04161H-7628. CM5 on the top side only.
* Keep the bucks ≥ 20 mm from the USB 3 and SATA pairs.
* SATA receptacles at 30 mm pitch leaves 2.5 mm between the 27.5 mm bodies for
  pigtail latches.
* Board size sets the 3D print: A is ~190 × 120 × 45 mm outside, which fits a
  220 mm printer bed in one piece.

## Recommendation

**Option A.** One cable face, drives in a row, M.2 door on the quiet side.
