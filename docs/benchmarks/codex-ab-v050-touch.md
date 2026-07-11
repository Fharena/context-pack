# Codex CLI Agent A/B

- Generated at: 2026-07-12T04:57:08+09:00
- Codex CLI: `codex-cli 0.144.0-alpha.4`
- Context Pack: `context-pack 0.5.0`
- Context Pack engine SHA-256: `a355e2e8f6d2418f8cbaa22948f8c911fc27447d47fc18d90208e7100b34acab`
- Model: `gpt-5.6-sol`; reasoning: `low`
- Scenario: `touch` (precise mobile touch regression)
- Subject: `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c` with the same hidden seeded regression
- Trials: 3 per condition; max parallel workers: 2

## Aggregate

| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3/3 | 96,119 | 89,655-104,202 | +0.0% | 13,111 | +0.0% | 37.2s | +0.0% |
| transient | 3/3 | 74,558 | 74,077-74,564 | +22.4% | 11,869 | +9.5% | 38.3s | +3.2% |
| curated | 3/3 | 67,823 | 53,911-69,869 | +29.4% | 7,663 | +41.6% | 40.0s | +7.5% |

## Agent Loop

| Condition | Median commands | First target-file command | Median tool output chars | Largest single tool output |
| --- | ---: | ---: | ---: | ---: |
| baseline | 3.0 | 2.0 | 24,824 | 30,972 |
| transient | 3.0 | 2.0 | 13,155 | 7,441 |
| curated | 3.0 | 2.0 | 4,721 | 3,317 |

## Runs

| Run | Condition | Status | Input | Cached | Output | Commands | First target | Tool chars | Time | Fixed | Minimal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| baseline-1 | baseline | ok | 89,655 | 76,544 | 791 | 3 | 2 | 24,824 | 46.0s | yes | yes |
| baseline-2 | baseline | ok | 96,119 | 84,480 | 834 | 4 | 3 | 19,417 | 37.2s | yes | yes |
| baseline-3 | baseline | ok | 104,202 | 85,760 | 778 | 3 | 2 | 36,001 | 33.8s | yes | yes |
| curated-1 | curated | ok | 53,911 | 47,104 | 641 | 3 | 2 | 4,721 | 40.0s | yes | yes |
| curated-2 | curated | ok | 67,823 | 60,160 | 694 | 3 | 2 | 5,035 | 45.3s | yes | yes |
| curated-3 | curated | ok | 69,869 | 61,184 | 620 | 3 | 2 | 4,216 | 35.2s | yes | yes |
| transient-1 | transient | ok | 74,558 | 65,280 | 787 | 3 | 2 | 13,155 | 36.1s | yes | yes |
| transient-2 | transient | ok | 74,564 | 62,208 | 834 | 3 | 2 | 13,597 | 38.3s | yes | yes |
| transient-3 | transient | ok | 74,077 | 62,208 | 771 | 3 | 2 | 12,952 | 39.8s | yes | yes |

## Interpretation Limits

- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.
- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.
- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.
- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.
- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.
- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.
