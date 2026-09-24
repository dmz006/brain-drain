#!/bin/sh
# Unattended routing chain after `route.py stage1` has been started (or finished): waits for it, then
# stage 2 (2.1.0, hours), stage 3 (2.4.1, bounded), DRC cleanup, final fanouts, DRC, reports, renders.
cd "$(dirname "$0")/.."
RD=routing; [ "${BD_PROJECT:-brain}" = card ] && RD=bay-card/routing
PCBF=brain-drain.kicad_pcb; [ "${BD_PROJECT:-brain}" = card ] && PCBF=bay-card/bay-card.kicad_pcb
log=$RD/chain.log
echo "chain start $(date)" > $log
while pgrep -f "^python3 tools/route.py stage1$" >/dev/null; do sleep 20; done   # any project; both chains never overlap stage 1
echo "stage1 done $(date)" >> $log
rm -f $RD/*.ses; : > /tmp/freerouting/freerouting.log
python3 tools/route.py stage2 > $RD/stage2.log 2>&1; echo "stage2 done $(date): $(grep -v 'memory leak\|assert\|Debug' $RD/stage2.log | tail -1)" >> $log
rm -f $RD/*.ses
BD_ROUTER=2.4.1 BD_PASSES=12 python3 tools/route.py stage3 > $RD/stage3.log 2>&1; echo "stage3 done $(date): $(grep -v 'memory leak\|assert\|Debug' $RD/stage3.log | tail -1)" >> $log
python3 tools/route.py drc-clean 2>&1 | grep drc_clean >> $log
kicad-cli pcb drc --format json --severity-all -o $RD/drc.json $PCBF >/dev/null 2>&1
python3 tools/route.py fanout 2>&1 | grep fanout >> $log
python3 tools/route.py fanout-big 2>&1 | grep fanout >> $log
python3 tools/route.py fanout-conn 2>&1 | grep fanout >> $log
python3 tools/route.py fanout-qfn 2>&1 | grep fanout >> $log
kicad-cli pcb drc --format json --severity-all -o $RD/drc.json $PCBF >/dev/null 2>&1
python3 tools/open_report.py 2>&1 | tail -1 >> $log
python3 tools/route.py pairs 2>&1 | grep pairs >> $log
sh tools/render_board.sh >/dev/null 2>&1
echo "chain done $(date)" >> $log
