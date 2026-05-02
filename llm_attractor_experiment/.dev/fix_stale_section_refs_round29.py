"""Round-29: remap stale §5.X references to the current §5 numbering.

Round-21 restructured §5 from 21 subsections to 13 (renaming/merging some,
demoting others to released tables). The body of the paper still contains
references to the old subsection numbers (§5.6.1, §5.14-§5.21). This
script remaps them to the current canonical sections.

Mapping (old -> new):
  §5.6.1 -> §5.1   (dense O1 rerun absorbed into headline §5.1)
  §5.14  -> §5.8   (per-cluster semantic inspection, kept)
  §5.15  -> §5.1   (persistence is in §5.1 now)
  §5.16  -> §5.12  (V* parameter-grid sensitivity merged into "density
                    landscapes are descriptive")
  §5.17  -> §5.2   (overwrite-vs-insert merged into "replace-mode
                    fragility is memory-policy effect")
  §5.18  -> §5.10  (cross-metric correlations absorbed into embedding
                    ablation discussion; full table moved to released
                    aggregate tables)
  §5.19  -> §5.13  (why exactly five regimes, kept)
  §5.20  -> §5.10  (embedding-space invariance, kept)
  §5.21  -> §5.11  (cross-model thesis verification, kept)
"""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

# Order longest-first so §5.6.1 matches before §5.6 prefix would.
# Use single-pass dict-callback to avoid double-substitution.
remap = {
    "5.6.1": "5.1",
    "5.14": "5.8",
    "5.15": "5.1",
    "5.16": "5.12",
    "5.17": "5.2",
    "5.18": "5.10",
    "5.19": "5.13",
    "5.20": "5.10",
    "5.21": "5.11",
}
keys_sorted = sorted(remap.keys(), key=lambda k: -len(k))
pat = re.compile(r"§(" + "|".join(re.escape(k) for k in keys_sorted) + r")\b")

n = 0
def replace(m: re.Match) -> str:
    global n
    n += 1
    return f"§{remap[m.group(1)]}"
text_new = pat.sub(replace, text)
print(f"§-ref remap substitutions: {n}")

# Also \S<num> tex-raw form
pat_tex = re.compile(r"\\S(" + "|".join(re.escape(k) for k in keys_sorted) + r")\b")
n_tex = 0
def replace_tex(m: re.Match) -> str:
    global n_tex
    n_tex += 1
    return f"\\S{remap[m.group(1)]}"
text_new = pat_tex.sub(replace_tex, text_new)
print(f"\\S-ref remap substitutions: {n_tex}")

ARTICLE.write_text(text_new, encoding="utf-8")

# Verify
remaining = sorted(set(re.findall(r"§5\.\d+(?:\.\d+)?", text_new)),
                   key=lambda s: tuple(int(x) for x in s[1:].split(".")))
print(f"\nremaining §5 refs: {remaining}")
stale = [r for r in remaining if r in {"§5.6.1", "§5.14", "§5.15", "§5.16",
                                        "§5.17", "§5.18", "§5.19", "§5.20",
                                        "§5.21"}]
if stale:
    print(f"WARN: still stale: {stale}")
else:
    print("all stale refs cleaned up")
