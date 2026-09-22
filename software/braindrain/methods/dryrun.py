"""Dry run: goes through the motions, writes nothing."""

from __future__ import annotations

from ..policy import Tier
from .base import Method, MethodResult, RunContext


class DryRun(Method):
    name = "dry-run"
    tier = Tier.NONE

    def supported(self, drive):
        return True, ""

    def run(self, drive, ctx: RunContext) -> MethodResult:
        res = MethodResult(self.name, self.tier, ok=False)
        steps = 20
        for i in range(steps):
            ctx.check_cancel()
            ctx.progress("dry-run", (i + 1) / steps, None)
            ctx.sleep(0.05)
        return res.finish(True, "dry run, no writes issued")
