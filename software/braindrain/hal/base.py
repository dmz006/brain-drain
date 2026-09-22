from __future__ import annotations

import abc

from ..policy import Dip


class Panel(abc.ABC):
    @abc.abstractmethod
    def read_dip(self) -> Dip: ...

    def m2_door_closed(self) -> bool:
        """Bay 5 access door: True when shut (switch pulls the line low)."""
        return False

    def m2_pedet_pcie(self) -> bool:
        """M.2 PEDET (pin 69): True = PCIe module or empty slot, False = SATA module grounding it."""
        return True

    def set_status(self, color: str) -> None:  # "off" | "green" | "red" | "amber"
        pass

    def buzz(self, pattern: str) -> None:  # "done" | "error" | "tick"
        pass

    def close(self) -> None:
        pass


class BayPower(abc.ABC):
    @abc.abstractmethod
    def set(self, bay: int, on: bool) -> None: ...

    def is_on(self, bay: int) -> bool:
        return True

    def pci_rescan(self) -> None:
        """Ask the kernel to enumerate the freshly powered M.2 slot."""

    def pci_remove(self, sysfs_path: str) -> None:
        """Detach a PCIe device before its power goes away."""

    def close(self) -> None:
        pass


class Display(abc.ABC):
    @abc.abstractmethod
    def show(self, lines: list[str]) -> None: ...

    def close(self) -> None:
        pass
