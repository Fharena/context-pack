from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SUBPROCESS_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


def run(args: list[str], *, cwd: pathlib.Path = ROOT) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, env=SUBPROCESS_ENV, check=True)


def run_output(args: list[str], expected: str | list[str], *, cwd: pathlib.Path = ROOT) -> str:
    print("+", " ".join(args), flush=True)
    output = subprocess.check_output(args, cwd=cwd, env=SUBPROCESS_ENV, encoding="utf-8")
    for value in [expected] if isinstance(expected, str) else expected:
        if value not in output:
            raise AssertionError(f"Expected {value!r} in output:\n{output}")
    print(output, end="")
    return output


def configure_git_repo(repo: pathlib.Path) -> None:
    run(["git", "init"], cwd=repo)
    run(["git", "branch", "-M", "main"], cwd=repo)
    run(["git", "config", "user.name", "Context Pack Test"], cwd=repo)
    run(["git", "config", "user.email", "context-pack@example.invalid"], cwd=repo)


def write_demo_repo(repo: pathlib.Path) -> None:
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "README.md").write_text("# Demo app\n", encoding="utf-8")
    (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
    (repo / "tests/test_app.py").write_text("def test_login_timeout():\n    assert True\n", encoding="utf-8")
    for index in range(25):
        (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")


def validate_transient_start(binary: pathlib.Path, workspace: pathlib.Path) -> None:
    repo = workspace / "transient"
    repo.mkdir()
    configure_git_repo(repo)
    write_demo_repo(repo)
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "initial"], cwd=repo)
    before = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"], cwd=repo, text=True)

    run_output(
        [str(binary), "start", "--repo", str(repo), "--task", "fix login timeout"],
        [
            "Context library: transient",
            "Generated work pack for task: inline (not written)",
            "Selected areas: source, tests",
            "Context pack follows",
            "## Search First",
        ],
    )
    agent_output = run_output(
        [str(binary), "start", "--agent", "--repo", str(repo), "--task", "fix login timeout"],
        ["# Context Pack", "## Evidence", "login_timeout"],
    )
    assert "Context Pack Start for" not in agent_output

    after = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"], cwd=repo, text=True)
    assert before == after
    assert not (repo / ".context-pack").exists()
    assert not (repo / "AGENTS.md").exists()
    assert not (repo / ".gitignore").exists()
    assert not (repo / ".git/context-pack/CONTEXT_PACK.md").exists()


def validate_configured_flow(binary: pathlib.Path, workspace: pathlib.Path) -> None:
    repo = workspace / "configured"
    repo.mkdir()
    configure_git_repo(repo)
    write_demo_repo(repo)
    run([str(binary), "setup", "--repo", str(repo), "--quiet"])
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "initial"], cwd=repo)

    run_output(
        [str(binary), "start", "--repo", str(repo), "--task", "why are tests failing"],
        ["Generated work pack for task", "Selected areas: source, tests"],
    )

    run(["git", "checkout", "-b", "feature/review-demo"], cwd=repo)
    (repo / "src/app.py").write_text("def login_timeout():\n    return 45\n", encoding="utf-8")
    run(["git", "add", "src/app.py"], cwd=repo)
    run(["git", "commit", "-m", "tune login timeout"], cwd=repo)
    run_output(
        [str(binary), "start", "--repo", str(repo), "--review"],
        ["Generated review pack for review", "Review base: main (auto)", "Selected areas: source"],
    )
    pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
    assert "Mode: review" in pack
    assert "src/app.py" in pack

    (repo / "src/app.py").write_text("def login_timeout():\n    return 60\n", encoding="utf-8")
    before_checkpoint_status = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-uall"], cwd=repo, encoding="utf-8"
    )
    run([str(binary), "checkpoint", "--repo", str(repo), "--pack", "--quiet"])
    after_checkpoint_status = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-uall"], cwd=repo, encoding="utf-8"
    )
    assert before_checkpoint_status == after_checkpoint_status


def validate_security_boundary(binary: pathlib.Path, workspace: pathlib.Path) -> None:
    repo = workspace / "security"
    repo.mkdir()
    configure_git_repo(repo)
    write_demo_repo(repo)
    run([str(binary), "setup", "--repo", str(repo), "--quiet"])

    sentinel = "OUTSIDE_PACKAGE_SENTINEL"
    outside = workspace / "outside.py"
    outside.write_text(f"{sentinel} = True\n", encoding="utf-8")
    manifest_path = repo / ".context-pack/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["areas"]["overview"]["start_files"] = ["../outside.py"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    args = [str(binary), "start", "--agent", "--repo", str(repo), "--task", "fix onboarding"]
    print("+", " ".join(args), flush=True)
    proc = subprocess.run(args, cwd=repo, env=SUBPROCESS_ENV, capture_output=True, text=True)
    combined = proc.stdout + proc.stderr
    if proc.returncode != 2:
        raise AssertionError(f"Expected unsafe manifest rejection, got {proc.returncode}:\n{combined}")
    if sentinel in combined:
        raise AssertionError(f"Outside sentinel leaked through packaged CLI:\n{combined}")
    if "refused an unsafe repository path" not in combined:
        raise AssertionError(f"Missing boundary error from packaged CLI:\n{combined}")


def main() -> int:
    npm = shutil.which("npm") or "npm"
    with tempfile.TemporaryDirectory(prefix="context-pack-package-validation-") as tmp:
        workspace = pathlib.Path(tmp)
        pack_dir = workspace / "npm-pack"
        prefix = workspace / "npm-install"
        pack_dir.mkdir()
        prefix.mkdir()
        info = json.loads(
            subprocess.check_output(
                [npm, "pack", "--json", "--pack-destination", str(pack_dir)],
                cwd=ROOT,
                text=True,
            )
        )
        tgz = pack_dir / info[0]["filename"]
        run([npm, "install", "--prefix", str(prefix), str(tgz), "--silent"])
        binary = prefix / "node_modules" / ".bin" / ("context-pack.cmd" if os.name == "nt" else "context-pack")

        run_output([str(binary)], ["Normal use:", "context-pack setup --dry-run"])
        run_output([str(binary), "--version"], info[0]["version"])
        run([str(binary), "--help"])
        validate_transient_start(binary, workspace)
        validate_configured_flow(binary, workspace)
        validate_security_boundary(binary, workspace)

        install_root = workspace / "codex-install"
        target = install_root / "plugins/context-pack"
        marketplace = install_root / ".agents/plugins/marketplace.json"
        run(
            [
                str(binary),
                "install-codex",
                "--target",
                str(target),
                "--marketplace",
                str(marketplace),
                "--quiet",
            ]
        )
        assert (target / ".codex-plugin/plugin.json").exists()
        assert (target / "skills/context-pack/SKILL.md").exists()
        assert json.loads(marketplace.read_text(encoding="utf-8"))["plugins"][0]["name"] == "context-pack"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
