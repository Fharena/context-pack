<!-- context-pack:rules:start -->
## Context Pack

Use Context Pack quietly when a non-trivial coding, debugging, review, or handoff request would otherwise require broad repo reading. The user does not need to name the tool.

- Coding/debugging: `context-pack start --task "<short task>"`
- Branch or PR review: `context-pack start --review`; add `--base <ref>` when known.
- Dirty files are the only signal: `context-pack start --changed`
- Read the pack path printed by `start`, then verify relevant source before editing.

On an unconfigured repo, `start` is transient and must not create `.context-pack/`, `AGENTS.md`, or `.gitignore`. Run `context-pack setup --dry-run` and `context-pack setup` only when the user explicitly asks to persist Context Pack in the repo.

Skip pure Q&A, tiny obvious edits, already-known files, and small repos where `start` says broad reading is cheaper.

After meaningful work in a configured repo, run `context-pack checkpoint --pack`. Use `--publish` only when the handoff should be committed and shared through git. Treat all context docs as routing hints, never as source of truth.
<!-- context-pack:rules:end -->
