# Changelog

All notable changes to Context Pack will be documented here.

## [Unreleased]

## [0.3.0] - 2026-07-11

### Added

- Added transient first-run packs that live under Git metadata or the system temp directory without creating repository files.
- Added generic area roles, bounded start-file inference, broad-glob diagnostics, bounded checkpoint logs, and package-resource sync checks.
- Added cross-platform integration tests that execute installed Git hooks and cover Unicode branch and renamed file paths.
- Added `scripts/benchmark_codex_ab.py` for parallel, isolated Codex CLI A/B trials with reported total/cached/uncached token usage, latency, and patch checks.
- Added `Search First` terms and scopes so task packs route agents to bounded matches instead of whole globs or large files.

### Changed

- Made `setup` the only operation that persists `.context-pack/` and agent instruction files; small unconfigured repos now skip unnecessary pack generation.
- Simplified the agent contract: the agent interprets natural-language intent and calls explicit task, review, or checkpoint operations.
- Replaced benchmark-specific routing buckets with generic source, tests, docs, assets, and automation behavior.
- Made normal `start` avoid repository-wide text-budget scans; estimates are now opt-in through `measure` or `--text-budget`.
- Reduced the default CLI help and public documentation to the primary workflow while retaining compatibility commands.
- Moved packaged skill, agent metadata, and plugin metadata to synchronized resource files instead of embedded hand-maintained strings.
- Updated the public benchmark to 10 passing repositories and a matching fresh-clone handoff signature.
- Interactive `start` now prints the complete pack inline; agents no longer need a second tool turn to reopen the saved pack.
- Transient first runs are inline and file-free instead of writing under `.git`, which can be blocked by agent sandboxes.
- The skill now tries one precise search before transient routing in unconfigured repos and skips Context Pack when that search is enough.
- Reframed benchmark evidence around actual Codex CLI usage: current five-run evidence shows 14.2% lower median uncached input but 17.2% higher median total input, so no universal total-token claim is made.

### Fixed

- Preserved absolute Unix paths in generated hooks, invoked the exact installation interpreter, and made safe hooks fail open.
- Decoded Git output with explicit UTF-8 and surrogate handling, including NUL-delimited status and filename parsing.
- Excluded Context Pack's own generated metadata from review routing when product files are also changed.

### Removed

- Removed the CLI's bilingual lifecycle phrase classifier, generated `REVIEW.md` and `CONTRACTS.md` duplicates, unbounded validation proxy artifacts, and internal beta/audit documents.

## [0.2.20] - 2026-06-30

### Added

- Added `scripts/benchmark_context_pack.py`, a reproducible benchmark harness for public-repo first-run routing, text-budget ratios, slow-measure flags, and synthetic handoff replay.
- Added benchmark result artifacts under `docs/benchmarks/` and refreshed English/Korean benchmark docs with 10 public scenarios plus handoff replay.

### Changed

- Improved first-run inference for Go repositories by detecting root `*.go`, top-level Go package directories, and `*_test.go` files.
- Improved first-run inference for Rust filter/search tasks by adding Rust crate start paths and Rust-specific source keywords.
- Skips known binary media/archive/font suffixes before text-budget reads and checks file size before reading, reducing cold-start work on media-heavy repos.
- Refreshed README benchmark positioning to distinguish deterministic routing/token-budget evidence from independent-agent patch quality.

## [0.2.19] - 2026-06-30

### Changed

- Improved first-run inference for web game and client/server JavaScript repos by recognizing `client/js`, `server/js`, and `shared/js`, splitting `sprites`, `maps`, and `media` from generic assets, and avoiding vendored `client/js/lib` in initial read-first globs.
- Added an A/B orientation benchmark on `mozilla/BrowserQuest` showing task-specific first reads at ~16-17% of broad repo text for mobile controls, sprite asset loading, and websocket connection prompts.

## [0.2.18] - 2026-06-30

### Changed

