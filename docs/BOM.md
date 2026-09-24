# brain-drain — Bill of Materials (v0)

Quantities are **per unit**. Prices are rough single-unit-to-qty-10 USD from
LCSC / Digi-Key / Mouser in 2026 and exist to size the budget, not to order from.
Items marked **verify** have a part family chosen but the exact orderable part
number still needs checking against the datasheet or current stock before layout.

Machine-readable copy: `hardware/bom/brain-drain-bom.csv`. The schematic-level parts list
(every R, C, L with values) is in `hardware/CONNECTIONS.md`, generated from the netlist.

## A. Compute

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| M1 | 1 | Raspberry Pi CM5102016 | CM5 **wireless**, 2 GB RAM, 16 GB eMMC | ~97 | C22: wireless variant (+$5 over CM5002016 at $92.50 2026 list). Lite wireless CM5102000 (~$72) works via the microSD socket; 4 GB about $130 |
| J1, J2 | 2 | Hirose DF40C-100DS-0.4V(51) | CM5 mating connectors, 100-pin 0.4 mm | 4 | 1.5 mm stack height |
| J3 | 1 | microSD push-push socket | for CM5 Lite variants | 1 | verify footprint |
| J5 | 1 | USB-C 16-pin receptacle (GCT USB4085-GF-A) | rpiboot + spare USB 2.0 | 1 | USB 2.0 only |
| J6 | 1 | 2-pin header + jumper | nRPIBOOT | 0.1 | |
| J7 | 1 | 3-pin header | UART0 debug | 0.1 | |
| HS1 | 1 | Raspberry Pi CM5 Cooler (passive) | | 6 | C23: passive; fan header J40 kept for an optional fan |
| BT1 | 1 | CR2032 holder + cell | CM5 on-module RTC backup | 1 | on CM5 battery pin |

## B. USB 3.0 hubs (§3.2)

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| U1, U2 | 2 | Microchip USB5744/2G (56-VQFN 7×7) | USB 3.2 Gen1 4-port hub, one per CM5 native USB 3.0 port, two downstream ports used each | 2.44 ea | public datasheet DS00001855M; -I/2G industrial $3.64; LCSC C633619/C633621 (C11) |
| Y1, Y2 | 2 | 25 MHz crystal, 3225 | hub reference clock | 0.3 ea | per datasheet §crystal |
| U3 | 1 | AP2112K-1.2, SOT-25 | 1.2 V core for both hubs | 0.3 | USB5744 needs an external 1.2 V (ds Fig. 4-1) |
| C_ss | 12 | 100 nF 0402 | USB 3 SS TX AC coupling (2 upstream + 4 downstream links) | — | |
| — | — | VIA VL817-Q7 | **NOT USED**: datasheet only on request (C11) | — | |

## C. USB→SATA bridges (×4 bays)

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| U10–U13 | 4 | ASMedia ASM1153E (QFN-48 6×6) | USB 3.0 → SATA 6G, UASP, SAT passthrough | 3 ea | decided C12; LCSC C2762919; datasheet Rev 0.4 mirror copy, local only |
| Y10–Y13 | 4 | 30 MHz crystal 3225, CL 16 pF | default clock strap, no strap resistors | 0.3 ea | |
| L10–L13 | 4 | 4.7 µH 1 A inductor | ASM1153E internal core switcher (LXI) | 0.3 ea | ASM1153E runs from 5 V alone: no external LDO |
| C_sata | 16 | 10 nF 0402 | SATA TX/RX AC coupling | — | 4 per link |
| D10–D13 | 4 | 3 mm LED, blue | bay activity, from bridge LED pin | 0.1 ea | through front panel |

