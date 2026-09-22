# Contributing

brain-drain is a one-person hardware project at the moment; these notes are so a
second person (or an agent) can work in it without breaking the conventions.

1. Read `AGENT.md` first. It is short and it is the rule set.
2. The owner decides; propose, do not choose. Open a decision as `D<n>` in
   `docs/DECISIONS.md` rather than silently picking a part.
3. Never hand-edit generated files (see `AGENT.md`). Change `design.py`,
   `params.scad` or the CSV pin tables and regenerate.
4. Before committing: `cd software && ruff check . && pytest`;
   `cd hardware && python3 tools/gen_sch.py` (0 errors); `cd enclosure && make`.
5. Conventional commits, one change per commit, changelog entry, status update.
6. Anything that touches a real disk goes through the safety fence and gets a
   review note in the commit message.

Vendor PDFs are not committed. If you need one, `hardware/ref/DOWNLOADS.md`
lists where to get it and what to name it.
