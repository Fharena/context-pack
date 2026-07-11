---
id: engine
status: active
paths:
  - plugins/context-pack/skills/context-pack/scripts/context_pack.py
  - src/context_pack/cli.py
tests:
  - python -m unittest discover -s tests -v
last_reviewed_head: b440399b85ee
---

# Engine

## Read When
- Changing routing, Git snapshots, packs, checkpoints, doctor, installers, or hooks.
- Debugging transient first-run behavior, stale fingerprints, Unicode paths, or review scope.

## Start With
- `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
- `tests/test_context_pack.py`

## Contracts
- The canonical engine remains Python stdlib-only.
- `start` does not persist repo files before explicit `setup`; tiny unconfigured repos may skip packs.
- Git parsing supports Unicode, spaces, renames, and NUL-delimited output.
- Safe hooks invoke the exact install interpreter and fail open.
- Normal `start` does not scan the full repo for text-budget statistics.
- Packs explain deterministic routing but never replace source verification.

## Common Failure Modes
- First-run work unexpectedly creates `.context-pack/`, `AGENTS.md`, or `.gitignore`.
- Context Pack metadata hides real product changes in review mode.
- A Unix absolute hook path loses its leading slash.
- A custom area name cannot receive a generic source/test/automation role.
- A fallback start file points at an entire source or test directory.

## Do Not Start With
- generated packs
- checkpoint logs unless the bug concerns checkpoint history
