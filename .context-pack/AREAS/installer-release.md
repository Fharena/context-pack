---
id: distribution
status: active
paths:
  - pyproject.toml
  - package.json
  - scripts/sync_packaged_assets.py
  - scripts/validate_packaged_cli.py
  - .github/workflows/**
tests:
  - python scripts/sync_packaged_assets.py --check
  - python scripts/validate_packaged_cli.py
last_reviewed_head: b440399b85ee
---

# Distribution

## Read When
- Changing Python/npm packaging, install-codex, synchronized resources, CI, or release workflows.
- Preparing a version bump or release artifact.

## Start With
- `MANIFEST.in`
- `pyproject.toml`
- `package.json`
- `scripts/sync_packaged_assets.py`
- `scripts/validate_packaged_cli.py`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

## Contracts
- Canonical engine, skill, agent metadata, and plugin manifest are synchronized before validation.
- The npm wrapper delegates to the bundled Python engine.
- Packaged validation covers transient start, setup, task, review, checkpoint, and install-codex.
- Source distributions include the development harness and pass the same test suite after extraction.
- CI reinstalls the built wheel before final CLI and plugin-install checks.
- Registry publishing remains opt-in until trusted publishing is configured.

## Common Failure Modes
- A wheel or npm tarball contains stale engine or skill resources.
- Package versions disagree across Python, npm, plugin, and engine metadata.
- Source-checkout tests pass while an installed entrypoint fails.
- Release assets are built from a revision other than the tag.
