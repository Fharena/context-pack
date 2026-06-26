from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(args: list[str], *, cwd: pathlib.Path = ROOT) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def run_output(args: list[str], expected: str, *, cwd: pathlib.Path = ROOT) -> None:
    print("+", " ".join(args), flush=True)
    output = subprocess.check_output(args, cwd=cwd, text=True)
    if expected not in output:
        raise AssertionError(f"Expected {expected!r} in output:\n{output}")
    print(output, end="")


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
    run_output([str(binary)], "Start here:")
    run_output([str(binary), "--version"], info[0]["version"])
    run([str(binary), "--help"])

    repo = pathlib.Path(tempfile.mkdtemp(prefix="context-pack-setup-"))
    run_output([str(binary), "setup", "--repo", str(repo), "--dry-run"], "No files were written.")
    assert not (repo / ".context-pack").exists()
    run([str(binary), "setup", "--repo", str(repo), "--quiet"])
    assert (repo / ".context-pack" / "manifest.json").exists()
    assert (repo / ".context-pack" / "CURRENT.md").exists()

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
