"""Strip AI-typography artefacts from ARTICLE.md.

- em dash `—`  -> spaced ASCII hyphen ` - `
- en dash `-`  -> ASCII hyphen `-`
- minus sign `-` -> ASCII hyphen `-`

Does NOT touch leading-indent whitespace or table padding.
Only collapses double-spaces that appear *after some non-space content*
on a line, so we don't damage bullet sub-item indentation.
"""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")
orig_len = len(text)

counts = {
    "em_dash": text.count("—"),
    "en_dash": text.count("–"),
    "minus":   text.count("−"),
}

# Replace dashes
text = text.replace(" — ", " - ")
text = text.replace("—", " - ")
text = text.replace("–", "-")
text = text.replace("−", "-")

# Collapse double-spaces only WITHIN content (preserve leading indent).
# Pattern: any non-space char followed by 2+ spaces -> non-space + single space.
# This leaves leading indentation alone.
text = re.sub(r"(?<=\S)  +", " ", text)

ARTICLE.write_text(text, encoding="utf-8")
delta = len(text) - orig_len
print(f"replaced em-dash: {counts['em_dash']}, en-dash: {counts['en_dash']}, minus-sign: {counts['minus']}")
print(f"delta chars: {delta:+d}, length now: {len(text)}")

for ch, name in [("—", "em dash"), ("–", "en dash"), ("−", "minus sign")]:
    n = text.count(ch)
    if n:
        print(f"WARN: still {n} occurrences of {name}")
