#!/usr/bin/env python3
"""Repo-local context packs for coding agents.

This script is intentionally stdlib-only so it can run from a bundled Codex
skill, from a plugin, or directly inside a checked-out repository.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


CONTEXT_DIR = Path(".context-pack")
AREAS_DIR = CONTEXT_DIR / "AREAS"
HANDOFF_DIR = CONTEXT_DIR
PACKS_DIR = CONTEXT_DIR / "packs"
LOCAL_DIR = CONTEXT_DIR / "local"
MANIFEST_PATH = CONTEXT_DIR / "manifest.json"
INDEX_PATH = CONTEXT_DIR / "INDEX.md"
REVIEW_PATH = CONTEXT_DIR / "REVIEW.md"
CONTRACTS_PATH = CONTEXT_DIR / "CONTRACTS.md"
CURRENT_PATH = CONTEXT_DIR / "CURRENT.md"
LOG_PATH = CONTEXT_DIR / "LOG.md"
DECISIONS_PATH = CONTEXT_DIR / "DECISIONS.md"
LOCAL_PATH = LOCAL_DIR / "LOCAL.md"
PACK_PATH = PACKS_DIR / "CONTEXT_PACK.md"
LEGACY_CONTEXT_DIR = Path(".codex/context")
LEGACY_AREAS_DIR = LEGACY_CONTEXT_DIR / "AREAS"
LEGACY_HANDOFF_DIR = Path(".codex/handoff")
LEGACY_PACKS_DIR = Path(".codex/packs")
LEGACY_MANIFEST_PATH = LEGACY_CONTEXT_DIR / "manifest.json"
LEGACY_INDEX_PATH = LEGACY_CONTEXT_DIR / "INDEX.md"
LEGACY_REVIEW_PATH = LEGACY_CONTEXT_DIR / "REVIEW.md"
LEGACY_CONTRACTS_PATH = LEGACY_CONTEXT_DIR / "CONTRACTS.md"
LEGACY_CURRENT_PATH = LEGACY_HANDOFF_DIR / "CURRENT.md"
LEGACY_LOG_PATH = LEGACY_HANDOFF_DIR / "LOG.md"
LEGACY_DECISIONS_PATH = LEGACY_HANDOFF_DIR / "DECISIONS.md"
LEGACY_LOCAL_PATH = LEGACY_HANDOFF_DIR / "LOCAL.md"
LEGACY_PACK_PATH = LEGACY_PACKS_DIR / "CONTEXT_PACK.md"
AGENTS_PATH = Path("AGENTS.md")
AGENT_DOC_TARGETS = {
    "agents": AGENTS_PATH,
    "claude": Path("CLAUDE.md"),
    "cursor": Path(".cursor/rules/context-pack.mdc"),
}
DEFAULT_AGENT_DOC_TARGETS = ("agents", "claude", "cursor")

FINGERPRINT_START = "<!-- context-pack:fingerprint:start -->"
FINGERPRINT_END = "<!-- context-pack:fingerprint:end -->"
AGENT_RULES_START = "<!-- context-pack:rules:start -->"
AGENT_RULES_END = "<!-- context-pack:rules:end -->"
HOOK_START = "# context-pack:start"
HOOK_END = "# context-pack:end"
CONTEXT_PACK_VERSION = "0.5.0"
TEXT_BUDGET_MAX_FILE_BYTES = 1_000_000
SMALL_REPO_FILE_THRESHOLD = 24
PUBLISHED_LOG_MAX_ENTRIES = 30
LOCAL_LOG_MAX_ENTRIES = 20
BROAD_AREA_MIN_FILES = 20
BROAD_AREA_RATIO = 0.65
AGENT_MAX_AREAS = 2
AGENT_MAX_SCOPES = 4
AGENT_MAX_CONTRACTS = 3
AGENT_MAX_FAILURE_MODES = 2
AGENT_MAX_TESTS = 1
AGENT_PACK_MAX_CHARS = 8_000
EVIDENCE_MAX_FILES = 160
EVIDENCE_MAX_SCAN_BYTES = 6_000_000
EVIDENCE_MAX_FILE_BYTES = 500_000
EVIDENCE_MAX_TERMS = 6
EVIDENCE_MAX_SNIPPETS = 2
EVIDENCE_MAX_CHARS = 4_500
EVIDENCE_MAX_LINE_CHARS = 220
EVIDENCE_CONTEXT_BEFORE = 3
EVIDENCE_CONTEXT_AFTER = 18
EVIDENCE_CLUSTER_DISTANCE = 32
EVIDENCE_BROAD_HIT_LIMIT = 30
TEXT_BUDGET_BINARY_SUFFIXES = {
    ".7z",
    ".avif",
    ".bmp",
    ".bz2",
    ".cur",
    ".dll",
    ".dylib",
    ".eot",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".ogg",
    ".otf",
    ".pdf",
    ".png",
    ".so",
    ".tar",
    ".tgz",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}
TOKEN_STOP_WORDS = {
    "about",
    "after",
    "again",
    "against",
    "all",
    "and",
    "any",
    "are",
    "before",
    "between",
    "both",
    "but",
    "can",
    "cannot",
    "code",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "its",
    "make",
    "more",
    "not",
    "now",
    "our",
    "out",
    "over",
    "should",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "this",
    "those",
    "through",
    "use",
    "using",
    "was",
    "what",
    "when",
    "where",
    "which",
    "while",
    "why",
    "will",
    "with",
    "work",
    "you",
    "your",
}
CODE_TASK_TOKENS = {
    "bug",
    "broken",
    "crash",
    "debug",
    "error",
    "exception",
    "fail",
    "failed",
    "failing",
    "failure",
    "fix",
    "implement",
    "issue",
    "patch",
    "problem",
    "regression",
    "refactor",
    "버그",
    "오류",
    "에러",
    "문제",
    "고쳐",
    "고쳐줘",
    "수정",
    "수정해줘",
    "해결해줘",
}
TASK_ACTION_TOKENS = CODE_TASK_TOKENS | {
    "review",
    "reviewed",
    "reviewing",
}
FAILURE_TOKENS = CODE_TASK_TOKENS | {"red", "실패", "실패해", "실패함"}
ROUTE_NOISE_TOKENS = {
    "agent",
    "agents",
    "context",
    "pack",
    "packs",
}


@dataclasses.dataclass
class TextBudget:
    chars: int = 0
    files: int = 0
    skipped: int = 0


@dataclasses.dataclass
class Snapshot:
    repo_root: Path
    is_git: bool
    branch: str
    head: str
    dirty_files: list[str]
    diff_hash: str
    timestamp: str
    status_lines: list[str]


@dataclasses.dataclass
class AreaSelection:
    area_id: str
    score: int
    reasons: list[str]
    matched_files: list[str]


@dataclasses.dataclass
class EvidenceSnippet:
    path: str
    start_line: int
    end_line: int
    term: str
    text: str


@dataclasses.dataclass
class EvidenceResult:
    terms: list[str]
    snippets: list[EvidenceSnippet]
    confidence: str
    reason: str


@dataclasses.dataclass(frozen=True)
class ContextLayout:
    name: str
    storage_dir: Path
    context_dir: Path
    areas_dir: Path
    handoff_dir: Path
    packs_dir: Path
    manifest_path: Path
    index_path: Path
    review_path: Path
    contracts_path: Path
    current_path: Path
    log_path: Path
    decisions_path: Path
    local_path: Path
    pack_path: Path


PRIMARY_LAYOUT = ContextLayout(
    name="primary",
    storage_dir=CONTEXT_DIR,
    context_dir=CONTEXT_DIR,
    areas_dir=AREAS_DIR,
    handoff_dir=HANDOFF_DIR,
    packs_dir=PACKS_DIR,
    manifest_path=MANIFEST_PATH,
    index_path=INDEX_PATH,
    review_path=REVIEW_PATH,
    contracts_path=CONTRACTS_PATH,
    current_path=CURRENT_PATH,
    log_path=LOG_PATH,
    decisions_path=DECISIONS_PATH,
    local_path=LOCAL_PATH,
    pack_path=PACK_PATH,
)

LEGACY_LAYOUT = ContextLayout(
    name="legacy",
    storage_dir=Path(".codex"),
    context_dir=LEGACY_CONTEXT_DIR,
    areas_dir=LEGACY_AREAS_DIR,
    handoff_dir=LEGACY_HANDOFF_DIR,
    packs_dir=LEGACY_PACKS_DIR,
    manifest_path=LEGACY_MANIFEST_PATH,
    index_path=LEGACY_INDEX_PATH,
    review_path=LEGACY_REVIEW_PATH,
    contracts_path=LEGACY_CONTRACTS_PATH,
    current_path=LEGACY_CURRENT_PATH,
    log_path=LEGACY_LOG_PATH,
    decisions_path=LEGACY_DECISIONS_PATH,
    local_path=LEGACY_LOCAL_PATH,
    pack_path=LEGACY_PACK_PATH,
)


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def now_local() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_path(value: str | Path) -> str:
    return str(value).replace("\\", "/").strip("/")


def absolute_shell_path(value: str | Path) -> str:
    return Path(value).resolve().as_posix()


def rel_to_repo(path: Path, repo: Path) -> str:
    try:
        return normalize_path(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return path.resolve().as_posix()


def run(
    cmd: list[str],
    cwd: Path,
    *,
    text: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess[Any]:
    kwargs: dict[str, Any] = {
        "cwd": str(cwd),
        "capture_output": True,
        "check": check,
    }
    if text:
        kwargs.update(text=True, encoding="utf-8", errors="surrogateescape")
    else:
        kwargs["text"] = False
    return subprocess.run(cmd, **kwargs)


def git_text(repo: Path, args: list[str]) -> str | None:
    try:
        proc = run(["git", *args], repo)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.rstrip("\r\n")


def git_bytes(repo: Path, args: list[str]) -> bytes:
    try:
        proc = run(["git", *args], repo, text=False)
    except FileNotFoundError:
        return b""
    if proc.returncode != 0:
        return b""
    return proc.stdout


def resolve_commit(repo: Path, ref: str | None) -> str | None:
    if not ref:
        return None
    return git_text(repo, ["rev-parse", "--verify", f"{ref}^{{commit}}"])


def git_file_text(repo: Path, ref: str, path: str | Path) -> str | None:
    commit = resolve_commit(repo, ref)
    if not commit:
        return None
    object_name = f"{commit}:{path_text(path)}"
    try:
        proc = run(["git", "show", object_name], repo, text=False)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8-sig", errors="surrogateescape")


def decode_git_path(value: bytes) -> str:
    return value.decode("utf-8", errors="surrogateescape")


def git_path_list(repo: Path, args: list[str]) -> list[str] | None:
    try:
        proc = run(["git", *args], repo, text=False)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    return [normalize_path(decode_git_path(item)) for item in proc.stdout.split(b"\0") if item]


def status_lines_from_porcelain_z(data: bytes) -> list[str]:
    parts = data.split(b"\0")
    lines: list[str] = []
    index = 0
    while index < len(parts):
        record = parts[index]
        index += 1
        if not record:
            continue
        if len(record) < 3:
            continue
        code = decode_git_path(record[:2])
        destination = normalize_path(decode_git_path(record[3:]))
        if "R" in code or "C" in code:
            source = ""
            if index < len(parts):
                source = normalize_path(decode_git_path(parts[index]))
                index += 1
            path = f"{source} -> {destination}" if source else destination
        else:
            path = destination
        lines.append(f"{code} {path}")
    return lines


def find_repo_root(start: Path) -> tuple[Path, bool]:
    root = git_text(start, ["rev-parse", "--show-toplevel"])
    if not root:
        return start.resolve(), False
    return Path(root).resolve(), True


def status_to_dirty_files(status_lines: Iterable[str]) -> list[str]:
    files: list[str] = []
    for raw in status_lines:
        if len(raw) < 4:
            continue
        path = raw[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            files.append(normalize_path(path.strip('"')))
    return sorted(dict.fromkeys(files))


def compute_diff_hash(repo: Path, status_lines: list[str]) -> str:
    if not status_lines:
        return "clean"

    h = hashlib.sha256()
    h.update("\n".join(status_lines).encode("utf-8", errors="replace"))
    h.update(b"\0--diff--\0")
    h.update(git_bytes(repo, ["diff", "--binary"]))
    h.update(b"\0--cached--\0")
    h.update(git_bytes(repo, ["diff", "--cached", "--binary"]))

    # `git diff` does not include untracked file contents. Include a bounded
    # content hash so a new note/script does not share the same fingerprint as
    # an empty placeholder with the same path.
    for line in status_lines:
        if not line.startswith("?? "):
            continue
        rel = normalize_path(line[3:].strip())
        path = repo / rel
        if not path.is_file():
            continue
        h.update(f"\0--untracked:{rel}--\0".encode("utf-8"))
        try:
            size = path.stat().st_size
            h.update(str(size).encode("ascii"))
            if size <= 1_000_000:
                h.update(path.read_bytes())
        except OSError:
            h.update(b"<unreadable>")

    return "sha256:" + h.hexdigest()[:24]


def collect_snapshot(start: Path) -> Snapshot:
    repo, is_git = find_repo_root(start)
    status_data = git_bytes(repo, ["status", "--porcelain=v1", "-z", "-uall"]) if is_git else b""
    status_lines = status_lines_from_porcelain_z(status_data)
    branch = git_text(repo, ["branch", "--show-current"]) if is_git else None
    if is_git and not branch:
        branch = git_text(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    head = git_text(repo, ["rev-parse", "--short=12", "HEAD"]) if is_git else None

    return Snapshot(
        repo_root=repo,
        is_git=is_git,
        branch=branch or ("unknown" if is_git else "not-a-git-repo"),
        head=head or ("unknown" if is_git else "not-a-git-repo"),
        dirty_files=status_to_dirty_files(status_lines),
        diff_hash=compute_diff_hash(repo, status_lines) if is_git else "not-a-git-repo",
        timestamp=now_local(),
        status_lines=status_lines,
    )


def layout_exists(repo: Path, layout: ContextLayout) -> bool:
    if layout.name == "legacy":
        return any(
            (repo / rel).exists()
            for rel in [layout.manifest_path, layout.index_path, layout.current_path]
        )
    return (repo / layout.manifest_path).exists() or (repo / layout.context_dir).exists() or (repo / layout.handoff_dir).exists()


def resolve_layout(repo: Path, *, for_write: bool = False) -> ContextLayout:
    if (repo / PRIMARY_LAYOUT.manifest_path).exists() or (repo / PRIMARY_LAYOUT.storage_dir).exists():
        return PRIMARY_LAYOUT
    if not for_write and layout_exists(repo, LEGACY_LAYOUT):
        return LEGACY_LAYOUT
    if for_write and layout_exists(repo, LEGACY_LAYOUT):
        return LEGACY_LAYOUT
    return PRIMARY_LAYOUT


def path_text(path: str | Path) -> str:
    return normalize_path(path)


def rewrite_legacy_paths(text: str) -> str:
    replacements = [
        (".codex/context/AREAS/", ".context-pack/AREAS/"),
        (".codex/context/tmp/", ".context-pack/tmp/"),
        (".codex/context/", ".context-pack/"),
        (".codex/handoff/LOCAL.md", ".context-pack/local/LOCAL.md"),
        (".codex/handoff/", ".context-pack/"),
        (".codex/packs/", ".context-pack/packs/"),
        (".codex/context/**", ".context-pack/**"),
        (".codex/handoff/**", ".context-pack/**"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def ensure_dirs(repo: Path, layout: ContextLayout | None = None) -> None:
    layout = layout or resolve_layout(repo, for_write=True)
    for rel in [layout.context_dir, layout.areas_dir, layout.handoff_dir, layout.packs_dir, layout.local_path.parent]:
        (repo / rel).mkdir(parents=True, exist_ok=True)


def default_manifest(layout: ContextLayout | None = None) -> dict[str, Any]:
    layout = layout or PRIMARY_LAYOUT
    return {
        "version": 1,
        "generated_by": "context-pack",
        "areas": {
            "overview": {
                "kind": "overview",
                "doc": path_text(layout.areas_dir / "overview.md"),
                "description": "Default project orientation and safe starting point.",
                "paths": [
                    "README.md",
                    "AGENTS.md",
                    "CLAUDE.md",
                    "codex.md",
                    path_text(layout.context_dir / "**"),
                ],
                "start_files": [
                    "README.md",
                    "AGENTS.md",
                    path_text(layout.index_path),
                    path_text(layout.current_path),
                ],
                "tests": [],
                "keywords": [
                    "overview",
                    "onboarding",
                    "new session",
                    "architecture",
                    "context",
                    "review",
                ],
                "contracts": [
                    "Treat context docs as routing hints, not ground truth.",
                    "Verify source code when the context fingerprint is stale.",
                ],
                "failure_modes": [
                    "Trusting old summaries after HEAD or dirty files changed.",
                    "Reading logs or generated packs before current source files.",
                    "Editing the wrong checkout or copied workspace.",
                ],
                "stale_if_paths": [
                    path_text(layout.context_dir / "**"),
                    path_text(layout.handoff_dir / "**"),
                    "AGENTS.md",
                    "README.md",
                ],
            }
        },
    }


def pattern_has_match(repo: Path, pattern: str) -> bool:
    pattern = normalize_path(pattern)
    if any(ch in pattern for ch in "*?["):
        try:
            return any(path for path in repo.glob(pattern) if ".git" not in path.parts)
        except ValueError:
            return False
    return (repo / pattern).exists()


def existing_patterns(repo: Path, patterns: list[str]) -> list[str]:
    return [pattern for pattern in patterns if pattern_has_match(repo, pattern)]


SOURCE_TOP_LEVEL_EXCLUDES = {
    ".git",
    ".github",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "docs",
    "examples",
    "scripts",
    "spec",
    "test",
    "tests",
}

WEB_SOURCE_PATHS = [
    "client/js/**",
    "server/js/**",
    "shared/js/**",
    "client/src/**",
    "server/src/**",
    "shared/src/**",
    "frontend/src/**",
    "backend/src/**",
    "web/src/**",
]

WEB_SOURCE_START_FILES = [
    "client/js/*.js",
    "server/js/*.js",
    "shared/js/*.js",
    "client/src/*",
    "server/src/*",
    "shared/src/*",
    "frontend/src/*",
    "backend/src/*",
    "web/src/*",
]

GO_SOURCE_DIR_EXCLUDES = SOURCE_TOP_LEVEL_EXCLUDES | {
    "assets",
    "benchmark",
    "benchmarks",
    "cmdline",
    "coverage",
    "fixtures",
    "testdata",
    "vendor",
}

GO_SOURCE_FILE_LIMIT = 24
GO_TEST_FILE_LIMIT = 24
RUST_SOURCE_PATHS = ["crates/*/src/**"]
RUST_SOURCE_START_FILES = ["src/lib.rs", "src/main.rs", "crates/*/src/lib.rs", "crates/*/src/main.rs"]


def top_level_source_dirs_with_extension(repo: Path, extension: str, *, exclude_suffix: str = "") -> list[str]:
    dirs: list[str] = []
    for child in sorted(repo.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir():
            continue
        name = child.name
        if name in GO_SOURCE_DIR_EXCLUDES or name.startswith("."):
            continue
        try:
            has_source = any(
                path.is_file()
                and path.suffix == extension
                and (not exclude_suffix or not path.name.endswith(exclude_suffix))
                for path in child.rglob(f"*{extension}")
            )
        except OSError:
            has_source = False
        if has_source:
            dirs.append(name)
    return dirs


def looks_like_go_repo(repo: Path) -> bool:
    if (repo / "go.mod").is_file():
        return True
    try:
        return any(path.is_file() for path in repo.glob("*.go"))
    except ValueError:
        return False


def discovered_go_source_files(repo: Path, limit: int = GO_SOURCE_FILE_LIMIT) -> list[str]:
    if not looks_like_go_repo(repo):
        return []
    candidates: list[Path] = []
    try:
        candidates.extend(path for path in repo.glob("*.go") if path.is_file() and not path.name.endswith("_test.go"))
    except ValueError:
        pass
    for dirname in top_level_source_dirs_with_extension(repo, ".go", exclude_suffix="_test.go"):
        try:
            candidates.extend(
                path
                for path in (repo / dirname).glob("*.go")
                if path.is_file() and not path.name.endswith("_test.go")
            )
        except OSError:
            continue
    return [rel_to_repo(path, repo) for path in sorted(candidates, key=lambda item: rel_to_repo(item, repo))[:limit]]


def discovered_go_test_files(repo: Path, limit: int = GO_TEST_FILE_LIMIT) -> list[str]:
    if not looks_like_go_repo(repo):
        return []
    try:
        candidates = sorted(repo.glob("**/*_test.go"), key=lambda item: rel_to_repo(item, repo))
    except ValueError:
        candidates = []
    return [rel_to_repo(path, repo) for path in candidates if ".git" not in path.parts][:limit]


def inferred_source_paths(repo: Path) -> tuple[list[str], list[str]]:
    paths = ["src/**", "lib/**", "app/**", "packages/**"] + WEB_SOURCE_PATHS + RUST_SOURCE_PATHS
    start_files = [
        "src/*.py",
        "src/*.js",
        "src/*.ts",
        "lib/*.py",
        "lib/*.js",
        "lib/*.ts",
        "app/*.py",
        "app/*.js",
        "app/*.ts",
        "packages/*/src/*",
    ] + WEB_SOURCE_START_FILES + RUST_SOURCE_START_FILES
    for child in sorted(repo.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir():
            continue
        name = child.name
        if name in SOURCE_TOP_LEVEL_EXCLUDES or name.startswith("."):
            continue
        if (child / "__init__.py").is_file():
            paths.append(f"{name}/**")
            start_files.extend([f"{name}/__init__.py", f"{name}/*.py"])
    go_source_files = discovered_go_source_files(repo)
    if go_source_files:
        paths.extend(["*.go", "cmd/**", "internal/**", "pkg/**"])
        paths.extend(f"{dirname}/**" for dirname in top_level_source_dirs_with_extension(repo, ".go", exclude_suffix="_test.go"))
        start_files.extend(go_source_files)
    return paths, start_files


def inferred_test_paths(repo: Path) -> tuple[list[str], list[str]]:
    paths = ["tests/**", "test/**", "__tests__/**", "spec/**"]
    start_files = [
        "tests/test_*.py",
        "tests/*_test.py",
        "test/test_*.py",
        "test/*_test.py",
        "__tests__/*",
        "spec/*",
    ]
    go_test_files = discovered_go_test_files(repo)
    if go_test_files:
        paths.extend(["*_test.go", "**/*_test.go"])
        start_files.extend(go_test_files)
    return paths, start_files


def inferred_verification_commands(repo: Path) -> list[str]:
    commands: list[str] = []
    package_json = repo / "package.json"
    if package_json.is_file():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            package = {}
        test_script = (package.get("scripts") or {}).get("test") if isinstance(package, dict) else None
        if test_script and "no test specified" not in str(test_script).lower():
            commands.append("npm test")
    if (repo / "go.mod").is_file():
        commands.append("go test ./...")
    if (repo / "Cargo.toml").is_file():
        commands.append("cargo test")
    if any((repo / name).is_file() for name in ("pytest.ini", "tox.ini", "conftest.py")):
        commands.append("python -m pytest")
    elif (repo / "tests").is_dir():
        try:
            has_unittest = any((repo / "tests").glob("test_*.py"))
        except OSError:
            has_unittest = False
        if has_unittest:
            commands.append("python -m unittest discover -s tests -v")
    makefile = repo / "Makefile"
    if makefile.is_file():
        try:
            has_test_target = any(line.startswith("test:") for line in makefile.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError):
            has_test_target = False
        if has_test_target:
            commands.append("make test")
    return unique(commands)[:2]


def inferred_area_candidates(repo: Path, layout: ContextLayout | None = None) -> dict[str, dict[str, Any]]:
    layout = layout or resolve_layout(repo)
    source_paths, source_start_files = inferred_source_paths(repo)
    test_paths, test_start_files = inferred_test_paths(repo)
    verify_commands = inferred_verification_commands(repo)
    candidates = {
        "source": {
            "kind": "source",
            "doc": path_text(layout.areas_dir / "source.md"),
            "description": "Application or library source code.",
            "paths": source_paths,
            "start_files": source_start_files,
            "tests": ["tests/**", "test/**"],
            "verify": verify_commands,
            "keywords": [
                "source",
                "implementation",
                "application",
                "library",
                "client",
                "server",
                "shared",
                "frontend",
                "backend",
                "web",
                "go",
                "golang",
                "route",
                "router",
                "rust",
                "crate",
            ],
            "contracts": [
                "Verify behavior in source before trusting summaries.",
                "Keep public interfaces backward compatible unless the task explicitly changes them.",
            ],
            "failure_modes": [
                "Changing implementation without updating nearby tests.",
                "Assuming generated or stale context docs reflect current source behavior.",
            ],
            "stale_if_paths": source_paths,
        },
        "assets": {
            "kind": "assets",
            "doc": path_text(layout.areas_dir / "assets.md"),
            "description": "Static assets and frontend media.",
            "paths": [
                "assets/**",
                "public/assets/**",
                "static/**",
                "shared/assets/**",
                "client/sprites/**",
                "client/maps/**",
                "client/img/**",
                "client/audio/**",
                "public/img/**",
                "public/audio/**",
                "media/**",
            ],
            "start_files": [
                "assets",
                "public/assets",
                "static",
                "shared/assets",
            ],
            "tests": [],
            "keywords": ["asset", "assets", "static", "media", "image", "audio"],
            "contracts": [
                "Verify asset paths against the loader code before renaming or moving files.",
                "Keep generated or exported asset formats compatible with runtime consumers.",
            ],
            "failure_modes": [
                "Treating missing assets as code-only bugs without checking manifests or generated maps.",
                "Reading large generated assets before identifying the loader or manifest contract.",
            ],
            "stale_if_paths": [
                "assets/**",
                "public/assets/**",
                "static/**",
                "shared/assets/**",
                "client/sprites/**",
                "client/maps/**",
                "client/img/**",
                "client/audio/**",
                "public/img/**",
                "public/audio/**",
                "media/**",
            ],
        },
        "tests": {
            "kind": "tests",
            "doc": path_text(layout.areas_dir / "tests.md"),
            "description": "Test suites, fixtures, and validation commands.",
            "paths": test_paths,
            "start_files": test_start_files,
            "tests": test_paths,
            "verify": verify_commands,
            "keywords": ["test", "tests", "fixture", "validation", "ci"],
            "contracts": [
                "Tests should exercise user-visible behavior, not only implementation details.",
            ],
            "failure_modes": [
                "Mocks pass while real integration paths fail.",
                "Fixtures drift from the source contracts they claim to cover.",
            ],
            "stale_if_paths": test_paths,
        },
        "docs": {
            "kind": "docs",
            "doc": path_text(layout.areas_dir / "docs.md"),
            "description": "User-facing docs, onboarding notes, and repository guidance.",
            "paths": ["README.md", "README.*.md", "docs/**"],
            "start_files": ["README.md", "docs/README.md", "docs/index.md"],
            "tests": [],
            "keywords": ["docs", "readme", "agents", "claude", "onboarding", "usage", "adoption", "proof"],
            "contracts": [
                "Docs should describe the current install and usage flow.",
                "Agent guidance should be concise and actionable.",
            ],
            "failure_modes": [
                "Docs promise behavior the tool does not implement.",
                "Local machine paths leak into public documentation.",
            ],
            "stale_if_paths": ["README.md", "README.*.md", "docs/**"],
        },
        "automation": {
            "kind": "automation",
            "doc": path_text(layout.areas_dir / "automation.md"),
            "description": "Build, release, scripts, CI, packaging, and developer automation.",
            "paths": [".github/**", "scripts/**", "pyproject.toml", "package.json", "Makefile"],
            "start_files": [
                "pyproject.toml",
                "package.json",
                "Makefile",
                ".github/workflows/*.yml",
                ".github/workflows/*.yaml",
                "scripts/*.py",
            ],
            "tests": [".github/workflows/**"],
            "verify": verify_commands,
            "keywords": ["automation", "ci", "release", "scripts", "packaging"],
            "contracts": [
                "Automation should be reproducible outside the maintainer's machine.",
                "Release checks should not depend on private local paths.",
            ],
            "failure_modes": [
                "CI passes locally but fails on GitHub runners.",
                "Install instructions depend on an unpublished local path.",
            ],
            "stale_if_paths": [".github/**", "scripts/**", "pyproject.toml", "package.json", "Makefile"],
        },
    }

    inferred: dict[str, dict[str, Any]] = {}
    for area_id, area in candidates.items():
        matched_paths = existing_patterns(repo, area["paths"])
        if not matched_paths:
            continue
        copy = dict(area)
        copy["paths"] = matched_paths
        copy["start_files"] = existing_patterns(repo, area["start_files"])
        copy["tests"] = existing_patterns(repo, area["tests"])
        copy["stale_if_paths"] = existing_patterns(repo, area["stale_if_paths"]) or matched_paths
        inferred[area_id] = copy
    return inferred


def merge_inferred_areas(repo: Path, manifest: dict[str, Any], layout: ContextLayout | None = None) -> dict[str, Any]:
    manifest.setdefault("areas", {})
    areas = manifest["areas"]
    for area_id, area in inferred_area_candidates(repo, layout).items():
        areas.setdefault(area_id, area)
    return manifest


def should_infer_areas(args: argparse.Namespace, manifest_path: Path) -> bool:
    explicit = getattr(args, "infer_areas", None)
    if explicit is not None:
        return bool(explicit)
    return not manifest_path.exists()


def setup_manifest(repo: Path, layout: ContextLayout, *, infer_areas: bool) -> dict[str, Any]:
    manifest = load_manifest(repo, layout)
    if infer_areas:
        manifest = merge_inferred_areas(repo, manifest, layout)
    return manifest


def manifest_needs_write(path: Path, manifest: dict[str, Any]) -> bool:
    if not path.exists():
        return True
    try:
        current = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return True
    return current != manifest


def parse_manifest(text: str, source: str, layout: ContextLayout) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{source} must contain a JSON object")
    data.setdefault("version", 1)
    data.setdefault("areas", {})
    return data


def load_manifest(repo: Path, layout: ContextLayout | None = None) -> dict[str, Any]:
    layout = layout or resolve_layout(repo)
    path = repo / layout.manifest_path
    if not path.exists():
        return default_manifest(layout)
    return parse_manifest(path.read_text(encoding="utf-8-sig"), path_text(layout.manifest_path), layout)


def load_manifest_from_ref(repo: Path, layout: ContextLayout, ref: str) -> tuple[dict[str, Any], str] | None:
    commit = resolve_commit(repo, ref)
    if not commit:
        return None
    text = git_file_text(repo, commit, layout.manifest_path)
    if text is None:
        return None
    source = f"{commit[:12]}:{path_text(layout.manifest_path)}"
    return parse_manifest(text, source, layout), commit


def resolve_pack_context(
    repo: Path,
    layout: ContextLayout,
    args: argparse.Namespace,
    *,
    has_context_library: bool,
) -> tuple[dict[str, Any], str | None, bool]:
    mode = getattr(args, "mode", "work")
    base = getattr(args, "base", None)
    if mode == "review" and base:
        trusted = load_manifest_from_ref(repo, layout, base)
        if trusted:
            manifest, commit = trusted
            return manifest, commit, False
        return inferred_manifest(repo, layout), None, True
    if has_context_library:
        return load_manifest(repo, layout), None, False
    return inferred_manifest(repo, layout), None, True


def inferred_manifest(repo: Path, layout: ContextLayout | None = None) -> dict[str, Any]:
    layout = layout or PRIMARY_LAYOUT
    return merge_inferred_areas(repo, default_manifest(layout), layout)


def transient_pack_path(repo: Path, snapshot: Snapshot) -> Path:
    if snapshot.is_git:
        git_path = git_text(repo, ["rev-parse", "--git-path", "context-pack/CONTEXT_PACK.md"])
        if git_path:
            path = Path(git_path)
            return path.resolve() if path.is_absolute() else (repo / path).resolve()
    key = hashlib.sha256(str(repo.resolve()).encode("utf-8", errors="surrogateescape")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / "context-pack" / key / "CONTEXT_PACK.md"


def write_text_lf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text_lf(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_if_missing(path: Path, content: str, *, force: bool = False) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(path, content)
    return True


def replace_marker(text: str, start: str, end: str, content: str) -> str:
    block = f"{start}\n{content.rstrip()}\n{end}"
    if start in text and end in text:
        before = text.split(start, 1)[0]
        after = text.split(end, 1)[1]
        prefix = before.rstrip()
        if prefix:
            prefix += "\n\n"
        return prefix + block + "\n" + after.lstrip()
    if text and not text.endswith("\n"):
        text += "\n"
    return text + "\n" + block + "\n"


def marker_content(block: str, start: str, end: str) -> str:
    if start not in block or end not in block:
        return block.strip()
    after_start = block.split(start, 1)[1]
    if after_start.startswith("\n"):
        after_start = after_start[1:]
    before_end = after_start.rsplit(end, 1)[0]
    return before_end.strip("\n")


def marker_fields(markdown: str, start: str, end: str) -> dict[str, str]:
    if start not in markdown or end not in markdown:
        return {}
    fields: dict[str, str] = {}
    for line in marker_content(markdown, start, end).splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def render_fingerprint(snapshot: Snapshot) -> str:
    dirty = ", ".join(snapshot.dirty_files) if snapshot.dirty_files else "none"
    return "\n".join(
        [
            f"- Repo root: {snapshot.repo_root}",
            f"- Git repo: {'yes' if snapshot.is_git else 'no'}",
            f"- Branch: {snapshot.branch}",
            f"- HEAD: {snapshot.head}",
            f"- Dirty files: {dirty}",
            f"- Dirty diff hash: {snapshot.diff_hash}",
            f"- Updated at: {snapshot.timestamp}",
        ]
    )


def overview_area_doc(snapshot: Snapshot, layout: ContextLayout | None = None) -> str:
    layout = layout or PRIMARY_LAYOUT
    return f"""---
