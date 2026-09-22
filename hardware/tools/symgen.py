"""Generate hardware/lib/brain-drain.kicad_sym from the pin tables in hardware/ref.

Symbols: CM5_J1, CM5_J2 (Compute Module 5 connectors, functional units),
USB5744, ASM1153E, TPS56637, TPS22965, SATA22, M2_MKEY, DIN4_KPJX.
Run:  python3 tools/symgen.py   (from hardware/)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import pins
from sexp import q

LIB = Path(__file__).resolve().parent.parent / "lib" / "brain-drain.kicad_sym"
PIN_LEN = 5.08
PITCH = 2.54
FONT = 1.27


@dataclass
class Pin:
    number: str
    name: str
    etype: str = "passive"  # input output bidirectional passive power_in power_out open_collector no_connect
    shape: str = "line"


@dataclass
class Unit:
    name: str
    left: list[Pin] = field(default_factory=list)
    right: list[Pin] = field(default_factory=list)


@dataclass
class Symbol:
    name: str
    reference: str
    value: str
    footprint: str
    description: str
    units: list[Unit]
    datasheet: str = "~"
    keywords: str = ""
    fp_filters: str = ""

    def geometry(self, u: Unit):
        rows = max(len(u.left), len(u.right), 1)
        ml = max((len(p.name) for p in u.left), default=0)
        mr = max((len(p.name) for p in u.right), default=0)
        w = math.ceil(((ml + mr) * 1.1 + 6) * FONT / PITCH) * PITCH
        w = max(w, 4 * PITCH)
        h = (rows + 1) * PITCH
        return w, h


def _prop(name, value, x, y, hide=False, rot=0):
    eff = f"(effects (font (size {FONT} {FONT})){' (hide yes)' if hide else ''})"
    return f'\t\t(property {q(name)} {q(value)}\n\t\t\t(at {x:.2f} {y:.2f} {rot})\n\t\t\t{eff}\n\t\t)'


def _pin(p: Pin, x, y, angle):
    return (f'\t\t\t(pin {p.etype} {p.shape}\n\t\t\t\t(at {x:.2f} {y:.2f} {angle})\n\t\t\t\t(length {PIN_LEN})\n'
            f'\t\t\t\t(name {q(p.name)} (effects (font (size {FONT} {FONT}))))\n'
            f'\t\t\t\t(number {q(p.number)} (effects (font (size {FONT} {FONT}))))\n\t\t\t)')


def dedupe_power_out(sym: "Symbol") -> None:
    seen = set()
    for u in sym.units:
        for p in u.left + u.right:
            if p.etype == "power_out":
                if p.name in seen:
                    p.etype = "passive"
                seen.add(p.name)


def render(sym: Symbol) -> str:
    dedupe_power_out(sym)
    out = [f'\t(symbol {q(sym.name)}\n\t\t(pin_names (offset 1.016))\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)']
    w0, h0 = sym.geometry(sym.units[0])
    out.append(_prop("Reference", sym.reference, -w0 / 2, h0 / 2 + PITCH))
    out.append(_prop("Value", sym.value, -w0 / 2, -h0 / 2 - PITCH))
    out.append(_prop("Footprint", sym.footprint, 0, 0, hide=True))
    out.append(_prop("Datasheet", sym.datasheet, 0, 0, hide=True))
    out.append(_prop("Description", sym.description, 0, 0, hide=True))
    if sym.keywords:
        out.append(_prop("ki_keywords", sym.keywords, 0, 0, hide=True))
    if sym.fp_filters:
        out.append(_prop("ki_fp_filters", sym.fp_filters, 0, 0, hide=True))
    for ui, u in enumerate(sym.units, start=1):
        w, h = sym.geometry(u)
        body = [f'\t\t(symbol {q(f"{sym.name}_{ui}_1")}']
        body.append(f'\t\t\t(rectangle (start {-w/2:.2f} {h/2:.2f}) (end {w/2:.2f} {-h/2:.2f})\n'
                    f'\t\t\t\t(stroke (width 0.254) (type default))\n\t\t\t\t(fill (type background))\n\t\t\t)')
        body.append(f'\t\t\t(text {q(u.name)} (at 0 {h/2 - 1.5:.2f} 0) (effects (font (size 1 1))))')
        for i, p in enumerate(u.left):
            y = h / 2 - PITCH * (i + 1)
            body.append(_pin(p, -w / 2 - PIN_LEN, y, 0))
        for i, p in enumerate(u.right):
            y = h / 2 - PITCH * (i + 1)
            body.append(_pin(p, w / 2 + PIN_LEN, y, 180))
        body.append("\t\t)")
        out.append("\n".join(body))
    out.append("\t\t(embedded_fonts no)\n\t)")
    return "\n".join(out)


# ---------------------------------------------------------------- symbol definitions

def _etype_cm5(sig: str) -> str:
    if sig == "GND":
        return "power_in"
    if sig.startswith("5V"):
        return "power_in"
    if "(Output)" in sig:
        return "power_out"
    if sig == "GPIO_VREF":
        return "power_in"
    if sig.startswith("GPIO") or sig.startswith("SD_DAT") or sig in ("ID_SD", "ID_SC", "SDA0", "SCL0", "SD_CMD",
                                                                    "HDMI0_SDA", "HDMI0_SCL", "HDMI1_SDA", "HDMI1_SCL",
                                                                    "HDMI0_CEC", "HDMI1_CEC", "CAM_GPIO0", "CAM_GPIO1",
                                                                    "USB_N", "USB_P") or "-DP" in sig or "-DM" in sig:
        return "bidirectional"
    if "TX" in sig or sig.endswith("_P") and "CLK" in sig or sig.endswith("_N") and "CLK" in sig:
        return "output"
    if "RX" in sig or "Pair" in sig or "MIPI" in sig:
        return "input" if "RX" in sig else "bidirectional"
    if sig in ("PCIe_nRST", "VBUS_EN", "PCIE_PWR_EN", "LED_nACT", "LED_nPWR", "SD_CLK", "SD_PWR_ON",
               "Ethernet_nLED2", "Ethernet_nLED3", "Fan_PWM", "Ethernet_SYNC_OUT"):
        return "output"
    return "input"


def _clean(sig: str) -> str:
    return sig.replace(" (Input)", "").replace(" (Output)", "")


def cm5_symbols():
    t = pins.cm5()

    def P(n):
        sig, _ = t[n]
        return Pin(str(n if n <= 100 else n - 100), _clean(sig), _etype_cm5(sig))

    def group(nums):
        return [P(n) for n in nums]

    j1_gnd = [n for n in range(1, 101) if t[n][0] == "GND"]
    j2_gnd = [n for n in range(101, 201) if t[n][0] == "GND"]
    pwr = Unit("PWR / CTRL (pins 1-100)",
               left=group([77, 79, 81, 83, 85, 87, 84, 86, 88, 90, 78, 76, 92, 99, 93, 95, 21, 20, 89, 91, 16, 19]),
               right=group([94, 96, 80, 82, 97, 100, 73, 75, 18]) + group(j1_gnd))
    gpio_order = {0: 36, 1: 35, 2: 58, 3: 56, 4: 54, 5: 34, 6: 30, 7: 37, 8: 39, 9: 40, 10: 44, 11: 38, 12: 31,
                  13: 28, 14: 55, 15: 51, 16: 29, 17: 50, 18: 49, 19: 26, 20: 27, 21: 25, 22: 46, 23: 47, 24: 45,
                  25: 41, 26: 24, 27: 48}
    gpio = Unit("GPIO / SD (pins 1-100)",
                left=group([gpio_order[i] for i in range(0, 28)]),
                right=group([57, 62, 63, 67, 69, 61, 68, 64, 72, 70]))
    eth = Unit("ETHERNET (pins 1-100)",
               left=group([12, 10, 4, 6, 11, 9, 3, 5]),
               right=group([17, 15]))
    j1 = Symbol("CM5_J1", "M", "CM5_J1", "Connector_Hirose_DF40:Hirose_DF40C-100DS-0.4V_2x50_P0.4mm",
                "Raspberry Pi Compute Module 5, connector J1 (CM5 pins 1-100)", [pwr, gpio, eth],
                datasheet="https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf", keywords="raspberry pi cm5")
    hs = Unit("USB / PCIe (pins 101-200, number = pin-100)",
              left=group([101, 103, 105, 111, 128, 130, 134, 136, 140, 142, 157, 159, 163, 165, 169, 171]),
              right=group([102, 104, 106, 109, 110, 112, 116, 118, 122, 124]) + group(j2_gnd))
    rest = [n for n in range(101, 201) if t[n][0] != "GND" and n not in
            {101, 103, 105, 111, 128, 130, 134, 136, 140, 142, 157, 159, 163, 165, 169, 171,
             102, 104, 106, 109, 110, 112, 116, 118, 122, 124}]
    half = (len(rest) + 1) // 2
    video = Unit("HDMI / MIPI, unused (pins 101-200)", left=group(rest[:half]), right=group(rest[half:]))
    j2 = Symbol("CM5_J2", "M", "CM5_J2", "Connector_Hirose_DF40:Hirose_DF40C-100DS-0.4V_2x50_P0.4mm",
                "Raspberry Pi Compute Module 5, connector J2 (CM5 pins 101-200)", [hs, video],
                datasheet="https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf", keywords="raspberry pi cm5")
    return [j1, j2]


def usb5744_symbol():
    t = pins.usb5744()

    def P(n, etype=None):
        name, buf = t[str(n)]
        if etype is None:
            if name.startswith("VDD"):
                etype = "power_in"
            elif "TXD" in name:
                etype = "output"
            elif "RXD" in name:
                etype = "input"
            elif name.startswith("USB2"):
                etype = "bidirectional"
            elif name in ("RESET_N", "VBUS_DET", "XTALI/CLK_IN"):
                etype = "input"
            elif name in ("XTALO", "ATEST", "RBIAS"):
                etype = "passive"
            elif name.startswith("PRT_CTL"):
                etype = "bidirectional"
            else:
                etype = "bidirectional"
        return Pin(str(n), name, etype)

    left = [P(n) for n in (45, 46, 47, 48, 50, 51, 54, 53, 56, 42, 37, 52, 38, 39, 40, 41, 36, 35, 34, 32)]
    right = [P(n) for n in (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27, 29, 30)]
    right += [P(n) for n in (16, 31, 44, 55)] + [P(n) for n in (5, 12, 15, 21, 28, 33, 43, 49)] + [Pin("EP", "VSS", "power_in")]
    return Symbol("USB5744", "U", "USB5744/2G", "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
                  "Microchip USB5744 4-port USB 3.2 Gen1 hub, 56-VQFN 7x7", [Unit("USB5744", left, right)],
                  datasheet="https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/USB5744-Data-Sheet-DS00001855.pdf",
                  keywords="usb hub", fp_filters="QFN*56*7x7*")


def asm1153e_symbol():
    t = pins.asm1153e()

    def P(n):
        name, typ, _ = t[n]
        etype = {"DI": "input", "DO": "output", "DB": "bidirectional", "I": "input", "O": "output",
                 "B": "bidirectional", "P": "power_in", "G": "power_in", "AI": "input", "AO": "output"}.get(typ, "passive")
        if name == "VCCO":
            etype = "power_out"
        if name in ("LXI", "REXT", "XI", "XO"):
            etype = "passive"
        return Pin(str(n), name, etype)

    left = [P(n) for n in (10, 15, 16, 20, 19, 23, 22, 17, 25, 26, 38, 42, 43, 44, 45, 2, 3, 5, 6, 8, 9, 35, 37, 40, 41)]
    right = [P(n) for n in (33, 32, 29, 30, 1, 48, 47, 11, 12, 4, 39, 14, 18, 34, 27, 7, 36, 46, 13, 24, 28, 21, 31, 49)]
    return Symbol("ASM1153E", "U", "ASM1153E", "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm",
                  "ASMedia ASM1153E USB 3.0 to SATA 6G bridge, QFN-48 6x6", [Unit("ASM1153E", left, right)],
                  keywords="usb sata bridge", fp_filters="QFN*48*6x6*")


def tps56637_symbol():
    left = [Pin("8", "VIN", "power_in"), Pin("1", "EN", "input"), Pin("10", "MODE", "input"), Pin("2", "FB", "input"),
            Pin("5", "NC", "no_connect")]
    right = [Pin("7", "BOOT", "passive"), Pin("6", "SW", "output"), Pin("4", "PG", "open_collector"),
             Pin("3", "AGND", "power_in"), Pin("9", "PGND", "power_in")]
    return Symbol("TPS56637", "U", "TPS56637RPAR", "brain-drain:Texas_RPA0010A_VQFN-HR-10_3x3mm",
                  "TI TPS56637 4.5-28V 6A synchronous buck, VQFN-HR-10 3x3", [Unit("TPS56637", left, right)],
                  datasheet="https://www.ti.com/lit/ds/symlink/tps56637.pdf", keywords="buck regulator")


def tps22965_symbol():
    left = [Pin("1", "VIN", "power_in"), Pin("2", "VIN", "power_in"), Pin("3", "ON", "input"), Pin("4", "VBIAS", "power_in")]
    right = [Pin("8", "VOUT", "power_out"), Pin("7", "VOUT", "power_out"), Pin("6", "CT", "passive"),
             Pin("5", "GND", "power_in"), Pin("9", "EP", "power_in")]
    return Symbol("TPS22965", "U", "TPS22965DSGR", "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm",
                  "TI TPS22965 5.5V 6A load switch, WSON-8 2x2", [Unit("TPS22965", left, right)],
                  datasheet="https://www.ti.com/lit/ds/symlink/tps22965.pdf", keywords="load switch")


def sata22_symbol():
    data = [("S1", "GND", "power_in"), ("S2", "A+", "output"), ("S3", "A-", "output"), ("S4", "GND", "power_in"),
            ("S5", "B-", "input"), ("S6", "B+", "input"), ("S7", "GND", "power_in")]
    power = [("P1", "3V3", "passive"), ("P2", "3V3", "passive"), ("P3", "3V3_PWDIS", "passive"),
             ("P4", "GND", "power_in"), ("P5", "GND", "power_in"), ("P6", "GND", "power_in"),
             ("P7", "5V", "power_in"), ("P8", "5V", "power_in"), ("P9", "5V", "power_in"),
             ("P10", "GND", "power_in"), ("P11", "DAS", "passive"), ("P12", "GND", "power_in"),
             ("P13", "12V", "power_in"), ("P14", "12V", "power_in"), ("P15", "12V", "power_in")]
    return Symbol("SATA22", "J", "SATA_22pin_receptacle", "brain-drain:SATA_22pin_Receptacle_RA",
                  "SATA 22-pin (7+15) backplane-style receptacle, right angle; P3 is PWDIS on SATA 3.3 drives",
                  [Unit("SATA 22", [Pin(*d) for d in data], [Pin(*p) for p in power])], keywords="sata")


def m2_symbol():
    t = pins.m2_mkey()

    def P(n):
        s = t[n]
        if s == "GND" or s == "3V3":
            e = "power_in"
        elif s.startswith("PET") or s in ("PERST#", "REFCLKn", "REFCLKp"):
            e = "input"   # host drives these into the module
        elif s.startswith("PER") or s in ("CLKREQ#", "PEWAKE#", "DAS/DSS#", "CONFIG_1/PEDET"):
            e = "output"  # module drives these
        elif s == "NC":
            e = "no_connect"
        else:
            e = "passive"
        return Pin(str(n), s, e)

    odd = [P(n) for n in sorted(t) if n % 2 == 1]
    even = [P(n) for n in sorted(t) if n % 2 == 0]
    return Symbol("M2_MKEY", "J", "M.2_M-Key_Socket", "brain-drain:M2_Socket3_MKey_4.2mm",
                  "M.2 Socket 3, M key, host side (PCIe x1 used); pins 59-66 are the key notch",
                  [Unit("M.2 M-KEY", odd, even)], keywords="m.2 nvme")


def din4_symbol():
    left = [Pin("1", "1", "passive"), Pin("2", "2", "passive")]
    right = [Pin("3", "3", "passive"), Pin("4", "4", "passive"), Pin("5", "SHIELD", "passive")]
    return Symbol("DIN4_KPJX", "J", "KPJX-4S-S", "brain-drain:Kycon_KPJX-4S-S",
                  "Kycon KPJX-4S-S 4-pin DIN power jack, 7.5 A/pin; pin assignment follows the chosen 12 V brick",
                  [Unit("DIN 4", left, right)], keywords="din power jack")


def build() -> str:
    syms = cm5_symbols() + [usb5744_symbol(), asm1153e_symbol(), tps56637_symbol(), tps22965_symbol(),
                            sata22_symbol(), m2_symbol(), din4_symbol()]
    body = "\n".join(render(s) for s in syms)
    return f'(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "brain-drain-symgen")\n\t(generator_version "9.0")\n{body}\n)\n'


if __name__ == "__main__":
    LIB.parent.mkdir(exist_ok=True)
    LIB.write_text(build())
    names = re.findall(r'^\t\(symbol "([^"]+)"', LIB.read_text(), re.M)
    print(f"wrote {LIB.relative_to(LIB.parents[2])}: {len(names)} symbols: {', '.join(names)}")
