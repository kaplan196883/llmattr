"""Round-33: insert new Fig 5 for the no-clip dose-response curve.

Atomic single-pass renumber: Fig 5..16 -> Fig 6..17, [^Fig5]..[^Fig16] -> [^Fig6]..[^Fig17].
"""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")
orig_len = len(text)

PLACEHOLDER = "\x00FIG33_PLACEHOLDER_"
shifts = list(range(16, 4, -1))  # 16..5

for old in shifts:
    text = text.replace(f"Fig {old}.", f"{PLACEHOLDER}{old}.")
    text = text.replace(f"[^Fig{old}]", f"{PLACEHOLDER}fn{old}]")
    text = re.sub(rf"\bFig {old}\b", f"{PLACEHOLDER}body{old}", text)
    text = re.sub(rf"\bFigure {old}\b", f"{PLACEHOLDER}long{old}", text)

for old in shifts:
    new = old + 1
    text = text.replace(f"{PLACEHOLDER}{old}.", f"Fig {new}.")
    text = text.replace(f"{PLACEHOLDER}fn{old}]", f"[^Fig{new}]")
    text = text.replace(f"{PLACEHOLDER}body{old}", f"Fig {new}")
    text = text.replace(f"{PLACEHOLDER}long{old}", f"Figure {new}")

ARTICLE.write_text(text, encoding="utf-8")
print(f"applied delta: {len(text) - orig_len:+d} chars")
