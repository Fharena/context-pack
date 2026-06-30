# Context Pack 벤치마크

이 문서는 `v0.2.19` 릴리즈 준비용 dogfood 및 A/B 오리엔테이션 결과입니다.

목표는 모든 프로젝트에서 같은 token 절감률을 주장하는 것이 아닙니다. Context Pack은 routing layer입니다. 에이전트가 넓게 읽기 전에 무엇을 먼저 볼지 고르고, 왜 골랐는지 설명하고, 한계도 드러내야 합니다.

## Dogfood 라우팅 방법

- 날짜: 2026-06-30
- 도구: local `v0.2.19` 후보를 `node bin/context-pack.js measure`로 실행
- 모드: read-only `measure`
- 대상: 공개 GitHub repo shallow clone
- 설정: 대상 repo에는 `.context-pack/`를 설치하지 않음. 즉 first-run inferred area 기준
- 추정치: text budget은 `chars/4` 근사값이며 binary, ignored, unreadable, 1 MB 초과 파일은 제외

## Dogfood 라우팅 결과

| Repo | HEAD | Prompt | 먼저 고른 영역 | 고려한 파일 | Read First entries | 대략적인 first-read text |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `pypa/sampleproject` | `621e4974ca25` | `ci is red` | `automation, source, tests` | 12 | 7 | 약 2.2k tokens, 약 67% |
| `psf/requests` | `23953c0c8752` | `why are tests failing` | `source, tests` | 130 | 4 | 약 103.7k tokens, 약 27% |
| `pallets/click` | `679a7a0eccbd` | `fix shell completion bug` | `source, tests` | 150 | 4 | 약 210.1k tokens, 약 59% |
| `encode/httpx` | `b5addb64f016` | `build failed` | `automation, source, tests` | 125 | 8 | 약 196.6k tokens, 약 79% |

## A/B 오리엔테이션 벤치마크

이 벤치마크는 "repo 전체를 읽는 것"이 비싸지만, task별 첫 읽기 범위는 줄일 수 있는 중간 규모 웹게임에서 확인했습니다.

- 날짜: 2026-06-30
- Repo: [`mozilla/BrowserQuest`](https://github.com/mozilla/BrowserQuest)
- HEAD: `af32d247cac3`
- 크기: 고려한 repo 파일 452개, text 파일 169개에서 약 602.2k text tokens
- Baseline: Context Pack routing 없이 넓게 repo text를 읽는 경우로 근사
- Context Pack: BrowserQuest에는 `.context-pack/`를 설치하지 않고 first-run inferred area만 사용

| Prompt | Context Pack 없음 | Context Pack 사용 | 먼저 고른 영역 | 절감 |
| --- | ---: | ---: | --- | ---: |
| `fix mobile controls bug on touch devices` | 약 602.2k tokens | 약 98.2k tokens | `source` | 약 84% |
| `fix missing sprite asset loading bug` | 약 602.2k tokens | 약 103.6k tokens | `source, sprites` | 약 83% |
| `debug websocket login connect failure` | 약 602.2k tokens | 약 98.2k tokens | `source` | 약 84% |

이 과정에서 제품 결함도 하나 잡았습니다. 수정 전 first-run inference는 BrowserQuest처럼 `src/` 대신 `client/js`, `server/js`, `shared/js`를 쓰는 repo를 `overview`로만 처리했습니다. 이제 엔진은 이런 웹 source 경로를 추론하고, `sprites`, `maps`, `media`를 분리하며, vendored `client/js/lib` 파일을 첫 읽기에 끌고 오지 않습니다.

## 검증된 점

- 사용자가 Context Pack 이름을 말하지 않아도 자연어 prompt를 적절한 area type으로 라우팅합니다.
- `Why selected` 출력으로 setup 파일을 쓰기 전에 선택 이유를 볼 수 있습니다.
- first-run inference가 일반적인 `src/`, tests, docs, automation, top-level Python package layout, 웹게임/client-server JS layout을 잡습니다.
- 중간 규모 웹게임에서 task별 first-read text budget을 넓은 repo text scan 대비 약 83-84% 줄였습니다.
- 실제 repo에서는 한계도 드러납니다. source/test area가 넓은 repo는 `.context-pack/AREAS/*.md`를 직접 정리해야 압축 효과가 좋아집니다.

## 아직 검증하지 못한 점

- 모든 repo에서 동일한 token 절감률을 보장하지 않습니다.
- 독립 에이전트의 정확도, 작업 시간, 최종 patch 품질까지 측정한 것은 아직 아닙니다.
- source verification을 대체하지 않습니다.
- monorepo 품질은 curated area boundary 없이 증명되지 않았습니다.

## 정직한 결론

Context Pack은 투명한 first-read router로는 이미 쓸 만합니다. 중간 규모 repo에서는 첫 파일 세트를 꽤 줄일 수 있지만, token 절감률은 repo 구조에 따라 달라집니다. 다음 증명 단계는 진짜 독립 에이전트 trace입니다. 같은 bug, 같은 repo에서 Context Pack 없는 run과 있는 run을 나누고, 읽은 token, 첫 관련 파일까지 걸린 시간, 최종 patch 품질, test 결과를 비교해야 합니다.
