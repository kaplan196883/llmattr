# O1 ED50 dense-dose rerun — execution plan

**Status:** scoped (config drafted, stats script implemented and validated against existing sparse data); **not yet executed**.

**Trigger:** OpenAI peer review of ARTICLE.md (`paper/openai_review.md`, 2026-04-30) flagged the headline "150-token barrier" claim as unsupported by the n=50 sparse dose-response. Highest-leverage fix in the reviewer's revision plan.

---

## What the existing sparse data actually says

Running the new hierarchical fit script on the *current* `exp_perturb_O1_dose_adversarial` data (n=50 per cell, 4 doses):

```
                dose  n  switched  rate
                 20  50    13     0.26
                 80  50    17     0.34
                200  50    27     0.54
                400  50    24     0.48
ED50 bootstrap median: 83 tokens
95% family-cluster-bootstrap CI: [18, 459]  ← spans 25×
4PL fit:  a=0.510, d=0.260, b=20.0   ← lower > upper (non-monotonic)
```

Three observations:

1. **The CI on ED50 is uninformative.** `[18, 459]` is a 25× range. The headline "~150 tokens" sits inside it but so does "20 tokens" and "very high".
2. **The dose-response never saturates above 50%.** Maximum observed rate is 54% at 200 tokens; it then *decreases* to 48% at 400 tokens. A 4PL fit reports an upper asymptote of 51%. This means ED50 may not even be a well-defined endpoint for this regime — there is a *non-switching population* that no in-distribution adversarial dose in the tested range can move.
3. **The fit produces `a > d`** — the algorithm sees a non-monotonic trend and tries to invert the curve. This is a fingerprint of insufficient data, not a problem with the fitter.

The visualization is at `data/exp_perturb_O1_dose_adversarial/reports/perturbation/ed50_curve.png`.

This already does much of the work the reviewer asked for: it makes it transparent that we *cannot* claim a precise barrier from the current data.

---

## Design of the dense rerun

### Config: `configs/perturbation/O1_ed50_dense.yaml`

| dimension | sparse pilot (current) | dense rerun (this plan) |
|---|---|---|
| doses | 4: 20, 80, 200, 400 | **8**: 20, 50, 80, 120, 160, 200, 300, 400 |
| families | 5 | 5 |
| ICs / family | 5 | **10** |
| runs / condition | 2 | **4** |
| n per cell | 50 | **200** |
| total trajectories | 250 | **1,800** |
| control runs / IC | 2 | **4** (enables control-vs-control floor) |

Doses chosen to bracket and densify around the apparent inflection (80–200 tokens) while preserving the lowest and highest endpoints from the original sweep so results are directly comparable.

### Stats script: `scripts/fit_ed50_hierarchical.py`

Computes:

