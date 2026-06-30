# Context Pack Benchmarks

These are release-readiness dogfood and orientation benchmarks for the `v0.2.20` candidate.

The goal is not to claim a universal token-saving percentage. Context Pack is a routing layer: it should tell an agent what to read first, explain why, and make limitations visible before the agent reads broadly.

## Method

- Date: 2026-06-30
- Tool: local candidate through `python scripts/benchmark_context_pack.py --public`
- Mode: read-only first-run routing plus one synthetic handoff replay
- Repos: shallow public GitHub clones with no `.context-pack/` installed
- Estimates: approximate text budget uses `chars/4` and skips ignored, unreadable, known binary, empty, and files over 1 MB
- Weak thresholds: expected selected areas must be present, read ratio must stay below each scenario threshold, and deterministic routing must finish under 5 seconds

Machine-readable results live in [`docs/benchmarks/latest.json`](benchmarks/latest.json). The generated summary lives in [`docs/benchmarks/latest.md`](benchmarks/latest.md).

## Public Orientation Results

| Scenario | Repo | Prompt | Selected first | Approx first-read text | Flags |
| --- | --- | --- | --- | ---: | --- |
| sampleproject-ci | `pypa/sampleproject` | `ci is red` | `automation, source, tests` | ~2.2k / ~3.3k tokens, 67% | ok |
| requests-tests | `psf/requests` | `why are tests failing` | `source, tests` | ~103.7k / ~386.9k tokens, 27% | ok |
| click-shell-completion | `pallets/click` | `fix shell completion bug` | `source, tests` | ~210.1k / ~357.8k tokens, 59% | ok |
| httpx-build | `encode/httpx` | `build failed` | `automation, source, tests` | ~196.6k / ~247.7k tokens, 79% | ok |
| browserquest-mobile | `mozilla/BrowserQuest` | `fix mobile controls bug on touch devices` | `source` | ~98.2k / ~602.2k tokens, 16% | ok |
| browserquest-sprites | `mozilla/BrowserQuest` | `fix missing sprite asset loading bug` | `source, sprites` | ~103.6k / ~602.2k tokens, 17% | ok |
| browserquest-websocket | `mozilla/BrowserQuest` | `debug websocket login connect failure` | `source` | ~98.2k / ~602.2k tokens, 16% | ok |
| gin-middleware | `gin-gonic/gin` | `fix middleware panic bug` | `source` | ~8.8k / ~217.6k tokens, 4% | ok |
| express-router | `expressjs/express` | `fix router middleware error handling` | `source` | ~15.5k / ~177.8k tokens, 9% | ok |
| fd-rust-filter | `sharkdp/fd` | `fix regex filter bug` | `source` | ~41.8k / ~138.6k tokens, 30% | ok |

## Handoff Replay

The synthetic replay benchmark creates a small repo, runs setup, checkpoints and publishes handoff state, clones the repo locally, then asks both checkouts the same test-failure prompt.

- Same routing signature after clone: yes
- Source checkout: `source, tests`, ~404 / ~4427 tokens, 9%
- Cloned checkout: `source, tests`, ~404 / ~4427 tokens, 9%

This checks the core promise that git-carried context can help a new session start from the same routing context. It does not prove that two independent agents will write identical answers.

## Weak Spots Found And Fixed

- Go repos were under-inferred. A `gin-gonic/gin` middleware prompt previously risked falling back to generic orientation because the engine did not infer root and top-level Go package files. The engine now recognizes Go repos, root `*.go`, common package directories, and `*_test.go` files. Final run: `gin-middleware` selected `source` at 4%.
- Rust repos were too broad. A `sharkdp/fd` regex/filter prompt initially pulled broader source/test context than needed. The engine now includes common Rust crate start files and Rust/filter/search keywords. Final run: `fd-rust-filter` selected `source` at 30%.
- Media-heavy repos exposed a cold-start cost. BrowserQuest contains many binary assets; pre-fix measurement could cross the slow threshold because binary files were read before being rejected as non-text. Text-budget scanning now skips known binary suffixes and checks file size before reading. Final BrowserQuest runs stayed under the 5 second threshold.
- Test expectations were tightened. For router/error-handling prompts, `source` is the correct first area when the generated pack still points to relevant test guidance separately; benchmarks should not reward unnecessary extra areas.

## What This Proves

- Natural prompts route to expected first-read area types without asking the user to name Context Pack.
- `Why selected` remains inspectable before setup writes context files.
- First-run inference now covers common Python, JavaScript client/server, web game asset, Go, and Rust layouts.
- On a medium web game, task-specific first reads can reduce broad repo text budget from ~602.2k tokens to ~98.2k-103.6k tokens.
- Handoff replay preserves deterministic routing across a fresh clone when context docs are committed.

## What This Does Not Prove

- It does not prove a universal token reduction percentage.
- It does not measure provider billing tokens exactly; counts are approximate text-budget estimates.
- Duration numbers are local wall-clock regression signals and depend on machine and filesystem cache state.
- It does not yet measure independent agent accuracy, wall-clock task speed, final patch quality, or answer consistency.
- It does not replace source verification.
- It does not prove monorepo quality without curated area boundaries.

## Next Proof Milestone

The next benchmark should be an independent-agent trace: same repo, same task, one run without Context Pack and one run with it. Compare first relevant file, read tokens, elapsed time, final patch quality, test result, and whether a fresh session reaches the same diagnosis.
