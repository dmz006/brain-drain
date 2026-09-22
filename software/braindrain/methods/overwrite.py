"""Host-side overwrite passes.

Patterns: "zeros" (0x00), "ones" (0xFF), "random" (one block of os.urandom per
pass, repeated across the drive; its SHA-256 goes in the certificate). A
repeated random block is what NIST calls a fixed pattern; it exists for people
who want it, zeros are the default and equally valid for Clear.
"""

from __future__ import annotations

import hashlib
import os
import time

from .. import blockio
from ..policy import Tier
from .base import Cancelled, Method, MethodError, MethodResult, RunContext

PATTERNS = ("zeros", "ones", "random")


def make_block(pattern: str, size: int) -> bytes:
    if pattern == "zeros":
        return bytes(size)
    if pattern == "ones":
        return b"\xff" * size
    if pattern == "random":
        return os.urandom(size)
    raise ValueError(pattern)


class Overwrite(Method):
    tier = Tier.CLEAR

    def __init__(self, passes: list[str]):
        for p in passes:
            if p not in PATTERNS:
                raise ValueError(p)
        self.passes = list(passes)
        self.name = f"overwrite-{len(passes)}pass"

    def supported(self, drive):
        if drive.size_bytes <= 0:
            return False, "zero capacity"
        return True, ""

    def run(self, drive, ctx: RunContext) -> MethodResult:
        cfg = ctx.config
        res = MethodResult(self.name, self.tier, ok=False)
        res.facts["passes"] = list(self.passes)
        block_size = cfg.block_size
        logical, _ = blockio.sector_sizes(drive.dev_path)
        size = drive.size_bytes - (drive.size_bytes % logical)
        if size <= 0:
            raise MethodError("target smaller than one sector")

        fd, direct = blockio.open_target(drive.dev_path, write=True, direct=cfg.direct_io)
        res.facts["direct_io"] = direct
        buf = blockio.AlignedBuffer(block_size)
        throttle = drive.sim.get("throttle_bps") if drive.sim else None
        try:
            npasses = len(self.passes)
            for pi, pattern in enumerate(self.passes, start=1):
                block = make_block(pattern, block_size)
                buf.fill(block)
                if pattern == "random":
                    res.facts[f"pass{pi}_sha256"] = hashlib.sha256(block).hexdigest()
                label = f"OW{pi}/{npasses}" if npasses > 1 else "OVW"
                off = 0
                last_sync = time.monotonic()
                while off < size:
                    ctx.check_cancel()
                    n = min(block_size, size - off)
                    try:
                        blockio.pwrite_all(fd, buf.view[:n], off)
                    except OSError as e:
                        if ctx.cancel.is_set():
                            raise Cancelled() from e
                        raise MethodError(f"write failed at offset {off}: {e}") from e
                    off += n
                    res.bytes_written += n
                    ctx.progress(label, (pi - 1 + off / size) / npasses, off)
                    if throttle:
                        time.sleep(n / throttle)
                    if not direct and time.monotonic() - last_sync > 2.0:
                        os.fdatasync(fd)
                        last_sync = time.monotonic()
                os.fdatasync(fd)
            res.expect_block = block
            res.facts["final_pattern"] = self.passes[-1]
            return res.finish(True, f"{npasses} pass(es), {res.bytes_written} bytes")
        finally:
            buf.close()
            os.close(fd)
