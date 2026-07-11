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

## 2026-07-11: Actual Token Evidence Must Stay Mixed

Codex CLI A/B uses reported cumulative input and derives uncached input separately. The first current-code confirmation reduced median uncached input and the worst total-input run, but increased median total input and latency. Until broader paired trials disagree, the product does not claim universal token or cost savings.

## 2026-07-11: Search Scopes Are Not Read Lists

Task packs route with bounded terms and search scopes. Files, directories, and globs are candidates for targeted search, not instructions to load all content. Inline output avoids a second pack read and transient first use leaves no files behind.

## 2026-07-11: Neglect Must Be Bounded

Published and local checkpoint logs rotate, generated state remains ignored, normal start avoids full-repo statistics, and doctor warns about overly broad areas. The library should degrade into warnings and source verification instead of growing without limit.

## 2026-07-11: Packaged Resources Are Synchronized

The canonical engine, skill, agent metadata, and plugin manifest remain readable source files. A deterministic sync script creates package resources, and CI fails when copies drift.
