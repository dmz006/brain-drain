"""OLED frame rendering. Pure: bay states in, 8 lines of 21 characters out.

128x64 with a 6x8 font gives 21 columns x 8 rows:
    row 0   BRAIN-DRAIN     AUTO
    row 1-4 one line per bay
    row 5   blank / message
    row 6-7 unit line (ip / time / counts)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .progress import fmt_eta, fmt_rate, fmt_size

COLS = 21
ROWS = 8
QR_COLS = 11   # text columns to the right of a 2 px/module QR code (58 px + 4 px gap = 62 px; 66 px left)


@dataclass
class Frame:
    """One display refresh: 8 text lines, optionally with a bitmap (the Wi-Fi QR code) drawn at the
    left edge, in which case the text is meant for the columns to its right."""

    lines: list[str] = field(default_factory=list)
    bitmap: list[list[bool]] | None = None
    bitmap_scale: int = 2
    text_x: int = 0   # pixel column where the text starts


def fit(s: str, n: int = COLS) -> str:
    return s[:n].ljust(n)


def bay_line(bay: int, st) -> str:
    """st is an engine.BayStatus-like object with .state, .drive, .progress, .message."""
    state = st.state
    if state == "IDLE":
        slot = getattr(st, "slot", None)
        if slot == "OFF" and bay > 8:
            return fit(f"{bay} ---- lid open")
        if slot in ("POWERING", "ON") and bay > 8:
            return fit(f"{bay} ---- scanning")
        if slot == "LATCHED" and bay > 8:
            return fit(f"{bay} ---- no NVMe")
        return fit(f"{bay} ----")
    d = st.drive
    if state == "DETECTED":
        return fit(f"{bay} {d.short_model:<10} in {st.countdown:>2}s")
    if state == "RUNNING":
        p = st.progress
        pct = "  ?%" if p.percent is None else f"{p.percent:3d}%"
        return fit(f"{bay} {p.phase:<4} {pct} {fmt_eta(p.eta_s):>6} {fmt_rate(p.rate_bps):>4}")
    if state == "DONE":
        return fit(f"{bay} DONE {st.tier_label:<5}{fmt_size(d.size_bytes):>5} out")
    if state == "ERROR":
        return fit(f"{bay} FAIL {st.message[:15]}")
    if state == "ABORTED":
        return fit(f"{bay} ABORTED {st.message[:12]}")
    return fit(f"{bay} {state}")


def wifi_frame(wifi, policy_label: str) -> Frame:
    """Idle screen on the access point: QR code (join the unit's Wi-Fi) and the key/address in text."""
    from . import qr

    m = qr.wifi_matrix(wifi.ssid, wifi.key)
    scale = qr.scale_for(m)
    px = len(m) * scale + 4
    cols = max(6, (128 - px) // 6)
    ssid1, ssid2 = wifi.ssid[:cols], wifi.ssid[cols:cols * 2]   # "brain-drain-7f3a" over two rows
    lines = [fit("BRAIN-DRAIN", cols), fit(policy_label, cols), fit("wifi " + ssid1, cols) if len(ssid1) + 5 <= cols else fit(ssid1, cols),
             fit(ssid2, cols), fit("key", cols), fit(wifi.key, cols), fit("then open", cols), fit(wifi.ip, cols)]
    return Frame(lines=lines, bitmap=m, bitmap_scale=scale, text_x=px)


def frame(policy_label: str, bays: dict, unit_line: str, message: str = "", wifi=None) -> Frame:
    """Pick the screen: the Wi-Fi QR code while the unit sits idle on its access point, else the bay
    table with the wireless address and key on the unit line."""
    idle = all(st.state in ("IDLE", "DONE", "ERROR", "ABORTED") for st in bays.values())
    if wifi is not None and wifi.mode == "ap" and idle and not message and all(st.state == "IDLE" for st in bays.values()):
        return wifi_frame(wifi, policy_label)
    # with wireless, the message row carries the unit key and the unit line the address
    if wifi is not None and wifi.mode in ("ap", "station"):
        message = message or f"key {wifi.key}"
        unit_line = fit(f"{wifi.ip} {wifi.ssid}"[:COLS])
    elif wifi is not None and wifi.mode == "joining":
        unit_line = fit(f"joining {wifi.ssid}"[:COLS])
    elif wifi is not None and wifi.mode == "off":
        unit_line = fit(f"wifi off {wifi.error}"[:COLS])
    return Frame(lines=render(policy_label, bays, unit_line, message))


def bay_cell(bay: int, st) -> str:
    """Ten-character bay summary for the two-column layout (eight slots + M.2 on one 128x64 panel)."""
    state = st.state
    if state == "IDLE":
        return fit(f"{bay} ----", 10)
    if state == "DETECTED":
        return fit(f"{bay} in {st.countdown:>2}s", 10)
    if state == "RUNNING":
        p = st.progress
        pct = " ?%" if p.percent is None else f"{p.percent:2d}%"
        return fit(f"{bay} {p.phase[:3]} {pct}", 10)
    if state == "DONE":
        return fit(f"{bay} DONE {st.tier_label[:1]}", 10)
    if state == "ERROR":
        return fit(f"{bay} FAIL", 10)
    if state == "ABORTED":
        return fit(f"{bay} ABORT", 10)
    return fit(f"{bay} {state[:7]}", 10)


def render(policy_label: str, bays: dict, unit_line: str, message: str = "") -> list[str]:
    lines = [fit(f"BRAIN-DRAIN {policy_label:>9}")]
    order = sorted(bays)
    if len(order) > 5:
        # two columns: bays 1-4 left, 5-8 right, the M.2 bay (if any) on its own row
        usb = [b for b in order if b <= 8]
        left, right = usb[:4], usb[4:8]
        for i in range(4):
            a = bay_cell(left[i], bays[left[i]]) if i < len(left) else fit("", 10)
            b = bay_cell(right[i], bays[right[i]]) if i < len(right) else fit("", 10)
            lines.append(fit(a + "|" + b))
        for b in order:
            if b > 8:
                lines.append(bay_line(b, bays[b]))
    else:
        for bay in order:
            lines.append(bay_line(bay, bays[bay]))
    while len(lines) < 6:
        lines.append(fit(""))
    lines = lines[:6]
    lines.append(fit(message))
    lines.append(fit(unit_line[:COLS]))
    return lines[:ROWS]
