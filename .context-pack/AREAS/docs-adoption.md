---
id: docs-adoption
status: active
paths:
  - README.md
  - README.ko.md
  - docs/BENCHMARKS.md
  - docs/benchmarks/**
tests:
  - tests/test_benchmarks.py
verify:
  - python -m unittest tests.test_benchmarks -v
  - python scripts/benchmark_context_pack.py --public --fail-on-weak
last_reviewed_head: 8e8138f9a1b8
---

# Docs And Adoption

## Read When
- Changing onboarding, positioning, benchmark claims, demo output, field reports, or release notes.

## Start With
- `README.md`
- `README.ko.md`
- `docs/BENCHMARKS.md`
- `docs/benchmarks/codex-ab-v050-summary.md`
- `scripts/benchmark_codex_ab.py`

## Contracts
- English and Korean onboarding describe the same behavior and evidence.
- The main README gives one primary install route per agent surface.
- Actual Codex results separate cumulative total input, uncached input, quality, commands, and latency.
- Maintained v0.5.0 context is reported as 14/14 on four small author-run task sets, not universal proof.
- The 11/14 transient result and token regressions remain visible beside successful results.
- Claude Code and Cursor file generation is distinguished from runtime validation.
- Approximate `chars/4` scope ratios are never presented as actual model tokens.

## Common Failure Modes
- A benchmark number is copied without method, task count, or limitations.
- Cached cumulative input is presented as peak context occupancy or direct billing.
- Failed runs disappear from public summaries.
- The demo implies unconfigured repositories are modified or automatically routed.
- A benchmark reuses a dirty work directory or a global engine.
