# Context Pack v0.5.0 Codex A/B Summary

This summary combines four independently generated aggregate files. Every run used Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol` with low reasoning, `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c`, and Context Pack engine SHA-256 `a355e2e8f6d2418f8cbaa22948f8c911fc27447d47fc18d90208e7100b34acab`.

| Scenario | Trials/arm | Baseline | Transient | Maintained | Maintained total change | Maintained uncached change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Precise mobile touch bug | 3 | 3/3 | 3/3 | 3/3 | 29.4% less | 41.6% less |
| Domain-routed zoning bug | 5 | 5/5 | 2/5 | 5/5 | 37.5% less | 44.1% less |
| Branch review | 3 | 3/3 | 3/3 | 3/3 | 16.5% less | 44.1% less |
| Session continuation | 3 | 3/3 | 3/3 | 3/3 | 21.3% less | 48.7% less |

Totals: baseline **14/14**, transient **11/14**, maintained **14/14** correct. Counts combine different task classes and are descriptive, not a significance test.

The transient condition is not the v0.5.0 default. Its 2/5 domain result and median total-input regressions of 14.1% on domain routing and 41.3% on continuation caused the installed skill to use ordinary targeted search in unconfigured repositories. Automatic Context Pack routing is reserved for repositories with a maintained `.context-pack/` library.

Source aggregates: [touch JSON](codex-ab-v050-touch.json), [zoning JSON](codex-ab-v050-zoning.json), [review JSON](codex-ab-v050-review.json), and [continuation JSON](codex-ab-v050-continuation.json). See [the benchmark methodology and limits](../BENCHMARKS.md) before quoting these numbers.
