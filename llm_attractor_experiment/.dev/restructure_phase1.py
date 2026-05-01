"""Phase 1 of §5 Results restructuring (low-risk, reversible).

Operations performed atomically against ARTICLE.md:

  1. Cut current §5.1 (Unified primary-results table) — content moves to
     a new §13.1 Extended Data Table 1.
  2. Cut current §5.2 (The four (plus one) regimes at a glance) — content
     moves to a new §13.2 Extended Data Table 2.
  3. Insert a new opening paragraph at the start of §5 Results (where §5.1
     used to be).
  4. Rename "Phase X" chronological titles to content-led titles
     (§5.3–§5.10).
  5. Renumber remaining §5.X → §5.(X−2) for X ≥ 3.
  6. Insert new §13.1 + §13.2 at the head of the §13 supplementary appendix.
  7. Renumber existing §13.X to make room: §13.1 → §13.3, §13.2 → §13.4,
     §13.3 (final pointers) → §13.16, §13.4..§13.14 → §13.5..§13.15.
  8. Atomically update all body cross-references.

Existing structure of §13 (before this script):
  §13.1 Full statements and proofs (Lemma 1, Conjecture 1)
  §13.2 Code-snippet definitions for §4.5 metrics
  §13.3 Pointers to remaining supplementary material   [final position]
  §13.4 Perturbation injection mechanics (full)
  §13.5 Animation rendering pipeline (full)
  §13.6 Exact prompt templates (full)
  §13.7 Model versioning (full table)
  §13.8 Phase-0 pilot validation (moved from §5.1)
  §13.9 Phase-1 small-N taxonomy (moved from §5.2)
  §13.10 Perturbation visualization toolkit (full implementation)
  §13.11 Reproducibility commands and repository tree (full)
  §13.12 Operational attractor criteria — audit table
  §13.13 Geometric V* and RG dendrogram per-regime tables (moved from §5.10)
  §13.14 How to instrument your own recursive system

After this script:
  §13.1 Extended Data Table 1 — Unified primary-results audit table
  §13.2 Extended Data Table 2 — Regime comparison at a glance
  §13.3 Full statements and proofs (Lemma 1, Conjecture 1)
  §13.4 Code-snippet definitions for §4.5 metrics
  §13.5 Perturbation injection mechanics (full)
  §13.6 Animation rendering pipeline (full)
  §13.7 Exact prompt templates (full)
  §13.8 Model versioning (full table)
  §13.9 Phase-0 pilot validation (moved from §5.1)
  §13.10 Phase-1 small-N taxonomy (moved from §5.2)
  §13.11 Perturbation visualization toolkit (full implementation)
  §13.12 Reproducibility commands and repository tree (full)
  §13.13 Operational attractor criteria — audit table
  §13.14 Geometric V* and RG dendrogram per-regime tables (moved from §5.10)
  §13.15 How to instrument your own recursive system
  §13.16 Pointers to remaining supplementary material   [moved to last]
"""
from __future__ import annotations

import re
from pathlib import Path


ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")


# === Step 1+2: cut §5.1 and §5.2 content, save for §13 placement ===
# We find the literal section heading lines and slice the content
# between consecutive `### ` (subsection-level) headings.

OPENING_PARAGRAPH = """\
In append-mode continuation, in-distribution adversarial text produced
a reproducible raw-switching dose response with $\\mathrm{ED50}_{\\mathrm{raw}}
\\approx 40$ tokens, but this was not durable basin redirection: paired
controls already diverged at ${\\approx}35\\%$, net switching saturated
at $+32$ percentage points, and persistent escape did not reach $50\\%$
at any tested dose up to 400 tokens. Replace-mode loops showed
near-saturated raw switching in the original perturbation pilots, but
overwrite-versus-insert probes attributed most of that apparent
fragility to the context-update rule discarding prior state rather than
to a low injected-token barrier. The remaining results establish the
regime taxonomy at publication scale, quantify the dose and timing
dependence of perturbations, and then test whether the conclusions
survive leakage-aware cross-validation, alternative cluster
granularities, persistence criteria, density-landscape sensitivity,
embedder ablations, and within-vendor generator replication. The rest
of §5 stress-tests these claims from the primary measurements outward.

For the full row-by-row audit of primary endpoints, uncertainty
estimates, source files, and caveat flags, see Extended Data Table 1
(§13.1). A compact cross-regime lookup table is provided as Extended
Data Table 2 (§13.2); the main text introduces each measurement in
sequence.

"""

