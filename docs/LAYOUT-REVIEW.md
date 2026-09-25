# Layout and design review guide

For the engineer who takes over the boards. Read this first, then [ARCHITECTURE.md](ARCHITECTURE.md). It says what you are receiving, how it was
made, what has been checked and, above all, **what has not**. Nothing has been fabricated. The layout was produced by scripts and an
autorouter and has never been reviewed by a board designer; treat it as a complete first draft, not as a finished design.

## 1. What you are receiving

| | Brain board | Bay card |
|---|---|---|
| Role | CM5 carrier: two USB 3 hubs, eight card slots, M.2 socket, power, UI | one per drive: USB 3 to SATA bridge, per-bay power switch, SATA receptacle |
| Size, layers | 150 x 122 mm, **6 layers**, 1.6 mm, ENIG | 45 x 46 mm, 4 layers, 1.6 mm, ENIG, PCIe-style finger tab |
| Parts, nets | 163 parts, 192 nets | 39 parts, 37 nets |
| Sides populated | both (hub bypass caps, CR2032 holder and two headers on the bottom) | top only |
| KiCad project | `hardware/brain-drain.kicad_pro` | `hardware/bay-card/bay-card.kicad_pro` |
| ERC | 0 findings | 2 warnings (stock 2N7002 symbol differs from the library copy, harmless) |
| DRC (kicad-cli 9.0.8) | 0 errors, 0 unconnected, silkscreen and dangling-stub warnings only | same |
| Differential pairs | 44, all routed, end-to-end skew under 0.15 mm | 8, all routed, skew under 0.15 mm |

Quantities: four bay cards are fitted in version 1, up to eight fit. One brain, four cards, the enclosure and the cables are one unit.

![brain](img/renders/brain-top.png)
![card](img/renders/card-front.png)
![assembly](img/renders/electronics-iso.png)

## 2. Where everything is

| What | Where |
|---|---|
| Design intent, all subsystems | [ARCHITECTURE.md](ARCHITECTURE.md) (start with sections 2, 3.2 to 3.5 and 3.10) |
| Every decision with its reason | [DECISIONS.md](DECISIONS.md), briefs in [decisions/](decisions/) |
| Open work and risks | [STATUS.md](STATUS.md) |
| Schematics (KiCad 9, hierarchical) | `hardware/brain-drain.kicad_sch` + `hardware/sheets/`, `hardware/bay-card/bay-card.kicad_sch`; PDFs in `hardware/review/*-schematic.pdf` |
| Boards | `hardware/brain-drain.kicad_pcb`, `hardware/bay-card/bay-card.kicad_pcb` |
| Per-layer images, 3D views, schematic sheets as PNG | `hardware/renders/`, `hardware/bay-card/renders/`, gallery in [RENDERS.md](RENDERS.md) |
| Generated review data (rules, stack-up, planes, keep-outs, routing statistics, DRC/ERC, footprint provenance, netlists, placement CSV) | `hardware/review/` (regenerate with `python3 hardware/tools/make_review_pack.py`) |
| Pin-by-pin connection lists | `hardware/CONNECTIONS.md`, `hardware/bay-card/CONNECTIONS.md` |
| Bill of materials (generated) | [BOM.md](BOM.md), `hardware/bom/*.csv` |
| Datasheets and vendor drawings used | `hardware/ref/datasheets/` (local only, gitignored), list in `hardware/ref/DOWNLOADS.md` |
| Fabrication and assembly plan, cost, ordering gates | [FABRICATION.md](FABRICATION.md), `hardware/tools/export_fab.sh` |
| Enclosure (OpenSCAD) | `enclosure/`, generated from the boards' connector positions |
| Software (Python service, tests) | `software/`, 74 tests |

## 3. How the boards were made, and why it matters for review

Nothing was drawn in the KiCad GUI. Both projects are **generated** from a single netlist source, then placed and routed by scripts:

