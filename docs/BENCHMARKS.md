# Context Pack Benchmarks

These are release-readiness dogfood runs for `v0.2.18`.

The goal is not to claim a universal token-saving percentage. Context Pack is a routing layer: it should tell an agent what to read first, explain why, and make the limitations visible before the agent reads broadly.

## Method

- Date: 2026-06-30
- Tool: local `v0.2.18` candidate through `node bin/context-pack.js measure`
- Mode: read-only `measure`
- Repos: fresh shallow public GitHub clones
- Setup: no `.context-pack/` installed in the target repos, so results use first-run inferred areas
- Estimates: Context Pack's approximate text budget uses `chars/4` and skips binary, ignored, unreadable, and files over 1 MB

## Results

| Repo | HEAD | Prompt | Selected first | Files considered | Read First entries | Approx first-read text |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `pypa/sampleproject` | `621e4974ca25` | `ci is red` | `automation, source, tests` | 12 | 7 | ~2.2k tokens, ~67% |
| `psf/requests` | `23953c0c8752` | `why are tests failing` | `source, tests` | 130 | 4 | ~103.7k tokens, ~27% |
| `pallets/click` | `679a7a0eccbd` | `fix shell completion bug` | `source, tests` | 150 | 4 | ~210.1k tokens, ~59% |
| `encode/httpx` | `b5addb64f016` | `build failed` | `automation, source, tests` | 125 | 8 | ~196.6k tokens, ~79% |

## What This Proves

- Natural prompts route to the expected area types without asking the user to name Context Pack.
- The `Why selected` output is inspectable before any setup files are written.
- First-run inference catches common `src/`, tests, docs, automation, and top-level Python package layouts.
- Real repositories reveal useful gaps: broad source/test areas still need curated `.context-pack/AREAS/*.md` docs for better compression.

## What This Does Not Prove

- It does not prove a universal token reduction percentage.
- It does not measure agent accuracy or wall-clock task speed.
- It does not replace source verification.
- It does not prove monorepo quality without curated area boundaries.

## Honest Takeaway

Context Pack is already useful as a transparent first-read router. On medium repos, first-run inference can reduce the initial file set sharply, but token reduction depends on repo shape. For larger repos, the next product milestone is better area curation and real before/after task traces.
