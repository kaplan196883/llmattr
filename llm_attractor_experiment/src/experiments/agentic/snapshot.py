"""Working-tree snapshot/restore for AC3 (docs/AGENTIC_AC3_SPEC.md §3).

The causal-laundering design resumes the agent from an *identical*
working-tree state under several context variants. We snapshot the
sandbox tree at the compaction boundary, then restore independent copies
into fresh sandboxes so each resume variant mutates its own tree without
affecting the others.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from src.experiments.agentic.sandbox import Sandbox, SandboxConfig


def snapshot_tree(sandbox: Sandbox, prefix: str = "ac3_snap_") -> Path:
    """Copy the sandbox's working tree into a standalone snapshot dir and
    return its path. The snapshot is a plain directory tree (no _oracle)."""
    snap = Path(tempfile.mkdtemp(prefix=prefix))
    for item in sandbox.root.iterdir():
        dest = snap / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copyfile(item, dest)
    return snap


def restore_tree(snapshot: Path, config: SandboxConfig | None = None,
                 prefix: str = "ac3_resume_") -> Sandbox:
    """Create a fresh Sandbox whose working tree is an independent copy of
    the snapshot. Each call yields an isolated tree."""
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    snapshot = Path(snapshot)
    for item in snapshot.iterdir():
        dest = tmp / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copyfile(item, dest)
    return Sandbox(root=tmp, config=config or SandboxConfig(), _own_tempdir=True)


def discard_snapshot(snapshot: Path) -> None:
    shutil.rmtree(snapshot, ignore_errors=True)