id: overview
last_reviewed_head: {snapshot.head}
status: active
paths:
  - README.md
  - AGENTS.md
  - {path_text(layout.context_dir / "**")}
tests: []
stale_if:
  - AGENTS.md changes
  - README.md changes
  - context manifest changes
---

# Overview

## Read When
- Starting a new session or code review.
- Unsure which area owns the task.
- Bootstrapping this repository's context library.

## Start With
- README.md
- AGENTS.md
- {path_text(layout.index_path)}
- {path_text(layout.current_path)}

## Contracts
- Context docs are routing hints, not ground truth.
- If HEAD, dirty files, or diff hash differ from the pack, verify source code before acting.
- Generated packs are temporary and should not be committed.

## Common Failure Modes
- Trusting stale summaries after the code moved on.
- Reading checkpoint history before the current source of truth.
- Editing a copied checkout or generated file instead of the canonical workspace.

## Expand Scope If
- Public API, CLI, schema, storage format, subprocess launch, or test helpers changed.
- The changed file does not match any known area.

## Do Not Start With
- {path_text(layout.packs_dir)}/
- archived logs
- generated artifacts
"""


def generic_area_doc(area_id: str, area: dict[str, Any], snapshot: Snapshot, layout: ContextLayout | None = None) -> str:
    layout = layout or PRIMARY_LAYOUT
    paths = "\n".join(f"  - {item}" for item in area.get("paths", []) or [])
    tests = "\n".join(f"  - {item}" for item in area.get("tests", []) or [])
    verify = "\n".join(f"  - {item}" for item in area.get("verify", []) or [])
    stale = "\n".join(f"  - {item} changes" for item in area.get("stale_if_paths", []) or [])
    start = "\n".join(f"- `{item}`" for item in area.get("start_files", []) or [])
    search = "\n".join(f"- `{item}`" for item in area.get("search_terms", []) or [])
    contracts = "\n".join(f"- {item}" for item in area.get("contracts", []) or [])
    failures = "\n".join(f"- {item}" for item in area.get("failure_modes", []) or [])
    return f"""---
id: {area_id}
last_reviewed_head: {snapshot.head}
status: active
paths:
{paths or "  - unknown"}
tests:
{tests or "  - none"}
verify:
{verify or "  - none"}
stale_if:
{stale or "  - relevant files change"}
---

# {area_id.replace("-", " ").title()}

## Read When
- {area.get("description", "Working in this area.")}

## Start With
{start or f"- Use `{path_text(layout.index_path)}` to choose source files."}

## Search First
{search or "- Use distinctive task terms or symbols within the Start With scopes."}

## Verify
{chr(10).join(f"- `{item}`" for item in area.get("verify", []) or []) or "- Use the repository's smallest relevant verification command."}

## Contracts
{contracts or "- Verify behavior in source before trusting summaries."}

## Common Failure Modes
{failures or "- Context docs drift from source behavior."}

## Expand Scope If
- Public API, CLI, schema, storage, tests, or generated outputs changed.
- A changed file does not match any known area.

## Do Not Start With
- `{path_text(layout.packs_dir)}/`
- generated artifacts unless the task is about generation
"""


def current_doc(snapshot: Snapshot, layout: ContextLayout | None = None) -> str:
    layout = layout or PRIMARY_LAYOUT
    fingerprint = render_fingerprint(snapshot)
    return f"""# Current Handoff

