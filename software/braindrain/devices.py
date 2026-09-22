"""Drive model, identity, and the safety fence.

The fence (ARCHITECTURE.md §4.3) is the only thing between this program and a
workstation's disks. `classify()` is pure and unit-tested; `collect_real()` is
the thin pyudev layer that feeds it.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import blockio
from .policy import Media

log = logging.getLogger(__name__)


@dataclass
class DriveCaps:
    sanitize: bool = False
    sanitize_crypto: bool = False
    sanitize_block: bool = False
    sanitize_overwrite: bool = False
    security: bool = False
    security_enabled: bool = False
    security_frozen: bool = False
    security_enhanced: bool = False
    erase_minutes: int | None = None
    enhanced_erase_minutes: int | None = None
    nvme_sanicap: int = 0


@dataclass
class Drive:
    bay: int
    dev_path: str
    model: str = "?"
    serial: str = "?"
    firmware: str = "?"
    size_bytes: int = 0
    logical_sector: int = 512
    physical_sector: int = 4096
    media: Media = Media.UNKNOWN
    transport: str = "unknown"  # "usb-sat", "nvme", "sim"
    rotation_rpm: int | None = None
    caps: DriveCaps = field(default_factory=DriveCaps)
    sysfs_path: str = ""
    usb_port: str = ""
    bridge_id: str = ""
    sim: dict = field(default_factory=dict)  # simulation-only knobs

    @property
    def is_sim(self) -> bool:
        return self.transport == "sim"

    @property
    def short_model(self) -> str:
        return self.model.replace(" ", "")[:10]

    def summary(self) -> dict:
        return {
            "bay": self.bay,
            "device": self.dev_path,
            "model": self.model,
            "serial": self.serial,
            "firmware": self.firmware,
            "size_bytes": self.size_bytes,
            "logical_sector": self.logical_sector,
            "physical_sector": self.physical_sector,
            "media": self.media.value,
            "transport": self.transport,
            "rotation_rpm": self.rotation_rpm,
            "usb_port": self.usb_port,
            "bridge_id": self.bridge_id,
            "caps": self.caps.__dict__,
        }


# --------------------------------------------------------------------------- fence


@dataclass
class DevInfo:
    """What the fence needs to know about a block device, independent of pyudev."""

    dev_path: str
    sysfs_path: str
    devtype: str  # "disk" or "partition"
    removable: bool
    size_bytes: int
    usb_port: str | None  # leaf port path of the nearest USB device parent, e.g. "1-1.2"
    bridge_vid: str | None
    bridge_pid: str | None
    is_system: bool  # holds root/boot/swap or any mounted filesystem


def classify(info: DevInfo, cfg) -> tuple[int | None, str]:
    """Return (bay, reason). bay is None when the device must not be touched."""
    if info.devtype != "disk":
        return None, "not a whole disk"
    if info.is_system:
        return None, "holds a mounted filesystem, root, boot or swap"
    if info.size_bytes <= 0:
        return None, "zero capacity (no medium)"
    if info.usb_port is None:
        name = os.path.basename(info.dev_path)
        if name.startswith("nvme") and getattr(cfg, "m2_bay", None) is not None:
            return cfg.m2_bay, "ok (native NVMe, M.2 bay)"
        return None, "not behind a USB port"
    if (info.bridge_vid, info.bridge_pid) not in cfg.allowed_bridges:
        return None, f"bridge {info.bridge_vid}:{info.bridge_pid} not on allow-list"
    for bay, port in cfg.bay_ports.items():
        if info.usb_port == port:
            return bay, "ok"
    return None, f"USB port {info.usb_port} is not a bay"


def system_devices() -> set[str]:
    """Kernel names (sda, nvme0n1, mmcblk0...) of disks that hold anything mounted or swap."""
    names: set[str] = set()
    try:
        out = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,PKNAME,MOUNTPOINTS,TYPE"],
            capture_output=True, text=True, check=True,
        ).stdout
        tree = json.loads(out)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        log.warning("lsblk failed (%s); treating every device as system", e)
        return {"*"}

    def walk(node, top):
        mps = node.get("mountpoints") or node.get("mountpoint") or []
        if isinstance(mps, str):
            mps = [mps]
        if any(mps):
            names.add(top)
        for ch in node.get("children", []) or []:
            walk(ch, top)

    for node in tree.get("blockdevices", []):
        walk(node, node["name"])
    try:
        with open("/proc/swaps") as f:
            for line in f.readlines()[1:]:
                dev = line.split()[0]
                names.add(re.sub(r"p?\d+$", "", os.path.basename(dev)))
    except OSError:
        pass
    return names


def collect_real(cfg) -> list[tuple[DevInfo, int | None, str]]:
    """Enumerate block disks via pyudev and classify each. Needs pyudev and Linux."""
    import pyudev  # imported lazily so simulation needs no pyudev

    ctx = pyudev.Context()
    sysnames = system_devices()
    out = []
    for dev in ctx.list_devices(subsystem="block"):
        if dev.get("DEVTYPE") != "disk":
            continue
        name = dev.sys_name
        usb = dev.find_parent("usb", "usb_device")
        port = usb.sys_name if usb is not None else None
        vid = usb.get("ID_VENDOR_ID") if usb is not None else None
        pid = usb.get("ID_MODEL_ID") if usb is not None else None
        if usb is not None and (vid is None or pid is None):
            try:
                vid = usb.attributes.asstring("idVendor")
                pid = usb.attributes.asstring("idProduct")
            except (KeyError, UnicodeDecodeError):
                pass
        try:
            size = int(dev.attributes.asstring("size")) * 512
        except (KeyError, ValueError):
            size = 0
        info = DevInfo(
            dev_path=dev.device_node or f"/dev/{name}",
            sysfs_path=dev.sys_path,
            devtype="disk",
            removable=dev.attributes.asstring("removable") == "1" if "removable" in dev.attributes.available_attributes else False,
            size_bytes=size,
            usb_port=port,
            bridge_vid=vid.lower() if vid else None,
            bridge_pid=pid.lower() if pid else None,
            is_system=("*" in sysnames) or (name in sysnames),
        )
        bay, reason = classify(info, cfg)
        out.append((info, bay, reason))
    return out


# ------------------------------------------------------------------------ identity


def identify_real(bay: int, info: DevInfo) -> Drive:
    """Fill a Drive from hdparm -I / sysfs / nvme id-ctrl. Never writes."""
    from .methods import ata, nvme

    d = Drive(bay=bay, dev_path=info.dev_path, sysfs_path=info.sysfs_path, usb_port=info.usb_port or "",
              bridge_id=f"{info.bridge_vid}:{info.bridge_pid}")
    d.size_bytes = blockio.device_size(info.dev_path)
    d.logical_sector, d.physical_sector = blockio.sector_sizes(info.dev_path)
    name = os.path.basename(info.dev_path)
    if name.startswith("nvme"):
        d.transport = "nvme"
        d.media = Media.NVME
        nvme.fill_identity(d)
        return d
    d.transport = "usb-sat"
    try:
        rot = Path(info.sysfs_path, "queue", "rotational").read_text().strip()
        d.media = Media.HDD if rot == "1" else Media.SSD
    except OSError:
        pass
    ata.fill_identity(d)  # refines media from the reported rotation rate when available
    return d


def identify_sim(bay: int, img: Path, meta: dict) -> Drive:
    d = Drive(bay=bay, dev_path=str(img), transport="sim")
    d.model = meta.get("model", "SIMDRIVE")
    d.serial = meta.get("serial", "SIM0000")
    d.firmware = meta.get("firmware", "0.1")
    d.size_bytes = blockio.device_size(str(img))
    d.logical_sector, d.physical_sector = 512, 4096
    d.media = Media(meta.get("media", "hdd"))
    d.rotation_rpm = 7200 if d.media is Media.HDD else 0
    d.sim = dict(meta.get("sim", {}))
    d.usb_port = f"sim-bay{bay}"
    d.bridge_id = "sim"
    fw = d.sim.get("firmware", {})
    d.caps.sanitize = bool(fw)
    d.caps.sanitize_crypto = bool(fw.get("crypto"))
    d.caps.sanitize_block = bool(fw.get("block"))
    d.caps.sanitize_overwrite = bool(fw.get("overwrite"))
    return d
