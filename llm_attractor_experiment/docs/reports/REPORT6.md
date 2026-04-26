# REPORT 6 — Three publication-scale experiments: the contractive, oscillatory, and stylistic-multi-basin regimes

**Date:** 2026-04-24
**Experiments:**
- `exp_pub_O1_continue`     — operator *continue*, loop_mode *append*     (REPORT5, re-referenced)
- `exp_pub_O2_paraphrase_replace` — operator *paraphrase*, loop_mode *replace*
- `exp_pub_D1_dialog_curious_helpful` — two-LLM *dialog*, loop_mode *append*

**Model:** `gpt-4o-mini`, T=0.8, `text-embedding-3-small`
**Aggregate resolution:** 15 × 30 × 3 = **1,350 recursive trajectories per operator-experiment**, 450 for D1 (5 dialog-appropriate families × 30 ICs × 3 runs)
**Aggregate API cost:** ~$110 (O2_pub ~$55 + D1_pub ~$5 + O1_pub $55 from REPORT5)

## 1. What this report answers

REPORT5 established publication-grade confirmation of the **contractive** regime (O1_pub, operator *continue*). Two regimes from REPORT3's small-N taxonomy remained unconfirmed at scale:

- the **oscillatory** regime claimed for `paraphrase + replace` (REPORT2 §4, N=3: best_period_median=2, period_2_score mean ≈ +0.40),
- the **stylistic multi-basin** regime claimed for two-LLM dialog (REPORT3 §5.3, N=45 across D1/D2/D3).

REPORT6 answers: **do those two regime claims also survive at 1,350 and 450 trajectories respectively?** And, secondarily, do the three regimes now give clean, distinct three-axis classifier signatures when scored on the same apparatus?

## 2. Three-axis verdict comparison

| axis | O1_pub (continue/append) | **O2_pub (paraphrase/replace)** | D1_pub (dialog/append) |
|---|---|---|---|
| **H1a — convergence** | strong_support | strong_support | strong_support |
| **H1b — recurrence** | not_supported | **moderate_support** | not_supported |
| **H1c — divergence** | not_supported | not_supported | not_supported |

All three land in a basin-like regime (H1a strong across the board). Only O2_pub shows the oscillation signature; O1_pub and D1_pub are clean period-1 contractive. None diverges.

## 3. The period-2 signature at N=1,350

The H1b verdict for O2_pub flips from `not_supported` (main analyze) to `moderate_support` (three-axis analyze_ext) because the two use different H1b metrics:

- **main pipeline** tests `late_recurrence_above_null` — the probability of returning to within ε=0.15 cosine of a past point after basin entry. A stable 2-cycle *does not* satisfy this — trajectories alternate between two distinct points ≥ ε apart, so late_recurrence stays near the temporal-null baseline.
- **three-axis classifier** additionally computes `period_2_score` (normalized autocorrelation at lag 2 vs lag 1) and `best_period` (argmax of the autocorrelation-period spectrum).

O2_pub's numbers (1,350 recursive trajectories, raw embedding space):

| observable | period_2_score mean | period_2_score std | best_period median | n |
|---|---:|---:|---:|---:|
| context_tail | **+0.0762** | 0.0559 | **2.0** | 1350 |
| output       | **+0.0762** | 0.0559 | **2.0** | 1350 |
| rolling_k3   | +0.0138 | 0.0127 | **2.0** | 1350 |

**Fraction of runs whose best period is > 1: 0.95** (1,283 / 1,350).

Per-family variation is small; the effect is global. Compare to the two period-1 experiments:

| experiment | mean period_2_score (rolling_k3) | fraction best_period > 1 |
|---|---:|---:|
| O1_pub | −0.037 | 0.02 |
| O2_pub | **+0.014** (+0.076 in `output` and `context_tail`) | **0.95** |
| D1_pub | −0.072 | 0.02 |

The small-N REPORT2 claim — `paraphrase + replace` yields a stable 2-cycle — **survives the 50× scale-up**. The cycle is not a sampling artifact of three runs.

**Why `replace` matters.** `paraphrase` with `loop_mode=append` would grow a chain of near-duplicate paraphrases (the old text stays in context), producing a slow contractive drift — the REPORT3 O4 pattern. With `loop_mode=replace` the context is overwritten each step; the model only sees last step's paraphrase, which it paraphrases again. Two-cycle emerges because `paraphrase(paraphrase(x)) ≈ x` — a specific semantic fixed-point of the composition, which is not the same as the fixed-point of `paraphrase` alone. This is the operator-composition signature predicted in Tuci et al. 2025 §3.2 for non-idempotent update rules under the random-dynamical-systems framework (REPORT4 §4).

## 4. Basin geometry across the three experiments

| experiment | basin mean | basin range [min, max] per family |
|---|---:|---|
| O1_pub | 0.933 | [0.80, 1.00] (15 families) |
| **O2_pub** | **0.979** | [0.94, 1.00] (15 families, highest ever recorded) |
| D1_pub | 0.775 | [0.68, 0.87] (5 families) |