{FINGERPRINT_START}
{fingerprint}
{FINGERPRINT_END}

## Active Goal
- Keep this short. Move details into `{path_text(layout.areas_dir)}/*.md`.

## Read First
1. `{path_text(layout.current_path)}`
2. `{path_text(layout.index_path)}`
3. The relevant `{path_text(layout.areas_dir)}/*.md` files

## Next Actions
1. Generate or consult a context pack before broad repo reading.

## Watch Outs
- Treat stale context as a hint, not a fact.
- Check the source-of-truth checkout before editing.

## Last Verified
- Not recorded yet.
"""


def local_checkpoint_doc(snapshot: Snapshot, layout: ContextLayout | None = None) -> str:
    layout = layout or PRIMARY_LAYOUT
    fingerprint = render_fingerprint(snapshot)
    return f"""# Local Checkpoint

This file is machine-local and ignored by git. Use it for automatic agent work-unit checkpoints without dirtying the tracked handoff.

{FINGERPRINT_START}
{fingerprint}
{FINGERPRINT_END}

## Latest
- Generated packs live in `{path_text(layout.packs_dir)}/` and are also ignored.
- Publish durable handoff state with `context-pack checkpoint --publish` when it should travel through git.

## Local Log
"""


def checkpoint_entry(snapshot: Snapshot) -> str:
    dirty = ", ".join(snapshot.dirty_files) if snapshot.dirty_files else "none"
    return "\n".join(
        [
            f"\n## {snapshot.timestamp}",
            f"- Branch: {snapshot.branch}",
            f"- HEAD: {snapshot.head}",
            f"- Dirty files: {dirty}",
            f"- Dirty diff hash: {snapshot.diff_hash}",
            "- Verification: not recorded",
            "",
        ]
    )


def compact_checkpoint_log(text: str, max_entries: int) -> str:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith("## 20") and "T" in line]
    if len(starts) <= max_entries:
        return text.rstrip() + "\n"
    keep_from = starts[-max_entries]
    prefix = lines[: starts[0]]
    kept = lines[keep_from:]
    return "\n".join(prefix).rstrip() + "\n\n" + "\n".join(kept).rstrip() + "\n"


def append_checkpoint_entry(path: Path, entry: str, *, max_entries: int) -> None:
    text = read_text(path)
    write_text_lf(path, compact_checkpoint_log(text.rstrip() + "\n" + entry.lstrip(), max_entries))


def checkpoint_pack_base(repo: Path, layout: ContextLayout, snapshot: Snapshot, *, publish: bool) -> str | None:
    if not snapshot.is_git or snapshot.dirty_files:
        return None
    candidates = [layout.current_path] if publish else [layout.local_path, layout.current_path]
    for rel in candidates:
        path = repo / rel
        if not path.exists():
            continue
        recorded_head = marker_fields(read_text(path), FINGERPRINT_START, FINGERPRINT_END).get("HEAD")
        if not recorded_head or recorded_head in {"unknown", "not-a-git-repo", snapshot.head}:
            continue
        changed_since = committed_files_between(repo, recorded_head)
        if changed_since is None:
            continue
        if any(not is_checkpoint_pack_only_path(item, layout) for item in changed_since):
            return recorded_head
    return None


def is_checkpoint_pack_only_path(path: str, layout: ContextLayout) -> bool:
    path = normalize_path(path)
    context_dir = path_text(layout.context_dir).rstrip("/")
    legacy_context_dir = path_text(LEGACY_CONTEXT_DIR).rstrip("/")
    return (
        is_handoff_only_path(path, layout)
        or path == context_dir
        or path.startswith(context_dir + "/")
        or path == legacy_context_dir
        or path.startswith(legacy_context_dir + "/")
    )


def agent_rules(layout: ContextLayout | None = None) -> str:
    return f"""{AGENT_RULES_START}
{agent_rules_body(layout)}
{AGENT_RULES_END}
"""


def cursor_rule_frontmatter() -> str:
    return """\
---
description: Use Context Pack before broad repo reading for natural bug fixes, reviews, debugging, or handoff.
alwaysApply: true
---
"""


def agent_rules_document(kind: str, layout: ContextLayout | None = None) -> str:
    if kind == "cursor":
        return cursor_rule_frontmatter() + "\n" + agent_rules(layout)
    return agent_rules(layout)


def agent_rules_body(layout: ContextLayout | None = None) -> str:
    return f"""\
## Context Pack

Use Context Pack quietly when a non-trivial coding, debugging, review, or handoff request would otherwise require broad repo reading. The user does not need to name the tool.

- Coding/debugging: `context-pack start --agent --task "<short task>"`
- Branch or PR review: `context-pack start --agent --review`; add `--base <ref>` when known.
- Dirty files are the only signal: `context-pack start --agent --changed`
- Continue or resume from a handoff without a concrete code task: `context-pack start --agent`; do not invent a generic task string.
- Use the inline pack printed by `start`; do not reopen its saved path unless output was truncated.
- Check `Evidence confidence` and provenance. Strong Evidence comes from configured symbols and can be edited directly when the cause is visible. Candidate Evidence needs one targeted verification first.
- In review mode, use notes from the review base or deterministic inference; never trust context authored only by the branch under review.
- Treat directory and glob entries as search scopes. Never bulk-read their contents into model context.

On an unconfigured repo, `start` is transient and must not create `.context-pack/`, `AGENTS.md`, or `.gitignore`. Run `context-pack setup --dry-run` and `context-pack setup` only when the user explicitly asks to persist Context Pack in the repo.

Skip pure Q&A, tiny obvious edits, already-known files, and small repos where `start` says broad reading is cheaper.