- Refined public docs and GitHub templates to use the current `context-pack` CLI, vendor-neutral `.context-pack/` paths, and agent-first wording that frames packs as focused triage instead of a manual chore.
- Slimmed the Codex skill and packaged plugin prompts around natural-language agent behavior, explicit skip cases, and concise routing commands instead of a full CLI manual.
- Updated generated `AGENTS.md`, `CLAUDE.md`, and Cursor rules to frame Context Pack as quiet orientation for natural-language tasks, with explicit skip cases for pure Q&A and tiny obvious edits.
- Reworked the no-argument CLI quickstart so normal agent prompts appear before direct CLI commands.
- Refreshed the README demo GIF around natural-language agent prompts, quiet orientation, skip cases, review routing, and local handoff checkpoints.
- Clarified the installed agent contract: users speak normally, agents orient before broad reading, read the generated pack, continue the actual task, and checkpoint meaningful work without making users manage packs manually.
- Made `context-pack start` useful for continuation sessions with no clear task by printing `CURRENT.md` and `INDEX.md` as read-next files even when no focused pack is generated.
- Added a small `start --task` intent guard so obvious review, continuation, and handoff phrases route to review mode, current/index orientation, or checkpoint guidance instead of noisy work packs.
- Added lightweight Korean natural-phrase handling for bug-fix, branch-review, and resume-later requests.
- Extended packaged CLI validation to smoke-test natural-language bug-fix and branch-review routing from the installed npm entrypoint.
- Paired `source` with `tests` for natural test-failure/debugging prompts such as "why are tests failing" so agents do not start from test files alone.
- Extended packaged CLI validation to cover natural handoff wording and prove `checkpoint --pack` keeps tracked files unchanged.
- Clarified `start --task` output for continuation and handoff wording so it no longer prints a generic no-dirty-files reason in dirty repos.
- Extended packaged CLI validation to cover natural branch-review routing on a clean committed feature branch with an inferred `main` base.
- Broadened natural review intent handling for softer prompts like "look over my changes" and "변경사항 봐줘" while keeping meta/documentation tasks out of review mode.
- Broadened natural handoff intent handling for short wrap-up prompts like "I'm done for now", "wrap this up", and "작업 끝났어" while avoiding false positives such as "done button".
- Broadened Korean bug routing for prompts like "버그 잡아줘" and "문제 해결해줘" while avoiding meta/documentation phrases such as "버그 리포트 문서 정리".
- Broadened English bug routing for broken/not-working prompts like "login is broken" and "checkout doesn't work" while avoiding loose matches such as "broken link report".
- Routed CI/build failure prompts like "CI is red" and "build failed" to automation/source/tests while avoiding badge/docs false positives.
- Inferred top-level Python package directories such as `httpx/` as source areas, improving first-run routing for repos that do not use `src/`.
- Added public beta dogfood benchmarks, launch copy, and a Codex skill audit for release readiness.

## [0.2.17] - 2026-06-27

### Changed

- Refreshed the README demo GIF to show the current first-run flow: read-only `measure`, explainable source/tests routing, setup dry-run, generated packs, and clean local checkpoints.

## [0.2.16] - 2026-06-27

### Changed

- `context-pack measure` and `context-pack start` now print why each selected or related area was chosen, making first-run routing easier to inspect before an agent reads files.

## [0.2.15] - 2026-06-27

### Changed

- Generic code tasks such as `fix login timeout` now route first-run inferred context to `source` and `tests` when no more specific area matches, instead of falling back to overview-only context.

## [0.2.14] - 2026-06-27

### Changed

- `context-pack measure` now infers source/test/docs/automation areas in memory when a repo has not been set up yet, so users can preview context savings before writing `.context-pack/` files.

### Fixed

- Scope-reduction file percentages are now capped at 100% for tiny repos where Read First entries include directories or missing pre-setup docs.

## [0.2.13] - 2026-06-27

### Added

- Added `context-pack measure`, a read-only proof command that previews selected areas, scope reduction, and approximate text budget without writing a generated pack.

## [0.2.12] - 2026-06-27

### Fixed

- Task keyword scoring now ignores common stop words so phrases like `and`, `the`, or `with` do not select unrelated areas or make generated packs noisy.

### Changed

- First-run inferred docs areas now include usage/adoption keywords so public onboarding and adoption tasks route to documentation context more reliably.

## [0.2.11] - 2026-06-27

### Changed

- Refreshed the terminal demo GIF to show the current setup dry-run, setup, start, text-budget, and checkpoint flow.
- Switched README demo images to a package-safe GitHub raw URL so registry pages do not rely on bundled relative assets.

## [0.2.10] - 2026-06-27

### Added

- `context-pack start` now prints the generated pack's approximate text-budget summary in the terminal, so the first-run output shows context savings before opening the pack.

