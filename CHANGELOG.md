# Changelog

All notable changes to Context Pack will be documented here.

## [0.1.9] - 2026-06-26

### Added

- `context-pack doctor --fix` to repair missing Context Pack setup files before validating the repo.
- `doctor --fix --agent-docs none|agents|claude|cursor|all` to control whether repair also restores shared agent docs.
- Tests for doctor repair on an empty repo, agent-doc-free repair, and no implicit git hook installation.

### Changed

- README, Korean README, Codex skill guidance, packaged skill synthesis, and plugin metadata now present doctor as both a validation and repair path.

## [0.1.8] - 2026-06-26

### Added

- `context-pack setup` as the one-command repo onboarding path: initialize context docs, handoff docs, `.gitignore`, shared agent docs, and run the same health checks.
- `setup --agent-docs none|agents|claude|cursor|all` and `setup --git-hooks off|safe|aggressive` for explicit setup-time choices.
- Tests for default setup, skipped agent docs, and safe git hook installation through setup.

### Changed

- README, Korean README, Codex skill guidance, packaged skill synthesis, and plugin metadata now lead with `setup` for first-time repo onboarding.

## [0.1.7] - 2026-06-26

### Added

- `context-pack install-agent-docs` to install shared Context Pack rules for `AGENTS.md`, `CLAUDE.md`, and Cursor project rules.
- Tests proving shared agent-doc installation is targetable, idempotent, and preserves existing user text outside the managed marker block.

### Changed

- README, Korean README, Codex skill guidance, packaged skill synthesis, and plugin metadata now position Context Pack as a multi-agent repo-rule layer instead of a Codex-only workflow.

## [0.1.6] - 2026-06-26

### Added

- Generated packs now include a `Scope Reduction` section showing repo files considered, selected areas, Read First entries, and changed files in scope.
- `context-pack start` output now shows a scope-reduction summary when a pack is generated.

### Changed

- README and Korean README demos now show the scope-reduction evidence users see on first run.

## [0.1.5] - 2026-06-26

### Added

- `context-pack install-codex` installs the Codex plugin and personal marketplace entry from either a source checkout or an installed package.
- `install-codex --activate` can run `codex plugin add context-pack@personal` after installation.
- Packaged install fallback can synthesize a valid plugin from the bundled engine when the source plugin tree is not present.

### Changed

- README and Korean README now lead with a clone-free Codex install path using `pipx run --spec git+https://github.com/Fharena/context-pack.git context-pack install-codex --activate`.

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
