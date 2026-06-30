from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import benchmark_context_pack as bench


ROOT = Path(__file__).resolve().parents[1]


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


def create_synthetic_repo(repo: Path) -> None:
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "docs").mkdir()
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "README.md").write_text("# Synthetic app\n", encoding="utf-8")
    (repo / "src" / "auth.py").write_text(
        "def login_timeout():\n"
        "    return 30\n\n"
        "def login(user, password):\n"
        "    return bool(user and password)\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_auth.py").write_text(
        "from src.auth import login_timeout\n\n"
        "def test_login_timeout():\n"
        "    assert login_timeout() == 45\n",
        encoding="utf-8",
    )
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    for idx in range(60):
        (repo / "docs" / f"note_{idx:02}.md").write_text(
            "# Background note\n\n"
            f"Noise file {idx}. This file is intentionally unrelated to login timeout failures.\n",
            encoding="utf-8",
        )


def expected_files_present(result: dict[str, Any], expected_files: list[str], repo: Path, engine: Any) -> bool:
    repo_file_list = engine.repo_files(repo)
    read_first = []
    scenario = bench.Scenario(
        "synthetic",
        "synthetic/trace",
        "",
        result["prompt"],
        tuple(result["expected"]),
        100,
    )
    snapshot = engine.collect_snapshot(repo.resolve())
    layout = engine.resolve_layout(repo)
    manifest = engine.load_manifest(repo, layout)
    if not (repo / layout.manifest_path).exists():
        manifest = engine.merge_inferred_areas(repo, manifest, layout)
    matches = engine.selected_area_matches(manifest, changed_files=[], task=scenario.prompt)
    pack = engine.render_pack(
        repo,
        manifest,
        snapshot,
        matches[:4],
        layout=layout,
        related_selections=matches[4:],
        changed_files=[],
        task=scenario.prompt,
        mode="work",
    )
    read_first = bench.parse_read_first(pack)
    read_files = set(engine.files_for_read_first_entries(repo, read_first, repo_file_list))
    return all(item in read_files for item in expected_files)


def run_synthetic_ab(engine: Any, workdir: Path) -> dict[str, Any]:
    repo = workdir / "synthetic-ab"
    if repo.exists():
        bench.remove_tree(repo)
    repo.mkdir(parents=True)
    create_synthetic_repo(repo)

    repo_file_list = engine.repo_files(repo)
    repo_budget = engine.text_budget_for_files(repo, repo_file_list)
    scenario = bench.Scenario(
        "synthetic-test-failure",
        "synthetic/ab",
        "",
        "why are tests failing",
        ("source", "tests"),
        35,
    )
    with_context = bench.measure_repo(engine, repo, scenario)
    expected_files = ["src/auth.py", "tests/test_auth.py"]
    return {
        "name": scenario.name,
        "prompt": scenario.prompt,
        "without_context": {
            "mode": "broad repo text budget",
            "files": len(repo_file_list),
            "text_files": repo_budget.files,
            "tokens": engine.estimated_tokens(repo_budget.chars),
        },
        "with_context": {
            "selected": with_context["selected"],
            "read_first_files": with_context["read_first_files"],
            "read_tokens": with_context["read_tokens"],
            "read_ratio": with_context["read_ratio"],
            "reduction": with_context["reduction"],
            "expected_files_present": expected_files_present(with_context, expected_files, repo, engine),
        },
        "expected_files": expected_files,
        "weak_flags": with_context["weak_flags"],
    }


def run_session_consistency(engine: Any, workdir: Path) -> dict[str, Any]:
    repo = workdir / "session-source"
    if repo.exists():
        bench.remove_tree(repo)
    repo.mkdir(parents=True)
    bench.configure_git(repo)
    create_synthetic_repo(repo)
    engine.main(["setup", "--repo", str(repo), "--quiet"])
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "initial"], cwd=repo)
    engine.main(["checkpoint", "--repo", str(repo), "--publish", "--pack", "--quiet"])
    run(["git", "add", ".context-pack/CURRENT.md", ".context-pack/LOG.md"], cwd=repo)
    run(["git", "commit", "-m", "publish handoff"], cwd=repo)

    clone = workdir / "session-clone"
    if clone.exists():
        bench.remove_tree(clone)
    run(["git", "clone", str(repo), str(clone)], cwd=workdir)

    scenarios = [
        bench.Scenario("tests-failing", "synthetic/session", "", "why are tests failing", ("source", "tests"), 35),
        bench.Scenario("ci-red", "synthetic/session", "", "ci is red", ("automation", "source", "tests"), 45),
        bench.Scenario("login-timeout", "synthetic/session", "", "fix login timeout", ("source", "tests"), 35),
    ]
    prompt_results = []
    for scenario in scenarios:
        source_result = bench.measure_repo(engine, repo, scenario)
        clone_result = bench.measure_repo(engine, clone, scenario)
        source_sig = bench.routing_signature(source_result)
        clone_sig = bench.routing_signature(clone_result)
        prompt_results.append(
            {
                "name": scenario.name,
                "prompt": scenario.prompt,
                "source": source_sig,
                "clone": clone_sig,
                "same_signature": source_sig == clone_sig,
                "weak_flags": source_result["weak_flags"] + clone_result["weak_flags"],
            }
        )
    return {
        "name": "session-consistency",
        "same_all": all(item["same_signature"] and not item["weak_flags"] for item in prompt_results),
        "prompts": prompt_results,
    }


