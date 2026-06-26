# Review Router

For code review, map changed files to areas, then check the listed contracts, tests, and failure modes before widening scope.

## Area Routing

### engine
- Doc: `.codex/context/AREAS/engine.md`
- If changed files match:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `plugins/context-pack/scripts/context_pack.py`
  - `src/context_pack/**`
- Inspect/run tests:
  - `tests/test_context_pack.py`
- Common failure modes:
  - Dirty files are matched only at directory level, missing the real changed file.
  - Review packs ignore committed branch changes when no dirty files exist.
  - Hook installation duplicates marker blocks or overwrites unrelated user hook logic.
  - Pack generation creates tracked generated files.
  - `setup` skips shared agent docs or installs git hooks without explicit setup flags.
  - `start` hides setup errors or creates noisy tracked files on first run.
  - `install-codex --force` overwrites the source plugin tree or writes an invalid marketplace entry.
  - `install-agent-docs` duplicates marker blocks or strips existing AGENTS.md, CLAUDE.md, or Cursor rule content.
  - Scope-reduction numbers are missing or imply false precision about exact token savings.

### installer-release
- Doc: `.codex/context/AREAS/installer-release.md`
- If changed files match:
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
  - `.agents/plugins/marketplace.json`
  - `.github/**`
  - `pyproject.toml`
  - `src/context_pack/**`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `assets/**`
  - `README.md`
  - `README.ko.md`
  - `LICENSE`
  - `SECURITY.md`
  - `.gitignore`
  - `.gitattributes`
- Inspect/run tests:
  - `python -m unittest discover -s tests -v`
  - `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
  - `python -m json.tool .agents/plugins/marketplace.json`
  - `python -m pip install -e .`
  - `context-pack --help`
  - `context-pack setup --repo <tmp> --quiet`
  - `context-pack status --quiet`
  - `context-pack start --task "agent-first CLI UX" --quiet`
  - `context-pack start --review --base HEAD~1 --quiet`
  - `context-pack install-codex --target <tmp>/plugins/context-pack --marketplace <tmp>/.agents/plugins/marketplace.json --quiet`
  - `context-pack install-agent-docs --repo <tmp> --quiet`
  - `context-pack checkpoint --pack --quiet does not dirty tracked files`
- Common failure modes:
  - Installer replaces a user's existing skill/plugin without explicit --force.
  - Marketplace entry points to the wrong relative plugin path.
  - README documents a command not covered by tests or validation.
  - Packaged CLI can start projects but cannot install the Codex skill/plugin experience.

### overview
- Doc: `.codex/context/AREAS/overview.md`
- If changed files match:
  - `README.md`
  - `README.ko.md`
  - `AGENTS.md`
  - `.cursor/rules/**`
  - `assets/**`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `SECURITY.md`
  - `CLAUDE.md`
  - `codex.md`
  - `.agents/plugins/marketplace.json`
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
  - `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
  - `python -m unittest discover -s tests -v`
- Common failure modes:
  - Skill docs describe behavior that the script cannot perform.
  - Plugin metadata promises automatic lifecycle hooks not actually installed by the manifest.
  - Trigger description is too narrow and only catches session handoff use cases.
  - Skill guidance teaches lower-level commands before the one-command start path.
  - Skill guidance teaches `init` plus `install-agent-docs` before the one-command `setup` path.
  - Install/update requests are routed to old local scripts instead of `install-codex`.
  - Claude/Cursor guidance drifts from the generated AGENTS.md rule block.

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
  - Installing shared agent docs twice duplicates marker blocks.
  - Setup drifts from the init/install-agent-docs/hook commands it composes.

## Escalate Review Scope When
- Public API, CLI, schema, storage format, subprocess launch, or cache/session identity changed.
- Tests or test helpers changed in a way that may hide behavior.
- A changed file does not map to any known area.
