# Context Pack

<p align="center">
  <strong>Version-aware context packs for Codex, Claude, Cursor, and coding agents.</strong>
</p>

<p align="center">
  <a href="https://github.com/Fharena/context-pack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Fharena/context-pack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/releases/tag/v0.1.0"><img alt="Release" src="https://img.shields.io/github/v/release/Fharena/context-pack?display_name=tag"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

<p align="center">
  <a href="README.ko.md">한국어</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#terminal-demo">Terminal Demo</a> ·
  <a href="#how-it-works">How It Works</a>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="Context Pack terminal demo" width="820">
</p>

Stop paying agents to rediscover your repo.

Context Pack keeps a small repo-local project library, checkpoints git state, and generates task-specific reading packs before an agent reads broadly. It is markdown-first, git-aware, stale-aware, and intentionally light: deterministic script first, semantic agent judgment second.

This gets more useful as coding agents move across local IDEs, cloud worktrees, hosted app sessions, and remote machines. When the workspace changes, the repo should carry the map.

## Why

Most AI coding waste starts before coding. The agent has to rediscover which files matter, which tests cover the change, which contracts must not break, and whether old notes are stale.

Context Pack turns that repeated search into a small project library:

- `.codex/context/` is the project index.
- `.codex/handoff/` is the current work state.
- `.codex/packs/CONTEXT_PACK.md` is the generated desk for the current task.

## Built For Multi-Session Agent Work

Modern agent work is no longer one local chat attached to one checkout. You might start in a local IDE, ask Codex to work in the app, run a cloud task, review from another machine, or hand a branch to a different agent.

Context Pack makes the repo carry enough context for that handoff:

- Which checkout and git state was last checkpointed
- Which areas own the changed files
- Which contracts and tests matter for review
- Which notes may be stale and need source verification
- Which generated/local files should not be trusted or committed

## Quick Start

Use directly from the repo:

```powershell
python plugins/context-pack/scripts/context_pack.py init
python plugins/context-pack/scripts/context_pack.py pack --task "startup bug"
python plugins/context-pack/scripts/context_pack.py review-pack --base main
python plugins/context-pack/scripts/context_pack.py checkpoint --pack
python plugins/context-pack/scripts/context_pack.py doctor
```

Install as a Codex skill:

```powershell
python scripts/install_skill.py
```

Install as a local Codex plugin:

```powershell
python scripts/install_plugin.py
codex plugin add context-pack@personal
```

This repository also includes a repo-scoped Codex marketplace:

```text
.agents/plugins/marketplace.json
```

After cloning, you can add this repo as a Codex plugin marketplace so Codex can discover the bundled plugin from the repo.

## Terminal Demo

```text
$ python plugins/context-pack/scripts/context_pack.py review-pack --base main
Context pack written to .codex/packs/CONTEXT_PACK.md
Selected areas: engine, installer-release, tests

$ Get-Content .codex/packs/CONTEXT_PACK.md -TotalCount 40
# Context Pack

Mode: review

## Selected Areas
- engine
- installer-release
- tests

## Read First
- .codex/context/AREAS/engine.md
- plugins/context-pack/skills/context-pack/scripts/context_pack.py
- tests/test_context_pack.py

## Contracts To Check
- The engine must remain stdlib-only.
- Generated packs must stay under .codex/packs/.
- Hook install must preserve unrelated hook contents.

## Tests
- tests/test_context_pack.py
```

The point is not to replace source code. The point is to make the agent start from the right shelf.

## What It Does

| Feature | What it saves |
| --- | --- |
| `init` | Creates a repo-local context library and handoff docs |
| `checkpoint` | Records branch, HEAD, dirty files, and diff hash |
| `pack` | Builds a task-specific reading pack |
| `review-pack` | Builds a code-review pack from dirty files or `--base` |
| `doctor` | Checks whether the context library is usable |
| `install-git-hooks` | Adds opt-in repo-local checkpoint automation |

## Agent UX

Tell the agent:

```text
Initialize context-pack in this repo.
Build a review context pack for my changes.
Checkpoint this work for the next session.
```

After initialization, agents should read:

1. `.codex/handoff/CURRENT.md`
2. `.codex/context/INDEX.md`
3. `.codex/packs/CONTEXT_PACK.md` when generated
4. Relevant `.codex/context/AREAS/*.md`
5. Actual source files

## How It Works

Context Pack is not a vector database and not a generic memory bank. It is a version-aware routing layer.

The script handles deterministic work:

- git branch, HEAD, dirty files, diff hash
- changed-file to area matching
- context pack assembly
- stale warnings
- generated file cleanup
- optional git hook installation

The agent handles semantic work:

- area summaries
- project contracts
- common failure modes
- durable decisions

## Git Policy

Track:

- `.codex/context/manifest.json`
- `.codex/context/INDEX.md`
- `.codex/context/REVIEW.md`
- `.codex/context/CONTRACTS.md`
- `.codex/context/AREAS/*.md`
- `.codex/handoff/CURRENT.md`
- `.codex/handoff/LOG.md`
- `.codex/handoff/DECISIONS.md`

Ignore:

- `.codex/packs/`
- `.codex/context/tmp/`
- `.codex/handoff/LOCAL.md`

## Automation

Optional safe git hooks:

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode safe
```

Safe mode installs:

- `pre-commit`: run `doctor`
- `post-checkout`: checkpoint after branch changes
- `post-merge`: checkpoint after pulls/merges

Aggressive mode also checkpoints after commits:

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode aggressive
```

Remove hook blocks:

```powershell
python plugins/context-pack/scripts/context_pack.py uninstall-git-hooks
```

## Development

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Validate the plugin and skill locally:

```powershell
python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack
python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack
```

GitHub Actions runs stdlib unit tests and JSON validation on Windows and Ubuntu for Python 3.11 and 3.12.

## Release

See [CHANGELOG.md](CHANGELOG.md). Current release: [v0.1.0](https://github.com/Fharena/context-pack/releases/tag/v0.1.0).
