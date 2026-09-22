# Decision brief: portable "brain box" (C21) and option B (D6)

Date 2026-09-23. Owner: dmz. Supersedes the outline brief of the same day (C19).

## What changed

The owner wants the device itself in a small printed case, with cables running
to bare drives: "I don't need to have a chassis or anything to carry the drives
in. I just want to be able to have the cables, power, and the brain drain in my
backpack. I can pull them out, connect drives, and wipe them."

The v0 board was 180 × 110 mm because the four 22-pin receptacles sat at
3.5-inch drive pitch so drives could dock straight into a rack. With cables,
the receptacles only need their own width.

## Options briefed

| | Board | What moves | Cost |
|---|---|---|---|
| **A. Bridges stay on the board, cabled bays (chosen)** | 150 × 98 mm | outline, walls, enclosure only | none of the chosen parts change |
| B. Bridges move into the cables | about 90 × 70 mm | board becomes CM5 + hubs + 4× USB-A + switched 12 V / 5 V outputs; four commercial USB 3 to SATA cables (ASM1153E based ones exist) | per-bay power sequencing needs a second cable per drive; the bridge allow-list depends on the exact cable model |
| C. Keep the board, redo only the enclosure | 180 × 110 mm | nothing on the board | stays 190 × 120 × 25 mm |

The owner chose A and asked that B be kept as an optional plan to investigate
later (D6).

## Bay connector kept as decided (C17)

The brief offered a 7-pin SATA data jack plus a Micro-Fit power jack per bay.
Building it showed the already-decided Molex 22-pin receptacle (C17) is the
better cabled connector: 28 mm wide against 31 mm for the pair, one
off-the-shelf 22-pin extension per drive instead of a data cable plus a custom
crimped power lead, and the drive end is native. So the connector did not
change; only the pitch tightened to 28.9 mm.

## The v1 layout (150 × 98 mm)

```
        rear edge: SATA 1   SATA 2   SATA 3   SATA 4        (drive cables)
        bridges U10..U13 with passives; bay LEDs; bay power switches
 left   ┌──────────────────────────────┬──────────┬──────┬──────┐
 wall:  │ CM5 (landscape, 55 × 40)     │ hub A    │ buck │ M.2  │
 DIN    │                              │ hub B    │ col. │ 2280 │
 RJ45   ├──────────────────────────────┴──────────┴──────┤ runs │
 USB-C  │ front band: LEDs, headers, microSD, DIP, OLED   │ fwd  │
        │ header, fan header, bulk caps, M.2 LED + switch │ slot │
        └─────────────────────────────────────────────────┴──────┘
        front wall: microSD slot            M.2 SSD slot (door)
```

* CR2032 holder and buzzer are on the bottom side under the CM5 (inside the
  6 mm standoff height); the buzzer gets sound holes in the tray floor.
* The M.2 power switch and its 0402/0603 parts sit under the SSD (max 1.5 mm
  tall); the 1.8 mm inductor L51 is placed beside the column instead.
* The OLED module is lid-mounted on a 4-wire lead, so its window sits over the
  M.2 column where the lid is free; the DIP switch has its own lid slot.
* Three board mounting holes plus the CM5's four standoffs and the M.2 standoff;
  the rear-right corner is taken by bay 4 and the M.2 column.

## Size levers still available (owner's call, not taken)

| Lever | Board | Case | Cost |
|---|---|---|---|
| Passive heatsink instead of the official cooler | same | about 28 mm tall instead of 39 | thermal margin on long overwrites |
| M.2 socket on the bottom side under the CM5 | about 124 × 88 mm | smaller footprint | SSD inserted before closing the case, no slot; PCIe pairs change layer |
| Drop the M.2 bay (C15 reversal) | about 124 × 88 mm | smaller | no NVMe wipes |
| Option B (D6) | about 90 × 70 mm | deck-of-cards class | see above |

## Option B plan (D6), for later

1. Pick a commercial USB 3 to SATA cable with a known bridge (ASM1153E or
   ASM235CM) and a 12 V input for 3.5" drives; verify UASP, SAT passthrough and
   Sanitize on the bench with the same tests as the Saturday plan.
2. Board: CM5, two USB5744 hubs, four USB-A 3.0 receptacles, a 4-way switched
   12 V / 5 V output block (the existing bay-switch sheets, new connector),
   DIN input, bucks, DIP, OLED header, LEDs. Delete the four bridge sheets.
3. Software: the allow-list moves from "our bridge on our port path" to "that
   cable's VID:PID on our port path"; power control of a bay becomes the power
   cable, so the unplug-aborts behaviour is unchanged.
4. Enclosure: same box style, about 100 × 80 × 35 mm.
