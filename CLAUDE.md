# Session Guardrails

Session: johnnyjohnny-a022 | Task: 

## Constraints
- Work only within: /home/dmz/workspace/brain-drain
- Commit changes to git frequently
- If rate limited: output DATAWATCH_RATE_LIMITED: resets at <time>
- If needing input: output DATAWATCH_NEEDS_INPUT: <question>
- When done: output DATAWATCH_COMPLETE: <summary>

# Local Claude Code details

- **Read first:** `BRAIN-DRAIN-CONTEXT.md` (project and repository), then `AGENT.md` (the rules). Do not put project facts or rules here.
- **RTK:** prefix shell commands with `rtk` (`rtk git status`, `rtk git add -A && rtk git commit -q -m ...`, `rtk git push`). It passes unknown commands through unchanged.
- **Environments:** system `python3` for `pcbnew` and KiCad scripts (`kicad-cli` 9.0.8 on the path); `software/.venv/bin/python` for pytest, ruff and cairosvg; `openscad` for the enclosure.
- **Long jobs:** `hardware/tools/route_full.sh` takes hours; start it with `run_in_background` and check its log under `hardware/routing/`.
- **Commits:** one logical change, conventional message (`hw`, `mech`, `docs`, ...), end with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`; push to `main` after each commit.
- **Memory:** durable notes live in the Claude project memory folder (`project-brain-drain-*`); the datawatch memory tools (`memory_recall`, `memory_remember`, `kg_query`) are used when the server is connected.
- **Working style:** the owner decides; interview format, one question at a time with a recommendation. Routine execution needs no question.

