# Release Guide

This project can be installed from GitHub today. Registry publishing is optional, but the release workflow keeps the package ready for PyPI and npm.

## Preflight

Run from a clean `main` checkout:

```bash
git status --short
python scripts/sync_packaged_assets.py --check
python -m unittest discover -s tests -v
python scripts/validate_packaged_cli.py
python -m json.tool plugins/context-pack/.codex-plugin/plugin.json
python -m json.tool .context-pack/manifest.json
python -m json.tool .agents/plugins/marketplace.json
python -m json.tool package.json
python -m pip install build twine
python -m build
python -m twine check dist/*
npm pack --dry-run
node bin/context-pack.js --help
```

## Version Bump

Update these files together:

```text
pyproject.toml
package.json
src/context_pack/__init__.py
plugins/context-pack/.codex-plugin/plugin.json
plugins/context-pack/skills/context-pack/scripts/context_pack.py
src/context_pack/bundled/context_pack.py
CHANGELOG.md
```

Then run `python scripts/sync_packaged_assets.py` so the packaged engine, skill instructions, agent metadata, and plugin manifest match their canonical sources.

Then verify version sync:

```bash
python -m unittest tests.test_context_pack.ContextPackTests.test_public_versions_stay_in_sync -v
```

## GitHub Release

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
gh release create vX.Y.Z --repo Fharena/context-pack --title "vX.Y.Z" --notes-file <notes.md>
```

The `Release` workflow runs when the GitHub release is published. It checks the tag against `pyproject.toml` and `package.json`, builds the Python wheel/sdist and npm tarball, verifies them, and uploads them as GitHub Release assets.

If a release already exists or the workflow needs to be retried:

```bash
gh workflow run release.yml --repo Fharena/context-pack -f tag=vX.Y.Z
```

Wait for both `CI` and `Release` workflows to pass before announcing.

## Optional Registry Automation

Registry publishing is intentionally opt-in. By default the release workflow only builds and uploads GitHub Release assets.

To publish on every GitHub release after trusted publishing is configured, add repository variables:

```text
PUBLISH_PYPI=true
PUBLISH_NPM=true
```

For a one-off manual publish through GitHub Actions:

```bash
gh workflow run release.yml --repo Fharena/context-pack \
  -f tag=vX.Y.Z \
  -f publish_pypi=true \
  -f publish_npm=true
```

## PyPI

Preferred path: configure PyPI Trusted Publishing for:

```text
owner: Fharena
repository: context-pack
workflow: release.yml
environment: pypi
package: context-pack
```

The workflow uses `pypa/gh-action-pypi-publish@release/v1` with `id-token: write`, so no PyPI token is needed after the publisher is configured.

Manual upload after preflight is still possible:

```bash
python -m twine upload dist/*
```

After publishing:

```bash
pipx install context-pack
context-pack --help
```

## npm

The scoped package must exist on npm before its trusted publisher can be attached. For the first release, sign in and publish the already validated tarball manually. Then configure npm Trusted Publishing with:

```text
package: @fharena/context-pack
organization/user: Fharena
repository: context-pack
workflow: release.yml
environment: npm
```

The workflow grants `id-token: write` and runs `npm publish --access public`. npm trusted publishing adds provenance automatically for supported packages.

Manual publish after preflight is still possible:

```bash
npm login
npm publish --access public
```

After publishing:

```bash
npx @fharena/context-pack --help
```

## Notes

- Do not publish registry packages before the GitHub release tag, `CI`, and `Release` are green.
- If publishing to registries, update README install snippets to prefer the registry path and keep the GitHub path as a fallback.
- `context-pack install-codex --activate` remains the recommended Codex path until plugin marketplace distribution is mature.
