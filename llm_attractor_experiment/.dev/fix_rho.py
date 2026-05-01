"""Fix the broken \\rho in ED Fig 13 caption."""
from pathlib import Path
ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")
broken = "$\\hat\nho$"
fixed = "$\\hat\\rho$"
n = text.count(broken)
text = text.replace(broken, fixed)
ARTICLE.write_text(text, encoding="utf-8")
print(f"replaced {n} broken-rho occurrences")
print("verification: 'hatho' in text:", "hatho" in text)
print("verification: 'hat\\\\rho' in text:", "hat\\rho" in text)
