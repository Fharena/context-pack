# Context Pack 벤치마크

Context Pack에는 서로 다른 두 종류의 벤치마크가 있습니다. 두 수치를 섞어 쓰면 안 됩니다.

1. **Codex CLI A/B**는 model이 보고한 usage와 실제 patch 또는 review finding을 검사합니다.
2. **Deterministic routing**은 agent를 실행하지 않고 area 선택과 clone replay를 검사합니다.

어느 쪽도 보편적인 생산성, 청구 비용 절감, 사용자 채택을 증명하지 않습니다.

## v0.5.0 Codex CLI A/B

릴리스 벤치마크는 `mozilla/BrowserQuest@af32d247cac3495ca430d0effbb88dd5f3250b2c`, Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol`, low reasoning, 각 JSON에 기록된 정확한 working-tree engine을 사용합니다.

세 조건은 서로 다른 clone에서 실행합니다.

- **baseline**: Context Pack 파일과 지시 없음
- **transient**: 유지된 프로젝트 지식 없이 추론한 routing을 사용하는 실험적 cold-start 정책
- **maintained**: symbol, contract, failure mode, 검증 명령이 들어 있는 versioned task area. 리뷰 note는 검토 브랜치가 아니라 base branch에 commit합니다.

작업은 정밀 touch bug, 도메인 용어가 필요한 zoning bug, branch review, 체크인된 handoff에서 이어받기를 다룹니다. 수정 작업은 기대한 source repair와 정확히 한 개의 product file 변경을 요구합니다. 리뷰는 파일을 수정하지 않고 올바른 파일과 실패 원인을 지적해야 합니다.

### 유지형 Context 결과

| 작업 | 조건당 횟수 | Baseline 정답 | 유지형 정답 | Baseline total | 유지형 total | Total 변화 | Baseline uncached | 유지형 uncached | Uncached 변화 | 시간 변화 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 정밀 버그 | 3 | 3/3 | 3/3 | 96,119 | 67,823 | 29.4% 감소 | 13,111 | 7,663 | 41.6% 감소 | 7.5% 증가 |
| 도메인 라우팅 버그 | 5 | 5/5 | 5/5 | 109,913 | 68,660 | 37.5% 감소 | 19,033 | 10,638 | 44.1% 감소 | 11.6% 단축 |
| 브랜치 리뷰 | 3 | 3/3 | 3/3 | 67,667 | 56,479 | 16.5% 감소 | 14,933 | 8,351 | 44.1% 감소 | 9.9% 증가 |
| 세션 이어받기 | 3 | 3/3 | 3/3 | 68,493 | 53,916 | 21.3% 감소 | 13,453 | 6,907 | 48.7% 감소 | 3.2% 단축 |

유지형 Context Pack과 baseline은 모두 **14/14**에서 정답이었습니다. 유지형은 네 시나리오 모두 관련 파일에 도달한 명령 순서 중앙값이 2였고, baseline은 2-3이었습니다.

백분율은 시나리오별 중앙값 비교이며 합산 청구액 추정이 아닙니다. 시간은 두 작업에서 줄고 두 작업에서 늘었으므로 일반적인 속도 향상을 주장하지 않습니다.

### 부정적인 Cold-Start 결과

| 작업 | Transient 정답 | Total 중앙값 | Baseline 대비 |
| --- | ---: | ---: | ---: |
| 정밀 버그 | 3/3 | 74,558 | 22.4% 감소 |
| 도메인 라우팅 버그 | 2/5 | 125,356 | 14.1% 증가 |
| 브랜치 리뷰 | 3/3 | 52,237 | 22.8% 감소 |
| 세션 이어받기 | 3/3 | 96,756 | 41.3% 증가 |

Transient routing은 **11/14**에서 정답이었습니다. 도메인 작업 세 번은 seeded coordinate 결함 대신 같은 파일의 가깝지만 무관한 조건문을 바꿨고, 이어받기에서는 정답 patch에 도달하고도 누적 input이 늘었습니다. 이 결과에 따라 설치된 스킬에서 암묵적 transient routing을 제거했습니다. 설정되지 않은 저장소는 사용자가 Context Pack preview나 평가를 명시하지 않는 한 평소의 targeted search를 사용합니다.

### 재현

```bash
python scripts/benchmark_codex_ab.py \
  --scenario zoning \
  --conditions baseline transient curated \
  --trials 5 \
  --max-workers 3 \
  --json docs/benchmarks/codex-ab-v050-zoning.json \
  --markdown docs/benchmarks/codex-ab-v050-zoning.md \
  --fail-on-error
