# Saturday bench plan — 2026-09-26

Goal: prove the software end to end on real drives, and measure the two things
the hardware design depends on: whether the ASM1153E passes Sanitize and
Security Erase through, and whether it survives a long erase.

## Bring

* A Raspberry Pi 5 (or a PC running Linux) with Raspberry Pi OS Lite 64-bit,
  network, and this repo checked out. A Pi 4 works too, slower.
* One or two USB 3 to SATA docks. Check the chip with `lsusb`:
  `174c:55aa` ASMedia (the design chip), `152d:0578` JMicron JMS578.
* Sacrificial drives: one HDD and, if possible, one SATA SSD. Everything on
  them will be destroyed.
* A 12 V supply for the 3.5" HDD if the dock does not have one.

## Install (once)

```
git clone <repo> && cd brain-drain
sudo software/deploy/install.sh --headless
```

`--headless` means: no carrier board, so no DIP switch, OLED or bay power
control. Policy comes from `headless_dip` in `/etc/brain-drain/config.json`
(default `00000000` = AUTO: HDD single pass zeros + full verify, SSD firmware
sanitize). The last "OLED" frame is written to `/var/lib/brain-drain/display.txt`.

## 1. Identify and map the dock (10 min)

```
lsusb                                        # note the bridge VID:PID
sudo /opt/brain-drain/venv/bin/braindrain list
sudo /opt/brain-drain/venv/bin/braindrain setup-bay 1 /dev/sdX
```

`list` prints every disk with the safety-fence verdict. The Pi's own SD card
or NVMe must show as *skip* (holds root). `setup-bay` writes the dock's USB
port path and bridge ID into the config. From now on **any drive plugged into
that dock is a wipe target** once the service runs.

## 2. Bridge passthrough bench (30 min, destructive)

```
sudo /opt/brain-drain/venv/bin/braindrain bench /dev/sdX
sudo /opt/brain-drain/venv/bin/braindrain bench /dev/sdX --destructive --out-dir ~/bench
```

Watch for, in order:

| Check | Pass looks like | If it fails |
|---|---|---|
| usb bridge | `174c:55aa ASMedia …` | different chip: note it, results apply to that chip |
| hdparm -I | model + serial printed | SAT passthrough broken: the design cannot use this bridge |
| SANITIZE feature set | crypto/block/overwrite flags | drive too old for Sanitize; Security Erase path will be used |
| sanitize-status | `state=idle` | parser fixture needed: copy the raw lines it prints into `tests/test_parsers.py` |
| SECURITY ERASE | rc=0 and "still enumerated" | "device gone" = the bridge reset mid-erase, the failure mode §4.4 warns about; note elapsed time |
| erase time vs estimate | within 2× | |

If the drive reports **frozen**, power-cycle the dock (not the Pi) and rerun.
Copy `~/bench/*.json` into the repo under `hardware/ref/bench/`.

Optional if time allows: `--sanitize` on the SSD (minutes) and on the HDD
(hours; can run unattended after the other tests).

## 3. Full service run (30 min)

```
sudo systemctl start brain-drain
journalctl -fu brain-drain
watch -n1 cat /var/lib/brain-drain/display.txt
```

Plug the sacrificial drive into the mapped dock. Expected: `detected …`, a
5 s countdown, `running overwrite-1pass` (HDD) or the sanitize chain (SSD),
progress on the display frame, `sanitized`, and a certificate under
`/var/lib/brain-drain/reports/`. Then:

* pull the drive mid-wipe → `aborted` certificate, bay back to IDLE;
* plug it again → a second wipe starts (single-use semantics);
* set `headless_dip` to `01100000` (3-pass) in the config, restart the
  service, plug again → three passes.

## 4. What to bring back

* `hardware/ref/bench/*.json` and the certificates from `/var/lib/brain-drain/reports/`.
* Raw `hdparm --sanitize-status` output if the parser flagged it.
* Which GPIO the dock's activity LED blinks on is not observable here; that
  stays a carrier-board question.
* Any drive that would not un-freeze: model and firmware.

These results close decision C12 (bridge) with evidence and settle the
Sanitize-vs-Security-Erase order in `policy.py`.
