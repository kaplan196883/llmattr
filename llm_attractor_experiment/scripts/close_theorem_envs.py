"""
Post-process paper.tex to wrap Lemma/Corollary/Conjecture statements
in proper LaTeX theorem environments with closing tags.

Why this exists: scripts/build_paper_tex.py converts ARTICLE.md to
paper.tex but cannot reliably auto-close `\\begin{lemma}` etc. because
the proof body spans multiple paragraphs with no clean closing token.
This script does the closure pass in-place.

Pipeline:
  1. Read paper.tex.
  2. For each `\\textbf{Lemma 1 (caption).}` (and Corollary 1/2,
     Conjecture 1):
       - replace with `\\begin{lemma}[caption]`
       - find the next `\\textbf{Proof.}` (proof opener)
       - insert `\\end{lemma}` immediately before it
       - replace `\\textbf{Proof.}` with `\\begin{proof}`
       - find the next `$\\square$` (proof terminator)
       - replace with `\\end{proof}`
  3. For Conjecture 1 (no proof): close at the marker paragraph
     "The O1 dose-response measurements in §5.6 are consistent with
     this conjecture." Pragmatic — that's the empirical-anchor
     paragraph that sits after the formal statement.
  4. Write paper.tex back in-place. Idempotent: skips any block
     already wrapped in `\\begin{...}` / `\\end{...}`.

Usage:
    python -m scripts.close_theorem_envs

Run AFTER `python -m scripts.build_paper_tex`.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEX_PATH = REPO / "paper" / "paper.tex"


# Theorem patterns in paper.tex. The regex captures the caption inside
# parens. Note: the period is INSIDE the \textbf{} braces in our
# build_paper_tex.py output (because **Lemma 1 (foo).** in markdown
# becomes \textbf{Lemma 1 (foo).}).
PATTERNS = [
    # (theorem env name, pattern matching the textbf opener, pretty label)
    ("lemma",      r"\\textbf\{Lemma\s+1\s*\(([^)]+)\)\.\}",      "Lemma 1"),
    ("corollary",  r"\\textbf\{Corollary\s+1\s*\(([^)]+)\)\.\}",  "Corollary 1"),
    ("corollary",  r"\\textbf\{Corollary\s+2\s*\(([^)]+)\)\.\}",  "Corollary 2"),
    ("conjecture", r"\\textbf\{Conjecture\s+1\s*\(([^)]+)\)\.\}", "Conjecture 1"),
]


def _close_lemma_or_corollary(text: str, env_name: str, pattern: str) -> tuple[str, bool]:
    """Process one Lemma/Corollary instance. Returns (new_text, did_change)."""
    m = re.search(pattern, text)
    if not m:
        return text, False
    open_start = m.start()
    open_end = m.end()
    caption = m.group(1).strip()
    # Find the NEXT \textbf{Proof.} after this opener
    proof_re = re.compile(r"\\textbf\{Proof\.\}", flags=re.M)
    proof_m = proof_re.search(text, pos=open_end)
    if not proof_m:
        # No proof — Conjecture-style. Caller should handle separately.
        return text, False
    proof_start = proof_m.start()
    proof_end = proof_m.end()
    # Find the next $\square$ after the proof opener
    square_re = re.compile(r"\$\\square\$")
    square_m = square_re.search(text, pos=proof_end)
    if not square_m:
        # Proof has no terminator — close at next blank line
        blank = re.compile(r"\n\s*\n")
        bm = blank.search(text, pos=proof_end + 200)
        if not bm:
            return text, False
        close_proof_pos = bm.start()
        replace_proof_terminator = ""
    else:
        close_proof_pos = square_m.start()
        replace_proof_terminator = ""

    # Build the rewritten text
    head = text[:open_start]
    statement_body = text[open_end:proof_start]
    # Trim trailing whitespace before \textbf{Proof.}
    statement_body = statement_body.rstrip()
    proof_body = text[proof_end:close_proof_pos].rstrip()
    after_proof = text[close_proof_pos + (len(square_m.group(0)) if square_m else 0):]

    rewritten = (
        head
        + f"\\begin{{{env_name}}}[{caption}]\n"
        + statement_body
        + f"\n\\end{{{env_name}}}\n\n"
        + "\\begin{proof}\n"
        + proof_body
        + "\n\\end{proof}\n"
        + after_proof
    )
    return rewritten, True


def _close_conjecture(text: str, pattern: str) -> tuple[str, bool]:
    """Process the Conjecture 1 instance. Closes at the
    empirical-anchor paragraph that begins "The O1 dose-response
    measurements" — pragmatic but matches our actual §3.1.3."""
    m = re.search(pattern, text)
    if not m:
        return text, False
    open_start = m.start()
    open_end = m.end()
    caption = m.group(1).strip()
    # Find the empirical-anchor paragraph
    anchor_patterns = [
        r"The O1 dose-response measurements in §5\.6",
        r"The O1 dose-response measurements",
        r"\\paragraph\{Empirical",
    ]
    anchor_pos = None
    for ap in anchor_patterns:
        am = re.search(ap, text[open_end:])
        if am:
            anchor_pos = open_end + am.start()
            break
    if anchor_pos is None:
        # Fallback: close at next \subsubsection or \subsection
        for ap in [r"\\subsubsection\{", r"\\subsection\{", r"\\section\{"]:
            am = re.search(ap, text[open_end:])
            if am:
                anchor_pos = open_end + am.start()
                break
    if anchor_pos is None:
        return text, False
    head = text[:open_start]
    body = text[open_end:anchor_pos].rstrip()
    after = text[anchor_pos:]
    rewritten = (
        head
        + f"\\begin{{conjecture}}[{caption}]\n"
        + body
        + "\n\\end{conjecture}\n\n"
        + after
    )
    return rewritten, True


def main() -> int:
    if not TEX_PATH.exists():
        print(f"error: {TEX_PATH} not found — run scripts/build_paper_tex first")
        return 1
    text = TEX_PATH.read_text(encoding="utf-8")
    n_changes = 0
    for env_name, pattern, label in PATTERNS:
        if env_name == "conjecture":
            new_text, changed = _close_conjecture(text, pattern)
        else:
            new_text, changed = _close_lemma_or_corollary(text, env_name, pattern)
        if changed:
            text = new_text
            n_changes += 1
            print(f"  closed {label} ({env_name})")
        else:
            # Check whether already in begin/end form
            if re.search(r"\\begin\{" + env_name + r"\}\[" + re.escape(label.split()[0]) + ".*", text):
                print(f"  {label}: already wrapped (idempotent skip)")
            else:
                print(f"  {label}: NOT FOUND — manual check needed")
    if n_changes:
        TEX_PATH.write_text(text, encoding="utf-8")
        print(f"\nwrote {TEX_PATH} ({n_changes} environments closed)")
    else:
        print("\nno changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
