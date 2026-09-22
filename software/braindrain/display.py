"""OLED frame rendering. Pure: bay states in, 8 lines of 21 characters out.

128x64 with a 6x8 font gives 21 columns x 8 rows:
    row 0   BRAIN-DRAIN     AUTO
    row 1-4 one line per bay
    row 5   blank / message
    row 6-7 unit line (ip / time / counts)
"""

from __future__ import annotations

from .progress import fmt_eta, fmt_rate, fmt_size

COLS = 21
ROWS = 8


def fit(s: str, n: int = COLS) -> str:
    return s[:n].ljust(n)


def bay_line(bay: int, st) -> str:
    """st is an engine.BayStatus-like object with .state, .drive, .progress, .message."""
    state = st.state
    if state == "IDLE":
        return fit(f"{bay} ----")
    d = st.drive
    if state == "DETECTED":
        return fit(f"{bay} {d.short_model:<10} in {st.countdown:>2}s")
    if state == "RUNNING":
        p = st.progress
        pct = "  ?%" if p.percent is None else f"{p.percent:3d}%"
        return fit(f"{bay} {p.phase:<4} {pct} {fmt_eta(p.eta_s):>6} {fmt_rate(p.rate_bps):>4}")
    if state == "DONE":
        return fit(f"{bay} DONE {st.tier_label:<5} {fmt_size(d.size_bytes):>5} unplug")
    if state == "ERROR":
        return fit(f"{bay} FAIL {st.message[:15]}")
    if state == "ABORTED":
        return fit(f"{bay} ABORTED {st.message[:12]}")
    return fit(f"{bay} {state}")


def render(policy_label: str, bays: dict, unit_line: str, message: str = "") -> list[str]:
    lines = [fit(f"BRAIN-DRAIN {policy_label:>9}")]
    for bay in sorted(bays):
        lines.append(bay_line(bay, bays[bay]))
    while len(lines) < 5:
        lines.append(fit(""))
    lines.append(fit(message))
    lines.append(fit(unit_line[:COLS]))
    lines.append(fit(unit_line[COLS:]))
    return lines[:ROWS]
