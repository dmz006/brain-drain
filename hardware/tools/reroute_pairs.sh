#!/bin/sh
# Pairs the tuner cannot fix (a side unrouted, or detoured beyond 0.15 mm): rip both nets up, let the bounded
# router (2.4.1) route them again with the rest of the copper locked, clean up, tune again. Each step is its
# own process because pcbnew's Python proxies break after heavy board edits. BD_PROJECT selects the board.
cd "$(dirname "$0")/.."
RD=routing; [ "${BD_PROJECT:-brain}" = card ] && RD=bay-card/routing
log=$RD/chain.log
python3 tools/route.py rip-pairs 2>&1 | grep rip_pairs | tee -a $log
rm -f $RD/*.ses
BD_ROUTER=2.4.1 BD_PASSES=${BD_PASSES:-12} python3 tools/route.py stage3 > $RD/stage3.log 2>&1
echo "reroute stage3: $(grep -v 'memory leak\|assert\|Debug' $RD/stage3.log | tail -1)" >> $log
python3 tools/route.py drc-clean 2>&1 | grep drc_clean >> $log
python3 tools/route.py tune 2>&1 | grep '^tune' >> $log
PCBF=brain-drain.kicad_pcb; [ "${BD_PROJECT:-brain}" = card ] && PCBF=bay-card/bay-card.kicad_pcb
kicad-cli pcb drc --format json --severity-all -o $RD/drc.json $PCBF >/dev/null 2>&1
python3 tools/open_report.py 2>&1 | tail -1 >> $log
python3 tools/route.py pairs 2>&1 | grep pairs >> $log
echo "reroute done $(date)" >> $log
