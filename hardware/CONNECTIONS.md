# brain-drain brain: CM5, two USB 3 hubs, eight bay slots, M.2 bay, power, UI — connection list

Generated from `hardware/tools/design.py`; do not edit by hand. One table per sheet: every
component with its symbol, value and footprint, then every net on that sheet with the pins
it joins. Nets marked **global** continue on other sheets. Pins listed under *No connect*
get an explicit no-connect flag.

Totals: 163 components, 192 nets.


## Sheet `power-input` — 12 V DIN input, fuse, TVS, reverse-polarity FET, bulk capacitance (sized for 8 bays)

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
| Q20 | `brain-drain:PMOS_SSSGDDDD` | AO4407A | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | reverse-polarity protection, body diode toward load; SO-8 power pin-out S 1-3, G 4, D 5-8 |
| R20 | `Device:R` | 100k | `Resistor_SMD:R_0603_1608Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `GND` | **global** | J21.3, J21.4, J21.5 (SHIELD), D20.1 (A1), R20.2, C20.2, C21.2, C22.2 | bay-slots, cm5, m2-nvme, power-bucks, usb3-hub-A, usb3-hub-B |
| `Q20_GATE` | local | Q20.4 (G), R20.1, D21.2 (A) |  |
| `VIN_12V_FUSED` | local | F1.2, D20.2 (A2), Q20.5 (D), Q20.6 (D), Q20.7 (D), Q20.8 (D) |  |
| `VIN_12V_RAW` | **global** | J21.1, J21.2, F1.1 |  |
| `+12V` | **global** | Q20.1 (S), Q20.2 (S), Q20.3 (S), C20.1, C21.1, C22.1, D21.1 (K) | bay-slots, m2-nvme, power-bucks |

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
| `GND` | **global** | C2000.2, C2001.2, U20.3 (AGND), U20.9 (PGND), R2001.2, C2003.2, C2004.2, C2005.2, C2100.2, C2101.2, U21.3 (AGND), U21.9 (PGND), R2101.2, C2103.2, C2104.2, C2105.2, U22.4 (GND), C2200.2, C2202.2, C2203.2, U3.2 (GND), C30.2, C31.2 | bay-slots, cm5, m2-nvme, power-input, usb3-hub-A, usb3-hub-B |
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
| `+12V` | **global** | U20.8 (VIN), C2000.1, C2001.1, R2002.1, U21.8 (VIN), C2100.1, C2101.1, R2102.1, U22.3 (IN), C2200.1, U22.2 (EN) | bay-slots, m2-nvme, power-input |
| `+1V2` | **global** | U3.5 (VOUT), C31.1 | usb3-hub-A, usb3-hub-B |
| `+3V3` | **global** | L22.2, C2202.1, C2203.1, U22.1 (FB), U3.1 (VIN), U3.3 (EN), C30.1 | bay-slots, cm5, usb3-hub-A, usb3-hub-B |
| `5V_HDD` | **global** | L21.2, C2103.1, C2104.1, C2105.1, R2100.1, R2103.1 | bay-slots |
| `5V_SYS` | **global** | L20.2, C2003.1, C2004.1, C2005.1, R2000.1, R2003.1 | cm5 |

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
| `BAY_EN1` | **global** | M1.34 (GPIO5) | bay-slots |
| `BAY_EN2` | **global** | M1.30 (GPIO6) | bay-slots |
| `BAY_EN3` | **global** | M1.31 (GPIO12) | bay-slots |
| `BAY_EN4` | **global** | M1.28 (GPIO13) | bay-slots |
| `BAY_EN5` | **global** | M1.37 (GPIO7) | bay-slots |
| `BAY_EN6` | **global** | M1.39 (GPIO8) | bay-slots |
| `BAY_EN7` | **global** | M1.40 (GPIO9) | bay-slots |
| `BAY_EN8` | **global** | M1.44 (GPIO10) | bay-slots |
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
| `GND` | **global** | M1.1 (GND), M1.2 (GND), M1.7 (GND), M1.8 (GND), M1.13 (GND), M1.14 (GND), M1.22 (GND), M1.23 (GND), M1.32 (GND), M1.33 (GND), M1.42 (GND), M1.43 (GND), M1.52 (GND), M1.53 (GND), M1.59 (GND), M1.60 (GND), M1.65 (GND), M1.66 (GND), M1.71 (GND), M1.74 (GND), M1.98 (GND), M1.107 (GND), M1.108 (GND), M1.113 (GND), M1.114 (GND), M1.119 (GND), M1.120 (GND), M1.125 (GND), M1.126 (GND), M1.131 (GND), M1.132 (GND), M1.137 (GND), M1.138 (GND), M1.144 (GND), M1.150 (GND), M1.155 (GND), M1.156 (GND), M1.161 (GND), M1.162 (GND), M1.167 (GND), M1.168 (GND), M1.173 (GND), M1.174 (GND), M1.179 (GND), M1.180 (GND), M1.185 (GND), M1.186 (GND), M1.191 (GND), M1.192 (GND), M1.197 (GND), M1.198 (GND), C1.2, C2.2, BT1.2 (-), J6.2 (Pin_2), J7.1 (Pin_1), J40.1 (Pin_1), D1.1 (K), SW1.16, SW1.15, SW1.14, SW1.13, SW1.12, SW1.11, SW1.10, SW1.9, J41.1 (Pin_1), J3.6 (VSS), J3.9 (SHIELD), U52.5 (GND), U52.9 (EP), C3.2, C4.2, J5.A1 (GND), J5.A12 (GND), J5.B1 (GND), J5.B12 (GND), J5.S1 (SHIELD) | bay-slots, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
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
| `+3V3` | **global** | R10.1, R1.1, R2.1, R3.1, J41.2 (Pin_2), U52.1 (VIN), U52.2 (VIN), U52.4 (VBIAS), C4.1, R11.1 | bay-slots, power-bucks, usb3-hub-A, usb3-hub-B |
| `5V_SYS` | **global** | M1.77 (5V), M1.79 (5V), M1.81 (5V), M1.83 (5V), M1.85 (5V), M1.87 (5V), C1.1, C2.1, J40.2 (Pin_2) | power-bucks |
| `nRPIBOOT` | local | M1.93 (nRPIBOOT), J6.1 (Pin_1) |  |

### No connect

* J5: A4 (VBUS), A8 (SBU1), A9 (VBUS), B4 (VBUS), B8 (SBU2), B9 (VBUS)
* M1: 10 (Ethernet_Pair0_N), 100 (CAM_GPIO1), 11 (Ethernet_Pair2_P), 115 (MIPI0_D0_N), 117 (MIPI0_D0_P), 12 (Ethernet_Pair0_P), 121 (MIPI0_D1_N), 123 (MIPI0_D1_P), 127 (MIPI0_C_N), 129 (MIPI0_C_P), 133 (MIPI0_D2_N), 135 (MIPI0_D2_P), 139 (MIPI0_D3_N), 141 (MIPI0_D3_P), 143 (HDMI1_HOTPLUG), 145 (HDMI1_SDA), 146 (HDMI1_TX2_P), 147 (HDMI1_SCL), 148 (HDMI1_TX2_N), 149 (HDMI1_CEC), 15 (Ethernet_nLED3), 151 (HDMI0_CEC), 152 (HDMI1_TX1_P), 153 (HDMI0_HOTPLUG), 154 (HDMI1_TX1_N), 158 (HDMI1_TX0_P), 160 (HDMI1_TX0_N), 164 (HDMI1_CLK_P), 166 (HDMI1_CLK_N), 17 (Ethernet_nLED2), 170 (HDMI0_TX2_P), 172 (HDMI0_TX2_N), 175 (MIPI1_D0_N), 176 (HDMI0_TX1_P), 177 (MIPI1_D0_P), 178 (HDMI0_TX1_N), 18 (Ethernet_SYNC_OUT), 181 (MIPI1_D1_N), 182 (HDMI0_TX0_P), 183 (MIPI1_D1_P), 184 (HDMI0_TX0_N), 187 (MIPI1_C_N), 188 (HDMI0_CLK_P), 189 (MIPI1_C_P), 190 (HDMI0_CLK_N), 193 (MIPI1_D2_N), 194 (MIPI1_D3_N), 195 (MIPI1_D2_P), 196 (MIPI1_D3_P), 199 (HDMI0_SDA), 20 (EEPROM_nWP), 200 (HDMI0_SCL), 3 (Ethernet_Pair3_P), 35 (ID_SC), 36 (ID_SD), 38 (GPIO11), 4 (Ethernet_Pair1_P), 49 (GPIO18), 5 (Ethernet_Pair3_N), 6 (Ethernet_Pair1_N), 64 (SD_DAT5), 68 (SD_DAT4), 70 (SD_DAT7), 72 (SD_DAT6), 73 (SD_VDD_OVERRIDE), 80 (SCL0), 82 (SDA0), 88 (CM5_1.8V), 89 (WL_nDisable), 9 (Ethernet_Pair2_N), 90 (CM5_1.8V), 91 (BT_nDisable), 92 (PWR_Button), 95 (LED_nPWR), 97 (CAM_GPIO0), 99 (PMIC_Enable)
* U52: 6 (CT)

### Notes

* GPIO_VREF is tied to the CM5's own 3.3 V output (pins 84/86) for 3.3 V GPIO signalling, per datasheet §4.2.
* PMIC_Enable and PWR_Button are left floating (internal pull-ups). nRPIBOOT goes to jumper J6.
* LED_nACT is an open-drain 20 mA output on the CM5: it sinks D2 directly. GPIO26 sinks D3 (software drives it low to light).
* microSD power goes through U52 so the CM5 can power-cycle the card on reboot via SD_PWR_ON, matching the CM5IO reference (which uses an RT9742).
* Ethernet dropped (C22). The CM5 wireless variant's PCB antenna is on the short module edge that carries MH1; that edge sits on the board's left edge with an 8 mm copper-free strip under it and no metal within 10 mm (CM5 datasheet 4.1.2).
* USB-C is a device port (rpiboot / gadget). As on the CM5IO, CC1/CC2 go straight to the CM5, which presents the sink pull-downs itself; VBUS is not connected (the board is powered from 12 V). USB_OTG_ID floats = device.

## Sheet `usb3-hub-A` — USB5744 hub A on CM5 USB3-0, bay slots 1-4

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
| C153 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN3 TX AC coupling |
| C154 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN4 TX AC coupling |
| C161 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN1 TX AC coupling |
| C162 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN2 TX AC coupling |
| C163 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN3 TX AC coupling |
| C164 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN4 TX AC coupling |
| R100 | `Device:R` | 12.0k 1% | `Resistor_SMD:R_0402_1005Metric` | RBIAS |
| R101 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | VBUS_DET to 3.3 V |
| R102 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RESET_N pull-up |
| R103 | `Device:R` | 200k | `Resistor_SMD:R_0402_1005Metric` | CFG_NON_REM: all ports removable |
| U1 | `brain-drain:USB5744` | USB5744/2G | `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` |  |
| Y1 | `Device:Crystal_GND24` | 25MHz CL=20pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY1_USB2_DM` | **global** | U1.2 (USB2DN_DM1/PRT_DIS_M1) | bay-slots |
| `BAY1_USB2_DP` | **global** | U1.1 (USB2DN_DP1/PRT_DIS_P1) | bay-slots |
| `BAY1_USB3_RX_N` | **global** | C161.2 | bay-slots |
| `BAY1_USB3_RX_P` | **global** | C151.2 | bay-slots |
| `BAY1_USB3_TX_N` | **global** | U1.7 (USB3DN_RXDM1) | bay-slots |
| `BAY1_USB3_TX_P` | **global** | U1.6 (USB3DN_RXDP1) | bay-slots |
| `BAY2_USB2_DM` | **global** | U1.9 (USB2DN_DM2/PRT_DIS_M2) | bay-slots |
| `BAY2_USB2_DP` | **global** | U1.8 (USB2DN_DP2/PRT_DIS_P2) | bay-slots |
| `BAY2_USB3_RX_N` | **global** | C162.2 | bay-slots |
| `BAY2_USB3_RX_P` | **global** | C152.2 | bay-slots |
| `BAY2_USB3_TX_N` | **global** | U1.14 (USB3DN_RXDM2) | bay-slots |
| `BAY2_USB3_TX_P` | **global** | U1.13 (USB3DN_RXDP2) | bay-slots |
| `BAY3_USB2_DM` | **global** | U1.18 (USB2DN_DM3/PRT_DIS_M3) | bay-slots |
| `BAY3_USB2_DP` | **global** | U1.17 (USB2DN_DP3/PRT_DIS_P3) | bay-slots |
| `BAY3_USB3_RX_N` | **global** | C163.2 | bay-slots |
| `BAY3_USB3_RX_P` | **global** | C153.2 | bay-slots |
| `BAY3_USB3_TX_N` | **global** | U1.23 (USB3DN_RXDM3) | bay-slots |
| `BAY3_USB3_TX_P` | **global** | U1.22 (USB3DN_RXDP3) | bay-slots |
| `BAY4_USB2_DM` | **global** | U1.25 (USB2DN_DM4/PRT_DIS_M4) | bay-slots |
| `BAY4_USB2_DP` | **global** | U1.24 (USB2DN_DP4/PRT_DIS_P4) | bay-slots |
| `BAY4_USB3_RX_N` | **global** | C164.2 | bay-slots |
| `BAY4_USB3_RX_P` | **global** | C154.2 | bay-slots |
| `BAY4_USB3_TX_N` | **global** | U1.30 (USB3DN_RXDM4) | bay-slots |
| `BAY4_USB3_TX_P` | **global** | U1.29 (USB3DN_RXDP4) | bay-slots |
| `GND` | **global** | U1.EP (VSS), U1.52 (ATEST), R100.2, R103.2, Y1.2 (G), Y1.4 (G), C110.2, C111.2, C112.2, C113.2, C120.2, C121.2, C122.2, C123.2, C130.2, C131.2, C100.2, C101.2 | bay-slots, cm5, m2-nvme, power-bucks, power-input, usb3-hub-B |
| `U1_CFG_NON_REM` | local | U1.41 (SPI_CE_N/CFG_NON_REM), R103.1 |  |
| `U1_DN1_TXDM` | local | U1.4 (USB3DN_TXDM1), C161.1 |  |
| `U1_DN1_TXDP` | local | U1.3 (USB3DN_TXDP1), C151.1 |  |
| `U1_DN2_TXDM` | local | U1.11 (USB3DN_TXDM2), C162.1 |  |
| `U1_DN2_TXDP` | local | U1.10 (USB3DN_TXDP2), C152.1 |  |
| `U1_DN3_TXDM` | local | U1.20 (USB3DN_TXDM3), C163.1 |  |
| `U1_DN3_TXDP` | local | U1.19 (USB3DN_TXDP3), C153.1 |  |
| `U1_DN4_TXDM` | local | U1.27 (USB3DN_TXDM4), C164.1 |  |
| `U1_DN4_TXDP` | local | U1.26 (USB3DN_TXDP4), C154.1 |  |
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
| `+3V3` | **global** | U1.16 (VDD33), U1.31 (VDD33), U1.44 (VDD33), U1.55 (VDD33), C110.1, C111.1, C112.1, C113.1, C130.1, R101.1, R102.1 | bay-slots, cm5, power-bucks, usb3-hub-B |

