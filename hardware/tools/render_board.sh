#!/bin/sh
# Board renders for the docs (kicad-cli 9). Run from hardware/.
set -e
cd "$(dirname "$0")/.."
mkdir -p renders
kicad-cli pcb export pdf -l F.Cu,F.SilkS,F.Mask,Edge.Cuts,F.CrtYd --ibt -o renders/board-top.pdf brain-drain.kicad_pcb
kicad-cli pcb export pdf -l In1.Cu,In2.Cu,B.Cu,Edge.Cuts --ibt -o renders/board-inner.pdf brain-drain.kicad_pcb
kicad-cli pcb render -w 1800 -h 1200 --side top --background opaque -o renders/board-3d-top.png brain-drain.kicad_pcb
kicad-cli pcb render -w 1800 -h 1200 --side bottom --background opaque -o renders/board-3d-bottom.png brain-drain.kicad_pcb
kicad-cli pcb render -w 1800 -h 1200 --perspective --rotate '-30,0,35' --zoom 1.1 --background opaque -o renders/board-3d-iso.png brain-drain.kicad_pcb
# PDF -> PNG for the README (pdftoppm from poppler-utils)
pdftoppm -r 110 -png -singlefile renders/board-top.pdf renders/board-top
pdftoppm -r 110 -png -singlefile renders/board-inner.pdf renders/board-inner
echo "renders written to hardware/renders/"