ED_TABLE_1_INTRO = """\
Extended Data Table 1 consolidates the decision-grade endpoints across
regimes, including point estimates, uncertainty, source artifacts, and
caveat flags. It is placed in Extended Data because it functions as an
audit map for reproducibility and interpretation, while the main
Results text reports the load-bearing measurements directly.

"""

ED_TABLE_2_INTRO = """\
Extended Data Table 2 provides the compact cross-regime comparison of
nudge type, content operator, basin predictability, recurrence,
sharpness dimension, perturbation response, dose scale, and
temperature sensitivity. It is placed in Extended Data to preserve the
original lookup table without interrupting the narrative sequence of
the Results section.

"""


# === Step 4: content-led title renames ===
# Old subsection title text → new subsection title text.
# Only the title line, not the section number prefix; the prefix
# is renumbered separately.
TITLE_MAP = {
    "5.3 Phase 0 — pilot validation (one-line)":
        "5.1 Pilot runs validate the measurement pipeline",
    "5.4 Phase 1 — small-N taxonomy (one-line)":
        "5.2 Small-N runs identify candidate regimes",
    "5.5 Phase 2 — publication-scale verification":
        "5.3 Publication-scale runs preserve regime ordering",
    "5.6 Phase 2b — temperature sensitivity":
        "5.4 Temperature sweep separates O1 and D1",
    "5.7 Phase 3a — perturbation pilots":
        "5.5 Perturbation pilots separate append from replace",
    "5.8 Phase 3b — dose-response":
        "5.6 Dose response depends on perturbation content",
    "5.8.1 Confirmatory dense-dose rerun (n=200/cell, 8 doses)":
        "5.6.1 Dense rerun localizes raw ED50",
    "5.9 Phase 3c — injection-time sweep":
        "5.7 Injection timing reveals basin hardening",
    "5.10 Phase 3d — drill-down dialog (D2)":
        "5.8 Drill-down dialog adds content gravity",
}

# === Step 5: §5.X renumber map (X ≥ 11) — mechanical shift by −2 ===
SECTION_5_RENUMBER = {
    # Already covered by TITLE_MAP for §5.3..§5.10 + §5.8.1
    "### 5.11 Cross-experiment aggregation": "### 5.9 Cross-experiment aggregation",
    "### 5.12 Geometric barriers from V(x) = −log ρ(x)": "### 5.10 Geometric barriers from V(x) = −log ρ(x)",
    "### 5.13 Group-aware basin-predictability": "### 5.11 Group-aware basin-predictability",
    "### 5.14 Cluster-stability check": "### 5.12 Cluster-stability check",
    "### 5.15 Multi-granularity switching": "### 5.13 Multi-granularity switching",
    "### 5.16 Per-cluster semantic inspection": "### 5.14 Per-cluster semantic inspection",
    '### 5.17 Per-family heterogeneity and persistence of "switching"':
        '### 5.15 Per-family heterogeneity and persistence of "switching"',
    "### 5.18 V* parameter-grid sensitivity": "### 5.16 V* parameter-grid sensitivity",
    "### 5.19 Replace-mode tautology probe — overwrite vs insert":
        "### 5.17 Replace-mode tautology probe — overwrite vs insert",
    "### 5.20 Cross-metric correlations": "### 5.18 Cross-metric correlations",
    "### 5.21 Why exactly five regimes? An unsupervised-clustering check":
        "### 5.19 Why exactly five regimes? An unsupervised-clustering check",
    "### 5.22 Embedding-space invariance": "### 5.20 Embedding-space invariance",
    "### 5.23 Cross-model thesis verification": "### 5.21 Cross-model thesis verification",
}


# === Body §-ref renumber maps (atomic, single regex pass) ===
# Old token → new token (without § prefix).
# Important: §5.1 (old) → §13.1 (Extended Data Table 1).
# Important: §5.2 (old) → §13.2 (Extended Data Table 2).
# All other §5.X (X ≥ 3) → §5.(X-2).
# §13.X renumber: §13.1 → §13.3, §13.2 → §13.4, §13.3 → §13.16,
# §13.4..§13.14 → §13.5..§13.15.

