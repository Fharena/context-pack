# Public Beta 홍보 초안

Context Pack을 소개할 때 쓸 수 있는 문안입니다. 톤은 정직하게 가져가세요. 이건 CI, package, dogfood evidence가 있는 public beta이지, 검증 끝난 생산성 수치가 있는 성숙 제품은 아닙니다.

## 짧은 소개

코딩 에이전트가 매 세션마다 repo를 처음부터 다시 읽을 필요는 없습니다.

Context Pack은 Codex, Claude, Cursor 같은 에이전트를 위한 가벼운 repo-local context layer입니다. 사용자가 "fix this bug", "CI is red", "review this branch", "I'm done for now"처럼 말하면, 에이전트가 넓게 읽기 전에 focused context pack부터 봅니다.

## 출시 글

Context Pack은 제가 코딩 에이전트와 긴 작업을 하다가 만든 도구입니다. 로컬 IDE, Codex, Claude, Cursor, cloud worktree, 새 세션을 오갈 때마다 에이전트가 같은 repo context를 다시 찾는 비용이 너무 컸습니다.

이 도구는 repo 안에 작은 `.context-pack/` 도서관을 만들고, 에이전트에게 단순한 규칙을 줍니다. 넓게 읽기 전에 `context-pack start`로 방향을 잡으라는 규칙입니다.

예시:

- `why are tests failing` -> `source, tests`
- `CI is red` -> `automation, source, tests`
- `review this branch` -> diff 기반 review pack
- `I'm done for now` -> ignored local checkpoint

벡터 DB나 또 다른 agent memory silo가 아닙니다. Markdown-first, git-aware, stale-aware, explainable한 routing layer입니다. pack은 왜 그 area가 선택됐는지 보여주고, 편집 전 source verification을 요구합니다.

현재 public beta는 Windows/Ubuntu, Python 3.11/3.12 CI를 통과했고, Python/npm tarball build path를 검증했으며, 공개 repo dogfood도 했습니다. read-only dogfood에서는 repo 구조에 따라 first-read context가 repo text의 약 27%-79% 범위였습니다. 이 범위는 일부러 정직하게 적었습니다. 큰 프로젝트에서는 curated area docs가 중요합니다.

Codex/Claude/Cursor를 많이 쓰고, local/cloud worktree를 오가는 분들의 피드백을 받고 싶습니다.

Repo: https://github.com/Fharena/context-pack

## 짧은 소셜 문안

코딩 에이전트가 매 세션마다 repo를 다시 읽지 않게 하려고 Context Pack을 만들었습니다.

Codex/Claude/Cursor가 넓게 읽기 전에 repo-local `.context-pack/` 지도를 봅니다.

- "why are tests failing" -> source/tests
- "CI is red" -> automation/source/tests
- "review this branch" -> review pack
- "done for now" -> checkpoint

Public beta: https://github.com/Fharena/context-pack
