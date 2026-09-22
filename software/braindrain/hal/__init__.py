"""Hardware abstraction: panel (DIP, LED, buzzer), bay power, display.

`make_hal(cfg)` returns simulated implementations when cfg.sim_dir is set and
real GPIO/I2C ones otherwise.
"""

from __future__ import annotations

from .base import BayPower, Display, Panel


def make_hal(cfg, display_mode: str = "auto") -> tuple[Panel, BayPower, Display]:
    if cfg.sim_dir is not None:
        from .sim import SimBayPower, SimDisplay, SimPanel

        mode = "term" if display_mode == "auto" else display_mode
        return SimPanel(cfg), SimBayPower(cfg), SimDisplay(mode, cfg.sim_dir)
    if cfg.hal == "headless":
        from .headless import HeadlessBayPower, HeadlessPanel, LogDisplay

        return HeadlessPanel(cfg), HeadlessBayPower(cfg), LogDisplay()
    from .gpio import GpioBayPower, GpioPanel
    from .oled import Oled

    return GpioPanel(cfg), GpioBayPower(cfg), Oled(cfg)
