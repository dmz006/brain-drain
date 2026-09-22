"""Headless HAL: a Raspberry Pi (or PC) with USB-SATA docks and no carrier board.

No DIP switch (policy comes from config.headless_dip), no OLED (frames go to the
log and to config.display_file), no bay power control (docks are always on), and
no M.2 slot (set m2_bay to null in the config).
"""

from __future__ import annotations

import logging

from ..policy import Dip
from .base import BayPower, Display, Panel

log = logging.getLogger(__name__)


class HeadlessPanel(Panel):
    def __init__(self, cfg):
        self.cfg = cfg

    def read_dip(self) -> Dip:
        return Dip.from_string(self.cfg.headless_dip)

    def set_status(self, color: str) -> None:
        log.info("status LED -> %s", color)

    def buzz(self, pattern: str) -> None:
        log.info("buzzer: %s", pattern)


class HeadlessBayPower(BayPower):
    def __init__(self, cfg):
        self.state = {b: True for b in cfg.bays}

    def set(self, bay: int, on: bool) -> None:
        self.state[bay] = on
        log.info("bay %d power %s (no control in headless mode)", bay, "ON" if on else "OFF")

    def is_on(self, bay: int) -> bool:
        return self.state.get(bay, True)


class LogDisplay(Display):
    def __init__(self):
        self.last = None

    def show(self, lines: list[str]) -> None:
        if lines != self.last:
            self.last = lines
            log.info("display:\n" + "\n".join("  |" + l + "|" for l in lines))
