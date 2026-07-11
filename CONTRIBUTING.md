# Contributing

Thanks for helping improve Context Pack.

## Development Setup

Context Pack is intentionally stdlib-only. No package install is required for the core engine.

Run tests:

```bash
python scripts/sync_packaged_assets.py --check
python -m unittest discover -s tests -v
python scripts/validate_packaged_cli.py
```

Run the opt-in, model-using A/B benchmark only when actual Codex usage evidence is needed:

```bash
python scripts/benchmark_codex_ab.py --scenario zoning --conditions baseline curated --trials 5 --max-workers 2
```

This consumes model tokens. Keep total, cached, uncached, latency, and patch-quality results together when reporting it.

Run the repo doctor:

```bash
context-pack doctor
```

## Project Layout

- `plugins/context-pack/skills/context-pack/scripts/context_pack.py`: deterministic engine
- `plugins/context-pack/skills/context-pack/SKILL.md`: Codex skill instructions
- `plugins/context-pack/.codex-plugin/plugin.json`: Codex plugin metadata
- `src/context_pack/bundled/`: synchronized resources used by installed packages
- `scripts/sync_packaged_assets.py`: updates and verifies packaged copies
- `.context-pack/`: project context library
- `tests/`: unit tests

## Pull Requests

Keep changes focused. If you change command behavior, update:

- tests
- `README.md` and `README.ko.md` when user-facing commands change
- `.context-pack/manifest.json` or `AREAS/*.md` when routing changes
- `CHANGELOG.md` for release-visible changes

## Design Rules

- Prefer deterministic script logic for factual repo state.
- Use agent judgment only for semantic summaries, contracts, failure modes, and decisions.
- Keep generated files under `.context-pack/packs/` and out of git.
- Treat context docs as routing hints, not source of truth.
- Keep natural-language intent interpretation in the agent skill; keep CLI operations explicit.
- Run `python scripts/sync_packaged_assets.py` after changing the engine, skill, agent metadata, or plugin manifest.
