# brain-drain 4-bay disk sanitizer carrier, CM5 — connection list

Generated from `hardware/tools/design.py`; do not edit by hand. One table per sheet: every
component with its symbol, value and footprint, then every net on that sheet with the pins
it joins. Nets marked **global** continue on other sheets. Pins listed under *No connect*
get an explicit no-connect flag.

Totals: 299 components, 260 nets.


## Sheet `power-input` — 12 V DIN input, fuse, TVS, reverse-polarity FET, bulk capacitance

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C20 | `Device:C_Polarized` | 680u 25V low-ESR | `Capacitor_SMD:CP_Elec_10x10.5` |  |
| C21 | `Device:C_Polarized` | 680u 25V low-ESR | `Capacitor_SMD:CP_Elec_10x10.5` |  |
| C22 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` |  |
| D20 | `Device:D_TVS` | SMBJ15A | `Diode_SMD:D_SMB` |  |
| D21 | `Device:D_Zener` | 12V 0.5W | `Diode_SMD:D_SOD-123` | clamps Vgs of Q20 |
| F1 | `Device:Fuse` | 10A slow 0453010.MR | `Fuse:Fuse_Littelfuse-NANO2-451_453` |  |
| J21 | `brain-drain:DIN4_KPJX` | KPJX-4S-S | `brain-drain:Kycon_KPJX-4S-S` |  |
| Q20 | `Transistor_FET:Q_PMOS_GSD` | AO4407A | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | reverse-polarity protection, body diode toward load |
| R20 | `Device:R` | 100k | `Resistor_SMD:R_0603_1608Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `GND` | **global** | J21.3, J21.4, J21.5 (SHIELD), D20.1 (A1), R20.2, C20.2, C21.2, C22.2 | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, usb3-hub-A, usb3-hub-B |
| `Q20_GATE` | local | Q20.1 (G), R20.1, D21.2 (A) |  |
| `VIN_12V_FUSED` | local | F1.2, D20.2 (A2), Q20.3 (D) |  |
| `VIN_12V_RAW` | **global** | J21.1, J21.2, F1.1 |  |
| `+12V` | **global** | Q20.2 (S), C20.1, C21.1, C22.1, D21.1 (K) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, m2-nvme, power-bucks |

### Notes

* J21 pins 1/2 = +12 V and 3/4 = GND is a PLACEHOLDER: wire to match the chosen 12 V/10 A brick's DIN pinout (C13).
* Q20 is a P-MOSFET used as an ideal-diode-style reverse-polarity switch: drain to the fused input, source to +12V, gate pulled to GND through R20 and clamped by D21.

## Sheet `power-bucks` — 5V_SYS and 5V_HDD (TPS56637), +3V3 and 3V3_M2 (AP63203), +1V2 LDO

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C30 | `Device:C` | 1u 10V | `Capacitor_SMD:C_0402_1005Metric` |  |
| C31 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2000 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` | VIN bypass |
| C2001 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` |  |
| C2002 | `Device:C` | 100n 25V | `Capacitor_SMD:C_0402_1005Metric` | BOOT |
| C2003 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2004 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2005 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2100 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` | VIN bypass |
| C2101 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` |  |
| C2102 | `Device:C` | 100n 25V | `Capacitor_SMD:C_0402_1005Metric` | BOOT |
| C2103 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2104 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2105 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2200 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` |  |
| C2201 | `Device:C` | 100n 10V | `Capacitor_SMD:C_0402_1005Metric` | BST |
| C2202 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2203 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| L20 | `Device:L` | 2.2u 8A | `Inductor_SMD:L_Taiyo-Yuden_NR-60xx` |  |
| L21 | `Device:L` | 2.2u 8A | `Inductor_SMD:L_Taiyo-Yuden_NR-60xx` |  |
| L22 | `Device:L` | 4.7u 3A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` |  |
| R2000 | `Device:R` | 73.2k | `Resistor_SMD:R_0402_1005Metric` | FB top, 1% |
| R2001 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | FB bottom, 1% |
| R2002 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | EN pull-up |
| R2003 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PG pull-up |
| R2100 | `Device:R` | 73.2k | `Resistor_SMD:R_0402_1005Metric` | FB top, 1% |
| R2101 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | FB bottom, 1% |
| R2102 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | EN pull-up |
| R2103 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PG pull-up |
| U3 | `Regulator_Linear:AP2112K-1.2` | AP2112K-1.2 | `Package_TO_SOT_SMD:SOT-23-5` |  |
| U20 | `brain-drain:TPS56637` | TPS56637RPAR | `brain-drain:Texas_RPA0010A_VQFN-HR-10_3x3mm` |  |
| U21 | `brain-drain:TPS56637` | TPS56637RPAR | `brain-drain:Texas_RPA0010A_VQFN-HR-10_3x3mm` |  |
| U22 | `Regulator_Switching:AP63203WU` | AP63203WU-7 | `Package_TO_SOT_SMD:TSOT-23-6` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `GND` | **global** | C2000.2, C2001.2, U20.3 (AGND), U20.9 (PGND), R2001.2, C2003.2, C2004.2, C2005.2, C2100.2, C2101.2, U21.3 (AGND), U21.9 (PGND), R2101.2, C2103.2, C2104.2, C2105.2, U22.4 (GND), C2200.2, C2202.2, C2203.2, U3.2 (GND), C30.2, C31.2 | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-input, usb3-hub-A, usb3-hub-B |
| `PG_5V_HDD` | local | U21.4 (PG), R2103.2 |  |
| `PG_5V_SYS` | local | U20.4 (PG), R2003.2 |  |
| `U20_BOOT` | local | U20.7 (BOOT), C2002.1 |  |
| `U20_EN` | local | U20.1 (EN), R2002.2 |  |
| `U20_FB` | local | U20.2 (FB), R2000.2, R2001.1 |  |
| `U20_SW` | local | U20.6 (SW), L20.1, C2002.2 |  |
| `U21_BOOT` | local | U21.7 (BOOT), C2102.1 |  |
| `U21_EN` | local | U21.1 (EN), R2102.2 |  |
| `U21_FB` | local | U21.2 (FB), R2100.2, R2101.1 |  |
| `U21_SW` | local | U21.6 (SW), L21.1, C2102.2 |  |
| `U22_BST` | local | U22.6 (BST), C2201.1 |  |
| `U22_SW` | local | U22.5 (SW), L22.1, C2201.2 |  |
| `+12V` | **global** | U20.8 (VIN), C2000.1, C2001.1, R2002.1, U21.8 (VIN), C2100.1, C2101.1, R2102.1, U22.3 (IN), C2200.1, U22.2 (EN) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, m2-nvme, power-input |
| `+1V2` | **global** | U3.5 (VOUT), C31.1 | usb3-hub-A, usb3-hub-B |
| `+3V3` | **global** | L22.2, C2202.1, C2203.1, U22.1 (FB), U3.1 (VIN), U3.3 (EN), C30.1 | cm5, usb3-hub-A, usb3-hub-B |
| `5V_HDD` | **global** | L21.2, C2103.1, C2104.1, C2105.1, R2100.1, R2103.1 | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4 |
| `5V_SYS` | **global** | L20.2, C2003.1, C2004.1, C2005.1, R2000.1, R2003.1 | bridge-1, bridge-2, bridge-3, bridge-4, cm5 |

### No connect

* U20: 10 (MODE), 5 (NC)
* U21: 10 (MODE), 5 (NC)
* U3: 4 (NC)

### Notes

* TPS56637 FB: Vref 0.6 V; 73.2k/10k gives 4.99 V. MODE floating = forced CCM (quietest for the CM5 rail).
* AP63203WU is the fixed 3.3 V variant: FB ties straight to the output. EN tied to VIN (always on).

