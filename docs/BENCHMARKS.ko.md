# Context Pack 벤치마크

Context Pack에는 서로 다른 두 종류의 벤치마크가 있습니다. 두 수치를 섞어 쓰면 안 됩니다.

1. **Codex CLI A/B**는 model run이 보고한 usage와 실제 patch를 검사합니다.
2. **Deterministic routing**은 agent를 실행하지 않고 area 선택과 clone replay를 검사합니다.

어느 쪽도 보편적인 생산성 향상이나 billing 절감을 증명하지는 않습니다.

## 실제 Codex CLI A/B

다음 명령으로 재현합니다.

```bash
python scripts/benchmark_codex_ab.py \
  --scenario zoning \
  --conditions baseline curated \
  --trials 5 \
  --max-workers 2 \
  --json docs/benchmarks/codex-ab-zoning-evidence.json \
  --markdown docs/benchmarks/codex-ab-zoning-evidence.md \
  --fail-on-error
```

harness는 다음을 수행합니다.

- `mozilla/BrowserQuest@af32d247cac3`를 shallow clone합니다.
- 같은 mobile zoning regression을 shallow root commit 안에 숨깁니다.
- baseline과 curated Context Pack checkout을 격리합니다.
- Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol`, low reasoning을 ephemeral mode로 실행합니다.
- 전역 설치본을 신뢰하지 않고 정확한 working-tree Context Pack engine을 agent PATH에 넣습니다.
- 최대 두 trial을 병렬로 실행합니다.
- JSONL의 `turn.completed.usage`를 읽습니다.
- 명령 수, 전체 tool-output 문자 수, 단일 tool output 최댓값을 기록합니다.
- 기대한 source 수정과 unrelated file이 바뀌지 않았는지 검사합니다.

### 5회 확인 결과

| 조건 | 정확한 최소 patch | Total input 중앙값 | Uncached 중앙값 | 명령 수 | Tool chars | 시간 중앙값 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 5/5 | 111,828 | 20,948 | 4 | 47,809 | 38.2초 |
| Evidence-first curated | 5/5 | 68,075 | 6,905 | 5 | 4,298 | 43.7초 |

baseline과 비교하면 evidence-first curated Context Pack은 **total input 중앙값 39.1%**, **uncached input 중앙값 67.0%**, **tool output 중앙값 91.0%**를 줄였습니다. 명령 중앙값은 4회에서 5회로 늘었고 시간 중앙값도 **14.3% 증가**했습니다. Total-input 범위는 baseline 101,287-247,516, curated 53,486-82,548이었습니다. 단일 tool result 최댓값은 baseline 1,048,576자, curated 3,364자였습니다.

모든 curated trace는 pack에 포함된 source evidence를 보고 같은 범위를 다시 열지 않은 채 수정했습니다. 남은 호출은 검증과 최종 diff 또는 package 확인이었습니다. 이번 배치에서는 낮은 token 양이 낮은 latency를 보장하지 않았습니다. 그래도 이는 유지된 symbol, contract, 검증 명령이 있는 하나의 seeded task 결과입니다. billing system은 cached input을 다르게 가격화할 수 있으며 이 저장소는 이를 보편적인 비용 절감 주장으로 환산하지 않습니다.

정확한 v0.4.0 결과는 [`codex-ab-zoning-evidence.md`](benchmarks/codex-ab-zoning-evidence.md)와 [`codex-ab-zoning-evidence.json`](benchmarks/codex-ab-zoning-evidence.json)에 있습니다. 이전 search-only 결과는 [`codex-ab-zoning-confirm.md`](benchmarks/codex-ab-zoning-confirm.md)에 남겨 두었습니다. raw JSONL trace와 patch는 machine path와 긴 model output을 포함하므로 로컬 benchmark work directory에만 보관합니다.

## A/B로 발견해 고친 점

A/B 반복은 실제 설계 결함 여러 개를 드러냈습니다.

- pack이 glob과 큰 파일을 `Read First`로 표현해 agent가 bounded search 대신 파일 전체를 읽기도 했습니다.
- `.git` 아래 transient pack은 Codex workspace sandbox에서 쓰기가 막혀 retry와 추가 turn을 만들 수 있었습니다.
- Search-only pack은 model turn을 추가해 uncached input을 줄이고도 median total input을 늘렸습니다.
- 벤치마크가 처음에는 전역 구버전 CLI를 잡아 working-tree의 새 flag가 실행되기 전에 실패했습니다.
- 검증 명령 2개를 주면 에이전트가 별도 model turn 두 번으로 실행했습니다.

현재 engine은 강한 configured symbol에서 최대 2개의 bounded source 구간을 반환하고, 중복 preamble 없는 compact agent output을 사용합니다. primary area 2개, contract 3개, failure mode 2개, 검증 명령 1개로 제한하며 transient first run은 파일을 쓰지 않습니다. 벤치마크는 격리된 PATH shim으로 정확한 engine을 실행합니다.

## Deterministic Routing

기존 공개 저장소 harness도 regression 검사에는 계속 유용합니다.

```bash
python scripts/benchmark_context_pack.py \
  --public \
  --json docs/benchmarks/latest.json \
  --markdown docs/benchmarks/latest.md \
  --fail-on-weak
```

공개 시나리오 10개는 기대한 area role, runtime threshold, fresh-clone handoff replay를 검사합니다. 과거 `chars/4` ratio는 candidate text scope일 뿐 실제 model token이 아니므로 핵심 세일즈 수치로 사용하면 안 됩니다.

## 한계

- 조건별 5회는 여전히 작은 표본입니다.
- 같은 prompt와 repo에서도 model 행동은 달라집니다.
- 병렬 실행은 시간을 줄이지만 prefix cache와 service load 조건을 공유할 수 있습니다.
- CLI `input_tokens`는 여러 model turn의 누적값이며 peak context-window 점유량이 아닙니다.
- `uncached_input_tokens`는 새로 처리한 input이지 직접적인 청구 금액이 아닙니다.
- Tool-output 문자 수는 탐색 형태를 설명하지만 token 수는 아닙니다.
- 하나의 seeded legacy JavaScript bug가 일반적인 patch 품질을 증명하지 않습니다.

다음 확장은 precise bug, domain-routed bug, branch review, session continuation을 각각 조건당 10-20회 실행하는 것입니다.
