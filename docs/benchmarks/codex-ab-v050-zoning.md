# Codex CLI Agent A/B

- Generated at: 2026-07-12T05:00:13+09:00
- Codex CLI: `codex-cli 0.144.0-alpha.4`
- Context Pack: `context-pack 0.5.0`
- Context Pack engine SHA-256: `a355e2e8f6d2418f8cbaa22948f8c911fc27447d47fc18d90208e7100b34acab`
- Model: `gpt-5.6-sol`; reasoning: `low`
- Scenario: `zoning` (domain-routed mobile edge transition regression)
- Subject: `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c` with the same hidden seeded regression
- Trials: 5 per condition; max parallel workers: 2

## Aggregate

| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 5/5 | 109,913 | 107,240-277,028 | +0.0% | 19,033 | +0.0% | 42.5s | +0.0% |
| transient | 2/5 | 125,356 | 98,017-220,418 | -14.1% | 21,420 | -12.5% | 51.3s | +20.7% |
| curated | 5/5 | 68,660 | 56,071-74,894 | +37.5% | 10,638 | +44.1% | 37.6s | -11.6% |

## Agent Loop

| Condition | Median commands | First target-file command | Median tool output chars | Largest single tool output |
| --- | ---: | ---: | ---: | ---: |
| baseline | 3.0 | 2.0 | 47,360 | 914,721 |
| transient | 4.0 | 2.0 | 37,177 | 1,038,528 |
| curated | 3.0 | 2.0 | 4,615 | 8,347 |

## Runs

| Run | Condition | Status | Input | Cached | Output | Commands | First target | Tool chars | Time | Fixed | Minimal |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| baseline-1 | baseline | ok | 277,028 | 211,968 | 1,476 | 6 | 3 | 1,100,070 | 64.9s | yes | yes |
| baseline-2 | baseline | ok | 113,767 | 96,768 | 899 | 4 | 3 | 41,549 | 36.9s | yes | yes |
| baseline-3 | baseline | ok | 108,170 | 89,856 | 770 | 3 | 2 | 49,623 | 100.4s | yes | yes |
| baseline-4 | baseline | ok | 109,913 | 90,880 | 906 | 3 | 2 | 47,360 | 42.5s | yes | yes |
| baseline-5 | baseline | ok | 107,240 | 87,808 | 837 | 3 | 2 | 47,095 | 38.2s | yes | yes |
| curated-1 | curated | ok | 56,071 | 43,008 | 637 | 3 | 2 | 4,321 | 37.2s | yes | yes |
| curated-2 | curated | ok | 74,894 | 64,256 | 762 | 3 | 2 | 13,069 | 37.6s | yes | yes |
| curated-3 | curated | ok | 68,650 | 61,184 | 763 | 3 | 2 | 4,862 | 35.7s | yes | yes |
| curated-4 | curated | ok | 68,660 | 57,088 | 1,002 | 6 | 2 | 4,339 | 46.4s | yes | yes |
| curated-5 | curated | ok | 68,883 | 61,184 | 937 | 5 | 2 | 4,615 | 42.0s | yes | yes |
| transient-1 | transient | ok | 98,017 | 82,688 | 805 | 3 | 2 | 33,511 | 34.6s | yes | yes |
| transient-2 | transient | ok | 125,356 | 103,936 | 1,022 | 4 | 0 | 36,261 | 47.1s | no | yes |
| transient-3 | transient | ok | 220,418 | 174,336 | 1,221 | 5 | 2 | 1,086,441 | 51.3s | no | yes |
| transient-4 | transient | ok | 123,271 | 105,984 | 930 | 4 | 2 | 37,177 | 56.9s | yes | yes |
| transient-5 | transient | ok | 199,472 | 166,656 | 1,195 | 7 | 5 | 478,943 | 54.1s | no | yes |

## Interpretation Limits

- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.
- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.
- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.
- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.
- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.
- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.
