# Context Pack Benchmarks

These results test Context Pack as a deterministic orientation layer. They do not claim a universal token-saving rate or prove that an agent writes a better patch.

## Method

- Date: 2026-07-11
- Engine: `0.3.0`
- Command: `python scripts/benchmark_context_pack.py --public --fail-on-weak`
- Inputs: 10 shallow public-repository clones with no Context Pack setup, plus one local handoff replay
- Estimate: readable text characters divided by four; ignored, binary, empty, unreadable, and files over 1 MB are excluded
- Pass condition: expected area roles selected, scenario-specific read-ratio ceiling met, no empty first-read route, routing completed under five seconds

The exact generated artifacts are [`benchmarks/latest.md`](benchmarks/latest.md) and [`benchmarks/latest.json`](benchmarks/latest.json).

## Latest Results

| Scenario | Repository | Selected first | Approx. first read / repo | Ratio |
| --- | --- | --- | ---: | ---: |
| CI failure | `pypa/sampleproject` | automation, source, tests | 2.2k / 3.3k | 65% |
| Test failure | `psf/requests` | source, tests | 41.3k / 386.9k | 11% |
| Shell completion | `pallets/click` | source, tests | 101.9k / 365.7k | 28% |
| Build failure | `encode/httpx` | automation, source, tests | 88.5k / 247.7k | 36% |
| Mobile controls | `mozilla/BrowserQuest` | source | 98.2k / 602.2k | 16% |
| Asset loading | `mozilla/BrowserQuest` | assets, source | 98.2k / 602.2k | 16% |
| WebSocket login | `mozilla/BrowserQuest` | source | 98.2k / 602.2k | 16% |
| Middleware panic | `gin-gonic/gin` | source, tests | 9.0k / 217.6k | 4% |
| Router errors | `expressjs/express` | source | 15.5k / 177.9k | 9% |
| Regex filter | `sharkdp/fd` | source, tests | 6.3k / 141.1k | 4% |

All 10 scenarios passed their declared thresholds. These ratios describe the files named in the first-read route, not all files an agent may eventually inspect.

## Handoff Replay

The harness sets up a synthetic repository, publishes a checkpoint, clones it, and routes the same test-failure task in both checkouts.

- Same routing signature after clone: yes
- Both checkouts: `source, tests`
- Approximate first read: 408 / 3,310 tokens, 12%
- First-read entries: 4 in each checkout

This verifies that git-carried context reproduces deterministic orientation. It does not imply identical natural-language answers or patches from independent agents.

## What Changed During This Run

- Custom area names now receive generic roles such as source, tests, docs, assets, and automation.
- The router no longer contains BrowserQuest-specific sprite/map buckets or benchmark-specific framework words.
- Inferred start files use bounded entry-point globs instead of whole source and test directories.
- Review routing suppresses Context Pack's own metadata when product files also changed.
- Normal `start` no longer scans the whole repository to print an approximate token statistic.

## Limits

- `chars/4` is a text-budget proxy, not provider billing or tokenizer output.
- Local durations are regression signals and vary with machine and filesystem cache.
- The benchmark tests routing and replay, not diagnosis accuracy, patch quality, test success, or task completion time.
- Curated area boundaries can outperform first-run inference; poor boundaries can also make routing worse.
- Source verification remains required.

The next meaningful proof is an independent-agent A/B study with captured reads, first relevant file, elapsed time, test outcome, and blinded patch review. Until then, marketing should describe these numbers as orientation measurements only.
