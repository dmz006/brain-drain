"""Method interface shared by host overwrite, ATA/NVMe firmware, and simulated methods."""

from __future__ import annotations

import abc
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from ..policy import Tier


class Cancelled(Exception):
    """Raised inside a method when the drive was removed or the job was aborted."""


class MethodError(Exception):
    """The method ran but failed; the engine moves on to the next in the chain."""


ProgressFn = Callable[[str, float | None, int | None], None]
# (phase label, fraction 0..1 or None if unknown, bytes done or None)


@dataclass
class RunContext:
    cancel: threading.Event
    progress: ProgressFn
    config: object
    log: logging.Logger
    policy: object = None

    def check_cancel(self) -> None:
        if self.cancel.is_set():
            raise Cancelled()

    def sleep(self, seconds: float) -> None:
        """Sleep that wakes early on cancel."""
        if self.cancel.wait(seconds):
            raise Cancelled()


@dataclass
class MethodResult:
    method: str
    tier: Tier
    ok: bool
    detail: str = ""
    started: float = field(default_factory=time.time)
    finished: float | None = None
    bytes_written: int = 0
    # For host overwrite: the exact block the last pass wrote, so verification can
    # regenerate the expected content. None for firmware methods (canary verify).
    expect_block: bytes | None = None
    # Extra facts for the certificate (pattern names, drive-reported durations...)
    facts: dict = field(default_factory=dict)

    def finish(self, ok: bool, detail: str = "") -> "MethodResult":
        self.ok = ok
        self.detail = detail
        self.finished = time.time()
        return self


class Method(abc.ABC):
    name: str = "abstract"
    tier: Tier = Tier.NONE
    firmware: bool = False  # True: verify with canaries instead of read-back compare

    @abc.abstractmethod
    def supported(self, drive) -> tuple[bool, str]:
        """(True, '') if this method can run on this drive, else (False, why)."""

    @abc.abstractmethod
    def run(self, drive, ctx: RunContext) -> MethodResult:
        """Run to completion. Raise Cancelled on cancel, MethodError on failure."""

    def __repr__(self) -> str:
        return f"<{self.name}>"
