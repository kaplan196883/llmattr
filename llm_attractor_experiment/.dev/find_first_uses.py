"""Find first occurrence and context for fail-list items."""
import re
text = open(r'D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md', encoding='utf-8').read()
patterns = [
    ('ED50_raw', r'\\mathrm\{ED50\}_\{?\\mathrm\{raw\}\}?'),
    ('ED50_persist', r'\\mathrm\{ED50\}_\{?\\mathrm\{persist\}\}?'),
    ('O1', r'\bO1\b'),
    ('O2', r'\bO2\b'),
    ('O3', r'\bO3\b'),
    ('D1', r'\bD1\b'),
    ('D2', r'\bD2\b'),
    ('RG', r'\bRG\b'),
]
for label, pat in patterns:
    m = re.search(pat, text)
    if m:
        line = text[:m.start()].count('\n') + 1
        s = max(0, m.start()-80)
        e = min(len(text), m.end()+120)
        ctx = text[s:e].replace('\n', ' / ')
        print(f"{label:14s} L{line:5d}: ...{ctx}...")
    else:
        print(f"{label:14s} NOT FOUND")
