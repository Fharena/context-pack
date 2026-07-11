# Context Pack Benchmarks

Context Pack has two benchmark layers. Do not mix their numbers.

1. **Codex CLI A/B** records model-reported usage and checks the resulting patch or review finding.
2. **Deterministic routing** checks area selection and clone replay without running an agent.

Neither layer proves universal productivity, billing savings, or human adoption.

## v0.5.0 Codex CLI A/B

The release benchmark uses `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c`, Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol`, low reasoning, and the exact working-tree engine recorded in each JSON file.

Three conditions are isolated in separate clones:

- **baseline**: no Context Pack files or instructions;
- **transient**: an experimental cold-start policy with inferred routing but no maintained project knowledge;
- **maintained**: a versioned task area with symbols, contracts, failure modes, and one verification command. Review notes are committed on the base branch, not supplied by the branch under review.

The tasks cover a precise touch bug, a domain-vocabulary zoning bug, branch review, and continuation from a checked-in handoff. Fix tasks require the expected source repair and exactly one changed product file. Review requires the correct file and failure mechanism with no edits.

### Maintained Context Results

| Task | Trials/arm | Baseline correct | Maintained correct | Baseline total | Maintained total | Total change | Baseline uncached | Maintained uncached | Uncached change | Time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Precise bug | 3 | 3/3 | 3/3 | 96,119 | 67,823 | 29.4% less | 13,111 | 7,663 | 41.6% less | 7.5% slower |
| Domain-routed bug | 5 | 5/5 | 5/5 | 109,913 | 68,660 | 37.5% less | 19,033 | 10,638 | 44.1% less | 11.6% faster |
| Branch review | 3 | 3/3 | 3/3 | 67,667 | 56,479 | 16.5% less | 14,933 | 8,351 | 44.1% less | 9.9% slower |
| Session continuation | 3 | 3/3 | 3/3 | 68,493 | 53,916 | 21.3% less | 13,453 | 6,907 | 48.7% less | 3.2% faster |

Maintained Context Pack and baseline were both correct in **14/14** runs. Maintained context reached the target file by command 2 in every scenario median; baseline medians ranged from command 2 to 3.

These percentages compare per-scenario medians. They are not pooled billing estimates. Latency improved on two tasks and regressed on two, so the release makes no general speed claim.

### Negative Cold-Start Result

| Task | Transient correct | Median total | Change vs baseline |
| --- | ---: | ---: | ---: |
| Precise bug | 3/3 | 74,558 | 22.4% less |
| Domain-routed bug | 2/5 | 125,356 | 14.1% more |
| Branch review | 3/3 | 52,237 | 22.8% less |
| Session continuation | 3/3 | 96,756 | 41.3% more |

Transient routing was correct in **11/14** runs. Three domain runs changed a nearby but unrelated condition instead of the seeded coordinate defect, and continuation used more cumulative input despite reaching the correct patch. This result removed implicit transient routing from the installed skill: unconfigured repositories now use normal targeted search unless the user explicitly requests a Context Pack preview or evaluation.

### Reproduce

```bash
python scripts/benchmark_codex_ab.py \
  --scenario zoning \
  --conditions baseline transient curated \
  --trials 5 \
  --max-workers 3 \
  --json docs/benchmarks/codex-ab-v050-zoning.json \
  --markdown docs/benchmarks/codex-ab-v050-zoning.md \
  --fail-on-error
```

The harness requires a new or empty `--workdir`, injects the exact engine through an isolated PATH shim, and persists each trial before aggregate rendering. It records cumulative input/cached/uncached usage, command count, first target-file command, tool-output volume, latency, and deterministic quality checks. Committed, uncommitted, and untracked edits count toward patch scope. Non-minimal or incorrect results fail `--fail-on-error` even when the agent exits successfully.

Raw aggregates:

- [Precise bug](benchmarks/codex-ab-v050-touch.json)
- [Domain-routed bug](benchmarks/codex-ab-v050-zoning.json)
- [Branch review](benchmarks/codex-ab-v050-review.json)
- [Session continuation](benchmarks/codex-ab-v050-continuation.json)
- [Human-readable summary](benchmarks/codex-ab-v050-summary.md)

Raw JSONL traces and patches remain in the local benchmark work directories because they contain machine paths and verbose model output.

## Product Changes Found By A/B

The measurements changed the product rather than merely validating it:

- search-only packs added turns and could increase cumulative input;
- large `Read First` scopes caused whole-file and whole-directory reads;
- untrusted branch-authored context could bias a review;
- generic evidence was presented with more confidence than its provenance justified;
- continuation prompts could discard the handoff by inventing a generic task string;
- reused benchmark directories could mistake an old patch for a successful new run;
- inferred transient context could route to the right file while distracting from the actual defect.

v0.5.0 adds evidence confidence, base-sourced review context, handoff-derived continuation routing, explicit verification commands, symbol-health diagnostics, and clean-workdir enforcement. The skill now reserves automatic routing for configured repositories.

## Deterministic Routing

The public-repository regression harness remains useful for non-model checks:

```bash
python scripts/benchmark_context_pack.py \
  --public \
  --json docs/benchmarks/latest.json \
  --markdown docs/benchmarks/latest.md \
  --fail-on-weak
```

Its 10 public scenarios validate expected area roles, runtime thresholds, and fresh-clone handoff replay. Historical `chars/4` ratios describe candidate text scope only. They are not actual model tokens.

## Limits

- There are only 3-5 trials per arm and model behavior varies.
- All agent runs use one model and one pinned legacy JavaScript repository.
- The defects are seeded; review and continuation reuse the zoning defect.
- The project author wrote the maintained area notes, so curation quality is not independent.
- Parallel runs can share service-load and prefix-cache conditions.
- CLI `input_tokens` is cumulative across model turns, not peak context-window occupancy.
- `uncached_input_tokens` is newly processed input, not a direct invoice amount.
- Quality checks are deterministic and task-specific, not human patch review.
- Claude Code and Cursor runtime behavior was not measured in this release.
- No external-user retention, maintenance burden, or time-to-completion study exists yet.

The next evidence milestone is independent maintainers using their own repositories and reporting first-relevant-file time, outcome quality, and upkeep after repeated sessions.
