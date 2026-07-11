# Context Pack Benchmarks

Context Pack has two different benchmark layers. Do not mix their numbers.

1. **Codex CLI A/B** records usage reported by the model run and checks the resulting patch.
2. **Deterministic routing** checks area selection and clone replay without running an agent.

Neither layer proves a universal productivity or billing reduction.

## Actual Codex CLI A/B

Run the experiment with:

```bash
python scripts/benchmark_codex_ab.py \
  --scenario zoning \
  --conditions baseline curated \
  --trials 5 \
  --max-workers 2 \
  --json docs/benchmarks/codex-ab-zoning-confirm.json \
  --markdown docs/benchmarks/codex-ab-zoning-confirm.md \
  --fail-on-error
```

The harness:

- shallow-clones `mozilla/BrowserQuest` at `af32d247cac3`;
- hides the same mobile zoning regression inside the shallow root commit;
- creates isolated baseline and curated Context Pack checkouts;
- runs Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol`, low reasoning, ephemerally;
- runs at most two trials in parallel;
- reads `turn.completed.usage` from JSONL;
- verifies the expected source repair and that no unrelated file changed.

### Five-Run Confirmation

| Condition | Correct minimal patch | Median total input | Total range | Median uncached input | Median duration |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 5/5 | 107,339 | 83,106-226,500 | 18,520 | 43.6s |
| Curated Context Pack | 5/5 | 125,848 | 118,769-153,498 | 15,890 | 45.1s |

Compared with baseline, curated Context Pack used **17.2% more median total input**, **14.2% less median uncached input**, and **3.4% more median time**. Its largest run was 153,498 total input tokens versus baseline's 226,500.

This is a mixed result, not a token-saving headline. The context route reduced newly processed exploration and tail size, while the extra tool turn added cached input. Billing systems may price cached input differently, but this repository does not convert the result into a cost claim.

The exact result is in [`codex-ab-zoning-confirm.md`](benchmarks/codex-ab-zoning-confirm.md) and [`codex-ab-zoning-confirm.json`](benchmarks/codex-ab-zoning-confirm.json). Raw JSONL traces and patches are retained only in the local benchmark work directory because they contain machine paths and verbose model output.

## Product Changes Found By A/B

The first A/B runs exposed two real design failures:

- A pack described globs and large files as `Read First`, so agents sometimes loaded whole files instead of searching bounded regions.
- Transient packs under `.git` could be unwritable inside a Codex workspace sandbox, causing retries and extra turns.

The engine now emits `Search First` terms and scopes, tells agents to inspect bounded matches, prints packs inline, and leaves transient first runs file-free. The skill also skips Context Pack when one precise search can localize the task.

## Deterministic Routing

The older public-repository harness remains useful for regression testing:

```bash
python scripts/benchmark_context_pack.py \
  --public \
  --json docs/benchmarks/latest.json \
  --markdown docs/benchmarks/latest.md \
  --fail-on-weak
```

Its 10 public scenarios validate expected area roles, runtime thresholds, and fresh-clone handoff replay. Historical `chars/4` ratios describe candidate text scope only. They are not actual model tokens and should not be used as the primary sales claim.

## Limits

- Five trials per arm are still a small sample.
- Model behavior varies even with the same prompt and repository.
- Parallel trials reduce wall-clock time but can share prefix-cache and service-load conditions.
- CLI `input_tokens` is cumulative across model turns; it is not peak context-window occupancy.
- `uncached_input_tokens` is newly processed input, not a direct invoice amount.
- One seeded legacy JavaScript bug does not establish general patch quality.

The next useful expansion is multiple task classes with at least 10-20 trials per arm: precise bug, domain-routed bug, branch review, and session continuation.
