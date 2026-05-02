"""Inventory all mathematical formulas in ARTICLE.md and emit context."""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

# Display math \[ ... \]: literal backslash-bracket delimiters
disp_pat = re.compile(r"\\\[([\s\S]*?)\\\]")
# Inline math \( ... \): literal backslash-paren delimiters
inline_pat = re.compile(r"\\\(([\s\S]*?)\\\)")
# Markdown $...$ math (avoiding $$): one-line lazy match
md_pat = re.compile(r"(?<!\$)\$((?:(?!\$|\n\s*\n)[\s\S])+?)\$(?!\$)")

disp = list(disp_pat.finditer(text))
inline = list(inline_pat.finditer(text))
md = list(md_pat.finditer(text))
print(f"Display math (\\[...\\]):     {len(disp)}")
print(f"Inline math (\\(...\\)):      {len(inline)}")
print(f"Inline math ($...$):           {len(md)}")
print(f"TOTAL math expressions:       {len(disp) + len(inline) + len(md)}")
print()
print("=== Display math (full list) ===")
for i, m in enumerate(disp, 1):
    line_no = text[:m.start()].count("\n") + 1
    body = m.group(1).strip().replace("\n", " ")
    if len(body) > 110:
        body = body[:107] + "..."
    print(f"D{i:2d} L{line_no:5d}: {body}")
