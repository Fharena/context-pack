---
id: tests
last_reviewed_head: 6ce2a3081689
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
  - setup behavior changes
  - doctor repair behavior changes
  - install-codex behavior changes
  - install-agent-docs behavior changes
  - pack format changes
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
- Coverage includes no-git initialization, no-argument quickstart, `--version`, first-run setup, doctor repair, first-run start, install-codex, install-agent-docs, Node wrapper help/setup/install-codex, scope-reduction pack output, dirty file packs, task keyword packs, committed review packs, and hook idempotency.
- Status coverage should include stale shared handoff fingerprints and avoid false positives after handoff-only publish commits.
- Version sync tests should include Python package, plugin manifest, engine, and npm package metadata.
- Git tests configure user identity locally in temp repos.

## Common Failure Modes
- Importing the engine differently than runtime execution.
- Forgetting committed branch review behavior and testing only dirty files.
- Installing hooks twice and duplicating marker blocks.
- Installing shared agent docs twice and duplicating marker blocks.
- Letting setup drift from the init/install-agent-docs/hook commands it composes.
- Adding handoff health warnings that become impossible to clear after committing tracked handoff docs.
- Testing doctor only as read-only validation after adding repair behavior.
- Node wrapper tests stop at `--help` after README starts recommending no-argument quickstart, `npx` setup, or install-codex paths.

## Expand Scope If
- Adding a command.
- Changing manifest schema.
- Changing git hook behavior.

## Do Not Start With
- plugin metadata unless validation fails
