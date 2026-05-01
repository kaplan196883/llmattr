"""Round-21 paper-wide restructure: replace §1-§9 with GPT-5.5 drafted versions.

Implementing 30 review items across all 5 tiers from round-20 advice.

Each chapter is loaded from a .dev/round21_new_chN.md file and replaces the
corresponding old §N block in ARTICLE.md, using anchor strings to delimit.

§10 Acknowledgments, §12 References, §11 Supplementary appendix are unchanged.

Run AFTER restructure_section_7_to_12.py + strip_ai_dashes.py.
"""
from __future__ import annotations

from pathlib import Path


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
DEV = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev")

CHAPTERS = [
    # (chapter_num, start_anchor, end_anchor_or_None, draft_filename)
    (1, "## 1. Introduction\n", "## 2. Background and related work\n",
     "round21_new_ch1.md"),
    (2, "## 2. Background and related work\n", "## 3. Formal framework and hypotheses\n",
     "round21_new_ch2.md"),
    (3, "## 3. Formal framework and hypotheses\n", "## 4. Methods\n",
     "round21_new_ch3.md"),
    (4, "## 4. Methods\n", "## 5. Results\n",
     "round21_new_ch4.md"),
    (5, "## 5. Results\n", "## 6. Discussion\n",
     "round21_new_ch5.md"),
    (6, "## 6. Discussion\n", "## 7. Limitations\n",
     "round21_new_ch6.md"),
    (7, "## 7. Limitations\n", "## 8. Future directions\n",
     "round21_new_ch7.md"),
    (8, "## 8. Future directions\n", "## 9. Data, code, and reproducibility\n",
     "round21_new_ch8.md"),
    (9, "## 9. Data, code, and reproducibility\n", "## 10. Acknowledgments\n",
     "round21_new_ch9.md"),
]


def replace_block(text: str, start_anchor: str, end_anchor: str,
                  replacement: str) -> tuple[str, bool]:
    """Replace text between start_anchor (inclusive) and end_anchor (exclusive)."""
    i = text.find(start_anchor)
    if i == -1:
        return text, False
    j = text.find(end_anchor, i + len(start_anchor))
    if j == -1:
        return text, False
    return text[:i] + replacement + text[j:], True


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")

    for chap_num, start_anchor, end_anchor, fname in CHAPTERS:
        new_block = (DEV / fname).read_text(encoding="utf-8").rstrip() + "\n\n"
        text, ok = replace_block(text, start_anchor, end_anchor, new_block)
        print(f"§{chap_num} replaced: {ok}")
        if not ok:
            raise RuntimeError(f"Failed to replace §{chap_num}: anchor not found")

    ARTICLE.write_text(text, encoding="utf-8")

    # Verification
    import re
    section_headings = re.findall(r"^## (\d+\.[^\n]+)", text, flags=re.M)
    print(f"\ntop-level sections after round-21: {len(section_headings)}")
    for h in section_headings:
        print(f"  {h}")

    n_em = text.count("—")  # em-dash
    n_en = text.count("–")  # en-dash
    n_ell = text.count("…")  # ellipsis
    print(f"\nAI-typography residue: em-dashes={n_em}, en-dashes={n_en}, ellipses={n_ell}")
    if n_em or n_en or n_ell:
        print("WARNING: AI-typography residue detected; rerun strip_ai_dashes.py")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
