# brain-drain: architecture

Standalone, headless disk sanitizer built on a Raspberry Pi Compute Module 5. A brain board carries the compute, two USB 3
hubs, eight bay slots, an M.2 socket and the user interface; a small bay card plugs into a slot for each SATA drive (four cards
in version 1, up to eight). Set the wipe policy on a DIP switch, plug a drive into a bay and it is wiped as soon as it is
ready; the OLED shows per-bay progress; unplugging a drive aborts it; each finished drive gets a sanitization certificate.
A Wi-Fi access point with a QR code on the OLED gives a phone the status page, the certificates and the network setup.
No buttons, no menus. Wipe methods follow NIST SP 800-88 Rev. 2.

Status: **design complete enough for layout review, nothing fabricated.** Both boards are routed with 0 DRC errors in KiCad
(see [STATUS.md](STATUS.md) and [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md) for the caveats). This document is the source of truth
for intent; change it before changing the hardware. The hardware sources are generated (`hardware/tools/`), never hand-edited.

![system](img/renders/system-iso.png)

---

## 1. Scope

| In scope | Out of scope (for v1) |
|---|---|
| Up to eight SATA HDD/SSD bays (3.5" and 2.5") on plug-in bay cards, four cards fitted | Physical destruction, degaussing |
| One M.2 NVMe bay (bay 9), PCIe Gen3 x1, under the lid | Wiping the CM5's own boot medium (explicitly forbidden) |
| NIST 800-88 Rev. 2 Clear and Purge for ATA and NVMe media | Signed / PKI certificates |
| Overwrite (host-side) and firmware Sanitize / Security Erase | Ethernet, buzzer, fan (header only), touchscreen |
| Per-drive progress and ETA on a 128 x 64 OLED | Hot-swap backplane, drive caddies, a rack |
| Wi-Fi access point, QR code, phone page with certificates and network setup | Cloud services |
| JSON certificate per drive, optional push | Drive power beyond 120 W with four cards (see 3.5) |
| Staggered spin-up, per-bay power control | |

## 2. System overview

```
   12 V brick ──DIN──► fuse, TVS, reverse-polarity FET ──┬─► U20 buck 5V_SYS ──► CM5, hubs, OLED, DIP
                                                           ├─► U21 buck 5V_HDD ──► slots (5 V per bay)
                                                           ├─► U22 buck 3V3    ──► hubs, IO, U3 (1.2 V LDO for the hubs)
                                                           ├─► U51 buck 3V3_M2 ─► U50 switch ─► M.2 socket
                                                           └─► +12V ────────────► slots (12 V per bay)

   Raspberry Pi CM5 (wireless, 2 GB / 16 GB eMMC)
      ├── USB 3.0 port 0 ──► U1 USB5744 hub A ── 4 downstream ports ──► slots 1-4 ┐
      ├── USB 3.0 port 1 ──► U2 USB5744 hub B ── 4 downstream ports ──► slots 5-8 ┤  per slot (PCIe x1-style socket,
      ├── PCIe Gen3 x1 ───► J50 M.2 M-key socket (bay 9, SSD lies under the lid)   │   custom pinout): USB 3 + USB 2 pairs,
      ├── GPIO BAY_EN 1-8 ─► slot pin B5 ─► bay-card power switch                  │   12 V, 5 V, GND, BAY_EN, LED_K
      ├── GPIO DIP x8, status LED, M2_DOOR, M2_PWR_EN                              ┘
      ├── I2C1 ──► OLED (SSD1306 / SH1106), Wi-Fi AP + phone page (nmcli, QR on the OLED)
      └── USB 2.0 ──► USB-C (rpiboot, spare host), microSD (CM5 Lite boot)

   Bay card (one per drive):  slot fingers ─► ASM1153E USB 3 to SATA bridge ─► SATA 22-pin receptacle ─► 0.5 m cable ─► drive
                              slot 12 V / 5 V ─► two P-FET switches + PTC fuses, enabled by BAY_EN ─► receptacle power pins
```

The brain board (six layers, 150 x 122 mm) and the bay cards (four layers, 45 x 46 mm) sit in a printed box about
157 x 145 x 62 mm. The box, its 12 V brick and the 22-pin cables travel in a backpack; the drives lie loose on the bench and
connect with off-the-shelf 0.5 m SATA extension cables that rise through windows in the lid. There is no rack, dock or chassis.

