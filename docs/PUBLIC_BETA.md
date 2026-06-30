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

The current public beta is CI-tested on Windows/Ubuntu, Python 3.11/3.12, packaged through both Python and npm tarball paths, and dogfooded on public repos. The current benchmark run covers 10 public-repo scenarios with 0 weak flags under the harness thresholds. First-read routing varied by repo shape: examples include `psf/requests` at ~27% of repo text, `gin-gonic/gin` at ~4%, `expressjs/express` at ~9%, and three `mozilla/BrowserQuest` web-game tasks at ~16-17% of broad repo text. A synthetic orientation proxy also reduced a broad 64-file first read to 2 files, ~97% less approximate text budget.

Those numbers are intentionally narrow claims: they measure deterministic orientation and approximate text-budget reduction, not provider billing tokens or independent-agent patch quality. Curated area docs still matter for larger projects.

Looking for feedback from heavy Codex/Claude/Cursor users, especially people moving work between local and cloud worktrees.

Repo: https://github.com/Fharena/context-pack

## X / Short Social

Context Pack gives Codex/Claude/Cursor a repo-local map before broad reading.

Benchmarked: 10 public-repo scenarios, 0 weak flags; BrowserQuest first-read was 16-17% of repo text.

코딩 에이전트가 repo를 다시 훑기 전에 필요한 맥락부터 보게 합니다.

https://github.com/Fharena/context-pack

## Show HN Title

Show HN: Context Pack, a repo-local context layer for coding agents

## Submission Notes

- Lead with the pain: agents rediscover repo context across sessions.
- Say it is public beta.
- Do not claim universal token savings.
- Mention the honest benchmark range and link to `docs/BENCHMARKS.md`.
- Ask for feedback from heavy agent users.
