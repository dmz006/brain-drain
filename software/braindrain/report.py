"""Per-drive sanitization certificate (JSON) and crash-recovery state."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from . import __version__

SCHEMA_VERSION = 1


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Attempt:
    method: str
    supported: bool
    reason: str = ""
    ok: bool | None = None
    detail: str = ""
    started: str | None = None
    finished: str | None = None
    facts: dict = field(default_factory=dict)


@dataclass
class Certificate:
    schema_version: int
    unit_id: str
    software_version: str
    bay: int
    drive: dict
    policy: dict
    started: str
    finished: str | None = None
    outcome: str = "running"  # running | sanitized | failed | aborted | interrupted | dry-run
    tier_claimed: str = "none"
    method_used: str | None = None
    attempts: list[Attempt] = field(default_factory=list)
    verification: dict | None = None
    smart_pre: dict | None = None
    smart_post: dict | None = None
    throughput_bps: float | None = None
    elapsed_s: float | None = None
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=False)

    def filename(self) -> str:
        serial = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(self.drive.get("serial", "unknown")))
        return f"{self.started.replace(':', '-')}_bay{self.bay}_{serial}.json"


def write_certificate(cert: Certificate, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / cert.filename()
    n = 1
    while path.exists():  # same drive, same bay, same second: never overwrite a certificate
        n += 1
        path = report_dir / cert.filename().replace(".json", f"-{n}.json")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(cert.to_json())
    os.replace(tmp, path)
    return path


def new_certificate(cfg, drive, policy) -> Certificate:
    return Certificate(
        schema_version=SCHEMA_VERSION,
        unit_id=cfg.unit_id,
        software_version=__version__,
        bay=drive.bay,
        drive=drive.summary(),
        policy={"mode": policy.mode.name, "dip": policy.dip, "random_pattern": policy.random_pattern,
                "sampled_verify": policy.sampled_verify},
        started=now_iso(),
    )


# ------------------------------------------------------------------ crash state


def save_state(state_file: Path, running: dict[int, dict]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps({"saved": now_iso(), "running": running}, indent=2))
    os.replace(tmp, state_file)


def load_state(state_file: Path) -> dict[int, dict]:
    try:
        data = json.loads(state_file.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return {int(k): v for k, v in data.get("running", {}).items()}


def write_interrupted(cfg, prior: dict[int, dict]) -> list[Path]:
    """On boot, turn last session's running jobs into 'interrupted' certificates."""
    out = []
    for bay, job in prior.items():
        cert = Certificate(
            schema_version=SCHEMA_VERSION, unit_id=cfg.unit_id, software_version=__version__,
            bay=bay, drive=job.get("drive", {}), policy=job.get("policy", {}),
            started=job.get("started", now_iso()), finished=now_iso(), outcome="interrupted",
            notes=["power loss or crash while running; drive is NOT sanitized"],
        )
        out.append(write_certificate(cert, cfg.report_dir))
    return out
