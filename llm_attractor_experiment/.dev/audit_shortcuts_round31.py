"""For each shortcut/abbreviation, find its first occurrence in ARTICLE.md
and grab ~600 chars of context before that point, so we can verify a
definition appears earlier or in the same paragraph."""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
OUT = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round31_shortcuts_first_use.md")
text = ARTICLE.read_text(encoding="utf-8")

# Comprehensive list of shortcuts/abbreviations used in the paper.
# Each pattern is a regex that matches a STANDALONE first occurrence
# (avoiding accidental sub-string matches like "ED50raw" matching ED50).
SHORTCUTS = [
    # Endpoint estimands
    ("ED50_raw", r"\bED50_?\\?raw\b|\\mathrm\{ED50\}_\\?\{?\\?mathrm\{raw\}\}?"),
    ("ED50_net", r"\bED50_?\\?net\b|\\mathrm\{ED50\}_\\?\{?\\?mathrm\{net\}\}?"),
    ("ED50_persist", r"\bED50_?\\?persist\b|\\mathrm\{ED50\}_\\?\{?\\?mathrm\{persist\}\}?"),
    # Switching estimand letters
    ("S_raw", r"\bS_\{?\\?mathrm\{raw\}\}?"),
    ("S_net", r"\bS_\{?\\?mathrm\{net\}\}?"),
    ("S_persist", r"\bS_\{?\\?mathrm\{persist\}\}?"),
    # Other estimands
    ("V*", r"V\^\*|V\^\\?star|V[\* ⋆]"),
    ("J_tau", r"J_\\?tau\b|J_\\?\{\\?tau\\?\}"),
    ("C_ref", r"C_\{?\\?mathrm\{ref\}\}?|C_ref"),
    ("C_T", r"C_T\b|C_T\^"),
    ("B_persist", r"\\mathrm\{B\}_\\?\{?\\?mathrm\{persist\}\}?|B_\\?persist\b"),
    ("p_0", r"\bp_0\b"),
    # Attractor criteria
    ("C1", r"\bC1\b"),
    ("C2", r"\bC2\b"),
    ("C3", r"\bC3\b"),
    ("C4", r"\bC4\b"),
    ("C1-C4", r"\bC1[–-]C4\b|C1\\?-C4"),
    # Regime codes
    ("O1", r"\bO1\b"),
    ("O2", r"\bO2\b"),
    ("O3", r"\bO3\b"),
    ("D1", r"\bD1\b"),
    ("D2", r"\bD2\b"),
    # Hypotheses
    ("H1", r"\bH1\b"),
    ("H2", r"\bH2\b"),
    ("H3", r"\bH3\b"),
    ("H4", r"\bH4\b"),
    # Math/statistics shortcuts
    ("lambda_1", r"\\lambda_1\b|\\lambda_\\?\{?1\\?,?r\\?\}"),
    ("SD", r"\bSD\b"),
    ("4PL", r"\b4PL\b"),
    ("GLMM", r"\bGLMM\b"),
    ("CV", r"\bCV\b"),
    ("CI", r"\bCI\b"),
    ("Wilson CI", r"Wilson CI"),
    # Observable / pipeline jargon
    ("PCA-2", r"\bPCA-?2\b"),
    ("PCA-3", r"\bPCA-?3\b"),
    ("PCA-10", r"\bPCA-?10\b"),
    ("PCA-50", r"\bPCA-?50\b"),
    ("t-SNE", r"\bt-SNE\b"),
    ("HDBSCAN", r"\bHDBSCAN\b"),
    ("K-means", r"\bK-?means\b"),
    ("KDE", r"\bKDE\b"),
    ("rolling_k3", r"\brolling_k3\b"),
    ("context_tail", r"\bcontext_tail\b"),
    ("turn_pair", r"\bturn_pair\b"),
    ("RG", r"\bRG\b"),
    # Other domain shortcuts
    ("IPI", r"\bIPI\b"),
    ("LFS", r"\bLFS\b"),
    ("API", r"\bAPI\b"),
    ("OOD", r"\bOOD\b"),
    ("MVP", r"\bMVP\b"),
    ("UTC", r"\bUTC\b"),
    ("RAM", r"\bRAM\b"),
    ("CPU", r"\bCPU\b"),
    ("GPU", r"\bGPU\b"),
    ("OS", r"\bOS\b"),
]

out_lines = []
for name, pat_str in SHORTCUTS:
    pat = re.compile(pat_str)
    m = pat.search(text)
    if m is None:
        out_lines.append(f"## {name}\n\n_(not found in ARTICLE.md)_\n\n---\n")
        continue
    line_no = text[:m.start()].count("\n") + 1
    # Capture ~700 chars of context BEFORE first use so we can see if
    # a definition has been emitted previously.
    start = max(0, m.start() - 700)
    end = min(len(text), m.end() + 200)
    context = text[start:end]
    # Trim to whole sentences if possible
    out_lines.append(
        f"## {name}\n\n"
        f"**First-use line:** {line_no}\n\n"
        f"**Match:** `{m.group(0)}`\n\n"
        f"**Context (700 chars before, 200 after):**\n\n"
        f"```\n{context}\n```\n\n---\n"
    )

OUT.write_text("\n".join(out_lines), encoding="utf-8")
print(f"wrote {OUT.name}")
print(f"total shortcuts probed: {len(SHORTCUTS)}")
