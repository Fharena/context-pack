from __future__ import annotations

import ast
import collections
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
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins" / "context-pack" / "skills" / "context-pack" / "scripts" / "context_pack.py"
BUNDLED_ENGINE = ROOT / "src" / "context_pack" / "bundled" / "context_pack.py"
BUNDLED_SKILL = ROOT / "src" / "context_pack" / "bundled" / "SKILL.md"
BUNDLED_OPENAI = ROOT / "src" / "context_pack" / "bundled" / "openai.yaml"
BUNDLED_PLUGIN = ROOT / "src" / "context_pack" / "bundled" / "plugin.json"
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

    def symlink_or_skip(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=target.is_dir())
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symbolic links unavailable: {exc}")

    def test_repository_relative_path_rejects_portable_escape_forms(self) -> None:
        unsafe = [
            "../secret.py",
            "src/../../secret.py",
            "/var/tmp/secret.py",
            r"X:\private\secret.py",
            r"X:private\secret.py",
            r"\\server\share\secret.py",
            "src/file.py:stream",
            "src/CON.txt",
            "NUL",
            "src/trailing.",
            "src/bad|name.py",
            "src/secret.py\0tail",
        ]
        for value in unsafe:
            with self.subTest(value=value):
                with self.assertRaises(self.engine.RepositoryBoundaryError):
                    self.engine.repository_relative_path(value, source="test path")

        self.assertEqual(
            self.engine.repository_relative_path(r"src\runtime\selector.py", source="test path"),
            "src/runtime/selector.py",
        )
        self.assertEqual(
            self.engine.repository_relative_path("./src//runtime.py", source="test path"),
            "src/runtime.py",
        )

    def test_repository_path_rejects_resolved_escape_and_symlink_redirect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            linked = repo / "linked.py"
            outside = repo.parent / "outside.py"
            path_type = type(repo)
            original_resolve = path_type.resolve

            def resolve_outside(path: Path, strict: bool = False) -> Path:
                if path == linked:
                    return outside
                return original_resolve(path, strict=strict)

            with mock.patch.object(path_type, "resolve", new=resolve_outside):
                with self.assertRaisesRegex(self.engine.RepositoryBoundaryError, "outside the repository"):
                    self.engine.repository_path(repo, "linked.py", source="test link")

            redirected = repo / "redirected.py"

            def resolve_inside(path: Path, strict: bool = False) -> Path:
                if path == linked:
                    return redirected
                return original_resolve(path, strict=strict)

            with mock.patch.object(path_type, "resolve", new=resolve_inside):
                with self.assertRaisesRegex(self.engine.RepositoryBoundaryError, "symbolic link"):
                    self.engine.repository_path(
                        repo,
                        "linked.py",
                        source="test link",
                        allow_symlinks=False,
                    )

    def test_scope_globs_do_not_cross_directory_boundaries(self) -> None:
        self.assertTrue(self.engine.scope_pattern_matches("client/js/app.js", "client/js/*.js"))
        self.assertFalse(self.engine.scope_pattern_matches("client/js/lib/app.js", "client/js/*.js"))
        self.assertFalse(self.engine.scope_pattern_matches("client/js/lib/app.js", "lib/*.js"))
        self.assertTrue(self.engine.scope_pattern_matches("lib/app.js", "lib/*.js"))
        self.assertFalse(self.engine.scope_pattern_matches("pkg/main.go", "*.go"))
        self.assertTrue(self.engine.scope_pattern_matches("client/js/lib/app.js", "client/js/**"))
        self.assertTrue(self.engine.scope_pattern_matches("pkg/deep/value_test.go", "**/*_test.go"))

    def test_manifest_escape_is_refused_before_read_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            outside = root / "outside.py"
            sentinel = "OUTSIDE_SECRET_SENTINEL"
            outside.write_text(f"{sentinel} = True\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["overview"]["start_files"] = ["../outside.py"]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                start_result = self.engine.main(
                    ["start", "--agent", "--task", "fix onboarding", "--repo", str(repo)]
                )
            self.assertEqual(start_result, 2)
            self.assertNotIn(sentinel, stdout.getvalue() + stderr.getvalue())

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                setup_result = self.engine.main(["setup", "--force", "--repo", str(repo)])
            self.assertEqual(setup_result, 2)
            self.assertEqual(outside.read_text(encoding="utf-8"), f"{sentinel} = True\n")

    def test_manifest_doc_is_confined_to_area_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("PROJECT_DOC_SENTINEL\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["overview"]["doc"] = "README.md"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = self.engine.main(
                    ["start", "--agent", "--task", "review overview", "--repo", str(repo)]
                )
            self.assertEqual(result, 2)
            self.assertIn("must remain under", stderr.getvalue())
            self.assertNotIn("PROJECT_DOC_SENTINEL", stderr.getvalue())

    def test_ignored_file_is_not_read_or_emitted_as_agent_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            with (repo / ".gitignore").open("a", encoding="utf-8") as handle:
                handle.write(".env\n")
            secret = "LOCAL_ENV_SECRET_SENTINEL=do-not-read\n"
            (repo / ".env").write_text(secret, encoding="utf-8")

            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["auth"] = {
                "kind": "source",
                "doc": ".context-pack/AREAS/auth.md",
                "description": "Authentication configuration.",
                "paths": [".env"],
                "start_files": [".env"],
                "search_terms": ["auth_config_token"],
                "keywords": ["auth"],
                "tests": [],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/auth.md").write_text("# Auth\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = self.engine.main(
                    ["start", "--agent", "--task", "fix auth", "--repo", str(repo)]
                )
            self.assertEqual(result, 0)
            self.assertNotIn("LOCAL_ENV_SECRET_SENTINEL", stdout.getvalue())
            self.assertNotIn("`.env`", stdout.getvalue())

    def test_manifest_symlink_escape_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "src").mkdir()
            outside = root / "outside.py"
            sentinel = "SYMLINK_SECRET_SENTINEL"
            outside.write_text(f"{sentinel} = True\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            self.symlink_or_skip(repo / "src/linked.py", outside)

            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["overview"]["start_files"] = ["src/linked.py"]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = self.engine.main(
                    ["start", "--agent", "--task", "fix linked source", "--repo", str(repo)]
                )
            self.assertEqual(result, 2)
            self.assertIn("refused an unsafe repository path", stderr.getvalue())
            self.assertIn("outside the repository", stderr.getvalue())
            self.assertNotIn(sentinel, stdout.getvalue() + stderr.getvalue())

    def test_checkpoint_does_not_follow_managed_file_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            outside = root / "outside-current.md"
            original = "OUTSIDE_CURRENT_SENTINEL\n"
            outside.write_text(original, encoding="utf-8")
            current = repo / ".context-pack/CURRENT.md"
            current.unlink()
            self.symlink_or_skip(current, outside)

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = self.engine.main(
                    ["checkpoint", "--publish", "--repo", str(repo), "--quiet"]
                )
            self.assertEqual(result, 2)
            self.assertIn("refused an unsafe repository path", stderr.getvalue())
            self.assertIn("outside the repository", stderr.getvalue())
            self.assertEqual(outside.read_text(encoding="utf-8"), original)

    def test_engine_has_no_unreferenced_top_level_symbols(self) -> None:
        tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
        definitions = {
            node.name: node.lineno
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        constants: dict[str, int] = {}
        for node in tree.body:
            target = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
            elif isinstance(node, ast.AnnAssign):
                target = node.target
            if isinstance(target, ast.Name) and target.id.isupper():
                constants[target.id] = node.lineno
        loads = collections.Counter(
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        )

        unused = [(name, line) for name, line in {**definitions, **constants}.items() if loads[name] == 0]
        self.assertEqual(unused, [])

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

    def test_start_missing_context_is_transient_and_does_not_write_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            before = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"], cwd=repo, text=True)

            self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--quiet"]), 0)

            self.assertFalse((repo / ".context-pack").exists())
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / ".gitignore").exists())
            after = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"], cwd=repo, text=True)
            self.assertEqual(before, after)

    def test_start_without_task_points_to_current_and_index_without_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo)]), 0)

            text = output.getvalue()
            self.assertIn("No pack generated", text)
            self.assertIn("Read next:", text)
            self.assertIn("- .context-pack/CURRENT.md", text)
            self.assertIn("- .context-pack/INDEX.md", text)
            self.assertFalse((repo / ".context-pack/packs/CONTEXT_PACK.md").exists())

    def test_agent_start_inlines_handoff_route_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text(
                "def choose_runtime():\n    return 'cpu'\n",
                encoding="utf-8",
            )
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "kind": "source",
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection and fallback behavior.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "search_terms": ["choose_runtime"],
                "keywords": ["runtime", "selector"],
                "tests": [],
                "verify": ["python -m py_compile src/runtime.py"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text("# Runtime\n", encoding="utf-8")
            (repo / ".context-pack/CURRENT.md").write_text(
                "# Current Handoff\n\n## Active Goal\n- Finish the runtime selector fallback.\n\n"
                "## Next Actions\n1. Inspect choose_runtime and verify the smallest fix.\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = self.engine.main(["start", "--agent", "--repo", str(repo)])

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("`runtime`", text)
            self.assertIn("Evidence confidence: `strong`", text)
            self.assertIn("choose_runtime", text)
            self.assertIn("python -m py_compile src/runtime.py", text)
            self.assertNotIn("Read `.context-pack/CURRENT.md`", text)

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

            self.assertEqual(
                self.engine.main(["setup", "--repo", str(repo), "--agent-docs", "all", "--quiet"]),
                0,
            )

            self.assertTrue((repo / ".context-pack/manifest.json").exists())
            self.assertTrue((repo / ".context-pack/CURRENT.md").exists())
            self.assertIn("Use Context Pack quietly", (repo / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("Skip pure Q&A", (repo / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertIn(
                "alwaysApply: true",
                (repo / ".cursor/rules/context-pack.mdc").read_text(encoding="utf-8"),
            )
            self.assertEqual(self.engine.main(["doctor", "--repo", str(repo), "--quiet"]), 0)

    def test_setup_auto_avoids_unused_agent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertFalse((repo / "CLAUDE.md").exists())
            self.assertFalse((repo / ".cursor").exists())

    def test_setup_auto_refreshes_detected_agent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "CLAUDE.md").write_text("# Existing Claude guidance\n", encoding="utf-8")
            (repo / ".cursor").mkdir()

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            self.assertIn("Existing Claude guidance", (repo / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertTrue((repo / ".cursor/rules/context-pack.mdc").exists())

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
            self.assertEqual(
                self.engine.main(
                    ["doctor", "--repo", str(repo), "--fix", "--agent-docs", "all", "--quiet"]
                ),
                0,
            )

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
            self.assertIn("Use Context Pack quietly", agents)
            self.assertIn("The user does not need to name the tool", agents)
            self.assertIn("context-pack start --agent --review", agents)
            self.assertIn("start` is transient", agents)
            self.assertIn("must not create `.context-pack/`", agents)
            self.assertIn("explicitly asks to persist", agents)
            self.assertIn("Skip pure Q&A", claude)
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
                "search_terms": ["main"],
                "tests": [],
                "keywords": ["cli", "command"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/cli.md").write_text(
                "---\nid: cli\nlast_reviewed_head: unknown\nstatus: active\n---\n# CLI\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with mock.patch.object(self.engine, "readable_text_chars", side_effect=AssertionError("unexpected text scan")):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "cli command bug"]), 0)

            text = output.getvalue()
            self.assertIn("Scope reduction: start from", text)
            self.assertNotIn("Approx text budget:", text)

            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("Mode: work", pack)
            self.assertIn("## Scope Reduction", pack)
            self.assertIn("- Repo files considered:", pack)
            self.assertIn("- Primary areas selected:", pack)
            self.assertIn("- Search scopes: 1", pack)
            self.assertIn("- Read First entries: 0 (~0% of repo files)", pack)
            self.assertNotIn("- Approx Read First text:", pack)
            self.assertNotIn("- Approx repo text:", pack)
            self.assertIn("- cli", pack)
            search_section = pack.split("## Search First", 1)[1].split("## Read First", 1)[0]
            read_section = pack.split("## Read First", 1)[1].split("## Changed Files", 1)[0]
            self.assertIn("`main`", search_section)
            self.assertIn("`src/cli.py`", search_section)
            self.assertNotIn("`src/cli.py`", read_section)
            self.assertIn("Do not bulk-read", search_section)

    def test_agent_start_returns_compact_bounded_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/game.js").write_text(
                """var Game = {
    startZoningFrom: function(x, y) {
        var z = this.zoningOrientation,
            xoffset = 10,
            yoffset = 10;
        if(z === UP || z === DOWN) {
            x = (z === UP) ? y - yoffset : y + yoffset;
        }
        camera.setPosition(x, y);
    }
};
""",
                encoding="utf-8",
            )
            (repo / "src/noise.js").write_text("noise\n" * 5000, encoding="utf-8")
            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)

            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["zoning"] = {
                "kind": "source",
                "doc": ".context-pack/AREAS/zoning.md",
                "description": "Phone edge camera transitions.",
                "keywords": ["phone", "edge", "camera", "transition"],
                "paths": ["src/**"],
                "start_files": ["src/game.js"],
                "search_terms": ["zoning", "startZoningFrom"],
                "contracts": ["Desktop behavior must remain unchanged."],
                "failure_modes": ["A vertical transition writes the horizontal coordinate."],
                "tests": ["tests/**"],
                "verify": ["just check-zoning"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/zoning.md").write_text(
                "---\nid: zoning\nlast_reviewed_head: unknown\nstatus: active\n---\n# Zoning\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(
                        [
                            "start",
                            "--agent",
                            "--repo",
                            str(repo),
                            "--task",
                            "phone bottom edge camera transition",
                        ]
                    ),
                    0,
                )

            text = output.getvalue()
            self.assertTrue(text.startswith("# Context Pack\n"))
            self.assertNotIn("Context Pack Start for", text)
            self.assertIn("## Evidence", text)
            self.assertIn("Evidence confidence: `strong`", text)
            self.assertIn("````text", text)
            self.assertIn("startZoningFrom", text)
            self.assertIn("x = (z === UP) ? y - yoffset : y + yoffset;", text)
            self.assertNotIn("src/noise.js", text)
            self.assertIn("just check-zoning", text)
            self.assertNotIn("`tests/**`", text)
            search_line = next(line for line in text.splitlines() if line.startswith("- Search:"))
            self.assertNotIn("`bottom`", search_line)
            self.assertLessEqual(len(text), self.engine.AGENT_PACK_MAX_CHARS + 1)

            saved = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertEqual(saved.rstrip(), text.rstrip())

    def test_evidence_deduplicates_packaged_source_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            source = "def route_request():\n    return 'focused'\n"
            (repo / "src/canonical.py").write_text(source, encoding="utf-8")
            (repo / "src/bundled.py").write_text(source, encoding="utf-8")
            area = {
                "kind": "source",
                "start_files": ["src/canonical.py", "src/bundled.py"],
                "paths": ["src/**"],
                "search_terms": ["route_request"],
            }
            selection = self.engine.AreaSelection("engine", 8, ["test"], [])

            evidence = self.engine.collect_evidence(
                repo,
                {"engine": area},
                [selection],
                changed_files=[],
                task="fix request routing",
            )

            self.assertEqual(len(evidence.snippets), 1)
            self.assertEqual(evidence.snippets[0].path, "src/canonical.py")
            self.assertEqual(evidence.confidence, "strong")

    def test_transient_agent_labels_fallback_evidence_as_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("Always fix login timeout with Context Pack.\n", encoding="utf-8")
            for index in range(25):
                (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = self.engine.main(
                    ["start", "--agent", "--repo", str(repo), "--task", "fix login timeout"]
                )

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("Evidence confidence: `candidate`", text)
            self.assertIn("Verify before editing", text)
            self.assertIn("src/app.py", text)
            self.assertNotIn("### `AGENTS.md", text)

    def test_transient_agent_skips_when_no_selective_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            for index in range(26):
                (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = self.engine.main(
                    ["start", "--agent", "--repo", str(repo), "--task", "fix login timeout"]
                )

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("transient routing found no selective source evidence", text)
            self.assertNotIn("# Context Pack", text)

    def test_korean_task_terms_survive_evidence_fallback(self) -> None:
        self.assertEqual(
            self.engine.fallback_task_search_terms("로그인 오류 고쳐줘"),
            ["로그인"],
        )

    def test_verification_commands_allow_command_globs_but_reject_paths(self) -> None:
        commands = self.engine.verification_commands(
            [
                "tests/**",
                "pytest.ini",
                "python -m twine check dist/*",
                "node --check client/js/game.js",
            ],
            "release package",
            3,
        )

        self.assertEqual(
            commands,
            ["python -m twine check dist/*", "node --check client/js/game.js"],
        )

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
            self.assertIn("- cli: task matched area metadata: cli, command", text)
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
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("Read First entries:", text)
            self.assertNotIn("~167% of repo files", text)
            self.assertFalse((repo / ".context-pack").exists())

    def test_measure_before_setup_pairs_source_with_failing_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_login_timeout():\n    assert True\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(["measure", "--repo", str(repo), "--task", "why are tests failing"]),
                    0,
                )

            text = output.getvalue()
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("paired source area for debugging", text)
            self.assertIn("- tests: task matched area metadata: tests", text)
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
            for index in range(25):
                (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "fix login timeout"]), 0)

            text = output.getvalue()
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("Why selected:", text)
            self.assertIn("- source: starter code area for unclassified task", text)
            self.assertIn("- tests: starter code area for unclassified task", text)
            snapshot = self.engine.collect_snapshot(repo)
            pack_path = self.engine.transient_pack_path(repo, snapshot)
            self.assertFalse(pack_path.exists())
            self.assertIn("Generated work pack for task: inline (not written)", text)
            self.assertIn("Context pack follows", text)
            pack = text.split("Context pack follows; do not reopen it unless this output was truncated:", 1)[1]
            self.assertIn("- source (score 2): starter code area for unclassified task", pack)
            self.assertIn("- tests (score 2): starter code area for unclassified task", pack)
            self.assertIn("## Search First", pack)
            self.assertFalse((repo / ".context-pack").exists())
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / ".gitignore").exists())

    def test_start_skips_small_unconfigured_repo_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "fix app bug"]), 0)

            self.assertIn("broad reading is likely cheaper", output.getvalue())
            self.assertFalse((repo / ".context-pack").exists())
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertFalse((repo / ".gitignore").exists())

    def test_review_filters_context_pack_setup_files_when_code_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            for index in range(25):
                (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")
            subprocess.run(["git", "add", "src"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            changed = repo / "src/module_0.py"
            changed.write_text("VALUE = 99\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--review", "--quiet"]), 0)

            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            changed_section = pack.split("## Changed Files", 1)[1].split("## Contracts", 1)[0]
            self.assertIn("src/module_0.py", changed_section)
            self.assertNotIn(".context-pack/", changed_section)
            self.assertNotIn("AGENTS.md", changed_section)
            self.assertNotIn(".gitignore", changed_section)
            self.assertIn("- source", pack)

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




    def test_start_existing_repo_pairs_source_with_failing_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "tests").mkdir()
            (repo / "src/app.py").write_text("def login_timeout():\n    return 30\n", encoding="utf-8")
            (repo / "tests/test_app.py").write_text("def test_login_timeout():\n    assert True\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(["start", "--repo", str(repo), "--task", "debug broken login test"]),
                    0,
                )

            text = output.getvalue()
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("paired source area for debugging", text)
            self.assertIn("- tests: task matched area metadata: test", text)
            pack = (repo / ".context-pack/packs/CONTEXT_PACK.md").read_text(encoding="utf-8")
            self.assertIn("paired source area for debugging", pack)
            self.assertIn("task matched area metadata: test", pack)





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

    def test_init_inferrs_top_level_python_package_as_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "httpx").mkdir()
            (repo / "tests").mkdir()
            (repo / ".github/workflows").mkdir(parents=True)
            (repo / "httpx/__init__.py").write_text("__version__ = '0.0.0'\n", encoding="utf-8")
            (repo / "tests/test_client.py").write_text("def test_client():\n    pass\n", encoding="utf-8")
            (repo / ".github/workflows/ci.yml").write_text("name: CI\n", encoding="utf-8")

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest = json.loads((repo / ".context-pack/manifest.json").read_text(encoding="utf-8"))
            source = manifest["areas"]["source"]
            self.assertIn("httpx/**", source["paths"])
            self.assertIn("httpx/__init__.py", source["start_files"])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(self.engine.main(["start", "--repo", str(repo), "--task", "build failed"]), 0)

            text = output.getvalue()
            self.assertIn("Selected areas: automation, source, tests", text)

    def test_measure_before_setup_infers_web_game_source_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "client/js").mkdir(parents=True)
            (repo / "server/js").mkdir(parents=True)
            (repo / "shared/js").mkdir(parents=True)
            (repo / "client/sprites").mkdir(parents=True)
            (repo / "client/maps").mkdir(parents=True)
            (repo / "client/js/input.js").write_text("export function handleTouch() {}\n", encoding="utf-8")
            (repo / "server/js/main.js").write_text("function connect() {}\n", encoding="utf-8")
            (repo / "shared/js/gametypes.js").write_text("exports.Messages = {};\n", encoding="utf-8")
            (repo / "client/sprites/player.json").write_text('{"id":"player"}\n', encoding="utf-8")
            (repo / "client/maps/world_client.json").write_text('{"height":1,"width":1}\n', encoding="utf-8")

            mobile_output = io.StringIO()
            with contextlib.redirect_stdout(mobile_output):
                self.assertEqual(
                    self.engine.main(
                        [
                            "measure",
                            "--repo",
                            str(repo),
                            "--task",
                            "fix mobile controls bug on touch devices",
                        ]
                    ),
                    0,
                )

            mobile_text = mobile_output.getvalue()
            self.assertIn("Selected areas: source", mobile_text)
            self.assertIn("- source: starter code area for unclassified task", mobile_text)
            self.assertNotIn("overview: fallback orientation", mobile_text)

            asset_output = io.StringIO()
            with contextlib.redirect_stdout(asset_output):
                self.assertEqual(
                    self.engine.main(
                        [
                            "measure",
                            "--repo",
                            str(repo),
                            "--task",
                            "fix missing sprite asset loading bug",
                        ]
                    ),
                    0,
                )

            asset_text = asset_output.getvalue()
            self.assertIn("Selected areas: assets, source", asset_text)
            self.assertIn("- assets: task matched area metadata:", asset_text)
            self.assertIn("- source: paired source area for debugging", asset_text)
            self.assertFalse((repo / ".context-pack").exists())

    def test_measure_before_setup_infers_go_source_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "binding").mkdir()
            (repo / "render").mkdir()
            (repo / "testdata").mkdir()
            (repo / "go.mod").write_text("module example.test/demo\n", encoding="utf-8")
            (repo / "gin.go").write_text("package gin\n\nfunc New() {}\n", encoding="utf-8")
            (repo / "context.go").write_text("package gin\n\nfunc recoverPanic() {}\n", encoding="utf-8")
            (repo / "gin_test.go").write_text("package gin\n\nfunc TestNew() {}\n", encoding="utf-8")
            (repo / "binding/json.go").write_text("package binding\n\nfunc BindJSON() {}\n", encoding="utf-8")
            (repo / "binding/json_test.go").write_text("package binding\n\nfunc TestBindJSON() {}\n", encoding="utf-8")
            (repo / "render/html.go").write_text("package render\n\nfunc HTML() {}\n", encoding="utf-8")
            (repo / "testdata/fixture.go").write_text("package testdata\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    self.engine.main(["measure", "--repo", str(repo), "--task", "fix middleware panic bug"]),
                    0,
                )

            text = output.getvalue()
            self.assertIn("Selected areas: source, tests", text)
            self.assertIn("- source: starter code area for unclassified task", text)
            self.assertNotIn("overview: fallback orientation", text)

            self.assertEqual(self.engine.main(["init", "--repo", str(repo), "--quiet"]), 0)
            manifest = json.loads((repo / ".context-pack/manifest.json").read_text(encoding="utf-8"))
            source = manifest["areas"]["source"]
            tests = manifest["areas"]["tests"]
            self.assertIn("*.go", source["paths"])
            self.assertIn("binding/**", source["paths"])
            self.assertIn("gin.go", source["start_files"])
            self.assertNotIn("testdata/**", source["paths"])
            self.assertIn("**/*_test.go", tests["paths"])
            self.assertIn("gin_test.go", tests["start_files"])
            self.assertEqual(source["verify"], ["go test ./..."])
            self.assertEqual(tests["verify"], ["go test ./..."])

    def test_text_budget_skips_known_binary_media_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "client/img").mkdir(parents=True)
            (repo / "README.md").write_bytes(b"# Demo\n")
            (repo / "client/img/sprite.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 1024)

            budget = self.engine.text_budget_for_files(repo, ["README.md", "client/img/sprite.png"])

            self.assertEqual(budget.files, 1)
            self.assertEqual(budget.skipped, 1)
            self.assertEqual(budget.chars, len("# Demo\n"))

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

    def test_routing_does_not_select_areas_from_contract_or_failure_prose(self) -> None:
        manifest = {
            "areas": {
                "engine": {
                    "kind": "source",
                    "description": "Core implementation.",
                    "keywords": ["routing"],
                    "paths": ["src/**"],
                },
                "distribution": {
                    "kind": "automation",
                    "description": "Packaging and release automation.",
                    "keywords": ["package"],
                    "paths": ["scripts/**"],
                    "contracts": ["The package must preserve routing logic."],
                    "failure_modes": ["Routing metadata drifts during release."],
                },
                "overview": {
                    "kind": "overview",
                    "description": "Project orientation.",
                    "keywords": ["overview"],
                    "paths": ["README.md"],
                },
            }
        }

        matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="reduce routing waste",
        )

        self.assertEqual([item.area_id for item in matches], ["engine"])

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
                "agent_docs": {
                    "description": "Agent context pack instructions.",
                    "paths": [],
                    "keywords": ["agent", "context", "pack"],
                },
                "review_notes": {
                    "description": "Review notes.",
                    "paths": [],
                    "keywords": ["review"],
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
        self.assertIn("task matched area metadata: adoption", adoption_matches[0].reasons)

        review_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="review this branch",
        )
        self.assertEqual([item.area_id for item in review_matches], ["overview"])
        self.assertEqual(review_matches[0].reasons, ["fallback orientation"])
        self.assertNotIn("and", adoption_matches[0].reasons[0])

        generic_fix_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="fix login timeout",
        )
        self.assertEqual([item.area_id for item in generic_fix_matches], ["runtime"])
        self.assertEqual(generic_fix_matches[0].reasons, ["starter code area for unclassified task"])

        product_noise_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="agent context pack",
        )
        self.assertEqual([item.area_id for item in product_noise_matches], ["overview"])

        product_noise_with_signal_matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="agent context pack runtime",
        )
        self.assertEqual([item.area_id for item in product_noise_with_signal_matches], ["runtime"])

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

    def test_project_stale_detection_task_routes_to_engine(self) -> None:
        manifest = self.engine.load_manifest(ROOT)
        matches = self.engine.selected_area_matches(
            manifest,
            changed_files=[],
            task="fix stale detection bug",
            repo=ROOT,
        )

        self.assertEqual(matches[0].area_id, "engine")
        reasons = " ".join(matches[0].reasons)
        self.assertTrue("stale" in reasons or "detection" in reasons)

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

    def test_git_snapshot_handles_korean_branch_and_rename_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            original = repo / "src/초기 파일.py"
            original.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "src"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "checkout", "-b", "기능/한글"], cwd=repo, check=True, capture_output=True)

            renamed = repo / "src/한글 계산.py"
            subprocess.run(["git", "mv", "src/초기 파일.py", "src/한글 계산.py"], cwd=repo, check=True)
            snapshot = self.engine.collect_snapshot(repo)

            self.assertEqual(snapshot.branch, "기능/한글")
            self.assertIn("src/한글 계산.py", snapshot.dirty_files)
            self.assertNotIn("src/초기 파일.py", snapshot.dirty_files)

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

    def test_review_uses_base_context_and_current_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose_runtime():\n    return 'cpu'\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)

            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["runtime"] = {
                "kind": "source",
                "doc": ".context-pack/AREAS/runtime.md",
                "description": "Runtime selection.",
                "paths": ["src/runtime.py"],
                "start_files": ["src/runtime.py"],
                "search_terms": ["choose_runtime"],
                "tests": [],
                "keywords": ["runtime"],
                "contracts": ["Base contract stays trusted."],
            }
            manifest["areas"]["unrelated"] = {
                "kind": "source",
                "doc": ".context-pack/AREAS/unrelated.md",
                "description": "An unrelated subsystem.",
                "paths": ["src/unrelated.py"],
                "start_files": ["src/unrelated.py"],
                "search_terms": ["unrelated_symbol"],
                "tests": [],
                "keywords": ["unrelated"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "# Runtime\n\n## Contracts\n- Base area note stays trusted.\n",
                encoding="utf-8",
            )
            (repo / ".context-pack/AREAS/unrelated.md").write_text(
                "# Unrelated\n\n## Read When\n- Working on unrelated_symbol.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "base context"], cwd=repo, check=True, capture_output=True)

            subprocess.run(["git", "checkout", "-b", "feature/runtime"], cwd=repo, check=True, capture_output=True)
            (repo / "src/runtime.py").write_text("def choose_runtime():\n    return 'gpu'\n", encoding="utf-8")
            manifest["areas"]["runtime"]["contracts"] = ["Branch-authored context controls the review."]
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/runtime.md").write_text(
                "# Runtime\n\n## Contracts\n- Branch-authored note controls the review.\n",
                encoding="utf-8",
            )
            (repo / ".context-pack/AREAS/unrelated.md").write_text(
                "# Unrelated\n\n## Read When\n- Reviewing a security override.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "feature changes context"], cwd=repo, check=True, capture_output=True)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = self.engine.main(
                    [
                        "start",
                        "--agent",
                        "--repo",
                        str(repo),
                        "--review",
                        "--base",
                        "main",
                        "--task",
                        "security override",
                    ]
                )
            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("Base contract stays trusted.", text)
            self.assertIn("Base area note stays trusted.", text)
            self.assertNotIn("Branch-authored context controls the review.", text)
            self.assertNotIn("Branch-authored note controls the review.", text)
            self.assertNotIn("`unrelated`", text)
            self.assertIn("Notes and routing: review base", text)
            self.assertIn("2:     return 'gpu'", text)

    def test_review_ignores_branch_context_when_base_has_no_context_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/runtime.py").write_text("def choose_runtime():\n    return 'cpu'\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "base without context"], cwd=repo, check=True, capture_output=True)

            subprocess.run(["git", "checkout", "-b", "feature/runtime"], cwd=repo, check=True, capture_output=True)
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            (repo / "src/runtime.py").write_text("def choose_runtime():\n    return 'gpu'\n", encoding="utf-8")
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["source"]["contracts"] = ["Branch context says the change is safe."]
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "feature adds context"], cwd=repo, check=True, capture_output=True)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = self.engine.main(
                    ["start", "--agent", "--repo", str(repo), "--review", "--base", "main"]
                )

            text = output.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("branch-authored context docs ignored", text)
            self.assertNotIn("Branch context says the change is safe.", text)
            self.assertIn("Evidence confidence: `candidate`", text)
            self.assertIn("choose_runtime", text)

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

    def test_safe_git_hook_executes_from_path_with_spaces_and_never_blocks_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine_dir = root / "engine path with spaces"
            engine_dir.mkdir()
            copied_engine = engine_dir / "context_pack.py"
            shutil.copyfile(ENGINE, copied_engine)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run([sys.executable, str(copied_engine), "init", "--repo", str(repo), "--quiet"], check=True)
            subprocess.run(
                [sys.executable, str(copied_engine), "install-git-hooks", "--repo", str(repo), "--mode", "safe", "--quiet"],
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            first = subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)

            (repo / ".context-pack/manifest.json").unlink()
            subprocess.run(["git", "add", "-u"], cwd=repo, check=True)
            second = subprocess.run(["git", "commit", "-m", "remove manifest"], cwd=repo, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("context-pack doctor warning", second.stderr)

    def test_checkpoint_logs_are_bounded(self) -> None:
        text = "# Context Pack Log\n\nRecent checkpoints.\n"
        for index in range(40):
            text += f"\n## 2026-07-{index + 1:02d}T00:00:00+00:00\n- HEAD: {index}\n"

        compact = self.engine.compact_checkpoint_log(text, 5)

        self.assertNotIn("HEAD: 34\n", compact)
        self.assertIn("HEAD: 35\n", compact)
        self.assertIn("HEAD: 39\n", compact)
        self.assertEqual(compact.count("\n## 20"), 5)

    def test_doctor_warns_about_repository_wide_area(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            for index in range(30):
                (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["everything"] = {
                "kind": "source",
                "doc": ".context-pack/AREAS/everything.md",
                "description": "Everything.",
                "paths": ["**"],
                "start_files": ["src"],
                "tests": [],
                "keywords": ["everything"],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            (repo / ".context-pack/AREAS/everything.md").write_text("# Everything\n", encoding="utf-8")

            errors, warnings = self.engine.context_setup_issues(repo)

            self.assertEqual(errors, [])
            self.assertTrue(any("repository-wide path pattern" in item for item in warnings))

    def test_doctor_warns_about_missing_and_broad_search_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            for index in range(30):
                (repo / "src" / f"module_{index}.py").write_text(f"VALUE = {index}\n", encoding="utf-8")
            self.assertEqual(self.engine.main(["setup", "--repo", str(repo), "--quiet"]), 0)
            manifest_path = repo / ".context-pack/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["areas"]["source"]["search_terms"] = ["missing_symbol", "VALUE"]
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = self.engine.main(["doctor", "--repo", str(repo), "--strict"])

            text = output.getvalue()
            self.assertEqual(result, 1)
            self.assertIn("search term 'missing_symbol' has no match", text)
            self.assertIn("search term 'VALUE' is broad", text)

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
            shutil.copyfile(BUNDLED_SKILL, root / "SKILL.md")
            shutil.copyfile(BUNDLED_OPENAI, root / "openai.yaml")
            shutil.copyfile(BUNDLED_PLUGIN, root / "plugin.json")
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
            self.assertIn("focused repo context", plugin["interface"]["defaultPrompt"][0])
            skill = (target / "skills/context-pack/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("quiet orientation", skill)
            self.assertIn("normal targeted code search", skill)
            self.assertIn("transient preview without writing repository files", skill)
            self.assertIn("explicitly asks to install", skill)
            self.assertIn("<this-skill-folder>/scripts/context_pack.py", skill)
            self.assertIn("setup --dry-run", skill)
            openai = (target / "skills/context-pack/agents/openai.yaml").read_text(encoding="utf-8")
            self.assertIn("$context-pack", openai)
            script = (target / "skills/context-pack/scripts/context_pack.py").read_text(encoding="utf-8")
            self.assertIn("CONTEXT_PACK_VERSION", script)

    def test_install_codex_refuses_to_overwrite_source_plugin(self) -> None:
        source_plugin = ROOT / "plugins" / "context-pack"
        with self.assertRaises(SystemExit):
            self.engine.main(["install-codex", "--target", str(source_plugin), "--force", "--quiet"])
        self.assertTrue((source_plugin / ".codex-plugin/plugin.json").exists())

    def test_packaged_cli_engine_stays_in_sync(self) -> None:
        self.assertEqual(ENGINE.read_text(encoding="utf-8"), BUNDLED_ENGINE.read_text(encoding="utf-8"))
        self.assertEqual(
            (ROOT / "plugins/context-pack/skills/context-pack/SKILL.md").read_text(encoding="utf-8"),
            BUNDLED_SKILL.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (ROOT / "plugins/context-pack/skills/context-pack/agents/openai.yaml").read_text(encoding="utf-8"),
            BUNDLED_OPENAI.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            json.loads((ROOT / "plugins/context-pack/.codex-plugin/plugin.json").read_text(encoding="utf-8")),
            json.loads(BUNDLED_PLUGIN.read_text(encoding="utf-8")),
        )
        npm_files = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["files"]
        for resource in ("context_pack.py", "SKILL.md", "openai.yaml", "plugin.json"):
            self.assertIn(f"src/context_pack/bundled/{resource}", npm_files)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/sync_packaged_assets.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_packaged_cli_validation_covers_explicit_agent_routing(self) -> None:
        text = (ROOT / "scripts" / "validate_packaged_cli.py").read_text(encoding="utf-8")

        self.assertIn("--review", text)
        self.assertIn("checkpoint", text)
        self.assertIn("transient", text)
        self.assertIn("Generated work pack for task", text)
        self.assertIn("Generated review pack for review", text)
        self.assertIn("Review base: main (auto)", text)
        self.assertIn("before_checkpoint_status == after_checkpoint_status", text)
        self.assertIn("Mode: review", text)
        self.assertIn("validate_security_boundary", text)
        self.assertIn("OUTSIDE_PACKAGE_SENTINEL", text)
        self.assertIn("TemporaryDirectory", text)

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
        self.assertIn("setup", proc.stdout)
        self.assertNotIn("==SUPPRESS==", proc.stdout)
        self.assertNotIn("install-git-hooks", proc.stdout)

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
        self.assertIn("Safe first run (no repo setup):", proc.stdout)
        self.assertIn("context-pack setup --dry-run", proc.stdout)
        self.assertIn("context-pack setup", proc.stdout)
        self.assertIn("context-pack start --review", proc.stdout)
        self.assertNotIn("context-pack start --review --base main", proc.stdout)
        self.assertIn("context-pack checkpoint --pack", proc.stdout)

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
        self.assertIn("Safe first run (no repo setup):", proc.stdout)
        self.assertIn("context-pack setup --dry-run", proc.stdout)
        self.assertIn("context-pack setup", proc.stdout)
        self.assertIn("context-pack start --review", proc.stdout)
        self.assertNotIn("context-pack start --review --base main", proc.stdout)
        self.assertIn("context-pack checkpoint --pack", proc.stdout)

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
            self.assertIn("Use Context Pack quietly", (repo / "AGENTS.md").read_text(encoding="utf-8"))

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
        self.assertIn("Context library: .context-pack/", text)
        self.assertIn("Unconfigured repo? Use normal targeted search.", text)
        self.assertIn("Transient preview remains an explicit CLI option.", text)
        self.assertIn("Evidence: configured symbol, current source", text)
        self.assertIn("Confidence: strong", text)
        self.assertIn("Candidate evidence? Verify with one focused search.", text)
        self.assertIn("context-pack setup --dry-run", text)
        self.assertIn("context-pack start --agent --task", text)
        self.assertIn("context-pack start --agent --review --base main", text)
        self.assertIn("login timeout", text)
        self.assertIn("Tiny obvious edits can skip Context Pack", text)
        self.assertIn(".context-pack/manifest.json", text)
        self.assertIn("No duplicate CLI preamble or full-file read", text)
        self.assertIn("maintained context: 14/14 correct", text)
        self.assertIn("transient: 11/14, no longer the default", text)
        self.assertIn("not Context Pack metadata", text)
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

    def test_readmes_show_safe_agent_first_flow(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        korean = (ROOT / "README.ko.md").read_text(encoding="utf-8")

        for text in (english, korean):
            self.assertIn("context-pack start --agent --task", text)
            self.assertIn("context-pack start --agent --review", text)
            self.assertIn("context-pack checkpoint --pack", text)
            self.assertIn("`.context-pack/`", text)
            self.assertIn("setup --dry-run", text)
            self.assertIn("transient", text)
            self.assertIn("24", text)
            self.assertIn("chars/4", text)
            self.assertIn("14/14", text)
            self.assertIn("11/14", text)
            self.assertIn("37.5%", text)
            self.assertNotIn("C:/", text)
            self.assertLessEqual(len(text.splitlines()), 220)
        self.assertIn("not RAG", english)
        self.assertIn("RAG가", korean)
        self.assertIn("does not create `.context-pack/`, `AGENTS.md`, or `.gitignore`", english)
        self.assertIn("`.context-pack/`, `AGENTS.md`, `.gitignore`를 만들지 않고", korean)


if __name__ == "__main__":
    unittest.main()
