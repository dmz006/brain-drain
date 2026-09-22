# Decision brief — hub, bridge, input connector, LEDs, M.2 bay

Prepared 2026-09-22 for dmz. Every fact marked *(ds)* was read from the part's
datasheet this session; prices are LCSC/JLCPCB list from the same day.
Standing rule for this project: dmz makes the decisions; this brief gives the
options, the facts, and a recommendation with its reasoning.

Rule applied throughout, per dmz: **if the spec is the same, prefer the part with
a fully public datasheet.**

---

## 1. USB 3.0 hub (two needed, one per CM5 native USB 3.0 port)

All three candidates are 4-port USB 3.x Gen 1 (5 Gbit/s) hubs with a USB 2.0
hub inside, so the electrical spec that matters to us is the same. Each hub
serves two bays; the other two downstream ports go unused.

| | VIA VL817-Q7 | **Microchip USB5744** | TI TUSB8041 | TI TUSB8044A |
|---|---|---|---|---|
| Datasheet | On request from VIA; LCSC "datasheet" link returns a web page | **Public** (DS00001855M, 51 pp) *(ds)* | **Public** (49 pp) *(ds)* | **Public** (69 pp) *(ds)* |
| Package | QFN-76, 9×9 mm | **56-VQFN, 7×7 mm** *(ds)* | 64-VQFN, 9×9 mm *(ds)* | 64-VQFN, 9×9 mm *(ds)* |
| Supplies | 5 V or 3.3 V in, regulators integrated | 3.3 V + **1.2 V core, external** *(ds Fig. 4-1)* | 3.3 V + 1.1 V core, external *(ds)* | 3.3 V + 1.1 V core, external *(ds)* |
| Config | strap pins | strap pins; optional SPI ROM or OTP; SMBus *(ds)* | strap pins; OTP/EEPROM/SMBus *(ds)* | same |
| KiCad stock symbol | no | no (I generate from the public pinout table) | **yes** | no |
| LCSC price / assembly | ~$2–4, C209756 | **$2.44 (/2G), $3.64 (-I/2G industrial), JLCPCB SMT** | $3.26, C486066 | ~$12 at JLCPCB |
| Track record | ubiquitous in cheap hubs, fine on Linux | common on SBC carriers and industrial boards, fine on Linux | older TI part, fine | newer TI part |

**Recommendation: USB5744.** It meets the public-datasheet rule, is the smallest
and cheapest of the documented parts, and is stocked for JLCPCB assembly. The
cost of choosing it over the VL817 is one extra regulator: a 1.2 V rail at a few
hundred mA, which one AP2112K-1.2 LDO (or a shared 1.2 V LDO for both hubs)
covers for about $0.30. TUSB8041 would be my second choice; it needs the same
kind of extra rail (1.1 V), is a larger package, and its only advantage is the
stock KiCad symbol, which is not worth much when I am generating symbols from
pin tables anyway. TUSB8044A is the same as TUSB8041 for our purposes at four
times the price.

*What changes in the design if you agree:* BOM section B becomes 2× USB5744 +
2× 25 MHz crystal + 1.2 V LDO. Nothing else moves.

## 2. USB→SATA bridge (four needed)

No USB-SATA bridge vendor publishes a datasheet openly; every one of them
(ASMedia, JMicron, VIA, Realtek) treats it as confidential. The difference is
in what is *available*:

| | ASMedia ASM1153E | JMicron JMS578 |
|---|---|---|
| Datasheet | Rev 0.4 copies marked "ASMedia Confidential" on mirror sites (y-ic.com, aliyun). Not fetchable by script, downloadable in a browser | **Rev 1.01, 23 pp, hosted on files.pine64.org**, complete: pin-out, application example, crystal, regulators *(ds)* |
| Package | QFN-48 6×6 | QFN-48 6×6 *(ds)* |
| Supplies | 3.3 V + 1.2 V (per reference designs; unverified) | **single 5 V**: embedded 5 V→1.2 V switcher (needs a 4.7 µH inductor) and 5 V→3.3 V LDO *(ds §2.7)* |
| Crystal | 25 MHz | 30 MHz *(ds)* |
| USB IDs | 174c:55aa / 174c:1153 | 152d:0578 |
| LCSC / JLCPCB | ~$3, C2762919, SMT available | C17700079, SMT available (price listing unclear, expect $2–3) |
| Linux reputation | preferred: UASP + TRIM work with no kernel quirks; many Pi-forum threads recommend it | mixed: early firmware had UASP/TRIM conflicts and spin-down "power cut" issues; fixed in later firmware (173.x) but chips from distributors ship with whatever firmware they have, and JMicron's updater is a Windows tool |
| Sanitize / Security Erase passthrough | unknown for both until measured. Both do ATA PASS-THROUGH (SAT); whether the bridge tolerates a long-running erase is the open question. |

**Recommendation: decide this on Saturday's bench, not on paper.** The two
chips are the same on the spec sheet; the difference is firmware behaviour, and
the one thing that matters for this product, whether `hdparm --sanitize-*`
and `SECURITY ERASE` pass through and survive, is not in either datasheet.
Concretely:

1. Buy two cheap docks or adapter cables, one with each chip. `lsusb` tells you
   which is which (`174c:55aa` ASMedia, `152d:0578` JMicron). Typical: UGREEN
   and StarTech adapters are ASMedia; many "JMicron" ones say so in the listing.
2. I extend `braindrain` with a `bench` command that runs the passthrough tests
   against a sacrificial drive and prints a pass/fail table per chip.
3. The chip that passes is the chip on the board. If both pass, the public
   datasheet rule says JMS578; if only ASMedia passes, we use a mirror copy of
   its datasheet and accept that.

