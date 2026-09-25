# DRC summary

kicad-cli 9 `pcb drc`, all severities.

## brain

* violations: 0 errors, 290 warnings; unconnected items: 0

| severity | type | count |
|---|---|---|
| warning | lib_footprint_mismatch | 1 |
| warning | silk_edge_clearance | 5 |
| warning | silk_over_copper | 82 |
| warning | silk_overlap | 199 |
| warning | track_dangling | 3 |

Warnings are silkscreen overlaps and dangling vias/tracks (fanout stubs); none affect copper.  `hole_clearance`, `clearance`, `track_width`, `copper_edge_clearance` and `shorting_items` are all zero. Reports: `routing/drc.json`, `routing/open.md`, `routing/pairs.md`.

## card

* violations: 0 errors, 44 warnings; unconnected items: 0

| severity | type | count |
|---|---|---|
| warning | silk_edge_clearance | 2 |
| warning | silk_over_copper | 7 |
| warning | silk_overlap | 32 |
| warning | track_dangling | 3 |

Warnings are silkscreen overlaps and dangling vias/tracks (fanout stubs); none affect copper.  `hole_clearance`, `clearance`, `track_width`, `copper_edge_clearance` and `shorting_items` are all zero. Reports: `routing/drc.json`, `routing/open.md`, `routing/pairs.md`.

