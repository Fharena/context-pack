---
name: context-pack
description: Build and maintain a repo-local context library for coding agents. Use when initializing project memory, creating task-specific context packs, preparing code review context, checkpointing handoff state, reducing token use before broad repo reading, refreshing context indexes, or continuing work across Codex, Claude, Cursor, or other agent sessions.
---

# Context Pack

Use this skill to keep a project-local context library and generate small task-specific context packs before reading broadly. Prefer deterministic script commands for factual repo state; use model judgment only for semantic summaries, contracts, failure modes, and decisions.

## Core Principle

Treat context docs as a routing layer, not source of truth. A context pack should answer:

- What should be read first?
- Which contracts and failure modes matter?
- Which tests are relevant?
- Is the context stale relative to git state?

Always verify behavior in source code before editing or reviewing.

## Bundled Engine

Run the stdlib-only engine from this skill folder:

```bash
python scripts/context_pack.py <command>
```

If used from the plugin root, the wrapper also works:

```bash
python scripts/context_pack.py <command>
```

## Commands

### Initialize a repo

Use when the project does not have `.codex/context` yet:

```bash
python scripts/context_pack.py init
```

This creates:

- `.codex/context/manifest.json`
- `.codex/context/INDEX.md`
- `.codex/context/REVIEW.md`
- `.codex/context/CONTRACTS.md`
- `.codex/context/AREAS/overview.md`
- `.codex/handoff/CURRENT.md`
- `.codex/handoff/LOG.md`
- `.codex/handoff/DECISIONS.md`

It also adds local/generated ignores for `.codex/packs/`, `.codex/context/tmp/`, and `.codex/handoff/LOCAL.md`, then appends context-pack rules to `AGENTS.md` unless `--no-agent-doc` is provided.

### Checkpoint after work

Run after meaningful edits, tests, or review:

```bash
python scripts/context_pack.py checkpoint --pack
```

This updates the fingerprint in `CURRENT.md`, appends `LOG.md`, and optionally generates `.codex/packs/CONTEXT_PACK.md` from changed files.

### Build a work pack

Run before broad repo reading:

```bash
python scripts/context_pack.py pack --task "serve-model startup bug"
python scripts/context_pack.py pack --changed
```

Read `.codex/packs/CONTEXT_PACK.md` first, then inspect the listed area docs and source files.

### Build a review pack

Run before code review:

```bash
python scripts/context_pack.py review-pack
python scripts/context_pack.py review-pack --base main
```

Use the generated contracts, failure modes, tests, and changed-file list to focus the review.
Without `--base`, `review-pack` uses dirty files first, then the upstream branch when available. Use `--base` for committed branch reviews.

### Refresh routing docs

Run after editing `.codex/context/manifest.json`:

```bash
python scripts/context_pack.py refresh
```

Use `--mark-stale` when changed files mean selected area docs need a human/agent semantic update:

```bash
python scripts/context_pack.py refresh --mark-stale
```

### Validate setup

Run before handoff or commit:

```bash
python scripts/context_pack.py doctor
```

### Install git hooks

Use opt-in git hooks for deterministic automation:

```bash
python scripts/context_pack.py install-git-hooks --mode safe
```

Safe mode installs:

- `pre-commit`: run `doctor`.
- `post-checkout`: checkpoint after branch changes.
- `post-merge`: checkpoint after pulls/merges.

Aggressive mode also checkpoints after commits:

```bash
python scripts/context_pack.py install-git-hooks --mode aggressive
```

Remove hook blocks with:

```bash
python scripts/context_pack.py uninstall-git-hooks
```

## Updating Context

Use script-generated facts for:

- branch, HEAD, dirty file list, diff hash
- changed-file to area matching
- stale warnings
- generated pack contents

Use agent judgment for:

- adding or revising `AREAS/*.md`
- recording durable contracts
- identifying common failure modes
- adding decisions to `DECISIONS.md`

Keep `CURRENT.md` short. Move stable project knowledge into `.codex/context/AREAS/*.md`.

## Area Manifest

The engine uses `.codex/context/manifest.json`. Each area can include:

```json
{
  "doc": ".codex/context/AREAS/runtime.md",
  "description": "Runtime selection and telemetry scoring.",
  "paths": ["src/runtime/**", "tests/test_runtime*.py"],
  "start_files": ["src/runtime/tuner.py"],
  "tests": ["tests/test_runtime_tuner.py"],
  "keywords": ["runtime", "telemetry", "profile"],
  "contracts": ["Missing telemetry must not crash startup."],
  "failure_modes": ["Stale telemetry dominates new measurements."],
  "stale_if_paths": ["src/cli.py"]
}
```

Prefer a few high-value areas over one summary per folder.

## Operating Rules

- Before broad reading, generate or consult a context pack.
- After substantial file edits, run `checkpoint --pack`.
- For code review, run `review-pack` before reading surrounding files.
- Do not commit `.codex/packs/` or `.codex/handoff/LOCAL.md`.
- Treat stale packs and stale area docs as hints only.
- If a changed file maps to no area, inspect source and update the manifest or an area doc after the task.
- For committed branch reviews, prefer `review-pack --base <base-ref>`.
