from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins" / "context-pack" / "skills" / "context-pack" / "scripts" / "context_pack.py"
BUNDLED_ENGINE = ROOT / "src" / "context_pack" / "bundled" / "context_pack.py"


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
            self.assertTrue((repo / ".codex/handoff/LOCAL.md").exists())
            current = (repo / ".codex/handoff/CURRENT.md").read_text(encoding="utf-8")
            self.assertIn("Git repo: no", current)
            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--quiet"]), 0)

    def test_checkpoint_defaults_to_ignored_local_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--pack", "--quiet"]), 0)
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "-uall"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertEqual(status.strip(), "")
            self.assertTrue((repo / ".codex/handoff/LOCAL.md").exists())
            self.assertTrue((repo / ".codex/packs/CONTEXT_PACK.md").exists())

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--publish", "--quiet"]), 0)
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "-uall"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertIn(".codex/handoff/CURRENT.md", status)
            self.assertIn(".codex/handoff/LOG.md", status)

    def test_start_initializes_missing_context_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--quiet"]), 0)

            self.assertTrue((repo / ".codex/context/manifest.json").exists())
            self.assertTrue((repo / ".codex/handoff/CURRENT.md").exists())
            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertFalse((repo / ".codex/packs/CONTEXT_PACK.md").exists())

    def test_start_with_task_generates_work_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".codex/context/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["cli"] = {
                "doc": ".codex/context/AREAS/cli.md",
                "description": "Command-line entrypoints.",
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

            self.assertEqual(
                self.engine.main(["start", "--repo", str(repo), "--task", "cli command bug", "--quiet"]),
                0,
            )
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: work", pack)
            self.assertIn("- cli", pack)

    def test_start_in_existing_dirty_repo_generates_changed_pack(self) -> None:
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
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".codex/context/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--quiet"]), 0)
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: work", pack)
            self.assertIn("- runtime", pack)
            self.assertIn("src/runtime.py", pack)

    def test_start_review_with_base_generates_review_pack(self) -> None:
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

            self.assertEqual(
                self.engine.main(["start", "--repo", str(repo), "--review", "--base", "HEAD~1", "--quiet"]),
                0,
            )
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: review", pack)
            self.assertIn("- runtime", pack)
            self.assertIn("src/runtime.py", pack)

    def test_init_inferrs_common_project_areas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "docs").mkdir()
            (repo / "src/app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_run():\n    pass\n", encoding="utf-8")
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest = json.loads((repo / ".codex/context/manifest.json").read_text(encoding="utf-8"))
            self.assertIn("source", manifest["areas"])
            self.assertIn("tests", manifest["areas"])
            self.assertIn("docs", manifest["areas"])
            self.assertTrue((repo / ".codex/context/AREAS/source.md").exists())
            self.assertTrue((repo / ".codex/context/AREAS/tests.md").exists())
            self.assertTrue((repo / ".codex/context/AREAS/docs.md").exists())

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

    def test_pack_limits_primary_areas_and_moves_extra_context_to_read_later(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            (repo / "src").mkdir()
            (repo / "docs").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")
            (repo / "docs/runtime.md").write_text("# Runtime docs\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".codex/context/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".codex/context/AREAS/runtime.md",
                "description": "Runtime internals.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py", "docs/runtime.md"],
                "tests": [],
                "keywords": ["runtime"],
                "contracts": [
                    "Runtime choice must be explainable.",
                    "Runtime choice must be explainable.",
                    "Runtime choices must be explainable.",
                ],
                "failure_modes": ["Fallback path silently changes behavior."],
            }
            manifest["areas"]["docs-runtime"] = {
                "doc": ".codex/context/AREAS/docs-runtime.md",
                "description": "Runtime docs.",
                "paths": ["docs/runtime.md"],
                "start_files": ["docs/runtime.md"],
                "tests": [],
                "keywords": ["runtime", "docs"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".codex/context/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n"
                "# Runtime\n\n## Contracts\n- Runtime choice must be explainable.\n",
                encoding="utf-8",
            )
            (repo / ".codex/context/AREAS/docs-runtime.md").write_text(
                "---\nid: docs-runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Docs Runtime\n",
                encoding="utf-8",
            )

            self.assertEqual(
                self.engine.main(
                    [
                        "pack",
                        "--repo",
                        str(repo),
                        "--task",
                        "runtime internals bug",
                        "--changed",
                        "--max-areas",
                        "1",
                        "--max-read-first",
                        "2",
                        "--quiet",
                    ]
                ),
                0,
            )
            pack = (repo / ".codex/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("## Related Areas", pack)
            self.assertIn("## Read Later", pack)
            self.assertEqual(pack.count("Runtime choice must be explainable."), 1)

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

    def test_first_modified_status_file_keeps_first_character(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            (repo / "README.md").write_text("# Demo\n\nChanged.\n", encoding="utf-8")

            snapshot = self.engine.collect_snapshot(repo)
            self.assertIn("README.md", snapshot.dirty_files)
            self.assertNotIn("EADME.md", snapshot.dirty_files)

    def test_status_and_mark_reviewed_manage_area_health(self) -> None:
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
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".codex/context/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: oldhead\nstatus: review_needed\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")

            status_proc = subprocess.run(
                [sys.executable, str(ENGINE), "status", "--repo", str(repo)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(status_proc.returncode, 0, status_proc.stderr)
            self.assertIn("runtime", status_proc.stdout)
            self.assertIn("Stale warnings:", status_proc.stdout)

            self.assertEqual(self.engine.main(["mark-reviewed", "--repo", str(repo), "runtime", "--quiet"]), 0)
            area_doc = (repo / ".codex/context/AREAS/runtime.md").read_text(encoding="utf-8")
            self.assertIn("status: active", area_doc)
            self.assertIn("last_reviewed_head:", area_doc)

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

    def test_install_codex_copies_plugin_and_updates_marketplace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "plugins" / "context-pack"
            marketplace = root / ".agents" / "plugins" / "marketplace.json"

            self.assertEqual(
                self.engine.main(
                    [
                        "install-codex",
                        "--target",
                        str(target),
                        "--marketplace",
                        str(marketplace),
                        "--quiet",
                    ]
                ),
                0,
            )
            self.assertTrue((target / ".codex-plugin/plugin.json").exists())
            self.assertTrue((target / "skills/context-pack/SKILL.md").exists())
            self.assertTrue((target / "skills/context-pack/scripts/context_pack.py").exists())
            data = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "personal")
            self.assertEqual(data["plugins"][0]["name"], "context-pack")
            self.assertEqual(data["plugins"][0]["source"]["path"], "./plugins/context-pack")

            with self.assertRaises(SystemExit):
                self.engine.main(
                    [
                        "install-codex",
                        "--target",
                        str(target),
                        "--marketplace",
                        str(marketplace),
                        "--quiet",
                    ]
                )
            self.assertEqual(
                self.engine.main(
                    [
                        "install-codex",
                        "--target",
                        str(target),
                        "--marketplace",
                        str(marketplace),
                        "--force",
                        "--quiet",
                    ]
                ),
                0,
            )

    def test_install_codex_can_synthesize_plugin_without_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            isolated_engine = root / "isolated_context_pack.py"
            isolated_engine.write_text(ENGINE.read_text(encoding="utf-8"), encoding="utf-8")
            target = root / "plugins" / "context-pack"
            marketplace = root / ".agents" / "plugins" / "marketplace.json"
            old_file = self.engine.__file__
            self.engine.__file__ = str(isolated_engine)
            try:
                self.assertEqual(
                    self.engine.main(
                        [
                            "install-codex",
                            "--target",
                            str(target),
                            "--marketplace",
                            str(marketplace),
                            "--quiet",
                        ]
                    ),
                    0,
                )
            finally:
                self.engine.__file__ = old_file

            plugin = json.loads((target / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(plugin["name"], "context-pack")
            self.assertEqual(plugin["version"], self.engine.CONTEXT_PACK_VERSION)
            skill = (target / "skills/context-pack/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("context-pack start", skill)
            script = (target / "skills/context-pack/scripts/context_pack.py").read_text(encoding="utf-8")
            self.assertIn("CONTEXT_PACK_VERSION", script)

    def test_install_codex_refuses_to_overwrite_source_plugin(self) -> None:
        source_plugin = ROOT / "plugins" / "context-pack"
        with self.assertRaises(SystemExit):
            self.engine.main(["install-codex", "--target", str(source_plugin), "--force", "--quiet"])
        self.assertTrue((source_plugin / ".codex-plugin/plugin.json").exists())

    def test_packaged_cli_engine_stays_in_sync(self) -> None:
        self.assertEqual(ENGINE.read_text(encoding="utf-8"), BUNDLED_ENGINE.read_text(encoding="utf-8"))

    def test_python_module_cli_runs(self) -> None:
        env = os.environ.copy()
        src = str(ROOT / "src")
        env["PYTHONPATH"] = src + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src
        proc = subprocess.run(
            [sys.executable, "-m", "context_pack", "--help"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("context-pack", proc.stdout)

    def test_public_versions_stay_in_sync(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        package_init: dict[str, str] = {}
        exec((ROOT / "src/context_pack/__init__.py").read_text(encoding="utf-8"), package_init)
        plugin = json.loads((ROOT / "plugins/context-pack/.codex-plugin/plugin.json").read_text(encoding="utf-8"))

        version = pyproject["project"]["version"]
        self.assertEqual(package_init["__version__"], version)
        self.assertEqual(plugin["version"], version)
        self.assertEqual(self.engine.CONTEXT_PACK_VERSION, version)


if __name__ == "__main__":
    unittest.main()
