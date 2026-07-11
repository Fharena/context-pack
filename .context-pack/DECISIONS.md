# Decisions

Only durable product and architecture choices belong here. Git history carries implementation detail.

## 2026-07-11: First Run Is Transient

Normal agent orientation must not modify tracked repository files. `start` infers an in-memory manifest and writes only under Git metadata or a temporary directory. Persistent `.context-pack/` files and agent rules require explicit `setup`. Tiny unconfigured repositories may skip pack creation entirely.

## 2026-07-11: Agents Interpret Intent

Natural-language understanding belongs to the coding agent. The skill maps user intent to explicit CLI operations such as task start, review, and checkpoint. The deterministic CLI does not maintain a bilingual lifecycle phrase classifier.

## 2026-07-11: Routing Must Stay Generic

First-run routing uses generic area roles and bounded entry-point globs. Public benchmark repositories must not gain dedicated buckets or vocabulary solely to improve benchmark scores.

## 2026-07-11: Evidence Is Orientation Evidence

`chars/4` numbers describe approximate first-read text scope only. They are never billed-token, answer-consistency, or patch-quality claims. Independent-agent A/B testing is a separate proof milestone.

## 2026-07-11: Actual Token Evidence Must Stay Honest

Codex CLI A/B uses reported cumulative input and derives uncached input separately. The first search-only confirmation reduced median uncached input and the worst total-input run, but increased median total input and latency. Later evidence-first runs may improve those numbers, but one curated task never becomes a universal token or cost claim.

## 2026-07-12: Route To Current Source Evidence

Agent mode returns at most two bounded, line-numbered regions from changed files or configured start files. Strong configured symbols run before task-word fallback. When the root cause is visible, agents edit directly instead of reopening the same range. Contracts and failure modes are ranked after area selection and cannot route unrelated work.

## 2026-07-12: Optimize Model Turns, Not Pack Size Alone

The search-only pack reduced raw exploration but added a model turn, increasing cumulative input. Agent output therefore removes duplicate preambles, limits primary areas and guardrails, exposes one verification command, and measures command count and tool-output size alongside tokens. Prompt-cache hits are not treated as removed context.

## 2026-07-12: Benchmarks Must Pin The Engine Under Test

Agent A/B trials place the working-tree Context Pack command on an isolated PATH. A global CLI is never trusted because version drift can add failed retries and invalidate usage comparisons. Every public aggregate records the exact engine SHA.

## 2026-07-11: Search Scopes Are Not Read Lists

Task packs route with bounded terms and search scopes. Files, directories, and globs are candidates for targeted search, not instructions to load all content. Inline output avoids a second pack read and transient first use leaves no files behind.

## 2026-07-11: Neglect Must Be Bounded

Published and local checkpoint logs rotate, generated state remains ignored, normal start avoids full-repo statistics, and doctor warns about overly broad areas. The library should degrade into warnings and source verification instead of growing without limit.

## 2026-07-11: Packaged Resources Are Synchronized

The canonical engine, skill, agent metadata, and plugin manifest remain readable source files. A deterministic sync script creates package resources, and CI fails when copies drift.
