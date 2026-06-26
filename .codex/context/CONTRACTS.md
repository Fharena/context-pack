# Project Contracts

Use this as a compact checklist. Keep area-specific details in `AREAS/*.md`.

## engine
- The engine must remain stdlib-only so it can run from a skill, plugin, or copied checkout.
- Generated packs must stay under .codex/packs/ and remain ignored by git.
- Context docs are routing hints; packs must include stale warnings instead of hiding uncertainty.
- `start` must stay a thin agent-first router over deterministic init, pack, review-pack, and dirty-file behavior.

## installer-release
- Install scripts must not overwrite existing local skill/plugin installs unless --force is explicit.
- Marketplace updates must preserve personal marketplace shape and include installation/authentication/category policy.
- Release checks must include unit tests, plugin validation, and skill validation.

## overview
- Treat context docs as routing hints, not ground truth.
- Verify source code when the context fingerprint is stale.

## skill-plugin
- The Codex skill must tell agents to use deterministic script commands before semantic summarization.
- Plugin manifest must remain validation-ready and avoid unsupported fields.
- The skill should be implicitly invokable for context setup, start routing, review packs, checkpointing, and token-saving repo orientation.

## tests
- Tests should exercise real command flows through the engine main entrypoint.
- Coverage should include no-git repos, first-run start, dirty changed files, committed review diffs, and hook idempotency.
