---
id: engine
last_reviewed_head: 4cd7e6c6caf4
status: active
paths:
  - plugins/context-pack/skills/context-pack/scripts/context_pack.py
  - plugins/context-pack/scripts/context_pack.py
tests:
  - tests/test_context_pack.py
stale_if:
  - engine command behavior changes
  - git matching behavior changes
  - hook install behavior changes
---

# Engine

## Read When
- Changing `context_pack.py` commands or output.
- Debugging checkpoint, pack, review-pack, status, mark-reviewed, refresh, doctor, or git hook behavior.
- Adding new deterministic operations that should not spend agent tokens.

## Start With
- `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
- `tests/test_context_pack.py`

## Contracts
- Engine stays stdlib-only.
- Dirty/untracked files must resolve to actual file paths for area matching.
- Review packs must support committed branch changes via `--base`.
- Packs should stay compact: rank areas, split Read First/Read Later, and omit overflow details with clear counts.
- Stale warnings should be actionable through `status` and `mark-reviewed`.
- Hook install must preserve unrelated hook contents and be idempotent.
- Generated packs live under `.codex/packs/` and stay ignored.

## Common Failure Modes
- `git status` reports an untracked directory instead of files.
- `review-pack` sees no dirty files and misses committed review scope.
- Existing hook files get overwritten instead of marker blocks being inserted.
- Stale area docs are hidden instead of surfaced as warnings.
- Broad overview/context patterns dominate the pack instead of specific changed-file areas.
- Contracts or failure modes repeat until the pack stops saving tokens.

## Expand Scope If
- Manifest schema changes.
- Pack markdown format changes.
- Git hook behavior changes.
- README/SKILL command examples change.

## Do Not Start With
- `.codex/packs/`
- append-only `LOG.md` unless debugging checkpoint history
