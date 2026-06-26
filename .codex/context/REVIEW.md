# Review Router

For code review, map changed files to areas, then check the listed contracts, tests, and failure modes before widening scope.

## Area Routing

### engine
- Doc: `.codex/context/AREAS/engine.md`
- If changed files match:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `plugins/context-pack/scripts/context_pack.py`
- Inspect/run tests:
  - `tests/test_context_pack.py`
- Common failure modes:
  - Dirty files are matched only at directory level, missing the real changed file.
  - Review packs ignore committed branch changes when no dirty files exist.
  - Hook installation duplicates marker blocks or overwrites unrelated user hook logic.
  - Pack generation creates tracked generated files.

### installer-release
- Doc: `.codex/context/AREAS/installer-release.md`
- If changed files match:
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
  - `README.md`
  - `LICENSE`
  - `.gitignore`
- Inspect/run tests:
  - `python -m unittest discover -s tests -v`
  - `python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack`
  - `python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack`
- Common failure modes:
  - Installer replaces a user's existing skill/plugin without explicit --force.
  - Marketplace entry points to the wrong relative plugin path.
  - README documents a command not covered by tests or validation.

### overview
- Doc: `.codex/context/AREAS/overview.md`
- If changed files match:
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `codex.md`
  - `.codex/context/**`
- Common failure modes:
  - Trusting old summaries after HEAD or dirty files changed.
  - Reading logs or generated packs before current source files.
  - Editing the wrong checkout or copied workspace.

### skill-plugin
- Doc: `.codex/context/AREAS/skill-plugin.md`
- If changed files match:
  - `plugins/context-pack/.codex-plugin/plugin.json`
  - `plugins/context-pack/skills/context-pack/SKILL.md`
  - `plugins/context-pack/skills/context-pack/agents/openai.yaml`
- Inspect/run tests:
  - `python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack`
  - `python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack`
- Common failure modes:
  - Skill docs describe behavior that the script cannot perform.
  - Plugin metadata promises automatic lifecycle hooks not actually installed by the manifest.
  - Trigger description is too narrow and only catches session handoff use cases.

### tests
- Doc: `.codex/context/AREAS/tests.md`
- If changed files match:
  - `tests/test_context_pack.py`
- Inspect/run tests:
  - `python -m unittest discover -s tests -v`
- Common failure modes:
  - Tests import the engine in a way that differs from script execution.
  - Git behavior is tested only with dirty files and misses committed review use cases.
  - Hook tests check creation but not idempotency or uninstall.

## Escalate Review Scope When
- Public API, CLI, schema, storage format, subprocess launch, or cache/session identity changed.
- Tests or test helpers changed in a way that may hide behavior.
- A changed file does not map to any known area.