REF_MAP = {
    # §5.X moves
    "5.1": "13.1",     # was Unified primary-results table
    "5.2": "13.2",     # was Master regime comparison
    "5.3": "5.1",
    "5.4": "5.2",
    "5.5": "5.3",
    "5.6": "5.4",
    "5.6.1": "5.4.1",  # SHOULD be 5.6.1 → 5.4.1? Wait, no. 5.6 → 5.4, so 5.6.1 → 5.4.1.
                       # But §5.8 (Dose-response) was renamed §5.6, and §5.8.1 → §5.6.1.
                       # So §5.6.1 (old) doesn't exist; §5.8.1 → §5.6.1 (new).
    "5.7": "5.5",
    "5.8": "5.6",
    "5.8.1": "5.6.1",  # subsubsection rename
    "5.9": "5.7",
    "5.10": "5.8",
    "5.11": "5.9",
    "5.12": "5.10",
    "5.13": "5.11",
    "5.14": "5.12",
    "5.15": "5.13",
    "5.16": "5.14",
    "5.17": "5.15",
    "5.18": "5.16",
    "5.19": "5.17",
    "5.20": "5.18",
    "5.21": "5.19",
    "5.22": "5.20",
    "5.23": "5.21",
    # §13.X renumbers
    "13.1": "13.3",      # Lemma proofs
    "13.2": "13.4",      # Code snippets
    "13.3": "13.16",     # Pointers (final)
    "13.4": "13.5",      # Perturbation injection
    "13.5": "13.6",      # Animation pipeline
    "13.6": "13.7",      # Prompt templates
    "13.7": "13.8",      # Model versioning
    "13.8": "13.9",      # Phase-0 pilot
    "13.9": "13.10",     # Phase-1 small-N
    "13.10": "13.11",    # Perturbation viz toolkit
    "13.11": "13.12",    # Repro commands
    "13.12": "13.13",    # Attractor criteria audit
    "13.13": "13.14",    # V* RG dendrogram
    "13.14": "13.15",    # Instrument recursive system
}


