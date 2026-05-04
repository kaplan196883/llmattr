"""Second pass — more nuanced AI tells."""
import re
from pathlib import Path
from collections import Counter

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

PATTERNS = [
    # AI-flavored connective tissue
    r"\bthat said,",
    r"\bwith that said,",
    r"\bin essence,",
    r"\bat its core,",
    r"\bat the heart of",
    r"\bat its heart,",
    r"\bkey (?:takeaway|insight)",
    r"\bthe fact that\b",
    # AI-flavored modifiers
    r"\bvarious\b",
    r"\bdiverse\b",
    r"\brich\b(?!\W*(?:representation|context|signal|information|in (?:nuance|detail)|er than))",
    r"\bnuanced\b",
    r"\bremarkable\b",
    r"\bfascinating\b",
    r"\bintricate(?:ly)?\b",
    # AI verbs, second batch
    r"\bshed (?:more )?light\b",
    r"\bplay(?:s|ed|ing)? (?:a |an )?(?:crucial|pivotal|key|important|significant|vital) role\b",
    r"\bbring(?:s|ing)? to (?:light|the fore(?:front)?)\b",
    r"\bopen(?:s|ed|ing)? up new\b",
    # Parallel rhythm / "First... Second... Finally..."
    r"\bensure(?:s)?\s+that\b",
    # AI-flavored prefaces
    r"\bin this paper\b",
    r"\bthis paper\b",
    r"\bthe present (?:paper|work|study)\b",
    r"\bthis study\b",
    # Excessive listing flag
    r"(?:^|\n)\s*1\.\s+[^\n]{1,200}\n\s*2\.\s+[^\n]{1,200}\n\s*3\.\s+[^\n]{1,200}",
    # AI-flavored conclusions
    r"\btogether(?:,|\.)? these results\b",
    r"\btaken together\b",
    r"\bcollectively,\b",
    # AI hedges
    r"\bcan be seen as\b",
    r"\bmight be (?:argued|considered|seen|viewed)\b",
    # "It is X to Y" structure (very AI)
    r"\bit is (?:important|essential|critical|vital|necessary|useful|valuable|noteworthy|interesting|telling)\b",
]

hits = []
for pat in PATTERNS:
    for m in re.finditer(pat, text, re.IGNORECASE):
        line_no = text[: m.start()].count("\n") + 1
        s = max(0, m.start() - 60)
        e = min(len(text), m.end() + 100)
        ctx = text[s:e].replace("\n", " / ")
        hits.append((pat, line_no, m.group(0), ctx))

by_pattern = Counter(pat for pat, *_ in hits)
print(f"=== Pattern hit counts ({len(hits)} total) ===")
for pat, n in by_pattern.most_common():
    print(f"  {pat!r:60s} {n:>3d} hits")

print()
print("=== Detailed hits ===")
for pat, line_no, hit, ctx in hits:
    print(f"L{line_no:>5d} {hit!r}: ...{ctx[:180]}...")
