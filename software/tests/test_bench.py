"""Bench sequencing against fake hdparm/smartctl."""

import subprocess

from braindrain.bench import Bench
from tests.test_parsers import HDPARM_I, HDPARM_I_SSD_FROZEN


class FakeRun:
    def __init__(self, ident=HDPARM_I, sanitize_status="State: SD0 Sanitize Idle", erase_rc=0,
                 drop_after_erase=False):
        self.ident, self.sanitize_status, self.erase_rc = ident, sanitize_status, erase_rc
        self.drop_after_erase = drop_after_erase
        self.calls = []
        self.erased = False

    def __call__(self, args, timeout):
        self.calls.append(args)
        tool = args[0]
        if tool == "hdparm":
            if "-I" in args:
                if self.erased and self.drop_after_erase:
                    return subprocess.CompletedProcess(args, 2, "", "HDIO_DRIVE_CMD failed: No such device")
                return subprocess.CompletedProcess(args, 0, self.ident, "")
            if "--sanitize-status" in args:
                return subprocess.CompletedProcess(args, 0, self.sanitize_status, "")
            if "--security-erase" in args or "--security-erase-enhanced" in args:
                self.erased = True
                return subprocess.CompletedProcess(args, self.erase_rc, "", "")
            return subprocess.CompletedProcess(args, 0, "", "")
        if tool == "smartctl":
            return subprocess.CompletedProcess(args, 0, '{"smart_status": {"passed": true}}', "")
        raise AssertionError(args)


def mk(tmp_path, **kw):
    img = tmp_path / "d.img"
    img.write_bytes(b"\xaa" * (4 << 20))
    run = FakeRun(**{k: v for k, v in kw.items() if k in ("ident", "sanitize_status", "erase_rc", "drop_after_erase")})
    b = Bench(str(img), run=run, log=lambda *a: None, io_bytes=2 << 20,
              destructive=kw.get("destructive", False), poll=0.01)
    return b, run, img


def results(b):
    return {c.name: c.ok for c in b.report.checks}


def test_non_destructive_sequence(tmp_path):
    b, _run, img = mk(tmp_path)
    b.run_all()
    r = results(b)
    assert r["hdparm -I (ATA IDENTIFY passthrough)"] is True
    assert r["SANITIZE feature set reported"] is True
    assert r["smartctl -d sat (SMART passthrough)"] is True
    assert r["hdparm --sanitize-status (16-byte passthrough)"] is True
    assert r["sequential read"] is True
    assert r["destructive tests"] is None
    assert img.read_bytes()[:16] == b"\xaa" * 16  # nothing written
    assert b.report.drive["serial"] == "WD-WCC7K1234567"


def test_destructive_runs_erase_and_checks_survival(tmp_path):
    b, run, img = mk(tmp_path, destructive=True)
    b.run_all()
    r = results(b)
    assert r["sequential write (destructive)"] is True
    assert r["SECURITY ERASE UNIT"] is True
    assert img.read_bytes()[:16] == bytes(16)
    assert any("--security-erase-enhanced" in c for c in run.calls)


def test_bridge_dropping_device_is_a_failure(tmp_path):
    b, _run, _img = mk(tmp_path, destructive=True, drop_after_erase=True)
    b.run_all()
    assert results(b)["SECURITY ERASE UNIT"] is False


def test_frozen_drive_skips_erase(tmp_path):
    b, _run, _img = mk(tmp_path, destructive=True, ident=HDPARM_I_SSD_FROZEN)
    b.run_all()
    r = results(b)
    assert r["SECURITY ERASE UNIT"] is None
    assert b.report.drive["rotation_rpm"] == 0


def test_unparseable_sanitize_status_fails(tmp_path):
    b, _run, _img = mk(tmp_path, sanitize_status="something the parser has never seen")
    b.run_all()
    assert results(b)["hdparm --sanitize-status (16-byte passthrough)"] is False


def test_report_saved(tmp_path):
    b, _run, _img = mk(tmp_path)
    b.run_all()
    p = b.save(tmp_path / "out")
    assert p.exists() and "WDWCC7K1234567" in p.name
