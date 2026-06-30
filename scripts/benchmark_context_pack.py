from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import stat
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "plugins" / "context-pack" / "skills" / "context-pack" / "scripts" / "context_pack.py"


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    repo: str
    url: str
    prompt: str
    expected: tuple[str, ...]
    max_ratio: int


PUBLIC_SCENARIOS = [
    Scenario("sampleproject-ci", "pypa/sampleproject", "https://github.com/pypa/sampleproject.git", "ci is red", ("automation", "source", "tests"), 75),
    Scenario("requests-tests", "psf/requests", "https://github.com/psf/requests.git", "why are tests failing", ("source", "tests"), 40),
    Scenario("click-shell-completion", "pallets/click", "https://github.com/pallets/click.git", "fix shell completion bug", ("source", "tests"), 65),
    Scenario("httpx-build", "encode/httpx", "https://github.com/encode/httpx.git", "build failed", ("automation", "source", "tests"), 85),
    Scenario("browserquest-mobile", "mozilla/BrowserQuest", "https://github.com/mozilla/BrowserQuest.git", "fix mobile controls bug on touch devices", ("source",), 25),
    Scenario("browserquest-sprites", "mozilla/BrowserQuest", "https://github.com/mozilla/BrowserQuest.git", "fix missing sprite asset loading bug", ("source", "sprites"), 25),
    Scenario("browserquest-websocket", "mozilla/BrowserQuest", "https://github.com/mozilla/BrowserQuest.git", "debug websocket login connect failure", ("source",), 25),
    Scenario("gin-middleware", "gin-gonic/gin", "https://github.com/gin-gonic/gin.git", "fix middleware panic bug", ("source",), 20),
    Scenario("express-router", "expressjs/express", "https://github.com/expressjs/express.git", "fix router middleware error handling", ("source",), 55),
    Scenario("fd-rust-filter", "sharkdp/fd", "https://github.com/sharkdp/fd.git", "fix regex filter bug", ("source",), 45),
]


