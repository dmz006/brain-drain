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

```
cd hardware
python3 tools/symgen.py          # lib/brain-drain.kicad_sym from ref/*.csv
python3 tools/design.py          # pin coverage check
python3 tools/gen_sch.py         # brain-drain.kicad_sch + sheets/, ERC via kicad-cli
python3 tools/gen_connections.py # CONNECTIONS.md
python3 tools/gen_pcb.py         # brain-drain.kicad_pcb: outline, holes, placed footprints with nets
python3 tools/route.py prepare   # net classes, diff-pair rules, copper zones
python3 tools/route.py dsn       # Specctra DSN -> routing/
java -Djava.awt.headless=true -jar tools/freerouting/freerouting-2.1.0.jar -de routing/brain-drain.dsn -do routing/brain-drain.ses -mp 20
python3 tools/route.py import    # session back into the board, bay nets stripped, zones filled
python3 tools/fpgen.py           # project footprints from vendor drawings
```

Open `hardware/brain-drain.kicad_pro` in KiCad 9 to inspect or tidy. Hand
placement survives regeneration if written to `tools/placement.json`.

## Enclosure

```
cd enclosure
make            # board.scad from the board file, then stl/{tray,lid,door,door_hinged,bezel,rack}.stl
make preview    # PNG previews via tools/stl_preview.py (no display needed)
```

Edit `params.scad` for print parameters; never edit `board.scad`.

## Documentation images

```
software/.venv/bin/python docs/tools/diagrams.py        # system-block, rear-panel, bay-flow (SVG + PNG)
software/.venv/bin/python software/tools/oled_mockup.py docs/img
```
