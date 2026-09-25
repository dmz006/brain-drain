# Export the printable parts and the renders. Needs openscad on PATH.
SCAD = openscad -q
PY = ../software/.venv/bin/python
PY3 = python3   # the gallery needs pcbnew (system KiCad Python) plus numpy and Pillow
PARTS = stl/tray.stl stl/lid.stl stl/bezel.stl
all: board.scad $(PARTS)
board.scad: ../hardware/brain-drain.kicad_pcb tools/kicad_to_scad.py
	python3 tools/kicad_to_scad.py
stl/tray.stl stl/lid.stl: shell.scad params.scad board.scad refinements.scad
	$(SCAD) -D 'part="$(basename $(notdir $@))"' -o $@ shell.scad
stl/bezel.stl: refinements.scad params.scad board.scad
	$(SCAD) -D 'part="$(basename $(notdir $@))"' -o $@ refinements.scad
# assembled scene: the unit, four loose drives and their cables, as separate STLs so the renderer can colour them
stl/scene_unit.stl stl/scene_drives.stl stl/scene_cables.stl stl/scene_open.stl: scene.scad shell.scad refinements.scad params.scad board.scad
	$(SCAD) -D 'group="$(patsubst scene_%,%,$(basename $(notdir $@)))"' -o $@ scene.scad
# OpenSCAD's own PNG export needs an X display; the gallery renders the STLs and the board models headlessly into ../docs/img/renders/
SCENE = stl/scene_unit.stl:205,208,214 stl/scene_drives.stl:90,94,100 stl/scene_cables.stl:200,40,40
renders: $(PARTS) stl/scene_unit.stl stl/scene_drives.stl stl/scene_cables.stl stl/scene_open.stl
	$(PY3) tools/gallery.py all
clean:
	rm -f stl/*.stl
.PHONY: all clean renders
