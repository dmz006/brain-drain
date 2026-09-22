"""Real GPIO via libgpiod v2. UNTESTED on hardware until the board exists."""

from __future__ import annotations

import logging
import threading
import time

from ..policy import Dip
from .base import BayPower, Panel

log = logging.getLogger(__name__)


def _gpiod():
    import gpiod  # type: ignore
    from gpiod.line import Bias, Direction, Value  # type: ignore

    return gpiod, Bias, Direction, Value


class GpioPanel(Panel):
    def __init__(self, cfg):
        gpiod, Bias, Direction, Value = _gpiod()
        self._Value = Value
        self.cfg = cfg
        self.req = gpiod.request_lines(
            cfg.gpiochip,
            consumer="braindrain-panel",
            config={
                tuple(cfg.dip_gpios) + (cfg.m2_door_gpio, cfg.m2_pedet_gpio): gpiod.LineSettings(
                    direction=Direction.INPUT, bias=Bias.PULL_UP
                ),
                (cfg.buzzer_gpio, cfg.status_led_gpio): gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE
                ),
            },
        )

    def m2_door_closed(self) -> bool:
        return self.req.get_value(self.cfg.m2_door_gpio) == self._Value.INACTIVE

    def m2_pedet_pcie(self) -> bool:
        return self.req.get_value(self.cfg.m2_pedet_gpio) == self._Value.ACTIVE

    def read_dip(self) -> Dip:
        vals = self.req.get_values(list(self.cfg.dip_gpios))
        # switches pull the line low when ON
        return Dip(tuple(v == self._Value.INACTIVE for v in vals))  # type: ignore[arg-type]

    def set_status(self, color: str) -> None:
        self.req.set_value(self.cfg.status_led_gpio, self._Value.ACTIVE if color != "off" else self._Value.INACTIVE)

    def buzz(self, pattern: str) -> None:
        beeps = {"done": [0.15, 0.1, 0.15], "error": [0.5, 0.2, 0.5, 0.2, 0.5], "tick": [0.03]}.get(pattern, [0.1])

        def run():
            on = True
            for d in beeps:
                self.req.set_value(self.cfg.buzzer_gpio, self._Value.ACTIVE if on else self._Value.INACTIVE)
                time.sleep(d)
                on = not on
            self.req.set_value(self.cfg.buzzer_gpio, self._Value.INACTIVE)

        threading.Thread(target=run, daemon=True).start()

    def close(self) -> None:
        self.req.release()


class GpioBayPower(BayPower):
    def __init__(self, cfg):
        gpiod, _bias, Direction, Value = _gpiod()
        self._Value = Value
        self.cfg = cfg
        self.req = gpiod.request_lines(
            cfg.gpiochip,
            consumer="braindrain-bays",
            config={tuple(cfg.bay_en_gpios.values()) + (cfg.m2_power_gpio,): gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE)},
        )
        self.state = {b: False for b in cfg.bays}

    def _gpio(self, bay: int) -> int:
        return self.cfg.m2_power_gpio if bay == self.cfg.m2_bay else self.cfg.bay_en_gpios[bay]

    def set(self, bay: int, on: bool) -> None:
        self.req.set_value(self._gpio(bay), self._Value.ACTIVE if on else self._Value.INACTIVE)
        self.state[bay] = on
        log.info("bay %d power %s", bay, "ON" if on else "OFF")

    def is_on(self, bay: int) -> bool:
        return self.state.get(bay, False)

    def pci_rescan(self) -> None:
        try:
            self.cfg.pci_rescan_path.write_text("1")
        except OSError as e:
            log.error("pci rescan failed: %s", e)

    def pci_remove(self, sysfs_path: str) -> None:
        # sysfs_path is the block device; walk up to the PCI function and remove it
        import os
        p = os.path.realpath(sysfs_path)
        while p and not os.path.exists(os.path.join(p, "remove")):
            p = os.path.dirname(p)
        if p and p != "/":
            try:
                with open(os.path.join(p, "remove"), "w") as f:
                    f.write("1")
            except OSError as e:
                log.error("pci remove %s failed: %s", p, e)

    def close(self) -> None:
        self.req.release()
