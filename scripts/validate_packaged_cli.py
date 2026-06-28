from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}


def run(args: list[str], *, cwd: pathlib.Path = ROOT) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, env=SUBPROCESS_ENV, check=True)


def run_output(args: list[str], expected: str | list[str], *, cwd: pathlib.Path = ROOT) -> str:
    print("+", " ".join(args), flush=True)
    output = subprocess.check_output(args, cwd=cwd, env=SUBPROCESS_ENV, encoding="utf-8")
    expected_values = [expected] if isinstance(expected, str) else expected
    for value in expected_values:
        if value not in output:
            raise AssertionError(f"Expected {value!r} in output:\n{output}")
    print(output, end="")
    return output


def configure_git_repo(repo: pathlib.Path) -> None:
    run(["git", "init"], cwd=repo)
    run(["git", "config", "user.name", "Context Pack Test"], cwd=repo)
    run(["git", "config", "user.email", "context-pack@example.invalid"], cwd=repo)


def validate_natural_start(binary: pathlib.Path) -> None:
    repo = pathlib.Path(tempfile.mkdtemp(prefix="context-pack-natural-start-"))
    configure_git_repo(repo)
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "README.md").write_text("# Demo app\n", encoding="utf-8")
    (repo / "src" / "app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
    (repo / "tests" / "test_app.py").write_text(
        "from src.app import login_timeout\n\n"
        "def test_login_timeout():\n"
        "    assert login_timeout() == 30\n",
        encoding="utf-8",
    )

    run([str(binary), "setup", "--repo", str(repo), "--quiet"])
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "initial"], cwd=repo)

    run_output(
        [str(binary), "start", "--repo", str(repo), "--task", "버그 고쳐줘"],
        ["Generated work pack for task", "Selected areas: source, tests"],
    )
    pack = (repo / ".context-pack" / "packs" / "CONTEXT_PACK.md").read_text(encoding="utf-8")
    assert "Task: 버그 고쳐줘" in pack
    assert "- source (score 2): starter code area for unclassified task" in pack
    assert "- tests (score 2): starter code area for unclassified task" in pack

    (repo / "src" / "app.py").write_text("def login_timeout():\n    return 45\n", encoding="utf-8")
    run_output(
        [str(binary), "start", "--repo", str(repo), "--task", "브랜치 리뷰해줘"],
        ["Generated review pack for review", "Selected areas: source"],
    )
    pack = (repo / ".context-pack" / "packs" / "CONTEXT_PACK.md").read_text(encoding="utf-8")
    assert "Mode: review" in pack
    assert "Task: 브랜치 리뷰해줘" in pack
    assert "- `src/app.py`" in pack


def main() -> int:
    npm = shutil.which("npm") or "npm"
    pack_dir = pathlib.Path(tempfile.mkdtemp(prefix="context-pack-npm-pack-"))
    prefix = pathlib.Path(tempfile.mkdtemp(prefix="context-pack-npm-install-"))

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
    run_output(
        [str(binary)],
        [
            "Normal use:",
            'Ask your agent: "Fix the login timeout."',
            "Direct CLI:",
            "context-pack setup --dry-run",
        ],
    )
    run_output([str(binary), "--version"], info[0]["version"])
    run([str(binary), "--help"])

    repo = pathlib.Path(tempfile.mkdtemp(prefix="context-pack-setup-"))
    run_output([str(binary), "setup", "--repo", str(repo), "--dry-run"], "No files were written.")
    assert not (repo / ".context-pack").exists()
    run([str(binary), "setup", "--repo", str(repo), "--quiet"])
    assert (repo / ".context-pack" / "manifest.json").exists()
    assert (repo / ".context-pack" / "CURRENT.md").exists()
    validate_natural_start(binary)

    install_root = pathlib.Path(tempfile.mkdtemp(prefix="context-pack-codex-install-"))
    target = install_root / "plugins" / "context-pack"
    marketplace = install_root / ".agents" / "plugins" / "marketplace.json"
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
    assert (target / ".codex-plugin" / "plugin.json").exists()
    assert (target / "skills" / "context-pack" / "SKILL.md").exists()
    assert (target / "skills" / "context-pack" / "scripts" / "context_pack.py").exists()
    data = json.loads(marketplace.read_text(encoding="utf-8"))
    assert data["plugins"][0]["name"] == "context-pack"

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
