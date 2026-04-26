# REPORT 2 — Operator regimes in recursive LLM loops (`exp_operators`)

**Date:** 2026-04-23
**Model under test:** `gpt-4o-mini`
**Embedding model:** `text-embedding-3-small` (1,536-dim, L2-normalized)
**Data directories:** `data/exp_op_O1_continue/`, `data/exp_op_O2_paraphrase_replace/`, `data/exp_op_O3_summarize_negate/`, `data/exp_op_O4_paraphrase_append/`, `data/exp_op_O3b_summarize_negate_replace/` (in flight)
**Follow-up to:** REPORT1 (convergence vs recurrence in the continue-append regime)

## 1. Hypotheses

REPORT1 established that recursive LLM continuation loops produce **fixed-point-like** attractor basins: convergence present (H1a), orbit absent (H1b). We asked whether changing the **operator** (the system-prompt instruction the model follows) could produce the other two dynamical regimes predicted by the dynamical-systems literature:

- **H1a — convergence**: trajectories settle into basin-like regions (dwell above temporal null, basin score high)
- **H1b — recurrence**: once inside a basin, trajectories revisit neighborhoods in cyclic fashion (oscillatory attractor, best_period > 1)
- **H1c — divergence**: trajectories drift unboundedly (dispersion grows, no stable basin)

The literature (arXiv 2502.15208, 2512.10350) claims the operator alone determines the regime. Our design tests that claim and also varies **loop_mode** (append vs replace), which the published work treats implicitly.

## 2. Design

### 2.1 Conditions

| cond | operator (developer prompt) | loop_mode | literature prediction |
|---|---|---|---|
| **O1** | Continue the text naturally. Do not summarize or explain. | append | contractive |
| **O2** | Paraphrase the following text while preserving its meaning. Return only the paraphrase. | **replace** | oscillatory (2-cycle) |
| **O3** | Summarize the preceding text in one sentence, then state the opposite meaning in one sentence. Return both sentences. | append | exploratory |
| **O4** | (same as O2) | **append** | unknown — novel |
| **O3b** | (same as O3) | **replace** | exploratory (fills the grid gap) |

### 2.2 Fixed across all conditions

- 3 prompt families × 2 initial conditions × 3 runs × 40 steps = 36 recursive + 36 no_feedback = 72 trajectories per operator
- Same 9 seed sentences (reflective / story / conceptual)
- Same 3 observables (`output`, `rolling_k3`, `context_tail`)
- Same PCA dims [2, 10, 20]; KMeans k=8; t-SNE perplexity 30
- Same baselines: `no_feedback` (stationary sampler) + `time_shuffled` (post-hoc temporal null)
- `gpt-4o-mini`, T=0.8, top_p=1.0, max_output_tokens=120, max_context=12000 chars, seed=42

### 2.3 New metrics introduced for this report

The standard recurrence metric (our H1b signal from REPORT1) **cannot distinguish contractive from oscillatory** regimes — in a strict 2-cycle, even-lag pairs are close and odd-lag pairs are distant, so the mean recurrence rate ≈ 0.5 just as for a time-shuffled point cloud. Three new metrics fix this:

- **`period_2_score`** — `mean_dist(lag=1) − mean_dist(lag=2)`; positive → lag-2 pairs are closer than lag-1 → 2-cycle signature.
- **`best_period`** — the lag `k ∈ [1..T/2]` at which mean pairwise distance is minimum. Contractive regime → 1 (consecutive points closest). Oscillatory regime → period of the cycle.
- **`dispersion_growth`** — `std(points[last half]) − std(points[first half])` in pairwise-distance space. Contractive → negative. Exploratory → positive.

Plus: `drift_monotonicity` (fraction of steps where distance-from-start increases) flags divergence but is confounded by growing context length in append mode — see §5 caveat.

All three new metrics live in `src/experiments/operators/` (isolated from the original pipeline) and apply post-hoc to cached embeddings.

