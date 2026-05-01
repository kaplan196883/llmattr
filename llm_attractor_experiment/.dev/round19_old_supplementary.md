## 12. Supplementary appendix

This appendix consolidates engineering documentation, full proofs,
and code-level metric definitions that were moved out of the main
body during the §6 revision (see review Writing & Structure #1, #6).
The main paper is self-contained; this appendix is for readers who
want to audit specific implementation details or full mathematical
proofs.

### 12.1 Extended Data Table 1 — Unified primary-results audit table

Extended Data Table 1 consolidates the decision-grade endpoints across
regimes, including point estimates, uncertainty, source artifacts, and
caveat flags. It is placed in Extended Data because it functions as an
audit map for reproducibility and interpretation, while the main
Results text reports the load-bearing measurements directly.


The central numerical story of this paper, in four numbers: O1 adversarial $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens; control-vs-control stochastic floor $\approx 35\%$; net switching saturates at +32 percentage points and never reaches the +50 pp threshold; persistent escape never crosses 50% in the tested 5–400 token range, with 16% as the maximum under canonical k=12 clustering at 400 tokens. The audit table below provides the supporting per-regime evidence; the rest of §5 stress-tests each of these numbers individually.

For audit, we consolidate all primary endpoints across all four
diagnostic regimes (O1, O2, O3, D1) into a single table. Each row
is a regime × endpoint; each column is the value, its uncertainty,
the source-CSV file, and any caveats from the revision. **D2 is
omitted** because it is exploratory-scale (n=25, no publication-
scale measurements) and does not satisfy the operational attractor
criteria (§3.1.3). For each endpoint we cite the §-section where
the original numbers appear and a status flag indicating whether
the endpoint has been re-validated under the revision's
leakage-aware / cluster-aware analyses.

**Sample sizes (frozen).** Operator regimes (O1, O2, O3): n =
15 prompt families × 30 ICs × 3 runs = 1,350 trajectories per
regime, 40 steps. Dialog regime D1: n = 5 dialog-suitable families
× 30 ICs × 3 runs = 450 trajectories per regime, 40 steps (see
§4.2 for the per-regime IC selection rule). Perturbation pilots
(O1/O2/O3/D1 + D2): reduced scope, n = 50 trajectories per
condition (5 fams × 5 ICs × 2 runs).

| regime | endpoint | value | 95% CI / uncertainty | source | status |
|---|---|---|---|---|---|
| O1 | basin predictability acc(k=10), stratified | **0.80** | n=1350, 5-fold CV | §5.3, `basin_pred.csv` | [!] **inflated by family leakage; group-aware = 0.73** |
| O1 | basin predictability acc(k=10), group-aware | **0.73** | family-cluster GroupKFold | §5.11 (this revision) | [OK] leakage-free |
| O1 | recurrence rate (canonical embedder) | 0.29 | bootstrap 95% CI | §5.18 | [OK] embedder-robust (§5.20: 0.30 / 0.10) |
| O1 | sharpness dimension (late) | 1.70 | trajectory-level | §12.2 | [OK] |
| O1 | Lyapunov $\lambda_1^{\mathrm{late}}$ | $\sim 0.008$ | ensemble-spread method | §4.5.5 | [OK] contractive |
| O1 adv | switching @ dose 200 (dense) | **0.620** | Wilson [0.55, 0.68], n=200 | §5.6.1 | [OK] dense rerun |
| O1 adv | switching @ dose 400 (dense) | **0.670** | Wilson [0.60, 0.73], n=200 | §5.6.1 | [OK] dense rerun |
| O1 adv | $\mathrm{ED50}_{\mathrm{raw}}$ (dense) | **36–52 tok** | 4PL=36; GLMM=41; family-cluster bootstrap median=52, 95% CI [8.5, 242] | §5.6.1 / §3.1.2 | [OK] established |
| O1 adv | upper asymptote (dense 4PL) | **$a = 0.69$** | non-switching subpopulation ~31% | §5.6.1 | [OK] |
| O1 adv | natural floor (control-vs-control, dense) | **0.347** | [0.310, 0.386], n=600 paired comparisons | §5.6.1 | [OK] established |
| O1 adv | $\mathrm{ED50}_{\mathrm{net}}$ (dense, raw − floor) | **not reached** | max net effect = +0.323 at dose 400 (50 pp threshold) | §3.1.2 | not reached in tested range |
| O1 adv | $\mathrm{ED50}_{\mathrm{persist}}$ (dense, kicked-AND-persisted) | **undefined** | max persistent escape = 16% at dose 400 | §5.15 (dense) / §3.1.2 | not reached in tested range |
| O1 neutral | switching @ dose 200 | 0.24 | Wilson [0.13, 0.38] | §5.6 / Fig 4 | [OK] sparse pilot |
| O1 neutral | switching @ dose 400 | 0.18 | Wilson [0.08, 0.32] | §5.6 / Fig 4 | [OK] sparse pilot |
| O1 lorem | switching @ dose 200 | 0.18 | Wilson [0.08, 0.32] | §5.6 / Fig 4 | [OK] sparse pilot |
| O1 attractor classification | C1–C4 strong attractor | 4/4 PASS | criteria from §3.1.3 | §3.1.3 | [OK] |
| O2 | basin predictability acc(k=10), stratified | **0.90** | n=1350, 5-fold CV | §5.3 | [!] **inflated by family leakage; group-aware = 0.60** |
| O2 | basin predictability acc(k=10), group-aware | **0.60** | family-cluster GroupKFold | §5.11 | [OK] leakage-free |
| O2 | recurrence rate | 0.875 | bootstrap | §5.18 / §5.20 | [OK] embedder-robust (0.71 / 0.78) |
| O2 | sharpness dimension (late) | 1.39 | trajectory-level | §12.2 | [OK] |
| O2 | switching adversarial (n=50, single dose) | 0.94 | Wilson [0.84, 0.98] | §5.5 | [OK] |
| O2 | switching neutral / lorem | 1.00 / 1.00 | Wilson [0.93, 1.00] each | §5.5 | [OK] |
| O2 attractor classification | C1–C4 strong attractor | 4/4 PASS | criteria from §3.1.3 | §3.1.3 | [OK] but see §5.14: basins are paraphrastic, not absorbing |
| O3 | basin predictability acc(k=10), stratified | **0.91** | n=1350, 5-fold CV | §5.3 | [!] **inflated by family leakage; group-aware = 0.63** |
| O3 | basin predictability acc(k=10), group-aware | **0.63** | family-cluster GroupKFold | §5.11 | [OK] leakage-free |
| O3 | recurrence rate | 0.92 | bootstrap | §5.18 / §5.20 | [OK] embedder-robust (0.85 / 0.86) |
| O3 | sharpness dimension (late) | 1.45 | trajectory-level | §12.2 | [OK] (note §6.6 historical "≈ 0" claim was wrong; corrected) |
| O3 | switching adversarial / neutral / lorem | 0.96 / 1.00 / 1.00 | Wilson 95% (n=50) | §5.5 | [OK] |
| O3 attractor classification | C1–C4 strong attractor | 4/4 PASS | criteria from §3.1.3 | §3.1.3 | [OK] but see §5.14: absorbing is template-formal, not semantic |
| D1 | basin predictability acc(k=10), stratified | 0.60 | n=450, 5-fold CV | §5.3 | [!] **inflated by family leakage; group-aware = 0.34** |
| D1 | basin predictability acc(k=10), group-aware | **0.34** | family-cluster GroupKFold | §5.11 | [OK] leakage-free (~chance for 11 classes is 0.09; signal is real but weak) |
| D1 | recurrence rate | 0.21 | bootstrap | §5.18 / §5.20 | [OK] embedder-robust (0.34 / 0.23) |
| D1 | sharpness dimension (late) | 1.89 | trajectory-level | §12.2 | [OK] |
| D1 | T-stability (acc range over T ∈ {0.3, 0.6, 0.8, 1.2}) | [0.57, 0.61] | reduced-scope cells, n=150 | §5.4 | [!] scope-confounded (28pp delta vs full-N) |
| D1 | switching adversarial / neutral / lorem | 0.60 / 0.76 / 0.56 | Wilson 95% (n=50) | §5.5 | [~] granularity-sensitive (§5.13: HDBSCAN drops to 0.40 on adversarial) |
| D1 attractor classification | C1–C4 strong attractor (formal); **attractor-like dialog regime in practice** | 4/4 PASS on operational criteria, BUT: group-aware basin predictability acc(k=10) = 0.34 (well below the τ_acc = 0.70 threshold under leakage-free CV); switching is granularity-sensitive (§5.13); semantic inspection (§5.14) finds dialogue-state / recent-context capture rather than a stable stylistic basin; neutral switching exceeds adversarial in the pilot. We retain D1 in the diagnostic taxonomy as an *attractor-like dialog regime* but do not claim full strong-attractor status under group-aware criteria. | §3.1.3 + §5.11 + §5.13 + §5.14 | [!] caveat-required |

**How to read the status column:**
- [OK] **validated** — endpoint survives the revision's stress tests (group-aware CV, multi-granularity, embedder ablation, attractor criteria, dense-dose rerun where applicable).
- [!] **caveat-required** — endpoint as originally reported is overstated; revised value or interpretation in cited subsection.
- *not reached in tested range* — the endpoint is well-defined but the experiment did not produce a value (dose grid does not reach the threshold).

The **two most defensible quantitative claims** in the paper are:
1. Under leakage-free GroupKFold, O1's contractive basin is
   predictable at acc(k=10) = 0.73 (down from the originally
   reported 0.80) — still well above any plausible chance baseline
   ($\sim 1/12$ for K-means $k=12$) and still the highest of the
   four regimes under the stress-test analysis.
2. The dense-dose rerun establishes a raw-switching
   $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens for O1 against
   in-distribution adversarial text, with a population
   decomposition (these are aggregate components of the observed
   rate, not latent subpopulations): 35% stochastic floor from
   control-vs-control pairs, plateau at ~67% suggesting a ~31%
   non-perturbable component, persistent-escape rate 10% (k=4) /
   16% (k=12) / 39.5% (HDBSCAN) at dose 400 (§5.15), and the
   remaining ~18% transient escape (kicked but drifted back).
   This replaces the earlier "150-token barrier" claim with a
   richer characterization that is empirically grounded; the strict
   $\mathrm{ED50}_{\mathrm{persist}}$ barrier is *not* reached in
   the tested 5–400 token range under any cluster granularity.

---

### 12.2 Extended Data Table 2 — Regime comparison at a glance

Extended Data Table 2 provides the compact cross-regime comparison of
nudge type, content operator, basin predictability, recurrence,
sharpness dimension, perturbation response, dose scale, and
temperature sensitivity. It is placed in Extended Data to preserve the
original lookup table without interrupting the narrative sequence of
the Results section.


Before walking through the experiment phases, a master comparison
of the diagnostic signatures across regimes. Each row is a regime;
each column is a diagnostic that distinguishes it from the others.
All numbers are at publication scale (Phase 2) or perturbation pilot
scope (Phase 3).

| regime | nudge | content op. $f$ | basin pred. acc(k=5→final) | recurrence | sharpness dim* | adversarial switch | dose 50% | T-stability |
|---|---|---|---|---|---|---|---|---|
| **O1** contractive | append | continue | 0.77 → 0.85 | low | 1.70 | 54% (sparse) / 62% (dense, n=200) | $\mathrm{ED50}_{\mathrm{raw}}$ ≈ 40 tok (4PL/GLMM/bootstrap), plateau ~67%, natural floor ~35% | degrades smoothly |
| **O2** oscillatory | replace | paraphrase | 0.90 → 0.91 | high (period-2) | 1.39 | 94% | n/a (saturated) | (not measured) |
| **O3** absorbing | replace | summarize+negate | 0.92 → 0.93 | trivial | 1.45 | 96% | n/a (saturated) | (not measured) |
| **D1** dialogue-state-driven multi-basin | dialog (append) | curious + helpful | n/a → 0.77 | low (per-style) | 1.89 | 60% | < 5 tokens | T-stable |
| **D2** drill-down | dialog (append) | explorer drill-down | (not measured) | (not measured) | (not measured) | 64% | (not measured) | (not measured) |

\* Sharpness dim is computed on a 2-element Lyapunov spectrum (rank ≤ N−1 = 2 for N=3 runs per IC), so values are bounded above by 2.0. Mean SD_late on `context_tail`. The *ordering* across regimes is informative, the absolute magnitudes are constrained by the rank ceiling. See §4.5.6.

\*\* D2 was run at exploratory scale (N=1 run per IC), which is below the N≥2 minimum required for ensemble-spread Lyapunov computation. D2's basin-predictability acc at k=5 is 0.20 with n=25 and 11 classes (chance ≈ 0.09), well underpowered for the canonical k=5,10,20,final probes.

Reading: the two **replace-mode** regimes (O2, O3) lock in early (acc
already ≈0.9 by step 5) and are perturbation-transparent. The
**append-mode** regimes (O1 and the dialog regimes D1/D2) admit
slower late-state determination and have measurable barrier structure.
O1 is uniquely T-sensitive; D1 is uniquely T-stable; D2 adds content
gravity beyond D1's dialogue-state basins (see §5.14).

The regime ordering — replace-mode locks in fast and capitulates
to any perturbation; append-mode locks in slowly and resists
out-of-distribution perturbation but yields to in-distribution
adversaries — runs through every diagnostic below.

![Figure 1. **Cross-experiment dynamics map.** Scatter plot of experiments in late-window $\lambda_1$ versus sharpness dimension, computed on the `rolling_k3` observable; points are experiment means and black bars are ±1 SD across trajectories. Colors denote the manually assigned regime labels. Replace-mode and dialog regimes occupy different parts of this diagnostic plane, while several append/contractive variants cluster near low $\lambda_1$. Source: `data/aggregated/dynamics_plots/regime_map_rolling_k3.png`.](data/aggregated/dynamics_plots/regime_map_rolling_k3.png)

### 12.3 Full proof of Lemma 1 (Replace-mode hitting bound)

**Lemma 1** (statement in §3.1.4).

**Proof.** Let $\mathcal{F}_s$ be the natural filtration and define
$A_k = \{\sigma_2 > t_{\mathrm{inj}} + k\}$. On $A_k$, the state
$X_{t_{\mathrm{inj}}+k}$ is reachable and outside $B_2$, so assumption
(1) gives

$$
\Pr(A_{k+1} \mid \mathcal{F}_{t_{\mathrm{inj}}+k})
\le \mathbf{1}_{A_k} (1 - q_0).
$$

Taking expectations yields $\Pr(A_{k+1}) \le (1 - q_0)\,\Pr(A_k)$,
hence $\Pr(A_m) \le (1 - q_0)^m$ by induction. This proves the
hitting bound. For terminal membership, decompose over the first
hitting time and use the Markov property together with assumption (2):

$$
\Pr(X_T \in B_2)
\ge \sum_{s = t_{\mathrm{inj}}+1}^{T}
\Pr(X_T \in B_2,\ \sigma_2 = s)
\ge r_0 \, \Pr(\sigma_2 \le T) .
$$

Combining with the hitting bound gives the displayed terminal bound.
Finally, by assumption (3) and the tower property,

$$
\mathbb{E} G_m
= \sum_{s = t_{\mathrm{inj}}}^{T-1}
\mathbb{E}\bigl[\mathbb{E}(|Y_s| \mid X_s)\bigr]
\le \kappa m . \qquad \square
$$

**Corollary 1 — full proof.** Choose $m = m_{1/2}$. Lemma 1 gives
$\Pr(X_{t_{\mathrm{inj}}+m} \in B_2) \ge \tfrac{1}{2}$ and
$\mathbb{E} G_m \le \kappa m$, so the displayed bound
$G^\star_{1/2}(B_1 \to B_2) \le \kappa\, m_{1/2}$ follows. The
explicit closed form when $0 < q_0 < 1$ and $r_0 > \tfrac{1}{2}$
follows from solving $r_0 [1 - (1-q_0)^m] \ge \tfrac{1}{2}$ for $m$
in the integers. The first-hit version sets $r_0 = 1$ and uses the
hitting bound $\Pr(\sigma_2 \le T) \ge 1 - (1-q_0)^m$ in place of
the terminal bound. $\square$

**Corollary 2 — full proof.** Take $m = 1$ in Lemma 1's terminal
bound: $\Pr(X_{t_{\mathrm{inj}}+1} \in B_2) \ge r_0 q_0 \ge
\tfrac{1}{2}$ when $q_0 r_0 \ge \tfrac{1}{2}$. Combined with
$\mathbb{E} G_1 \le \kappa$ from Lemma 1's third conclusion,
$G^\star_{1/2}(B_1 \to B_2) \le \kappa$ follows. The first-hit
version (with $r_0 = 1$) sets $q_0 \ge \tfrac{1}{2}$ as the
sufficient condition. $\square$

### 12.4 Code-snippet definitions for §4.5 metrics

Recurrence:

```python
D = pairwise_distances(z, metric="cosine")  # T × T
mask = (np.abs(np.arange(T)[:, None] - np.arange(T)[None, :]) > tau) & np.triu(np.ones((T, T)), 1).astype(bool)
recurrence = (D < epsilon)[mask].sum() / mask.sum()
```

Basin score:

```python
clusters = KMeans(n_clusters=12).fit_predict(z_pca10)
target_cluster = mode(clusters[t > 0.7 * T])
basin_score = (clusters[t > 0.7 * T] == target_cluster).mean()
```

Lyapunov spectrum (sample-driven):

```python
# z_runs : (n_runs, T, d_pca)
for t in range(T):
    centered = z_runs[:, t, :] - z_runs[:, t, :].mean(axis=0)
    sigmas = np.linalg.svd(centered, full_matrices=False, compute_uv=False)
    lambda_t = np.log(sigmas) / 2.0  # (d_pca,)
```

Sharpness dimension (Tuci-style fractional dimension on the ordered
Lyapunov spectrum; see §4.5.6):

```python
lam = np.sort(lambda_t)[::-1]
cumsum = np.cumsum(lam)
nonneg = np.where(cumsum >= 0)[0]
if lam[0] < 0:
    SD_t = 0.0
elif len(nonneg) == len(lam):
    SD_t = float(len(lam))             # full-d case
else:
    j_star = int(nonneg[-1]) + 1       # 1-indexed
    SD_t = j_star + cumsum[j_star - 1] / abs(lam[j_star])
```

Basin predictability:

```python
y = mode(clusters[t > 0.7 * T])  # late-window cluster per trajectory
acc_curve = np.zeros(T)
for k in range(T):
    X = z_pca10[:, k, :]
    clf = LogisticRegression(multi_class="auto", max_iter=1000)
    acc_curve[k] = cross_val_score(clf, X, y, cv=5).mean()
```

These are reference implementations only; the executable, test-
covered code lives at `src/analysis/` and `src/experiments/dynamics/`.

### 12.5 Perturbation injection mechanics (full)

For dialog-mode experiments, the injection happens at the user-turn
step (odd-numbered if Explorer initiates). The injection text replaces
the user turn's output verbatim. The trajectory then continues with
the agent's response to this overridden user turn, and from there
back to normal alternation.

For operator-mode experiments, the injection text replaces step k's
output entirely. The recurrence picks up from $X_{k+1} =
\mathrm{clip}(X_k \Vert Y_k^{\text{inj}})$ (append) or $X_{k+1} =
\mathrm{clip}(Y_k^{\text{inj}})$ (replace).

The adversarial-source experiment for each regime is taken from the
*publication-scale* run of the same regime (e.g., O1 perturbation
adversarial draws from `exp_pub_O1_continue`). Adversarial samples
exclude the *family* of the trajectory being perturbed but may share
its overall topic distribution.

**Insert vs overwrite modes.** The `adversarial_doseN` condition
implements *state overwrite* (the operator output for step $k$ is
replaced wholesale by the injection text). A second
condition `adversarial_insert_doseN` implements *context insertion*
(the injection text is prepended to the context for step $k$'s
generation, but the model's normal generated output is preserved
and used as $Y_k$). The runner code at `src/experiments/perturbation/runner_op.py`
dispatches between the two modes based on the substring `_insert_`
in the condition name.

### 12.6 Animation rendering pipeline (full)

The 3D animation pipeline (`trajectory_animation_3d.py`) supports
parallel rendering via `concurrent.futures.ProcessPoolExecutor`. Each
worker process imports matplotlib with the Agg backend, builds a fresh
figure for one frame, and saves a PNG. The main process stitches PNGs
into MP4 via `imageio-ffmpeg` (libx264, quality 8). With 40 workers,
75 frames at DPI 180 take ~80 seconds wall-time vs ~11 minutes
single-threaded.

### 12.7 Exact prompt templates (full)

The full prompt-family seed library (15 families × 30 ICs each = 450
unique seed sentences) lives in `configs/prompt_library_publication.yaml`
and is reproduced verbatim by every cross-model and ablation run.

**O1 — Continue (append):**

```
Continue the text naturally. Do not summarize or explain.
```

**O2 — Paraphrase + replace:**

```
Paraphrase the following text while preserving its meaning.
Return only the paraphrase.
```

**O3 — Summarize + negate (replace):**

```
Summarize the following text in one sentence, then state its
opposite. Return only the negated summary.
```

**D1 — Dialog (curious user + helpful agent), append.**
Two roles alternate; each role has its own `system_prompt`:

- *role A (curious user)*: `You are a curious person. Ask one short follow-up question, in plain language, that probes deeper into the topic.`
- *role B (helpful agent)*: `You are a thoughtful assistant. Answer briefly and clearly, in two or three sentences.`

**D2 — Dialog drill-down (explorer + expert), append.**

- *role A (explorer)*: `You are exploring this topic. Ask the next, more specific question that drills into a single concrete subtopic.`
- *role B (expert)*: `You are an expert. Answer briefly and concretely, then anchor the conversation to the most informative subtopic.`

**Perturbation conditions (injection format).** At step `override_step`
(default 15), the perturbation pipeline replaces the model's normal
step-15 generation with a fixed-length adversarial sample drawn
according to the condition:

- `control` — no injection (normal generation).
- `adversarial_doseN` — N tokens of late-step output sampled from
  another (family, IC) trajectory of the same regime, excluding the
  current trajectory's own family. Source experiment is named in
  `perturbation.adversarial_source_experiment`.
- `adversarial_insert_doseN` — N tokens prepended to the context for
  one generation; model's normal output is preserved (§12.5).
- `neutral_doseN` — N tokens of in-distribution but topically
  unrelated continuation drawn from a Wikipedia corpus.
- `lorem_doseN` — N tokens of out-of-distribution Lorem-ipsum text.

The injection text is appended to the running context for `append`-mode
operators and replaces the generated step entirely for `replace`-mode
operators (per §9.2 / §12.5).

### 12.8 Model versioning (full table)

OpenAI model aliases can update silently; this is the exact set used
for the publication-scale experiments:

| role | model alias | underlying snapshot |
|---|---|---|
| primary generator | `gpt-4o-mini` | `gpt-4o-mini-2024-07-18` (resolved 2025–2026 across all publication runs; OpenAI did not retire this snapshot during the experiment window) |
| secondary generator (cross-model) | `gpt-4.1-nano` | `gpt-4.1-nano-2025-04-14` |
| canonical embedder | `text-embedding-3-small` | (single immutable model; no snapshot suffix exists) |
| ablation embedder #1 | `text-embedding-3-large` | (same) |
| ablation embedder #2 | `all-mpnet-base-v2` (sentence-transformers) | hugging-face `sentence-transformers/all-mpnet-base-v2` |

For the cross-vendor pilot configs (under `configs/cross_model/text01/`)
the secondary generator is MiniMax `MiniMax-Text-01` via the official
MiniMax chat-completions API.

### 12.9 Phase-0 pilot validation

The earliest pilot runs validated the pipeline end-to-end on small-N
(2–5 trajectories per regime) configurations covering the major
operator and dialog architectures. These pilots established that:
(a) the embedding pipeline produces stable PCA-2 / PCA-10 / t-SNE
projections, (b) K-means at $k = 12$ recovers visually-distinct
clusters in late-window points, and (c) recurrence and basin-score
diagnostics produce numerically sensible values. They are not
load-bearing for any §4.13 decision-grade endpoint and are summarised
here for completeness only; raw outputs at `data/exp_op_*_pilot/` and
`data/exp_dialog_*_pilot/`.

### 12.10 Phase-1 small-N taxonomy

The phase-1 small-N runs ($n \approx 50$ trajectories per cell)
identified the three operator regimes (O1 contractive append; O2
oscillatory paraphrase/replace; O3 absorbing summarize+negate/replace)
and the two dialog regimes (D1 dialogue-state-driven multi-basin; D2 drill-down)
that became the diagnostic taxonomy at publication scale. These
small-N runs are not load-bearing — every regime claim in the main
body is now grounded in publication-scale or perturbation-pilot
data. Configurations and outputs at `configs/operators/`,
`configs/dialog/`, and `data/exp_*_pilot/`. The boundary cases (O3b
summarize+negate at append; O4 paraphrase+append; D3 debate dialog)
are documented as pilot variants but do not satisfy the operational
attractor criteria of §3.1.3 at publication scale.

### 12.11 Perturbation visualization toolkit (full implementation)

For perturbation experiments we additionally compute:

#### Effective potential

```
ρ̂(x) = Gaussian-smoothed kernel density on PCA-2 grid
V(x) = −log(ρ̂(x) + ε),  ε = 0.1·min{ρ̂ : ρ̂ > 0}
V is shifted so V_min = 0 and capped at v_cap (default 8.0)
```

#### Geodesic skeleton

We find local minima of V via 8-connected `maximum_filter` on −V,
keeping the top n basin centers. For each pair of basin centers
(i, j) we compute the Dijkstra shortest path on the V grid
(8-connected, edge weight = V at endpoint). The maximum V along
the path is the **barrier height V*(i, j)**.

#### Volumetric iso-density rendering

For 3D animations we extract iso-density shells at five density
fractions (4%, 10%, 20%, 35%, 55% of max ρ) using
`scipy.ndimage.gaussian_filter` smoothing and
`skimage.measure.marching_cubes`. Each shell is rendered as a
transparent `Poly3DCollection` in `matplotlib`'s
`mpl_toolkits.mplot3d`, with colors from the `plasma` colormap and
per-shell alpha from 0.05 (outermost) to 0.27 (innermost).

#### Parallel rendering

Animations of 50 trajectories with 75 frames at DPI 180 are
rendered via `concurrent.futures.ProcessPoolExecutor` with 40
workers, each worker creating a fresh figure for one frame. Frames
are stitched into MP4 via `imageio-ffmpeg` (libx264 codec, quality
8). Wall-time per animation: ~80s vs ~11 min single-threaded.

### 12.12 Reproducibility commands and repository tree (full)

#### Pipeline commands

```bash
# Generate (only for new experiments)
python -m src.experiments.dialog.main run    --config <cfg.yaml>
python -m src.experiments.operators.main run --config <cfg.yaml>
python -m src.experiments.perturbation.main run --config <cfg.yaml>

# Derive (works on existing steps.jsonl)
python -m src.experiments.<runner>.main embed --config <cfg.yaml>
python -m src.experiments.<runner>.main analyze --config <cfg.yaml>
python -m src.experiments.dynamics.basin_predictability --config <cfg.yaml>
python -m src.experiments.dynamics.regime_plots --data-dir data
python -m src.experiments.perturbation.flow_skeleton --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.geodesic_skeleton --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.bulk_plots --experiment <exp_id> --override-step <k> [--is-dialog]
python -m src.experiments.perturbation.rg_dendrogram --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.trajectory_animation_3d \
       --experiment <exp_id> --condition <c> --parallel 40

# Aggregate
python -m scripts.aggregate_perturbation_cross_regime
python -m scripts.aggregate_dose_response
python -m scripts.aggregate_basin_hardening
python -m scripts.aggregate_basin_predictability
python -m scripts.aggregate_t_sweep
python -m scripts.aggregate_o1_d1_t_sensitivity
python -m scripts.aggregate_perturbation_geometric_barriers

# Audit / catalog
python -m scripts.build_coverage          # rebuild COVERAGE.csv (37 × 60 matrix)
python -m scripts.publication_summary     # rebuild RESULTS.md (verify §5 cells against data)
```

#### Repository layout

```
llm_attractor_experiment/
├── README.md, requirements.txt, ARTICLE.md
├── EVIDENCE.md             claim-to-evidence map (every ARTICLE claim
│                           ↔ data file ↔ source code function ↔ CLI)
├── COVERAGE.csv            37 × 60 artifact-presence matrix
├── RESULTS.md              §5 numeric-claim verification (103/103 ✓)
├── docs/
│   ├── DATA_INDEX.md
│   └── reports/REPORT1.md … REPORT6.md
├── src/
│   ├── analysis/      basin, recurrence, dwell, PCA, t-SNE, distances, …
│   ├── api/           OpenAI client + embedder + generator
│   ├── core/          trajectory runner, observables, baselines, context
│   ├── experiments/
│   │   ├── dialog/    D1/D2/D3 alternating-role runner
│   │   ├── operators/ O1–O4 single-role recursive operators
│   │   ├── dynamics/  10 post-hoc CLI analysis modules
│   │   └── perturbation/ 14 modules: runner, analyze, corpora, plot+animation
│   ├── reports/       narrative report writer
│   └── utils/         io, logging, seeds, text helpers
├── scripts/           build_publication_configs + 6 aggregators
├── configs/           dialog/ + operators/ + perturbation/ + archive/
├── tests/             99 pytest tests
└── data/              37 experiment dirs + aggregated/ outputs
```

### Engineering memory-policy correspondences (illustrative)

These pseudo-YAML blocks illustrate how the formal nudges of §3.1
correspond to implementable agent memory policies. They are *not*
experimental conditions of this paper; they are engineering
correspondences provided for readers adapting the framework to their
own systems.

**Append-mode (full transcript):**

```yaml
memory_policy:
  mode: append
  clip: tail
  max_context_chars: 12000
  include:
    - user_goal
    - recent_tool_output
    - recent_model_outputs
```

**Replace-mode (summary as state):**

```yaml
memory_policy:
  mode: replace
  state_source: generated_summary
  preserve_raw_history: false
```

**Hybrid (pinned + rolling + provenance-preserving):**

```yaml
memory_policy:
  mode: hybrid
  rolling_window:
    last_turns: 8
  pinned:
    - original_user_goal
    - acceptance_tests
    - security_policy
  summaries:
    older_history: extractive
    untrusted_tool_output: preserve_provenance
```

The risk profile of each policy is qualitatively distinct (§3.1 table;
§5.16 overwrite-vs-insert; §6.2 "summary as effective next state").

### 12.13 Operational attractor criteria — audit table

The C1–C4 criteria of §3.1.3 are operationally auditable. The
table below records the actual numeric values backing each
PASS/FAIL verdict. Tabulated below from publication-scale runs
(`exp_pub_O1_continue` etc.; bootstrap statistics from
`metrics/bootstrap_summary.csv`; basin-predictability from §5.11;
embedder-robustness from §5.20). Empty cells are marked "n.t." (not
directly tabulated in published artefacts at this resolution; would
need a small new aggregation script to compute).

#### C1 — Late-window basin predictability $A^{\mathrm{final}}$

Threshold for PASS: $A_r^{\mathrm{final}} \ge 0.70$.

| regime | acc(k=10) stratified 5-fold | acc(k=10) GroupKFold-by-family | leakage Δ | C1 PASS? |
|---|---:|---:|---:|---|
| O1 | 0.80 | 0.73 | 0.07 | PASS (both ≥ 0.70) |
| O2 | 0.90 | 0.60 | 0.30 | PASS (stratified); FAIL (group-aware) |
| O3 | 0.91 | 0.63 | 0.28 | PASS (stratified); FAIL (group-aware) |
| D1 | 0.60 | 0.34 | 0.27 | FAIL (both below 0.70) |
| D2 | 0.20 (n=25) | n.t. | n.t. | FAIL (exploratory scope) |

Source: §5.11, `data/aggregated/group_aware_basin_pred.csv`.

#### C2 — Temporal recurrence vs null

Threshold for PASS: $z = (R_r - \mu_R^{\text{null}}) / \sigma_R^{\text{null}} \ge 2$ AND Cohen's $d \ge 0.5$, OR equivalent for dwell.

Recurrence on `context_tail` PCA-10 (PASS via raw recurrence > null requires recursive > baseline):

| regime | recursive R | no_feedback μ | time_shuffled μ | recursive vs no_feedback | recursive vs time_shuffled |
|---|---:|---:|---:|---|---|
| O1 | 0.289 | 0.902 | 0.377 | recursive < null | recursive < null |
| O2 | 0.875 | 0.938 | 0.886 | recursive < null | recursive ≈ null |
| O3 | 0.924 | 0.706 | 0.932 | recursive > null (z >> 2) | recursive ≈ null |
| D1 | 0.210 | n.t. (not run) | 0.315 | n.t. | recursive < null |

(Source: `metrics/bootstrap_summary.csv` per regime, n=1350 / 450.)

**Reading**: Only O3 has *recurrence above the no_feedback null*.
O1, O2, D1 have recurrence *below* the no_feedback baseline (the
no_feedback baseline produces highly similar outputs from
independent regenerations against the same prompt, so it has high
self-similarity by construction). The C2 criterion as stated in
§3.1.3 — "max(z_R, z_D) ≥ 2 AND d ≥ 0.5" — therefore PASSES on
recurrence only for O3. For O1/O2/D1 it must pass via *dwell*
(time spent in single late-window basin) rather than raw recurrence.
Dwell statistics are produced by the pipeline (`dwell.csv` per
experiment) but per-regime null comparisons are not directly
tabulated; the §12.2 master table reports the late-window basin
dwell of >0.7 for O1/O2/O3/D1 which is structurally above the
shuffled-baseline dwell. **Honest assessment**: C2 PASSES on
recurrence-vs-null only for O3 in the strict sense; O1/O2/D1's
PASS rests on dwell-vs-null which is observed but not formally
$z \ge 2$-tested in the published bootstrap output. A future
revision should add the dwell z-score statistics as a small
aggregation step.

#### C3 — Projection / embedder robustness

Threshold for PASS: recurrence-bin agreement ($b_e(r)$) across
canonical + ≥1 of 2 alternative embedders (`text-embedding-3-large`,
`all-mpnet-base-v2`).

| regime | recurrence (canonical 3-small) | recurrence (3-large) | recurrence (mpnet) | bin agreement | C3 PASS? |
|---|---:|---:|---:|---|---|
| O1 | 0.289 (low) | 0.304 (low) | 0.096 (low) | 3/3 low | PASS |
| O2 | 0.875 (high) | 0.711 (high) | 0.783 (high) | 3/3 high | PASS |
| O3 | 0.924 (high) | 0.850 (high) | 0.862 (high) | 3/3 high | PASS |
| D1 | 0.210 (low) | 0.337 (low) | 0.226 (low) | 3/3 low | PASS |
| D2 | 0.296 (low) | 0.176 (low) | 0.073 (low) | 3/3 low | PASS but small-N |

Source: §5.20 embedding ablation table.

#### C4 — Re-entry / contraction / collapse

Threshold for PASS: any of (a) $\lambda_1^{\text{late}} \le 0.015$,
(b) `best_period = 2` AND `period_2_score > 0`, (c) $R_r \ge 0.90$
AND $SD_r \le 1.50$, (d) exit-return above null.

| regime | $\lambda_1^{\text{late}}$ | best_period | $R_r$ | $SD_r$ | C4 PASS via |
|---|---:|---|---:|---:|---|
| O1 | ~0.008 | n.t. | 0.29 | 1.70 | (a) λ₁ ≤ 0.015 |
| O2 | n.t. | 2 (period_2_score > 0) | 0.875 | 1.39 | (b) period-2 |
| O3 | n.t. | n.t. | 0.924 | 1.45 | (c) R ≥ 0.90 AND SD ≤ 1.50 |
| D1 | ~0.011 | n.t. | 0.21 | 1.89 | (a) λ₁ ≤ 0.015 |
| D2 | n.t. | n.t. | n.t. | n.t. | n.t. (insufficient data) |

Source: §12.2 master table, §5.18 / §5.19.

#### Aggregate verdict

| regime | C1 (group-aware) | C2 (z-tested only for O3) | C3 | C4 | Strong attractor (all 4)? | Attractor-like (≥3/4)? |
|---|---|---|---|---|---|---|
| **O1** | PASS | PASS via dwell (not z-tested), recurrence z fails | PASS | PASS | **borderline** (3/4 z-tested PASS) | **YES** |
| **O2** | FAIL group-aware | PASS via dwell (recurrence z fails) | PASS | PASS | **borderline** (3/4 z-tested PASS) | **YES** |
| **O3** | FAIL group-aware | PASS (recurrence z >> 2) | PASS | PASS | **borderline** (3/4 z-tested PASS) | **YES** |
| **D1** | FAIL group-aware (acc 0.34) | PASS via dwell only | PASS | PASS | **NO** (group-aware C1 fails) | **borderline** (3/4 PASS structural) |
| **D2** | FAIL exploratory | n.t. | PASS small-N | n.t. | NO | NO |

**Honest reading.** Under the strict criteria (group-aware C1,
z-tested C2 on raw recurrence), no regime achieves a clean 4/4
strong-attractor classification — every regime relies on at least
one criterion passing via dwell or via the stratified rather than
group-aware version. The taxonomy survives at the *attractor-like*
(≥ 3/4) level for O1/O2/O3 and is borderline for D1. A future
revision should produce dwell-vs-null z-scores as a small new
aggregation script; the underlying `dwell.csv` data are already
produced by the pipeline.

The §12.1 primary-results table reflects this: "C1–C4 strong
attractor" passes are reported but always paired with the more
informative group-aware basin-predictability and stress-test
caveats. The §3.1.3 label rule (4/4 strong, ≥3/4
attractor-like, <3/4 not attractor) gives O1/O2/O3 strong-
attractor status under the *non*-stress-tested C1 (without z-testing C2), which is the weaker reading; under the strict group-aware C1 + z-tested C2 reading shown in the aggregate-verdict table above, no regime currently achieves "strong attractor" — all four are downgraded to attractor-like or borderline at best.

### 12.14 Geometric V* and RG dendrogram per-regime tables

#### Geodesic V* skeleton table

Per-condition mean barrier height $V^\star$ across the 6 inter-basin
geodesics (`V_star_mean` column in
`data/exp_perturb_*_pilot/reports/perturbation/geodesic_barriers_summary.csv`):

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 4.4 | 2.3 | 2.6 | 2.2 |
| O2 | 2.8 | 3.5 | **5.6** | 1.6 |
| O3 | 1.1 | 5.2 | **7.0** | 2.2 |
| D1 | 1.3 | 1.1 | 0.8 | 0.4 |

The $V_{\max} \approx 8.0$ ceiling appears when a geodesic crosses
a region of near-zero density. Per-geodesic raw values are written
alongside the figures to `geodesic_barriers_pca.csv`. Reading:

- **O2/O3 lorem** has $V^\star \approx 5.6 / 7.0$ — the highest
  barriers in the matrix. Those barriers separate *control* from a
  *new* basin that lorem injection creates far from any pre-
  perturbation density mass; geodesics between the original and
  lorem-induced basins traverse low-density plateaus where
  $\rho \approx \varepsilon$ (V near the ceiling). Switch rates are
  ~100% because the perturbation places the trajectory *into* the
  new basin — the perturbed run does not have to climb the barrier;
  it lands on the far side.
- **O1 adversarial** has $V^\star \approx 2.2$ — basins remain
  distinct but the kick occasionally clears the ridge → consistent
  with 62% raw switching at dose 200 (dense rerun, §5.6.1; net of
  natural floor ~27 pp; note that persistent escape under any
  cluster granularity is much lower per §5.15, so the geometric
  ridge-crossing reading should be interpreted as raw-switching-
  consistent, not persistent-escape-validating).
- **D1 adversarial** has $V^\star \approx 0.4$ — content-independent
  basins, geometric barrier is small.

#### Hierarchical RG dendrogram cloud-expansion table

Per-condition maximum Ward-linkage merge distance across $k=48$
fine-cluster centroids:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 2.38 | 2.27 | 2.37 | 2.06 |
| O2 | 2.31 | 2.32 | **3.64** | 1.90 |
| O3 | 2.16 | 2.39 | **3.25** | 1.85 |
| D1 | 1.79 | 1.79 | 1.79 | 1.80 |

Three patterns: (1) **D1 is invariant** at 1.79–1.80 across all
four conditions; (2) **O2/O3 lorem expands the cloud** to merge
distance 3.64/3.25 (vs control 2.31/2.16) — the largest signal in
the matrix, consistent with replace-mode lorem producing a *new*
basin far from the original attractor; (3) **O1 adversarial mildly
compresses** (2.06 vs 2.38) — in-distribution adversarial text
pulls into a tighter region.

### 12.15 How to instrument your own recursive system

The framework of this paper is portable. Engineers wishing to apply the three-endpoint decomposition (§3.1.2) to their own recursive systems — coding agents, multi-turn assistants, agentic tool loops, summarization pipelines, recursive RAG systems, or any application with a generator and a context-update rule — can follow this recipe. Each step deliberately preserves the rigor of the protocol while making it implementable without reproducing this paper's embedding pipeline.

#### Recipe

1. **Define the state-update rule explicitly.** Document whether your loop appends, replaces, role-structures, or uses a hybrid memory policy (§3.1, §13 engineering correspondences). Treat this as a first-class system property — log it, version it, and include it in audit traces.

2. **Choose observables.** Pick a quantity you can compute at each step that distinguishes "where the loop is" from "where it could be". Embedding clusters (§4.4, §4.5) work for text-trajectory analysis. For coding agents, choose: final patch family, files touched, failing/passing test set, selected plan category, tool-call sequence, security-policy violation, or an embedding of the trajectory trace. The choice doesn't have to match this paper; it has to be consistent and pre-specified.

3. **Run paired controls.** For each task, run the same loop multiple times *without* perturbation. The disagreement rate between paired controls is your stochastic floor (§4.7, §5.11). Report it; this is what every later "switching rate" must be calibrated against.

4. **Inject matched perturbations.** Run treatment cases with controlled perturbations. At minimum, include three content classes (this paper found them informative): *neutral* (in-distribution but topic-orthogonal), *lorem-style* (out-of-distribution gibberish), and *adversarial* (in-distribution, content-targeted, drawn from another trajectory of the same regime — see §4.7 corpora). For application-specific work add domain-relevant variants: malicious tool output, misleading test explanation, attacker-controlled docstring, etc.

5. **Measure raw, net, and persistent endpoints (Algorithm 1, §4.5.11).** Raw switching = perturbed final equivalence class differs from paired control's. Net switching = raw minus the stochastic floor. Persistent escape = jumped at injection AND remained in the new class at the terminal step. Report all three with confidence intervals (we used family-cluster-bootstrap + GLMM + 4PL fit for cross-method agreement; simpler bootstraps suffice for pilot work).

6. **Report a dose-response curve.** Vary perturbation length / strength systematically and fit a logistic. Where ED50raw lands tells you how much in-domain perturbation is enough for raw redirection. Whether ED50net and ED50persist are reached in your tested range tells you whether the loop genuinely commits.

7. **Separate overwrite-style interventions from genuine perturbation response.** If your update rule replaces state with a generated summary, run an *insert-mode* probe (§5.17): inject the same content as a non-replacing addition to context. The gap between overwrite and insert is the operator-overwrite contribution. If it dominates, your "fragility" measurement is partly a statement about your memory policy, not your generator.

8. **Pre-register the equivalence rule and the analysis plan.** Persistence and net-effect estimates are sensitive to clustering granularity (§5.12, §5.13) and to the choice of equivalence rule. Pre-registering protects the report from inadvertent post-hoc tuning of the threshold.

#### Reporting template

A minimum reporting template for any application of this framework:

```text
Loop:        <append / replace / dialog / hybrid>
Generator:   <model + version>
Observable:  <embedding-cluster / patch-family / pass-fail / ...>
Equivalence: <K-means k=N / cluster-pair-Hamming / files-touched-Jaccard / ...>
n_seeds:     <N per condition>

Stochastic floor (control-vs-control divergence): rate ± CI
Raw switching at dose τ: rate ± CI
Net switching at dose τ:    raw − floor ± CI
Persistent escape at dose τ: rate ± CI
ED50_raw:     <tokens / cycles / interventions>
ED50_net:     <if reached>
ED50_persist: <if reached>

Overwrite-vs-insert gap (replace-mode systems only): pp ± CI
```

This template is the academic-paper equivalent of the eval-loop pseudocode that practitioners may already be reaching for. Reporting all three endpoints separately, with the stochastic floor calibration and the overwrite-vs-insert separation, is the minimum disclosure standard implied by §3.1.2, §5.11, §5.15, and §5.17.

### 12.16 Box 1 — Minimum reporting standard for recursive-loop perturbation studies

This Box collects the reporting standard described in §6.5 in checklist form. It is intended as a minimum disclosure template for studies that use perturbations to evaluate recursive LLM loops, agent scaffolds, memory policies, or related generator–nudge systems.

1. **Generator and version.** Report the generator model, provider, resolved snapshot or version if available, decoding parameters, output-token limits, and any model changes across conditions.

2. **Nudge / memory policy.** Report the context-update rule explicitly: append, replace, dialog, rolling window, generated-summary replacement, pinned-memory hybrid, or another specified mechanism.

3. **Observable and equivalence rule.** Define what counts as the trajectory state for evaluation and how equivalence classes are assigned: embedding cluster, patch family, files touched, tests passed, tool-call sequence, policy violation, factual claim set, or another pre-specified observable.

4. **Control-vs-control stochastic floor.** Run paired unperturbed controls and report the natural disagreement rate with confidence intervals; raw perturbation effects should not be interpreted without this floor.

5. **Raw, net, and persistent rates.** Report raw switching, net switching after subtracting the stochastic floor, and persistent escape, where persistent escape requires an injection-time jump that remains through the terminal measurement.

6. **Dose-response curve and ED50 endpoint type.** Vary perturbation strength or length systematically and state which endpoint the fitted ED50 refers to: $\mathrm{ED50}_{\mathrm{raw}}$, $\mathrm{ED50}_{\mathrm{net}}$, or $\mathrm{ED50}_{\mathrm{persist}}$.

7. **Overwrite-vs-insert gap for replace-style systems.** For replace, summary, scratchpad, or "current state" memory policies, compare overwrite-mode perturbations with insert-mode perturbations and report the overwrite-minus-insert gap.

8. **Scope caveat.** State what was not tested: other generators, longer doses, other languages, production scaffolds, tool environments, safety prompts, jailbreak attacks, human users, factuality-grounded tasks, or domain-specific agent benchmarks.

### 12.17 Pointers to remaining supplementary material

The following content remains in the main body and is a candidate
for further extraction in a future revision cycle:

- §5.9 Cross-experiment aggregation (pipeline-script documentation).
- §4.8 Static visualization battery, §4.9 Flow-field computation,
  §4.11 End-to-end pipeline diagram (engineering deep dives).
- §3.1.5 effective-context-share formulation and geometric refinement (theory deep details).
- §5.4 Temperature-sweep extended tables, §5.18 cross-metric
  correlation full table, §5.20 embedding-ablation full table,
  §5.21 cross-model audit details (secondary-analysis deep dives).

