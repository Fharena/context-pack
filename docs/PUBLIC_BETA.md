# Public Beta Launch Notes

Use these when announcing Context Pack. Keep the tone honest: this is a public beta with CI, package, and dogfood evidence, not a mature productivity claim.

## Short Pitch

Your coding agent should not rediscover your repo from scratch every session.

Context Pack is a lightweight repo-local context layer for Codex, Claude, Cursor, and other coding agents. Say "fix this bug", "CI is red", "review this branch", or "I'm done for now"; the agent starts from a focused context pack instead of reading broadly.

## Launch Post

I built Context Pack because my coding agents kept wasting time rediscovering the same repo context between local IDEs, Codex, Claude, Cursor, cloud worktrees, and fresh sessions.

It adds a small `.context-pack/` library to a repo and gives agents a simple rule: before broad reading, run `context-pack start`.

Examples:

- `why are tests failing` -> `source, tests`
- `CI is red` -> `automation, source, tests`
- `review this branch` -> review pack from the diff
- `I'm done for now` -> ignored local checkpoint

It is intentionally not a vector DB or another agent memory silo. It is markdown-first, git-aware, stale-aware, and explainable. The pack says why each area was selected and reminds the agent to verify source before editing.

The current public beta is CI-tested on Windows/Ubuntu, Python 3.11/3.12, packaged through both Python and npm tarball paths, and dogfooded on public repos. Early read-only dogfood examples selected first-read context from about 27% to 79% of repo text depending on repo shape. That range is honest: curated area docs matter for larger projects.

Looking for feedback from heavy Codex/Claude/Cursor users, especially people moving work between local and cloud worktrees.

Repo: https://github.com/Fharena/context-pack

## X / Short Social

I built Context Pack so coding agents stop rediscovering the same repo every session.

It gives Codex/Claude/Cursor a repo-local `.context-pack/` map before broad reading:

- "why are tests failing" -> source/tests
- "CI is red" -> automation/source/tests
- "review this branch" -> review pack
- "done for now" -> checkpoint

Public beta: https://github.com/Fharena/context-pack

## Show HN Title

Show HN: Context Pack, a repo-local context layer for coding agents

## Submission Notes

- Lead with the pain: agents rediscover repo context across sessions.
- Say it is public beta.
- Do not claim universal token savings.
- Mention the honest benchmark range and link to `docs/BENCHMARKS.md`.
- Ask for feedback from heavy agent users.