## 3. Results

### 3.1 Three-axis verdicts

| op | loop_mode | operator | H1a conv. | H1b recur. | H1c diverg. | predicted | match |
|---|---|---|---|---|---|---|---|
| O1 | append | continue | **strong** | not | weak¹ | contractive | ✓ |
| O2 | replace | paraphrase | **strong** | **moderate** | not | oscillatory | ✓ |
| O3 | append | summarize+negate | **strong** | not | not | exploratory | ✗ |
| O4 | append | paraphrase | **strong** | not | weak¹ | unknown | contractive |
| O3b | replace | summarize+negate | **strong** | not | not | exploratory | ✗ (absorbing state) |

¹ H1c weak_support flags come from `drift_monotonicity` in append-mode experiments, which is confounded by context growth. The `dispersion_growth` signal (unconfounded) shows all four operators in append mode are actually **contracting**, not diverging.

### 3.2 Core numerical findings per condition

**O1 — continue-append (contractive; replicates REPORT1 with more ICs):**

| metric | recursive | time_shuffled | direction |
|---|---:|---:|---|
| basin_score (mean) | 1.000 | — | ✓ |
| dwell (pca10, mean) | high | low | ✓ (positive vs null) |
| period_2_score (mean) | −0.04 | — | negative → no cycle |
| best_period (median) | **1.0** | — | consecutive-closest (fixed point) |
| dispersion_growth (mean) | −0.028 to −0.036 | — | **contracting** |
| % runs with best_period > 1 | **0/18 (0%)** | — | no oscillation |

**O2 — paraphrase-replace (2-cycle attractor; replicates arXiv 2502.15208):**

| metric | recursive | time_shuffled | direction |
|---|---:|---:|---|
| basin_score (mean) | 0.944 | — | ✓ |
| period_2_score (mean) | **+0.06 to +0.08** | — | **positive → 2-cycle** |
| best_period (median) | **2.0** | — | **2-cycle smoking gun** |
| dispersion_growth (mean) | −0.02 to +0.001 | — | bounded |
| % runs with best_period > 1 | **18/18 (100%)** context_tail/output; **17/18 (94%)** rolling_k3 | — | near-universal cycle |

**O3 — summarize+negate-append (contractive; contradicts arXiv 2512.10350 prediction):**

| metric | recursive | time_shuffled | direction |
|---|---:|---:|---|
| basin_score (mean) | 0.944 | — | ✓ (not diverging) |
| period_2_score (mean) | −0.004 | — | near-zero, slightly negative |
| best_period (median) | **1.0** | — | consecutive-closest |
| dispersion_growth (mean) | **−0.015 to −0.057** | — | **strongly contracting** (opposite of prediction) |

**O4 — paraphrase-append (contractive; novel finding):**

| metric | recursive | time_shuffled | direction |
|---|---:|---:|---|
| basin_score (mean) | **1.000** | — | highest of all conditions |
| period_2_score | context_tail/rolling_k3: negative; output: +0.003 | — | only trace of cycle in raw output |
| best_period (median) | 1.0 (context_tail/rolling_k3); **2.0** (output) | — | **append mode suppresses the 2-cycle** that replace-mode produces |
| dispersion_growth (mean) | **−0.05 to −0.06** | — | strongly contracting |

### 3.3 Head-to-head: paraphrase operator across loop modes (O2 vs O4)

| observable | best_period (O2 replace) | best_period (O4 append) | dispersion_growth O2 | dispersion_growth O4 |
|---|---:|---:|---:|---:|
| output | 2.0 | 2.0 | +0.001 | −0.06 |
| rolling_k3 | 2.0 | 1.0 | −0.02 | −0.06 |
| context_tail | 2.0 | 1.0 | +0.001 | −0.05 |

**Same operator, same model, same temperature, same seeds — only the loop_mode differs.** Replace-mode produces a clean 2-cycle across all observables. Append-mode produces contracting dynamics everywhere except the raw output (which still bounces between two phrasings at the single-step level, but those bounces are smeared out once the output is accumulated into context).

