---
id: tests
last_reviewed_head: fd38d64e168b
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
- Natural-language product promises should stay covered by a small-repo flow: English fix, crash, and broken/not-working bug orientation, Korean bug orientation, failing-test and CI/build failure orientation, dirty and committed branch review, soft review wording, long and short handoff wording, and handoff checkpoint.
- First-run inference coverage should include common top-level Python package source layouts such as `httpx/`.
- First-run inference coverage should include common web game layouts with `client/js`, `server/js`, `shared/js`, and sprite assets so BrowserQuest-like repos do not regress to overview-only context.
- Status coverage should include stale shared handoff fingerprints and avoid false positives after handoff-only publish commits.
- Version sync tests should include Python package, plugin manifest, engine, and npm package metadata.
- Git tests configure user identity locally in temp repos.

## Common Failure Modes
- Importing the engine differently than runtime execution.
- Forgetting committed branch review behavior and testing only dirty files.
- Natural branch-review wording is tested only with dirty files, so auto base inference can regress unnoticed.
- Soft review wording coverage is removed from the packaged npm entrypoint, leaving release behavior weaker than unit tests.
- Short handoff wording coverage is removed from the packaged npm entrypoint, leaving release behavior weaker than unit tests.
- Installing hooks twice and duplicating marker blocks.
- Installing shared agent docs twice and duplicating marker blocks.
- Letting setup drift from the init/install-agent-docs/hook commands it composes.
- Adding handoff health warnings that become impossible to clear after committing tracked handoff docs.
- Testing doctor only as read-only validation after adding repair behavior.
- Node wrapper tests stop at `--help` after README starts recommending no-argument quickstart, `npx` setup, or install-codex paths.
- Packaged CLI validation installs successfully but does not exercise the natural-language bug/review flow advertised to agents.
- README advertises "why are tests failing" but tests do not prove that source context is included with tests.
- CI/build failure routing coverage is removed from the packaged npm entrypoint, leaving release behavior weaker than unit tests.
- Top-level Python package inference is removed, so real repos without `src/` miss source context during first-run routing.
- Web/client-server JavaScript inference is removed, so BrowserQuest-like repos miss source/sprite context during first-run routing.
- English broken/not-working routing coverage is removed from the packaged npm entrypoint, leaving release behavior weaker than unit tests.
- Korean bug routing tests cover only "버그 고쳐줘" and miss "버그 잡아줘" / "문제 해결해줘" variants or their false-positive guard.
- Packaged CLI validation covers bug/review prompts but not the resume-later handoff prompt from the public docs.

## Expand Scope If
- Adding a command.
- Changing manifest schema.
- Changing git hook behavior.

## Do Not Start With
- plugin metadata unless validation fails
