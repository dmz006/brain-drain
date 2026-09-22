# brain-drain — Architecture

Standalone, headless, four-bay disk sanitizer. Plug in up to four SATA drives via
external pigtails, set the wipe policy on a DIP switch, press Start, watch progress
on the OLED, get a per-drive sanitization certificate. Wipe methods follow
NIST SP 800-88 Rev. 2.

Status: **v0 design, nothing built yet.** This document is the source of truth for
all three workstreams; change it before changing the hardware.

---

## 1. Scope

| In scope | Out of scope (for v1) |
|---|---|
| 4× SATA HDD/SSD (3.5" and 2.5") over USB-SATA bridges | Direct NVMe bays (see §3.3 for the path to add one) |
| NIST 800-88 Rev. 2 Clear and Purge for ATA media | Physical destruction, degaussing |
| Overwrite (host-side) and firmware Sanitize / Security Erase | Wiping the CM4's own boot medium (explicitly forbidden) |
| Per-drive progress/ETA on a small OLED | Touchscreen, web UI (a read-only status page is a cheap later add) |
| JSON certificate per drive, optional network push | Signed/PKI certificates |
| Staggered spin-up, per-bay power control | Hot-swap backplane / drive caddies |

## 2. System overview

```
                 12 V DC in ──► protection ──┬──► 5V_SYS buck ──► CM4, USB host, bridges, UI
                                            ├──► 5V_HDD buck ──► bay switches ──┐
                                            ├──► 3V3 buck    ──► bridges, RTC   │
                                            └──► 12V_HDD     ──► bay switches ──┤
                                                                                │
   ┌──────────────┐ PCIe Gen2 x1 ┌─────────────┐  USB 3.0 ×4  ┌──────────────┐ │  SATA 22-pin
   │ RPi CM4      │◄────────────►│ VL805 xHCI  │◄────────────►│ ASM1153E ×4  │◄┼──► pigtail ──► drive ×4
   │ (eMMC, GbE)  │              │ (4 SS ports)│              │ USB→SATA     │ │  (data + 5 V + 12 V)
   └──┬───┬───┬───┘              └─────────────┘              └──────────────┘ │
      │   │   │                                                                │
      │   │   └── GPIO ×4 BAY_EN ──► per-bay 12 V / 5 V P-FET switches ────────┘
      │   └────── GPIO ×8 DIP, ×1 Start, ×1 buzzer, ×2 LED
      └────────── I2C1 ──► SSD1306 OLED, PCF85063 RTC
```

Everything except the drives lives on one 4-layer carrier board inside a printed
enclosure. Drives sit outside on a mat or rack and connect with 0.5 m
22-pin SATA (7 data + 15 power) extension cables.

## 3. Workstream 1 — Carrier board (KiCad)

### 3.1 Compute: Raspberry Pi Compute Module 4

* **Variant:** CM4004008 (no wireless, 4 GB RAM, 8 GB eMMC). eMMC avoids an SD
  card that could fall out mid-wipe; 4 GB is more than enough. Wireless is not
  wanted on a sanitization appliance. A microSD slot is still fitted so CM4 Lite
  variants work.
* **Connectors:** 2× Hirose DF40C-100DS-0.4V(51).
* **Interfaces used:** PCIe Gen2 x1 (USB 3 host), USB 2.0 (to USB-C for `rpiboot`
  eMMC flashing and as a spare host port), GbE (RJ45 magjack, for NTP, SSH and
  certificate push), I2C1, UART0 (debug header), 20 GPIO. HDMI is not populated.
* **nRPIBOOT** jumper next to the USB-C port.

### 3.2 USB topology — decision required

The CM4 exposes **one USB 2.0 port and no USB 3.0**. A VL817 hub hung from that port
would give four drives a shared 480 Mbit/s link, about 35 MB/s total, i.e. roughly
9 MB/s per drive with four running. A 4 TB single-pass overwrite would take
about five days per drive. That is not usable.

USB 3.0 on a CM4 has to come from a PCIe xHCI controller on the CM4's single
PCIe Gen2 x1 lane (the same trick the Pi 4B uses). Candidates:

