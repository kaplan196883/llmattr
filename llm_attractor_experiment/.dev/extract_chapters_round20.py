"""Slice ARTICLE.md into per-chapter files for GPT-5.5 review (round 20).

Captures chapters 1-9 + abstract+plain-language summary as context.
Skips Acknowledgments (10), References (12), Supplementary (11).
"""
from __future__ import annotations

from pathlib import Path
import re


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
OUT = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev")

# (chapter_num, heading_text, output_filename)
CHAPTERS = [
    (1, "## 1. Introduction", "round20_chapter_1_introduction.md"),
    (2, "## 2. Background and related work", "round20_chapter_2_background.md"),
    (3, "## 3. Formal framework and hypotheses", "round20_chapter_3_framework.md"),
    (4, "## 4. Methods", "round20_chapter_4_methods.md"),
    (5, "## 5. Results", "round20_chapter_5_results.md"),
    (6, "## 6. Discussion", "round20_chapter_6_discussion.md"),
    (7, "## 7. Limitations", "round20_chapter_7_limitations.md"),
    (8, "## 8. Future directions", "round20_chapter_8_future.md"),
    (9, "## 9. Data, code, and reproducibility", "round20_chapter_9_repro.md"),
]


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")

    # Front matter (title + abstract + plain-language) is shared context.
    intro_idx = text.find("## 1. Introduction")
    front = text[:intro_idx].rstrip()
    (OUT / "round20_front_matter.md").write_text(front + "\n", encoding="utf-8")
    print(f"front matter: {len(front.splitlines())} lines")

    # Top-level section boundaries
    headings = [
        (m.start(), m.group(0))
        for m in re.finditer(r"^## .+$", text, flags=re.MULTILINE)
    ]
    headings.sort()

    for chap_num, heading, fname in CHAPTERS:
        # Find this heading in text
        i = next((idx for idx, h in headings if h == heading), None)
        if i is None:
            print(f"WARN chapter {chap_num} heading not found: {heading!r}")
            continue
        # Find next ## heading
        next_idx = next((idx for idx, _ in headings if idx > i), len(text))
        chapter_text = text[i:next_idx].rstrip()
        (OUT / fname).write_text(chapter_text + "\n", encoding="utf-8")
        n_lines = len(chapter_text.splitlines())
        print(f"chapter {chap_num} ({fname}): {n_lines} lines")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
