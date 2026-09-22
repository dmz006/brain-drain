"""braindrain command line.

  braindrain simulate [--sim-dir D] [--grace S] [--display term|log|none]
  braindrain sim-plug BAY --size 256M [--media hdd|ssd|nvme] [--fw crypto,block] [--throttle 20M]
  braindrain sim-unplug BAY
  braindrain sim-door open|closed  bay 5 access door (M.2 slot powers only while closed)
  braindrain sim-pedet pcie|sata   M.2 PEDET pin; a SATA module is refused
  braindrain dip 00000000          decode a DIP setting
  braindrain list                  real enumeration + safety-fence verdicts (needs pyudev)
  braindrain run [--config F]      the appliance service (real or headless HAL per the config)
  braindrain status [--config F]   last display frame and bay states
  braindrain config-init [--headless] [--config F]   write a starting config file
  braindrain setup-bay BAY /dev/sdX [--config F]     map the dock behind /dev/sdX to a bay
  braindrain bench /dev/sdX        USB-SATA bridge passthrough tests (see bench.py)
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from . import __version__
from .config import DEFAULT_CONFIG_PATH, Config
from .policy import Dip, Policy

DEFAULT_SIM_DIR = Path.home() / ".brain-drain-sim"


def _unit_line(cfg):
    import socket
    import time

    def f():
        return f"{cfg.unit_id[:10]} {time.strftime('%H:%M')} {socket.gethostname()[:20]}"

    return f


def cmd_simulate(a) -> int:
    from .engine import Engine
    from .hal import make_hal
    from .hal.sim import SimDisplay
    from .sim.bays import SimWatcher

    sim_dir = Path(a.sim_dir)
    sim_dir.mkdir(parents=True, exist_ok=True)
    dip = sim_dir / "dip"
    if not dip.exists():
        dip.write_text("00000000\n")
    for name, default in (("door", "closed"), ("pedet", "pcie")):
        if not (sim_dir / name).exists():
            (sim_dir / name).write_text(default + "\n")
    cfg = Config.for_simulation(sim_dir, grace_seconds=a.grace, block_size=a.block_size)
    panel, power, _ = make_hal(cfg)
    disp = SimDisplay(a.display, sim_dir)
    watcher = SimWatcher(cfg)
    eng = Engine(cfg, watcher, panel, power, disp, _unit_line(cfg))
    watcher.visible = eng.m2_visible
    signal.signal(signal.SIGINT, lambda *_: eng.stop.set())
    signal.signal(signal.SIGTERM, lambda *_: eng.stop.set())
    logging.getLogger().info("simulating in %s; plug drives with `braindrain sim-plug`", sim_dir)
    eng.run_forever()
    return 0


def cmd_sim_plug(a) -> int:
    from .sim.bays import parse_size, plug

    fw = None
    if a.fw:
        fw = {k.strip(): True for k in a.fw.split(",") if k.strip()}
        fw["seconds"] = a.fw_seconds
    thr = parse_size(a.throttle) if a.throttle else None
    img = plug(Path(a.sim_dir), a.bay, parse_size(a.size), media=a.media, model=a.model,
               serial=a.serial, firmware=fw, throttle_bps=thr, prefill=a.prefill)
    print(f"plugged {a.media} {a.size} into bay {a.bay}: {img}")
    return 0


def cmd_sim_unplug(a) -> int:
    from .sim.bays import unplug

    unplug(Path(a.sim_dir), a.bay)
    print(f"unplugged bay {a.bay}")
    return 0


def cmd_sim_door(a) -> int:
    (Path(a.sim_dir) / "door").write_text(a.state + "\n")
    print(f"bay 5 door {a.state}")
    return 0


def cmd_sim_pedet(a) -> int:
    (Path(a.sim_dir) / "pedet").write_text(a.kind + "\n")
    print(f"bay 5 PEDET = {a.kind}")
    return 0


def cmd_dip(a) -> int:
    p = Policy.from_dip(Dip.from_string(a.bits))
    print(f"mode={p.mode.name} pattern={'random' if p.random_pattern else 'zeros'} "
          f"verify={'sampled' if p.sampled_verify else 'full'} maintenance={p.maintenance}")
    return 0


def cmd_list(a) -> int:
    from .devices import collect_real

    cfg = Config.load(a.config)
    rows = collect_real(cfg)
    for info, bay, reason in rows:
        tag = f"BAY {bay}" if bay else "skip "
        print(f"{tag:6} {info.dev_path:14} {info.size_bytes / 1e9:8.1f} GB  usb={info.usb_port or '-':8} "
              f"bridge={info.bridge_vid or '-'}:{info.bridge_pid or '-'}  {reason}")
    if not rows:
        print("no block disks found")
    return 0


def cmd_bench(a) -> int:
    from .bench import Bench, confirm_destructive

    b = Bench(a.device, destructive=a.destructive, sanitize=a.sanitize, io_bytes=a.io_mib << 20)
    if a.destructive:
        b.bridge()
        b.identify()
        if not b.ident:
            return 1
        if not a.yes and not confirm_destructive(b.ident["serial"], b.ident["model"]):
            print("aborted")
            return 1
        b.report.checks.clear()
    rep = b.run_all()
    path = b.save(Path(a.out_dir))
    fails = [c.name for c in rep.checks if c.ok is False]
    passes = len([c for c in rep.checks if c.ok])
    print(f"\n{rep.bridge_name} ({rep.bridge_id}) with {rep.drive.get('model')}: "
          f"{passes} pass, {len(fails)} fail -> {path}")
    return 1 if fails else 0


def cmd_config_init(a) -> int:
    cfg = Config()
    cfg.display_file = Path("/var/lib/brain-drain/display.txt")
    if a.headless:
        cfg.hal = "headless"
        cfg.m2_bay = None
        cfg.bay_ports = {}
    path = cfg.save(a.config)
    print(f"wrote {path} (hal={cfg.hal}); edit bay_ports / allowed_bridges or use `braindrain setup-bay`")
    return 0


def cmd_setup_bay(a) -> int:
    from .devices import describe_device

    cfg = Config.load(a.config)
    info = describe_device(a.device)
    if info is None:
        print(f"{a.device}: not found")
        return 1
    if info.usb_port is None:
        print(f"{a.device}: not behind a USB port (internal disk?) - refusing")
        return 1
    if info.is_system:
        print(f"{a.device}: holds a mounted filesystem, root or swap - refusing")
        return 1
    cfg.bay_ports[a.bay] = info.usb_port
    bridge = (info.bridge_vid, info.bridge_pid)
    if bridge not in cfg.allowed_bridges:
        cfg.allowed_bridges = frozenset(cfg.allowed_bridges | {bridge})
        print(f"added bridge {info.bridge_vid}:{info.bridge_pid} to the allow-list")
    cfg.save(a.config)
    print(f"bay {a.bay} = USB port {info.usb_port} ({info.bridge_vid}:{info.bridge_pid}) -> {a.config}")
    print("note: the mapping is by USB *port*; any drive plugged into that dock is now a wipe target")
    return 0


def cmd_status(a) -> int:
    cfg = Config.load(a.config)
    if cfg.display_file and Path(cfg.display_file).exists():
        print(Path(cfg.display_file).read_text(), end="")
    else:
        print("no display file yet (is the service running?)")
    st = Path(cfg.state_file)
    if st.exists():
        print("state:", st.read_text().strip()[:400])
    return 0


def cmd_run(a) -> int:
    from .engine import Engine
    from .hal import make_hal
    from .sim.udev import UdevWatcher

    cfg = Config.load(a.config)
    if cfg.hal == "real" and not cfg.bay_ports:
        print("config has no bay_ports; run `braindrain setup-bay` first", file=sys.stderr)
        return 2
    panel, power, disp = make_hal(cfg)
    eng = Engine(cfg, UdevWatcher(cfg), panel, power, disp, _unit_line(cfg))
    signal.signal(signal.SIGTERM, lambda *_: eng.stop.set())
    signal.signal(signal.SIGINT, lambda *_: eng.stop.set())
    eng.run_forever()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="braindrain", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("simulate", help="run the engine against simulated bays")
    s.add_argument("--sim-dir", default=str(DEFAULT_SIM_DIR))
    s.add_argument("--grace", type=float, default=5.0)
    s.add_argument("--block-size", type=int, default=8 * 1024 * 1024)
    s.add_argument("--display", choices=["term", "log", "none"], default="term")
    s.set_defaults(fn=cmd_simulate)

    s = sub.add_parser("sim-plug", help="plug a simulated drive into a bay")
    s.add_argument("bay", type=int)
    s.add_argument("--sim-dir", default=str(DEFAULT_SIM_DIR))
    s.add_argument("--size", default="256M")
    s.add_argument("--media", choices=["hdd", "ssd", "nvme"], default="hdd")
    s.add_argument("--model")
    s.add_argument("--serial")
    s.add_argument("--fw", help="simulated firmware sanitize kinds, e.g. crypto,block")
    s.add_argument("--fw-seconds", type=float, default=3.0)
    s.add_argument("--throttle", help="cap overwrite rate, e.g. 20M (bytes/s)")
    s.add_argument("--prefill", action="store_true", help="fill with random data first")
    s.set_defaults(fn=cmd_sim_plug)

    s = sub.add_parser("sim-unplug", help="unplug a simulated drive")
    s.add_argument("bay", type=int)
    s.add_argument("--sim-dir", default=str(DEFAULT_SIM_DIR))
    s.set_defaults(fn=cmd_sim_unplug)

    s = sub.add_parser("sim-door", help="open or close the simulated bay 5 door")
    s.add_argument("state", choices=["open", "closed"])
    s.add_argument("--sim-dir", default=str(DEFAULT_SIM_DIR))
    s.set_defaults(fn=cmd_sim_door)

    s = sub.add_parser("sim-pedet", help="simulate the M.2 PEDET pin: pcie (normal) or sata (refused)")
    s.add_argument("kind", choices=["pcie", "sata"])
    s.add_argument("--sim-dir", default=str(DEFAULT_SIM_DIR))
    s.set_defaults(fn=cmd_sim_pedet)

    s = sub.add_parser("dip", help="decode a DIP switch setting")
    s.add_argument("bits")
    s.set_defaults(fn=cmd_dip)

    s = sub.add_parser("list", help="enumerate real disks and show fence verdicts")
    s.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("status", help="show the last display frame and state")
    s.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("config-init", help="write a starting config file")
    s.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    s.add_argument("--headless", action="store_true", help="Pi + USB docks, no carrier board")
    s.set_defaults(fn=cmd_config_init)

    s = sub.add_parser("setup-bay", help="map the USB dock behind a block device to a bay number")
    s.add_argument("bay", type=int)
    s.add_argument("device", help="/dev/sdX currently attached through the dock")
    s.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    s.set_defaults(fn=cmd_setup_bay)

    s = sub.add_parser("bench", help="test ATA passthrough through a USB-SATA bridge")
    s.add_argument("device", help="/dev/sdX of the drive behind the bridge")
    s.add_argument("--destructive", action="store_true", help="also run write test and SECURITY ERASE")
    s.add_argument("--sanitize", action="store_true", help="also run SANITIZE (hours on an HDD)")
    s.add_argument("--yes", action="store_true", help="skip the serial-number confirmation")
    s.add_argument("--io-mib", type=int, default=1024, help="MiB for read/write speed tests")
    s.add_argument("--out-dir", default=".", help="where to write bench-*.json")
    s.set_defaults(fn=cmd_bench)

    s = sub.add_parser("run", help="run the appliance service on real hardware")
    s.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    s.set_defaults(fn=cmd_run)

    a = ap.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
