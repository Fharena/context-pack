# Context Pack 벤치마크

이 문서는 `v0.2.20` 후보의 릴리즈 준비용 dogfood 및 orientation 벤치마크입니다.

목표는 모든 프로젝트에서 같은 token 절감률을 주장하는 것이 아닙니다. Context Pack은 routing layer입니다. 에이전트가 넓게 읽기 전에 무엇을 먼저 볼지 고르고, 왜 골랐는지 설명하고, 한계도 같이 드러내야 합니다.

## 방법

- 날짜: 2026-06-30
- 도구: local 후보를 `python scripts/benchmark_context_pack.py --public`로 실행
- 모드: read-only first-run routing 및 synthetic handoff replay
- 대상: `.context-pack/`가 없는 공개 GitHub repo shallow clone
- 추정치: text budget은 `chars/4` 근사값이며 ignored, unreadable, known binary, empty, 1 MB 초과 파일은 제외
- 약점 기준: 기대한 영역이 선택되어야 하고, read ratio가 각 시나리오 threshold보다 낮아야 하며, deterministic routing이 5초 안에 끝나야 함

기계가 읽는 결과는 [`docs/benchmarks/latest.json`](benchmarks/latest.json)에 있고, 생성된 요약은 [`docs/benchmarks/latest.md`](benchmarks/latest.md)에 있습니다.

## 공개 repo 오리엔테이션 결과

| Scenario | Repo | Prompt | 먼저 고른 영역 | 대략적인 first-read text | Flags |
| --- | --- | --- | --- | ---: | --- |
| sampleproject-ci | `pypa/sampleproject` | `ci is red` | `automation, source, tests` | 약 2.2k / 약 3.3k tokens, 67% | ok |
| requests-tests | `psf/requests` | `why are tests failing` | `source, tests` | 약 103.7k / 약 386.9k tokens, 27% | ok |
| click-shell-completion | `pallets/click` | `fix shell completion bug` | `source, tests` | 약 210.1k / 약 357.8k tokens, 59% | ok |
| httpx-build | `encode/httpx` | `build failed` | `automation, source, tests` | 약 196.6k / 약 247.7k tokens, 79% | ok |
| browserquest-mobile | `mozilla/BrowserQuest` | `fix mobile controls bug on touch devices` | `source` | 약 98.2k / 약 602.2k tokens, 16% | ok |
| browserquest-sprites | `mozilla/BrowserQuest` | `fix missing sprite asset loading bug` | `source, sprites` | 약 103.6k / 약 602.2k tokens, 17% | ok |
| browserquest-websocket | `mozilla/BrowserQuest` | `debug websocket login connect failure` | `source` | 약 98.2k / 약 602.2k tokens, 16% | ok |
| gin-middleware | `gin-gonic/gin` | `fix middleware panic bug` | `source` | 약 8.8k / 약 217.6k tokens, 4% | ok |
| express-router | `expressjs/express` | `fix router middleware error handling` | `source` | 약 15.5k / 약 177.8k tokens, 9% | ok |
| fd-rust-filter | `sharkdp/fd` | `fix regex filter bug` | `source` | 약 41.8k / 약 138.6k tokens, 30% | ok |

## Handoff Replay

synthetic replay 벤치마크는 작은 repo를 만들고, setup을 실행하고, handoff state를 publish한 뒤, repo를 로컬 clone하고, 양쪽 checkout에 같은 test-failure prompt를 던집니다.

- clone 이후 같은 routing signature 유지: yes
- 원본 checkout: `source, tests`, 약 404 / 약 4427 tokens, 9%
- clone checkout: `source, tests`, 약 404 / 약 4427 tokens, 9%

이 결과는 git에 실린 context가 새 세션에서도 같은 routing context를 제공할 수 있다는 핵심 약속을 확인합니다. 다만 서로 다른 독립 에이전트가 완전히 같은 답변을 낸다는 증명은 아닙니다.

## 발견하고 보강한 약점

- Go repo 추론이 약했습니다. `gin-gonic/gin` middleware prompt는 이전에는 root/top-level Go package 파일을 충분히 추론하지 못해 generic orientation으로 빠질 위험이 있었습니다. 이제 엔진은 Go repo, root `*.go`, top-level package directory, `*_test.go` 파일을 인식합니다. 최종 run에서 `gin-middleware`는 `source`를 골랐고 read ratio는 4%였습니다.
- Rust repo가 너무 넓게 잡혔습니다. `sharkdp/fd` regex/filter prompt는 처음에는 source/test context를 넓게 잡았습니다. 이제 공통 Rust crate start file과 Rust/filter/search keyword를 반영합니다. 최종 run에서 `fd-rust-filter`는 `source`를 골랐고 read ratio는 30%였습니다.
- media가 많은 repo에서 cold-start 비용이 드러났습니다. BrowserQuest에는 binary asset이 많고, 수정 전에는 binary file을 읽은 뒤에야 non-text로 버려서 slow threshold를 넘을 수 있었습니다. 이제 text-budget scan은 known binary suffix를 먼저 제외하고, 파일 크기를 읽기 전에 확인합니다. 최종 BrowserQuest run은 모두 5초 threshold 아래였습니다.
- benchmark 기대값도 정리했습니다. router/error-handling prompt에서는 generated pack이 별도 test guidance를 제공하므로 `source`가 올바른 첫 영역입니다. 불필요하게 더 많은 영역을 고르는 것을 좋은 점수로 보지 않도록 했습니다.

## 검증된 점

- 사용자가 Context Pack 이름을 말하지 않아도 자연어 prompt를 기대한 first-read area type으로 라우팅합니다.
- `Why selected` 출력으로 setup 파일을 쓰기 전에 선택 이유를 볼 수 있습니다.
- first-run inference가 Python, JavaScript client/server, web game asset, Go, Rust layout을 더 넓게 다룹니다.
- 중간 규모 웹게임에서 task별 first-read text budget이 넓은 repo text budget 약 602.2k tokens에서 약 98.2k-103.6k tokens로 줄었습니다.
- handoff replay는 context docs가 commit된 fresh clone에서도 deterministic routing이 유지됨을 보여줍니다.

## 아직 검증하지 못한 점

- 모든 repo에서 동일한 token 절감률을 보장하지 않습니다.
- provider billing token을 정확히 측정한 것이 아니라 text-budget 근사값입니다.
- duration 숫자는 로컬 wall-clock 회귀 신호이며 머신과 파일시스템 캐시 상태에 영향을 받습니다.
- 독립 에이전트의 정확도, 실제 작업 시간, 최종 patch 품질, 답변 일관성까지 측정한 것은 아직 아닙니다.
- source verification을 대체하지 않습니다.
- curated area boundary 없는 monorepo 품질은 아직 증명하지 못했습니다.

## 다음 증명 단계

다음 벤치마크는 independent-agent trace여야 합니다. 같은 repo, 같은 task를 Context Pack 없이 한 번, Context Pack으로 한 번 실행하고, 첫 관련 파일까지 걸린 시간, 읽은 token, elapsed time, 최종 patch 품질, test 결과, 새 세션이 같은 진단에 도달하는지를 비교해야 합니다.
