# brain-drain — Bill of Materials (v0)

Quantities are **per unit**. Prices are rough single-unit-to-qty-10 USD from
LCSC / Digi-Key / Mouser in 2026 and exist to size the budget, not to order from.
Items marked **verify** have a part family chosen but the exact orderable part
number still needs checking against the datasheet or current stock before layout.

Machine-readable copy: `hardware/bom/brain-drain-bom.csv`.

## A. Compute

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| M1 | 1 | Raspberry Pi CM4004008 | CM4, no wireless, 4 GB RAM, 8 GB eMMC | 65 | Any CM4 fits; Lite needs microSD |
| J1, J2 | 2 | Hirose DF40C-100DS-0.4V(51) | CM4 mating connectors, 100-pin 0.4 mm | 4 | 1.5 mm stack height |
| J3 | 1 | microSD push-push socket | for CM4 Lite variants | 1 | verify footprint |
| J4 | 1 | GbE magjack, 1000BASE-T, w/ LEDs (e.g. Hanrun HR911130A) | network for NTP / SSH / cert push | 2.5 | verify |
| J5 | 1 | USB-C 16-pin receptacle (GCT USB4085-GF-A) | rpiboot + spare USB 2.0 | 1 | USB 2.0 only |
| J6 | 1 | 2-pin header + jumper | nRPIBOOT | 0.1 | |
| J7 | 1 | 3-pin header | UART0 debug | 0.1 | |
| HS1 | 1 | CM4 heatsink, 40×30 mm, thermal pad | | 3 | mandatory |

## B. USB 3.0 host (Option A, §3.2)

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| U1 | 1 | VIA VL805-Q6 | PCIe Gen2 x1 → 4× USB 3.0 xHCI | 6 | LCSC stock varies; alt Renesas uPD720201 (~9) |
| Y1 | 1 | 25 MHz crystal, 3225 | VL805 reference clock | 0.3 | per ref design |
| U2 | 1 | W25X20CL / W25Q80 SOIC-8 SPI flash | VL805 firmware | 0.4 | **DNP** unless bootloader load fails |
| U3 | 1 | 1.2 V LDO (e.g. AP2112K-1.2) | VL805 core | 0.3 | verify VL805 core rail needs |
| C_pcie | 2 | 220 nF 0402 | PCIe TX AC coupling | — | |
| C_ss | 8 | 100 nF 0402 | USB 3 SS TX AC coupling (4 ports) | — | |
| — | — | VIA VL817-Q7 + 25 MHz xtal | **ALT, Option B only**: USB 3 hub | 4 | not in default build |

## C. USB→SATA bridges (×4 bays)

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| U10–U13 | 4 | ASMedia ASM1153E | USB 3.0 → SATA 6G, UASP, SAT passthrough | 3 ea | alt ASM235CM, pin-incompatible |
| Y10–Y13 | 4 | 25 MHz crystal 3225 | | 0.3 ea | |
| U14–U17 | 4 | 1.2 V LDO (AP2112K-1.2) | bridge core | 0.3 ea | verify per ref design |
| C_sata | 16 | 10 nF 0402 | SATA TX/RX AC coupling | — | 4 per link |
| D10–D13 | 4 | 3 mm LED, blue | bay activity, from bridge LED pin | 0.1 ea | through front panel |

## D. Drive connectors and pigtails

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| J10–J13 | 4 | SATA 22-pin (7+15) right-angle receptacle, backplane style (e.g. Molex 67491 series) | bay connectors | 0.8 ea | verify exact PN; generic LCSC part fine |
| CBL1–4 | 4 | SATA 22-pin male→female extension cable, 0.5 m | drive pigtails | 3 ea | off-the-shelf |

