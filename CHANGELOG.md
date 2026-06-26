# Changelog

All notable changes to Context Pack will be documented here.

## [0.1.4] - 2026-06-26

### Added

- `context-pack start` as the agent-first entrypoint: auto-initialize missing context docs, prepare task packs, prepare review packs, or route dirty-file work from one command.
- Tests for first-run `start`, task-based start packs, and changed-file start packs.

### Changed

- README, Korean README, Codex skill guidance, plugin metadata, and generated `AGENTS.md` rules now lead with `context-pack start` instead of requiring users or agents to pick lower-level commands first.

## [0.1.3] - 2026-06-26

### Changed

- `context-pack checkpoint` now writes ignored local checkpoint state by default, so proactive agent end-of-work checkpoints do not dirty tracked handoff files.
- Use `context-pack checkpoint --publish` to update tracked `.codex/handoff/CURRENT.md` and `LOG.md` for handoffs that should travel through git.
- Updated agent guidance, README docs, and demo GIF to clarify local automatic checkpoints versus published durable handoffs.

### Added

- Test coverage proving default checkpoints keep a clean git worktree while `--publish` intentionally updates tracked handoff docs.

## [0.1.2] - 2026-06-26

### Added

- `context-pack status` for context health, likely areas, stale warnings, and next actions.
- `context-pack mark-reviewed` for closing stale warnings after source verification.
- Pack budget controls: `--max-areas`, `--max-read-first`, `--max-contracts`, and `--max-failure-modes`.

### Changed

- Packs now rank selected areas by relevance and move overflow context into `Read Later`.
- Packs now deduplicate similar contract and failure-mode bullets.
- `overview` is treated as fallback/related context instead of dominating packs through broad `.codex/context/**` matches.
- Skill and repo guidance now tell agents to use Context Pack proactively before broad reading, review, unfamiliar debugging, and handoff.

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
