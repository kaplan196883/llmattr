"""Fix \\rho in ED Fig 13 caption by rephrasing to plain English."""
from pathlib import Path
ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")
old = r"five density fractions (4%, 10%, 20%, 35%, 55% of max $\hat\rho$)"
new = "five density fractions (4%, 10%, 20%, 35%, 55% of peak density)"
n = text.count(old)
print(f"matches: {n}")
text = text.replace(old, new)
ARTICLE.write_text(text, encoding="utf-8")
print("rho:", "\\rho" in text)
