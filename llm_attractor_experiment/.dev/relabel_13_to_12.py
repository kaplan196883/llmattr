"""Relabel markdown §13 → §12 to match LaTeX auto-numbering.

The build pipeline strips `## 12. References` (sent to refs.bib) so
LaTeX auto-numbering goes 11 → 12 for the supplementary appendix.
The markdown labels were §13.X but the rendered PDF showed §12.X — a
pre-existing off-by-one. This script aligns the markdown labels to
match the rendered PDF.

Run AFTER restructure_phase1.py.
"""
from __future__ import annotations

import re
from pathlib import Path


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")

    # === Heading rename ===
    text = text.replace(
        "## 13. Supplementary appendix",
        "## 12. Supplementary appendix",
    )

    n_subsec = 0
    new_lines = []
    for line in text.split("\n"):
        if line.startswith("### 13."):
            new_line = "### 12." + line[len("### 13."):]
            new_lines.append(new_line)
            n_subsec += 1
        else:
            new_lines.append(line)
    text = "\n".join(new_lines)
    print(f"renamed {n_subsec} ### 13.X subsections → ### 12.X")

    # === Body §-ref renumber: §13.X → §12.X ===
    # Pattern: literal "§" + "13." + digits (with optional .digits).
    # Anchored on literal §, no \S non-whitespace ambiguity.
    pat_section = re.compile(r"§13\.(\d+(?:\.\d+)?)")
    text, n_section = pat_section.subn(lambda m: f"§12.{m.group(1)}", text)
    print(f"body §13.X → §12.X subs: {n_section}")

    # === tex-raw \S13.X → \S12.X ===
    # In Python regex, to match a literal backslash + S in text we need
    # the regex `\\S` (escape-for-literal-backslash + literal-S).
    # Written as a raw string this is r"\\S" (3 chars: \, \, S).
    # NOT r"\\\\S" (which would match \\S — two backslashes).
    pat_backslashS = re.compile(r"\\S13\.(\d+(?:\.\d+)?)")
    text, n_backslashS = pat_backslashS.subn(
        lambda m: f"\\S12.{m.group(1)}", text
    )
    print(f"tex-raw \\S13.X → \\S12.X subs: {n_backslashS}")

    ARTICLE.write_text(text, encoding="utf-8")

    # === Verification ===
    leftover_13 = re.findall(r"§13\.\d", text)
    leftover_S13 = re.findall(r"\\S13\.\d", text)
    print(f"leftover §13.X: {len(leftover_13)}")
    print(f"leftover \\S13.X: {len(leftover_S13)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
