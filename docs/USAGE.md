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

Unattended, from placement to finished routing: `BD_PROJECT=brain sh tools/route_full.sh` (card about 10 min, brain about 3.5 h: pairs first, then signals and planes, gap closer, tuner, reports, renders). Length matching is `route.py tune`, the small-gap router is `route.py close-gaps`.

Two boards share one pipeline: `BD_PROJECT=brain` (default, files in `hardware/`)
and `BD_PROJECT=card` (the bay card, files in `hardware/bay-card/`).

```
cd hardware
python3 tools/symgen.py          # lib/brain-drain.kicad_sym from ref/*.csv
python3 tools/design.py          # pin coverage check
python3 tools/gen_sch.py         # brain-drain.kicad_sch + sheets/, ERC via kicad-cli
python3 tools/gen_connections.py # CONNECTIONS.md
python3 tools/gen_pcb.py         # brain-drain.kicad_pcb: outline, holes, placed footprints with nets
python3 tools/check_place.py     # every courtyard inside the outline, no clashes (-v lists positions)
python3 tools/route.py prepare   # net classes (written into brain-drain.kicad_pro, which is where KiCad keeps them),
                                 # diff-pair rules, copper zones, CM5 hole and antenna keep-outs (zones only on a fresh board)
python3 tools/route.py fanout    # via + stub next to every SMD pad on a plane net (small parts only)
python3 tools/route.py dsn       # Specctra DSN -> routing/ (full, and lite = no diff pairs / bay nets)
java -Djava.awt.headless=true -jar tools/freerouting/freerouting-2.1.0.jar -de routing/brain-drain-lite.dsn -do routing/brain-drain-lite.ses -mp 8 -oit 2
                                 # (or `route.py all` which runs the whole chain); -oit 2 stops the optimizer looping forever
python3 tools/route.py import    # session back into the board; anything crossing a keep-out stripped; zones filled
# staged flow used for the v2 board (each stage locks what exists and routes on top of it):
python3 tools/route.py fanout-big && python3 tools/route.py fanout-conn   # exposed-pad vias, connector-row vias
python3 tools/route.py stage1    # signal nets            (2.1.0, ~12 min)
python3 tools/route.py stage2    # planes, rails, bays    (2.1.0, ~3.5 h: it stops only at pass 999)
BD_ROUTER=2.4.1 BD_PASSES=12 python3 tools/route.py stage3   # pairs, bounded run on Java 25 (~45 min)
python3 tools/route.py drc-clean # remove any copper the router left in violation
python3 tools/open_report.py     # routing/open.md; pairs: python3 tools/route.py pairs -> routing/pairs.md
python3 tools/fpgen.py           # project footprints from vendor drawings
sh tools/render_board.sh         # renders/board-top.png, board-inner.png, board-3d-{top,bottom,iso}.png, schematic PDF + PNGs
sh tools/export_fab.sh           # fab/<date>/: gerbers + drill zip, placement CSV, BOM CSV, assembly PDFs (order pack)
kicad-cli pcb drc --format json --severity-all -o routing/drc.json brain-drain.kicad_pcb
```

Open `hardware/brain-drain.kicad_pro` in KiCad 9 to inspect or tidy. Hand
placement survives regeneration if written to `tools/placement.json`. Check the
DSN before a long router run: its `(rule` block must say `clearance 150` and
the `(class` list must have four classes; a DSN exported without the project's
net classes carries KiCad's 0.2 mm default, which makes every 0.4 mm-pitch pad
a violation and the router routes nothing. Freerouting reads its own limits from
`/tmp/freerouting/freerouting.json` (`router.max_passes`, default 9999): the run
ends when the optimizer gives up, which took about 12 minutes here.

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
make            # board.scad from the board file, then stl/{tray,lid,bezel}.stl
make renders    # scene STLs (closed unit with four loose drives and cables, lid open) and renders/*.png (no display needed)
```

Edit `params.scad` for print parameters; never edit `board.scad`.

## Documentation images

```
software/.venv/bin/python docs/tools/diagrams.py        # system-block, rear/right panels, bay-flow (SVG + PNG)
software/.venv/bin/python software/tools/oled_mockup.py docs/img
```
