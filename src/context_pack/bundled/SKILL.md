---
name: context-pack
description: Orient coding agents from focused repo context before broad reading. Use proactively for non-trivial implementation, debugging, failing tests or CI, branch and PR review, session continuation, and handoff across agents, machines, or worktrees. Skip pure Q&A, tiny obvious edits, already-known files, and small repos where routing adds no value.
---

# Context Pack

Use Context Pack as quiet orientation, then continue the user's actual task. Do not ask the user to name the tool or manage packs manually.

## Workflow

1. Choose the explicit operation from the user's intent:

   - Coding or debugging: `start --task "<short task>"`
   - Branch or PR review: `start --review`; add `--base <ref>` when known
   - Dirty files are the only signal: `start --changed`
   - Resume a configured project with no clear task: `start`

2. Run `context-pack <operation>` in the target repo. If the CLI is unavailable, run:

   ```bash
   python <this-skill-folder>/scripts/context_pack.py <operation>
   ```

   Do not use a target repo's similarly named script unless that repo is Context Pack itself.

3. Read the pack path printed by `start`. It may be under `.context-pack/packs/` or a transient Git-local/cache path.
4. Read only the listed files first, verify source behavior, and perform the requested work.

## Persistence

Treat first use and installation as different actions.

- On an unconfigured repo, `start` is transient and must not create `.context-pack/`, `AGENTS.md`, or `.gitignore`.
- Run `setup --dry-run` and then `setup` only when the user explicitly asks to install, configure, or persist Context Pack in the repo.
- Use `doctor --fix` only for an explicitly configured but broken setup.
- Do not install Git hooks unless the user asks for Git-boundary automation.

## Handoff

After meaningful work in a configured repo, run:

```bash
context-pack checkpoint --pack
```

This updates ignored local state. Use `checkpoint --publish --pack` only when the handoff should be committed and shared through git. Do not checkpoint an unconfigured repo.

## Limits

- Skip Context Pack when direct reading is cheaper or relevant files are already known.
- Respect a `start` message saying a small repo does not need a pack.
- Treat area summaries, decisions, and stale warnings as routing hints, never as ground truth.
- Prefer explicit `--review` and `--changed` flags; do not ask the CLI to infer session lifecycle intent from prose.
- Use `measure` only when the user asks for approximate text-budget evidence.
