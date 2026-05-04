"""Third pass — rhetorical / rhythmic AI tells in round-32 additions."""
import re
from pathlib import Path
from collections import Counter

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

PATTERNS = [
    # "X is not just/merely/only Y; it is Z" rhetorical (very AI)
    r"\bis not (?:just|merely|only) [^.;]{2,80}[;,]",
    # "Beyond X, Y" sentence opener
    r"(?:^|[.\n])\s*Beyond ",
    # "Not X but Y" rhetorical
    r"\bnot (?:X|just|simply|merely)[^,]{0,40},?\s+but\s+",
    # "While X, Y" sentence opener (very common AI)
    r"(?:^|\n)\s*While\s+\w",
    # "Despite X, Y" sentence opener
    r"(?:^|\n)\s*Despite\s+\w",
    # "Although X, Y" sentence opener
    r"(?:^|\n)\s*Although\s+\w",
    # "However," after period (overused as connective)
    r"(?:\.|\!|\?)\s+However,",
    # "By contrast," / "In contrast," sentence opener
    r"(?:^|\n)\s*By contrast,",
    r"(?:^|\n)\s*In contrast,",
    # "Indeed," anywhere
    r"\bIndeed,",
    # AI-flavored "what we found" / "what we did"
    r"\bWhat we found\b",
    r"\bWhat we did\b",
    # "A simple X" / "A clean X" rhetorical lead-ins
    r"\bA (?:simple|clean|natural|principled) (?:way|approach|test|check|design|protocol)\b",
    # "It turns out that"
    r"\bit turns out\b",
    # "This is consistent with"
    r"\bthis is consistent with\b",
    # "We then" / "We therefore" / "We thus" (light AI rhythm)
    r"\bWe (?:then|therefore|thus)\b",
    # "to put it another way"
    r"\bto put it another way\b",
    # AI summary "These findings" / "These results" lead-ins
    r"\bThese (?:findings|results) (?:show|indicate|reveal|demonstrate|suggest)\b",
    # AI rhythm "where X, Y holds"
    r"\bwhere\s+\w+,\s+",
    # AI cliche "lens"
    r"\bthrough the lens of\b",
    r"\ba lens for\b",
    # "Among X" sentence opener
    r"(?:^|\n)\s*Among\s+(?:the\s+)?\w+",
]

hits = []
for pat in PATTERNS:
    for m in re.finditer(pat, text):
        line_no = text[: m.start()].count("\n") + 1
        s = max(0, m.start() - 50)
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
    print(f"L{line_no:>5d} {hit!r}: ...{ctx[:200]}...")
