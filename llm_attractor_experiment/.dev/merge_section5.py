"""Merge §5.8+§5.9, §5.10+§5.11, §5.12+§5.13 into 3 consolidated subsections.

Old §5.8 + §5.9  -> new §5.8 "Within-regime structure: cluster semantics and family heterogeneity"
Old §5.10 + §5.11 -> new §5.9 "Robustness: embedder ablation and within-vendor cross-model verification"
Old §5.12 + §5.13 -> new §5.10 "Bulk geometry is descriptive, not endpoint-defining"

Approach:
1. Rewrite the header of §5.8 to the merged header (containing intro paragraph)
2. Replace `### 5.9` with a `**Family heterogeneity sub-section**` strong-emphasis intro
3. Rewrite header of §5.10 to merged header + intro
4. Replace `### 5.11` with `**Cross-model thesis verification.**`
5. Rewrite header of §5.12 to merged header + intro
6. Replace `### 5.13` with `**Why exactly five regimes.**`
7. Globally renumber cross-refs §5.9->§5.8, §5.10/§5.11->§5.9, §5.12/§5.13->§5.10
   using two-pass placeholder substitution to avoid swap cycles
8. Update the §5 reading guide.
"""
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")

# ============================================================
# Step 1: Rewrite §5.8 header
# ============================================================
old_58_header = "### 5.8 Per-cluster semantic inspection\n\nWe extracted representative trajectory text from each K-means cluster"
new_58_header = (
    "### 5.8 Within-regime structure: cluster semantics and family heterogeneity\n\n"
    "Two analyses examine variability within each regime. The first inspects what the K-means clusters "
    "represent semantically, on a per-regime basis. The second documents per-family heterogeneity behind "
    "the population-level O1 dose response. Together they sharpen the regime taxonomy without changing "
    "the headline endpoint claims.\n\n"
    "**Cluster semantics.** We extracted representative trajectory text from each K-means cluster"
)
assert old_58_header in text, "expected §5.8 header anchor not found"
text = text.replace(old_58_header, new_58_header, 1)

# ============================================================
# Step 2: Replace §5.9 header with bold-tag continuation
# ============================================================
old_59_header = "### 5.9 Per-family heterogeneity\n\nThe sparse O1 adversarial dose grid"
new_59_header = "**Family heterogeneity.** The sparse O1 adversarial dose grid"
assert old_59_header in text, "expected §5.9 header anchor not found"
text = text.replace(old_59_header, new_59_header, 1)

# ============================================================
# Step 3: Rewrite §5.10 header
# ============================================================
old_510_header = "### 5.10 Embedding-space invariance\n\nThe main measurements use `text-embedding-3-small`"
new_510_header = (
    "### 5.9 Robustness: embedder ablation and within-vendor cross-model verification\n\n"
    "Two robustness checks address whether the regime taxonomy survives substitution of the measurement "
    "embedder and substitution of the generator. The first re-embeds representative experiments with "
    "alternative text embedders. The second reruns the regime-level predicates on a within-vendor smaller "
    "model. Both checks confirm the qualitative taxonomy without numerically replicating the headline "
    "ED50 or persistence endpoints.\n\n"
    "**Embedder ablation.** The main measurements use `text-embedding-3-small`"
)
assert old_510_header in text, "expected §5.10 header anchor not found"
text = text.replace(old_510_header, new_510_header, 1)

# ============================================================
# Step 4: Replace §5.11 header
# ============================================================
old_511_header = "### 5.11 Cross-model thesis verification\n\nWe also ran a cross-generator audit"
new_511_header = "**Cross-model thesis verification.** We also ran a cross-generator audit"
assert old_511_header in text, "expected §5.11 header anchor not found"
text = text.replace(old_511_header, new_511_header, 1)