## Sheet `cm5` — Compute Module 5 (wireless): power, control, GPIO, microSD, USB-C, UART, RTC cell, fan, DIP, LEDs, OLED

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| BT1 | `Device:Battery_Cell` | CR2032 | `Battery:BatteryHolder_Keystone_1060_1x2032` |  |
| C1 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C2 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C3 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C4 | `Device:C` | 1u 10V | `Capacitor_SMD:C_0402_1005Metric` |  |
| D1 | `Device:LED` | green PWR | `LED_THT:LED_D3.0mm` |  |
| D2 | `Device:LED` | green ACT | `LED_THT:LED_D3.0mm` |  |
| D3 | `Device:LED` | red STATUS | `LED_THT:LED_D3.0mm` |  |
| J3 | `Connector:Micro_SD_Card` | microSD | `Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5` |  |
| J5 | `Connector:USB_C_Receptacle_USB2.0_16P` | USB-C rpiboot | `Connector_USB:USB_C_Receptacle_GCT_USB4085` |  |
| J6 | `Connector_Generic:Conn_01x02` | nRPIBOOT | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |
| J7 | `Connector_Generic:Conn_01x03` | UART0 GND/TX/RX | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` |  |
| J40 | `Connector_Generic:Conn_01x04` | Fan GND/5V/TACH/PWM | `Connector:FanPinHeader_1x04_P2.54mm_Vertical` |  |
| J41 | `Connector_Generic:Conn_01x04` | OLED GND/VCC/SCL/SDA | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` |  |
| M1 (unit 1,2,3,5) | `brain-drain:CM5` | CM5002016 | `brain-drain:Raspberry-Pi-5-Compute-Module` |  |
| R1 | `Device:R` | 1k | `Resistor_SMD:R_0603_1608Metric` |  |
| R2 | `Device:R` | 1k | `Resistor_SMD:R_0603_1608Metric` |  |
| R3 | `Device:R` | 1k | `Resistor_SMD:R_0603_1608Metric` |  |
| R10 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | FAN_PWM pull-up (open-drain output), as on CM5IO |
| R11 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | SD_PWR_ON pull-up |
| SW1 | `Switch:SW_DIP_x08` | DIP x8 | `Button_Switch_THT:SW_DIP_SPSTx08_Piano_10.8x21.88mm_W7.62mm_P2.54mm` |  |
| U52 | `brain-drain:TPS22965` | TPS22965DSGR | `Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm` | microSD power switch, driven by SD_PWR_ON (as CM5IO does with an RT9742) |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY_EN1` | **global** | M1.34 (GPIO5) | bay-switch-1 |
| `BAY_EN2` | **global** | M1.30 (GPIO6) | bay-switch-2 |
| `BAY_EN3` | **global** | M1.31 (GPIO12) | bay-switch-3 |
| `BAY_EN4` | **global** | M1.28 (GPIO13) | bay-switch-4 |
| `CM5_3V3` | local | M1.84 (CM5_3.3V), M1.86 (CM5_3.3V), M1.78 (GPIO_VREF) |  |
| `D1_A` | local | R1.2, D1.2 (A) |  |
| `D2_A` | local | R2.2, D2.2 (A) |  |
| `D3_A` | local | R3.2, D3.2 (A) |  |
| `DIP1` | local | M1.29 (GPIO16), SW1.1 |  |
| `DIP2` | local | M1.50 (GPIO17), SW1.2 |  |
| `DIP3` | local | M1.27 (GPIO20), SW1.3 |  |
| `DIP4` | local | M1.25 (GPIO21), SW1.4 |  |
| `DIP5` | local | M1.46 (GPIO22), SW1.5 |  |
| `DIP6` | local | M1.47 (GPIO23), SW1.6 |  |
| `DIP7` | local | M1.45 (GPIO24), SW1.7 |  |
| `DIP8` | local | M1.41 (GPIO25), SW1.8 |  |
| `FAN_PWM` | local | M1.19 (Fan_PWM), J40.4 (Pin_4), R10.2 |  |
| `FAN_TACHO` | local | M1.16 (Fan_Tacho), J40.3 (Pin_3) |  |
| `GND` | **global** | M1.1 (GND), M1.2 (GND), M1.7 (GND), M1.8 (GND), M1.13 (GND), M1.14 (GND), M1.22 (GND), M1.23 (GND), M1.32 (GND), M1.33 (GND), M1.42 (GND), M1.43 (GND), M1.52 (GND), M1.53 (GND), M1.59 (GND), M1.60 (GND), M1.65 (GND), M1.66 (GND), M1.71 (GND), M1.74 (GND), M1.98 (GND), M1.107 (GND), M1.108 (GND), M1.113 (GND), M1.114 (GND), M1.119 (GND), M1.120 (GND), M1.125 (GND), M1.126 (GND), M1.131 (GND), M1.132 (GND), M1.137 (GND), M1.138 (GND), M1.144 (GND), M1.150 (GND), M1.155 (GND), M1.156 (GND), M1.161 (GND), M1.162 (GND), M1.167 (GND), M1.168 (GND), M1.173 (GND), M1.174 (GND), M1.179 (GND), M1.180 (GND), M1.185 (GND), M1.186 (GND), M1.191 (GND), M1.192 (GND), M1.197 (GND), M1.198 (GND), C1.2, C2.2, BT1.2 (-), J6.2 (Pin_2), J7.1 (Pin_1), J40.1 (Pin_1), D1.1 (K), SW1.16, SW1.15, SW1.14, SW1.13, SW1.12, SW1.11, SW1.10, SW1.9, J41.1 (Pin_1), J3.6 (VSS), J3.9 (SHIELD), U52.5 (GND), U52.9 (EP), C3.2, C4.2, J5.A1 (GND), J5.A12 (GND), J5.B1 (GND), J5.B12 (GND), J5.S1 (SHIELD) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `I2C1_SCL` | local | M1.56 (GPIO3), J41.3 (Pin_3) |  |
| `I2C1_SDA` | local | M1.58 (GPIO2), J41.4 (Pin_4) |  |
| `LED_nACT` | local | D2.1 (K), M1.21 (LED_nACT) |  |
| `M2_DOOR` | **global** | M1.54 (GPIO4) | m2-nvme |
| `M2_PEDET` | **global** | M1.26 (GPIO19) | m2-nvme |
| `M2_PWR_EN` | **global** | M1.48 (GPIO27) | m2-nvme |
| `SD_CLK` | local | M1.57 (SD_CLK), J3.5 (CLK) |  |
| `SD_CMD` | local | M1.62 (SD_CMD), J3.3 (CMD) |  |
| `SD_DAT0` | local | M1.63 (SD_DAT0), J3.7 (DAT0) |  |
| `SD_DAT1` | local | M1.67 (SD_DAT1), J3.8 (DAT1) |  |
| `SD_DAT2` | local | M1.69 (SD_DAT2), J3.1 (DAT2) |  |
| `SD_DAT3` | local | M1.61 (SD_DAT3), J3.2 (DAT3/CD) |  |
| `SD_PWR_ON` | local | M1.75 (SD_PWR_ON), U52.3 (ON), R11.2 |  |
| `SD_VDD` | **global** | U52.8 (VOUT), U52.7 (VOUT), J3.4 (VDD), C3.1 |  |
| `STATUS_LED` | local | D3.1 (K), M1.24 (GPIO26) |  |
| `UART0_RXD` | local | M1.51 (GPIO15), J7.3 (Pin_3) |  |
| `UART0_TXD` | local | M1.55 (GPIO14), J7.2 (Pin_2) |  |
| `USB2_DM` | **global** | J5.A7 (D-), J5.B7 (D-) | m2-nvme |
| `USB2_DP` | **global** | J5.A6 (D+), J5.B6 (D+) | m2-nvme |
| `USBC_CC1` | local | J5.A5 (CC1), M1.94 (CC1) |  |
| `USBC_CC2` | local | J5.B5 (CC2), M1.96 (CC2) |  |
| `VBAT` | local | M1.76 (VBAT), BT1.1 (+) |  |
| `+3V3` | **global** | R10.1, R1.1, R2.1, R3.1, J41.2 (Pin_2), U52.1 (VIN), U52.2 (VIN), U52.4 (VBIAS), C4.1, R11.1 | power-bucks, usb3-hub-A, usb3-hub-B |
| `5V_SYS` | **global** | M1.77 (5V), M1.79 (5V), M1.81 (5V), M1.83 (5V), M1.85 (5V), M1.87 (5V), C1.1, C2.1, J40.2 (Pin_2) | bridge-1, bridge-2, bridge-3, bridge-4, power-bucks |
| `nRPIBOOT` | local | M1.93 (nRPIBOOT), J6.1 (Pin_1) |  |

### No connect

* J5: A4 (VBUS), A8 (SBU1), A9 (VBUS), B4 (VBUS), B8 (SBU2), B9 (VBUS)
* M1: 10 (Ethernet_Pair0_N), 100 (CAM_GPIO1), 11 (Ethernet_Pair2_P), 115 (MIPI0_D0_N), 117 (MIPI0_D0_P), 12 (Ethernet_Pair0_P), 121 (MIPI0_D1_N), 123 (MIPI0_D1_P), 127 (MIPI0_C_N), 129 (MIPI0_C_P), 133 (MIPI0_D2_N), 135 (MIPI0_D2_P), 139 (MIPI0_D3_N), 141 (MIPI0_D3_P), 143 (HDMI1_HOTPLUG), 145 (HDMI1_SDA), 146 (HDMI1_TX2_P), 147 (HDMI1_SCL), 148 (HDMI1_TX2_N), 149 (HDMI1_CEC), 15 (Ethernet_nLED3), 151 (HDMI0_CEC), 152 (HDMI1_TX1_P), 153 (HDMI0_HOTPLUG), 154 (HDMI1_TX1_N), 158 (HDMI1_TX0_P), 160 (HDMI1_TX0_N), 164 (HDMI1_CLK_P), 166 (HDMI1_CLK_N), 17 (Ethernet_nLED2), 170 (HDMI0_TX2_P), 172 (HDMI0_TX2_N), 175 (MIPI1_D0_N), 176 (HDMI0_TX1_P), 177 (MIPI1_D0_P), 178 (HDMI0_TX1_N), 18 (Ethernet_SYNC_OUT), 181 (MIPI1_D1_N), 182 (HDMI0_TX0_P), 183 (MIPI1_D1_P), 184 (HDMI0_TX0_N), 187 (MIPI1_C_N), 188 (HDMI0_CLK_P), 189 (MIPI1_C_P), 190 (HDMI0_CLK_N), 193 (MIPI1_D2_N), 194 (MIPI1_D3_N), 195 (MIPI1_D2_P), 196 (MIPI1_D3_P), 199 (HDMI0_SDA), 20 (EEPROM_nWP), 200 (HDMI0_SCL), 3 (Ethernet_Pair3_P), 35 (ID_SC), 36 (ID_SD), 37 (GPIO7), 38 (GPIO11), 39 (GPIO8), 4 (Ethernet_Pair1_P), 40 (GPIO9), 44 (GPIO10), 49 (GPIO18), 5 (Ethernet_Pair3_N), 6 (Ethernet_Pair1_N), 64 (SD_DAT5), 68 (SD_DAT4), 70 (SD_DAT7), 72 (SD_DAT6), 73 (SD_VDD_OVERRIDE), 80 (SCL0), 82 (SDA0), 88 (CM5_1.8V), 89 (WL_nDisable), 9 (Ethernet_Pair2_N), 90 (CM5_1.8V), 91 (BT_nDisable), 92 (PWR_Button), 95 (LED_nPWR), 97 (CAM_GPIO0), 99 (PMIC_Enable)
* U52: 6 (CT)

### Notes

* GPIO_VREF is tied to the CM5's own 3.3 V output (pins 84/86) for 3.3 V GPIO signalling, per datasheet §4.2.
* PMIC_Enable and PWR_Button are left floating (internal pull-ups). nRPIBOOT goes to jumper J6.
* LED_nACT is an open-drain 20 mA output on the CM5: it sinks D2 directly. GPIO26 sinks D3 (software drives it low to light).
* microSD power goes through U52 so the CM5 can power-cycle the card on reboot via SD_PWR_ON, matching the CM5IO reference (which uses an RT9742).
* Ethernet dropped (C22). The CM5 wireless variant's PCB antenna is on the short module edge that carries MH1; that edge sits on the board's left edge with an 8 mm copper-free strip under it and no metal within 10 mm (CM5 datasheet 4.1.2).
* USB-C is a device port (rpiboot / gadget). As on the CM5IO, CC1/CC2 go straight to the CM5, which presents the sink pull-downs itself; VBUS is not connected (the board is powered from 12 V). USB_OTG_ID floats = device.

## Sheet `usb3-hub-A` — USB5744 hub A on CM5 USB3-0, bays 1 and 2

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C100 | `Device:C` | 33p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C101 | `Device:C` | 33p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C110 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C111 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C112 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C113 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C120 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C121 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C122 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C123 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C130 | `Device:C` | 4.7u 10V | `Capacitor_SMD:C_0603_1608Metric` |  |
| C131 | `Device:C` | 4.7u 10V | `Capacitor_SMD:C_0603_1608Metric` |  |
| C140 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 upstream TX AC coupling |
| C141 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 upstream TX AC coupling |
| C151 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN1 TX AC coupling |
| C152 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN2 TX AC coupling |
| C161 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN1 TX AC coupling |
| C162 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN2 TX AC coupling |
| R100 | `Device:R` | 12.0k 1% | `Resistor_SMD:R_0402_1005Metric` | RBIAS |
| R101 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | VBUS_DET to 3.3 V |
| R102 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RESET_N pull-up |
| R103 | `Device:R` | 200k | `Resistor_SMD:R_0402_1005Metric` | CFG_NON_REM: all ports removable |
| R113 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_P3 strap |
| R114 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_P4 strap |
| R123 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_M3 strap |
| R124 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_M4 strap |
| U1 | `brain-drain:USB5744` | USB5744/2G | `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` |  |
| Y1 | `Device:Crystal_GND24` | 25MHz CL=20pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY1_USB2_DM` | **global** | U1.2 (USB2DN_DM1/PRT_DIS_M1) | bridge-1 |
| `BAY1_USB2_DP` | **global** | U1.1 (USB2DN_DP1/PRT_DIS_P1) | bridge-1 |
| `BAY1_USB3_RX_N` | **global** | C161.2 | bridge-1 |
| `BAY1_USB3_RX_P` | **global** | C151.2 | bridge-1 |
| `BAY1_USB3_TX_N` | **global** | U1.7 (USB3DN_RXDM1) | bridge-1 |
| `BAY1_USB3_TX_P` | **global** | U1.6 (USB3DN_RXDP1) | bridge-1 |
| `BAY2_USB2_DM` | **global** | U1.9 (USB2DN_DM2/PRT_DIS_M2) | bridge-2 |
| `BAY2_USB2_DP` | **global** | U1.8 (USB2DN_DP2/PRT_DIS_P2) | bridge-2 |
| `BAY2_USB3_RX_N` | **global** | C162.2 | bridge-2 |
| `BAY2_USB3_RX_P` | **global** | C152.2 | bridge-2 |
| `BAY2_USB3_TX_N` | **global** | U1.14 (USB3DN_RXDM2) | bridge-2 |
| `BAY2_USB3_TX_P` | **global** | U1.13 (USB3DN_RXDP2) | bridge-2 |
| `GND` | **global** | U1.EP (VSS), U1.52 (ATEST), R100.2, R103.2, Y1.2 (G), Y1.4 (G), C110.2, C111.2, C112.2, C113.2, C120.2, C121.2, C122.2, C123.2, C130.2, C131.2, C100.2, C101.2 | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-B |
| `U1_CFG_NON_REM` | local | U1.41 (SPI_CE_N/CFG_NON_REM), R103.1 |  |
| `U1_DN1_TXDM` | local | U1.4 (USB3DN_TXDM1), C161.1 |  |
| `U1_DN1_TXDP` | local | U1.3 (USB3DN_TXDP1), C151.1 |  |
| `U1_DN2_TXDM` | local | U1.11 (USB3DN_TXDM2), C162.1 |  |
| `U1_DN2_TXDP` | local | U1.10 (USB3DN_TXDP2), C152.1 |  |
| `U1_PRT_DIS_M3` | local | U1.18 (USB2DN_DM3/PRT_DIS_M3), R123.2 |  |
| `U1_PRT_DIS_M4` | local | U1.25 (USB2DN_DM4/PRT_DIS_M4), R124.2 |  |
| `U1_PRT_DIS_P3` | local | U1.17 (USB2DN_DP3/PRT_DIS_P3), R113.2 |  |
| `U1_PRT_DIS_P4` | local | U1.24 (USB2DN_DP4/PRT_DIS_P4), R114.2 |  |
| `U1_RBIAS` | local | U1.56 (RBIAS), R100.1 |  |
| `U1_RESET_N` | local | U1.42 (RESET_N), R102.2 |  |
| `U1_UP_TXDM` | local | U1.48 (USB3UP_TXDM), C141.1 |  |
| `U1_UP_TXDP` | local | U1.47 (USB3UP_TXDP), C140.1 |  |
| `U1_VBUS_DET` | local | U1.37 (VBUS_DET), R101.2 |  |
| `U1_XTALI` | local | U1.54 (XTALI/CLK_IN), Y1.1, C100.1 |  |
| `U1_XTALO` | local | U1.53 (XTALO), Y1.3, C101.1 |  |
| `USB3_0_DM` | **global** | U1.46 (USB2UP_DM) | m2-nvme |
| `USB3_0_DP` | **global** | U1.45 (USB2UP_DP) | m2-nvme |
| `USB3_0_RX_N` | **global** | C141.2 | m2-nvme |
| `USB3_0_RX_P` | **global** | C140.2 | m2-nvme |
| `USB3_0_TX_N` | **global** | U1.51 (USB3UP_RXDM) | m2-nvme |
| `USB3_0_TX_P` | **global** | U1.50 (USB3UP_RXDP) | m2-nvme |
| `+1V2` | **global** | U1.5 (VDD12), U1.12 (VDD12), U1.15 (VDD12), U1.21 (VDD12), U1.28 (VDD12), U1.33 (VDD12), U1.43 (VDD12), U1.49 (VDD12), C120.1, C121.1, C122.1, C123.1, C131.1 | power-bucks, usb3-hub-B |
| `+3V3` | **global** | U1.16 (VDD33), U1.31 (VDD33), U1.44 (VDD33), U1.55 (VDD33), C110.1, C111.1, C112.1, C113.1, C130.1, R101.1, R102.1, R113.1, R123.1, R114.1, R124.1 | cm5, power-bucks, usb3-hub-B |

