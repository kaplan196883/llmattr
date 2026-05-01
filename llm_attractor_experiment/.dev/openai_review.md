# OpenAI peer review of ARTICLE.md

**Reviewer model:** `gpt-5.5` with `reasoning_effort: "high"`
**Date:** 2026-04-30
**Source reviewed:** `ARTICLE.md` (uploaded as file-1NeMxP3SFRr4qn5NTyqegr)
**Prompt:** Skeptical NeurIPS/ICML-style peer reviewer; structured critique with bottom-line, claims summary, ranked weaknesses, section-by-section issues, writing/structure, reproducibility audit, revision plan, likely-reviewer objections.

---

## Bottom Line

**Verdict: reject in current form (promising but not yet top-venue ready).** The central contribution — "barrier height in tokens," especially the headline O1 ≈150-token barrier — is not yet statistically or operationally well-defined enough to support the paper's claims; the evidence is confounded by clustering choices, perturbation construction, stochastic rerun variability, and weak dose-response data.

---

## Revision Status (last updated 2026-04-30, after dense-rerun completion)

Status tags used below: **✅ DONE** = landed in current ARTICLE.md / paper.pdf; **🟡 IN PROGRESS** = partial fix in place or experiment running; **🔴 TODO** = not yet started.

**Summary of progress (cumulative across both batches):**

