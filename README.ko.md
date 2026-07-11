# Context Pack

<p align="center">
  <strong>코딩 에이전트를 위한 repo-local context router.</strong><br>
  저장소 전체를 다시 탐색하기 전에 지금 필요한 가장 작은 지도에서 시작합니다.
</p>

<p align="center">
  <a href="https://github.com/Fharena/context-pack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Fharena/context-pack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/Fharena/context-pack?display_name=tag"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg"></a>
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/docs-English-blue.svg"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Fharena/context-pack/main/assets/demo.gif" alt="Context Pack 터미널 데모" width="820">
</p>

코딩 에이전트는 코드를 잘 읽습니다. 낭비는 새 세션마다 같은 아키텍처, 관련 파일, 테스트, 미완료 상태를 다시 찾게 할 때 생깁니다.

Context Pack은 repo 안에 작은 버전 관리형 프로젝트 지도를 두고, 현재 작업에 필요한 bounded source evidence가 포함된 focused pack을 만듭니다. Codex, Claude Code, Cursor와 repository instruction을 따르는 다른 에이전트에서 사용할 수 있습니다.

## 누구에게 맞는가

다음 상황에서 특히 유용합니다.

- 로컬과 클라우드 세션, 기기, worktree, 에이전트를 자주 오가는 작업
- 전체 탐색 비용이 무시하기 어려운 중간 이상 크기의 저장소
- 같은 contract, test, failure mode를 반복 확인하는 코드 리뷰
- handoff 상태를 git과 함께 옮기려는 maintainer

아주 작은 저장소, 순수 Q&A, 명확한 단일 파일 수정에서는 의도적으로 빠져나옵니다.

## 설치

### Codex

GitHub에서 플러그인을 설치합니다.

```bash
pipx run --spec git+https://github.com/Fharena/context-pack.git context-pack install-codex --activate
```

설치 후 새 Codex 작업을 시작하세요. repo orientation이 유용한 상황이면 스킬이 Context Pack을 알아서 사용합니다.

### Claude Code, Cursor, 기타 에이전트

CLI를 설치합니다.

```bash
pipx install git+https://github.com/Fharena/context-pack.git
```

그다음 공유 context library와 agent rule을 repo에 명시적으로 설치합니다.

```bash
context-pack setup --dry-run
context-pack setup
```

`setup`은 `AGENTS.md`, `CLAUDE.md`, Cursor project rule의 관리 블록 밖에 있는 기존 문장을 보존합니다.
기본값은 `AGENTS.md`를 항상 관리하고, Claude/Cursor 파일은 해당 에이전트 파일이 이미 있을 때만 갱신합니다. 세 종류를 모두 만들려면 `--agent-docs all`을 사용합니다.

| 환경 | v0.5.0 검증 수준 |
| --- | --- |
| Codex | skill/plugin 설치, packaged CLI, 실제 CLI A/B 실행 |
| Claude Code | `CLAUDE.md` 생성·보존 테스트 통과; 이번 릴리스 환경에는 runtime CLI가 없어 미검증 |
| Cursor | `.cursor/rules/*.mdc` 생성·보존 테스트 통과; 이번 릴리스 환경에는 runtime CLI가 없어 미검증 |

## 평소 UX

사용자는 자연스럽게 말하고, 에이전트가 결정론적 동작을 고릅니다.

| 사용자 요청 | 에이전트 동작 |
| --- | --- |
| “로그인 타임아웃 버그 고쳐줘.” | `context-pack start --agent --task "fix login timeout"` |
| “테스트가 왜 실패하지?” | `context-pack start --agent --task "tests failing"` |
| “이 브랜치 리뷰해줘.” | `context-pack start --agent --review` |
| “나중에 이어가기 쉽게 정리해줘.” | `context-pack checkpoint --pack --quiet` |

CLI가 리뷰나 handoff 문장을 직접 분류할 필요는 없습니다. 이미 의도를 이해한 에이전트가 명시적 플래그를 넘깁니다.

## 안전한 첫 실행

`start`와 `setup`은 서로 다른 작업입니다.

설정되지 않은 Git repo에서는 설치된 스킬이 평소의 targeted code search를 사용합니다. Context Pack을 암묵적으로 실행하거나 파일을 만들지 않습니다.

CLI에는 `context-pack start --task "..."`로 명시적으로 실행하는 transient preview가 남아 있습니다. 이 preview는:

- source, tests, docs, automation, assets 영역을 메모리에서 추론하고,
- repo에 파일을 쓰지 않고 compact한 bounded source evidence를 바로 출력하며,
- `.context-pack/`, `AGENTS.md`, `.gitignore`를 만들지 않고,
- 파일이 24개 이하라 전체 읽기가 더 싸면 pack 생성 자체를 건너뜁니다.

Transient routing은 setup을 평가하는 데는 쓸 수 있지만, v0.5.0 A/B에서 자동 기본값으로 쓰기에는 불안정했습니다. 스킬이 신뢰하고 재사용할 유지형 context library는 명시적인 `setup`에서만 생성합니다.

## 영구 Context Library

setup 후 버전 관리되는 도서관은 작게 유지됩니다.

```text
.context-pack/
  manifest.json
  INDEX.md
  CURRENT.md
  DECISIONS.md
  LOG.md
  AREAS/
    source.md
    tests.md
    ...
```

- `INDEX.md`: 작업을 영역으로 라우팅합니다.
- `AREAS/*.md`: contract, failure mode, 시작 파일을 짧게 보관합니다.
- `CURRENT.md`: 공유 handoff fingerprint와 다음 작업을 기록합니다.
- `DECISIONS.md`: 오래 유지할 방향성 결정만 기록합니다.
- `LOG.md`: 최근 publish checkpoint 30개만 유지합니다. 이전 기록은 git history에 남습니다.

