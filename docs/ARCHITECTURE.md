# brain-drain — Architecture

Standalone, headless, four-bay disk sanitizer built on a Raspberry Pi Compute Module 5. Set the wipe policy on a DIP switch,
plug a drive into any bay and it is wiped as soon as it is ready; the OLED
shows per-bay progress; unplugging a drive aborts it; each finished drive
gets a sanitization certificate. No buttons, no menus. Wipe methods follow
NIST SP 800-88 Rev. 2.

Status: **v0 design, nothing built yet.** This document is the source of truth for
all three workstreams; change it before changing the hardware.

---

## 1. Scope

| In scope | Out of scope (for v1) |
|---|---|
| 4× SATA HDD/SSD (3.5" and 2.5") over USB-SATA bridges | Direct NVMe bays (see §3.3 for the path to add one) |
| NIST 800-88 Rev. 2 Clear and Purge for ATA media | Physical destruction, degaussing |
| Overwrite (host-side) and firmware Sanitize / Security Erase | Wiping the CM5's own boot medium (explicitly forbidden) |
| Per-drive progress/ETA on a small OLED | Touchscreen, web UI (a read-only status page is a cheap later add) |
| JSON certificate per drive, optional network push | Signed/PKI certificates |
| Staggered spin-up, per-bay power control | Hot-swap backplane / drive caddies |

## 2. System overview

```
                 12 V DC in ──► protection ──┬──► 5V_SYS buck ──► CM5, hubs, bridges, UI
                                            ├──► 5V_HDD buck ──► bay switches ──┐
                                            ├──► 3V3 buck    ──► hubs, bridges  │
                                            └──► 12V_HDD     ──► bay switches ──┤
                                                                                │
   ┌──────────────┐  USB 3.0 #0  ┌─────────────┐  USB 3.0 ×2  ┌──────────────┐ │  SATA 22-pin
   │ RPi CM5      │◄────────────►│ USB5744  A  │◄────────────►│ ASM1153E ×2  │◄┼──► pigtail ──► bays 1, 2
   │ (eMMC/Lite,  │  USB 3.0 #1  ├─────────────┤  USB 3.0 ×2  ├──────────────┤ │  (data + 5 V + 12 V)
   │  GbE, RTC)   │◄────────────►│ USB5744  B  │◄────────────►│ ASM1153E ×2  │◄┼──► pigtail ──► bays 3, 4
   └──┬───┬───┬─┬─┘              └─────────────┘              └──────────────┘ │
      │   │   │ └── PCIe Gen3 x1 ──► (free; optional M.2 NVMe bay, see D10)    │
      │   │   └── GPIO ×4 BAY_EN ──► per-bay 12 V / 5 V P-FET switches ────────┘
      │   └────── GPIO ×8 DIP, ×1 LED
      └────────── I2C1 ──► SSD1306 OLED
```

Everything except the drives lives on one 4-layer carrier board inside a printed
box about 157 × 105 × 39 mm (C21). The box, its 12 V brick and four cables travel
in a backpack; drives lie loose on the bench and connect with 0.5 m 22-pin SATA
(7 data + 15 power) extension cables. There is no rack, dock or chassis.

## 3. Workstream 1 — Carrier board (KiCad)

### 3.1 Compute: Raspberry Pi Compute Module 5

* **Variant:** CM5002016 (no wireless, 2 GB RAM, 16 GB eMMC) for production
  units. The service needs well under 1 GB, so 2 GB is the right size. Wireless
  is not wanted on a sanitization appliance.
* **Lite works on the same carrier.** A microSD socket is fitted and wired to the
  CM5's SD pins; Lite variants (CM5002000) boot from it, eMMC variants ignore it.
  Use Lite for development boards and eMMC for units that run 20-hour jobs.
  The boot order is pinned to eMMC/SD only, never USB or NVMe, so a drive in a
  bay can never become the boot medium.
