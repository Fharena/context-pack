# Changelog

All notable changes to Context Pack will be documented here.

## [0.1.0] - 2026-06-26

### Added

- Initial Codex plugin and `context-pack` skill.
- Stdlib-only deterministic engine for `init`, `checkpoint`, `pack`, `review-pack`, `refresh`, `doctor`, `gc`, and git hook installation.
- Repo-local context library under `.codex/context/`.
- Handoff checkpoint docs under `.codex/handoff/`.
- Generated task/review packs under `.codex/packs/`.
- Unit tests for initialization, dirty-file packs, task keyword packs, committed review packs, and git hook idempotency.
- English and Korean README files.
