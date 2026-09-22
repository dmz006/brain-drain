"""Runtime configuration.

Everything hardware-specific (GPIO numbers, bay to USB port-path mapping, bridge
USB IDs) lives here as data so the same engine runs on the appliance, on a
workstation with a USB dock, or fully simulated.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field
from pathlib import Path

# USB port paths, as they appear in sysfs (the leaf of the device path, e.g. "1-1.2"),
# for each bay. PLACEHOLDERS: fill in from the real board once it exists
# (`braindrain list` prints every candidate with its port path).
DEFAULT_BAY_PORTS: dict[int, str] = {1: "1-1.1", 2: "1-1.2", 3: "2-1.1", 4: "2-1.2"}

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
DEFAULT_BAY_EN_GPIOS: dict[int, int] = {1: 5, 2: 6, 3: 12, 4: 13}
DEFAULT_BUZZER_GPIO = 18
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
    buzzer_gpio: int = DEFAULT_BUZZER_GPIO
    status_led_gpio: int = DEFAULT_STATUS_LED_GPIO
    oled_driver: str = "ssd1306"  # or "sh1106"
    i2c_port: int = 1
    oled_address: int = 0x3C

    # Simulation
    sim_dir: Path | None = None

    @property
    def bays(self) -> list[int]:
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


def env_flag(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")
