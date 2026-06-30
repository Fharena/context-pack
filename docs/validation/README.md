# Context Pack Validation

Latest validation date: 2026-06-30

This folder records post-release validation beyond normal unit tests and CI.

## Latest Results

- Deterministic A/B proxy: pass
- Fresh-clone session consistency: pass
- GitHub `npx` install path: pass, `context-pack 0.2.20`
- GitHub Release npm tarball install: pass, `context-pack 0.2.20`
- GitHub Release Python wheel install: pass, `context-pack 0.2.20`
- npm registry package: not published yet
- PyPI package: not published yet

See [`latest.md`](latest.md) and [`latest.json`](latest.json) for the reproducible A/B proxy and session consistency run.

## What Was Checked

- A synthetic test-failure repo compared broad repo reading against Context Pack's first-read routing.
- A committed handoff was cloned locally and checked against three prompts:
  - `why are tests failing`
  - `ci is red`
  - `fix login timeout`
- Install paths were checked from GitHub and release assets, not only from the local checkout.

## Remaining Gap

The only major validation still not done is true independent LLM patch-quality testing. The current run proves deterministic routing, first-read reduction, fresh-clone consistency, and installability. It does not prove that two separate AI agents will produce the same diagnosis or patch.
