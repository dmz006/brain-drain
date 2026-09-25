# brain-drain bay card: ASM1153E USB-SATA bridge, switched 12 V / 5 V, 22-pin SATA receptacle — connection list

Generated from `hardware/tools/design.py`; do not edit by hand. One table per sheet: every
component with its symbol, value and footprint, then every net on that sheet with the pins
it joins. Nets marked **global** continue on other sheets. Pins listed under *No connect*
get an explicit no-connect flag.

Totals: 39 components, 37 nets.


## Sheet `bridge` — ASM1153E USB 3 to SATA bridge, 30 MHz crystal, core switcher, AC coupling

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C1 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C2 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C3 | `Device:C` | 2.2u | `Capacitor_SMD:C_0603_1608Metric` | RST# delay |
| C4 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | core rail |
| C5 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCIN bypass |
| C6 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCO 3.3 V out |
| C7 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C8 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C9 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C10 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C11 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C12 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C13 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C14 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C15 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX+ AC coupling |
| C16 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX- AC coupling |
| C17 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX+ AC coupling |
| C18 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX- AC coupling |
| L1 | `Device:L` | 4.7u 1A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` | core switcher inductor (value per ASMedia reference design, verify) |
| R1 | `Device:R` | 12.1k 1% | `Resistor_SMD:R_0402_1005Metric` | REXT |
| R2 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RST# pull-up |
| U1 | `brain-drain:ASM1153E` | ASM1153E | `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm` |  |
| Y1 | `Device:Crystal_GND24` | 30MHz CL=16pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `GND` | **global** | U1.47 (PGND), U1.21 (GNDA), U1.31 (GNDA), U1.49 (GND), U1.42 (TEST_EN), R1.2, C3.2, Y1.2 (G), Y1.4 (G), C1.2, C2.2, C4.2, C5.2, C6.2, C7.2, C8.2, C9.2, C10.2, C11.2, C12.2 | bay-switch, edge |
| `LED_K` | **global** | U1.43 (GPIO0) | edge |
| `SATA_A_N` | **global** | C16.2 | edge |
| `SATA_A_P` | **global** | C15.2 | edge |
| `SATA_B_N` | **global** | C18.1 | edge |
| `SATA_B_P` | **global** | C17.1 | edge |
| `U1_LXI` | local | U1.48 (LXI), L1.1 |  |
| `U1_REXT` | local | U1.17 (REXT), R1.1 |  |
| `U1_RST` | local | U1.38 (RST#), R2.2, C3.1 |  |
| `U1_SRXN` | local | C18.2, U1.30 (SRXN) |  |
| `U1_SRXP` | local | C17.2, U1.29 (SRXP) |  |
| `U1_STXN` | local | U1.32 (STXN), C16.1 |  |
| `U1_STXP` | local | U1.33 (STXP), C15.1 |  |
| `U1_UTXN` | local | U1.19 (UTXN), C14.1 |  |
| `U1_UTXP` | local | U1.20 (UTXP), C13.1 |  |
| `U1_VCCO` | local | U1.12 (VCCO), C6.1, U1.4 (VCC), U1.39 (VCC), U1.14 (VCCU), U1.18 (VCCU), U1.34 (VCCS), U1.27 (VCCTXL), C9.1, C10.1, C11.1, C12.1, R2.1 |  |
| `U1_VDD_CORE` | **global** | L1.2, C4.1, U1.7 (VDD), U1.36 (VDD), U1.46 (VDD), U1.13 (VDDU), U1.24 (VDDU), U1.28 (VDDS), C7.1, C8.1 |  |
| `U1_XI` | local | U1.25 (XI), Y1.1, C1.1 |  |
| `U1_XO` | local | U1.26 (XO), Y1.3, C2.1 |  |
| `USB2_DM` | **global** | U1.16 (UDM) | edge |
| `USB2_DP` | **global** | U1.15 (UDP) | edge |
| `USB3_RX_N` | **global** | U1.22 (URXN) | edge |
| `USB3_RX_P` | **global** | U1.23 (URXP) | edge |
| `USB3_TX_N` | **global** | C14.2 | edge |
| `USB3_TX_P` | **global** | C13.2 | edge |
| `5V_HDD` | **global** | U1.10 (VBUS), U1.11 (VBUS_LDO), U1.1 (VCCIN), C5.1 | bay-switch, edge |

### No connect

* U1: 2 (I2C_DATA), 3 (I2C_CLK), 35 (GPIO7), 37 (GPIO6), 40 (UART_RX), 41 (UART_TX), 44 (GPIO1), 45 (HDDPC), 5 (GPIO5), 6 (GPIO4), 8 (GPIO3), 9 (GPIO2)

### Notes

* ASM1153E runs from 5 V only (the brain's always-on 5V_HDD rail through the edge): VBUS_LDO -> VCCO (3.3 V) and VCCIN -> LXI switcher -> 1.05 V core.
* Clock straps GPIO3/GPIO7 at their internal pull-up default (11) = 30 MHz crystal. GPIO6 default = I2C mode, no SPI ROM. Bay activity LED assumed on GPIO0 (verify on the bench); it sinks the brain's LED through the edge.

## Sheet `bay-switch` — Switched 12 V and 5 V for the drive: P-FET high-side switches with soft-start, PTC fuses

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C19 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| C20 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| F1 | `Device:Polyfuse` | 3A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| F2 | `Device:Polyfuse` | 2A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| Q1 | `brain-drain:PMOS_SSSGDDDD_EP` | AON7403 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 12 V switch (AOS AON7403, -30 V, DFN 3x3-8); DFN 3x3-8 power pin-out S 1-3, G 4, D 5-8 + EP |
| Q2 | `brain-drain:PMOS_SSSGDDDD_EP` | AON7403 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 5 V switch (AOS AON7403); same pin-out |
| Q3 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 12 V gate driver |
| Q4 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 5 V gate driver |
| R3 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q1 gate pull-up (off) |
| R4 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R5 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q2 gate pull-up (off) |
| R6 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R7 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | BAY_EN pull-down: off at boot and with the slot empty |
| R8 | `Device:R` | 1k | `Resistor_SMD:R_0402_1005Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY_EN` | **global** | R8.1, R7.1 | edge |
| `EN_G` | local | R8.2, Q3.1 (G), Q4.1 (G) |  |
| `GND` | **global** | R7.2, Q3.2 (S), Q4.2 (S) | bridge, edge |
| `Q1_G` | local | Q1.4 (G), R3.2, C19.2, R4.1 |  |
| `Q2_G` | local | Q2.4 (G), R5.2, C20.2, R6.1 |  |
| `Q3_D` | local | R4.2, Q3.3 (D) |  |
| `Q4_D` | local | R6.2, Q4.3 (D) |  |
| `+12V` | **global** | Q1.1 (S), Q1.2 (S), Q1.3 (S), R3.1, C19.1 | edge |
| `12V_BAY` | **global** | F1.2 | edge |
| `12V_BAY_SW` | local | Q1.5 (D), Q1.6 (D), Q1.7 (D), Q1.8 (D), Q1.9 (D), F1.1 |  |
| `5V_BAY` | **global** | F2.2 | edge |
| `5V_BAY_SW` | local | Q2.5 (D), Q2.6 (D), Q2.7 (D), Q2.8 (D), Q2.9 (D), F2.1 |  |
| `5V_HDD` | **global** | Q2.1 (S), Q2.2 (S), Q2.3 (S), R5.1, C20.1 | bridge, edge |

### Notes

* P-FET high-side switch: 100k gate pull-up holds it off; the 2N7002 pulls the gate down through 10k with 100n gate-source, ~1 ms ramp so the drive's bulk caps do not trip the fuse. BAY_EN pull-down keeps the bay off through boot.

## Sheet `edge` — Card edge to the brain (PCIe x1 fingers, bay-card pinout) and the SATA 22-pin receptacle

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| J1 | `brain-drain:BAY_EDGE` | bay card edge | `Connector_PCBEdge:BUS_PCIexpress_x1` |  |
| J2 | `brain-drain:SATA22` | SATA 22-pin | `brain-drain:SATA_22pin_Receptacle_RA` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY_EN` | **global** | J1.B5 (BAY_EN) | bay-switch |
| `GND` | **global** | J1.A3 (GND), J1.A4 (GND), J1.A7 (GND), J1.A10 (GND), J1.A11 (GND), J1.A12 (GND), J1.A13 (GND), J1.A16 (GND), J1.A17 (GND), J1.A18 (GND), J1.B4 (GND), J1.B7 (GND), J1.B11 (GND), J1.B14 (GND), J1.B17 (GND), J1.B18 (GND), J2.S1 (GND), J2.S4 (GND), J2.S7 (GND), J2.P4 (GND), J2.P5 (GND), J2.P6 (GND), J2.P10 (GND), J2.P12 (GND) | bay-switch, bridge |
| `LED_K` | **global** | J1.B6 (LED_K) | bridge |
| `SATA_A_N` | **global** | J2.S3 (A-) | bridge |
| `SATA_A_P` | **global** | J2.S2 (A+) | bridge |
| `SATA_B_N` | **global** | J2.S5 (B-) | bridge |
| `SATA_B_P` | **global** | J2.S6 (B+) | bridge |
| `USB2_DM` | **global** | J1.B12 (USB2_DM) | bridge |
| `USB2_DP` | **global** | J1.B13 (USB2_DP) | bridge |
| `USB3_RX_N` | **global** | J1.B15 (USB3_RX_N) | bridge |
| `USB3_RX_P` | **global** | J1.B16 (USB3_RX_P) | bridge |
| `USB3_TX_N` | **global** | J1.A14 (USB3_TX_N) | bridge |
| `USB3_TX_P` | **global** | J1.A15 (USB3_TX_P) | bridge |
| `+12V` | **global** | J1.A1 (12V), J1.A2 (12V), J1.B1 (12V), J1.B2 (12V), J1.B3 (12V) | bay-switch |
| `12V_BAY` | **global** | J2.P13 (12V), J2.P14 (12V), J2.P15 (12V) | bay-switch |
| `5V_BAY` | **global** | J2.P7 (5V), J2.P8 (5V), J2.P9 (5V) | bay-switch |
| `5V_HDD` | **global** | J1.A8 (5V), J1.A9 (5V), J1.B8 (5V), J1.B9 (5V), J1.B10 (5V) | bay-switch, bridge |

### No connect

* J1: A5 (NC), A6 (NC)
* J2: P1 (3V3), P11 (DAS), P2 (3V3), P3 (3V3_PWDIS)

### Notes

* Fingers: Connector_PCBEdge:BUS_PCIexpress_x1 on the card's bottom edge (chamfer the edge, ENIG is fine for a few insertions). Pinout in symgen.SLOT_PINS.
* SATA P1-P3 (3.3 V) are not connected on purpose: P3 is PWDIS on SATA 3.3 drives and a 3.3 V supply there keeps them from spinning up.

## Power flags

Add a PWR_FLAG to each of these nets (they are driven by connectors or passive parts): `+12V`, `12V_BAY`, `5V_BAY`, `5V_HDD`, `U1_VDD_CORE`

