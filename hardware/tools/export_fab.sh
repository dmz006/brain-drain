#!/bin/sh
# Fabrication pack for a JLCPCB/PCBWay-style order (docs/FABRICATION.md gate 6). Run from hardware/.
#   BD_PROJECT=brain (default) or BD_PROJECT=card
# Output: fab/<date>/<name>/ with gerbers + drill (zipped), pick-and-place CSV, BOM CSV, assembly PDFs, a DRC report.
set -e
cd "$(dirname "$0")/.."
if [ "${BD_PROJECT:-brain}" = card ]; then
    N=bay-card; PCB=bay-card/bay-card.kicad_pcb; COPPER=F.Cu,In1.Cu,In2.Cu,B.Cu
else
    N=brain-drain; PCB=brain-drain.kicad_pcb; COPPER=F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu
fi
OUT="fab/$(date +%Y-%m-%d)/$N"
rm -rf "$OUT"; mkdir -p "$OUT/gerbers"
kicad-cli pcb export gerbers --board-plot-params --subtract-soldermask -l $COPPER,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o "$OUT/gerbers/" $PCB
kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 -o "$OUT/gerbers/" $PCB
kicad-cli pcb export pos --format csv --units mm --side both --use-drill-file-origin -o "$OUT/$N-pos.csv" $PCB
cp bom/$N-bom.csv "$OUT/$N-bom.csv" 2>/dev/null || cp bom/brain-drain-bom.csv "$OUT/$N-bom.csv"
kicad-cli pcb export pdf -l F.Cu,F.SilkS,F.Fab,Edge.Cuts -o "$OUT/assembly-top.pdf" $PCB
kicad-cli pcb export pdf -l B.Cu,B.SilkS,B.Fab,Edge.Cuts --mirror -o "$OUT/assembly-bottom.pdf" $PCB
kicad-cli pcb drc --format json --severity-error -o "$OUT/drc.json" $PCB >/dev/null
(cd "$OUT" && zip -q -r $N-gerbers.zip gerbers)
echo "fab pack in $OUT:"; ls "$OUT"
