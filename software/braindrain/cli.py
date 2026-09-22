"""braindrain command line.

  braindrain simulate [--sim-dir D] [--grace S] [--display term|log|none]
  braindrain sim-plug BAY --size 256M [--media hdd|ssd|nvme] [--fw crypto,block] [--throttle 20M]
  braindrain sim-unplug BAY
  braindrain dip 00000000          decode a DIP setting
  braindrain list                  real enumeration + safety-fence verdicts (needs pyudev)
  braindrain run                   the appliance service (real HAL)
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from . import __version__
from .config import Config
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
    cfg = Config.for_simulation(sim_dir, grace_seconds=a.grace, block_size=a.block_size)
    panel, power, _ = make_hal(cfg)
    disp = SimDisplay(a.display, sim_dir)
    eng = Engine(cfg, SimWatcher(cfg), panel, power, disp, _unit_line(cfg))
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


def cmd_dip(a) -> int:
    p = Policy.from_dip(Dip.from_string(a.bits))
    print(f"mode={p.mode.name} pattern={'random' if p.random_pattern else 'zeros'} "
          f"verify={'sampled' if p.sampled_verify else 'full'} maintenance={p.maintenance}")
    return 0


def cmd_list(a) -> int:
    from .devices import collect_real

    cfg = Config()
    rows = collect_real(cfg)
    for info, bay, reason in rows:
        tag = f"BAY {bay}" if bay else "skip "
        print(f"{tag:6} {info.dev_path:14} {info.size_bytes / 1e9:8.1f} GB  usb={info.usb_port or '-':8} "
              f"bridge={info.bridge_vid or '-'}:{info.bridge_pid or '-'}  {reason}")
    if not rows:
        print("no block disks found")
    return 0


def cmd_run(a) -> int:
    from .engine import Engine
    from .hal import make_hal
    from .sim.udev import UdevWatcher

    cfg = Config()
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

    s = sub.add_parser("dip", help="decode a DIP switch setting")
    s.add_argument("bits")
    s.set_defaults(fn=cmd_dip)

    s = sub.add_parser("list", help="enumerate real disks and show fence verdicts")
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("run", help="run the appliance service on real hardware")
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