* **Connectors:** 2× Hirose DF40C-100DS-0.4V(51), same footprint as CM4.
* **Interfaces used:** 2× native USB 3.0 (RP1) for the drive hubs, USB 2.0 (to
  USB-C for `rpiboot` eMMC flashing and as a spare host port), GbE (RJ45 magjack,
  for NTP, SSH and certificate push), I2C1, UART0 (debug header), 20 GPIO,
  on-module RTC with backup-battery pin. PCIe Gen3 x1 is left free (see D10).
  HDMI is not populated.
* **CM4 fallback:** the carrier is electrically CM4-compatible except that a CM4
  has no USB 3 on those pins, so bays would not enumerate. Do not plan on it.
* **Thermal:** CM5 runs hotter than CM4. The official CM5 cooler or an
  equivalent heatsink plus the fan header is required, not optional.
* **nRPIBOOT** jumper next to the USB-C port.

### 3.2 USB topology (decision D1, closed)

The CM5 has **two native USB 3.0 ports** (5 Gbit/s each, via the RP1 I/O
controller) plus a PCIe Gen3 x1 lane. The CM4 had neither USB 3 port, which is
why an earlier draft needed a PCIe xHCI controller; that is gone.

Chosen topology: **one Microchip USB5744 hub per native USB 3.0 port, two
ASM1153E bridges per hub** (decisions C11, C12). The USB5744 was chosen over the
originally specified VL817 because it has the same 4-port 5 Gbit/s spec and a
fully public datasheet; the VL817's is only available on request.

| Link | Practical rate | Shared by |
|---|---|---|
| CM5 USB 3.0 port → USB5744 | ~400 MB/s | two bays |
| USB5744 → ASM1153E, per port | ~400 MB/s | one bay |
| RP1 upstream to the SoC (PCIe Gen2 x4) | ~1.4 GB/s | both ports, Ethernet |
| ASM1153E → drive (SATA III) | ~550 MB/s | one bay |
| A 3.5" HDD | 100–200 MB/s, ~150 average | — |

Two HDDs per hub want at most ~400 MB/s together, so **all four bays run at
native drive speed** in host-overwrite mode. Aggregate ~800 MB/s.

Why not the alternatives:

* *Native ports direct to bays 1–2 plus a VL805 on PCIe for bays 3–4:* more
  bandwidth on paper (~1.1 GB/s) but never used by HDDs, adds a PCIe device that
  needs firmware loading and Gen2 routing, and spends the PCIe lane.
* *One hub on one port for all four bays:* ~100 MB/s per bay under load, and
  the second native port idle. Cheaper by one hub, slower by ~1.5×.

Each USB5744 has its own 25 MHz crystal and needs 3.3 V plus an external
1.2 V core rail (one shared LDO serves both hubs). Its per-port power-enable and
overcurrent pins are left unused since bay power is switched on the drive rails
(§3.6), not the USB side. Bridges are always powered. Configuration is by strap
pins; no SPI ROM.

### 3.3 USB→SATA bridges

* **ASMedia ASM1153E** ×4, one per bay. Chosen for reliable SCSI-ATA Translation
  (ATA PASS-THROUGH 12/16), UASP, and support for SANITIZE / SECURITY ERASE
  passthrough, which is what makes firmware wipes possible over USB.
* Each bridge has its own 25 MHz crystal, LED output (routed to a front-panel bay
  LED), and SATA AC-coupling caps.
* Alternate: ASM235CM (newer, USB 3.2 Gen2, also SAT-capable) if ASM1153E stock
  is poor. Pin-incompatible; decide before layout.