![electronics](img/renders/electronics-iso.png)

## 3. Workstream 1: the boards (KiCad)

### 3.1 Compute: Raspberry Pi Compute Module 5

* **Variant:** CM5 with wireless, 2 GB RAM, 16 GB eMMC (SKU CM5102016; the schematic's value field still reads CM5002016 and is
  corrected at the next regeneration, confirm the SKU when ordering). The service needs well under 1 GB.
* **Lite works on the same board.** A microSD socket is wired to the CM5's SD pins; Lite variants boot from it, eMMC variants
  ignore it. The boot order is pinned to eMMC / SD only, never USB or NVMe, so a drive in a bay can never become the boot medium.
* **Connectors:** 2 x Hirose DF40C-100DS-0.4V(51), 0.4 mm pitch, on the brain's right edge. The wireless module's PCB antenna is
  on the short edge that carries mounting hole MH1; that edge sits on the board's right edge with an 8 mm copper-free strip on
  every layer and no metal within 10 mm (CM5 datasheet 4.1.2). The rule area `keepout_CM5_antenna` enforces it.
* **Interfaces used:** two native USB 3.0 ports (from RP1) for the hubs, USB 2.0 to the USB-C port, PCIe Gen3 x1 to the M.2 socket,
  I2C1, UART0 (debug header), 20 GPIO, SD, the on-module RTC (CR2032 holder on the battery pin). Ethernet and HDMI are not used.
* **Thermal:** a passive CM5 cooler under a convection grille in the lid; a 4-pin fan header is kept for a summer bench (C23).
* **nRPIBOOT** jumper (J6) and a UART header (J7) sit on the bottom side under the CM5.

### 3.2 USB topology (decision D1, closed; C11, C24)

One Microchip **USB5744** hub per native USB 3.0 port. Each hub has four downstream ports and all four are used:
hub A (U1) feeds slots 1-4, hub B (U2) slots 5-8. Each USB5744 has its own 25 MHz crystal and needs 3.3 V plus an external 1.2 V
core rail (one AP2112K-1.2 LDO, U3, serves both). Port power enables and overcurrent pins are unused: bay power is switched on the
drive rails, on the card. Configuration is by strap pins, no SPI ROM.

| Link | Practical rate | Shared by |
|---|---|---|
| CM5 USB 3.0 port to hub | about 400 MB/s | up to four bays |
| Hub port to bridge (ASM1153E on the card) | about 400 MB/s | one bay |
| ASM1153E to drive (SATA III) | about 550 MB/s | one bay |
| A 3.5" HDD | 100-200 MB/s, about 150 average | |

Four drives on **one** hub share about 400 MB/s, roughly 100 MB/s each, below a modern HDD's speed. **Populate slots 1, 2, 5 and 6**
instead of 1-4 to give each pair of drives its own 5 Gb/s link; the software identifies a bay by its USB port path (`config.py`),
so nothing else changes. With eight bays busy every drive sees about 100 MB/s.

### 3.3 The bay card (C24, C27)

One 45 x 46 mm four-layer board per bay, one design for every slot:

* **ASM1153E** (ASMedia, QFN-48) USB 3.0 to SATA 6G bridge with SAT passthrough, which makes SANITIZE / SECURITY ERASE possible over USB.
  30 MHz crystal (default strap, no strap resistors), 4.7 uH core inductor, SATA AC-coupling caps. ASM1153E runs from 5 V alone.
* **Power switch:** two AON7403 P-MOSFETs (12 V and 5 V, -30 V, DFN 3x3) driven through 2N7002s from `BAY_EN`, with a gate RC for
  about 1 ms of soft start and 100 k pull-ups that keep the bay off; a 10 k pull-down on `BAY_EN` keeps an empty or half-inserted
  slot off. PTC fuses: 3 A hold on 12 V, 2 A hold on 5 V.
* **Receptacle:** Molex 47018-4001, SATA 22-pin (7 data + 15 power) host receptacle, top-mount PCB-edge type, centred on the
  card's top edge; the cable leaves upward. It is 40.46 mm wide, which sets the card width. P3 (PWDIS) and P11 (staggered spin-up)
  are not connected.
* **Fingers:** KiCad's stock `BUS_PCIexpress_x1` pattern with its own tab outline and key notch, ENIG. The contacts are not PCIe:
  the pinout below is our own.