| Option | Topology | Aggregate bandwidth | Chips | Notes |
|---|---|---|---|---|
| **A (recommended)** | CM4 PCIe → **VL805** → 4× ASM1153E directly | ~400 MB/s (PCIe Gen2 x1 bound) | 5 | VL805 has four SuperSpeed ports; no hub needed. Firmware-loaded by Pi bootloader as on Pi 4B; SPI-flash footprint kept as DNP fallback. |
| B | CM4 PCIe → VL805 (1 port) → **VL817** hub → 4× ASM1153E | ~400 MB/s (same bound, USB 3.0 link ≈ PCIe Gen2 x1) | 6 | As requested. Adds a chip, a crystal, and routing for no bandwidth gain. Only worth it as the building block for an **8-bay** variant (two VL817s on two VL805 ports). |
| C | CM4 USB 2.0 → VL817 → 4× ASM1153E | ~35 MB/s | 5 | Only viable if firmware Sanitize is the *only* method used (progress polling needs no bandwidth). Not recommended. |

The rest of this document assumes **Option A**, and keeps Option B as a
documented variant. The user-specified VL817 stays in the BOM as an alternate.

Bandwidth reality check for Option A: four 3.5" HDDs at 150–250 MB/s each want
~800 MB/s, so with all four bays writing they will each see ~100 MB/s. A 4 TB
drive single-pass + full verify then takes ~22 h. Firmware Sanitize runs inside
the drive and is not bandwidth-limited.

VL805 alternate: Renesas uPD720201 (also PCIe Gen2 x1 → 4× USB 3.0, stocked at
Mouser/Digi-Key, needs its own SPI firmware flash). Pin-incompatible; pick one
before layout.

### 3.3 USB→SATA bridges

* **ASMedia ASM1153E** ×4, one per bay. Chosen for reliable SCSI-ATA Translation
  (ATA PASS-THROUGH 12/16), UASP, and support for SANITIZE / SECURITY ERASE
  passthrough, which is what makes firmware wipes possible over USB.
* Each bridge has its own 25 MHz crystal, LED output (routed to a front-panel bay
  LED), and SATA AC-coupling caps.
* Alternate: ASM235CM (newer, USB 3.2 Gen2, also SAT-capable) if ASM1153E stock
  is poor. Pin-incompatible; decide before layout.
* **NVMe:** there is no native NVMe path on this board. `nvme-cli` support in the
  service is for (a) running the service on a PC, and (b) a future board revision
  that puts an ASM1184e PCIe packet switch on the CM4 lane to add an M.2 slot next
  to the VL805. USB-NVMe bridges (RTL9210 etc.) present as SCSI and cannot receive
  NVMe Sanitize; they fall back to SCSI SANITIZE or overwrite.

### 3.4 Drive connectors and pigtails

* Board side: 4× **SATA 22-pin (7+15) right-angle receptacle**, backplane style,
  along the rear edge on ~28 mm pitch.
* Pigtail: off-the-shelf **22-pin male-to-female SATA extension, 0.5 m**. No
  custom cable. The drive end plugs straight onto the drive.
* Pin 11 of the 15-pin power segment (staggered-spin-up / activity) is left
  floating so drives spin up on power, which the board controls itself (§3.6).
* Bays are numbered 1–4 left to right, and the software maps each bay to a
  fixed USB port path (§4.3), so bay numbers on the OLED match the silkscreen.

### 3.5 Power tree and budget

Input: **12 V DC**, single rail. Everything else is derived on-board.

| Rail | Source | Loads | Typical | Peak (staggered) | Peak (worst, all spin-up) |
|---|---|---|---|---|---|
| 12V_HDD | input, via per-bay switch | 4× HDD 12 V | 4×0.8 = 3.2 A | 2.0 + 3×0.8 = 4.4 A | 4×2.0 = 8.0 A |
| 5V_SYS | TPS56637 buck | CM4 (≤2.5 A), VL805 (0.3 A), 4× ASM1153E (0.4 A), UI (0.1 A) | 1.8 A | 3.3 A | 3.3 A |
| 5V_HDD | TPS56637 buck, via per-bay switch | 4× HDD 5 V | 4×0.6 = 2.4 A | 1.0 + 3×0.6 = 2.8 A | 4×1.0 = 4.0 A |
| 3V3 | AP63203 buck | bridges' IO, VL805 IO, RTC, OLED | 0.6 A | 1.0 A | 1.0 A |
| 12 V input total | | 12V_HDD + (5 V loads / 0.92 eff / 12 V) | ≈ 5.1 A | ≈ 7.2 A | ≈ 11.5 A |

