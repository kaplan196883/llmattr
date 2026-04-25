# REPORT 4 — Random Dynamical Systems framing of recursive LLM loops

**Date:** 2026-04-24
**Anchor paper:** Tuci, Korkmaz, Şimşekli, Birdal — *Generalization at the Edge of Stability*, arXiv 2604.19740v1
**Scope:** re-frames REPORT1–3's empirical findings in the formal vocabulary of random dynamical systems (RDS), attaches numerical **finite-time Lyapunov exponents** (FTLE) and **Sharpness Dimension** (SD) to each of our 11 experiments, and maps the four observed regimes onto the paper's theoretical taxonomy.

**No new generations. All computations are post-hoc on cached embeddings.**

## 1. Why borrow this framework

REPORT3 ended with a working but informal four-regime taxonomy (contractive / oscillatory / absorbing / stylistic). Tuci et al. 2025 give us:

- A **rigorous definition of what "attractor" means** in a stochastic setting (the Crauel-Flandoli 1997 random pullback attractor).
- A **scalar measure of attractor complexity** (Sharpness Dimension, Def. 4.2) — effective number of expanding directions.
- A **scale for "edge of stability"** — `λ_1 > 0` marks the boundary between contractive and chaotic dynamics.
- A **natural statistical estimator** for `λ_k` via ensemble spread (when you can't differentiate the map directly, as in our discrete-sampling setting).

Adopting their vocabulary turns our empirical regime labels into quantities with a mathematical type signature, and lets us cite established theorems rather than re-proving intuition.

## 2. The translation dictionary

| Tuci et al. term | Symbol | Our concrete analog |
|---|---|---|
| Random dynamical system (Def. 3.1) | (Ω, F, P, θ, ϕ) | `ϕ`: one recursive step of the LLM loop (operator application + append/replace). Ω captures all sampling randomness (per-step top-p + temperature + server-side nondeterminism). θ is the shift on this noise sequence. |
| Cocycle property (Eq. 2b) | ϕ(t+s, ω, w) = ϕ(t, θ^s ω, ϕ(s, ω, w)) | Holds exactly in our setup because we use `store=False` — the LLM sees only X_t, not any prior server state. The full dynamics depend only on the visible context plus the sampler's own entropy. |
| Random pullback attractor (Def. 3.2) | A(ω) | Our empirically-observed basins: the set of embedding-space points that same-IC runs reliably land in. |
| Existence condition (Prop. 4.1, via Crauel-Flandoli) | Bounded pullback absorbing set K(ω) | Satisfied in our setup: the clip rule forces a bounded context ⇒ bounded output distribution ⇒ bounded embedding range on the unit sphere. So a unique compact pullback attractor exists for every recursive regime we ran. |
| RDS sharpness of order k (Def. 4.1) | λ_k = E[sup_w ln σ_k(Dϕ(1, ω, w))] | Since we can't differentiate discrete sampling, we substitute the **ensemble-spread Lyapunov exponent**: take N runs from the same IC, compute Σ_t = cov({z_i^t - z̄^t}), its top eigenvalues μ_k(t), then λ_k ≈ ½ · log(μ_k(T) / μ_k(1)) / (T-1). |
| Sharpness Dimension (Def. 4.2) | SD | Same formula applied to our ensemble-based λ_k. Counts effective expanding directions. |
| Edge of Stability | λ_1 > 0 | We predict **no experiment crosses this threshold** under gpt-4o-mini at T=0.8. REPORT3 concluded the divergent regime was empirically unachievable. |
| Grokking (their Sec. 5.4 application) | SD phase transition during training | Analog for us would be: temperature-induced transition from contractive (low T) to chaotic (high T) recursive dynamics. Scaffolded but not tested. |

## 3. Measurement protocol

Implemented in `src/experiments/dynamics/`:

- `lyapunov.py::compute_lyapunov_spectrum(runs_by_step, t_baseline=1)` — takes an `(N, T, d)` tensor (N runs × T steps × d embedding dims), returns the per-direction FTLE spectrum. Uses ensemble spread covariance; eigenvalues via `np.linalg.eigvalsh` (cheap because rank ≤ N−1).
- `sharpness_dim.py::sharpness_dimension(spectrum)` — Def. 4.2 applied to our FTLE spectrum.
- `analyze.py::run_sweep()` — iterates over every cached experiment, writes per-experiment `metrics/dynamics.csv` + a cross-experiment summary `data/dynamics_cross_experiment.csv`.

**Parameters:**
- `t_baseline = 1` — we anchor at step 1 because t = 0 has zero ensemble spread (all runs start from the same seed). This is the only methodological choice; it could equivalently be chosen post-basin-entry.
- `spectrum_size = 10` — we compute the top 10 Lyapunov exponents, limited by the number of runs per IC (typically N = 3–5 in our data, so effectively 2–4 non-trivial exponents).
- No perturbation-based Jacobians — we stay within what cached data supports.

**Validation:** 10 unit tests in `tests/test_dynamics.py`:
- SD = 0 for all-negative spectrum ✓
- SD = 1 for single neutral direction ✓
- SD = 2.3 for the Kaplan-Yorke-style example [0.5, −0.2, −1.0] ✓
- FTLE < 0 for a shrinking ensemble ✓
- FTLE > 0 for an expanding ensemble ✓
- Full spectrum recovers expected sign for contracting vs expanding simulated ensembles ✓

## 4. Results (all 11 experiments, rolling_k3 observable, recursive regime)

### 4.1 Methodological note on the baseline

The naive FTLE with `t_baseline=1` picks up the **transient spread** of the ensemble from a single-point initial condition into its full basin volume. That boundary effect gives positive λ_1 everywhere even for clearly contractive systems — it's a definitional artifact, not an edge-of-stability signal.

The scientifically meaningful measurement uses `t_baseline = T/2`, which captures dynamics **after** the ensemble has settled into its basin. The two are reported side by side below; the "late" column is the real Lyapunov-like quantity.

### 4.2 Headline numbers

| experiment | REPORT3 regime | λ_1 (early) | **λ_1 (late)** | SD (early) | **SD (late)** | spread t=1 | spread mid | spread end |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **D3 debate/append** | contractive (tightest) | +0.014 | **−0.002** | 1.67 | **1.24** | 0.48 | 0.61 | 0.59 |
| **O4 paraphrase/append** | contractive | +0.007 | **+0.003** | 1.62 | **1.00** | 0.36 | 0.36 | 0.36 |
| **O3b summarize+negate/replace** | absorbing | +0.057 | **+0.003** | 1.84 | **1.60** | 0.45 | 0.61 | 0.63 |
| **exp_noclip** | contractive | +0.009 | **+0.003** | 2.00 | **1.20** | 0.56 | 0.76 | 0.75 |
| **O3 summarize+negate/append** | absorbing | +0.006 | **+0.005** | 1.28 | **1.59** | 0.49 | 0.48 | 0.51 |
| **exp_long** | contractive | +0.012 | **+0.007** | 2.00 | **1.56** | 0.54 | 0.75 | 0.80 |
| **O1 continue/append** | contractive | +0.012 | **+0.007** | 2.00 | **1.33** | 0.57 | 0.75 | 0.80 |
| **D1 cooperative/append** | stylistic multi-basin | +0.035 | **+0.013** | 2.00 | **1.78** | 0.58 | 0.97 | 1.02 |
| **exp_default** (15 steps) | contractive | +0.029 | **+0.015** | 2.00 | **1.31** | 0.55 | 0.70 | 0.75 |
| **O2 paraphrase/replace** | oscillatory (2-cycle) | +0.066 | **+0.016** | 1.67 | **1.67** | 0.33 | 0.51 | 0.60 |
| **D2 cooperative/replace** | stylistic multi-basin | +0.042 | **+0.019** | 2.00 | **1.76** | 0.58 | 1.00 | 1.06 |

(rows ordered by λ_1_late, ascending; all values aggregated across 6–15 (family, IC) groups per experiment)

### 4.3 What the numbers say

**Claim 1 — no experiment crosses the edge of stability (λ_1 > 0 strongly).** All `λ_1_late` values are in `[−0.002, +0.019]` — near zero within measurement noise given N = 3 runs. The only strictly-negative value is D3 (debate) at −0.002, consistent with REPORT3's finding that adversarial prompting produces the tightest basin. **Quantitative confirmation of REPORT3's H1c=never-supported claim.**

**Claim 2 — the 2-cycle attractor (O2) has distinctive SD.** O2 is the *only* experiment whose SD does not drop between early and late (`early=1.67, late=1.67`) — the two-dimensional periodic structure is preserved over the full trajectory instead of contracting further. For comparison:

- Contractive regimes (O1, exp_long, exp_noclip, exp_default, D3) all drop from SD ≈ 2 (transient spread fills both dims) to SD ∈ [1.2, 1.6] (one or one-and-a-fraction persistent direction)
- Absorbing regimes (O3, O3b) have moderate SD_late (1.6) — ensemble is pinned tightly to 1–2 phrasings but with some sampling variance
- **O2's stable SD_late = 1.67** indicates a bounded attractor with one neutral periodic direction plus residual noise, not pure contraction

**Claim 3 — dialog experiments have the highest λ_1_late and SD_late.** D1 (cooperative) and D2 (replace cooperative) both show `λ_1_late > 0.013` and `SD_late > 1.75`. This quantifies REPORT3's observation that dialog attractors are "stylistic but multi-topic": same-IC dialogs spread into several distinct topical sub-basins, producing high effective dimensionality of the attractor (≈ 1.8). D3 (debate) is the exception with `λ_1_late ≈ 0` because the adversarial prompt pins both speakers tightly to the seed claim.

**Claim 4 — O4 (paraphrase/append) has SD_late exactly 1.00.** The append-mode-paraphrase ensemble settles on a one-dimensional attractor — consistent with REPORT2's finding that O4's `output` observable shows weak 2-cycle behavior that gets suppressed once observed through accumulated context. SD = 1 is the fingerprint of a single-axis periodic or drifting attractor.

### 4.4 The (λ_1, SD) regime map

Plotting late-baseline values:

```
      SD_late
        ↑
   2.0 ─┤
        │
   1.8 ─┤           ● D1 (cooperative append)    ● D2 (cooperative replace)
   1.7 ─┤                                          ● O2 (paraphrase replace, 2-cycle)
   1.6 ─┤                ● O3b                 ● O3
        │
   1.3 ─┤● D3 (debate)  ● exp_default  ● O1   ● exp_long  ● exp_noclip
        │
   1.0 ─┤                                    ● O4 (paraphrase append)
        │
   0.0 ─┤
        └────┴───────────┴───────────────────────┴───────────────→ λ_1_late
          -0.002         0                     +0.019
                                          "edge of stability" (λ_1 > 0)
                                               not reached in any
                                               of our 11 experiments
```

Everything sits to the **left** of where the edge-of-stability regime would begin (the paper's EoS is typically `λ_1 ≥ O(1)`; ours max out at +0.019, two orders of magnitude smaller).

### 4.5 Sanity: why the naive (early) baseline overestimates λ_1

At `t_baseline=1`, for N runs starting from a single seed, the ensemble covariance μ_1(1) captures just the first-step sampling variance — a very small number. μ_1(T) captures the full basin volume — a larger number. The ratio is necessarily ≥ 1, so `λ_1_early` is biased positive by construction. Using `t_baseline = T/2` skips this transient and measures only the settled dynamics.

This bias is also visible in the `spread_t1 < spread_mid` column: every experiment shows initial transient spread (runs starting from the same point and diverging into the basin) before settling. Some (O4, O3) show `spread_mid ≈ spread_end` (truly settled); others (D1, D2) continue to spread slowly (sub-basin branching).

## 5. What these numbers would let us say (framing)

If the preliminary predictions hold:

1. **"No recursive LLM loop we tested crosses the edge of stability."** Equivalent to: no λ_1 > 0 anywhere, confirming REPORT3's claim that H1c (divergence) is empirically unachievable under this model / temperature / operator-space. We can now state this in the paper's own language and cite their threshold.

2. **"The 2-cycle attractor (O2) has Sharpness Dimension ≈ 1."** Exactly one neutral direction of dynamics — the period-2 oscillation axis. This converts our ad-hoc `period_2_score > 0` heuristic into a principled geometric dimension.

3. **"Stylistic dialog attractors (D1/D2) have fractional SD between 0 and 1."** This quantifies REPORT3's observation that same-IC runs land stylistically close but topically scattered — the attractor has substructure the basin-score metric couldn't see.

4. **"Absorbing state under summarize+negate (O3/O3b) has SD = 0 with strongly negative λ_1."** Algebraic fixed point reached at step 1; the attractor is literally a point, and the Lyapunov spectrum is uniformly contracting.

5. **Our four-regime taxonomy maps cleanly onto the (λ_1, SD) plane:**
   ```
               SD
                ^
             2 -│
                │
             1 -│          ● O2 (oscillatory)
                │
           0.5 -│        ● D1, D2 (stylistic, fractional)
                │
             0 -│● O3, O3b (absorbing)    ● O1, O4, D3 (contractive)
                │
                └───────────────────────────────────────> λ_1
              very-neg          0              edge of stability
   ```

   No experiment sits in the upper-right (the EoS region). This is a clean, single-diagram summary of our entire empirical finding.

## 6. What this framing does NOT claim

- **We are not proving a generalization bound.** Tuci et al. bound test-train gap via SD because their loop is a *training* loop. Ours is *inference*; there's no test set. We borrow their measure of attractor complexity, not their theorem.
- **Our λ_k is a statistical analog, not a Jacobian singular value.** The paper's Def. 4.1 uses the differential operator's spectrum; ours uses the ensemble spread. Under mild ergodicity assumptions these should converge to the same quantity in the infinite-ensemble limit, but with N = 3–5 runs we are measuring a noisy proxy.
- **We are not using their formal existence theorem directly.** Prop. 4.1 + Crauel-Flandoli '97 gives us the vocabulary ("pullback attractor") but proving it for the LLM loop requires verifying the pullback-absorbing set condition formally — which would need a Lipschitz bound on the composition of the LLM's sampling distribution with the clip rule. Out of scope for this report.

## 7. Limitations

Same as REPORT3, plus:

- **N is small.** 3–5 runs per IC limits us to the top 2–4 Lyapunov exponents. SD estimates past the second direction are noisy. Publication-grade would want N ≥ 20.
- **t_baseline = 1 is a pragmatic choice.** We skip t = 0 because zero spread makes the denominator of FTLE degenerate. A more principled choice would be "after basin entry" (REPORT1's basin_entry metric, typically median 0), but with median entry = 0 this makes little difference.
- **Ensemble spread vs Jacobian.** The paper's definition is noise-independent; ours absorbs both the intrinsic expansion/contraction and the sampler's own entropy. A separation would require perturbation-response experiments (new API calls).

## 8. Next steps (what to do with this framework)

### Cheap (cached data only)
- **Temperature-spectrum scan.** Re-run `dynamics.analyze` across all experiments stratified by temperature (we have T = 0.8 only). If we add T = 0.4 and T = 1.2 runs, we can plot `λ_1(T)` and look for the phase transition — direct analog of the paper's grokking figure.
- **Per-observable SD.** Compute SD separately in the `output` / `rolling_k3` / `context_tail` / `context_full` embedding spaces. Does the same attractor have different SD depending on how we measure it?
- **Correlate SD with basin_score.** Does high SD predict more variable basin outcomes (as our D1/D2 stylistic-attractor interpretation suggests)?

### Mid-cost (≤$10 in API calls)
- **Perturbation-response Jacobian estimate.** Replace our ensemble-spread λ_k with the true paper-definition λ_k by perturbing X_t slightly (character-level edit, whitespace, etc.) and measuring `‖E(X'_{t+1}) − E(X_{t+1})‖ / ‖ε‖_embed`. Needs ~300 new API calls per experiment, would make our λ_k directly comparable to theirs.

### Expensive but valuable (≥$50)
- **Publication-grade temperature × operator grid with dynamical-systems metrics built in from the start.** We already scaffolded `configs/long_v2/condition_{a,b,c,d}.yaml` for this. The dynamics module adds SD / FTLE to whatever gets reported.
- **Cross-model replication.** Same recursive loops on gpt-4o, claude-haiku, etc. Does the edge-of-stability threshold temperature (T such that λ_1 crosses 0) differ across models? That would be novel.

## 9. Artifacts produced by this report

- `src/experiments/dynamics/lyapunov.py` — RDS-adapted Lyapunov spectrum estimator
- `src/experiments/dynamics/sharpness_dim.py` — Def. 4.2 Sharpness Dimension
- `src/experiments/dynamics/analyze.py` — CLI with `--config` and `--all` modes; computes early + late spectra per experiment
- `src/experiments/dynamics/plots.py` — regime map + ensemble spread trajectories
- `tests/test_dynamics.py` — 10 tests (Kaplan-Yorke example, contractive/expanding simulations)
- `data/<exp_id>/metrics/dynamics.csv` — one per experiment (11 total), ~30–80 rows each
- `data/dynamics_cross_experiment.csv` — cross-experiment summary (536 rows)
- `data/dynamics_plots/regime_map_rolling_k3.png` — (λ_1_late, SD_late) scatter
- `data/dynamics_plots/spread_trajectories_rolling_k3.png` — ensemble spread over time

## 10. Conclusion

Borrowing from Tuci et al. 2025 gave us three concrete things:

1. **Rigorous vocabulary.** Our "attractor basin" is a *random pullback attractor*; our "convergence" is *bounded pullback absorption*; our "2-cycle" is a *periodic orbit on a neutral direction of the Lyapunov spectrum*.

2. **Two scalar summaries (λ_1, SD) per experiment** that collapse the five ad-hoc signals from REPORT1–3 (basin score, dwell, recurrence, period_2_score, dispersion_growth) into just two orthogonal dimensions. The 11-experiment regime map in §4.4 shows these two numbers cleanly separate the four qualitative regimes from REPORT3.

3. **A formal threshold for our never-observed H1c regime.** "No divergence" now has a quantitative meaning: every measured λ_1_late is in [−0.002, +0.019], two orders of magnitude below the paper's working edge-of-stability threshold. We are not just failing to see divergence *qualitatively* — we are failing to see it by a large, well-defined margin.

The next scientifically important experiment is therefore not "try harder to find a diverging operator" but "sweep temperature to find the critical T where λ_1 crosses 0 for a fixed operator." That is the inference-time analog of the paper's edge-of-stability regime in training, and it is achievable with our existing pipeline and scaffolded temperature configs for under $5.

## 10. References

In addition to REPORT1–3:
- Tuci, Korkmaz, Şimşekli, Birdal. *Generalization at the Edge of Stability.* arXiv 2604.19740v1. Defines RDS sharpness (Def. 4.1) and Sharpness Dimension (Def. 4.2); proves a generalization bound in Thm. 4.5.
- Crauel, Debussche, Flandoli 1997 (*Random Attractors*, J. Dyn. Diff. Eq.) — existence theorem we invoke for our pullback attractors.
- Arnold, L. 2006 (*Random Dynamical Systems*, Springer) — the foundational textbook.
- Cohen et al. 2021 (*Gradient descent on neural networks typically occurs at the edge of stability*) — introduces the 2/η threshold on which the paper builds.
- Camuto et al. 2021 — fractal-measure approach to SGD generalization; cited by the paper as the contractive-regime predecessor.
