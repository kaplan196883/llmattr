"""Replace round-23 footnote definitions in ARTICLE.md with round-25 deeper versions.
Existing markers [^figN] are kept in place; only the definitions at the bottom
of the document are replaced.
"""
import json
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
DESC = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round25_descriptions.json")

text = ARTICLE.read_text(encoding="utf-8")
descriptions = json.loads(DESC.read_text(encoding="utf-8"))

# Strip the entire existing footnote-definitions block (everything after the
# sentinel comment — round-23 originally, round-25 in subsequent runs).
for sentinel in (
    "<!-- Figure footnote definitions (round-25 deeper) -->",
    "<!-- Figure footnote definitions (round-23) -->",
):
    i = text.find(sentinel)
    if i != -1:
        break
else:
    raise SystemExit("no footnote-definitions sentinel found")

text_before = text[:i].rstrip()

# Build the new footnote-definitions block.
def fig_sort_key(fid: str):
    is_ed = 1 if fid.startswith("ED") else 0
    num = int(re.sub(r"\D", "", fid))
    return (is_ed, num)

defs_block = "\n\n<!-- Figure footnote definitions (round-25 deeper) -->\n\n"
for fid in sorted(descriptions.keys(), key=fig_sort_key):
    body = descriptions[fid].strip().replace("\n", " ")
    defs_block += f"[^{fid}]: {body}\n\n"

text_new = text_before + defs_block
ARTICLE.write_text(text_new, encoding="utf-8")

# Verification
n_markers = len(re.findall(r"\[\^(?:Fig|EDFig)\d+\](?!:)", text_new))  # inline refs
n_defs = len(re.findall(r"^\[\^(?:Fig|EDFig)\d+\]:", text_new, flags=re.MULTILINE))
print(f"inline marker references: {n_markers}")
print(f"footnote definitions: {n_defs}")
