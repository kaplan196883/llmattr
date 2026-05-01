"""One-shot section-renumbering for ARTICLE.md.

Eliminates the §3.1.1bis / §3.1.1.5 / §5.0bis / §5.10.x naming hacks by
renumbering all §3.1.x and §5.x headings + body references so that
markdown-source labels match LaTeX's auto-numbering (and so the
rendered PDF has clean monotone section numbers).

Heading map (markdown source, decreasing OLD-number to avoid collisions
during in-place string replace):

  §3.1 group:
    3.1.4   → 3.1.6   (Tokens vs nats)
    3.1.3   → 3.1.5   (Append-mode accumulation barrier)
    3.1.2   → 3.1.4   (Replace-mode access bound)
    3.1.1.5 → 3.1.3   (Operational criteria)
    3.1.1bis → 3.1.2  (Three operational endpoints)

  §5 group:
    5.0bis    → 5.1    (Unified primary-results table)
    5.0       → 5.2    (The four (plus one) regimes)
    5.1       → 5.3    (Phase 0)
    5.2       → 5.4    (Phase 1 small-N)
    5.3       → 5.5    (Phase 2)
    5.4       → 5.6    (Phase 2b T-sweep)
    5.5       → 5.7    (Phase 3a perturbation pilots)
    5.6       → 5.8    (Phase 3b dose-response)
    5.6.1     → 5.8.1  (Confirmatory dense-dose rerun)
    5.7       → 5.9    (Phase 3c injection-time sweep)
    5.8       → 5.10   (Phase 3d D2 drill-down)
    5.9       → 5.11   (Cross-experiment aggregation)
    5.10      → 5.12   (Geometric barriers)
    5.10.5    → 5.13   (Group-aware basin-predictability)
    5.10.6    → 5.14   (Cluster-stability check)
    5.10.7    → 5.15   (Multi-granularity switching)
    5.10.8    → 5.16   (Per-cluster semantic inspection)
    5.10.9    → 5.17   (Per-family heterogeneity / persistence)
    5.10.10   → 5.18   (V* parameter-grid sensitivity)
    5.10.11   → 5.19   (Replace-mode tautology probe)
    5.11      → 5.20   (Cross-metric correlations)
    5.12      → 5.21   (Why exactly five regimes)
    5.13      → 5.22   (Embedding-space invariance)
    5.14      → 5.23   (Cross-model thesis verification)

Body refs (§N.M tokens) are renumbered atomically via a single regex
pass so the many collisions (e.g. old 5.10 → 5.12 and old 5.12 → 5.21)
don't step on each other.
"""
from __future__ import annotations

import re
from pathlib import Path


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")

# === Heading map (markdown-source line → markdown-source line) ===
# Order: descending OLD number to avoid intra-pass collisions.
HEADING_MAP = [
    # §3.1 (descending old number)
    ("#### 3.1.4 Tokens vs nats — a brief caveat",
     "#### 3.1.6 Tokens vs nats — a brief caveat"),
    ("#### 3.1.3 Append-mode accumulation barrier (Conjecture 1)",
     "#### 3.1.5 Append-mode accumulation barrier (Conjecture 1)"),
    ("#### 3.1.2 Replace-mode access bound: hitting probability and generation budget",
     "#### 3.1.4 Replace-mode access bound: hitting probability and generation budget"),
    ('#### 3.1.1.5 Operational criteria for "attractor-like" regimes',
     '#### 3.1.3 Operational criteria for "attractor-like" regimes'),
    ('#### 3.1.1bis Three operational endpoints for "barrier height"',
     '#### 3.1.2 Three operational endpoints for "barrier height"'),

    # §5.10.x → 5.13–5.19 (descending so 5.10.11 done before 5.10.10 etc.)
    ("### 5.10.11 Replace-mode tautology probe — overwrite vs insert",
     "### 5.19 Replace-mode tautology probe — overwrite vs insert"),
    ("### 5.10.10 V* parameter-grid sensitivity (review weakness #5 follow-up)",
     "### 5.18 V* parameter-grid sensitivity"),
    ('### 5.10.9 Per-family heterogeneity and persistence of "switching"',
     '### 5.17 Per-family heterogeneity and persistence of "switching"'),
    ("### 5.10.8 Per-cluster semantic inspection: what do the basins actually contain?",
     "### 5.16 Per-cluster semantic inspection"),
    ("### 5.10.7 Multi-granularity switching: does the dose-response survive different cluster definitions?",
     "### 5.15 Multi-granularity switching"),
    ("### 5.10.6 Cluster-stability check: do the basins survive method changes?",
     "### 5.14 Cluster-stability check"),
    ("### 5.10.5 Group-aware basin-predictability: how much leakage is in the headline number?",
     "### 5.13 Group-aware basin-predictability"),

    # §5.11–5.14 → 5.20–5.23 (descending)
    ("### 5.14 Cross-model thesis verification: do the headline claims survive on a smaller generator?",
     "### 5.23 Cross-model thesis verification"),
    ("### 5.13 Embedding-space invariance: do the regimes survive a different embedder?",
     "### 5.22 Embedding-space invariance"),
    ("### 5.12 Why exactly five regimes? An unsupervised-clustering check",
     "### 5.21 Why exactly five regimes? An unsupervised-clustering check"),
    ("### 5.11 Cross-metric correlations: do the regime diagnostics agree?",
     "### 5.20 Cross-metric correlations"),

    # §5.10 → 5.12, descending after that
    ("### 5.10 Geometric barriers from V(x) = −log ρ(x)",
     "### 5.12 Geometric barriers from V(x) = −log ρ(x)"),
    ("### 5.9 Cross-experiment aggregation",
     "### 5.11 Cross-experiment aggregation"),
    ("### 5.8 Phase 3d — drill-down dialog (D2)",
     "### 5.10 Phase 3d — drill-down dialog (D2)"),
    ("### 5.7 Phase 3c — injection-time sweep",
     "### 5.9 Phase 3c — injection-time sweep"),
    ("#### 5.6.1 Confirmatory dense-dose rerun (n=200/cell, 8 doses)",
     "#### 5.8.1 Confirmatory dense-dose rerun (n=200/cell, 8 doses)"),
    ("### 5.6 Phase 3b — dose-response",
     "### 5.8 Phase 3b — dose-response"),
    ("### 5.5 Phase 3a — perturbation pilots",
     "### 5.7 Phase 3a — perturbation pilots"),
    ("### 5.4 Phase 2b — temperature sensitivity",
     "### 5.6 Phase 2b — temperature sensitivity"),
    ("### 5.3 Phase 2 — publication-scale verification",
     "### 5.5 Phase 2 — publication-scale verification"),
    ("### 5.2 Phase 1 — small-N taxonomy (one-line)",
     "### 5.4 Phase 1 — small-N taxonomy (one-line)"),
    ("### 5.1 Phase 0 — pilot validation (one-line)",
     "### 5.3 Phase 0 — pilot validation (one-line)"),
    ("### 5.0 The four (plus one) regimes at a glance",
     "### 5.2 The four (plus one) regimes at a glance"),
    ("### 5.0bis Unified primary-results table",
     "### 5.1 Unified primary-results table"),
]

