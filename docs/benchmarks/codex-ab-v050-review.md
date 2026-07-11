# Codex CLI Agent A/B

- Generated at: 2026-07-12T04:56:19+09:00
- Codex CLI: `codex-cli 0.144.0-alpha.4`
- Context Pack: `context-pack 0.5.0`
- Context Pack engine SHA-256: `a355e2e8f6d2418f8cbaa22948f8c911fc27447d47fc18d90208e7100b34acab`
- Model: `gpt-5.6-sol`; reasoning: `low`
- Scenario: `review-zoning` (branch review of a mobile edge transition regression)
- Subject: `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c` with the same hidden seeded regression
- Trials: 3 per condition; max parallel workers: 2

## Aggregate

| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3/3 | 67,667 | 66,649-86,357 | +0.0% | 14,933 | +0.0% | 28.5s | +0.0% |
| transient | 3/3 | 52,237 | 50,709-52,802 | +22.8% | 7,181 | +51.9% | 29.4s | +3.0% |
| curated | 3/3 | 56,479 | 40,735-58,610 | +16.5% | 8,351 | +44.1% | 31.3s | +9.9% |

## Agent Loop

| Condition | Median commands | First target-file command | Median tool output chars | Largest single tool output |
| --- | ---: | ---: | ---: | ---: |
| baseline | 3.0 | 2.0 | 108,187 | 104,245 |
| transient | 3.0 | 3.0 | 7,245 | 6,026 |
| curated | 3.0 | 2.0 | 12,127 | 6,446 |

## Runs

| Run | Condition | Status | Input | Cached | Output | Commands | First target | Tool chars | Time | Fixed | Minimal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| baseline-1 | baseline | ok | 86,357 | 71,424 | 629 | 4 | 2 | 108,187 | 30.2s | yes | yes |
| baseline-2 | baseline | ok | 67,667 | 41,984 | 533 | 3 | 2 | 108,631 | 28.5s | yes | yes |
| baseline-3 | baseline | ok | 66,649 | 53,248 | 424 | 3 | 2 | 105,457 | 23.9s | yes | yes |
| curated-1 | curated | ok | 40,735 | 34,048 | 482 | 2 | 2 | 9,618 | 29.8s | yes | yes |
| curated-2 | curated | ok | 56,479 | 48,128 | 514 | 3 | 2 | 12,127 | 31.3s | yes | yes |
| curated-3 | curated | ok | 58,610 | 49,152 | 521 | 3 | 2 | 13,698 | 35.2s | yes | yes |
| transient-1 | transient | ok | 52,802 | 43,008 | 504 | 3 | 3 | 9,636 | 26.1s | yes | yes |
| transient-2 | transient | ok | 52,237 | 45,056 | 492 | 3 | 3 | 7,245 | 31.8s | yes | yes |
| transient-3 | transient | ok | 50,709 | 44,032 | 564 | 3 | 3 | 3,253 | 29.4s | yes | yes |

## Interpretation Limits

- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.
- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.
- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.
- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.
- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.
- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.