* **NVMe, bay 5 (decision C15, populated in v1):** the CM5's PCIe Gen3 x1
  lane feeds an M.2 M-key slot with its own switched 3V3 rail, giving native
  NVMe wipes (`nvme sanitize`, `nvme format --ses`). PCIe is not hot-plug: the
  service keeps the slot unpowered while idle, and a job is started by closing
  the access door (a microswitch on a spare GPIO), which powers the slot,
  rescans the PCIe bus, and treats the device that appears as bay 5. Opening the
  door removes power and aborts. The boot order excludes NVMe. M.2 SATA (B+M
  key) drives will not work in this slot and are reported as such.
  USB-NVMe bridges (RTL9210 etc.) present as SCSI and cannot receive NVMe
  Sanitize; they fall back to SCSI SANITIZE or overwrite.

### 3.4 Drive connectors and pigtails

* Board side: 4× **SATA 22-pin (7+15) right-angle receptacle**, backplane style,
  along the rear edge on 28.9 mm pitch (pad span 27.94 mm plus clearance).
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
| 5V_SYS | TPS56637 buck | CM5 (≤3.0 A), 2× USB5744 (0.4 A), 4× ASM1153E (0.4 A), UI (0.1 A) | 2.0 A | 3.8 A | 3.8 A |
| 5V_HDD | TPS56637 buck, via per-bay switch | 4× HDD 5 V | 4×0.6 = 2.4 A | 1.0 + 3×0.6 = 2.8 A | 4×1.0 = 4.0 A |
| 3V3 | AP63203 buck | hubs, bridges' IO, OLED | 0.6 A | 1.0 A | 1.0 A |
| 12 V input total | | 12V_HDD + (5 V loads / 0.92 eff / 12 V) | ≈ 5.3 A | ≈ 7.4 A | ≈ 11.5 A |

Design conclusions:

1. **Staggered spin-up is mandatory**, not optional: it is the difference between
   a 7 A and an 11.5 A input. The software never enables two bays within 4 s of
   each other.
2. **Supply:** 12 V / 10 A (120 W) desktop brick.
3. **Input connector (C13):** 4-pin DIN, Kycon KPJX-4S-S, 7.5 A per pin with
   two pins per polarity. Barrel jacks, including Kycon's "high-current" KLDHCX,
   are rated 5 A and were dropped. The brick is chosen before layout and the
   DIN pins are wired to match it, because DIN pin assignments differ between
   brick vendors.
4. **Input protection:** 10 A SMD fuse, SMBJ15A TVS, P-FET reverse-polarity
   protection (a Schottky would burn ~4 W at 8 A), 2× 680 µF 25 V low-ESR bulk
   near the SATA power pins for spin-up transients.
5. **Two separate 5 V bucks** so HDD spin-up ripple stays off the CM5 rail. The
   same TPS56637 (4.5–28 V in, 6 A) is used for both to keep one part number.
   Raspberry Pi specifies a 5 A-capable 5 V supply for CM5; 5V_SYS carries the
   CM5 plus ~0.8 A of hubs, bridges and UI, so the 6 A buck has ~1.4 A margin.
   If the M.2 bay (D10) is populated, move it to 5V_HDD.
6. The USB5744 1.2 V core rail and any ASM1153E core rail come from small LDOs off
   3V3 per the vendor reference designs (verify against the datasheets; both parts
   are documented mainly through reference schematics).

### 3.6 Per-bay power switching (staggered spin-up)

Each bay's 12 V and 5 V are switched by a logic-level P-MOSFET (−30 V, ≥6 A,
≤30 mΩ, DFN 3×3) driven through a 2N7002 from one CM5 GPIO (`BAY_EN[n]`),
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
| 2, 3 | I2C1 SDA/SCL | — | OLED (0x3C), optional INA3221, optional PCF85063 (0x51) |
| 4 | M2_DOOR | in, pull-up | bay 5 access-door microswitch, closed = low |
| 5, 6, 12, 13 | BAY_EN 1–4 | out | active high, 10 k pull-down |
| 14, 15 | UART0 TX/RX | — | debug console header |
| 16, 17, 20, 21, 22, 23, 24, 25 | DIP 1–8 | in, pull-up | ON = low |
| 18 | (free) | — | buzzer removed (C23) |
| 26 | STATUS_LED | out | green/red bicolour, front panel |
| 27 | M2_PWR_EN | out | 3V3_M2 load switch enable, 10 k pull-down |
| 0, 1 | reserved | — | ID EEPROM per Pi convention, not populated |

