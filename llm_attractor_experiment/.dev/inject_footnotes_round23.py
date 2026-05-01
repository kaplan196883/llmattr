"""Inject [^figN] markers into figure captions and add [^figN]: <description>
definitions immediately after each figure block.

The marker is appended to the existing caption text (before the closing `](path)`)
so it appears at the end of the rendered caption sentence."""
import json
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
DESC = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round23_descriptions.json")

text = ARTICLE.read_text(encoding="utf-8")
descriptions = json.loads(DESC.read_text(encoding="utf-8"))

# Pattern that matches each figure block.
# We use the same lazy match as extract_figures_round23.py.
fig_pat = re.compile(
    r"!\[(Fig|ED Fig)\s+(\d+)\.\s+\*\*(.+?)\.\*\*\s+(.+?)\]\(([^)]+\.png)\)",
    re.DOTALL,
)


def replacer(m: re.Match) -> str:
    label_class = m.group(1)
    num = int(m.group(2))
    title = m.group(3)
    body = m.group(4).rstrip()
    path = m.group(5)
    fid = f"{label_class.replace(' ', '')}{num}"  # e.g., Fig1 or EDFig1
    if fid not in descriptions:
        # Skip; leave figure as-is
        return m.group(0)
    # Insert marker at the very end of the caption body (before the close-bracket).
    new_body = body.rstrip() + f"[^{fid}]"
    return f"![{label_class} {num}. **{title}.** {new_body}]({path})"


text_new, n = fig_pat.subn(replacer, text)
print(f"injected markers into {n} figure blocks")

# Append all definitions at the end of the document (after the supplementary).
# Definitions can live anywhere; placing them at the end keeps the figure
# blocks themselves clean.
defs_block = "\n\n<!-- Figure footnote definitions (round-23) -->\n\n"
for fid in sorted(descriptions.keys(), key=lambda k: (
        0 if not k.startswith("ED") else 1,
        int(re.sub(r"\D", "", k)),
)):
    body = descriptions[fid].strip()
    defs_block += f"[^{fid}]: {body}\n\n"

text_new = text_new.rstrip() + defs_block

ARTICLE.write_text(text_new, encoding="utf-8")

# Verify
n_markers = len(re.findall(r"\[\^(?:Fig|EDFig)\d+\]", text_new))
n_defs = len(re.findall(r"^\[\^(?:Fig|EDFig)\d+\]:", text_new, flags=re.MULTILINE))
print(f"final: {n_markers} marker references, {n_defs} definitions")
