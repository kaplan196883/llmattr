"""For each display formula, capture ~6 lines of context before and after."""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
OUT = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round30_math_contexts.md")

text = ARTICLE.read_text(encoding="utf-8")
lines = text.split("\n")
disp_pat = re.compile(r"\\\[([\s\S]*?)\\\]")

CONTEXT_LINES = 6
out_lines = []
for i, m in enumerate(disp_pat.finditer(text), 1):
    line_no = text[:m.start()].count("\n") + 1
    body = m.group(1).strip()
    # Find the paragraph context: lines around line_no
    start = max(0, line_no - 1 - CONTEXT_LINES)
    end = min(len(lines), line_no - 1 + CONTEXT_LINES + body.count("\n") + 1)
    ctx = "\n".join(lines[start:end])
    out_lines.append(f"## D{i:02d} (line {line_no})\n\n{ctx}\n\n---\n")

OUT.write_text("\n".join(out_lines), encoding="utf-8")
print(f"wrote {OUT.name} with {i} formulas + context")
