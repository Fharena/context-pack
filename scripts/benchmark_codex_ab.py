#!/usr/bin/env python3
"""Run parallel Codex CLI A/B trials with reported token usage.

The benchmark seeds the same mobile-input regression into isolated BrowserQuest
clones and compares three conditions:

- baseline: no Context Pack instructions or files
- transient: a repo rule asks Codex to use transient Context Pack orientation
- curated: a persistent, task-specific Context Pack area is committed

The result measures the usage reported by Codex CLI. It is not a billing
statement and one benchmark task is not proof of general patch quality.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import random
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "plugins/context-pack/skills/context-pack/scripts/context_pack.py"
REPO_URL = "https://github.com/mozilla/BrowserQuest.git"
SCENARIOS: dict[str, dict[str, Any]] = {
    "touch": {
        "title": "precise mobile touch regression",
        "task": "mobile single-finger tap regression",
        "target_file": "client/js/main.js",
        "good_code": "event.originalEvent.touches[0]",
        "bad_code": "event.originalEvent.touches[1]",
        "prompt": (
            "Players report that mobile single-finger taps no longer move the character after recent "
            "compatibility work, while desktop clicks still work. Find and fix the smallest root cause. "
            "Do not modify generated or vendored assets. Inspect and verify locally as far as this legacy "
            "repository permits. In the final answer, briefly state the changed file and verification."
        ),
        "area_id": "mobile-controls",
        "area_title": "Mobile Controls",
        "description": "Mobile touch input and movement event adaptation.",
        "read_when": "Debugging touch, tap, pointer-coordinate, or mobile movement behavior.",
        "keywords": ["mobile", "touch", "tap", "finger", "pointer", "movement", "input"],
        "paths": ["client/js/main.js", "client/js/app.js", "client/js/game.js", "client/js/renderer.js"],
        "start_files": ["client/js/main.js", "client/js/app.js", "client/js/game.js"],
        "search_terms": ["touchstart", "touches", "setMouseCoordinates", "game.click"],
        "contracts": [
            "Mobile pointer input is adapted near the desktop click path before movement reaches game.click().",
            "Desktop click behavior remains unchanged during touch-only fixes.",
        ],
        "failure_modes": [
            "Browser touch wrappers and desktop mouse events expose coordinates through different object shapes.",
            "A local event-adaptation bug causes broad renderer or map changes.",
        ],
        "tests": ["node --check client/js/main.js"],
    },
    "zoning": {
        "title": "domain-routed mobile edge transition regression",
        "task": "phone bottom-edge camera transition",
        "target_file": "client/js/game.js",
        "good_code": "y = (z === Types.Orientations.UP) ? c.y - yoffset : c.y + yoffset;",
        "bad_code": "x = (z === Types.Orientations.UP) ? c.y - yoffset : c.y + yoffset;",
        "prompt": (
            "On phones, walking through the bottom edge of the visible world now makes the camera jump "
            "sideways instead of continuing into the next area. Desktop edge transitions still work. "
            "Find and fix the smallest root cause without changing generated maps or renderer behavior. "
            "Inspect and verify locally as far as this legacy repository permits. In the final answer, "
            "briefly state the changed file and verification."
        ),
        "area_id": "mobile-zoning",
        "area_title": "Mobile Edge Transitions",
        "description": "Mobile screen-edge transitions and camera zoning behavior.",
        "read_when": "Debugging phone or tablet movement across visible world boundaries.",
        "keywords": ["mobile", "phone", "edge", "boundary", "camera", "transition", "movement", "zoning"],
        "paths": ["client/js/game.js", "client/js/updater.js", "client/js/camera.js", "client/js/renderer.js"],
        "start_files": ["client/js/game.js", "client/js/updater.js", "client/js/camera.js"],
        "search_terms": ["zoning", "startZoningFrom", "getZoningOrientation", "updateZoning"],
        "contracts": [
            "Screen-edge map transitions are called zoning in the client code.",
            "Mobile and tablet zoning updates the camera directly; desktop zoning is animated by the updater.",
        ],
        "failure_modes": [
            "Mobile shortcut and desktop animation paths drift in coordinate behavior.",
            "A mobile-only zoning fix changes the desktop updater path unnecessarily.",
        ],
        "tests": ["node --check client/js/game.js"],
    },
}


def transient_rules(scenario: dict[str, Any]) -> str:
    return f"""# Agent Instructions

