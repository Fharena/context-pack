# Context Pack Benchmark Run

- Generated at: 2026-07-11T19:21:09+09:00
- Engine version: `0.3.0`
- Subject HEAD: `7beb3041dbe9`
- Public scenarios: 10
- Weak public scenarios: 0

## Public Orientation Results

| Scenario | Repo | Prompt | Selected | Read / Repo Tokens | Ratio | Duration | Flags |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| sampleproject-ci | `pypa/sampleproject` | `ci is red` | `automation, source, tests` | ~2.2k / ~3.3k | 65% | 314 ms | ok |
| requests-tests | `psf/requests` | `why are tests failing` | `source, tests` | ~41.3k / ~386.9k | 11% | 398 ms | ok |
| click-shell-completion | `pallets/click` | `fix shell completion bug` | `source, tests` | ~101.9k / ~365.7k | 28% | 348 ms | ok |
| httpx-build | `encode/httpx` | `build failed` | `automation, source, tests` | ~88.5k / ~247.7k | 36% | 361 ms | ok |
| browserquest-mobile | `mozilla/BrowserQuest` | `fix mobile controls bug on touch devices` | `source` | ~98.2k / ~602.2k | 16% | 645 ms | ok |
| browserquest-assets | `mozilla/BrowserQuest` | `fix missing sprite asset loading bug` | `assets, source` | ~98.2k / ~602.2k | 16% | 292 ms | ok |
| browserquest-websocket | `mozilla/BrowserQuest` | `debug websocket login connect failure` | `source` | ~98.2k / ~602.2k | 16% | 281 ms | ok |
| gin-middleware | `gin-gonic/gin` | `fix middleware panic bug` | `source, tests` | ~9.0k / ~217.6k | 4% | 473 ms | ok |
| express-router | `expressjs/express` | `fix router middleware error handling` | `source` | ~15.5k / ~177.9k | 9% | 303 ms | ok |
| fd-rust-filter | `sharkdp/fd` | `fix regex filter bug` | `source, tests` | ~6.3k / ~141.1k | 4% | 283 ms | ok |

## Handoff Replay

- Same routing signature after local clone: yes
- Source signature: `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 12, "read_tokens": 408, "repo_tokens": 3310, "selected": ["source", "tests"]}`
- Clone signature: `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 12, "read_tokens": 408, "repo_tokens": 3310, "selected": ["source", "tests"]}`

## Weak Spots

- none under this benchmark's thresholds

## Limits

- Token counts are approximate `chars/4` text-budget estimates, not provider billing tokens.
- Durations are local wall-clock checks for regression signals and are machine/cache dependent.
- This measures deterministic orientation and replay, not independent agent patch quality.
- Public repos are shallow clones at the recorded HEAD.
