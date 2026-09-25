#!/bin/sh
# From the placed, unrouted board to the finished routing, unattended, with the differential pairs routed
# FIRST on the empty board (stage 0, bounded router 2.4.1) so their escapes from the 0.4 mm-pitch pins are
# not blocked by other copper; single-ended stages then route around them (BD_PAIRS_FIRST=1).
# BD_PROJECT=brain|card. Log: <routing>/chain.log.  Total: card ~10 min, brain ~2 h.
cd "$(dirname "$0")/.."
export BD_PAIRS_FIRST=1
RD=routing; [ "${BD_PROJECT:-brain}" = card ] && RD=bay-card/routing
PCBF=brain-drain.kicad_pcb; [ "${BD_PROJECT:-brain}" = card ] && PCBF=bay-card/bay-card.kicad_pcb
log=$RD/chain.log
echo "full chain start $(date)" > $log
run() { python3 tools/route.py "$@" 2>&1 | grep -E "^(fanout|tune|pairs|drc_clean|via_clean|close_gaps|update_nets|rip_pairs|project net)" >> $log; }
drc() { kicad-cli pcb drc --format json --severity-all -o $RD/drc.json $PCBF >/dev/null 2>&1; }
python3 tools/gen_pcb.py > /dev/null 2>&1
python3 tools/route.py prepare > $RD/prepare.log 2>&1
drc
run fanout-big; run fanout-conn; run fanout; drc; run fanout-qfn-rip; drc
echo "fanouts done $(date)" >> $log
rm -f $RD/*.ses
BD_ROUTER=2.4.1 BD_PASSES=${BD_PASSES:-12} python3 tools/route.py stage0 > $RD/stage0.log 2>&1
echo "stage0 (pairs first) done $(date): $(grep -v 'memory leak\|assert\|Debug' $RD/stage0.log | tail -1)" >> $log
rm -f $RD/*.ses
python3 tools/route.py stage1 > $RD/stage1.log 2>&1
echo "stage1 done $(date): $(grep -v 'memory leak\|assert\|Debug' $RD/stage1.log | tail -1)" >> $log
rm -f $RD/*.ses
python3 tools/route.py stage2 > $RD/stage2.log 2>&1
echo "stage2 done $(date): $(grep -v 'memory leak\|assert\|Debug' $RD/stage2.log | tail -1)" >> $log
run drc-clean; drc
run fanout; run fanout-big; run fanout-conn; run fanout-qfn
run close-gaps; run close-gaps-pairs; run drc-clean; run tune
sh tools/fix_pairs.sh
run via-clean
drc
python3 tools/open_report.py 2>&1 | tail -1 >> $log
run pairs
sh tools/render_board.sh >/dev/null 2>&1
echo "chain done $(date)" >> $log
