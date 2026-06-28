---
name: context-pack
description: Prepare focused repo context for coding agents. Use for natural coding, review, debugging, or handoff requests when the agent would otherwise read broadly or lose session context. Skip for tiny obvious edits, pure Q&A, or tasks where the relevant file is already known.
---

# Context Pack

Context Pack is an agent behavior, not a command the user should have to remember.

When a user says things like "fix this bug", "review this branch", "why are tests failing?", or "I need to continue this later", use Context Pack to orient before broad repo reading, then continue the actual task. The generated docs are routing hints, not source of truth; verify behavior in source before editing or reviewing.

## Core Loop

1. Decide whether orientation is worth it.
2. Run the bundled engine from this skill folder:

   ```bash
   python scripts/context_pack.py <command>
   ```

3. Read `.context-pack/packs/CONTEXT_PACK.md` when generated.
4. Read only the listed area docs and source files first.
5. Continue the user's coding, review, debugging, or handoff task.

Report briefly. Usually one sentence is enough: selected areas, stale warning if any, and what you will inspect next. Only include scope-reduction or text-budget numbers when the user asks for proof, you ran `measure`, or the numbers materially explain the next step.

## When To Use

| Situation | Action |
| --- | --- |
| Context Pack is missing and the user wants repo memory/setup | `setup --dry-run`, then `setup` if setup was requested |
| Starting non-trivial coding/debugging | `start --task "<short task>"` |
| Reviewing a branch/PR/dirty files | `start --review`; add `--base <base-ref>` when known. Without a base, Context Pack tries upstream/common default branches |
| Changed files are the only signal | `start --changed` |
| User asks for proof before writing packs | `measure --task "<short task>"` |
| Setup looks broken or incomplete | `doctor --fix` |
| Meaningful work ended or handoff is requested | `checkpoint --pack` |
| Handoff must travel through git | `checkpoint --publish --pack` |

## When To Skip

- The user asks a pure question that does not need repo orientation.
- The change is a tiny, obvious single-file edit.
- The relevant file and test are already clear from the conversation.
- A fresh generated pack already matches the current task and git state.
- Running the tool would be more expensive than directly answering.

If you skip it, just proceed. Do not apologize or explain unless the user asked why.

## Setup Behavior

For first-time setup, preview writes first:

```bash
python scripts/context_pack.py setup --dry-run
```

If the user explicitly asked to configure or install Context Pack, apply setup:

```bash
python scripts/context_pack.py setup
```

This creates `.context-pack/`, ignored generated/local paths, and shared agent rules for `AGENTS.md`, `CLAUDE.md`, and Cursor rules. Preserve user text outside managed blocks. Do not install git hooks unless the user explicitly asks for git-boundary automation.

For legacy repos, migrate only when needed:

```bash
python scripts/context_pack.py migrate
```

## Task And Review Behavior

For normal coding/debugging:

```bash
python scripts/context_pack.py start --task "<short task>"
```

For review:

```bash
python scripts/context_pack.py start --review
```

Add `--base <base-ref>` when the review base is known; otherwise review mode tries upstream/common default branches and uses the first diff it finds.

After running `start`, read the generated pack if present. Treat stale warnings as prompts to verify source, not as facts.

## Checkpoint Behavior

At the end of meaningful agent work:

```bash
python scripts/context_pack.py checkpoint --pack
```

This writes ignored local state by default, so proactive checkpoints do not dirty tracked files. Use `checkpoint --publish --pack` only when the handoff should be committed and shared through git.

## Admin Commands

Use these only when directly relevant:

```bash
python scripts/context_pack.py install-codex --force
python scripts/context_pack.py install-agent-docs
python scripts/context_pack.py status
python scripts/context_pack.py measure --task "<short task>"
python scripts/context_pack.py doctor --fix
python scripts/context_pack.py mark-reviewed <area-id>
python scripts/context_pack.py refresh
python scripts/context_pack.py install-git-hooks --mode safe
```

Run `python scripts/context_pack.py <command> --help` for options instead of expanding this skill into a full CLI manual.

## Operating Rules

- Keep the user in their normal workflow; do not make them manage packs manually.
- Prefer `start` over lower-level `pack` commands.
- Prefer source verification over trusting summaries.
- Keep `CURRENT.md` short; durable knowledge belongs in `.context-pack/AREAS/*.md`.
- Do not commit `.context-pack/packs/` or `.context-pack/local/LOCAL.md`.
- If a changed file maps to no area, finish the task first, then consider updating the manifest or area docs.
