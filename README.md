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

On an unconfigured Git repo, `start` runs in transient mode:

- infers source, tests, docs, automation, and assets in memory;
- prints compact, bounded source evidence inline without writing it to the repository;
- does not create `.context-pack/`, `AGENTS.md`, or `.gitignore`;
- skips pack generation when the repo has 24 files or fewer and broad reading is likely cheaper.

The skill first tries a targeted search in unconfigured repos and uses transient routing only when the task remains broad. Only explicit `setup` creates persistent repository files.

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

Context Pack has an actual Codex CLI A/B harness, not only a `chars/4` routing proxy. In the v0.4.0 five-run BrowserQuest zoning benchmark, baseline and evidence-first curated Context Pack both produced the correct minimal patch in 5/5 runs.

| Median | Baseline | Curated Context Pack | Change |
| --- | ---: | ---: | ---: |
| Total input tokens | 111,828 | 68,075 | 39.1% less |
| Uncached input tokens | 20,948 | 6,905 | 67.0% less |
| Commands | 4 | 5 | 25.0% more |
| Tool output chars | 47,809 | 4,298 | 91.0% less |
| Duration | 38.2s | 43.7s | 14.3% slower |
| Total-input range | 101,287-247,516 | 53,486-82,548 | lower and tighter |

The largest single tool output was 1,048,576 characters for baseline and 3,364 for curated. Token and tool-output reductions did not produce a latency reduction in this batch. This is evidence for one maintained area on one seeded JavaScript bug, not a universal billing, latency, or productivity claim. Total input is cumulative across model turns, and curated context includes task-relevant symbols, contracts, and a verification command. See [docs/BENCHMARKS.md](docs/BENCHMARKS.md) and the [machine-readable v0.4.0 result](docs/benchmarks/codex-ab-zoning-evidence.json).

The previous search-only v0.3.0 result used 17.2% more median total input despite lowering uncached input. That failure drove evidence-first retrieval, compact agent output, and the benchmark PATH isolation used here.

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
