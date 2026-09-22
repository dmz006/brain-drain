"""Render design.py as hardware/CONNECTIONS.md: the connection list for drawing the schematic by hand."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import design

HW = Path(__file__).resolve().parent.parent


def main():
    d = design.build()
    pin_net = d.pin_net()
    out = [f"# {d.title} — connection list\n",
           "Generated from `hardware/tools/design.py`; do not edit by hand. One table per sheet: every",
           "component with its symbol, value and footprint, then every net on that sheet with the pins",
           "it joins. Nets marked **global** continue on other sheets. Pins listed under *No connect*",
           "get an explicit no-connect flag.\n",
           f"Totals: {len(d.comps)} components, {len(d.nets)} nets.\n"]
    for sheet, desc in d.sheets:
        out.append(f"\n## Sheet `{sheet}` — {desc}\n")
        comps = [c for c in d.comps.values() if sheet in (c.sheet, *c.unit_sheets.values())]
        out.append("### Components\n\n| Ref | Symbol | Value | Footprint | Note |\n|---|---|---|---|---|")
        for c in sorted(comps, key=lambda c: (c.ref[0], len(c.ref), c.ref)):
            units = [u for u, s in c.unit_sheets.items() if s == sheet]
            ref = c.ref + (f" (unit {','.join(map(str, units))})" if c.unit_sheets and units else "")
            out.append(f"| {ref} | `{c.lib_id}` | {c.value} | `{c.footprint}` | {c.note} |")
        nets_here = defaultdict(list)
        for net, lst in d.nets.items():
            for ref, num in lst:
                if d.sheet_of_pin(ref, num) == sheet:
                    nets_here[net].append((ref, num))
        out.append("\n### Nets\n\n| Net | Scope | Pins on this sheet | Also on |\n|---|---|---|---|")
        for net in sorted(nets_here, key=lambda n: (not n[0].isupper(), n)):
            pins = nets_here[net]
            others = sorted(d.net_sheets(net) - {sheet})
            scope = "**global**" if others or net in d.pwr_flags else "local"
            def fmt(ref, num):
                c = d.comps[ref]
                p = next(p for p in c.sym().pins if p.number == num)
                return f"{ref}.{num}" if p.name in ("~", num) else f"{ref}.{num} ({p.name})"
            out.append(f"| `{net}` | {scope} | {', '.join(fmt(r, n) for r, n in pins)} | {', '.join(others)} |")
        ncs = sorted((r, n) for r, n in d.ncs if d.sheet_of_pin(r, n) == sheet)
        if ncs:
            out.append("\n### No connect\n")
            byref = defaultdict(list)
            for r, n in ncs:
                byref[r].append(n)
            for r in sorted(byref):
                c = d.comps[r]
                names = [next(p.name for p in c.sym().pins if p.number == n) for n in byref[r]]
                out.append(f"* {r}: " + ", ".join(f"{n} ({nm})" if nm not in ('~', n) else n for n, nm in zip(byref[r], names)))
        if d.notes.get(sheet):
            out.append("\n### Notes\n")
            out.extend(f"* {n}" for n in d.notes[sheet])
    flagged = sorted(d.pwr_flags)
    out.append("\n## Power flags\n\nAdd a PWR_FLAG to each of these nets (they are driven by connectors or passive parts): " + ", ".join(f"`{n}`" for n in flagged) + "\n")
    (HW / "CONNECTIONS.md").write_text("\n".join(out) + "\n")
    print(f"wrote hardware/CONNECTIONS.md ({len(out)} lines)")


if __name__ == "__main__":
    main()
