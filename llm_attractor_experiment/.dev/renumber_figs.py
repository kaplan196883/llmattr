"""Renumber Fig 6..Fig 31 -> Fig 7..Fig 32 in ARTICLE.md.

A new Fig 6 (dip-vs-terminal-step decay plot) was inserted in §5.1.3, so
all subsequent figures shift by 1. Uses two-pass placeholder substitution
to avoid swap collisions.

Patterns renumbered:
  "Fig N"            -> "Fig (N+1)"      (where 6 <= N <= 31)
  "[^FigN]"          -> "[^Fig(N+1)]"
  "Figure N" (rare)  -> "Figure (N+1)"

NOT touched:
  Fig 1..Fig 5      (positions before the new insertion, unchanged)
  ED Fig N          (extended-data figures, separate sequence — none in this paper)
  Section refs §N.M (figure renumber doesn't affect section numbers)
  The new placeholder [^Fig6dip] (not numeric, unaffected)
"""
from __future__ import annotations

import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

PH = "\x00FIG"  # placeholder marker

# Pass 1: original "Fig N" -> placeholder "\x00FIG_<old>" for N in 6..31
for n in range(31, 5, -1):  # high to low so 31 is replaced before 3 (which is in 31)
    # \bFig 31\b style - need word boundary AFTER digits to not match "Fig 312"
    pat = rf"\bFig {n}(?!\d)"
    text = re.sub(pat, f"{PH}_{n}", text)

# Pass 2: "[^FigN]" -> "\x00FIG_F_<n>"
for n in range(31, 5, -1):
    pat = rf"\[\^Fig{n}\](?!\w)"
    text = re.sub(pat, f"{PH}_F_{n}", text)

# Pass 3: optional "Figure N" (rarer)
for n in range(31, 5, -1):
    pat = rf"\bFigure {n}(?!\d)"
    text = re.sub(pat, f"{PH}_Fu_{n}", text)

# Pass 4: resolve placeholders to incremented numbers
for n in range(6, 32):
    text = text.replace(f"{PH}_{n}", f"Fig {n + 1}")
    text = text.replace(f"{PH}_F_{n}", f"[^Fig{n + 1}]")
    text = text.replace(f"{PH}_Fu_{n}", f"Figure {n + 1}")

ARTICLE.write_text(text, encoding="utf-8")
print(f"renumbered. final length: {len(text)} chars")