O2_pub's basin mean is the highest of any experiment run in this project. The interpretation is consistent: a stable 2-cycle is a *more strongly contracting* attractor than a point basin, because the Jacobian of `paraphrase ∘ paraphrase` is more constrained than `paraphrase` alone (any drift in one step is corrected by the next). The 2-cycle is a **1-dimensional attractor** in embedding space, and basin_score measures cross-run cluster agreement, so both runs entering the same orbit count as "same basin" regardless of phase.

D1_pub's lower basin mean (0.775) is the stylistic-multi-basin regime: within a single family (e.g., *reflective*, basin=0.684), different ICs end up in different sub-clusters depending on the conversational trajectory. The 5 dialog-appropriate families span [0.68, 0.87] with the most open-ended (`reflective`, `emotional`) at the low end and the most convention-bound (`creative_dialog`, `practical_dialog`) at the high end.

## 5. Permutation-test signatures (recursive − time_shuffled, 1000 resamples)

### Dwell — all three experiments show highly significant positive effects

- **O1_pub:** dwell positive in 3/3 observables, all p=0.000, mean_diff [1.59, 7.79] steps
- **O2_pub:** dwell positive in 1/3 observables significantly (`rolling_k3`, mean_diff=**+3.16**, p=0.000); other two positive but not significant at α=0.05
- **D1_pub:** dwell positive in 8/8 observables, all p=0.000, mean_diff [0.53, 4.40] steps

The weaker O2_pub dwell signal in `output` and `context_tail` is a direct consequence of the 2-cycle: in the K-means assignment, a trajectory that alternates between two neighboring clusters has short per-cluster dwell times by construction. The `rolling_k3` window averages across the 2-cycle and therefore preserves the signal — as expected.

### Global recurrence — all three are *below* time_shuffled (= contractive flow)

- **O1_pub:** 8/12 combinations with p < 0.001
- **O2_pub:** 3/12 significant (`rolling_k3 × {raw, pca10, pca20}`). Weaker than O1 because a 2-cycle has its recurrence split across two centers rather than piled at one.
- **D1_pub:** **32/32 combinations** (observable × space × metric) with p = 0.000 — the strongest recurrence-below-null signature of any experiment. Attributed to dialog's role alternation producing narrow regions in the role-specific observables (`last_user_turn`, `rolling_agent_k3`, etc.), which show cleanly separated per-speaker basins.

## 6. The (λ_1, SD) regime map adds a third cluster

REPORT5 Table §5 showed the 15-family (λ_1_late, SD_late) scatter for O1_pub, range λ_1_late ∈ [+0.004, +0.009], SD_late ∈ [1.19, 1.86] — all in the "contractive" quadrant.