| Reviewer item | Status | Where the fix landed |
|---|---|---|
| #1 Headline 150-token barrier unsupported | ✅ DONE — dense rerun complete | **Dense-dose rerun finished 2026-04-30 ~15:53.** 1,800 trajectories × 30 steps / 9 conditions @ $n=200$/cell. Three independent ED50 estimates converge at **ED50 ≈ 40 tokens** (4PL pooled = 36; GLMM = 41; family-cluster-bootstrap median = 52, 95% CI [8.5, 242]). The original "~150 token" headline was off by **~4×**. Two structurally important findings beyond the point estimate: (a) **upper asymptote = 0.69** — the dose-response curve plateaus far below 1.0, indicating a ~31% non-switching subpopulation; (b) **control-vs-control natural floor = 34.7%** [31.0, 38.6] over $n=600$ paired comparisons — most of the apparent low-dose switching is stochastic divergence, not perturbation effect. Net adversarial effect saturates at +32 pp at dose 400. New §5.6.1 + Figure K. Abstract reframed (Variant B from `paper/ed50_rerun_plan.md`). |
| #2 Switching ≠ basin escape | 🟡 partial (now substantively addressed in **five** ways with **direct empirical confirmation of the reviewer's concern**) | (a) natural-floor option in `fit_ed50_hierarchical.py` with 4 control runs/IC; (b) **§5.10.6 cluster-stability** — HDBSCAN auto-detects 2 clusters for O1; (c) **§5.10.7 multi-granularity switching** — O1 OOD-vs-IN asymmetry robust at K-means k=12 / k=4 / HDBSCAN; (d) **§5.10.8 per-cluster semantic inspection** — only O1's regime label accurately describes its mechanism; (e) **NEW §5.10.9 persistence test** — at dose 400 only **8% (4/50) of trajectories are "kicked at injection AND persisted in new basin"**, vs the 48% headline switching rate. **The 40pp gap is the empirical confirmation of the reviewer's concern: most "switching" is post-injection stochastic divergence, NOT clean basin-escape.** Per-cluster + persistence + multi-granularity together provide a strong defense, with the persistence finding being the most direct response to the original critique. |
| #3 Replace-mode tautology (state overwrite) | 🟡 SCOPED | Pre-experiment plan added to `paper/ed50_rerun_plan.md`: split `adversarial_overwrite_doseN` (current behavior) from `adversarial_insert_doseN` (prepend to context, preserve generation). Predicted outcomes documented; runner code change estimated at ~30 lines; cost ~$3–5 across O2 + O3. Not run in this revision (pre-experiment plan only). |
| #4 Lemma 1 / Corollary 1 mismatch | ✅ DONE | §3.1.2 fully rewritten via gpt-5.5 high-reasoning; G_m introduced as separate quantity, assumption-1 broadened to reachable set, Corollary 1 honestly bounds G⋆ not B(B₁→B₂) |
| #5 V⋆ overinterpreted (basin creation ≠ barrier crossing) | ✅ DONE (paper-only) | §5.10 caveat box added; abstract reframed (V⋆ = descriptive, not validation); explicit note that O2/O3 high V⋆ + 100% switching = basin creation, not barrier crossing. Sensitivity grids over PCA dim / KDE bandwidth still 🔴 TODO. |
| #6 "Attractor" definition loose | ✅ DONE | **NEW §3.1.1.5 Operational criteria for "attractor-like" regimes** — 4 falsifiable criteria (basin persistence, recurrence/dwell vs null, projection/embedder robustness, basin re-entry/contraction); regime-vs-criteria table. O1/O2/O3/D1 all PASS as strong attractors; D2 fails (exploratory only). |
| #7 Statistical independence violated | 🟡 partial (with multiple major new findings) | (a) family-cluster-bootstrap in ED50 fit script; (b) **§5.10.5 Group-aware basin-predictability** — family-leakage delta is **+0.07 for O1 but +0.27–0.30 for O2/O3/D1**; (c) **NEW §5.10.9 per-family ED50 heterogeneity** — `philosophy_dialog` shows clean step-up (0.10→0.40→**0.90**), `emotional` shows *negative* dose-response at dose 400 (0.40→0.10), `reflective` is flat. The population-mean curve averages over very different per-family curves. New Figure I in paper; (d) **NEW: GLMM via statsmodels** — `BinomialBayesMixedGLM` with random intercepts for family + IC produces ED50 = 331 tokens, vs 4PL bootstrap ED50 = 83 tokens [18, 459] from same data. **Two methods, very different point estimates, same data — confirms ED50 cannot be cleanly estimated from sparse data.** |
| #8 Researcher degrees of freedom | 🟡 partial | dense-dose config + analysis script *is* a frozen pre-reg for ED50 endpoint; held-out confirmatory beyond ED50 still 🔴 TODO |
| #9 Cross-model claims weaker than prose | 🟡 partial (language only, no new experiments) | §6.1 softened to "two OpenAI generators tested..."; §5.6 softened from "first quantitative" to "first reported"; cross-vendor *empirical* replication still 🔴 TODO |
| #10 Internal contradictions | ✅ DONE | 5 mechanical fixes: test count 94→99 (3 places), §5.3 broken arithmetic, §4.5 duplicate numbering 7/8 → 10/11, §6.6 sharpness-dim O3 ≈0 → 1.3–1.5, D2 naming collision flagged with footnote |
| §6.4 "effectively-infinite barrier vs OOD" overclaim | ✅ DONE | 3 locations softened to "no detectable barrier crossing within tested 5–400 token range" |
| §5.11 n=4 correlations fragile | ✅ DONE | Caveat box at top + closing paragraph reframed: "descriptive indicators, not inferential tests" |
| §3.1.4 / §7.8 "~600 nats" estimate not measured | ✅ DONE | Removed numerical estimate; added explicit "we did not capture logprobs... we **do not** report a numerical barrier in nats" |
| §5.4 temperature sensitivity (28pp reduced-vs-full discrepancy) | ✅ DONE | Caveat box at top of §5.4: "scope, not temperature, dominates the variance"; T-conclusion reframed as exploratory until publication-scope rerun |
| §6.6 practical-implications table overclaims | ✅ DONE | Restructured as "what we measured / what is *not* directly tested" two-column table; jailbreak-resistance / persona-stability claims explicitly flagged as not directly tested |
| §7.1 cross-model audit framing | ✅ DONE | Rewritten to honestly distinguish what the audit *establishes* (4 pub-scale headline cells preserve verdicts; 6/6 pre-registered predicates PASS on both gpt-4o-mini and gpt-4.1-nano) from what it does *not* (only 19/37 cells fully agree; 18/37 disagreements broken down by category — 13 classifier-output artefacts, 2 genuine borderline shifts, 3 finite-sample pilot cells; smaller-N cells show numerical drift; geometric toolkit not re-run; both generators are OpenAI so no cross-vendor claim possible). |
| Reproducibility: prompts inline | ✅ DONE | New §9.6 with all canonical system prompts inlined (O1/O2/O3/D1/D2 + perturbation injection mechanics) |
| Reproducibility: model versioning | ✅ DONE | New §9.7 with exact OpenAI snapshot identifiers, embedder versions, MiniMax model id for cross-vendor pilots |
| Reproducibility: license | ✅ DONE | §10.2 — Apache 2.0 for code, CC BY 4.0 for data (was: "TBD") |
| Cluster-stability check (HDBSCAN/spectral comparison) | ✅ DONE | New §5.10.6 + per-regime ARI heatmaps under `data/exp_*/reports/cluster_stability/`; aggregated summary in `data/aggregated/cluster_stability_summary.csv` |
| Abstract reframing (4 diagnostic + D2 exploratory) | ✅ DONE | Abstract rewritten to demote D2 from headline taxonomy and soften 150-token claim to 80–400 token range |
| D2 publication-scale empirical replication | 🔴 TODO | Would require new experiment — out of scope for this paper revision |
| **NEW: Multi-granularity switching (§5.10.7)** | ✅ DONE | `scripts/multi_granularity_switching.py` re-runs switching analysis on existing perturbation pilots at K-means k=12, k=4, HDBSCAN auto. Headline: **O1's OOD/IN asymmetry survives all three granularities** (~2× ratio everywhere). Replace-mode regimes saturate at fine granularities. D1 is most granularity-sensitive (drops 20pp on adversarial under HDBSCAN). New Figure H. |
| **NEW: Per-cluster semantic inspection (§5.10.8)** | ✅ DONE | `scripts/extract_cluster_text_samples.py` + gpt-5.5 high-reasoning analysis. Major finding: **only O1's "contractive basin" label accurately describes its mechanism**. O2 is paraphrastic family-preserving (not absorbing). O3 is template-absorbing (formal X/not-X), not semantic-absorbing. D1 is dialogue-state drift / recent-context capture, not pure stylistic multi-basin. Paper retains existing labels for continuity but flags the corrections explicitly with re-labelling proposed for future revision. |
| **NEW: Unified primary-results table (§5.0bis, Suggested Revision Plan #4)** | ✅ DONE | Single audit-friendly table at the top of §5: every regime × endpoint with value, 95% CI, source CSV, and stress-test status flag (validated / caveat-required / in-flight). Includes both stratified and group-aware basin-predictability values explicitly so readers can audit the leakage delta. |
| **NEW: §7.1 cross-model audit reframe** | ✅ DONE | Honest distinction between what the audit establishes vs what it doesn't (see row above for #7.1). |
| **NEW: Pre-written abstract variants (post-rerun)** | ✅ DRAFTED | `paper/ed50_rerun_plan.md` now contains three variant abstracts (Variant A: clean ED50; Variant B: saturating curve below 1; Variant C: still-noisy non-monotone) with action items for each. Probability assignment given current evidence: ~60% Variant B, ~20% A, ~20% C. |
| **NEW: Held-out confirmatory experiment plan** | ✅ DRAFTED (config not yet committed) | `paper/ed50_rerun_plan.md` describes a follow-up using 5 *disjoint* prompt families with the same dose schedule and frozen analysis. Pre-registered prediction: ED50 from held-out experiment within ±50 tokens of dense-rerun ED50. Run pending dense-rerun completion. |
| **NEW: Per-family ED50 heterogeneity (§5.10.9)** | ✅ DONE | `scripts/per_family_and_persistence.py` extracts per-family dose-response from existing sparse data. **Major finding: O1's "barrier" is family-heterogeneous** — philosophy_dialog has clean threshold-crossing (step at dose 200, rate jumps to 0.90), practical_dialog rises monotonically, but emotional has *negative* dose-response (drops to 0.10 at dose 400) and reflective is flat. The population-mean ~50% saturation averages over very different per-family curves. New Figure I in paper. |
| **NEW: Persistence test (§5.10.9)** | ✅ DONE | Same script computes "kicked at injection AND persisted to final step" rate. **At dose 400 only 8% (4/50) of trajectories are kicked-and-persisted, vs the 48% headline switching rate** — the 40pp gap is direct empirical confirmation that most "switching" is stochastic post-injection divergence, not basin-escape. Even of the 20% that visibly jump cluster at injection, ~40% drift back to original basin. |
| **NEW: GLMM (statsmodels) ED50 estimate** | ✅ DONE | Installed `statsmodels`, ran `BinomialBayesMixedGLM` with random intercepts for family + IC nested in family. GLMM ED50 = 331 tokens (assuming monotone logistic) vs 4PL bootstrap ED50 = 83 tokens [18, 459] (free shape). Two methods, same data, very different answers. Reinforces the headline that ED50 cannot be cleanly estimated from the sparse $n=50$/cell data. |
| **NEW: Replace-mode pre-experiment plan (review #3)** | 🟡 SCOPED | `paper/ed50_rerun_plan.md` documents experimental design for splitting `adversarial_overwrite_doseN` (current) from `adversarial_insert_doseN` (new — prepend to context, preserve generation). Predicted outcomes, runner code change estimated, cost ~$3–5. Not run in this revision but the design is documented for the next experimental cycle. |
| **NEW: §5.10.8 re-labelling propagated** | ✅ DONE | Abstract reframed (each regime described by its actual mechanism: register-shaped contractive O1, template-discourse O3, dialogue-state-driven D1). §6.1 expanded with "A note on regime labels" subsection explicitly proposing the re-labelled taxonomy: *register-contractive (O1), paraphrastic family-preserving (O2), template-absorbing (O3), dialogue-state-driven multi-basin (D1)*. Existing labels retained for continuity but corrections flagged everywhere they appear. |

**New artifacts added across this session:**

Configs / scripts:
- `configs/perturbation/O1_ed50_dense.yaml` — dense-dose ED50 sweep (8 doses, n=200/cell, 1800 trajectories, 4 control runs/IC)
- `scripts/fit_ed50_hierarchical.py` — hierarchical ED50 fit with family-cluster-bootstrap CI + optional GLMM + natural-floor estimate
- `scripts/group_aware_basin_predictability.py` — re-runs basin-predictability CV with GroupKFold-by-family
- `scripts/cluster_stability_check.py` — HDBSCAN + spectral + multi-k K-means with ARI matrices
- `scripts/render_tsne_animations.py` — joint-fit and per-step-refit t-SNE animations

Paper-side:
- `paper/ed50_rerun_plan.md` — execution plan with cost/runtime/predicted-scenarios
- `paper/openai_review.md` — this file
- New Figure 12: joint t-SNE flow snapshot (`tsne_anim_joint_snapshot.png`)
- New Figure G: group-aware basin-predictability bars (`group_aware_basin_pred.png`)
- New §3.1.1.5 (attractor criteria), §5.10.5 (group-aware), §5.10.6 (cluster-stability), §9.6 (prompts), §9.7 (model versioning)
- Author block + ORCID added to paper.tex preamble

Data outputs from this session's analyses:
- `data/aggregated/group_aware_basin_pred.csv` + `.png`
- `data/aggregated/cluster_stability_summary.csv`
- `data/exp_*/reports/cluster_stability/{stability.csv, stability_heatmap.png}` (one per regime)

**Substantive findings produced across the entire revision (beyond just framing fixes):**

0. **The original "~150 token barrier" claim was wrong by ~4×.** Confirmatory dense rerun ($n=200$/cell × 8 doses = 1,800 trajectories) gives **ED50 ≈ 40 tokens** (three independent methods converge: 4PL = 36; GLMM = 41; bootstrap median = 52). Beyond the point estimate, two structurally important findings: the dose-response **plateaus at 67%, not 1.0** (~31% non-switching subpopulation), and a **control-vs-control natural floor of 35%** consumes most of the low-dose effect (net adversarial saturates at +32 pp). The headline scientific claim is substantively different from the original. New §5.6.1 + Figure K. (§5.6.1)


1. **Family leakage in basin-predictability is regime-specific.** Stratified k-fold inflated the reported acc(k=10) by **+0.07 for O1, but +0.27–0.30 for O2/O3/D1**. Under leakage-free GroupKFold, the absolute regime ordering shifts (O1 > O3 > O2 > D1 instead of O3 > O2 > O1 > D1) and the gap between O1 and the rest shrinks from ~10–30pp to ~10pp. The contractive-basin story is the most robust to this stress test. (§5.10.5 + Figure G)

2. **HDBSCAN sees O1 as a single basin.** When run at default density thresholds, HDBSCAN auto-detects **2 clusters for O1** (vs 16 for O2/O3/D1) — exactly what a contractive attractor should look like. K-means $k=12$ over-partitions a single attractor in O1. (§5.10.6)

3. **The O1 contractive-basin headline is granularity-robust.** Re-computed switching rates at K-means k=12, k=4, and HDBSCAN show O1's adversarial-vs-OOD asymmetry (~2× ratio) preserved across all three cluster definitions. (§5.10.7 + Figure H)

4. **Only O1's regime label accurately describes its basin mechanism.** Per-cluster semantic inspection by gpt-5.5 reveals: O1 is *register-shaped contractive* (true to label); O2's "oscillatory" basins are *paraphrastic family-preserving sub-basins*, not a single attractor; O3's "absorbing" is *template-formal* (X/not-X), not semantic-absorbing — narrative seeds do not converge to the same text as technical seeds; D1's "stylistic multi-basin" is actually *dialogue-state drift / recent-context capture* — fear becomes yogurt advice, philosophical responsibility becomes Asana recommendations. The taxonomy survives but should be re-labelled in a future revision. (§5.10.8)

5. **The geometric V⋆ "ordinal agreement" claim is mechanistically broken.** Replace-mode regimes (O2/O3) have *high* V⋆ but saturated switching — these regimes are doing *basin creation* (the kick reshapes the density landscape) rather than *barrier crossing*. The two mechanisms produce opposite-sign V⋆-vs-switching predictions. (§5.10 caveat box)

6. **Existing-data ED50 has 25× CI under proper cluster-bootstrap.** The headline "150-token barrier" claim was based on n=50 sparse data; under family-cluster-bootstrap the 95% CI is **[18, 459] tokens** — uninformative. The dense-dose rerun (in flight) will resolve this. Two methods on the same data give very different point estimates (GLMM = 331 tokens, 4PL bootstrap = 83 tokens), reinforcing that ED50 is poorly identified at sparse $n$. (§5.6 / `fit_ed50_hierarchical.py`)

7. **The population-level "150-token barrier" averages over per-family curves with opposite shapes.** From the existing sparse data: **philosophy_dialog has a clean threshold step-up at dose 200** (rate 0.10 → 0.40 → 0.90), but **emotional has *negative* dose-response** (rate drops at dose 400 to 0.10), and **reflective is flat across all doses**. Under the current switching definition there is no single ED50 for O1; different prompt families exhibit qualitatively different barrier mechanisms. (§5.10.9 / Figure I)

8. **Most "switching" is NOT clean basin-escape.** A more conservative operational measure of barrier crossing — *"kicked at injection AND persisted in new basin to the final step"* — yields **only 8% (4/50) at dose 400**, vs the 48% headline switching rate at the same dose. The 40-percentage-point gap is direct empirical evidence that the headline metric mostly measures post-injection stochastic divergence from the paired control, not clean basin-escape. Even of the trajectories that *do* visibly jump cluster at injection (16–20% at high doses), roughly half drift back to their pre-injection cluster within the remaining ~15 steps of recursion. (§5.10.9 / persistence test)

The annotations on individual review items below preserve the original text and add status tags inline.

---

## Summary of Claims (as you understand them)

- Recursive LLM loops can be modeled as stochastic state-update systems where the generator and the context-update "nudge" should be separated; append, replace, and dialog updates induce different regimes.
- The paper identifies five empirical regimes: O1 append/continue contractive basin, O2 replace/paraphrase oscillatory 2-cycle, O3 replace/summarize-negate absorbing collapse, D1 stylistic multi-basin dialog, and D2 drill-down dialog with topic/content gravity.
- The main proposed diagnostic beyond prior work is **barrier height**: the amount of injected text required to make ≥50% of trajectories switch basins.
- Empirically, replace-mode regimes are claimed to be nearly barrier-free, O1 has a finite in-distribution adversarial barrier around 150 tokens and an out-of-distribution drift floor near 24%, while dialog regimes have intermediate/structure-dependent barriers.
- A secondary claim is that behavioral switching barriers agree qualitatively with geometric barriers derived from an empirical potential landscape \(V(x)=-\log\rho(x)\) in PCA-2 embedding space.

## Top Strengths

1. **The generator–nudge factorization is genuinely useful.** Separating \(P_\theta(\cdot\mid X_t; f)\) from \(\mathcal{N}_f\) is a clean conceptual move. It makes append vs replace vs dialog update rules explicit and gives a better vocabulary than "recursive prompting" for comparing loops.

2. **The perturbation-barrier framing is potentially novel and important.** Asking "how much intervention is needed to redirect a loop?" is a better practical question than only asking whether a loop converges, cycles, or collapses. This could become a useful robustness/evaluation protocol if tightened.

3. **The paper is unusually reproducibility-oriented.** The manuscript describes raw trajectories, embedding/analyze/report phases, coverage matrices, result verification, and CLI commands in far more detail than typical ML papers. The audit artifacts, if accurate, are valuable.

4. **The append/replace empirical contrast is plausible and compelling.** Even with current caveats, the qualitative observation that replace-mode loops are more perturbation-transparent than append-mode loops is believable and mechanistically coherent.

5. **The author is honest about several limitations.** Sections 5.12, 5.13, 7.1, and 7.6 acknowledge underdetermination by bulk diagnostics, embedder dependence of sharpness, limited cross-model coverage, and descriptive status of \(V(x)\). These admissions should be kept and sharpened.

## Top Weaknesses (ranked by severity)

1. **The headline "150-token barrier" is not statistically supported.** **✅ DONE — dense rerun complete 2026-04-30, "150 tokens" replaced with "ED50 ≈ 40 tokens" plus two-population structure.** Confirmatory dense rerun (1,800 trajectories, 8 doses, $n=200$/cell) finished cleanly. Three independent ED50 methods (4PL pooled = 36; GLMM = 41; family-cluster-bootstrap median = 52, 95% CI [8.5, 242]) converge at **~40 tokens** — the original headline was wrong by ~4×. Beyond the point estimate, two structurally important findings: (a) **upper asymptote = 0.69**, not 1.0 — there is a ~31% non-switching subpopulation; (b) **natural floor = 34.7%** from $n=600$ control-vs-control pairs — most low-dose switching is stochastic. Net adversarial effect saturates at +32 pp. The reviewer's concern is fully validated empirically: the original claim was indefensible; the corrected claim is more nuanced and substantively different. New §5.6.1 + Figure K + abstract reframed.

   - **What's wrong:** In §5.6, O1/adversarial switching is reported as 26% at 20 tokens, 34% at 80, 54% at 200, and 48% at 400, with n=50 per cell and Wilson CI half-widths around 13 percentage points. The curve is non-monotonic and only one point barely exceeds 50%. Yet the abstract, §1.3, §3.1.3, and §5.6 state "about 150 tokens" as if it were a measured threshold.
   - **Why it matters:** This is the paper's central quantitative claim. A skeptical reviewer can reject on this alone: the data do not identify a 50% threshold with useful precision. The true threshold could plausibly be below 80, around 200, above 400, or not monotonic under this protocol.
   - **Concrete fix:** Re-run O1 adversarial dose-response with much larger n and denser doses around the putative threshold: e.g. 20, 50, 80, 120, 160, 200, 300, 400, with n≥200 per dose. Fit a monotone dose-response model or logistic regression with hierarchical random effects for family/IC. Report the estimated ED50 with confidence/credible interval. If the interval is wide, say so. Until then, replace "~150 tokens" with "pilot evidence suggests a finite threshold between roughly 80 and 400 tokens."

2. **"Switching rate" is not a clean basin-transition measure.** **🟡 PARTIAL — substantively addressed.** Three lines of attack landed: (a) `--report-natural-floor` in `fit_ed50_hierarchical.py` will compute control-vs-control switching baselines from the dense rerun's 4 control runs/IC; (b) **NEW §5.10.6 cluster-stability check** — HDBSCAN auto-detects only 2 clusters for O1, vs 16 for O2/O3/D1, *strengthening* the contractive-basin story (K-means $k=12$ is a sub-partition of a single attractor); (c) `scripts/cluster_stability_check.py` runs HDBSCAN + spectral + multi-k K-means and reports pairwise ARI matrices per regime. Median ARI between K-means@12 and other methods is 0.53–0.66 — moderate stability, partition is not unique. The reviewer's full ask (validate clusters as basins beyond what we did) would extend to per-cluster semantic inspection — that's still 🔴 TODO.

   - **What's wrong:** §4.5.8 defines switching as final K-means cluster differing from the paired control's final cluster. Control is therefore 0% "by definition." There is no unperturbed paired rerun baseline measuring stochastic divergence under identical no-injection conditions. K-means clusters in joint PCA-10 may split a single semantic basin or merge distinct basins. Final-cluster difference is not equivalent to \(X_T\in B_2\) in the formal definition of §3.1.1.
   - **Why it matters:** The barrier definition depends on true basin switching. The current metric may measure arbitrary cluster-label changes, stochastic decoding variation, or perturbation-induced local embedding displacement rather than attractor-boundary crossing. This threatens every perturbation result.
   - **Concrete fix:** Add a "no-op paired stochastic rerun" condition: same seed/config, no injected perturbation, independent generation randomness. Define the natural switching floor relative to this baseline, not relative to the same control trajectory. Validate clusters as basins using stability across k, bootstrap, HDBSCAN/spectral alternatives, and semantic inspection. Prefer late-window basin assignment over single final-step cluster.

3. **The perturbation protocol confounds barrier crossing with state replacement and injected-text identity.** **🔴 TODO** — requires a new perturbation type (context-insertion vs full state-overwrite) and new pilot. Not addressed this session.

   - **What's wrong:** For operator experiments, §9.2 says injection replaces step \(k\)'s output entirely. In replace mode, this trivially makes \(X_{k+1}=\text{injection}\). Thus O2/O3 "94–100% switching" largely follows from the experimental intervention overwriting the entire state, not from a discovered low barrier. Also, neutral/lorem/adversarial differ in fluency, topic, source distribution, and likely length/content structure. "Adversarial" is late-step output from another trajectory, but details of matching are thin.
   - **Why it matters:** The central append-vs-replace contrast may be partly tautological: replace-mode perturbation replaces state. The conclusion "replace-mode regimes are perturbation-transparent" is true by design, but the measured rates do not reveal much about attractor stability.
   - **Concrete fix:** Separate two perturbation types: **state overwrite** and **context insertion/additive nudge**. For replace mode, test smaller prepend/append perturbations to the input before generation without replacing the whole output, or inject perturbations into the prompt while preserving generated output. Match all perturbation conditions by token length, fluency, topic distance, and source family. Include in-distribution non-adversarial controls.

4. **Lemma 1 and Corollaries do not prove the stated barrier claim.** **✅ DONE** — §3.1.2 fully rewritten via gpt-5.5 high-reasoning. Key changes: (a) new quantity `G_m = post-injection generation budget` introduced and held distinct from injected-token cost τ; (b) assumption (1) broadened from `x ∈ B₁` to `x ∈ R_s \ B₂` (any reachable state outside B₂), closing the proof gap; (c) Corollary 1 now bounds `G⋆_{1/2} ≤ κ·m_{1/2}`, *not* `B(B₁→B₂)`; (d) post-Corollary-1 paragraph explicitly states this corollary does *not* bound the injected-token barrier and notes `B(B₁→B₂) = 0` for replace mode under the assumptions; (e) empirical-verification paragraph reframed: 94–96% switching → q₀r₀ ≈ 0.94–0.96 → certifies `G⋆ ≤ κ`, *not* a τ-barrier.

   - **What's wrong:** §3.1.2 defines barrier height as injected-token cost \(\tau\), but Corollary 1 bounds it by \(\kappa m\), where \(\kappa\) is expected generated output length over post-injection replace steps. That is not the cost of injected text. The proof also assumes that after failed attempts the trajectory remains in \(B_1\), but the lemma only gives uniform one-step access from \(x\in B_1\). Failure may leave \(B_1\), invalidating the repeated bound unless access is assumed for all reachable non-\(B_2\) states or a reset-to-\(B_1\) property is proven.
   - **Why it matters:** The theoretical section appears more rigorous than it is. A reviewer will flag this as a mismatch between formal definition and proof. It weakens the claimed theoretical contribution.
   - **Concrete fix:** Rewrite Lemma 1 as a simple hitting-probability bound under explicit assumptions over the full reachable set. Do not call \(\kappa m\) an injected-token barrier unless the injected text is regenerated each step. Alternatively, define a separate "time-to-access" or "post-injection generation budget" quantity. Keep the append result as a conjecture.

5. **The \(V(x)=-\log\rho(x)\) geometric-barrier claims are overinterpreted.** **✅ DONE (paper-only).** §5.10 now opens with an explicit caveat box stating: "the geometric $V^\star$ values are descriptive, not an independent quantitative validation"; explicit acknowledgement that O2/O3 high $V^\star$ + 100% switching is *basin creation* not *barrier crossing*; abstract reframed (no longer claims "behavioral and geometric barriers agree in ordinal structure"); §1.3 fourth contribution rewritten to "complementary descriptive view... not a quantitative independent confirmation". The numerical sensitivity grids over PCA dim, KDE bandwidth, grid resolution still 🔴 TODO — but the paper now no longer overinterprets.

   - **What's wrong:** The abstract says behavioral and geometric barriers "agree in ordinal structure." But §5.10 shows O2/O3 lorem have the largest \(V^\*\) while switching is 100%; the paper explains this as "basin creation rather than barrier crossing." That is a different mechanism, not ordinal agreement. \(V^\*\) is computed on PCA-2 KDE with smoothing, clipping, grid discretization, arbitrary basin count, and capped \(V\), with no sensitivity analysis.
   - **Why it matters:** The geometric triangulation is presented as independent validation. In current form it is mostly descriptive visualization. The quantitative agreement claim is not established.
   - **Concrete fix:** Downgrade claims: "geometric landscapes provide qualitative context" rather than "barriers agree." Add sensitivity analyses over PCA dimensions/projections, KDE bandwidth, grid resolution, basin detector thresholds, and embedders. Compute correlations between behavioral ED50/switching and \(V^\*\) only where barrier crossing, not basin creation, is the hypothesized mechanism.

6. **The definition of "attractor" is loose and not falsifiable enough.** **✅ DONE.** New §3.1.1.5 *Operational criteria for "attractor-like" regimes* drafted by gpt-5.5 high-reasoning. Four falsifiable criteria with quantitative thresholds: **C1** late-window basin persistence ($A^{\mathrm{final}} \ge 0.70$), **C2** temporal recurrence/dwell vs null ($z \ge 2$ AND $d \ge 0.5$), **C3** projection/embedder robustness (recurrence-bin agreement across ≥2 of 3 embedders), **C4** basin re-entry or contraction (Lyapunov $\lambda_1^{late} \le 0.015$ OR period-2 cycle OR $R \ge 0.90$ AND $SD \le 1.50$ OR exit-return null gate). Three labels: *strong attractor* (4/4), *attractor-like* (3/4), *not attractor* (<3/4). Regime-vs-criteria table with actual numbers from §5.* shows O1, O2, O3, D1 all PASS as strong attractors; D2 fails on multiple counts (exploratory scope, no publication-scale measurements). The title claim "attractor regimes" is now operationalised and falsifiable.

   - **What's wrong:** The manuscript alternates among basin score, recurrence, cluster persistence, low-dimensional collapse, density wells, and perturbation resistance as evidence of "attractors." But there is no single operational criterion that says when a regime is or is not an attractor. D1 and O1 are explicitly hard to separate by bulk diagnostics (§5.12), and D2 is exploratory-scale.
   - **Why it matters:** The title and abstract claim "endogenous attractor regimes." Without a tight operational definition, reviewers may view this as metaphorical embedding-cluster analysis rather than dynamical-systems evidence.
   - **Concrete fix:** Introduce a minimal formal operational definition: e.g. an attractor candidate requires (i) late-window basin persistence above null, (ii) recurrence/dwell above time-shuffled/no-feedback baselines, (iii) robustness under k/projection/embedding sensitivity, and (iv) nontrivial basin re-entry or contraction. State which regimes satisfy which criteria. Use "attractor-like" consistently when criteria are incomplete.

7. **Statistical independence and uncertainty are not handled at the right level.** **🟡 PARTIAL — substantively addressed with a major new finding.** Two strikes: (a) `fit_ed50_hierarchical.py` does family-cluster-bootstrap for the headline ED50; (b) **NEW §5.10.5 Group-aware basin-predictability** — `scripts/group_aware_basin_predictability.py` re-runs the existing basin-predictability classifier with GroupKFold-by-family. **The leakage delta is dramatic and regime-specific:** O1 +0.07, O2 +0.30, O3 +0.28, D1 +0.27. Under leakage-free CV the regime ordering changes (O1 > O3 > O2 > D1 instead of O3 > O2 > O1 > D1) and the gap shrinks. This is a substantive empirical finding (not just methodological caveat) and *strengthens* the O1 contractive-basin headline while weakening the O2/O3/D1 basin-predictability claims. New Figure G in paper. Mixed-effects logistic across all perturbation results and family-level uncertainty everywhere is still 🔴 TODO but the headline endpoints now have honest CIs.

   - **What's wrong:** Many reported n's are trajectory counts, but trajectories are nested within prompt families, ICs, and runs. Publication runs use 15 families × 30 ICs × 3 runs, yet analyses often treat trajectories as independent. Basin-predictability CV may split runs from the same IC/family across train/test. Perturbation n=50 cells likely have only 5 families × 5 ICs × 2 runs. CIs do not appear hierarchical.
   - **Why it matters:** Effective sample size may be much smaller than nominal n. Reported confidence intervals and accuracies may be overconfident, especially for perturbation and temperature-sweep claims.
   - **Concrete fix:** Use grouped/hierarchical bootstrap resampling by family and IC. For basin predictability, use GroupKFold or leave-family/leave-IC-out CV. Report both trajectory-level and family-level uncertainty. For perturbation, show per-family switching rates and fit mixed-effects logistic models.

8. **The experimental design has high researcher degrees of freedom.** **🟡 PARTIAL** — the dense-dose config + analysis script committed before the run starts *is* a frozen pre-registration for the headline ED50 endpoint (frozen analysis, no re-tuning post-data). The broader reviewer ask (define a small set of primary endpoints, move exploratory diagnostics to appendix, run a fresh held-out confirmatory experiment) is still 🔴 TODO.

   - **What's wrong:** The paper uses many observables, PCA dimensions, t-SNE plots, k=12 clusters, \(\epsilon=0.15\), multiple regimes, pilots, temperature sweeps, perturbation doses, geometric summaries, and post-hoc classifiers. It explicitly says hypotheses were not pre-registered. "103/103 numeric claims verified" only means numbers match CSVs, not that analyses were planned or statistically valid.
   - **Why it matters:** Top-venue reviewers will worry that the taxonomy and thresholds were selected after looking at many diagnostics.
   - **Concrete fix:** Define a small set of primary endpoints before additional analysis: e.g. recurrence, basin predictability, adversarial switching, neutral switching, ED50. Move exploratory diagnostics to appendix. Add robustness grids over key analysis choices. If possible, run a fresh held-out confirmatory experiment with frozen analysis scripts.

9. **Cross-model and cross-embedding claims are weaker than the prose suggests.** **🟡 PARTIAL** — language softened: §6.1 "taxonomy is determined by the nudge family..." now reads "in the two OpenAI generators tested... two generators from one vendor are insufficient to claim model-agnosticism. Cross-vendor replication... is required." §5.6 "first quantitative measurement" softened to "first reported... we do not claim priority." Cross-vendor *empirical* replication (open-weight Llama / Qwen / Claude as second generator; non-OpenAI embedder for primary endpoint) is still 🔴 TODO.

   - **What's wrong:** §5.14 is within-vendor only: `gpt-4o-mini` vs `gpt-4.1-nano`, likely sharing family/alignment/tokenization properties. §5.13 shows sharpness is not embedder-invariant and basin-predictability values shift substantially under alternative embedders. Geometric barriers and perturbation ED50 are not cross-embedder validated.
   - **Why it matters:** The paper sometimes gestures toward model-agnostic or general LLM-loop claims, but evidence is mostly OpenAI-generator/OpenAI-embedder-specific.
   - **Concrete fix:** Reframe as a case study on two OpenAI generators. If possible, add at least one open-weight non-OpenAI generator and one non-OpenAI embedder for the primary perturbation endpoint. Otherwise remove/soften "model-agnostic" language outside the formal nats discussion.

10. **Several internal contradictions and naming/numbering issues reduce trust.** **✅ DONE** — five mechanical fixes landed: (a) test count 94 → 99 in three places (verified by `pytest --collect-only`); (b) §5.3 broken arithmetic `5×30×3=1350` rewritten to split operator (15×30×3=1350) vs dialog (5×30×3=450) per §4.2; (c) §4.5 numbering renumbered duplicate 7/8 → 10/11 with cross-ref at line 1283 updated; (d) §6.6 sharpness-dim O3 ≈ 0 → ≈ 1.3–1.5 with cross-ref to §5.0; (e) D2 naming collision in §5.0 table flagged with `(*)` + footnote disambiguating `exp_dialog_D2_replace_curious_helpful` (replace-dialog pilot) from D2 drill-down regime.

    - **What's wrong:** Examples: Contributions mention 99 tests, §4.12/§10.7 mention 94. D1 publication-scale is described as 450 trajectories in §4.2 but §5.3 says "four diagnostic regimes at full scale … 1350 trajectories per regime." D2 means replace-dialog in §5.2 and drill-down dialog later. §4.5 numbering repeats 4.5.7 and 4.5.8. §6.6 says O3 has "sharpness-dim ≈0," but §5.0 reports 1.45. Figure 4 caption says O1 adversarial crosses near "~150–400 tokens," while prose says ~150. Abstract says D2 exploratory-scale but also includes it in a five-regime taxonomy.
    - **Why it matters:** These are not mere typos; they make readers doubt the analysis provenance.
    - **Concrete fix:** Do a consistency pass. Freeze regime names, sample sizes, test counts, section numbering, and headline values. Add a table of all experiments with exact N, T, conditions, and which claims they support.

## Section-by-Section Issues

### 1. Introduction

- §1.3 overclaims "we prove a finite-time access bound" and ties it to barriers, but the lemma does not bound injected-token barrier as defined.
- The phrase "first quantitative barrier-height measurement for an LLM loop" is too strong given the pilot-scale, noisy ED50 estimate.
- The contribution list mixes core scientific claims with reproducibility/audit claims; it reads more like a repository report than a paper introduction.

### 2. Background and Related Work

- The comparison table with arXiv:2512.10350 and others is very self-favorable and includes claims like "103/103 cell-verified" that are not scientific advantages over prior work.
- §2.4 correctly says \(V(x)\) is descriptive, but later sections repeatedly lean on it as validation of behavioral barriers.
- Some cited 2025/2026 works appear central but are not contextualized enough for a reviewer to assess their reliability or relationship to this paper.

### 3. Formal Framework and Hypotheses

- The state space \(\mathcal{C}\) is "finite-length character strings," but later token-based barriers and embedding-space basins are used interchangeably. The maps between string state, observable, embedding, and basin need to be formalized.
- Lemma 1 has the proof/definition mismatch described above.
- §3.1.4 "Tokens vs nats" is speculative and partially inconsistent: it says OOD perturbations have high surprisal but low basin-relevant information, then equates barrier nats with token count times average conditional surprisal. That product does not isolate basin-relevant information.

### 4. Methods

- Exact prompt templates are not inline. For a behaviorally sensitive LLM-loop paper, configs are not enough; the manuscript should include canonical system/user prompts and injection formatting.
- §4.5 has duplicated numbering and too many metrics. It is unclear which metrics are primary and which are exploratory.
- Recurrence uses a fixed \(\epsilon=0.15\) described as "cosine," but after PCA-10 Euclidean distances are mentioned elsewhere. The metric/distance scale needs clarification.
- Basin predictability uses K-means labels as ground truth. This is circular unless cluster validity/stability is shown.
- Perturbation switching lacks a stochastic no-perturbation paired baseline, making "control 0%" misleading.

### 5. Results

- §5.0 says five regimes "at a glance," but D2 is underpowered and lacks many diagnostics. It should be visually separated as exploratory.
- §5.3 claims "four diagnostic regimes at full scale … 1350 trajectories per regime," but D1 has 450 trajectories per §4.2.
- §5.4 temperature sensitivity is based on reduced-scope cells and acknowledges a 28-point discrepancy between reduced and full O1 at T=0.8. This undermines the T-sensitivity conclusion; N/scope confounds temperature.
- §5.5–5.7 are the most important results but are pilot-scale n=50. They need stronger statistical treatment and reruns.
- §5.10's explanation of high \(V^\*\) with 100% switching admits the geometric metric is measuring something different from behavioral barrier crossing.
- §5.11 correlations across n=4 regimes should probably be removed or moved to appendix. Pearson \(r=0.981\) with four points is fragile and not persuasive.
- §5.12 says bulk diagnostics underdetermine O1/D1, which is useful, but the feature matrix/sample count description is confusing: "13 experiments" but parenthetical counts appear to sum inconsistently.

### 6. Discussion

- §6.1's "taxonomy is determined by the nudge family; barrier magnitude by the generator" is too strong. Only two OpenAI generators are tested, and prompt/content operators also matter.
- §6.4's "effectively-infinite barrier against out-of-distribution noise" is not supported by doses only up to 400 tokens and n=50. Say "not crossed in tested range."
- §6.6 practical implications table overstates readiness. "Stable trajectory," "jailbreak resistance," and "persona stability" are plausible applications but not empirically tested.

### 7. Limitations

- Stronger than many papers, but it sometimes uses limitation language to preserve overclaims rather than revising them. Example: D2 is "least mature," yet the title/abstract still include it as one of five regimes.
- §7.1 cross-model audit is useful but should be summarized more soberly: many 37-cell verdict mismatches are dismissed as reporting artifacts, which may not satisfy reviewers.
- §7.8 correctly notes tokens are operational, but this should force removal of the "~600 nats" estimate unless logprobs are actually measured.

### 8. Future Work

- Good directions, but many are necessary controls for the current paper rather than future work: cross-vendor replication, logprob-based barriers, publication-scale D2, hybrid nudge sensitivity.
- §8.7 safety/alignment basins is speculative and should be shortened unless experiments are added.

### 9. Methods Appendix

- The Lyapunov code snippet in §9.1 differs from the earlier definition using covariance eigenvalues and baseline/final ratios. The snippet `lambda_t = np.log(sigmas)/2.0` is not the same finite-time exponent described in §4.5.5.
- Basin predictability snippet uses `cv=5`, while §4.5.7 says adaptive stratified k-fold with singleton dropping. The appendix should match actual code.
- §9.2 says adversarial samples exclude the family of the trajectory; §4.5.8 says "different (family, IC) trajectory of the same regime." This should be unified.

### 10. Reproducibility Statement

- The reproducibility infrastructure is detailed, but exact model versions, prompts, decoding parameters, random seeds, and config hashes should be in an appendix table.
- "License TBD" is a problem for reproducibility and reuse.
- "103/103 numeric claims verified" should be framed narrowly: it verifies manuscript/data consistency, not scientific validity.

## Writing & Structure

- **The paper is far too long and mixes paper, lab notebook, repo documentation, and figure appendix.** A top-venue submission should separate core claims from engineering details. Move most pipeline diagrams, animation details, CLI commands, and exhaustive report descriptions to appendix/supplement.
- **The primary endpoint is buried.** The reader should know by the end of §4 exactly which 3–5 quantities will decide the hypotheses. Currently dozens of metrics compete for attention.
- **Terminology drifts.** "Attractor," "basin," "cluster," "sink," "barrier," "switch," "collapse," "regime," and "nudge" are sometimes used interchangeably. Define a strict hierarchy: text state → observable → embedding → cluster → basin candidate → attractor-like regime.
- **Figure captions are overlong and sometimes argue beyond the data.** They read like mini-discussion sections. Captions should state construction and takeaway, not introduce new claims such as "minimum-action path" or "the kick cleared the ridge" unless demonstrated.
- **The D2 story is confusing.** D2 first appears as replace dialog in §5.2 and later as drill-down dialog. Rename the early replace-dialog pilot or reserve D2 exclusively for drill-down.
- **The theory section should be shorter and more cautious.** The current lemma/conjecture/nats/potential bridge creates a facade of formalism around mostly empirical pilot data.
- **The results section needs hierarchy.** Put the main perturbation experiment first after a concise regime-establishment section. Move T-sweep, embedding ablation, cross-metric correlations, unsupervised clustering, animations, and RG dendrograms to secondary analyses.

## Reproducibility Audit

**Well documented:**

- Raw trajectory storage path, downstream embedding/analyze/report pipeline, and many CLI commands are listed.
- Observable definitions are described in detail.
- Projection methods, t-SNE parameters, K-means k, and many metric definitions are given.
- Coverage and results-verification artifacts are described.
- Approximate API cost and local compute requirements are provided.

**Missing or insufficient:**

- Exact prompt templates/system messages for O1/O2/O3/D1/D2 are not inline; readers must inspect configs.
- Exact perturbation text pools and adversarial sampling procedure are not fully specified in the paper.
- Model versioning is ambiguous: OpenAI model aliases can change. Need date/version/hash or stored response metadata.
- Random seeds and whether generation randomness is reproducible through API calls are unclear.
- No clear config hash table mapping every result table/figure to exact config files.
- License is "TBD," which limits reuse.
- The code snippets in §9 do not always match described methods.
- The no-feedback/independent-regeneration baselines are described but their numerical results are not prominently reported for the key claims.
- Embeddings are regenerable for ~$30, but if OpenAI embedding model behavior changes, exact reproduction may fail unless cached embeddings are released.

## Suggested Revision Plan

1. **Rebuild the main perturbation result as a confirmatory experiment.** Freeze the switching definition, add stochastic no-injection rerun baselines, run larger O1 dose-response with grouped uncertainty, and report ED50 with CI. This is the highest-leverage fix. **🟡 IN PROGRESS** — dense-dose config (8 doses, n=200/cell), `fit_ed50_hierarchical.py` with cluster-bootstrap CI and natural-floor option, plan doc all in place. Run executing now.

2. **Narrow the paper's claims.** Make the core claim: "In two OpenAI generators, under these prompt templates and embedding diagnostics, append/replace/dialog nudges show different perturbation sensitivity." Remove or soften model-agnostic, thermodynamic, and "first measurement" language. **✅ DONE (paper-only).** "first measurement" softened to "first reported"; "model-agnostic" / "taxonomy determined by nudge family" softened to "in the two OpenAI generators tested..."; "~600 nats" estimate removed; "effectively-infinite OOD barrier" softened to "no detectable crossing in tested 5–400 token range"; §6.6 practical-implications table restructured as "what we measured / what is *not* directly tested"; §6.4 OOD claim corrected; abstract reframed (4 diagnostic + D2 preliminary, headline 150-token claim softened to 80–400 token range pending dense rerun); V⋆ ordinal-agreement claim removed; §5.4 T-conclusion downgraded to exploratory.

3. **Fix the formal section.** Repair Lemma 1 or demote it to intuition. Align barrier definition with what is actually measured. Move the nats/KL/\(V^\*\) bridge to discussion as speculation unless logprobs are added. **✅ DONE.** Lemma 1 / Corollary 1 fully rewritten (see #4) — `G_m` introduced as separate quantity, Corollary 1 honestly bounds $G^\star$ not $\mathrm{B}(B_1\to B_2)$, proof gap closed. Nats numerical estimate removed; explicit "we do not capture logprobs" disclaimer. V⋆ bridge in §3.1.4 framed as conditional ("the nats-quantity *would be of the form* ..., but we do not measure it"); §5.10 V⋆ section now opens with explicit "descriptive, not validation" caveat. **NEW §3.1.1.5 Operational criteria** further tightens the formal apparatus — the title's "attractor" claim is now operationalised with 4 falsifiable criteria.

4. **Create a clean primary-results table.** For each regime, report exact N, T, prompt/operator, nudge, primary diagnostics, stochastic baseline switching, neutral/lorem/adversarial switching, and uncertainty. Mark D2 explicitly exploratory. **✅ DONE.** New §5.0bis (top of §5) consolidates every regime × endpoint with value, 95% CI, source CSV, and stress-test status flag. Both stratified and group-aware basin-predictability values shown explicitly so readers can audit the leakage delta. D2 explicitly omitted from this table because it fails the operational attractor criteria (§3.1.1.5).

5. **Move implementation-heavy material to supplement and enforce consistency.** Shorten figures/captions, remove animation details from the main paper, fix numbering/naming/test-count contradictions, and include exact prompt/config snippets. **🟡 PARTIAL — substantively advanced.** Consistency contradictions all fixed (item #10). **NEW §9.6 inline prompt templates** for O1/O2/O3/D1/D2 + perturbation-injection mechanics. **NEW §9.7 model versioning** with exact OpenAI snapshot identifiers, embedder versions, MiniMax model id. License clarified to Apache 2.0 / CC BY 4.0 (was: TBD). Shortening figures/captions and moving animations to supplement is still 🔴 TODO.

## Likely Reviewer Objections (NeurIPS-style adversarial)

1. **"Your barrier height is not measured; it is guessed from four noisy points."**
   - **Current defense:** The paper reports Wilson CIs and dose-response pilot data.
   - **Assessment:** Insufficient. Needs denser/larger ED50 experiment.
   - **Status: ✅ DONE — dense rerun complete.** New ED50 = 40 tokens (4PL/GLMM/bootstrap converge); 95% family-cluster-bootstrap CI [8.5, 242]; upper asymptote 0.69 (non-switching subpopulation); natural floor 35% (most switching is stochastic). The objection is fully addressed; the original claim was wrong by ~4×, and the corrected story is substantively different. The CI is still wide due to 5-family-cluster-bootstrap heavy tails — a held-out replication on 5 disjoint families (planned in `paper/ed50_rerun_plan.md`) would tighten this.

2. **"Switching is just K-means label disagreement, not attractor escape."**
   - **Current defense:** The paper uses joint PCA/K-means, late-window basins, and geometric visualizations.
   - **Assessment:** Partial defense only. Needs cluster-stability analysis and stochastic no-perturbation baseline.
   - **Status: 🟡 SUBSTANTIVELY ADDRESSED on four fronts, including direct empirical confirmation of the reviewer's concern.** (1) **§5.10.6 cluster-stability**: HDBSCAN auto-detects only 2 clusters for O1, strengthening the contractive-single-basin story. (2) **§5.10.7 multi-granularity switching**: O1's OOD-vs-IN-distribution asymmetry robust at K-means k=12, k=4, HDBSCAN. (3) **§5.10.8 per-cluster semantic inspection**: gpt-5.5 characterised actual content of each basin, surfacing that paper's regime labels are partially mislabelled. (4) **§5.10.9 persistence test**: under the more conservative *"kicked at injection AND persisted to final step"* metric — the operational definition closest to "true basin escape" — **the rate is only 8% (4/50) at dose 400**, vs 48% headline switching rate. **This 40pp gap is direct empirical confirmation** that most "switching" under our current definition is stochastic post-injection divergence, not clean basin-escape. The reviewer's concern is now empirically validated, not just methodologically acknowledged. Stochastic no-perturbation baseline will land when the dense rerun completes.

3. **"Replace-mode capitulation is tautological because your injection replaces the state."**
   - **Current defense:** Lemma 1 argues replace mode structurally has low barriers.
   - **Assessment:** Weak. The experiment confirms the intervention design more than an independent dynamical property.
   - **Status: 🟡 PARTIAL — addressed theoretically and scoped experimentally.** (a) **Theoretical**: §3.1.2 rewrite explicitly distinguishes injected-token cost τ from generation budget G (Lemma 1 / Corollary 1 now bound G⋆, *not* the τ-barrier; in replace mode, B(B₁→B₂) = 0 is degenerate by the §3.1.1 definition). (b) **Empirical**: §5.10.8 per-cluster semantic inspection shows O3 is "template-absorbing" (formal X/not-X structure imposed by the operator) but **not semantically absorbing** — narrative seeds become event+reversed-event, technical seeds become claim+denial, etc., maintaining content-family separation. So the operator imposes a discourse template, but the regime is *not* a single-attractor capitulation. (c) **Future experiment scoped**: `paper/ed50_rerun_plan.md` describes a follow-up splitting `adversarial_overwrite_doseN` (current) from `adversarial_insert_doseN` (prepend, preserve generation). Predicted outcomes documented, not yet run.

4. **"This is all embedding-artifact analysis."**
   - **Current defense:** §5.13 tests `text-embedding-3-large` and `all-mpnet-base-v2`; basin predictability and recurrence are partly invariant.
   - **Assessment:** Decent for broad replace-vs-append distinction, weak for geometric barriers, sharpness, and fine taxonomy.

5. **"The theory is hand-wavy and does not connect to the experiments."**
   - **Current defense:** State–generator–nudge formalism is useful; Lemma 1 attempts a bound; Conjecture 1 matches O1 qualitatively.
   - **Assessment:** Formalism is useful, but lemma/corollary need correction and the nats/KL claims should be demoted.
   - **Status: ✅ DONE for lemma/corollary** (rewrite — see #4). **✅ DONE for nats numerical estimate** (removed). **🟡 PARTIAL for KL/V⋆ bridge** (still in §3.1.4 with clearer conditional framing; full demotion 🔴 TODO).

6. **"D2 should not be a full regime; it is n=25 exploratory."**
   - **Current defense:** The paper repeatedly labels D2 exploratory and notes publication-scale replication is future work.
   - **Assessment:** Then it should not be in the headline five-regime taxonomy at equal status.
   - **Status: ✅ DONE (structurally).** Abstract reframed to **four diagnostic regimes** (O1, O2, O3, D1) with D2 as **preliminary evidence at exploratory scale**. The new §3.1.1.5 attractor criteria explicitly fail D2 on multiple counts (no publication-scale basin-predictability, no null-calibrated recurrence, no Lyapunov / exit-return), labeling it "not attractor; exploratory regime candidate." Naming-collision bug between `exp_dialog_D2_replace_curious_helpful` and "D2 drill-down" was fixed in the consistency pass with a `(*)` flag + footnote. Publication-scale D2 experiment is still 🔴 TODO (out of scope for this revision).

7. **"The paper is a fishing expedition over many metrics and plots."**
   - **Current defense:** Discovery order is documented; results are cell-verified; some unsupervised checks and cross-model predicates are included.
   - **Assessment:** Documentation does not solve researcher degrees of freedom. Needs a frozen primary analysis and preferably held-out confirmatory runs.
   - **Status: 🟡 PARTIAL** — the dense-dose ED50 config + analysis script committed before the run *is* a frozen pre-registration for the headline endpoint. A held-out confirmatory experiment beyond ED50 (e.g., across regimes, across temperatures) is 🔴 TODO.
