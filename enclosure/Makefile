# Export the printable parts. Needs openscad on PATH.
SCAD = openscad -q
all: board.scad stl/tray.stl stl/lid.stl stl/door.stl stl/door_hinged.stl stl/bezel.stl stl/rack.stl
board.scad: ../hardware/brain-drain.kicad_pcb tools/kicad_to_scad.py
	python3 tools/kicad_to_scad.py
stl/tray.stl stl/lid.stl stl/door.stl: shell.scad params.scad board.scad refinements.scad
	$(SCAD) -D 'part="$(basename $(notdir $@))"' -o $@ shell.scad
stl/door_hinged.stl stl/bezel.stl stl/rack.stl: refinements.scad params.scad board.scad
	$(SCAD) -D 'part="$(basename $(notdir $@))"' -o $@ refinements.scad
# OpenSCAD's own PNG export needs an X display; these previews render the STLs headlessly
PY = ../software/.venv/bin/python
preview: stl/tray.stl stl/lid.stl
	$(PY) tools/stl_preview.py stl/tray.stl stl/tray-iso.png --view iso
	$(PY) tools/stl_preview.py stl/lid.stl stl/lid-inside.png --view top
clean:
	rm -f stl/*.stl stl/*.png
.PHONY: all clean preview
