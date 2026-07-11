# Context Pack

<p align="center">
  <strong>A repo-local context router for coding agents.</strong><br>
  Start from the smallest useful map instead of rediscovering the whole repository.
</p>

<p align="center">
  <a href="https://github.com/Fharena/context-pack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Fharena/context-pack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/Fharena/context-pack?display_name=tag"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg"></a>
  <a href="README.ko.md"><img alt="한국어" src="https://img.shields.io/badge/docs-한국어-blue.svg"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Fharena/context-pack/main/assets/demo.gif" alt="Context Pack terminal demo" width="820">
</p>

Coding agents are good at reading code. The waste comes from making each new session rediscover the same architecture, relevant files, tests, and unfinished state.

Context Pack keeps a small versioned project map in the repo and generates a focused pack with bounded source evidence for the current task. It works with Codex, Claude Code, Cursor, and other agents that follow repository instructions.

## Who It Is For

Context Pack is most useful when:

- work moves between local and cloud sessions, machines, worktrees, or agents;
- a repository is large enough that broad orientation is expensive;
- reviews repeatedly need the same contracts, tests, and failure modes;
- maintainers want handoff state to travel with git.

It intentionally gets out of the way for tiny repositories, pure Q&A, and obvious one-file edits.

## Install

### Codex

Install the plugin from GitHub:

```bash
pipx run --spec git+https://github.com/Fharena/context-pack.git context-pack install-codex --activate
```

Start a new Codex task after installation. The skill will use Context Pack automatically when orientation is worthwhile.

### Claude Code, Cursor, Or Other Agents

Install the CLI:

```bash
pipx install git+https://github.com/Fharena/context-pack.git
```

Then explicitly persist the shared context library and agent rules in a repo:

```bash
context-pack setup --dry-run
context-pack setup
```

`setup` preserves existing text outside managed blocks in `AGENTS.md`, `CLAUDE.md`, and Cursor project rules.
By default it always manages `AGENTS.md` and refreshes Claude/Cursor files only when those agent files already exist. Use `--agent-docs all` to create all three explicitly.

| Surface | v0.5.0 validation |
| --- | --- |
| Codex | Skill/plugin install, packaged CLI, and real CLI A/B runs |
| Claude Code | `CLAUDE.md` generation and preservation tests; runtime CLI not available in this release environment |
| Cursor | `.cursor/rules/*.mdc` generation and preservation tests; runtime CLI not available in this release environment |

## Normal UX

The user speaks normally. The agent chooses the deterministic operation.

| User request | Agent operation |
| --- | --- |
| “Fix the login timeout.” | `context-pack start --agent --task "fix login timeout"` |
| “Why are tests failing?” | `context-pack start --agent --task "tests failing"` |
| “Review this branch.” | `context-pack start --agent --review` |
| “Leave this easy to resume.” | `context-pack checkpoint --pack --quiet` |

The CLI does not need to classify review or handoff prose. The agent already understands that intent and passes an explicit flag.

## Safe First Run

`start` and `setup` are different operations.

On an unconfigured Git repo, the installed skill uses normal targeted code search. It does not invoke Context Pack or create files implicitly.

The CLI still offers an explicit transient preview through `context-pack start --task "..."`. That preview:

- infers source, tests, docs, automation, and assets in memory;
- prints compact, bounded source evidence inline without writing it to the repository;
- does not create `.context-pack/`, `AGENTS.md`, or `.gitignore`;
- skips pack generation when the repo has 24 files or fewer and broad reading is likely cheaper.

Transient routing is useful for evaluating setup, but the v0.5.0 A/B found it unreliable as an automatic default. Only explicit `setup` creates the maintained context library that the skill can trust and reuse.

## Persistent Library

After setup, the versioned library is intentionally small:

```text
.context-pack/
  manifest.json
  INDEX.md
  CURRENT.md
  DECISIONS.md
  LOG.md
  AREAS/
    source.md
    tests.md
    ...
```