If you would rather decide now: JMS578 satisfies your rule and has the nicer
power story (single 5 V rail), and I would pick it only if you are comfortable
that the firmware on distributor-supplied chips is recent, which we cannot check
until we have one. That is why I prefer the measurement.

## 3. D2 — 12 V input connector

Verified ratings *(ds / distributor pages)*:

| Connector | Rating | Fits our 7.4 A staggered peak? | Notes |
|---|---|---|---|
| Kycon KLDX-0202 barrel, 5.5×2.1/2.5 | 3.5–5 A | **no** | The standard barrel jack. Earlier I guessed the "high-current" KLDHCX was ~11 A; the catalog says **5 A**. Barrels top out around 5 A whatever the listing claims. |
| Kycon KLDHCX-0202-A locking barrel | 5 A | **no** | Same limit, adds a locking collar. |
| **Kycon KPJX-4S-S 4-pin DIN** | **7.5 A per pin, 48 V DC**; two pins each for +12 and GND gives large margin | **yes** | The connector on most 12 V/8–10 A desktop bricks (NAS boxes, LCD monitors). **Pinout differs between brick vendors**, so the brick is chosen first and the footprint wired to match it. |
| Molex Mini-Fit Jr 2×2 (5566/5569) | 9–13 A per pin | yes | Less common on bricks; usually needs a pigtail. |
| XT60 | 30 A | yes | Hobby-grade; no brick ships with it; would need a pigtail. |

**Recommendation: 4-pin DIN only; drop the barrel footprint.** Reasons: the
barrel cannot carry the current the power budget needs, and keeping an
under-rated footprint on the board invites someone to populate it. The DIN is
what 12 V/10 A bricks come with, is rated with margin, and locks. The one job it
creates is choosing the brick before layout so the +12/GND pin assignment
matches; I will put that as a checklist item in the hardware README.

*If you want the barrel anyway* (for example a 12 V/5 A brick and a 2-bay
build), the design would need a hard current limit: either populate only two
bays or add an eFuse on the input set to 5 A. I do not recommend this.

## 4. D7 — front-panel LEDs (power, status, 4× bay activity)

| Option | Parts | Assembly | Enclosure coupling | Look |
|---|---|---|---|---|
| **A. 3 mm through-hole LEDs on the board, through 3.2 mm holes in the lid** | 6× 3 mm LED (~$0.05), optional 3 mm LED clips ($0.05) | hand-soldered after the lid height is known, or JLC THT | loose: hole positions only; lead length sets height | classic, bright, slightly "maker" |
| B. 0603 SMD LEDs + vertical light pipes | 6× 0603 LED + 6× light pipe (Bivar/Dialight, $0.30–0.60 each) | LEDs by SMT line; pipes are press-fit through-hole | tight: pipe length is fixed, so board-to-lid distance must match the pipe | clean flush dots |
| C. Right-angle SMD LEDs at the rear edge, shining through side holes | 6× right-angle 0805 | SMT line, no hand work | medium: board edge must sit at the wall | side-visible only |
| D. No bay LEDs; OLED only, one power LED | 1 LED | — | minimal | sparse |

**Recommendation: A, 3 mm through-hole.** It costs nothing, tolerates a
millimetre or two of enclosure error, and the bay LEDs are driven directly by
the bridge chips' LED pins so they blink with real disk activity, which the
1 Hz OLED cannot show. Option D is tempting for simplicity but loses that
signal. Option B looks best but ties the enclosure and board together more
tightly than a first-run 3D print deserves; it is the right upgrade for a later
revision once the mechanicals are proven.

## 5. D10 — optional M.2 NVMe bay on the free PCIe Gen3 x1 lane

Facts: the CM5's PCIe lane is otherwise unused. An M.2 M-key socket (~$1),
2280/2260/2242 standoff positions, a switched 3.3 V at 3 A (TPS22965 load
switch, ~$0.80), PERST#, CLKREQ# and the REFCLK pair from the CM5. PCIe is not
hot-plug, so the software power-cycles the slot and rescans the bus per job.
Native NVMe is the **only** way to Purge an NVMe drive (`nvme sanitize`);
USB-NVMe adapters cannot pass those commands.

| Option | BOM cost | Layout cost | What it buys |
|---|---|---|---|
| **A. Footprint on the board, unpopulated (DNP)** | $0 | ~22×80 mm of board area, one short 85 Ω pair from the DF40, a handful of traces | populate later with a soldering iron and a firmware flag; no board respin |
| B. Populate in v1 | ~$2 | same, plus an enclosure access door and a slot cutout | NVMe wipes from day one |
| C. Omit | $0 | none; board can shrink ~15 % | nothing |

**Recommendation: A, footprint only.** It is nearly free to keep the option
open, and NVMe is the media type most likely to show up in a wipe pile in
2026. Populating in v1 (B) I would hold until the SATA bays are proven, because
the M.2 door complicates the enclosure and the PCIe rescan path is untested
software. Omitting (C) closes the door on the one feature that needs the CM5's
strongest interface. Two things to accept with A: the board stays around
160 × 100 mm, and the enclosure gets a blanked-off door position now so a
later door does not need a reprint.

## Summary of recommendations

| # | Decision | Recommendation |
|---|---|---|
| 1 | Hub | USB5744 (public datasheet, cheapest, JLC-assembled; +1 LDO) |
| 2 | Bridge (D3) | Measure on Saturday with one dock of each chip; the one that passes wins; tie → JMS578 |
| 3 | Input (D2) | 4-pin DIN only; choose the brick before layout |
| 4 | LEDs (D7) | 3 mm through-hole |
| 5 | M.2 (D10) | footprint, unpopulated |
