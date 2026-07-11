# Context Pack Log

Recent published checkpoints only; older history remains available in git.

## 2026-07-11T19:23:51+09:00
- Branch: main
- HEAD: fb5dc67db21f
- Dirty files: none
- Dirty diff hash: clean
- Verification: 71 unit/integration tests passed; packaged npm CLI flow passed; Python wheel/sdist and twine checks passed; skill/plugin validators passed; 10 public routing scenarios passed with 0 weak flags; fresh-clone handoff replay matched; GitHub Actions run 29149300970 passed on Ubuntu/Windows with Python 3.11/3.12.
## 2026-07-11T20:44:58+09:00
- Branch: main
- HEAD: 391a40efb5a9
- Dirty files: none
- Dirty diff hash: clean
- Verification: 76 tests passed in the checkout and extracted sdist; npm packaged workflow, wheel/sdist, twine, npm tarball, skill/plugin validators, and 10 public routing scenarios passed; actual Codex CLI A/B produced correct minimal patches in both 5/5 arms with mixed token and latency results documented; GitHub Actions run 29151499931 passed on Ubuntu/Windows with Python 3.11/3.12.
## 2026-07-12T02:58:56+09:00
- Branch: main
- HEAD: 0d7973562a68
- Dirty files: .context-pack/CURRENT.md, docs/benchmarks/latest.json, docs/benchmarks/latest.md
- Dirty diff hash: sha256:0e76faf22865ae3e58afafef
- Verification: 83 unit/integration tests passed; the exact npm tarball passed transient Evidence, configured, review, checkpoint, and Codex install flows; wheel/sdist, twine, npm dry-run, skill/plugin validators, and 10 public routing scenarios passed; the five-run Codex A/B produced correct minimal patches in both arms with median total input -39.1%, uncached input -67.0%, tool output -91.0%, commands +25.0%, and duration +14.3% for curated runs.
## 2026-07-12T03:02:49+09:00
- Branch: main
- HEAD: 01f4814d3a1e
- Dirty files: none
- Dirty diff hash: clean
- Verification: GitHub CI run 29162621139 passed on Ubuntu/Windows with Python 3.11/3.12; release run 29162703130 rebuilt and uploaded wheel, sdist, and npm tarball assets to v0.4.0; PyPI/npm publication was intentionally skipped pending trusted-publisher setup.