생성 pack과 로컬 checkpoint는 ignore됩니다.

```text
.context-pack/packs/
.context-pack/local/
.context-pack/tmp/
```

## 핵심 명령

```bash
# 영구 설치 또는 상태 확인
context-pack setup --dry-run
context-pack setup
context-pack doctor

# 작업과 리뷰 orientation
context-pack start --agent --task "fix stale detection bug"
context-pack start --agent --review

# handoff
context-pack checkpoint --pack
context-pack checkpoint --publish --pack
```

`--publish`는 의도적인 동작입니다. git으로 옮길 tracked handoff 파일을 갱신합니다. 기본 checkpoint는 로컬 ignore 상태만 갱신합니다.

## 라우팅 방식

Context Pack은 RAG가 아니며 embedding이나 vector database를 사용하지 않습니다. 라우팅은 결정론적입니다.

1. Git에서 changed file과 현재 branch/HEAD를 읽습니다.
2. path를 설정된 area에 매핑합니다.
3. task 단어를 area 이름, keyword, 설정된 search term, path, 짧은 routing note와 비교합니다.
4. `source`, `tests`, `automation` 같은 area role로 커스텀 영역 이름에서도 일반 폴백을 제공합니다.
5. agent mode는 강한 configured symbol부터 검색하고 최대 2개의 bounded line-numbered source 구간을 반환합니다.
6. contract, failure mode, 검증 명령 1개는 routing 이후에만 task 관련도로 정렬하며 다른 area를 선택하지 않습니다.

Area note는 계속 routing hint입니다. pack의 `Evidence`는 현재 source에서 직접 추출되므로 원인이 보이면 같은 범위를 다시 열지 않고 수정할 수 있습니다.

## 유지 비용 제한

- 실제 제품 파일이 바뀌면 리뷰 라우팅에서 Context Pack 자체 metadata를 분리합니다.
- `doctor`가 repo 대부분을 덮는 넓은 area glob을 경고합니다.
- area note에 stale fingerprint와 review status가 있습니다.
- checkpoint log는 무한 append 대신 상한을 둡니다.
- text-budget scan은 `measure` 또는 `--text-budget`에서만 실행합니다. 평소 `start`는 통계를 위해 전체 text를 읽지 않습니다.
- agent 출력은 상한을 두고, 중복 preamble과 동일한 packaged source 복사본을 제거합니다.
- 선택형 `safe` Git hook은 설치 당시 Python을 정확히 사용하며 실패해도 commit을 막지 않습니다.

## 검증과 한계

이제 `chars/4` proxy뿐 아니라 실제 Codex CLI usage를 수집하는 A/B harness가 있습니다. v0.5.0은 같은 model, prompt, 고정된 source revision, 격리된 working-tree engine으로 BrowserQuest 작업 네 종류를 검증했습니다.

| 작업 | Baseline 정답 | 유지형 정답 | Total input 중앙값 | Uncached input 중앙값 | 시간 중앙값 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 정밀 버그 (조건당 3회) | 3/3 | 3/3 | 29.4% 감소 | 41.6% 감소 | 7.5% 증가 |
| 도메인 라우팅 버그 (조건당 5회) | 5/5 | 5/5 | 37.5% 감소 | 44.1% 감소 | 11.6% 단축 |
| 브랜치 리뷰 (조건당 3회) | 3/3 | 3/3 | 16.5% 감소 | 44.1% 감소 | 9.9% 증가 |
| 세션 이어받기 (조건당 3회) | 3/3 | 3/3 | 21.3% 감소 | 48.7% 감소 | 3.2% 단축 |

유지형 Context Pack과 baseline은 모두 **14/14**에서 정답이었습니다. 실험적인 transient 정책은 **11/14**였고, 도메인 작업과 이어받기 작업에서는 total input 중앙값이 각각 14.1%, 41.3% 늘었습니다. 설정되지 않은 저장소에서 이제 평소 검색을 기본값으로 쓰는 이유입니다.

이는 고정된 legacy JavaScript 저장소 하나에서 seeded defect와 저자가 관리한 symbol을 사용한 작은 표본입니다. 보편적인 token, billing, latency, patch-quality 향상을 증명하지 않습니다. Total input은 turn 누적값이고 uncached input도 청구 금액이 아닙니다. 자세한 방법과 raw aggregate는 [docs/BENCHMARKS.ko.md](docs/BENCHMARKS.ko.md)와 [v0.5.0 결과 요약](docs/benchmarks/codex-ab-v050-summary.md)에 있습니다.

기존 deterministic benchmark는 routing과 clone replay를 계속 검사합니다. 해당 `chars/4` 수치는 실제 model usage가 아니라 search-scope 추정입니다.

큐레이션 비용을 완전히 없앨 수도 없습니다. 유용한 area 경계와 짧은 note가 있을 때 가치가 커집니다. 대신 방치됐을 때 해를 끼치지 않는 것이 제품 목표입니다. 경고하고, 로그를 줄이고, 생성 상태를 ignore하며, 최종적으로 source verification으로 폴백합니다.

## 개발

```bash
python scripts/sync_packaged_assets.py --check
python -m unittest discover -s tests -v
python scripts/validate_packaged_cli.py
```

엔진은 Python stdlib-only입니다. Pillow는 `assets/demo.gif` 재생성에만 선택적으로 사용합니다.

[CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), [docs/RELEASE.ko.md](docs/RELEASE.ko.md)도 참고하세요.

## 라이선스

[MIT](LICENSE)