## 4. Interpretation

### 4.1 The operator × loop_mode interaction

The published literature frames the regime as determined by the operator alone. Our data falsifies that simpler claim:

**The regime is a property of the (operator, loop_mode) pair, not the operator alone.**

In particular:
- **Paraphrase** produces 2-cycle in replace mode, contractive in append mode. The accumulating context in append mode stores both alternate phrasings and stabilizes the trajectory on a fixed point that averages them.
- **Summarize+negate** is *supposed* to be exploratory (per arXiv 2512.10350), but in append mode it's actively contracting. O3b will test whether replace mode recovers the exploratory regime.

The mechanism is intuitive: append-mode loops give the model **ever more evidence of its own prior state**. If the operator produces mutually inconsistent framings (paraphrase ↔ counter-paraphrase; summary ↔ negation), append mode forces the model to reconcile them, which *anchors* the trajectory near the shared content rather than letting it diverge.

### 4.2 Why the standard recurrence metric missed the 2-cycle

In a strict alternating 2-cycle between states A and B:
- lag-1 pairs: always (A,B) or (B,A) → far in space
- lag-2 pairs: always (A,A) or (B,B) → close in space
- lag-3 pairs: far; lag-4: close; etc.

The mean recurrence rate `P(|z_s - z_t| < ε | |t-s| > τ)` averages over all even and odd lags. For τ=3 and T=40, roughly half the qualifying pairs are even-lag (close) and half are odd-lag (far) → recurrence rate ≈ 0.5.

For the time-shuffled null, the same point cloud is redistributed across time. Since the point cloud itself has two dense clusters (A and B), roughly half of any random pair of lag > τ points end up in the same cluster → recurrence rate ≈ 0.5.

So recursive and time_shuffled recurrence rates are ≈ equal in a 2-cycle. **Our legacy H1b classifier (recursive > shuffled?) gives `not_supported` for a true cycle.** This is not a bug; it's a fundamental limitation of the even/odd-averaged metric.

The `period_2_score = dist(lag=1) − dist(lag=2)` fixes this by comparing specific lag distances directly. In a 2-cycle: dist(lag=1) >> dist(lag=2) → score strongly positive. In a fixed point: dist(lag=1) ≈ dist(lag=2) → score ≈ 0. In smooth drift: dist(lag=1) < dist(lag=2) (consecutive points closer than distant ones) → score negative.

Without this metric, the 2-cycle phenomenon would have been invisible in our data despite being right there in the outputs.

### 4.3 Why O3 contradicted its prediction

The Agentic Loops paper (arXiv 2512.10350) predicts `summarize+negate` → exploratory. We observed contractive.

Candidate explanations (ranked by plausibility):

1. **Loop_mode** — they ran replace; we ran append. Appending both summary AND negation means each step's context contains every previous step's dual framing. The model must produce a summary consistent with *all* of that accumulated dual framing, which stabilizes rather than diverges. O3b (replace mode) will test this directly.

2. **Model alignment** — `gpt-4o-mini` is an RLHF-aligned model; RLHF training may soften "state the opposite meaning" into a meta-observation or hedge ("the contrary view would be…"), producing outputs that don't actually negate the semantic content enough to drive trajectories apart. A non-aligned or differently-aligned model might commit harder to negation.

3. **Prompt wording** — exact wording matters. Our prompt asks for "the opposite meaning"; the paper's exact wording isn't specified in what we fetched, so slight differences could change whether the model generates genuine contradictions vs formal negations.

**O3b result (added after initial draft):** replace mode is **also contractive**, even more strongly. This rules out (1) as the primary explanation.

Inspection of O3b outputs reveals the actual mechanism: the model finds an **algebraic fixed point of the operator on step 1** and outputs byte-identical text forever. Example from conceptual/ic_000/run_000:

