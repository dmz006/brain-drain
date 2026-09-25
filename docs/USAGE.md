# Usage

## Software: simulate on a workstation

```
cd software
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest                                    # 61 tests
braindrain simulate --grace 2             # terminal 1: the appliance, OLED drawn in the terminal
```

In a second terminal:

```
braindrain sim-plug 1 --size 1G --media hdd --prefill --throttle 50M   # host overwrite + full verify, slow enough to watch
braindrain sim-plug 3 --size 256M --media ssd --fw crypto,block         # simulated firmware sanitize + canary check
braindrain sim-plug 5 --size 256M --media nvme --fw crypto,block        # NVMe in the M.2 slot
braindrain sim-door closed                                              # slot powers, rescans, wipe starts
braindrain sim-unplug 1                                                 # aborts bay 1
echo 01100000 > ~/.brain-drain-sim/dip                                  # legacy 3-pass (DIP 1-3 = 011)
braindrain dip 01100000                                                 # decode a setting
```

Certificates: `~/.brain-drain-sim/reports/`. Last OLED frame: `~/.brain-drain-sim/display.txt`.

DIP switch (ON = 1): 1–3 mode (000 auto, 001 purge, 010 clear, 011 3-pass,
100 7-pass, 101 crypto-only, 111 dry-run), 4 random pattern, 5 sampled verify,
8 maintenance (never wipe).

## Software: bench a USB-SATA dock

```
sudo .venv/bin/braindrain bench /dev/sdX                       # non-destructive: bridge id, IDENTIFY, SMART, sanitize-status, read speed
sudo .venv/bin/braindrain bench /dev/sdX --destructive         # + write test and SECURITY ERASE, asks for the serial
sudo .venv/bin/braindrain bench /dev/sdX --destructive --sanitize   # + full SANITIZE (hours on an HDD)
```

## Software: deploy on a Raspberry Pi

```
sudo software/deploy/install.sh --headless   # Pi + docks, no carrier board
sudo /opt/brain-drain/venv/bin/braindrain list
sudo /opt/brain-drain/venv/bin/braindrain setup-bay 1 /dev/sdX
sudo systemctl start brain-drain && journalctl -fu brain-drain
```

Without `--headless` the real HAL is used (DIP, OLED, bay power, M.2 slot);
that needs the carrier board. Config lives in `/etc/brain-drain/config.json`.

## Hardware: regenerate everything from the netlist

Needs KiCad 9 (`kicad-cli` and the `pcbnew` Python module of the system Python 3), Python packages `numpy` and `Pillow`, poppler-utils (`pdftoppm`),
and, for routing only, Java 21 and Java 25 plus the two freerouting jars downloaded from https://github.com/freerouting/freerouting/releases
(v2.1.0 and v2.4.1) into `hardware/tools/freerouting/` (they are not in the repository). Two boards share one pipeline:
`BD_PROJECT=brain` (default, files in `hardware/`) and `BD_PROJECT=card` (the bay card, files in `hardware/bay-card/`).

**Everything from the netlist to a routed board, unattended** (card about 10 minutes, brain about 1.5 hours):

```
cd hardware
python3 tools/symgen.py                               # lib/brain-drain.kicad_sym (symbols, incl. the bay slot and the P-FETs)
python3 tools/fpgen.py                                # lib/brain-drain.pretty (PCIe slot, SATA receptacle, DIN, TPS56637)
BD_PROJECT=brain python3 tools/gen_sch.py             # schematic files + ERC     (repeat with BD_PROJECT=card)
BD_PROJECT=brain sh tools/route_full.sh               # gen_pcb, rules and planes, fanout, pairs first (stage 0), signals, planes,
                                                      # gap router, tuner, pair fixer, via clean-up, reports, renders
tail -f routing/chain.log                             # progress (bay-card/routing/chain.log for the card)
```

The log ends with the open-connection and pair counts; the results are in `routing/open.md`, `routing/pairs.md` and `routing/drc.json`.
**Regenerating overwrites the board.** Once a designer edits a board in KiCad, keep that copy and do not run `route_full.sh` on it.

**The individual steps** (each is one `python3 tools/route.py <command>` in `hardware/`):