## E. Power

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| PSU1 | 1 | 12 V / 10 A desktop brick, 120 W | | 25 | connector must match J20/J21 |
| J20 | 1 | High-current DC barrel jack, 5.5×2.5 mm (Kycon KLDHCX series) | input, ≥8 A | 1.5 | **verify rating**; populate J20 *or* J21 |
| J21 | 1 | 4-pin DIN power jack (Kycon KPJX-4S-S) | input, alt footprint | 2.5 | standard on 12 V/10 A bricks |
| F1 | 1 | SMD fuse 10 A slow (Littelfuse 0453010.MR) | input | 1.5 | |
| D20 | 1 | SMBJ15A | input TVS | 0.3 | |
| Q20 | 1 | P-MOSFET −30 V ≥12 A (e.g. AO4407A / SQJ431EP) + 12 V zener | reverse polarity | 0.8 | |
| C20, C21 | 2 | 680 µF 25 V low-ESR electrolytic | 12 V bulk | 0.6 ea | near SATA power |
| U20 | 1 | TI TPS56637RPAR | 5V_SYS buck, 6 A | 2.5 | |
| U21 | 1 | TI TPS56637RPAR | 5V_HDD buck, 6 A | 2.5 | same PN |
| L20, L21 | 2 | 2.2 µH shielded inductor, ≥8 A Isat, ≤10 mΩ | for TPS56637 | 1.5 ea | |
| U22 | 1 | Diodes AP63203WU-7 | 3V3 buck, 2 A fixed | 0.6 | |
| L22 | 1 | 4.7 µH shielded inductor, 3 A | for AP63203 | 0.4 | |
| C_buck | ~12 | 22 µF 25 V 1210 + 22 µF 10 V 0805 | buck in/out | — | |
| Q30–Q37 | 8 | P-MOSFET −30 V ≥6 A ≤30 mΩ DFN3×3 (e.g. AON7403 / DMP3007SFG) | per-bay 12 V and 5 V switch | 0.4 ea | verify RDS(on) at Vgs = −5 V for the 5 V side |
| Q38–Q41 | 4 | 2N7002 | gate driver | 0.05 ea | |
| F10–F13 | 4 | PTC 1812 3 A hold | per-bay 12 V | 0.3 ea | |
| F14–F17 | 4 | PTC 1812 2 A hold | per-bay 5 V | 0.3 ea | |
| U30, U31 | 2 | TI INA3221 | per-bay 12 V current monitor | 1.5 ea | **DNP** in v1 |

## F. UI and misc

| Ref | Qty | Part | Description | ~USD | Note |
|---|---|---|---|---|---|
| SW1 | 1 | 8-way DIP switch, 2.54 mm through-hole | mode select | 1 | |
| SW2 | 1 | 16 mm illuminated momentary pushbutton, panel mount + 4-pin header | Start | 3 | |
| DS1 | 1 | 0.96" SSD1306 128×64 I2C OLED module (or 1.3" SH1106) | status | 3 | 4-pin header; alt 2.42" SSD1309 |
| D1 | 1 | 3 mm LED green | power | 0.1 | |
| D2 | 1 | 3 mm bicolour LED | status | 0.2 | |
| BZ1 | 1 | 5 V magnetic buzzer + NPN | | 0.5 | |
| U40 | 1 | NXP PCF85063AT | I2C RTC | 1 | |
| Y40 | 1 | 32.768 kHz crystal | RTC | 0.3 | |
| BT1 | 1 | CR2032 holder + cell | RTC backup | 1 | |
| J40 | 1 | 3-pin fan header | 5 V PWM fan | 0.1 | fan optional |
| — | — | passives, test points, mounting hardware | | 5 | |

## G. PCB and assembly

| Item | Qty | Description | ~USD | Note |
|---|---|---|---|---|
| PCB | 5 | 4-layer 160×100 mm, 1.6 mm, ENIG, JLC04161H-7628 | 60 / 5 | controlled impedance |
| Assembly | 5 | SMD side assembled, through-hole hand-fitted | 150 / 5 | QFN + 0.4 mm DF40 |

## H. Enclosure

| Item | Qty | Description | ~USD |
|---|---|---|---|
| Print | 1 | PETG/ASA, ~250 g | 6 |
| Inserts + screws | 8 | M2.5 heat-set + M2.5×6 | 1 |
| Feet | 4 | rubber bumpers | 0.5 |
| Fan | 1 | 40 mm 5 V (optional) | 3 |

## Rough unit cost

| Block | ~USD |
|---|---|
| CM4 + heatsink | 68 |
| Board-mounted electronics | 55 |
| PCB + assembly share (qty 5) | 42 |
| Connectors, cables, UI, OLED | 25 |
| PSU | 25 |
| Enclosure | 10 |
| **Total** | **~225** |
