# Context Pack

<p align="center">
  <strong>Version-aware context packs for Codex, Claude, Cursor, and coding agents.</strong>
</p>

<p align="center">
  <a href="https://github.com/Fharena/context-pack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Fharena/context-pack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/actions/workflows/release.yml"><img alt="Release workflow" src="https://github.com/Fharena/context-pack/actions/workflows/release.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/releases/tag/v0.2.2"><img alt="Release" src="https://img.shields.io/github/v/release/Fharena/context-pack?display_name=tag"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

<p align="center">
  <a href="README.ko.md">한국어</a> ·
  <a href="#install">Install</a> ·
  <a href="#basic-usage-flow">Usage</a> ·
  <a href="#terminal-demo">Terminal Demo</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="docs/RELEASE.md">Release Guide</a>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="Context Pack terminal demo" width="820">
</p>

Stop paying agents to rediscover your repo.

Context Pack keeps a small repo-local project library, checkpoints git state, and generates compact task-specific reading packs before an agent reads broadly. It is markdown-first, git-aware, stale-aware, and intentionally light: deterministic script first, semantic agent judgment second.

This gets more useful as coding agents move across local IDEs, cloud worktrees, hosted app sessions, and remote machines. When the workspace changes, the repo should carry the map.

## Who It Is For

Use Context Pack when you:

- move work between Codex, Claude, Cursor, cloud worktrees, local IDEs, or remote machines
- review branches where an agent should start from the risky files instead of the whole repo
- maintain a project where future AI contributors need a small, current map
- want markdown context that travels with git instead of living inside one vendor's memory system

Skip it for tiny throwaway repos, one-off prompts, or projects where a single short `AGENTS.md` is already enough.

## Why

Most AI coding waste starts before coding. The agent has to rediscover which files matter, which tests cover the change, which contracts must not break, and whether old notes are stale.

Context Pack turns that repeated search into a small project library:

- `.context-pack/INDEX.md` and `.context-pack/AREAS/*.md` are the project index.
- `.context-pack/CURRENT.md` is the current work state.
- `.context-pack/packs/CONTEXT_PACK.md` is the generated desk for the current task.

## Built For Multi-Session Agent Work

Modern agent work is no longer one local chat attached to one checkout. You might start in a local IDE, ask Codex to work in the app, run a cloud task, review from another machine, or hand a branch to a different agent.

Context Pack makes the repo carry enough context for that handoff:

- Which checkout and git state was last checkpointed
- Which areas own the changed files
- Which contracts and tests matter for review
- Which notes may be stale and need source verification
- Which generated/local files should not be trusted or committed

## Install

Fastest Codex path, from GitHub without cloning:

```bash
npx github:Fharena/context-pack install-codex --activate
```

This requires Node plus Python 3.11+ on `PATH`. If the Codex CLI is not on `PATH`, omit `--activate` and run the printed `codex plugin add ...` command later.

Then talk to your agent:

```text
Use $context-pack to set up this repo.
Use $context-pack to start work on this bug.
Use $context-pack to checkpoint this work.
```

The agent runs the engine, reads the generated pack, and continues from the focused context. In a context-enabled repo, the skill is also designed for proactive use: an agent should run `context-pack start` before broad reading, review, unfamiliar debugging, or handoff even when you did not name the tool.

If you already installed the CLI, update or install the Codex plugin with:

```bash
context-pack install-codex --activate
```

For repo setup with Claude, Cursor, other agents, or direct terminal use:

```bash
npx github:Fharena/context-pack setup
npx github:Fharena/context-pack start
npx github:Fharena/context-pack start --task "fix login timeout"
npx github:Fharena/context-pack start --review --base main
```

Prefer Python tooling or want a persistent CLI?

```bash
pipx install git+https://github.com/Fharena/context-pack.git
context-pack setup
```

For a one-command trial without installing the CLI permanently:

```bash
pipx run --spec git+https://github.com/Fharena/context-pack.git context-pack setup
```

The `npx` route is a thin wrapper over the same Python engine. It avoids asking Node-first users to install a Python package before they can try the tool.

Examples below use `context-pack` for readability. If you are staying on the GitHub `npx` path, replace `context-pack` with `npx github:Fharena/context-pack`.

Not sure what to run next? Run `context-pack` with no arguments to print the quickstart, or `context-pack --version` to confirm the installed version.

`setup` initializes the repo context library, handoff docs, `.gitignore` entries, and shared agent rules for `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules/context-pack.mdc`.

If you already have a context library and only want to refresh shared repo rules:

```bash
context-pack install-agent-docs
```