Bay activity LEDs are driven directly by each ASM1153E's LED pin, not by GPIO.

### 3.8 Front-panel UI

* **OLED:** 128×64 I2C, SSD1306 (0.96") or SH1106 (1.3"), on a 4-pin header so
  either module fits. Eight text rows: header, four bay rows
  (`B1 WD40EFRX 4.0T  OVW 42% 6h12m`), a footer with mode and unit status.
  A 2.42" SSD1309 is a drop-in option for readability if the enclosure grows.
* **DIP switch:** 8-way, through-hole, reachable through an enclosure slot.
  Semantics in §4.5. This is the only control on the unit.
* **LEDs (C14):** power, status (bicolour), 4× SATA bay activity, 1× M.2 bay
  activity, all 3 mm through-hole standing through 3.2 mm holes in the lid.
* **Buzzer:** completion chirp, error pattern.

### 3.9 Other on-board

* **RTC:** the CM5 has an on-module RTC; the carrier provides a CR2032 holder on
  the CM5 battery pin. Certificates need trustworthy timestamps off-network. A
  PCF85063AT footprint stays on the I2C bus, unpopulated, as a fallback.
* **Fan header:** 4-pin 5 V PWM (Pi fan pinout), driven from the CM5 fan
  control. A fan is expected on CM5 during 20-hour jobs.
