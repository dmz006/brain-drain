"""NVMe native methods through nvme-cli. Only reachable on native NVMe (D10 / PC)."""

from __future__ import annotations

import json
import subprocess
import time

from ..policy import Tier
from .base import Method, MethodError, MethodResult, RunContext

NVME = "nvme"
SANACT = {"block": 2, "overwrite": 3, "crypto": 4}


def _run(args, timeout=120):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def controller_path(dev_path: str) -> str:
    # /dev/nvme0n1 -> /dev/nvme0
    import re

    return re.sub(r"n\d+$", "", dev_path)


def fill_identity(drive) -> None:
    try:
        cp = _run([NVME, "id-ctrl", "-o", "json", controller_path(drive.dev_path)])
        info = json.loads(cp.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return
    drive.model = str(info.get("mn", "?")).strip()
    drive.serial = str(info.get("sn", "?")).strip()
    drive.firmware = str(info.get("fr", "?")).strip()
    sanicap = int(info.get("sanicap", 0))
    c = drive.caps
    c.nvme_sanicap = sanicap
    c.sanitize_crypto = bool(sanicap & 0x1)
    c.sanitize_block = bool(sanicap & 0x2)
    c.sanitize_overwrite = bool(sanicap & 0x4)
    c.sanitize = sanicap != 0
    drive.rotation_rpm = 0


def parse_sanitize_log(text: str) -> tuple[str, float | None]:
    try:
        info = json.loads(text)
    except json.JSONDecodeError:
        return "unknown", None
    sstat = int(info.get("sstat", 0))
    sprog = int(info.get("sprog", 0))
    status = sstat & 0x7
    frac = sprog / 65535.0
    return {0: "never", 1: "success", 2: "in_progress", 3: "failed"}.get(status, "unknown"), frac


class NvmeSanitize(Method):
    tier = Tier.PURGE
    firmware = True

    def __init__(self, kind: str):
        assert kind in SANACT
        self.kind = kind
        self.name = f"nvme-sanitize-{kind}"

    def supported(self, drive):
        if drive.transport != "nvme":
            return False, "not native NVMe"
        ok = {"crypto": drive.caps.sanitize_crypto, "block": drive.caps.sanitize_block,
              "overwrite": drive.caps.sanitize_overwrite}[self.kind]
        return (True, "") if ok else (False, f"SANICAP lacks {self.kind}")

    def run(self, drive, ctx: RunContext) -> MethodResult:
        res = MethodResult(self.name, self.tier, ok=False)
        ctrl = controller_path(drive.dev_path)
        cp = _run([NVME, "sanitize", ctrl, "--sanact", str(SANACT[self.kind])])
        if cp.returncode != 0:
            raise MethodError(f"nvme sanitize failed: {cp.stderr.strip() or cp.stdout.strip()}")
        start = time.monotonic()
        while True:
            ctx.sleep(ctx.config.firmware_poll_seconds)
            cp = _run([NVME, "sanitize-log", "-o", "json", ctrl])
            state, frac = parse_sanitize_log(cp.stdout)
            if state == "in_progress":
                ctx.progress("SANZ", frac, None)
            elif state == "success":
                res.facts["elapsed_s"] = round(time.monotonic() - start, 1)
                return res.finish(True, f"nvme sanitize {self.kind} complete")
            elif state == "failed":
                raise MethodError("controller reports sanitize failed")
            elif time.monotonic() - start > 60:
                raise MethodError(f"unexpected sanitize log state {state}")


class NvmeFormat(Method):
    tier = Tier.CLEAR  # SES=1 (user data erase) is Clear-grade; SES=2 (crypto) is Purge
    firmware = True

    def __init__(self, ses: int):
        self.ses = ses
        self.name = f"nvme-format-ses{ses}"
        self.tier = Tier.PURGE if ses == 2 else Tier.CLEAR

    def supported(self, drive):
        if drive.transport != "nvme":
            return False, "not native NVMe"
        return True, ""

    def run(self, drive, ctx: RunContext) -> MethodResult:
        res = MethodResult(self.name, self.tier, ok=False)
        ctx.progress("FMT", None, None)
        cp = _run([NVME, "format", drive.dev_path, "--ses", str(self.ses), "--force"], timeout=3600)
        if cp.returncode != 0:
            raise MethodError(f"nvme format failed: {cp.stderr.strip() or cp.stdout.strip()}")
        return res.finish(True, f"nvme format ses={self.ses} complete")