## C2. Bay card (C24), per card; four in v1, up to eight

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| U1 | 1 | ASMedia ASM1153E (QFN-48) | USB 3 → SATA bridge | 3 | as U10–U13 before |
| Y1, L1, C1–C18, R1–R2 | — | crystal 30 MHz, 4.7 µH, passives | bridge support | 1.2 | |
| Q1, Q2 | 2 | P-FET −30 V ≥6 A DFN3×3, pin-out S 1–3 / G 4 / D 5–8 + EP | 12 V and 5 V switches | 0.8 | part number to be chosen (R24); candidates AON7403 (AOS), Vishay / Nexperia equivalents with the same pin-out |
| Q3, Q4 | 2 | 2N7002 | gate drivers | 0.1 | |
| F1, F2 | 2 | PTC 1812, 3 A and 2 A hold | per-bay fuses | 0.6 | |
| R3–R8, C19, C20 | — | switch passives | soft-start, pull-ups, BAY_EN pull-down | 0.2 | |
| J2 | 1 | Molex 47018-4001 SATA 22-pin receptacle | drive cable | 1.5 | C17 |
| J1 | — | card-edge fingers (PCIe x1 pattern), ENIG | into the brain's slot | 0 | chamfer the tab |
| PCB | 1 | 4-layer 40 × 46 mm, panelised | | 3–4 | share of a panel of 8–16 |
| **Card total** | | | | **~11 + PCB** | |

## D. Slots and drive cables

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| J10–J17 | 8 | PCI Express x1 socket, through-hole (Amphenol 10018783-10100TLF or TE 1-1734774-1) | bay slots on the brain, custom pinout | 1 ea | placeholder footprint until the drawing arrives (`ref/DOWNLOADS.md`) |
| D10–D17, R60–R67 | 8 + 8 | 3 mm blue LED, 470 Ω | bay activity LEDs on the brain, sunk by the card | 0.15 ea | |
| CBL1–4 (–8) | 4 (8) | SATA 22-pin male→female extension cable, 0.5 m | drive cables; the drive end plugs straight onto a bare drive | 3 ea | off-the-shelf |

## E. Power

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| PSU1 | 1 | 12 V / 10 A desktop brick, 120 W (four bays); 150–180 W for eight | | 25–45 | connector must match J21; DIN pins paralleled for 12 V |
| J21 | 1 | 4-pin DIN power jack, Kycon KPJX-4S-S | 12 V input, 7.5 A per pin, 48 V | 2.5 | decided C13; barrel dropped (5 A rated). **Choose the brick before layout; DIN pin assignment varies by vendor** |
| F1 | 1 | SMD fuse 10 A slow (Littelfuse 0453010.MR) | input | 1.5 | |
| D20 | 1 | SMBJ15A | input TVS | 0.3 | |
| Q20 | 1 | P-MOSFET −30 V ≥12 A (AO4407A, SO-8, S 1–3 / G 4 / D 5–8) | reverse polarity | 0.8 | symbol `PMOS_SSSGDDDD` |
| D21 | 1 | 12 V zener, SOD-123 | Q20 gate clamp | 0.1 | |
| R20 | 1 | 100k | Q20 gate pull-down | — | |
| C20, C21 | 2 | 680 µF 25 V low-ESR electrolytic | 12 V bulk | 0.6 ea | near SATA power |
| U20 | 1 | TI TPS56637RPAR | 5V_SYS buck, 6 A | 2.5 | |
| U21 | 1 | TI TPS56637RPAR | 5V_HDD buck, 6 A | 2.5 | same PN |
| L20, L21 | 2 | 2.2 µH shielded inductor, ≥8 A Isat, ≤10 mΩ | for TPS56637 | 1.5 ea | |
| U22 | 1 | Diodes AP63203WU-7 | 3V3 buck, 2 A fixed | 0.6 | |
| L22 | 1 | 4.7 µH shielded inductor, 3 A | for AP63203 | 0.4 | |
| C_buck | ~12 | 22 µF 25 V 1210 + 22 µF 10 V 0805 | buck in/out | — | |
| Q30–Q37 | 8 | P-MOSFET −30 V ≥6 A ≤30 mΩ DFN3×3 (e.g. AON7403 / DMP3007SFG) | per-bay 12 V and 5 V switch | 0.4 ea | verify RDS(on) at Vgs = −5 V for the 5 V side |
| Q51–Q64 (8) + Q1 | 9 | 2N7002 | bay switch gate drivers (two per bay) and buzzer driver | 0.05 ea | |
| F10–F13 | 4 | PTC 1812 3 A hold | per-bay 12 V | 0.3 ea | |
| F14–F17 | 4 | PTC 1812 2 A hold | per-bay 5 V | 0.3 ea | |
| U30, U31 | 2 | TI INA3221 | per-bay 12 V current monitor | 1.5 ea | **DNP** in v1 |