* **M.2 M-key slot, bay 5 (C15):** PCIe Gen3 x1 from the CM5 (REFCLK pair,
  PERST#, CLKREQ#, PCIE_PWR_EN), 3V3_M2 from a dedicated AP63203 buck through
  a TPS22965 load switch enabled by GPIO, door microswitch input, activity LED
  from the slot's LED pin (via a transistor, it is an open-drain sink).
* **Test points** on every rail and each bay's BAY_EN.

### 3.10 PCB

* **Size:** 150 × 112 mm (v3, decision D7 option B, 2026-09-23; v2 was
  136 × 100, C19 was 180 × 110). Rear edge: the four SATA receptacles only.
  Right wall: USB-C rpiboot, microSD, DIN 12 V. Left edge: the CM5 wireless
  module's antenna edge (the short edge with mounting hole MH1) sits flush with
  the board edge, with an 8 mm copper-free strip on all four layers under it and
  no metal part within 10 mm (CM5 datasheet 4.1.2). Rows from the rear: the
  receptacles; behind each one its power-switch block directly behind the power
  pads and the bridge QFN behind the data pads, the bridge passives in the band
  below, every QFN with at least 2.5 mm of free board around it. Then the CM5 in
  landscape at the left (x 0–55, y 39–79). Its USB 3 and PCIe pins are on the
  connector row nearest the front, so the two hubs sit in the front-left corner
  right under them, and the M.2 socket is front-right with the 2280 module lying
  toward the middle (its switch and 0402/0603 passives sit under the SSD, under
  1.5 mm tall). Buck and input column right of the CM5, DIP switch and fan header
  in the right column, lid microswitch rear-right. The CR2032 holder and the two
  service headers are on the bottom side under the CM5, inside the 6 mm standoff
  height. Placement is generated (`gen_pcb.py`) and checked for outline and
  courtyard clashes (`check_place.py`).
* **Stack:** 4-layer, 1.6 mm, ENIG. Sig / GND / PWR / Sig. Target the JLCPCB
  JLC04161H-7628 stackup so controlled impedance is free: 90 Ω differential for
  USB 3 SS and SATA pairs, 85 Ω for the PCIe Gen3 pair to the M.2 slot. Length-match
  within a pair to ±0.15 mm; USB 2.0 pairs to 90 Ω as well. Design rules are
  the CM5IO reference's: 0.13 mm tracks, 0.125 mm clearance, 0.45/0.2 mm vias,
  because nothing coarser escapes the 0.4 mm-pitch CM5 connector. Gen3 needs short,
  clean routing from the DF40 to the M.2 slot; keep them adjacent.
* **Fab:** JLCPCB or PCBWay, 5 pcs. USB5744 and ASM1153E are 0.4–0.5 mm QFN, and
  the DF40 connectors are 0.4 mm pitch, so use the fab's assembly service for the
  SMD side and hand-fit the through-hole connectors.
* **KiCad 9**, hierarchical sheets: `cm5`, `usb3-hub` (×2 instances), `bridge`
  (×4 instances), `power-input`, `power-bucks`, `bay-switch` (×4 instances),
  `ui`, `io`, `m2-nvme`.

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
    gpio.py        # BAY_EN, DIP, LEDs (real + simulated)
  wifi.py          # access point / station via nmcli, ephemeral key, resets
  webui.py         # the phone page (stdlib HTTP)
  qr.py            # Wi-Fi QR matrix for the OLED
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

Bays are powered at boot, staggered 4 s apart, and stay powered. A drive plugged
into a live pigtail is detected by the bridge (SATA connectors are hot-plug by
design), a block device with capacity > 0 appears behind the bay's port path,
and udev delivers an add event. Removal delivers a remove event, which aborts
any running job in that bay. There is no confirmation step beyond a short
grace countdown (default 5 s, shown on the OLED) during which pulling the drive
back out cancels cleanly.

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
| 6 | reserved | |
| 7 | reserved | |
| 8 | **maintenance**: SSH + serial shell, never wipe | normal |

Mode index (DIP 1–3, ON = 1): `000 auto` (HDD → Clear+verify, SSD → Purge),
`001 purge`, `010 clear`, `011 legacy-3pass`, `100 legacy-7pass`,
`101 crypto-erase-only`, `110 service (never wipes; Wi-Fi reset at boot, factory reset with DIP 8)`, `111 dry-run`.

DIP is read at boot and again each time a drive is detected, and the decoded
mode is shown on the OLED footer.

### 4.6 State machine and UX

Per bay, independently:

```
IDLE ─(drive add)─► DETECTED (identity, SMART pre-check, grace countdown)
     ─► RUNNING (one worker thread: method chain, then verify)
     ─► DONE | ERROR (LED, certificate written; drive spun down)
     ─(drive remove, from any state)─► IDLE
```

Bay 5 (the M.2 slot) adds a slot state in front of this: the slot is unpowered
until its door switch reads closed and PEDET reads PCIe; the service then
powers the slot, waits one second, rescans the PCIe bus, and the NVMe device
that appears enters the same IDLE → DETECTED → RUNNING flow as a USB bay. If
nothing enumerates within ten seconds the slot is powered off and latched until
the door is opened again. Opening the door at any point aborts the job,
detaches the PCIe device, and cuts slot power. A SATA M.2 module (PEDET low) is
refused with a message on the OLED.

A remove event while RUNNING cancels the worker and writes an `aborted`
certificate. A drive that re-enumerates in a DONE bay with the same serial
within 30 s (a bridge glitch) stays DONE rather than being wiped again. Power
loss mid-wipe leaves a `state.json` so the next boot writes `interrupted`
certificates for the drives that were running.

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
sparse files, DIP from a file you edit, OLED rendered to the terminal. This is
how the engine gets developed and tested on a workstation before the board
exists. `pytest` covers policy selection, safety fence, progress math, report
schema, and each method against fake `hdparm`/`nvme` subprocess outputs.

## 5. Workstream 3 — Enclosure

* **Tool:** OpenSCAD, everything driven from `enclosure/params.scad`. Connector
  positions are generated from the KiCad PCB by a small script
  (`enclosure/tools/kicad_to_scad.py`) so the shell tracks the board.
* **Form (C21–C23):** a box about 157 × 119 × 32 mm, bottom tray + a lid hinged
  along the rear top edge (filament pin) with a snap latch at the front, so it
  pops open for the M.2 SSD; a lid microswitch is the bay-5 "door". Board on
  M2.5 heat-set inserts. Rear wall: 4× SATA 22-pin windows (the drive cables).
  Right wall: DC input, USB-C, microSD. Left wall (antenna side) and front:
  vent slots, no metal. Lid: OLED window with a recess for the module (on a
  4-wire lead, over the SSD), 8-way DIP slot, 8× LED holes, convection grille
  over the passive CM5 cooler. Floor: feet pockets. No button: the DIP switch is
  the only control. Nothing carries the drives; they lie on the bench.
* **Print:** PETG or ASA, 0.2 mm layers, no supports required by design
  (chamfered overhangs, lid printed upside down).
* **Refinements (`enclosure/refinements.scad`):** an OLED bezel that clamps the
  module under the lid window, rubber-feet pockets. Renders of the parts, of the
  unit on the bench with four loose drives, and of the lid open in
  `enclosure/renders/`.

## 6. Cross-cutting

* **Safety fence** (§4.3) is reviewed on every change to `devices.py` or `bays.py`.
* **Thermal:** passive CM5 cooler (C23); the workload is I/O bound. The fan
  header stays for a 5 V PWM fan under the lid grille if a summer bench shows
  throttling. ASM1153E, hubs and bucks are fine.
* **Wireless and the phone page (C22):** the CM5 wireless variant runs an
  access point (`nmcli` hotspot, 10.42.0.1/24) with SSID `brain-drain-<4 hex>`
  and an 8-character key made fresh at every boot. Idle, the OLED shows a Wi-Fi
  QR code (`WIFI:T:WPA;S:…;P:…;;`) plus the key and address; running, the key
  and address take the bottom rows. The page (`webui.py`, standard library
  HTTP on port 80) serves status, certificates (single or zip), the log tail,
  and two actions that need the key: join a network (saved to
  `/var/lib/brain-drain/wifi.json`, joined at every boot, falls back to the
  access point if it fails) and reset (Wi-Fi: forget the network and rotate the
  key; factory: also delete certificates and state). Without a network, DIP
  mode 110 at boot does the Wi-Fi reset, and 110 with DIP 8 the factory reset;
  `braindrain wifi-reset [--factory]` does the same over SSH. The key is the
  only authorisation: reading the screen is the permission.
* **Compliance record:** the certificate schema is versioned; the report states
  which 800-88 tier was achieved, and says so honestly when only overwrite was
  possible on an SSD.
* **Boot order:** the CM5 EEPROM config pins boot to eMMC/SD only. USB and NVMe
  boot are disabled so a drive in a bay can never be booted from or mistaken for
  the root device.

## 7. Open decisions

See `docs/DECISIONS.md`. Closed: CM5, USB topology, module size, hub, bridge,
input connector, LEDs, M.2 bay. Still open: OLED size (D5).

## 8. Throughput expectations and build order

With four bays at native drive speed (§3.2), a 4 TB HDD single-pass overwrite
takes ~7.5 h and a full read-back verify another ~7.5 h, and **four such drives
in parallel take the same ~15 h**, not longer. Firmware Sanitize runs inside the
drive at a similar rate with no bus load. SATA SSDs overwrite at ~400 MB/s per
bay (the USB port limit); crypto scramble takes seconds.

1. **Software in simulation** — the engine, policy, safety fence, and methods can
   be built and tested now on any Linux box with a USB-SATA dock, and are the
   riskiest part to get right. Hardware questions (bridge SAT behaviour under
   Sanitize, USB bridge timeouts) get answered on a bench dock before the board
   is committed. A Pi 5 plus two USB-SATA docks is a near-exact software
   test bed for this topology.
2. **Carrier board schematic** — while the software matures. Layout after the
   §7 decisions.
3. **Enclosure** — last, once the board outline and connector positions are frozen.
