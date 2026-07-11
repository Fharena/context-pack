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
  --json docs/benchmarks/codex-ab-zoning-confirm.json \
  --markdown docs/benchmarks/codex-ab-zoning-confirm.md \
  --fail-on-error
```

harness는 다음을 수행합니다.

- `mozilla/BrowserQuest@af32d247cac3`를 shallow clone합니다.
- 같은 mobile zoning regression을 shallow root commit 안에 숨깁니다.
- baseline과 curated Context Pack checkout을 격리합니다.
- Codex CLI `0.144.0-alpha.4`, `gpt-5.6-sol`, low reasoning을 ephemeral mode로 실행합니다.
- 최대 두 trial을 병렬로 실행합니다.
- JSONL의 `turn.completed.usage`를 읽습니다.
- 기대한 source 수정과 unrelated file이 바뀌지 않았는지 검사합니다.

### 5회 확인 결과

| 조건 | 정확한 최소 patch | Total input 중앙값 | Total 범위 | Uncached input 중앙값 | 시간 중앙값 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 5/5 | 107,339 | 83,106-226,500 | 18,520 | 43.6초 |
| Curated Context Pack | 5/5 | 125,848 | 118,769-153,498 | 15,890 | 45.1초 |

baseline과 비교하면 curated Context Pack은 **total input 중앙값이 17.2% 늘었고**, **uncached input 중앙값은 14.2% 줄었으며**, **시간 중앙값은 3.4% 늘었습니다**. 가장 큰 run은 Context Pack 153,498, baseline 226,500 total input tokens였습니다.

이는 token 절감 headline이 아니라 혼합된 결과입니다. context route가 새로 처리하는 탐색과 tail 크기는 줄였지만 추가 tool turn이 cached input을 늘렸습니다. billing system은 cached input을 다르게 가격화할 수 있지만 이 저장소는 이를 비용 절감 주장으로 환산하지 않습니다.

정확한 결과는 [`codex-ab-zoning-confirm.md`](benchmarks/codex-ab-zoning-confirm.md)와 [`codex-ab-zoning-confirm.json`](benchmarks/codex-ab-zoning-confirm.json)에 있습니다. raw JSONL trace와 patch는 machine path와 긴 model output을 포함하므로 로컬 benchmark work directory에만 보관합니다.

## A/B로 발견해 고친 점

첫 A/B run은 실제 설계 결함 두 개를 드러냈습니다.

- pack이 glob과 큰 파일을 `Read First`로 표현해 agent가 bounded search 대신 파일 전체를 읽기도 했습니다.
- `.git` 아래 transient pack은 Codex workspace sandbox에서 쓰기가 막혀 retry와 추가 turn을 만들 수 있었습니다.

현재 engine은 `Search First` term과 scope를 출력하고 bounded match만 보도록 지시합니다. pack은 inline으로 출력하며 transient first run은 파일을 쓰지 않습니다. 스킬도 한 번의 정확한 검색으로 찾을 수 있는 작업에서는 Context Pack을 건너뜁니다.

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
- 하나의 seeded legacy JavaScript bug가 일반적인 patch 품질을 증명하지 않습니다.

다음 확장은 precise bug, domain-routed bug, branch review, session continuation을 각각 조건당 10-20회 실행하는 것입니다.
