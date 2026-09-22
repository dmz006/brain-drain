import logging
import threading
import time
from pathlib import Path

import pytest

from braindrain.config import Config
from braindrain.engine import Engine
from braindrain.hal.sim import SimBayPower, SimDisplay, SimPanel
from braindrain.sim.bays import SimWatcher

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def sim_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sim"
    d.mkdir()
    (d / "dip").write_text("00000000\n")
    return d


@pytest.fixture
def sim_cfg(sim_dir: Path) -> Config:
    return Config.for_simulation(
        sim_dir, grace_seconds=0.2, poll_interval=0.05, stagger_seconds=0.0,
        block_size=1 << 20, verify_sample_window_bytes=64 * 1024, verify_edge_bytes=256 * 1024,
        verify_sample_windows=4, reinsert_guard_seconds=5.0, display_hz=20.0,
    )


class EngineRunner:
    """Runs an Engine in a thread for end-to-end tests."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        panel = SimPanel(cfg)
        self.engine = Engine(cfg, SimWatcher(cfg), panel, SimBayPower(cfg), SimDisplay("none", cfg.sim_dir))
        self.thread = threading.Thread(target=self.engine.run_forever, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.engine.stop.set()
        self.thread.join(timeout=30)

    def wait_state(self, bay: int, states, timeout: float = 30.0) -> str:
        if isinstance(states, str):
            states = {states}
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            st = self.engine.bays[bay].state
            if st in states:
                return st
            time.sleep(0.02)
        raise AssertionError(f"bay {bay} never reached {states}; last {self.engine.bays[bay].state}")


@pytest.fixture
def runner(sim_cfg: Config):
    r = EngineRunner(sim_cfg).start()
    yield r
    r.stop()
