# Changelog

All notable changes to Context Pack will be documented here.

## [0.1.1] - 2026-06-26

### Added

- Packaged Python CLI entry point for `pipx install git+https://github.com/Fharena/context-pack.git` and `context-pack ...` commands.
- First-run area inference for common source, tests, docs, and automation paths.
- CI coverage for editable package installation and CLI entry points.

### Changed

- Repositioned README around agent-first usage, target users, and comparison with `AGENTS.md`, `CLAUDE.md`, and editor rules.
- Replaced public validation examples that referenced maintainer-local absolute paths.
- Updated context routing docs to include package files and public validation checks.

## [0.1.0] - 2026-06-26

### Added

- Initial Codex plugin and `context-pack` skill.
- Stdlib-only deterministic engine for `init`, `checkpoint`, `pack`, `review-pack`, `refresh`, `doctor`, `gc`, and git hook installation.
- Repo-local context library under `.codex/context/`.
- Handoff checkpoint docs under `.codex/handoff/`.
- Generated task/review packs under `.codex/packs/`.
- Unit tests for initialization, dirty-file packs, task keyword packs, committed review packs, and git hook idempotency.
- English and Korean README files.
