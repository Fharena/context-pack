# Context Index

Use this file as a router. It should reduce reading, not replace source verification.

## Areas

### engine
- Doc: `.context-pack/AREAS/engine.md`
- Read when: Deterministic context-pack engine: git snapshot, start routing, area matching, pack generation, doctor, and git hooks.
- Start with:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `src/context_pack/cli.py`
  - `tests/test_context_pack.py`
- Matches:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `plugins/context-pack/scripts/context_pack.py`
  - `src/context_pack/**`
- Tests:
  - `tests/test_context_pack.py`

### installer-release
- Doc: `.context-pack/AREAS/installer-release.md`
- Read when: Install and release workflow for local skill/plugin distribution.
- Start with:
  - `README.md`
  - `README.ko.md`
  - `CHANGELOG.md`
  - `package.json`
  - `bin/context-pack.js`
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
- Matches:
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
  - `.agents/plugins/marketplace.json`
  - `.github/**`
  - `pyproject.toml`
  - `package.json`
  - `bin/**`
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
- Tests:
  - `python -m unittest discover -s tests -v`
  - `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
  - `python -m json.tool .agents/plugins/marketplace.json`
  - `python -m pip install -e .`
  - `context-pack --help`
  - `node bin/context-pack.js --help`
  - `npm pack --dry-run`
  - `context-pack setup --repo <tmp> --quiet`
  - `context-pack doctor --repo <tmp> --fix --quiet`
  - `context-pack status --quiet`
  - `context-pack start --task "agent-first CLI UX" --quiet`
  - `context-pack start --review --base HEAD~1 --quiet`
  - `context-pack install-codex --target <tmp>/plugins/context-pack --marketplace <tmp>/.agents/plugins/marketplace.json --quiet`
  - `context-pack install-agent-docs --repo <tmp> --quiet`
  - `context-pack checkpoint --pack --quiet does not dirty tracked files`

### overview
- Doc: `.context-pack/AREAS/overview.md`
- Read when: Default project orientation and safe starting point.
- Start with:
  - `README.md`
  - `README.ko.md`
  - `AGENTS.md`
  - `CHANGELOG.md`
  - `.context-pack/INDEX.md`
  - `.context-pack/CURRENT.md`
- Matches:
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
  - `.context-pack/**`

### skill-plugin
- Doc: `.context-pack/AREAS/skill-plugin.md`
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
  - `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
  - `python -m unittest discover -s tests -v`

### tests
- Doc: `.context-pack/AREAS/tests.md`
- Read when: Unit tests for the deterministic engine and release-critical flows.
- Start with:
  - `tests/test_context_pack.py`
- Matches:
  - `tests/test_context_pack.py`
- Tests:
  - `python -m unittest discover -s tests -v`

## Generated Packs
- `.context-pack/packs/CONTEXT_PACK.md` is generated and should not be committed.