def load_engine():
    spec = importlib.util.spec_from_file_location("context_pack_benchmark_engine", ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git_text(repo: Path, args: list[str]) -> str:
    return run(["git", *args], cwd=repo).stdout.strip()


def slug(repo: str) -> str:
    return repo.replace("/", "__")


def clone_or_reuse(url: str, repo_name: str, workdir: Path, *, reuse: bool) -> Path:
    target = workdir / slug(repo_name)
    if target.exists() and reuse:
        return target
    if target.exists():
        remove_tree(target)
    run(["git", "clone", "--depth", "1", url, str(target)], cwd=workdir)
    return target


def remove_tree(path: Path) -> None:
    def onerror(func, item, exc_info):
        try:
            os.chmod(item, stat.S_IWRITE)
            func(item)
        except OSError:
            raise

    shutil.rmtree(path, onerror=onerror)


def parse_read_first(pack: str) -> list[str]:
    items: list[str] = []
    in_section = False
    for line in pack.splitlines():
        stripped = line.strip()
        if stripped == "## Read First":
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section or not stripped.startswith("- "):
            continue
        value = stripped[2:].strip()
        if value == "none":
            continue
        if value.startswith("`"):
            value = value.split("`", 2)[1]
        value = value.replace(" (missing)", "").strip()
        if value:
            items.append(value)
    return items


def measure_repo(engine: Any, repo: Path, scenario: Scenario) -> dict[str, Any]:
    started = time.perf_counter()
    snapshot = engine.collect_snapshot(repo.resolve())
    layout = engine.resolve_layout(repo)
    has_context_library = (repo / layout.manifest_path).exists()
    manifest = engine.load_manifest(repo, layout)
    if not has_context_library:
        manifest = engine.merge_inferred_areas(repo, manifest, layout)
    matches = engine.selected_area_matches(manifest, changed_files=[], task=scenario.prompt)
    primary = matches[:4]
    pack = engine.render_pack(
        repo,
        manifest,
        snapshot,
        primary,
        layout=layout,
        related_selections=matches[4:],
        changed_files=[],
        task=scenario.prompt,
        mode="work",
    )
    duration_ms = round((time.perf_counter() - started) * 1000)
    repo_file_list = engine.repo_files(repo)
    repo_budget = engine.text_budget_for_files(repo, repo_file_list)
    read_first = parse_read_first(pack)
    read_first_files = engine.files_for_read_first_entries(repo, read_first, repo_file_list)
    read_budget = engine.text_budget_for_files(repo, read_first_files)
    repo_tokens = engine.estimated_tokens(repo_budget.chars)
    read_tokens = engine.estimated_tokens(read_budget.chars)
    ratio = round((read_tokens / repo_tokens) * 100) if repo_tokens and read_tokens else 0
    selected = [item.area_id for item in primary]
    selected_set = set(selected)
    expected_set = set(scenario.expected)
    weak_flags: list[str] = []
    if selected == ["overview"]:
        weak_flags.append("overview_fallback")
    if not expected_set.issubset(selected_set):
        weak_flags.append("expected_miss")
    if ratio > scenario.max_ratio:
        weak_flags.append("high_budget")
    if duration_ms > 5000:
        weak_flags.append("slow_measure")
    return {
        "name": scenario.name,
        "repo": scenario.repo,
        "head": snapshot.head,
        "prompt": scenario.prompt,
        "selected": selected,
        "expected": list(scenario.expected),
        "expected_ok": expected_set.issubset(selected_set),
        "repo_files": len(repo_file_list),
        "read_first_entries": len(read_first),
        "read_first_files": read_budget.files,
        "repo_text_files": repo_budget.files,
        "read_tokens": read_tokens,
        "repo_tokens": repo_tokens,
        "read_ratio": ratio,
        "reduction": max(0, 100 - ratio),
        "max_ratio": scenario.max_ratio,
        "duration_ms": duration_ms,
        "weak_flags": weak_flags,
        "reasons": {item.area_id: item.reasons for item in primary},
    }


def configure_git(repo: Path) -> None:
    run(["git", "init"], cwd=repo)
    run(["git", "branch", "-M", "main"], cwd=repo)
    run(["git", "config", "user.name", "Context Pack Benchmark"], cwd=repo)
    run(["git", "config", "user.email", "context-pack-benchmark@example.invalid"], cwd=repo)


def routing_signature(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected": result["selected"],
        "read_first_entries": result["read_first_entries"],
        "read_first_files": result["read_first_files"],
        "read_tokens": result["read_tokens"],
        "repo_tokens": result["repo_tokens"],
        "read_ratio": result["read_ratio"],
    }


def run_replay_benchmark(engine: Any, workdir: Path) -> dict[str, Any]:
    repo = workdir / "handoff-replay-source"
    if repo.exists():
        remove_tree(repo)
    repo.mkdir(parents=True, exist_ok=True)
    configure_git(repo)
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "README.md").write_text("# Replay demo\n", encoding="utf-8")
    (repo / "src" / "auth.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
    (repo / "tests" / "test_auth.py").write_text(
        "from src.auth import login_timeout\n\n"
        "def test_login_timeout():\n"
        "    assert login_timeout() == 30\n",
        encoding="utf-8",
    )
    engine.main(["setup", "--repo", str(repo), "--quiet"])
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "initial"], cwd=repo)
    engine.main(["checkpoint", "--repo", str(repo), "--publish", "--pack", "--quiet"])
    run(["git", "add", ".context-pack/CURRENT.md", ".context-pack/LOG.md"], cwd=repo)
    run(["git", "commit", "-m", "publish handoff"], cwd=repo)

    scenario = Scenario(
        "handoff-replay",
        "synthetic/handoff-replay",
        "",
        "why are tests failing",
        ("source", "tests"),
        25,
    )
    first = measure_repo(engine, repo, scenario)
    clone = workdir / "handoff-replay-clone"
    if clone.exists():
        remove_tree(clone)
    run(["git", "clone", str(repo), str(clone)], cwd=workdir)
    second = measure_repo(engine, clone, scenario)
    first_sig = routing_signature(first)
    second_sig = routing_signature(second)
    return {
        "name": "handoff-replay",
        "prompt": scenario.prompt,
        "same_signature": first_sig == second_sig,
        "source": first_sig,
        "clone": second_sig,
        "weak_flags": [] if first_sig == second_sig else ["replay_mismatch"],
    }


