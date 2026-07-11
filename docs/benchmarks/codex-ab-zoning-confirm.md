# Codex CLI Agent A/B

- Generated at: 2026-07-11T20:22:35+09:00
- Codex CLI: `codex-cli 0.144.0-alpha.4`
- Context Pack: `context-pack 0.3.0`
- Context Pack engine SHA-256: `52f379af2c27f9838b56a36145acac6a339f5cf951511872070b6fd57096f085`
- Model: `gpt-5.6-sol`; reasoning: `low`
- Scenario: `zoning` (domain-routed mobile edge transition regression)
- Subject: `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c` with the same hidden seeded regression
- Trials: 5 per condition; max parallel workers: 2

## Aggregate

| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 5/5 | 107,339 | 83,106-226,500 | +0.0% | 18,520 | +0.0% | 43.6s | +0.0% |
| curated | 5/5 | 125,848 | 118,769-153,498 | -17.2% | 15,890 | +14.2% | 45.1s | +3.4% |

## Runs

| Run | Condition | Status | Input | Cached | Output | Time | Fixed | Minimal |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-1 | baseline | ok | 106,328 | 87,808 | 1,230 | 43.6s | yes | yes |
| baseline-2 | baseline | ok | 83,106 | 65,536 | 815 | 34.1s | yes | yes |
| baseline-3 | baseline | ok | 226,500 | 192,512 | 1,306 | 50.3s | yes | yes |
| baseline-4 | baseline | ok | 155,420 | 131,328 | 1,120 | 43.7s | yes | yes |
| baseline-5 | baseline | ok | 107,339 | 88,832 | 1,087 | 40.6s | yes | yes |
| curated-1 | curated | ok | 127,762 | 111,872 | 1,143 | 45.1s | yes | yes |
| curated-2 | curated | ok | 122,974 | 107,776 | 1,107 | 45.1s | yes | yes |
| curated-3 | curated | ok | 153,498 | 136,192 | 1,223 | 55.5s | yes | yes |
| curated-4 | curated | ok | 125,848 | 110,848 | 1,102 | 46.7s | yes | yes |
| curated-5 | curated | ok | 118,769 | 95,488 | 1,064 | 43.6s | yes | yes |

## Interpretation Limits

- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.
- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.
- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.
- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.
- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.
- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.