| Step | Tool | Notes |
|---|---|---|
| Netlist, parts, sheets | `hardware/tools/design.py` | every pin comes from a datasheet table saved in the repository |
| Symbols and footprints | `symgen.py`, `fpgen.py` | custom parts (slot pinout, DIN jack, TPS56637 land pattern, PCIe socket, SATA receptacle) |
| Schematic files, ERC | `gen_sch.py` | label-based sheets, so a reviewer sees nets by name, not wires |
| Placement | `gen_pcb.py` | regions and fixed positions; passives are shelf-packed next to their IC; then `check_place.py` |
| Rules, planes, fanout vias | `route.py prepare`, `fanout*` | net classes are written into the `.kicad_pro` |
| Routing | freerouting 2.1.0 and 2.4.1 (differential pairs first), then a small gap router of our own, a length tuner and clean-up | `tools/route_full.sh` runs it unattended, brain in about 1.5 hours |
| Reports | `open_report.py`, `route.py pairs`, `make_review_pack.py` | |

Consequences you should expect:

* **Placement is a first arrangement, not an optimised one.** The regions are sensible, the packing inside them is mechanical.
* **Routing is autorouter output.** It obeys the design rules and has no shorts, but it makes choices a designer would not (see 4.2).
* **Regenerating overwrites the boards.** Once you start editing in KiCad, stop running `gen_pcb.py` / `route_full.sh` on that copy. Keep the
  generators as the record of intent; the `.kicad_pcb` files become the source of truth for layout. The schematic files are generated too;
  edit them in KiCad if you take over, and update `design.py` only if you want to keep the generators alive.
* Some KiCad quirks are handled in the tools: net classes live in the `.kicad_pro`; plane zones are created once and never deleted; the
  zone filler in this KiCad build needs a fresh process after heavy edits. Open each board in the GUI, refill all zones (`B`) and rerun DRC before anything else.

## 4. Priority review items

Ordered by how much they can cost. "Where" points to evidence in this repository.

### 4.1 Stack-up and impedance (must fix before ordering)

* The six-layer stack is F.Cu / In1 GND / In2 signal / In3 signal / In4 power islands / B.Cu (brain). It was chosen because the four-layer
  board could not be routed (decision C26), not derived from an impedance calculation. **Choose the fab's real stack-up (for JLCPCB the
  JLC06161H family), then recalculate the pair geometry.** The pair class `DiffPair90` (0.147 mm track, 0.253 mm gap) is carried over from the
  Raspberry Pi CM5IO four-layer design and is very likely wrong for this stack-up. Targets: 90 ohm differential for USB 3, SATA and USB 2, 85 ohm for the PCIe pair to the M.2 socket.
* **About 90 % of the pair copper is on the two inner signal layers** (2250 mm on In2, 1812 mm on In3, 372 mm on F.Cu, 202 mm on B.Cu;
  `hardware/review/routing-stats.md`). In2 is next to the solid GND plane, which is good. **In3 is next to In4, which is split into power
  islands** (+3V3, 5V_SYS, +12V, 5V_HDD): half the In3 pair length runs over +3V3 or 5V_HDD, and 38 island boundaries lie under pair segments on 19 pair nets. Each is a
  return-path discontinuity. Fixes to consider: make In4 solid GND and move the power islands to In2/In3 or the outer layers; or route
  pairs only on In2, F.Cu and B.Cu; or stitch the islands with capacitors at every crossing.
* **In2 and In3 are adjacent signal layers:** in 21 % of the sampled In3 pair length an In2 track lies within 0.3 mm in plan view (broadside coupling). Enforce orthogonal routing or spacing rules between the two layers.
* Segment mismatch: 18 of the 44 pairs have a 0.2 to 6 mm length difference **within a segment** (largest 5.96 mm) that is compensated in the
  other half of the AC-coupled link, so the end-to-end skew is under 0.15 mm. Standard practice is to compensate where the mismatch arises.
  A designer will want the mismatch removed at the source (`hardware/review/brain-pairs.md`, column "mismatch mm" versus "end-to-end skew mm").
* Via counts differ between the two sides of many pairs (column "vias P/N"); each via is counted as 0.6 mm of length in the tuning, which is a guess.

