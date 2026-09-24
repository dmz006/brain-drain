"""Summarise the open connections in routing/drc.json by net group and by part -> routing/open.md.
Run after `kicad-cli pcb drc --format json --severity-all -o routing/drc.json brain-drain.kicad_pcb`."""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

HW = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HW / "tools"))
import design  # noqa: E402
import project as _project  # noqa: E402
import route  # noqa: E402

PRJ = _project.current()

PLANES = route.POWER_NETS


def main() -> None:
    d = design.build(PRJ.key)
    j = json.loads((PRJ.routing / "drc.json").read_text())
    items = j.get("unconnected_items", [])
    pairs, bays = route.diff_pair_nets(d), route.bay_nets(d)
    by_net, by_part, by_group = collections.Counter(), collections.Counter(), collections.Counter()
    for it in items:
        desc = it["items"][0]["description"]
        m = re.search(r"\[(.*?)\]", desc); net = m.group(1) if m else "?"
        by_net[net] += 1
        for i in it["items"]:
            m2 = re.search(r"of (\w+) on", i["description"])
            if m2:
                by_part[m2.group(1)] += 1
        if net in PLANES:
            g = "plane (needs a via to its plane)"
        elif net in pairs:
            g = "differential pair"
        elif net in bays or net.startswith(("12V_BAY", "5V_BAY")):
            g = "bay power / control"
        elif re.match(r"U1[0-3]_", net):
            g = "bridge-local rail"
        else:
            g = "signal"
        by_group[g] += 1
    lines = [f"# Open connections: {len(items)}", "", "| group | open |", "|---|---|"]
    lines += [f"| {g} | {n} |" for g, n in by_group.most_common()]
    lines += ["", "| net | open |", "|---|---|"] + [f"| {n} | {c} |" for n, c in by_net.most_common(15)]
    lines += ["", "| part | open pins |", "|---|---|"] + [f"| {p} | {c} |" for p, c in by_part.most_common(15)]
    (PRJ.routing / "open.md").write_text("\n".join(lines) + "\n")
    print(f"open connections: {len(items)}; groups: {dict(by_group)}; report routing/open.md")


if __name__ == "__main__":
    main()
