"""Task suite loader + grading oracle. See docs/AGENTIC_MVP_SPEC.md §4.

A task is a seed directory (copied into the sandbox, visible to the
agent) plus a hidden ``_oracle/`` directory of authoritative tests that
grade the agent's *source* changes at the terminal step. The oracle
tests are never copied into the visible tree (Sandbox.from_seed skips
``_oracle``); they are applied fresh at grading time so the agent cannot
satisfy the oracle by editing the visible tests.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.experiments.agentic.sandbox import Sandbox
from src.utils.logging import get_logger

log = get_logger(__name__)

REPO = Path(__file__).resolve().parents[3]


@dataclass
class Task:
    id: str
    goal: str
    seed_dir: Path
    oracle: str            # pytest | pytest_plus_dupcheck | pytest_full
    redirect: str


def load_tasks(config: dict) -> list[Task]:
    tasks = []
    for t in config["tasks"]:
        seed = Path(t["seed_dir"])
        if not seed.is_absolute():
            seed = REPO / seed
        tasks.append(Task(
            id=t["id"], goal=t["goal"], seed_dir=seed,
            oracle=t["oracle"], redirect=t["redirect"],
        ))
    return tasks


def _pytest_passed(output: str) -> bool:
    low = output.lower()
    if "no tests ran" in low:
        return False
    if re.search(r"\d+ (failed|error)", low):
        return False
    return bool(re.search(r"\d+ passed", low))


def _dupcheck_ok(sandbox: Sandbox) -> bool:
    """refactor_extract: the retry body should no longer be duplicated.
    The seed has the `attempt += 1` retry body twice (once per function);
    a correct extraction (shared helper or decorator) leaves it at most
    once."""
    src = sandbox.resolve("service.py")
    if not src.exists():
        return False
    text = src.read_text(encoding="utf-8", errors="replace")
    return text.count("attempt += 1") <= 1


def run_oracle(task: Task, sandbox: Sandbox) -> tuple[bool, str]:
    """Grade the agent's final working tree. Returns (passed, detail)."""
    oracle_dir = task.seed_dir / "_oracle"
    if not oracle_dir.exists():
        return False, f"[oracle] missing {oracle_dir}"

    # Copy oracle test files into the sandbox under a reserved prefix so
    # they don't collide with (or get shadowed by) the agent's edits.
    copied: list[Path] = []
    for tf in sorted(oracle_dir.glob("*.py")):
        dest = sandbox.root / f"_oracle_{tf.name}"
        shutil.copyfile(tf, dest)
        copied.append(dest)
    try:
        targets = " ".join(f"_oracle_{tf.name}" for tf in sorted(oracle_dir.glob("*.py")))
        output = sandbox.run_bash(f"python -m pytest -q {targets}")
        passed = _pytest_passed(output)
        if passed and task.oracle == "pytest_plus_dupcheck":
            if not _dupcheck_ok(sandbox):
                return False, f"[oracle] tests passed but duplication remains\n{output}"
        return passed, output
    finally:
        for p in copied:
            p.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# self-test: verify each oracle FAILS on the unmodified seed (the bug is
# present) and the seed dirs are well-formed.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import yaml
    from src.experiments.agentic.sandbox import SandboxConfig

    cfg = yaml.safe_load((REPO / "configs/agentic/AC1_mvp.yaml").read_text())
    for task in load_tasks(cfg):
        sb = Sandbox.from_seed(task.seed_dir, SandboxConfig())
        passed, detail = run_oracle(task, sb)
        # On the seed, the oracle should FAIL (bug present / stub unimplemented)
        verdict = "OK (seed fails as expected)" if not passed else "!! seed already passes"
        last = detail.strip().splitlines()[-1] if detail.strip() else ""
        print(f"{task.id:18s} oracle={task.oracle:22s} seed_passed={passed}  {verdict}  | {last}")
        sb.close()