Design conclusions:

1. **Staggered spin-up is mandatory**, not optional: it is the difference between
   a 7 A and an 11.5 A input. The software never enables two bays within 4 s of
   each other.
2. **Supply:** 12 V / 10 A (120 W) desktop brick.
3. **Input connector:** a standard 5.5 × 2.5 mm barrel jack is rated ~5 A and is
   *under* the 7.2 A staggered peak. The board carries **two footprints**: a
   high-current barrel jack (Kycon KLDHCX series, ≥8 A rated — verify the exact
   variant's rating in its datasheet) and a **4-pin DIN (Kycon KPJX-4S)**, which is
   what 12 V/10 A bricks normally ship with. Populate one. Decision needed (§7).
4. **Input protection:** 10 A SMD fuse, SMBJ15A TVS, P-FET reverse-polarity
   protection (a Schottky would burn ~4 W at 8 A), 2× 680 µF 25 V low-ESR bulk
   near the SATA power pins for spin-up transients.
5. **Two separate 5 V bucks** so HDD spin-up ripple stays off the CM4 rail. The
   same TPS56637 (4.5–28 V in, 6 A) is used for both to keep one part number.
6. Any 1.2 V core rails the VL805 or ASM1153E require come from small LDOs off
   3V3 per the vendor reference designs (verify against the datasheets; both parts
   are documented mainly through reference schematics).

### 3.6 Per-bay power switching (staggered spin-up)

Each bay's 12 V and 5 V are switched by a logic-level P-MOSFET (−30 V, ≥6 A,
≤30 mΩ, DFN 3×3) driven through a 2N7002 from one CM4 GPIO (`BAY_EN[n]`),
with an RC on the gate for ~5 ms soft-start so the drive's bulk caps don't trip
the upstream fuse. A 10 kΩ pull-down on each `BAY_EN` keeps all bays **off** during
boot and while the service is not running.

Per-bay 1812 PTC resettable fuses (3 A hold on 12 V, 2 A hold on 5 V) catch a
shorted drive. An alternate footprint for a TPS25982 eFuse is documented but not
in the v1 BOM.

Per-bay power control also gives the software two things it needs anyway:

* **Un-freezing** a drive whose SECURITY/SANITIZE state is frozen (power cycle the
  bay, not the whole unit).
* **Resetting** a hung bridge without disturbing the other three wipes.

Optional (DNP): INA3221 current monitors on 12V_HDD to detect spin-up completion
and drive presence electrically. v1 detects presence through USB enumeration.

### 3.7 GPIO map (BCM numbering)

| GPIO | Function | Direction | Notes |
|---|---|---|---|
| 2, 3 | I2C1 SDA/SCL | — | OLED (0x3C), RTC PCF85063 (0x51), optional INA3221 |
| 4 | START_BTN | in, pull-up | active low, panel-mount momentary; hold 3 s = abort |
| 5, 6, 12, 13 | BAY_EN 1–4 | out | active high, 10 k pull-down |
| 14, 15 | UART0 TX/RX | — | debug console header |
| 16, 17, 20, 21, 22, 23, 24, 25 | DIP 1–8 | in, pull-up | ON = low |
| 18 | BUZZER | out (PWM0) | magnetic buzzer via NPN |
| 26 | STATUS_LED | out | green/red bicolour, front panel |
| 27 | BTN_LED | out | Start button ring LED |
| 0, 1 | reserved | — | ID EEPROM per Pi convention, not populated |

Bay activity LEDs are driven directly by each ASM1153E's LED pin, not by GPIO.

### 3.8 Front-panel UI

* **OLED:** 128×64 I2C, SSD1306 (0.96") or SH1106 (1.3"), on a 4-pin header so
  either module fits. Eight text rows: header, four bay rows
  (`B1 WD40EFRX 4.0T  OVW 42% 6h12m`), a footer with mode and unit status.
  A 2.42" SSD1309 is a drop-in option for readability if the enclosure grows.
