"""Round-31: define shortcuts at or before first use, per GPT-5.5 audit.

FAILs fixed by inline definitions or strategic glossaries:
  ED50_raw, ED50_persist  -> brief inline def at first abstract/§1.3 use
  O1, O2, O3, D1, D2      -> regime-code glossary inserted at end of §3.1
  RG                      -> expand "RG merge-distance" to "renormalization-
                              group-style merge-distance" on first use

MINORs fixed by acronym expansion on first use:
  4PL, GLMM, HDBSCAN, KDE, LFS, MVP, PCA-10
"""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

# === FAIL: ED50_raw in abstract — inline definition ===
text = text.replace(
    "produce raw-switching $\\mathrm{ED50}_{\\mathrm{raw}} \\approx 40$\ntokens, with convergent estimates from pooled logistic fitting,",
    "produce a raw-switching effective dose at 50% ($\\mathrm{ED50}_{\\mathrm{raw}}$, the smallest injected-token dose at which the perturbed trajectory's final cluster differs from its paired control's final cluster with probability at least one half) of approximately 40 tokens, with convergent estimates from pooled logistic fitting,",
)

# === FAIL: ED50_persist in §1.3 — inline definition ===
text = text.replace(
    "and $\\mathrm{ED50}_{\\mathrm{persist}}$ is not reached for any tested dose from 5 to 400 tokens.",
    "and the persistent-escape ED50 ($\\mathrm{ED50}_{\\mathrm{persist}}$, the smallest dose at which the perturbation produces a visible at-injection basin jump that is also retained at the terminal step with probability at least one half) is not reached for any tested dose from 5 to 400 tokens.",
)

# === FAIL: regime-code glossary inserted at end of §3.1 ===
# Insert just before the §3.1.1 sub-subsection
glossary = (
    "Throughout the paper we refer to five concrete instantiations of the "
    "$(f, \\eta)$ framework by short code:\n\n"
    "- **O1 (contractive append):** continuation operator $f=\\text{continue}$ under append nudge.\n"
    "- **O2 (oscillatory replace):** paraphrase operator under replace nudge.\n"
    "- **O3 (absorbing replace):** summarize-and-negate operator under replace nudge.\n"
    "- **D1 (role-structured dialog):** curious-user / helpful-agent dialog under the dialog nudge.\n"
    "- **D2 (drill-down dialog):** explorer / expert dialog under the dialog nudge, with successive subtopic refinement.\n\n"
    "The dialog regimes are append-style at the trajectory level but role-structured at the turn level. "
    "Wherever \"O1\", \"O2\", \"O3\", \"D1\", or \"D2\" appears below, it refers to the corresponding generator-nudge pair listed here.\n\n"
)
text = text.replace(
    "#### 3.1.1 Barrier height as a persistent-escape estimand",
    glossary + "#### 3.1.1 Barrier height as a persistent-escape estimand",
)

# === FAIL: RG expansion ===
text = text.replace(
    "Full $V^\\star$ tables, RG merge-distance tables,",
    "Full $V^\\star$ tables, renormalization-group-style merge-distance tables (RG merge-distance: maximum Ward-linkage merge height across $k=48$ fine cluster centroids, used as a coarse-graining diagnostic of trajectory-cloud expansion),",
)

# === MINOR: 4PL on first use ===
text = text.replace(
    "the pooled 4PL fit gives ED50 = 36 tokens",
    "the pooled four-parameter logistic (4PL) fit gives ED50 = 36 tokens",
)

# === MINOR: GLMM expansion on first use ===
text = text.replace(
    "the mixed-effects GLMM gives 41 tokens",
    "the mixed-effects generalized linear mixed model (GLMM) gives 41 tokens",
)

# === MINOR: HDBSCAN first-use expansion ===
text = text.replace(
    "10% under K-means $k=4$, and 39.5% under HDBSCAN",
    "10% under K-means $k=4$, and 39.5% under HDBSCAN (hierarchical density-based spatial clustering of applications with noise, a variable-k density-based partition)",
    1,  # only first occurrence
)

# === MINOR: KDE first-use expansion ===
text = text.replace(
    "kernel-density estimator",
    "kernel density estimation (KDE)",
    1,
)

# === MINOR: LFS first-use expansion ===
text = text.replace(
    "tracked through LFS",
    "tracked through Git Large File Storage (git-LFS)",
    1,
)
text = text.replace(
    "LFS-tracked",
    "git-LFS-tracked",
)

# === MINOR: MVP first-use expansion ===
text = text.replace(
    "an MVP cross-vendor replication",
    "a minimum viable product (MVP) cross-vendor replication",
    1,
)
text = text.replace(
    "after the MVP matrix",
    "after the minimum-viable matrix",
    1,
)

# === MINOR: PCA-10 first-use expansion ===
# The first use is in §4.0 endpoint contract — ad inline note
text = text.replace(
    "by predicting the late basin from early PCA-10 state",
    "by predicting the late basin from early 10-component PCA projection (PCA-10) state",
)

ARTICLE.write_text(text, encoding="utf-8")
print(f"file length: {len(text)} chars")
