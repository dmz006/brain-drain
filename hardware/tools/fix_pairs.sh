#!/bin/sh
# Pairs still off by more than 0.15 mm after `tune` (no room to meander): try ripping up both sides, only the second side,
# or only the first side, and route them again with the pair-aware gap router on a 0.05 mm grid at three margin settings,
# tune after each try, and keep the best result if it is better than what the board has. One pair at a time, every
# step in its own process (pcbnew's Python proxies break after heavy edits). BD_PROJECT selects the board.
cd "$(dirname "$0")/.."
RD=routing; [ "${BD_PROJECT:-brain}" = card ] && RD=bay-card/routing
PCBF=brain-drain.kicad_pcb; [ "${BD_PROJECT:-brain}" = card ] && PCBF=bay-card/bay-card.kicad_pcb
log=$RD/chain.log
mismatch() {   # $1 = "P / N": mismatch from pairs.md, 999 when unrouted
    awk -F'|' -v k="$1" '{ n=$2; gsub(/^ +| +$/, "", n); if (n == k) { m=$6; gsub(/ /, "", m); s=$8; if (s ~ /UNROUTED/) m=999; print m } }' $RD/pairs.md
}
grep "match >\|UNROUTED" $RD/pairs.md | sed 's/^| \([^ ]*\) \/ \([^ ]*\) .*/\1 \2/' | while read P N; do
    key="$P / $N"
    best=$(mismatch "$key"); cp $PCBF /tmp/fp_orig.kicad_pcb; cp $PCBF /tmp/fp_best.kicad_pcb; start=$best
    for who in "$P,$N" "$N" "$P"; do
        for m in 0.2 0.5 1.0; do
            cp /tmp/fp_orig.kicad_pcb $PCBF
            BD_ONLY=$who python3 tools/route.py rip-named >/dev/null 2>&1
            BD_ONLY=$who BD_RES=0.05 BD_MARGIN=$m python3 tools/route.py close-gaps-pairs >/dev/null 2>&1
            python3 tools/route.py drc-clean >/dev/null 2>&1
            python3 tools/route.py tune >/dev/null 2>&1
            after=$(mismatch "$key")
            if awk -v a="$after" -v b="$best" 'BEGIN{exit !(a+0 < b+0)}'; then best=$after; cp $PCBF /tmp/fp_best.kicad_pcb; fi
        done
    done
    cp /tmp/fp_best.kicad_pcb $PCBF
    python3 tools/route.py pairs 2>&1 | grep '^pairs' >> $log
    echo "fix $key: mismatch $start -> $best" >> $log
done
