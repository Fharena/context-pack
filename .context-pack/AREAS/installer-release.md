---
id: installer-release
last_reviewed_head: 47823b3d3170
status: active
paths:
  - scripts/install_skill.py
  - scripts/install_plugin.py
  - .agents/plugins/marketplace.json
  - .github/**
  - pyproject.toml
  - package.json
  - bin/**
  - src/context_pack/**
  - assets/**
  - docs/**
  - CHANGELOG.md
  - CONTRIBUTING.md
  - README.md
  - README.ko.md
  - LICENSE
  - SECURITY.md
  - .gitignore
  - .gitattributes
tests:
  - python -m unittest discover -s tests -v
  - python -m json.tool plugins/context-pack/.codex-plugin/plugin.json
  - python -m json.tool .agents/plugins/marketplace.json
  - python -m build
  - python -m twine check dist/*
  - npm pack --dry-run
stale_if:
  - install paths change
  - marketplace policy changes
  - release checks change
---

# Installer Release

## Read When
- Changing installation scripts or release instructions.
- Documenting shared agent rules for Codex, Claude, Cursor, or mixed-agent repos.
- Preparing a local plugin/skill distribution.
- Updating README command examples.
- Improving clone-free or one-command first-run onboarding.
- Updating npm/npx wrapper metadata or package contents.
- Updating PyPI/npm release readiness or registry publishing instructions.

## Start With
- `README.md`
- `README.ko.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `package.json`
- `bin/context-pack.js`
- `docs/RELEASE.md`
- `docs/RELEASE.ko.md`
- `src/context_pack/cli.py`
- `assets/demo.gif`
- `scripts/install_skill.py`
- `scripts/install_plugin.py`
- `scripts/validate_packaged_cli.py`
- `.agents/plugins/marketplace.json`
- `.github/workflows/ci.yml`

## Contracts
- Installers must not overwrite existing installs unless `--force` is explicit.
- Codex plugin install must work from a package install without requiring a repo clone.
- The personal marketplace entry must include `policy.installation`, `policy.authentication`, and `category`.
- Release checks include unit tests, plugin validation, and skill validation.
- GitHub Actions should run stdlib unit tests without relying on local Codex validator paths.
- Packaged CLI behavior should match the bundled skill engine.
- Node/npx wrapper should delegate to the bundled Python engine without duplicating business logic.
- Node/npx wrapper should be smoke-tested for first-time `setup` and packaged `install-codex`, not only `--help`.
- Python wheel/sdist builds must pass `twine check` before registry publishing.
- Release workflow must build from the requested tag, verify Python/npm version sync, and upload Python wheel/sdist plus npm tarball assets to the matching GitHub Release.
- PyPI/npm publishing must stay opt-in unless trusted publishing is explicitly enabled through repository variables or manual workflow inputs.
- README should distinguish Codex plugin installation from shared repo-rule installation.
- README should lead direct terminal users to `context-pack setup` before lower-level commands.
- README should show `doctor --fix` as the recovery path for broken or partial setup.
- Contributor validation should expose the packaged npx smoke path through `scripts/validate_packaged_cli.py`.

## Common Failure Modes
- Marketplace path is correct but the copied plugin source is stale.
- README tells users to install a plugin without telling them the Codex add command.
- Packaged CLI can start projects but cannot install the Codex skill/plugin experience.
- Korean README drifts from the English install or release flow.
- Demo GIF no longer matches the command output or product positioning.
- CI depends on local-only validator paths from one developer machine.
- npm package metadata drifts from Python/plugin versions or omits the bundled engine.
- README leads with an `npx` command path that is not covered by packaged CLI smoke tests.
- PyPI metadata starts warning or rendering poorly because build/twine checks are not in CI.
- Release workflow builds from `main` instead of the release tag, producing assets that do not match the tag.
- Registry publishing runs automatically before PyPI/npm trusted publishing has been configured.
- Marketplace JSON points at a plugin path that does not exist in the repo.
- Installer overwrites a local user customization without `--force`.
- README teaches lower-level commands before the one-command `start` path.
- README teaches `init` plus `install-agent-docs` before the one-command `setup` path.
- README tells users to reinstall from scratch instead of repairing with `doctor --fix`.
- README makes `install-agent-docs` sound required for single-agent Codex use.

## Expand Scope If
- Moving from local marketplace install to packaged release.
- Adding npm/pip distribution.
- Changing package metadata or CLI entry points.
- Adding plugin-native hooks.

## Do Not Start With
- engine internals unless install commands fail