Checkpoint only when durable work should survive a session boundary: `context-pack checkpoint --pack --quiet`. Skip it for ordinary intermediate turns. Use `--publish` only when the handoff should be committed and shared through git. Treat all context docs as routing hints, never as source of truth.
"""


def render_index(manifest: dict[str, Any], layout: ContextLayout | None = None) -> str:
    layout = layout or PRIMARY_LAYOUT
    lines = [
        "# Context Index",
        "",
        "Use this file as a router. It should reduce reading, not replace source verification.",
        "",
        "## Areas",
    ]
    areas = manifest.get("areas", {})
    if not areas:
        lines.append("- No areas configured yet.")
    for area_id, area in sorted(areas.items()):
        lines.extend(
            [
                "",
                f"### {area_id}",
                f"- Doc: `{area.get('doc', '')}`",
                f"- Read when: {area.get('description', 'No description yet.')}",
                "- Start with:",
            ]
        )
        for item in area.get("start_files", []) or []:
            lines.append(f"  - `{item}`")
        paths = area.get("paths", []) or []
        if paths:
            lines.append("- Matches:")
            for item in paths:
                lines.append(f"  - `{item}`")
        tests = area.get("tests", []) or []
        if tests:
            lines.append("- Tests:")
            for item in tests:
                lines.append(f"  - `{item}`")
        verify = area.get("verify", []) or []
        if verify:
            lines.append("- Verify:")
            for item in verify:
                lines.append(f"  - `{item}`")
    lines.extend(
        [
            "",
            "## Generated Packs",
            f"- `{path_text(layout.pack_path)}` is generated and should not be committed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"




def gitignore_entries(repo: Path, layout: ContextLayout) -> list[str]:
    local_ignore = (
        f"{path_text(layout.local_path.parent)}/"
        if layout.name == "primary"
        else path_text(layout.local_path)
    )
    entries = [
        f"{path_text(layout.packs_dir)}/",
        f"{path_text(layout.context_dir / 'tmp')}/",
        local_ignore,
    ]
    if layout.name == "primary" and layout_exists(repo, LEGACY_LAYOUT):
        entries.extend(
            [
                f"{path_text(LEGACY_PACKS_DIR)}/",
                f"{path_text(LEGACY_CONTEXT_DIR / 'tmp')}/",
                path_text(LEGACY_LOCAL_PATH),
            ]
        )
    return entries


def missing_gitignore_entries(repo: Path, layout: ContextLayout) -> list[str]:
    path = repo / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    normalized = set(line.strip() for line in text.splitlines())
    return [entry for entry in gitignore_entries(repo, layout) if entry not in normalized]


def append_gitignore(repo: Path, layout: ContextLayout | None = None) -> None:
    layout = layout or PRIMARY_LAYOUT
    path = repo / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = missing_gitignore_entries(repo, layout)
    if not missing:
        return
    prefix = "" if not text or text.endswith("\n") else "\n"
    block = "\n# context-pack generated/local files\n" + "\n".join(missing) + "\n"
    write_text_lf(path, text + prefix + block)


def append_agent_rules(repo: Path, *, agent_doc: str = "AGENTS.md", layout: ContextLayout | None = None) -> None:
    layout = layout or resolve_layout(repo)
    path = repo / agent_doc
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    rules = agent_rules(layout)
    if AGENT_RULES_START in text and AGENT_RULES_END in text:
        text = replace_marker(text, AGENT_RULES_START, AGENT_RULES_END, agent_rules_body(layout))
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + rules
    write_text_lf(path, text.lstrip())


def append_agent_rules_for_kind(repo: Path, kind: str, layout: ContextLayout | None = None) -> Path:
    layout = layout or resolve_layout(repo)
    rel_path = AGENT_DOC_TARGETS[kind]
    path = repo / rel_path
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if AGENT_RULES_START in text and AGENT_RULES_END in text:
        text = replace_marker(text, AGENT_RULES_START, AGENT_RULES_END, agent_rules_body(layout))
    elif not text:
        text = agent_rules_document(kind, layout)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + agent_rules(layout)
    write_text_lf(path, text)
    return rel_path


def auto_agent_doc_targets(repo: Path) -> list[str]:
    targets = ["agents"]
    if (repo / AGENT_DOC_TARGETS["claude"]).exists() or (repo / ".claude").exists():
        targets.append("claude")
    if (repo / AGENT_DOC_TARGETS["cursor"]).exists() or (repo / ".cursor").exists():
        targets.append("cursor")
    return targets


def resolve_agent_doc_targets(targets: list[str] | None, repo: Path | None = None) -> list[str]:
    requested = targets or ["all"]
    resolved: list[str] = []
    for item in requested:
        if item == "auto":
            for target in auto_agent_doc_targets(repo or Path.cwd()):
                if target not in resolved:
                    resolved.append(target)
            continue
        if item == "all":
            for default in DEFAULT_AGENT_DOC_TARGETS:
                if default not in resolved:
                    resolved.append(default)
            continue
        if item not in AGENT_DOC_TARGETS:
            raise SystemExit(f"Unknown agent doc target: {item}")
        if item not in resolved:
            resolved.append(item)
    return resolved


def setup_file_action(repo: Path, rel_path: Path, *, force: bool) -> str:
    if not (repo / rel_path).exists():
        return "create"
    return "overwrite" if force else "leave unchanged"


def setup_manifest_action(repo: Path, layout: ContextLayout, manifest: dict[str, Any], *, force: bool) -> str:
    path = repo / layout.manifest_path
    if not path.exists():
        return "create"
    if force:
        return "overwrite"
    if manifest_needs_write(path, manifest):
        return "update"
    return "leave unchanged"


def setup_gitignore_action(repo: Path, layout: ContextLayout) -> str:
    if not (repo / ".gitignore").exists():
        return "create"
    if missing_gitignore_entries(repo, layout):
        return "append missing ignores"
    return "leave unchanged"


def setup_agent_doc_action(repo: Path, kind: str) -> str:
    rel_path = AGENT_DOC_TARGETS[kind]
    path = repo / rel_path
    if not path.exists():
        return "create"
    text = path.read_text(encoding="utf-8")
    if AGENT_RULES_START in text and AGENT_RULES_END in text:
        return "refresh managed block"
    if not text:
        return "write managed block"
    return "append managed block"


def setup_context_target_actions(
    repo: Path,
    layout: ContextLayout,
    *,
    force: bool,
    infer_areas: bool,
) -> list[tuple[str, Path]]:
    manifest = setup_manifest(repo, layout, infer_areas=infer_areas)
    targets: list[tuple[str, Path]] = [
        (setup_manifest_action(repo, layout, manifest, force=force), layout.manifest_path),
        (setup_file_action(repo, layout.areas_dir / "overview.md", force=force), layout.areas_dir / "overview.md"),
    ]
    for area_id, area in sorted((manifest.get("areas") or {}).items()):
        if area_id == "overview":
            continue
        doc = normalize_path(area.get("doc", ""))
        if doc:
            rel_path = Path(doc)
            targets.append((setup_file_action(repo, rel_path, force=force), rel_path))
    targets.extend(
        [
            (setup_file_action(repo, layout.index_path, force=force), layout.index_path),
            (setup_file_action(repo, layout.current_path, force=force), layout.current_path),
            (setup_file_action(repo, layout.log_path, force=force), layout.log_path),
            (setup_file_action(repo, layout.decisions_path, force=force), layout.decisions_path),
            (setup_file_action(repo, layout.local_path, force=force), layout.local_path),
            (setup_gitignore_action(repo, layout), Path(".gitignore")),
        ]
    )
    return unique_target_actions(targets)


def unique_target_actions(targets: Iterable[tuple[str, Path]]) -> list[tuple[str, Path]]:
    seen: set[str] = set()
    unique_items: list[tuple[str, Path]] = []
    for action, path in targets:
        key = path_text(path)
        if key in seen:
            continue
        seen.add(key)
        unique_items.append((action, path))
    return unique_items


def setup_hook_targets(mode: str) -> list[str]:
    if mode == "off":
        return []
    hooks = ["pre-commit", "post-checkout", "post-merge"]
    if mode == "aggressive":
        hooks.append("post-commit")
    return hooks


def command_arg(value: str) -> str:
    safe = set("-_./:\\")
    if value and all(ch.isalnum() or ch in safe for ch in value):
        return value
    return '"' + value.replace('"', '\\"') + '"'


def setup_apply_command(args: argparse.Namespace) -> str:
    parts = ["context-pack", "setup"]
    if args.repo != ".":
        parts.extend(["--repo", args.repo])
    if args.force:
        parts.append("--force")
    if getattr(args, "infer_areas", None) is True:
        parts.append("--infer-areas")
    elif getattr(args, "infer_areas", None) is False:
        parts.append("--no-infer-areas")
    if args.agent_docs != "auto":
        parts.extend(["--agent-docs", args.agent_docs])
    if args.git_hooks != "off":
        parts.extend(["--git-hooks", args.git_hooks])
    return " ".join(command_arg(str(part)) for part in parts)


def cmd_setup_dry_run(args: argparse.Namespace, repo: Path, snapshot: Snapshot, layout: ContextLayout) -> int:
    if args.quiet:
        return 0

    agent_docs: list[tuple[str, Path]] = []
    if args.agent_docs != "none":
        targets = [args.agent_docs]
        agent_docs = [
            (setup_agent_doc_action(repo, kind), AGENT_DOC_TARGETS[kind])
            for kind in resolve_agent_doc_targets(targets, repo)
        ]

    print(f"Context Pack setup dry run for {repo}")
    print("")
    print("Setup plan:")
    print("Context files:")
    infer_areas = should_infer_areas(args, repo / layout.manifest_path)
    for action, rel_path in setup_context_target_actions(repo, layout, force=args.force, infer_areas=infer_areas):
        print(f"- {action} {path_text(rel_path)}")

    print("")
    if agent_docs:
        print("Agent docs:")
        for action, rel_path in agent_docs:
            print(f"- {action} {path_text(rel_path)}")
    else:
        print("Agent docs: skipped")

    hooks = setup_hook_targets(args.git_hooks)
    print("")
    print(f"Git hooks: {args.git_hooks}")
    hook_error = False
    if hooks:
        if not snapshot.is_git:
            hook_error = True
            print("- would fail: git hooks require a git repository")
        else:
            for hook in hooks:
                print(f"- install or update .git/hooks/{hook}")

    print("")
    print("No files were written.")
    print("Next:")
    print("- Run the same command without `--dry-run` to apply this plan:")
    print(f"  {setup_apply_command(args)}")
    return 1 if hook_error else 0


def cmd_install_agent_docs(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo)
    written = [append_agent_rules_for_kind(repo, kind, layout) for kind in resolve_agent_doc_targets(args.target, repo)]
    if not args.quiet:
        print(f"Installed Context Pack agent docs in {repo}")
        for rel_path in written:
            print(f"- {rel_path}")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo, for_write=True)

    if args.dry_run:
        return cmd_setup_dry_run(args, repo, snapshot, layout)

    init_args = argparse.Namespace(
        repo=str(repo),
        quiet=True,
        force=args.force,
        infer_areas=args.infer_areas,
        no_agent_doc=True,
        agent_doc="AGENTS.md",
    )
    result = cmd_init(init_args)
    if result != 0:
        return result

    agent_docs: list[Path] = []
    if args.agent_docs != "none":
        targets = [args.agent_docs]
        agent_docs = [append_agent_rules_for_kind(repo, kind, layout) for kind in resolve_agent_doc_targets(targets, repo)]

    if args.git_hooks != "off":
        hook_args = argparse.Namespace(repo=str(repo), quiet=True, mode=args.git_hooks)
        result = cmd_install_git_hooks(hook_args)
        if result != 0:
            return result

    errors, warnings = context_setup_issues(repo)
    if not args.quiet:
        print(f"Context Pack setup complete for {repo}")
        print("")
        print("Ready:")
        print(f"- Context library: {layout.context_dir}")
        print(f"- Handoff docs: {layout.handoff_dir}")
        if agent_docs:
            print("- Agent docs:")
            for rel_path in agent_docs:
                print(f"  - {rel_path}")
        else:
            print("- Agent docs: skipped")
        print(f"- Git hooks: {args.git_hooks}")
        if warnings:
            print("")
            print("Warnings:")
            for item in warnings:
                print(f"- {item}")
        if errors:
            print("")
            print("Errors:")
            for item in errors:
                print(f"- {item}")
        print("")
        print("Next:")
        print('- `context-pack start --task "..."` before broad reading')
        print("- `context-pack start --review` before branch review")
        print("- `context-pack checkpoint --pack` after meaningful work")
    return 1 if errors else 0


def cmd_init(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo, for_write=True)
    ensure_dirs(repo, layout)
    manifest_path = repo / layout.manifest_path
    manifest = setup_manifest(repo, layout, infer_areas=should_infer_areas(args, manifest_path))
    if args.force or manifest_needs_write(manifest_path, manifest):
        write_json(manifest_path, manifest)
    write_if_missing(repo / layout.areas_dir / "overview.md", overview_area_doc(snapshot, layout), force=args.force)
    for area_id, area in (manifest.get("areas") or {}).items():
        if area_id == "overview":
            continue
        write_if_missing(repo / normalize_path(area.get("doc", "")), generic_area_doc(area_id, area, snapshot, layout), force=args.force)
    write_if_missing(repo / layout.index_path, render_index(manifest, layout), force=args.force)
    write_if_missing(repo / layout.current_path, current_doc(snapshot, layout), force=args.force)
    write_if_missing(
        repo / layout.log_path,
        "# Context Pack Log\n\nRecent published checkpoints only; older history remains available in git.\n",
        force=args.force,
    )
    write_if_missing(repo / layout.decisions_path, "# Decisions\n\nRecord durable direction changes only.\n", force=args.force)
    write_if_missing(repo / layout.local_path, local_checkpoint_doc(snapshot, layout), force=args.force)

    append_gitignore(repo, layout)
    if not args.no_agent_doc:
        append_agent_rules(repo, agent_doc=args.agent_doc, layout=layout)

    if not args.quiet:
        print(f"Initialized Context Pack in {repo}")
        print("")
        print("Created:")
        print(f"- Context index: {layout.index_path}")
        print(f"- Handoff: {layout.current_path}")
        print(f"- Manifest: {layout.manifest_path}")
        print("")
        print("Ask your agent next:")
        print('- "Review this branch against main."')
        print('- "Fix the login timeout without rereading the whole repo."')
        print("")
        print("Optional automation:")
        print('- Ask: "Use $context-pack to install safe git hook automation."')
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo, for_write=True)
    if not (repo / layout.manifest_path).exists():
        if not args.quiet:
            print("Context Pack is not configured; no checkpoint files were written.")
            print("Run `context-pack setup --dry-run` only when persistent handoff state is wanted.")
        return 1
    ensure_dirs(repo, layout)
    pack_base = checkpoint_pack_base(repo, layout, snapshot, publish=args.publish) if args.pack else None

    entry = checkpoint_entry(snapshot)
    if args.publish:
        if not (repo / layout.current_path).exists():
            write_if_missing(repo / layout.current_path, current_doc(snapshot, layout))

        current = (repo / layout.current_path).read_text(encoding="utf-8")
        current = replace_marker(current, FINGERPRINT_START, FINGERPRINT_END, render_fingerprint(snapshot))
        write_text_lf(repo / layout.current_path, current)

        if not (repo / layout.log_path).exists():
            write_if_missing(
                repo / layout.log_path,
                "# Context Pack Log\n\nRecent published checkpoints only; older history remains available in git.\n",
            )
        append_checkpoint_entry(repo / layout.log_path, entry, max_entries=PUBLISHED_LOG_MAX_ENTRIES)
        checkpoint_path = layout.current_path
        checkpoint_kind = "Published handoff"
    else:
        if not (repo / layout.local_path).exists():
            write_if_missing(repo / layout.local_path, local_checkpoint_doc(snapshot, layout))

        local = (repo / layout.local_path).read_text(encoding="utf-8")
        local = replace_marker(local, FINGERPRINT_START, FINGERPRINT_END, render_fingerprint(snapshot))
        if "## Local Log" not in local:
            local = local.rstrip() + "\n\n## Local Log\n"
        local = compact_checkpoint_log(local.rstrip() + "\n" + entry.lstrip("\n"), LOCAL_LOG_MAX_ENTRIES)
        write_text_lf(repo / layout.local_path, local)
        checkpoint_path = layout.local_path
        checkpoint_kind = "Local checkpoint"

    if args.pack:
        pack_args = argparse.Namespace(
            repo=str(repo),
            task=None,
            changed=True,
            base=pack_base,
            output=str(repo / layout.pack_path),
            quiet=True,
            mode="work",
            max_areas=4,
            max_read_first=12,
            max_contracts=12,
            max_failure_modes=10,
        )
        build_pack(pack_args)

    if not args.quiet:
        print(f"{checkpoint_kind} updated at {normalize_path(checkpoint_path)}")
        print(f"HEAD: {snapshot.head}; dirty: {len(snapshot.dirty_files)} file(s); hash: {snapshot.diff_hash}")
        if args.pack:
            print(f"Context pack: {normalize_path(layout.pack_path)}")
            if pack_base:
                print(f"Context pack base: {pack_base}")
        if not args.publish:
            print("Note: local checkpoints are ignored by git. Use --publish when this handoff should be committed.")
        print('Next agent prompt: "Use $context-pack to continue from the current handoff."')
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo)
    had_context = (repo / layout.manifest_path).exists()
    transient = not had_context

    mode = "work"
    changed = False
    pack_reason = ""
    effective_task = args.task
    if (
        args.agent
        and had_context
        and not args.review
        and not args.base
        and not args.task
        and not args.changed
        and not snapshot.dirty_files
    ):
        effective_task = handoff_task(repo, layout)

    if args.review or args.base:
        mode = "review"
        changed = True
        pack_reason = "review"
        args.mode = mode
        review_base_inferred = maybe_infer_review_base(args, repo, snapshot)
    elif effective_task:
        review_base_inferred = False
        changed = args.changed or (transient and bool(snapshot.dirty_files))
        pack_reason = "task" if args.task else "handoff"
    elif args.changed or snapshot.dirty_files:
        review_base_inferred = False
        changed = True
        pack_reason = "changed files"
    else:
        review_base_inferred = False

    manifest, context_ref, inferred_context = resolve_pack_context(
        repo,
        layout,
        args,
        has_context_library=had_context,
    )
    context_transient = transient or (mode == "review" and inferred_context)
    repo_file_total = len(repo_files(repo)) if transient or not args.agent else 0

    small_repo_skip = transient and not args.output and repo_file_total <= SMALL_REPO_FILE_THRESHOLD
    pack_generated = bool(pack_reason) and not small_repo_skip
    max_areas = min(args.max_areas, AGENT_MAX_AREAS) if args.agent else args.max_areas
    selected: list[AreaSelection] = []
    pack_content = ""
    value_skip = False
    inline_transient = transient and not args.output and not args.quiet
    if args.output:
        output_path = Path(args.output)
    elif transient:
        output_path = transient_pack_path(repo, snapshot)
    else:
        output_path = repo / layout.pack_path
    if not output_path.is_absolute():
        output_path = repo / output_path

    if pack_generated:
        pack_args = argparse.Namespace(
            repo=str(repo),
            task=effective_task,
            changed=changed,
            base=args.base,
            output=str(output_path),
            quiet=True,
            mode=mode,
            max_areas=max_areas,
            max_read_first=args.max_read_first,
            max_contracts=args.max_contracts,
            max_failure_modes=args.max_failure_modes,
            text_budget=args.text_budget,
            agent=args.agent,
            manifest=manifest,
            layout=layout,
            transient=context_transient,
            context_ref=context_ref,
            inferred_context=inferred_context,
        )
        changed_files = resolve_changed_files(repo, snapshot, pack_args)
        matches = selected_area_matches(
            manifest,
            changed_files=changed_files,
            task=effective_task,
            repo=repo,
            context_ref=context_ref,
        )
        selected = matches[:max_areas]
        if inline_transient:
            pack_content = render_pack(
                repo,
                manifest,
                snapshot,
                selected,
                layout=layout,
                related_selections=matches[max_areas:],
                changed_files=changed_files,
                task=effective_task,
                mode=mode,
                include_text_budget=args.text_budget,
                transient=context_transient,
                context_ref=context_ref,
                inferred_context=inferred_context,
                compact=args.agent,
                include_evidence=args.agent,
                max_read_first=args.max_read_first,
                max_contracts=args.max_contracts,
                max_failure_modes=args.max_failure_modes,
            )
        else:
            result = build_pack(pack_args)
            if result != 0:
                return result
            pack_content = read_text(output_path)

    if args.agent and inline_transient and pack_generated and "## Evidence" not in pack_content:
        pack_generated = False
        value_skip = True

    if args.agent and not args.quiet:
        if pack_generated:
            print(pack_content.rstrip())
        elif small_repo_skip:
            print(f"Context Pack skipped: unconfigured repo has {repo_file_total} files; direct reading is cheaper.")
        elif value_skip:
            print("Context Pack skipped: transient routing found no selective source evidence; use one targeted search instead.")
        elif had_context:
            print(f"Read `{normalize_path(layout.current_path)}` and `{normalize_path(layout.index_path)}`.")
        else:
            print("Context Pack found no task, review, or changed-file signal.")
        return 0

    if not args.quiet:
        print(f"Context Pack Start for {repo}")
        print(f"Git: {'yes' if snapshot.is_git else 'no'}; branch: {snapshot.branch}; HEAD: {snapshot.head}")
        if had_context:
            print("Context library: ok")
        else:
            print("Context library: transient; no repository files were changed")
        print(f"Dirty files: {len(snapshot.dirty_files)}; diff hash: {snapshot.diff_hash}")
        print("")
        if pack_generated:
            location = "inline (not written)" if inline_transient else rel_to_repo(output_path, repo)
            print(f"Generated {mode} pack for {pack_reason}: {location}")
            if mode == "review" and args.base:
                suffix = " (auto)" if review_base_inferred else ""
                print(f"Review base: {args.base}{suffix}")
            print("Selected areas: " + (", ".join(item.area_id for item in selected) if selected else "none"))
            print_selection_reasons("Why selected:", selected)
            if repo_file_total:
                print(f"Scope reduction: start from {len(selected)} area(s) instead of scanning {repo_file_total} repo file(s)")
            text_budget = pack_text_budget_summary(output_path) if not inline_transient else None
            if text_budget:
                print(f"Approx text budget: {text_budget}")
            print("")
            if not inline_transient:
                print(f"Saved pack: {rel_to_repo(output_path, repo)}")
            print("Context pack follows; do not reopen it unless this output was truncated:")
            print("")
            print(pack_content.rstrip())
        else:
            if small_repo_skip:
                print(
                    f"No pack generated: this unconfigured repo has {repo_file_total} files; "
                    "broad reading is likely cheaper."
                )
            else:
                print("No pack generated: no task, review request, or pre-existing dirty files were found.")
            print("")
            if had_context:
                print("Read next:")
                print(f"- {normalize_path(layout.current_path)}")
                print(f"- {normalize_path(layout.index_path)}")
            elif not small_repo_skip:
                print("Run `context-pack setup --dry-run` only when persistent repo context is wanted.")
        print("")
        if had_context:
            print("End-of-work checkpoint: `context-pack checkpoint --pack`")
    return 0


def pattern_matches(path: str, pattern: str) -> bool:
    path = normalize_path(path)
    pattern = normalize_path(pattern)
    if pattern in {"*", "**"}:
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if "/" not in pattern and fnmatch.fnmatchcase(Path(path).name, pattern):
        return True
    return False


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(pattern_matches(path, pat) for pat in patterns or [])


def tokenize(value: str) -> set[str]:
    cleaned = []
    for ch in value.lower():
        cleaned.append(ch if ch.isalnum() else " ")
    return {
        part
        for part in "".join(cleaned).split()
        if (len(part) >= 3 or part == "ci" or (len(part) >= 2 and any(ord(ch) > 127 for ch in part)))
        and part not in TOKEN_STOP_WORDS
    }


def ordered_tokens(value: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return unique(
        part
        for part in cleaned.split()
        if (len(part) >= 3 or part == "ci" or (len(part) >= 2 and any(ord(ch) > 127 for ch in part)))
        and part not in TOKEN_STOP_WORDS
    )


def term_specificity(term: str) -> int:
    value = str(term).strip()
    if not value:
        return -100
    score = min(len(value), 24)
    if "_" in value or "::" in value or "." in value:
        score += 12
    if any(ch.isupper() for ch in value[1:]):
        score += 12
    if " " in value:
        score -= 6
    return score


def configured_search_terms(areas: dict[str, Any], selections: Iterable[AreaSelection]) -> list[str]:
    terms: list[str] = []
    for selection in selections:
        terms.extend(areas.get(selection.area_id, {}).get("search_terms", []) or [])
    values = unique_text(terms)
    indexed = list(enumerate(values))
    indexed.sort(key=lambda item: (0 if term_is_symbolic(item[1]) else 1, item[0]))
    return [term for _, term in indexed[:EVIDENCE_MAX_TERMS]]


def fallback_task_search_terms(task: str | None) -> list[str]:
    noise = TASK_ACTION_TOKENS | ROUTE_NOISE_TOKENS
    return [
        token
        for token in ordered_tokens(task or "")
        if token not in noise and (len(token) >= 4 or (len(token) >= 2 and any(ord(ch) > 127 for ch in token)))
    ][:EVIDENCE_MAX_TERMS]


def area_role(area_id: str, area: dict[str, Any]) -> str:
    explicit = str(area.get("kind", "")).strip().lower()
    if explicit:
        return explicit

    identity = tokenize(f"{area_id} {area.get('description', '')}")
    role_words = {
        "overview": {"overview", "orientation"},
        "tests": {"test", "tests", "spec", "specs", "qa"},
        "docs": {"doc", "docs", "documentation", "readme"},
        "automation": {"automation", "build", "ci", "deploy", "installer", "packaging", "release", "workflow"},
        "assets": {"asset", "assets", "audio", "image", "media", "static"},
        "source": {"api", "app", "application", "backend", "cli", "client", "core", "engine", "frontend", "library", "runtime", "server", "source"},
    }
    for role in ("overview", "tests", "docs", "automation", "assets", "source"):
        if identity & role_words[role]:
            return role

    paths = " ".join(str(item) for item in area.get("paths", []) or []).lower()
    if any(token in paths for token in ("tests/", "test/", "__tests__", "spec/", "*_test.")):
        return "tests"
    if any(token in paths for token in ("readme", "docs/", "*.md")):
        return "docs"
    if any(token in paths for token in (".github/", "workflows/", "pyproject.toml", "package.json", "makefile")):
        return "automation"
    if any(token in paths for token in ("assets/", "static/", "media/", "*.png", "*.jpg", "*.mp3")):
        return "assets"
    if area.get("paths"):
        return "source"
    return ""


def area_routing_text(
    repo: Path | None,
    area_id: str,
    area: dict[str, Any],
    context_ref: str | None = None,
) -> tuple[set[str], set[str]]:
    strong_parts = [area_id, area.get("kind", "")]
    strong_parts.extend(area.get("keywords", []) or [])
    strong_parts.extend(area.get("search_terms", []) or [])
    support_parts = [area.get("description", "")]
    for field in ("paths", "start_files"):
        support_parts.extend(area.get(field, []) or [])
    if repo is not None:
        if context_ref:
            markdown = area_doc_text(repo, area, context_ref)
        else:
            doc = area_doc_path(repo, area)
            markdown = read_text(doc) if doc.is_file() else ""
        if markdown:
            for heading in ("Read When", "Start With", "Search First"):
                support_parts.extend(extract_section_bullets(markdown, heading))
    return tokenize(" ".join(str(item) for item in strong_parts)), tokenize(" ".join(str(item) for item in support_parts))


def area_ids_for_role(areas: dict[str, Any], role: str) -> list[str]:
    return [area_id for area_id, area in areas.items() if area_role(area_id, area) == role]


def selected_area_matches(
    manifest: dict[str, Any],
    *,
    changed_files: list[str],
    task: str | None,
    repo: Path | None = None,
    context_ref: str | None = None,
) -> list[AreaSelection]:
    areas = manifest.get("areas") or {}
    selections: list[AreaSelection] = []
    task_tokens = tokenize(task or "")
    route_tokens = task_tokens - TASK_ACTION_TOKENS - ROUTE_NOISE_TOKENS

    for area_id, area in areas.items():
        score = 0
        reasons: list[str] = []
        matched_files: list[str] = []
        path_patterns = area.get("paths", []) or []
        stale_patterns = area.get("stale_if_paths", []) or []

        for path in changed_files:
            if matches_any(path, path_patterns):
                score += 10
                matched_files.append(path)
            elif matches_any(path, stale_patterns):
                score += 4
                matched_files.append(path)

        if matched_files:
            shown = ", ".join(unique(matched_files)[:3])
            more = len(unique(matched_files)) - 3
            reasons.append(f"changed files matched: {shown}" + (f" (+{more} more)" if more > 0 else ""))

        if route_tokens:
            strong_tokens, support_tokens = area_routing_text(repo, area_id, area, context_ref)
            strong_overlap = route_tokens & strong_tokens
            support_overlap = (route_tokens & support_tokens) - strong_overlap
            if strong_overlap or support_overlap:
                score += 8 * len(strong_overlap) + 3 * len(support_overlap)
                overlap = sorted(strong_overlap | support_overlap)
                reasons.append("task matched area metadata: " + ", ".join(overlap[:5]))

        if area_id == "overview" and score > 0:
            score = min(score, 3)

        if score > 0:
            selections.append(
                AreaSelection(
                    area_id=area_id,
                    score=score,
                    reasons=reasons or ["selected by context-pack"],
                    matched_files=unique(matched_files),
                )
            )

    selections.sort(key=lambda item: (-item.score, item.area_id))
    selected_ids = {item.area_id for item in selections}
    selected_roles = {area_role(item.area_id, areas[item.area_id]) for item in selections}
    failure_task = bool(task_tokens & FAILURE_TOKENS)

    roles_to_pair: list[str] = []
    if failure_task and "automation" in selected_roles:
        roles_to_pair.extend(["source", "tests"])
    elif failure_task and "tests" in selected_roles:
        roles_to_pair.append("source")
    if is_code_task_hint(task_tokens) and "assets" in selected_roles:
        roles_to_pair.append("source")

    for role in unique(roles_to_pair):
        candidates = area_ids_for_role(areas, role)
        if candidates:
            area_id = candidates[0]
            score = max((item.score for item in selections), default=2)
            if area_id in selected_ids:
                existing = next(item for item in selections if item.area_id == area_id)
                existing.score = max(existing.score, score)
                reason = f"paired {role} area for debugging"
                if reason not in existing.reasons:
                    existing.reasons.append(reason)
            else:
                selections.append(
                    AreaSelection(
                        area_id=area_id,
                        score=score,
                        reasons=[f"paired {role} area for debugging"],
                        matched_files=[],
                    )
                )
                selected_ids.add(area_id)
    selections.sort(key=lambda item: (-item.score, item.area_id))

    if not selections and "overview" in areas:
        source_ids = area_ids_for_role(areas, "source")[:1]
        test_ids = area_ids_for_role(areas, "tests")[:1]
        starter_ids = unique(source_ids + test_ids)
        if source_ids and is_code_task_hint(task_tokens):
            return [
                AreaSelection(
                    area_id=area_id,
                    score=2,
                    reasons=["starter code area for unclassified task"],
                    matched_files=[],
                )
                for area_id in starter_ids
            ]
        selections.append(
            AreaSelection(
                area_id="overview",
                score=1,
                reasons=["fallback orientation"],
                matched_files=[],
            )
        )
    return selections


def is_code_task_hint(task_tokens: set[str]) -> bool:
    return bool(task_tokens & CODE_TASK_TOKENS)


def selected_areas(
    manifest: dict[str, Any],
    *,
    changed_files: list[str],
    task: str | None,
    repo: Path | None = None,
) -> list[str]:
    return [item.area_id for item in selected_area_matches(manifest, changed_files=changed_files, task=task, repo=repo)]


def selection_reason(item: AreaSelection) -> str:
    return "; ".join(item.reasons) if item.reasons else "selected by context-pack"


def print_selection_reasons(title: str, selections: list[AreaSelection]) -> None:
    if not selections:
        return
    print(title)
    for item in selections:
        print(f"- {item.area_id}: {selection_reason(item)}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def extract_frontmatter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---\n"):
        return {}
    end = markdown.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in markdown[4:end].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def extract_section_bullets(markdown: str, heading: str) -> list[str]:
    target = "## " + heading.lower()
    lines = markdown.splitlines()
    in_section = False
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == target:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def extract_section_items(markdown: str, heading: str) -> list[str]:
    target = "## " + heading.lower()
    in_section = False
    items: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.lower() == target:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
            continue
        prefix, separator, value = stripped.partition(". ")
        if separator and prefix.isdigit() and value:
            items.append(value.strip())
    return items


def handoff_task(repo: Path, layout: ContextLayout) -> str | None:
    text = read_text(repo / layout.current_path)
    values = extract_section_items(text, "Active Goal") + extract_section_items(text, "Next Actions")
    placeholders = (
        "keep this short",
        "generate or consult a context pack",
        "not recorded",
    )
    useful = [
        " ".join(value.split())
        for value in values
        if value and not any(marker in value.casefold() for marker in placeholders)
    ]
    if not useful:
        return None
    return " ".join(unique_text(useful)[:3])[:600].rstrip()


def unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def repo_files(repo: Path) -> list[str]:
    files = git_path_list(repo, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    if files is not None:
        return files

    ignored_parts = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    ignored_prefixes = {
        ".context-pack/packs/",
        ".context-pack/tmp/",
        ".context-pack/local/",
        ".codex/packs/",
        ".codex/context/tmp/",
    }
    out: list[str] = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel = rel_to_repo(path, repo)
        parts = set(Path(rel).parts)
        if parts & ignored_parts:
            continue
        if any(rel.startswith(prefix) for prefix in ignored_prefixes):
            continue
        out.append(rel)
    return sorted(out)


def readable_text_chars(path: Path) -> int | None:
    if path.suffix.lower() in TEXT_BUDGET_BINARY_SUFFIXES:
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if not size or size > TEXT_BUDGET_MAX_FILE_BYTES:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return len(data.decode("utf-8"))
    except UnicodeDecodeError:
        return None


def text_budget_for_files(repo: Path, files: Iterable[str]) -> TextBudget:
    budget = TextBudget()
    for rel in unique(files):
        chars = readable_text_chars(repo / rel)
        if chars is None:
            budget.skipped += 1
            continue
        budget.files += 1
        budget.chars += chars
    return budget


def files_for_read_first_entries(repo: Path, entries: Iterable[str], repo_file_list: list[str]) -> list[str]:
    repo_file_set = set(repo_file_list)
    out: list[str] = []
    for raw in entries:
        entry = normalize_path(raw)
        if not entry:
            continue
        path = repo / entry
        if any(ch in entry for ch in "*?["):
            try:
                matches = [rel_to_repo(item, repo) for item in repo.glob(entry) if item.is_file()]
            except ValueError:
                matches = []
            out.extend(item for item in matches if item in repo_file_set)
            continue
        if path.is_file() and entry in repo_file_set:
            out.append(entry)
            continue
        if path.is_dir():
            prefix = entry.rstrip("/") + "/"
            out.extend(item for item in repo_file_list if item.startswith(prefix))
    return unique(out)


def files_for_evidence_entries(repo: Path, entries: Iterable[str], repo_file_list: list[str]) -> list[str]:
    out: list[str] = []
    for raw in entries:
        entry = normalize_path(raw)
        if not entry:
            continue
        path = repo / entry
        if path.is_file():
            out.append(entry)
        elif path.is_dir():
            prefix = entry.rstrip("/") + "/"
            out.extend(item for item in repo_file_list if item.startswith(prefix))
        else:
            out.extend(item for item in repo_file_list if pattern_matches(item, entry))
    return unique(out)


def is_generated_context_path(path: str) -> bool:
    normalized = normalize_path(path)
    agent_docs = {path_text(item) for item in AGENT_DOC_TARGETS.values()}
    return (
        normalized.startswith(".context-pack/")
        or normalized.startswith(".codex/")
        or normalized in agent_docs
    )


def read_evidence_lines(path: Path) -> tuple[list[str], int] | None:
    if path.suffix.lower() in TEXT_BUDGET_BINARY_SUFFIXES:
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if not size or size > EVIDENCE_MAX_FILE_BYTES:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text.splitlines(), len(data)


def term_is_symbolic(term: str) -> bool:
    value = str(term).strip()
    return (
        "_" in value
        or "::" in value
        or "." in value
        or any(ch.isupper() for ch in value[1:])
    )


def format_evidence_window(lines: list[str], hit_line: int, max_chars: int) -> tuple[int, int, str]:
    start = max(0, hit_line - EVIDENCE_CONTEXT_BEFORE)
    end = min(len(lines), hit_line + EVIDENCE_CONTEXT_AFTER + 1)

    def render(current_start: int, current_end: int) -> str:
        width = len(str(current_end))
        rendered: list[str] = []
        for index in range(current_start, current_end):
            value = lines[index].replace("\t", "    ")
            if len(value) > EVIDENCE_MAX_LINE_CHARS:
                value = value[: EVIDENCE_MAX_LINE_CHARS - 3] + "..."
            rendered.append(f"{index + 1:>{width}}: {value}")
        return "\n".join(rendered)

    text = render(start, end)
    while len(text) > max_chars and end - start > 7:
        if end - hit_line > 7:
            end -= 1
        elif hit_line - start > 2:
            start += 1
        else:
            break
        text = render(start, end)
    return start + 1, end, text


def collect_evidence(
    repo: Path,
    areas: dict[str, Any],
    selections: list[AreaSelection],
    *,
    changed_files: list[str],
    task: str | None,
) -> EvidenceResult:
    configured_terms = configured_search_terms(areas, selections)
    fallback_terms = fallback_task_search_terms(task)
    if not fallback_terms and changed_files:
        fallback_terms = unique_text(
            token
            for path in changed_files
            for token in ordered_tokens(Path(path).stem)
            if len(token) >= 4
        )[:EVIDENCE_MAX_TERMS]
    repo_file_list = repo_files(repo)

    preferred_entries: list[str] = list(changed_files)
    fallback_entries: list[str] = []
    for selection in selections:
        area = areas.get(selection.area_id, {})
        preferred_entries.extend(area.get("start_files", []) or [])
        fallback_entries.extend(area.get("paths", []) or [])
    candidate_files = files_for_evidence_entries(repo, preferred_entries, repo_file_list)
    if not candidate_files:
        candidate_files = files_for_evidence_entries(repo, fallback_entries, repo_file_list)
    candidate_files = [
        path
        for path in candidate_files
        if not is_generated_context_path(path)
    ]
    changed_set = set(changed_files)
    candidate_files.sort(key=lambda path: (0 if path in changed_set else 1))

    records: list[tuple[str, list[str]]] = []
    scanned_bytes = 0
    for rel in candidate_files[:EVIDENCE_MAX_FILES]:
        result = read_evidence_lines(repo / rel)
        if result is None:
            continue
        lines, size = result
        if scanned_bytes + size > EVIDENCE_MAX_SCAN_BYTES:
            break
        records.append((rel, lines))
        scanned_bytes += size

    def find_hits(terms: list[str], *, configured: bool) -> tuple[list[str], list[tuple[int, str, int, int]]]:
        if not terms:
            return [], []
        hit_counts = {term: 0 for term in terms}
        file_counts = {term: 0 for term in terms}
        raw_hits: dict[str, list[tuple[int, int]]] = {term: [] for term in terms}
        folded_terms = {term: term.casefold() for term in terms}

        for file_index, (_, lines) in enumerate(records):
            seen_in_file: set[str] = set()
            for line_index, line in enumerate(lines):
                folded = line.casefold()
                for term in terms:
                    if folded_terms[term] not in folded:
                        continue
                    hit_counts[term] += 1
                    seen_in_file.add(term)
                    if len(raw_hits[term]) < EVIDENCE_BROAD_HIT_LIMIT + 1:
                        raw_hits[term].append((file_index, line_index))
            for term in seen_in_file:
                file_counts[term] += 1

        accepted: list[str] = []
        for term in terms:
            hits = hit_counts[term]
            if not hits:
                continue
            if term_is_symbolic(term):
                accepted.append(term)
            elif configured and hits <= EVIDENCE_BROAD_HIT_LIMIT:
                accepted.append(term)
            elif not configured and hits <= 12 and file_counts[term] <= 4:
                accepted.append(term)

        candidates: list[tuple[int, str, int, int]] = []
        task_tokens = tokenize(task or "")
        for term_index, term in enumerate(accepted):
            for file_index, line_index in raw_hits[term]:
                rel, lines = records[file_index]
                window_start = max(0, line_index - EVIDENCE_CONTEXT_BEFORE)
                window_end = min(len(lines), line_index + EVIDENCE_CONTEXT_AFTER + 1)
                window = "\n".join(lines[window_start:window_end])
                overlap = len(task_tokens & tokenize(window))
                line = lines[line_index].casefold()
                definition = (
                    "def " in line
                    or "function" in line
                    or "class " in line
                    or f"{term.casefold()}:" in line
                )
                score = 120 - (term_index * 8)
                score += term_specificity(term)
                score += min(overlap, 6) * 10
                score += 24 if definition else 0
                score += 30 if rel in changed_set else 0
                score -= min(hit_counts[term], 20)
                score -= min(file_index, 20)
                candidates.append((score, term, file_index, line_index))
        candidates.sort(key=lambda item: (-item[0], item[2], item[3], item[1]))
        return accepted, candidates

    evidence_source = "configured"
    accepted_terms, candidates = find_hits(configured_terms, configured=True)
    if not candidates and fallback_terms:
        evidence_source = "fallback"
        accepted_terms, candidates = find_hits(fallback_terms, configured=False)

    snippets: list[EvidenceSnippet] = []
    snippet_fingerprints: set[str] = set()
    remaining_chars = EVIDENCE_MAX_CHARS
    for score, term, file_index, line_index in candidates:
        if len(snippets) >= EVIDENCE_MAX_SNIPPETS or remaining_chars < 500:
            break
        rel, lines = records[file_index]
        if any(
            snippet.path == rel
            and abs(line_index + 1 - ((snippet.start_line + snippet.end_line) // 2)) <= EVIDENCE_CLUSTER_DISTANCE
            for snippet in snippets
        ):
            continue
        slots_left = EVIDENCE_MAX_SNIPPETS - len(snippets)
        snippet_budget = max(500, remaining_chars // slots_left)
        start_line, end_line, text = format_evidence_window(lines, line_index, snippet_budget)
        fingerprint = "\n".join(line.rstrip() for line in lines[start_line - 1 : end_line]).strip()
        if fingerprint in snippet_fingerprints:
            continue
        snippets.append(
            EvidenceSnippet(
                path=rel,
                start_line=start_line,
                end_line=end_line,
                term=term,
                text=text,
            )
        )
        snippet_fingerprints.add(fingerprint)
        remaining_chars -= len(text)

    selected_terms = unique([snippet.term for snippet in snippets] + accepted_terms)[:EVIDENCE_MAX_TERMS]
    if not selected_terms:
        selected_terms = configured_terms or fallback_terms
    if snippets and evidence_source == "configured":
        confidence = "strong"
        reason = "configured symbols matched bounded current-source regions"
    elif snippets:
        confidence = "candidate"
        reason = "task terms matched bounded current-source regions"
    else:
        confidence = "none"
        reason = "no selective current-source match was found within the evidence budget"
    return EvidenceResult(
        terms=selected_terms,
        snippets=snippets,
        confidence=confidence,
        reason=reason,
    )


def estimated_tokens(chars: int) -> int:
    if chars <= 0:
        return 0
    return max(1, (chars + 3) // 4)


def format_token_count(tokens: int) -> str:
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k"
    return str(tokens)


def pack_text_budget_summary(pack_path: Path) -> str:
    read_first = ""
    repo_text = ""
    for line in read_text(pack_path).splitlines():
        if line.startswith("- Approx Read First text: "):
            read_first = line.split(": ", 1)[1]
        elif line.startswith("- Approx repo text: "):
            repo_text = line.split(": ", 1)[1]
    if read_first and repo_text:
        return f"Read First {read_first}; repo {repo_text}"
    if read_first:
        return f"Read First {read_first}"
    return ""


def percent(part: int, whole: int) -> int:
    if part <= 0 or whole <= 0:
        return 0
    return min(100, max(1, round((part / whole) * 100)))


def similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def unique_text(items: Iterable[str]) -> list[str]:
    seen_exact: set[str] = set()
    seen_tokens: list[set[str]] = []
    out: list[str] = []
    for raw in items:
        item = " ".join(str(raw).strip().split())
        if not item:
            continue
        key = item.casefold().strip(". ")
        if key in seen_exact:
            continue
        tokens = tokenize(key)
        if tokens and any(similarity(tokens, previous) >= 0.68 for previous in seen_tokens):
            continue
        seen_exact.add(key)
        seen_tokens.append(tokens)
        out.append(item)
    return out


def extend_distinct_text(target: list[str], items: Iterable[str], threshold: float = 0.55) -> None:
    token_sets: list[set[str]] = []
    for item in target:
        tokens = tokenize(item)
        if tokens:
            token_sets.append(tokens)
    exact = {" ".join(str(item).strip().split()).casefold() for item in target}
    for raw in items:
        item = " ".join(str(raw).strip().split())
        if not item or item.casefold() in exact:
            continue
        tokens = tokenize(item)
        if tokens and any(similarity(tokens, previous) >= threshold for previous in token_sets):
            continue
        target.append(item)
        exact.add(item.casefold())
        if tokens:
            token_sets.append(tokens)


def split_limited(items: Iterable[str], limit: int | None) -> tuple[list[str], list[str]]:
    values = unique_text(items)
    if limit is None or limit < 1:
        return values, []
    return values[:limit], values[limit:]


def rank_task_text(items: Iterable[str], task: str | None, limit: int) -> list[str]:
    values = unique_text(items)
    if limit < 1:
        return []
    task_tokens = tokenize(task or "") - TASK_ACTION_TOKENS - ROUTE_NOISE_TOKENS
    scored: list[tuple[int, int, str]] = []
    for index, item in enumerate(values):
        overlap = task_tokens & tokenize(item)
        scored.append((len(overlap), index, item))
    if any(score for score, _, _ in scored):
        scored.sort(key=lambda item: (-item[0], item[1]))
    return [item for _, _, item in scored[:limit]]


def verification_commands(items: Iterable[str], task: str | None, limit: int) -> list[str]:
    executables = {
        "cargo",
        "dotnet",
        "git",
        "go",
        "gradle",
        "make",
        "mvn",
        "node",
        "npm",
        "npx",
        "pnpm",
        "pytest",
        "python",
        "python3",
        "ruby",
        "uv",
        "yarn",
    }
    commands: list[str] = []
    for item in unique_text(items):
        parts = str(item).strip().split(maxsplit=1)
        if parts and parts[0].lower() in executables:
            commands.append(item)
    return rank_task_text(commands, task, limit)


def area_doc_path(repo: Path, area: dict[str, Any]) -> Path:
    return repo / normalize_path(area.get("doc", ""))


def area_doc_text(repo: Path, area: dict[str, Any], context_ref: str | None = None) -> str:
    rel = normalize_path(area.get("doc", ""))
    if not rel:
        return ""
    if context_ref:
        return git_file_text(repo, context_ref, rel) or ""
    return read_text(repo / rel)


def context_provenance(mode: str, context_ref: str | None, inferred_context: bool) -> str:
    if mode == "review" and context_ref:
        return f"Notes and routing: review base `{context_ref[:12]}`; Evidence: current source under review."
    if mode == "review" and inferred_context:
        return "Notes and routing: deterministic inference only; branch-authored context docs ignored; Evidence: current source under review."
    if inferred_context:
        return "Notes and routing: transient deterministic inference; Evidence: current source."
    return "Notes and routing: tracked working-tree context; Evidence: current source."


def stale_warning(repo: Path, snapshot: Snapshot, area_id: str, area: dict[str, Any], changed_files: list[str]) -> str | None:
    doc = area_doc_path(repo, area)
    if not doc.exists():
        return f"{area_id}: area doc missing at {rel_to_repo(doc, repo)}"
    text = read_text(doc)
    frontmatter = extract_frontmatter(text)
    status = frontmatter.get("status", "")
    reviewed = frontmatter.get("last_reviewed_head", "")
    if status in {"stale", "review_needed", "superseded"}:
        return f"{area_id}: status is {status}"
    if reviewed and reviewed not in {"unknown", snapshot.head} and snapshot.head not in {"unknown", "not-a-git-repo"}:
        patterns = (area.get("paths", []) or []) + (area.get("stale_if_paths", []) or [])
        if any(matches_any(path, patterns) for path in changed_files):
            return f"{area_id}: reviewed at {reviewed}, current HEAD is {snapshot.head}"
    return None


def concise_text(value: str, limit: int = 240) -> str:
    text = " ".join(str(value).strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def render_agent_pack(
    snapshot: Snapshot,
    selections: list[AreaSelection],
    *,
    search_terms: list[str],
    search_scopes: list[str],
    changed_files: list[str],
    contracts: list[str],
    failures: list[str],
    tests: list[str],
    warnings: list[str],
    evidence: EvidenceResult | None,
    provenance: str,
) -> str:
    visible_scopes = unique(search_scopes)[:AGENT_MAX_SCOPES]
    visible_changed = unique(changed_files)[:8]
    visible_contracts = [concise_text(item) for item in contracts]
    visible_failures = [concise_text(item) for item in failures]
    visible_tests = [concise_text(item) for item in tests]
    visible_warnings = [concise_text(item) for item in unique(warnings)[:3]]
    snippets = list(evidence.snippets if evidence else [])

    def build() -> str:
        terms = evidence.terms if evidence and evidence.terms else search_terms
        lines = ["# Context Pack", "", "## Route"]
        for selection in selections:
            reason = concise_text(selection.reasons[0] if selection.reasons else "selected by context-pack", 180)
            lines.append(f"- `{selection.area_id}`: {reason}")
        if not selections:
            lines.append("- No area selected")
        if terms:
            lines.append("- Search: " + ", ".join(f"`{term}`" for term in terms[:EVIDENCE_MAX_TERMS]))
        if visible_scopes:
            lines.append("- Scopes: " + ", ".join(f"`{scope}`" for scope in visible_scopes))
        if evidence:
            lines.append(f"- Evidence confidence: `{evidence.confidence}` ({evidence.reason})")

        if snippets:
            if evidence and evidence.confidence == "strong":
                evidence_rule = "Configured symbols matched current source. Edit directly if the cause is visible; do not reopen these ranges."
            else:
                evidence_rule = "Task terms produced candidate current-source regions. Verify before editing and expand only if needed."
            lines.extend(
                [
                    "",
                    "## Evidence",
                    f"- {evidence_rule}",
                ]
            )
            for snippet in snippets:
                lines.extend(
                    [
                        f"### `{snippet.path}:{snippet.start_line}-{snippet.end_line}` (`{snippet.term}`)",
                        "````text",
                        snippet.text,
                        "````",
                    ]
                )

        if visible_changed:
            lines.extend(["", "## Changed"])
            lines.extend(f"- `{path}`" for path in visible_changed)
            remaining = len(unique(changed_files)) - len(visible_changed)
            if remaining > 0:
                lines.append(f"- {remaining} more changed file(s) omitted")

        if visible_contracts or visible_failures:
            lines.extend(["", "## Guardrails"])
            lines.extend(f"- Contract: {item}" for item in visible_contracts)
            lines.extend(f"- Watch: {item}" for item in visible_failures)

        if visible_tests:
            lines.extend(["", "## Verify"])
            lines.extend(f"- `{item}`" for item in visible_tests)

        if visible_warnings:
            lines.extend(["", "## Stale"])
            lines.extend(f"- {item}" for item in visible_warnings)

        lines.extend(
            [
                "",
                "## State",
                (
                    f"- Repo: `{snapshot.repo_root}`; branch: `{snapshot.branch}`; "
                    f"HEAD: `{snapshot.head[:12]}`; dirty: {len(snapshot.dirty_files)}; hash: `{snapshot.diff_hash}`"
                ),
                f"- {provenance}",
                (
                    "- Use the next tool call for editing or verification when strong Evidence is sufficient; otherwise expand with a targeted search."
                    if evidence and evidence.confidence == "strong" and snippets
                    else "- Expand with one targeted search before editing when Evidence is candidate or absent."
                ),
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    content = build()
    while len(content) > AGENT_PACK_MAX_CHARS and len(snippets) > 1:
        snippets.pop()
        content = build()
    while len(content) > AGENT_PACK_MAX_CHARS and visible_failures:
        visible_failures.pop()
        content = build()
    while len(content) > AGENT_PACK_MAX_CHARS and visible_contracts:
        visible_contracts.pop()
        content = build()
    return content


def render_pack(
    repo: Path,
    manifest: dict[str, Any],
    snapshot: Snapshot,
    selections: list[AreaSelection],
    *,
    layout: ContextLayout | None = None,
    related_selections: list[AreaSelection] | None = None,
    changed_files: list[str],
    task: str | None,
    mode: str,
    include_text_budget: bool = False,
    transient: bool = False,
    context_ref: str | None = None,
    inferred_context: bool = False,
    compact: bool = False,
    include_evidence: bool = False,
    max_read_first: int = 12,
    max_contracts: int = 12,
    max_failure_modes: int = 10,
) -> str:
    layout = layout or resolve_layout(repo)
    areas = manifest.get("areas") or {}
    related_selections = related_selections or []
    changed = changed_files
    search_scopes: list[str] = []
    read_first: list[str] = []
    read_later: list[str] = []
    tests: list[str] = []
    verify: list[str] = []
    contracts: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    def collect_area(selection: AreaSelection, *, primary: bool) -> None:
        area = areas.get(selection.area_id, {})
        target = read_first if primary else read_later
        start_files = area.get("start_files", []) or []
        for start_file in start_files:
            is_scope = any(ch in start_file for ch in "*?[") or (repo / start_file).is_dir()
            if primary and (task or is_scope):
                search_scopes.append(start_file)
            else:
                target.append(start_file)
        target.extend(path for path in changed if matches_any(path, area.get("paths", []) or []))
        if primary:
            tests.extend(area.get("tests", []) or [])
            verify.extend(area.get("verify", []) or [])
            area_contracts = area.get("contracts", []) or []
            area_failures = area.get("failure_modes", []) or []
            contracts.extend(area_contracts)
            failures.extend(area_failures)

        text = area_doc_text(repo, area, context_ref)
        if primary:
            extend_distinct_text(contracts, extract_section_bullets(text, "Contracts"))
            extend_distinct_text(failures, extract_section_bullets(text, "Common Failure Modes"))

        if not transient and not context_ref:
            warning = stale_warning(repo, snapshot, selection.area_id, area, changed)
            if warning:
                warnings.append(warning)

    for selection in selections:
        collect_area(selection, primary=True)
    if not compact:
        for selection in related_selections:
            collect_area(selection, primary=False)

    search_terms = configured_search_terms(areas, selections)
    if not search_terms:
        search_terms = fallback_task_search_terms(task)

    search_scopes = unique(search_scopes)
    search_terms = unique_text(search_terms)[:EVIDENCE_MAX_TERMS]

    if compact:
        evidence = (
            collect_evidence(
                repo,
                areas,
                selections,
                changed_files=changed,
                task=task,
            )
            if include_evidence and (task or changed)
            else None
        )
        return render_agent_pack(
            snapshot,
            selections,
            search_terms=search_terms,
            search_scopes=search_scopes,
            changed_files=changed,
            contracts=rank_task_text(contracts, task, min(max_contracts, AGENT_MAX_CONTRACTS)),
            failures=rank_task_text(failures, task, min(max_failure_modes, AGENT_MAX_FAILURE_MODES)),
            tests=(
                rank_task_text(verify, task, AGENT_MAX_TESTS)
                if verify
                else verification_commands(tests, task, AGENT_MAX_TESTS)
            ),
            warnings=warnings,
            evidence=evidence,
            provenance=context_provenance(mode, context_ref, inferred_context),
        )

    read_first_unique = unique(read_first)
    read_first_visible = read_first_unique[:max_read_first]
    read_later = unique(read_first_unique[max_read_first:] + read_later)
    contracts_visible, contracts_hidden = split_limited(contracts, max_contracts)
    failures_visible, failures_hidden = split_limited(failures, max_failure_modes)
    repo_file_list = repo_files(repo)
    repo_file_total = len(repo_file_list)
    read_first_total = len(read_first_visible)
    area_total = len(areas)
    read_first_ratio = percent(read_first_total, repo_file_total) if repo_file_total else 0
    repo_budget = TextBudget()
    read_first_budget = TextBudget()
    repo_tokens = 0
    read_first_tokens = 0
    budget_ratio = 0
    if include_text_budget:
        repo_budget = text_budget_for_files(repo, repo_file_list)
        read_first_files = files_for_read_first_entries(repo, read_first_visible, repo_file_list)
        read_first_budget = text_budget_for_files(repo, read_first_files)
        repo_tokens = estimated_tokens(repo_budget.chars)
        read_first_tokens = estimated_tokens(read_first_budget.chars)
        budget_ratio = round((read_first_tokens / repo_tokens) * 100) if repo_tokens and read_first_tokens else 0

    def path_line(item: str) -> str:
        is_glob = any(ch in item for ch in "*?[")
        suffix = "" if is_glob or (item and (repo / item).exists()) else " (missing)"
        return f"- `{item}`{suffix}"

    task_label = task if task else ("changed files" if changed else "general orientation")
    lines = [
        "# Context Pack",
        "",
        f"Generated at: {snapshot.timestamp}",
        f"Mode: {mode}",
        f"Task: {task_label}",
        "",
        "## State Fingerprint",
        f"- Repo root: {snapshot.repo_root}",
        f"- Git repo: {'yes' if snapshot.is_git else 'no'}",
        f"- Branch: {snapshot.branch}",
        f"- HEAD: {snapshot.head}",
        f"- Dirty diff hash: {snapshot.diff_hash}",
        "",
        "## Context Provenance",
        f"- {context_provenance(mode, context_ref, inferred_context)}",
        "",
        "## Scope Reduction",
        f"- Repo files considered: {repo_file_total if repo_file_total else 'unknown'}",
        f"- Primary areas selected: {len(selections)} of {area_total}",
        f"- Search scopes: {len(search_scopes)}",
        f"- Read First entries: {read_first_total}" + (f" (~{read_first_ratio}% of repo files)" if repo_file_total else ""),
        f"- Changed files in scope: {len(changed)}",
    ]
    if include_text_budget:
        lines.extend(
            [
                (
                    f"- Approx Read First text: ~{format_token_count(read_first_tokens)} tokens "
                    f"from {read_first_budget.files} file(s)"
                    + (f" (~{budget_ratio}% of repo text)" if repo_tokens else "")
                ),
                f"- Approx repo text: ~{format_token_count(repo_tokens)} tokens from {repo_budget.files} text file(s)",
                "- Token estimates use chars/4 and skip binary, unreadable, ignored, and >1 MB files.",
            ]
        )
    lines.extend(["", "## Selected Areas"])
    for item in selections:
        reason = "; ".join(item.reasons)
        lines.append(f"- {item.area_id} (score {item.score}): {reason}")
    if not selections:
        lines.append("- none")

    if related_selections:
        lines.extend(["", "## Related Areas"])
        for item in related_selections:
            reason = "; ".join(item.reasons)
            lines.append(f"- {item.area_id} (score {item.score}): {reason}")

    lines.extend(["", "## Search First"])
    if search_terms:
        lines.append("- Terms/symbols: " + ", ".join(f"`{item}`" for item in search_terms))
    else:
        lines.append("- Terms/symbols: use the task's most distinctive identifiers")
    if search_scopes:
        lines.append("- Scopes:")
        for item in search_scopes[:12]:
            lines.append(f"  - `{item}`")
        if len(search_scopes) > 12:
            lines.append(f"  - ... {len(search_scopes) - 12} more scope(s) omitted")
    else:
        lines.append("- Scopes: selected area paths")
    lines.append("- Search first, then inspect only matching regions. Do not bulk-read a directory, glob, or large file.")

    lines.extend(["", "## Read First"])
    for item in read_first_visible:
        lines.append(path_line(item))
    if not read_first_visible:
        lines.append("- none")

    if read_later:
        lines.extend(["", "## Read Later"])
        for item in read_later[:20]:
            lines.append(path_line(item))
        if len(read_later) > 20:
            lines.append(f"- ... {len(read_later) - 20} more item(s) omitted")

    lines.extend(["", "## Changed Files"])
    if changed:
        for item in changed:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Contracts To Check"])
    for item in contracts_visible:
        lines.append(f"- {item}")
    if contracts_hidden:
        lines.append(f"- ... {len(contracts_hidden)} more contract(s) omitted; inspect area docs if needed")
    if not contracts_visible:
        lines.append("- none recorded")

    lines.extend(["", "## Common Failure Modes"])
    for item in failures_visible:
        lines.append(f"- {item}")
    if failures_hidden:
        lines.append(f"- ... {len(failures_hidden)} more failure mode(s) omitted; inspect area docs if needed")
    if not failures_visible:
        lines.append("- none recorded")

    lines.extend(["", "## Verify"])
    for item in unique(verify):
        lines.append(f"- `{item}`")
    if not verify:
        lines.append("- none recorded")

    lines.extend(["", "## Tests"])
    for item in unique(tests):
        lines.append(f"- `{item}`")
    if not tests:
        lines.append("- none recorded")

    lines.extend(["", "## Stale Warnings"])
    if warnings:
        for item in unique(warnings):
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Operating Rule",
            "- Follow Search First with targeted queries and bounded snippets before opening full files.",
            "- Treat globs and directories as search scopes, never as instructions to bulk-read their contents.",
            "- Verify behavior in source code before editing or reviewing.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_pack(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = getattr(args, "layout", None) or resolve_layout(repo, for_write=True)
    if getattr(args, "mode", "work") == "review":
        maybe_infer_review_base(args, repo, snapshot)
    has_context_library = (repo / layout.manifest_path).exists()
    manifest = getattr(args, "manifest", None)
    context_ref = getattr(args, "context_ref", None)
    inferred_context = bool(getattr(args, "inferred_context", False))
    if manifest is None:
        manifest, context_ref, inferred_context = resolve_pack_context(
            repo,
            layout,
            args,
            has_context_library=has_context_library,
        )
    transient = bool(getattr(args, "transient", False)) or (
        getattr(args, "mode", "work") == "review" and inferred_context
    )
    changed = resolve_changed_files(repo, snapshot, args)
    matches = selected_area_matches(
        manifest,
        changed_files=changed,
        task=args.task,
        repo=repo,
        context_ref=context_ref,
    )
    max_areas = getattr(args, "max_areas", 4) or len(matches)
    primary = matches[:max_areas]
    related = matches[max_areas:]
    area_ids = [item.area_id for item in primary]
    content = render_pack(
        repo,
        manifest,
        snapshot,
        primary,
        layout=layout,
        related_selections=related,
        changed_files=changed,
        task=args.task,
        mode=args.mode,
        include_text_budget=bool(getattr(args, "text_budget", False)),
        transient=transient,
        context_ref=context_ref,
        inferred_context=inferred_context,
        compact=bool(getattr(args, "agent", False)),
        include_evidence=bool(getattr(args, "agent", False)),
        max_read_first=getattr(args, "max_read_first", 12),
        max_contracts=getattr(args, "max_contracts", 12),
        max_failure_modes=getattr(args, "max_failure_modes", 10),
    )
    output = Path(args.output) if args.output else repo / layout.pack_path
    if not output.is_absolute():
        output = repo / output
    output.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(output, content)
    if not args.quiet:
        print(f"Context pack written to {output}")
        print("Selected areas: " + (", ".join(area_ids) if area_ids else "none"))
        if related:
            print("Related areas: " + ", ".join(item.area_id for item in related))
        print("")
        print("Read next:")
        print(f"- {rel_to_repo(output, repo)}")
        for area_id in area_ids[:5]:
            area = (manifest.get("areas") or {}).get(area_id, {})
            doc = area.get("doc")
            if doc:
                print(f"- {doc}")
    return 0


def pack_scope_value(pack_markdown: str, label: str) -> str:
    prefix = f"- {label}: "
    for line in pack_markdown.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return ""


def cmd_measure(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo)
    has_context_library = (repo / layout.manifest_path).exists()
    args.mode = "review" if getattr(args, "review", False) or getattr(args, "base", None) else "work"
    review_base_inferred = maybe_infer_review_base(args, repo, snapshot) if args.mode == "review" else False
    manifest, context_ref, inferred_context = resolve_pack_context(
        repo,
        layout,
        args,
        has_context_library=has_context_library,
    )
    changed = resolve_changed_files(repo, snapshot, args)
    matches = selected_area_matches(
        manifest,
        changed_files=changed,
        task=args.task,
        repo=repo,
        context_ref=context_ref,
    )
    max_areas = getattr(args, "max_areas", 4) or len(matches)
    primary = matches[:max_areas]
    related = matches[max_areas:]
    content = render_pack(
        repo,
        manifest,
        snapshot,
        primary,
        layout=layout,
        related_selections=related,
        changed_files=changed,
        task=args.task,
        mode=args.mode,
        include_text_budget=True,
        transient=not has_context_library or (args.mode == "review" and inferred_context),
        context_ref=context_ref,
        inferred_context=inferred_context,
        max_read_first=getattr(args, "max_read_first", 12),
        max_contracts=getattr(args, "max_contracts", 12),
        max_failure_modes=getattr(args, "max_failure_modes", 10),
    )
    if not args.quiet:
        repo_files_considered = pack_scope_value(content, "Repo files considered")
        read_first_entries = pack_scope_value(content, "Read First entries")
        changed_in_scope = pack_scope_value(content, "Changed files in scope")
        read_first_text = pack_scope_value(content, "Approx Read First text")
        repo_text = pack_scope_value(content, "Approx repo text")
        print(f"Context Pack Measure for {repo}")
        print(f"Git: {'yes' if snapshot.is_git else 'no'}; branch: {snapshot.branch}; HEAD: {snapshot.head[:12]}")
        if has_context_library:
            print("Context library: ok")
        else:
            print("Context library: not installed; using inferred areas for measurement")
        print("Mode: " + args.mode)
        if args.mode == "review" and args.base:
            suffix = " (auto)" if review_base_inferred else ""
            print(f"Review base: {args.base}{suffix}")
        if args.task:
            print(f"Task: {args.task}")
        print("No files written.")
        print("")
        print("Selected areas: " + (", ".join(item.area_id for item in primary) if primary else "none"))
        print_selection_reasons("Why selected:", primary)
        if related:
            print("Related areas: " + ", ".join(item.area_id for item in related))
            print_selection_reasons("Why related:", related)
        if repo_files_considered:
            print(f"Scope reduction: start from {len(primary)} area(s) instead of scanning {repo_files_considered} repo file(s)")
        if read_first_entries:
            print(f"Read First entries: {read_first_entries}")
        if changed_in_scope:
            print(f"Changed files in scope: {changed_in_scope}")
        if read_first_text and repo_text:
            print(f"Approx text budget: Read First {read_first_text}; repo {repo_text}")
        print("")
        print("Run next:")
        if args.mode == "review":
            suffix = f" --base {args.base}" if getattr(args, "base", None) else ""
            print(f"- context-pack start --review{suffix}")
        elif args.task:
            task = args.task.replace('"', '\\"')
            print(f'- context-pack start --task "{task}"')
        elif getattr(args, "changed", False):
            print("- context-pack start --changed")
        else:
            print("- context-pack start --task \"<your task>\"")
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    args.mode = "work"
    return build_pack(args)


def cmd_review_pack(args: argparse.Namespace) -> int:
    args.mode = "review"
    args.changed = True
    snapshot = collect_snapshot(Path(args.repo).resolve())
    maybe_infer_review_base(args, snapshot.repo_root, snapshot)
    return build_pack(args)


def diff_name_only(repo: Path, base: str) -> list[str]:
    if not base:
        return []
    attempts = [
        ["diff", "--name-only", "-z", "--diff-filter=ACMRTUXB", f"{base}...HEAD"],
        ["diff", "--name-only", "-z", "--diff-filter=ACMRTUXB", base],
    ]
    for cmd in attempts:
        output = git_path_list(repo, cmd)
        if output is not None:
            return output
    return []


def upstream_ref(repo: Path) -> str | None:
    return git_text(repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])


def append_unique(values: list[str], value: str | None) -> None:
    if value and value not in values:
        values.append(value)


def review_base_candidates(repo: Path, snapshot: Snapshot) -> list[str]:
    candidates: list[str] = []
    append_unique(candidates, upstream_ref(repo))
    append_unique(candidates, git_text(repo, ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"]))
    for ref in (
        "origin/main",
        "origin/master",
        "origin/trunk",
        "origin/develop",
        "origin/dev",
        "main",
        "master",
        "trunk",
        "develop",
        "dev",
    ):
        append_unique(candidates, ref)
    return [ref for ref in candidates if ref not in {"HEAD", snapshot.branch}]


def infer_review_base(repo: Path, snapshot: Snapshot) -> str | None:
    if not snapshot.is_git or snapshot.dirty_files:
        return None
    for candidate in review_base_candidates(repo, snapshot):
        if diff_name_only(repo, candidate):
            return candidate
    return None


def maybe_infer_review_base(args: argparse.Namespace, repo: Path, snapshot: Snapshot) -> bool:
    if getattr(args, "base", None):
        return False
    if getattr(args, "mode", "") != "review" and not getattr(args, "review", False):
        return False
    inferred = infer_review_base(repo, snapshot)
    if not inferred:
        return False
    args.base = inferred
    return True


def is_context_metadata_path(repo: Path, path: str, layout: ContextLayout) -> bool:
    path = normalize_path(path)
    prefixes = {
        path_text(layout.context_dir).rstrip("/"),
        path_text(LEGACY_CONTEXT_DIR).rstrip("/"),
        path_text(LEGACY_HANDOFF_DIR).rstrip("/"),
        path_text(LEGACY_PACKS_DIR).rstrip("/"),
    }
    if any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes):
        return True
    if path in {path_text(item) for item in AGENT_DOC_TARGETS.values()}:
        return AGENT_RULES_START in read_text(repo / path)
    if path == ".gitignore":
        return "# context-pack generated/local files" in read_text(repo / path)
    return False


def filter_context_metadata_changes(repo: Path, files: Iterable[str], layout: ContextLayout) -> list[str]:
    values = sorted(dict.fromkeys(normalize_path(item) for item in files if item))
    product_files = [item for item in values if not is_context_metadata_path(repo, item, layout)]
    return product_files or values


def resolve_changed_files(repo: Path, snapshot: Snapshot, args: argparse.Namespace) -> list[str]:
    layout = resolve_layout(repo)
    maybe_infer_review_base(args, repo, snapshot)
    base = getattr(args, "base", None)
    if base:
        return filter_context_metadata_changes(repo, diff_name_only(repo, base), layout)

    if getattr(args, "mode", "") == "review":
        if snapshot.dirty_files:
            return filter_context_metadata_changes(repo, snapshot.dirty_files, layout)
        upstream = upstream_ref(repo)
        if upstream:
            files = diff_name_only(repo, upstream)
            if files:
                return filter_context_metadata_changes(repo, files, layout)

    if getattr(args, "changed", False):
        return filter_context_metadata_changes(repo, snapshot.dirty_files, layout)
    return []


def update_frontmatter_fields(path: Path, fields: dict[str, str]) -> bool:
    text = read_text(path)
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end == -1:
        return False
    front = text[4:end].splitlines()
    changed = False
    for key, value in fields.items():
        found = False
        replacement = f"{key}: {value}"
        for i, line in enumerate(front):
            if line.startswith(f"{key}:"):
                found = True
                if line != replacement:
                    front[i] = replacement
                    changed = True
                break
        if not found:
            front.append(replacement)
            changed = True
    if not changed:
        return False
    new_text = "---\n" + "\n".join(front) + text[end:]
    write_text_lf(path, new_text)
    return True


def update_frontmatter_status(path: Path, status: str) -> bool:
    return update_frontmatter_fields(path, {"status": status})


def committed_files_between(repo: Path, base: str, head: str = "HEAD") -> list[str] | None:
    if not base or base in {"unknown", "not-a-git-repo"}:
        return []
    return git_path_list(repo, ["diff", "--name-only", "-z", "--diff-filter=ACMRTUXB", f"{base}..{head}"])


def is_handoff_only_path(path: str, layout: ContextLayout) -> bool:
    path = normalize_path(path)
    return path in {
        path_text(layout.current_path),
        path_text(layout.log_path),
        path_text(LEGACY_CURRENT_PATH),
        path_text(LEGACY_LOG_PATH),
    }


def handoff_fingerprint_warning(repo: Path, snapshot: Snapshot, layout: ContextLayout) -> str | None:
    path = repo / layout.current_path
    if not path.exists():
        return None
    fields = marker_fields(read_text(path), FINGERPRINT_START, FINGERPRINT_END)
    if not fields:
        return f"{path_text(layout.current_path)} has no fingerprint; run `context-pack checkpoint --publish` if this handoff should be shared"

    problems: list[str] = []
    branch = fields.get("Branch")
    if snapshot.is_git and branch and branch not in {"unknown", snapshot.branch}:
        problems.append(f"branch {branch} != {snapshot.branch}")

    diff_hash = fields.get("Dirty diff hash")
    if diff_hash and diff_hash != snapshot.diff_hash:
        problems.append(f"diff hash {diff_hash} != {snapshot.diff_hash}")

    recorded_head = fields.get("HEAD")
    if snapshot.is_git and recorded_head and recorded_head not in {"unknown", snapshot.head}:
        changed_since = committed_files_between(repo, recorded_head)
        if changed_since is None:
            problems.append(f"recorded HEAD {recorded_head} is not comparable to {snapshot.head}")
        else:
            material = [path for path in changed_since if not is_handoff_only_path(path, layout)]
            if material:
                shown = ", ".join(material[:3])
                more = len(material) - 3
                problems.append(
                    f"material files changed since handoff HEAD {recorded_head}: {shown}"
                    + (f" (+{more} more)" if more > 0 else "")
                )

    if not problems:
        return None
    return f"{path_text(layout.current_path)} fingerprint is stale ({'; '.join(problems)}); run `context-pack checkpoint --publish` when the shared handoff should move"


def broad_area_warnings(repo: Path, manifest: dict[str, Any], layout: ContextLayout) -> list[str]:
    files = [item for item in repo_files(repo) if not is_context_metadata_path(repo, item, layout)]
    if len(files) < BROAD_AREA_MIN_FILES:
        return []
    warnings: list[str] = []
    for area_id, area in sorted((manifest.get("areas") or {}).items()):
        if area_role(area_id, area) == "overview":
            continue
        patterns = area.get("paths", []) or []
        if any(normalize_path(pattern) in {"*", "**"} for pattern in patterns):
            warnings.append(f"area {area_id} uses a repository-wide path pattern")
            continue
        matched = sum(1 for path in files if matches_any(path, patterns))
        ratio = matched / len(files)
        if matched >= BROAD_AREA_MIN_FILES and ratio >= BROAD_AREA_RATIO:
            warnings.append(f"area {area_id} matches {matched}/{len(files)} repo files ({ratio:.0%}); narrow or split its paths")
    return warnings


def search_term_health_warnings(repo: Path, manifest: dict[str, Any]) -> list[str]:
    repo_file_list = repo_files(repo)
    warnings: list[str] = []
    owners: dict[str, list[str]] = {}
    for area_id, area in sorted((manifest.get("areas") or {}).items()):
        terms = unique_text(area.get("search_terms", []) or [])
        if not terms:
            continue
        for term in terms:
            owners.setdefault(term.casefold(), []).append(area_id)

        entries = area.get("start_files", []) or area.get("paths", []) or []
        candidates = files_for_evidence_entries(repo, entries, repo_file_list)[:EVIDENCE_MAX_FILES]
        counts = {term: 0 for term in terms}
        file_counts = {term: 0 for term in terms}
        scanned_bytes = 0
        for rel in candidates:
            result = read_evidence_lines(repo / rel)
            if result is None:
                continue
            lines, size = result
            if scanned_bytes + size > EVIDENCE_MAX_SCAN_BYTES:
                break
            scanned_bytes += size
            text = "\n".join(lines).casefold()
            for term in terms:
                count = text.count(term.casefold())
                if count:
                    counts[term] += count
                    file_counts[term] += 1

        for term in terms:
            if counts[term] == 0:
                warnings.append(f"area {area_id} search term {term!r} has no match in its evidence scopes")
                continue
            broad_limit = 100 if term_is_symbolic(term) else EVIDENCE_BROAD_HIT_LIMIT
            too_many_files = file_counts[term] > 12 or (not term_is_symbolic(term) and file_counts[term] > 4)
            if counts[term] > broad_limit or too_many_files:
                warnings.append(
                    f"area {area_id} search term {term!r} is broad "
                    f"({counts[term]} matches across {file_counts[term]} files)"
                )

    for term, area_ids in sorted(owners.items()):
        unique_areas = sorted(set(area_ids))
        if len(unique_areas) > 1:
            warnings.append(f"search term {term!r} is shared by areas {', '.join(unique_areas)}")
    return warnings


def context_setup_issues(repo: Path, snapshot: Snapshot | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    snapshot = snapshot or collect_snapshot(repo)
    layout = resolve_layout(repo)

    required = [layout.context_dir, layout.areas_dir, layout.handoff_dir, layout.manifest_path, layout.index_path, layout.current_path]
    for rel in required:
        if not (repo / rel).exists():
            errors.append(f"missing {rel}")

    if (repo / layout.manifest_path).exists():
        manifest = load_manifest(repo, layout)
        areas = manifest.get("areas") or {}
        if not areas:
            warnings.append("manifest has no areas")
        for area_id, area in sorted(areas.items()):
            doc = area_doc_path(repo, area)
            if not doc.exists():
                errors.append(f"area {area_id} doc missing: {rel_to_repo(doc, repo)}")
            if not area.get("paths"):
                warnings.append(f"area {area_id} has no path patterns")
        warnings.extend(broad_area_warnings(repo, manifest, layout))
        warnings.extend(search_term_health_warnings(repo, manifest))

    gitignore = repo / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        required_ignores = [
            f"{path_text(layout.packs_dir)}/",
            f"{path_text(layout.context_dir / 'tmp')}/",
            f"{path_text(layout.local_path.parent)}/" if layout.name == "primary" else path_text(layout.local_path),
        ]
        for item in required_ignores:
            if item not in text:
                warnings.append(f"{item} is not ignored")
    else:
        warnings.append(".gitignore missing")

    if layout.name == "legacy":
        warnings.append("using legacy .codex context layout; run `context-pack migrate` to use .context-pack")
    elif layout_exists(repo, LEGACY_LAYOUT):
        warnings.append("legacy .codex context files are still present after .context-pack setup")

    if not errors and (warning := handoff_fingerprint_warning(repo, snapshot, layout)):
        warnings.append(warning)

    return errors, warnings


def cmd_status(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo)
    errors, warnings = context_setup_issues(repo, snapshot)

    if not (repo / layout.manifest_path).exists():
        if not args.quiet:
            print(f"Context Pack Status for {repo}")
            print("Context library: missing")
            print("")
            print("Next:")
            print("- context-pack setup")
        return 1

    manifest = load_manifest(repo, layout)
    routing_changed = filter_context_metadata_changes(repo, snapshot.dirty_files, layout)
    matches = selected_area_matches(manifest, changed_files=routing_changed, task=args.task, repo=repo)
    max_areas = getattr(args, "max_areas", 4)
    primary = matches[:max_areas]
    related = matches[max_areas:]
    stale = [
        warning
        for selection in matches
        if (warning := stale_warning(repo, snapshot, selection.area_id, (manifest.get("areas") or {}).get(selection.area_id, {}), routing_changed))
    ]

    if not args.quiet:
        print(f"Context Pack Status for {repo}")
        print(f"Git: {'yes' if snapshot.is_git else 'no'}; branch: {snapshot.branch}; HEAD: {snapshot.head}")
        print(f"Dirty files: {len(snapshot.dirty_files)}; diff hash: {snapshot.diff_hash}")
        print(f"Context library: {'error' if errors else 'ok'}")
        if warnings:
            print(f"Warnings: {len(warnings)}")
        if errors:
            print(f"Errors: {len(errors)}")
        print("")
        print("Primary areas:")
        if primary:
            for item in primary:
                print(f"- {item.area_id} (score {item.score})")
        else:
            print("- none")
        if related:
            print(f"Related areas: {', '.join(item.area_id for item in related)}")
        print("")
        print("Health warnings:")
        if warnings:
            for item in warnings:
                print(f"- {item}")
        else:
            print("- none")
        print("")
        print("Stale warnings:")
        if stale:
            for item in unique(stale):
                print(f"- {item}")
        else:
            print("- none")
        print("")
        print("Next:")
        if errors:
            print("- Fix setup errors or run `context-pack setup`.")
        elif snapshot.dirty_files:
            print("- Run `context-pack start --changed` before broad reading.")
            print("- After source verification, run `context-pack mark-reviewed <area>` for updated area docs.")
        else:
            print("- Context is ready. Use `context-pack start --task \"...\"` for focused work.")
    return 1 if errors else 0


def cmd_mark_reviewed(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo)
    manifest = load_manifest(repo, layout)
    areas = manifest.get("areas") or {}

    if args.all:
        area_ids = sorted(areas)
    elif args.areas:
        area_ids = args.areas
    elif not snapshot.dirty_files and not args.task:
        if not args.quiet:
            print("No areas selected. Pass area IDs, --task, or --all.")
        return 1
    else:
        changed = filter_context_metadata_changes(repo, snapshot.dirty_files, layout)
        area_ids = selected_areas(manifest, changed_files=changed, task=args.task, repo=repo)

    marked: list[str] = []
    missing: list[str] = []
    for area_id in area_ids:
        area = areas.get(area_id)
        if not area:
            missing.append(area_id)
            continue
        doc = area_doc_path(repo, area)
        if not doc.exists():
            missing.append(area_id)
            continue
        if update_frontmatter_fields(doc, {"last_reviewed_head": snapshot.head, "status": "active"}):
            marked.append(area_id)

    if not args.quiet:
        print("Marked reviewed: " + (", ".join(marked) if marked else "none changed"))
        if missing:
            print("Missing areas/docs: " + ", ".join(missing))
    return 1 if missing else 0


def cmd_refresh(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo, for_write=True)
    ensure_dirs(repo, layout)
    manifest = load_manifest(repo, layout)
    write_text_lf(repo / layout.index_path, render_index(manifest, layout))

    marked: list[str] = []
    if args.mark_stale:
        changed = filter_context_metadata_changes(repo, snapshot.dirty_files, layout)
        for area_id in selected_areas(manifest, changed_files=changed, task=args.task, repo=repo):
            area = (manifest.get("areas") or {}).get(area_id, {})
            doc = area_doc_path(repo, area)
            if doc.exists() and update_frontmatter_status(doc, "review_needed"):
                marked.append(area_id)

    if not args.quiet:
        print("Refreshed INDEX.md")
        if marked:
            print("Marked review_needed: " + ", ".join(marked))
    return 0


def cmd_gc(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    layout = resolve_layout(snapshot.repo_root)
    packs = snapshot.repo_root / layout.packs_dir
    if not packs.exists():
        return 0
    removed = 0
    for path in packs.iterdir():
        if path.name == "CONTEXT_PACK.md" and not args.all:
            continue
        if path.is_file():
            path.unlink()
            removed += 1
        elif path.is_dir():
            shutil.rmtree(path)
            removed += 1
    if not args.quiet:
        print(f"Removed {removed} generated pack item(s)")
    return 0


def migrate_file(repo: Path, source_rel: Path, target_rel: Path, *, force: bool) -> bool:
    source = repo / source_rel
    target = repo / target_rel
    if not source.exists() or not source.is_file():
        return False
    if target.exists() and not force:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8")
    write_text_lf(target, rewrite_legacy_paths(text))
    return True


def safe_remove_tree(path: Path, repo: Path) -> None:
    resolved = path.resolve()
    repo_resolved = repo.resolve()
    if resolved == repo_resolved or repo_resolved not in resolved.parents:
        raise SystemExit(f"Refusing to remove path outside repo: {path}")
    if path.exists():
        shutil.rmtree(path)


def cmd_migrate(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    if not layout_exists(repo, LEGACY_LAYOUT):
        if not args.quiet:
            print("No legacy .codex context layout found.")
        return 0
    if layout_exists(repo, PRIMARY_LAYOUT) and not args.force:
        if not args.quiet:
            print(".context-pack already exists. Use --force to overwrite copied files.")
        return 1

    ensure_dirs(repo, PRIMARY_LAYOUT)
    mappings = [
        (LEGACY_MANIFEST_PATH, MANIFEST_PATH),
        (LEGACY_INDEX_PATH, INDEX_PATH),
        (LEGACY_REVIEW_PATH, REVIEW_PATH),
        (LEGACY_CONTRACTS_PATH, CONTRACTS_PATH),
        (LEGACY_CURRENT_PATH, CURRENT_PATH),
        (LEGACY_LOG_PATH, LOG_PATH),
        (LEGACY_DECISIONS_PATH, DECISIONS_PATH),
        (LEGACY_LOCAL_PATH, LOCAL_PATH),
    ]
    migrated = 0
    skipped = 0
    for source_rel, target_rel in mappings:
        before = (repo / target_rel).exists()
        if migrate_file(repo, source_rel, target_rel, force=args.force):
            migrated += 1
        elif (repo / source_rel).exists() and before:
            skipped += 1

    legacy_areas = repo / LEGACY_AREAS_DIR
    if legacy_areas.exists():
        for source in legacy_areas.rglob("*"):
            if not source.is_file():
                continue
            rel = source.relative_to(legacy_areas)
            target_rel = AREAS_DIR / rel
            before = (repo / target_rel).exists()
            if migrate_file(repo, LEGACY_AREAS_DIR / rel, target_rel, force=args.force):
                migrated += 1
            elif before:
                skipped += 1

    if args.include_packs:
        legacy_packs = repo / LEGACY_PACKS_DIR
        if legacy_packs.exists():
            for source in legacy_packs.rglob("*"):
                if not source.is_file():
                    continue
                rel = source.relative_to(legacy_packs)
                target = repo / PACKS_DIR / rel
                if target.exists() and not args.force:
                    skipped += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                migrated += 1

    append_gitignore(repo, PRIMARY_LAYOUT)

    if args.remove_legacy:
        for rel in [LEGACY_CONTEXT_DIR, LEGACY_HANDOFF_DIR]:
            safe_remove_tree(repo / rel, repo)
        if args.include_packs:
            safe_remove_tree(repo / LEGACY_PACKS_DIR, repo)

    if not args.quiet:
        print(f"Migrated legacy .codex context to {CONTEXT_DIR}")
        print(f"- Copied/rewritten files: {migrated}")
        if skipped:
            print(f"- Skipped existing files: {skipped}")
        if args.remove_legacy:
            print("- Removed legacy context/handoff directories")
        else:
            print("- Legacy files left in place; remove them after verifying .context-pack")
    return 0


def packaged_resource_text(name: str) -> str:
    script = Path(__file__).resolve()
    candidates = [script.with_name(name)]
    if name == "SKILL.md":
        candidates.append(script.parent.parent / "SKILL.md")
    elif name == "openai.yaml":
        candidates.append(script.parent.parent / "agents" / "openai.yaml")
    elif name == "plugin.json":
        candidates.extend(parent / ".codex-plugin" / "plugin.json" for parent in script.parents)

    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise SystemExit(f"Packaged Context Pack resource is missing: {name}")


def plugin_manifest_doc() -> dict[str, Any]:
    try:
        data = json.loads(packaged_resource_text("plugin.json"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid packaged plugin.json: {exc}") from exc
    data["version"] = CONTEXT_PACK_VERSION
    return data


def packaged_skill_doc() -> str:
    return packaged_resource_text("SKILL.md")


def packaged_openai_yaml() -> str:
    return packaged_resource_text("openai.yaml")


def plugin_wrapper_script() -> str:
    return """\
