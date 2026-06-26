---
id: installer-release
last_reviewed_head: 4cd7e6c6caf4
status: active
paths:
  - scripts/install_skill.py
  - scripts/install_plugin.py
  - README.md
  - README.ko.md
  - LICENSE
tests:
  - python -m unittest discover -s tests -v
  - plugin validation
  - skill validation
stale_if:
  - install paths change
  - marketplace policy changes
  - release checks change
---

# Installer Release

## Read When
- Changing installation scripts or release instructions.
- Preparing a local plugin/skill distribution.
- Updating README command examples.

## Start With
- `README.md`
- `README.ko.md`
- `scripts/install_skill.py`
- `scripts/install_plugin.py`

## Contracts
- Installers must not overwrite existing installs unless `--force` is explicit.
- The personal marketplace entry must include `policy.installation`, `policy.authentication`, and `category`.
- Release checks include unit tests, plugin validation, and skill validation.

## Common Failure Modes
- Marketplace path is correct but the copied plugin source is stale.
- README tells users to install a plugin without telling them the Codex add command.
- Korean README drifts from the English install or release flow.
- Installer overwrites a local user customization without `--force`.

## Expand Scope If
- Moving from local marketplace install to packaged release.
- Adding npm/pip distribution.
- Adding plugin-native hooks.

## Do Not Start With
- engine internals unless install commands fail