1. **Per-trajectory binary switching outcomes** by pairing each perturbed trajectory with its same-(family, IC, run) control, falling back to control run_000 if the same-run pairing is missing. Mirrors the existing pipeline's definition (consistent with §4.5.8).
2. **Pooled 4-parameter logistic** dose-response fit: `p(switch) = a + (d-a)/(1+(dose/ED50)^b)`. The 4PL gives explicit asymptotes — important here because the upper asymptote `d` itself is a finding (if d < 1, there's a non-switching subpopulation worth reporting).
3. **Family-cluster-bootstrap CI** for ED50: resample the 5 prompt-family labels with replacement at each iteration, refit, record. 1,000 iterations by default.
4. **Per-dose hierarchical CI** for the rate at each individual dose, again via family-cluster-bootstrap.
5. **Optional confirmatory mixed-effects logistic GLM** via `statsmodels.BinomialBayesMixedGLM` with random intercepts for family + IC nested in family, if statsmodels is installed.
6. **Optional natural-floor estimate** (`--report-natural-floor`): control-vs-control switching rate computed by pairing each control run with every other control run from the same (family, IC). Enabled by `runs_per_condition: 4` in the new config — yields up to 12 distinct ordered pairs per (family, IC), so n_pairs ≈ 600 across the experiment. **This is the partial fix for review-Weakness #2**: the no-injection stochastic divergence floor that the existing pipeline implicitly assumes is 0%.

Outputs at `data/exp_perturb_O1_ed50_dense/reports/perturbation/`:
- `ed50_summary.csv` — point estimates, bootstrap CI, GLMM ED50, natural floor
- `ed50_per_dose_ci.csv` — per-dose rate with hierarchical CI
- `ed50_curve.png` — fitted 4PL with bootstrap band + observed points

### What the rerun will resolve

| Question | Resolved by dense rerun? |
|---|---|
| Is the upper asymptote `d` < 1? (i.e., is there a non-switching subpopulation?) | **Yes** — 200 trajectories per dose is enough to estimate `d` cleanly. If `d` < 1, the headline reframes from "barrier ≈ X tokens" to "fraction X of trajectories cross at threshold Y; fraction 1-X never cross." |
| Is the dose-response monotone in this range? | **Yes** — the dip at 400 tokens in the sparse data (54%→48%) was within Wilson noise; 200/cell collapses that uncertainty. |
| Where is the 50% threshold (if it exists)? | **Probably not** — if `d` < 1 and never reaches 0.5, ED50 is undefined. We'd report `EDp` for whatever threshold the curve actually hits. Honest answer is: *there may be no 50% point*. |
| Is the family-level variance the limiting factor on CI width? | **Yes** — with 200/cell, the within-cell Wilson half-width drops to ~7pp, but the 5-family bootstrap variance dominates. The dense rerun cuts the CI but won't make it tight. To beat that, we'd need >5 families. |

### What the rerun will *not* resolve

- **Weakness #2 (cluster-disagreement ≠ basin escape)** is only partially addressed. We get the natural floor, but K-means cluster validity is unchanged. Need separate cluster-stability study.
- **Weakness #3 (replace-mode tautology)** is not addressed — that's about the O2/O3 protocol, not O1.
- **Weakness #4 (Lemma 1 mismatch)** is theoretical, not empirical.
- **Generality**: still only `gpt-4o-mini`, still `text-embedding-3-small`. Cross-model and cross-embedder validation is a separate task.

---

## Cost & runtime estimate

**Generation:**
- 1,800 trajectories × 30 steps = 54,000 chat-completion calls
- gpt-4o-mini: ~200 input + ~120 output tokens per call
- Pricing (Apr 2026): $0.15/M input, $0.60/M output
- Cost: 54,000 × ($0.00003 + $0.00007) ≈ **$5.40**

**Embeddings:**
- 54,000 trajectory snapshots × 3 observables = 162,000 embedding calls
- text-embedding-3-small: ~50 tokens average input, $0.02/M tokens
- Cost: 162,000 × 50 × $0.00000002 ≈ **$0.16**

**Adversarial sample sourcing** (re-uses existing `exp_pub_O1_continue` outputs; no new generation): $0.

**Total OpenAI cost: ~$5.50–10.**

**Wall-clock:** at 12 parallel trajectories, ~3-4 hours generation + ~30 min embeddings + ~10 min analysis. The pilot at 250 trajectories took roughly 30 min generation, so 1,800 ≈ 7× → ~3.5 hr generation.

**Local compute:** PCA/clustering/bootstrap on 54K rows is trivial (~minutes).

---

## Execution steps

```bash
# 1. Run the experiment (generation + embeddings + analysis pipeline)
python -m src.run_pipeline --config configs/perturbation/O1_ed50_dense.yaml

# 2. The standard perturbation analyzer produces joint_pca10_clusters.csv
#    automatically. (Verify it lands at:
#    data/exp_perturb_O1_ed50_dense/reports/perturbation/joint_pca10_clusters.csv)

# 3. Fit the hierarchical model
python -m scripts.fit_ed50_hierarchical \
    --exp exp_perturb_O1_ed50_dense \
    --n-bootstrap 1000 \
    --report-natural-floor

# 4. Inspect outputs
ls data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_*
```

The script has been smoke-tested against the existing sparse data and runs in ~10 seconds for n=200 trajectories at 500 bootstrap iterations.

---

## Predicted outcomes (so we can pre-commit to interpretation)

Based on the sparse-data shape, three plausible scenarios:

**Scenario A: clean 4PL with `d` < 1.** Curve saturates around 50–60% across 200–400 tokens. We report: "≥X% of trajectories switch at any tested dose; the remaining (1-X)% appear to be in a hardened sub-basin that adversarial nudges in this token range cannot reach." This *strengthens* a more nuanced story than the original.

**Scenario B: clean 4PL with `d` ≈ 1, ED50 well-localized.** Curve crosses 50% cleanly between 80 and 200 tokens with tight CI. Original "150-token" headline is vindicated, just with proper statistics. Probably <30% likely given current data shape.

**Scenario C: still-noisy non-monotone curve.** If even at n=200 the curve doesn't behave, the conclusion is "this regime cannot be summarized by an ED50." Then we'd need to report per-dose rates only, drop the barrier-height framing, and revisit the operational definition of "barrier" (review-Weakness #6).

In all three cases the paper improves over the current state because the conclusion is grounded in data that can support whatever claim we end up making.

---

## Open questions for the author

1. **Are 5 families enough?** Family-bootstrap variance dominates the CI width. Adding 5 more families (10 total) would cut the family-bootstrap variance by roughly ~30% but doubles the experiment size and requires writing 50 new ICs. Worth it?
2. **Should we also add open-weight non-OpenAI generators in the same rerun?** The reviewer flagged cross-vendor generality (Weakness #9). Could share the same dose schedule and analysis pipeline but adds ~2× cost + dependency on a second provider.
3. **Pre-register the analysis?** Once the config + analysis is frozen and committed, that *is* a pre-registration. Worth git-tagging the commit before kicking off generation, so reviewers can verify nothing was tweaked post-hoc.

---

## Files in this scoping pass

- `configs/perturbation/O1_ed50_dense.yaml` — dense-dose config (ready to run)
- `scripts/fit_ed50_hierarchical.py` — hierarchical stats script (validated on existing data)
- `paper/ed50_rerun_plan.md` — this document
- `paper/openai_review.md` — full reviewer feedback motivating the rerun

---

## Pre-written abstract variants (to swap in once results land)

These are drafted **before** seeing the rerun result so that we
commit to interpretation conditional only on what the result actually
shows — a soft pre-registration.

### Variant A (clean ED50 around 100–150 tokens, upper asymptote → 1)

> ... O1 has a finite barrier to in-distribution adversarial text
> with **ED50 = X tokens [95% CI: Y–Z]** (n=200/cell × 8 doses,
> family-cluster-bootstrap CI; `scripts/fit_ed50_hierarchical.py`).
> Out-of-distribution perturbations show no detectable barrier
> crossing within the tested 5–400 token range, saturating near a
> 24% drift floor. ...

Action items if Variant A holds:
- Replace the current "in the 80–400-token range" hedge in the abstract with the measured ED50 + CI
- Update §5.6 prose with the same number
- Update §6.6 practical-implications table with the measured barrier
- Update Conjecture 1 / §3.1.3 to reference the empirical ED50

### Variant B (saturating curve below 1.0; non-switching subpopulation)

> ... O1 shows a graded but **non-saturating** dose-response: the
> upper asymptote of the 4PL fit is `d = X` (95% CI: Y–Z) — meaning
> a fraction `1 − d` of trajectories does *not* switch even at the
> highest tested adversarial dose (400 tokens). Among trajectories
> in the switching-eligible subpopulation, the half-switch dose is
> `EDp_d/2` tokens. Out-of-distribution perturbations show no
> detectable barrier crossing within the tested 5–400 token range. ...

Action items if Variant B holds:
- The headline finding shifts from "barrier height" to "two-population structure": one population has finite barrier, the other appears to be hardened against in-distribution perturbations in this range
- Add a new §5.6.1 reporting the upper-asymptote estimate and discussing the two-population interpretation
- Re-frame §3.1.3 Conjecture 1: "for a fraction $d$ of trajectories, the append-mode barrier is finite at scale $\tau \sim X$ tokens; the remaining $1-d$ are not crossed in tested doses"
- This is a *more interesting* result than Variant A — a structurally novel claim

### Variant C (still-noisy non-monotone curve at n=200)

> ... O1 dose-response data do not localize a 50% threshold even at
> n=200/cell × 8 doses. The 95% family-cluster-bootstrap CI on ED50
> spans [low, high] tokens; the 4PL upper asymptote is `d = X` (CI
> [Y, Z]). We report per-dose switching rates rather than a barrier
> estimate, and conclude that O1's in-distribution adversarial
> response is not summarisable by a single barrier number under the
> current switching definition. ...

Action items if Variant C holds:
- The headline retreats further: drop "barrier height" as a primary endpoint
- Operationalise a different endpoint (e.g., switching-rate slope, or AUC over the dose range)
- Tighten the operational definition of "switching" before any further claims (per review weakness #2)
- Push barrier-height work to future work; reframe paper around the four-regime taxonomy as the load-bearing contribution

### Probability assignment (rough, before the rerun lands)

Based on the existing sparse data shape (curve flattens around 50% in the 200–400-token range; 4PL fit reports `d ≈ 0.51`):

- **Variant B is most likely** (~60% probability) — the existing data already suggests an upper asymptote below 1
- **Variant A is plausible** (~20%) if the dense data reveals the sparse-data flatness was Wilson-CI noise
- **Variant C is possible** (~20%) if family-cluster heterogeneity is dominant

We will know which holds within roughly the time it takes the dense pipeline to finish + ~10 min of stats analysis.

---

## Held-out confirmatory experiment plan (Suggested Revision Plan #4)

Even after the dense rerun lands, a single experiment is not a
confirmatory replication. To meet the "frozen pre-registered
analysis on a held-out sample" bar, we propose a follow-up:

- **Same config except**: 5 *different* prompt families (drawn from
  the same library section but disjoint from the original 5)
- **Same doses** (20, 50, 80, 120, 160, 200, 300, 400)
- **Same n** (5 fams × 10 ICs × 4 runs = 200/cell, 1800 trajectories)
- **Same analysis**: `scripts/fit_ed50_hierarchical.py` with the
  current code frozen (committed before run starts)
- **Pre-registered prediction**: ED50 from the held-out experiment
  is within ±50 tokens of the dense-rerun ED50 (the prediction
  itself is set BEFORE looking at held-out data)
- **Cost / runtime**: same as the dense rerun (~$10, ~6 hours wall
  with parallel=24)

This config would be `configs/perturbation/O1_ed50_holdout.yaml` and
would use the prompt families *not* in the current dense rerun
(noise_control, narrative, technical, etc. — there are 15 families
total in the publication library, so plenty of unused ones).

We do not run this experiment in the current revision because it
depends on first seeing the dense-rerun result (which determines
whether the held-out test is even meaningful — Variant C above
would imply the held-out test should target a different endpoint).

---

## Replace-mode tautology pre-experiment plan (review weakness #3)

**Problem.** Reviewer weakness #3 flagged that O2/O3's near-100%
switching rates are partially tautological: the replace-mode
operator overwrites the trajectory's state with injected text by
construction, so "the trajectory's state changed" is true by
definition of the perturbation protocol. The Lemma 1 rewrite in
§3.1.2 already addressed this *theoretically* (G_m as separate
quantity from injected-token cost τ), but the experimental design
was not changed.

**Proposed experimental fix: split state-overwrite from context-
insertion.** Two new perturbation conditions for replace-mode regimes:

1. **`adversarial_overwrite_doseN`** (current behavior, baseline) —
   inject N tokens of adversarial text in place of the model's
   step-15 output. State is fully replaced.
2. **`adversarial_insert_doseN`** (new) — inject N tokens prepended
   to the *prompt context* before step-15 generation, but **preserve
   the model's normal step-15 generation**. Context is enriched;
   state is not overwritten.

Comparing switching rates between these two conditions tests whether
the high replace-mode switching is driven by the operator (overwrite)
or by the perturbation reaching the basin (insert).

**Predicted outcomes.**

- If switching rate(insert) ≈ switching rate(overwrite) → the
  perturbation is driving regime change, not the operator. O2/O3
  remain "barrier-low" regimes in a meaningful sense.
- If switching rate(insert) ≪ switching rate(overwrite) → the
  reviewer's tautology critique is correct; O2/O3's "no barrier"
  reading is mostly an artefact of state-overwrite.
- Most likely **intermediate**: insert switching rate substantially
  lower than overwrite, but still above append-mode O1 — replace-
  mode regimes have *some* genuine sensitivity to perturbation but
  the operator amplifies it.

**Implementation sketch.** New config
`configs/perturbation/O2_overwrite_vs_insert.yaml`:

```yaml
experiment_id: exp_perturb_O2_overwrite_vs_insert
generation_model: gpt-4o-mini
embedding_model: text-embedding-3-small
steps_per_run: 30
runs_per_condition: 2
initial_conditions_per_family: 5
loop_mode: replace          # O2 paraphrase
# operator config matches exp_pub_O2_paraphrase_replace
# ... (same as O1_dose_adversarial.yaml otherwise)
perturbation:
  enabled: true
  override_step: 15
  conditions:
    - control
    - adversarial_overwrite_dose80
    - adversarial_overwrite_dose200
    - adversarial_insert_dose80    # NEW
    - adversarial_insert_dose200   # NEW
  adversarial_source_experiment: exp_pub_O2_paraphrase_replace
```

**Pipeline change required.** `src/experiments/perturbation/runner_op.py`
currently implements only the overwrite mode. The new `adversarial_insert_doseN`
condition needs a small new code path: at injection step, prepend
the N-token adversarial text to the context fed to the next
generation, but do NOT replace the previous step's output. This is
roughly a 30-line addition to the runner.

**Cost / runtime.** 5 conditions × 5 fams × 5 ICs × 2 runs × 30 steps
= 750 trajectories per regime × 2 regimes (O2 + O3) = 1,500
trajectories total. ~$3–5 OpenAI cost, ~2 hours wall-clock at
parallel=24.

**Why we do not run this in the current revision.** This is a
new experimental design that the reviewer did not pre-register,
adds engineering work to the runner, and is not on the path to
the dense ED50 result. It is the highest-priority *next* experiment
once the dense rerun lands and §5 is updated.
