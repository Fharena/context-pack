# Context Pack Benchmark Run

- Generated at: 2026-06-30T14:18:27+09:00
- Engine version: `0.2.20`
- Subject HEAD: `d3cf9a783ace`
- Public scenarios: 10
- Weak public scenarios: 0

## Public Orientation Results

| Scenario | Repo | Prompt | Selected | Read / Repo Tokens | Ratio | Duration | Flags |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| sampleproject-ci | `pypa/sampleproject` | `ci is red` | `automation, source, tests` | ~2.2k / ~3.3k | 67% | 392 ms | ok |
| requests-tests | `psf/requests` | `why are tests failing` | `source, tests` | ~103.7k / ~386.9k | 27% | 349 ms | ok |
| click-shell-completion | `pallets/click` | `fix shell completion bug` | `source, tests` | ~210.1k / ~357.8k | 59% | 670 ms | ok |
| httpx-build | `encode/httpx` | `build failed` | `automation, source, tests` | ~196.6k / ~247.7k | 79% | 390 ms | ok |
| browserquest-mobile | `mozilla/BrowserQuest` | `fix mobile controls bug on touch devices` | `source` | ~98.2k / ~602.2k | 16% | 384 ms | ok |
| browserquest-sprites | `mozilla/BrowserQuest` | `fix missing sprite asset loading bug` | `source, sprites` | ~103.6k / ~602.2k | 17% | 380 ms | ok |
| browserquest-websocket | `mozilla/BrowserQuest` | `debug websocket login connect failure` | `source` | ~98.2k / ~602.2k | 16% | 345 ms | ok |
| gin-middleware | `gin-gonic/gin` | `fix middleware panic bug` | `source` | ~8.8k / ~217.6k | 4% | 433 ms | ok |
| express-router | `expressjs/express` | `fix router middleware error handling` | `source` | ~15.5k / ~177.8k | 9% | 308 ms | ok |
| fd-rust-filter | `sharkdp/fd` | `fix regex filter bug` | `source` | ~41.8k / ~138.6k | 30% | 265 ms | ok |

## Handoff Replay

- Same routing signature after local clone: yes
- Source signature: `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 9, "read_tokens": 404, "repo_tokens": 4427, "selected": ["source", "tests"]}`
- Clone signature: `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 9, "read_tokens": 404, "repo_tokens": 4427, "selected": ["source", "tests"]}`

## Weak Spots

- none under this benchmark's thresholds

## Limits

- Token counts are approximate `chars/4` text-budget estimates, not provider billing tokens.
- Durations are local wall-clock checks for regression signals and are machine/cache dependent.
- This measures deterministic orientation and replay, not independent agent patch quality.
- Public repos are shallow clones at the recorded HEAD.
