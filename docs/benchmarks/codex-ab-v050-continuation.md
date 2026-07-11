# Codex CLI Agent A/B

- Generated at: 2026-07-12T04:57:03+09:00
- Codex CLI: `codex-cli 0.144.0-alpha.4`
- Context Pack: `context-pack 0.5.0`
- Context Pack engine SHA-256: `a355e2e8f6d2418f8cbaa22948f8c911fc27447d47fc18d90208e7100b34acab`
- Model: `gpt-5.6-sol`; reasoning: `low`
- Scenario: `continuation-zoning` (session continuation for an unfinished mobile transition fix)
- Subject: `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c` with the same hidden seeded regression
- Trials: 3 per condition; max parallel workers: 2

## Aggregate

| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 3/3 | 68,493 | 67,668-83,301 | +0.0% | 13,453 | +0.0% | 37.9s | +0.0% |
| transient | 3/3 | 96,756 | 84,502-97,123 | -41.3% | 10,262 | +23.7% | 41.0s | +8.1% |
| curated | 3/3 | 53,916 | 53,736-54,011 | +21.3% | 6,907 | +48.7% | 36.7s | -3.2% |

## Agent Loop

| Condition | Median commands | First target-file command | Median tool output chars | Largest single tool output |
| --- | ---: | ---: | ---: | ---: |
| baseline | 3.0 | 3.0 | 8,249 | 16,853 |
| transient | 4.0 | 4.0 | 8,518 | 12,144 |
| curated | 2.0 | 2.0 | 4,333 | 3,586 |

## Runs

| Run | Condition | Status | Input | Cached | Output | Commands | First target | Tool chars | Time | Fixed | Minimal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| baseline-1 | baseline | ok | 83,301 | 69,376 | 1,007 | 3 | 3 | 19,635 | 40.8s | yes | yes |
| baseline-2 | baseline | ok | 68,493 | 55,040 | 906 | 3 | 3 | 8,249 | 37.9s | yes | yes |
| baseline-3 | baseline | ok | 67,668 | 59,136 | 714 | 3 | 3 | 7,832 | 32.8s | yes | yes |
| curated-1 | curated | ok | 54,011 | 47,104 | 645 | 3 | 2 | 4,333 | 36.7s | yes | yes |
| curated-2 | curated | ok | 53,736 | 47,104 | 495 | 2 | 2 | 4,333 | 32.4s | yes | yes |
| curated-3 | curated | ok | 53,916 | 43,008 | 577 | 2 | 2 | 4,333 | 36.9s | yes | yes |
| transient-1 | transient | ok | 96,756 | 83,456 | 745 | 4 | 4 | 14,319 | 35.2s | yes | yes |
| transient-2 | transient | ok | 97,123 | 87,296 | 864 | 5 | 4 | 4,838 | 48.4s | yes | yes |
| transient-3 | transient | ok | 84,502 | 74,240 | 769 | 4 | 4 | 8,518 | 41.0s | yes | yes |

## Interpretation Limits

- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.
- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.
- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.
- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.
- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.
- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.
