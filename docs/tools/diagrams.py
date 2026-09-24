"""Generate the documentation diagrams as SVG (+PNG via cairosvg when available):
   docs/img/system-block.svg   architecture block diagram
   docs/img/left-panel.svg   wall elevation with the cutouts, from enclosure/board.scad
   docs/img/bay-flow.svg       per-bay state machine
Run from the repo root:  software/.venv/bin/python docs/tools/diagrams.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "docs" / "img"
FONT = "font-family='Helvetica, Arial, sans-serif'"


def box(x, y, w, h, title, sub="", fill="#e8eef7", stroke="#2c3e50"):
    t = f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{fill}' stroke='{stroke}' stroke-width='2'/>"
    t += f"<text x='{x + w / 2}' y='{y + 24}' text-anchor='middle' {FONT} font-size='15' font-weight='700' fill='#1f2d3d'>{title}</text>"
    if sub:
        for i, line in enumerate(sub.split("|")):
            t += f"<text x='{x + w / 2}' y='{y + 44 + i * 16}' text-anchor='middle' {FONT} font-size='12' fill='#34495e'>{line}</text>"
    return t


def arrow(x1, y1, x2, y2, label="", color="#2c3e50", width=2, dash=""):
    d = f" stroke-dasharray='{dash}'" if dash else ""
    t = f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' stroke-width='{width}' marker-end='url(#ah)'{d}/>"
    if label:
        t += f"<text x='{(x1 + x2) / 2}' y='{(y1 + y2) / 2 - 6}' text-anchor='middle' {FONT} font-size='11' fill='{color}'>{label}</text>"
    return t


def svg(w, h, body, out):
    head = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}'>"
            "<defs><marker id='ah' markerWidth='10' markerHeight='8' refX='9' refY='4' orient='auto'>"
            "<path d='M0,0 L10,4 L0,8 z' fill='#2c3e50'/></marker></defs>"
            f"<rect width='100%' height='100%' fill='white'/>")
    (IMG / out).write_text(head + body + "</svg>")
    try:
        import cairosvg
        cairosvg.svg2png(url=str(IMG / out), write_to=str(IMG / out.replace(".svg", ".png")), output_width=w * 2)
    except Exception as e:  # noqa: BLE001
        print("png skipped:", e)
    print("wrote", out)


def system_block():
    b = ""
    b += f"<text x='560' y='30' text-anchor='middle' {FONT} font-size='20' font-weight='700' fill='#1f2d3d'>brain-drain carrier board: system block diagram</text>"
    # power column
    b += box(20, 70, 150, 60, "12 V DC in", "4-pin DIN, 10 A brick", "#fdf2e9")
    b += box(20, 160, 150, 70, "Protection", "10 A fuse, TVS,|reverse-polarity FET", "#fdf2e9")
    b += box(20, 260, 150, 60, "5V_SYS buck", "TPS56637, 6 A", "#fdf2e9")
    b += box(20, 340, 150, 60, "5V_HDD buck", "TPS56637, 6 A", "#fdf2e9")
    b += box(20, 420, 150, 60, "+3V3 / 3V3_M2", "2x AP63203, 1.2 V LDO", "#fdf2e9")
    b += arrow(95, 130, 95, 160) + arrow(95, 230, 95, 260) + arrow(60, 230, 60, 340, dash="4 3") + arrow(130, 230, 130, 420, dash="4 3")
    # CM5 and panel
    b += box(260, 200, 220, 130, "Raspberry Pi CM5", "2 GB / 16 GB eMMC|GbE, USB 2.0, GPIO, I2C|2x USB 3.0, PCIe Gen3 x1", "#e8f6ef")
    b += arrow(170, 290, 260, 265, "5V_SYS")
    b += box(260, 60, 220, 100, "Panel", "8-way DIP (policy)|128x64 I2C OLED (QR code)|8 LEDs", "#fff9e6")
    b += arrow(370, 200, 370, 160, "GPIO / I2C")
    b += box(560, 215, 170, 70, "Wi-Fi AP + phone page", "USB-C rpiboot, microSD, UART", "#f4f4f4")
    b += arrow(560, 250, 480, 265)
    # hubs
    b += box(560, 90, 170, 70, "USB5744 hub A", "USB 3.0 port 0", "#e8eef7")
    b += box(560, 340, 170, 70, "USB5744 hub B", "USB 3.0 port 1", "#e8eef7")
    b += arrow(480, 225, 560, 130, "5 Gb/s") + arrow(480, 315, 560, 370, "5 Gb/s")
    # bay slots + cards (C24): hub A -> slots 1-4, hub B -> slots 5-8; cards 1-4 fitted in v1
    for i in range(8):
        y = 20 + i * 58
        hub_y = 125 if i < 4 else 375
        fitted = i < 4
        b += box(800, y, 300, 46, f"slot {i + 1}: bay card" if fitted else f"slot {i + 1}: empty (expansion)",
                 "ASM1153E, 12 V / 5 V switch, PTC, 22-pin cable" if fitted else "PCIe-x1 socket, custom pinout",
                 "#eef7e8" if fitted else "#f4f4f4")
        b += arrow(730, hub_y, 800, y + 23, "5 Gb/s" if i in (0, 4) else "")
    b += f"<text x='950' y='510' text-anchor='middle' {FONT} font-size='11' fill='#34495e'>each slot carries +12V, 5V_HDD, BAY_EN and the bay LED</text>"
    b += arrow(170, 370, 260, 560, "5V_HDD, +12V")
    b += box(260, 540, 220, 50, "Bay power", "5V_HDD and +12V to the eight slots", "#fdf2e9")
    # M.2
    b += box(560, 460, 170, 70, "M.2 M-key, bay 9", "PCIe Gen3 x1, 3V3_M2 switch,|lid switch, PEDET", "#f4f4f4")
    b += arrow(480, 320, 560, 480, "PCIe")
    svg(1120, 600, b, "system-block.svg")


PANELS = {
    # kind: (title, axis, mirrored, names)
    "left": ("Left wall from outside (rear edge at the right)", "y", True,
             {"J21": "DIN 12 V", "J5": "USB-C", "J3": "microSD"}),
}


def panel(kind):
    """Elevation of one enclosure wall from enclosure/board.scad (cutouts before print clearance)."""
    txt = (ROOT / "enclosure" / "board.scad").read_text()
    bw = float(re.search(r"board_w = ([\d.]+)", txt).group(1))
    bh = float(re.search(r"board_h = ([\d.]+)", txt).group(1))
    title, axis, mirrored, names = PANELS[kind]
    kinds = (kind,)
    feats = []
    for k in kinds:
        feats += re.findall(r'\["(\w+)", "%s", ([\d.-]+), ([\d.-]+), (-?\d+), ([\d.]+), ([\d.]+), ([\d.]+)\]' % k, txt)
    length = bw if axis == "x" else bh
    S = 6.0  # px per mm
    W = max(int(length * S + 120), 1000); H = 360
    b = f"<text x='{W / 2}' y='28' text-anchor='middle' {FONT} font-size='18' font-weight='700' fill='#1f2d3d'>{title}; mm along the board edge</text>"
    y0 = 240  # board top surface line
    b += f"<rect x='60' y='{y0 - 40 * S / 2 - 10}' width='{length * S}' height='{40 * S / 2 + 40}' fill='#f2efe6' stroke='#7f8c8d'/>"
    b += f"<line x1='60' y1='{y0}' x2='{60 + length * S}' y2='{y0}' stroke='#7f8c8d' stroke-dasharray='6 4'/>"
    b += f"<text x='{60 + length * S + 6}' y='{y0 + 4}' {FONT} font-size='11' fill='#7f8c8d'>board top</text>"
    for ref, x, y, rot, w, h, z in feats:
        u = float(x) if axis == "x" else float(y)
        w, h, z = float(w), float(h), float(z)
        if ref == "J50":   # the M.2 slot is the door opening, not the socket
            w, h, z = 26.0, 8.0, 0.5
        if mirrored:
            u = length - u
        px = 60 + (u - w / 2) * S; py = y0 - (z + h) * S
        b += f"<rect x='{px}' y='{py}' width='{w * S}' height='{h * S}' fill='#2c3e50' opacity='0.85' rx='3'/>"
        b += f"<text x='{60 + u * S}' y='{py - 8}' text-anchor='middle' {FONT} font-size='12' font-weight='700' fill='#1f2d3d'>{names.get(ref, ref)}</text>"
        b += f"<text x='{60 + u * S}' y='{y0 + 22}' text-anchor='middle' {FONT} font-size='11' fill='#34495e'>{'x' if axis == 'x' else 'y'}={float(x) if axis == 'x' else float(y):.0f}</text>"
        b += f"<text x='{60 + u * S}' y='{y0 + 36}' text-anchor='middle' {FONT} font-size='10' fill='#7f8c8d'>{w:.0f}x{h:.0f}</text>"
    b += f"<text x='60' y='{H - 20}' {FONT} font-size='12' fill='#34495e'>Connector faces before the 0.6 mm print clearance. Board {bw:.0f} x {bh:.0f} mm (C24). Right wall: antenna, vents. Rear: eight bay slots under lid windows. Front: latch.</text>"
    svg(W, H, b, f"{kind}-panel.svg")


def lid_plan():
    """Plan view of the lid: the eight slot windows, LEDs, OLED, DIP and the M.2 bay under it (from board.scad, C24)."""
    txt = (ROOT / "enclosure" / "board.scad").read_text()
    bw = float(re.search(r"board_w = ([\d.]+)", txt).group(1))
    bh = float(re.search(r"board_h = ([\d.]+)", txt).group(1))
    feats = re.findall(r'\["(\w+)", "(\w+)", ([\d.-]+), ([\d.-]+), (-?\d+), ([\d.]+), ([\d.]+), ([\d.]+)\]', txt)
    S = 5.0
    W = int(bw * S + 120); H = int(bh * S + 130)
    b = f"<text x='{W / 2}' y='28' text-anchor='middle' {FONT} font-size='18' font-weight='700' fill='#1f2d3d'>Lid, viewed from above (rear edge at the top); windows before the 0.6 mm print clearance</text>"
    x0, y0 = 60, 60
    b += f"<rect x='{x0}' y='{y0}' width='{bw * S}' height='{bh * S}' fill='#f2efe6' stroke='#7f8c8d'/>"
    for ref, kind, x, y, rot, w, h, z in feats:
        x, y, w, h = float(x), float(y), float(w), float(h)
        if kind == "slot":
            px, py = x0 + (x - w / 2) * S, y0 + (y - h / 2) * S
            b += f"<rect x='{px}' y='{py}' width='{w * S}' height='{h * S}' fill='#2c3e50' opacity='0.85' rx='3'/>"
            b += f"<text x='{x0 + x * S}' y='{py - 6}' text-anchor='middle' {FONT} font-size='11' font-weight='700' fill='#1f2d3d'>slot {int(ref[1:]) - 9}</text>"
        elif kind == "led":
            b += f"<circle cx='{x0 + x * S}' cy='{y0 + y * S}' r='{w / 2 * S}' fill='#2c3e50' opacity='0.85'/>"
        elif kind == "m2":
            px, py = x0 + (x - h / 2) * S, y0 + (y - w / 2) * S
            b += f"<rect x='{px}' y='{py}' width='{h * S}' height='{w * S}' fill='none' stroke='#7f8c8d' stroke-dasharray='5 4'/>"
            b += f"<text x='{x0 + x * S}' y='{y0 + y * S + 4}' text-anchor='middle' {FONT} font-size='11' fill='#7f8c8d'>M.2 bay 9 (under the lid)</text>"
        elif kind == "cm5":
            px, py = x0 + (x - h / 2) * S, y0 + (y - w / 2) * S
            b += f"<rect x='{px}' y='{py}' width='{h * S}' height='{w * S}' fill='none' stroke='#7f8c8d' stroke-dasharray='5 4'/>"
            b += f"<text x='{x0 + x * S}' y='{y0 + y * S + 4}' text-anchor='middle' {FONT} font-size='11' fill='#7f8c8d'>CM5 + grille</text>"
    b += f"<text x='{x0}' y='{H - 30}' {FONT} font-size='12' fill='#34495e'>Board {bw:.0f} x {bh:.0f} mm. Drive cables rise through the slot windows; the OLED and DIP cutouts are in enclosure/params.scad (oled_pos, dip_pos).</text>"
    b += f"<text x='{x0}' y='{H - 14}' {FONT} font-size='12' fill='#34495e'>Left wall: DIN 12 V, USB-C, microSD. Right wall: antenna side, vents only. Front: lid latch. Rear: hinge.</text>"
    svg(W, H, b, "lid-plan.svg")


def rear_panel():
    for kind in PANELS:
        panel(kind)
    lid_plan()


def bay_flow():
    b = f"<text x='500' y='30' text-anchor='middle' {FONT} font-size='18' font-weight='700' fill='#1f2d3d'>Per-bay state machine (USB bays 1-8; bay 9 adds the slot power step)</text>"
    states = [("IDLE", 40, "bay powered,|no drive"), ("DETECTED", 240, "identify, SMART,|grace countdown"), ("RUNNING", 440, "method chain,|then verify"),
              ("DONE", 640, "certificate,|drive spun down"), ("ERROR", 840, "certificate,|not sanitized")]
    for name, x, sub in states:
        b += box(x, 120, 150, 80, name, sub, "#e8eef7" if name not in ("ERROR",) else "#fdecea")
    b += arrow(190, 160, 240, 160, "drive add") + arrow(390, 160, 440, 160, "grace over") + arrow(590, 160, 640, 160, "verified") + arrow(590, 175, 840, 175, "fail", "#c0392b")
    b += box(440, 280, 150, 60, "ABORTED", "certificate: aborted", "#fdecea")
    b += arrow(515, 200, 515, 280, "drive removed", "#c0392b")
    b += f"<path d='M715,200 C715,360 115,360 115,200' fill='none' stroke='#2c3e50' stroke-width='2' marker-end='url(#ah)' stroke-dasharray='5 4'/>"
    b += f"<text x='420' y='372' text-anchor='middle' {FONT} font-size='11' fill='#2c3e50'>drive removed (from any state) returns the bay to IDLE</text>"
    b += box(40, 420, 920, 90, "Bay 9 (M.2) in front of IDLE", "door closed and PEDET = PCIe -> slot power on -> 1 s -> PCIe rescan -> NVMe appears -> IDLE/DETECTED as above|door opened at any time -> abort, PCIe remove, slot power off. No device in 10 s -> power off and latch until the door cycles.", "#fff9e6")
    svg(1000, 540, b, "bay-flow.svg")


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    system_block(); rear_panel(); bay_flow()
