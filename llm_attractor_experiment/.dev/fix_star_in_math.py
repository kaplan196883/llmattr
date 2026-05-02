"""Fix '\\*' inside inline math '\\(...\\)' to plain '*'.
Also handles 'j\\*' etc. which appear in §11 supp metric snippets.
"""
import re
from pathlib import Path
ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

# Find every \( ... \) inline math block and remove '\*' -> '*' inside.
def fix(m: re.Match) -> str:
    body = m.group(1)
    body_fixed = body.replace(r"\*", "*")
    return r"\(" + body_fixed + r"\)"

# Match \( body \) lazily (any chars, including newlines) — using literal
# backslash-open-paren and backslash-close-paren as delimiters.
pat = re.compile(r"\\\(([^)]*?)\\\)")
text_new, n = pat.subn(fix, text)

# Same for \[ ... \] display math (rare, but be safe)
pat_disp = re.compile(r"\\\[([\s\S]*?)\\\]")
def fix_disp(m: re.Match) -> str:
    body = m.group(1).replace(r"\*", "*")
    return r"\[" + body + r"\]"
text_new = pat_disp.sub(fix_disp, text_new)

# Also handle code-snippet stars: '\*\)' patterns that came from GPT escaping
# in §11.4 metric definitions. Specifically 'j\*=' should be 'j*='.
n_code = text_new.count(r"j\*=")
text_new = text_new.replace(r"j\*=", "j*=")
n_code += text_new.count(r"j\*+1")
text_new = text_new.replace(r"j\*+1", "j*+1")

ARTICLE.write_text(text_new, encoding="utf-8")
print(f"fixed {n} math \\* occurrences (inline + display)")
print(f"fixed {n_code} code-snippet 'j\\*' occurrences")
print(f"remaining \\*: {text_new.count(chr(92)+chr(42))}")
