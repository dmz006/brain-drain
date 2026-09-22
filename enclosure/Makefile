# Export the printable parts. Needs openscad on PATH.
SCAD = openscad -q
all: board.scad stl/tray.stl stl/lid.stl stl/door.stl
board.scad: ../hardware/brain-drain.kicad_pcb tools/kicad_to_scad.py
	python3 tools/kicad_to_scad.py
stl/%.stl: shell.scad params.scad board.scad
	$(SCAD) -D 'part="$*"' -o $@ shell.scad
preview.png: shell.scad params.scad board.scad
	$(SCAD) --autocenter --viewall --imgsize=1600,1000 -o $@ shell.scad
clean:
	rm -f stl/*.stl preview.png
.PHONY: all clean
