# brain-drain

Standalone four-bay disk sanitizer: Raspberry Pi CM5 carrier board, Python
sanitizer service, and a 3D-printed enclosure. Wipe methods follow
NIST SP 800-88 Rev. 2.

**Status: design phase. Nothing has been built or fabricated.**

Read `docs/ARCHITECTURE.md` first. `docs/BOM.md` is the parts list,
`docs/DECISIONS.md` the list of open and closed design decisions.

| Directory | Workstream |
|---|---|
| `hardware/` | KiCad 9 carrier board: CM5, 2× USB5744 hubs, 4× ASM1153E, per-bay power switching, UI |
| `software/` | `braindrain` Python service: enumerate, policy, wipe, verify, report, OLED |
| `enclosure/` | OpenSCAD parametric enclosure |
| `docs/` | architecture, BOM, decisions |

## Safety

This device destroys data by design. The software's safety fence
(`docs/ARCHITECTURE.md` §4.3) is the only thing standing between it and the boot
medium or a workstation's drives when run in development. Do not weaken it.