* **DIP switch:** 8-way, through-hole, reachable through an enclosure slot.
  Semantics in §4.5.
* **Start button:** 16 mm illuminated momentary, panel mount, on a 4-pin header.
* **LEDs:** power, status (bicolour), 4× bay activity, all 3 mm through-hole
  poking through the panel, or 0603 + light pipes (decide with enclosure).
* **Buzzer:** completion chirp, error pattern.

### 3.9 Other on-board

* **RTC:** PCF85063AT + CR2032. Certificates need trustworthy timestamps even
  when the unit is off-network.
* **Fan header:** 3-pin 5 V, PWM on a spare GPIO if a CM4 heatsink alone is not
  enough (CM4 at sustained 100 MB/s ×4 USB/PCIe traffic runs warm).
* **Test points** on every rail, PCIe REFCLK, and each bay's BAY_EN.

### 3.10 PCB

* **Size:** ~160 × 100 mm (four 22-pin SATA connectors set the width).
* **Stack:** 4-layer, 1.6 mm, ENIG. Sig / GND / PWR / Sig. Target the JLCPCB
  JLC04161H-7628 stackup so controlled impedance is free: 90 Ω differential for
  USB 3 SS, PCIe, and SATA pairs; 85 Ω is acceptable for PCIe. Length-match
  within a pair to ±0.15 mm; USB 2.0 pairs to 90 Ω as well.
* **Fab:** JLCPCB or PCBWay, 5 pcs. VL805 and ASM1153E are 0.4–0.5 mm QFN, and
  the DF40 connectors are 0.4 mm pitch, so use the fab's assembly service for the
  SMD side and hand-fit the through-hole connectors.
* **KiCad 9**, hierarchical sheets: `cm4`, `usb3-host`, `bridge` (×4 instances),
  `power-input`, `power-bucks`, `bay-switch` (×4 instances), `ui`, `io`.

## 4. Workstream 2 — Sanitizer service (Python)

### 4.1 Stack

* Raspberry Pi OS Lite 64-bit (Bookworm or newer), Python 3.11+.
* Package `braindrain`, run by a `systemd` unit as root (raw block access).
* Python deps: `pyudev` (device events and sysfs), `gpiod` (libgpiod v2),
  `luma.oled` (SSD1306/SH1106), `smbus2`.
* System tools driven via subprocess: `hdparm` ≥ 9.65 (ATA SANITIZE/SECURITY),
  `nvme-cli`, `sg3-utils` (`sg_sanitize`, `sg_inq`, `sg_readcap`),
  `smartmontools` (`smartctl` for identity, SMART pre-check, and post-check),
  `util-linux` (`lsblk -J`, `blockdev`).

### 4.2 Package layout

```
software/braindrain/
  __init__.py
  config.py        # paths, timings, DIP semantics table
  hal/
    gpio.py        # BAY_EN, DIP, button, buzzer, LEDs (real + simulated)
    display.py     # OLED rendering (real + terminal simulator)
    bays.py        # bay ↔ USB port-path table, power sequencing
  devices.py       # enumerate candidate drives, identity, safety filter
  policy.py        # DIP bits + media type → ordered list of methods to try
  methods/
    base.py        # Method interface: supported(), run(), progress()
    overwrite.py   # host-side passes (zeros / pattern / seeded random) + verify
    ata.py         # hdparm: SANITIZE {crypto,block,overwrite}, SECURITY ERASE
    nvme.py        # nvme-cli: sanitize, format --ses
    scsi.py        # sg_sanitize for USB-NVMe / SAS oddities
  verify.py        # full read-back, sampled read-back, canary check
  report.py        # certificate JSON, write to /var/lib/brain-drain and USB stick
  progress.py      # per-bay % and ETA (EWMA throughput)
  engine.py        # state machine: IDLE → ARMED → RUNNING → DONE/ERROR
  cli.py           # `braindrain run|status|list|simulate`
software/tests/
```

### 4.3 Device enumeration and the safety fence