* **Bay LED** stays on the brain (in front of the slot); the bridge's LED pin sinks it through finger B6 (`LED_K`).

| Finger | Signal | Finger | Signal |
|---|---|---|---|
| A1, A2 | +12V | B1, B2, B3 | +12V |
| A3, A4, A7, A10-A13, A16-A18 | GND | B4, B7, B11, B14, B17, B18 | GND |
| A5, A6 | not connected | B5 | BAY_EN (in, from the brain) |
| A8, A9 | 5V (5V_HDD) | B6 | LED_K (bridge LED output, sunk on the brain) |
| A14, A15 | USB3_TX_N, USB3_TX_P (hub to bridge) | B8, B9, B10 | 5V (5V_HDD) |
| | | B12, B13 | USB2_DM, USB2_DP |
| | | B15, B16 | USB3_RX_N, USB3_RX_P (bridge to hub) |

The pinout lives in `hardware/tools/symgen.py` (`SLOT_PINS`) and feeds both the card and the slot symbols. The connector is rated
1.1 A per contact (TE/Amphenol PCI Express specification); five contacts per rail carry 5.5 A per bay.

### 3.4 Slots, drive cables and the M.2 bay

* **Slots:** eight Amphenol FCI 10018783-10100TLF PCI Express x1 vertical through-hole sockets (36 contacts, 1.0 mm pitch, board
  locks/pegs) at 14.5 mm pitch along the brain's rear edge. The footprint follows the Amphenol customer drawing 10018784: four rows
  of 0.70 mm holes at 2.0 mm pitch, pegs at 11.65 and 20.80 mm. The cards stand vertically, plane front to back, with the receptacle
  facing the next slot; the 45 mm card overhangs the board's rear edge by 15 mm (C27), which keeps the bay LEDs in front of the slots visible.
* **Drive cables:** off-the-shelf 22-pin male-to-female SATA extensions, 0.5 m; the drive end plugs straight onto a bare drive.
  The cable rises through a window in the lid over each receptacle.
