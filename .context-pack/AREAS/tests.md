---
id: tests
status: active
paths:
  - tests/test_context_pack.py
tests:
  - python -m unittest discover -s tests -v
---

# Tests

## Read When
- Changing engine behavior or investigating a release regression.

## Start With
- `tests/test_context_pack.py`
- `scripts/validate_packaged_cli.py` for installed-package behavior

## Contracts
- Tests use real temporary Git repositories and command entrypoints.
- Hook coverage executes the installed hook and checks safe failure behavior.
- Unicode branch, filename, and rename cases stay covered.
- Resource sync and packaged CLI validation are release gates.

## Common Failure Modes
- Tests inspect generated hook text but never execute it.
- Windows-only fixtures hide Unix path breakage.
- ASCII-only fixtures hide Korean path decoding failures.
- Direct imports pass while wheel/npm entrypoints fail.
