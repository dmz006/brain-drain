# software — `braindrain` sanitizer service

Python 3.11+. See `../docs/ARCHITECTURE.md` §4.

## Development on a workstation

```
cd software
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
BRAIN_DRAIN_SIM=1 braindrain simulate     # fake bays, terminal OLED, keyboard DIP
pytest
```

Running against a real USB-SATA dock on a workstation is possible but the
safety fence must recognise the dock's USB port path as a bay; see
`braindrain/hal/bays.py`. Never bypass the fence to "just test".

## On the appliance

Raspberry Pi OS Lite 64-bit. Requires `hdparm >= 9.65`, `nvme-cli`,
`sg3-utils`, `smartmontools`, `util-linux`, `libgpiod2`, `python3-libgpiod`,
`i2c-tools`. Installed as `brain-drain.service` (systemd), runs as root.
