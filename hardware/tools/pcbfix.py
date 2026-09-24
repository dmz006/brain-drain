"""Small post-processing fixes on a generated .kicad_pcb."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

UUID = re.compile(r'\((uuid|tstamp) "([0-9a-fA-F-]{36})"\)')


def uniquify_uuids(path: Path) -> int:
    """Footprints loaded from the same library file carry identical pad and graphic UUIDs; KiCad resolves
    DRC items by UUID, so it then reports the wrong pad (a slot's pad shows up as the first slot's). Give every
    repeat a fresh UUID. Returns how many were replaced."""
    text = Path(path).read_text()
    seen: set[str] = set()
    n = 0

    def sub(m):
        nonlocal n
        key = m.group(2).lower()
        if key in seen:
            n += 1
            return f'({m.group(1)} "{uuid.uuid4()}")'
        seen.add(key)
        return m.group(0)

    out = UUID.sub(sub, text)
    if n:
        Path(path).write_text(out)
    return n


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(p, uniquify_uuids(Path(p)), "duplicate UUIDs replaced")