#!/usr/bin/env python3
\"\"\"Wrapper for the bundled context-pack engine.\"\"\"

from __future__ import annotations

import runpy
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[1] / "skills" / "context-pack" / "scripts" / "context_pack.py"


if __name__ == "__main__":
    runpy.run_path(str(ENGINE), run_name="__main__")
"""


def find_plugin_source() -> Path | None:
    script = Path(__file__).resolve()
    for parent in script.parents:
        if (parent / ".codex-plugin" / "plugin.json").exists() and (parent / "skills" / "context-pack" / "SKILL.md").exists():
            return parent
    return None


def copy_or_synthesize_plugin(target: Path, *, force: bool) -> str:
    source = find_plugin_source()
    if source and source.resolve() == target.resolve():
        raise SystemExit(f"Refusing to install over the source plugin directory: {target}")
    if target.exists():
        if not force:
            raise SystemExit(f"Target already exists: {target}. Use --force to replace it.")
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source and source.resolve() != target.resolve():
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return "copied"

    write_json(target / ".codex-plugin" / "plugin.json", plugin_manifest_doc())
    skill_dir = target / "skills" / "context-pack"
    write_text_lf(skill_dir / "SKILL.md", packaged_skill_doc())
    write_text_lf(skill_dir / "agents" / "openai.yaml", packaged_openai_yaml())
    write_text_lf(skill_dir / "scripts" / "context_pack.py", Path(__file__).read_text(encoding="utf-8"))
    write_text_lf(target / "scripts" / "context_pack.py", plugin_wrapper_script())
    return "synthesized"


def load_marketplace(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": "personal",
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def update_marketplace(path: Path, plugin_name: str) -> str:
    data = load_marketplace(path)
    marketplace_name = str(data.setdefault("name", "personal"))
    data.setdefault("interface", {"displayName": "Personal"})
    data.setdefault("plugins", [])
    entry = {
        "name": plugin_name,
        "source": {"source": "local", "path": f"./plugins/{plugin_name}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    plugins = data["plugins"]
    if not isinstance(plugins, list):
        raise SystemExit(f"{path} field 'plugins' must be a list")
    for idx, existing in enumerate(plugins):
        if isinstance(existing, dict) and existing.get("name") == plugin_name:
            plugins[idx] = entry
            break
    else:
        plugins.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)
    return marketplace_name


def cmd_install_codex(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve()
    marketplace = Path(args.marketplace).expanduser().resolve()
    mode = copy_or_synthesize_plugin(target, force=args.force)
    marketplace_name = update_marketplace(marketplace, "context-pack")

    activated = False
    if args.activate:
        codex = shutil.which(args.codex_command)
        if not codex:
            raise SystemExit(f"Installed plugin, but could not find `{args.codex_command}` to activate it.")
        proc = run([codex, "plugin", "add", f"context-pack@{marketplace_name}"], cwd=target.parent)
        if proc.returncode != 0:
            raise SystemExit((proc.stderr or proc.stdout or "codex plugin add failed").strip())
        activated = True

    if not args.quiet:
        print(f"Installed Codex plugin to {target} ({mode})")
        print(f"Updated marketplace {marketplace}")
        if activated:
            print(f"Activated with: codex plugin add context-pack@{marketplace_name}")
        else:
            print(f"Activate in Codex with: codex plugin add context-pack@{marketplace_name}")
    return 0


def hook_block(engine: Path, hook_name: str, mode: str) -> str:
    engine_posix = shlex.quote(absolute_shell_path(engine))
    python_posix = shlex.quote(absolute_shell_path(sys.executable))
    if hook_name == "pre-commit":
        failure = 'exit "$code"' if mode == "aggressive" else "true"
        body = f"""\
