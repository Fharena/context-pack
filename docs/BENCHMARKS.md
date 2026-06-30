# Context Pack Benchmarks

These are release-readiness dogfood and A/B orientation runs for `v0.2.19`.

The goal is not to claim a universal token-saving percentage. Context Pack is a routing layer: it should tell an agent what to read first, explain why, and make the limitations visible before the agent reads broadly.

## Dogfood Routing Method

- Date: 2026-06-30
- Tool: local `v0.2.19` candidate through `node bin/context-pack.js measure`
- Mode: read-only `measure`
- Repos: fresh shallow public GitHub clones
- Setup: no `.context-pack/` installed in the target repos, so results use first-run inferred areas
- Estimates: Context Pack's approximate text budget uses `chars/4` and skips binary, ignored, unreadable, and files over 1 MB

## Dogfood Routing Results

| Repo | HEAD | Prompt | Selected first | Files considered | Read First entries | Approx first-read text |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `pypa/sampleproject` | `621e4974ca25` | `ci is red` | `automation, source, tests` | 12 | 7 | ~2.2k tokens, ~67% |
| `psf/requests` | `23953c0c8752` | `why are tests failing` | `source, tests` | 130 | 4 | ~103.7k tokens, ~27% |
| `pallets/click` | `679a7a0eccbd` | `fix shell completion bug` | `source, tests` | 150 | 4 | ~210.1k tokens, ~59% |
| `encode/httpx` | `b5addb64f016` | `build failed` | `automation, source, tests` | 125 | 8 | ~196.6k tokens, ~79% |

## A/B Orientation Benchmark

This benchmark checks a larger web game where "read the whole repo" is expensive but a task-specific first read is plausible.

- Date: 2026-06-30
- Repo: [`mozilla/BrowserQuest`](https://github.com/mozilla/BrowserQuest)
- HEAD: `af32d247cac3`
- Size: 452 repo files considered; ~602.2k text tokens from 169 text files
- Baseline: no Context Pack routing, approximated as broad repo text budget
- Context Pack: first-run inferred areas only; no `.context-pack/` files installed in BrowserQuest

| Prompt | Without Context Pack | With Context Pack | Selected first | Reduction |
| --- | ---: | ---: | --- | ---: |
| `fix mobile controls bug on touch devices` | ~602.2k tokens | ~98.2k tokens | `source` | ~84% |
| `fix missing sprite asset loading bug` | ~602.2k tokens | ~103.6k tokens | `source, sprites` | ~83% |
| `debug websocket login connect failure` | ~602.2k tokens | ~98.2k tokens | `source` | ~84% |

This run also found and fixed a product gap: pre-fix first-run inference treated BrowserQuest as `overview` only because it uses `client/js`, `server/js`, and `shared/js` instead of `src/`. The engine now infers those web source paths, separates `sprites`, `maps`, and `media`, and avoids pulling vendored `client/js/lib` files into the initial read.

## What This Proves

- Natural prompts route to the expected area types without asking the user to name Context Pack.
- The `Why selected` output is inspectable before any setup files are written.
- First-run inference catches common `src/`, tests, docs, automation, top-level Python package layouts, and common web game/client-server JS layouts.
- On a medium web game, task-specific first reads can reduce the initial text budget by roughly 83-84% compared with a broad repo text scan.
- Real repositories reveal useful gaps: broad source/test areas still need curated `.context-pack/AREAS/*.md` docs for better compression.

## What This Does Not Prove

- It does not prove a universal token reduction percentage.
- It does not yet measure independent agent accuracy, wall-clock task speed, or final patch quality.
- It does not replace source verification.
- It does not prove monorepo quality without curated area boundaries.

## Honest Takeaway

Context Pack is already useful as a transparent first-read router. On medium repos, first-run inference can reduce the initial file set sharply, but token reduction depends on repo shape. The next proof milestone is a true independent-agent trace: same bug, same repo, one run without Context Pack and one run with it, comparing read tokens, time to first relevant file, final patch quality, and test result.
