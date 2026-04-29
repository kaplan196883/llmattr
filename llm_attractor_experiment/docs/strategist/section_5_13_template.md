# §5.13 — Embedding-space invariance ablation (template)

**Status**: ablation running in background. This file is the writeup
skeleton that will be inlined into ARTICLE.md once `data/aggregated/
embedding_ablation/results.csv` lands.

---

### 5.13 Embedding-space invariance: do the regimes survive a different embedder?

A natural reviewer challenge: the regime taxonomy is defined on
embeddings from `text-embedding-3-small` (OpenAI, 1536-dim). Would
the regimes change with a different embedder? We test this by
re-embedding 5,000-step subsamples of 5 representative experiments
(one per regime) under two alternative models:

- **`text-embedding-3-large`** (OpenAI, 3072-dim) — within-vendor
  scale-up.
- **`all-mpnet-base-v2`** (sentence-transformers, 768-dim, local) —
  cross-architecture, open-source.

For each (experiment × embedding model) cell we recompute three
canonical diagnostics (recurrence rate at PCA-10, sharpness dim_late
from PCA-10 ensemble spread, basin predictability acc(*k*=10) from
KMeans-late + LR-from-step-10).

| regime | metric | small (1536) | large (3072) | mpnet (768) |
|---|---|---:|---:|---:|
| O1 | recurrence | TBD | TBD | TBD |
| O1 | sharpness_dim_late | TBD | TBD | TBD |
| O1 | basin_pred(k=10) | TBD | TBD | TBD |
| O2 | … | … | … | … |
| O3 | … | … | … | … |
| D1 | … | … | … | … |
| D2 | … | … | … | … |

**Robustness criterion (per regime)**: are the three diagnostics
within ±20% of each other across embedding models? Are the
between-regime *orderings* preserved (i.e., does O3 still have the
highest recurrence; D1 the highest sharpness dim; etc.)?

**Expected answer**: yes — embeddings from different models share
the same coarse semantic axes, so the cluster / basin structure
should be invariant under embedding-space dimensional rescaling.
Discrepancies would signal the regime taxonomy is an artifact of a
specific embedder's biases rather than a property of the recursive
LLM dynamics.

**Result** (placeholder — populate from `data/aggregated/
embedding_ablation/results.csv`):

> [TBD: e.g., "All three diagnostics are within ±18% across the
> three embedding models for every regime; the regime ordering on
> recurrence (O3 > O2 ≫ O1, D1 ≈ D2) is preserved by all three
> embedders. The regime taxonomy is therefore robust to embedding
> choice in the tested range — the regimes are properties of the
> recursive dynamics, not of the embedding model."]

(Full ablation script: `scripts/embedding_ablation.py`. Per-cell
results: `data/aggregated/embedding_ablation/results.csv`. Comparison
plot: `data/aggregated/embedding_ablation/comparison.png`.)

---

*This template will be inlined into ARTICLE.md after §5.12 once the
ablation completes. The §5.x section numbering shifts: current
§5.10 → §5.10 (geometric barriers); §5.11 → §5.11 (cross-metric
correlations); §5.12 → §5.12 (cluster validation); new §5.13
(embedding ablation).*
