# Context Index

Use this file as a router. It should reduce reading, not replace source verification.

## Areas

### distribution
- Doc: `.context-pack/AREAS/installer-release.md`
- Read when: Python/npm packaging, synchronized resources, CI, release workflow, and install smoke tests.
- Start with:
  - `MANIFEST.in`
  - `pyproject.toml`
  - `package.json`
  - `scripts/sync_packaged_assets.py`
  - `scripts/validate_packaged_cli.py`
  - `.github/workflows/ci.yml`
  - `.github/workflows/release.yml`
- Matches:
  - `scripts/install_skill.py`
  - `scripts/install_plugin.py`
  - `scripts/sync_packaged_assets.py`
  - `scripts/validate_packaged_cli.py`
  - `.github/workflows/**`
  - `.agents/plugins/marketplace.json`
  - `MANIFEST.in`
  - `pyproject.toml`
  - `package.json`
  - `bin/**`
  - `src/context_pack/__init__.py`
  - `src/context_pack/bundled/SKILL.md`
  - `src/context_pack/bundled/openai.yaml`
  - `src/context_pack/bundled/plugin.json`
- Tests:
  - `tests/test_context_pack.py`
  - `scripts/validate_packaged_cli.py`
- Verify:
  - `python scripts/sync_packaged_assets.py --check`
  - `python scripts/validate_packaged_cli.py`
  - `python -m build`
  - `python -m twine check dist/*`
  - `npm pack --dry-run`

### docs-adoption
- Doc: `.context-pack/AREAS/docs-adoption.md`
- Read when: Public positioning, onboarding, benchmark evidence, demo, changelog, and release notes.
- Start with:
  - `README.md`
  - `README.ko.md`
  - `docs/BENCHMARKS.md`
  - `docs/benchmarks/codex-ab-v050-summary.md`
  - `scripts/benchmark_codex_ab.py`
  - `scripts/benchmark_context_pack.py`
- Matches:
  - `README.md`
  - `README.ko.md`
  - `CHANGELOG.md`
  - `CONTRIBUTING.md`
  - `assets/demo.gif`
  - `docs/BENCHMARKS.md`
  - `docs/BENCHMARKS.ko.md`
  - `docs/RELEASE.md`
  - `docs/RELEASE.ko.md`
  - `docs/benchmarks/**`
  - `docs/releases/**`
  - `scripts/benchmark_codex_ab.py`
  - `scripts/benchmark_context_pack.py`
- Tests:
  - `tests/test_benchmarks.py`
- Verify:
  - `python scripts/benchmark_context_pack.py --public --fail-on-weak`

### engine
- Doc: `.context-pack/AREAS/engine.md`
- Read when: Deterministic Git snapshot, compact evidence routing, packs, checkpoints, doctor, installers, and hooks.
- Start with:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `tests/test_context_pack.py`
- Matches:
  - `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
  - `plugins/context-pack/scripts/context_pack.py`
  - `src/context_pack/cli.py`
  - `src/context_pack/bundled/context_pack.py`
- Tests:
  - `tests/test_context_pack.py`
- Verify:
  - `python -m unittest discover -s tests -v`

### overview
- Doc: `.context-pack/AREAS/overview.md`
- Read when: Project orientation, shared handoff state, and repository-level agent rules.
- Start with:
  - `.context-pack/CURRENT.md`
  - `.context-pack/INDEX.md`
  - `README.md`
- Matches:
  - `.context-pack/**`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.cursor/rules/**`
  - `SECURITY.md`
  - `LICENSE`

### skill-plugin
- Doc: `.context-pack/AREAS/skill-plugin.md`
- Read when: Codex skill instructions, agent metadata, and plugin-facing natural-language behavior.
- Start with:
  - `plugins/context-pack/skills/context-pack/SKILL.md`
  - `plugins/context-pack/skills/context-pack/agents/openai.yaml`
  - `plugins/context-pack/.codex-plugin/plugin.json`
- Matches:
  - `plugins/context-pack/.codex-plugin/plugin.json`
  - `plugins/context-pack/skills/context-pack/SKILL.md`
  - `plugins/context-pack/skills/context-pack/agents/openai.yaml`
- Tests:
  - `tests/test_context_pack.py`
- Verify:
  - `python scripts/sync_packaged_assets.py --check`
  - `python -m unittest discover -s tests -v`

### tests
- Doc: `.context-pack/AREAS/tests.md`
- Read when: Unit and integration coverage for engine behavior and release-critical flows.
- Start with:
  - `tests/test_context_pack.py`
  - `tests/test_benchmarks.py`
- Matches:
  - `tests/test_context_pack.py`
  - `tests/test_benchmarks.py`
- Tests:
  - `tests/test_context_pack.py`
  - `tests/test_benchmarks.py`
- Verify:
  - `python -m unittest discover -s tests -v`

## Generated Packs
- `.context-pack/packs/CONTEXT_PACK.md` is generated and should not be committed.
