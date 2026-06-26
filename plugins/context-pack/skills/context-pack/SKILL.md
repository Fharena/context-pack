---
name: context-pack
description: Prepare focused repo context for coding agents. Use proactively when starting substantial coding work, debugging unfamiliar code, reviewing changes, entering a repo with existing context docs, needing to reduce token use before broad reading, or ending an agent work unit that should be resumable. Also use when the user asks to start project memory, initialize context docs, prepare a task or review context pack, checkpoint work for another session, refresh context indexes, or continue work across Codex, Claude, Cursor, cloud worktrees, remote machines, or other agent sessions.
---

# Context Pack

Use this skill as the agent-facing workflow for Context Pack. The user should not need to know script paths or internal commands. Run the bundled engine yourself, read the generated pack, then continue the user's actual coding, review, or handoff task.

Do not wait for the user to name Context Pack when the situation clearly calls for it. Use it proactively before broad repo reading, before review, during unfamiliar debugging, and at the end of a meaningful agent work unit.

## Promise

Start from the right shelf instead of rereading the repo.

Context Pack keeps a repo-local context library and generates small task-specific packs:

- `.codex/context/` -> stable project index and area docs
- `.codex/handoff/` -> current checkout/work state
- `.codex/packs/CONTEXT_PACK.md` -> generated reading pack for this task

Treat these docs as routing hints, not source of truth. Always verify behavior in source code before editing or reviewing.

## How To Respond To Users

When the user says something like:

- "Use context-pack here"
- "Initialize this repo"
- "Prepare review context"
- "Make a context pack for this bug"
- "Checkpoint this work"
- "Continue from the project memory"

do the work. Do not stop at instructions.

Also use this skill without explicit naming when:

- entering a repo that already has `.codex/context/manifest.json`
- starting a task that may touch multiple files or unknown ownership
- reviewing dirty files, a branch, or a PR
- debugging a failure in an unfamiliar area
- about to read broadly because the right files are unclear
- finishing meaningful edits, tests, or review notes that another session may need

Report back in user terms:

- what pack/checkpoint was created
- selected areas
- read-first files
- stale warnings, if any
- what you will inspect next

## Engine Location

Run from this skill folder:

```bash
python scripts/context_pack.py <command>
```

If operating from the plugin root, the wrapper also works:

```bash
python scripts/context_pack.py <command>
```

Use the script for factual repo state. Use model judgment only for semantic summaries, contracts, failure modes, and decisions.

## Workflows

### Fast Path

Use this first when entering a repo or starting a non-trivial task. It initializes missing context docs, chooses a task/review/changed-files pack when enough signal exists, and prints what to read next.

```bash
python scripts/context_pack.py start --task "<short task description>"
```

For reviews:

```bash
python scripts/context_pack.py start --review --base <base-ref>
```

With no task, use:

```bash
python scripts/context_pack.py start
```

Then read `.codex/packs/CONTEXT_PACK.md` if it was generated. If no pack was generated, follow the command's next action.

### Initialize Project Memory

Use when `.codex/context/manifest.json` is missing or the user asks to set up Context Pack.

Prefer the fast path above unless the user specifically asked for initialization only.

1. Run:

   ```bash
   python scripts/context_pack.py init
   ```

2. Run:

   ```bash
   python scripts/context_pack.py doctor
   ```

3. If setup succeeds, summarize the created files and suggest the next natural-language prompt, such as "Build a review context pack for this branch."

Do not install git hooks during init unless the user explicitly asks for automation.

### Prepare A Task Or Debugging Pack

Use before broad repo reading for a feature, bug, or debugging task. If `.codex/context/manifest.json` exists and the task is non-trivial, prefer generating a pack even when the user did not explicitly ask for Context Pack.

1. Run:

   ```bash
   python scripts/context_pack.py start --task "<short task description>"
   ```

2. Read `.codex/packs/CONTEXT_PACK.md`.
3. Read only the listed area docs and source files first.
4. Continue the user's task from that focused context.

If the user has already changed files and no task is clear, run:

```bash
python scripts/context_pack.py start --changed
```

### Prepare Code Review Context

Use when reviewing local changes, a branch, or a PR.

1. Prefer an explicit base when available:

   ```bash
   python scripts/context_pack.py start --review --base <base-ref>
   ```

2. If no base is known, run:

   ```bash
   python scripts/context_pack.py start --review
   ```

3. Read `.codex/packs/CONTEXT_PACK.md`.
4. Review changed files against the listed contracts, failure modes, and tests before widening scope.

### Checkpoint Work

Use after meaningful edits, tests, review, or when the user asks to hand off work. This writes ignored local state by default, so proactive agent checkpoints do not dirty tracked handoff files.

```bash
python scripts/context_pack.py checkpoint --pack
```

Then report:

- current branch and HEAD
- dirty file count
- generated pack path
- next files/areas another agent should read

When the handoff should be committed and shared through git, publish it explicitly:

```bash
python scripts/context_pack.py checkpoint --publish --pack
```

Do not commit tracked handoff updates unless the user's requested git workflow includes them.

### Check Context Health

Use when deciding whether to generate a pack, when stale warnings feel noisy, or when entering an existing repo:

```bash
python scripts/context_pack.py status
```

If an area doc has been verified against current source, mark it reviewed:

```bash
python scripts/context_pack.py mark-reviewed <area-id>
```

### Refresh Context Routing

Use after `.codex/context/manifest.json` or area ownership changes.

```bash
python scripts/context_pack.py refresh
```

If changed files suggest area docs are stale:

```bash
python scripts/context_pack.py refresh --mark-stale
```

After refresh, inspect updated `INDEX.md`, `REVIEW.md`, and `CONTRACTS.md` if relevant.

### Optional Git Hook Automation

Git hooks are optional. They are not required to use Context Pack.

Only install them if the user explicitly asks for automatic checkpointing near git work boundaries:

```bash
python scripts/context_pack.py install-git-hooks --mode safe
```

Safe mode installs:

- `pre-commit`: run `doctor`
- `post-checkout`: checkpoint after branch changes
- `post-merge`: checkpoint after pulls/merges

Remove hooks with:

```bash
python scripts/context_pack.py uninstall-git-hooks
```

## Area Manifest

The engine uses `.codex/context/manifest.json`. Each area may include:

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

Prefer a few high-value responsibility areas over one summary per folder.

## Operating Rules

- Generate or consult a context pack before broad reading.
- Read generated packs as routing hints, not source truth.
- Verify stale warnings against source before acting.
- Keep `CURRENT.md` short; move durable knowledge into `AREAS/*.md`.
- Do not commit `.codex/packs/` or `.codex/handoff/LOCAL.md`.
- If a changed file maps to no area, inspect source and update the manifest or area docs after the task.
- For committed branch reviews, prefer `start --review --base <base-ref>`.
