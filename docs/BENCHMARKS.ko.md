# Context Pack 벤치마크

이 결과는 Context Pack의 결정론적 orientation 성능을 확인합니다. 보편적인 token 절감률을 주장하거나 에이전트가 더 좋은 patch를 만든다는 것을 증명하지는 않습니다.

## 측정 방법

- 날짜: 2026-07-11
- 엔진: `0.3.0`
- 명령: `python scripts/benchmark_context_pack.py --public --fail-on-weak`
- 입력: Context Pack을 설정하지 않은 공개 저장소 shallow clone 10개와 로컬 handoff replay 1개
- 추정 방식: 읽을 수 있는 text 문자 수를 4로 나눔. ignore, binary, empty, unreadable, 1 MB 초과 파일은 제외
- 통과 조건: 기대 area role 선택, 시나리오별 read ratio 상한 충족, 비어 있는 first-read route 없음, 5초 안에 routing 완료

정확한 생성 결과는 [`benchmarks/latest.md`](benchmarks/latest.md)와 [`benchmarks/latest.json`](benchmarks/latest.json)에 있습니다.

## 최신 결과

| 시나리오 | 저장소 | 먼저 선택된 영역 | 대략적인 first read / repo | 비율 |
| --- | --- | --- | ---: | ---: |
| CI 실패 | `pypa/sampleproject` | automation, source, tests | 2.2k / 3.3k | 65% |
| 테스트 실패 | `psf/requests` | source, tests | 41.3k / 386.9k | 11% |
| Shell completion | `pallets/click` | source, tests | 101.9k / 365.7k | 28% |
| Build 실패 | `encode/httpx` | automation, source, tests | 88.5k / 247.7k | 36% |
| Mobile control | `mozilla/BrowserQuest` | source | 98.2k / 602.2k | 16% |
| Asset loading | `mozilla/BrowserQuest` | assets, source | 98.2k / 602.2k | 16% |
| WebSocket login | `mozilla/BrowserQuest` | source | 98.2k / 602.2k | 16% |
| Middleware panic | `gin-gonic/gin` | source, tests | 9.0k / 217.6k | 4% |
| Router error | `expressjs/express` | source | 15.5k / 177.9k | 9% |
| Regex filter | `sharkdp/fd` | source, tests | 6.3k / 141.1k | 4% |

10개 시나리오가 모두 미리 정한 기준을 통과했습니다. 이 비율은 first-read route에 이름이 올라간 파일 범위이며, 에이전트가 작업 중 최종적으로 읽을 모든 파일을 뜻하지 않습니다.

## Handoff Replay

벤치마크는 synthetic repo를 설정하고 checkpoint를 publish한 뒤 clone합니다. 그리고 두 checkout에서 같은 test-failure 작업을 routing합니다.

- clone 후 동일한 routing signature: yes
- 두 checkout 모두: `source, tests`
- 대략적인 first read: 408 / 3,310 tokens, 12%
- first-read entry: 각 checkout에서 4개

이는 git으로 이동한 context가 결정론적 orientation을 재현한다는 뜻입니다. 서로 독립적인 에이전트가 같은 자연어 답변이나 patch를 만든다는 뜻은 아닙니다.

## 이번 검증에서 바뀐 점

- 커스텀 area 이름에도 source, tests, docs, assets, automation 같은 일반 role을 부여합니다.
- BrowserQuest 전용 sprite/map bucket과 벤치마크에 맞춘 framework 단어를 제거했습니다.
- 추론된 시작 범위는 source/test 폴더 전체 대신 제한된 entry-point glob을 사용합니다.
- 실제 제품 파일도 바뀌었으면 review routing에서 Context Pack 자체 metadata를 분리합니다.
- 평소 `start`는 token 통계를 출력하려고 repo 전체를 scan하지 않습니다.

## 한계

- `chars/4`는 text-budget proxy이며 provider billing이나 실제 tokenizer 결과가 아닙니다.
- 로컬 duration은 regression signal이며 머신과 filesystem cache에 따라 달라집니다.
- routing과 replay를 측정할 뿐 진단 정확도, patch 품질, test 성공률, 작업 완료 시간은 측정하지 않습니다.
- 잘 큐레이션된 area 경계는 first-run 추론보다 좋을 수 있고, 나쁜 경계는 오히려 routing을 해칠 수 있습니다.
- 실제 source 검증은 항상 필요합니다.

다음으로 의미 있는 증명은 독립 에이전트 A/B입니다. 읽은 파일, 첫 관련 파일 도달, 소요 시간, test 결과, blinded patch review를 함께 기록해야 합니다. 그전까지 홍보 수치는 orientation 측정값으로만 표현해야 합니다.
