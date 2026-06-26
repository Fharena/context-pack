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


CONTEXT_DIR = Path(".codex/context")
AREAS_DIR = CONTEXT_DIR / "AREAS"
HANDOFF_DIR = Path(".codex/handoff")
PACKS_DIR = Path(".codex/packs")
MANIFEST_PATH = CONTEXT_DIR / "manifest.json"
INDEX_PATH = CONTEXT_DIR / "INDEX.md"
REVIEW_PATH = CONTEXT_DIR / "REVIEW.md"
CONTRACTS_PATH = CONTEXT_DIR / "CONTRACTS.md"
CURRENT_PATH = HANDOFF_DIR / "CURRENT.md"
LOG_PATH = HANDOFF_DIR / "LOG.md"
DECISIONS_PATH = HANDOFF_DIR / "DECISIONS.md"
LOCAL_PATH = HANDOFF_DIR / "LOCAL.md"
PACK_PATH = PACKS_DIR / "CONTEXT_PACK.md"
AGENTS_PATH = Path("AGENTS.md")

FINGERPRINT_START = "<!-- context-pack:fingerprint:start -->"
FINGERPRINT_END = "<!-- context-pack:fingerprint:end -->"
AGENT_RULES_START = "<!-- context-pack:rules:start -->"
AGENT_RULES_END = "<!-- context-pack:rules:end -->"
HOOK_START = "# context-pack:start"
HOOK_END = "# context-pack:end"


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
    return proc.stdout.strip()


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


def ensure_dirs(repo: Path) -> None:
    for rel in [CONTEXT_DIR, AREAS_DIR, HANDOFF_DIR, PACKS_DIR]:
        (repo / rel).mkdir(parents=True, exist_ok=True)


def default_manifest() -> dict[str, Any]:
    return {
        "version": 1,
        "generated_by": "context-pack",
        "areas": {
            "overview": {
                "doc": ".codex/context/AREAS/overview.md",
                "description": "Default project orientation and safe starting point.",
                "paths": [
                    "README.md",
                    "AGENTS.md",
                    "CLAUDE.md",
                    "codex.md",
                    ".codex/context/**",
                ],
                "start_files": [
                    "README.md",
                    "AGENTS.md",
                    ".codex/context/INDEX.md",
                    ".codex/handoff/CURRENT.md",
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
                    ".codex/context/**",
                    ".codex/handoff/**",
                    "AGENTS.md",
                    "README.md",
                ],
            }
        },
    }


def load_manifest(repo: Path) -> dict[str, Any]:
    path = repo / MANIFEST_PATH
    if not path.exists():
        return default_manifest()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {MANIFEST_PATH}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{MANIFEST_PATH} must contain a JSON object")
    data.setdefault("version", 1)
    data.setdefault("areas", {})
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_if_missing(path: Path, content: str, *, force: bool = False) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def replace_marker(text: str, start: str, end: str, content: str) -> str:
    block = f"{start}\n{content.rstrip()}\n{end}"
    if start in text and end in text:
        before = text.split(start, 1)[0]
        after = text.split(end, 1)[1]
        return before.rstrip() + "\n\n" + block + "\n" + after.lstrip()
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


def overview_area_doc(snapshot: Snapshot) -> str:
    return f"""---
id: overview
last_reviewed_head: {snapshot.head}
status: active
paths:
  - README.md
  - AGENTS.md
  - .codex/context/**
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
- .codex/context/INDEX.md
- .codex/handoff/CURRENT.md

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
- .codex/packs/
- archived logs
- generated artifacts
"""


def current_doc(snapshot: Snapshot) -> str:
    fingerprint = render_fingerprint(snapshot)
    return f"""# Current Handoff

{FINGERPRINT_START}
{fingerprint}
{FINGERPRINT_END}

## Active Goal
- Keep this short. Move details into `.codex/context/AREAS/*.md`.

## Read First
1. `.codex/handoff/CURRENT.md`
2. `.codex/context/INDEX.md`
3. The relevant `.codex/context/AREAS/*.md` files

## Next Actions
1. Generate or consult a context pack before broad repo reading.

## Watch Outs
- Treat stale context as a hint, not a fact.
- Check the source-of-truth checkout before editing.

## Last Verified
- Not recorded yet.
"""


