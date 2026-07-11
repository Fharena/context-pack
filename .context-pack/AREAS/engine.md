---
id: engine
status: active
paths:
  - plugins/context-pack/skills/context-pack/scripts/context_pack.py
  - src/context_pack/cli.py
tests:
  - tests/test_context_pack.py
verify:
  - python -m unittest discover -s tests -v
last_reviewed_head: c18bd9bcc69b
---

# Engine

## Read When
- Changing routing, Git snapshots, Evidence, packs, checkpoints, doctor, installers, or hooks.

## Start With
- `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
- `tests/test_context_pack.py`

## Search First
- `resolve_pack_context`
- `collect_evidence`
- `render_agent_pack`
- `cmd_start`

## Contracts
- The canonical engine remains Python stdlib-only.
- Normal `start` never persists repository files before explicit `setup`.
- Review routing reads context from the base commit; branch-only notes are untrusted.
- Evidence always comes from current source and reports `strong`, `candidate`, or no confidence.
- Candidate Evidence requires one targeted verification before editing.
- Agent output is bounded and avoids generated context or managed agent docs as source Evidence.
- Safe hooks invoke the exact install interpreter and fail open.
- Normal `start` does not scan the full repository for text-budget statistics.

## Common Failure Modes
- Branch-authored context biases a review.
- A nearby task-word match is presented as a verified root cause.
- Continuation invents a generic task and ignores `CURRENT.md`.
- Context Pack metadata hides product changes or appears as source Evidence.
- A Unix absolute hook path loses its leading slash.
- Search-only routing adds a model turn without removing later exploration.

## Do Not Start With
- generated packs
- checkpoint history unless the bug concerns handoff state
