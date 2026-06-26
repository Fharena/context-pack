<!-- context-pack:rules:start -->
## Context Pack

At the start of substantial work, run `context-pack start --task "<short task description>"` when available. With no clear task, run `context-pack start`. This initializes missing context docs, chooses a focused pack when possible, and prints what to read next.

Use Context Pack proactively. Do not wait for the user to name it when starting a non-trivial task, debugging unfamiliar code, reviewing dirty files or a branch, entering an existing context-enabled repo, or preparing work another agent may continue.

When a review needs orientation, prefer `context-pack start --review --base <base-ref>`. When changed files are the only signal, use `context-pack start --changed`.

For reviews and debugging, prefer a generated context pack from `.context-pack/packs/CONTEXT_PACK.md` when present. Treat context docs as routing hints, not ground truth. If HEAD, dirty files, or diff hash differ from the current repo state, verify against source code before acting.

At the end of substantial work or after changing files, run `context-pack checkpoint --pack` when available. This writes an ignored local checkpoint by default so automatic agent use does not dirty tracked handoff files. Use `context-pack checkpoint --publish --pack` only when the handoff should be committed and shared through git.

<!-- context-pack:rules:end -->
