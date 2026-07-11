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
  - tests/test_context_pack.py
  - scripts/validate_packaged_cli.py
verify:
  - python scripts/sync_packaged_assets.py --check
  - python scripts/validate_packaged_cli.py
  - python -m build
  - python -m twine check dist/*
  - npm pack --dry-run
last_reviewed_head: c18bd9bcc69b
---

# Distribution

## Read When
- Changing Python/npm packaging, install-codex, synchronized resources, CI, or release workflows.

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
- Packaged validation covers transient preview, setup, task, review, continuation, checkpoint, and install-codex.
- Release assets are built from the exact tag after version and test checks.
- Registry publication remains opt-in until PyPI and npm trusted publishers are configured on their registry sites.
- `pypi` and `npm` GitHub environments provide OIDC boundaries; no registry token is committed.

## Common Failure Modes
- A wheel or npm tarball contains stale engine or skill resources.
- Package versions disagree across Python, npm, plugin, and engine metadata.
- Source-checkout tests pass while installed entrypoints fail.
- Registry publication is claimed even though only GitHub release assets exist.
- Release assets are built from a revision other than the tag.
