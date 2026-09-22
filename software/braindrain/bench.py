"""Bench test for a USB-SATA bridge + drive: does ATA passthrough work well enough
for brain-drain to rely on? Run on a workstation or a Pi with a dock attached.

    sudo braindrain bench /dev/sdX                      # non-destructive checks only
    sudo braindrain bench /dev/sdX --destructive        # + 1 GiB write test, SECURITY ERASE
    sudo braindrain bench /dev/sdX --destructive --sanitize   # + SANITIZE (hours on an HDD)

Every check is a Check(name, ok, detail); results print as a table and land in
bench-<serial>-<timestamp>.json. Command execution is injected so the sequencing
is unit-testable with fake hdparm/smartctl output.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import blockio
from .methods.ata import SECURITY_PASSWORD, parse_identify, parse_sanitize_status

BRIDGES = {
    ("174c", "55aa"): "ASMedia ASM1153E/ASM1051E/ASM1351 family",
    ("174c", "1153"): "ASMedia ASM1153",
    ("174c", "235c"): "ASMedia ASM235CM",
    ("152d", "0578"): "JMicron JMS578",
    ("152d", "0562"): "JMicron JMS567",
    ("152d", "0583"): "JMicron JMS583 (NVMe)",
    ("0bda", "9210"): "Realtek RTL9210 (NVMe)",
    ("2109", "0715"): "VIA VL715/VL716",
}


@dataclass
class Check:
    name: str
    ok: bool | None  # None = skipped
    detail: str = ""
    seconds: float | None = None


@dataclass
class BenchReport:
    device: str
    started: str
    bridge_id: str = "?"
    bridge_name: str = "?"
    usb_port: str = "?"
    drive: dict = field(default_factory=dict)
    checks: list[Check] = field(default_factory=list)

    def add(self, name, ok, detail="", seconds=None):
        self.checks.append(Check(name, ok, detail, seconds))
        return ok


RunFn = Callable[[list[str], float], subprocess.CompletedProcess]


def default_run(args: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def usb_identity(dev_path: str) -> tuple[str, str, str]:
    """(vid:pid, name, port) for the USB device above a block device, via sysfs."""
    name = os.path.basename(dev_path)
    try:
        p = Path(f"/sys/block/{name}").resolve()
    except OSError:
        return "?", "?", "?"
    for anc in p.parents:
        vid, pid = anc / "idVendor", anc / "idProduct"
        if vid.exists() and pid.exists():
            v, i = vid.read_text().strip().lower(), pid.read_text().strip().lower()
            return f"{v}:{i}", BRIDGES.get((v, i), "unknown bridge"), anc.name
    return "-", "not behind USB", "-"


class Bench:
    def __init__(self, dev_path: str, run: RunFn = default_run, log=print,
                 destructive: bool = False, sanitize: bool = False, poll: float = 5.0,
                 io_bytes: int = 1 << 30):
        self.dev = dev_path
        self.run = run
        self.log = log
        self.destructive = destructive
        self.sanitize = sanitize
        self.poll = poll
        self.io_bytes = io_bytes
        self.report = BenchReport(dev_path, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        self.ident: dict = {}

    # ------------------------------------------------------------ helpers
    def _hdparm(self, *args, timeout=60):
        return self.run(["hdparm", *args, self.dev], timeout)

    def _say(self, c: Check):
        mark = {True: "PASS", False: "FAIL", None: "skip"}[c.ok]
        t = f" ({c.seconds:.0f}s)" if c.seconds is not None else ""
        self.log(f"  [{mark}] {c.name}: {c.detail}{t}")

    def _check(self, name, ok, detail="", seconds=None):
        self.report.add(name, ok, detail, seconds)
        self._say(self.report.checks[-1])
        return ok

    # ------------------------------------------------------------ checks
    def bridge(self):
        vidpid, name, port = usb_identity(self.dev)
        r = self.report
        r.bridge_id, r.bridge_name, r.usb_port = vidpid, name, port
        self._check("usb bridge", vidpid not in ("?", "-"), f"{vidpid} {name} on port {port}")

    def identify(self):
        t0 = time.monotonic()
        cp = self._hdparm("-I")
        el = time.monotonic() - t0
        if cp.returncode != 0:
            return self._check("hdparm -I (ATA IDENTIFY passthrough)", False,
                               (cp.stderr or cp.stdout).strip()[:120], el)
        self.ident = parse_identify(cp.stdout)
        i = self.ident
        self.report.drive = {k: i.get(k) for k in ("model", "serial", "firmware", "rotation_rpm",
                                                   "sanitize", "sanitize_crypto", "sanitize_block",
                                                   "sanitize_overwrite", "security", "security_frozen",
                                                   "security_enhanced", "erase_minutes",
                                                   "enhanced_erase_minutes")}
        ok = i["model"] != "?" and i["serial"] != "?"
        media = "SSD" if i["rotation_rpm"] == 0 else f"{i['rotation_rpm']} rpm" if i["rotation_rpm"] else "?"
        self._check("hdparm -I (ATA IDENTIFY passthrough)", ok, f"{i['model']} {i['serial']} fw {i['firmware']} {media}", el)
        self._check("SANITIZE feature set reported", i["sanitize"],
                    f"crypto={i['sanitize_crypto']} block={i['sanitize_block']} overwrite={i['sanitize_overwrite']}")
        self._check("SECURITY feature set reported", i["security"],
                    f"frozen={i['security_frozen']} enhanced={i['security_enhanced']} "
                    f"erase={i['erase_minutes']}min enhanced={i['enhanced_erase_minutes']}min")
        if i["security_frozen"]:
            self.log("        drive is FROZEN: power-cycle the dock (not the host) and rerun before the erase test")

    def smart(self):
        t0 = time.monotonic()
        cp = self.run(["smartctl", "-d", "sat", "-j", "-H", "-i", self.dev], 60)
        el = time.monotonic() - t0
        try:
            j = json.loads(cp.stdout or "{}")
        except json.JSONDecodeError:
            j = {}
        ok = "smart_status" in j
        passed = j.get("smart_status", {}).get("passed")
        self._check("smartctl -d sat (SMART passthrough)", ok, f"health passed={passed}" if ok else "no JSON smart_status", el)

    def sanitize_status(self):
        t0 = time.monotonic()
        cp = self._hdparm("--sanitize-status")
        el = time.monotonic() - t0
        state, _frac = parse_sanitize_status(cp.stdout + cp.stderr)
        self._check("hdparm --sanitize-status (16-byte passthrough)", state != "unknown" and cp.returncode == 0,
                    f"state={state} rc={cp.returncode}", el)
        if state == "unknown":
            self.log("        raw output for parser fixture:\n" + "\n".join("        | " + l for l in (cp.stdout + cp.stderr).splitlines()[:8]))

    def read_speed(self):
        size = blockio.device_size(self.dev)
        n = min(self.io_bytes, size)
        fd, direct = blockio.open_target(self.dev, write=False, direct=True)
        buf = blockio.AlignedBuffer(8 << 20)
        try:
            t0 = time.monotonic()
            off = 0
            while off < n:
                m = min(buf.size, n - off)
                got = blockio.pread_all(fd, buf.view[:m], off)
                if got != m:
                    return self._check("sequential read", False, f"short read at {off}")
                off += m
            el = time.monotonic() - t0
        finally:
            buf.close()
            os.close(fd)
        rate = n / el / 1e6
        self._check("sequential read", rate > 20, f"{rate:.0f} MB/s over {n >> 20} MiB, O_DIRECT={direct}", el)

    def write_speed(self):
        size = blockio.device_size(self.dev)
        n = min(self.io_bytes, size)
        fd, _direct = blockio.open_target(self.dev, write=True, direct=True)
        buf = blockio.AlignedBuffer(8 << 20)
        buf.fill(b"\0")
        try:
            t0 = time.monotonic()
            off = 0
            while off < n:
                m = min(buf.size, n - off)
                blockio.pwrite_all(fd, buf.view[:m], off)
                off += m
            os.fdatasync(fd)
            el = time.monotonic() - t0
        finally:
            buf.close()
            os.close(fd)
        rate = n / el / 1e6
        self._check("sequential write (destructive)", rate > 20, f"{rate:.0f} MB/s over {n >> 20} MiB", el)

    def _device_still_there(self) -> tuple[bool, str]:
        cp = self._hdparm("-I")
        if cp.returncode != 0:
            return False, "device gone or not answering"
        i = parse_identify(cp.stdout)
        if i["serial"] != self.ident.get("serial"):
            return False, f"serial changed: {i['serial']}"
        return True, f"still enumerated, security enabled={i['security_enabled']} frozen={i['security_frozen']}"

    def security_erase(self):
        i = self.ident
        if not i.get("security"):
            return self._check("SECURITY ERASE UNIT", None, "not supported")
        if i.get("security_frozen"):
            return self._check("SECURITY ERASE UNIT", None, "frozen; power-cycle the dock and rerun")
        enhanced = bool(i.get("security_enhanced"))
        est = (i.get("enhanced_erase_minutes") if enhanced else i.get("erase_minutes")) or 0
        self.log(f"        starting {'enhanced ' if enhanced else ''}security erase, drive estimates {est} min")
        cp = self._hdparm("--user-master", "u", "--security-set-pass", SECURITY_PASSWORD)
        if cp.returncode != 0:
            return self._check("SECURITY ERASE UNIT", False, "set-pass failed: " + (cp.stderr or cp.stdout).strip()[:100])
        flag = "--security-erase-enhanced" if enhanced else "--security-erase"
        t0 = time.monotonic()
        cp = self._hdparm("--user-master", "u", flag, SECURITY_PASSWORD, timeout=max(600, est * 60 * 3))
        el = time.monotonic() - t0
        alive, why = self._device_still_there()
        ok = cp.returncode == 0 and alive
        self._check("SECURITY ERASE UNIT", ok, f"rc={cp.returncode}, {why}", el)
        if not ok and not alive:
            self.log("        the bridge dropped the device during the erase: this is the failure mode the design must handle")
        if el and est:
            self._check("erase time vs drive estimate", el <= est * 60 * 2, f"{el / 60:.1f} min vs {est} min estimate")

    def sanitize_run(self):
        i = self.ident
        if not i.get("sanitize"):
            return self._check("SANITIZE", None, "not supported")
        kind = "block-erase" if i.get("sanitize_block") else "crypto-scramble" if i.get("sanitize_crypto") else "overwrite"
        flag = ["--sanitize-" + kind] + (["0x00000000"] if kind == "overwrite" else [])
        cp = self._hdparm("--yes-i-know-what-i-am-doing", *flag, timeout=120)
        if cp.returncode != 0:
            return self._check(f"SANITIZE {kind}", False, "start failed: " + (cp.stderr or cp.stdout).strip()[:100])
        t0 = time.monotonic()
        last = None
        misses = 0
        while True:
            time.sleep(self.poll)
            cp = self._hdparm("--sanitize-status")
            state, frac = parse_sanitize_status(cp.stdout + cp.stderr)
            if state == "in_progress":
                misses = 0
                if frac is not None and frac != last:
                    self.log(f"        sanitize {frac * 100:.0f}%")
                    last = frac
                continue
            if state in ("success", "idle"):
                el = time.monotonic() - t0
                alive, why = self._device_still_there()
                return self._check(f"SANITIZE {kind}", alive, f"completed, {why}", el)
            if state == "failed":
                return self._check(f"SANITIZE {kind}", False, "drive reports failure", time.monotonic() - t0)
            misses += 1
            if misses > 12:
                return self._check(f"SANITIZE {kind}", False, "status unparseable / device unresponsive", time.monotonic() - t0)

    # ------------------------------------------------------------ driver
    def run_all(self) -> BenchReport:
        self.log(f"brain-drain bench: {self.dev}")
        self.bridge()
        self.identify()
        if not self.ident:
            return self.report
        self.smart()
        self.sanitize_status()
        self.read_speed()
        if self.destructive:
            self.write_speed()
            self.security_erase()
            if self.sanitize:
                self.sanitize_run()
        else:
            self._check("destructive tests", None, "not run (add --destructive)")
        return self.report

    def save(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        serial = "".join(c for c in str(self.report.drive.get("serial", "unknown")) if c.isalnum())
        p = out_dir / f"bench-{serial}-{self.report.started.replace(':', '-')}.json"
        p.write_text(json.dumps(asdict(self.report), indent=2))
        return p


def confirm_destructive(serial: str, model: str, prompt=input) -> bool:
    print(f"\nDESTRUCTIVE: this will erase {model} serial {serial}. Type the serial to continue: ", end="")
    return prompt("").strip() == serial
