"""Per-bay progress with rate smoothing and ETA."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Progress:
    phase: str = ""
    fraction: float | None = None  # 0..1 within the whole job
    bytes_done: int | None = None
    rate_bps: float | None = None
    eta_s: float | None = None
    started: float = field(default_factory=time.monotonic)
    _last_t: float | None = None
    _last_b: int | None = None
    _last_f: float | None = None
    _ewma: float | None = None

    def update(self, phase: str, fraction: float | None, bytes_done: int | None) -> None:
        now = time.monotonic()
        if phase != self.phase:
            self.phase = phase
            self._last_t = self._last_b = self._last_f = None
            self._ewma = None
        self.fraction = fraction
        if bytes_done is not None:
            if self._last_t is not None and self._last_b is not None and now > self._last_t:
                inst = (bytes_done - self._last_b) / (now - self._last_t)
                if inst >= 0:
                    self._ewma = inst if self._ewma is None else 0.8 * self._ewma + 0.2 * inst
            self._last_t, self._last_b = now, bytes_done
            self.bytes_done = bytes_done
            self.rate_bps = self._ewma
        if fraction is not None:
            if self._last_f is None:
                self._phase_t0, self._phase_f0 = now, fraction
            self._last_f = fraction
            el = now - getattr(self, "_phase_t0", now)
            df = fraction - getattr(self, "_phase_f0", fraction)
            if el > 1.0 and df > 0.001:
                self.eta_s = (1.0 - fraction) * el / df
            elif fraction >= 1.0:
                self.eta_s = 0.0

    @property
    def percent(self) -> int | None:
        return None if self.fraction is None else int(min(max(self.fraction, 0.0), 1.0) * 100)


def fmt_eta(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    s = int(seconds)
    if s >= 36000:
        return f"{s // 3600}h"
    if s >= 3600:
        return f"{s // 3600}h{(s % 3600) // 60:02d}"
    if s >= 60:
        return f"{s // 60}m{s % 60:02d}"
    return f"{s}s"


def fmt_rate(bps: float | None) -> str:
    if bps is None:
        return "   -"
    mb = bps / 1e6
    if mb >= 1000:
        return f"{mb / 1000:.1f}G"
    if mb >= 100:
        return f"{mb:.0f}M"
    return f"{mb:.1f}M" if mb >= 10 else f"{mb:.2f}M"[:4]


def fmt_size(nbytes: int) -> str:
    tb = nbytes / 1e12
    if tb >= 1:
        return f"{tb:.1f}T"
    gb = nbytes / 1e9
    if gb >= 1:
        return f"{gb:.0f}G"
    return f"{nbytes / 1e6:.0f}M"
