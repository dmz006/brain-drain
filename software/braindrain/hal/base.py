from __future__ import annotations

import abc

from ..policy import Dip


class Panel(abc.ABC):
    @abc.abstractmethod
    def read_dip(self) -> Dip: ...

    def set_status(self, color: str) -> None:  # "off" | "green" | "red" | "amber"
        pass

    def buzz(self, pattern: str) -> None:  # "done" | "error" | "tick"
        pass

    def close(self) -> None:
        pass


class BayPower(abc.ABC):
    @abc.abstractmethod
    def set(self, bay: int, on: bool) -> None: ...

    def close(self) -> None:
        pass


class Display(abc.ABC):
    @abc.abstractmethod
    def show(self, lines: list[str]) -> None: ...

    def close(self) -> None:
        pass
