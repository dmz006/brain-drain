import logging
import os
import threading

import pytest

from braindrain.config import Config
from braindrain.devices import Drive
from braindrain.methods.base import Cancelled, RunContext
from braindrain.methods.overwrite import Overwrite
from braindrain.policy import Media
from braindrain.verify import (
    check_canaries,
    full_verify,
    sample_windows,
    sampled_verify,
    write_canaries,
)


def mk(tmp_path, size=3 * 1024 * 1024 + 4096, random_fill=True):
    img = tmp_path / "d.img"
    with open(img, "wb") as f:
        if random_fill:
            f.write(os.urandom(size))
        else:
            f.truncate(size)
    return Drive(bay=1, dev_path=str(img), size_bytes=size, media=Media.HDD, transport="sim")


def ctx(cfg, cancel=None):
    return RunContext(cancel=cancel or threading.Event(), progress=lambda *a: None, config=cfg,
                      log=logging.getLogger("t"))


@pytest.fixture
def cfg():
    return Config(block_size=1 << 20, verify_sample_window_bytes=64 * 1024, verify_edge_bytes=256 * 1024,
                  verify_sample_windows=4, canary_count=4)


def test_zero_pass_then_full_verify(tmp_path, cfg):
    d = mk(tmp_path)
    res = Overwrite(["zeros"]).run(d, ctx(cfg))
    assert res.ok and res.bytes_written == d.size_bytes
    with open(d.dev_path, "rb") as f:
        assert f.read() == bytes(d.size_bytes)
    v = full_verify(d, res.expect_block, ctx(cfg))
    assert v.ok and v.bytes_checked == d.size_bytes


def test_random_pass_verifies_against_repeated_block(tmp_path, cfg):
    d = mk(tmp_path)
    res = Overwrite(["random"]).run(d, ctx(cfg))
    assert "pass1_sha256" in res.facts
    assert full_verify(d, res.expect_block, ctx(cfg)).ok
    assert sampled_verify(d, res.expect_block, ctx(cfg)).ok


def test_three_pass_final_pattern_is_random(tmp_path, cfg):
    d = mk(tmp_path)
    res = Overwrite(["zeros", "ones", "random"]).run(d, ctx(cfg))
    assert res.facts["final_pattern"] == "random"
    assert res.bytes_written == 3 * d.size_bytes


def test_verify_detects_tampering(tmp_path, cfg):
    d = mk(tmp_path)
    res = Overwrite(["zeros"]).run(d, ctx(cfg))
    with open(d.dev_path, "r+b") as f:
        f.seek(2 * 1024 * 1024 + 512)
        f.write(b"\x01")
    v = full_verify(d, res.expect_block, ctx(cfg))
    assert not v.ok and v.mismatches == [2 * 1024 * 1024]


def test_cancel_stops_overwrite(tmp_path, cfg):
    d = mk(tmp_path, size=8 * 1024 * 1024)
    d.sim = {"throttle_bps": 2 * 1024 * 1024}  # ~4 s total
    ev = threading.Event()
    threading.Timer(0.3, ev.set).start()
    with pytest.raises(Cancelled):
        Overwrite(["zeros"]).run(d, ctx(cfg, ev))


def test_sample_windows_cover_edges_and_interior(cfg):
    w = sample_windows(64 * 1024 * 1024, cfg, seed=1)
    assert w[0][0] == 0
    assert w[1][0] + w[1][1] == 64 * 1024 * 1024
    assert len(w) == 2 + cfg.verify_sample_windows
    assert all(off % 4096 == 0 for off, _ in w)
    assert sample_windows(100 * 1024, cfg, seed=1) == [(0, 100 * 1024)]


def test_canaries_survive_until_wiped(tmp_path, cfg):
    d = mk(tmp_path)
    cs = write_canaries(d, cfg, logging.getLogger("t"))
    assert len(cs) == 4
    assert not check_canaries(d, cs, ctx(cfg)).ok  # nothing wiped yet -> canaries present
    Overwrite(["zeros"]).run(d, ctx(cfg))
    assert check_canaries(d, cs, ctx(cfg)).ok
