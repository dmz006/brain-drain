# Export the printable parts and the renders. Needs openscad on PATH.
SCAD = openscad -q
PY = ../software/.venv/bin/python
PARTS = stl/tray.stl stl/lid.stl stl/door.stl stl/door_hinged.stl stl/bezel.stl
all: board.scad $(PARTS)
board.scad: ../hardware/brain-drain.kicad_pcb tools/kicad_to_scad.py
	python3 tools/kicad_to_scad.py
stl/tray.stl stl/lid.stl stl/door.stl: shell.scad params.scad board.scad refinements.scad
	$(SCAD) -D 'part="$(basename $(notdir $@))"' -o $@ shell.scad
stl/door_hinged.stl stl/bezel.stl: refinements.scad params.scad board.scad
	$(SCAD) -D 'part="$(basename $(notdir $@))"' -o $@ refinements.scad
# assembled scene: the unit, four loose drives and their cables, as separate STLs so the renderer can colour them
stl/scene_unit.stl stl/scene_drives.stl stl/scene_cables.stl: scene.scad shell.scad refinements.scad params.scad board.scad
	$(SCAD) -D 'group="$(patsubst scene_%,%,$(basename $(notdir $@)))"' -o $@ scene.scad
# OpenSCAD's own PNG export needs an X display; these previews render the STLs headlessly
SCENE = stl/scene_unit.stl:205,208,214 stl/scene_drives.stl:90,94,100 stl/scene_cables.stl:200,40,40
renders: $(PARTS) stl/scene_unit.stl stl/scene_drives.stl stl/scene_cables.stl
	$(PY) tools/stl_preview.py renders/assembled-iso.png --view iso $(SCENE)
	$(PY) tools/stl_preview.py renders/assembled-iso-left.png --view iso2 $(SCENE)
	$(PY) tools/stl_preview.py renders/assembled-top.png --view top $(SCENE)
	$(PY) tools/stl_preview.py renders/unit-iso.png --view iso stl/scene_unit.stl:205,208,214
	$(PY) tools/stl_preview.py renders/tray-iso.png --view iso stl/tray.stl:205,208,214
	$(PY) tools/stl_preview.py renders/lid-inside.png --view top stl/lid.stl:205,208,214
	$(PY) tools/stl_preview.py renders/door-hinged.png --view iso stl/door_hinged.stl:205,208,214
	$(PY) tools/stl_preview.py renders/bezel.png --view iso stl/bezel.stl:205,208,214
clean:
	rm -f stl/*.stl
.PHONY: all clean renders
