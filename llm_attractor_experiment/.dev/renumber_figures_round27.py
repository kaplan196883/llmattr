"""Renumber figures so caption/marker labels match source-order LaTeX numbering.

Single-pass approach: stash all rename targets behind \\x00 sentinels first,
then perform the rename, then restore. Avoids the serial-sub cycle problem
where a swap remap (3<->4) re-cycles after the first pass.
"""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

# Step 1: build remap by walking figure blocks in source order
pat_block = re.compile(r"!\[(Fig|ED Fig)\s+(\d+)\.\s+\*\*")
fig_n = ed_n = 0
remap_fig: dict[int, int] = {}
remap_ed: dict[int, int] = {}
for m in pat_block.finditer(text):
    cls = m.group(1); old = int(m.group(2))
    if cls == "Fig":
        fig_n += 1
        remap_fig[old] = fig_n
    else:
        ed_n += 1
        remap_ed[old] = ed_n

needed = sum(1 for k, v in remap_fig.items() if k != v) \
       + sum(1 for k, v in remap_ed.items() if k != v)
print(f"changes needed: {needed}")
for k, v in sorted(remap_fig.items()):
    if k != v: print(f"  Fig {k} -> Fig {v}")
for k, v in sorted(remap_ed.items()):
    if k != v: print(f"  ED Fig {k} -> ED Fig {v}")

# Step 2: build a SINGLE big regex that matches every reference we want to
# rename. Captures cover all four reference forms:
#   (a) "![Fig N. **" or "![ED Fig N. **" — figure-block caption header
#   (b) "[^FigN]" or "[^EDFigN]" — footnote marker / definition-key
#   (c) "Fig N" / "Figure N" / "ED Fig N" / "ED Figure N" — prose reference
# Using alternation we ensure each character span is consumed once and
# remap is applied atomically.
pat_master = re.compile(
    r"(?P<caphdr>!\[(?P<caphdr_cls>Fig|ED Fig)\s+(?P<caphdr_n>\d+)\.\s+\*\*)"
    r"|"
    r"(?P<mark>\[\^(?P<mark_cls>Fig|EDFig)(?P<mark_n>\d+)\])"
    r"|"
    r"(?P<ref>\b(?P<ref_cls>ED\s+Fig(?:ure)?|Fig(?:ure)?)\s+(?P<ref_n>\d+)\b)"
)

def repl(m: re.Match) -> str:
    if m.group("caphdr"):
        cls = m.group("caphdr_cls")
        old = int(m.group("caphdr_n"))
        if cls == "Fig":
            return f"![Fig {remap_fig.get(old, old)}. **"
        else:
            return f"![ED Fig {remap_ed.get(old, old)}. **"
    elif m.group("mark"):
        cls = m.group("mark_cls")
        old = int(m.group("mark_n"))
        if cls == "Fig":
            return f"[^Fig{remap_fig.get(old, old)}]"
        else:
            return f"[^EDFig{remap_ed.get(old, old)}]"
    else:
        cls_word = m.group("ref_cls")
        old = int(m.group("ref_n"))
        if cls_word.lstrip().startswith("ED"):
            new = remap_ed.get(old, old)
            return f"ED Fig {new}"
        else:
            new = remap_fig.get(old, old)
            # Preserve "Fig" vs "Figure" word choice
            word = "Figure" if cls_word == "Figure" else "Fig"
            return f"{word} {new}"

text_new = pat_master.sub(repl, text)
ARTICLE.write_text(text_new, encoding="utf-8")

# Verify ordering
fig_n = ed_n = 0
ok = True
for m in re.finditer(r"!\[(Fig|ED Fig)\s+(\d+)\.\s+\*\*", text_new):
    cls = m.group(1); n = int(m.group(2))
    if cls == "Fig":
        fig_n += 1; expected = fig_n
    else:
        ed_n += 1; expected = ed_n
    if n != expected:
        print(f"FAIL: {cls} {n} at position {expected}")
        ok = False
        break
if ok:
    print(f"\nverified: {fig_n} Fig + {ed_n} ED Fig in source-order sequence")