repo="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python_exe={python_posix}
engine={engine_posix}
"$python_exe" "$engine" doctor --repo "$repo" --quiet
code=$?
if [ "$code" -ne 0 ]; then
  echo "context-pack doctor warning (exit $code); run: context-pack doctor --repo \"$repo\"" >&2
  {failure}
fi"""
    else:
        command = "checkpoint --pack"
        body = f"""\
repo="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python_exe={python_posix}
engine={engine_posix}
"$python_exe" "$engine" {command} --repo "$repo" --quiet >/dev/null 2>&1 || true"""
    return f"{HOOK_START}\n# mode: {mode}; hook: {hook_name}\n{body}\n{HOOK_END}\n"


def install_hook(path: Path, block: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else "#!/bin/sh\n"
    if HOOK_START in existing and HOOK_END in existing:
        existing = replace_marker(existing, HOOK_START, HOOK_END, marker_content(block, HOOK_START, HOOK_END))
    else:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += "\n" + block
    write_text_lf(path, existing)
    try:
        path.chmod(path.stat().st_mode | 0o755)
    except OSError:
        pass


def remove_hook_block(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if HOOK_START not in text or HOOK_END not in text:
        return False
    before = text.split(HOOK_START, 1)[0]
    after = text.split(HOOK_END, 1)[1]
    write_text_lf(path, (before.rstrip() + "\n" + after.lstrip()).lstrip())
    return True


def cmd_install_git_hooks(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    if not snapshot.is_git:
        raise SystemExit("install-git-hooks requires a git repository")
    repo = snapshot.repo_root
    git_dir_text = git_text(repo, ["rev-parse", "--git-dir"])
    if not git_dir_text:
        raise SystemExit("Could not locate .git directory")
    git_dir = (repo / git_dir_text).resolve() if not Path(git_dir_text).is_absolute() else Path(git_dir_text)
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    engine = Path(__file__).resolve()
    hooks = ["pre-commit", "post-checkout", "post-merge"]
    if args.mode == "aggressive":
        hooks.append("post-commit")
    for hook in hooks:
        install_hook(hooks_dir / hook, hook_block(engine, hook, args.mode))
    if not args.quiet:
        print(f"Installed context-pack git hooks in {hooks_dir}")
        print("Mode: " + args.mode)
    return 0


def cmd_uninstall_git_hooks(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    if not snapshot.is_git:
        return 0
    repo = snapshot.repo_root
    git_dir_text = git_text(repo, ["rev-parse", "--git-dir"])
    if not git_dir_text:
        return 0
    git_dir = (repo / git_dir_text).resolve() if not Path(git_dir_text).is_absolute() else Path(git_dir_text)
    hooks_dir = git_dir / "hooks"
    removed = 0
    for hook in ["pre-commit", "post-checkout", "post-merge", "post-commit"]:
        if remove_hook_block(hooks_dir / hook):
            removed += 1
    if not args.quiet:
        print(f"Removed context-pack blocks from {removed} git hook(s)")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    errors, warnings = context_setup_issues(repo, snapshot)

    if args.fix:
        if not args.quiet:
            print(f"Repairing Context Pack setup in {repo}")
        setup_args = argparse.Namespace(
            repo=str(repo),
            quiet=True,
            dry_run=False,
            force=False,
            infer_areas=None,
            agent_docs=args.agent_docs,
            git_hooks="off",
        )
        result = cmd_setup(setup_args)
        snapshot = collect_snapshot(repo)
        errors, warnings = context_setup_issues(repo, snapshot)
        if result != 0 and errors:
            if not args.quiet:
                print("Repair incomplete.")
            return result

    if not args.quiet:
        print(f"Context-pack doctor for {repo}")
        print(f"HEAD: {snapshot.head}; dirty files: {len(snapshot.dirty_files)}")
        if args.fix:
            print("Repair: completed" if not errors else "Repair: attempted")
        for item in warnings:
            print(f"WARNING: {item}")
        for item in errors:
            print(f"ERROR: {item}")
        if not warnings and not errors:
            print("OK")
    if errors or (args.strict and warnings):
        return 1
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    data = dataclasses.asdict(snapshot)
    data["repo_root"] = str(snapshot.repo_root)
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=".", help="Repository or workspace path")
    parser.add_argument("--quiet", action="store_true", help="Reduce command output")


def add_pack_budget(
    parser: argparse.ArgumentParser,
    *,
    max_areas: int = 4,
    max_read_first: int = 12,
    max_contracts: int = 12,
    max_failure_modes: int = 10,
) -> None:
    parser.add_argument("--max-areas", type=int, default=max_areas, help="Maximum primary areas in the pack")
    parser.add_argument(
        "--max-read-first",
        type=int,
        default=max_read_first,
        help="Maximum Read First entries before spilling to Read Later",
    )
    parser.add_argument("--max-contracts", type=int, default=max_contracts, help="Maximum contract bullets in the pack")
    parser.add_argument(
        "--max-failure-modes",
        type=int,
        default=max_failure_modes,
        help="Maximum failure mode bullets in the pack",
    )
    parser.add_argument(
        "--text-budget",
        action="store_true",
        help="Scan repo text to include approximate chars/4 budget metrics (measure always enables this)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context-pack",
        description="Route coding agents to focused repo context.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {CONTEXT_PACK_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="{setup,start,checkpoint,doctor,install-codex}")

    p = sub.add_parser("setup", help="Set up Context Pack in a repo with safe onboarding defaults")
    add_common(p)
    p.add_argument("--dry-run", action="store_true", help="Preview setup changes without writing files")
    p.add_argument("--force", action="store_true", help="Overwrite existing context docs")
    infer_group = p.add_mutually_exclusive_group()
    infer_group.add_argument(
        "--infer-areas",
        dest="infer_areas",
        action="store_true",
        default=None,
        help="Add missing inferred source/test/docs/automation areas even when a manifest already exists",
    )
    infer_group.add_argument(
        "--no-infer-areas",
        dest="infer_areas",
        action="store_false",
        help="Skip inferred area creation even on first setup",
    )
    p.add_argument(
        "--agent-docs",
        choices=["auto", "all", "agents", "claude", "cursor", "none"],
        default="auto",
        help="Agent docs to install; auto writes AGENTS.md and refreshes detected Claude/Cursor rules",
    )
    p.add_argument(
        "--git-hooks",
        choices=["off", "safe", "aggressive"],
        default="off",
        help="Optionally install repo-local git hooks during setup",
    )
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("init", help=argparse.SUPPRESS, description="Initialize .context-pack docs in a repo")
    add_common(p)
    p.add_argument("--force", action="store_true", help="Overwrite existing context files")
    infer_group = p.add_mutually_exclusive_group()
    infer_group.add_argument(
        "--infer-areas",
        dest="infer_areas",
        action="store_true",
        default=None,
        help="Add missing inferred source/test/docs/automation areas even when a manifest already exists",
    )
    infer_group.add_argument(
        "--no-infer-areas",
        dest="infer_areas",
        action="store_false",
        help="Skip inferred area creation even on first init",
    )
    p.add_argument("--no-agent-doc", action="store_true", help="Do not update AGENTS.md")
    p.add_argument("--agent-doc", default="AGENTS.md", help="Agent instruction file to update")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("install-agent-docs", help=argparse.SUPPRESS, description="Install Context Pack rules for coding agents")
    add_common(p)
    p.add_argument(
        "--target",
        action="append",
        choices=["auto", "all", *AGENT_DOC_TARGETS.keys()],
        help="Agent docs to update: auto, all, agents, claude, or cursor. Repeat to select multiple targets.",
    )
    p.set_defaults(func=cmd_install_agent_docs)

    p = sub.add_parser("checkpoint", help="Write ignored local checkpoint state, or publish tracked handoff files")
    add_common(p)
    p.add_argument("--pack", action="store_true", help="Also generate a changed-files context pack")
    p.add_argument("--publish", action="store_true", help="Update tracked handoff files instead of ignored local checkpoint state")
    p.set_defaults(func=cmd_checkpoint)

    p = sub.add_parser("start", help="Prepare focused context without modifying an unconfigured repo")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--review", action="store_true", help="Prepare a review pack instead of a work pack")
    p.add_argument("--base", help="Review committed changes against a base ref; omitted review bases are inferred when possible")
    p.add_argument("--changed", action="store_true", help="Include dirty files when preparing a work pack")
    p.add_argument("--output", help="Output markdown path")
    p.add_argument("--agent", action="store_true", help="Emit compact evidence-first output for an agent")
    add_pack_budget(p)
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("pack", help=argparse.SUPPRESS, description="Generate a task or changed-files context pack")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--changed", action="store_true", help="Select areas from dirty files")
    p.add_argument("--output", help="Output markdown path")
    add_pack_budget(p)
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("measure", help=argparse.SUPPRESS, description="Preview estimated context reduction without writing a pack")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--changed", action="store_true", help="Select areas from dirty files")
    p.add_argument("--review", action="store_true", help="Measure a review pack instead of a work pack")
    p.add_argument("--base", help="Review committed changes against a base ref; omitted review bases are inferred when possible")
    add_pack_budget(p)
    p.set_defaults(func=cmd_measure)

    p = sub.add_parser("review-pack", help=argparse.SUPPRESS, description="Generate a code-review context pack from dirty files")
    add_common(p)
    p.add_argument("--task", help="Optional review focus")
    p.add_argument("--base", help="Review committed changes against a base ref; omitted review bases are inferred when possible")
    p.add_argument("--output", help="Output markdown path")
    add_pack_budget(p)
    p.set_defaults(func=cmd_review_pack)

    p = sub.add_parser("refresh", help=argparse.SUPPRESS, description="Regenerate routing docs from manifest")
    add_common(p)
    p.add_argument("--task", help="Optional task for stale marking")
    p.add_argument("--mark-stale", action="store_true", help="Mark selected area docs review_needed")
    p.set_defaults(func=cmd_refresh)

    p = sub.add_parser("doctor", help="Validate context-pack repo setup")
    add_common(p)
    p.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    p.add_argument("--fix", action="store_true", help="Repair missing setup files before validating")
    p.add_argument(
        "--agent-docs",
        choices=["auto", "all", "agents", "claude", "cursor", "none"],
        default="auto",
        help="Agent docs to install when --fix repairs setup",
    )
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("status", help=argparse.SUPPRESS, description="Show context health, selected areas, and next action")
    add_common(p)
    p.add_argument("--task", help="Optional task to score areas against")
    p.add_argument("--max-areas", type=int, default=4, help="Maximum primary areas to show")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("mark-reviewed", help=argparse.SUPPRESS, description="Mark area docs reviewed at the current HEAD")
    add_common(p)
    p.add_argument("areas", nargs="*", help="Area IDs to mark; defaults to changed-file selected areas")
    p.add_argument("--task", help="Optional task to select areas when no explicit areas are provided")
    p.add_argument("--all", action="store_true", help="Mark all area docs reviewed")
    p.set_defaults(func=cmd_mark_reviewed)

    p = sub.add_parser("gc", help=argparse.SUPPRESS, description="Remove generated context packs")
    add_common(p)
    p.add_argument("--all", action="store_true", help="Also remove CONTEXT_PACK.md")
    p.set_defaults(func=cmd_gc)

    p = sub.add_parser("migrate", help=argparse.SUPPRESS, description="Migrate legacy .codex context docs to .context-pack")
    add_common(p)
    p.add_argument("--force", action="store_true", help="Overwrite existing .context-pack files during migration")
    p.add_argument("--include-packs", action="store_true", help="Also copy generated legacy packs")
    p.add_argument("--remove-legacy", action="store_true", help="Remove legacy .codex context and handoff dirs after copying")
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("snapshot", help=argparse.SUPPRESS, description="Print current repo fingerprint as JSON")
    add_common(p)
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("install-codex", help="Install the Codex plugin into the personal marketplace")
    p.add_argument("--target", type=Path, default=Path.home() / "plugins" / "context-pack", help="Plugin target directory")
    p.add_argument(
        "--marketplace",
        type=Path,
        default=Path.home() / ".agents" / "plugins" / "marketplace.json",
        help="Personal marketplace.json path",
    )
    p.add_argument("--force", action="store_true", help="Replace an existing plugin target")
    p.add_argument("--activate", action="store_true", help="Run `codex plugin add context-pack@<marketplace>` after installing")
    p.add_argument("--codex-command", default="codex", help="Codex CLI executable to use with --activate")
    p.add_argument("--quiet", action="store_true", help="Reduce command output")
    p.set_defaults(func=cmd_install_codex)

    p = sub.add_parser("install-git-hooks", help=argparse.SUPPRESS, description="Install repo-local git hooks for automatic checkpoints")
    add_common(p)
    p.add_argument(
        "--mode",
        choices=["safe", "aggressive"],
        default="safe",
        help="safe installs pre-commit doctor plus post-checkout/post-merge checkpoints; aggressive also checkpoints after commits",
    )
    p.set_defaults(func=cmd_install_git_hooks)

    p = sub.add_parser("uninstall-git-hooks", help=argparse.SUPPRESS, description="Remove context-pack blocks from repo-local git hooks")
    add_common(p)
    p.set_defaults(func=cmd_uninstall_git_hooks)

    visible_commands = {"setup", "start", "checkpoint", "doctor", "install-codex"}
    sub._choices_actions[:] = [choice for choice in sub._choices_actions if choice.dest in visible_commands]
    return parser


def print_quickstart() -> None:
    print("Context Pack")
    print("Focused repo orientation for coding agents.")
    print("")
    print("Normal use:")
    print('  Ask your agent: "Fix the login timeout."')
    print('  Ask your agent: "Review this branch."')
    print('  Ask your agent: "Leave this work easy to resume later."')
    print("")
    print("Safe first run (no repo setup):")
    print('  context-pack start --task "fix login timeout"')
    print("  context-pack start --review")
    print("")
    print("Persist Context Pack in this repo:")
    print("  context-pack setup --dry-run")
    print("  context-pack setup")
    print("")
    print("Handoff after meaningful work:")
    print("  context-pack checkpoint --pack")
    print("")
    print("Need details?")
    print("  context-pack --help")
    print("  context-pack doctor")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print_quickstart()
        return 0
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        eprint("Interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
