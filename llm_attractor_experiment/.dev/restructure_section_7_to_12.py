"""Round-19 restructure: §7-§12 full restructure for Nature-style flow.

Before:
  §7  Limitations            (9 fragmented subsections)
  §8  Future work             (9 overlapping subsections)
  §9  Methods appendix        (7 — duplicates content in §12 Supp)
  §10 Reproducibility         (8 fragmented)
  §11 Acknowledgments
  §12 References              (stripped to refs.bib at build)
  §12 Supplementary appendix  (17 sprawling subsections)

After:
  §7  Limitations             (5 thematic, content-led titles)
  §8  Future directions       (5 grouped)
  §9  Data, code, reproducibility  (4 — replaces old §10; old §9 deleted)
  §10 Acknowledgments         (was §11)
  §12 References              (still stripped to refs.bib)
  §11 Supplementary appendix  (12 — was §12, with old §9 Methods merged in)

Body §-ref cascade applied globally afterwards (old §9.X→§11.X,
§10.X→§9.X, §12.X→§11.X).

Run AFTER restructure_section6.py.
"""
from __future__ import annotations

import re
from pathlib import Path


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
NEW_7_8_9 = Path(
    r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round19_new_7_8_9.md"
)
NEW_SUPP = Path(
    r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round19_new_supplementary.md"
)


# Body §-ref cascade. Single dict-callback regex; longest-key-first
# alternation so e.g. §12.17 matches before §12.1.
#
# Mapping rationale:
#   §9.X  (old Methods appendix, being deleted)         → §11.X (new Supp)
#   §10.X (old Reproducibility, replaced by new §9)      → §9.X
#   §12.X (old Supplementary)                            → §11.X (new Supp)
SECTION_REF_MAP: dict[str, str] = {
    # §9.X (old Methods) → merged supp subsections
    "9.1": "11.4",   # exact metric defs → metric defs/clustering/PCA
    "9.2": "11.5",   # perturbation injection mechanics
    "9.3": "11.4",   # K-means choice/stability → merged into 11.4
    "9.4": "11.4",   # PCA stability → merged into 11.4
    "9.5": "11.8",   # animation rendering → in viz toolkit
    "9.6": "11.6",   # prompt templates → prompts+models
    "9.7": "11.6",   # model versioning → prompts+models
    # §10.X (old Reproducibility) → new §9 Data/code
    "10.1": "9.1",
    "10.2": "9.2",
    "10.3": "9.3",
    "10.4": "9.4",
    "10.5": "9.1",   # per-experiment catalog → trajectories/audit tables
    "10.6": "9.1",   # stage reports → trajectories/audit tables
    "10.7": "9.4",   # test coverage → tests/claim verification
    "10.8": "9.2",   # repository layout → codebase/licenses/env
    # §12.X (old Supp) → new §11 Supp
    "12.1": "11.1",
    "12.2": "11.2",
    "12.3": "11.3",
    "12.4": "11.4",
    "12.5": "11.5",
    "12.6": "11.8",   # animation rendering merged into viz toolkit
    "12.7": "11.6",
    "12.8": "11.6",
    "12.9": "11.7",
    "12.10": "11.7",
    "12.11": "11.8",
    "12.12": "11.9",
    "12.13": "11.10",
    "12.14": "11.11",
    "12.15": "11.12",
    "12.16": "11.12",
    "12.17": "11.12",  # pointers section deleted; closing fallback
}


def renumber_section_refs(text: str) -> tuple[str, int]:
    """Apply SECTION_REF_MAP to body §X.Y and \\SX.Y refs in-text."""
    keys_sorted = sorted(SECTION_REF_MAP.keys(), key=lambda k: -len(k))
    pattern = "|".join(re.escape(k) for k in keys_sorted)

    n = 0

    pat_section = re.compile(rf"§({pattern})(\.\d+)?\b")

    def replace_section(m: re.Match) -> str:
        nonlocal n
        n += 1
        old = m.group(1)
        suffix = m.group(2) or ""
        new = SECTION_REF_MAP[old]
        return f"§{new}{suffix}"

    text = pat_section.sub(replace_section, text)

    # tex-raw \SX.Y form. In a regex, to match a literal backslash + S
    # we write `\\S` (3 chars: \, \, S). NOT r"\\\\S".
    pat_texraw = re.compile(rf"\\S({pattern})(\.\d+)?\b")

    def replace_texraw(m: re.Match) -> str:
        nonlocal n
        n += 1
        old = m.group(1)
        suffix = m.group(2) or ""
        new = SECTION_REF_MAP[old]
        return f"\\S{new}{suffix}"

    text = pat_texraw.sub(replace_texraw, text)
    return text, n


