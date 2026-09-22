"""Render what the 128x64 OLED shows, as PNGs for the docs, using the real frame renderer.
    .venv/bin/python tools/oled_mockup.py ../docs/img
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from braindrain import display
from braindrain.devices import Drive
from braindrain.engine import BayStatus
from braindrain.policy import Media
from braindrain.progress import Progress

COLS, ROWS = 21, 8
SCALE = 6
PAD = 28


MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def _font(size, mono=False):
    try:
        if mono:
            return ImageFont.truetype(MONO, size)
        return ImageFont.load_default(size=size)
    except (OSError, TypeError):
        return ImageFont.load_default()


def frame_png(lines, path: Path, title: str, bitmap=None, scale=2, text_x=0):
    font = _font(8, mono=True)   # ~4.8 px advance: 21 columns in 128 px, like a 6x8 panel font
    small = Image.new("L", (128, 64), 0)
    d = ImageDraw.Draw(small)
    if bitmap:
        for y, row in enumerate(bitmap):
            for x, on in enumerate(row):
                if on:
                    d.rectangle((x * scale, y * scale, x * scale + scale - 1, y * scale + scale - 1), fill=255)
    for i, line in enumerate(lines[:ROWS]):
        for j, ch in enumerate(line[:COLS]):
            d.text((text_x + j * 6, i * 8 - 1), ch, fill=255, font=font)
    big = small.resize((128 * SCALE, 64 * SCALE), Image.NEAREST)
    out = Image.new("RGB", (128 * SCALE + 2 * PAD, 64 * SCALE + 2 * PAD + 44), (16, 18, 22))
    od = ImageDraw.Draw(out)
    od.rounded_rectangle((PAD - 10, PAD - 10, PAD + 128 * SCALE + 10, PAD + 64 * SCALE + 10), radius=10,
                         fill=(30, 32, 38), outline=(70, 74, 82), width=3)
    yellow = Image.new("RGB", big.size, (255, 200, 40))
    out.paste(yellow, (PAD, PAD), big)
    od.text((PAD, PAD + 64 * SCALE + 18), title, fill=(160, 168, 180), font=_font(15))
    out.save(path)
    print("wrote", path)


def status(bay, state, drive=None, phase="", frac=None, eta=None, rate=None, tier="", msg="", countdown=0, slot="OFF"):
    st = BayStatus(bay)
    st.state, st.drive, st.message, st.tier_label, st.countdown, st.slot = state, drive, msg, tier, countdown, slot
    p = Progress()
    p.phase, p.fraction, p.eta_s, p.rate_bps = phase, frac, eta, rate
    st.progress = p
    return st


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    hdd = Drive(bay=1, dev_path="/dev/sda", model="WD40EFRX", serial="WCC7K1", size_bytes=4_000_787_030_016, media=Media.HDD)
    ssd = Drive(bay=2, dev_path="/dev/sdb", model="860 EVO", serial="S3Z8NB", size_bytes=1_000_204_886_016, media=Media.SSD)
    hdd2 = Drive(bay=3, dev_path="/dev/sdc", model="ST4000DM", serial="ZDH1", size_bytes=4_000_787_030_016, media=Media.HDD)
    hdd3 = Drive(bay=4, dev_path="/dev/sdd", model="HGST HUS", serial="X", size_bytes=2_000_398_934_016, media=Media.HDD)
    nvme = Drive(bay=5, dev_path="/dev/nvme0n1", model="SN770", serial="2321", size_bytes=1_000_204_886_016, media=Media.NVME)
    unit = "brain-drain 14:02 10.0.0.42"
    running = {
        1: status(1, "RUNNING", hdd, "OVW", 0.42, 6 * 3600 + 12 * 60, 152e6),
        2: status(2, "DONE", ssd, tier="PURGE"),
        3: status(3, "RUNNING", hdd2, "VRFY", 0.87, 41 * 60, 168e6),
        4: status(4, "DETECTED", hdd3, countdown=3),
        5: status(5, "RUNNING", nvme, "SANZ", 0.65, 95, None, slot="ON"),
    }
    frame_png(display.render("AUTO", running, unit), out_dir / "oled-running.png",
              "Running: bay 1 overwriting, bay 2 done (Purge), bay 3 verifying, bay 4 starting, bay 5 NVMe sanitize")
    idle = {b: status(b, "IDLE") for b in (1, 2, 3, 4)}
    idle[5] = status(5, "IDLE", slot="OFF")
    frame_png(display.render("AUTO", idle, unit), out_dir / "oled-idle.png", "Idle: no drives, bay 5 door open")
    err = dict(running)
    err[1] = status(1, "ERROR", hdd, msg="verify fail")
    err[3] = status(3, "ABORTED", hdd2, msg="removed")
    frame_png(display.render("3PASS", err, unit, "bay 5: SATA M.2 not supported"), out_dir / "oled-errors.png",
              "Errors: verify failure, drive pulled mid-wipe, SATA M.2 refused; DIP set to legacy 3-pass")
    # idle on the access point: the Wi-Fi QR code plus the key and address (C22)
    from braindrain.wifi import WifiState
    w = WifiState(mode="ap", ssid="brain-drain-7f3a", key="kx7m2pq4", ip="10.42.0.1")
    f = display.frame("AUTO", {b: status(b, "IDLE") for b in (1, 2, 3, 4, 5)}, unit, "", w)
    frame_png(f.lines, out_dir / "oled-wifi.png", "Idle on the access point: scan the QR code to join, then open the address; the key also unlocks actions on the phone page",
              bitmap=f.bitmap, scale=f.bitmap_scale, text_x=f.text_x)
    w2 = WifiState(mode="station", ssid="shop-wifi", key="kx7m2pq4", ip="192.168.1.77")
    f2 = display.frame("AUTO", running, unit, "", w2)
    frame_png(f2.lines, out_dir / "oled-running.png", "Running on the shop network: bay 1 overwriting, bay 2 done (Purge), bay 3 verifying, bay 4 starting, bay 5 NVMe sanitize; key and address on the bottom rows")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "../docs/img"))