### No connect

* U1: 19 (USB3DN_TXDP3), 20 (USB3DN_TXDM3), 22 (USB3DN_RXDP3), 23 (USB3DN_RXDM3), 26 (USB3DN_TXDP4), 27 (USB3DN_TXDM4), 29 (USB3DN_RXDP4), 30 (USB3DN_RXDM4), 32 (PRT_CTL4/GANG_PWR), 34 (PRT_CTL3), 35 (PRT_CTL2), 36 (PRT_CTL1), 38 (SPI_CLK/SMCLK), 39 (SPI_DO/SMDAT), 40 (SPI_DI/CFG_BC_EN)

### Notes

* Hub A: upstream on CM5 USB3-0. Downstream ports 1,2 -> bays 1,2. Ports 3,4 disabled by PRT_DIS straps (verify the strap resistor value against USB5744 §3.4.2).
* No SPI ROM and no SMBus pull-ups: the hub runs its internal ROM defaults. RESET_N has a pull-up only; add an RC if strap timing (1 ms hold) is a concern.
* Crystal: 25 MHz, CL 20 pF per datasheet table 10-10; 33 pF load caps assume ~3 pF stray, adjust to the chosen crystal.

## Sheet `usb3-hub-B` — USB5744 hub B on CM5 USB3-1, bays 3 and 4

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C200 | `Device:C` | 33p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C201 | `Device:C` | 33p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C210 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C211 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C212 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C213 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD33 decoupling |
| C220 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C221 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C222 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C223 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | VDD12 decoupling |
| C230 | `Device:C` | 4.7u 10V | `Capacitor_SMD:C_0603_1608Metric` |  |
| C231 | `Device:C` | 4.7u 10V | `Capacitor_SMD:C_0603_1608Metric` |  |
| C240 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 upstream TX AC coupling |
| C241 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 upstream TX AC coupling |
| C251 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN1 TX AC coupling |
| C252 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN2 TX AC coupling |
| C261 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN1 TX AC coupling |
| C262 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN2 TX AC coupling |
| R200 | `Device:R` | 12.0k 1% | `Resistor_SMD:R_0402_1005Metric` | RBIAS |
| R201 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | VBUS_DET to 3.3 V |
| R202 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RESET_N pull-up |
| R203 | `Device:R` | 200k | `Resistor_SMD:R_0402_1005Metric` | CFG_NON_REM: all ports removable |
| R213 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_P3 strap |
| R214 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_P4 strap |
| R223 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_M3 strap |
| R224 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PRT_DIS_M4 strap |
| U2 | `brain-drain:USB5744` | USB5744/2G | `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` |  |
| Y2 | `Device:Crystal_GND24` | 25MHz CL=20pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY3_USB2_DM` | **global** | U2.2 (USB2DN_DM1/PRT_DIS_M1) | bridge-3 |
| `BAY3_USB2_DP` | **global** | U2.1 (USB2DN_DP1/PRT_DIS_P1) | bridge-3 |
| `BAY3_USB3_RX_N` | **global** | C261.2 | bridge-3 |
| `BAY3_USB3_RX_P` | **global** | C251.2 | bridge-3 |
| `BAY3_USB3_TX_N` | **global** | U2.7 (USB3DN_RXDM1) | bridge-3 |
| `BAY3_USB3_TX_P` | **global** | U2.6 (USB3DN_RXDP1) | bridge-3 |
| `BAY4_USB2_DM` | **global** | U2.9 (USB2DN_DM2/PRT_DIS_M2) | bridge-4 |
| `BAY4_USB2_DP` | **global** | U2.8 (USB2DN_DP2/PRT_DIS_P2) | bridge-4 |
| `BAY4_USB3_RX_N` | **global** | C262.2 | bridge-4 |
| `BAY4_USB3_RX_P` | **global** | C252.2 | bridge-4 |
| `BAY4_USB3_TX_N` | **global** | U2.14 (USB3DN_RXDM2) | bridge-4 |
| `BAY4_USB3_TX_P` | **global** | U2.13 (USB3DN_RXDP2) | bridge-4 |
| `GND` | **global** | U2.EP (VSS), U2.52 (ATEST), R200.2, R203.2, Y2.2 (G), Y2.4 (G), C210.2, C211.2, C212.2, C213.2, C220.2, C221.2, C222.2, C223.2, C230.2, C231.2, C200.2, C201.2 | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A |
| `U2_CFG_NON_REM` | local | U2.41 (SPI_CE_N/CFG_NON_REM), R203.1 |  |
| `U2_DN1_TXDM` | local | U2.4 (USB3DN_TXDM1), C261.1 |  |
| `U2_DN1_TXDP` | local | U2.3 (USB3DN_TXDP1), C251.1 |  |
| `U2_DN2_TXDM` | local | U2.11 (USB3DN_TXDM2), C262.1 |  |
| `U2_DN2_TXDP` | local | U2.10 (USB3DN_TXDP2), C252.1 |  |
| `U2_PRT_DIS_M3` | local | U2.18 (USB2DN_DM3/PRT_DIS_M3), R223.2 |  |
| `U2_PRT_DIS_M4` | local | U2.25 (USB2DN_DM4/PRT_DIS_M4), R224.2 |  |
| `U2_PRT_DIS_P3` | local | U2.17 (USB2DN_DP3/PRT_DIS_P3), R213.2 |  |
| `U2_PRT_DIS_P4` | local | U2.24 (USB2DN_DP4/PRT_DIS_P4), R214.2 |  |
| `U2_RBIAS` | local | U2.56 (RBIAS), R200.1 |  |
| `U2_RESET_N` | local | U2.42 (RESET_N), R202.2 |  |
| `U2_UP_TXDM` | local | U2.48 (USB3UP_TXDM), C241.1 |  |
| `U2_UP_TXDP` | local | U2.47 (USB3UP_TXDP), C240.1 |  |
| `U2_VBUS_DET` | local | U2.37 (VBUS_DET), R201.2 |  |
| `U2_XTALI` | local | U2.54 (XTALI/CLK_IN), Y2.1, C200.1 |  |
| `U2_XTALO` | local | U2.53 (XTALO), Y2.3, C201.1 |  |
| `USB3_1_DM` | **global** | U2.46 (USB2UP_DM) | m2-nvme |
| `USB3_1_DP` | **global** | U2.45 (USB2UP_DP) | m2-nvme |
| `USB3_1_RX_N` | **global** | C241.2 | m2-nvme |
| `USB3_1_RX_P` | **global** | C240.2 | m2-nvme |
| `USB3_1_TX_N` | **global** | U2.51 (USB3UP_RXDM) | m2-nvme |
| `USB3_1_TX_P` | **global** | U2.50 (USB3UP_RXDP) | m2-nvme |
| `+1V2` | **global** | U2.5 (VDD12), U2.12 (VDD12), U2.15 (VDD12), U2.21 (VDD12), U2.28 (VDD12), U2.33 (VDD12), U2.43 (VDD12), U2.49 (VDD12), C220.1, C221.1, C222.1, C223.1, C231.1 | power-bucks, usb3-hub-A |
| `+3V3` | **global** | U2.16 (VDD33), U2.31 (VDD33), U2.44 (VDD33), U2.55 (VDD33), C210.1, C211.1, C212.1, C213.1, C230.1, R201.1, R202.1, R213.1, R223.1, R214.1, R224.1 | cm5, power-bucks, usb3-hub-A |

### No connect

* U2: 19 (USB3DN_TXDP3), 20 (USB3DN_TXDM3), 22 (USB3DN_RXDP3), 23 (USB3DN_RXDM3), 26 (USB3DN_TXDP4), 27 (USB3DN_TXDM4), 29 (USB3DN_RXDP4), 30 (USB3DN_RXDM4), 32 (PRT_CTL4/GANG_PWR), 34 (PRT_CTL3), 35 (PRT_CTL2), 36 (PRT_CTL1), 38 (SPI_CLK/SMCLK), 39 (SPI_DO/SMDAT), 40 (SPI_DI/CFG_BC_EN)

### Notes

* Hub B: upstream on CM5 USB3-1. Downstream ports 1,2 -> bays 3,4. Ports 3,4 disabled by PRT_DIS straps (verify the strap resistor value against USB5744 §3.4.2).
* No SPI ROM and no SMBus pull-ups: the hub runs its internal ROM defaults. RESET_N has a pull-up only; add an RC if strap timing (1 ms hold) is a concern.
* Crystal: 25 MHz, CL 20 pF per datasheet table 10-10; 33 pF load caps assume ~3 pF stray, adjust to the chosen crystal.

## Sheet `bridge-1` — Bay 1: ASM1153E USB-SATA bridge and 22-pin SATA receptacle

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C1000 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1001 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1002 | `Device:C` | 2.2u | `Capacitor_SMD:C_0603_1608Metric` | RST# delay |
| C1003 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | core rail |
| C1004 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCIN bypass |
| C1005 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCO 3.3 V out |
| C1006 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1007 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1008 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1009 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1010 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1011 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1020 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1021 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1030 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX+ AC coupling |
| C1031 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX- AC coupling |
| C1032 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX+ AC coupling |
| C1033 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX- AC coupling |
| D10 | `Device:LED` | blue bay activity | `LED_THT:LED_D3.0mm` |  |
| J10 | `brain-drain:SATA22` | SATA 22-pin | `brain-drain:SATA_22pin_Receptacle_RA` |  |
| L10 | `Device:L` | 4.7u 1A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` | core switcher inductor (value per ASMedia reference design, verify) |
| R1000 | `Device:R` | 12.1k 1% | `Resistor_SMD:R_0402_1005Metric` | REXT |
| R1001 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RST# pull-up |
| R1002 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| U10 | `brain-drain:ASM1153E` | ASM1153E | `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm` |  |
| Y10 | `Device:Crystal_GND24` | 30MHz CL=16pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY1_LED_A` | local | R1002.2, D10.2 (A) |  |
| `BAY1_SATA_A_N` | local | C1031.2, J10.S3 (A-) |  |
| `BAY1_SATA_A_P` | local | C1030.2, J10.S2 (A+) |  |
| `BAY1_SATA_B_N` | local | J10.S5 (B-), C1033.1 |  |
| `BAY1_SATA_B_P` | local | J10.S6 (B+), C1032.1 |  |
| `BAY1_USB2_DM` | **global** | U10.16 (UDM) | usb3-hub-A |
| `BAY1_USB2_DP` | **global** | U10.15 (UDP) | usb3-hub-A |
| `BAY1_USB3_RX_N` | **global** | U10.22 (URXN) | usb3-hub-A |
| `BAY1_USB3_RX_P` | **global** | U10.23 (URXP) | usb3-hub-A |
| `BAY1_USB3_TX_N` | **global** | C1021.2 | usb3-hub-A |
| `BAY1_USB3_TX_P` | **global** | C1020.2 | usb3-hub-A |
| `GND` | **global** | U10.47 (PGND), U10.21 (GNDA), U10.31 (GNDA), U10.49 (GND), U10.42 (TEST_EN), R1000.2, C1002.2, Y10.2 (G), Y10.4 (G), C1000.2, C1001.2, C1003.2, C1004.2, C1005.2, C1006.2, C1007.2, C1008.2, C1009.2, C1010.2, C1011.2, J10.S1 (GND), J10.S4 (GND), J10.S7 (GND), J10.P4 (GND), J10.P5 (GND), J10.P6 (GND), J10.P10 (GND), J10.P12 (GND) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `U10_LED` | local | D10.1 (K), U10.43 (GPIO0) |  |
| `U10_LXI` | local | U10.48 (LXI), L10.1 |  |
| `U10_REXT` | local | U10.17 (REXT), R1000.1 |  |
| `U10_RST` | local | U10.38 (RST#), R1001.2, C1002.1 |  |
| `U10_SRXN` | local | C1033.2, U10.30 (SRXN) |  |
| `U10_SRXP` | local | C1032.2, U10.29 (SRXP) |  |
| `U10_STXN` | local | U10.32 (STXN), C1031.1 |  |
| `U10_STXP` | local | U10.33 (STXP), C1030.1 |  |
| `U10_UTXN` | local | U10.19 (UTXN), C1021.1 |  |
| `U10_UTXP` | local | U10.20 (UTXP), C1020.1 |  |
| `U10_VCCO` | local | U10.12 (VCCO), C1005.1, U10.4 (VCC), U10.39 (VCC), U10.14 (VCCU), U10.18 (VCCU), U10.34 (VCCS), U10.27 (VCCTXL), C1008.1, C1009.1, C1010.1, C1011.1, R1001.1, R1002.1 |  |
| `U10_VDD_CORE` | **global** | L10.2, C1003.1, U10.7 (VDD), U10.36 (VDD), U10.46 (VDD), U10.13 (VDDU), U10.24 (VDDU), U10.28 (VDDS), C1006.1, C1007.1 |  |
| `U10_XI` | local | U10.25 (XI), Y10.1, C1000.1 |  |
| `U10_XO` | local | U10.26 (XO), Y10.3, C1001.1 |  |
| `12V_BAY1` | **global** | J10.P13 (12V), J10.P14 (12V), J10.P15 (12V) | bay-switch-1 |
| `5V_BAY1` | **global** | J10.P7 (5V), J10.P8 (5V), J10.P9 (5V) | bay-switch-1 |
| `5V_SYS` | **global** | U10.10 (VBUS), U10.11 (VBUS_LDO), U10.1 (VCCIN), C1004.1 | bridge-2, bridge-3, bridge-4, cm5, power-bucks |

### No connect

* J10: P1 (3V3), P11 (DAS), P2 (3V3), P3 (3V3_PWDIS)
* U10: 2 (I2C_DATA), 3 (I2C_CLK), 35 (GPIO7), 37 (GPIO6), 40 (UART_RX), 41 (UART_TX), 44 (GPIO1), 45 (HDDPC), 5 (GPIO5), 6 (GPIO4), 8 (GPIO3), 9 (GPIO2)

### Notes

* ASM1153E runs from 5 V only: VBUS_LDO -> VCCO (3.3 V, feeds VCC/VCCU/VCCS/VCCTXL) and VCCIN -> LXI switcher -> 1.05 V core (VDD/VDDU/VDDS). Datasheet notes VCCIN must be tied to 5 V.
* Clock straps GPIO3/GPIO7 left at their internal pull-up default (11) = 30 MHz crystal, so no strap resistors. GPIO6 default = I2C mode, no SPI ROM.
* SATA P1-P3 (3.3 V) are not connected on purpose: P3 is PWDIS on SATA 3.3 drives and a 3.3 V supply there keeps them from spinning up.
* Bay activity LED assumed on GPIO0 (bridge firmware default): confirm on the bench; GPIO1 is the alternative.

## Sheet `bay-switch-1` — Bay 1: switched 12 V and 5 V with soft-start and PTC fuses

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C310 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| C410 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| F10 | `Device:Polyfuse` | 3A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| F14 | `Device:Polyfuse` | 2A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| Q31 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 12 V switch |
| Q41 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 5 V switch |
| Q51 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 12 V gate driver |
| Q61 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 5 V gate driver |
| R310 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q3 gate pull-up (off) |
| R311 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R410 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q4 gate pull-up (off) |
| R411 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R510 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | BAY_EN pull-down: off at boot |
| R511 | `Device:R` | 1k | `Resistor_SMD:R_0402_1005Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY1_EN_G` | local | R511.2, Q51.1 (G), Q61.1 (G) |  |
| `BAY_EN1` | **global** | R511.1, R510.1 | cm5 |
| `GND` | **global** | R510.2, Q51.2 (S), Q61.2 (S) | bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `Q31_G` | local | Q31.1 (G), R310.2, C310.2, R311.1 |  |
| `Q41_G` | local | Q41.1 (G), R410.2, C410.2, R411.1 |  |
| `Q51_D` | local | R311.2, Q51.3 (D) |  |
| `Q61_D` | local | R411.2, Q61.3 (D) |  |
| `+12V` | **global** | Q31.2 (S), R310.1, C310.1 | bay-switch-2, bay-switch-3, bay-switch-4, m2-nvme, power-bucks, power-input |
| `12V_BAY1` | **global** | F10.2 | bridge-1 |
| `12V_BAY1_SW` | local | Q31.3 (D), F10.1 |  |
| `5V_BAY1` | **global** | F14.2 | bridge-1 |
| `5V_BAY1_SW` | local | Q41.3 (D), F14.1 |  |
| `5V_HDD` | **global** | Q41.2 (S), R410.1, C410.1 | bay-switch-2, bay-switch-3, bay-switch-4, power-bucks |

### Notes

* P-FET high-side switch: 100k gate pull-up holds it off; the 2N7002 pulls the gate down through 10k with 100n gate-source, ~1 ms ramp so the drive's bulk caps do not trip the fuse. BAY_EN pull-down keeps the bay off through boot.

## Sheet `bridge-2` — Bay 2: ASM1153E USB-SATA bridge and 22-pin SATA receptacle

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C1100 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1101 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1102 | `Device:C` | 2.2u | `Capacitor_SMD:C_0603_1608Metric` | RST# delay |
| C1103 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | core rail |
| C1104 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCIN bypass |
| C1105 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCO 3.3 V out |
| C1106 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1107 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1108 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1109 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1110 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1111 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1120 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1121 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1130 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX+ AC coupling |
| C1131 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX- AC coupling |
| C1132 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX+ AC coupling |
| C1133 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX- AC coupling |
| D11 | `Device:LED` | blue bay activity | `LED_THT:LED_D3.0mm` |  |
| J11 | `brain-drain:SATA22` | SATA 22-pin | `brain-drain:SATA_22pin_Receptacle_RA` |  |
| L11 | `Device:L` | 4.7u 1A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` | core switcher inductor (value per ASMedia reference design, verify) |
| R1100 | `Device:R` | 12.1k 1% | `Resistor_SMD:R_0402_1005Metric` | REXT |
| R1101 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RST# pull-up |
| R1102 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| U11 | `brain-drain:ASM1153E` | ASM1153E | `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm` |  |
| Y11 | `Device:Crystal_GND24` | 30MHz CL=16pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY2_LED_A` | local | R1102.2, D11.2 (A) |  |
| `BAY2_SATA_A_N` | local | C1131.2, J11.S3 (A-) |  |
| `BAY2_SATA_A_P` | local | C1130.2, J11.S2 (A+) |  |
| `BAY2_SATA_B_N` | local | J11.S5 (B-), C1133.1 |  |
| `BAY2_SATA_B_P` | local | J11.S6 (B+), C1132.1 |  |
| `BAY2_USB2_DM` | **global** | U11.16 (UDM) | usb3-hub-A |
| `BAY2_USB2_DP` | **global** | U11.15 (UDP) | usb3-hub-A |
| `BAY2_USB3_RX_N` | **global** | U11.22 (URXN) | usb3-hub-A |
| `BAY2_USB3_RX_P` | **global** | U11.23 (URXP) | usb3-hub-A |
| `BAY2_USB3_TX_N` | **global** | C1121.2 | usb3-hub-A |
| `BAY2_USB3_TX_P` | **global** | C1120.2 | usb3-hub-A |
| `GND` | **global** | U11.47 (PGND), U11.21 (GNDA), U11.31 (GNDA), U11.49 (GND), U11.42 (TEST_EN), R1100.2, C1102.2, Y11.2 (G), Y11.4 (G), C1100.2, C1101.2, C1103.2, C1104.2, C1105.2, C1106.2, C1107.2, C1108.2, C1109.2, C1110.2, C1111.2, J11.S1 (GND), J11.S4 (GND), J11.S7 (GND), J11.P4 (GND), J11.P5 (GND), J11.P6 (GND), J11.P10 (GND), J11.P12 (GND) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `U11_LED` | local | D11.1 (K), U11.43 (GPIO0) |  |
| `U11_LXI` | local | U11.48 (LXI), L11.1 |  |
| `U11_REXT` | local | U11.17 (REXT), R1100.1 |  |
| `U11_RST` | local | U11.38 (RST#), R1101.2, C1102.1 |  |
| `U11_SRXN` | local | C1133.2, U11.30 (SRXN) |  |
| `U11_SRXP` | local | C1132.2, U11.29 (SRXP) |  |
| `U11_STXN` | local | U11.32 (STXN), C1131.1 |  |
| `U11_STXP` | local | U11.33 (STXP), C1130.1 |  |
| `U11_UTXN` | local | U11.19 (UTXN), C1121.1 |  |
| `U11_UTXP` | local | U11.20 (UTXP), C1120.1 |  |
| `U11_VCCO` | local | U11.12 (VCCO), C1105.1, U11.4 (VCC), U11.39 (VCC), U11.14 (VCCU), U11.18 (VCCU), U11.34 (VCCS), U11.27 (VCCTXL), C1108.1, C1109.1, C1110.1, C1111.1, R1101.1, R1102.1 |  |
| `U11_VDD_CORE` | **global** | L11.2, C1103.1, U11.7 (VDD), U11.36 (VDD), U11.46 (VDD), U11.13 (VDDU), U11.24 (VDDU), U11.28 (VDDS), C1106.1, C1107.1 |  |
| `U11_XI` | local | U11.25 (XI), Y11.1, C1100.1 |  |
| `U11_XO` | local | U11.26 (XO), Y11.3, C1101.1 |  |
| `12V_BAY2` | **global** | J11.P13 (12V), J11.P14 (12V), J11.P15 (12V) | bay-switch-2 |
| `5V_BAY2` | **global** | J11.P7 (5V), J11.P8 (5V), J11.P9 (5V) | bay-switch-2 |
| `5V_SYS` | **global** | U11.10 (VBUS), U11.11 (VBUS_LDO), U11.1 (VCCIN), C1104.1 | bridge-1, bridge-3, bridge-4, cm5, power-bucks |

### No connect

* J11: P1 (3V3), P11 (DAS), P2 (3V3), P3 (3V3_PWDIS)
* U11: 2 (I2C_DATA), 3 (I2C_CLK), 35 (GPIO7), 37 (GPIO6), 40 (UART_RX), 41 (UART_TX), 44 (GPIO1), 45 (HDDPC), 5 (GPIO5), 6 (GPIO4), 8 (GPIO3), 9 (GPIO2)

### Notes

* ASM1153E runs from 5 V only: VBUS_LDO -> VCCO (3.3 V, feeds VCC/VCCU/VCCS/VCCTXL) and VCCIN -> LXI switcher -> 1.05 V core (VDD/VDDU/VDDS). Datasheet notes VCCIN must be tied to 5 V.
* Clock straps GPIO3/GPIO7 left at their internal pull-up default (11) = 30 MHz crystal, so no strap resistors. GPIO6 default = I2C mode, no SPI ROM.
* SATA P1-P3 (3.3 V) are not connected on purpose: P3 is PWDIS on SATA 3.3 drives and a 3.3 V supply there keeps them from spinning up.
* Bay activity LED assumed on GPIO0 (bridge firmware default): confirm on the bench; GPIO1 is the alternative.

## Sheet `bay-switch-2` — Bay 2: switched 12 V and 5 V with soft-start and PTC fuses

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C320 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| C420 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| F11 | `Device:Polyfuse` | 3A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| F15 | `Device:Polyfuse` | 2A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| Q32 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 12 V switch |
| Q42 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 5 V switch |
| Q52 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 12 V gate driver |
| Q62 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 5 V gate driver |
| R320 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q3 gate pull-up (off) |
| R321 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R420 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q4 gate pull-up (off) |
| R421 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R520 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | BAY_EN pull-down: off at boot |
| R521 | `Device:R` | 1k | `Resistor_SMD:R_0402_1005Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY2_EN_G` | local | R521.2, Q52.1 (G), Q62.1 (G) |  |
| `BAY_EN2` | **global** | R521.1, R520.1 | cm5 |
| `GND` | **global** | R520.2, Q52.2 (S), Q62.2 (S) | bay-switch-1, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `Q32_G` | local | Q32.1 (G), R320.2, C320.2, R321.1 |  |
| `Q42_G` | local | Q42.1 (G), R420.2, C420.2, R421.1 |  |
| `Q52_D` | local | R321.2, Q52.3 (D) |  |
| `Q62_D` | local | R421.2, Q62.3 (D) |  |
| `+12V` | **global** | Q32.2 (S), R320.1, C320.1 | bay-switch-1, bay-switch-3, bay-switch-4, m2-nvme, power-bucks, power-input |
| `12V_BAY2` | **global** | F11.2 | bridge-2 |
| `12V_BAY2_SW` | local | Q32.3 (D), F11.1 |  |
| `5V_BAY2` | **global** | F15.2 | bridge-2 |
| `5V_BAY2_SW` | local | Q42.3 (D), F15.1 |  |
| `5V_HDD` | **global** | Q42.2 (S), R420.1, C420.1 | bay-switch-1, bay-switch-3, bay-switch-4, power-bucks |

### Notes

* P-FET high-side switch: 100k gate pull-up holds it off; the 2N7002 pulls the gate down through 10k with 100n gate-source, ~1 ms ramp so the drive's bulk caps do not trip the fuse. BAY_EN pull-down keeps the bay off through boot.

## Sheet `bridge-3` — Bay 3: ASM1153E USB-SATA bridge and 22-pin SATA receptacle

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C1200 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1201 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1202 | `Device:C` | 2.2u | `Capacitor_SMD:C_0603_1608Metric` | RST# delay |
| C1203 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | core rail |
| C1204 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCIN bypass |
| C1205 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCO 3.3 V out |
| C1206 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1207 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1208 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1209 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1210 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1211 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1220 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1221 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1230 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX+ AC coupling |
| C1231 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX- AC coupling |
| C1232 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX+ AC coupling |
| C1233 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX- AC coupling |
| D12 | `Device:LED` | blue bay activity | `LED_THT:LED_D3.0mm` |  |
| J12 | `brain-drain:SATA22` | SATA 22-pin | `brain-drain:SATA_22pin_Receptacle_RA` |  |
| L12 | `Device:L` | 4.7u 1A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` | core switcher inductor (value per ASMedia reference design, verify) |
| R1200 | `Device:R` | 12.1k 1% | `Resistor_SMD:R_0402_1005Metric` | REXT |
| R1201 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RST# pull-up |
| R1202 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| U12 | `brain-drain:ASM1153E` | ASM1153E | `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm` |  |
| Y12 | `Device:Crystal_GND24` | 30MHz CL=16pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY3_LED_A` | local | R1202.2, D12.2 (A) |  |
| `BAY3_SATA_A_N` | local | C1231.2, J12.S3 (A-) |  |
| `BAY3_SATA_A_P` | local | C1230.2, J12.S2 (A+) |  |
| `BAY3_SATA_B_N` | local | J12.S5 (B-), C1233.1 |  |
| `BAY3_SATA_B_P` | local | J12.S6 (B+), C1232.1 |  |
| `BAY3_USB2_DM` | **global** | U12.16 (UDM) | usb3-hub-B |
| `BAY3_USB2_DP` | **global** | U12.15 (UDP) | usb3-hub-B |
| `BAY3_USB3_RX_N` | **global** | U12.22 (URXN) | usb3-hub-B |
| `BAY3_USB3_RX_P` | **global** | U12.23 (URXP) | usb3-hub-B |
| `BAY3_USB3_TX_N` | **global** | C1221.2 | usb3-hub-B |
| `BAY3_USB3_TX_P` | **global** | C1220.2 | usb3-hub-B |
| `GND` | **global** | U12.47 (PGND), U12.21 (GNDA), U12.31 (GNDA), U12.49 (GND), U12.42 (TEST_EN), R1200.2, C1202.2, Y12.2 (G), Y12.4 (G), C1200.2, C1201.2, C1203.2, C1204.2, C1205.2, C1206.2, C1207.2, C1208.2, C1209.2, C1210.2, C1211.2, J12.S1 (GND), J12.S4 (GND), J12.S7 (GND), J12.P4 (GND), J12.P5 (GND), J12.P6 (GND), J12.P10 (GND), J12.P12 (GND) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `U12_LED` | local | D12.1 (K), U12.43 (GPIO0) |  |
| `U12_LXI` | local | U12.48 (LXI), L12.1 |  |
| `U12_REXT` | local | U12.17 (REXT), R1200.1 |  |
| `U12_RST` | local | U12.38 (RST#), R1201.2, C1202.1 |  |
| `U12_SRXN` | local | C1233.2, U12.30 (SRXN) |  |
| `U12_SRXP` | local | C1232.2, U12.29 (SRXP) |  |
| `U12_STXN` | local | U12.32 (STXN), C1231.1 |  |
| `U12_STXP` | local | U12.33 (STXP), C1230.1 |  |
| `U12_UTXN` | local | U12.19 (UTXN), C1221.1 |  |
| `U12_UTXP` | local | U12.20 (UTXP), C1220.1 |  |
| `U12_VCCO` | local | U12.12 (VCCO), C1205.1, U12.4 (VCC), U12.39 (VCC), U12.14 (VCCU), U12.18 (VCCU), U12.34 (VCCS), U12.27 (VCCTXL), C1208.1, C1209.1, C1210.1, C1211.1, R1201.1, R1202.1 |  |
| `U12_VDD_CORE` | **global** | L12.2, C1203.1, U12.7 (VDD), U12.36 (VDD), U12.46 (VDD), U12.13 (VDDU), U12.24 (VDDU), U12.28 (VDDS), C1206.1, C1207.1 |  |
| `U12_XI` | local | U12.25 (XI), Y12.1, C1200.1 |  |
| `U12_XO` | local | U12.26 (XO), Y12.3, C1201.1 |  |
| `12V_BAY3` | **global** | J12.P13 (12V), J12.P14 (12V), J12.P15 (12V) | bay-switch-3 |
| `5V_BAY3` | **global** | J12.P7 (5V), J12.P8 (5V), J12.P9 (5V) | bay-switch-3 |
| `5V_SYS` | **global** | U12.10 (VBUS), U12.11 (VBUS_LDO), U12.1 (VCCIN), C1204.1 | bridge-1, bridge-2, bridge-4, cm5, power-bucks |

### No connect

* J12: P1 (3V3), P11 (DAS), P2 (3V3), P3 (3V3_PWDIS)
* U12: 2 (I2C_DATA), 3 (I2C_CLK), 35 (GPIO7), 37 (GPIO6), 40 (UART_RX), 41 (UART_TX), 44 (GPIO1), 45 (HDDPC), 5 (GPIO5), 6 (GPIO4), 8 (GPIO3), 9 (GPIO2)

### Notes

* ASM1153E runs from 5 V only: VBUS_LDO -> VCCO (3.3 V, feeds VCC/VCCU/VCCS/VCCTXL) and VCCIN -> LXI switcher -> 1.05 V core (VDD/VDDU/VDDS). Datasheet notes VCCIN must be tied to 5 V.
* Clock straps GPIO3/GPIO7 left at their internal pull-up default (11) = 30 MHz crystal, so no strap resistors. GPIO6 default = I2C mode, no SPI ROM.
* SATA P1-P3 (3.3 V) are not connected on purpose: P3 is PWDIS on SATA 3.3 drives and a 3.3 V supply there keeps them from spinning up.
* Bay activity LED assumed on GPIO0 (bridge firmware default): confirm on the bench; GPIO1 is the alternative.

## Sheet `bay-switch-3` — Bay 3: switched 12 V and 5 V with soft-start and PTC fuses

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C330 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| C430 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| F12 | `Device:Polyfuse` | 3A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| F16 | `Device:Polyfuse` | 2A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| Q33 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 12 V switch |
| Q43 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 5 V switch |
| Q53 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 12 V gate driver |
| Q63 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 5 V gate driver |
| R330 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q3 gate pull-up (off) |
| R331 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R430 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q4 gate pull-up (off) |
| R431 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R530 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | BAY_EN pull-down: off at boot |
| R531 | `Device:R` | 1k | `Resistor_SMD:R_0402_1005Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY3_EN_G` | local | R531.2, Q53.1 (G), Q63.1 (G) |  |
| `BAY_EN3` | **global** | R531.1, R530.1 | cm5 |
| `GND` | **global** | R530.2, Q53.2 (S), Q63.2 (S) | bay-switch-1, bay-switch-2, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `Q33_G` | local | Q33.1 (G), R330.2, C330.2, R331.1 |  |
| `Q43_G` | local | Q43.1 (G), R430.2, C430.2, R431.1 |  |
| `Q53_D` | local | R331.2, Q53.3 (D) |  |
| `Q63_D` | local | R431.2, Q63.3 (D) |  |
| `+12V` | **global** | Q33.2 (S), R330.1, C330.1 | bay-switch-1, bay-switch-2, bay-switch-4, m2-nvme, power-bucks, power-input |
| `12V_BAY3` | **global** | F12.2 | bridge-3 |
| `12V_BAY3_SW` | local | Q33.3 (D), F12.1 |  |
| `5V_BAY3` | **global** | F16.2 | bridge-3 |
| `5V_BAY3_SW` | local | Q43.3 (D), F16.1 |  |
| `5V_HDD` | **global** | Q43.2 (S), R430.1, C430.1 | bay-switch-1, bay-switch-2, bay-switch-4, power-bucks |

### Notes

* P-FET high-side switch: 100k gate pull-up holds it off; the 2N7002 pulls the gate down through 10k with 100n gate-source, ~1 ms ramp so the drive's bulk caps do not trip the fuse. BAY_EN pull-down keeps the bay off through boot.

## Sheet `bridge-4` — Bay 4: ASM1153E USB-SATA bridge and 22-pin SATA receptacle

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C1300 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1301 | `Device:C` | 22p | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1302 | `Device:C` | 2.2u | `Capacitor_SMD:C_0603_1608Metric` | RST# delay |
| C1303 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | core rail |
| C1304 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCIN bypass |
| C1305 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` | VCCO 3.3 V out |
| C1306 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1307 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1308 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1309 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1310 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1311 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` |  |
| C1320 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1321 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 TX AC coupling |
| C1330 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX+ AC coupling |
| C1331 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA TX- AC coupling |
| C1332 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX+ AC coupling |
| C1333 | `Device:C` | 10n | `Capacitor_SMD:C_0402_1005Metric` | SATA RX- AC coupling |
| D13 | `Device:LED` | blue bay activity | `LED_THT:LED_D3.0mm` |  |
| J13 | `brain-drain:SATA22` | SATA 22-pin | `brain-drain:SATA_22pin_Receptacle_RA` |  |
| L13 | `Device:L` | 4.7u 1A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` | core switcher inductor (value per ASMedia reference design, verify) |
| R1300 | `Device:R` | 12.1k 1% | `Resistor_SMD:R_0402_1005Metric` | REXT |
| R1301 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RST# pull-up |
| R1302 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| U13 | `brain-drain:ASM1153E` | ASM1153E | `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm` |  |
| Y13 | `Device:Crystal_GND24` | 30MHz CL=16pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY4_LED_A` | local | R1302.2, D13.2 (A) |  |
| `BAY4_SATA_A_N` | local | C1331.2, J13.S3 (A-) |  |
| `BAY4_SATA_A_P` | local | C1330.2, J13.S2 (A+) |  |
| `BAY4_SATA_B_N` | local | J13.S5 (B-), C1333.1 |  |
| `BAY4_SATA_B_P` | local | J13.S6 (B+), C1332.1 |  |
| `BAY4_USB2_DM` | **global** | U13.16 (UDM) | usb3-hub-B |
| `BAY4_USB2_DP` | **global** | U13.15 (UDP) | usb3-hub-B |
| `BAY4_USB3_RX_N` | **global** | U13.22 (URXN) | usb3-hub-B |
| `BAY4_USB3_RX_P` | **global** | U13.23 (URXP) | usb3-hub-B |
| `BAY4_USB3_TX_N` | **global** | C1321.2 | usb3-hub-B |
| `BAY4_USB3_TX_P` | **global** | C1320.2 | usb3-hub-B |
| `GND` | **global** | U13.47 (PGND), U13.21 (GNDA), U13.31 (GNDA), U13.49 (GND), U13.42 (TEST_EN), R1300.2, C1302.2, Y13.2 (G), Y13.4 (G), C1300.2, C1301.2, C1303.2, C1304.2, C1305.2, C1306.2, C1307.2, C1308.2, C1309.2, C1310.2, C1311.2, J13.S1 (GND), J13.S4 (GND), J13.S7 (GND), J13.P4 (GND), J13.P5 (GND), J13.P6 (GND), J13.P10 (GND), J13.P12 (GND) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `U13_LED` | local | D13.1 (K), U13.43 (GPIO0) |  |
| `U13_LXI` | local | U13.48 (LXI), L13.1 |  |
| `U13_REXT` | local | U13.17 (REXT), R1300.1 |  |
| `U13_RST` | local | U13.38 (RST#), R1301.2, C1302.1 |  |
| `U13_SRXN` | local | C1333.2, U13.30 (SRXN) |  |
| `U13_SRXP` | local | C1332.2, U13.29 (SRXP) |  |
| `U13_STXN` | local | U13.32 (STXN), C1331.1 |  |
| `U13_STXP` | local | U13.33 (STXP), C1330.1 |  |
| `U13_UTXN` | local | U13.19 (UTXN), C1321.1 |  |
| `U13_UTXP` | local | U13.20 (UTXP), C1320.1 |  |
| `U13_VCCO` | local | U13.12 (VCCO), C1305.1, U13.4 (VCC), U13.39 (VCC), U13.14 (VCCU), U13.18 (VCCU), U13.34 (VCCS), U13.27 (VCCTXL), C1308.1, C1309.1, C1310.1, C1311.1, R1301.1, R1302.1 |  |
| `U13_VDD_CORE` | **global** | L13.2, C1303.1, U13.7 (VDD), U13.36 (VDD), U13.46 (VDD), U13.13 (VDDU), U13.24 (VDDU), U13.28 (VDDS), C1306.1, C1307.1 |  |
| `U13_XI` | local | U13.25 (XI), Y13.1, C1300.1 |  |
| `U13_XO` | local | U13.26 (XO), Y13.3, C1301.1 |  |
| `12V_BAY4` | **global** | J13.P13 (12V), J13.P14 (12V), J13.P15 (12V) | bay-switch-4 |
| `5V_BAY4` | **global** | J13.P7 (5V), J13.P8 (5V), J13.P9 (5V) | bay-switch-4 |
| `5V_SYS` | **global** | U13.10 (VBUS), U13.11 (VBUS_LDO), U13.1 (VCCIN), C1304.1 | bridge-1, bridge-2, bridge-3, cm5, power-bucks |

### No connect

* J13: P1 (3V3), P11 (DAS), P2 (3V3), P3 (3V3_PWDIS)
* U13: 2 (I2C_DATA), 3 (I2C_CLK), 35 (GPIO7), 37 (GPIO6), 40 (UART_RX), 41 (UART_TX), 44 (GPIO1), 45 (HDDPC), 5 (GPIO5), 6 (GPIO4), 8 (GPIO3), 9 (GPIO2)

### Notes

* ASM1153E runs from 5 V only: VBUS_LDO -> VCCO (3.3 V, feeds VCC/VCCU/VCCS/VCCTXL) and VCCIN -> LXI switcher -> 1.05 V core (VDD/VDDU/VDDS). Datasheet notes VCCIN must be tied to 5 V.
* Clock straps GPIO3/GPIO7 left at their internal pull-up default (11) = 30 MHz crystal, so no strap resistors. GPIO6 default = I2C mode, no SPI ROM.
* SATA P1-P3 (3.3 V) are not connected on purpose: P3 is PWDIS on SATA 3.3 drives and a 3.3 V supply there keeps them from spinning up.
* Bay activity LED assumed on GPIO0 (bridge firmware default): confirm on the bench; GPIO1 is the alternative.

## Sheet `bay-switch-4` — Bay 4: switched 12 V and 5 V with soft-start and PTC fuses

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C340 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| C440 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | soft-start G-S |
| F13 | `Device:Polyfuse` | 3A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| F17 | `Device:Polyfuse` | 2A hold 1812 | `Fuse:Fuse_1812_4532Metric` |  |
| Q34 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 12 V switch |
| Q44 | `Transistor_FET:Q_PMOS_GSD` | P-FET -30V 6A DFN3x3 | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm` | 5 V switch |
| Q54 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 12 V gate driver |
| Q64 | `Transistor_FET:2N7002` | 2N7002 | `Package_TO_SOT_SMD:SOT-23` | 5 V gate driver |
| R340 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q3 gate pull-up (off) |
| R341 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R440 | `Device:R` | 100k | `Resistor_SMD:R_0402_1005Metric` | Q4 gate pull-up (off) |
| R441 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | soft-start series |
| R540 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | BAY_EN pull-down: off at boot |
| R541 | `Device:R` | 1k | `Resistor_SMD:R_0402_1005Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY4_EN_G` | local | R541.2, Q54.1 (G), Q64.1 (G) |  |
| `BAY_EN4` | **global** | R541.1, R540.1 | cm5 |
| `GND` | **global** | R540.2, Q54.2 (S), Q64.2 (S) | bay-switch-1, bay-switch-2, bay-switch-3, bridge-1, bridge-2, bridge-3, bridge-4, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `Q34_G` | local | Q34.1 (G), R340.2, C340.2, R341.1 |  |
| `Q44_G` | local | Q44.1 (G), R440.2, C440.2, R441.1 |  |
| `Q54_D` | local | R341.2, Q54.3 (D) |  |
| `Q64_D` | local | R441.2, Q64.3 (D) |  |
| `+12V` | **global** | Q34.2 (S), R340.1, C340.1 | bay-switch-1, bay-switch-2, bay-switch-3, m2-nvme, power-bucks, power-input |
| `12V_BAY4` | **global** | F13.2 | bridge-4 |
| `12V_BAY4_SW` | local | Q34.3 (D), F13.1 |  |
| `5V_BAY4` | **global** | F17.2 | bridge-4 |
| `5V_BAY4_SW` | local | Q44.3 (D), F17.1 |  |
| `5V_HDD` | **global** | Q44.2 (S), R440.1, C440.1 | bay-switch-1, bay-switch-2, bay-switch-3, power-bucks |

