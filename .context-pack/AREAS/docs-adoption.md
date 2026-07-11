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
last_reviewed_head: b440399b85ee
---

# Docs And Adoption

## Read When
- Changing onboarding, positioning, benchmark claims, demo output, or release notes.

## Start With
- `README.md`
- `README.ko.md`
- `docs/BENCHMARKS.md`
- `docs/benchmarks/latest.md`

## Contracts
- English and Korean onboarding describe the same behavior.
- The main README gives one primary install route per agent surface.
- Approximate orientation ratios are never presented as billed tokens or patch-quality evidence.
- Internal audit notes do not crowd the public getting-started path.

## Common Failure Modes
- README examples drift from the packaged CLI.
- A benchmark number is copied without its method or limitations.
- Demo output shows a setup flow that normal first-run work no longer uses.
