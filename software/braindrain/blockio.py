"""Low-level block I/O helpers: O_DIRECT with aligned buffers, size queries."""

from __future__ import annotations

import errno
import fcntl
import mmap
import os
import stat
import struct

BLKGETSIZE64 = 0x80081272
BLKSSZGET = 0x1268
BLKPBSZGET = 0x127B


def is_block_device(path: str) -> bool:
    try:
        return stat.S_ISBLK(os.stat(path).st_mode)
    except FileNotFoundError:
        return False


def device_size(path: str) -> int:
    if is_block_device(path):
        fd = os.open(path, os.O_RDONLY)
        try:
            buf = fcntl.ioctl(fd, BLKGETSIZE64, b"\0" * 8)
            return struct.unpack("Q", buf)[0]
        finally:
            os.close(fd)
    return os.stat(path).st_size


def sector_sizes(path: str) -> tuple[int, int]:
    """(logical, physical) sector size. Files report 512/4096 for alignment purposes."""
    if is_block_device(path):
        fd = os.open(path, os.O_RDONLY)
        try:
            lo = struct.unpack("i", fcntl.ioctl(fd, BLKSSZGET, b"\0" * 4))[0]
            ph = struct.unpack("i", fcntl.ioctl(fd, BLKPBSZGET, b"\0" * 4))[0]
            return lo, ph
        finally:
            os.close(fd)
    return 512, 4096


class AlignedBuffer:
    """Page-aligned, reusable buffer suitable for O_DIRECT reads and writes."""

    def __init__(self, size: int):
        self.size = size
        self._mm = mmap.mmap(-1, size)
        self.view = memoryview(self._mm)

    def fill(self, pattern: bytes) -> None:
        if not pattern:
            raise ValueError("empty pattern")
        reps, rem = divmod(self.size, len(pattern))
        self._mm.seek(0)
        self._mm.write(pattern * reps + pattern[:rem])

    def close(self) -> None:
        self.view.release()
        self._mm.close()


def open_target(path: str, write: bool, direct: bool) -> tuple[int, bool]:
    """Open a block device or file. Returns (fd, direct_actually_enabled).

    O_DIRECT is attempted when requested; filesystems that refuse it (tmpfs)
    make us fall back to buffered I/O with explicit fdatasync.
    """
    flags = (os.O_RDWR if write else os.O_RDONLY) | getattr(os, "O_CLOEXEC", 0)
    if is_block_device(path):
        flags |= os.O_EXCL
    if direct:
        try:
            fd = os.open(path, flags | os.O_DIRECT)
            # tmpfs accepts the open but fails the first I/O; probe with a tiny read.
            try:
                os.pread(fd, 0, 0)
                return fd, True
            except OSError as e:
                if e.errno != errno.EINVAL:
                    raise
                os.close(fd)
        except OSError as e:
            if e.errno not in (errno.EINVAL, errno.ENOTSUP):
                raise
    fd = os.open(path, flags)
    return fd, False


def pwrite_all(fd: int, view: memoryview, offset: int) -> None:
    done = 0
    n = len(view)
    while done < n:
        w = os.pwrite(fd, view[done:], offset + done)
        if w <= 0:
            raise OSError(errno.EIO, "short write")
        done += w


def pread_all(fd: int, view: memoryview, offset: int) -> int:
    """Read exactly len(view) bytes unless EOF is reached. Returns bytes read."""
    done = 0
    n = len(view)
    while done < n:
        r = os.preadv(fd, [view[done:]], offset + done)
        if r == 0:
            break
        done += r
    return done
