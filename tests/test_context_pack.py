from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins" / "context-pack" / "skills" / "context-pack" / "scripts" / "context_pack.py"
BUNDLED_ENGINE = ROOT / "src" / "context_pack" / "bundled" / "context_pack.py"
NODE_WRAPPER = ROOT / "bin" / "context-pack.js"
DEMO_GIF_SCRIPT = ROOT / "scripts" / "generate_demo_gif.py"


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
            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertTrue((repo / ".context-pack/CURRENT.md").exists())
            self.assertTrue((repo / "AGENTS.md").exists())

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--quiet"]), 0)
            self.assertTrue((repo / ".context-pack/local/LOCAL.md").exists())
            current = (repo / ".context-pack/CURRENT.md").read_text(encoding="utf-8")
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
            self.assertTrue((repo / ".context-pack/local/LOCAL.md").exists())
            self.assertTrue((repo / ".context-pack/packs/CONTEXT_PACK.md").exists())

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--publish", "--quiet"]), 0)
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "-uall"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertIn(".context-pack/CURRENT.md", status)
            self.assertIn(".context-pack/LOG.md", status)

    def test_checkpoint_pack_uses_previous_checkpoint_for_clean_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--pack", "--quiet"]), 0)
            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/runtime.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "change runtime"], cwd=repo, check=True, capture_output=True)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--pack"]), 0)

            self.assertIn("Context pack base:", output.getvalue())
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Changed files in scope: 1", pack)
            self.assertIn("src/runtime.py", pack)
            self.assertIn("- runtime", pack)
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "-uall"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertEqual(status.strip(), "")

    def test_checkpoint_pack_ignores_context_only_commits_for_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--pack", "--quiet"]), 0)

            area_doc = repo / ".context-pack/AREAS/overview.md"
            area_doc.write_text(area_doc.read_text(encoding="utf-8") + "\nReviewed locally.\n", encoding="utf-8")
            subprocess.run(["git", "add", ".context-pack/AREAS/overview.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "context maintenance"], cwd=repo, check=True, capture_output=True)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--pack"]), 0)

            self.assertNotIn("Context pack base:", output.getvalue())
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Changed files in scope: 0", pack)
            self.assertNotIn(".context-pack/AREAS/overview.md", pack.split("## Changed Files", 1)[-1])

    def test_start_initializes_missing_context_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--quiet"]), 0)

            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertTrue((repo / ".context-pack/CURRENT.md").exists())
            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertFalse((repo / ".context-pack/packs/CONTEXT_PACK.md").exists())

    def test_legacy_codex_layout_still_routes_until_migrated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            (repo / ".codex/context/AREAS").mkdir(parents=True)
            (repo / ".codex/handoff").mkdir(parents=True)
            (repo / ".codex/context/manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_by": "context-pack",
                        "areas": {
                            "cli": {
                                "doc": ".codex/context/AREAS/cli.md",
                                "description": "Command-line entrypoints.",
                                "paths": ["src/cli.py"],
                                "start_files": ["src/cli.py"],
                                "tests": [],
                                "keywords": ["cli", "command"],
                            }
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / ".codex/context/AREAS/cli.md").write_text(
                "---\nid: cli\nlast_reviewed_head: unknown\nstatus: active\n---\n# CLI\n",
                encoding="utf-8",
            )
            (repo / ".codex/context/INDEX.md").write_text("# Context Index\n", encoding="utf-8")
            (repo / ".codex/context/REVIEW.md").write_text("# Review Router\n", encoding="utf-8")
            (repo / ".codex/context/CONTRACTS.md").write_text("# Contracts\n", encoding="utf-8")
            (repo / ".codex/handoff/CURRENT.md").write_text("# Current Handoff\n", encoding="utf-8")

            self.assertEqual(
                self.engine.main(["start", "--repo", str(repo), "--task", "cli command bug", "--quiet"]),
                0,
            )

            self.assertTrue((repo / ".codex/packs/CONTEXT_PACK.md").exists())
            self.assertFalse((repo / ".context-pack/packs/CONTEXT_PACK.md").exists())

    def test_migrate_legacy_codex_layout_to_context_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".codex/context/AREAS").mkdir(parents=True)
            (repo / ".codex/handoff").mkdir(parents=True)
            (repo / ".codex/context/manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_by": "context-pack",
                        "areas": {
                            "runtime": {
                                "doc": ".codex/context/AREAS/runtime.md",
                                "description": "Runtime selection.",
                                "paths": ["src/runtime.py"],
                                "start_files": [".codex/context/INDEX.md", "src/runtime.py"],
                                "tests": [],
                                "keywords": ["runtime"],
                            }
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / ".codex/context/AREAS/runtime.md").write_text(
                "# Runtime\n\nSee `.codex/context/INDEX.md` first.\n",
                encoding="utf-8",
            )
            (repo / ".codex/context/INDEX.md").write_text("# Context Index\n", encoding="utf-8")
            (repo / ".codex/handoff/CURRENT.md").write_text("# Current\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["migrate", "--repo", str(repo), "--quiet"]), 0)

            manifest = json.loads((repo / ".context-pack/manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["areas"]["runtime"]["doc"], ".context-pack/AREAS/runtime.md")
            self.assertIn(".context-pack/INDEX.md", manifest["areas"]["runtime"]["start_files"])
            area_doc = (repo / ".context-pack/AREAS/runtime.md").read_text(encoding="utf-8")
            self.assertIn(".context-pack/INDEX.md", area_doc)
            self.assertNotIn(".codex/context", area_doc)

    def test_setup_initializes_context_and_common_agent_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertTrue((repo / ".context-pack/CURRENT.md").exists())
            self.assertIn("quiet orientation", (repo / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("Skip Context Pack", (repo / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertIn(
                "alwaysApply: true",
                (repo / ".cursor/rules/context-pack.mdc").read_text(encoding="utf-8"),
            )
            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--quiet"]), 0)

    def test_setup_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo with space"
            repo.mkdir()
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--dry-run"]), 0)

            text = output.getvalue()
            self.assertIn("Context Pack setup dry run", text)
            self.assertIn("Setup plan:", text)
            self.assertIn("Context files:", text)
            self.assertIn("create .context-pack/manifest.json", text)
            self.assertIn("create AGENTS.md", text)
            self.assertIn("No files were written.", text)
            self.assertIn("without `--dry-run`", text)
            self.assertIn("context-pack setup", text)
            self.assertIn('--repo "', text)
            self.assertIn('repo with space"', text)
            self.assertFalse((repo / ".context-pack").exists())
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / "CLAUDE.md").exists())
            self.assertFalse((repo / ".cursor").exists())

    def test_setup_dry_run_reports_preserved_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--dry-run"]), 0)

            text = output.getvalue()
            self.assertIn("leave unchanged .context-pack/manifest.json", text)
            self.assertIn("leave unchanged .context-pack/CURRENT.md", text)
            self.assertIn("leave unchanged .gitignore", text)
            self.assertIn("refresh managed block AGENTS.md", text)
            self.assertNotIn("update .context-pack/CURRENT.md", text)

    def test_setup_rerun_preserves_curated_manifest_unless_inference_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_run():\n    pass\n", encoding="utf-8")
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--dry-run"]), 0)

            text = output.getvalue()
            self.assertIn("leave unchanged .context-pack/manifest.json", text)
            self.assertNotIn("source.md", text)
            self.assertNotIn("tests.md", text)
            self.assertNotIn("docs.md", text)

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            manifest = json.loads((repo / ".context-pack/manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(manifest["areas"]), ["overview"])
            self.assertFalse((repo / ".context-pack/AREAS/source.md").exists())

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(["setup", "--repo", str(repo), "--dry-run", "--infer-areas"]),
                    0,
                )

            text = output.getvalue()
            self.assertIn("update .context-pack/manifest.json", text)
            self.assertIn("create .context-pack/AREAS/source.md", text)
            self.assertIn("create .context-pack/AREAS/tests.md", text)
            self.assertIn("create .context-pack/AREAS/docs.md", text)
            self.assertIn("--infer-areas", text)

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--infer-areas", "--quiet"]), 0)
            manifest = json.loads((repo / ".context-pack/manifest.json").read_text(encoding="utf-8"))
            self.assertIn("source", manifest["areas"])
            self.assertIn("tests", manifest["areas"])
            self.assertIn("docs", manifest["areas"])
            self.assertTrue((repo / ".context-pack/AREAS/source.md").exists())

    def test_setup_dry_run_respects_agent_docs_and_git_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(
                        [
                            "setup",
                            "--repo",
                            str(repo),
                            "--dry-run",
                            "--agent-docs",
                            "none",
                            "--git-hooks",
                            "safe",
                        ]
                    ),
                    0,
                )

            text = output.getvalue()
            self.assertIn("Agent docs: skipped", text)
            self.assertIn("Git hooks: safe", text)
            self.assertIn(".git/hooks/pre-commit", text)
            self.assertIn(".git/hooks/post-checkout", text)
            self.assertIn(".git/hooks/post-merge", text)
            self.assertIn("--agent-docs none", text)
            self.assertIn("--git-hooks safe", text)
            self.assertNotIn("--dry-run --agent-docs", text)
            self.assertFalse((repo / ".context-pack").exists())
            self.assertFalse((repo / ".git/hooks/pre-commit").exists())

    def test_setup_dry_run_reports_git_hook_errors_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(["setup", "--repo", str(repo), "--dry-run", "--git-hooks", "safe"]),
                    1,
                )

            self.assertIn("would fail: git hooks require a git repository", output.getvalue())
            self.assertFalse((repo / ".context-pack").exists())

    def test_setup_can_skip_agent_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(
                self.engine.main(["setup", "--repo", str(repo), "--agent-docs", "none", "--quiet"]),
                0,
            )

            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / "CLAUDE.md").exists())
            self.assertFalse((repo / ".cursor/rules/context-pack.mdc").exists())

    def test_setup_can_install_safe_git_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(
                self.engine.main(["setup", "--repo", str(repo), "--git-hooks", "safe", "--quiet"]),
                0,
            )

            hooks = repo / ".git/hooks"
            self.assertIn("context-pack:start", (hooks / "pre-commit").read_text(encoding="utf-8"))
            self.assertIn("context-pack:start", (hooks / "post-checkout").read_text(encoding="utf-8"))
            self.assertIn("context-pack:start", (hooks / "post-merge").read_text(encoding="utf-8"))
            self.assertFalse((hooks / "post-commit").exists())

    def test_doctor_fix_repairs_missing_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--quiet"]), 1)
            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--fix", "--quiet"]), 0)

            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertTrue((repo / ".context-pack/CURRENT.md").exists())
            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertTrue((repo / "CLAUDE.md").exists())
            self.assertTrue((repo / ".cursor/rules/context-pack.mdc").exists())

    def test_doctor_fix_can_skip_agent_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(
                self.engine.main(["doctor", "--repo", str(repo), "--fix", "--agent-docs", "none", "--quiet"]),
                0,
            )

            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / "CLAUDE.md").exists())
            self.assertFalse((repo / ".cursor/rules/context-pack.mdc").exists())

    def test_doctor_fix_does_not_install_git_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--fix", "--quiet"]), 0)

            self.assertFalse((repo / ".git/hooks/pre-commit").exists())
            self.assertFalse((repo / ".git/hooks/post-checkout").exists())
            self.assertFalse((repo / ".git/hooks/post-merge").exists())

    def test_install_agent_docs_writes_common_agent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(self.engine.main(["install-agent-docs", "--repo", str(repo), "--quiet"]), 0)
            self.assertEqual(self.engine.main(["install-agent-docs", "--repo", str(repo), "--quiet"]), 0)

            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
            cursor = (repo / ".cursor/rules/context-pack.mdc").read_text(encoding="utf-8")
            self.assertFalse(agents.startswith("\n"))
            self.assertFalse(claude.startswith("\n"))
            self.assertFalse(cursor.startswith("\n"))
            self.assertIn("quiet orientation", agents)
            self.assertIn("The user does not need to name it", agents)
            self.assertIn("Missing `.context-pack/` during a normal task", agents)
            self.assertIn("it auto-initializes lightweight context docs", agents)
            self.assertIn("Skip Context Pack", claude)
            self.assertIn("alwaysApply: true", cursor)
            self.assertIn("context-pack checkpoint --pack", cursor)
            self.assertIn("natural bug fixes, reviews, debugging, or handoff", cursor)
            self.assertEqual(cursor.count("context-pack:rules:start"), 1)

    def test_install_agent_docs_is_idempotent_and_preserves_existing_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "CLAUDE.md").write_text("\n# Existing guidance\n\nKeep this paragraph.\n", encoding="utf-8")

            args = ["install-agent-docs", "--repo", str(repo), "--target", "claude", "--quiet"]
            self.assertEqual(self.engine.main(args), 0)
            self.assertEqual(self.engine.main(args), 0)

            text = (repo / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("\n# Existing guidance"))
            self.assertIn("# Existing guidance", text)
            self.assertIn("Keep this paragraph.", text)
            self.assertIn("context-pack start", text)
            self.assertEqual(text.count("context-pack:rules:start"), 1)
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / ".cursor/rules/context-pack.mdc").exists())

    def test_install_agent_docs_can_target_cursor_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(
                self.engine.main(["install-agent-docs", "--repo", str(repo), "--target", "cursor", "--quiet"]),
                0,
            )

            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / "CLAUDE.md").exists())
            cursor = (repo / ".cursor/rules/context-pack.mdc").read_text(encoding="utf-8")
            self.assertTrue(cursor.startswith("---\n"))
            self.assertIn("description: Use Context Pack", cursor)
            self.assertIn("alwaysApply: true", cursor)

    def test_start_with_task_generates_work_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["cli"] = {
                "doc": ".context-pack/AREAS/cli.md",
                "description": "Command-line entrypoints.",
                "paths": ["src/cli.py"],
                "start_files": ["src/cli.py"],
                "tests": [],
                "keywords": ["cli", "command"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/cli.md").write_text(
                "---\nid: cli\nlast_reviewed_head: unknown\nstatus: active\n---\n# CLI\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "cli command bug"]), 0)

            text = output.getvalue()
            self.assertIn("Scope reduction: start from", text)
            self.assertIn("Approx text budget: Read First", text)
            self.assertIn("; repo", text)

            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: work", pack)
            self.assertIn("## Scope Reduction", pack)
            self.assertIn("- Repo files considered:", pack)
            self.assertIn("- Primary areas selected:", pack)
            self.assertIn("- Read First entries:", pack)
            self.assertIn("- Approx Read First text:", pack)
            self.assertIn("- Approx repo text:", pack)
            self.assertIn("- Token estimates use chars/4", pack)
            self.assertIn("- cli", pack)

    def test_measure_reports_scope_without_writing_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["cli"] = {
                "doc": ".context-pack/AREAS/cli.md",
                "description": "Command-line entrypoints.",
                "paths": ["src/cli.py"],
                "start_files": ["src/cli.py"],
                "tests": [],
                "keywords": ["cli", "command"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/cli.md").write_text(
                "---\nid: cli\nlast_reviewed_head: unknown\nstatus: active\n---\n# CLI\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["measure", "--repo", str(repo), "--task", "cli command bug"]), 0)

            text = output.getvalue()
            self.assertIn("Context Pack Measure", text)
            self.assertIn("No files written.", text)
            self.assertIn("Selected areas: cli", text)
            self.assertIn("Why selected:", text)
            self.assertIn("- cli: task matched keywords: cli, command", text)
            self.assertIn("Scope reduction: start from", text)
            self.assertIn("Approx text budget: Read First", text)
            self.assertIn('context-pack start --task "cli command bug"', text)
            self.assertFalse((repo / ".context-pack/packs/CONTEXT_PACK.md").exists())

    def test_measure_infers_areas_before_setup_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_app():\n    assert True\n", encoding="utf-8")
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["measure", "--repo", str(repo), "--task", "fix tests"]), 0)

            text = output.getvalue()
            self.assertIn("Context library: not installed; using inferred areas for measurement", text)
            self.assertIn("Selected areas: tests", text)
            self.assertIn("Read First entries:", text)
            self.assertNotIn("~167% of repo files", text)
            self.assertFalse((repo / ".context-pack").exists())

    def test_measure_before_setup_routes_unclassified_code_task_to_source_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_login_timeout():\n    assert True\n", encoding="utf-8")
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["measure", "--repo", str(repo), "--task", "fix login timeout"]), 0)

            text = output.getvalue()
            self.assertIn("Context library: not installed; using inferred areas for measurement", text)
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("Why selected:", text)
            self.assertIn("- source: starter code area for unclassified task", text)
            self.assertIn("- tests: starter code area for unclassified task", text)
            self.assertFalse((repo / ".context-pack").exists())

    def test_start_first_run_routes_unclassified_code_task_to_source_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_login_timeout():\n    assert True\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "fix login timeout"]), 0)

            text = output.getvalue()
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("Why selected:", text)
            self.assertIn("- source: starter code area for unclassified task", text)
            self.assertIn("- tests: starter code area for unclassified task", text)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("- source (score 2): starter code area for unclassified task", pack)
            self.assertIn("- tests (score 2): starter code area for unclassified task", pack)

    def test_start_existing_repo_routes_unclassified_code_task_to_source_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_login_timeout():\n    assert True\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "fix login timeout"]), 0)

            text = output.getvalue()
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("- source: starter code area for unclassified task", text)
            self.assertIn("- tests: starter code area for unclassified task", text)

    def test_start_in_existing_dirty_repo_generates_changed_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--quiet"]), 0)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
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
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
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
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: review", pack)
            self.assertIn("- runtime", pack)
            self.assertIn("src/runtime.py", pack)

    def test_start_review_without_base_infers_main_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "checkout", "-b", "feature/runtime"], cwd=repo, check=True, capture_output=True)

            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/runtime.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "change runtime"], cwd=repo, check=True, capture_output=True)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--review"]), 0)

            text = output.getvalue()
            self.assertIn("Review base: main (auto)", text)
            self.assertIn("Selected areas: runtime", text)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
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
            manifest = json.loads((repo / ".context-pack/manifest.json").read_text(encoding="utf-8"))
            self.assertIn("source", manifest["areas"])
            self.assertIn("tests", manifest["areas"])
            self.assertIn("docs", manifest["areas"])
            self.assertTrue((repo / ".context-pack/AREAS/source.md").exists())
            self.assertTrue((repo / ".context-pack/AREAS/tests.md").exists())
            self.assertTrue((repo / ".context-pack/AREAS/docs.md").exists())

    def test_changed_file_selects_area_and_generates_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")
            (repo / "tests/test_runtime.py").write_text("def test_choose():\n    pass\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
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
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n"
                "# Runtime\n\n## Contracts\n- Missing config must not crash startup.\n",
                encoding="utf-8",
            )

            self.assertEqual(self.engine.main(["pack", "--repo", str(repo), "--changed", "--quiet"]), 0)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
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
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
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
                "doc": ".context-pack/AREAS/docs-runtime.md",
                "description": "Runtime docs.",
                "paths": ["docs/runtime.md"],
                "start_files": ["docs/runtime.md"],
                "tests": [],
                "keywords": ["runtime", "docs"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n"
                "# Runtime\n\n## Contracts\n- Runtime choice must be explainable.\n",
                encoding="utf-8",
            )
            (repo / ".context-pack/AREAS/docs-runtime.md").write_text(
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
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("## Related Areas", pack)
            self.assertIn("## Read Later", pack)
            self.assertEqual(pack.count("Runtime choice must be explainable."), 1)

    def test_task_selects_area_by_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["cli"] = {
                "doc": ".context-pack/AREAS/cli.md",
                "description": "Command-line interface behavior.",
                "paths": ["src/cli.py"],
                "start_files": ["src/cli.py"],
                "tests": [],
                "keywords": ["cli", "command"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/cli.md").write_text(
                "---\nid: cli\nlast_reviewed_head: unknown\nstatus: active\n---\n# CLI\n",
                encoding="utf-8",
            )

            self.assertEqual(self.engine.main(["pack", "--repo", str(repo), "--task", "cli command bug", "--quiet"]), 0)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("- cli", pack)

    def test_task_keyword_scoring_ignores_stop_words(self) -> None:
        manifest = {
            "areas": {
                "runtime": {
                    "description": "Runtime and worker behavior.",
                    "paths": [],
                    "keywords": ["runtime"],
                },
                "docs": {
                    "description": "Documentation and adoption guidance.",
                    "paths": [],
                    "keywords": ["docs", "adoption"],
                },
                "overview": {
                    "description": "Project orientation.",
                    "paths": [],
                    "keywords": ["overview"],
                },
                "engine": {
                    "description": "Engine internals.",
                    "paths": [],
                    "keywords": ["fix"],
                },
            }
        }

        stop_word_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="and the with for this work",
        )
        self.assertEqual([item.area_id for item in stop_word_matches], ["overview"])

        adoption_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="public adoption proof and evidence",
        )
        self.assertEqual(adoption_matches[0].area_id, "docs")
        self.assertIn("task matched keywords: adoption", adoption_matches[0].reasons)
        self.assertNotIn("and", adoption_matches[0].reasons[0])

        generic_fix_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="fix login timeout",
        )
        self.assertEqual([item.area_id for item in generic_fix_matches], ["overview"])

        tests_only_manifest = {
            "areas": {
                "tests": {
                    "description": "Test suites.",
                    "paths": [],
                    "keywords": ["tests"],
                },
                "overview": {
                    "description": "Project orientation.",
                    "paths": [],
                    "keywords": ["overview"],
                },
            }
        }
        tests_only_matches = self.engine.selected_area_matches(
            tests_only_manifest,
            changed_files=[],
            task="fix login timeout",
        )
        self.assertEqual([item.area_id for item in tests_only_matches], ["overview"])

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

    def test_status_warns_when_shared_handoff_fingerprint_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "add context"], cwd=repo, check=True, capture_output=True)

            status_proc = subprocess.run(
                [sys.executable, str(ENGINE), "status", "--repo", str(repo)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(status_proc.returncode, 0, status_proc.stderr)
            self.assertIn("Health warnings:", status_proc.stdout)
            self.assertIn(".context-pack/CURRENT.md fingerprint is stale", status_proc.stdout)
            self.assertIn("material files changed since handoff HEAD", status_proc.stdout)

            self.assertEqual(self.engine.main(["checkpoint", "--repo", str(repo), "--publish", "--quiet"]), 0)
            subprocess.run(["git", "add", ".context-pack/CURRENT.md", ".context-pack/LOG.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "publish handoff"], cwd=repo, check=True, capture_output=True)

            fresh_proc = subprocess.run(
                [sys.executable, str(ENGINE), "status", "--repo", str(repo)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(fresh_proc.returncode, 0, fresh_proc.stderr)
            self.assertIn("Health warnings:\n- none", fresh_proc.stdout)
            self.assertNotIn("fingerprint is stale", fresh_proc.stdout)

    def test_status_and_mark_reviewed_manage_area_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose():\n    return 'cpu'\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
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
            area_doc = (repo / ".context-pack/AREAS/runtime.md").read_text(encoding="utf-8")
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
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "tests": [],
                "keywords": ["runtime"],
                "contracts": ["Runtime choice must be explainable."],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "---\nid: runtime\nlast_reviewed_head: unknown\nstatus: active\n---\n# Runtime\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            (repo / "src/runtime.py").write_text("def choose():\n    return 'gpu'\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/runtime.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "change runtime"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["review-pack", "--repo", str(repo), "--base", "HEAD~1", "--quiet"]), 0)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
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
            self.assertIn("natural requests like fixing bugs", plugin["interface"]["longDescription"])
            self.assertIn("reviewing branches", plugin["interface"]["longDescription"])
            self.assertIn("focused task or review packs", plugin["interface"]["longDescription"])
            self.assertIn("focused repo context", plugin["interface"]["defaultPrompt"][0])
            skill = (target / "skills/context-pack/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("agent behavior", skill)
            self.assertIn("Do not ask the user to name Context Pack first", skill)
            self.assertIn("Use `start`; it auto-initializes lightweight context docs", skill)
            self.assertIn("context_pack.py measure", skill)
            self.assertIn("setup --dry-run", skill)
            openai = (target / "skills/context-pack/agents/openai.yaml").read_text(encoding="utf-8")
            self.assertIn("focused repo context", openai)
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

    def test_python_module_without_args_shows_quickstart(self) -> None:
        env = os.environ.copy()
        src = str(ROOT / "src")
        env["PYTHONPATH"] = src + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src
        proc = subprocess.run(
            [sys.executable, "-m", "context_pack"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Normal use:", proc.stdout)
        self.assertIn('Ask your agent: "Fix the login timeout."', proc.stdout)
        self.assertIn('Ask your agent: "Review this branch."', proc.stdout)
        self.assertNotIn('Ask your agent: "Review this branch against main."', proc.stdout)
        self.assertIn("Direct CLI:", proc.stdout)
        self.assertIn("context-pack setup --dry-run", proc.stdout)
        self.assertIn("context-pack setup", proc.stdout)
        self.assertIn("context-pack measure", proc.stdout)
        self.assertIn("context-pack start --review", proc.stdout)
        self.assertNotIn("context-pack start --review --base main", proc.stdout)
        self.assertIn("context-pack install-codex --activate", proc.stdout)

    def test_python_module_reports_version(self) -> None:
        env = os.environ.copy()
        src = str(ROOT / "src")
        env["PYTHONPATH"] = src + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src
        proc = subprocess.run(
            [sys.executable, "-m", "context_pack", "--version"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(self.engine.CONTEXT_PACK_VERSION, proc.stdout)

    def test_node_wrapper_runs_bundled_engine(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        proc = subprocess.run(
            [node, str(NODE_WRAPPER), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("context-pack", proc.stdout)
        self.assertIn("setup", proc.stdout)

    def test_node_wrapper_without_args_shows_quickstart(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        proc = subprocess.run(
            [node, str(NODE_WRAPPER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Normal use:", proc.stdout)
        self.assertIn('Ask your agent: "Fix the login timeout."', proc.stdout)
        self.assertIn('Ask your agent: "Review this branch."', proc.stdout)
        self.assertNotIn('Ask your agent: "Review this branch against main."', proc.stdout)
        self.assertIn("Direct CLI:", proc.stdout)
        self.assertIn("context-pack setup --dry-run", proc.stdout)
        self.assertIn("context-pack setup", proc.stdout)
        self.assertIn("context-pack measure", proc.stdout)
        self.assertIn("context-pack start --review", proc.stdout)
        self.assertNotIn("context-pack start --review --base main", proc.stdout)
        self.assertIn("context-pack install-codex --activate", proc.stdout)

    def test_node_wrapper_reports_version(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        proc = subprocess.run(
            [node, str(NODE_WRAPPER), "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(self.engine.CONTEXT_PACK_VERSION, proc.stdout)

    def test_node_wrapper_can_setup_repo(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            proc = subprocess.run(
                [node, str(NODE_WRAPPER), "setup", "--repo", str(repo), "--quiet"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertTrue((repo / ".context-pack/CURRENT.md").exists())
            self.assertIn("quiet orientation", (repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_node_wrapper_can_install_codex_plugin(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "plugins" / "context-pack"
            marketplace = root / ".agents" / "plugins" / "marketplace.json"
            proc = subprocess.run(
                [
                    node,
                    str(NODE_WRAPPER),
                    "install-codex",
                    "--target",
                    str(target),
                    "--marketplace",
                    str(marketplace),
                    "--quiet",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((target / ".codex-plugin/plugin.json").exists())
            self.assertTrue((target / "skills/context-pack/SKILL.md").exists())
            self.assertTrue((target / "skills/context-pack/scripts/context_pack.py").exists())
            data = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual(data["plugins"][0]["name"], "context-pack")

    def test_node_wrapper_skips_old_python_candidates(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            if os.name == "nt":
                (bin_dir / "py.cmd").write_text("@echo off\r\nexit /b 1\r\n", encoding="utf-8")
                (bin_dir / "python.cmd").write_text(
                    "@echo off\r\n"
                    'if "%1"=="-c" exit /b 0\r\n'
                    "echo context-pack\r\n"
                    "echo setup\r\n"
                    "exit /b 0\r\n",
                    encoding="utf-8",
                )
            else:
                old_python = bin_dir / "python3"
                old_python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
                old_python.chmod(0o755)
                good_python = bin_dir / "python"
                good_python.write_text(
                    "#!/bin/sh\n"
                    'if [ "$1" = "-c" ]; then exit 0; fi\n'
                    "echo context-pack\n"
                    "echo setup\n",
                    encoding="utf-8",
                )
                good_python.chmod(0o755)

            proc = subprocess.run(
                [node, str(NODE_WRAPPER), "--help"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("context-pack", proc.stdout)
            self.assertIn("setup", proc.stdout)

    def test_public_versions_stay_in_sync(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        package_init: dict[str, str] = {}
        exec((ROOT / "src/context_pack/__init__.py").read_text(encoding="utf-8"), package_init)
        plugin = json.loads((ROOT / "plugins/context-pack/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        npm_package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

        version = pyproject["project"]["version"]
        self.assertEqual(package_init["__version__"], version)
        self.assertEqual(plugin["version"], version)
        self.assertEqual(npm_package["version"], version)
        self.assertEqual(npm_package["bin"]["context-pack"], "bin/context-pack.js")
        self.assertEqual(self.engine.CONTEXT_PACK_VERSION, version)

    def test_demo_gif_script_matches_current_product_flow(self) -> None:
        text = DEMO_GIF_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("User: Fix the login timeout.", text)
        self.assertIn("quiet orientation", text)
        self.assertIn("context-pack setup --dry-run", text)
        self.assertIn("context-pack start --task", text)
        self.assertIn("context-pack start --review --base main", text)
        self.assertIn("fix login timeout", text)
        self.assertIn("Tiny obvious edits can skip Context Pack", text)
        self.assertIn(".context-pack/manifest.json", text)
        self.assertIn("Approx text budget shown with chars/4 caveat", text)
        self.assertIn("checkpoint --pack", text)
        self.assertIn("Next session starts from the same map.", text)
        self.assertNotIn("Stop paying agents", text)
        self.assertNotIn(".codex/", text)
        self.assertTrue((ROOT / "assets/demo.gif").exists())
        demo_url = "https://raw.githubusercontent.com/Fharena/context-pack/main/assets/demo.gif"
        for readme in (ROOT / "README.md", ROOT / "README.ko.md"):
            readme_text = readme.read_text(encoding="utf-8")
            self.assertIn(demo_url, readme_text)
            self.assertNotIn('src="assets/demo.gif"', readme_text)


if __name__ == "__main__":
    unittest.main()