def agent_rules() -> str:
    return f"""{AGENT_RULES_START}
{agent_rules_body()}
{AGENT_RULES_END}
"""


def agent_rules_body() -> str:
    return """\
## Context Pack

At the start of substantial work, read `.codex/handoff/CURRENT.md` and `.codex/context/INDEX.md`, then use the relevant `.codex/context/AREAS/*.md` files before broad repo reading.

For reviews and debugging, prefer a generated context pack from `.codex/packs/CONTEXT_PACK.md` when present. Treat context docs as routing hints, not ground truth. If HEAD, dirty files, or diff hash differ from the current repo state, verify against source code before acting.

At the end of substantial work or after changing files, run the context-pack checkpoint script when available so the next agent has an up-to-date fingerprint and log entry.
"""


def render_index(manifest: dict[str, Any]) -> str:
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
            "- `.codex/packs/CONTEXT_PACK.md` is generated and should not be committed.",
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


def append_gitignore(repo: Path) -> None:
    entries = [
        ".codex/packs/",
        ".codex/context/tmp/",
        ".codex/handoff/LOCAL.md",
    ]
    path = repo / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    normalized = set(line.strip() for line in text.splitlines())
    missing = [entry for entry in entries if entry not in normalized]
    if not missing:
        return
    prefix = "" if not text or text.endswith("\n") else "\n"
    block = "\n# context-pack generated/local files\n" + "\n".join(missing) + "\n"
    path.write_text(text + prefix + block, encoding="utf-8")


