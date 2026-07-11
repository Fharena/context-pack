from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import benchmark_codex_ab
from scripts import benchmark_context_pack


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_prepare_workdir_rejects_nonempty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp) / "benchmark"
            workdir.mkdir()
            (workdir / "existing.txt").write_text("old run", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be new or empty"):
                benchmark_codex_ab.prepare_workdir(str(workdir))

    def make_browserquest_fixture(self, root: Path) -> Path:
        source = root / "source"
        (source / "client/js").mkdir(parents=True)
        scenario = benchmark_codex_ab.SCENARIOS["zoning"]
        (source / "client/js/game.js").write_text(
            "function zoning() {\n    " + scenario["good_code"] + "\n}\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Benchmark Test"], cwd=source, check=True)
        subprocess.run(["git", "config", "user.email", "benchmark@example.invalid"], cwd=source, check=True)
        subprocess.run(["git", "add", "."], cwd=source, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=source, check=True, capture_output=True)
        return source

    def test_changed_files_since_includes_committed_and_untracked_edits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_browserquest_fixture(Path(tmp))
            seed_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            game = repo / "client/js/game.js"
            game.write_text(game.read_text(encoding="utf-8") + "// committed edit\n", encoding="utf-8")
            subprocess.run(["git", "add", "client/js/game.js"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "agent hides edit"], cwd=repo, check=True, capture_output=True)
            (repo / "unexpected.txt").write_text("untracked", encoding="utf-8")

            self.assertEqual(
                benchmark_codex_ab.changed_files_since(repo, seed_head),
                ["client/js/game.js", "unexpected.txt"],
            )

    def test_review_quality_requires_specific_positive_failure_mechanism(self) -> None:
        scenario = benchmark_codex_ab.SCENARIOS["review-zoning"]
        correct = (
            "client/js/game.js:2134 assigns the vertical camera coordinate to x instead of y. "
            "c.setPosition therefore leaves the Y position unchanged and jumps horizontally."
        )

        self.assertTrue(benchmark_codex_ab.review_finding_matches(correct, scenario))
        self.assertFalse(
            benchmark_codex_ab.review_finding_matches(
                "There is no sideways bug in client/js/game.js.",
                scenario,
            )
        )
        self.assertFalse(
            benchmark_codex_ab.review_finding_matches(
                "client/js/game.js contains an unrelated horizontal coordinate observation.",
                scenario,
            )
        )
        denial_with_all_signals = (
            "There is no defect in client/js/game.js:2134: the vertical path assigns x instead of y "
            "and would cause a horizontal jump."
        )
        unrelated_with_all_signals = (
            "Unrelated observation only: client/js/game.js:2134 assigns the vertical coordinate to x "
            "instead of y and causes a horizontal jump."
        )
        self.assertFalse(benchmark_codex_ab.review_finding_matches(denial_with_all_signals, scenario))
        self.assertFalse(benchmark_codex_ab.review_finding_matches(unrelated_with_all_signals, scenario))

    def test_context_pack_invocation_and_unexpected_result_are_serializable(self) -> None:
        self.assertTrue(
            benchmark_codex_ab.context_pack_was_invoked(
                ['context-pack start --agent --task "fix zoning"']
            )
        )
        self.assertFalse(benchmark_codex_ab.context_pack_was_invoked(["rg zoning client/js"]))

        result = benchmark_codex_ab.unexpected_trial_result("curated", 2, NameError("missing"))
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["quality"]["fixed"])
        self.assertIn("NameError", json.dumps(result))

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

    def test_review_benchmark_places_curated_context_on_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_browserquest_fixture(root)
            target = root / "review"
            scenario = benchmark_codex_ab.SCENARIOS["review-zoning"]

            benchmark_codex_ab.prepare_trial(
                source,
                target,
                "curated",
                [sys.executable, str(benchmark_codex_ab.ENGINE_PATH)],
                scenario,
            )

            base_manifest = subprocess.check_output(
                ["git", "show", "main:.context-pack/manifest.json"],
                cwd=target,
                text=True,
            )
            self.assertIn("mobile-zoning", base_manifest)
            self.assertEqual(
                subprocess.check_output(["git", "branch", "--show-current"], cwd=target, text=True).strip(),
                "benchmark-work",
            )
            current = (target / scenario["target_file"]).read_text(encoding="utf-8")
            base = subprocess.check_output(
                ["git", "show", f"main:{scenario['target_file']}"],
                cwd=target,
                text=True,
            )
            self.assertIn(scenario["bad_code"], current)
            self.assertIn(scenario["good_code"], base)

    def test_continuation_benchmark_writes_curated_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_browserquest_fixture(root)
            target = root / "continuation"
            scenario = benchmark_codex_ab.SCENARIOS["continuation-zoning"]

            benchmark_codex_ab.prepare_trial(
                source,
                target,
                "curated",
                [sys.executable, str(benchmark_codex_ab.ENGINE_PATH)],
                scenario,
            )

            handoff = (target / ".context-pack/CURRENT.md").read_text(encoding="utf-8")
            self.assertIn("unfinished", handoff.lower())
            self.assertIn(scenario["verify"][0], handoff)

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
                "first_target_command": 3 if condition == "baseline" else 1,
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
        self.assertEqual(summary["curated"]["first_target_command_median"], 1)
        self.assertEqual(summary["curated"]["tool_output_chars_median"], 20_000)
        self.assertEqual(summary["curated"]["max_tool_output_chars"], 12_000)

    def test_public_evidence_numbers_match_generated_aggregates(self) -> None:
        names = ("touch", "zoning", "review", "continuation")
        data = [
            json.loads(
                (ROOT / f"docs/benchmarks/codex-ab-v050-{name}.json").read_text(encoding="utf-8")
            )
            for name in names
        ]
        total_runs = sum(result["summary"]["baseline"]["runs"] for result in data)
        expected = {
            f"{sum(result['summary'][condition]['fixed_runs'] for result in data)}/{total_runs}"
            for condition in ("baseline", "transient", "curated")
        }
        for result in data:
            curated = result["summary"]["curated"]
            expected.add(f"{curated['input_reduction_vs_baseline_percent']:.1f}%")
            expected.add(f"{curated['uncached_reduction_vs_baseline_percent']:.1f}%")
            transient_change = result["summary"]["transient"]["input_reduction_vs_baseline_percent"]
            if transient_change < 0:
                expected.add(f"{abs(transient_change):.1f}%")

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
