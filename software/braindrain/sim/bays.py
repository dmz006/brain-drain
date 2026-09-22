from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from ..devices import Drive, identify_sim

SIZES = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}


def parse_size(s: str) -> int:
    s = s.strip().upper()
    if s[-1] in SIZES:
        return int(float(s[:-1]) * SIZES[s[-1]])
    return int(s)


def bay_dir(sim_dir: Path, bay: int) -> Path:
    return Path(sim_dir) / f"bay{bay}"


def plug(sim_dir: Path, bay: int, size: int, media: str = "hdd", model: str | None = None,
         serial: str | None = None, firmware: dict | None = None, throttle_bps: int | None = None,
         prefill: bool = False) -> Path:
    d = bay_dir(sim_dir, bay)
    d.mkdir(parents=True, exist_ok=True)
    img = d / "drive.img"
    meta = d / "drive.json"
    if meta.exists():
        raise FileExistsError(f"bay {bay} already has a drive plugged in")
    with open(img, "wb") as f:
        if prefill:
            chunk = os.urandom(1 << 20)
            left = size
            while left > 0:
                n = min(len(chunk), left)
                f.write(chunk[:n])
                left -= n
        else:
            f.truncate(size)
    sim: dict = {}
    if firmware:
        sim["firmware"] = firmware
    if throttle_bps:
        sim["throttle_bps"] = throttle_bps
    data = {
        "model": model or ("SIM-HDD" if media == "hdd" else "SIM-SSD"),
        "serial": serial or f"SIM{int(time.time()) % 100000:05d}B{bay}",
        "firmware": "SIM1",
        "media": media,
        "sim": sim,
    }
    tmp = d / "drive.json.tmp"
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, meta)  # atomic: watcher never sees a half-written drive.json
    return img


def unplug(sim_dir: Path, bay: int, keep_image: bool = False) -> None:
    d = bay_dir(sim_dir, bay)
    meta = d / "drive.json"
    if meta.exists():
        meta.unlink()
    if not keep_image:
        img = d / "drive.img"
        if img.exists():
            img.unlink()


@dataclass
class SimEvent:
    action: str  # "add" | "remove"
    bay: int
    drive: Drive | None = None


class SimWatcher:
    """Polls the bay directories and yields add/remove events like udev would."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.sim_dir = Path(cfg.sim_dir)
        self.present: dict[int, str] = {}  # bay -> serial

    def poll(self) -> list[SimEvent]:
        events: list[SimEvent] = []
        for bay in self.cfg.bays:
            d = bay_dir(self.sim_dir, bay)
            meta = d / "drive.json"
            img = d / "drive.img"
            here = meta.exists() and img.exists()
            if here and bay not in self.present:
                try:
                    data = json.loads(meta.read_text())
                except (OSError, json.JSONDecodeError):
                    continue
                drive = identify_sim(bay, img, data)
                self.present[bay] = drive.serial
                events.append(SimEvent("add", bay, drive))
            elif not here and bay in self.present:
                del self.present[bay]
                events.append(SimEvent("remove", bay))
        return events