## [0.2.9] - 2026-06-27

### Added

- Generated context packs now include approximate Read First and repo text-budget estimates so users can see the initial context-size reduction, with an explicit chars/4 caveat.

## [0.2.8] - 2026-06-27

### Changed

- `context-pack setup` and `init` now preserve existing curated manifests by default; first-run area inference remains automatic, and `--infer-areas` / `--no-infer-areas` make area inference explicit when needed.

## [0.2.7] - 2026-06-27

### Changed

- `context-pack setup --dry-run` now reports more precise setup actions, including preserved files, `.gitignore` appends, and managed agent-doc block refreshes.
- Generated `AGENTS.md` and `CLAUDE.md` no longer cause an otherwise empty repo to infer a separate docs area on the next setup run.

## [0.2.6] - 2026-06-27

### Changed

- Agent-facing skill and plugin prompts now teach previewable setup with `setup --dry-run`, and this repository now dogfoods shared `AGENTS.md`, `CLAUDE.md`, and Cursor rules that use the `context-pack start` fast path.

## [0.2.5] - 2026-06-27

### Changed

- The no-argument quickstart now shows `context-pack setup --dry-run` before setup, and setup dry runs now print an apply command that preserves selected setup options.

## [0.2.4] - 2026-06-27

### Added

- Added `context-pack setup --dry-run` so first-time users can preview setup file, agent-doc, and git-hook changes without writing to the repo.

## [0.2.3] - 2026-06-27

### Added

- Added a `Release` GitHub Actions workflow that builds GitHub Release assets from a tag, verifies Python/npm versions, uploads Python wheel/sdist and npm tarball assets, and can optionally publish to PyPI/npm through trusted publishing.
- Added test coverage and a local validation script proving the Node/npx wrapper can run first-time `setup` and `install-codex`, not just `--help`.
- Added a no-argument quickstart and `--version` flag so `context-pack` and the Node/npx wrapper handle first-run inspection without argparse errors.

### Changed

- Updated CI to current major versions of the official checkout/setup actions and disabled implicit package-manager cache setup for the Node wrapper checks.
- README and Korean README now lead with the shorter GitHub `npx` install path for Codex and direct repo setup, with `pipx` documented as the persistent Python CLI path.

## [0.2.2] - 2026-06-27

### Added

- Added English and Korean release guides for GitHub, PyPI, and npm publishing.
- CI now builds Python sdist/wheel artifacts and runs `twine check` before npm tarball validation.

### Changed

- Modernized Python package license metadata to SPDX-style `license = "MIT"` with explicit license files.

## [0.2.1] - 2026-06-27

### Added

- `status` and `doctor --strict` now detect stale shared `.context-pack/CURRENT.md` fingerprints when the recorded branch, dirty diff hash, or material committed files no longer match the current checkout.

### Fixed

- Avoids noisy handoff stale warnings after a handoff-only publish commit, so tracked `CURRENT.md` can be committed without creating an endless stale loop.

## [0.2.0] - 2026-06-27

### Changed

- Switched the default repo context library from Codex-branded `.codex/context` and `.codex/handoff` paths to vendor-neutral `.context-pack/`.
- Updated README, Korean README, generated agent rules, and the Codex skill docs to describe `.context-pack/` as the shared multi-agent context library.
- Tightened the English README onboarding flow to match the Korean README positioning.
- Made `pack --changed` visible in the feature tables.
- Reframed source-run commands as contributor-oriented local install options.
- Added README positioning against repo rules, vendor memory, RAG, and context dumpers.
- Documented area selection heuristics, monorepo tuning, and current scoring limits.
- Clarified the current project scope, GitHub-first install paths, and CI coverage.

### Added

- Added `context-pack migrate` to copy legacy `.codex/context` and `.codex/handoff` docs into `.context-pack/` while rewriting internal path references.

## [0.1.10] - 2026-06-26

### Added

- npm package metadata and a `bin/context-pack.js` wrapper so developers can run Context Pack through Node tooling.
- README and Korean README now show `npx github:Fharena/context-pack setup` as a Python-light onboarding path.
- Node wrapper fallback skips Python candidates that are present but older than Python 3.11.
- Tests for the Node wrapper, Python-version fallback, and npm package version/bin metadata.

### Changed

- Release validation docs now include `node bin/context-pack.js --help` and `npm pack --dry-run`.

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
