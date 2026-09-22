"""Simulated firmware sanitize, so the engine's firmware path (canaries, status
polling, cancellation mid-command) can be exercised without a drive.

A simulated drive advertises it via drive.json:
    {"sim": {"firmware": {"crypto": true, "block": true, "seconds": 3}}}
"""

from __future__ import annotations

import os
import time

from .. import blockio
from ..policy import Tier
from .base import Method, MethodResult, RunContext


class SimSanitize(Method):
    tier = Tier.PURGE
    firmware = True

    def __init__(self, kind: str):
        self.kind = kind
        self.name = f"sim-sanitize-{kind}"

    def supported(self, drive):
        if not drive.is_sim:
            return False, "not a simulated drive"
        fw = drive.sim.get("firmware") or {}
        if not fw.get(self.kind):
            return False, f"simulated firmware lacks {self.kind}"
        return True, ""

    def run(self, drive, ctx: RunContext) -> MethodResult:
        res = MethodResult(self.name, self.tier, ok=False)
        fw = drive.sim["firmware"]
        seconds = float(fw.get("seconds", 2.0))
        fail_at = fw.get("fail_at")  # fraction at which the sim reports failure
        fd, _ = blockio.open_target(drive.dev_path, write=True, direct=ctx.config.direct_io)
        buf = blockio.AlignedBuffer(min(ctx.config.block_size, 1 << 20))
        buf.fill(b"\0" if self.kind != "crypto" else os.urandom(4096))
        try:
            size = drive.size_bytes
            steps = 20
            off = 0
            for i in range(steps):
                ctx.sleep(seconds / steps)
                frac = (i + 1) / steps
                if fail_at is not None and frac >= fail_at:
                    from .base import MethodError

                    raise MethodError("simulated firmware failure")
                target = (size * (i + 1)) // steps
                while off < target:
                    n = min(buf.size, target - off)
                    blockio.pwrite_all(fd, buf.view[:n], off)
                    off += n
                ctx.progress("SANZ", frac, None)
            os.fdatasync(fd)
            res.facts["simulated"] = True
            return res.finish(True, f"simulated {self.kind} sanitize in {seconds}s")
        finally:
            buf.close()
            os.close(fd)
