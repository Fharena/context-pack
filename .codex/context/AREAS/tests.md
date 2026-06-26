---
id: tests
last_reviewed_head: 4cd7e6c6caf4
status: active
paths:
  - tests/test_context_pack.py
tests:
  - python -m unittest discover -s tests -v
stale_if:
  - engine commands change
- hook behavior changes
- review-pack behavior changes
- start behavior changes
---

# Tests

## Read When
- Adding or changing engine behavior.
- Debugging release validation.
- Reviewing whether a new command has coverage.

## Start With
- `tests/test_context_pack.py`

## Contracts
- Tests call the engine through `main()` to stay close to script usage.
- Coverage includes no-git initialization, first-run start, dirty file packs, task keyword packs, committed review packs, and hook idempotency.
- Git tests configure user identity locally in temp repos.

## Common Failure Modes
- Importing the engine differently than runtime execution.
- Forgetting committed branch review behavior and testing only dirty files.
- Installing hooks twice and duplicating marker blocks.

## Expand Scope If
- Adding a command.
- Changing manifest schema.
- Changing git hook behavior.

## Do Not Start With
- plugin metadata unless validation fails
