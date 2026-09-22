"""Simulated panel, bay power and display for workstation development.

DIP: the file <sim_dir>/dip holds 8 characters of 0/1 (DIP1 first). Edit it
any time; it is re-read whenever the engine needs it. Missing file = all OFF.
Bay 5: <sim_dir>/door holds "closed" or "open" (missing = open), <sim_dir>/pedet
holds "pcie" or "sata" (missing = pcie).
Display: "term" redraws the 8 OLED lines in place, "log" prints on change,
"none" is silent (tests). The latest frame is always in <sim_dir>/display.txt.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from ..policy import Dip
from .base import BayPower, Display, Panel

log = logging.getLogger(__name__)


class SimPanel(Panel):
    def __init__(self, cfg):
        self.path = Path(cfg.sim_dir) / "dip"
        self.status = "off"

    def read_dip(self) -> Dip:
        try:
            return Dip.from_string(self.path.read_text())
        except (OSError, ValueError):
            return Dip.from_string("00000000")

    def set_status(self, color: str) -> None:
        if color != self.status:
            log.info("status LED -> %s", color)
            self.status = color

    def m2_door_closed(self) -> bool:
        try:
            return (self.path.parent / "door").read_text().strip().lower() == "closed"
        except OSError:
            return False

    def m2_pedet_pcie(self) -> bool:
        try:
            return (self.path.parent / "pedet").read_text().strip().lower() != "sata"
        except OSError:
            return True



class SimBayPower(BayPower):
    def __init__(self, cfg):
        self.state = {b: False for b in cfg.bays}

    def set(self, bay: int, on: bool) -> None:
        if self.state.get(bay) != on:
            log.info("bay %d power %s", bay, "ON" if on else "OFF")
        self.state[bay] = on

    def is_on(self, bay: int) -> bool:
        return self.state.get(bay, False)

    def pci_rescan(self) -> None:
        log.info("pci rescan (simulated)")

    def pci_remove(self, sysfs_path: str) -> None:
        log.info("pci remove %s (simulated)", sysfs_path)


class SimDisplay(Display):
    def __init__(self, mode: str = "term", sim_dir: Path | None = None):
        self.mode = mode
        self.last: list[str] | None = None
        self.file = Path(sim_dir) / "display.txt" if sim_dir else None
        self._first = True

    def show(self, lines: list[str]) -> None:
        if lines == self.last:
            return
        self.last = lines
        if self.file:
            try:
                self.file.write_text("\n".join(lines) + "\n")
            except OSError:
                pass
        if self.mode == "none":
            return
        box = "+" + "-" * 21 + "+"
        body = "\n".join(f"|{l}|" for l in lines)
        if self.mode == "term" and sys.stdout.isatty():
            if not self._first:
                sys.stdout.write("\x1b[10A")  # move up 10 lines (box + 8 + box)
            self._first = False
            sys.stdout.write(f"{box}\n{body}\n{box}\n")
        else:
            sys.stdout.write(f"{box}\n{body}\n{box}\n")
        sys.stdout.flush()
