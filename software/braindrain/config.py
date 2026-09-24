"""Runtime configuration.

Everything hardware-specific (GPIO numbers, bay to USB port-path mapping, bridge
USB IDs) lives here as data so the same engine runs on the appliance, on a
workstation with a USB dock, or fully simulated.
"""

from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass, field, fields
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("/etc/brain-drain/config.json")

# USB port paths, as they appear in sysfs (the leaf of the device path, e.g. "1-1.2"),
# for each bay. PLACEHOLDERS: fill in from the real board once it exists
# (`braindrain list` prints every candidate with its port path).
# Eight bay slots (C24): hub A's four downstream ports are bays 1-4, hub B's are bays 5-8. Only the
# slots that hold a card enumerate; an empty slot is simply never seen.
DEFAULT_BAY_PORTS: dict[int, str] = {1: "1-1.1", 2: "1-1.2", 3: "1-1.3", 4: "1-1.4", 5: "2-1.1", 6: "2-1.2", 7: "2-1.3", 8: "2-1.4"}

# USB bridge VID:PID allow-list. Only drives behind one of these bridges, on a bay
# port path, are ever candidates for wiping.
DEFAULT_ALLOWED_BRIDGES: frozenset[tuple[str, str]] = frozenset(
    {
        ("174c", "55aa"),  # ASMedia ASM1153E / ASM1051E / ASM1351 family (verify on bench)
        ("174c", "1153"),  # ASMedia ASM1153 (verify on bench)
    }
)

# BCM GPIO numbers, ARCHITECTURE.md §3.7.
DEFAULT_DIP_GPIOS: tuple[int, ...] = (16, 17, 20, 21, 22, 23, 24, 25)
DEFAULT_BAY_EN_GPIOS: dict[int, int] = {1: 5, 2: 6, 3: 12, 4: 13, 5: 7, 6: 8, 7: 9, 8: 10}
DEFAULT_STATUS_LED_GPIO = 26

MiB = 1024 * 1024
GiB = 1024 * MiB


@dataclass
class Config:
    bay_ports: dict[int, str] = field(default_factory=lambda: dict(DEFAULT_BAY_PORTS))
    allowed_bridges: frozenset[tuple[str, str]] = DEFAULT_ALLOWED_BRIDGES
    report_dir: Path = Path("/var/lib/brain-drain/reports")
    state_file: Path = Path("/var/lib/brain-drain/state.json")
    unit_id: str = field(default_factory=socket.gethostname)

    # Timing
    grace_seconds: float = 5.0  # countdown between detection and first write
    stagger_seconds: float = 4.0  # between bay power-ups at boot
    reinsert_guard_seconds: float = 30.0  # same serial reappearing in a DONE bay
    poll_interval: float = 0.5  # simulated watcher / firmware status polling
    display_hz: float = 1.0
    firmware_poll_seconds: float = 5.0

    # I/O
    block_size: int = 8 * MiB
    direct_io: bool = True  # O_DIRECT when the target supports it; falls back otherwise

    # Verification
    verify_sample_windows: int = 64
    verify_sample_window_bytes: int = 16 * MiB
    verify_edge_bytes: int = 1 * GiB  # clamped to size/8 for small targets
    canary_count: int = 8

    # GPIO (real HAL only)
    gpiochip: str = "/dev/gpiochip0"
    dip_gpios: tuple[int, ...] = DEFAULT_DIP_GPIOS
    bay_en_gpios: dict[int, int] = field(default_factory=lambda: dict(DEFAULT_BAY_EN_GPIOS))
    status_led_gpio: int = DEFAULT_STATUS_LED_GPIO
    oled_driver: str = "ssd1306"  # or "sh1106"
    i2c_port: int = 1
    oled_address: int = 0x3C

    # Bay 9: M.2 NVMe slot on the CM5 PCIe lane (ARCHITECTURE.md §3.3, decision C15; bays 1-8 are the slots, C24)
    m2_bay: int | None = 9
    m2_door_gpio: int = 4       # microswitch, closed = low
    m2_pedet_gpio: int = 19     # M.2 pin 69, pulled up; a SATA module grounds it
    m2_power_gpio: int = 27     # TPS22965 enable for 3V3_M2
    m2_settle_seconds: float = 1.0   # power-on to PCIe rescan
    m2_appear_seconds: float = 10.0  # rescan to block device, else power off and retry on next door cycle
    pci_rescan_path: Path = Path("/sys/bus/pci/rescan")

    # HAL selection: "real" (carrier board), "headless" (Pi + USB docks, no panel/OLED/bay power),
    # or simulation when sim_dir is set.
    hal: str = "real"
    headless_dip: str = "00000000"   # policy used by the headless HAL, which has no switches
    display_file: Path | None = None  # last OLED frame as text, for `braindrain status`

    # Wireless and the phone page (C22). The AP key is ephemeral (per boot) and lives only in memory.
    wifi_iface: str = "wlan0"
    wifi_file: Path = Path("/var/lib/brain-drain/wifi.json")   # saved station network, if any
    wifi_join_timeout: float = 45.0
    ap_ip: str = "10.42.0.1"
    web_enabled: bool = True
    web_port: int = 80

    # Simulation
    sim_dir: Path | None = None

    @property
    def bays(self) -> list[int]:
        bays = sorted(self.bay_ports)
        if self.m2_bay is not None:
            bays.append(self.m2_bay)
        return bays

    @property
    def usb_bays(self) -> list[int]:
        return sorted(self.bay_ports)

    @classmethod
    def for_simulation(cls, sim_dir: Path, **overrides) -> Config:
        sim_dir = Path(sim_dir)
        cfg = cls(
            report_dir=sim_dir / "reports",
            state_file=sim_dir / "state.json",
            sim_dir=sim_dir,
            unit_id=overrides.pop("unit_id", "sim-" + socket.gethostname()),
            stagger_seconds=0.0,
        )
        for k, v in overrides.items():
            if not hasattr(cfg, k):
                raise AttributeError(k)
            setattr(cfg, k, v)
        return cfg


    # ------------------------------------------------------------------ file I/O
    _PATH_FIELDS = ("report_dir", "state_file", "pci_rescan_path", "sim_dir", "display_file", "wifi_file")

    @classmethod
    def load(cls, path: Path | str | None = None) -> Config:
        """Config from a JSON file; keys are field names. Missing file -> defaults."""
        path = Path(path or DEFAULT_CONFIG_PATH)
        cfg = cls()
        if not path.exists():
            return cfg
        data = json.loads(path.read_text())
        cfg.apply(data)
        return cfg

    def apply(self, data: dict) -> Config:
        names = {f.name for f in fields(self)}
        for k, v in data.items():
            if k not in names:
                raise KeyError(f"unknown config key {k!r}")
            if k == "bay_ports":
                v = {int(b): str(p) for b, p in v.items()}
            elif k == "bay_en_gpios":
                v = {int(b): int(g) for b, g in v.items()}
            elif k == "allowed_bridges":
                v = frozenset((str(a).lower(), str(b).lower()) for a, b in v)
            elif k == "dip_gpios":
                v = tuple(int(x) for x in v)
            elif k in self._PATH_FIELDS and v is not None:
                v = Path(v)
            setattr(self, k, v)
        return self

    def to_dict(self) -> dict:
        out = {}
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, Path):
                v = str(v)
            elif isinstance(v, frozenset):
                v = sorted(list(x) for x in v)
            elif isinstance(v, tuple):
                v = list(v)
            elif isinstance(v, dict):
                v = {str(k): val for k, val in v.items()}
            out[f.name] = v
        return out

    def save(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        return path


def env_flag(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")