The single most important property of this software: **it must never touch the
boot medium or any drive that is not in a bay.** Defence in depth:

1. A drive is a candidate only if its sysfs path passes through the USB port path
   assigned to a bay in `hal/bays.py` (e.g. `usb2/2-1/2-1.3` → bay 3) **and** the
   USB bridge VID:PID is on the allow-list (ASM1153E `174c:55aa` / `174c:1153`).
2. The device's `major:minor` must not be, or be a parent of, anything mounted or
   holding the root/boot filesystem (checked via `findmnt` and `/proc/swaps`).
3. Removable-media and zero-capacity devices are ignored.
4. Every method opens the target with `O_EXCL`.
5. A dry-run DIP setting (§4.5) exercises the whole pipeline without writes.

Presence is detected by powering bays up staggered (4 s apart) and waiting for a
block device with capacity > 0 to appear behind the bay's port path.

### 4.4 Wipe methods and NIST SP 800-88 Rev. 2 mapping

Rev. 2 keeps the Clear / Purge / Destroy tiers, drops the idea that multi-pass
overwrites add anything on modern media, and pushes toward drive-native sanitize
commands (Sanitize, Crypto Erase) for Purge. Verification, full or sampled, is
part of every Clear/Purge. The table below is the intended mapping; it must be
checked line by line against the published Rev. 2 text before the first release.

| Media | Clear | Purge |
|---|---|---|
| Magnetic HDD (ATA) | 1 pass host overwrite, fixed pattern, **full verify** | ATA `SANITIZE OVERWRITE EXT` → fallback `SECURITY ERASE UNIT` (enhanced) → fallback host overwrite |
| SATA SSD (ATA) | 1 pass host overwrite (may miss over-provisioned blocks; flagged in report) | ATA `SANITIZE CRYPTO SCRAMBLE` (if supported) then `SANITIZE BLOCK ERASE` → fallback `SECURITY ERASE UNIT` enhanced |
| NVMe (native only) | `nvme format --ses=1` | `nvme sanitize --sanact=crypto-erase` or `block-erase` |
| Unknown / USB-NVMe / SAS | host overwrite | SCSI `SANITIZE` via `sg_sanitize` → fallback overwrite |

Method implementations:

* **Overwrite:** `O_DIRECT`, 8 MiB blocks, aligned to physical sector size; pattern
  zeros by default, seeded ChaCha20 keystream for "random" so verification can
  regenerate the stream instead of storing it. Throughput and ETA from an EWMA of
  the last 30 s. Bad sectors are logged and the pass continues; any unwritable LBA
  fails the certificate.
* **Firmware (ATA):** `hdparm --sanitize-*` then poll `--sanitize-status` for
  percentage. Frozen state → power-cycle the bay via `BAY_EN` and retry once.
  Known risk: a USB bridge may drop the device mid-Security-Erase because the
  drive stays busy longer than the SCSI timeout; the drive keeps erasing, so the
  service waits, re-enumerates, and checks security status rather than failing.
  Sanitize is preferred over Security Erase precisely because it is asynchronous
  with a status query.
* **Verify:** full read-back compare for host overwrite (default) or sampled
  (first/last 1 GiB plus 64 random 16 MiB windows) when DIP 5 is on. For firmware
  methods the "canary" check applies: before the command, write a known marker at
  eight LBAs; after, read them back and confirm the marker is gone (crypto erase
  yields noise, block erase yields zeros/FFs; both pass).
* **Legacy multi-pass:** 3-pass (0x00, 0xFF, random + verify) and 7-pass
  (DoD 5220.22-M ECE-style) kept for customers who insist. The certificate labels
  these as *exceeding* Clear, not as Purge.

### 4.5 DIP switch semantics (v0 proposal)

| DIP | ON | OFF (default) |
|---|---|---|
| 1–3 | mode index, see below | 000 = `auto` |
| 4 | overwrite pattern = seeded random | zeros |
| 5 | sampled verify | full verify |
| 6 | auto-start when all detected bays are ready | wait for Start |
| 7 | power bays down when finished | leave powered for removal check |
| 8 | **maintenance**: SSH + serial shell, never wipe | normal |