Both commands preserve existing text outside the managed Context Pack block. Use `setup --agent-docs none` when you only want the `.context-pack/` library, or `install-agent-docs --target claude` / `--target cursor` when you only want specific agent docs.

Already using an older `.codex/context` library? Run:

```bash
context-pack migrate
```

Context Pack still reads the legacy layout when `.context-pack/` is not present, but new setup uses the vendor-neutral `.context-pack/` directory.

## Local Install Options

These are mostly for contributors hacking on this repository. New users should start with the `pipx`, `npx`, or `install-codex` paths above.

Install from a clone as a local Codex plugin:

```powershell
python plugins/context-pack/scripts/context_pack.py install-codex --force --activate
```

Install only the skill:

```powershell
python scripts/install_skill.py
```

Run from source without installing anything:

```powershell
python plugins/context-pack/scripts/context_pack.py setup
python plugins/context-pack/scripts/context_pack.py start --review --base main
```

This repository also includes a repo-scoped Codex marketplace:

```text
.agents/plugins/marketplace.json
```

After cloning, you can add this repo as a local Codex plugin marketplace so Codex can discover the bundled plugin from the repo:

```bash
codex plugin marketplace add .
codex plugin add context-pack@context-pack
```

## Terminal Demo

```text
$ context-pack start --task "improve CLI onboarding" --max-areas 3 --max-read-first 8
Context Pack Start for /work/context-pack
Git: yes; branch: main; HEAD: 67f7355488c0
Context library: ok
Dirty files: 0; diff hash: clean

Generated work pack for task: .context-pack/packs/CONTEXT_PACK.md
Selected areas: installer-release, skill-plugin, engine
Scope reduction: start from 3 area(s) instead of scanning 82 repo file(s)

Read next:
- .context-pack/packs/CONTEXT_PACK.md
- .context-pack/AREAS/installer-release.md
- .context-pack/AREAS/skill-plugin.md
- .context-pack/AREAS/engine.md

$ Get-Content .context-pack/packs/CONTEXT_PACK.md -TotalCount 40
# Context Pack

Mode: work

## Scope Reduction
- Repo files considered: 82
- Primary areas selected: 3 of 5
- Read First entries: 5 (~6% of repo files)
- Changed files in scope: 0

## Selected Areas
- installer-release (score 68): changed files matched: CHANGELOG.md, README.ko.md, README.md (+5 more)
- skill-plugin (score 40): changed files matched: plugins/context-pack/.codex-plugin/plugin.json, plugins/context-pack/skills/context-pack/SKILL.md, plugins/context-pack/skills/context-pack/agents/openai.yaml (+1 more); task matched keywords: agent
- engine (score 34): changed files matched: plugins/context-pack/skills/context-pack/scripts/context_pack.py, src/context_pack/__init__.py, src/context_pack/bundled/context_pack.py (+1 more)

## Related Areas
- tests (score 14): changed files matched: plugins/context-pack/skills/context-pack/scripts/context_pack.py, tests/test_context_pack.py

## Read First
- .context-pack/AREAS/installer-release.md
- README.md
- README.ko.md
- CHANGELOG.md
- pyproject.toml

## Read Later
- .context-pack/AREAS/skill-plugin.md
- plugins/context-pack/skills/context-pack/SKILL.md
- .context-pack/AREAS/engine.md

## Contracts To Check
- The engine must remain stdlib-only so it can run from a skill, plugin, or copied checkout.
- ... more contract(s) omitted; inspect area docs if needed
```

The point is not to replace source code. The point is to make the agent start from the right shelf.

## Basic Usage Flow

For direct terminal use:

Before starting work:

```powershell
context-pack start --task "the bug or feature you are about to work on"
```

Before reviewing code:

```powershell
context-pack start --review --base main
```

When you only want a pack for current dirty or changed files:

```powershell
context-pack pack --changed
```

After meaningful work:

```powershell
context-pack checkpoint --pack
```

To validate setup:

```powershell
context-pack doctor
```

After verifying source against stale area docs:

```powershell
context-pack mark-reviewed runtime tests
```

If you installed the Codex plugin, you usually do not type these commands yourself. Ask the agent to use `$context-pack`, and the repo rules installed by `setup` tell agents to run the right command at task, review, debugging, and checkpoint boundaries.

## What It Does

