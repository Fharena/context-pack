# Project Contracts

Use this as a compact checklist. Keep area-specific details in `AREAS/*.md`.

## engine
- The engine must remain stdlib-only so it can run from a skill, plugin, or copied checkout.
- Generated packs must stay under .codex/packs/ and remain ignored by git.
- Context docs are routing hints; packs must include stale warnings instead of hiding uncertainty.
- `setup` must stay the lowest-friction repo onboarding path and compose deterministic init, agent-doc install, optional hooks, and doctor checks.
- `start` must stay a thin agent-first router over deterministic init, pack, review-pack, and dirty-file behavior.
- `install-codex` must refuse unsafe overwrites and be able to install from both source checkouts and packaged CLI installs.
- `install-agent-docs` must preserve existing user text and only replace the managed marker block.
- Generated packs should show scope-reduction metrics without pretending they replace source verification.

## installer-release
- Install scripts must not overwrite existing local skill/plugin installs unless --force is explicit.
- Codex plugin install must work from a package install without requiring a repo clone.
- Marketplace updates must preserve personal marketplace shape and include installation/authentication/category policy.
- Release checks must include unit tests, plugin validation, and skill validation.

## overview
- Treat context docs as routing hints, not ground truth.
- Verify source code when the context fingerprint is stale.

## skill-plugin
- The Codex skill must tell agents to use deterministic script commands before semantic summarization.
- Plugin manifest must remain validation-ready and avoid unsupported fields.
- The skill should use `context-pack setup` when Context Pack is missing or the user asks to configure project memory.
- The skill should be implicitly invokable for context setup, install/update requests, shared agent-doc rules, start routing, review packs, checkpointing, and token-saving repo orientation.

## tests
- Tests should exercise real command flows through the engine main entrypoint.
- Coverage should include no-git repos, first-run setup, first-run start, install-codex, install-agent-docs, dirty changed files, committed review diffs, and hook idempotency.
