#!/bin/sh
# Fabrication pack for a JLCPCB/PCBWay-style order (docs/FABRICATION.md gate 6). Run from hardware/.
# Output: fab/<date>/ with gerbers + drill (zipped), pick-and-place CSV, BOM CSV, board PDFs.
set -e
cd "$(dirname "$0")/.."
OUT="fab/$(date +%Y-%m-%d)"
rm -rf "$OUT"; mkdir -p "$OUT/gerbers"
kicad-cli pcb export gerbers --board-plot-params --subtract-soldermask -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o "$OUT/gerbers/" brain-drain.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 -o "$OUT/gerbers/" brain-drain.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin -o "$OUT/brain-drain-pos.csv" brain-drain.kicad_pcb
cp bom/brain-drain-bom.csv "$OUT/brain-drain-bom.csv"
kicad-cli pcb export pdf -l F.Cu,F.SilkS,F.Fab,Edge.Cuts -o "$OUT/assembly-top.pdf" brain-drain.kicad_pcb
kicad-cli pcb export pdf -l B.Cu,B.SilkS,B.Fab,Edge.Cuts --mirror -o "$OUT/assembly-bottom.pdf" brain-drain.kicad_pcb
kicad-cli pcb drc --format json --severity-error -o "$OUT/drc.json" brain-drain.kicad_pcb >/dev/null
(cd "$OUT" && zip -q -r brain-drain-gerbers.zip gerbers)
echo "fab pack in $OUT:"; ls "$OUT"
