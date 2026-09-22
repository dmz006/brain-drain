"""SSD1306 / SH1106 over I2C via luma.oled. UNTESTED on hardware until the board exists."""

from __future__ import annotations

from .base import Display


class Oled(Display):
    def __init__(self, cfg):
        from luma.core.interface.serial import i2c  # type: ignore
        from luma.core.render import canvas  # type: ignore
        from luma.oled.device import sh1106, ssd1306  # type: ignore
        from PIL import ImageFont  # type: ignore

        serial = i2c(port=cfg.i2c_port, address=cfg.oled_address)
        dev_cls = sh1106 if cfg.oled_driver == "sh1106" else ssd1306
        self.device = dev_cls(serial, width=128, height=64)
        self.canvas = canvas
        self.font = ImageFont.load_default()

    def show(self, lines: list[str]) -> None:
        with self.canvas(self.device) as draw:
            for i, line in enumerate(lines[:8]):
                draw.text((0, i * 8), line, font=self.font, fill=255)

    def close(self) -> None:
        self.device.cleanup()
