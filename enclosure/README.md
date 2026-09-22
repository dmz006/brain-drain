# enclosure — parametric OpenSCAD shell

See `../docs/ARCHITECTURE.md` §5. Not started; waits on the board outline.

```
enclosure/
  params.scad            # every dimension lives here
  board.scad             # generated from KiCad by tools/kicad_to_scad.py (do not edit)
  shell.scad             # bottom tray + lid, cutouts
  drive-rack.scad        # later: 4-slot rack for the external drives
  tools/kicad_to_scad.py # reads brain-drain.kicad_pcb, emits board.scad
  stl/                   # exported prints
```

Print PETG or ASA, 0.2 mm layers, designed to need no supports.
