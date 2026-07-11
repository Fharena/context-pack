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
  --json docs/benchmarks/codex-ab-zoning-evidence.json \
  --markdown docs/benchmarks/codex-ab-zoning-evidence.md \
  --fail-on-error
```

The harness:

- shallow-clones `mozilla/BrowserQuest` at `af32d247cac3`;
- hides the same mobile zoning regression inside the shallow root commit;
- creates isolated baseline and curated Context Pack checkouts;
- runs Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol`, low reasoning, ephemerally;
- puts the exact working-tree Context Pack engine on the agent PATH instead of trusting a global install;
- runs at most two trials in parallel;
- reads `turn.completed.usage` from JSONL;
- records command count, total tool-output characters, and the largest single tool output;
- verifies the expected source repair and that no unrelated file changed.

### Five-Run Confirmation

| Condition | Correct minimal patch | Median total input | Median uncached | Commands | Tool chars | Median duration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 5/5 | 111,828 | 20,948 | 4 | 47,809 | 38.2s |
| Evidence-first curated | 5/5 | 68,075 | 6,905 | 5 | 4,298 | 43.7s |

Compared with baseline, evidence-first curated Context Pack used **39.1% less median total input**, **67.0% less median uncached input**, and **91.0% less median tool output**. Median command count increased from 4 to 5 and median time increased **14.3%**. Total-input ranges were 101,287-247,516 for baseline and 53,486-82,548 for curated. The largest single tool result was 1,048,576 characters for baseline and 3,364 for curated.

All curated traces used the embedded source evidence to edit without reopening the shown range. Remaining calls were verification and final diff or package inspection. Lower token volume did not guarantee lower latency in this batch. This is still one seeded task with maintained symbols, contracts, and a verification command. Billing systems may price cached input differently, and this repository does not convert the result into a universal cost claim.

The exact v0.4.0 result is in [`codex-ab-zoning-evidence.md`](benchmarks/codex-ab-zoning-evidence.md) and [`codex-ab-zoning-evidence.json`](benchmarks/codex-ab-zoning-evidence.json). The earlier search-only result remains in [`codex-ab-zoning-confirm.md`](benchmarks/codex-ab-zoning-confirm.md). Raw JSONL traces and patches remain local because they contain machine paths and verbose model output.

## Product Changes Found By A/B

The A/B iterations exposed several real design failures:

- A pack described globs and large files as `Read First`, so agents sometimes loaded whole files instead of searching bounded regions.
- Transient packs under `.git` could be unwritable inside a Codex workspace sandbox, causing retries and extra turns.
- Search-only Context Pack added a model turn, so median total input increased even while uncached input fell.
- The benchmark initially picked up a globally installed old CLI, making a new flag fail before the working-tree engine ran.
- Supplying two verification commands caused two separate model turns.

The engine now returns at most two bounded source regions from strong configured symbols, emits compact agent-only output without a duplicate preamble, limits routing to two primary areas, ranks three contracts, two failure modes, and one verification command, and keeps transient first runs file-free. The benchmark injects the exact engine through an isolated PATH shim.

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
- Tool-output characters explain exploration shape but are not tokens.
- One seeded legacy JavaScript bug does not establish general patch quality.

The next useful expansion is multiple task classes with at least 10-20 trials per arm: precise bug, domain-routed bug, branch review, and session continuation.