def replace_block(text: str, start_anchor: str, end_anchor: str | None,
                  replacement: str) -> tuple[str, bool]:
    """Replace text between start_anchor (inclusive) and end_anchor (exclusive).

    If end_anchor is None, replace from start_anchor to end of file.
    Returns (new_text, success).
    """
    i = text.find(start_anchor)
    if i == -1:
        return text, False
    if end_anchor is None:
        return text[:i] + replacement, True
    j = text.find(end_anchor, i + len(start_anchor))
    if j == -1:
        return text, False
    return text[:i] + replacement + text[j:], True


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")
    new_7_8_9 = NEW_7_8_9.read_text(encoding="utf-8").rstrip()
    new_supp = NEW_SUPP.read_text(encoding="utf-8").rstrip()

    # Split new_7_8_9 into the three sections.
    # File contains: ## 7. ..., ## 8. ..., ## 9. ...
    parts = new_7_8_9.split("\n## ")
    # parts[0] = "## 7. Limitations\n..."
    # parts[1] = "8. Future directions\n..."
    # parts[2] = "9. Data, code, ..."
    new_section_7 = parts[0].rstrip() + "\n\n"
    new_section_8 = "## " + parts[1].rstrip() + "\n\n"
    new_section_9 = "## " + parts[2].rstrip() + "\n\n"

    # === Block replacements ===
    # Order: do them top-down (line numbers don't matter; we use anchor strings).

    # Replace §7 block
    text, ok = replace_block(
        text,
        start_anchor="## 7. Limitations\n",
        end_anchor="## 8. Future work\n",
        replacement=new_section_7,
    )
    print(f"§7 block replaced: {ok}")
    assert ok

    # Replace §8 block
    text, ok = replace_block(
        text,
        start_anchor="## 8. Future work\n",
        end_anchor="## 9. Methods appendix\n",
        replacement=new_section_8,
    )
    print(f"§8 block replaced: {ok}")
    assert ok

    # Delete §9 Methods appendix block (replace with empty string)
    text, ok = replace_block(
        text,
        start_anchor="## 9. Methods appendix\n",
        end_anchor="## 10. Reproducibility statement\n",
        replacement="",
    )
    print(f"§9 Methods appendix deleted: {ok}")
    assert ok

    # Replace §10 Reproducibility with new §9 Data/code
    text, ok = replace_block(
        text,
        start_anchor="## 10. Reproducibility statement\n",
        end_anchor="## 11. Acknowledgments\n",
        replacement=new_section_9,
    )
    print(f"§10 Reproducibility replaced with new §9: {ok}")
    assert ok

    # Renumber §11 Acknowledgments → §10 Acknowledgments (heading only)
    if "## 11. Acknowledgments\n" not in text:
        raise RuntimeError("Acknowledgments heading not found")
    text = text.replace(
        "## 11. Acknowledgments\n",
        "## 10. Acknowledgments\n",
    )
    print("§11 Acknowledgments → §10 Acknowledgments (heading renumbered)")

    # Replace §12 Supplementary appendix block (to end of file)
    text, ok = replace_block(
        text,
        start_anchor="## 12. Supplementary appendix\n",
        end_anchor=None,
        replacement=new_supp + "\n",
    )
    print(f"§12 Supp replaced with new §11 Supp: {ok}")
    assert ok

    # Note: ## 12. References stays in place (build script strips it to
    # refs.bib at LaTeX build time, so it does not consume a section number).

    # === Global body §-ref cascade ===
    text, n_renumbered = renumber_section_refs(text)
    print(f"body §-ref renumbering substitutions: {n_renumbered}")

    ARTICLE.write_text(text, encoding="utf-8")

    # === Verification ===
    leftover_old_refs = re.findall(
        r"§(?:9\.\d|10\.\d|12\.\d)\b", text
    )
    leftover_old_texraw = re.findall(
        r"\\S(?:9\.\d|10\.\d|12\.\d)\b", text
    )
    print(f"leftover old-style §X.Y refs: {len(leftover_old_refs)}")
    if leftover_old_refs:
        print(f"  examples: {leftover_old_refs[:10]}")
    print(f"leftover old-style \\SX.Y refs: {len(leftover_old_texraw)}")
    if leftover_old_texraw:
        print(f"  examples: {leftover_old_texraw[:10]}")

    # Quick sanity check: top-level section count
    section_headings = re.findall(r"^## (\d+\.[^\n]+)", text, flags=re.M)
    print(f"top-level sections after restructure: {len(section_headings)}")
    for h in section_headings:
        print(f"  {h}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
