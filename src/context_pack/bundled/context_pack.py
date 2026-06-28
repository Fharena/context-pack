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
import shutil
import subprocess
import sys
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
    "agents": Path("AGENTS.md"),
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
CONTEXT_PACK_VERSION = "0.2.17"
TEXT_BUDGET_MAX_FILE_BYTES = 1_000_000
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
    "crash",
    "debug",
    "error",
    "exception",
    "fail",
    "failed",
    "fails",
    "failing",
    "failure",
    "fix",
    "implement",
    "issue",
    "patch",
    "regression",
    "refactor",
    "고쳐줘",
    "고쳐주세요",
    "수정해줘",
}
TASK_ACTION_TOKENS = CODE_TASK_TOKENS | {
    "broken",
    "problem",
    "review",
    "reviewed",
    "reviewing",
}
TEST_FAILURE_TOKENS = {
    "broken",
    "crash",
    "debug",
    "error",
    "exception",
    "fail",
    "failed",
    "fails",
    "failing",
    "failure",
    "red",
    "실패",
    "실패해",
    "실패함",
}
TEST_SCOPE_TOKENS = {
    "spec",
    "specs",
    "test",
    "tests",
    "테스트",
}
ROUTE_NOISE_TOKENS = {
    "agent",
    "agents",
    "context",
    "pack",
    "packs",
}
REVIEW_INTENT_TOKENS = {
    "branch",
    "change",
    "changed",
    "changes",
    "commit",
    "commits",
    "diff",
    "pr",
    "pull",
    "request",
}
CONTINUATION_INTENT_TOKENS = {
    "continue",
    "left",
    "resume",
    "session",
}
HANDOFF_INTENT_TOKENS = {
    "another",
    "checkpoint",
    "done",
    "easy",
    "handoff",
    "later",
    "machine",
    "resume",
    "session",
    "state",
    "work",
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


def rel_to_repo(path: Path, repo: Path) -> str:
    try:
        return normalize_path(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return normalize_path(path)


def run(
    cmd: list[str],
    cwd: Path,
    *,
    text: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=text,
        check=check,
    )


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
    status = git_text(repo, ["status", "--porcelain=v1", "-uall"]) if is_git else None
    status_lines = status.splitlines() if status else []
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


def inferred_area_candidates(repo: Path, layout: ContextLayout | None = None) -> dict[str, dict[str, Any]]:
    layout = layout or resolve_layout(repo)
    candidates = {
        "source": {
            "doc": path_text(layout.areas_dir / "source.md"),
            "description": "Application or library source code.",
            "paths": ["src/**", "lib/**", "app/**", "packages/**"],
            "start_files": ["src", "lib", "app", "packages"],
            "tests": ["tests/**", "test/**"],
            "keywords": ["source", "implementation", "application", "library"],
            "contracts": [
                "Verify behavior in source before trusting summaries.",
                "Keep public interfaces backward compatible unless the task explicitly changes them.",
            ],
            "failure_modes": [
                "Changing implementation without updating nearby tests.",
                "Assuming generated or stale context docs reflect current source behavior.",
            ],
            "stale_if_paths": ["src/**", "lib/**", "app/**", "packages/**"],
        },
        "tests": {
            "doc": path_text(layout.areas_dir / "tests.md"),
            "description": "Test suites, fixtures, and validation commands.",
            "paths": ["tests/**", "test/**", "__tests__/**", "spec/**"],
            "start_files": ["tests", "test", "__tests__", "spec"],
            "tests": ["tests/**", "test/**", "__tests__/**", "spec/**"],
            "keywords": ["test", "tests", "fixture", "validation", "ci"],
            "contracts": [
                "Tests should exercise user-visible behavior, not only implementation details.",
            ],
            "failure_modes": [
                "Mocks pass while real integration paths fail.",
                "Fixtures drift from the source contracts they claim to cover.",
            ],
            "stale_if_paths": ["tests/**", "test/**", "__tests__/**", "spec/**"],
        },
        "docs": {
            "doc": path_text(layout.areas_dir / "docs.md"),
            "description": "User-facing docs, onboarding notes, and repository guidance.",
            "paths": ["README.md", "README.*.md", "docs/**"],
            "start_files": ["README.md", "docs"],
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
            "doc": path_text(layout.areas_dir / "automation.md"),
            "description": "Build, release, scripts, CI, packaging, and developer automation.",
            "paths": [".github/**", "scripts/**", "pyproject.toml", "package.json", "Makefile"],
            "start_files": ["pyproject.toml", "package.json", "Makefile", ".github/workflows", "scripts"],
            "tests": [".github/workflows/**"],
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


def load_manifest(repo: Path, layout: ContextLayout | None = None) -> dict[str, Any]:
    layout = layout or resolve_layout(repo)
    path = repo / layout.manifest_path
    if not path.exists():
        return default_manifest(layout)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {layout.manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{layout.manifest_path} must contain a JSON object")
    data.setdefault("version", 1)
    data.setdefault("areas", {})
    return data


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
- Reading append-only logs before the current source of truth.
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
    stale = "\n".join(f"  - {item} changes" for item in area.get("stale_if_paths", []) or [])
    start = "\n".join(f"- `{item}`" for item in area.get("start_files", []) or [])
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
stale_if:
{stale or "  - relevant files change"}
---

# {area_id.replace("-", " ").title()}

## Read When
- {area.get("description", "Working in this area.")}

## Start With
{start or f"- Use `{path_text(layout.index_path)}` to choose source files."}

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
    layout = layout or PRIMARY_LAYOUT
    pack_path = path_text(layout.pack_path)
    return f"""\
## Context Pack

Use Context Pack as quiet orientation for natural-language coding, review, debugging, and handoff requests. The user does not need to name it or ask for a pack.

Treat requests like "fix this bug", "why are tests failing?", "review this branch", "continue where we left off", or "leave this easy to resume" as normal triggers. Run Context Pack as part of the work, then keep going with the user's actual task.

Run it only when repo orientation would save broad reading or preserve useful handoff state:
- Session start or continuation with no clear task yet: `context-pack start`, then read `CURRENT.md` and `INDEX.md`.
- Non-trivial bug, feature, or debugging task: `context-pack start --task "<short task>"`
- Review, PR, or branch work: `context-pack start --review`; add `--base <base-ref>` when known. Without a base, Context Pack tries upstream/common default branches.
- Changed files are the only signal: `context-pack start --changed`
- Missing `.context-pack/` during a normal task: still use `context-pack start`; it auto-initializes lightweight context docs.
- Explicit install/configuration request: `context-pack setup --dry-run`, then `context-pack setup` if setup was requested; use `context-pack doctor --fix` for broken setup.
- End of meaningful work or handoff: `context-pack checkpoint --pack`

Skip Context Pack for pure Q&A, tiny obvious single-file edits, or tasks where the relevant files and tests are already clear.

When a pack is generated, read `{pack_path}` before broad source reads. Treat context docs as routing hints, not ground truth; verify against source when state, stale warnings, or code behavior disagree.

Use `context-pack checkpoint --publish --pack` only when the handoff should be committed and shared through git.
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
    lines.extend(
        [
            "",
            "## Generated Packs",
            f"- `{path_text(layout.pack_path)}` is generated and should not be committed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_review(manifest: dict[str, Any]) -> str:
    lines = [
        "# Review Router",
        "",
        "For code review, map changed files to areas, then check the listed contracts, tests, and failure modes before widening scope.",
        "",
        "## Area Routing",
    ]
    for area_id, area in sorted((manifest.get("areas") or {}).items()):
        lines.extend(["", f"### {area_id}", f"- Doc: `{area.get('doc', '')}`"])
        paths = area.get("paths", []) or []
        if paths:
            lines.append("- If changed files match:")
            for item in paths:
                lines.append(f"  - `{item}`")
        tests = area.get("tests", []) or []
        if tests:
            lines.append("- Inspect/run tests:")
            for item in tests:
                lines.append(f"  - `{item}`")
        failures = area.get("failure_modes", []) or []
        if failures:
            lines.append("- Common failure modes:")
            for item in failures:
                lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "## Escalate Review Scope When",
            "- Public API, CLI, schema, storage format, subprocess launch, or cache/session identity changed.",
            "- Tests or test helpers changed in a way that may hide behavior.",
            "- A changed file does not map to any known area.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_contracts(manifest: dict[str, Any]) -> str:
    lines = [
        "# Project Contracts",
        "",
        "Use this as a compact checklist. Keep area-specific details in `AREAS/*.md`.",
    ]
    for area_id, area in sorted((manifest.get("areas") or {}).items()):
        contracts = area.get("contracts", []) or []
        if not contracts:
            continue
        lines.extend(["", f"## {area_id}"])
        for item in contracts:
            lines.append(f"- {item}")
    if len(lines) == 3:
        lines.extend(["", "- No contracts recorded yet."])
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


def resolve_agent_doc_targets(targets: list[str] | None) -> list[str]:
    requested = targets or ["all"]
    resolved: list[str] = []
    for item in requested:
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
            (setup_file_action(repo, layout.review_path, force=force), layout.review_path),
            (setup_file_action(repo, layout.contracts_path, force=force), layout.contracts_path),
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
    if args.agent_docs != "all":
        parts.extend(["--agent-docs", args.agent_docs])
    if args.git_hooks != "off":
        parts.extend(["--git-hooks", args.git_hooks])
    return " ".join(command_arg(str(part)) for part in parts)


def cmd_setup_dry_run(args: argparse.Namespace, repo: Path, snapshot: Snapshot, layout: ContextLayout) -> int:
    if args.quiet:
        return 0

    agent_docs: list[tuple[str, Path]] = []
    if args.agent_docs != "none":
        targets = ["all"] if args.agent_docs == "all" else [args.agent_docs]
        agent_docs = [
            (setup_agent_doc_action(repo, kind), AGENT_DOC_TARGETS[kind])
            for kind in resolve_agent_doc_targets(targets)
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
    written = [append_agent_rules_for_kind(repo, kind, layout) for kind in resolve_agent_doc_targets(args.target)]
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
        targets = ["all"] if args.agent_docs == "all" else [args.agent_docs]
        agent_docs = [append_agent_rules_for_kind(repo, kind, layout) for kind in resolve_agent_doc_targets(targets)]

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
    write_if_missing(repo / layout.review_path, render_review(manifest), force=args.force)
    write_if_missing(repo / layout.contracts_path, render_contracts(manifest), force=args.force)
    write_if_missing(repo / layout.current_path, current_doc(snapshot, layout), force=args.force)
    write_if_missing(repo / layout.log_path, "# Context Pack Log\n\nAppend-only operational log.\n", force=args.force)
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
            write_if_missing(repo / layout.log_path, "# Context Pack Log\n\nAppend-only operational log.\n")
        with (repo / layout.log_path).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(entry)
        checkpoint_path = layout.current_path
        checkpoint_kind = "Published handoff"
    else:
        if not (repo / layout.local_path).exists():
            write_if_missing(repo / layout.local_path, local_checkpoint_doc(snapshot, layout))

        local = (repo / layout.local_path).read_text(encoding="utf-8")
        local = replace_marker(local, FINGERPRINT_START, FINGERPRINT_END, render_fingerprint(snapshot))
        if "## Local Log" not in local:
            local = local.rstrip() + "\n\n## Local Log\n"
        local = local.rstrip() + "\n" + entry.lstrip("\n")
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
    initialized = False

    if not had_context:
        if args.no_init:
            if not args.quiet:
                print(f"Context Pack Start for {repo}")
                print("Context library: missing")
                print("")
                print("Next:")
                print("- Run `context-pack setup` or rerun `context-pack start` without `--no-init`.")
            return 1
        init_args = argparse.Namespace(
            repo=str(repo),
            quiet=True,
            force=False,
            no_agent_doc=args.no_agent_doc,
            agent_doc=args.agent_doc,
        )
        result = cmd_init(init_args)
        if result != 0:
            return result
        initialized = True
        snapshot = collect_snapshot(repo)
        layout = resolve_layout(repo)

    mode = "work"
    changed = False
    pack_reason = ""
    task_intent = infer_start_task_intent(args.task)

    if args.review or args.base or task_intent == "review":
        mode = "review"
        changed = True
        pack_reason = "review"
        args.mode = mode
        review_base_inferred = maybe_infer_review_base(args, repo, snapshot)
    elif task_intent in {"continue", "checkpoint"}:
        review_base_inferred = False
    elif args.task:
        review_base_inferred = False
        changed = args.changed or (bool(snapshot.dirty_files) and not initialized)
        pack_reason = "task"
    elif args.changed or (snapshot.dirty_files and not initialized):
        review_base_inferred = False
        changed = True
        pack_reason = "changed files"
    else:
        review_base_inferred = False

    pack_generated = bool(pack_reason)
    selected: list[AreaSelection] = []
    output_path = Path(args.output) if args.output else repo / layout.pack_path
    if not output_path.is_absolute():
        output_path = repo / output_path

    if pack_generated:
        pack_args = argparse.Namespace(
            repo=str(repo),
            task=args.task,
            changed=changed,
            base=args.base,
            output=str(output_path),
            quiet=True,
            mode=mode,
            max_areas=args.max_areas,
            max_read_first=args.max_read_first,
            max_contracts=args.max_contracts,
            max_failure_modes=args.max_failure_modes,
        )
        manifest = load_manifest(repo, layout)
        changed_files = resolve_changed_files(repo, snapshot, pack_args)
        selected = selected_area_matches(manifest, changed_files=changed_files, task=args.task)[: args.max_areas]
        result = build_pack(pack_args)
        if result != 0:
            return result

    if not args.quiet:
        print(f"Context Pack Start for {repo}")
        print(f"Git: {'yes' if snapshot.is_git else 'no'}; branch: {snapshot.branch}; HEAD: {snapshot.head}")
        if initialized:
            print(f"Initialized: {normalize_path(layout.manifest_path)}")
        else:
            print("Context library: ok")
        print(f"Dirty files: {len(snapshot.dirty_files)}; diff hash: {snapshot.diff_hash}")
        print("")
        if pack_generated:
            print(f"Generated {mode} pack for {pack_reason}: {rel_to_repo(output_path, repo)}")
            if mode == "review" and args.base:
                suffix = " (auto)" if review_base_inferred else ""
                print(f"Review base: {args.base}{suffix}")
            print("Selected areas: " + (", ".join(item.area_id for item in selected) if selected else "none"))
            print_selection_reasons("Why selected:", selected)
            repo_file_total = len(repo_files(repo))
            if repo_file_total:
                print(f"Scope reduction: start from {len(selected)} area(s) instead of scanning {repo_file_total} repo file(s)")
            text_budget = pack_text_budget_summary(output_path)
            if text_budget:
                print(f"Approx text budget: {text_budget}")
            print("")
            print("Read next:")
            print(f"- {rel_to_repo(output_path, repo)}")
            for item in selected:
                area = (load_manifest(repo, layout).get("areas") or {}).get(item.area_id, {})
                doc = area.get("doc")
                if doc:
                    print(f"- {doc}")
        else:
            print("No pack generated: no task, review request, or pre-existing dirty files were found.")
            print("")
            if task_intent == "checkpoint":
                print("Detected handoff/checkpoint wording.")
                print("")
                print("Run next:")
                print("- `context-pack checkpoint --pack`")
                print("- `context-pack checkpoint --publish --pack` when the handoff should travel through git")
            else:
                print("Read next:")
                print(f"- {normalize_path(layout.current_path)}")
                print(f"- {normalize_path(layout.index_path)}")
                print("")
                print("Optional next commands:")
                print('- `context-pack start --task "..."` for a focused work pack')
                print("- `context-pack start --review` for a review pack")
                print("- `context-pack start --changed` if you want to force dirty-file routing")
        print("")
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
    return {part for part in "".join(cleaned).split() if len(part) >= 3 and part not in TOKEN_STOP_WORDS}


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def infer_start_task_intent(task: str | None) -> str:
    if not task:
        return ""
    text = f" {task.lower()} "
    tokens = tokenize(task)
    if (
        "review" in tokens
        and (tokens & REVIEW_INTENT_TOKENS or " pull request " in text or " pr " in text)
    ) or ("리뷰" in text and contains_any(text, ["브랜치", "변경", "변경사항", "커밋", " pr ", " pull request "])):
        return "review"
    if (
        "checkpoint" in tokens
        or ("handoff" in tokens and bool(tokens & (HANDOFF_INTENT_TOKENS - {"handoff"})))
        or " hand off " in text
        or ("later" in tokens and bool(tokens & (HANDOFF_INTENT_TOKENS - {"later"})))
        or (contains_any(text, ["나중", "인계"]) and contains_any(text, ["이어", "정리", "넘겨"]))
        or ("정리" in text and contains_any(text, ["이어", "세션", "인계"]))
    ):
        return "checkpoint"
    if (
        "where we left off" in text
        or ("continue" in tokens and bool(tokens & (CONTINUATION_INTENT_TOKENS - {"continue"})))
        or ("resume" in tokens and bool(tokens & {"session", "work"}))
        or contains_any(text, ["이어가", "이어서", "계속 이어"])
    ):
        return "continue"
    return ""


def area_text(area_id: str, area: dict[str, Any]) -> str:
    parts = [area_id, area.get("description", "")]
    parts.extend(area.get("keywords", []) or [])
    parts.extend(area.get("paths", []) or [])
    return " ".join(str(part) for part in parts)


def selected_area_matches(
    manifest: dict[str, Any],
    *,
    changed_files: list[str],
    task: str | None,
) -> list[AreaSelection]:
    areas = manifest.get("areas") or {}
    selections: list[AreaSelection] = []
    task_tokens = tokenize(task or "")

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

        route_tokens = task_tokens - TASK_ACTION_TOKENS - ROUTE_NOISE_TOKENS
        if route_tokens:
            overlap = route_tokens & tokenize(area_text(area_id, area))
            if overlap:
                score += 6 * len(overlap)
                reasons.append("task matched keywords: " + ", ".join(sorted(overlap)[:5]))

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
    if (
        "tests" in selected_ids
        and "source" in areas
        and "source" not in selected_ids
        and task_tokens & TEST_SCOPE_TOKENS
        and task_tokens & TEST_FAILURE_TOKENS
    ):
        score = max((item.score for item in selections if item.area_id == "tests"), default=2)
        selections.append(
            AreaSelection(
                area_id="source",
                score=score,
                reasons=["paired with tests for failure debugging"],
                matched_files=[],
            )
        )
        selections.sort(key=lambda item: (-item.score, item.area_id))

    if not selections and "overview" in areas:
        starter_ids = [area_id for area_id in ("source", "tests") if area_id in areas]
        if "source" in starter_ids and task_tokens & CODE_TASK_TOKENS:
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


def selected_areas(
    manifest: dict[str, Any],
    *,
    changed_files: list[str],
    task: str | None,
) -> list[str]:
    return [item.area_id for item in selected_area_matches(manifest, changed_files=changed_files, task=task)]


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
    except OSError:
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
    files = git_text(repo, ["ls-files", "--cached", "--others", "--exclude-standard"])
    if files is not None:
        return [normalize_path(line) for line in files.splitlines() if line.strip()]

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
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data or len(data) > TEXT_BUDGET_MAX_FILE_BYTES or b"\0" in data:
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
    if whole <= 0:
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


def split_limited(items: Iterable[str], limit: int | None) -> tuple[list[str], list[str]]:
    values = unique_text(items)
    if limit is None or limit < 1:
        return values, []
    return values[:limit], values[limit:]


def area_doc_path(repo: Path, area: dict[str, Any]) -> Path:
    return repo / normalize_path(area.get("doc", ""))


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
    max_read_first: int = 12,
    max_contracts: int = 12,
    max_failure_modes: int = 10,
) -> str:
    layout = layout or resolve_layout(repo)
    areas = manifest.get("areas") or {}
    related_selections = related_selections or []
    changed = changed_files
    read_first: list[str] = []
    read_later: list[str] = []
    tests: list[str] = []
    contracts: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    def collect_area(selection: AreaSelection, *, primary: bool) -> None:
        area = areas.get(selection.area_id, {})
        doc_path = normalize_path(area.get("doc", ""))
        if doc_path:
            (read_first if primary else read_later).append(doc_path)
        target = read_first if primary else read_later
        target.extend(area.get("start_files", []) or [])
        target.extend(path for path in changed if matches_any(path, area.get("paths", []) or []))
        if primary:
            tests.extend(area.get("tests", []) or [])
            contracts.extend(area.get("contracts", []) or [])
            failures.extend(area.get("failure_modes", []) or [])

        doc = area_doc_path(repo, area)
        text = read_text(doc)
        if primary:
            contracts.extend(extract_section_bullets(text, "Contracts"))
            failures.extend(extract_section_bullets(text, "Common Failure Modes"))

        warning = stale_warning(repo, snapshot, selection.area_id, area, changed)
        if warning:
            warnings.append(warning)

    for selection in selections:
        collect_area(selection, primary=True)
    for selection in related_selections:
        collect_area(selection, primary=False)

    if mode == "review":
        read_first.insert(0, path_text(layout.review_path))
        read_first.insert(0, path_text(layout.contracts_path))

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
    repo_budget = text_budget_for_files(repo, repo_file_list)
    read_first_files = files_for_read_first_entries(repo, read_first_visible, repo_file_list)
    read_first_budget = text_budget_for_files(repo, read_first_files)
    repo_tokens = estimated_tokens(repo_budget.chars)
    read_first_tokens = estimated_tokens(read_first_budget.chars)
    budget_ratio = round((read_first_tokens / repo_tokens) * 100) if repo_tokens and read_first_tokens else 0

    def path_line(item: str) -> str:
        suffix = "" if item and (repo / item).exists() else " (missing)"
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
        "## Scope Reduction",
        f"- Repo files considered: {repo_file_total if repo_file_total else 'unknown'}",
        f"- Primary areas selected: {len(selections)} of {area_total}",
        f"- Read First entries: {read_first_total}" + (f" (~{read_first_ratio}% of repo files)" if repo_file_total else ""),
        f"- Changed files in scope: {len(changed)}",
        (
            f"- Approx Read First text: ~{format_token_count(read_first_tokens)} tokens "
            f"from {read_first_budget.files} file(s)"
            + (f" (~{budget_ratio}% of repo text)" if repo_tokens else "")
        ),
        f"- Approx repo text: ~{format_token_count(repo_tokens)} tokens from {repo_budget.files} text file(s)",
        "- Token estimates use chars/4 and skip binary, unreadable, ignored, and >1 MB files.",
        "",
        "## Selected Areas",
    ]
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
            "- Use this pack to choose what to inspect first. Verify behavior in source code before editing or reviewing.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_pack(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    layout = resolve_layout(repo, for_write=True)
    ensure_dirs(repo, layout)
    manifest = load_manifest(repo, layout)
    changed = resolve_changed_files(repo, snapshot, args)
    matches = selected_area_matches(manifest, changed_files=changed, task=args.task)
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
    manifest = load_manifest(repo, layout)
    if not has_context_library:
        manifest = merge_inferred_areas(repo, manifest, layout)
    args.mode = "review" if getattr(args, "review", False) or getattr(args, "base", None) else "work"
    review_base_inferred = maybe_infer_review_base(args, repo, snapshot) if args.mode == "review" else False
    changed = resolve_changed_files(repo, snapshot, args)
    matches = selected_area_matches(manifest, changed_files=changed, task=args.task)
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
        ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base}...HEAD"],
        ["diff", "--name-only", "--diff-filter=ACMRTUXB", base],
    ]
    for cmd in attempts:
        output = git_text(repo, cmd)
        if output is not None:
            return [normalize_path(line) for line in output.splitlines() if line.strip()]
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


def resolve_changed_files(repo: Path, snapshot: Snapshot, args: argparse.Namespace) -> list[str]:
    maybe_infer_review_base(args, repo, snapshot)
    base = getattr(args, "base", None)
    if base:
        return sorted(dict.fromkeys(diff_name_only(repo, base)))

    if getattr(args, "mode", "") == "review":
        if snapshot.dirty_files:
            return snapshot.dirty_files
        upstream = upstream_ref(repo)
        if upstream:
            files = diff_name_only(repo, upstream)
            if files:
                return sorted(dict.fromkeys(files))

    if getattr(args, "changed", False):
        return snapshot.dirty_files
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
    output = git_text(repo, ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base}..{head}"])
    if output is None:
        return None
    return [normalize_path(line) for line in output.splitlines() if line.strip()]


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
    matches = selected_area_matches(manifest, changed_files=snapshot.dirty_files, task=args.task)
    max_areas = getattr(args, "max_areas", 4)
    primary = matches[:max_areas]
    related = matches[max_areas:]
    stale = [
        warning
        for selection in matches
        if (warning := stale_warning(repo, snapshot, selection.area_id, (manifest.get("areas") or {}).get(selection.area_id, {}), snapshot.dirty_files))
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
        area_ids = selected_areas(manifest, changed_files=snapshot.dirty_files, task=args.task)

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
    write_text_lf(repo / layout.review_path, render_review(manifest))
    write_text_lf(repo / layout.contracts_path, render_contracts(manifest))

    marked: list[str] = []
    if args.mark_stale:
        changed = snapshot.dirty_files
        for area_id in selected_areas(manifest, changed_files=changed, task=args.task):
            area = (manifest.get("areas") or {}).get(area_id, {})
            doc = area_doc_path(repo, area)
            if doc.exists() and update_frontmatter_status(doc, "review_needed"):
                marked.append(area_id)

    if not args.quiet:
        print("Refreshed INDEX.md, REVIEW.md, and CONTRACTS.md")
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


def plugin_manifest_doc() -> dict[str, Any]:
    return {
        "name": "context-pack",
        "version": CONTEXT_PACK_VERSION,
        "description": "Repo-local context packs and handoff checkpoints for coding agents.",
        "author": {"name": "Context Pack"},
        "license": "MIT",
        "keywords": ["context", "handoff", "code-review", "agents", "codex", "claude", "cursor"],
        "skills": "./skills/",
        "interface": {
            "displayName": "Context Pack",
            "shortDescription": "Start agents from focused repo context.",
            "longDescription": (
                "Context Pack gives coding agents a lightweight repo-local map before they read broadly. It turns "
                "natural requests like fixing bugs, debugging failing tests, reviewing branches, and handing off work "
                "into focused task or review packs with relevant files, contracts, tests, and stale warnings, while "
                "keeping generated checkpoints local by default."
            ),
            "developerName": "Context Pack",
            "category": "Productivity",
            "capabilities": ["Write", "Automation"],
            "defaultPrompt": [
                "Fix a bug from focused repo context.",
                "Review this branch without rereading the whole repo.",
                "Leave this work easy to resume later.",
            ],
            "brandColor": "#2563EB",
        },
    }


def packaged_skill_doc() -> str:
    return """\
---
name: context-pack
description: Prepare focused repo context for coding agents. Use proactively when the user naturally asks to fix a bug, debug failing tests, review a branch or PR, continue or hand off work, or start non-trivial coding where the agent would otherwise read broadly. Skip tiny obvious edits, pure Q&A, or tasks where relevant files are already known.
---

# Context Pack

Context Pack is an agent behavior, not a command the user should have to remember.

When a user says things like "fix this bug", "review this branch", "why are tests failing?", "continue this from the last session", or "I need to hand this off", use Context Pack to orient before broad repo reading, then continue the actual task. Do not ask the user to name Context Pack first. The generated docs are routing hints, not source of truth; verify behavior in source before editing or reviewing.

## Core Loop

1. Decide whether orientation is worth it.
2. Run Context Pack in the target repo:

   ```bash
   context-pack <command>
   ```

   If the CLI is not on `PATH`, run the bundled engine from this skill folder instead:

   ```bash
   python <this-skill-folder>/scripts/context_pack.py <command>
   ```

   Do not use a target repo's `scripts/context_pack.py` unless the target repo is Context Pack itself.

3. Read `.context-pack/packs/CONTEXT_PACK.md` when generated.
4. Read only the listed area docs and source files first.
5. Continue the user's coding, review, debugging, or handoff task.

Report briefly. Usually one sentence is enough: selected areas, stale warning if any, and what you will inspect next. Only include scope-reduction or text-budget numbers when the user asks for proof, you ran `measure`, or the numbers materially explain the next step.

## When To Use

| Situation | Action |
| --- | --- |
| Context Pack is missing during normal task work | Use `start`; it auto-initializes lightweight context docs |
| User explicitly asks to install/configure repo memory | `setup --dry-run`, then `setup` if setup was requested |
| Continuing with no clear task yet | `start`, then read `CURRENT.md` and `INDEX.md` |
| Starting non-trivial coding/debugging | `start --task "<short task>"` |
| Reviewing a branch/PR/dirty files | `start --review`; add `--base <base-ref>` when known. Without a base, Context Pack tries upstream/common default branches |
| Changed files are the only signal | `start --changed` |
| User asks for proof before writing packs | `measure --task "<short task>"` |
| Setup looks broken or incomplete | `doctor --fix` |
| Meaningful work ended or handoff is requested | `checkpoint --pack` |
| Handoff must travel through git | `checkpoint --publish --pack` |

## When To Skip

- The user asks a pure question that does not need repo orientation.
- The change is a tiny, obvious single-file edit.
- The relevant file and test are already clear from the conversation.
- A fresh generated pack already matches the current task and git state.
- Running the tool would be more expensive than directly answering.

If you skip it, just proceed. Do not apologize or explain unless the user asked why.

## Setup Behavior

For normal work in an uninitialized repo, use `start` first; it auto-initializes lightweight context docs and keeps the user in the task.

For explicit setup/configuration requests, preview writes first:

```bash
context-pack setup --dry-run
```

If the user explicitly asked to configure or install Context Pack, apply setup:

```bash
context-pack setup
```

This creates `.context-pack/`, ignored generated/local paths, and shared agent rules for `AGENTS.md`, `CLAUDE.md`, and Cursor rules. Preserve user text outside managed blocks. Do not install git hooks unless the user explicitly asks for git-boundary automation.

For legacy repos, migrate only when needed:

```bash
context-pack migrate
```

## Task And Review Behavior

For normal coding/debugging:

```bash
context-pack start --task "<short task>"
```

For review:

```bash
context-pack start --review
```

Add `--base <base-ref>` when the review base is known; otherwise review mode tries upstream/common default branches and uses the first diff it finds.

After running `start`, read the generated pack if present. Treat stale warnings as prompts to verify source, not as facts.

## Checkpoint Behavior

At the end of meaningful agent work:

```bash
context-pack checkpoint --pack
```

This writes ignored local state by default, so proactive checkpoints do not dirty tracked files. Use `checkpoint --publish --pack` only when the handoff should be committed and shared through git.

When the worktree is clean after commits, `checkpoint --pack` uses committed changes since the previous checkpoint when available, so handoff packs still point at the work just finished.

## Admin Commands

Use these only when directly relevant:

```bash
context-pack install-codex --force
context-pack install-agent-docs
context-pack status
context-pack measure --task "<short task>"
context-pack doctor --fix
context-pack mark-reviewed <area-id>
context-pack refresh
context-pack install-git-hooks --mode safe
```

Run `context-pack <command> --help` for options instead of expanding this skill into a full CLI manual. Use the bundled script path only as the fallback command prefix.

## Operating Rules

- Keep the user in their normal workflow; do not make them manage packs manually.
- Prefer `start` over lower-level `pack` commands.
- Prefer source verification over trusting summaries.
- Keep `CURRENT.md` short; durable knowledge belongs in `.context-pack/AREAS/*.md`.
- Do not commit `.context-pack/packs/` or `.context-pack/local/LOCAL.md`.
- If a changed file maps to no area, finish the task first, then consider updating the manifest or area docs.
"""


def packaged_openai_yaml() -> str:
    return """\
interface:
  display_name: "Context Pack"
  short_description: "Start agents from focused repo context"
  default_prompt: "Fix, review, debug, or hand off work from focused repo context before broad reading."
policy:
  allow_implicit_invocation: true
"""


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
    engine_posix = normalize_path(engine)
    if hook_name == "pre-commit":
        body = f"""\
repo="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if command -v python >/dev/null 2>&1; then
  python "{engine_posix}" doctor --repo "$repo" --quiet
  code=$?
  if [ "$code" -ne 0 ]; then
    echo "context-pack doctor failed; run: python {engine_posix} doctor --repo \"$repo\"" >&2
    exit "$code"
  fi
fi"""
    else:
        command = "checkpoint --pack"
        body = f"""\
repo="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if command -v python >/dev/null 2>&1; then
  python "{engine_posix}" {command} --repo "$repo" --quiet >/dev/null 2>&1 || true
fi"""
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


def add_pack_budget(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-areas", type=int, default=4, help="Maximum primary areas in the pack")
    parser.add_argument("--max-read-first", type=int, default=12, help="Maximum Read First entries before spilling to Read Later")
    parser.add_argument("--max-contracts", type=int, default=12, help="Maximum contract bullets in the pack")
    parser.add_argument("--max-failure-modes", type=int, default=10, help="Maximum failure mode bullets in the pack")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context-pack",
        description="Build repo-local context packs for coding agents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {CONTEXT_PACK_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

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
        choices=["all", "agents", "claude", "cursor", "none"],
        default="all",
        help="Agent docs to install during setup",
    )
    p.add_argument(
        "--git-hooks",
        choices=["off", "safe", "aggressive"],
        default="off",
        help="Optionally install repo-local git hooks during setup",
    )
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("init", help="Initialize .context-pack docs in a repo")
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

    p = sub.add_parser("install-agent-docs", help="Install Context Pack rules for Codex, Claude, Cursor, and other agents")
    add_common(p)
    p.add_argument(
        "--target",
        action="append",
        choices=["all", *AGENT_DOC_TARGETS.keys()],
        help="Agent docs to update: all, agents, claude, or cursor. Repeat to select multiple targets.",
    )
    p.set_defaults(func=cmd_install_agent_docs)

    p = sub.add_parser("checkpoint", help="Write ignored local checkpoint state, or publish tracked handoff files")
    add_common(p)
    p.add_argument("--pack", action="store_true", help="Also generate a changed-files context pack")
    p.add_argument("--publish", action="store_true", help="Update tracked handoff files instead of ignored local checkpoint state")
    p.set_defaults(func=cmd_checkpoint)

    p = sub.add_parser("start", help="Auto-initialize if needed and prepare the right context pack")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--review", action="store_true", help="Prepare a review pack instead of a work pack")
    p.add_argument("--base", help="Review committed changes against a base ref; omitted review bases are inferred when possible")
    p.add_argument("--changed", action="store_true", help="Include dirty files when preparing a work pack")
    p.add_argument("--no-init", action="store_true", help="Do not initialize missing context docs")
    p.add_argument("--no-agent-doc", action="store_true", help="When initializing, do not update AGENTS.md")
    p.add_argument("--agent-doc", default="AGENTS.md", help="Agent instruction file to update when initializing")
    p.add_argument("--output", help="Output markdown path")
    add_pack_budget(p)
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("pack", help="Generate a task or changed-files context pack")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--changed", action="store_true", help="Select areas from dirty files")
    p.add_argument("--output", help="Output markdown path")
    add_pack_budget(p)
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("measure", help="Preview estimated context reduction without writing a pack")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--changed", action="store_true", help="Select areas from dirty files")
    p.add_argument("--review", action="store_true", help="Measure a review pack instead of a work pack")
    p.add_argument("--base", help="Review committed changes against a base ref; omitted review bases are inferred when possible")
    add_pack_budget(p)
    p.set_defaults(func=cmd_measure)

    p = sub.add_parser("review-pack", help="Generate a code-review context pack from dirty files")
    add_common(p)
    p.add_argument("--task", help="Optional review focus")
    p.add_argument("--base", help="Review committed changes against a base ref; omitted review bases are inferred when possible")
    p.add_argument("--output", help="Output markdown path")
    add_pack_budget(p)
    p.set_defaults(func=cmd_review_pack)

    p = sub.add_parser("refresh", help="Regenerate routing docs from manifest")
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
        choices=["all", "agents", "claude", "cursor", "none"],
        default="all",
        help="Agent docs to install when --fix repairs setup",
    )
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("status", help="Show context health, selected areas, and next action")
    add_common(p)
    p.add_argument("--task", help="Optional task to score areas against")
    p.add_argument("--max-areas", type=int, default=4, help="Maximum primary areas to show")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("mark-reviewed", help="Mark area docs reviewed at the current HEAD")
    add_common(p)
    p.add_argument("areas", nargs="*", help="Area IDs to mark; defaults to changed-file selected areas")
    p.add_argument("--task", help="Optional task to select areas when no explicit areas are provided")
    p.add_argument("--all", action="store_true", help="Mark all area docs reviewed")
    p.set_defaults(func=cmd_mark_reviewed)

    p = sub.add_parser("gc", help="Remove generated context packs")
    add_common(p)
    p.add_argument("--all", action="store_true", help="Also remove CONTEXT_PACK.md")
    p.set_defaults(func=cmd_gc)

    p = sub.add_parser("migrate", help="Migrate legacy .codex context docs to .context-pack")
    add_common(p)
    p.add_argument("--force", action="store_true", help="Overwrite existing .context-pack files during migration")
    p.add_argument("--include-packs", action="store_true", help="Also copy generated legacy packs")
    p.add_argument("--remove-legacy", action="store_true", help="Remove legacy .codex context and handoff dirs after copying")
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("snapshot", help="Print current repo fingerprint as JSON")
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

    p = sub.add_parser("install-git-hooks", help="Install repo-local git hooks for automatic checkpoints")
    add_common(p)
    p.add_argument(
        "--mode",
        choices=["safe", "aggressive"],
        default="safe",
        help="safe installs pre-commit doctor plus post-checkout/post-merge checkpoints; aggressive also checkpoints after commits",
    )
    p.set_defaults(func=cmd_install_git_hooks)

    p = sub.add_parser("uninstall-git-hooks", help="Remove context-pack blocks from repo-local git hooks")
    add_common(p)
    p.set_defaults(func=cmd_uninstall_git_hooks)

    return parser


def print_quickstart() -> None:
    print("Context Pack")
    print("Agent-first repo context for Codex, Claude, Cursor, and coding agents.")
    print("")
    print("Normal use:")
    print('  Ask your agent: "Fix the login timeout."')
    print('  Ask your agent: "Review this branch."')
    print('  Ask your agent: "Leave this work easy to resume later."')
    print("")
    print("Set up this repo:")
    print("  context-pack setup --dry-run")
    print("  context-pack setup")
    print("")
    print("Direct CLI:")
    print('  context-pack measure --task "fix login timeout"')
    print('  context-pack start --task "fix login timeout"')
    print("  context-pack start --review")
    print("  context-pack checkpoint --pack")
    print("")
    print("Codex plugin:")
    print("  context-pack install-codex --activate")
    print("")
    print("Need details?")
    print("  context-pack --help")
    print("  context-pack doctor --fix")


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