| Feature | What it saves |
| --- | --- |
| `setup` | One-command repo onboarding: context library, handoff docs, `.gitignore`, shared agent rules, and doctor check |
| `start` | One-command first step: auto-init if needed and prepare a task, review, or changed-files pack |
| `install-codex` | Installs the Codex plugin and personal marketplace entry from a package or clone |
| `install-agent-docs` | Writes shared Context Pack rules to `AGENTS.md`, `CLAUDE.md`, and Cursor project rules |
| `init` | Creates a repo-local context library, handoff docs, and inferred source/test/doc areas |
| `migrate` | Copies legacy `.codex/context` and `.codex/handoff` docs into `.context-pack/` |
| `status` | Shows context health, likely areas, stale warnings, and next action |
| `checkpoint` | Records branch, HEAD, dirty files, and diff hash to ignored local state by default |
| `pack` / `pack --changed` | Builds a compact task-specific or changed-files reading pack with selected and related areas |
| `review-pack` | Builds a compact code-review pack from dirty files or `--base` |
| `mark-reviewed` | Marks verified area docs reviewed at the current HEAD |
| `doctor` | Checks whether the context library is usable; `doctor --fix` repairs missing setup files |
| `install-git-hooks` | Adds opt-in repo-local checkpoint automation |

## Agent-First UX

Tell the agent:

```text
Use $context-pack to set up Context Pack in this repo.
Use $context-pack to make a context pack for this bug.
Use $context-pack to review this branch against main.
Use $context-pack to checkpoint this work.
Initialize context-pack in this repo.
Build a review context pack for my changes.
Checkpoint this work for the next session.
```

The more important path is implicit:

- before broad repo reading: run `context-pack start --task "..."`
- when Context Pack is missing: run `context-pack setup`
- when setup looks broken: run `context-pack doctor --fix`
- before review: run `context-pack start --review --base <base-ref>` when a base is known
- during unfamiliar debugging: generate a task pack before opening many files
- after meaningful edits or review notes: run `checkpoint --pack` so the local agent state is resumable without dirtying git
- when a handoff should travel through git: run `checkpoint --publish --pack`
- after verifying changed source against area docs: run `mark-reviewed <area>` to close stale warnings

For teams or personal repos that move between Codex, Claude, and Cursor, run `context-pack install-agent-docs` once so each agent sees the same proactive rules at repo entry.

After initialization, agents should read:

1. `.context-pack/CURRENT.md`
2. `.context-pack/INDEX.md`
3. `.context-pack/packs/CONTEXT_PACK.md` when generated
4. Relevant `.context-pack/AREAS/*.md`
5. Actual source files

## Why Not Just AGENTS.md Or CLAUDE.md?

Use those files. Context Pack is not a replacement.

