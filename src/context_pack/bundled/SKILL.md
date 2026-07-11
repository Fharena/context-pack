---
name: context-pack
description: Orient coding agents from a configured repo context library before broad reading. Use for unfamiliar implementation, debugging, failing tests or CI, branch and PR review, continuation, and handoff across agents, machines, or worktrees. In unconfigured repos, use transient routing only after a targeted search remains broad. Skip pure Q&A, precise or obvious edits, and small repos where routing adds no value.
---

# Context Pack

Use Context Pack as quiet orientation, then continue the user's actual task. Do not ask the user to name the tool or manage packs manually.

## Workflow

1. Check whether `.context-pack/manifest.json` exists.

   - Configured repo: use Context Pack before broad orientation.
   - Unconfigured repo: try one targeted search first. Use transient `start` only if the task remains broad/cross-area or the user asks for a preview. Do not add setup implicitly.

2. Choose the explicit operation from the user's intent:

   - Coding or debugging: `start --agent --task "<short task>"`
   - Branch or PR review: `start --agent --review`; add `--base <ref>` when known
   - Dirty files are the only signal: `start --agent --changed`
   - Resume a configured project with no clear task: `start --agent`

3. Run `context-pack <operation>` in the target repo. If the CLI is unavailable, run:

   ```bash
   python <this-skill-folder>/scripts/context_pack.py <operation>
   ```

   Do not use a target repo's similarly named script unless that repo is Context Pack itself.

4. Use the inline pack printed by `start`. Do not reopen its saved path unless command output was truncated.
5. Treat embedded `Evidence` as current source. If the root cause is visible, edit directly and spend the next tool call on verification. Do not grep, cat, or reopen shown ranges.
6. Search only the listed terms and scopes when Evidence is insufficient, then perform the requested work. Never bulk-read a glob or directory.

## Persistence

Treat first use and installation as different actions.

- On an unconfigured repo, interactive `start` prints a transient pack without writing repository files.
- Run `setup --dry-run` and then `setup` only when the user explicitly asks to install, configure, or persist Context Pack in the repo.
- Use `doctor --fix` only for an explicitly configured but broken setup.
- Do not install Git hooks unless the user asks for Git-boundary automation.

## Handoff

Checkpoint only when durable work should survive a session boundary:

```bash
context-pack checkpoint --pack --quiet
```

This updates ignored local state. Skip it for ordinary intermediate turns. Use `checkpoint --publish --pack` only when the handoff should be committed and shared through git. Do not checkpoint an unconfigured repo.

## Limits

- Skip Context Pack when direct reading is cheaper or relevant files are already known.
- Skip it when an exact file, symbol, stack frame, or distinctive error can be localized with one targeted search; use it only if that search stays broad or crosses areas.
- Respect a `start` message saying a small repo does not need a pack.
- Treat area summaries, decisions, and stale warnings as routing hints, never as ground truth.
- Prefer explicit `--review` and `--changed` flags; do not ask the CLI to infer session lifecycle intent from prose.
- Use `measure` only when the user asks for approximate text-budget evidence.
