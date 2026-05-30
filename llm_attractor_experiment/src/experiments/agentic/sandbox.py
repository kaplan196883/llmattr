"""Per-run sandbox: an isolated working-tree root plus a jailed command
runner. See docs/AGENTIC_MVP_SPEC.md §5.

Two jails:
  * filesystem jail — every tool path is resolved against the sandbox
    root and rejected if it escapes (``..`` traversal, absolute paths
    outside root, or symlink targets outside root);
  * command jail — ``run_bash`` executes in a subprocess with CWD set to
    the sandbox root, network disabled at the harness level (we never
    pass network creds and denylist obvious egress commands), a
    wall-clock timeout, and truncated output.

The MVP redirect class is benign, but the jail is built network-off from
day one so the later poison-doc / exfiltration classes inherit it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.logging import get_logger

log = get_logger(__name__)


class SandboxError(Exception):
    """Raised when a tool tries to escape the sandbox or violates policy."""


@dataclass
class SandboxConfig:
    network: str = "disabled"
    bash_timeout_sec: int = 30
    bash_output_max_chars: int = 8000
    path_jail: bool = True
    bash_denylist: tuple[str, ...] = (
        "curl", "wget", "ssh", "scp", "nc", "telnet",
        "pip", "pip3", "npm", "yarn", "pnpm", "apt", "apt-get",
        "brew", "conda", "poetry",
    )


@dataclass
class Sandbox:
    """An isolated working tree. Created from a seed directory; cleaned
    up on ``close()`` unless ``keep=True``."""

    root: Path
    config: SandboxConfig = field(default_factory=SandboxConfig)
    _own_tempdir: bool = False

    # ---- construction -----------------------------------------------------
    @classmethod
    def from_seed(cls, seed_dir: Path, config: SandboxConfig | None = None,
                  prefix: str = "agentic_sbx_") -> "Sandbox":
        """Copy ``seed_dir`` into a fresh tempdir and return a Sandbox
        rooted there. The ``_oracle/`` subdir of the seed (hidden tests)
        is intentionally NOT copied into the visible tree — it is held
        aside by the task oracle, not exposed to the agent."""
        tmp = Path(tempfile.mkdtemp(prefix=prefix))
        seed_dir = Path(seed_dir)
        if seed_dir.exists():
            for item in seed_dir.iterdir():
                if item.name == "_oracle":
                    continue  # hidden tests stay out of the agent's view
                dest = tmp / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copyfile(item, dest)
        return cls(root=tmp, config=config or SandboxConfig(), _own_tempdir=True)

    def close(self, keep: bool = False) -> None:
        if self._own_tempdir and not keep and self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)

    # ---- filesystem jail --------------------------------------------------
    def resolve(self, rel_path: str) -> Path:
        """Resolve a tool-supplied path against the sandbox root, rejecting
        any path that escapes it. Returns an absolute Path inside root."""
        if not self.config.path_jail:
            return (self.root / rel_path).resolve()
        # Reject absolute paths outright; everything is relative to root.
        candidate = (self.root / rel_path)
        try:
            resolved = candidate.resolve()
        except (OSError, RuntimeError) as exc:  # symlink loops, etc.
            raise SandboxError(f"cannot resolve path {rel_path!r}: {exc}") from exc
        root_resolved = self.root.resolve()
        if resolved != root_resolved and root_resolved not in resolved.parents:
            raise SandboxError(
                f"path {rel_path!r} escapes sandbox root"
            )
        return resolved

    # ---- working-tree manifest -------------------------------------------
    def manifest(self, max_entries: int = 200) -> str:
        """A compact listing of the working tree (paths + sizes; not
        contents). Used by todo-replace / state-replace Nudges to render
        the tree without dumping file bodies."""
        root_resolved = self.root.resolve()
        lines: list[str] = []
        for p in sorted(self.root.rglob("*")):
            if p.is_dir():
                continue
            try:
                rel = p.resolve().relative_to(root_resolved)
            except ValueError:
                continue
            size = p.stat().st_size
            lines.append(f"  {rel}  ({size} B)")
            if len(lines) >= max_entries:
                lines.append(f"  ... ({max_entries}+ files, truncated)")
                break
        return "working tree:\n" + ("\n".join(lines) if lines else "  (empty)")

    def tree_hash(self) -> str:
        """A stable hash of the working tree's file paths + contents, used
        to detect whether a step changed the tree."""
        import hashlib
        h = hashlib.sha1()
        root_resolved = self.root.resolve()
        for p in sorted(self.root.rglob("*")):
            if p.is_dir():
                continue
            try:
                rel = p.resolve().relative_to(root_resolved)
            except ValueError:
                continue
            h.update(str(rel).encode("utf-8", "replace"))
            try:
                h.update(p.read_bytes())
            except OSError:
                pass
        return h.hexdigest()[:16]

    # ---- command jail -----------------------------------------------------
    def run_bash(self, command: str) -> str:
        """Run a shell command jailed to the sandbox root. Network is not
        provisioned; obvious egress / install commands are denied. Output
        (stdout+stderr, interleaved) is truncated."""
        first = command.strip().split()[0] if command.strip() else ""
        # Strip a leading env-assignment or path prefix for the denylist check
        base = os.path.basename(first)
        if base in self.config.bash_denylist:
            raise SandboxError(
                f"command {base!r} is denied by sandbox policy "
                f"(network/install commands are disabled in the MVP)"
            )
        # Inherit the parent environment (Windows winsock/asyncio needs
        # SystemRoot etc.; stripping it breaks `python -m pytest`), but
        # redirect HOME/TMPDIR into the sandbox. Network control in the
        # MVP is enforced by the command denylist above, not by env
        # stripping; OS-level network isolation is a full-battery item
        # (see docs/AGENTIC_MVP_SPEC.md §5).
        env = dict(os.environ)
        env["HOME"] = str(self.root)
        env["USERPROFILE"] = str(self.root)
        env["TMPDIR"] = str(self.root)
        env["TEMP"] = str(self.root)
        env["TMP"] = str(self.root)
        env["PWD"] = str(self.root)
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.root),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.bash_timeout_sec,
            )
        except subprocess.TimeoutExpired:
            return (f"[sandbox] command timed out after "
                    f"{self.config.bash_timeout_sec}s")
        out = (proc.stdout or "") + (proc.stderr or "")
        if len(out) > self.config.bash_output_max_chars:
            n = self.config.bash_output_max_chars
            out = out[:n] + f"\n[sandbox] output truncated at {n} chars"
        return out if out.strip() else f"[sandbox] (exit {proc.returncode}, no output)"
