# Codex CLI Agent A/B

- Generated at: 2026-07-12T02:50:01+09:00
- Codex CLI: `codex-cli 0.144.0-alpha.4`
- Context Pack: `context-pack 0.4.0`
- Context Pack engine SHA-256: `85c13db7b111d5af1681c4315844c920f4519b09cee2885460db585c7ae3f424`
- Model: `gpt-5.6-sol`; reasoning: `low`
- Scenario: `zoning` (domain-routed mobile edge transition regression)
- Subject: `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c` with the same hidden seeded regression
- Trials: 5 per condition; max parallel workers: 2

## Aggregate

| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 5/5 | 111,828 | 101,287-247,516 | +0.0% | 20,948 | +0.0% | 38.2s | +0.0% |
| curated | 5/5 | 68,075 | 53,486-82,548 | +39.1% | 6,905 | +67.0% | 43.7s | +14.3% |

## Agent Loop

| Condition | Median commands | Median tool output chars | Largest single tool output |
| --- | ---: | ---: | ---: |
| baseline | 4.0 | 47,809 | 1,048,576 |
| curated | 5.0 | 4,298 | 3,364 |

## Runs

| Run | Condition | Status | Input | Cached | Output | Commands | Tool chars | Time | Fixed | Minimal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| baseline-1 | baseline | ok | 235,269 | 197,632 | 1,142 | 6 | 653,594 | 56.2s | yes | yes |
| baseline-2 | baseline | ok | 247,516 | 208,896 | 1,068 | 6 | 1,079,159 | 51.5s | yes | yes |
| baseline-3 | baseline | ok | 104,225 | 86,784 | 778 | 3 | 43,940 | 37.2s | yes | yes |
| baseline-4 | baseline | ok | 111,828 | 90,880 | 906 | 3 | 47,809 | 38.2s | yes | yes |
| baseline-5 | baseline | ok | 101,287 | 86,528 | 834 | 4 | 31,854 | 37.4s | yes | yes |
| curated-1 | curated | ok | 68,089 | 61,184 | 889 | 5 | 4,298 | 43.7s | yes | yes |
| curated-2 | curated | ok | 53,486 | 47,104 | 675 | 3 | 4,005 | 34.6s | yes | yes |
| curated-3 | curated | ok | 82,548 | 74,240 | 1,175 | 6 | 4,872 | 49.2s | yes | yes |
| curated-4 | curated | ok | 53,494 | 47,104 | 668 | 3 | 4,006 | 34.7s | yes | yes |
| curated-5 | curated | ok | 68,075 | 57,088 | 916 | 5 | 5,395 | 46.2s | yes | yes |

## Interpretation Limits

- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.
- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.
- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.
- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.
- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.
- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.
