"""Strip GPT/AI-style typography from ARTICLE.md.

Targets:
- em-dashes (—) — classic GPT prose tell, replace with comma/period
- en-dashes (–) — both numeric ranges and compound modifiers, replace with -
- ellipses (…) — replace with ...

Preserves: math, code blocks, table structure, list indentation.
"""
from __future__ import annotations

import re
from pathlib import Path


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")
    n_em_before = text.count("—")
    n_en_before = text.count("–")
    n_ell_before = text.count("…")

    # === Em-dash handling ===
    # When em-dash has both surrounding spaces, treat as in-prose pause.
    # Default replacement is ", " (comma + space). Avoid creating double
    # punctuation by handling preceding-punctuation cases first.

    # 1. Punctuation before em-dash: drop the dash entirely
    text = text.replace(", — ", ", ")
    text = text.replace("; — ", "; ")
    text = text.replace(": — ", ": ")

    # 2. Period before em-dash: keep period, drop dash
    text = text.replace(". — ", ". ")
    text = text.replace("? — ", "? ")
    text = text.replace("! — ", "! ")

    # 3. Em-dash before sentence-final punctuation: drop dash
    text = text.replace(" — .", ".")
    text = text.replace(" — ;", ";")
    text = text.replace(" — :", ":")
    text = text.replace(" — ,", ",")

    # 4. Default: space-emdash-space → comma-space
    text = text.replace(" — ", ", ")

    # 5. One-sided spaces (rare, e.g. " —and" or "word— ")
    text = text.replace("— ", ", ")
    text = text.replace(" —", ",")

    # 6. Any leftover em-dash (no surrounding spaces): treat as hyphen
    text = text.replace("—", "-")

    # === En-dash handling ===
    # Convert all en-dashes to ASCII hyphens. This covers:
    #   - numeric ranges (5–400 → 5-400)
    #   - compound modifiers (state–generator–nudge → state-generator-nudge)
    text = text.replace("–", "-")

    # === Ellipsis ===
    text = text.replace("…", "...")

    # === Cleanup: double commas left over from punctuation collisions ===
    text = re.sub(r",\s+,", ",", text)
    text = text.replace(",,", ",")

    # === Cleanup: double spaces inside lines (NOT touching indentation) ===
    # Only collapse 2+ spaces between non-whitespace chars on the same line.
    text = re.sub(r"(?<=\S)  +(?=\S)", " ", text)

    # === Verify no AI-typography characters remain ===
    n_em_after = text.count("—")
    n_en_after = text.count("–")
    n_ell_after = text.count("…")

    ARTICLE.write_text(text, encoding="utf-8")

    print(f"em-dashes: {n_em_before} -> {n_em_after}")
    print(f"en-dashes: {n_en_before} -> {n_en_after}")
    print(f"ellipses:  {n_ell_before} -> {n_ell_after}")

    if n_em_after or n_en_after or n_ell_after:
        print("WARNING: residue remains")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
