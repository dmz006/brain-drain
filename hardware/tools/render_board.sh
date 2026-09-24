#!/bin/sh
# Board renders for the docs (kicad-cli 9). Run from hardware/.
set -e
cd "$(dirname "$0")/.."
VENV_PY="$(pwd)/../software/.venv/bin/python"
# project-aware: BD_PROJECT=brain (default, hardware/) or card (hardware/bay-card/)
if [ "${BD_PROJECT:-brain}" = card ]; then cd bay-card; N=bay-card; else N=brain-drain; fi
mkdir -p renders renders/schematic
kicad-cli pcb export pdf -l F.Cu,F.SilkS,F.Mask,Edge.Cuts,F.CrtYd -o renders/board-top.pdf $N.kicad_pcb
kicad-cli pcb export pdf -l In1.Cu,In2.Cu,B.Cu,Edge.Cuts -o renders/board-inner.pdf $N.kicad_pcb
kicad-cli pcb render -w 1800 -h 1200 --side top --background opaque -o renders/board-3d-top.png $N.kicad_pcb
kicad-cli pcb render -w 1800 -h 1200 --side bottom --background opaque -o renders/board-3d-bottom.png $N.kicad_pcb
kicad-cli pcb render -w 1800 -h 1200 --perspective --rotate '-30,0,35' --zoom 1.1 --background opaque -o renders/board-3d-iso.png $N.kicad_pcb
# PDF -> PNG for the README (pdftoppm from poppler-utils)
pdftoppm -r 110 -png -singlefile renders/board-top.pdf renders/board-top
pdftoppm -r 110 -png -singlefile renders/board-inner.pdf renders/board-inner
echo "renders written to $(pwd)/renders/"
# schematic PDF + one PNG per sheet
kicad-cli sch export pdf -o renders/schematic/$N-schematic.pdf $N.kicad_sch
rm -f renders/schematic/sheet-*.png
pdftoppm -r 60 -png renders/schematic/$N-schematic.pdf renders/schematic/sheet
# crop the PDF-derived PNGs to the board (the export still draws the sheet frame)
"$VENV_PY" - <<'PY'
from PIL import Image, ImageChops
for n in ("board-top", "board-inner"):
    im = Image.open(f"renders/{n}.png").convert("RGB")
    w, h = im.size
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 40 else 0)
    bb = diff.crop((int(w * 0.03), int(h * 0.04), int(w * 0.97), int(h * 0.84))).getbbox()
    if bb:
        x0, y0, x1, y1 = bb
        im.crop((x0 + int(w * 0.03) - 10, y0 + int(h * 0.04) - 10, x1 + int(w * 0.03) + 10, y1 + int(h * 0.04) + 10)).save(f"renders/{n}.png")
PY