O2_pub adds a second cluster to that plot:
- λ_1_late mean (rolling_k3, aggregate over 15 families): **+0.0012** (≈ 5× smaller than O1_pub's +0.0066) → stable, but with near-zero expansion: consistent with a 2-cycle's neutral per-step Jacobian.
- SD_late mean: **0.97 ± 0.4** (vs 1.58 in O1_pub) → roughly half a dimension, matching the 1-D orbit interpretation: a 2-cycle has rank-1 ensemble covariance at late times.

D1_pub's regime-map position:
- λ_1_late mean (rolling_k3): +0.0089
- SD_late mean: 1.71
Similar to O1_pub but slightly more expansive, consistent with multi-sub-basin structure within each family.

The three experiments now occupy three visibly distinct positions in (λ_1_late, SD_late) space:

| experiment | λ_1_late | SD_late | regime interpretation |
|---|---:|---:|---|
| O1_pub | +0.0066 | 1.58 | contractive point-basin |
| **O2_pub** | **+0.0012** | **0.97** | **stable 2-cycle on 1-D orbit** |
| D1_pub | +0.0089 | 1.71 | stylistic multi-basin |

This is the REPORT3 three-regime taxonomy *quantitatively reproduced* at publication scale, using the RDS-framework measurements from REPORT4.

## 7. New finding unique to O2_pub — the cycle is globally synchronous

A subtle observation visible only at N=1,350: the two centers of the period-2 orbit are **the same across different ICs within a family**, not IC-specific. That is, `paraphrase ∘ paraphrase` on the 30 distinct philosophy-dialog seeds converges to essentially one 2-cycle orbit per family, with the 30 seeds sorting into "even-step basin" vs "odd-step basin" depending on phase.

Evidence: per-IC basin_score is 1.00 for 95% of ICs (runs from the same IC lock into the same orbit phase), but the per-family target_cluster (used for basin scoring) is the same for most ICs in a family. This is a much stronger attractor than O1_pub's contractive basin, where each IC has its own basin center.

**Interpretation:** O2_pub reveals gpt-4o-mini has (within each prompt family) a characteristic *paraphrase fixed-point pair* — a two-element orbit the model gravitates to when composing paraphrase with itself. This is directly analogous to the "statistical optimum" predicted in Tuci et al. 2025 §2.3 for non-identity operators whose composition has a 2-fold symmetry.

## 8. Visualization summary (v2 dark-theme plots)

All 3 pub experiments produce identically-structured plots under their `reports/plots/`:

| plot | O1_pub | O2_pub | D1_pub |
|---|---|---|---|
| `A_v2_joint_by_family_rolling_k3.png` | 15 families visible | 15 families, **tighter clusters** | 5 families, role-stratified |
| `A_v2_joint_by_regime_rolling_k3.png` | orange filaments vs blue clumps | orange **2-point centroids** | orange sub-clusters vs blue clumps |
| `A_v2_joint_by_step_rolling_k3.png` | time-ordered drift-in | step alternation visible (odd/even steps separate) | time-ordered drift + role alternation |
| `B_v2_per_family_grid_rolling_k3.png` | 30 sub-basins per family | 30 ICs collapsed into 2-point orbits per family | 30 ICs forming 2-5 sub-clusters per family |

The O2_pub `A_v2_joint_by_step` plot is diagnostic: within-family, odd-step embeddings and even-step embeddings occupy distinct regions of t-SNE space, matching the 2-cycle signature directly in the visualization.

## 9. Data and cost summary

| experiment | recursive trajectories | total steps | API calls | wall time |
|---|---:|---:|---:|---:|
| O1_pub | 1350 | 54000 | 108K gen + 5K embed | 7h |
| **O2_pub** | **1350** | **54000** | **108K gen + 5K embed** | **~6h** |
| D1_pub | 450 | 9000 | 18K gen + 1K embed | ~45 min |
| **total** | **3150** | **117000** | **~245K** | **~14h** |
| total cost (gpt-4o-mini + emb) | | | | **~$110** |

Plus 2700 no_feedback baseline trajectories for O1/O2 each, 450 for D1.

## 10. Limitations this report does not resolve

Inherits all of REPORT4 and REPORT5's limitations; adds:

1. **No O3_pub** (`summarize+negate`), which would confirm the absorbing-state regime at scale. The small-N O3 run (REPORT2 §5) showed basin_score = 1.00 with SD_late ≈ 0.2 — a degenerate point attractor. At $55 per operator it's deferred.
2. **D1_pub at 20 steps vs 40 steps for O1/O2.** Dialog turns are 2× longer (user + agent) so 20 dialog steps = 40 turns, making the comparison fair in *turn count*, but dispersion statistics that depend on long-time asymptotic behavior may be partly immature at step 20. A 40-step D1 rerun (~$10) could verify.
3. **No temperature sweep yet.** All three experiments are at T=0.8. The edge-of-stability experiment (T ∈ {0.2, 0.4, 0.8, 1.1, 1.5} on a reduced grid) remains open for REPORT7.
4. **Single model.** gpt-4o-mini only. A gpt-4o replication of *just* O1_pub and O2_pub at reduced N (~5 families × 10 ICs × 3 runs × 40 steps, ~$80 per experiment) would test cross-model regime preservation and is the highest-value follow-up.
5. **Operator composition not isolated.** The 2-cycle emerges from `paraphrase ∘ paraphrase`, but an ideal decomposition would run `paraphrase_forward_then_back` (paraphrase x, then paraphrase the paraphrase back toward x) and measure whether *that* closes the loop in 1 step — isolating composition-order effects from non-idempotence.

## 11. Bottom line

Three regimes of the H1 taxonomy are now publication-scale confirmed:

1. **Contractive point-basin** (O1_pub, continue+append): 1,350 trajectories, 15 families, λ_1_late = +0.0066, SD = 1.58, basin = 0.933, period_2_score = −0.037.
2. **Stable 2-cycle** (O2_pub, paraphrase+replace): 1,350 trajectories, 15 families, **λ_1_late = +0.0012, SD = 0.97, basin = 0.979, period_2_score = +0.014 to +0.076, 95% of runs best_period = 2.**
3. **Stylistic multi-basin** (D1_pub, dialog+append): 450 trajectories, 5 families, λ_1_late = +0.0089, SD = 1.71, basin = 0.775 (lower because of multi-sub-basin structure within family), period_2_score = −0.072, 32/32 recurrence tests p=0.000.

All three converge (H1a strong), but only O2_pub recurs in the sense of periodic orbit (H1b moderate via period-2 score), and none diverges (H1c no).

The most surprising outcome is that the small-N 2-cycle claim — which I had provisionally suspected to be a three-run artifact before running the analyze_ext — is **confirmed at 1,350 runs with 95% cycle fraction**. The headline two-axis H1b `not_supported` verdict from O2_pub's main report is a *metric-choice artifact*: `late_recurrence` is a return-to-neighborhood test that a 2-cycle fails by design. The three-axis classifier that includes `period_2_score` and `best_period` restores the correct regime classification.

Remaining work for REPORT7: O3_pub (absorbing state) or the temperature sweep, whichever the user wants to prioritize.

## 12. References

Same as REPORTs 1–5. Tuci et al. 2025, arXiv:2604.19740v1. This report's primary reproduction target is REPORT2 §4 (the small-N 2-cycle claim, now at 50× scale) and REPORT3 §5.3 (the stylistic-multi-basin claim, at 10× scale for dialog).
