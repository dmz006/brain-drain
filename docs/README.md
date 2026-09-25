# brain-drain documentation

| Document | What it is for |
|---|---|
| [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md) | **For the board layout engineer:** what was delivered, how it was made, what is verified, the risks in priority order, a sign-off checklist. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The design: hardware, software, enclosure, cross-cutting rules. Source of truth for intent. |
| [STATUS.md](STATUS.md) | What is done, what is placeholder, what is blocked, what comes next. |
| [USAGE.md](USAGE.md) | How to run the simulator, the bench tool, the Pi service, and how to regenerate hardware and enclosure files. |
| [BOM.md](BOM.md) | Generated parts list of both boards with vendor part numbers and prices; CSV copies in `hardware/bom/`. |
| [RENDERS.md](RENDERS.md) | Every render: boards one by one, the assembled electronics, the case, the unit open, exploded, cut-away, the complete system. |
| [FABRICATION.md](FABRICATION.md) | Who can fabricate and fully assemble a small run, what it costs, and the gates before ordering. |
| [DECISIONS.md](DECISIONS.md) | Every decision, open (`D<n>`) or closed (`C<n>`), with reasons. |
| [decisions/](decisions/) | The longer briefs behind the bigger decisions. |
| [testing-tracker.md](testing-tracker.md) | Tested vs validated, per interface and part. |
| [saturday-bench-plan.md](saturday-bench-plan.md) | Step-by-step plan for the first real-drive bench, 2026-09-26. |
| [plans/](plans/) | Multi-session work plans (none yet). |
| [HISTORY.md](HISTORY.md) | Session log: how the repository got here. |
| [img/](img/) | Diagrams and mockups; regenerate with `software/.venv/bin/python docs/tools/diagrams.py` and `software/tools/oled_mockup.py`. |

## Diagrams

| | |
|---|---|
| ![system](img/system-block.png) | ![bay flow](img/bay-flow.png) |
| ![lid plan](img/lid-plan.png) | ![left panel](img/left-panel.png) |
| ![oled wifi](img/oled-wifi.png) | ![oled](img/oled-running.png) |

Renders of the boards, the assembly, the case and the complete system are in [RENDERS.md](RENDERS.md) (files in `img/renders/`); KiCad views and
per-layer images in `../hardware/renders/`; generated review data in `../hardware/review/`.