### 4.2 High-speed nets, one by one

| Family | Count | Route | What to check |
|---|---|---|---|
| USB 3 hub to slot, TX (through 100 nF series caps on the brain) | 8 | hub QFN, caps, In2/In3, slot fingers A14/A15 | length, via count, reference plane, the AC caps near the transmitter |
| USB 3 slot to hub, RX | 8 | slot B15/B16 to hub | same |
| USB 3 hub upstream to the CM5 (two ports) | 2 x TX, 2 x RX | 38 to 108 mm plus 18 to 22 mm to the hub, In3 mostly | the longest USB 3 runs; reference over In4 islands |
| USB 2 hub to slot, and the CM5 USB 2 to the USB-C | 8 + 1 | 40 to 50 mm bay, 97 mm CM5 (USB3_0_DP) | 90 ohm, spacing from USB 3 |
| PCIe TX, RX, REFCLK between the CM5 and the M.2 | 3 | 92 mm (RX), 138 mm (TX), 142 mm (REFCLK), through 3 to 4 vias per side | 85 ohm; the 8 GT/s loss budget is borderline over 140 mm of FR4 with AC caps and vias; moving the M.2 socket toward the CM5 would shorten it a lot |
| SATA on the bay card | 2 + 2 | bridge to receptacle, 33 to 43 mm | length, 10 nF caps near the bridge |
| USB 3 / USB 2 on the bay card | 4 + 1 | fingers to bridge, 39 to 58 mm | see below |

* The pair routes are **long** for USB 3 Gen 1: many are 50 to 80 mm on the brain plus 30 to 50 mm on the card plus a card-edge connector at
  1 mm pitch that is not rated for 5 Gb/s. Its impedance and loss have not been simulated. The slot is a PCI Express x1 socket (rated for
  8 GT/s PCIe Gen 3) used with our own pinout, so the connector itself should be adequate, but the pinout puts a 12 V contact next to the
  SS pairs; check crosstalk and the ground contacts around A14/A15 and B15/B16.
* **Nothing has been simulated.** A designer should at least run an impedance and loss estimate for the worst hub-to-drive channel.

### 4.3 Power, planes and thermal

* **Brain power:** 12 V input through a 10 A slow fuse, an SMBJ15A TVS and a reverse-polarity P-FET, two 680 uF bulk caps, then two TPS56637
  bucks (5V_SYS and 5V_HDD, 6 A each), an AP63203 for 3V3 and one for the M.2. The buck layouts are auto-placed: check the input-cap hot loops,
  inductor placement, feedback routing and thermal vias against the TPS56637 datasheet (the land pattern is ours, generated from the datasheet).
* **Slot power:** each slot passes 12 V on five contacts and 5 V on five contacts (1.1 A per contact, 5.5 A per rail per bay) from planes on In4. Check the
  plane necks and the vias that connect the slot pins to In4, and voltage drop at eight bays. The 12 V strip on In4 is a rectangle across the slot row (`route.py _zones`).
* **Eight bays exceed the input design.** The 10 A fuse, the DIN rating and the 6 A 5V_HDD buck are sized for four drives (about 7.4 A staggered peak).
  Eight need 150 to 180 W and heavier parts (STATUS R23).
* **Thermal:** the CM5 is cooled passively; the bucks are small QFNs on a 1.6 mm board; the drive-side bay switches dissipate little. No thermal simulation exists.
* Copper widths are the router's: 0.3 mm power tracks for short runs, the planes carry the current. Check any long power track (5V_SYS to the hubs).

### 4.4 Placement and mechanical

* **Connector footprints from vendor drawings** (`hardware/review/footprints.md`): PCIe x1 socket (Amphenol 10018784 drawing) and Molex 47018-4001 SATA receptacle were built from the
  drawings' hole patterns. Two facts the drawings do not give: where the Molex mating face sits relative to the PCB edge (assumed flush; check the Molex STEP model) and the socket housing
  ends (assumed symmetrical). The M.2 socket footprint is still the CM5IO's, not yet compared with the TE drawing. The DIN jack pinout must match the brick that is bought (STATUS R3).
