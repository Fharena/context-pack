# Context Index

Use this file as a router. It should reduce reading, not replace source verification.

## Areas

### engine
- Doc: `.codex/context/AREAS/engine.md`
- Read when: Deterministic context-pack engine: git snapshot, area matching, pack generation, doctor, and git hooks.
- Start with:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `tests/test_context_pack.py`
- Matches:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `plugins/context-pack/scripts/context_pack.py`
- Tests:
  - `tests/test_context_pack.py`

### installer-release
- Doc: `.codex/context/AREAS/installer-release.md`
- Read when: Install and release workflow for local skill/plugin distribution.
- Start with:
  - `README.md`
  - `README.ko.md`
  - `CHANGELOG.md`
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
- Matches:
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
  - `.agents/plugins/marketplace.json`
  - `.github/**`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `README.md`
  - `README.ko.md`
  - `LICENSE`
  - `SECURITY.md`
  - `.gitignore`
- Tests:
  - `python -m unittest discover -s tests -v`
  - `python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack`
  - `python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack`

### overview
- Doc: `.codex/context/AREAS/overview.md`
- Read when: Default project orientation and safe starting point.
- Start with:
  - `README.md`
  - `README.ko.md`
  - `AGENTS.md`
  - `CHANGELOG.md`
  - `.codex/context/INDEX.md`
  - `.codex/handoff/CURRENT.md`
- Matches:
  - `README.md`
  - `README.ko.md`
  - `AGENTS.md`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `SECURITY.md`
  - `CLAUDE.md`
  - `codex.md`
  - `.agents/plugins/marketplace.json`
  - `.codex/context/**`

### skill-plugin
- Doc: `.codex/context/AREAS/skill-plugin.md`
- Read when: Codex skill instructions, plugin manifest metadata, and agent-facing UX.
- Start with:
  - `plugins/context-pack/skills/context-pack/SKILL.md`
  - `plugins/context-pack/.codex-plugin/plugin.json`
  - `plugins/context-pack/skills/context-pack/agents/openai.yaml`
- Matches:
  - `plugins/context-pack/.codex-plugin/plugin.json`
  - `plugins/context-pack/skills/context-pack/SKILL.md`
  - `plugins/context-pack/skills/context-pack/agents/openai.yaml`
- Tests:
  - `python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack`
  - `python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack`

### tests
- Doc: `.codex/context/AREAS/tests.md`
- Read when: Unit tests for the deterministic engine and release-critical flows.
- Start with:
  - `tests/test_context_pack.py`
- Matches:
  - `tests/test_context_pack.py`
- Tests:
  - `python -m unittest discover -s tests -v`

## Generated Packs
- `.codex/packs/CONTEXT_PACK.md` is generated and should not be committed.