def append_agent_rules(repo: Path, *, agent_doc: str = "AGENTS.md") -> None:
    path = repo / agent_doc
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    rules = agent_rules()
    if AGENT_RULES_START in text and AGENT_RULES_END in text:
        text = replace_marker(text, AGENT_RULES_START, AGENT_RULES_END, agent_rules_body())
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + rules
    path.write_text(text.lstrip(), encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    ensure_dirs(repo)
    manifest = load_manifest(repo)

    write_if_missing(repo / MANIFEST_PATH, json.dumps(manifest, indent=2, sort_keys=True) + "\n", force=args.force)
    write_if_missing(repo / AREAS_DIR / "overview.md", overview_area_doc(snapshot), force=args.force)
    write_if_missing(repo / INDEX_PATH, render_index(manifest), force=args.force)
    write_if_missing(repo / REVIEW_PATH, render_review(manifest), force=args.force)
    write_if_missing(repo / CONTRACTS_PATH, render_contracts(manifest), force=args.force)
    write_if_missing(repo / CURRENT_PATH, current_doc(snapshot), force=args.force)
    write_if_missing(repo / LOG_PATH, "# Context Pack Log\n\nAppend-only operational log.\n", force=args.force)
    write_if_missing(repo / DECISIONS_PATH, "# Decisions\n\nRecord durable direction changes only.\n", force=args.force)
    write_if_missing(repo / LOCAL_PATH, "# Local Context\n\nMachine-local notes. This file is ignored by default.\n", force=args.force)

    append_gitignore(repo)
    if not args.no_agent_doc:
        append_agent_rules(repo, agent_doc=args.agent_doc)

    if not args.quiet:
        print(f"Initialized context-pack in {repo}")
        print(f"- Context index: {INDEX_PATH}")
        print(f"- Handoff: {CURRENT_PATH}")
        print(f"- Manifest: {MANIFEST_PATH}")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    ensure_dirs(repo)

    if not (repo / CURRENT_PATH).exists():
        write_if_missing(repo / CURRENT_PATH, current_doc(snapshot))

    current = (repo / CURRENT_PATH).read_text(encoding="utf-8")
    current = replace_marker(current, FINGERPRINT_START, FINGERPRINT_END, render_fingerprint(snapshot))
    (repo / CURRENT_PATH).write_text(current, encoding="utf-8")

    if not (repo / LOG_PATH).exists():
        write_if_missing(repo / LOG_PATH, "# Context Pack Log\n\nAppend-only operational log.\n")
    dirty = ", ".join(snapshot.dirty_files) if snapshot.dirty_files else "none"
    entry = "\n".join(
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
    with (repo / LOG_PATH).open("a", encoding="utf-8") as handle:
        handle.write(entry)

    if args.pack:
        pack_args = argparse.Namespace(
            repo=str(repo),
            task=None,
            changed=True,
            output=str(repo / PACK_PATH),
            quiet=True,
            mode="work",
        )
        build_pack(pack_args)

    if not args.quiet:
        print(f"Checkpoint updated at {CURRENT_PATH}")
        print(f"HEAD: {snapshot.head}; dirty: {len(snapshot.dirty_files)} file(s); hash: {snapshot.diff_hash}")
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
    return {part for part in "".join(cleaned).split() if len(part) >= 3}


def area_text(area_id: str, area: dict[str, Any]) -> str:
    parts = [area_id, area.get("description", "")]
    parts.extend(area.get("keywords", []) or [])
    parts.extend(area.get("paths", []) or [])
    return " ".join(str(part) for part in parts)


def selected_areas(
    manifest: dict[str, Any],
    *,
    changed_files: list[str],
    task: str | None,
) -> list[str]:
    areas = manifest.get("areas") or {}
    selected: set[str] = set()

    for path in changed_files:
        for area_id, area in areas.items():
            patterns = (area.get("paths", []) or []) + (area.get("stale_if_paths", []) or [])
            if matches_any(path, patterns):
                selected.add(area_id)

    if task:
        task_tokens = tokenize(task)
        for area_id, area in areas.items():
            score = len(task_tokens & tokenize(area_text(area_id, area)))
            if score:
                selected.add(area_id)

    if not selected and "overview" in areas:
        selected.add("overview")
    return sorted(selected)


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
    area_ids: list[str],
    *,
    changed_files: list[str],
    task: str | None,
    mode: str,
) -> str:
    areas = manifest.get("areas") or {}
    changed = changed_files
    read_first: list[str] = []
    tests: list[str] = []
    contracts: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    for area_id in area_ids:
        area = areas.get(area_id, {})
        doc_path = normalize_path(area.get("doc", ""))
        if doc_path:
            read_first.append(doc_path)
        read_first.extend(area.get("start_files", []) or [])
        read_first.extend(path for path in changed if matches_any(path, area.get("paths", []) or []))
        tests.extend(area.get("tests", []) or [])
        contracts.extend(area.get("contracts", []) or [])
        failures.extend(area.get("failure_modes", []) or [])

        doc = area_doc_path(repo, area)
        text = read_text(doc)
        contracts.extend(extract_section_bullets(text, "Contracts"))
        failures.extend(extract_section_bullets(text, "Common Failure Modes"))

        warning = stale_warning(repo, snapshot, area_id, area, changed)
        if warning:
            warnings.append(warning)

    if mode == "review":
        read_first.insert(0, ".codex/context/REVIEW.md")
        read_first.insert(0, ".codex/context/CONTRACTS.md")

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
        "## Selected Areas",
    ]
    for area_id in area_ids:
        lines.append(f"- {area_id}")
    if not area_ids:
        lines.append("- none")

    lines.extend(["", "## Read First"])
    for item in unique(read_first):
        if item and (repo / item).exists():
            lines.append(f"- `{item}`")
        elif item:
            lines.append(f"- `{item}` (missing)")

    lines.extend(["", "## Changed Files"])
    if changed:
        for item in changed:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Contracts To Check"])
    for item in unique(contracts):
        lines.append(f"- {item}")
    if not contracts:
        lines.append("- none recorded")

    lines.extend(["", "## Common Failure Modes"])
    for item in unique(failures):
        lines.append(f"- {item}")
    if not failures:
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
    ensure_dirs(repo)
    manifest = load_manifest(repo)
    changed = resolve_changed_files(repo, snapshot, args)
    area_ids = selected_areas(manifest, changed_files=changed, task=args.task)
    content = render_pack(repo, manifest, snapshot, area_ids, changed_files=changed, task=args.task, mode=args.mode)
    output = Path(args.output) if args.output else repo / PACK_PATH
    if not output.is_absolute():
        output = repo / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    if not args.quiet:
        print(f"Context pack written to {output}")
        print("Selected areas: " + (", ".join(area_ids) if area_ids else "none"))
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    args.mode = "work"
    return build_pack(args)


def cmd_review_pack(args: argparse.Namespace) -> int:
    args.mode = "review"
    args.changed = True
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


