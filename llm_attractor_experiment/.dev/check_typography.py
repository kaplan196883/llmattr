"""Audit AI-typography in ARTICLE.md before cleanup."""
import re
from pathlib import Path

text = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md").read_text(encoding="utf-8")

# Examine prose multi-space runs (not at line start, not in tables)
prose_double = []
for i, line in enumerate(text.split("\n"), 1):
    if not line:
        continue
    if line[0] in ("|", " ", "\t", "#"):
        continue
    # Skip tables that are inline (a row in a table block)
    if re.match(r"^\s*\|", line):
        continue
    if "  " in line:
        prose_double.append((i, line[:140]))

print(f"prose lines with double-space: {len(prose_double)}")
for i, l in prose_double[:8]:
    print(f"  L{i}: {l!r}")

# Sample em-dash contexts
print("\nem-dash contexts (first 8):")
for m in list(re.finditer("—", text))[:8]:
    s = max(0, m.start() - 50)
    e = min(len(text), m.end() + 50)
    ctx = text[s:e].replace("\n", " / ")
    line_no = text[: m.start()].count("\n") + 1
    print(f"  L{line_no}: ...{ctx}...")

# Sample en-dash contexts (only 3)
print("\nen-dash contexts (all 3):")
for m in list(re.finditer("–", text)):
    s = max(0, m.start() - 50)
    e = min(len(text), m.end() + 50)
    ctx = text[s:e].replace("\n", " / ")
    line_no = text[: m.start()].count("\n") + 1
    print(f"  L{line_no}: ...{ctx}...")

# Sample minus-sign contexts (5)
print("\nminus-sign contexts (all 5):")
for m in list(re.finditer("−", text)):
    s = max(0, m.start() - 50)
    e = min(len(text), m.end() + 50)
    ctx = text[s:e].replace("\n", " / ")
    line_no = text[: m.start()].count("\n") + 1
    print(f"  L{line_no}: ...{ctx}...")