def render_markdown(data: dict[str, Any]) -> str:
    ab = data["synthetic_ab"]
    lines = [
        "# Remaining Validation Run",
        "",
        f"- Generated at: {data['generated_at']}",
        f"- Engine version: `{data['engine_version']}`",
        f"- Subject HEAD: `{data['subject_head']}`",
        "",
        "## Synthetic A/B Proxy",
        "",
        "| Prompt | Without Context Pack | With Context Pack | Reduction | Expected files present | Flags |",
        "| --- | ---: | ---: | ---: | --- | --- |",
        "| {prompt} | ~{without_tokens} tokens / {without_files} files | ~{with_tokens} tokens / {with_files} files | {reduction}% | {present} | {flags} |".format(
            prompt=ab["prompt"],
            without_tokens=ab["without_context"]["tokens"],
            without_files=ab["without_context"]["files"],
            with_tokens=ab["with_context"]["read_tokens"],
            with_files=ab["with_context"]["read_first_files"],
            reduction=ab["with_context"]["reduction"],
            present="yes" if ab["with_context"]["expected_files_present"] else "no",
            flags=", ".join(ab["weak_flags"]) if ab["weak_flags"] else "ok",
        ),
        "",
        "## Session Consistency",
        "",
        "| Prompt | Source signature | Clone signature | Same | Flags |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in data["session_consistency"]["prompts"]:
        flags = ", ".join(item["weak_flags"]) if item["weak_flags"] else "ok"
        lines.append(
            "| {prompt} | `{source}` | `{clone}` | {same} | {flags} |".format(
                prompt=item["prompt"],
                source=json.dumps(item["source"], sort_keys=True),
                clone=json.dumps(item["clone"], sort_keys=True),
                same="yes" if item["same_signature"] else "no",
                flags=flags,
            )
        )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- This is a deterministic proxy for agent orientation, not a true independent LLM patch-quality benchmark.",
            "- It checks first relevant context, routing stability, and fresh-clone signature consistency.",
            "- True answer-quality validation still needs separate agent runs with captured transcripts.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    engine = bench.load_engine()
    workdir = Path(args.workdir).resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="context-pack-remaining-"))
    workdir.mkdir(parents=True, exist_ok=True)
    cleanup = not args.keep_workdir and not args.workdir
    try:
        data = {
            "generated_at": engine.now_local(),
            "engine_version": engine.CONTEXT_PACK_VERSION,
            "subject_head": bench.git_text(ROOT, ["rev-parse", "--short=12", "HEAD"]),
            "workdir": str(workdir),
            "synthetic_ab": run_synthetic_ab(engine, workdir),
            "session_consistency": run_session_consistency(engine, workdir),
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
    parser = argparse.ArgumentParser(description="Run remaining Context Pack validation checks.")
    parser.add_argument("--workdir", help="Workspace for validation repos.")
    parser.add_argument("--keep-workdir", action="store_true", help="Keep temporary validation workspace.")
    parser.add_argument("--json", help="Write machine-readable validation results.")
    parser.add_argument("--markdown", help="Write a Markdown validation report.")
    parser.add_argument("--fail-on-weak", action="store_true", help="Exit non-zero when validation flags are present.")
    args = parser.parse_args(argv)
    data = run_validation(args)
    print(render_markdown(data))
    weak = []
    weak.extend(data["synthetic_ab"]["weak_flags"])
    for item in data["session_consistency"]["prompts"]:
        if not item["same_signature"]:
            weak.append(f"{item['name']}: signature_mismatch")
        weak.extend(item["weak_flags"])
    return 1 if args.fail_on_weak and weak else 0


if __name__ == "__main__":
    raise SystemExit(main())
