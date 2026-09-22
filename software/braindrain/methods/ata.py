"""ATA firmware methods through hdparm (SCSI-ATA translation over the USB bridge).

SANITIZE is preferred over SECURITY ERASE UNIT: it is asynchronous with a
status query, so a USB bridge dropping the device mid-command is survivable.
Output parsing is based on hdparm 9.65 and MUST be re-checked on the bench;
`parse_identify` and `parse_sanitize_status` are unit-tested against fixtures.
"""

from __future__ import annotations

import re
import subprocess
import time

from ..policy import Media, Tier
from .base import Cancelled, Method, MethodError, MethodResult, RunContext

HDPARM = "hdparm"
SECURITY_PASSWORD = "braindrain"


def _run(args: list[str], timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def parse_identify(text: str) -> dict:
    """Pull the fields we need out of `hdparm -I` output."""
    out: dict = {}
    m = re.search(r"Model Number:\s*(.+)", text)
    out["model"] = m.group(1).strip() if m else "?"
    m = re.search(r"Serial Number:\s*(.+)", text)
    out["serial"] = m.group(1).strip() if m else "?"
    m = re.search(r"Firmware Revision:\s*(.+)", text)
    out["firmware"] = m.group(1).strip() if m else "?"
    m = re.search(r"Nominal Media Rotation Rate:\s*(.+)", text)
    rot = m.group(1).strip() if m else ""
    if "Solid State" in rot:
        out["rotation_rpm"] = 0
    elif rot.isdigit():
        out["rotation_rpm"] = int(rot)
    else:
        out["rotation_rpm"] = None
    out["sanitize"] = "SANITIZE feature set" in text
    out["sanitize_crypto"] = "CRYPTO_SCRAMBLE_EXT command" in text
    out["sanitize_block"] = "BLOCK_ERASE_EXT command" in text
    out["sanitize_overwrite"] = "OVERWRITE_EXT command" in text

    sec = text.split("Security:", 1)[1] if "Security:" in text else ""
    sec_lines = [l.strip() for l in sec.splitlines()[:12]]
    out["security"] = any(l == "supported" for l in sec_lines)
    out["security_enabled"] = any(l == "enabled" for l in sec_lines)
    out["security_frozen"] = any(l == "frozen" for l in sec_lines)
    out["security_enhanced"] = "supported: enhanced erase" in sec
    m = re.search(r"(\d+)min for SECURITY ERASE UNIT", sec)
    out["erase_minutes"] = int(m.group(1)) if m else None
    m = re.search(r"(\d+)min for ENHANCED SECURITY ERASE UNIT", sec)
    out["enhanced_erase_minutes"] = int(m.group(1)) if m else None
    return out


def fill_identity(drive) -> None:
    try:
        cp = _run([HDPARM, "-I", drive.dev_path])
    except (OSError, subprocess.TimeoutExpired):
        drive.model = drive.model if drive.model != "?" else "unknown"
        drive.caps.sanitize = False
        return
    if cp.returncode != 0:
        return
    info = parse_identify(cp.stdout)
    drive.model, drive.serial, drive.firmware = info["model"], info["serial"], info["firmware"]
    drive.rotation_rpm = info["rotation_rpm"]
    if drive.rotation_rpm == 0:
        drive.media = Media.SSD
    elif drive.rotation_rpm:
        drive.media = Media.HDD
    c = drive.caps
    for k in ("sanitize", "sanitize_crypto", "sanitize_block", "sanitize_overwrite", "security",
              "security_enabled", "security_frozen", "security_enhanced", "erase_minutes",
              "enhanced_erase_minutes"):
        setattr(c, k, info[k])


def parse_sanitize_status(text: str) -> tuple[str, float | None]:
    """('idle'|'in_progress'|'success'|'failed'|'unknown', fraction or None)."""
    low = text.lower()
    frac = None
    m = re.search(r"\((\d+(?:\.\d+)?)%\)", text)
    if m:
        frac = float(m.group(1)) / 100.0
    else:
        m = re.search(r"progress[^0-9a-fx]*0x([0-9a-f]+)", low)
        if m:
            frac = int(m.group(1), 16) / 65535.0
    if "in progress" in low:
        return "in_progress", frac
    if "failed" in low or "error" in low:
        return "failed", frac
    if "successful" in low or "completed" in low:
        return "success", frac
    if "idle" in low:
        return "idle", frac
    return "unknown", frac


class AtaSanitize(Method):
    tier = Tier.PURGE
    firmware = True

    def __init__(self, kind: str):
        assert kind in ("crypto", "block", "overwrite")
        self.kind = kind
        self.name = f"ata-sanitize-{kind}"

    def supported(self, drive):
        if drive.transport != "usb-sat":
            return False, "not an ATA device over SAT"
        c = drive.caps
        if not c.sanitize:
            return False, "SANITIZE feature set not reported"
        ok = {"crypto": c.sanitize_crypto, "block": c.sanitize_block, "overwrite": c.sanitize_overwrite}[self.kind]
        return (True, "") if ok else (False, f"{self.kind} sanitize not supported")

    def run(self, drive, ctx: RunContext) -> MethodResult:
        res = MethodResult(self.name, self.tier, ok=False)
        flag = {
            "crypto": ["--sanitize-crypto-scramble"],
            "block": ["--sanitize-block-erase"],
            "overwrite": ["--sanitize-overwrite", "0x00000000"],
        }[self.kind]
        cp = _run([HDPARM, "--yes-i-know-what-i-am-doing"] + flag + [drive.dev_path], timeout=120)
        if cp.returncode != 0:
            raise MethodError(f"hdparm {flag[0]} failed rc={cp.returncode}: {cp.stderr.strip() or cp.stdout.strip()}")
        ctx.progress("SANZ", None, None)
        start = time.monotonic()
        misses = 0
        while True:
            ctx.sleep(ctx.config.firmware_poll_seconds)
            try:
                cp = _run([HDPARM, "--sanitize-status", drive.dev_path], timeout=60)
            except (OSError, subprocess.TimeoutExpired):
                misses += 1
                if misses > 30:
                    raise MethodError("drive stopped answering sanitize status")
                continue
            state, frac = parse_sanitize_status(cp.stdout + cp.stderr)
            if state == "in_progress":
                misses = 0
                ctx.progress("SANZ", frac, None)
                continue
            if state in ("success", "idle"):
                res.facts["elapsed_s"] = round(time.monotonic() - start, 1)
                return res.finish(True, f"sanitize {self.kind} complete")
            if state == "failed":
                raise MethodError(f"drive reports sanitize failed: {cp.stdout.strip()}")
            misses += 1
            if misses > 30:
                raise MethodError(f"unparseable sanitize status: {cp.stdout.strip()[:200]}")


class AtaSecurityErase(Method):
    tier = Tier.PURGE
    firmware = True

    def __init__(self, enhanced: bool):
        self.enhanced = enhanced
        self.name = "ata-security-erase-enhanced" if enhanced else "ata-security-erase"

    def supported(self, drive):
        if drive.transport != "usb-sat":
            return False, "not an ATA device over SAT"
        c = drive.caps
        if not c.security:
            return False, "security feature set not supported"
        if c.security_frozen:
            return False, "security frozen (needs a bay power cycle)"
        if self.enhanced and not c.security_enhanced:
            return False, "enhanced erase not supported"
        return True, ""

    def run(self, drive, ctx: RunContext) -> MethodResult:
        res = MethodResult(self.name, self.tier, ok=False)
        minutes = drive.caps.enhanced_erase_minutes if self.enhanced else drive.caps.erase_minutes
        cp = _run([HDPARM, "--user-master", "u", "--security-set-pass", SECURITY_PASSWORD, drive.dev_path], timeout=60)
        if cp.returncode != 0:
            raise MethodError(f"security-set-pass failed: {cp.stderr.strip() or cp.stdout.strip()}")
        flag = "--security-erase-enhanced" if self.enhanced else "--security-erase"
        # hdparm blocks for the whole erase. Run it in the background and poll for cancel.
        proc = subprocess.Popen(
            [HDPARM, "--user-master", "u", flag, SECURITY_PASSWORD, drive.dev_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        start = time.monotonic()
        expected = (minutes or 0) * 60
        try:
            while proc.poll() is None:
                if ctx.cancel.is_set():
                    proc.kill()
                    raise Cancelled()
                el = time.monotonic() - start
                ctx.progress("SECE", min(el / expected, 0.99) if expected else None, None)
                time.sleep(2)
        finally:
            out = proc.stdout.read() if proc.stdout else ""
        res.facts["elapsed_s"] = round(time.monotonic() - start, 1)
        res.facts["drive_estimate_min"] = minutes
        if proc.returncode != 0:
            # The bridge may have reset mid-erase while the drive keeps going. Try to
            # confirm by re-reading identity; a drive still erasing answers BSY/errors.
            raise MethodError(f"hdparm {flag} rc={proc.returncode}: {out.strip()[:300]}")
        return res.finish(True, "security erase complete")
