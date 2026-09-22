# enclosure — parametric OpenSCAD shell

Two printed parts plus a door blank, sized from the real board:

* `board.scad` is **generated** from `hardware/brain-drain.kicad_pcb` by
  `tools/kicad_to_scad.py` (board outline, mounting holes, and every connector,
  switch and LED the shell must cut). Re-run it whenever the board changes.
* `params.scad` holds the printed-part parameters: walls, clearances, heights,
  insert sizes, OLED window, door size.
* `shell.scad` builds the tray (board on M2.5 heat-set standoffs, rear wall
  cutouts for DIN / RJ45 / USB-C / 4× SATA, microSD slot on the left, M.2 door
  opening on the right, front vents), the lid (OLED window + module recess,
  DIP slot, 8 LED holes, fan grille over the CM5, corner screws), and a snap-in
  door blank.

```
make            # board.scad + stl/tray.stl, lid.stl, door.stl  (needs openscad)
make preview    # stl/tray-iso.png, stl/lid-inside.png via tools/stl_preview.py (no display needed)
```

Verified 2026-09-23 with OpenSCAD 2021.01: all three parts export without
warnings; tray 186.8 × 116.8 × 40 mm, lid 6.4 mm including its skirt.

Print PETG or ASA, 0.2 mm layers. The tray prints as modelled; the lid prints
upside down. Outer size is about 190 × 120 × 44 mm.

Known simplifications in v1: the OLED module is lid-mounted on a 4-wire lead
to J41; the M.2 door is a blank plug, not a hinge; rear cutouts are rectangles
sized from nominal connector faces, so check the DIN jack round face and the
SATA plug latch clearance on the first print.
