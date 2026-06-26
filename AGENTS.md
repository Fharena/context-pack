<!-- context-pack:rules:start -->
## Context Pack

At the start of substantial work, run `context-pack status` when available, read `.codex/handoff/CURRENT.md` and `.codex/context/INDEX.md`, then use the relevant `.codex/context/AREAS/*.md` files before broad repo reading.

Use Context Pack proactively. Do not wait for the user to name it when starting a non-trivial task, debugging unfamiliar code, reviewing dirty files or a branch, entering an existing context-enabled repo, or preparing work another agent may continue.

When a task or review needs orientation, generate a focused context pack first with `context-pack pack --task "..."`, `context-pack pack --changed`, or `context-pack review-pack --base <base-ref>`.

For reviews and debugging, prefer a generated context pack from `.codex/packs/CONTEXT_PACK.md` when present. Treat context docs as routing hints, not ground truth. If HEAD, dirty files, or diff hash differ from the current repo state, verify against source code before acting.

At the end of substantial work or after changing files, run `context-pack checkpoint --pack` when available. This writes ignored local checkpoint state by default, so automatic agent checkpoints do not dirty tracked handoff files. Use `context-pack checkpoint --publish --pack` only when the handoff should be committed and shared through git.

<!-- context-pack:rules:end -->
