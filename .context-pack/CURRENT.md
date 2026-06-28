# Current Handoff

<!-- context-pack:fingerprint:start -->
- Repo root: D:\SJWORK\my_project_memory
- Git repo: yes
- Branch: main
- HEAD: 81d36d6db1c8
- Dirty files: none
- Dirty diff hash: clean
- Updated at: 2026-06-28T21:40:22+09:00
<!-- context-pack:fingerprint:end -->
## Active Goal
- Product hardening for Context Pack. Latest work: `81d36d6 feat: support Korean natural start phrases` routes "버그 고쳐줘" to source/tests, "브랜치 리뷰해줘" to review mode, and "나중에 이어가게 정리해줘" to checkpoint guidance while avoiding meta-task false positives.

## Read First
1. `.context-pack/CURRENT.md`
2. `.context-pack/INDEX.md`
3. The relevant `.context-pack/AREAS/*.md` files

## Next Actions
1. Watch CI after pushing the latest handoff.
2. Next product iteration: test Context Pack on 3-5 external repos and collect before/after orientation examples.
3. Improve registry publishing readiness only after the lightweight skill UX stays stable.

## Watch Outs
- Treat stale context as a hint, not a fact.
- Check the source-of-truth checkout before editing.
- `context-pack setup --dry-run` now preserves this repo's curated manifest by default; use `--infer-areas` only when intentionally expanding area docs.
- Text-budget metrics are approximate (`chars/4`) and should be described as context-size guidance, not exact billing tokens.

## Last Verified
- `python -m unittest discover -s tests -v` (65 passed)
- `python scripts/validate_packaged_cli.py`
- `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
- `python -m json.tool .agents/plugins/marketplace.json`
- `git diff --check`
- temporary repo smoke: `context-pack start --task "버그 고쳐줘"` selects source/tests
- temporary repo smoke: `context-pack start --task "브랜치 리뷰해줘"` produces a review pack with only the changed source area
- `npm pack --dry-run`
- `python -m build`
- `python -m twine check dist/*`
