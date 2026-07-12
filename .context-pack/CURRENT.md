# Current Handoff

<!-- context-pack:fingerprint:start -->
- Repo root: D:\SJWORK\my_project_memory
- Git repo: yes
- Branch: main
- HEAD: f450046cf68a
- Dirty files: .context-pack/CURRENT.md
- Dirty diff hash: sha256:d52a9533651dcb3b4881c1ee
- Updated at: 2026-07-12T13:51:31+09:00
<!-- context-pack:fingerprint:end -->
## Active Goal
- Context Pack `v0.5.1` is published with a strict repository trust boundary for manifest paths, automatic Evidence, managed writes, non-Git discovery, and legacy migration.

## Read First
1. `.context-pack/INDEX.md`
2. `docs/releases/v0.5.1.md` and `SECURITY.md` for the security boundary
3. `.context-pack/AREAS/engine.md` for implementation contracts
4. `docs/BENCHMARKS.md` and `docs/benchmarks/codex-ab-v050-summary.md` for current performance evidence

## Next Actions
1. Complete first-package registration and trusted-publisher setup on PyPI/npm; GitHub environments and OIDC workflow jobs already exist.
2. Gather independent field and security reports through GitHub issue #1 and private vulnerability reporting.
3. Run Claude Code/Cursor runtime checks before broad compatibility or productivity claims.

## Watch Outs
- Manifest paths are portable repository-relative paths; area docs stay in `AREAS/`; ignored files, symbolic links, device names, and NTFS stream syntax are excluded from automatic context.
- Packaged validation now uses one automatically cleaned temporary workspace. Keep future test fixtures on D while local C capacity is constrained.
- Maintained context and baseline were both correct in 14/14 author-run BrowserQuest trials, with maintained per-scenario median total input 16.5%-37.5% lower and uncached input 41.6%-48.7% lower.
- Experimental transient routing was correct in 11/14 and increased median total input by 14.1% on the domain task and 41.3% on continuation. It is no longer an automatic skill default.
- Codex CLI reports cumulative input, not peak context-window occupancy; cached-token pricing is provider-specific.
- PyPI/npm names are currently unregistered and npm authentication is absent; do not claim registry publication until account-side setup succeeds.

## Last Verified
- `python -m unittest discover -s tests -v` (106 passed locally; two real-symlink cases skipped only because this Windows account lacks link privilege)
- GitHub CI run `29180231197` passed on Ubuntu/Windows with Python 3.11/3.12; real symlink rejection and packaged CLI validation passed on both platforms.
- `python scripts/validate_packaged_cli.py` installed the v0.5.1 npm tarball, exercised transient/configured/review/checkpoint/install-codex flows, rejected an outside-path sentinel, and removed its workspace.
- `python scripts/sync_packaged_assets.py --check`
- `python scripts/benchmark_context_pack.py --public --fail-on-weak` passed 10/10 scenarios with matching handoff replay; BrowserQuest stayed at 16% approximate scope after segment-aware glob regression coverage.
- `python -m build` and `python -m twine check` passed for v0.5.1; the wheel installed and reported `context-pack 0.5.1` in an isolated D-drive venv.
- GitHub Release run `29180289927` rebuilt and uploaded the v0.5.1 wheel, sdist, and npm tarball; PyPI/npm jobs were intentionally skipped.
- Release: `https://github.com/Fharena/context-pack/releases/tag/v0.5.1`.
- Public field-test issue: `https://github.com/Fharena/context-pack/issues/1`.
- `git diff --check`