def format_tokens(value: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return str(value)


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Context Pack Benchmark Run",
        "",
        f"- Generated at: {data['generated_at']}",
        f"- Engine version: `{data['engine_version']}`",
        f"- Subject HEAD: `{data['subject_head']}`",
        f"- Public scenarios: {len(data['public_results'])}",
        f"- Weak public scenarios: {len(data['weak_public_results'])}",
        "",
        "## Public Orientation Results",
        "",
        "| Scenario | Repo | Prompt | Selected | Read / Repo Tokens | Ratio | Duration | Flags |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in data["public_results"]:
        flags = ", ".join(item["weak_flags"]) if item["weak_flags"] else "ok"
        lines.append(
            "| {name} | `{repo}` | `{prompt}` | `{selected}` | ~{read} / ~{repo_tokens} | {ratio}% | {duration} ms | {flags} |".format(
                name=item["name"],
                repo=item["repo"],
                prompt=item["prompt"],
                selected=", ".join(item["selected"]),
                read=format_tokens(item["read_tokens"]),
                repo_tokens=format_tokens(item["repo_tokens"]),
                ratio=item["read_ratio"],
                duration=item["duration_ms"],
                flags=flags,
            )
        )
    lines.extend(["", "## Handoff Replay", ""])
    replay = data["handoff_replay"]
    lines.extend(
        [
            f"- Same routing signature after local clone: {'yes' if replay['same_signature'] else 'no'}",
            f"- Source signature: `{json.dumps(replay['source'], sort_keys=True)}`",
            f"- Clone signature: `{json.dumps(replay['clone'], sort_keys=True)}`",
        ]
    )
    if data["weak_public_results"] or replay["weak_flags"]:
        lines.extend(["", "## Weak Spots", ""])
        for item in data["weak_public_results"]:
            lines.append(f"- `{item['name']}`: {', '.join(item['weak_flags'])}")
        for flag in replay["weak_flags"]:
            lines.append(f"- `handoff-replay`: {flag}")
    else:
        lines.extend(["", "## Weak Spots", "", "- none under this benchmark's thresholds"])
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- Token counts are approximate `chars/4` text-budget estimates, not provider billing tokens.",
            "- Durations are local wall-clock checks for regression signals and are machine/cache dependent.",
            "- This measures deterministic orientation and replay, not independent agent patch quality.",
            "- Public repos are shallow clones at the recorded HEAD.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_benchmarks(args: argparse.Namespace) -> dict[str, Any]:
    engine = load_engine()
    if args.workdir:
        workdir = Path(args.workdir).resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        workdir = Path(tempfile.mkdtemp(prefix="context-pack-benchmark-"))
        cleanup = not args.keep_workdir
    try:
        public_results = []
        if args.public:
            cloned_repos: dict[str, Path] = {}
            for scenario in PUBLIC_SCENARIOS:
                if scenario.repo not in cloned_repos:
                    cloned_repos[scenario.repo] = clone_or_reuse(scenario.url, scenario.repo, workdir, reuse=args.reuse)
                repo_path = cloned_repos[scenario.repo]
                public_results.append(measure_repo(engine, repo_path, scenario))
        replay = run_replay_benchmark(engine, workdir)
        data = {
            "generated_at": engine.now_local(),
            "engine_version": engine.CONTEXT_PACK_VERSION,
            "subject_head": git_text(ROOT, ["rev-parse", "--short=12", "HEAD"]),
            "workdir": str(workdir),
            "public_results": public_results,
            "weak_public_results": [item for item in public_results if item["weak_flags"]],
            "handoff_replay": replay,
        }
        if args.json:
            output = Path(args.json)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.markdown:
            output = Path(args.markdown)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_markdown(data), encoding="utf-8", newline="\n")
        return data
    finally:
        if cleanup:
            shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Context Pack orientation and replay benchmarks.")
    parser.add_argument("--public", action="store_true", help="Clone and benchmark public GitHub repositories.")
    parser.add_argument("--workdir", help="Workspace for benchmark clones and synthetic repos.")
    parser.add_argument("--reuse", action="store_true", help="Reuse existing clones in --workdir.")
    parser.add_argument("--keep-workdir", action="store_true", help="Keep temporary benchmark workspace.")
    parser.add_argument("--json", help="Write machine-readable benchmark results.")
    parser.add_argument("--markdown", help="Write a Markdown benchmark report.")
    parser.add_argument("--fail-on-weak", action="store_true", help="Exit non-zero when a scenario exceeds thresholds.")
    args = parser.parse_args(argv)
    data = run_benchmarks(args)
    print(render_markdown(data))
    weak_count = len(data["weak_public_results"]) + len(data["handoff_replay"]["weak_flags"])
    return 1 if args.fail_on_weak and weak_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