`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, and similar files are durable instruction layers: coding style, commands, policies, and project rules. Context Pack is the routing layer beside them:

- It snapshots branch, HEAD, dirty files, and diff hash.
- It maps changed files or a task prompt to the relevant area docs.
- It generates a temporary read-first pack for the current task or review.
- It warns when summaries may be stale.
- It keeps generated/local context out of git while tracking durable project memory.

So the agent reads the rule file for behavior, then reads Context Pack for where to look first.

`context-pack install-agent-docs` is the bridge between those layers: it writes the behavior rule into the agent-native files, while the generated packs and `.context-pack/` docs keep the dynamic routing state outside any single vendor memory system.

## How Context Pack Is Different

Context Pack overlaps with a few familiar ideas, but it is narrower on purpose:

| Alternative | Good at | Context Pack adds |
| --- | --- | --- |
| `AGENTS.md`, `CLAUDE.md`, editor rules | Durable behavior instructions | Version-aware routing: branch, HEAD, dirty files, stale area docs, and task/review packs |
| Vendor memory or project knowledge | Agent-specific recall | Markdown context that travels with git across Codex, Claude, Cursor, cloud worktrees, and local machines |
| RAG or vector databases | Semantic retrieval across large corpora | Deterministic, reviewable routing with no service, index server, embeddings, or hidden ranking state |
| Context dumpers | Fast bundle of files | Area ownership, Read First / Read Later ordering, contracts, failure modes, and stale warnings |

The bet is not "more memory." The bet is that most agent work starts better when the repo tells the agent where to look first, what may be stale, and which checks matter.

## Area Selection And Monorepos

Context Pack's first pass is intentionally simple and inspectable:

- `setup` / `init` infer initial areas from common source, test, docs, and automation paths.
- Changed files are matched against area path globs.
- Task text can add keyword score to areas.
- Packs split context into selected areas, related areas, Read First, and Read Later.
- Stale warnings compare reviewed area docs with the current git state.

That makes the tool predictable, but not magical. For a complex monorepo, the best results come from editing `.context-pack/manifest.json` and `.context-pack/AREAS/*.md` so area boundaries match how the project is really owned. If an area is too broad, split it. If a generated pack is noisy, lower `--max-areas` / `--max-read-first`, tighten path globs, and mark verified areas with `mark-reviewed`.

The current scoring is a routing heuristic, not a semantic understanding engine. That is deliberate: every selected file and warning should be explainable in plain Markdown before an agent spends tokens on source code.

## Current Scope

Context Pack is a small, repo-local tool, not a hosted platform. It is best suited today for small to medium projects, agent-heavy personal repos, open-source repos that want AI contributor orientation, and teams moving work across local and cloud agent sessions.

The public install paths currently run from GitHub through `pipx` or `npx`. Registry publishing is opt-in, but the release workflow already builds and verifies Python wheel/sdist artifacts and the npm tarball, then uploads them to the GitHub Release. CI covers Windows and Ubuntu on Python 3.11/3.12, plus package, Codex plugin, Node wrapper, and npm tarball smoke paths.

## How It Works

Context Pack is not a vector database and not a generic memory bank. It is a version-aware routing layer.

The script handles deterministic work:

- git branch, HEAD, dirty files, diff hash
- one-command `setup` for repo onboarding and shared agent rules
- Codex plugin installation from an installed package or source checkout
- GitHub `npx` wrapper for developers who do not start from Python tooling
- shared repo-rule installation for `AGENTS.md`, `CLAUDE.md`, and Cursor project rules
- one-command `start` routing for first-run init, task packs, review packs, and dirty-file packs
- first-run inference for common source, test, docs, and automation areas
- changed-file path matching and task-keyword scoring for area matching
- compact context pack assembly with primary and related areas
- scope-reduction metrics that show how much reading is avoided
- Read First / Read Later splitting
- contract and failure-mode deduplication
- stale warnings
- context health status and reviewed-state updates
- `doctor --fix` repair for missing setup files
- generated file cleanup
- optional git hook installation

The agent can then improve semantic context over time:

- area summaries
- project contracts
- common failure modes
- durable decisions

You do not need to hand-write a full taxonomy to start. `init` creates useful defaults from the files already in the repo; semantic refinement is the compounding layer.

## Git Policy

Track:

- `.context-pack/manifest.json`
- `.context-pack/INDEX.md`
- `.context-pack/REVIEW.md`
- `.context-pack/CONTRACTS.md`
- `.context-pack/AREAS/*.md`
- `.context-pack/CURRENT.md`
- `.context-pack/LOG.md`
- `.context-pack/DECISIONS.md`

Ignore:

- `.context-pack/packs/`
- `.context-pack/tmp/`
- `.context-pack/local/LOCAL.md`

Automatic agent checkpoints write to `.context-pack/local/LOCAL.md` and `.context-pack/packs/` by default, so normal end-of-work checkpointing should not dirty tracked files. Use `context-pack checkpoint --publish --pack` when the handoff itself is part of the work you want to commit.

## Automation

Optional safe git hooks. You do not need this to use Context Pack.

The primary automation model is agent behavior: the installed skill plus repo `AGENTS.md`, `CLAUDE.md`, or Cursor rules tell agents to use Context Pack proactively at task, review, debugging, and handoff boundaries. `checkpoint` writes ignored local state by default, so agents can use it at the end of a work unit without dirtying tracked handoff docs. Git hooks are only a mechanical backup for git boundaries such as checkout, merge, and commit.

```powershell
context-pack install-git-hooks --mode safe
```

Safe mode installs:

- `pre-commit`: run `doctor`
- `post-checkout`: checkpoint after branch changes
- `post-merge`: checkpoint after pulls/merges

Aggressive mode also checkpoints after commits:

```powershell
context-pack install-git-hooks --mode aggressive
```

Remove hook blocks:

```powershell
context-pack uninstall-git-hooks
```

## Development

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Validate public metadata and CLI packaging:

```powershell
python -m json.tool plugins/context-pack/.codex-plugin/plugin.json
python -m json.tool .agents/plugins/marketplace.json
python -m pip install -e .
context-pack --help
context-pack doctor --fix --help
node bin/context-pack.js --help
python -m pip install build twine
python -m build
python -m twine check dist/*
npm pack --dry-run
python scripts/validate_packaged_cli.py
```

GitHub Actions runs stdlib unit tests, JSON validation, packaged CLI checks, Python wheel/sdist checks, and Node/npm wrapper checks on Windows and Ubuntu for Python 3.11 and 3.12. The release workflow builds GitHub Release assets from the tag and can optionally publish to PyPI/npm after trusted publishing is configured.

## Release

See [CHANGELOG.md](CHANGELOG.md) and [docs/RELEASE.md](docs/RELEASE.md). Current release: [v0.2.2](https://github.com/Fharena/context-pack/releases/tag/v0.2.2).
