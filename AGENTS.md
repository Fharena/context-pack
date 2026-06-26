<!-- context-pack:rules:start -->
## Context Pack

At the start of substantial work, read `.codex/handoff/CURRENT.md` and `.codex/context/INDEX.md`, then use the relevant `.codex/context/AREAS/*.md` files before broad repo reading. When a task or review needs orientation, generate a focused context pack first.

For reviews and debugging, prefer a generated context pack from `.codex/packs/CONTEXT_PACK.md` when present. Treat context docs as routing hints, not ground truth. If HEAD, dirty files, or diff hash differ from the current repo state, verify against source code before acting.

At the end of substantial work or after changing files, run `context-pack checkpoint --pack` when available so the next agent has an up-to-date fingerprint, log entry, and generated read-first pack.

<!-- context-pack:rules:end -->