# ============================================================
# Step 5: Rewrite §5.12 header
# ============================================================
old_512_header = "### 5.12 Density landscapes are descriptive, not calibrated\n\nThe $V(x) = -\\log \\hat{\\rho}(x)$ density-landscape analyses"
new_512_header = (
    "### 5.10 Bulk geometry is descriptive, not endpoint-defining\n\n"
    "Two methodological analyses test whether bulk-geometry diagnostics could replace perturbation evidence "
    "as the basis for regime classification. The first checks the parameter sensitivity of the empirical "
    "potential-barrier summary $V^\\star$. The second asks whether unsupervised clustering of bulk "
    "diagnostic vectors recovers the five-regime taxonomy. Both analyses conclude that bulk geometry is "
    "useful for description but cannot stand in for the perturbation endpoints used in §5.1 and §5.2.\n\n"
    "**Density landscape sensitivity.** The $V(x) = -\\log \\hat{\\rho}(x)$ density-landscape analyses"
)
assert old_512_header in text, "expected §5.12 header anchor not found"
text = text.replace(old_512_header, new_512_header, 1)

# ============================================================
# Step 6: Replace §5.13 header
# ============================================================
old_513_header = "### 5.13 Why exactly five regimes?\n\nThis subsection is supportive: it shows that bulk geometry alone"
new_513_header = "**Why exactly five regimes.** This sub-analysis shows that bulk geometry alone"
assert old_513_header in text, "expected §5.13 header anchor not found"
text = text.replace(old_513_header, new_513_header, 1)

# ============================================================
# Step 7: Globally renumber cross-references using placeholder pass
# ============================================================
# Order matters. Convert old refs to placeholders, then placeholders to new refs.
PH = "\x00§§"  # unique placeholder marker
mappings = [
    ("§5.13",  PH + "10b"),  # §5.13 -> §5.10
    ("§5.12",  PH + "10a"),  # §5.12 -> §5.10
    ("§5.11",  PH + "9b"),   # §5.11 -> §5.9
    ("§5.10",  PH + "9a"),   # §5.10 -> §5.9
    ("§5.9",   PH + "8b"),   # §5.9  -> §5.8
]
for old, ph in mappings:
    text = text.replace(old, ph)

# Resolve placeholders to new section numbers
text = text.replace(PH + "10a", "§5.10")
text = text.replace(PH + "10b", "§5.10")
text = text.replace(PH + "9a",  "§5.9")
text = text.replace(PH + "9b",  "§5.9")
text = text.replace(PH + "8b",  "§5.8")

# ============================================================
# Step 8: Update the §5 reading guide paragraph
# ============================================================
old_guide = (
    "*Phase B - regime characterization and robustness* spans §5.3 through §5.13 and supports the regime "
    "taxonomy: §5.3 publication-scale ordering; §5.4 perturbation-content separation; §5.5 dialog drill-down; "
    "§5.6 injection-timing basin hardening; §5.7 cluster-granularity stability; §5.8 per-cluster semantics; "
    "§5.9 family heterogeneity; §5.10 embedding invariance; §5.11 cross-model verification; §5.12 "
    "density-landscape sensitivity; §5.13 why exactly five regimes."
)
new_guide = (
    "*Phase B - regime characterization and robustness* spans §5.3 through §5.10 and supports the regime "
    "taxonomy: §5.3 publication-scale ordering; §5.4 perturbation-content separation; §5.5 dialog drill-down; "
    "§5.6 injection-timing basin hardening; §5.7 cluster-granularity stability; §5.8 within-regime "
    "structure (cluster semantics and family heterogeneity); §5.9 robustness (embedder ablation and "
    "within-vendor cross-model verification); §5.10 bulk geometry is descriptive."
)
# The guide has slightly different ASCII-dash forms; try both
if old_guide in text:
    text = text.replace(old_guide, new_guide, 1)
else:
    # the guide may have been modified by the placeholder pass already
    # search for the new pattern that resulted from the renumbering
    interim_guide = (
        "*Phase B - regime characterization and robustness* spans §5.3 through §5.10 and supports the regime "
        "taxonomy: §5.3 publication-scale ordering; §5.4 perturbation-content separation; §5.5 dialog drill-down; "
        "§5.6 injection-timing basin hardening; §5.7 cluster-granularity stability; §5.8 per-cluster semantics; "
        "§5.8 family heterogeneity; §5.9 embedding invariance; §5.9 cross-model verification; §5.10 "
        "density-landscape sensitivity; §5.10 why exactly five regimes."
    )
    if interim_guide in text:
        text = text.replace(interim_guide, new_guide, 1)
    else:
        print("WARN: §5 reading guide not matched; manual fix needed")

ARTICLE.write_text(text, encoding="utf-8")
print(f"final length: {len(text)} chars")
