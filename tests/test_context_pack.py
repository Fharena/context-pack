from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins" / "context-pack" / "skills" / "context-pack" / "scripts" / "context_pack.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("context_pack_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ContextPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_engine()

    def test_init_checkpoint_and_doctor_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            self.assertTrue((repo / ".codex/context/manifest.json").exists())
            self.assertTrue((repo / ".codex/handoff/CURRENT.md").exists())
            self.assertTrue((repo / "AGENTS.md").exists())

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--quiet"]), 0)
            current = (repo / ".codex/handoff/CURRENT.md").read_text(encoding="utf-8")
            self.assertIn("Git repo: no", current)
            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--quiet"]), 0)

    def test_changed_file_selects_area_and_generates_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")
            (repo / "tests/test_runtime.py").write_text("def test_choose():\n    pass\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".codex/context/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".codex/context/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": ["tests/test_runtime.py"],
                "keywords": ["runtime"],
                "contracts": ["Runtime choice must be explainable."],
                "failure_modes": ["Fallback path silently changes behavior."],
                "stale_if_paths": ["src/runtime.py"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".codex/context/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n"
                "# Runtime\n\n## Contracts\n- Missing config must not crash startup.\n",
                encoding="utf-8",
            )

            self.assertEqual(self.engine.main(["pack", "--repo", str(repo), "--changed", "--quiet"]), 0)
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("- runtime", pack)
            self.assertIn("src/runtime.py", pack)
            self.assertIn("Runtime choice must be explainable.", pack)
            self.assertIn("Missing config must not crash startup.", pack)
            self.assertIn("tests/test_runtime.py", pack)

    def test_task_selects_area_by_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".codex/context/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["cli"] = {
                "doc": ".codex/context/AREAS/cli.md",
                "description": "Command-line interface behavior.",
                "paths": ["src/cli.py"],
                "start_files": ["src/cli.py"],
                "tests": [],
                "keywords": ["cli", "command"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".codex/context/AREAS/cli.md").write_text(
                "---\nid: cli\nlast_reviewed_head: unknown\nstatus: active\n---\n# CLI\n",
                encoding="utf-8",
            )

            self.assertEqual(self.engine.main(["pack", "--repo", str(repo), "--task", "cli command bug", "--quiet"]), 0)
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("- cli", pack)

    def test_review_pack_can_use_base_ref_for_committed_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".codex/context/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".codex/context/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
                "contracts": ["Runtime choice must be explainable."],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".codex/context/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/runtime.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "change runtime"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["review-pack", "--repo", str(repo), "--base", "HEAD~1", "--quiet"]), 0)
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: review", pack)
            self.assertIn("- runtime", pack)
            self.assertIn("src/runtime.py", pack)

    def test_git_hook_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            self.assertEqual(self.engine.main(["install-git-hooks", "--repo", str(repo), "--quiet"]), 0)
            self.assertEqual(self.engine.main(["install-git-hooks", "--repo", str(repo), "--quiet"]), 0)
            hook = repo / ".git/hooks/pre-commit"
            text = hook.read_text(encoding="utf-8")
            self.assertEqual(text.count("# context-pack:start"), 1)
            self.assertIn("doctor", text)
            self.assertEqual(self.engine.main(["uninstall-git-hooks", "--repo", str(repo), "--quiet"]), 0)
            text = hook.read_text(encoding="utf-8")
            self.assertNotIn("# context-pack:start", text)


if __name__ == "__main__":
    unittest.main()
