---
id: engine
last_reviewed_head: 367e96d5010f
status: active
paths:
  - plugins/context-pack/skills/context-pack/scripts/context_pack.py
  - plugins/context-pack/scripts/context_pack.py
tests:
  - tests/test_context_pack.py
stale_if:
  - engine command behavior changes
  - git matching behavior changes
  - hook install behavior changes
---

# Engine

## Read When
- Changing `context_pack.py` commands or output.
- Debugging setup, start, install-codex, checkpoint, pack, review-pack, status, mark-reviewed, refresh, doctor, or git hook behavior.
- Debugging shared agent-doc installation for `AGENTS.md`, `CLAUDE.md`, or Cursor rules.
- Adding new deterministic operations that should not spend agent tokens.

## Start With
- `plugins/context-pack/skills/context-pack/scripts/context_pack.py`
- `tests/test_context_pack.py`

## Contracts
- Engine stays stdlib-only.
- Dirty/untracked files must resolve to actual file paths for area matching.
- Review packs must support committed branch changes via `--base`.
- Review mode without an explicit base should infer upstream/common default branches when a diff exists.
- Packs should stay compact: rank areas, split Read First/Read Later, and omit overflow details with clear counts.
- Packs should show scope-reduction metrics without pretending they replace source verification.
- Stale warnings should be actionable through `status` and `mark-reviewed`.
- `status` and `doctor --strict` should surface stale shared `CURRENT.md` fingerprints without treating handoff-only publish commits as stale forever.
- Default checkpoints should write ignored local state; tracked handoff updates require `--publish`.
- `checkpoint --pack` should route clean committed work from the previous checkpoint head when available, not fall back to overview-only context.
- `setup` should stay the lowest-friction repo onboarding path and compose deterministic init, agent-doc install, optional hooks, and doctor checks.
- `doctor --fix` should repair missing setup files through the same safe setup path and must not install git hooks.
- `start` should stay a thin agent-first router over deterministic init, pack, review-pack, and dirty-file behavior.
- Test-failure/debugging prompts should pair source with tests when both inferred areas exist, so agents do not inspect tests alone.
- English broken/not-working prompts should route common coding phrases like "login is broken" and "checkout doesn't work" to source/tests while avoiding loose matches such as "broken link report".
- Korean bug prompts should route common coding phrases like "버그 잡아줘" and "문제 해결해줘" to source/tests while avoiding meta/docs phrases such as "버그 리포트 문서 정리".
- Natural review prompts should handle softer user wording like "look over my changes" and "변경사항 봐줘" while keeping meta/documentation tasks in normal work mode.
- Natural handoff prompts should handle short wrap-up wording like "I'm done for now", "wrap this up", and "작업 끝났어" while avoiding broad matches on words like `done` or `wrap`.
- Continuation and handoff wording should explain why no pack was generated without contradicting dirty-file state.
- Running `context-pack` with no arguments should print a quickstart and exit successfully.
- `context-pack --version` should report the public package version.
- `install-codex` should refuse unsafe overwrites and work from both source checkouts and packaged CLI installs.
- `install-agent-docs` should preserve existing user text and only replace the managed marker block.
- Hook install must preserve unrelated hook contents and be idempotent.
- Generated packs live under `.context-pack/packs/` and stay ignored.

## Common Failure Modes
- `git status` reports an untracked directory instead of files.
- `review-pack` sees no dirty files and misses committed review scope.
- `start --review` without `--base` falls back to overview instead of finding branch changes against a common base.
- Existing hook files get overwritten instead of marker blocks being inserted.
- Stale area docs are hidden instead of surfaced as warnings.
- Shared `CURRENT.md` points at old work while `status` reports the context library as healthy.
- Broad overview/context patterns dominate the pack instead of specific changed-file areas.
- Contracts or failure modes repeat until the pack stops saving tokens.
- Automatic end-of-work checkpoints dirty tracked handoff files and create commit noise.
- Clean committed work ends with an overview-only checkpoint pack because there are no dirty files.
- Context-only maintenance commits become the checkpoint pack base and hide the actual prior work.
- Generic task verbs like `fix` select unrelated areas instead of acting as code-task hints.
- Natural prompts like "why are tests failing" route only to tests and omit source context needed to debug failures.
- English bug routing is too narrow and misses "login is broken" / "checkout doesn't work", or too broad and treats "broken link report" as code work.
- Korean bug routing is too narrow and misses "버그 잡아줘" / "문제 해결해줘", or too broad and treats bug-report documentation as code work.
- Natural review intent is either too narrow to catch "look over my changes" / "변경사항 봐줘" or too broad and turns product/documentation work into review mode.
- Short handoff intent is either too narrow to catch "I'm done for now" / "작업 끝났어" or too broad and turns "done button" / "wrap parser errors" into checkpoint guidance.
- Handoff wording in a dirty repo prints the generic no-dirty-files reason, making correct routing look suspicious.
- Product-wide words like `context`, `pack`, or `agent` select most areas instead of narrowing the route.
- `setup` skips shared agent docs or installs git hooks without explicit setup flags.
- `doctor --fix` reports success while required context files are still missing.
- `start` hides setup errors or creates noisy tracked files on first run.
- No-argument CLI invocation exits with an argparse error instead of a useful first-run quickstart.
- Users cannot confirm the installed package version through `context-pack --version`.
- `install-codex --force` overwrites the source plugin tree or writes an invalid marketplace entry.
- `install-agent-docs` duplicates marker blocks or strips existing `AGENTS.md`, `CLAUDE.md`, or Cursor rule content.
- Scope-reduction numbers are missing or imply false precision about exact token savings.

## Expand Scope If
- Manifest schema changes.
- Pack markdown format changes.
- Git hook behavior changes.
- README/SKILL command examples change.

## Do Not Start With
- `.context-pack/packs/`
- append-only `LOG.md` unless debugging checkpoint history
