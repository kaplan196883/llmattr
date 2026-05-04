"""Find AI-tell phrases in ARTICLE.md.

Run, eyeball the report, then write targeted edits. Patterns are
case-insensitive and word-boundary anchored where appropriate.
"""
import re
from pathlib import Path
from collections import Counter

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

PATTERNS = {
    # Throat-clearing / hedge openers
    r"\bit'?s worth noting\b":      "throat-clear",
    r"\bit'?s worth mentioning\b":  "throat-clear",
    r"\bit'?s important to note\b": "throat-clear",
    r"\bit should be noted\b":      "throat-clear",
    r"\bit is worth\b":             "throat-clear",
    r"\bnotably,":                  "throat-clear",
    r"\bimportantly,":              "throat-clear",
    r"\bcrucially,":                "throat-clear",
    r"\bindeed,":                   "throat-clear",
    r"\bof course,":                "throat-clear",
    r"\bit goes without saying":    "throat-clear",
    r"\bone might argue":           "throat-clear",
    # Overused AI verbs
    r"\bdelve(s|d|ing)?\b":         "AI-overused-verb",
    r"\bleverag(e|es|ed|ing)\b":    "AI-overused-verb",
    r"\bnavigat(e|es|ed|ing)\b":    "AI-overused-verb",
    r"\bshowcas(e|es|ed|ing)\b":    "AI-overused-verb",
    r"\bunderscor(e|es|ed|ing)\b":  "AI-overused-verb",
    r"\bfacilitat(e|es|ed|ing)\b":  "AI-overused-verb",
    r"\bharness(es|ed|ing)?\b":     "AI-overused-verb",
    r"\belucidat(e|es|ed|ing)\b":   "AI-overused-verb",
    r"\bencompass(es|ed|ing)?\b":   "AI-overused-verb",
    r"\bexemplif(y|ies|ied|ying)\b":"AI-overused-verb",
    # Overused AI nouns/adjectives
    r"\btapestry\b":                 "AI-cliche",
    r"\bmyriad\b":                   "AI-cliche",
    r"\bplethora\b":                 "AI-cliche",
    r"\brealm\b":                    "AI-cliche",
    r"\blandscape of\b":             "AI-cliche",
    r"\bvibrant\b":                  "AI-cliche",
    r"\bprofound(?!\W*(insight|change))": "AI-cliche",
    r"\bever-evolving\b":            "AI-cliche",
    r"\bcomprehensive\b":            "AI-cliche",
    r"\bin the realm of\b":          "AI-cliche",
    r"\bit'?s essential\b":          "AI-cliche",
    r"\bremember that\b":            "AI-cliche",
    # Concluding/summary openers
    r"\bin conclusion,":             "summary-tell",
    r"\bin summary,":                "summary-tell",
    r"\bultimately,":                "summary-tell",
    r"\boverall,":                   "summary-tell",
    r"\bin essence,":                "summary-tell",
    r"\bto sum up,":                 "summary-tell",
    # Continuation openers (overused)
    r"\bfurthermore,":               "continuation-tell",
    r"\bmoreover,":                  "continuation-tell",
    r"\badditionally,":              "continuation-tell",
    # Hedge/reassurance
    r"\bit'?s worth (?:considering|emphasizing|highlighting)": "hedge",
    r"\brest assured":               "hedge",
    # Parallel-construction tells (look at frequency)
    r"\bfirst,\b":                   "parallel-tell",
    r"\bsecond,\b":                  "parallel-tell",
    r"\bfinally,\b":                 "parallel-tell",
    # Em-dash-style "key takeaway" rhythm
    r"\bin other words,":            "AI-rhythm",
    r"\bthat said,":                 "AI-rhythm",
    r"\bwith that in mind,":         "AI-rhythm",
}

hits = []
for pat, tag in PATTERNS.items():
    for m in re.finditer(pat, text, re.IGNORECASE):
        line_no = text[: m.start()].count("\n") + 1
        s = max(0, m.start() - 60)
        e = min(len(text), m.end() + 80)
        ctx = text[s:e].replace("\n", " / ")
        hits.append((tag, pat, line_no, m.group(0), ctx))

# Group by pattern
by_pattern = Counter((tag, pat) for tag, pat, *_ in hits)
print("=== Pattern hit counts ===")
for (tag, pat), n in by_pattern.most_common():
    print(f"  [{tag:22s}] {pat!r:50s} {n:>3d} hits")

print()
print(f"=== Detailed hits (first 120) ===")
for tag, pat, line_no, hit, ctx in hits[:120]:
    print(f"L{line_no:>5d} [{tag:18s}] {hit!r}: ...{ctx[:160]}...")

print(f"\nTOTAL hits: {len(hits)}")
