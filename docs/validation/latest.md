# Remaining Validation Run

- Generated at: 2026-06-30T14:33:32+09:00
- Engine version: `0.2.20`
- Subject HEAD: `b2a66032ba93`

## Synthetic A/B Proxy

| Prompt | Without Context Pack | With Context Pack | Reduction | Expected files present | Flags |
| --- | ---: | ---: | ---: | --- | --- |
| why are tests failing | ~1570 tokens / 64 files | ~51 tokens / 2 files | 97% | yes | ok |

## Session Consistency

| Prompt | Source signature | Clone signature | Same | Flags |
| --- | --- | --- | --- | --- |
| why are tests failing | `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 6, "read_tokens": 421, "repo_tokens": 6572, "selected": ["source", "tests"]}` | `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 6, "read_tokens": 421, "repo_tokens": 6572, "selected": ["source", "tests"]}` | yes | ok |
| ci is red | `{"read_first_entries": 6, "read_first_files": 6, "read_ratio": 10, "read_tokens": 626, "repo_tokens": 6572, "selected": ["automation", "source", "tests"]}` | `{"read_first_entries": 6, "read_first_files": 6, "read_ratio": 10, "read_tokens": 626, "repo_tokens": 6572, "selected": ["automation", "source", "tests"]}` | yes | ok |
| fix login timeout | `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 6, "read_tokens": 421, "repo_tokens": 6572, "selected": ["source", "tests"]}` | `{"read_first_entries": 4, "read_first_files": 4, "read_ratio": 6, "read_tokens": 421, "repo_tokens": 6572, "selected": ["source", "tests"]}` | yes | ok |

## Limits

- This is a deterministic proxy for agent orientation, not a true independent LLM patch-quality benchmark.
- It checks first relevant context, routing stability, and fresh-clone signature consistency.
- True answer-quality validation still needs separate agent runs with captured transcripts.