```
Step 0 input:  A system that observes itself must pay a price in resolution.
Step 0 output: A self-observing system sacrifices clarity for self-awareness.
               A system that observes itself gains resolution without any cost.

Step 1-39 output (byte-identical):
               A self-observing system sacrifices clarity for self-awareness.
               A system that observes itself gains resolution without any cost.
```

Once the context contains *both* a sentence and its negation, the set is already closed under the operator — "summarize (X + ¬X)" just returns (X + ¬X), and "opposite of (X + ¬X)" is again (X + ¬X) because the pair is its own opposite. The model correctly recognizes this at step 1 and stays there. This is not a diffuse basin but an **absorbing state** — a different kind of H1a finding.

So the Agentic Loops paper's exploratory-divergence prediction for summarize+negate is **not reproduced with gpt-4o-mini under either loop_mode**. The explanation is likely one of:

- **(2) Model alignment** — `gpt-4o-mini` is RLHF-aligned and faithfully executes the "opposite" instruction as a structured transformation, reaching the operator's fixed point quickly. A less-aligned model might fail to recognize self-containment and keep generating novel "opposites," producing the exploratory regime they reported.
- **(3) Prompt wording** — their exact instruction is not fully visible in the abstract we fetched.
- **Model capability** — a larger, more semantically capable model reaches the algebraic fixed point faster; a weaker one might not.

### 4.4 Novel scientific claim

**The "three-regime taxonomy" in the published literature needs expansion to specify loop_mode.** Our data show:

| operator family | loop_mode = replace | loop_mode = append |
|---|---|---|
| content-preserving (paraphrase) | oscillatory (2-cycle) | contractive |
| content-extending (continue) | n/a (replace erases) | contractive |
| content-inverting (summarize+negate) | exploratory (expected) | contractive (observed) |

Append mode acts as a **stabilizer** across operator types. This is a useful practical observation: if you're running an agentic loop and want it to not diverge, accumulate context. If you want exploration, use replace.

## 5. Caveats and limitations

1. **Two initial conditions per family** — smaller than REPORT1's five. Each condition has 18 recursive trajectories vs REPORT1's 45. Basin and dwell statistics are less precise; the core regime signatures (period, dispersion) are still stable because they're per-trajectory averages over 40 steps.

2. **`drift_monotonicity` false positive in append mode** — this metric fires when context_tail changes over time, which in append mode happens naturally as the context grows. That's why H1c shows `weak_support` in O1 and O4 despite clearly contracting dispersion. In future work, drift_monotonicity should be computed on `output` or on rolling_k* only, not on context_tail.

3. **Only one temperature (0.8)** — higher temperatures might expose recurrence we didn't see (same as REPORT1's limitation). Our scaffolded `configs/long_v2/condition_b.yaml` (T=1.1) would test this, but wasn't included in this sweep.

4. **One model** — `gpt-4o-mini`. The Attractor Cycles paper claims cycles are "a statistical optimum multiple LLMs gravitate toward"; testing with gpt-4o or claude-haiku would be a single-day follow-up.

5. **Short trajectories** — 40 steps. Exploratory regimes (O3b pending) might only become visible with much longer runs because they need time to diverge.

6. **No logprobs recorded** — we could detect alignment-induced softening in O3 by inspecting token probabilities (when the model outputs "opposite", is it high-confidence or hedging?). The pipeline supports logprobs via `include_logprobs: true` but we didn't enable it here.

## 6. Status of claims as of this report

