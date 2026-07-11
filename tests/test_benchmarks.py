from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from scripts import benchmark_codex_ab
from scripts import benchmark_context_pack


class BenchmarkTests(unittest.TestCase):
    def test_codex_benchmark_defaults_to_working_tree_engine(self) -> None:
        command = benchmark_codex_ab.discover_context_pack(None)

        self.assertEqual(command[0], sys.executable)
        self.assertEqual(Path(command[1]), benchmark_codex_ab.ENGINE_PATH)

    def test_codex_jsonl_usage_and_commands_are_parsed(self) -> None:
        events = [
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "command": "rg zoning client/js"},
            },
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "Fixed client/js/game.js"},
            },
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 125_848,
                    "cached_input_tokens": 110_848,
                    "output_tokens": 1_102,
                    "reasoning_output_tokens": 39,
                },
            },
        ]
        stdout = "\n".join(json.dumps(event) for event in events)

        usage, final_message, commands, event_count = benchmark_codex_ab.parse_events(stdout)

        self.assertEqual(usage["input_tokens"], 125_848)
        self.assertEqual(usage["cached_input_tokens"], 110_848)
        self.assertEqual(final_message, "Fixed client/js/game.js")
        self.assertEqual(commands, ["rg zoning client/js"])
        self.assertEqual(event_count, 3)

    def test_codex_summary_uses_successful_run_medians(self) -> None:
        def result(condition: str, input_tokens: int, cached: int, duration: float) -> dict:
            return {
                "condition": condition,
                "status": "ok",
                "duration_seconds": duration,
                "usage": {
                    "input_tokens": input_tokens,
                    "uncached_input_tokens": input_tokens - cached,
                },
                "quality": {"fixed": True, "minimal_patch": True},
                "context_pack_invoked": condition == "curated",
            }

        rows = [
            result("baseline", 100, 70, 10),
            result("baseline", 200, 150, 20),
            result("curated", 120, 100, 12),
            result("curated", 140, 110, 14),
        ]

        summary = benchmark_codex_ab.summarize(rows, ["baseline", "curated"])

        self.assertEqual(summary["baseline"]["input_tokens_median"], 150)
        self.assertEqual(summary["curated"]["input_tokens_median"], 130)
        self.assertEqual(summary["curated"]["input_reduction_vs_baseline_percent"], 13.3)
        self.assertEqual(summary["curated"]["uncached_reduction_vs_baseline_percent"], 37.5)
        self.assertEqual(summary["curated"]["duration_change_vs_baseline_percent"], -13.3)

    def test_codex_benchmark_treats_patch_quality_as_failure(self) -> None:
        good = {"status": "ok", "quality": {"fixed": True, "minimal_patch": True}}
        wrong = {"status": "ok", "quality": {"fixed": False, "minimal_patch": True}}
        broad = {"status": "ok", "quality": {"fixed": True, "minimal_patch": False}}

        self.assertFalse(benchmark_codex_ab.failed_result(good))
        self.assertTrue(benchmark_codex_ab.failed_result(wrong))
        self.assertTrue(benchmark_codex_ab.failed_result(broad))

    def test_search_first_scopes_are_parsed_without_terms_or_instruction(self) -> None:
        pack = """# Context Pack

## Search First
- Terms/symbols: `zoning`, `updateZoning`
- Scopes:
  - `client/js/game.js`
  - `client/js/*.js`
- Search first, then inspect only matching regions.

## Read First
- none
"""

        self.assertEqual(
            benchmark_context_pack.parse_search_scopes(pack),
            ["client/js/game.js", "client/js/*.js"],
        )


if __name__ == "__main__":
    unittest.main()
