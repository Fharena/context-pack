<!-- context-pack:rules:start -->
## Context Pack

Use Context Pack as quiet orientation for natural-language coding, review, debugging, and handoff requests. The user does not need to name it.

Run it only when repo orientation would save broad reading or preserve useful handoff state:
- Non-trivial bug, feature, or debugging task: `context-pack start --task "<short task>"`
- Review, PR, or branch work: `context-pack start --review`; add `--base <base-ref>` when known. Without a base, Context Pack tries upstream/common default branches.
- Changed files are the only signal: `context-pack start --changed`
- Missing or broken setup when repo memory is wanted: `context-pack setup --dry-run`, then `context-pack setup` if setup was requested; use `context-pack doctor --fix` for repair
- End of meaningful work or handoff: `context-pack checkpoint --pack`

Skip Context Pack for pure Q&A, tiny obvious single-file edits, or tasks where the relevant files and tests are already clear.

When a pack is generated, read `.context-pack/packs/CONTEXT_PACK.md` before broad source reads. Treat context docs as routing hints, not ground truth; verify against source when state, stale warnings, or code behavior disagree.

Use `context-pack checkpoint --publish --pack` only when the handoff should be committed and shared through git.
<!-- context-pack:rules:end -->