# Body §-ref renumbering done atomically via regex callback so all
# old → new mappings substitute simultaneously without collision.
REF_MAP = {
    "3.1.1bis": "3.1.2",
    "3.1.1.5": "3.1.3",
    "3.1.4":   "3.1.6",
    "3.1.3":   "3.1.5",
    "3.1.2":   "3.1.4",
    "5.0bis":  "5.1",
    "5.0":     "5.2",
    "5.1":     "5.3",
    "5.2":     "5.4",
    "5.3":     "5.5",
    "5.4":     "5.6",
    "5.5":     "5.7",
    "5.6.1":   "5.8.1",
    "5.6":     "5.8",
    "5.7":     "5.9",
    "5.8":     "5.10",
    "5.9":     "5.11",
    "5.10":    "5.12",
    "5.10.5":  "5.13",
    "5.10.6":  "5.14",
    "5.10.7":  "5.15",
    "5.10.8":  "5.16",
    "5.10.9":  "5.17",
    "5.10.10": "5.18",
    "5.10.11": "5.19",
    "5.11":    "5.20",
    "5.12":    "5.21",
    "5.13":    "5.22",
    "5.14":    "5.23",
}


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")

    # === Pass 1: heading renames ===
    missing = []
    for old, new in HEADING_MAP:
        if old not in text:
            missing.append(old)
            continue
        text = text.replace(old, new)
    if missing:
        print(f"WARNING: {len(missing)} heading(s) not found:")
        for m in missing:
            print(f"  {m!r}")

    # === Pass 2: body §-ref renumbering ===
    # Two regex passes: one for §-style refs, one for \S-style refs
    # (which appear inside tex-raw blocks). Both anchor on a literal
    # leading marker so §4.5.X refs are NOT touched.
    #
    # NOTE: in Python regex, `\S` is the special class "non-whitespace".
    # To match a literal backslash-S in text we need pattern `\\S`,
    # which in a Python raw string is written `r"\\\\S"` (4 backslashes
    # → regex sees `\\S` → literal `\` + literal `S`).
    sec_alt = r"(3\.1\.(?:1bis|\d+(?:\.\d+)?)|5\.(?:0bis|\d+(?:\.\d+)?))"
    pat_section = re.compile(r"§" + sec_alt)
    # Match literal backslash + S in text (the `\S` macro inside
    # tex-raw blocks). In a Python raw string, `\\S` = backslash +
    # backslash + S (3 chars); regex parses as escape-backslash plus
    # literal-S, matching `\S` in text.
    pat_backslashS = re.compile(r"\\S" + sec_alt)

    def repl(m: re.Match, prefix: str) -> str:
        key = m.group(1)
        new = REF_MAP.get(key, key)
        return f"{prefix}{new}"

    new_text, n_section = pat_section.subn(lambda m: repl(m, "§"), text)
    new_text, n_backslashS = pat_backslashS.subn(lambda m: repl(m, "\\S"), new_text)
    print(f"§-ref substitutions: {n_section}")
    print(f"\\S-ref substitutions: {n_backslashS}")

    ARTICLE.write_text(new_text, encoding="utf-8")

    # === Verification: confirm no bis/.5 patterns remain ===
    leftover_bis = re.findall(r"§?\d+\.\d+(?:\.\d+)?bis", new_text)
    leftover_15 = re.findall(r"§3\.1\.1\.5", new_text)
    leftover_5_15 = re.findall(r"§5\.0bis", new_text)
    print(f"leftover bis: {len(leftover_bis)} (samples: {leftover_bis[:5]})")
    print(f"leftover §3.1.1.5: {len(leftover_15)}")
    print(f"leftover §5.0bis: {len(leftover_5_15)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