## F. UI and misc

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| SW1 | 1 | 8-way DIP switch, 2.54 mm through-hole, piano style | mode select | 1 | |
| SW3 | 1 | 6 mm tactile / microswitch | lid closed sense (bay 5 "door") | 0.2 | |
| DS1 | 1 | 0.96" SSD1306 128×64 I2C OLED module (or 1.3" SH1106) | status | 3 | 4-pin header; alt 2.42" SSD1309 |
| D1 | 1 | 3 mm LED green | power | 0.1 | C14: all panel LEDs 3 mm through-hole |
| D2 | 1 | 3 mm bicolour LED | status | 0.2 | |
| D50 | 1 | 3 mm LED blue | M.2 bay activity | 0.1 | |
| J40 | 1 | 4-pin fan header, Pi pinout | optional 5 V PWM fan | 0.1 | not populated with a fan by default (C23) |
| J50 | 1 | TE 2199230-4, M.2 M-key socket, 4.2 mm | NVMe bay 5 on PCIe Gen3 x1 | 1.2 | decided C15/C18: **populated in v1** |
| MP50 | 3 | M.2 standoff + M2 screw, 2242/2260/2280 positions | | 0.3 | |
| U50 | 1 | TI TPS22965DSGR load switch, 5.5 V 6 A | switched 3V3 for the M.2 slot, 3 A budget | 0.8 | soft-start; enable from GPIO |
| U51 | 1 | AP63203WU-7 | dedicated 3V3_M2 buck from 12 V (M.2 SSDs draw up to 2.5–3 A) | 0.6 | keeps SSD load off the logic 3V3 |
| L51 | 1 | 4.7 µH shielded inductor, 3 A | | 0.4 | |
| — | — | passives, test points, mounting hardware | | 5 | |

## G. PCB and assembly

| Item | Qty | Description | ~USD | Note |
|---|---|---|---|---|
| PCB | 5 | 4-layer 136×100 mm, 1.6 mm, ENIG, JLC04161H-7628 | 60–90 / 5 | controlled impedance; outline C21–C23 |
| Assembly | 2 | full assembly, both sides, SMD and through-hole (owner solders nothing on the board) | 80–140 / 2 + parts | see `FABRICATION.md` for vendors and the full estimate |

## H. Enclosure

| Item | Qty | Description | ~USD |
|---|---|---|---|
| Print | 1 | PETG/ASA, ~250 g | 6 |
| Inserts + screws | 8 | M2.5 heat-set + M2.5×6 | 1 |
| Feet | 4 | rubber bumpers | 0.5 |
| Hinge pin | 1 | 1.75 mm filament, 140 mm | 0 |
| Fan | 1 | 40 mm 5 V (optional, not fitted) | 3 |

## Rough unit cost

| Block | ~USD |
|---|---|
| CM5 + cooler + RTC cell | 100 |
| Board-mounted electronics | 58 |
| PCB + assembly share (qty 5) | 42 |
| Connectors, cables, UI, OLED | 25 |
| PSU | 25 |
| Enclosure | 10 |
| **Total** | **~260** |

## Compute module list prices (Raspberry Pi product briefs, September 2026)

Prices rose sharply through 2025–2026 (memory-driven rises in Oct 2025, Feb 2026,
Apr 2026). No-wireless variants; wireless adds $5 on both modules.

| RAM | CM4 Lite | CM4 8 GB | CM4 16 GB | CM4 32 GB | CM5 Lite | CM5 16 GB | CM5 32 GB |
|---|---|---|---|---|---|---|---|
| 1 GB | 41.25 | 66.25 | 66.25 | 76.25 | — | — | — |
| 2 GB | 57.50 | 82.50 | 82.50 | 92.50 | 67.50 | 92.50 | 102.50 |
| 4 GB | 90 | 115 | 115 | 125 | 100 | 125 | 135 |
| 8 GB | 155 | 180 | 180 | 190 | 165 | 190 | 200 |
| 16 GB | — | — | — | — | 335 | 360 | 370 |

CM5 costs exactly **$10 more** than CM4 at the same RAM and eMMC size. CM5 has
no 1 GB or 8 GB-eMMC options. eMMC adds $25 over Lite on both. **Chosen: CM5**
(decision C7); production units CM5002016, dev units may use CM5002000 Lite.
