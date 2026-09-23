# enclosure — parametric OpenSCAD "brain box"

The unit is a printed box (about 157 × 119 × 32 mm outside) that goes in a
backpack with its 12 V brick and four 22-pin cables; drives lie loose on the
bench while they are wiped (decisions C21–C23). The lid is hinged along the rear
edge and snaps shut at the front: open it to fit an M.2 SSD. Printed parts are
sized from the real board:

![assembled](renders/assembled-iso.png)
![lid open](renders/lid-open.png)

| Face | What is on it |
|---|---|
| rear (cable side) | four SATA 22-pin receptacles; the lid hinge knuckles above them |
| right | DIN 12 V jack, USB-C (rpiboot), microSD |
| left | the CM5 antenna edge: vent slots only, no metal |
| front | vent slots, the lid latch |
| lid | OLED window over the SSD (module on a 4-wire lead, clamped by the bezel), DIP switch slot, 8 LED holes, convection grille over the passive CM5 cooler |
| floor | rubber-feet pockets |

* `board.scad` is **generated** from `hardware/brain-drain.kicad_pcb` by
  `tools/kicad_to_scad.py` (board outline, mounting holes, and the centre of
  every connector, switch and LED the shell must cut). Re-run it whenever the
  board changes.
* `params.scad` holds the printed-part parameters: walls, clearances, heights,
  insert sizes, OLED window position, hinge and latch sizes.
* `refinements.scad`: OLED bezel, feet pockets.
* `scene.scad`: the render scenes (closed unit, four loose drives, cables; lid open).
* `shell.scad`: the tray (board on M2.5 heat-set standoffs, cutouts on the rear
  and right walls, vents, hinge knuckles, latch groove) and the lid (front and
  side skirt, hinge knuckles, latch bump).

```
make            # board.scad + stl/tray.stl, lid.stl, bezel.stl  (needs openscad)
make renders    # scene STLs and renders/*.png via tools/stl_preview.py (numpy + Pillow, no display needed)
```

Verified 2026-09-23 with OpenSCAD 2021.01: all parts export without warnings.

Print PETG or ASA, 0.2 mm layers. The tray prints as modelled; the lid prints
upside down. The hinge pin is a 140 mm length of 1.75 mm filament.

Known simplifications: cutouts are rectangles sized from nominal connector
faces, so check the DIN jack round face and the SATA plug latch clearance on the
first print; the hinge knuckles and the latch bump are first guesses at fit
(0.3 mm pin clearance, 1.6 mm bump); the OLED lead from J41 to the window is
about 40 mm.