* **Card geometry:** the 45 mm bay card overhangs the brain's rear edge by 15 mm (decision C27); its receptacle body is 40.46 mm wide. The card's fingers sit 6 mm from its front edge. Check
  the enclosure fit in `enclosure/` (lid windows 11.8 x 43 mm, tray 16 mm deeper).
* **Mounting:** four M2.5 holes in the brain corners plus the CM5's four standoff holes (keep-out areas around them, 3.05 mm radius). There are no mounting features on the card except the slot
  itself; add retention (a guide in the enclosure or a latch) if the cards must survive a backpack.
* **Antenna:** the CM5 wireless module's antenna strip (x 142 to 150 mm, y 57 to 100 mm) is a keep-out on all layers; nothing metal within 10 mm. Verify with the CM5 datasheet 4.1.2.
* **Bottom side:** ten bypass capacitors per hub sit under the chips, plus the CR2032 holder and two headers. The enclosure has 6 mm of standoff for them.

### 4.5 Design for manufacture and assembly

* Minimum features used: 0.13 mm track / 0.125 mm space, 0.45 / 0.2 mm vias (0.3 / 0.15 mm on 53 brain vias and 36 card vias for the QFN supply pins, decision D8), 0.3 mm copper to board edge,
  0.2 mm hole clearance. Confirm with the fab that 0.3 / 0.15 mm vias and 0.4 mm-pitch QFN dog-bones are inside their six-layer capability and price tier.
* Both sides are assembled (bottom: caps, holder, headers); ask for through-hole assembly for the slots, DIN jack, DIP switch, LEDs and headers.
* **No fiducials, no test points, no panelisation** are drawn. Add fiducials and test points on every rail and each `BAY_EN`; panelise the card (8 to 16 per panel, tab routed, key notch).
* The silkscreen has about 300 overlap warnings (auto-placed reference text); clean before fabrication. Mask openings and paste stencil are the KiCad defaults.

### 4.6 Schematic review

Sheets of the brain: `power-input`, `power-bucks`, `cm5`, `usb3-hub-A`, `usb3-hub-B`, `bay-slots`, `m2-nvme`. Card: `bridge`, `bay-switch`, `edge`. For each, check the
connection lists against the datasheets in `hardware/ref/datasheets/`:

* USB5744 strap pins and reset, crystal and 1.2 V core; downstream port enable / overcurrent pins are deliberately unused.
* ASM1153E: strap resistors are absent on purpose (default 30 MHz crystal, no SPI ROM); REXT 12.1 k; the bridge runs from 5 V alone; the SATA AC caps are 10 nF.
* The slot pinout (`SLOT_PINS` in `symgen.py`, table in ARCHITECTURE 3.3) and that each card contact meets the right socket contact (the footprints share the naming A1 to B18).
* Bay switch: AON7403 pin table (S 1-3, G 4, D 5-8 + exposed pad, verified against the datasheet), gate network, the fuse ratings (3 A / 2 A hold).
* CM5 pin mapping (copied from the CM5IO reference), boot straps, GPIO usage against `ARCHITECTURE.md` 3.7, the M.2 sideband and the PCIe REFCLK routing.
* Protection: only the DC input has a TVS. **There is no ESD protection on the USB-C port, the DIP switch or the slot fingers.** Decide whether that is acceptable.
* Power-on and hot-plug behaviour of the bay card (inrush through the P-FET soft start).

## 5. Assumptions and open items

