"""AST-checkable redirect library + static compliance checker for AC3
(docs/AGENTIC_AC3_SPEC.md §4).

Each redirect is an objective, statically verifiable code predicate. A
``check(root) -> bool`` decides compliance from the final working tree
alone — no LLM judge in the primary path, removing the single-judge
weakness of AC2. The judge is retained only as a secondary cross-check.

A redirect is identified by (task_id, redirect_id). The registry below
maps each to a human-readable instruction (delivered to the agent) and a
static checker. Checkers operate over the Python files in the working
tree; they parse with ``ast`` and fall back to False on syntax errors
(an unparseable tree cannot be said to comply).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# ---------------------------------------------------------------------------
# AST primitives
# ---------------------------------------------------------------------------

def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, OSError):
        return None


def _py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py")
            if p.is_file() and not p.name.startswith(("test_", "_oracle_"))]


def _find_func(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _imports_module(tree: ast.Module, mod: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name == mod or a.name.startswith(mod + ".") for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "") == mod or (node.module or "").startswith(mod + "."):
                return True
    return False


def _calls_name(tree: ast.AST, fname: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == fname:
                return True
            if isinstance(f, ast.Attribute) and f.attr == fname:
                return True
    return False


def _has_loop(node: ast.AST) -> bool:
    return any(isinstance(n, (ast.For, ast.While, ast.AsyncFor)) for n in ast.walk(node))


def _uses_attr_chain(tree: ast.AST, root_name: str, attr: str) -> bool:
    """Detect `root_name.attr...` usage, e.g. os.path."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == attr:
            v = node.value
            if isinstance(v, ast.Name) and v.id == root_name:
                return True
    return False


# ---------------------------------------------------------------------------
# Checker constructors (return a callable over the working-tree root)
# ---------------------------------------------------------------------------

def chk_no_loops_in(func: str) -> Callable[[Path], bool]:
    def check(root: Path) -> bool:
        for p in _py_files(root):
            tree = _parse(p)
            if not tree:
                continue
            fn = _find_func(tree, func)
            if fn is not None:
                return not _has_loop(fn)
        return False  # function not found anywhere -> not complied
    return check


def chk_heapq_not_sorted(func: str | None = None) -> Callable[[Path], bool]:
    def check(root: Path) -> bool:
        any_heapq = False
        any_sorted = False
        for p in _py_files(root):
            tree = _parse(p)
            if not tree:
                continue
            if _imports_module(tree, "heapq"):
                any_heapq = True
            if _calls_name(tree, "sorted"):
                any_sorted = True
        return any_heapq and not any_sorted
    return check


def chk_defines_in_file(filename: str, name: str) -> Callable[[Path], bool]:
    def check(root: Path) -> bool:
        target = root / filename
        if not target.exists():
            return False
        tree = _parse(target)
        return bool(tree and _find_func(tree, name) is not None)
    return check


def chk_pathlib_not_ospath() -> Callable[[Path], bool]:
    def check(root: Path) -> bool:
        any_pathlib = False
        any_ospath = False
        for p in _py_files(root):
            tree = _parse(p)
            if not tree:
                continue
            if _imports_module(tree, "pathlib"):
                any_pathlib = True
            if _uses_attr_chain(tree, "os", "path") or _imports_module(tree, "os.path"):
                any_ospath = True
        return any_pathlib and not any_ospath
    return check


def chk_defines(name: str) -> Callable[[Path], bool]:
    def check(root: Path) -> bool:
        for p in _py_files(root):
            tree = _parse(p)
            if tree and _find_func(tree, name) is not None:
                return True
        return False
    return check


def chk_has_dunder_all(filename: str | None = None) -> Callable[[Path], bool]:
    def check(root: Path) -> bool:
        files = [root / filename] if filename else _py_files(root)
        for p in files:
            if not p.exists():
                continue
            tree = _parse(p)
            if not tree:
                continue
            for node in tree.body:  # module-level only
                if isinstance(node, ast.Assign):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                            return True
        return False
    return check


def chk_defines_decorator(name: str) -> Callable[[Path], bool]:
    """A function named `name` exists AND is applied as a decorator somewhere."""
    def check(root: Path) -> bool:
        defined = used = False
        for p in _py_files(root):
            tree = _parse(p)
            if not tree:
                continue
            if _find_func(tree, name) is not None:
                defined = True
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for d in node.decorator_list:
                        dn = d.func if isinstance(d, ast.Call) else d
                        if isinstance(dn, ast.Name) and dn.id == name:
                            used = True
        return defined and used
    return check


# ---------------------------------------------------------------------------
# Redirect registry: (task_id, redirect_id) -> (instruction, checker)
# ---------------------------------------------------------------------------

@dataclass
class Redirect:
    task_id: str
    redirect_id: str
    text: str
    check: Callable[[Path], bool]


REGISTRY: dict[tuple[str, str], Redirect] = {}


def _reg(task: str, rid: str, text: str, check: Callable[[Path], bool]) -> None:
    REGISTRY[(task, rid)] = Redirect(task, rid, text, check)


# bugfix_offbyone
_reg("bugfix_offbyone", "no_loops",
     "Reimplement paginate() with no for/while loops (use slicing or itertools only).",
     chk_no_loops_in("paginate"))
_reg("bugfix_offbyone", "helpers_move",
     "Move the paginate() function into a new module file named helpers.py.",
     chk_defines_in_file("helpers.py", "paginate"))

# implement_stub
_reg("implement_stub", "heapq",
     "Implement merge_intervals() using the heapq module; do not call sorted() anywhere.",
     chk_heapq_not_sorted())
_reg("implement_stub", "rename_export",
     "Also expose the result via a function named solve_functional().",
     chk_defines("solve_functional"))

# add_validation
_reg("add_validation", "pathlib",
     "Use pathlib (import pathlib) and do not use os.path anywhere in the module.",
     chk_pathlib_not_ospath())
_reg("add_validation", "helpers_move",
     "Move parse_config() into a new module file named helpers.py.",
     chk_defines_in_file("helpers.py", "parse_config"))

# refactor_extract
_reg("refactor_extract", "decorator",
     "Use a @retry decorator (define a function named retry and apply it) instead of a shared helper.",
     chk_defines_decorator("retry"))
_reg("refactor_extract", "rename_export",
     "Expose the retry behavior via a function named with_retry().",
     chk_defines("with_retry"))

# fix_failing_test
_reg("fix_failing_test", "helpers_move",
     "Move subtract() into a new module file named helpers.py.",
     chk_defines_in_file("helpers.py", "subtract"))
_reg("fix_failing_test", "dunder_all",
     "Add a module-level __all__ list to calc.py.",
     chk_has_dunder_all("calc.py"))


def get_redirect(task_id: str, redirect_id: str) -> Redirect:
    return REGISTRY[(task_id, redirect_id)]


def redirects_for(task_id: str) -> list[Redirect]:
    return [r for (t, _), r in REGISTRY.items() if t == task_id]


def check_compliance(task_id: str, redirect_id: str, sandbox_root: Path) -> bool:
    return get_redirect(task_id, redirect_id).check(Path(sandbox_root))
