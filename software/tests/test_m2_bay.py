"""M.2 NVMe bay (bay 9): lid switch, PEDET, slot power, abort on lid open."""

M2 = 9   # the M.2 bay number (C24: slots are bays 1-8)
import json
import time
from pathlib import Path

from braindrain.sim.bays import plug


def certs(cfg):
    return sorted(Path(cfg.report_dir).glob("*.json"))


def read(p):
    return json.loads(p.read_text())


def door(cfg, state):
    (cfg.sim_dir / "door").write_text(state + "\n")


def test_slot_stays_dark_with_door_open(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, M2, 1024 * 1024, media="nvme", serial="NVME1", firmware={"crypto": True, "seconds": 0.3})
    time.sleep(0.6)
    assert runner.engine.bays[M2].state == "IDLE"
    assert not runner.engine.bay_power.is_on(M2)
    assert "lid open" in (cfg.sim_dir / "display.txt").read_text()


def test_door_closed_powers_slot_and_wipes_nvme(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, M2, 1024 * 1024, media="nvme", serial="NVME1", prefill=True,
         firmware={"crypto": True, "seconds": 0.3})
    door(cfg, "closed")
    runner.wait_state(M2, "DONE", 20)
    assert runner.engine.bay_power.is_on(M2)
    c = read(certs(cfg)[0])
    assert c["drive"]["media"] == "nvme" and c["outcome"] == "sanitized" and c["tier_claimed"] == "purge"
    assert c["method_used"] == "sim-sanitize-crypto"
    skipped = [a["method"] for a in c["attempts"] if not a["supported"]]
    assert "nvme-sanitize-crypto" in skipped  # real nvme-cli path refuses a sim drive
    door(cfg, "open")
    runner.wait_state(M2, "IDLE", 5)
    time.sleep(0.3)
    assert not runner.engine.bay_power.is_on(M2)


def test_door_open_mid_wipe_aborts_and_powers_off(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, M2, 16 * 1024 * 1024, media="nvme", serial="SLOWNV", throttle_bps=4 * 1024 * 1024)
    (cfg.sim_dir / "dip").write_text("01000000\n")  # CLEAR: host overwrite so it takes a while
    door(cfg, "closed")
    runner.wait_state(M2, "RUNNING", 10)
    time.sleep(0.4)
    door(cfg, "open")
    runner.wait_state(M2, "IDLE", 10)
    c = read(certs(cfg)[0])
    assert c["outcome"] == "aborted"
    assert not runner.engine.bay_power.is_on(M2)


def test_sata_module_is_refused(runner):
    cfg = runner.cfg
    (cfg.sim_dir / "pedet").write_text("sata\n")
    plug(cfg.sim_dir, M2, 1024 * 1024, media="nvme", serial="SATAM2")
    door(cfg, "closed")
    time.sleep(0.8)
    assert runner.engine.bays[M2].state == "IDLE"
    assert not runner.engine.bay_power.is_on(M2)
    assert "SATA M.2" in runner.engine.message
    assert certs(cfg) == []


def test_empty_slot_powers_off_after_timeout(runner):
    cfg = runner.cfg
    door(cfg, "closed")
    time.sleep(0.5)
    assert runner.engine.bay_power.is_on(M2)
    time.sleep(2.5)
    assert not runner.engine.bay_power.is_on(M2)
    assert "no NVMe" in runner.engine.message


def test_usb_bays_unaffected_by_door(runner):
    cfg = runner.cfg
    plug(cfg.sim_dir, 2, 1024 * 1024, serial="USB2")
    runner.wait_state(2, "DONE", 20)
    assert runner.engine.bay_power.is_on(2)
