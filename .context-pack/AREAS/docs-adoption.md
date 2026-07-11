---
id: docs-adoption
status: active
paths:
  - README.md
  - README.ko.md
  - docs/BENCHMARKS.md
  - docs/benchmarks/**
tests:
  - python scripts/benchmark_context_pack.py --public --fail-on-weak
last_reviewed_head: 9b5789e04e19
---

# Docs And Adoption

## Read When
- Changing onboarding, positioning, benchmark claims, demo output, or release notes.

## Start With
- `README.md`
- `README.ko.md`
- `docs/BENCHMARKS.md`
- `docs/benchmarks/codex-ab-zoning-confirm.md`
- `scripts/benchmark_codex_ab.py`

## Contracts
- English and Korean onboarding describe the same behavior.
- The main README gives one primary install route per agent surface.
- Approximate orientation ratios are never presented as billed tokens or patch-quality evidence.
- Actual Codex A/B results separate cumulative total input from newly processed uncached input.
- Mixed or negative benchmark results remain public; no universal token-saving claim is made from one task.
- Internal audit notes do not crowd the public getting-started path.

## Common Failure Modes
- README examples drift from the packaged CLI.
- A benchmark number is copied without its method or limitations.
- Cached cumulative input is presented as peak context occupancy or direct billing.
- Demo output shows a setup flow that normal first-run work no longer uses.