- `INDEX.md` routes work to areas.
- `AREAS/*.md` stores compact contracts, failure modes, and starting files.
- `CURRENT.md` stores the shared handoff fingerprint and next actions.
- `DECISIONS.md` is for durable direction changes only.
- `LOG.md` keeps only the 30 most recent published checkpoints; older entries remain in git history.

Generated packs and local checkpoints stay ignored:

```text
.context-pack/packs/
.context-pack/local/
.context-pack/tmp/
```

## Core Commands

```bash
# Persistent install or repair
context-pack setup --dry-run
context-pack setup
context-pack doctor

# Task and review orientation
context-pack start --agent --task "fix stale detection bug"
context-pack start --agent --review

# Handoff
context-pack checkpoint --pack
context-pack checkpoint --publish --pack
```

`--publish` is deliberate: it updates tracked handoff files so they can travel through git. The default checkpoint remains local and ignored.

## Routing Model

Context Pack is not RAG and does not use embeddings or a vector database. Routing is deterministic:

1. Git identifies changed files and the current branch/HEAD.
2. Paths map files to configured areas.
3. Task words are matched against area names, keywords, configured search terms, paths, and concise routing notes.
4. Area roles such as `source`, `tests`, and `automation` provide generic fallbacks even when a project uses custom area names.
5. Agent mode searches strong configured symbols first and returns at most two bounded, line-numbered source regions.
6. Contracts, failure modes, and one verification command are ranked only after routing; they do not select unrelated areas.

Area notes remain hints. Embedded `Evidence` is extracted from the current source and can be edited directly when the root cause is visible.

## Maintenance Controls

- Review routing suppresses Context Pack metadata when real product files changed.
- `doctor` warns when an area glob covers most of the repository.
- Area notes carry stale fingerprints and review status.
- Checkpoint logs are bounded instead of append-only forever.
- Text-budget scanning is opt-in through `measure` or `--text-budget`; normal `start` does not read every text file for a statistic.
- Agent output is capped, omits duplicate preambles, and avoids duplicate packaged source copies.
- Optional `safe` Git hooks use the exact local Python interpreter and warn without blocking commits.

## Evidence And Limits

Context Pack has an actual Codex CLI A/B harness, not only a `chars/4` routing proxy. v0.5.0 tested maintained context on four BrowserQuest workflows with the same model, prompts, pinned source revision, and isolated working-tree engine.

| Task | Baseline correct | Maintained correct | Median total input | Median uncached input | Median time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Precise bug (3/arm) | 3/3 | 3/3 | 29.4% less | 41.6% less | 7.5% slower |
| Domain-routed bug (5/arm) | 5/5 | 5/5 | 37.5% less | 44.1% less | 11.6% faster |
| Branch review (3/arm) | 3/3 | 3/3 | 16.5% less | 44.1% less | 9.9% slower |
| Session continuation (3/arm) | 3/3 | 3/3 | 21.3% less | 48.7% less | 3.2% faster |

Maintained Context Pack and baseline were both correct in **14/14** runs. The experimental transient policy was correct in **11/14**; on the domain and continuation tasks it used 14.1% and 41.3% more median total input. That negative result is why unconfigured repositories now use normal search by default.

These are small, author-run samples on one pinned legacy JavaScript repository with seeded defects and maintained symbols. They do not prove universal token, billing, latency, or patch-quality gains. Total input is cumulative across turns; uncached input is not an invoice. See [docs/BENCHMARKS.md](docs/BENCHMARKS.md) and the [v0.5.0 aggregate files](docs/benchmarks/codex-ab-v050-summary.md).

The older deterministic benchmark still checks routing and clone replay. Its `chars/4` figures are search-scope estimates, not actual model usage.

Context Pack also cannot remove curation cost completely. Its value depends on useful area boundaries and concise notes. The product goal is to remain harmless when those notes are neglected: warn, rotate, prune generated state, and fall back to source verification.

## Development

```bash
python scripts/sync_packaged_assets.py --check
python -m unittest discover -s tests -v
python scripts/validate_packaged_cli.py
```

The engine is stdlib-only. Pillow is optional and used only to regenerate `assets/demo.gif`.

See [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and [docs/RELEASE.md](docs/RELEASE.md).

## License

[MIT](LICENSE)
