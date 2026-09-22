"""End-to-end: engine + simulated bays + certificates."""

import json
import time
from pathlib import Path

from braindrain.sim.bays import plug, unplug


def certs(cfg):
    return sorted(Path(cfg.report_dir).glob("*.json"))


def read(p):
    return json.loads(p.read_text())


def test_plug_wipes_hdd_and_writes_certificate(runner):
    cfg = runner.cfg
    img = plug(cfg.sim_dir, 2, 2 * 1024 * 1024, media="hdd", serial="HDD1", prefill=True)
    runner.wait_state(2, "DONE", 30)
    assert img.read_bytes() == bytes(2 * 1024 * 1024)
    cs = certs(cfg)
    assert len(cs) == 1
    c = read(cs[0])
    assert c["outcome"] == "sanitized" and c["tier_claimed"] == "clear"
    assert c["method_used"] == "overwrite-1pass" and c["verification"]["kind"] == "full"
    assert c["drive"]["serial"] == "HDD1" and c["bay"] == 2
    # display shows DONE and stays until unplug
    time.sleep(0.3)
    assert "DONE" in (cfg.sim_dir / "display.txt").read_text()
    unplug(cfg.sim_dir, 2)
    runner.wait_state(2, "IDLE", 5)


def test_unplug_during_wipe_aborts(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, 1, 16 * 1024 * 1024, media="hdd", serial="SLOW", throttle_bps=4 * 1024 * 1024)
    runner.wait_state(1, "RUNNING", 5)
    time.sleep(0.5)
    unplug(cfg.sim_dir, 1)
    runner.wait_state(1, "IDLE", 10)
    c = read(certs(cfg)[0])
    assert c["outcome"] == "aborted"
    assert "NOT sanitized" in c["notes"][0]


def test_unplug_during_grace_cancels_cleanly(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, 3, 1024 * 1024, serial="QUICK")
    runner.wait_state(3, "DETECTED", 5)
    unplug(cfg.sim_dir, 3)
    runner.wait_state(3, "IDLE", 5)
    time.sleep(0.5)
    assert certs(cfg) == []


def test_ssd_uses_simulated_firmware_and_canaries(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, 4, 2 * 1024 * 1024, media="ssd", serial="SSD1", prefill=True,
         firmware={"crypto": True, "block": True, "seconds": 0.5})
    runner.wait_state(4, "DONE", 30)
    c = read(certs(cfg)[0])
    assert c["outcome"] == "sanitized" and c["tier_claimed"] == "purge"
    assert c["method_used"] == "sim-sanitize-block"
    assert c["verification"]["kind"] == "canary" and c["verification"]["ok"]
    skipped = [a["method"] for a in c["attempts"] if not a["supported"]]
    assert "ata-sanitize-crypto" in skipped  # real firmware methods refuse a sim drive


def test_firmware_failure_falls_back_to_overwrite(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, 1, 1024 * 1024, media="ssd", serial="SSDFAIL",
         firmware={"block": True, "seconds": 0.3, "fail_at": 0.5})
    runner.wait_state(1, "DONE", 30)
    c = read(certs(cfg)[0])
    assert c["method_used"] == "overwrite-1pass" and c["tier_claimed"] == "clear"
    att = {a["method"]: a for a in c["attempts"]}
    assert att["sim-sanitize-block"]["ok"] is False
    assert any("over-provisioned" in n for n in c["notes"])


def test_maintenance_mode_never_wipes(runner):
    cfg = runner.cfg
    (cfg.sim_dir / "dip").write_text("00000001\n")
    img = plug(cfg.sim_dir, 2, 1024 * 1024, serial="MAINT", prefill=True)
    before = img.read_bytes()
    time.sleep(1.0)
    assert runner.engine.bays[2].state == "IDLE"
    assert img.read_bytes() == before
    assert certs(cfg) == []


def test_dry_run_writes_nothing(runner):
    cfg = runner.cfg
    (cfg.sim_dir / "dip").write_text("11100000\n")
    img = plug(cfg.sim_dir, 2, 1024 * 1024, serial="DRY", prefill=True)
    before = img.read_bytes()
    runner.wait_state(2, "DONE", 10)
    assert img.read_bytes() == before
    assert read(certs(cfg)[0])["outcome"] == "dry-run"


def test_reinsert_guard_keeps_done(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, 1, 1024 * 1024, serial="SAME")
    runner.wait_state(1, "DONE", 20)
    unplug(cfg.sim_dir, 1, keep_image=True)
    runner.wait_state(1, "IDLE", 5)
    plug(cfg.sim_dir, 1, 1024 * 1024, serial="SAME")
    time.sleep(1.0)
    # a genuine re-plug after IDLE is wiped again (single-use semantics), so we get 2 certs
    runner.wait_state(1, "DONE", 20)
    assert len(certs(cfg)) == 2


def test_interrupted_state_yields_certificate(sim_cfg):
    from braindrain import report
    from tests.conftest import EngineRunner

    report.save_state(sim_cfg.state_file, {3: {"drive": {"serial": "LOST"}, "policy": {}, "started": "2026-01-01T00:00:00Z"}})
    r = EngineRunner(sim_cfg).start()
    time.sleep(0.5)
    r.stop()
    cs = certs(sim_cfg)
    assert len(cs) == 1 and read(cs[0])["outcome"] == "interrupted"
    assert report.load_state(sim_cfg.state_file) == {}