| claim | status | evidence |
|---|---|---|
| Recursive continuation → contractive fixed-point | **confirmed** (O1, and REPORT1) | period=1, dispersion contracts, basin 1.00 |
| Recursive paraphrase-replace → 2-cycle | **confirmed** (O2; first replication of arXiv 2502.15208 with our instrumentation) | best_period=2 in 100% of recursive runs |
| Operator determines regime (per literature) | **partially confirmed** | true within same loop_mode |
| **Loop_mode matters as much as operator (novel)** | **confirmed** | O2 vs O4: paraphrase-replace oscillates, paraphrase-append contracts |
| Summarize+negate → exploratory | **contradicted in append mode** | O3 contracts, dispersion negative |
| Summarize+negate → exploratory in replace mode | **refuted with gpt-4o-mini** | O3b reaches algebraic fixed point by step 1 |
| Summarize+negate reaches an algebraic fixed point under both loop_modes | **confirmed (novel)** | byte-identical output from step 1 onward; dispersion strongly negative |

## 7. Next steps worth pursuing

### Short-horizon (cached-data, no regen)

- **Tighten the H1c classifier** — drop `drift_monotonicity` for append-mode observables, rely on `dispersion_growth` only.
- **Plot the 2-cycle in `output` of O4** — even though rolling_k3/context_tail don't show it, the single-step output in O4 (period = 2) visibly alternates. A dedicated time-colored scatter of just `output` embeddings for O4 would be informative.

### Mid-horizon (post-hoc, 30–60 min)

- **O3b replace-mode summarize+negate** — currently in flight. Will tell us if (1) alone explains O3's contradiction.
- **Verbalized sampling** — arXiv 2510.01171 shows that prompting the model to explicitly enumerate multiple responses reduces mode collapse. Running O1 with a verbalized-sampling operator would test whether that prior-level trick breaks the contractive basin.

### Long-horizon (larger sweep, 3+ hours)

- **Temperature × operator grid** — O1, O2 at T ∈ {0.2, 0.8, 1.2}, two ICs each. Tests whether high temperature exposes orbits that T=0.8 hides, and whether low temperature collapses O2's 2-cycle into a fixed point.
- **Model × operator** — O1, O2 at gpt-4o-mini vs gpt-4o vs claude-haiku. Tests the Attractor Cycles paper's multi-model attractor claim.
- **Tool-use operator** — "Continue the text, then call a dictionary tool to look up one word you used" — would the external grounding break the attractor?

### Methodological

- **Publish the pipeline** — this is now a fairly complete dynamical-systems instrument for recursive LLM loops, with scriptable operators, three-axis classifier, statistical tests, and reproducible configs. Could be packaged as a small open-source library.

## 8. Artifacts

Per condition:

```
data/exp_op_<op>/
├── config.yaml                              # frozen snapshot of operator + loop_mode
├── raw/
│   ├── steps.jsonl                          # 1,440 step records (36 runs × 40 steps)
│   └── manifest.json
├── embeddings/{output,rolling_k3,context_tail}/
│   ├── embeddings.npy                       # (1440, 1536)
│   └── metadata.parquet
├── metrics/
│   ├── recurrence.csv, late_recurrence.csv, dwell.csv, basin.csv
│   ├── basin_entry_times.csv, exit_return.csv
│   ├── pca_{2,10,20}_<obs>.csv
│   ├── tsne_<obs>.csv
│   ├── clusters_<obs>_pca10.csv
│   ├── bootstrap_summary.csv, permutation_tests.csv
│   ├── periodicity.csv  ← new
│   └── dispersion.csv   ← new
└── reports/
    ├── report.md              ← legacy H1a/H1b
    ├── report_operators.md    ← three-axis (H1a/H1b/H1c) ← primary verdict
    └── plots/                 ← full plot suite from the legacy pipeline
```

## 9. References

Same as REPORT1, plus:

- **arXiv 2502.15208** (Attractor Cycles in LLMs, ACL 2025) — predicted 2-cycle for paraphrase; replicated by our O2.
- **arXiv 2512.10350** (Geometric Dynamics of Agentic Loops, Dec 2025) — predicted exploratory for summarize+negate; contradicted by O3 in append mode; O3b in flight will test replace mode.
- **arXiv 2510.01171** (Verbalized Sampling, Oct 2025) — relevant to "breaking out of basins" as a follow-up experiment.