* **M.2 (bay 9, C15):** TE 2199230-4 M-key socket at the front left, PCIe Gen3 x1 from the CM5 (REFCLK pair, PERST#, CLKREQ#),
  3V3_M2 from a dedicated AP63203 buck (U51) through a TPS22965 load switch (U50) enabled by GPIO. The module lies under the lid
  along the front; the lid hinge with a microswitch (SW3) is the "door": closing it powers the slot and rescans the PCIe bus.
  M.2 SATA (B+M key) modules are refused. USB-NVMe bridges present as SCSI and fall back to SCSI SANITIZE or overwrite.

### 3.5 Power tree and budget

Input: **12 V DC**, one rail; everything else is derived on the brain. Input connector J21: Kycon KPJX-4S-S 4-pin DIN, 7.5 A per
pin with two pins per polarity (barrel jacks were dropped at 5 A). The brick is chosen before layout is frozen because DIN pin
assignments differ between vendors (STATUS R3).

| Rail | Source | Loads | Notes |
|---|---|---|---|
| +12V | input after F1 (10 A slow), D20 (SMBJ15A), Q20 (AO4407A reverse-polarity FET), 2 x 680 uF bulk | the slots' 12 V pins | per-bay switch on the card |
| 5V_SYS | U20 TPS56637 (6 A) | CM5 (up to 3 A), 2 hubs, OLED, DIP, U22 | keeps drive spin-up ripple off the CM5 rail |
| 5V_HDD | U21 TPS56637 (6 A) | the slots' 5 V pins | per-bay switch on the card |
| 3V3 | U22 AP63203 (2 A) | hubs, IO, U3 | |
| 1V2 | U3 AP2112K-1.2 | both hubs' core | |
| 3V3_M2 | U51 AP63203, switched by U50 | M.2 socket | slot power is off while idle |

Budget, four drives: 12 V about 3.2 A typical, 4.4 A staggered peak; 5 V drives about 2.4 A typical, 2.8 A peak; the 12 V input
is about 5.3 A typical and 7.4 A staggered peak (11.5 A if all four spun up together, which the software never does). The 120 W brick,
the 10 A fuse and the DIN rating cover four bays. **Eight simultaneous drives need about 9.5 A typical and 11.7 A at a staggered peak:
a 150-180 W brick, a larger input fuse, two parallel DIN pins for 12 V and heavier bulk capacitors, and 5V_HDD at 6 A is at its limit
for eight drives.** Do not fit eight cards before those are revisited (STATUS R23).

Staggered spin-up is mandatory: the software never enables two bays within 4 s of each other.

### 3.6 Per-bay power switching

On each card, `BAY_EN` (from a CM5 GPIO, active high) turns on both P-FETs through the 2N7002 gate drivers. The gate RC gives about 1 ms
of ramp so a drive's bulk capacitors do not trip the upstream fuse; the pull-down keeps everything off during boot. Per-bay
resettable fuses catch a shorted drive. Power control also lets the software un-freeze a drive (cycle its bay) or reset a hung
bridge without disturbing the others.

### 3.7 GPIO map (BCM numbering)

| GPIO | Function | Direction | Notes |
|---|---|---|---|
| 2, 3 | I2C1 SDA / SCL | | OLED (0x3C) |
| 4 | M2_DOOR | in, pull-up | lid microswitch, closed = low |
| 5, 6, 12, 13 | BAY_EN 1-4 | out | active high, 10 k pull-down on each card |
| 7, 8, 9, 10 | BAY_EN 5-8 | out | same |
| 14, 15 | UART0 TX / RX | | debug header J7 |
| 16, 17, 20, 21, 22, 23, 24, 25 | DIP 1-8 | in, pull-up | ON = low |
| 26 | STATUS_LED | out | red status LED |
| 27 | M2_PWR_EN | out | 3V3_M2 load switch enable, 10 k pull-down |
| 18 | free | | buzzer removed (C23) |
| 0, 1 | reserved | | ID EEPROM per Pi convention, not populated |

Bay activity LEDs are driven by each bridge's LED pin through the slot, not by GPIO.

### 3.8 User interface

* **OLED:** 128 x 64 I2C (SSD1306 0.96" or SH1106 1.3") on a 4-pin header (J41), in a recess in the lid. Idle it shows the Wi-Fi QR
  code, the key and the address; running, one row per bay in two columns when more than five bays are configured.
* **DIP switch:** 8-way, through-hole, reachable through a lid slot. Semantics in 4.5. The only control on the unit.
* **LEDs:** power (green), activity (green), status (red), eight bay LEDs (blue), M.2 (blue), all 3 mm through-hole standing in 3.2 mm lid holes.

### 3.9 Other on-board

* **RTC:** the CM5's on-module RTC with a CR2032 holder (BT1) on the CM5 battery pin, so certificates carry trustworthy times off-network.
* **Fan header** (J40): 4-pin 5 V PWM, optional.
* **microSD** (J3), **USB-C** (J5, USB 2.0 only: rpiboot and a spare host port).
* **Test points:** none placed yet; the layout engineer should add them on the rails and each `BAY_EN` (see LAYOUT-REVIEW.md).

### 3.10 PCBs

Both boards come from `hardware/tools/` (netlist in `design.py`, placement in `gen_pcb.py`, routing pipeline in `route.py`), one
KiCad project each: `hardware/brain-drain.*` and `hardware/bay-card/bay-card.*`.

* **Brain, 150 x 122 mm, six layers:** F.Cu signal, In1 GND plane, In2 and In3 signal, In4 power islands (5V_SYS, 5V_HDD, +12V, +3V3),
  B.Cu signal with a GND pour; 1.6 mm, ENIG. Eight slots along the rear edge with their bay LEDs in front; the two hubs behind their
  slots; the CM5 in landscape on the right edge with its antenna out; DIN, USB-C and microSD on the left wall; bucks and input block in
  the middle; the M.2 socket front left; DIP and fan header front right; CR2032 holder and service headers on the bottom under the CM5.
  Each hub's ten bypass capacitors sit on the **bottom** side around the chip so the top layer keeps its space for pin escapes;
  the coupling caps of each differential pair are placed side by side.
* **Bay card, 45 x 46 mm, four layers:** F.Cu / GND / power / B.Cu, 1.6 mm, ENIG, receptacle on the top edge, bridge below it, the
  switch block above the finger tab.
* **Rules:** the Raspberry Pi CM5IO reference's 0.13 mm tracks, 0.125 mm clearance, 0.45/0.2 mm vias, because nothing coarser escapes
  the 0.4 mm-pitch CM5 connector; 0.3/0.15 mm vias only for the 0.4 mm QFN supply pins (D8, confirm with the fab); power nets 0.3 mm tracks
  with 0.6/0.3 vias. 90 ohm differential pairs (0.147 mm track, 0.253 mm gap, set for the four-layer stack-up) for USB 3, SATA and USB 2;
  85 ohm for the PCIe pair to the M.2. **The pair geometry must be recalculated for the fab's six-layer stack-up before ordering.**
  Pairs are length-matched end to end (across the series capacitors) to 0.15 mm.
* **Fab:** JLCPCB or PCBWay with assembly; see [FABRICATION.md](FABRICATION.md). USB5744, ASM1153E and the DF40 connectors need the
  assembler's SMT line.

![brain](img/renders/brain-iso-rear.png)
![card](img/renders/card-iso.png)

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
   assigned to a bay in `config.py` (e.g. `usb2/2-1/2-1.3` → bay 7) **and** the
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

### 4.5 DIP switch semantics

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

Bay 9 (the M.2 slot) adds a slot state in front of this: the slot is unpowered
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

## 5. Workstream 3: enclosure

* **Tool:** OpenSCAD, everything driven from `enclosure/params.scad`. Connector positions are generated from the KiCad PCB by
  `enclosure/tools/kicad_to_scad.py` so the shell tracks the board. **The generated `board.scad` is mirrored in x** (measured from the
  board's right edge): KiCad's top view is left-handed, OpenSCAD is right-handed, so a board that is seen from the front with x to the
  right sits in the tray with x measured from the tray's x = max wall. The renders and the lid-plan diagram undo the mirror.
* **Form (C21-C27):** a box about 157 x 145 x 62 mm: a tray and a lid hinged along the rear top edge (filament pin) with a snap latch at
  the front, so it pops open for the M.2 SSD; the lid microswitch is the M.2 "door". The brain sits on M2.5 heat-set standoffs. The tray is
  16 mm deeper behind the board than the board itself because the 45 mm bay cards overhang its rear edge (C27).
  Left wall (as seen from the front): DIN 12 V, USB-C, microSD. Right wall: the CM5 antenna side, vents only, no metal. Rear and right:
  vent slots. Lid: eight 11.8 x 43 mm windows over the cards' SATA receptacles (the drive cables rise through them), OLED window with a
  recess for the module (on a 4-wire lead, over the SSD), DIP slot, twelve LED holes, convection grille over the CM5 cooler.
  Floor: feet pockets. Nothing carries the drives; they lie on the bench.
* **Height:** the socket is 11.25 mm tall and the card body stands 37.6 mm above it, so the card top edge is 48.9 mm above the board;
  `above_board` is 50 mm and the plugs pass through the lid windows.
* **Print:** PETG or ASA, 0.2 mm layers, no supports by design (lid printed upside down).
* **Card retention (C30):** the lid carries a comb of nine 2.6 mm ribs, 8 mm deep, one in every gap between neighbouring receptacle
  housings (0.4 mm clearance to the card back face and to the next housing; the straight plug path stays free), and the tray has eight
  blocks under the cards' rear overhang, each with a 2.0 mm groove 0.5 mm below the card shoulder. `enclosure/tools/check_fit.py` checks
  the gaps against the placed card models. The lid holds the cards only when closed; with the lid open a card is held by its socket.
* **Artwork (C30):** the octopus logo, `BRAIN-DRAIN` and `NIST 800-88 DISK SANITIZER` are engraved 0.6 mm into the lid's outer face
  (impression, prints on the bed face). The brain board carries the same logo as top silkscreen with the name, a tagline and
  `github.com/dmz006/brain-drain` and the board revision (`REV` in `branding.py`, also written to the KiCad title block), placed in the largest free area left of the middle (`hardware/tools/branding.py`); the card carries its name.
* **Refinements** (`refinements.scad`): an OLED bezel that clamps the module under the lid window, rubber-feet pockets.
* **Images:** `docs/img/renders/` (see [RENDERS.md](RENDERS.md)), generated by `enclosure/tools/gallery.py`.

![open](img/renders/unit-open-front.png)

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

See `docs/DECISIONS.md`. Closed: CM5, USB topology, hub, bridge, input connector, LEDs, M.2 bay, brain plus bay cards (C24),
six layers (C26), card width (C27). Still open: OLED size (D5), option B with bridges in the cables (D6, parked).

## 8. Throughput expectations and build order

With four bays at native drive speed (§3.2; cards in slots 1, 2, 5 and 6), a 4 TB HDD single-pass overwrite
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