```

harness는 새롭거나 비어 있는 `--workdir`만 허용하고, 격리된 PATH shim으로 정확한 engine을 주입하며, aggregate를 만들기 전에 각 trial을 저장합니다. 누적 input/cached/uncached usage, 명령 수, 첫 target-file 명령, tool-output 양, 시간, 결정론적 품질 검사를 기록합니다. committed, uncommitted, untracked edit를 모두 patch 범위에 포함하며, agent가 정상 종료해도 patch가 틀리거나 불필요하게 넓으면 `--fail-on-error`가 실패합니다.

원본 aggregate:

- [정밀 버그](benchmarks/codex-ab-v050-touch.json)
- [도메인 라우팅 버그](benchmarks/codex-ab-v050-zoning.json)
- [브랜치 리뷰](benchmarks/codex-ab-v050-review.json)
- [세션 이어받기](benchmarks/codex-ab-v050-continuation.json)
- [읽기용 요약](benchmarks/codex-ab-v050-summary.md)

Raw JSONL trace와 patch는 machine path와 긴 model output을 포함하므로 로컬 benchmark work directory에만 둡니다.

## A/B로 바뀐 제품

측정은 단순 검증이 아니라 제품 동작을 바꿨습니다.

- search-only pack이 turn을 추가해 누적 input을 늘릴 수 있었습니다.
- 큰 `Read First` 범위가 파일·디렉터리 전체 읽기를 유도했습니다.
- 검토 브랜치가 만든 context를 믿으면 review가 편향될 수 있었습니다.
- 일반 추론 Evidence에 출처보다 높은 확신을 표시했습니다.
- continuation prompt가 generic task를 만들어 handoff를 버릴 수 있었습니다.
- benchmark directory를 재사용하면 과거 patch를 새 성공으로 오인할 수 있었습니다.
- inferred transient context가 관련 파일을 찾고도 실제 결함에서 agent를 벗어나게 할 수 있었습니다.

v0.5.0은 Evidence confidence, base-sourced review context, handoff 기반 continuation routing, 명시적 verify 명령, symbol health 진단, clean-workdir 강제를 추가했습니다. 스킬의 자동 routing은 설정된 저장소에만 적용합니다.

## Deterministic Routing

공개 저장소 regression harness는 model 없는 검사에 계속 사용합니다.

```bash
python scripts/benchmark_context_pack.py \
  --public \
  --json docs/benchmarks/latest.json \
  --markdown docs/benchmarks/latest.md \
  --fail-on-weak
```

공개 시나리오 10개는 기대한 area role, runtime threshold, fresh-clone handoff replay를 검사합니다. 과거 `chars/4` ratio는 candidate text scope일 뿐 실제 model token이 아닙니다.

## 한계

- 조건당 3-5회뿐이며 model 행동은 달라질 수 있습니다.
- 모든 agent run은 model 하나와 고정된 legacy JavaScript 저장소 하나를 사용합니다.
- 결함은 주입한 것이며 review와 continuation은 같은 zoning 결함을 재사용합니다.
- 프로젝트 저자가 유지형 area note를 작성했으므로 큐레이션 품질이 독립적이지 않습니다.
- 병렬 실행은 service load와 prefix-cache 조건을 공유할 수 있습니다.
- CLI `input_tokens`는 model turn 누적값이며 peak context-window 점유량이 아닙니다.
- `uncached_input_tokens`는 새로 처리한 input이지 직접적인 청구 금액이 아닙니다.
- 품질 검사는 task-specific deterministic check이며 사람의 patch review가 아닙니다.
- 이번 릴리스에서는 Claude Code와 Cursor runtime을 측정하지 않았습니다.
- 외부 사용자의 재사용률, 유지 부담, 완료 시간 연구는 아직 없습니다.

다음 증거 단계는 독립 maintainer가 자신의 저장소에서 반복 사용하고, 첫 관련 파일 도달 시간·결과 품질·유지 부담을 보고하는 것입니다.