Mode index (DIP 1–3, ON = 1): `000 auto` (HDD → Clear+verify, SSD → Purge),
`001 purge`, `010 clear`, `011 legacy-3pass`, `100 legacy-7pass`,
`101 crypto-erase-only`, `110 reserved`, `111 dry-run`.

DIP is read when the Start button is pressed, and shown on the OLED footer.

### 4.6 State machine and UX

```
BOOT ─► IDLE (bays off) ─► [Start] ─► DETECT (stagger bays on, enumerate, SMART pre-check)
     ─► ARMED (OLED shows drives + method; hold Start 3 s to begin, or DIP6 auto)
     ─► RUNNING (per-bay worker threads; one method chain per bay)
     ─► DONE | ERROR (buzzer, status LED, certificates written)
     ─► [Start] ─► IDLE
```

Bays are independent: a failed drive in bay 2 does not stop bays 1, 3, 4.
Holding Start 3 s while RUNNING aborts all bays and marks their certificates
`aborted`. Power loss mid-wipe leaves a `state.json` so the next boot reports the
interrupted drives as *not sanitized*.

### 4.7 Certificate

One JSON file per drive per run, e.g.
`/var/lib/brain-drain/reports/2026-09-21T14-02-11Z_WD-WCC4E1234567.json`:
unit ID, firmware version, bay, drive model/serial/firmware/capacity, media
type detection evidence, method chain attempted and the one that succeeded,
NIST tier claimed (Clear/Purge/none), verification type and result, start/end
timestamps (RTC), throughput, SMART pre/post summary, operator DIP settings.
Also copied to any FAT-formatted USB stick present at completion and, if
configured, POSTed to an HTTP endpoint.

### 4.8 Simulation and tests

`BRAIN_DRAIN_SIM=1` swaps the HAL for fakes: bays backed by loop devices or
sparse files, DIP/button from a small TUI, OLED rendered to the terminal. This is
how the engine gets developed and tested on a workstation before the board
exists. `pytest` covers policy selection, safety fence, progress math, report
schema, and each method against fake `hdparm`/`nvme` subprocess outputs.

## 5. Workstream 3 — Enclosure

* **Tool:** OpenSCAD, everything driven from `enclosure/params.scad`. Connector
  positions are generated from the KiCad PCB by a small script
  (`enclosure/tools/kicad_to_scad.py`) so the shell tracks the board.
* **Form:** two-part shell, bottom tray + top lid, board on M2.5 heat-set
  inserts. Rear wall: 4× SATA 22-pin windows, DC input, RJ45, USB-C, UART slot.
  Top: OLED window with a recess for the module, 8-way DIP slot, 16 mm button
  hole, 6× LED holes. Sides: vents. Optional 40 mm fan grille over the CM4.
* **Print:** PETG or ASA, 0.2 mm layers, no supports required by design
  (chamfered overhangs, lid printed upside down).
* **Later:** a matching 4-slot drive rack that keeps the pigtails tidy.

## 6. Cross-cutting

* **Safety fence** (§4.3) is reviewed on every change to `devices.py` or `bays.py`.
* **Thermal:** CM4 heatsink mandatory; fan optional; ASM1153E and bucks fine.
* **Compliance record:** the certificate schema is versioned; the report states
  which 800-88 tier was achieved, and says so honestly when only overwrite was
  possible on an SSD.
* **Firmware for VL805:** the Pi bootloader loads it as on the Pi 4B. If that turns
  out not to work on this carrier, populate the SPI flash footprint.

## 7. Open decisions

See `docs/DECISIONS.md`. Headline items: USB topology (A vs B), input connector
(barrel vs DIN), bridge chip (ASM1153E vs ASM235CM), OLED size, CM4 variant, and
what to build first.

## 8. Suggested build order

1. **Software in simulation** — the engine, policy, safety fence, and methods can
   be built and tested now on any Linux box with a USB-SATA dock, and are the
   riskiest part to get right. Hardware questions (bridge SAT behaviour under
   Sanitize, USB bridge timeouts) get answered on a bench dock before the board
   is committed.
2. **Carrier board schematic** — while the software matures. Layout after the
   §7 decisions.
3. **Enclosure** — last, once the board outline and connector positions are frozen.
