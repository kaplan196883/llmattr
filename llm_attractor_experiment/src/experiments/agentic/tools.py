"""The five sandboxed tools (plus the optional ``todo_write`` for the
A3 todo-replace Nudge). See docs/AGENTIC_MVP_SPEC.md §2.2.

Each tool is defined once as an Anthropic tool schema and once as a
dispatch function ``(sandbox, params, state) -> result_str``. The
``state`` dict carries cross-tool mutable state (currently just the
Todo list for A3); most tools ignore it.

A typed abstraction of each call (file role / command class / edit type)
is produced by ``classify_tool_call`` for the tool-trace sequence
analysis (ARTICLE_CODING.md §1.3 — tool *parameters* matter and need
typed abstraction rather than literal-string explosion).
"""
from __future__ import annotations

import shlex
from typing import Any, Callable

from src.experiments.agentic.sandbox import Sandbox, SandboxError

# ---------------------------------------------------------------------------
# Anthropic tool schemas (the `tools` arg of the Messages API)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: dict[str, dict] = {
    "read_file": {
        "name": "read_file",
        "description": "Read a UTF-8 text file from the working tree. "
                       "Path is relative to the project root.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    "write_file": {
        "name": "write_file",
        "description": "Write (create or overwrite) a UTF-8 text file in "
                       "the working tree. Path is relative to the root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    "edit_file": {
        "name": "edit_file",
        "description": "Replace the first exact occurrence of `old` with "
                       "`new` in a file. Fails if `old` is absent or not "
                       "unique.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
            },
            "required": ["path", "old", "new"],
        },
    },
    "run_bash": {
        "name": "run_bash",
        "description": "Run a shell command in the project root. No network "
                       "access. 30s timeout. Use for running tests "
                       "(e.g. `pytest`), listing files, etc.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
    "search": {
        "name": "search",
        "description": "Search file contents with a regex pattern, "
                       "optionally restricted to a glob. Returns matching "
                       "lines with file:line prefixes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "glob": {"type": "string"},
            },
            "required": ["pattern"],
        },
    },
    # Added to the toolset only for the A3 todo-replace Nudge.
    "todo_write": {
        "name": "todo_write",
        "description": "Replace your task list. Pass the full list of todo "
                       "items; each item is a short imperative string. This "
                       "is your persistent memory of what to do next.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["items"],
        },
    },
}

BASE_TOOLS = ["read_file", "write_file", "edit_file", "run_bash", "search"]


def tool_schemas(names: list[str]) -> list[dict]:
    return [TOOL_SCHEMAS[n] for n in names]


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def _read_file(sb: Sandbox, params: dict, state: dict) -> str:
    path = sb.resolve(params["path"])
    if not path.exists():
        return f"[error] file not found: {params['path']}"
    if not path.is_file():
        return f"[error] not a file: {params['path']}"
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[error] could not read {params['path']}: {exc}"


def _write_file(sb: Sandbox, params: dict, state: dict) -> str:
    path = sb.resolve(params["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(params["content"], encoding="utf-8")
    except OSError as exc:
        return f"[error] could not write {params['path']}: {exc}"
    n = len(params["content"])
    return f"[ok] wrote {params['path']} ({n} chars)"


def _edit_file(sb: Sandbox, params: dict, state: dict) -> str:
    path = sb.resolve(params["path"])
    if not path.exists():
        return f"[error] file not found: {params['path']}"
    text = path.read_text(encoding="utf-8", errors="replace")
    old = params["old"]
    count = text.count(old)
    if count == 0:
        return f"[error] `old` string not found in {params['path']}"
    if count > 1:
        return (f"[error] `old` string is not unique in {params['path']} "
                f"({count} occurrences); make it more specific")
    path.write_text(text.replace(old, params["new"], 1), encoding="utf-8")
    return f"[ok] edited {params['path']}"


def _run_bash(sb: Sandbox, params: dict, state: dict) -> str:
    try:
        return sb.run_bash(params["command"])
    except SandboxError as exc:
        return f"[sandbox-denied] {exc}"


def _search(sb: Sandbox, params: dict, state: dict) -> str:
    import re
    pattern = params["pattern"]
    glob = params.get("glob") or "**/*"
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        return f"[error] bad regex: {exc}"
    hits: list[str] = []
    root_resolved = sb.root.resolve()
    for p in sorted(sb.root.glob(glob)):
        if not p.is_file():
            continue
        try:
            rel = p.resolve().relative_to(root_resolved)
        except ValueError:
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8",
                                                 errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{i}: {line.strip()}")
                    if len(hits) >= 100:
                        hits.append("... (100+ matches, truncated)")
                        return "\n".join(hits)
        except OSError:
            continue
    return "\n".join(hits) if hits else "[no matches]"


def _todo_write(sb: Sandbox, params: dict, state: dict) -> str:
    items = params.get("items", [])
    state["todo"] = list(items)
    rendered = "\n".join(f"  - {it}" for it in items) or "  (empty)"
    return f"[ok] todo list updated ({len(items)} items):\n{rendered}"


DISPATCH: dict[str, Callable[[Sandbox, dict, dict], str]] = {
    "read_file": _read_file,
    "write_file": _write_file,
    "edit_file": _edit_file,
    "run_bash": _run_bash,
    "search": _search,
    "todo_write": _todo_write,
}


def dispatch(name: str, sb: Sandbox, params: dict, state: dict) -> str:
    fn = DISPATCH.get(name)
    if fn is None:
        return f"[error] unknown tool: {name}"
    try:
        return fn(sb, params, state)
    except SandboxError as exc:
        return f"[sandbox-denied] {exc}"
    except Exception as exc:  # never let a tool crash the loop
        return f"[error] tool {name} raised: {exc}"


# ---------------------------------------------------------------------------
# Typed abstraction for tool-trace sequence analysis (ARTICLE_CODING §1.3)
# ---------------------------------------------------------------------------

_CMD_CLASSES = {
    "test": ("pytest", "python -m pytest", "unittest", "nose"),
    "run": ("python", "python3", "node", "go run"),
    "inspect": ("ls", "cat", "head", "tail", "find", "tree", "pwd", "grep", "rg"),
    "vcs": ("git",),
}


def classify_tool_call(name: str, params: dict) -> str:
    """Return a coarse typed label for a tool call, abstracting away
    literal strings so tool-trace clustering doesn't explode on unique
    paths/commands. E.g. read_file:source, run_bash:test, edit_file."""
    if name in ("read_file", "write_file", "edit_file"):
        path = (params.get("path") or "").lower()
        if "test" in path:
            role = "test"
        elif path.endswith((".md", ".txt", ".rst")) or "readme" in path:
            role = "doc"
        elif path.endswith((".cfg", ".toml", ".ini", ".yaml", ".yml", ".json")):
            role = "config"
        else:
            role = "source"
        return f"{name}:{role}"
    if name == "run_bash":
        cmd = (params.get("command") or "").strip()
        try:
            first = shlex.split(cmd)[0] if cmd else ""
        except ValueError:
            first = cmd.split()[0] if cmd else ""
        for klass, prefixes in _CMD_CLASSES.items():
            if any(cmd.startswith(p) or first == p.split()[0] for p in prefixes):
                return f"run_bash:{klass}"
        return "run_bash:other"
    if name == "search":
        return "search"
    if name == "todo_write":
        return "todo_write"
    return name
