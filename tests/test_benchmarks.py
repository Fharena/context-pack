from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from scripts import benchmark_codex_ab
from scripts import benchmark_context_pack


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_codex_benchmark_defaults_to_working_tree_engine(self) -> None:
        command = benchmark_codex_ab.discover_context_pack(None)

        self.assertEqual(command[0], sys.executable)
        self.assertEqual(Path(command[1]), benchmark_codex_ab.ENGINE_PATH)

    def test_codex_benchmark_shims_working_tree_engine_into_agent_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tool_bin = benchmark_codex_ab.install_context_pack_shim(
                Path(tmp),
                [sys.executable, str(benchmark_codex_ab.ENGINE_PATH)],
            )

            candidates = list(tool_bin.glob("context-pack*"))
            self.assertEqual(len(candidates), 1)
            text = candidates[0].read_text(encoding="utf-8")
            self.assertIn(str(benchmark_codex_ab.ENGINE_PATH), text)
            self.assertIn(sys.executable, text)

    def test_codex_jsonl_usage_and_commands_are_parsed(self) -> None:
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "rg zoning client/js",
                    "aggregated_output": "client/js/game.js:2119:startZoningFrom\n",
                },
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

        usage, final_message, commands, event_count, tool_chars, max_tool_chars = benchmark_codex_ab.parse_events(stdout)

        self.assertEqual(usage["input_tokens"], 125_848)
        self.assertEqual(usage["cached_input_tokens"], 110_848)
        self.assertEqual(final_message, "Fixed client/js/game.js")
        self.assertEqual(commands, ["rg zoning client/js"])
        self.assertEqual(event_count, 3)
        expected_tool_chars = len(events[0]["item"]["aggregated_output"])
        self.assertEqual(tool_chars, expected_tool_chars)
        self.assertEqual(max_tool_chars, expected_tool_chars)

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
                "command_count": 4 if condition == "baseline" else 3,
                "tool_output_chars": 50_000 if condition == "baseline" else 20_000,
                "max_tool_output_chars": 30_000 if condition == "baseline" else 12_000,
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
        self.assertEqual(summary["curated"]["command_count_median"], 3)
        self.assertEqual(summary["curated"]["tool_output_chars_median"], 20_000)
        self.assertEqual(summary["curated"]["max_tool_output_chars"], 12_000)

    def test_public_evidence_numbers_match_generated_aggregate(self) -> None:
        data = json.loads(
            (ROOT / "docs/benchmarks/codex-ab-zoning-evidence.json").read_text(encoding="utf-8")
        )
        baseline = data["summary"]["baseline"]
        curated = data["summary"]["curated"]
        tool_reduction = round(
            (1 - curated["tool_output_chars_median"] / baseline["tool_output_chars_median"]) * 100,
            1,
        )
        expected = (
            f"{baseline['input_tokens_median']:,.0f}",
            f"{curated['input_tokens_median']:,.0f}",
            f"{curated['input_reduction_vs_baseline_percent']:.1f}%",
            f"{curated['uncached_reduction_vs_baseline_percent']:.1f}%",
            f"{tool_reduction:.1f}%",
        )

        for path in ("README.md", "README.ko.md", "docs/BENCHMARKS.md", "docs/BENCHMARKS.ko.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            for value in expected:
                self.assertIn(value, text, f"{value} missing from {path}")

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