def find_subsection(text: str, heading_pattern: str) -> tuple[int, int]:
    """Return (start, end) byte offsets of the subsection identified by
    the literal heading_pattern. The subsection extends from the heading
    line through (but not including) the next subsection-level heading
    (`### `) at the same level."""
    start = text.index(heading_pattern)
    # Find the end: next `### ` or `## ` heading after the heading line
    after_heading = start + len(heading_pattern)
    nl = text.index("\n", after_heading)
    rest_start = nl + 1
    # Scan forward line by line for next `### ` or `## ` at line start
    pos = rest_start
    end = len(text)
    while pos < len(text):
        nl = text.find("\n", pos)
        if nl == -1:
            break
        line = text[pos:nl]
        if line.startswith("### ") or line.startswith("## "):
            end = pos
            break
        pos = nl + 1
    return start, end


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")

    # === Step 1+2: cut §5.1 and §5.2 ===
    sec_51_start, sec_51_end = find_subsection(text, "### 5.1 Unified primary-results table")
    sec_51_content = text[sec_51_start:sec_51_end]
    text = text[:sec_51_start] + text[sec_51_end:]
    print(f"cut §5.1: {sec_51_end - sec_51_start} chars")

    sec_52_start, sec_52_end = find_subsection(text, "### 5.2 The four (plus one) regimes at a glance")
    sec_52_content = text[sec_52_start:sec_52_end]
    text = text[:sec_52_start] + text[sec_52_end:]
    print(f"cut §5.2: {sec_52_end - sec_52_start} chars")

    # Strip the original heading line from each — we'll attach a new heading.
    sec_51_body = sec_51_content.split("\n", 1)[1]
    sec_52_body = sec_52_content.split("\n", 1)[1]

    # === Step 3: insert opening paragraph at start of §5 ===
    # §5 Results header was the first ## heading in the §5 area.
    # New §5.1 (was §5.3) is "Phase 0 — pilot validation". Insert opening
    # paragraph just before that heading.
    pivot = text.index("### 5.3 Phase 0 — pilot validation (one-line)")
    text = text[:pivot] + OPENING_PARAGRAPH + text[pivot:]
    print(f"inserted opening paragraph ({len(OPENING_PARAGRAPH)} chars)")

    # === Step 4: rename §5.3..§5.10 with content-led titles ===
    for old_title, new_title in TITLE_MAP.items():
        old_heading = f"### {old_title}" if not old_title.startswith("5.8.1") else f"#### {old_title}"
        new_heading = f"### {new_title}" if not new_title.startswith("5.6.1") else f"#### {new_title}"
        if old_heading in text:
            text = text.replace(old_heading, new_heading)
        else:
            print(f"WARN: title not found: {old_heading!r}")

    # === Step 5: §5.11..§5.23 renumber with simple −2 shift ===
    for old_h, new_h in SECTION_5_RENUMBER.items():
        if old_h in text:
            text = text.replace(old_h, new_h)
        else:
            print(f"WARN: section not found: {old_h!r}")

    # === Step 7: renumber existing §13 sections to make room ===
    # Order: descending → ascending to avoid intra-pass collisions.
    # Specifically, §13.14 → §13.15 first, then §13.13 → §13.14, etc.
    # And §13.3 → §13.16 (special case).
    # Heading text taken verbatim from current HEAD; parenthetical
    # "(moved from §5.X)" annotations are dropped as part of cleanup.
    s13_renumbers = [
        ("### 13.14 How to instrument your own recursive system",
         "### 13.15 How to instrument your own recursive system"),
        ("### 13.13 Geometric V* and RG dendrogram per-regime tables (moved from §5.12)",
         "### 13.14 Geometric V* and RG dendrogram per-regime tables"),
        ("### 13.12 Operational attractor criteria — audit table",
         "### 13.13 Operational attractor criteria — audit table"),
        ("### 13.11 Reproducibility commands and repository tree (full)",
         "### 13.12 Reproducibility commands and repository tree (full)"),
        ("### 13.10 Perturbation visualization toolkit (full implementation)",
         "### 13.11 Perturbation visualization toolkit (full implementation)"),
        ("### 13.9 Phase-1 small-N taxonomy (moved from §5.4)",
         "### 13.10 Phase-1 small-N taxonomy"),
        ("### 13.8 Phase-0 pilot validation (moved from §5.3)",
         "### 13.9 Phase-0 pilot validation"),
        ("### 13.7 Model versioning (full table)",
         "### 13.8 Model versioning (full table)"),
        ("### 13.6 Exact prompt templates (full)",
         "### 13.7 Exact prompt templates (full)"),
        ("### 13.5 Animation rendering pipeline (full)",
         "### 13.6 Animation rendering pipeline (full)"),
        ("### 13.4 Perturbation injection mechanics (full)",
         "### 13.5 Perturbation injection mechanics (full)"),
        ("### 13.3 Pointers to remaining supplementary material",
         "### 13.16 Pointers to remaining supplementary material"),
        ("### 13.2 Code-snippet definitions for §4.5 metrics",
         "### 13.4 Code-snippet definitions for §4.5 metrics"),
        ("### 13.1 Full proof of Lemma 1 (Replace-mode hitting bound)",
         "### 13.3 Full proof of Lemma 1 (Replace-mode hitting bound)"),
    ]
    for old, new in s13_renumbers:
        if old in text:
            text = text.replace(old, new)
        else:
            print(f"WARN: §13 heading not found: {old!r}")

    # === Step 6: insert new §13.1 (was §5.1 content) and §13.2 (was §5.2 content) ===
    # Insert at the start of §13 supplementary appendix (before what is now §13.3).
    pivot13 = text.index("### 13.3 Full proof of Lemma 1")
    new_13_1 = (
        "### 13.1 Extended Data Table 1 — Unified primary-results audit table\n"
        "\n"
        + ED_TABLE_1_INTRO
        + sec_51_body.rstrip()
        + "\n\n"
    )
    new_13_2 = (
        "### 13.2 Extended Data Table 2 — Regime comparison at a glance\n"
        "\n"
        + ED_TABLE_2_INTRO
        + sec_52_body.rstrip()
        + "\n\n"
    )
    text = text[:pivot13] + new_13_1 + new_13_2 + text[pivot13:]
    print(
        f"inserted §13.1 ({len(new_13_1)} chars) + §13.2 ({len(new_13_2)} chars) "
        f"at offset {pivot13}"
    )

    # === Step 8: atomic body §-ref renumber ===
    # Pattern matches §X.Y(.Z) or \SX.Y(.Z) inside tex-raw blocks.
    sec_alt = r"((?:5|13)\.\d+(?:\.\d+)?)"
    pat_section = re.compile(r"§" + sec_alt)
    pat_backslashS = re.compile(r"\\S" + sec_alt)

    def make_repl(prefix: str):
        def repl(m: re.Match) -> str:
            key = m.group(1)
            new = REF_MAP.get(key, key)
            return f"{prefix}{new}"
        return repl

    text, n_section = pat_section.subn(make_repl("§"), text)
    text, n_backslashS = pat_backslashS.subn(make_repl("\\S"), text)
    print(f"§-ref body subs: {n_section}; \\S-ref tex-raw subs: {n_backslashS}")

    # === Final: write back ===
    ARTICLE.write_text(text, encoding="utf-8")

    # === Verification ===
    print()
    print("Heading sequence (sanity check):")
    for line in text.split("\n"):
        if line.startswith("### 5.") or line.startswith("### 13.") or line == "## 5. Results":
            print(f"  {line[:120]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
