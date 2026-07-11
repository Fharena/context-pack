# Context Pack Benchmark Run

- Generated at: 2026-07-12T02:58:48+09:00
- Engine version: `0.4.0`
- Subject HEAD: `0d7973562a68`
- Public scenarios: 10
- Weak public scenarios: 0

## Public Orientation Results

| Scenario | Repo | Prompt | Selected | Search Scope / Repo Tokens | Ratio | Duration | Flags |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| sampleproject-ci | `pypa/sampleproject` | `ci is red` | `automation, source, tests` | ~2.2k / ~3.3k | 65% | 343 ms | ok |
| requests-tests | `psf/requests` | `why are tests failing` | `source, tests` | ~41.3k / ~386.9k | 11% | 432 ms | ok |
| click-shell-completion | `pallets/click` | `fix shell completion bug` | `source, tests` | ~101.9k / ~365.7k | 28% | 357 ms | ok |
| httpx-build | `encode/httpx` | `build failed` | `automation, source, tests` | ~88.5k / ~247.7k | 36% | 420 ms | ok |
| browserquest-mobile | `mozilla/BrowserQuest` | `fix mobile controls bug on touch devices` | `source` | ~98.2k / ~602.2k | 16% | 751 ms | ok |
| browserquest-assets | `mozilla/BrowserQuest` | `fix missing sprite asset loading bug` | `assets, source` | ~98.2k / ~602.2k | 16% | 697 ms | ok |
| browserquest-websocket | `mozilla/BrowserQuest` | `debug websocket login connect failure` | `source` | ~98.2k / ~602.2k | 16% | 655 ms | ok |
| gin-middleware | `gin-gonic/gin` | `fix middleware panic bug` | `source, tests` | ~9.0k / ~217.6k | 4% | 771 ms | ok |
| express-router | `expressjs/express` | `fix router middleware error handling` | `source` | ~15.5k / ~177.9k | 9% | 430 ms | ok |
| fd-rust-filter | `sharkdp/fd` | `fix regex filter bug` | `source, tests` | ~6.3k / ~141.1k | 4% | 383 ms | ok |

## Handoff Replay

- Same routing signature after local clone: yes
- Source signature: `{"orientation_entries": 2, "orientation_files": 2, "read_first_entries": 0, "repo_tokens": 3665, "scope_ratio": 1, "scope_tokens": 34, "search_scope_entries": 2, "selected": ["source", "tests"]}`
- Clone signature: `{"orientation_entries": 2, "orientation_files": 2, "read_first_entries": 0, "repo_tokens": 3665, "scope_ratio": 1, "scope_tokens": 34, "search_scope_entries": 2, "selected": ["source", "tests"]}`

## Weak Spots

- none under this benchmark's thresholds

## Limits

- Search-scope counts are approximate `chars/4` candidate-text estimates, not files actually read or provider billing tokens.
- Durations are local wall-clock checks for regression signals and are machine/cache dependent.
- This measures deterministic orientation and replay, not independent agent patch quality.
- Public repos are shallow clones at the recorded HEAD.