For this non-trivial bug, run `context-pack start --agent --task "{scenario['task']}"` before broad
repository reading. Use its inline Evidence first and search only the listed terms and scopes if
needed. Then verify source behavior and continue the requested fix. Do not persist Context Pack
setup in this repository.
"""


def curated_area_doc(scenario: dict[str, Any]) -> str:
    paths = "\n".join(f"  - {item}" for item in scenario["paths"])
    starts = "\n".join(f"- `{item}`" for item in scenario["start_files"])
    search = "\n".join(f"- `{item}`" for item in scenario["search_terms"])
    contracts = "\n".join(f"- {item}" for item in scenario["contracts"])
    failures = "\n".join(f"- {item}" for item in scenario["failure_modes"])
    tests = "\n".join(f"  - {item}" for item in scenario["tests"])
    return f"""---
id: {scenario['area_id']}
status: active
paths:
{paths}
tests:
{tests}
---

# {scenario['area_title']}

## Read When
- {scenario['read_when']}

## Start With
{starts}

## Search First
{search}

## Contracts
{contracts}

## Common Failure Modes
{failures}
"""


def run(cmd: list[str], cwd: Path, *, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], repo, check=check)


def discover_codex(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    configured = os.environ.get("CODEX_CLI_PATH")
    if configured:
        candidates.append(Path(configured).expanduser())
    local_bin = Path.home() / "AppData/Local/OpenAI/Codex/bin"
    if local_bin.is_dir():
        candidates.extend(sorted(local_bin.glob("*/codex.exe"), key=lambda path: path.stat().st_mtime, reverse=True))
    candidates.append(Path.home() / ".codex/.sandbox-bin/codex.exe")
    path_command = shutil.which("codex")
    if path_command:
        candidates.append(Path(path_command))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise SystemExit("Could not find a usable Codex CLI. Pass --codex <path>.")


def discover_context_pack(explicit: str | None) -> list[str]:
    if explicit:
        candidate = Path(shutil.which(explicit) or explicit).expanduser()
        if not candidate.is_file():
            raise SystemExit(f"Context Pack executable does not exist: {candidate}")
        return [str(candidate.resolve())]
    if not ENGINE_PATH.is_file():
        raise SystemExit("Could not find the working-tree Context Pack engine. Pass --context-pack <path>.")
    return [sys.executable, str(ENGINE_PATH)]


def install_context_pack_shim(workdir: Path, command: list[str]) -> Path:
    tool_bin = workdir / "context-pack-bin"
    tool_bin.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        shim = tool_bin / "context-pack.cmd"
        invocation = subprocess.list2cmdline(command)
        shim.write_text(f"@echo off\r\n{invocation} %*\r\n", encoding="utf-8", newline="")
    else:
        shim = tool_bin / "context-pack"
        invocation = shlex.join(command)
        shim.write_text(f"#!/bin/sh\nexec {invocation} \"$@\"\n", encoding="utf-8", newline="\n")
        shim.chmod(0o755)
    return tool_bin


def prepare_source(workdir: Path, source: str | None) -> Path:
    if source:
        source_path = Path(source).resolve()
        if not (source_path / ".git").exists():
            raise SystemExit(f"--source is not a Git checkout: {source_path}")
        return source_path
    source_path = workdir / "browserquest-source"
    run(["git", "clone", "--depth", "1", REPO_URL, str(source_path)], workdir, timeout=180)
    return source_path


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    status = git(repo, "status", "--porcelain=v1").stdout.strip()
    if status:
        git(repo, "commit", "-m", message)


def curated_manifest(scenario: dict[str, Any]) -> dict[str, Any]:
    area_id = str(scenario["area_id"])
    return {
        "version": 1,
        "generated_by": "context-pack-agent-ab",
        "areas": {
            area_id: {
                "kind": "source",
                "description": scenario["description"],
                "doc": f".context-pack/AREAS/{area_id}.md",
                "keywords": scenario["keywords"],
                "paths": scenario["paths"],
                "start_files": scenario["start_files"],
                "search_terms": scenario["search_terms"],
                "contracts": scenario["contracts"],
                "failure_modes": scenario["failure_modes"],
                "stale_if_paths": scenario["paths"],
                "tests": scenario["tests"],
            },
            "overview": {
                "kind": "overview",
                "description": "Fallback project orientation.",
                "doc": ".context-pack/AREAS/overview.md",
                "keywords": ["overview", "architecture"],
                "paths": ["README.md", ".context-pack/**"],
                "start_files": ["README.md", ".context-pack/INDEX.md"],
                "contracts": ["Verify source behavior before trusting context notes."],
                "failure_modes": ["Overview context displaces a task-specific route."],
                "stale_if_paths": ["README.md"],
                "tests": [],
            },
        },
    }


def prepare_trial(
    source: Path,
    target: Path,
    condition: str,
    context_pack: list[str],
    scenario: dict[str, Any],
) -> str:
    run(["git", "clone", "--quiet", str(source), str(target)], source.parent, timeout=180)
    git(target, "config", "user.name", "Context Pack Benchmark")
    git(target, "config", "user.email", "benchmark@example.invalid")

    target_file = target / str(scenario["target_file"])
    source_text = target_file.read_text(encoding="utf-8")
    good_code = str(scenario["good_code"])
    bad_code = str(scenario["bad_code"])
    count = source_text.count(good_code)
    if count != 1:
        raise RuntimeError(f"Expected one seed location in {scenario['target_file']}, found {count}")
    target_file.write_text(source_text.replace(good_code, bad_code, 1), encoding="utf-8", newline="\n")
    git(target, "add", str(scenario["target_file"]))
    git(target, "commit", "--amend", "--no-edit")

    if condition == "transient":
        (target / "AGENTS.md").write_text(transient_rules(scenario), encoding="utf-8", newline="\n")
        commit_all(target, "benchmark: add transient orientation rule")
    elif condition == "curated":
        run(
            [*context_pack, "setup", "--repo", str(target), "--agent-docs", "agents", "--no-infer-areas", "--quiet"],
            target,
        )
        manifest_path = target / ".context-pack/manifest.json"
        manifest_path.write_text(
            json.dumps(curated_manifest(scenario), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        area_path = target / f".context-pack/AREAS/{scenario['area_id']}.md"
        area_path.write_text(curated_area_doc(scenario), encoding="utf-8", newline="\n")
        run([*context_pack, "refresh", "--repo", str(target), "--quiet"], target)
        commit_all(target, "benchmark: add curated context pack")
    return git(target, "rev-parse", "HEAD").stdout.strip()


def parse_events(stdout: str) -> tuple[dict[str, int], str, list[str], int, int, int]:
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    final_message = ""
    commands: list[str] = []
    event_count = 0
    tool_output_chars = 0
    max_tool_output_chars = 0
    for raw in stdout.splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        event_count += 1
        if event.get("type") == "turn.completed":
            for key in usage:
                usage[key] = int((event.get("usage") or {}).get(key, usage[key]) or 0)
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message":
            final_message = str(item.get("text", ""))
        elif item.get("type") == "command_execution":
            commands.append(str(item.get("command", "")))
            output_chars = len(str(item.get("aggregated_output", "")))
            tool_output_chars += output_chars
            max_tool_output_chars = max(max_tool_output_chars, output_chars)
    return usage, final_message, commands, event_count, tool_output_chars, max_tool_output_chars


def trial_result(
    *,
    run_id: str,
    condition: str,
    trial: int,
    source: Path,
    runs_dir: Path,
    artifacts_dir: Path,
    codex: Path,
    context_pack: list[str],
    tool_bin: Path,
    model: str,
    reasoning: str,
    prompt: str,
    timeout: int,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    repo = runs_dir / run_id
    artifact = artifacts_dir / run_id
    artifact.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    error = ""
    return_code = -1
    seed_head = ""
    stdout = ""
    stderr = ""
    try:
        seed_head = prepare_trial(source, repo, condition, context_pack, scenario)
        cmd = [
            str(codex),
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "workspace-write",
            "--model",
            model,
            "-c",
            f'model_reasoning_effort="{reasoning}"',
            "-c",
            'approval_policy="never"',
        ]
        if os.name == "nt":
            cmd.extend(["-c", 'windows.sandbox="elevated"'])
        cmd.extend(["--cd", str(repo), prompt])
        proc = subprocess.run(
            cmd,
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={**os.environ, "PATH": str(tool_bin) + os.pathsep + os.environ.get("PATH", "")},
        )
        return_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        error = f"timeout after {timeout}s"
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    except Exception as exc:  # The result should preserve one failed trial without losing the batch.
        error = f"{type(exc).__name__}: {exc}"

    duration = time.perf_counter() - started
    usage, final_message, commands, event_count, tool_output_chars, max_tool_output_chars = parse_events(stdout)
    target_file = Path(str(scenario["target_file"]))
    target_path = repo / target_file
    target_text = target_path.read_text(encoding="utf-8") if target_path.is_file() else ""
    changed_files = []
    if (repo / ".git").exists():
        changed_files = [line for line in git(repo, "diff", "--name-only", check=False).stdout.splitlines() if line]
    fixed = str(scenario["good_code"]) in target_text and str(scenario["bad_code"]) not in target_text
    minimal = changed_files == [target_file.as_posix()]
    command_text = "\n".join(commands).lower()
    public_error = (error or (stderr.strip()[-500:] if return_code else "")).replace(str(repo), "<trial-repo>")

    (artifact / "events.jsonl").write_text(stdout, encoding="utf-8", newline="\n")
    (artifact / "stderr.log").write_text(stderr, encoding="utf-8", newline="\n")
    (artifact / "final.md").write_text(final_message, encoding="utf-8", newline="\n")
    if (repo / ".git").exists():
        diff = git(repo, "diff", "--", check=False).stdout
        (artifact / "patch.diff").write_text(diff, encoding="utf-8", newline="\n")

    return {
        "id": run_id,
        "condition": condition,
        "trial": trial,
        "status": "ok" if return_code == 0 and not error and usage["input_tokens"] else "error",
        "error": public_error,
        "return_code": return_code,
        "duration_seconds": round(duration, 3),
        "seed_head": seed_head[:12],
        "usage": {
            **usage,
            "uncached_input_tokens": max(0, usage["input_tokens"] - usage["cached_input_tokens"]),
            "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        },
        "quality": {
            "fixed": fixed,
            "minimal_patch": minimal,
            "changed_files": changed_files,
        },
        "context_pack_invoked": "context-pack" in command_text,
        "command_count": len(commands),
        "tool_output_chars": tool_output_chars,
        "max_tool_output_chars": max_tool_output_chars,
        "event_count": event_count,
    }


def metric_values(results: list[dict[str, Any]], condition: str, key: str) -> list[float]:
    return [
        float(item["usage"][key])
        for item in results
        if item["condition"] == condition and item["status"] == "ok"
    ]


def result_values(results: list[dict[str, Any]], condition: str, key: str) -> list[float]:
    return [
        float(item.get(key, 0))
        for item in results
        if item["condition"] == condition and item["status"] == "ok"
    ]


def summarize(results: list[dict[str, Any]], conditions: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    baseline_values = metric_values(results, "baseline", "input_tokens")
    baseline_median = statistics.median(baseline_values) if baseline_values else 0
    for condition in conditions:
        rows = [item for item in results if item["condition"] == condition]
        tokens = metric_values(results, condition, "input_tokens")
        uncached = metric_values(results, condition, "uncached_input_tokens")
        durations = [float(item["duration_seconds"]) for item in rows if item["status"] == "ok"]
        command_counts = result_values(results, condition, "command_count")
        tool_outputs = result_values(results, condition, "tool_output_chars")
        max_tool_outputs = result_values(results, condition, "max_tool_output_chars")
        median_tokens = statistics.median(tokens) if tokens else 0
        summary[condition] = {
            "runs": len(rows),
            "successful_runs": len(tokens),
            "fixed_runs": sum(bool(item["quality"]["fixed"]) for item in rows),
            "minimal_patch_runs": sum(bool(item["quality"]["minimal_patch"]) for item in rows),
            "context_pack_invocations": sum(bool(item["context_pack_invoked"]) for item in rows),
            "input_tokens_mean": round(statistics.mean(tokens), 1) if tokens else 0,
            "input_tokens_median": round(median_tokens, 1) if tokens else 0,
            "input_tokens_min": round(min(tokens), 1) if tokens else 0,
            "input_tokens_max": round(max(tokens), 1) if tokens else 0,
            "uncached_input_tokens_median": round(statistics.median(uncached), 1) if uncached else 0,
            "uncached_input_tokens_min": round(min(uncached), 1) if uncached else 0,
            "uncached_input_tokens_max": round(max(uncached), 1) if uncached else 0,
            "duration_seconds_median": round(statistics.median(durations), 3) if durations else 0,
            "command_count_median": round(statistics.median(command_counts), 1) if command_counts else 0,
            "tool_output_chars_median": round(statistics.median(tool_outputs), 1) if tool_outputs else 0,
            "max_tool_output_chars": round(max(max_tool_outputs), 1) if max_tool_outputs else 0,
            "input_reduction_vs_baseline_percent": round((1 - median_tokens / baseline_median) * 100, 1)
            if tokens and baseline_median
            else 0,
        }
    baseline_uncached = summary.get("baseline", {}).get("uncached_input_tokens_median", 0)
    baseline_duration = summary.get("baseline", {}).get("duration_seconds_median", 0)
    for item in summary.values():
        item["uncached_reduction_vs_baseline_percent"] = (
            round((1 - item["uncached_input_tokens_median"] / baseline_uncached) * 100, 1)
            if baseline_uncached and item["uncached_input_tokens_median"]
            else 0
        )
        item["duration_change_vs_baseline_percent"] = (
            round((item["duration_seconds_median"] / baseline_duration - 1) * 100, 1)
            if baseline_duration and item["duration_seconds_median"]
            else 0
        )
    return summary


def failed_result(result: dict[str, Any]) -> bool:
    quality = result.get("quality") or {}
    return (
        result.get("status") != "ok"
        or not quality.get("fixed")
        or not quality.get("minimal_patch")
    )


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Codex CLI Agent A/B",
        "",
        f"- Generated at: {data['generated_at']}",
        f"- Codex CLI: `{data['codex_version']}`",
        f"- Context Pack: `{data['context_pack_version']}`",
        f"- Context Pack engine SHA-256: `{data['context_pack_engine_sha256']}`",
        f"- Model: `{data['model']}`; reasoning: `{data['reasoning_effort']}`",
        f"- Scenario: `{data['scenario']}` ({data['scenario_title']})",
        f"- Subject: `mozilla/BrowserQuest@{data['source_head']}` with the same hidden seeded regression",
        f"- Trials: {data['trials_per_condition']} per condition; max parallel workers: {data['max_workers']}",
        "",
        "## Aggregate",
        "",
        "| Condition | Correct | Median total input | Total range | Total reduction | Median uncached | Uncached reduction | Median time | Time change |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in data["conditions"]:
        item = data["summary"][condition]
        lines.append(
            f"| {condition} | {item['fixed_runs']}/{item['runs']} | {item['input_tokens_median']:,.0f} | "
            f"{item['input_tokens_min']:,.0f}-{item['input_tokens_max']:,.0f} | "
            f"{item['input_reduction_vs_baseline_percent']:+.1f}% | {item['uncached_input_tokens_median']:,.0f} | "
            f"{item['uncached_reduction_vs_baseline_percent']:+.1f}% | {item['duration_seconds_median']:.1f}s | "
            f"{item['duration_change_vs_baseline_percent']:+.1f}% |"
        )
    lines.extend(
        [
            "",
            "## Agent Loop",
            "",
            "| Condition | Median commands | Median tool output chars | Largest single tool output |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for condition in data["conditions"]:
        item = data["summary"][condition]
        lines.append(
            f"| {condition} | {item['command_count_median']:.1f} | "
            f"{item['tool_output_chars_median']:,.0f} | {item['max_tool_output_chars']:,.0f} |"
        )
    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| Run | Condition | Status | Input | Cached | Output | Commands | Tool chars | Time | Fixed | Minimal |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in sorted(data["results"], key=lambda row: (row["condition"], row["trial"])):
        usage = item["usage"]
        quality = item["quality"]
        lines.append(
            f"| {item['id']} | {item['condition']} | {item['status']} | {usage['input_tokens']:,} | "
            f"{usage['cached_input_tokens']:,} | {usage['output_tokens']:,} | {item['command_count']} | "
            f"{item['tool_output_chars']:,} | {item['duration_seconds']:.1f}s | "
            f"{'yes' if quality['fixed'] else 'no'} | {'yes' if quality['minimal_patch'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Limits",
            "",
            "- Tokens are the actual usage reported by Codex CLI `turn.completed`, not `chars/4` estimates.",
            "- `input_tokens` includes cached input and repeated model calls during the task; provider billing can weight cached tokens differently.",
            "- Total input is the best available CLI usage total, while uncached input better reflects newly processed context; neither is a direct invoice amount.",
            "- Parallel trials reduce wall-clock time but do not remove model variance, shared-prefix caching, or service-load effects.",
            "- This seeded task measures one legacy JavaScript bug. It does not prove a universal reduction or general patch-quality gain.",
            "- Curated context includes task-relevant project knowledge; transient context has routing rules but no maintained semantic note.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run parallel Codex CLI token and patch-quality A/B trials.")
    parser.add_argument("--source", help="Existing BrowserQuest checkout; otherwise a shallow clone is created.")
    parser.add_argument("--codex", help="Codex CLI executable path.")
    parser.add_argument("--context-pack", help="Context Pack CLI executable path.")
    parser.add_argument("--scenario", default="touch", choices=sorted(SCENARIOS))
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high", "ultra"])
    parser.add_argument("--trials", type=int, default=2, help="Trials per condition.")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=300, help="Seconds per Codex run.")
    parser.add_argument("--conditions", nargs="+", default=["baseline", "transient", "curated"], choices=["baseline", "transient", "curated"])
    parser.add_argument("--prompt", help="Override the selected scenario prompt.")
    parser.add_argument("--workdir", help="Workspace for clones and raw artifacts.")
    parser.add_argument("--keep-workdir", action="store_true")
    parser.add_argument("--json", help="Write aggregate JSON results.")
    parser.add_argument("--markdown", help="Write aggregate Markdown results.")
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit non-zero for a run error, incorrect fix, or non-minimal patch.",
    )
    args = parser.parse_args(argv)

    if args.trials < 1 or args.max_workers < 1:
        parser.error("--trials and --max-workers must be positive")
    if "baseline" not in args.conditions:
        parser.error("--conditions must include baseline so reductions have a reference")
    if len(set(args.conditions)) != len(args.conditions):
        parser.error("--conditions must not contain duplicates")

    codex = discover_codex(args.codex)
    context_pack = discover_context_pack(args.context_pack)
    scenario = SCENARIOS[args.scenario]
    prompt = args.prompt or str(scenario["prompt"])
    workdir = Path(args.workdir).resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="context-pack-codex-ab-"))
    workdir.mkdir(parents=True, exist_ok=True)
    tool_bin = install_context_pack_shim(workdir, context_pack)
    cleanup = not args.keep_workdir and not args.workdir
    runs_dir = workdir / "runs"
    artifacts_dir = workdir / "artifacts"
    runs_dir.mkdir(exist_ok=True)
    artifacts_dir.mkdir(exist_ok=True)

    try:
        source = prepare_source(workdir, args.source)
        source_head = git(source, "rev-parse", "HEAD").stdout.strip()
        codex_version = run([str(codex), "--version"], ROOT).stdout.strip()
        context_pack_version = run([*context_pack, "--version"], ROOT).stdout.strip()
        engine_sha256 = hashlib.sha256(ENGINE_PATH.read_bytes()).hexdigest() if not args.context_pack else "external"
        jobs = [
            (condition, trial)
            for trial in range(1, args.trials + 1)
            for condition in args.conditions
        ]
        random.Random(20260711).shuffle(jobs)
        results: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.max_workers, len(jobs))) as executor:
            futures = {
                executor.submit(
                    trial_result,
                    run_id=f"{condition}-{trial}",
                    condition=condition,
                    trial=trial,
                    source=source,
                    runs_dir=runs_dir,
                    artifacts_dir=artifacts_dir,
                    codex=codex,
                    context_pack=context_pack,
                    tool_bin=tool_bin,
                    model=args.model,
                    reasoning=args.reasoning_effort,
                    prompt=prompt,
                    timeout=args.timeout,
                    scenario=scenario,
                ): (condition, trial)
                for condition, trial in jobs
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                usage = result["usage"]
                print(
                    f"{result['id']}: {result['status']}; input={usage['input_tokens']}; "
                    f"cached={usage['cached_input_tokens']}; fixed={result['quality']['fixed']}; "
                    f"time={result['duration_seconds']:.1f}s",
                    flush=True,
                )

        data = {
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "codex_version": codex_version,
            "context_pack_version": context_pack_version,
            "context_pack_engine_sha256": engine_sha256,
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "repo": "mozilla/BrowserQuest",
            "source_head": source_head,
            "scenario": args.scenario,
            "scenario_title": scenario["title"],
            "seed": {
                "file": scenario["target_file"],
                "from": scenario["good_code"],
                "to": scenario["bad_code"],
            },
            "prompt": prompt,
            "conditions": args.conditions,
            "trials_per_condition": args.trials,
            "max_workers": min(args.max_workers, len(jobs)),
            "summary": summarize(results, args.conditions),
            "results": sorted(results, key=lambda row: (row["condition"], row["trial"])),
        }
        markdown = render_markdown(data)
        if args.json:
            output = Path(args.json)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        if args.markdown:
            output = Path(args.markdown)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8", newline="\n")
        print(markdown)
        has_failure = any(failed_result(item) for item in results)
        return 1 if args.fail_on_error and has_failure else 0
    finally:
        if cleanup:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
