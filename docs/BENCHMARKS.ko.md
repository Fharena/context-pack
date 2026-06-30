# Context Pack 벤치마크

이 문서는 `v0.2.18` 릴리즈 준비용 dogfood 결과입니다.

목표는 모든 프로젝트에서 같은 token 절감률을 주장하는 것이 아닙니다. Context Pack은 routing layer입니다. 에이전트가 넓게 읽기 전에 무엇을 먼저 볼지 고르고, 왜 골랐는지 설명하고, 한계도 드러내야 합니다.

## 방법

- 날짜: 2026-06-30
- 도구: local `v0.2.18` 후보를 `node bin/context-pack.js measure`로 실행
- 모드: read-only `measure`
- 대상: 공개 GitHub repo shallow clone
- 설정: 대상 repo에는 `.context-pack/`를 설치하지 않음. 즉 first-run inferred area 기준
- 추정치: text budget은 `chars/4` 근사값이며 binary, ignored, unreadable, 1 MB 초과 파일은 제외

## 결과

| Repo | HEAD | Prompt | 먼저 고른 영역 | 고려한 파일 | Read First entries | 대략적인 first-read text |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `pypa/sampleproject` | `621e4974ca25` | `ci is red` | `automation, source, tests` | 12 | 7 | 약 2.2k tokens, 약 67% |
| `psf/requests` | `23953c0c8752` | `why are tests failing` | `source, tests` | 130 | 4 | 약 103.7k tokens, 약 27% |
| `pallets/click` | `679a7a0eccbd` | `fix shell completion bug` | `source, tests` | 150 | 4 | 약 210.1k tokens, 약 59% |
| `encode/httpx` | `b5addb64f016` | `build failed` | `automation, source, tests` | 125 | 8 | 약 196.6k tokens, 약 79% |

## 검증된 점

- 사용자가 Context Pack 이름을 말하지 않아도 자연어 prompt를 적절한 area type으로 라우팅합니다.
- `Why selected` 출력으로 setup 파일을 쓰기 전에 선택 이유를 볼 수 있습니다.
- first-run inference가 일반적인 `src/`, tests, docs, automation, top-level Python package layout을 잡습니다.
- 실제 repo에서는 한계도 드러납니다. source/test area가 넓은 repo는 `.context-pack/AREAS/*.md`를 직접 정리해야 압축 효과가 좋아집니다.

## 아직 검증하지 못한 점

- 모든 repo에서 동일한 token 절감률을 보장하지 않습니다.
- 에이전트 정확도나 작업 시간을 측정한 것은 아닙니다.
- source verification을 대체하지 않습니다.
- monorepo 품질은 curated area boundary 없이 증명되지 않았습니다.

## 정직한 결론

Context Pack은 투명한 first-read router로는 이미 쓸 만합니다. 중간 규모 repo에서는 첫 파일 세트를 꽤 줄일 수 있지만, token 절감률은 repo 구조에 따라 달라집니다. 다음 제품 마일스톤은 더 나은 area curation과 실제 작업 before/after trace입니다.