| Command | Does |
|---|---|
| `python3 tools/gen_pcb.py`, `check_place.py` | placement, courtyard and outline check (`-v` lists positions) |
| `route.py prepare` | net classes into the `.kicad_pro`, pair rules, zones (fresh board only), CM5 hole and antenna keep-outs |
| `route.py fanout`, `fanout-big`, `fanout-conn`, `fanout-qfn`, `fanout-qfn-rip` | plane and supply vias for small parts, exposed pads, connector rows, 0.4 mm QFN pins |
| `route.py stage0` (pairs alone, first), `stage1` (signals), `stage2` (planes, rails, bays) | freerouting stages; each locks what exists (`BD_PAIRS_FIRST=1`, `BD_ROUTER=2.4.1 BD_PASSES=12` for the bounded router) |
| `route.py drc-clean` | removes copper the router left in violation, widens slivers |
| `route.py close-gaps`, `close-gaps-pairs` | our grid router for what is left; `BD_RES=0.05 BD_MARGIN=0.2 BD_ONLY=net,net` for a tight pin |
| `route.py tune` | meanders the shorter side of every pair, end to end across the series caps; `sh tools/fix_pairs.sh` retries stubborn pairs |
| `route.py via-clean` | removes overlapping and dangling vias when connectivity is unchanged |
| `python3 tools/open_report.py`, `route.py pairs` | `routing/open.md`, `routing/pairs.md` |
| `sh tools/render_board.sh` | KiCad 3D views, per-layer PNGs in `renders/layers/`, schematic PDF and PNGs |
| `python3 tools/gen_bom.py` | BOM of both boards: `bom/*.csv` and `docs/BOM.md` |
| `python3 tools/make_review_pack.py` | `hardware/review/`: rules, stack-up, planes, keep-outs, routing statistics, DRC / ERC, footprint provenance, netlists, placement CSV |
| `sh tools/export_fab.sh` | `fab/<date>/`: gerbers and drill zip, placement CSV, BOM, assembly PDFs (order pack, gitignored) |
| `kicad-cli pcb drc --format json --severity-all -o routing/drc.json brain-drain.kicad_pcb` | the DRC report used everywhere |

Open `hardware/brain-drain.kicad_pro` (or `hardware/bay-card/bay-card.kicad_pro`) in KiCad 9 to inspect or edit. Before any routing run, check the
DSN: its `(rule` block must say `clearance 150` and the `(class` list must have the project's classes; a DSN exported without the project's net
classes carries KiCad's 0.2 mm default, which makes every 0.4 mm-pitch pad a violation and the router routes nothing. Freerouting 2.1.0 ignores its
pass limit and stops only when its board history is exhausted; the scripts allow for that. After heavy edits pcbnew's Python proxies break, so the
tools run each edit step in a fresh process. Details of the tool set: [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md) section 6.

## The phone page and Wi-Fi

The unit boots into its own access point. On the OLED, idle, you see a QR code
and the key. Scan the code (or join `brain-drain-xxxx` by hand with the key as
the password) and open `http://10.42.0.1/`. The page shows the bays, the
certificates (download one or all as a zip), the log, and two forms that need
the key from the screen:

* **Join a network**: the unit joins it now and at every boot; the new address
  shows on the OLED. If the join fails it falls back to the access point.
* **Reset**: *Wi-Fi reset* forgets the network and starts the access point
  with a fresh key; *factory reset* also deletes every certificate and the
  crash-recovery state.

Without a network: set the DIP to mode `110` and power-cycle for a Wi-Fi reset,
`110` with DIP 8 ON for a factory reset (the unit never wipes in that mode; set
the policy back afterwards). Over SSH: `braindrain wifi-reset [--factory]`.

In the simulator the page is on `http://127.0.0.1:8080/` (`--web PORT`) and
the wireless backend is a file in the sim directory.

## Enclosure

```
cd enclosure
make            # board.scad from the board file (x mirrored, see ARCHITECTURE 5), then stl/{tray,lid,bezel}.stl
make renders    # scene STLs, then every image of the case, the electronics inside it and the complete system into docs/img/renders/
```

Edit `params.scad` for print parameters; never edit `board.scad`. `python3 enclosure/tools/gallery.py [boards|electronics|case|unit|all]` renders one set;
it needs pcbnew, numpy and Pillow (no display). The 3D proxy model of the boards is `hardware/tools/board_model.py`.

## Documentation images

```
software/.venv/bin/python docs/tools/diagrams.py        # system block, lid plan, wall panel, bay flow (SVG + PNG)
software/.venv/bin/python software/tools/oled_mockup.py docs/img
python3 enclosure/tools/gallery.py all                   # docs/img/renders/*.png
python3 hardware/tools/make_review_pack.py               # hardware/review/
```
