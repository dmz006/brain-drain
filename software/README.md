# software — `braindrain` sanitizer service

Python 3.11+. Design in `../docs/ARCHITECTURE.md` §4. Status: engine, policy,
safety fence, host overwrite, verification, certificates, the bay 9 M.2 slot
controller and the simulated HAL are implemented and tested. The ATA/NVMe firmware wrappers, real GPIO and OLED
drivers are written but **untested on hardware**.

## Develop on a workstation (simulation)

```
cd software
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest

# terminal 1: the appliance, with a 2 s grace period and the OLED drawn in the terminal
braindrain simulate --grace 2

# terminal 2: plug drives in and out
braindrain sim-plug 1 --size 512M --media hdd --prefill          # host overwrite + full verify
braindrain sim-plug 3 --size 256M --media ssd --fw crypto,block  # simulated firmware sanitize + canaries
braindrain sim-plug 2 --size 2G --throttle 50M                   # slow enough to watch % and ETA
braindrain sim-unplug 2                                          # aborts bay 2
braindrain sim-plug 9 --size 256M --media nvme --fw crypto,block # NVMe in the M.2 slot (bay 9)
braindrain sim-door closed                                       # shut the M.2 door (bay 9): slot powers, rescans, wipe starts
braindrain sim-door open                                         # aborts bay 9 and cuts slot power
braindrain sim-pedet sata                                        # pretend a SATA M.2 module: refused
echo 01100000 > ~/.brain-drain-sim/dip                           # switch to legacy 3-pass (DIP 1-3 = 011)
braindrain dip 01100000                                          # decode a DIP setting
```

Certificates land in `~/.brain-drain-sim/reports/`. The last OLED frame is in
`~/.brain-drain-sim/display.txt`.

Simulated drives are sparse files under `~/.brain-drain-sim/bay<N>/`. The
engine never touches anything else: on a workstation it cannot see real disks
in simulation mode at all.

## Layout

```
braindrain/
  config.py          bay <-> USB port map, bridge allow-list, GPIO numbers, timings
  policy.py          DIP decoding, NIST tier, method chain per media type
  devices.py         Drive model, safety fence (classify), pyudev enumeration, identity
  blockio.py         O_DIRECT + aligned buffers, size/sector ioctls
  verify.py          full / sampled read-back, canaries for firmware wipes
  progress.py        EWMA rate, ETA, formatters
  report.py          certificate JSON, crash state
  engine.py          per-bay state machine and workers
  display.py         21x8 OLED frame renderer (pure)
  methods/           overwrite, ata (hdparm), nvme (nvme-cli), simfw, dryrun
  hal/               sim, gpio (libgpiod v2), oled (luma.oled)
  sim/               simulated bays + udev watcher for real hardware
  cli.py
tests/
```

## Real hardware or a bench dock

Needs `hdparm >= 9.65`, `nvme-cli`, `sg3-utils`, `smartmontools`, `util-linux`,
plus `pip install -e ".[hw]"` on the appliance (`gpiod`, `luma.oled`).

`sudo braindrain list` enumerates every disk and prints the fence verdict for
each, including the USB port path. To use a bench dock, put its port path into
`Config.bay_ports` and its bridge VID:PID into `Config.allowed_bridges`; nothing
outside those is ever a candidate. `sudo braindrain run` starts the service.

## Bench questions still open (need a dock + sacrificial drives)

* Does `hdparm --sanitize-*` pass through the dock's bridge, and does
  `--sanitize-status` report progress in the format `parse_sanitize_status` expects?
* Does the bridge survive a full `SECURITY ERASE UNIT` without resetting?
* What does the bridge do to a hot-plugged SATA drive: clean add event, or reset?
