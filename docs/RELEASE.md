# Release Guide

This project can be installed from GitHub today. Registry publishing is optional, but these checks keep the package ready for PyPI and npm.

## Preflight

Run from a clean `main` checkout:

```bash
git status --short
context-pack status
python -m unittest discover -s tests -v
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
README.md
README.ko.md
CHANGELOG.md
```

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

Wait for GitHub Actions to pass before announcing.

## PyPI

First-time publish needs either a PyPI API token or Trusted Publishing configured for this repository.

Manual upload after preflight:

```bash
python -m twine upload dist/*
```

After publishing:

```bash
pipx install context-pack
context-pack --help
```

## npm

First-time publish needs an npm account with access to the `@fharena` scope.

Manual publish after preflight:

```bash
npm login
npm publish --access public
```

After publishing:

```bash
npx @fharena/context-pack --help
```

## Notes

- Do not publish registry packages before the GitHub release tag and CI are green.
- If publishing to registries, update README install snippets to prefer the registry path and keep the GitHub path as a fallback.
- `context-pack install-codex --activate` remains the recommended Codex path until plugin marketplace distribution is mature.