| # | Item | Why it matters | Evidence / next step |
|---|---|---|---|
| A1 | Pair geometry set for a four-layer stack-up | impedance wrong on six layers | 4.1; use the fab's calculator |
| A2 | In3 pairs over split In4, In2/In3 adjacency | return-path and crosstalk risk | `hardware/review/routing-stats.md`; change the plane assignment or the layer rules |
| A3 | Molex mating-face position (assumed flush) | card outline and enclosure window | Molex STEP in `hardware/ref/datasheets/`; verify before fab |
| A4 | Slot socket housing ends assumed | courtyard and enclosure fit | TE / Amphenol 3D model |
| A5 | M.2 socket footprint not compared with the TE drawing | wrong peg holes | `te-2199230-4-drawing.pdf` vs `M2_Socket3_MKey_CM5IO` (STATUS R2) |
| A6 | DIN pinout vs the chosen brick | wrong polarity or voltage | STATUS R3, brick datasheet still missing |
| A7 | 0.3 / 0.15 mm vias | fab capability and cost | ask the fab |
| A8 | CM5 SKU (value field says CM5002016; wireless is CM5102016) | wrong part ordered | BOM note; corrected at regeneration |
| A9 | Eight-bay power (fuse, DIN, 5V_HDD buck, bulk caps) | hardware sized for four drives | STATUS R23 |
| A10 | USB 3 channel not simulated | signal integrity across brain, slot, card, receptacle and cable | 4.2 |
| A11 | ASM1153E behaviour with SANITIZE passthrough | firmware wipes over USB | bench plan, 2026-09-26 (`saturday-bench-plan.md`) |
| A12 | No fiducials, test points, ESD parts, panel | manufacturing and bring-up | 4.5, 4.6 |
| A13 | Silkscreen and reference text | assembly drawings unreadable | clean up in the GUI |
| A14 | Parts marked `verify` in the BOM | orderability and ratings | [BOM.md](BOM.md) column "Check" |

## 6. Tool inventory (all in `hardware/tools/`)

| Tool | Does |
|---|---|
| `design.py` | the netlist of both boards |
| `symgen.py`, `fpgen.py`, `kilib.py`, `kifp.py`, `sexp.py` | KiCad symbol and footprint generation and file access |
| `gen_sch.py`, `gen_connections.py` | schematic files with ERC, connection lists |
| `gen_pcb.py`, `check_place.py` | placement and courtyard / outline check |
| `route.py` | rules and zones, fanout, staged autorouting, DRC clean-up, pair tuner, via clean-up |
| `gapclose.py` | grid A* router that closes what the autorouter leaves (0.1 or 0.05 mm grid) |
| `route_full.sh`, `reroute_pairs.sh`, `fix_pairs.sh`, `route_chain.sh` | unattended flows |
| `open_report.py` | open connections by class |
| `render_board.sh` | KiCad renders, per-layer images, schematic PNGs |
| `board_model.py` | 3D proxy model for `enclosure/tools/gallery.py` |
| `gen_bom.py` | BOM from the design |
| `make_review_pack.py` | `hardware/review/` |
| `export_fab.sh` | gerbers, drill, placement, BOM, assembly PDFs into `hardware/fab/<date>/` |

Reproduce everything from scratch: see [USAGE.md](USAGE.md). Freerouting jars are downloaded into `hardware/tools/freerouting/` (Java 21 and 25 are used).

## 7. Sign-off checklist

- [ ] Stack-up chosen with the fab; pair impedance recalculated and the pair class updated (4.1)
- [ ] Reference planes under the pairs reviewed, In3 / In4 assignment decided (4.1)
- [ ] Pair layouts reviewed by hand; per-segment mismatch removed where it arises
- [ ] Buck converter layouts reviewed against the datasheets (4.3)
- [ ] Slot power planes and vias sized for the bay current (4.3)
- [ ] Connector footprints checked against the vendor 3D models (4.4), M.2 footprint against the TE drawing
- [ ] DIN pinout matched to the brick
- [ ] Test points, fiducials, ESD protection decided and added (4.5, 4.6)
- [ ] Silkscreen cleaned; assembly drawings checked
- [ ] Fab DFM check passed on the gerbers (`export_fab.sh`)
- [ ] Bay card panel drawing, finger chamfer and key notch specified
- [ ] Enclosure fit checked with the final boards (`enclosure/`, gallery renders)
- [ ] First-article bench test plan agreed ([saturday-bench-plan.md](saturday-bench-plan.md))
