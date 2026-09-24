"""brain-drain carrier board: the netlist, in Python.

Single source of truth for both schematic deliverables:
  gen_sch.py         -> hardware/brain-drain.kicad_sch + sheets (label-based, ERC-checked)
  gen_connections.py -> hardware/CONNECTIONS.md (for drawing by hand)

Pin references: "REF.<pin number>" or "REF.<pin name>". A pin *name* shared by
several pins (VDD12, GND...) expands to all of them.

Decisions applied: C7 CM5, C8 two hubs, C10 no button, C11 USB5744, C12 ASM1153E,
C13 4-pin DIN input, C14 3 mm LEDs, C15 M.2 bay populated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import kilib


@dataclass
class Comp:
    ref: str
    lib_id: str
    value: str
    sheet: str
    footprint: str = ""
    dnp: bool = False
    unit_sheets: dict[int, str] = field(default_factory=dict)  # unit -> sheet (multi-unit symbols)
    rotation: int = 0
    note: str = ""

    def sym(self):
        return kilib.get(self.lib_id)


@dataclass
class Design:
    title: str
    comps: dict[str, Comp] = field(default_factory=dict)
    nets: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # net -> [(ref, pin number)]
    ncs: set[tuple[str, str]] = field(default_factory=set)
    sheets: list[tuple[str, str]] = field(default_factory=list)  # (name, description)
    notes: dict[str, list[str]] = field(default_factory=dict)
    pwr_flags: set[str] = field(default_factory=set)

    # ------------------------------------------------------------ building
    def sheet(self, name, description):
        self.sheets.append((name, description))
        self.notes.setdefault(name, [])

    def note(self, sheet, text):
        self.notes.setdefault(sheet, []).append(text)

    def part(self, ref, lib_id, value, sheet, footprint="", dnp=False, rotation=0, note="", unit_sheets=None):
        if ref in self.comps:
            raise ValueError(f"duplicate ref {ref}")
        c = Comp(ref, lib_id, value, sheet, footprint or kilib_default_fp(lib_id), dnp, unit_sheets or {}, rotation, note)
        self.comps[ref] = c
        return c

    def _resolve(self, token: str) -> list[tuple[str, str]]:
        ref, pin = token.split(".", 1)
        c = self.comps[ref]
        pins = c.sym().pins
        nums = [p.number for p in pins if p.number == pin]
        if nums:
            return [(ref, pin)]
        byname = [p.number for p in pins if p.name == pin]
        if not byname:
            raise KeyError(f"{token}: no pin numbered or named {pin!r} on {c.lib_id}")
        return [(ref, n) for n in byname]

    def net(self, name, *tokens):
        lst = self.nets.setdefault(name, [])
        for t in tokens:
            for rp in self._resolve(t):
                if rp in self.ncs:
                    raise ValueError(f"{rp} marked NC and connected to {name}")
                if rp not in lst:
                    lst.append(rp)
        return self

    def nc(self, *tokens):
        for t in tokens:
            for rp in self._resolve(t):
                self.ncs.add(rp)

    def pwr_flag(self, *nets):
        self.pwr_flags.update(nets)

    # ------------------------------------------------------------ queries
    def pin_net(self) -> dict[tuple[str, str], str]:
        return {rp: n for n, lst in self.nets.items() for rp in lst}

    def check(self):
        """Every pin is either on a net, NC, or reported."""
        pn = self.pin_net()
        missing = []
        for c in self.comps.values():
            for p in c.sym().pins:
                rp = (c.ref, p.number)
                if rp not in pn and rp not in self.ncs:
                    missing.append((c.ref, p.number, p.name))
        return missing

    def sheet_of_pin(self, ref, number) -> str:
        c = self.comps[ref]
        p = next(p for p in c.sym().pins if p.number == number)
        return c.unit_sheets.get(p.unit, c.sheet)

    def net_sheets(self, net) -> set[str]:
        return {self.sheet_of_pin(r, n) for r, n in self.nets[net]}


def kilib_default_fp(lib_id: str) -> str:
    try:
        sd = kilib.get(lib_id)
    except KeyError:
        return ""
    import sexp
    for p in sexp.find_all(sd.node, "property"):
        if str(p[1]) == "Footprint":
            return str(p[2])
    return ""


# ====================================================================== the board

FP = {
    "R0402": "Resistor_SMD:R_0402_1005Metric",
    "R0603": "Resistor_SMD:R_0603_1608Metric",
    "R0805": "Resistor_SMD:R_0805_2012Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C1210": "Capacitor_SMD:C_1210_3225Metric",
    "CP_10x10": "Capacitor_SMD:CP_Elec_10x10.5",
    "XTAL3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT25": "Package_TO_SOT_SMD:SOT-23-5",
    "TSOT26": "Package_TO_SOT_SMD:TSOT-23-6",
    "DFN8": "Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm",
    "SO8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "SMB": "Diode_SMD:D_SMB",
    "F1206": "Fuse:Fuse_1206_3216Metric",
    "PTC1812": "Fuse:Fuse_1812_4532Metric",
    "L_6x6": "Inductor_SMD:L_Taiyo-Yuden_NR-60xx",
    "L_4x4": "Inductor_SMD:L_Taiyo-Yuden_NR-40xx",
    "LED3": "LED_THT:LED_D3.0mm",
    "HDR1x2": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "HDR1x3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "HDR1x4": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "FAN4": "Connector:FanPinHeader_1x04_P2.54mm_Vertical",
    "DIP8": "Button_Switch_THT:SW_DIP_SPSTx08_Piano_10.8x21.88mm_W7.62mm_P2.54mm",
    "USBC16": "Connector_USB:USB_C_Receptacle_GCT_USB4085",
    "MICROSD": "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5",
    "RJ45": "Connector_RJ:RJ45_Wuerth_7499111446_Horizontal",
    "CR2032": "Battery:BatteryHolder_Keystone_1060_1x2032",
    "SW_DOOR": "Button_Switch_THT:SW_PUSH_6mm",
}


PROJECTS = ("brain", "card")   # C24: the brain board with eight bay slots, and the bay card built per bay


def build(project: str = "brain") -> Design:
    return build_card() if project == "card" else build_brain()


def build_brain() -> Design:
    d = Design("brain-drain brain: CM5, two USB 3 hubs, eight bay slots, M.2 bay, power, UI")

    d.sheet("power-input", "12 V DIN input, fuse, TVS, reverse-polarity FET, bulk capacitance (sized for 8 bays)")
    d.sheet("power-bucks", "5V_SYS and 5V_HDD (TPS56637), +3V3 and 3V3_M2 (AP63203), +1V2 LDO")
    d.sheet("cm5", "Compute Module 5 (wireless): power, control, GPIO, microSD, USB-C, UART, RTC cell, fan, DIP, LEDs, OLED")
    d.sheet("usb3-hub-A", "USB5744 hub A on CM5 USB3-0, bay slots 1-4")
    d.sheet("usb3-hub-B", "USB5744 hub B on CM5 USB3-1, bay slots 5-8")
    d.sheet("bay-slots", "Eight bay slots (PCIe x1 sockets, bay-card pinout): USB 3, USB 2, 12 V, 5 V, BAY_EN, bay LEDs")
    d.sheet("m2-nvme", "Bay 9: M.2 M-key on PCIe Gen3 x1, 3V3_M2 buck + load switch, lid switch")

    # ---------------------------------------------------------------- power input
    s = "power-input"
    d.part("J21", "brain-drain:DIN4_KPJX", "KPJX-4S-S", s)
    d.part("F1", "Device:Fuse", "10A slow 0453010.MR", s, "Fuse:Fuse_Littelfuse-NANO2-451_453")
    d.part("D20", "Device:D_TVS", "SMBJ15A", s, FP["SMB"])
    d.part("Q20", "brain-drain:PMOS_SSSGDDDD", "AO4407A", s, FP["SO8"], note="reverse-polarity protection, body diode toward load; SO-8 power pin-out S 1-3, G 4, D 5-8")
    d.part("R20", "Device:R", "100k", s, FP["R0603"])
    d.part("D21", "Device:D_Zener", "12V 0.5W", s, "Diode_SMD:D_SOD-123", note="clamps Vgs of Q20")
    d.part("C20", "Device:C_Polarized", "680u 25V low-ESR", s, FP["CP_10x10"])
    d.part("C21", "Device:C_Polarized", "680u 25V low-ESR", s, FP["CP_10x10"])
    d.part("C22", "Device:C", "10u 25V", s, FP["C1210"])
    d.net("VIN_12V_RAW", "J21.1", "J21.2", "F1.1")
    d.net("GND", "J21.3", "J21.4", "J21.SHIELD")
    d.net("VIN_12V_FUSED", "F1.2", "D20.2", "Q20.D")
    d.net("GND", "D20.1", "R20.2")
    d.net("+12V", "Q20.S", "C20.1", "C21.1", "C22.1", "D21.K")
    d.net("Q20_GATE", "Q20.G", "R20.1", "D21.A")
    d.net("GND", "C20.2", "C21.2", "C22.2")
    d.pwr_flag("VIN_12V_RAW", "+12V", "GND")
    d.note(s, "J21 pins 1/2 = +12 V and 3/4 = GND is a PLACEHOLDER: wire to match the chosen 12 V/10 A brick's DIN pinout (C13).")
    d.note(s, "Q20 is a P-MOSFET used as an ideal-diode-style reverse-polarity switch: drain to the fused input, source to +12V, gate pulled to GND through R20 and clamped by D21.")

    # ---------------------------------------------------------------- bucks
    s = "power-bucks"
    for ref, rail, rt, rb in (("U20", "5V_SYS", "73.2k", "10k"), ("U21", "5V_HDD", "73.2k", "10k")):
        n = ref[1:]
        d.part(ref, "brain-drain:TPS56637", "TPS56637RPAR", s)
        d.part(f"C{n}00", "Device:C", "10u 25V", s, FP["C1210"], note="VIN bypass")
        d.part(f"C{n}01", "Device:C", "10u 25V", s, FP["C1210"])
        d.part(f"C{n}02", "Device:C", "100n 25V", s, FP["C0402"], note="BOOT")
        d.part(f"L{n}", "Device:L", "2.2u 8A", s, FP["L_6x6"])
        d.part(f"C{n}03", "Device:C", "22u 10V", s, FP["C0805"])
        d.part(f"C{n}04", "Device:C", "22u 10V", s, FP["C0805"])
        d.part(f"C{n}05", "Device:C", "22u 10V", s, FP["C0805"])
        d.part(f"R{n}00", "Device:R", rt, s, FP["R0402"], note="FB top, 1%")
        d.part(f"R{n}01", "Device:R", rb, s, FP["R0402"], note="FB bottom, 1%")
        d.part(f"R{n}02", "Device:R", "100k", s, FP["R0402"], note="EN pull-up")
        d.part(f"R{n}03", "Device:R", "10k", s, FP["R0402"], note="PG pull-up")
        d.net("+12V", f"{ref}.VIN", f"C{n}00.1", f"C{n}01.1", f"R{n}02.1")
        d.net("GND", f"C{n}00.2", f"C{n}01.2", f"{ref}.AGND", f"{ref}.PGND", f"R{n}01.2", f"C{n}03.2", f"C{n}04.2", f"C{n}05.2")
        d.net(f"{ref}_EN", f"{ref}.EN", f"R{n}02.2")
        d.net(f"{ref}_SW", f"{ref}.SW", f"L{n}.1", f"C{n}02.2")
        d.net(f"{ref}_BOOT", f"{ref}.BOOT", f"C{n}02.1")
        d.net(rail, f"L{n}.2", f"C{n}03.1", f"C{n}04.1", f"C{n}05.1", f"R{n}00.1", f"R{n}03.1")
        d.net(f"{ref}_FB", f"{ref}.FB", f"R{n}00.2", f"R{n}01.1")
        d.net(f"PG_{rail}", f"{ref}.PG", f"R{n}03.2")
        d.nc(f"{ref}.MODE", f"{ref}.NC")
    d.pwr_flag("5V_SYS", "5V_HDD")
    d.note(s, "TPS56637 FB: Vref 0.6 V; 73.2k/10k gives 4.99 V. MODE floating = forced CCM (quietest for the CM5 rail).")
    # 3V3 and 3V3_M2 from AP63203 (fixed 3.3 V, 2 A)
    for ref, rail in (("U22", "+3V3"), ("U51", "3V3_M2")):
        n = ref[1:]
        d.part(ref, "Regulator_Switching:AP63203WU", "AP63203WU-7", s if ref == "U22" else "m2-nvme", FP["TSOT26"])
        sh = d.comps[ref].sheet
        d.part(f"C{n}00", "Device:C", "10u 25V", sh, FP["C1210"])
        d.part(f"C{n}01", "Device:C", "100n 10V", sh, FP["C0402"], note="BST")
        d.part(f"L{n}", "Device:L", "4.7u 3A", sh, FP["L_4x4"])
        d.part(f"C{n}02", "Device:C", "22u 10V", sh, FP["C0805"])
        d.part(f"C{n}03", "Device:C", "22u 10V", sh, FP["C0805"])
        d.net("+12V", f"{ref}.IN", f"C{n}00.1", f"{ref}.EN")
        d.net("GND", f"{ref}.GND", f"C{n}00.2", f"C{n}02.2", f"C{n}03.2")
        d.net(f"{ref}_SW", f"{ref}.SW", f"L{n}.1", f"C{n}01.2")
        d.net(f"{ref}_BST", f"{ref}.BST", f"C{n}01.1")
        d.net(rail, f"L{n}.2", f"C{n}02.1", f"C{n}03.1", f"{ref}.FB")
    d.pwr_flag("+3V3", "3V3_M2")
    d.note(s, "AP63203WU is the fixed 3.3 V variant: FB ties straight to the output. EN tied to VIN (always on).")
    # 1.2 V LDO for the two hubs
    d.part("U3", "Regulator_Linear:AP2112K-1.2", "AP2112K-1.2", s, FP["SOT25"])
    d.part("C30", "Device:C", "1u 10V", s, FP["C0402"])
    d.part("C31", "Device:C", "10u 10V", s, FP["C0805"])
    d.net("+3V3", "U3.VIN", "U3.EN", "C30.1")
    d.net("GND", "U3.GND", "C30.2", "C31.2")
    d.net("+1V2", "U3.VOUT", "C31.1")
    d.nc("U3.NC")
    d.pwr_flag("+1V2")

    # ---------------------------------------------------------------- CM5
    s = "cm5"
    d.part("M1", "brain-drain:CM5", "CM5002016", s, unit_sheets={1: s, 2: s, 3: s, 4: "m2-nvme", 5: s})
    d.part("C1", "Device:C", "22u 10V", s, FP["C0805"])
    d.part("C2", "Device:C", "22u 10V", s, FP["C0805"])
    d.net("5V_SYS", "M1.5V", "C1.1", "C2.1")
    d.net("GND", "M1.GND", "C1.2", "C2.2")
    d.net("CM5_3V3", "M1.CM5_3.3V", "M1.GPIO_VREF")
    d.nc("M1.CM5_1.8V", "M1.PWR_Button", "M1.PMIC_Enable", "M1.LED_nPWR", "M1.EEPROM_nWP", "M1.WL_nDisable",
         "M1.BT_nDisable", "M1.SCL0", "M1.SDA0", "M1.CAM_GPIO0", "M1.CAM_GPIO1",
         "M1.SD_VDD_OVERRIDE", "M1.Ethernet_SYNC_OUT")
    d.note(s, "GPIO_VREF is tied to the CM5's own 3.3 V output (pins 84/86) for 3.3 V GPIO signalling, per datasheet §4.2.")
    d.note(s, "PMIC_Enable and PWR_Button are left floating (internal pull-ups). nRPIBOOT goes to jumper J6.")
    # RTC cell
    d.part("BT1", "Device:Battery_Cell", "CR2032", s, FP["CR2032"])
    d.net("VBAT", "M1.VBAT", "BT1.+")
    d.net("GND", "BT1.-")
    # nRPIBOOT jumper
    d.part("J6", "Connector_Generic:Conn_01x02", "nRPIBOOT", s, FP["HDR1x2"])
    d.net("nRPIBOOT", "M1.nRPIBOOT", "J6.1")
    d.net("GND", "J6.2")
    # UART debug
    d.part("J7", "Connector_Generic:Conn_01x03", "UART0 GND/TX/RX", s, FP["HDR1x3"])
    d.net("GND", "J7.1")
    d.net("UART0_TXD", "M1.GPIO14", "J7.2")
    d.net("UART0_RXD", "M1.GPIO15", "J7.3")
    # Fan header (Pi pinout: 1 GND, 2 +5V, 3 tacho, 4 PWM)
    d.part("J40", "Connector_Generic:Conn_01x04", "Fan GND/5V/TACH/PWM", s, FP["FAN4"])
    d.net("GND", "J40.1")
    d.net("5V_SYS", "J40.2")
    d.net("FAN_TACHO", "M1.Fan_Tacho", "J40.3")
    d.part("R10", "Device:R", "10k", s, FP["R0402"], note="FAN_PWM pull-up (open-drain output), as on CM5IO")
    d.net("+3V3", "R10.1")
    d.net("FAN_PWM", "M1.Fan_PWM", "J40.4", "R10.2")
    # Activity + power LEDs
    d.part("D1", "Device:LED", "green PWR", s, FP["LED3"])
    d.part("R1", "Device:R", "1k", s, FP["R0603"])
    d.part("D2", "Device:LED", "green ACT", s, FP["LED3"])
    d.part("R2", "Device:R", "1k", s, FP["R0603"])
    d.part("D3", "Device:LED", "red STATUS", s, FP["LED3"])
    d.part("R3", "Device:R", "1k", s, FP["R0603"])
    d.net("+3V3", "R1.1", "R2.1", "R3.1")
    d.net("D1_A", "R1.2", "D1.A")
    d.net("GND", "D1.K")
    d.net("D2_A", "R2.2", "D2.A")
    d.net("LED_nACT", "D2.K", "M1.LED_nACT")
    d.net("D3_A", "R3.2", "D3.A")
    d.net("STATUS_LED", "D3.K", "M1.GPIO26")
    d.note(s, "LED_nACT is an open-drain 20 mA output on the CM5: it sinks D2 directly. GPIO26 sinks D3 (software drives it low to light).")
    # DIP switch: GPIO16,17,20,21,22,23,24,25 = DIP1..8, other side GND (internal pull-ups in software)
    d.part("SW1", "Switch:SW_DIP_x08", "DIP x8", s, FP["DIP8"])
    for i, g in enumerate((16, 17, 20, 21, 22, 23, 24, 25), start=1):
        d.net(f"DIP{i}", f"M1.GPIO{g}", f"SW1.{i}")
        d.net("GND", f"SW1.{17 - i}")
    # No buzzer (C23): the phone page, OLED and LEDs carry the done/error signal. GPIO18 stays free.
    d.nc("M1.GPIO18")
    # OLED header: GND, VCC, SCL, SDA
    d.part("J41", "Connector_Generic:Conn_01x04", "OLED GND/VCC/SCL/SDA", s, FP["HDR1x4"])
    d.net("GND", "J41.1")
    d.net("+3V3", "J41.2")
    d.net("I2C1_SCL", "M1.GPIO3", "J41.3")
    d.net("I2C1_SDA", "M1.GPIO2", "J41.4")
    # microSD (CM5 Lite)
    d.part("J3", "Connector:Micro_SD_Card", "microSD", s, FP["MICROSD"])
    d.net("SD_CLK", "M1.SD_CLK", "J3.CLK")
    d.net("SD_CMD", "M1.SD_CMD", "J3.CMD")
    d.net("SD_DAT0", "M1.SD_DAT0", "J3.DAT0")
    d.net("SD_DAT1", "M1.SD_DAT1", "J3.DAT1")
    d.net("SD_DAT2", "M1.SD_DAT2", "J3.DAT2")
    d.net("SD_DAT3", "M1.SD_DAT3", "J3.DAT3/CD")
    d.part("U52", "brain-drain:TPS22965", "TPS22965DSGR", s, note="microSD power switch, driven by SD_PWR_ON (as CM5IO does with an RT9742)")
    d.part("R11", "Device:R", "10k", s, FP["R0402"], note="SD_PWR_ON pull-up")
    d.part("C3", "Device:C", "10u 10V", s, FP["C0805"])
    d.part("C4", "Device:C", "1u 10V", s, FP["C0402"])
    d.net("+3V3", "U52.VIN", "U52.VBIAS", "C4.1", "R11.1")
    d.net("SD_PWR_ON", "M1.SD_PWR_ON", "U52.ON", "R11.2")
    d.net("SD_VDD", "U52.VOUT", "J3.VDD", "C3.1")
    d.net("GND", "J3.VSS", "J3.SHIELD", "U52.GND", "U52.EP", "C3.2", "C4.2")
    d.nc("U52.CT", "M1.SD_DAT4", "M1.SD_DAT5", "M1.SD_DAT6", "M1.SD_DAT7")
    d.pwr_flag("SD_VDD")
    d.note(s, "microSD power goes through U52 so the CM5 can power-cycle the card on reboot via SD_PWR_ON, matching the CM5IO reference (which uses an RT9742).")
    # No Ethernet (C22): standalone appliance, Wi-Fi access point for the phone page. PHY pins unused.
    d.nc("M1.Ethernet_Pair0_P", "M1.Ethernet_Pair0_N", "M1.Ethernet_Pair1_P", "M1.Ethernet_Pair1_N",
         "M1.Ethernet_Pair2_P", "M1.Ethernet_Pair2_N", "M1.Ethernet_Pair3_P", "M1.Ethernet_Pair3_N",
         "M1.Ethernet_nLED2", "M1.Ethernet_nLED3")
    d.note(s, "Ethernet dropped (C22). The CM5 wireless variant's PCB antenna is on the short module edge that carries MH1; that edge sits on the board's left edge with an 8 mm copper-free strip under it and no metal within 10 mm (CM5 datasheet 4.1.2).")
    # USB-C for rpiboot (device mode; USB_OTG_ID floating)
    d.part("J5", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C rpiboot", s, FP["USBC16"])
    d.net("USB2_DP", "J5.D+", "M1.USB_P")
    d.net("USB2_DM", "J5.D-", "M1.USB_N")
    d.net("USBC_CC1", "J5.CC1", "M1.CC1")
    d.net("USBC_CC2", "J5.CC2", "M1.CC2")
    d.net("GND", "J5.GND", "J5.SHIELD")
    d.nc("J5.VBUS", "J5.SBU1", "J5.SBU2", "M1.USB_OTG_ID", "M1.VBUS_EN")
    d.note(s, "USB-C is a device port (rpiboot / gadget). As on the CM5IO, CC1/CC2 go straight to the CM5, which presents the sink pull-downs itself; VBUS is not connected (the board is powered from 12 V). USB_OTG_ID floats = device.")
    # bay enables and M.2 controls from GPIO
    for b, g in ((1, 5), (2, 6), (3, 12), (4, 13), (5, 7), (6, 8), (7, 9), (8, 10)):
        d.net(f"BAY_EN{b}", f"M1.GPIO{g}")
    d.net("M2_DOOR", "M1.GPIO4")
    d.net("M2_PWR_EN", "M1.GPIO27")
    d.net("M2_PEDET", "M1.GPIO19")
    d.nc("M1.ID_SD", "M1.ID_SC", "M1.GPIO11")
    # unused high-speed / video pins on M2 unit 2
    for p in kilib.get("brain-drain:CM5").pins:
        if p.unit == 5:
            d.nc(f"M1.{p.number}")

    # ---------------------------------------------------------------- hubs
    for hub, port, bays in (("A", 0, (1, 2, 3, 4)), ("B", 1, (5, 6, 7, 8))):
        s = f"usb3-hub-{hub}"
        u = "U1" if hub == "A" else "U2"
        n = u[1:]
        d.part(u, "brain-drain:USB5744", "USB5744/2G", s)
        d.part(f"Y{n}", "Device:Crystal_GND24", "25MHz CL=20pF", s, FP["XTAL3225"])
        d.part(f"C{n}00", "Device:C", "33p", s, FP["C0402"])
        d.part(f"C{n}01", "Device:C", "33p", s, FP["C0402"])
        d.part(f"R{n}00", "Device:R", "12.0k 1%", s, FP["R0402"], note="RBIAS")
        d.part(f"R{n}01", "Device:R", "10k", s, FP["R0402"], note="VBUS_DET to 3.3 V")
        d.part(f"R{n}02", "Device:R", "10k", s, FP["R0402"], note="RESET_N pull-up")
        d.part(f"R{n}03", "Device:R", "200k", s, FP["R0402"], note="CFG_NON_REM: all ports removable")
        for i in range(4):
            d.part(f"C{n}1{i}", "Device:C", "100n", s, FP["C0402"], note="VDD33 decoupling")
        for i in range(4):
            d.part(f"C{n}2{i}", "Device:C", "100n", s, FP["C0402"], note="VDD12 decoupling")
        d.part(f"C{n}30", "Device:C", "4.7u 10V", s, FP["C0603"])
        d.part(f"C{n}31", "Device:C", "4.7u 10V", s, FP["C0603"])
        # upstream SS AC caps (hub TX side)
        d.part(f"C{n}40", "Device:C", "100n", s, FP["C0402"], note="USB3 upstream TX AC coupling")
        d.part(f"C{n}41", "Device:C", "100n", s, FP["C0402"], note="USB3 upstream TX AC coupling")
        d.net("+3V3", f"{u}.VDD33", f"C{n}10.1", f"C{n}11.1", f"C{n}12.1", f"C{n}13.1", f"C{n}30.1", f"R{n}01.1", f"R{n}02.1")
        d.net("+1V2", f"{u}.VDD12", f"C{n}20.1", f"C{n}21.1", f"C{n}22.1", f"C{n}23.1", f"C{n}31.1")
        d.net("GND", f"{u}.VSS", f"{u}.ATEST", f"R{n}00.2", f"R{n}03.2", f"Y{n}.2", f"Y{n}.4",
              *[f"C{n}{a}{b}.2" for a in (1, 2) for b in range(4)], f"C{n}30.2", f"C{n}31.2", f"C{n}00.2", f"C{n}01.2")
        d.net(f"{u}_RBIAS", f"{u}.RBIAS", f"R{n}00.1")
        d.net(f"{u}_VBUS_DET", f"{u}.VBUS_DET", f"R{n}01.2")
        d.net(f"{u}_RESET_N", f"{u}.RESET_N", f"R{n}02.2")
        d.net(f"{u}_CFG_NON_REM", f"{u}.SPI_CE_N/CFG_NON_REM", f"R{n}03.1")
        d.net(f"{u}_XTALI", f"{u}.XTALI/CLK_IN", f"Y{n}.1", f"C{n}00.1")
        d.net(f"{u}_XTALO", f"{u}.XTALO", f"Y{n}.3", f"C{n}01.1")
        # upstream to CM5 USB3-port (CM5 TX has its AC caps on the module)
        d.net(f"USB3_{port}_TX_P", f"M1.USB3-{port}-TX_P", f"{u}.USB3UP_RXDP")
        d.net(f"USB3_{port}_TX_N", f"M1.USB3-{port}-TX_N", f"{u}.USB3UP_RXDM")
        d.net(f"{u}_UP_TXDP", f"{u}.USB3UP_TXDP", f"C{n}40.1")
        d.net(f"{u}_UP_TXDM", f"{u}.USB3UP_TXDM", f"C{n}41.1")
        d.net(f"USB3_{port}_RX_P", f"C{n}40.2", f"M1.USB3-{port}-RX_P")
        d.net(f"USB3_{port}_RX_N", f"C{n}41.2", f"M1.USB3-{port}-RX_N")
        d.net(f"USB3_{port}_DP", f"M1.USB3-{port}-DP", f"{u}.USB2UP_DP")
        d.net(f"USB3_{port}_DM", f"M1.USB3-{port}-DM", f"{u}.USB2UP_DM")
        # downstream ports 1-4 -> bay slots
        for pi, bay in zip((1, 2, 3, 4), bays):
            d.part(f"C{n}5{pi}", "Device:C", "100n", s, FP["C0402"], note=f"USB3 DN{pi} TX AC coupling")
            d.part(f"C{n}6{pi}", "Device:C", "100n", s, FP["C0402"], note=f"USB3 DN{pi} TX AC coupling")
            d.net(f"{u}_DN{pi}_TXDP", f"{u}.USB3DN_TXDP{pi}", f"C{n}5{pi}.1")
            d.net(f"{u}_DN{pi}_TXDM", f"{u}.USB3DN_TXDM{pi}", f"C{n}6{pi}.1")
            d.net(f"BAY{bay}_USB3_RX_P", f"C{n}5{pi}.2")   # to bridge URXP
            d.net(f"BAY{bay}_USB3_RX_N", f"C{n}6{pi}.2")
            d.net(f"BAY{bay}_USB3_TX_P", f"{u}.USB3DN_RXDP{pi}")  # from bridge UTXP via its caps
            d.net(f"BAY{bay}_USB3_TX_N", f"{u}.USB3DN_RXDM{pi}")
            d.net(f"BAY{bay}_USB2_DP", f"{u}.USB2DN_DP{pi}/PRT_DIS_P{pi}")
            d.net(f"BAY{bay}_USB2_DM", f"{u}.USB2DN_DM{pi}/PRT_DIS_M{pi}")
        d.nc(f"{u}.PRT_CTL1", f"{u}.PRT_CTL2", f"{u}.PRT_CTL3", f"{u}.PRT_CTL4/GANG_PWR",
             f"{u}.SPI_CLK/SMCLK", f"{u}.SPI_DO/SMDAT", f"{u}.SPI_DI/CFG_BC_EN")
        d.note(s, f"Hub {hub}: upstream on CM5 USB3-{port}. Downstream ports 1-4 -> bay slots {bays[0]}-{bays[3]} (C24: eight slots, four cards populated in v1).")
        d.note(s, "No SPI ROM and no SMBus pull-ups: the hub runs its internal ROM defaults. RESET_N has a pull-up only; add an RC if strap timing (1 ms hold) is a concern.")
        d.note(s, "Crystal: 25 MHz, CL 20 pF per datasheet table 10-10; 33 pF load caps assume ~3 pF stray, adjust to the chosen crystal.")

    # ---------------------------------------------------------------- bay slots (C24)
    s = "bay-slots"
    for b in range(1, 9):
        j = f"J1{b - 1}"   # J10..J17, slot n = bay n
        d.part(j, "brain-drain:BAY_SLOT", f"bay slot {b}", s)
        d.part(f"D1{b - 1}", "Device:LED", f"blue bay {b} activity", s, FP["LED3"])
        d.part(f"R6{b - 1}", "Device:R", "470", s, FP["R0402"])
        d.net("+12V", f"{j}.A1", f"{j}.A2", f"{j}.B1", f"{j}.B2", f"{j}.B3")
        d.net("5V_HDD", f"{j}.A8", f"{j}.A9", f"{j}.B8", f"{j}.B9", f"{j}.B10")
        d.net("GND", f"{j}.A3", f"{j}.A4", f"{j}.A7", f"{j}.A10", f"{j}.A11", f"{j}.A12", f"{j}.A13", f"{j}.A16", f"{j}.A17", f"{j}.A18",
              f"{j}.B4", f"{j}.B7", f"{j}.B11", f"{j}.B14", f"{j}.B17", f"{j}.B18")
        d.nc(f"{j}.A5", f"{j}.A6")
        d.net(f"BAY_EN{b}", f"{j}.B5")
        d.net(f"BAY{b}_LED_K", f"{j}.B6", f"D1{b - 1}.K")
        d.net(f"BAY{b}_LED_A", f"R6{b - 1}.2", f"D1{b - 1}.A")
        d.net("+3V3", f"R6{b - 1}.1")
        # hub side: the card's TX pair (already AC-coupled on the card) feeds the hub's RX, and the hub's
        # coupled TX pair feeds the card's RX
        d.net(f"BAY{b}_USB3_TX_P", f"{j}.A15")
        d.net(f"BAY{b}_USB3_TX_N", f"{j}.A14")
        d.net(f"BAY{b}_USB3_RX_P", f"{j}.B16")
        d.net(f"BAY{b}_USB3_RX_N", f"{j}.B15")
        d.net(f"BAY{b}_USB2_DP", f"{j}.B13")
        d.net(f"BAY{b}_USB2_DM", f"{j}.B12")
    d.note(s, "Bay slots are PCI Express x1 sockets used with the bay-card pinout (symgen SLOT_PINS), not PCIe signalling. Five contacts each for 12 V and 5 V (about 1 A per contact), grounds beside every pair. v1 populates cards in slots 1-4; slots 5-8 take cards later (bigger brick, D9).")
    d.note(s, "The bay LED sits on the brain (lid) and is sunk by the card's bridge LED pin through B6.")

    # ---------------------------------------------------------------- M.2 bay 9
    s = "m2-nvme"
    d.part("J50", "brain-drain:M2_MKEY", "M.2 M-key", s)
    d.part("U50", "brain-drain:TPS22965", "TPS22965DSGR", s)
    d.part("C500", "Device:C", "10u 10V", s, FP["C0805"])
    d.part("C501", "Device:C", "22u 10V", s, FP["C0805"])
    d.part("C502", "Device:C", "1n", s, FP["C0402"], note="CT slew")
    d.part("R500", "Device:R", "10k", s, FP["R0402"], note="M2_PWR_EN pull-down")
    d.part("R501", "Device:R", "10k", s, FP["R0402"], note="PEDET pull-up")
    d.part("R502", "Device:R", "0R (cap DNP alt)", s, FP["C0402"], note="PERp0 series: 0R populated, 100n alternative")
    d.part("R503", "Device:R", "0R (cap DNP alt)", s, FP["C0402"], note="PERn0 series: 0R populated, 100n alternative")
    d.part("R504", "Device:R", "10k", s, FP["R0402"], note="CLKREQ# pull-up")
    d.part("R505", "Device:R", "470", s, FP["R0402"])
    d.part("D50", "Device:LED", "blue M.2 activity", s, FP["LED3"])
    d.part("SW3", "Switch:SW_Push", "lid microswitch", s, FP["SW_DOOR"])
    d.net("3V3_M2", "U50.VIN", "U50.VBIAS", "C500.1")
    d.net("3V3_M2_SW", "U50.VOUT", "C501.1", "J50.3V3", "R501.1", "R504.1", "R505.1")
    d.net("GND", "U50.GND", "U50.EP", "C500.2", "C501.2", "C502.2", "R500.2", "J50.GND", "SW3.2",
          "J50.S1", "J50.S2", "J50.M3", "J50.M4")
    d.net("U50_CT", "U50.CT", "C502.1")
    d.net("M2_PWR_EN", "U50.ON", "R500.1")
    d.pwr_flag("3V3_M2_SW")
    # PCIe lane 0: CM5 TX (caps on module) -> PET; PER -> series 0R -> CM5 RX
    d.net("PCIE_TX_P", "M1.PCIe_TX_P", "J50.PETp0")
    d.net("PCIE_TX_N", "M1.PCIe_TX_N", "J50.PETn0")
    d.net("M2_PERp0", "J50.PERp0", "R502.1")
    d.net("M2_PERn0", "J50.PERn0", "R503.1")
    d.net("PCIE_RX_P", "R502.2", "M1.PCIe_RX_P")
    d.net("PCIE_RX_N", "R503.2", "M1.PCIe_RX_N")
    d.net("PCIE_CLK_P", "M1.PCIe_CLK_P", "J50.REFCLKp")
    d.net("PCIE_CLK_N", "M1.PCIe_CLK_N", "J50.REFCLKn")
    d.net("PCIE_nRST", "M1.PCIe_nRST", "J50.PERST#")
    d.net("PCIE_CLKREQ", "M1.PCIe_CLK_nREQ", "J50.CLKREQ#", "R504.2")
    d.net("PCIE_nWAKE", "M1.PCIE_nWAKE", "J50.PEWAKE#")
    d.nc("M1.PCIE_PWR_EN")
    d.net("M2_PEDET", "J50.CONFIG_1/PEDET", "R501.2")
    d.net("M2_LED_A", "R505.2", "D50.A")
    d.net("M2_DAS", "D50.K", "J50.DAS/DSS#")
    d.net("M2_DOOR", "SW3.1")
    d.nc("J50.CONFIG_0", "J50.CONFIG_2", "J50.CONFIG_3", "J50.DEVSLP", "J50.SUSCLK", "J50.MFG1", "J50.MFG2")
    for p in kilib.get("brain-drain:M2_MKEY").pins:
        if p.name == "NC" or p.name.startswith(("PER", "PET")) and p.name[-1] != "0":
            d.nc(f"J50.{p.number}")
    d.note(s, "Polarity: CM5 TX_P -> PETp0 (49), TX_N -> PETn0 (47), PERp0 (43) -> RX_P, PERn0 (41) -> RX_N. The CM5IO reference wires both pairs inverted (TX_P to 47, RX_P to 41), which PCIe link training tolerates; either works.")
    d.note(s, "Only PCIe lane 0 is wired (x1). PET = host transmit (CM5 TX, AC caps on the module). PER = host receive: per the M.2 spec the SSD carries its own TX caps, so R502/R503 are 0R; the same 0402 pads take 100n if a module without caps turns up.")
    d.note(s, "PEDET (pin 69) is pulled up and read by GPIO19: an M.2 SATA module grounds it, and the software refuses the bay instead of trying PCIe.")
    d.note(s, "Door switch SW3 to GPIO4 (software pull-up): closed = low = door shut. Software powers the slot (M2_PWR_EN, GPIO27 -> U50) and rescans PCIe.")
    return d


if __name__ == "__main__":
    d = build()
    missing = d.check()
    print(f"{len(d.comps)} components, {len(d.nets)} nets, {len(d.ncs)} explicit no-connects")
    if missing:
        print("UNASSIGNED PINS:")
        for m in missing:
            print("  ", m)
    else:
        print("every pin is assigned or NC")


def build_card() -> Design:
    """One bay card (C24): ASM1153E bridge, switched 12 V / 5 V with soft-start and PTC fuses, the 22-pin
    SATA receptacle on its rear edge, PCIe-x1 card-edge fingers to the brain. Built once per bay."""
    d = Design("brain-drain bay card: ASM1153E USB-SATA bridge, switched 12 V / 5 V, 22-pin SATA receptacle")
    d.sheet("bridge", "ASM1153E USB 3 to SATA bridge, 30 MHz crystal, core switcher, AC coupling")
    d.sheet("bay-switch", "Switched 12 V and 5 V for the drive: P-FET high-side switches with soft-start, PTC fuses")
    d.sheet("edge", "Card edge to the brain (PCIe x1 fingers, bay-card pinout) and the SATA 22-pin receptacle")

    # ---------------------------------------------------------------- edge + receptacle
    s = "edge"
    d.part("J1", "brain-drain:BAY_EDGE", "bay card edge", s)
    d.part("J2", "brain-drain:SATA22", "SATA 22-pin", s)
    d.net("+12V", "J1.A1", "J1.A2", "J1.B1", "J1.B2", "J1.B3")
    d.net("5V_HDD", "J1.A8", "J1.A9", "J1.B8", "J1.B9", "J1.B10")
    d.net("GND", "J1.A3", "J1.A4", "J1.A7", "J1.A10", "J1.A11", "J1.A12", "J1.A13", "J1.A16", "J1.A17", "J1.A18",
          "J1.B4", "J1.B7", "J1.B11", "J1.B14", "J1.B17", "J1.B18")
    d.nc("J1.A5", "J1.A6")
    d.net("BAY_EN", "J1.B5")
    d.net("LED_K", "J1.B6")
    d.net("USB3_TX_P", "J1.A15")
    d.net("USB3_TX_N", "J1.A14")
    d.net("USB3_RX_P", "J1.B16")
    d.net("USB3_RX_N", "J1.B15")
    d.net("USB2_DP", "J1.B13")
    d.net("USB2_DM", "J1.B12")
    d.pwr_flag("+12V", "5V_HDD")
    d.note(s, "Fingers: Connector_PCBEdge:BUS_PCIexpress_x1 on the card's bottom edge (chamfer the edge, ENIG is fine for a few insertions). Pinout in symgen.SLOT_PINS.")
    d.note(s, "SATA P1-P3 (3.3 V) are not connected on purpose: P3 is PWDIS on SATA 3.3 drives and a 3.3 V supply there keeps them from spinning up.")

    # ---------------------------------------------------------------- bridge
    s = "bridge"
    d.part("U1", "brain-drain:ASM1153E", "ASM1153E", s)
    d.part("Y1", "Device:Crystal_GND24", "30MHz CL=16pF", s, FP["XTAL3225"])
    d.part("C1", "Device:C", "22p", s, FP["C0402"])
    d.part("C2", "Device:C", "22p", s, FP["C0402"])
    d.part("R1", "Device:R", "12.1k 1%", s, FP["R0402"], note="REXT")
    d.part("R2", "Device:R", "10k", s, FP["R0402"], note="RST# pull-up")
    d.part("C3", "Device:C", "2.2u", s, FP["C0603"], note="RST# delay")
    d.part("L1", "Device:L", "4.7u 1A", s, FP["L_4x4"], note="core switcher inductor (value per ASMedia reference design, verify)")
    d.part("C4", "Device:C", "10u 10V", s, FP["C0805"], note="core rail")
    d.part("C5", "Device:C", "10u 10V", s, FP["C0805"], note="VCCIN bypass")
    d.part("C6", "Device:C", "10u 10V", s, FP["C0805"], note="VCCO 3.3 V out")
    for i in range(7, 13):
        d.part(f"C{i}", "Device:C", "100n", s, FP["C0402"])
    d.part("C13", "Device:C", "100n", s, FP["C0402"], note="USB3 TX AC coupling")
    d.part("C14", "Device:C", "100n", s, FP["C0402"], note="USB3 TX AC coupling")
    for i, nm in enumerate(("TX+", "TX-", "RX+", "RX-"), start=15):
        d.part(f"C{i}", "Device:C", "10n", s, FP["C0402"], note=f"SATA {nm} AC coupling")
    d.net("5V_HDD", "U1.VBUS", "U1.VBUS_LDO", "U1.VCCIN", "C5.1")   # the brain's always-on 5 V rail
    d.net("U1_LXI", "U1.LXI", "L1.1")
    d.net("U1_VDD_CORE", "L1.2", "C4.1", "U1.VDD", "U1.VDDU", "U1.VDDS", "C7.1", "C8.1")
    d.net("U1_VCCO", "U1.VCCO", "C6.1", "U1.VCC", "U1.VCCU", "U1.VCCS", "U1.VCCTXL", "C9.1", "C10.1", "C11.1", "C12.1", "R2.1")
    d.net("GND", "U1.PGND", "U1.GNDA", "U1.GND", "U1.TEST_EN", "R1.2", "C3.2", "Y1.2", "Y1.4",
          *[f"C{i}.2" for i in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12)])
    d.pwr_flag("U1_VDD_CORE")
    d.net("U1_REXT", "U1.REXT", "R1.1")
    d.net("U1_RST", "U1.RST#", "R2.2", "C3.1")
    d.net("U1_XI", "U1.XI", "Y1.1", "C1.1")
    d.net("U1_XO", "U1.XO", "Y1.3", "C2.1")
    d.net("USB2_DP", "U1.UDP")
    d.net("USB2_DM", "U1.UDM")
    d.net("USB3_RX_P", "U1.URXP")
    d.net("USB3_RX_N", "U1.URXN")
    d.net("U1_UTXP", "U1.UTXP", "C13.1")
    d.net("U1_UTXN", "U1.UTXN", "C14.1")
    d.net("USB3_TX_P", "C13.2")
    d.net("USB3_TX_N", "C14.2")
    d.net("U1_STXP", "U1.STXP", "C15.1")
    d.net("U1_STXN", "U1.STXN", "C16.1")
    d.net("SATA_A_P", "C15.2", "J2.S2")
    d.net("SATA_A_N", "C16.2", "J2.S3")
    d.net("SATA_B_P", "J2.S6", "C17.1")
    d.net("SATA_B_N", "J2.S5", "C18.1")
    d.net("U1_SRXP", "C17.2", "U1.SRXP")
    d.net("U1_SRXN", "C18.2", "U1.SRXN")
    d.net("GND", "J2.S1", "J2.S4", "J2.S7", "J2.P4", "J2.P5", "J2.P6", "J2.P10", "J2.P12")
    d.net("5V_BAY", "J2.P7", "J2.P8", "J2.P9")
    d.net("12V_BAY", "J2.P13", "J2.P14", "J2.P15")
    d.nc("J2.P1", "J2.P2", "J2.P3", "J2.P11")
    d.net("LED_K", "U1.GPIO0")
    d.nc("U1.GPIO1", "U1.GPIO2", "U1.GPIO3", "U1.GPIO4", "U1.GPIO5", "U1.GPIO6", "U1.GPIO7",
         "U1.HDDPC", "U1.I2C_DATA", "U1.I2C_CLK", "U1.UART_RX", "U1.UART_TX")
    d.note(s, "ASM1153E runs from 5 V only (the brain's always-on 5V_HDD rail through the edge): VBUS_LDO -> VCCO (3.3 V) and VCCIN -> LXI switcher -> 1.05 V core.")
    d.note(s, "Clock straps GPIO3/GPIO7 at their internal pull-up default (11) = 30 MHz crystal. GPIO6 default = I2C mode, no SPI ROM. Bay activity LED assumed on GPIO0 (verify on the bench); it sinks the brain's LED through the edge.")

    # ---------------------------------------------------------------- bay power switch
    s = "bay-switch"
    d.part("F1", "Device:Polyfuse", "3A hold 1812", s, FP["PTC1812"])
    d.part("F2", "Device:Polyfuse", "2A hold 1812", s, FP["PTC1812"])
    d.part("Q1", "brain-drain:PMOS_SSSGDDDD_EP", "AON7403", s, FP["DFN8"], note="12 V switch (AOS AON7403, -30 V, DFN 3x3-8); DFN 3x3-8 power pin-out S 1-3, G 4, D 5-8 + EP")
    d.part("Q2", "brain-drain:PMOS_SSSGDDDD_EP", "AON7403", s, FP["DFN8"], note="5 V switch (AOS AON7403); same pin-out")
    d.part("Q3", "Transistor_FET:2N7002", "2N7002", s, FP["SOT23"], note="12 V gate driver")
    d.part("Q4", "Transistor_FET:2N7002", "2N7002", s, FP["SOT23"], note="5 V gate driver")
    d.part("R3", "Device:R", "100k", s, FP["R0402"], note="Q1 gate pull-up (off)")
    d.part("R4", "Device:R", "10k", s, FP["R0402"], note="soft-start series")
    d.part("C19", "Device:C", "100n", s, FP["C0402"], note="soft-start G-S")
    d.part("R5", "Device:R", "100k", s, FP["R0402"], note="Q2 gate pull-up (off)")
    d.part("R6", "Device:R", "10k", s, FP["R0402"], note="soft-start series")
    d.part("C20", "Device:C", "100n", s, FP["C0402"], note="soft-start G-S")
    d.part("R7", "Device:R", "10k", s, FP["R0402"], note="BAY_EN pull-down: off at boot and with the slot empty")
    d.part("R8", "Device:R", "1k", s, FP["R0402"])
    d.net("BAY_EN", "R8.1", "R7.1")
    d.net("EN_G", "R8.2", "Q3.G", "Q4.G")
    d.net("GND", "R7.2", "Q3.S", "Q4.S")
    d.net("+12V", "Q1.S", "R3.1", "C19.1")
    d.net("Q1_G", "Q1.G", "R3.2", "C19.2", "R4.1")
    d.net("Q3_D", "R4.2", "Q3.D")
    d.net("12V_BAY_SW", "Q1.D", "F1.1")
    d.net("12V_BAY", "F1.2")
    d.net("5V_HDD", "Q2.S", "R5.1", "C20.1")
    d.net("Q2_G", "Q2.G", "R5.2", "C20.2", "R6.1")
    d.net("Q4_D", "R6.2", "Q4.D")
    d.net("5V_BAY_SW", "Q2.D", "F2.1")
    d.net("5V_BAY", "F2.2")
    d.pwr_flag("12V_BAY", "5V_BAY")
    d.note(s, "P-FET high-side switch: 100k gate pull-up holds it off; the 2N7002 pulls the gate down through 10k with 100n gate-source, ~1 ms ramp so the drive's bulk caps do not trip the fuse. BAY_EN pull-down keeps the bay off through boot.")
    return d
