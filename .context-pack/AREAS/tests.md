---
id: tests
last_reviewed_head: b9ddcaa1caaf
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
- Coverage includes no-git initialization, no-argument quickstart, `--version`, first-run setup, doctor repair, first-run start, install-codex, install-agent-docs, Node wrapper help/setup/install-codex, packaged natural-language start routing, scope-reduction pack output, dirty file packs, task keyword packs, committed review packs, and hook idempotency.
- Natural-language product promises should stay covered by a small-repo flow: bug orientation, failing-test orientation, dirty and committed branch review, soft review wording, natural handoff wording, and handoff checkpoint.
- Status coverage should include stale shared handoff fingerprints and avoid false positives after handoff-only publish commits.
- Version sync tests should include Python package, plugin manifest, engine, and npm package metadata.
- Git tests configure user identity locally in temp repos.

## Common Failure Modes
- Importing the engine differently than runtime execution.
- Forgetting committed branch review behavior and testing only dirty files.
- Natural branch-review wording is tested only with dirty files, so auto base inference can regress unnoticed.
- Soft review wording coverage is removed from the packaged npm entrypoint, leaving release behavior weaker than unit tests.
- Installing hooks twice and duplicating marker blocks.
- Installing shared agent docs twice and duplicating marker blocks.
- Letting setup drift from the init/install-agent-docs/hook commands it composes.
- Adding handoff health warnings that become impossible to clear after committing tracked handoff docs.
- Testing doctor only as read-only validation after adding repair behavior.
- Node wrapper tests stop at `--help` after README starts recommending no-argument quickstart, `npx` setup, or install-codex paths.
- Packaged CLI validation installs successfully but does not exercise the natural-language bug/review flow advertised to agents.
- README advertises "why are tests failing" but tests do not prove that source context is included with tests.
- Packaged CLI validation covers bug/review prompts but not the resume-later handoff prompt from the public docs.

## Expand Scope If
- Adding a command.
- Changing manifest schema.
- Changing git hook behavior.

## Do Not Start With
- plugin metadata unless validation fails