### No connect

* U1: 32 (PRT_CTL4/GANG_PWR), 34 (PRT_CTL3), 35 (PRT_CTL2), 36 (PRT_CTL1), 38 (SPI_CLK/SMCLK), 39 (SPI_DO/SMDAT), 40 (SPI_DI/CFG_BC_EN)

### Notes

* Hub A: upstream on CM5 USB3-0. Downstream ports 1-4 -> bay slots 1-4 (C24: eight slots, four cards populated in v1).
* No SPI ROM and no SMBus pull-ups: the hub runs its internal ROM defaults. RESET_N has a pull-up only; add an RC if strap timing (1 ms hold) is a concern.
* Crystal: 25 MHz, CL 20 pF per datasheet table 10-10; 33 pF load caps assume ~3 pF stray, adjust to the chosen crystal.

## Sheet `usb3-hub-B` — USB5744 hub B on CM5 USB3-1, bay slots 5-8

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
| C253 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN3 TX AC coupling |
| C254 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN4 TX AC coupling |
| C261 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN1 TX AC coupling |
| C262 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN2 TX AC coupling |
| C263 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN3 TX AC coupling |
| C264 | `Device:C` | 100n | `Capacitor_SMD:C_0402_1005Metric` | USB3 DN4 TX AC coupling |
| R200 | `Device:R` | 12.0k 1% | `Resistor_SMD:R_0402_1005Metric` | RBIAS |
| R201 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | VBUS_DET to 3.3 V |
| R202 | `Device:R` | 10k | `Resistor_SMD:R_0402_1005Metric` | RESET_N pull-up |
| R203 | `Device:R` | 200k | `Resistor_SMD:R_0402_1005Metric` | CFG_NON_REM: all ports removable |
| U2 | `brain-drain:USB5744` | USB5744/2G | `Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` |  |
| Y2 | `Device:Crystal_GND24` | 25MHz CL=20pF | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY5_USB2_DM` | **global** | U2.2 (USB2DN_DM1/PRT_DIS_M1) | bay-slots |
| `BAY5_USB2_DP` | **global** | U2.1 (USB2DN_DP1/PRT_DIS_P1) | bay-slots |
| `BAY5_USB3_RX_N` | **global** | C261.2 | bay-slots |
| `BAY5_USB3_RX_P` | **global** | C251.2 | bay-slots |
| `BAY5_USB3_TX_N` | **global** | U2.7 (USB3DN_RXDM1) | bay-slots |
| `BAY5_USB3_TX_P` | **global** | U2.6 (USB3DN_RXDP1) | bay-slots |
| `BAY6_USB2_DM` | **global** | U2.9 (USB2DN_DM2/PRT_DIS_M2) | bay-slots |
| `BAY6_USB2_DP` | **global** | U2.8 (USB2DN_DP2/PRT_DIS_P2) | bay-slots |
| `BAY6_USB3_RX_N` | **global** | C262.2 | bay-slots |
| `BAY6_USB3_RX_P` | **global** | C252.2 | bay-slots |
| `BAY6_USB3_TX_N` | **global** | U2.14 (USB3DN_RXDM2) | bay-slots |
| `BAY6_USB3_TX_P` | **global** | U2.13 (USB3DN_RXDP2) | bay-slots |
| `BAY7_USB2_DM` | **global** | U2.18 (USB2DN_DM3/PRT_DIS_M3) | bay-slots |
| `BAY7_USB2_DP` | **global** | U2.17 (USB2DN_DP3/PRT_DIS_P3) | bay-slots |
| `BAY7_USB3_RX_N` | **global** | C263.2 | bay-slots |
| `BAY7_USB3_RX_P` | **global** | C253.2 | bay-slots |
| `BAY7_USB3_TX_N` | **global** | U2.23 (USB3DN_RXDM3) | bay-slots |
| `BAY7_USB3_TX_P` | **global** | U2.22 (USB3DN_RXDP3) | bay-slots |
| `BAY8_USB2_DM` | **global** | U2.25 (USB2DN_DM4/PRT_DIS_M4) | bay-slots |
| `BAY8_USB2_DP` | **global** | U2.24 (USB2DN_DP4/PRT_DIS_P4) | bay-slots |
| `BAY8_USB3_RX_N` | **global** | C264.2 | bay-slots |
| `BAY8_USB3_RX_P` | **global** | C254.2 | bay-slots |
| `BAY8_USB3_TX_N` | **global** | U2.30 (USB3DN_RXDM4) | bay-slots |
| `BAY8_USB3_TX_P` | **global** | U2.29 (USB3DN_RXDP4) | bay-slots |
| `GND` | **global** | U2.EP (VSS), U2.52 (ATEST), R200.2, R203.2, Y2.2 (G), Y2.4 (G), C210.2, C211.2, C212.2, C213.2, C220.2, C221.2, C222.2, C223.2, C230.2, C231.2, C200.2, C201.2 | bay-slots, cm5, m2-nvme, power-bucks, power-input, usb3-hub-A |
| `U2_CFG_NON_REM` | local | U2.41 (SPI_CE_N/CFG_NON_REM), R203.1 |  |
| `U2_DN1_TXDM` | local | U2.4 (USB3DN_TXDM1), C261.1 |  |
| `U2_DN1_TXDP` | local | U2.3 (USB3DN_TXDP1), C251.1 |  |
| `U2_DN2_TXDM` | local | U2.11 (USB3DN_TXDM2), C262.1 |  |
| `U2_DN2_TXDP` | local | U2.10 (USB3DN_TXDP2), C252.1 |  |
| `U2_DN3_TXDM` | local | U2.20 (USB3DN_TXDM3), C263.1 |  |
| `U2_DN3_TXDP` | local | U2.19 (USB3DN_TXDP3), C253.1 |  |
| `U2_DN4_TXDM` | local | U2.27 (USB3DN_TXDM4), C264.1 |  |
| `U2_DN4_TXDP` | local | U2.26 (USB3DN_TXDP4), C254.1 |  |
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
| `+3V3` | **global** | U2.16 (VDD33), U2.31 (VDD33), U2.44 (VDD33), U2.55 (VDD33), C210.1, C211.1, C212.1, C213.1, C230.1, R201.1, R202.1 | bay-slots, cm5, power-bucks, usb3-hub-A |

### No connect

* U2: 32 (PRT_CTL4/GANG_PWR), 34 (PRT_CTL3), 35 (PRT_CTL2), 36 (PRT_CTL1), 38 (SPI_CLK/SMCLK), 39 (SPI_DO/SMDAT), 40 (SPI_DI/CFG_BC_EN)

### Notes

* Hub B: upstream on CM5 USB3-1. Downstream ports 1-4 -> bay slots 5-8 (C24: eight slots, four cards populated in v1).
* No SPI ROM and no SMBus pull-ups: the hub runs its internal ROM defaults. RESET_N has a pull-up only; add an RC if strap timing (1 ms hold) is a concern.
* Crystal: 25 MHz, CL 20 pF per datasheet table 10-10; 33 pF load caps assume ~3 pF stray, adjust to the chosen crystal.

## Sheet `bay-slots` — Eight bay slots (PCIe x1 sockets, bay-card pinout): USB 3, USB 2, 12 V, 5 V, BAY_EN, bay LEDs

### Components

| Ref | Symbol | Value | Footprint | Note |
|---|---|---|---|---|
| D10 | `Device:LED` | blue bay 1 activity | `LED_THT:LED_D3.0mm` |  |
| D11 | `Device:LED` | blue bay 2 activity | `LED_THT:LED_D3.0mm` |  |
| D12 | `Device:LED` | blue bay 3 activity | `LED_THT:LED_D3.0mm` |  |
| D13 | `Device:LED` | blue bay 4 activity | `LED_THT:LED_D3.0mm` |  |
| D14 | `Device:LED` | blue bay 5 activity | `LED_THT:LED_D3.0mm` |  |
| D15 | `Device:LED` | blue bay 6 activity | `LED_THT:LED_D3.0mm` |  |
| D16 | `Device:LED` | blue bay 7 activity | `LED_THT:LED_D3.0mm` |  |
| D17 | `Device:LED` | blue bay 8 activity | `LED_THT:LED_D3.0mm` |  |
| J10 | `brain-drain:BAY_SLOT` | bay slot 1 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J11 | `brain-drain:BAY_SLOT` | bay slot 2 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J12 | `brain-drain:BAY_SLOT` | bay slot 3 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J13 | `brain-drain:BAY_SLOT` | bay slot 4 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J14 | `brain-drain:BAY_SLOT` | bay slot 5 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J15 | `brain-drain:BAY_SLOT` | bay slot 6 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J16 | `brain-drain:BAY_SLOT` | bay slot 7 | `brain-drain:PCIe_x1_Socket_THT` |  |
| J17 | `brain-drain:BAY_SLOT` | bay slot 8 | `brain-drain:PCIe_x1_Socket_THT` |  |
| R60 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R61 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R62 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R63 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R64 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R65 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R66 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |
| R67 | `Device:R` | 470 | `Resistor_SMD:R_0402_1005Metric` |  |

### Nets

| Net | Scope | Pins on this sheet | Also on |
|---|---|---|---|
| `BAY1_LED_A` | local | R60.2, D10.2 (A) |  |
| `BAY1_LED_K` | local | J10.B6 (LED_K), D10.1 (K) |  |
| `BAY1_USB2_DM` | **global** | J10.B12 (USB2_DM) | usb3-hub-A |
| `BAY1_USB2_DP` | **global** | J10.B13 (USB2_DP) | usb3-hub-A |
| `BAY1_USB3_RX_N` | **global** | J10.B15 (USB3_RX_N) | usb3-hub-A |
| `BAY1_USB3_RX_P` | **global** | J10.B16 (USB3_RX_P) | usb3-hub-A |
| `BAY1_USB3_TX_N` | **global** | J10.A14 (USB3_TX_N) | usb3-hub-A |
| `BAY1_USB3_TX_P` | **global** | J10.A15 (USB3_TX_P) | usb3-hub-A |
| `BAY2_LED_A` | local | R61.2, D11.2 (A) |  |
| `BAY2_LED_K` | local | J11.B6 (LED_K), D11.1 (K) |  |
| `BAY2_USB2_DM` | **global** | J11.B12 (USB2_DM) | usb3-hub-A |
| `BAY2_USB2_DP` | **global** | J11.B13 (USB2_DP) | usb3-hub-A |
| `BAY2_USB3_RX_N` | **global** | J11.B15 (USB3_RX_N) | usb3-hub-A |
| `BAY2_USB3_RX_P` | **global** | J11.B16 (USB3_RX_P) | usb3-hub-A |
| `BAY2_USB3_TX_N` | **global** | J11.A14 (USB3_TX_N) | usb3-hub-A |
| `BAY2_USB3_TX_P` | **global** | J11.A15 (USB3_TX_P) | usb3-hub-A |
| `BAY3_LED_A` | local | R62.2, D12.2 (A) |  |
| `BAY3_LED_K` | local | J12.B6 (LED_K), D12.1 (K) |  |
| `BAY3_USB2_DM` | **global** | J12.B12 (USB2_DM) | usb3-hub-A |
| `BAY3_USB2_DP` | **global** | J12.B13 (USB2_DP) | usb3-hub-A |
| `BAY3_USB3_RX_N` | **global** | J12.B15 (USB3_RX_N) | usb3-hub-A |
| `BAY3_USB3_RX_P` | **global** | J12.B16 (USB3_RX_P) | usb3-hub-A |
| `BAY3_USB3_TX_N` | **global** | J12.A14 (USB3_TX_N) | usb3-hub-A |
| `BAY3_USB3_TX_P` | **global** | J12.A15 (USB3_TX_P) | usb3-hub-A |
| `BAY4_LED_A` | local | R63.2, D13.2 (A) |  |
| `BAY4_LED_K` | local | J13.B6 (LED_K), D13.1 (K) |  |
| `BAY4_USB2_DM` | **global** | J13.B12 (USB2_DM) | usb3-hub-A |
| `BAY4_USB2_DP` | **global** | J13.B13 (USB2_DP) | usb3-hub-A |
| `BAY4_USB3_RX_N` | **global** | J13.B15 (USB3_RX_N) | usb3-hub-A |
| `BAY4_USB3_RX_P` | **global** | J13.B16 (USB3_RX_P) | usb3-hub-A |
| `BAY4_USB3_TX_N` | **global** | J13.A14 (USB3_TX_N) | usb3-hub-A |
| `BAY4_USB3_TX_P` | **global** | J13.A15 (USB3_TX_P) | usb3-hub-A |
| `BAY5_LED_A` | local | R64.2, D14.2 (A) |  |
| `BAY5_LED_K` | local | J14.B6 (LED_K), D14.1 (K) |  |
| `BAY5_USB2_DM` | **global** | J14.B12 (USB2_DM) | usb3-hub-B |
| `BAY5_USB2_DP` | **global** | J14.B13 (USB2_DP) | usb3-hub-B |
| `BAY5_USB3_RX_N` | **global** | J14.B15 (USB3_RX_N) | usb3-hub-B |
| `BAY5_USB3_RX_P` | **global** | J14.B16 (USB3_RX_P) | usb3-hub-B |
| `BAY5_USB3_TX_N` | **global** | J14.A14 (USB3_TX_N) | usb3-hub-B |
| `BAY5_USB3_TX_P` | **global** | J14.A15 (USB3_TX_P) | usb3-hub-B |
| `BAY6_LED_A` | local | R65.2, D15.2 (A) |  |
| `BAY6_LED_K` | local | J15.B6 (LED_K), D15.1 (K) |  |
| `BAY6_USB2_DM` | **global** | J15.B12 (USB2_DM) | usb3-hub-B |
| `BAY6_USB2_DP` | **global** | J15.B13 (USB2_DP) | usb3-hub-B |
| `BAY6_USB3_RX_N` | **global** | J15.B15 (USB3_RX_N) | usb3-hub-B |
| `BAY6_USB3_RX_P` | **global** | J15.B16 (USB3_RX_P) | usb3-hub-B |
| `BAY6_USB3_TX_N` | **global** | J15.A14 (USB3_TX_N) | usb3-hub-B |
| `BAY6_USB3_TX_P` | **global** | J15.A15 (USB3_TX_P) | usb3-hub-B |
| `BAY7_LED_A` | local | R66.2, D16.2 (A) |  |
| `BAY7_LED_K` | local | J16.B6 (LED_K), D16.1 (K) |  |
| `BAY7_USB2_DM` | **global** | J16.B12 (USB2_DM) | usb3-hub-B |
| `BAY7_USB2_DP` | **global** | J16.B13 (USB2_DP) | usb3-hub-B |
| `BAY7_USB3_RX_N` | **global** | J16.B15 (USB3_RX_N) | usb3-hub-B |
| `BAY7_USB3_RX_P` | **global** | J16.B16 (USB3_RX_P) | usb3-hub-B |
| `BAY7_USB3_TX_N` | **global** | J16.A14 (USB3_TX_N) | usb3-hub-B |
| `BAY7_USB3_TX_P` | **global** | J16.A15 (USB3_TX_P) | usb3-hub-B |
| `BAY8_LED_A` | local | R67.2, D17.2 (A) |  |
| `BAY8_LED_K` | local | J17.B6 (LED_K), D17.1 (K) |  |
| `BAY8_USB2_DM` | **global** | J17.B12 (USB2_DM) | usb3-hub-B |
| `BAY8_USB2_DP` | **global** | J17.B13 (USB2_DP) | usb3-hub-B |
| `BAY8_USB3_RX_N` | **global** | J17.B15 (USB3_RX_N) | usb3-hub-B |
| `BAY8_USB3_RX_P` | **global** | J17.B16 (USB3_RX_P) | usb3-hub-B |
| `BAY8_USB3_TX_N` | **global** | J17.A14 (USB3_TX_N) | usb3-hub-B |
| `BAY8_USB3_TX_P` | **global** | J17.A15 (USB3_TX_P) | usb3-hub-B |
| `BAY_EN1` | **global** | J10.B5 (BAY_EN) | cm5 |
| `BAY_EN2` | **global** | J11.B5 (BAY_EN) | cm5 |
| `BAY_EN3` | **global** | J12.B5 (BAY_EN) | cm5 |
| `BAY_EN4` | **global** | J13.B5 (BAY_EN) | cm5 |
| `BAY_EN5` | **global** | J14.B5 (BAY_EN) | cm5 |
| `BAY_EN6` | **global** | J15.B5 (BAY_EN) | cm5 |
| `BAY_EN7` | **global** | J16.B5 (BAY_EN) | cm5 |
| `BAY_EN8` | **global** | J17.B5 (BAY_EN) | cm5 |
| `GND` | **global** | J10.A3 (GND), J10.A4 (GND), J10.A7 (GND), J10.A10 (GND), J10.A11 (GND), J10.A12 (GND), J10.A13 (GND), J10.A16 (GND), J10.A17 (GND), J10.A18 (GND), J10.B4 (GND), J10.B7 (GND), J10.B11 (GND), J10.B14 (GND), J10.B17 (GND), J10.B18 (GND), J11.A3 (GND), J11.A4 (GND), J11.A7 (GND), J11.A10 (GND), J11.A11 (GND), J11.A12 (GND), J11.A13 (GND), J11.A16 (GND), J11.A17 (GND), J11.A18 (GND), J11.B4 (GND), J11.B7 (GND), J11.B11 (GND), J11.B14 (GND), J11.B17 (GND), J11.B18 (GND), J12.A3 (GND), J12.A4 (GND), J12.A7 (GND), J12.A10 (GND), J12.A11 (GND), J12.A12 (GND), J12.A13 (GND), J12.A16 (GND), J12.A17 (GND), J12.A18 (GND), J12.B4 (GND), J12.B7 (GND), J12.B11 (GND), J12.B14 (GND), J12.B17 (GND), J12.B18 (GND), J13.A3 (GND), J13.A4 (GND), J13.A7 (GND), J13.A10 (GND), J13.A11 (GND), J13.A12 (GND), J13.A13 (GND), J13.A16 (GND), J13.A17 (GND), J13.A18 (GND), J13.B4 (GND), J13.B7 (GND), J13.B11 (GND), J13.B14 (GND), J13.B17 (GND), J13.B18 (GND), J14.A3 (GND), J14.A4 (GND), J14.A7 (GND), J14.A10 (GND), J14.A11 (GND), J14.A12 (GND), J14.A13 (GND), J14.A16 (GND), J14.A17 (GND), J14.A18 (GND), J14.B4 (GND), J14.B7 (GND), J14.B11 (GND), J14.B14 (GND), J14.B17 (GND), J14.B18 (GND), J15.A3 (GND), J15.A4 (GND), J15.A7 (GND), J15.A10 (GND), J15.A11 (GND), J15.A12 (GND), J15.A13 (GND), J15.A16 (GND), J15.A17 (GND), J15.A18 (GND), J15.B4 (GND), J15.B7 (GND), J15.B11 (GND), J15.B14 (GND), J15.B17 (GND), J15.B18 (GND), J16.A3 (GND), J16.A4 (GND), J16.A7 (GND), J16.A10 (GND), J16.A11 (GND), J16.A12 (GND), J16.A13 (GND), J16.A16 (GND), J16.A17 (GND), J16.A18 (GND), J16.B4 (GND), J16.B7 (GND), J16.B11 (GND), J16.B14 (GND), J16.B17 (GND), J16.B18 (GND), J17.A3 (GND), J17.A4 (GND), J17.A7 (GND), J17.A10 (GND), J17.A11 (GND), J17.A12 (GND), J17.A13 (GND), J17.A16 (GND), J17.A17 (GND), J17.A18 (GND), J17.B4 (GND), J17.B7 (GND), J17.B11 (GND), J17.B14 (GND), J17.B17 (GND), J17.B18 (GND) | cm5, m2-nvme, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
| `+12V` | **global** | J10.A1 (12V), J10.A2 (12V), J10.B1 (12V), J10.B2 (12V), J10.B3 (12V), J11.A1 (12V), J11.A2 (12V), J11.B1 (12V), J11.B2 (12V), J11.B3 (12V), J12.A1 (12V), J12.A2 (12V), J12.B1 (12V), J12.B2 (12V), J12.B3 (12V), J13.A1 (12V), J13.A2 (12V), J13.B1 (12V), J13.B2 (12V), J13.B3 (12V), J14.A1 (12V), J14.A2 (12V), J14.B1 (12V), J14.B2 (12V), J14.B3 (12V), J15.A1 (12V), J15.A2 (12V), J15.B1 (12V), J15.B2 (12V), J15.B3 (12V), J16.A1 (12V), J16.A2 (12V), J16.B1 (12V), J16.B2 (12V), J16.B3 (12V), J17.A1 (12V), J17.A2 (12V), J17.B1 (12V), J17.B2 (12V), J17.B3 (12V) | m2-nvme, power-bucks, power-input |
| `+3V3` | **global** | R60.1, R61.1, R62.1, R63.1, R64.1, R65.1, R66.1, R67.1 | cm5, power-bucks, usb3-hub-A, usb3-hub-B |
| `5V_HDD` | **global** | J10.A8 (5V), J10.A9 (5V), J10.B8 (5V), J10.B9 (5V), J10.B10 (5V), J11.A8 (5V), J11.A9 (5V), J11.B8 (5V), J11.B9 (5V), J11.B10 (5V), J12.A8 (5V), J12.A9 (5V), J12.B8 (5V), J12.B9 (5V), J12.B10 (5V), J13.A8 (5V), J13.A9 (5V), J13.B8 (5V), J13.B9 (5V), J13.B10 (5V), J14.A8 (5V), J14.A9 (5V), J14.B8 (5V), J14.B9 (5V), J14.B10 (5V), J15.A8 (5V), J15.A9 (5V), J15.B8 (5V), J15.B9 (5V), J15.B10 (5V), J16.A8 (5V), J16.A9 (5V), J16.B8 (5V), J16.B9 (5V), J16.B10 (5V), J17.A8 (5V), J17.A9 (5V), J17.B8 (5V), J17.B9 (5V), J17.B10 (5V) | power-bucks |

### No connect

* J10: A5 (NC), A6 (NC)
* J11: A5 (NC), A6 (NC)
* J12: A5 (NC), A6 (NC)
* J13: A5 (NC), A6 (NC)
* J14: A5 (NC), A6 (NC)
* J15: A5 (NC), A6 (NC)
* J16: A5 (NC), A6 (NC)
* J17: A5 (NC), A6 (NC)

### Notes

* Bay slots are PCI Express x1 sockets used with the bay-card pinout (symgen SLOT_PINS), not PCIe signalling. Five contacts each for 12 V and 5 V (about 1 A per contact), grounds beside every pair. v1 populates cards in slots 1-4; slots 5-8 take cards later (bigger brick, D9).
* The bay LED sits on the brain (lid) and is sunk by the card's bridge LED pin through B6.

## Sheet `m2-nvme` — Bay 9: M.2 M-key on PCIe Gen3 x1, 3V3_M2 buck + load switch, lid switch

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
| `GND` | **global** | U51.4 (GND), C5100.2, C5102.2, C5103.2, U50.5 (GND), U50.9 (EP), C500.2, C501.2, C502.2, R500.2, J50.3 (GND), J50.9 (GND), J50.15 (GND), J50.27 (GND), J50.33 (GND), J50.39 (GND), J50.45 (GND), J50.51 (GND), J50.57 (GND), J50.71 (GND), J50.73 (GND), SW3.2, J50.S1 (SHIELD1), J50.S2 (SHIELD2), J50.M3 (GND2260), J50.M4 (GND2280) | bay-slots, cm5, power-bucks, power-input, usb3-hub-A, usb3-hub-B |
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
| `+12V` | **global** | U51.3 (IN), C5100.1, U51.2 (EN) | bay-slots, power-bucks, power-input |
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

Add a PWR_FLAG to each of these nets (they are driven by connectors or passive parts): `+12V`, `+1V2`, `+3V3`, `3V3_M2`, `3V3_M2_SW`, `5V_HDD`, `5V_SYS`, `GND`, `SD_VDD`, `VIN_12V_RAW`

