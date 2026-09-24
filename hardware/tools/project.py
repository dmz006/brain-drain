"""Which board the generators work on: BD_PROJECT=brain (default) or card (C24 bay card).

    brain -> hardware/brain-drain.*      sheets/ routing/ lib/
    card  -> hardware/bay-card/bay-card.* sheets/ routing/ (shares ../lib)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

HW = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Project:
    key: str          # "brain" | "card"
    name: str         # file stem
    dir: Path         # project directory
    lib_uri: str      # for sym-lib-table / fp-lib-table

    @property
    def pcb(self) -> Path: return self.dir / f"{self.name}.kicad_pcb"
    @property
    def sch(self) -> Path: return self.dir / f"{self.name}.kicad_sch"
    @property
    def pro(self) -> Path: return self.dir / f"{self.name}.kicad_pro"
    @property
    def sheets(self) -> Path: return self.dir / "sheets"
    @property
    def routing(self) -> Path: return self.dir / "routing"
    @property
    def renders(self) -> Path: return self.dir / "renders"


PROJECTS = {
    "brain": Project("brain", "brain-drain", HW, "${KIPRJMOD}/lib"),
    "card": Project("card", "bay-card", HW / "bay-card", "${KIPRJMOD}/../lib"),
}


def current() -> Project:
    key = os.environ.get("BD_PROJECT", "brain")
    if key not in PROJECTS:
        raise SystemExit(f"BD_PROJECT must be one of {list(PROJECTS)}, not {key!r}")
    p = PROJECTS[key]
    p.dir.mkdir(exist_ok=True)
    return p