### Notes

* P-FET high-side switch: 100k gate pull-up holds it off; the 2N7002 pulls the gate down through 10k with 100n gate-source, ~1 ms ramp so the drive's bulk caps do not trip the fuse. BAY_EN pull-down keeps the bay off through boot.

## Sheet `m2-nvme` — Bay 5: M.2 M-key on PCIe Gen3 x1, 3V3_M2 buck + load switch, door switch

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| C500 | `Device:C` | 10u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C501 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C502 | `Device:C` | 1n | `Capacitor_SMD:C_0402_1005Metric` | CT slew |
| C5100 | `Device:C` | 10u 25V | `Capacitor_SMD:C_1210_3225Metric` |  |
| C5101 | `Device:C` | 100n 10V | `Capacitor_SMD:C_0402_1005Metric` | BST |
| C5102 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| C5103 | `Device:C` | 22u 10V | `Capacitor_SMD:C_0805_2012Metric` |  |
| D50 | `Device:LED` | blue M.2 activity | `LED_THT:LED_D3.0mm` |  |
| J50 | `brain-drain:M2_MKEY` | M.2 M-key | `brain-drain:M2_Socket3_MKey_CM5IO` |  |
| L51 | `Device:L` | 4.7u 3A | `Inductor_SMD:L_Taiyo-Yuden_NR-40xx` |  |
| M1 (unit 4) | `brain-drain:CM5` | CM5002016 | `brain-drain:Raspberry-Pi-5-Compute-Module` |  |
| R500 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | M2_PWR_EN pull-down |
| R501 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | PEDET pull-up |
| R502 | `Device:R` | 0R (cap DNP alt) | `Capacitor_SMD:C_0402_1005Metric` | PERp0 series: 0R populated, 100n alternative |
| R503 | `Device:R` | 0R (cap DNP alt) | `Capacitor_SMD:C_0402_1005Metric` | PERn0 series: 0R populated, 100n alternative |
| R504 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | CLKREQ# pull-up |
| R505 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| SW3 | `Switch:SW_Push` | lid microswitch | `Button_Switch_THT:SW_PUSH_6mm` |  |
| U50 | `brain-drain:TPS22965` | TPS22965DSGR | `Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm` |  |
| U51 | `Regulator_Switching:AP63203WU` | AP63203WU-7 | `Package_TO_SOT_SMD:TSOT-23-6` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `GND` | **global** | U51.4 (GND), C5100.2, C5102.2, C5103.2, U50.5 (GND), U50.9 (EP), C500.2, C501.2, C502.2, R500.2, J50.3 (GND), J50.9 (GND), J50.15 (GND), J50.27 (GND), J50.33 (GND), J50.39 (GND), J50.45 (GND), J50.51 (GND), J50.57 (GND), J50.71 (GND), J50.73 (GND), SW3.2, J50.S1 (SHIELD1), J50.S2 (SHIELD2), J50.M3 (GND2260), J50.M4 (GND2280) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, bridge-1, bridge-2, bridge-3, bridge-4, cm5, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `M2_DAS` | local | D50.1 (K), J50.10 (DAS/DSS#) |  |
| `M2_DOOR` | **global** | SW3.1 | cm5 |
| `M2_LED_A` | local | R505.2, D50.2 (A) |  |
| `M2_PEDET` | **global** | J50.69 (CONFIG_1/PEDET), R501.2 | cm5 |
| `M2_PERn0` | local | J50.41 (PERn0), R503.1 |  |
| `M2_PERp0` | local | J50.43 (PERp0), R502.1 |  |
| `M2_PWR_EN` | **global** | U50.3 (ON), R500.1 | cm5 |
| `PCIE_CLKREQ` | local | M1.102 (PCIe_CLK_nREQ), J50.52 (CLKREQ#), R504.2 |  |
| `PCIE_CLK_N` | local | M1.112 (PCIe_CLK_N), J50.53 (REFCLKn) |  |
| `PCIE_CLK_P` | local | M1.110 (PCIe_CLK_P), J50.55 (REFCLKp) |  |
| `PCIE_RX_N` | local | R503.2, M1.118 (PCIe_RX_N) |  |
| `PCIE_RX_P` | local | R502.2, M1.116 (PCIe_RX_P) |  |
| `PCIE_TX_N` | local | M1.124 (PCIe_TX_N), J50.47 (PETn0) |  |
| `PCIE_TX_P` | local | M1.122 (PCIe_TX_P), J50.49 (PETp0) |  |
| `PCIE_nRST` | local | M1.109 (PCIe_nRST), J50.50 (PERST#) |  |
| `PCIE_nWAKE` | local | M1.104 (PCIE_nWAKE), J50.54 (PEWAKE#) |  |
| `U50_CT` | local | U50.6 (CT), C502.1 |  |
| `U51_BST` | local | U51.6 (BST), C5101.1 |  |
| `U51_SW` | local | U51.5 (SW), L51.1, C5101.2 |  |
| `USB2_DM` | **global** | M1.103 (USB_N) | cm5 |
| `USB2_DP` | **global** | M1.105 (USB_P) | cm5 |
| `USB3_0_DM` | **global** | M1.136 (USB3-0-DM) | usb3-hub-A |
| `USB3_0_DP` | **global** | M1.134 (USB3-0-DP) | usb3-hub-A |
| `USB3_0_RX_N` | **global** | M1.128 (USB3-0-RX_N) | usb3-hub-A |
| `USB3_0_RX_P` | **global** | M1.130 (USB3-0-RX_P) | usb3-hub-A |
| `USB3_0_TX_N` | **global** | M1.140 (USB3-0-TX_N) | usb3-hub-A |
| `USB3_0_TX_P` | **global** | M1.142 (USB3-0-TX_P) | usb3-hub-A |
| `USB3_1_DM` | **global** | M1.165 (USB3-1-DM) | usb3-hub-B |
| `USB3_1_DP` | **global** | M1.163 (USB3-1-DP) | usb3-hub-B |
| `USB3_1_RX_N` | **global** | M1.157 (USB3-1-RX_N) | usb3-hub-B |
| `USB3_1_RX_P` | **global** | M1.159 (USB3-1-RX_P) | usb3-hub-B |
| `USB3_1_TX_N` | **global** | M1.169 (USB3-1-TX_N) | usb3-hub-B |
| `USB3_1_TX_P` | **global** | M1.171 (USB3-1-TX_P) | usb3-hub-B |
| `+12V` | **global** | U51.3 (IN), C5100.1, U51.2 (EN) | bay-switch-1, bay-switch-2, bay-switch-3, bay-switch-4, power-bucks, power-input |
| `3V3_M2` | **global** | L51.2, C5102.1, C5103.1, U51.1 (FB), U50.1 (VIN), U50.2 (VIN), U50.4 (VBIAS), C500.1 |  |
| `3V3_M2_SW` | **global** | U50.8 (VOUT), U50.7 (VOUT), C501.1, J50.2 (3V3), J50.4 (3V3), J50.12 (3V3), J50.14 (3V3), J50.16 (3V3), J50.18 (3V3), J50.70 (3V3), J50.72 (3V3), J50.74 (3V3), R501.1, R504.1, R505.1 |  |

### No connect

* J50: 1 (CONFIG_3), 11 (PETn3), 13 (PETp3), 17 (PERn2), 19 (PERp2), 20 (NC), 21 (CONFIG_0), 22 (NC), 23 (PETn2), 24 (NC), 25 (PETp2), 26 (NC), 28 (NC), 29 (PERn1), 30 (NC), 31 (PERp1), 32 (NC), 34 (NC), 35 (PETn1), 36 (NC), 37 (PETp1), 38 (DEVSLP), 40 (NC), 42 (NC), 44 (NC), 46 (NC), 48 (NC), 5 (PERn3), 50 (PERST#), 56 (MFG1), 58 (MFG2), 6 (NC), 67 (NC), 68 (SUSCLK), 7 (PERp3), 75 (CONFIG_2), 8 (NC)
* M1: 101 (USB_OTG_ID), 106 (PCIE_PWR_EN), 111 (VBUS_EN)

### Notes

* Polarity: CM5 TX_P -> PETp0 (49), TX_N -> PETn0 (47), PERp0 (43) -> RX_P, PERn0 (41) -> RX_N. The CM5IO reference wires both pairs inverted (TX_P to 47, RX_P to 41), which PCIe link training tolerates; either works.
* Only PCIe lane 0 is wired (x1). PET = host transmit (CM5 TX, AC caps on the module). PER = host receive: per the M.2 spec the SSD carries its own TX caps, so R502/R503 are 0R; the same 0402 pads take 100n if a module without caps turns up.
* PEDET (pin 69) is pulled up and read by GPIO19: an M.2 SATA module grounds it, and the software refuses the bay instead of trying PCIe.
* Door switch SW3 to GPIO4 (software pull-up): closed = low = door shut. Software powers the slot (M2_PWR_EN, GPIO27 -> U50) and rescans PCIe.

## Power flags

Add a PWR_FLAG to each of these nets (they are driven by connectors or passive parts): `+12V`, `+1V2`, `+3V3`, `12V_BAY1`, `12V_BAY2`, `12V_BAY3`, `12V_BAY4`, `3V3_M2`, `3V3_M2_SW`, `5V_BAY1`, `5V_BAY2`, `5V_BAY3`, `5V_BAY4`, `5V_HDD`, `5V_SYS`, `GND`, `SD_VDD`, `U10_VDD_CORE`, `U11_VDD_CORE`, `U12_VDD_CORE`, `U13_VDD_CORE`, `VIN_12V_RAW`