def resolve_changed_files(repo: Path, snapshot: Snapshot, args: argparse.Namespace) -> list[str]:
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


def update_frontmatter_status(path: Path, status: str) -> bool:
    text = read_text(path)
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end == -1:
        return False
    front = text[4:end].splitlines()
    changed = False
    found = False
    for i, line in enumerate(front):
        if line.startswith("status:"):
            found = True
            if line != f"status: {status}":
                front[i] = f"status: {status}"
                changed = True
            break
    if not found:
        front.append(f"status: {status}")
        changed = True
    if not changed:
        return False
    new_text = "---\n" + "\n".join(front) + text[end:]
    path.write_text(new_text, encoding="utf-8")
    return True


def cmd_refresh(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(Path(args.repo).resolve())
    repo = snapshot.repo_root
    ensure_dirs(repo)
    manifest = load_manifest(repo)
    (repo / INDEX_PATH).write_text(render_index(manifest), encoding="utf-8")
    (repo / REVIEW_PATH).write_text(render_review(manifest), encoding="utf-8")
    (repo / CONTRACTS_PATH).write_text(render_contracts(manifest), encoding="utf-8")

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
    packs = snapshot.repo_root / PACKS_DIR
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
    path.write_text(existing, encoding="utf-8", newline="\n")
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
    path.write_text((before.rstrip() + "\n" + after.lstrip()).lstrip(), encoding="utf-8", newline="\n")
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
    errors: list[str] = []
    warnings: list[str] = []

    required = [CONTEXT_DIR, AREAS_DIR, HANDOFF_DIR, MANIFEST_PATH, INDEX_PATH, CURRENT_PATH]
    for rel in required:
        if not (repo / rel).exists():
            errors.append(f"missing {rel}")

    manifest = load_manifest(repo)
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
        if ".codex/packs/" not in text:
            warnings.append(".codex/packs/ is not ignored")
        if ".codex/handoff/LOCAL.md" not in text:
            warnings.append(".codex/handoff/LOCAL.md is not ignored")
    else:
        warnings.append(".gitignore missing")

    if not args.quiet:
        print(f"Context-pack doctor for {repo}")
        print(f"HEAD: {snapshot.head}; dirty files: {len(snapshot.dirty_files)}")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context_pack.py",
        description="Build repo-local context packs for coding agents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Initialize .codex context docs in a repo")
    add_common(p)
    p.add_argument("--force", action="store_true", help="Overwrite existing context files")
    p.add_argument("--no-agent-doc", action="store_true", help="Do not update AGENTS.md")
    p.add_argument("--agent-doc", default="AGENTS.md", help="Agent instruction file to update")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("checkpoint", help="Update CURRENT.md fingerprint and append LOG.md")
    add_common(p)
    p.add_argument("--pack", action="store_true", help="Also generate a changed-files context pack")
    p.set_defaults(func=cmd_checkpoint)

    p = sub.add_parser("pack", help="Generate a task or changed-files context pack")
    add_common(p)
    p.add_argument("--task", help="Natural language task to match against area metadata")
    p.add_argument("--changed", action="store_true", help="Select areas from dirty files")
    p.add_argument("--output", help="Output markdown path")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("review-pack", help="Generate a code-review context pack from dirty files")
    add_common(p)
    p.add_argument("--task", help="Optional review focus")
    p.add_argument("--base", help="Review committed changes against a base ref, such as main")
    p.add_argument("--output", help="Output markdown path")
    p.set_defaults(func=cmd_review_pack)

    p = sub.add_parser("refresh", help="Regenerate routing docs from manifest")
    add_common(p)
    p.add_argument("--task", help="Optional task for stale marking")
    p.add_argument("--mark-stale", action="store_true", help="Mark selected area docs review_needed")
    p.set_defaults(func=cmd_refresh)

    p = sub.add_parser("doctor", help="Validate context-pack repo setup")
    add_common(p)
    p.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("gc", help="Remove generated context packs")
    add_common(p)
    p.add_argument("--all", action="store_true", help="Also remove CONTEXT_PACK.md")
    p.set_defaults(func=cmd_gc)

    p = sub.add_parser("snapshot", help="Print current repo fingerprint as JSON")
    add_common(p)
    p.set_defaults(func=cmd_snapshot)

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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        eprint("Interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
