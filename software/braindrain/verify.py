"""Post-wipe verification: full read-back, sampled read-back, and canaries."""

from __future__ import annotations

import os
import random
import uuid
from dataclasses import dataclass, field

from . import blockio
from .methods.base import Cancelled, RunContext

CANARY_LEN = 4096


@dataclass
class VerifyResult:
    kind: str  # "full", "sampled", "canary", "none"
    ok: bool
    detail: str = ""
    bytes_checked: int = 0
    mismatches: list[int] = field(default_factory=list)  # offsets
    facts: dict = field(default_factory=dict)


def _open_read(drive, cfg):
    return blockio.open_target(drive.dev_path, write=False, direct=cfg.direct_io)


def expected_at(expect_block: bytes, off: int, n: int) -> bytes:
    """The bytes a drive overwritten with a repeated `expect_block` holds at [off, off+n)."""
    bs = len(expect_block)
    phase = off % bs
    if phase == 0 and n <= bs:
        return expect_block[:n]
    reps = (phase + n) // bs + 2
    return (expect_block * reps)[phase : phase + n]


def _check_region(fd, buf, off, n, expect_block, mismatches, limit=16) -> int:
    got = blockio.pread_all(fd, buf.view[:n], off)
    if got != n:
        mismatches.append(off)
        return got
    expected = expected_at(expect_block, off, n)
    if bytes(buf.view[:n]) != expected:
        # locate the first differing 4 KiB for the report
        data = bytes(buf.view[:n])
        for i in range(0, n, 4096):
            if data[i : i + 4096] != expected[i : i + 4096]:
                mismatches.append(off + i)
                break
        if len(mismatches) > limit:
            raise _TooMany()
    return got


class _TooMany(Exception):
    pass


def full_verify(drive, expect_block: bytes, ctx: RunContext) -> VerifyResult:
    cfg = ctx.config
    res = VerifyResult("full", ok=False)
    block_size = len(expect_block)
    logical, _ = blockio.sector_sizes(drive.dev_path)
    size = drive.size_bytes - (drive.size_bytes % logical)
    fd, _ = _open_read(drive, cfg)
    buf = blockio.AlignedBuffer(block_size)
    try:
        off = 0
        while off < size:
            ctx.check_cancel()
            n = min(block_size, size - off)
            try:
                _check_region(fd, buf, off, n, expect_block, res.mismatches)
            except _TooMany:
                res.detail = "too many mismatches"
                return res
            except OSError as e:
                if ctx.cancel.is_set():
                    raise Cancelled() from e
                res.mismatches.append(off)
                res.detail = f"read error at {off}: {e}"
                return res
            off += n
            res.bytes_checked += n
            ctx.progress("VRFY", off / size, off)
        res.ok = not res.mismatches
        res.detail = "all bytes match" if res.ok else f"{len(res.mismatches)} mismatching region(s)"
        return res
    finally:
        buf.close()
        os.close(fd)


def sample_windows(size: int, cfg, seed: int) -> list[tuple[int, int]]:
    """(offset, length) windows: both edges plus seeded random interior windows."""
    win = cfg.verify_sample_window_bytes
    edge = min(cfg.verify_edge_bytes, max(size // 8, win))
    edge -= edge % win or 0
    edge = max(edge, min(win, size))
    windows: list[tuple[int, int]] = []
    if size <= 2 * edge:
        return [(0, size)]
    windows.append((0, edge))
    windows.append((size - edge, edge))
    rng = random.Random(seed)
    interior = size - 2 * edge
    for _ in range(cfg.verify_sample_windows):
        if interior <= win:
            break
        off = edge + rng.randrange(0, interior - win)
        off -= off % 4096
        windows.append((off, win))
    return windows


def sampled_verify(drive, expect_block: bytes, ctx: RunContext) -> VerifyResult:
    cfg = ctx.config
    seed = int.from_bytes(os.urandom(4), "little")
    res = VerifyResult("sampled", ok=False, facts={"seed": seed})
    block_size = len(expect_block)
    logical, _ = blockio.sector_sizes(drive.dev_path)
    size = drive.size_bytes - (drive.size_bytes % logical)
    windows = sample_windows(size, cfg, seed)
    total = sum(n for _, n in windows)
    fd, _ = _open_read(drive, cfg)
    buf = blockio.AlignedBuffer(block_size)
    try:
        done = 0
        for off, n in windows:
            # windows may be larger than the buffer; walk them in block-size steps
            end = off + n
            while off < end:
                ctx.check_cancel()
                m = min(block_size, end - off)
                try:
                    _check_region(fd, buf, off, m, expect_block, res.mismatches)
                except _TooMany:
                    res.detail = "too many mismatches"
                    return res
                except OSError as e:
                    if ctx.cancel.is_set():
                        raise Cancelled() from e
                    res.mismatches.append(off)
                    res.detail = f"read error at {off}: {e}"
                    return res
                off += m
                done += m
                res.bytes_checked += m
                ctx.progress("VRFY", done / total, done)
        res.ok = not res.mismatches
        res.detail = (
            f"{len(windows)} windows, all match" if res.ok else f"{len(res.mismatches)} mismatch(es)"
        )
        return res
    finally:
        buf.close()
        os.close(fd)


@dataclass
class Canary:
    offset: int
    marker: bytes


def write_canaries(drive, cfg, log) -> list[Canary]:
    """Before a firmware wipe, plant known markers spread across the drive."""
    logical, _ = blockio.sector_sizes(drive.dev_path)
    size = drive.size_bytes - (drive.size_bytes % logical)
    n = max(1, min(cfg.canary_count, size // CANARY_LEN))
    fd, _ = blockio.open_target(drive.dev_path, write=True, direct=cfg.direct_io)
    buf = blockio.AlignedBuffer(CANARY_LEN)
    canaries: list[Canary] = []
    try:
        for i in range(n):
            off = (size * i) // n
            off -= off % CANARY_LEN
            off = min(off, size - CANARY_LEN)
            marker = f"BRAIN-DRAIN-CANARY {uuid.uuid4()} {off}".encode()
            buf.fill(marker + b"\0")
            blockio.pwrite_all(fd, buf.view, off)
            canaries.append(Canary(off, marker))
        os.fdatasync(fd)
    finally:
        buf.close()
        os.close(fd)
    log.info("planted %d canaries", len(canaries))
    return canaries


def check_canaries(drive, canaries: list[Canary], ctx: RunContext) -> VerifyResult:
    """After a firmware wipe, every marker must be gone."""
    cfg = ctx.config
    res = VerifyResult("canary", ok=False, facts={"count": len(canaries)})
    fd, _ = _open_read(drive, cfg)
    buf = blockio.AlignedBuffer(CANARY_LEN)
    try:
        for c in canaries:
            ctx.check_cancel()
            got = blockio.pread_all(fd, buf.view, c.offset)
            data = bytes(buf.view[:got])
            res.bytes_checked += got
            if c.marker in data:
                res.mismatches.append(c.offset)
        res.ok = not res.mismatches
        res.detail = (
            "all canaries gone" if res.ok else f"{len(res.mismatches)} canary(ies) survived"
        )
        return res
    finally:
        buf.close()
        os.close(fd)
