## 5. Results

Adversarial append-mode perturbations produce a clear raw-switching dose response in the O1 continuation loop, with $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, but they do not establish durable basin escape in the tested range. The dense rerun shows a raw plateau near 67%, a natural stochastic-divergence floor near 35%, a maximum net adversarial effect of +32 percentage points at 400 tokens, and a maximum persistent-escape rate of 16% under the canonical K-means $k=12$ definition. Replace-mode loops initially appear almost fully perturbation-transparent, but the overwrite-versus-insert probe shows that most of this effect comes from the memory policy discarding prior state, not from a low injected-token barrier. Phase-0 and Phase-1 pilots validated the measurement pipeline and identified candidate regimes; full pilot history is in §11.7, the aggregation and per-experiment catalog is in §11.9, and row-level endpoint audit tables are in Extended Data Tables 1 and 2 (§11.1, §11.2).

---

### Phase A, headline endpoint

### 5.1 Adversarial append perturbations produce raw switching but not persistent escape

The central perturbation endpoint is O1 append-mode continuation under in-distribution adversarial text. In the sparse pilot, O1 adversarial perturbations showed a graded response, while O1 neutral perturbations remained flat near the out-of-distribution drift floor and D1 neutral perturbations saturated even at very small doses. The dense rerun then localized the O1 adversarial raw-switching curve at $n=200$ trajectories per dose and separated three quantities that must not be conflated:

1. **Raw switching:** final K-means cluster differs from the paired control trajectory.
2. **Net switching:** raw switching minus the control-control stochastic-divergence floor.
3. **Persistent escape:** the trajectory visibly changes cluster at injection and remains in the post-injection cluster to the terminal step.

The dense rerun was pre-registered before execution: $n=200$ per cell, equal to 5 families × 10 ICs × 4 runs, with 8 adversarial dose conditions plus one control condition, for 1,800 trajectories total. The configuration was `configs/perturbation/O1_ed50_dense.yaml`; the analysis script was `scripts/fit_ed50_hierarchical.py`.

**Dense O1 adversarial dose response, separating raw, net, and persistent endpoints**

| dose (tokens) | raw switch rate | Wilson 95% CI | net over natural floor | persistent escape, K-means $k=12$ |
|---:|---:|---|---:|---:|
| 20 | 0.415 | [0.349, 0.484] | +0.068 | 0.035 |
| 50 | 0.510 | [0.441, 0.578] | +0.163 | 0.070 |
| 80 | 0.575 | [0.506, 0.641] | +0.228 | 0.035 |
| 120 | 0.630 | [0.561, 0.694] | +0.283 | 0.090 |
| 160 | 0.605 | [0.536, 0.670] | +0.258 | 0.115 |
| 200 | 0.620 | [0.551, 0.684] | +0.273 | 0.130 |
| 300 | 0.655 | [0.587, 0.717] | +0.308 | 0.140 |
| 400 | 0.670 | [0.602, 0.731] | +0.323 | 0.160 |

The control-control natural floor is 34.7% [31.0%, 38.6%] across $n=600$ ordered control-control pairs. Thus two trajectories with the same family and IC seed but different generation RNG end in different K-means clusters 35% of the time without any perturbation. The raw 50% crossing occurs between 20 and 50 tokens, but much of that apparent switching is baseline stochastic divergence. Under the stricter net endpoint, the curve does not reach +50 percentage points within the tested range.

Three independent ED50 estimates agree on the raw-switching scale:

| method | ED50 (tokens) | uncertainty |
|---|---:|---|
| 4PL pooled fit | 36 | point estimate |
| Mixed-effects logistic GLMM | 41 | point estimate, log10-dose slope |
| Family-cluster bootstrap median | 52 | 95% CI [8.5, 242] |

The point estimates cluster in the 36-52 token range, substantially below the earlier sparse-grid estimate near 150 tokens. The family-cluster bootstrap interval remains wide because only five prompt families are available for resampling.

Two structural findings matter more than the exact ED50 point estimate. First, the raw curve plateaus near 67%, not near 100%. The 4-parameter logistic upper asymptote is $a = 0.69$, implying a substantial non-switching subpopulation under the present protocol. Second, the persistent-escape endpoint is much smaller than raw switching. At dose 400, raw switching is 67%, but persistent escape is 16% under K-means $k=12$. Most raw switching is therefore not clean barrier crossing. It is final-step divergence from the paired control, often without a durable at-injection jump into a new basin.

The persistence decomposition on the dense rerun confirms this interpretation. At dose 400, 69 of 200 trajectories visibly changed cluster at injection. Of those, 32 persisted in the post-injection cluster, 13 drifted back to the pre-injection cluster, and 24 drifted elsewhere. Even among trajectories that visibly jump at injection, roughly half do not remain in the post-injection basin.

Because persistence is cluster-defined, we also recomputed it under three granularities: K-means $k=12$, K-means $k=4$, and HDBSCAN. The formal persistent-escape ED50, the dose at which persistent escape reaches 50%, is not reached under any of the three definitions.

| dose | persistent escape, $k=12$ | persistent escape, $k=4$ | persistent escape, HDBSCAN | kicked at injection, HDBSCAN |
|---:|---:|---:|---:|---:|
| 20 | 3.5% | 1.5% | 7.0% | 12.0% |
| 50 | 7.0% | 3.0% | 16.5% | 28.5% |
| 80 | 3.5% | 5.0% | 28.5% | 48.0% |
| 120 | 9.0% | 4.5% | 35.5% | 58.0% |
| 160 | 11.5% | 9.5% | 41.0% | 64.5% |
| 200 | 13.0% | 13.5% | 40.5% | 60.0% |
| 300 | 14.0% | 8.5% | 40.0% | 66.5% |
| 400 | 16.0% | 10.0% | 39.5% | 68.5% |

HDBSCAN is the most permissive definition and gives the largest persistent-escape values, but even there the maximum is 39.5%, below the 50% threshold. The conclusion is therefore robust to cluster granularity: O1 adversarial append perturbations create a finite raw-switching dose response, but persistent basin escape is not demonstrated up to 400 injected tokens.

The sparse dose-response pilot remains useful for the qualitative contrast among perturbation contents. In that pilot, D1 neutral switching was already high at 5 tokens and stayed high across the grid, O1 neutral switching stayed near 22-26% from 20 to 400 tokens, and O1 adversarial switching rose from 26% to roughly 50%. The dense rerun shows that the O1 adversarial pattern is real, but it also shows why the endpoint must be named carefully. The defensible headline is **raw ED50 ≈ 40 tokens**, not a persistent-escape barrier height.

![Figure K. **Dense-dose ED50 fit.** O1 adversarial dose-response from the confirmatory rerun, with 8 doses × $n=200$ per cell and one control cell. Black points are observed switching rates with family-cluster-bootstrap 95% CIs; the blue curve is a 4-parameter logistic fit (`a=0.69, d=0.28, b=1.16, ED50=36 tok`); the dashed red line marks the bootstrap-median ED50 = 52 tokens [CI 8.5, 242]. Source: `data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png`.](data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png)

### 5.2 Replace-mode fragility is primarily a memory-policy effect

The original perturbation pilots made O2 and O3 appear nearly maximally fragile. Under the original replace-mode protocol, non-control perturbations overwrite the model output at the injection step, so the next state is conditioned on the injected text rather than on the loop's prior generated state. This produces 94-100% final-cluster disagreement with the paired control trajectory:

| regime | neutral | lorem | adversarial |
|---|---:|---:|---:|
| O2, paraphrase replace | 100% [93-100] | 100% [93-100] | 94% [84-98] |
| O3, summarize-negate replace | 100% [93-100] | 100% [93-100] | 96% [86-99] |

Read alone, these numbers suggest that replace-mode regimes have almost zero injected-token barriers. The overwrite-versus-insert probe shows that this is mostly a memory-policy effect. We re-ran O2 and O3 with the same adversarial doses under two intervention modes:

- **Overwrite:** the original protocol. The injection replaces step 15's output entirely.
- **Insert:** the injected text is prepended to the context for step 15, but the model's own generated output is preserved as the state. The injected text does not remain as the state by construction.

The O2 paraphrase-replace results were:

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80`, overwrite | 0.92 | [0.81, 0.97] |
| `adversarial_insert_dose80` | 0.32 | [0.21, 0.46] |
| `adversarial_dose200`, overwrite | 0.98 | [0.90, 1.00] |
| `adversarial_insert_dose200` | 0.18 | [0.10, 0.31] |

The O3 summarize-negate-replace results were:

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80`, overwrite | 0.90 | [0.79, 0.96] |
| `adversarial_insert_dose80` | 0.18 | [0.10, 0.31] |
| `adversarial_dose200`, overwrite | 0.92 | [0.81, 0.97] |
| `adversarial_insert_dose200` | 0.12 | [0.06, 0.24] |

The overwrite-minus-insert gap is 60-80 percentage points across both regimes and both doses:

| regime | dose | overwrite | insert | overwrite minus insert |
|---|---:|---:|---:|---:|
| O2 | 80 | 0.92 | 0.32 | +0.60 |
| O2 | 200 | 0.98 | 0.18 | +0.80 |
| O3 | 80 | 0.90 | 0.18 | +0.72 |
| O3 | 200 | 0.92 | 0.12 | +0.80 |

Thus most apparent replace-mode perturbation transparency comes from the update rule discarding prior state. Once the perturbation no longer overwrites the loop state, switching falls to 12-32%, below or near the natural stochastic-divergence floor measured for O1. The original O2/O3 result remains an important systems finding, but it should be described as **overwrite-induced state replacement**, not as a discovered low behavioral barrier comparable to the O1 dose-response measurement.

This has a direct engineering analogue. Any architecture that periodically replaces accumulated context with a generated summary, scratchpad, task state, or memory record can fail by promoting untrusted text into the replacement state. In that case, the system has not merely been persuaded by injected text; its previous state has been removed by the memory policy.

---

### Phase B, regime establishment with leakage-aware analysis

### 5.3 Publication-scale runs preserve regime ordering

REPORT5 ran the four diagnostic regimes at publication scale. Operator regimes O1, O2, and O3 used 15 prompt families × 30 ICs × 3 runs, for 1,350 trajectories per regime. Dialog regime D1 used 5 dialog-suitable families × 30 ICs × 3 runs, for 450 trajectories. All four were 40 steps long.

Basin predictability is measured by 5-fold multinomial logistic regression on PCA-10, predicting the trajectory's late-window K-means cluster at $k=12$ from the embedding at step $k$. The late-window cluster is the majority cluster over $t \geq \lceil 0.7T \rceil$. For $T = 40$, this is a 12-step late window. For D1 with role-restricted observables, the latest predictor step is 26, the last agent turn before the late window opens at step 28.

At first exposure we report both the original stratified cross-validation accuracy and the leakage-aware GroupKFold accuracy at $k=10$, where entire prompt families are held out across folds.

| experiment | regime | acc(k=5) | acc(k=10), stratified | acc(k=10), group-aware | leakage delta | acc(k=20) | acc(final) |
|---|---|---:|---:|---:|---:|---:|---:|
| `exp_pub_O1_continue` | O1, contractive | 0.77 | 0.803 | 0.732 | +0.071 | 0.81 | 0.85 |
| `exp_pub_O2_paraphrase_replace` | O2, oscillatory replace | 0.90 | 0.896 | 0.596 | +0.301 | 0.91 | 0.91 |
| `exp_pub_O3_summarize_negate_replace` | O3, absorbing replace | 0.92 | 0.912 | 0.629 | +0.283 | 0.92 | 0.93 |
| `exp_pub_D1_dialog_curious_helpful_v2` | D1, dialogue-state multi-basin | n/a | 0.604 | 0.336 | +0.269 | 0.69 | 0.77 |

The stratified values reproduce the original regime ordering: O2 and O3 lock in very early, O1 is slower but still strongly predictable, and D1 remains the least predictable at early steps. The group-aware analysis changes the interpretation. O1 loses only 7 percentage points when prompt families are held out, while O2, O3, and D1 lose 27-30 percentage points. Thus O1's basin predictability is the most cross-family robust result. For O2, O3, and D1, a substantial part of the original predictability is a family or style fingerprint.

The qualitative regime separation survives. O3 and O2 remain high-recurrence replace-mode regimes, O1 remains a cross-family contractive append regime, and D1 remains a slower, more family-sensitive dialog regime. The main correction is evidential: stratified accuracies should be read as upper bounds, and the leakage-aware columns are the relevant values for cross-family generalization.

![Figure 2. **Basin-predictability across regimes.** Top-1 accuracy for predicting each trajectory's late-window K-means cluster from its embedding at step $k$, using publication-scale runs where available. Source: `data/aggregated/basin_predictability_cross/cross_basin_predictability.png`.](data/aggregated/basin_predictability_cross/cross_basin_predictability.png)

### 5.4 Perturbation pilots separate append from replace

The cross-regime perturbation pilots used 5 families × 5 ICs × 2 runs × 30 steps, for $n=50$ trajectories per condition, except D2 where $n=25$. Switching is final-step K-means cluster disagreement with the paired control trajectory.

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1, contractive append | 0% [0-7] | 24% [14-37] | 18% [10-31] | 54% [40-67] |
| O2, paraphrase replace | 0% [0-7] | 100% [93-100] | 100% [93-100] | 94% [84-98] |
| O3, summarize-negate replace | 0% [0-7] | 100% [93-100] | 100% [93-100] | 96% [86-99] |
| D1, dialogue-state dialog | 0% [0-7] | 76% [62-86] | 54% [40-67] | 60% [46-73] |
| D2, drill-down dialog | 0% [0-13] | n/a | n/a | 64% [44-80] |

This table is now read through §5.2. The O2/O3 values are real measurements of the original overwrite protocol, but they are not fair injected-token barrier estimates. They mostly measure replacement of prior state. O1 shows the cleanest content-dependent append result: in-distribution adversarial text switches more often than neutral or lorem text. D1 is broadly susceptible across perturbation types, consistent with a dialog-state basin that is easier to redirect than O1 but less mechanically overwritten than O2/O3.

![Figure 3. **Perturbation switching by regime.** Grouped bar chart of final-step switching rate, defined as final K-means cluster disagreement with the paired control trajectory. Source: `data/aggregated/perturbation_cross_regime/cross_switching_rates.png`.](data/aggregated/perturbation_cross_regime/cross_switching_rates.png)

### 5.5 Drill-down dialog adds content gravity

D2 is an Explorer-Expert drill-down dialog. Each user turn asks for a deeper, more specific explanation of one concept from the previous expert turn. The exploratory run used 5 topic families × 5 seed topics, for 25 trajectories at 50 steps each. An adversarial perturbation was injected at step 25, drawing expert text from a different topic family, followed by 25 post-injection steps.

The D2 adversarial switch rate was **64%** [44%, 80%]. This is not a publication-scale estimate, and it is not perfectly matched to the D1 timing cells because dose, content, and post-injection horizon differ. The qualitative signal is nevertheless useful: 36% of D2 trajectories did not switch under a late, in-distribution adversarial expert-text injection. The drill-down format imposes content gravity through progressive specialization into a topic tree, which free dialog lacks.

D2 is therefore retained as an exploratory fifth regime. It is distinct from D1 because the dialog state is not only conversational style or recent-context capture; it is also anchored by an accumulating content path.

### 5.6 Injection timing reveals basin hardening

We injected the same perturbation at three times in a 30-step trajectory: D1 neutral at dose 80 and O1 adversarial at dose 200, with $n=50$ per cell.

| inject step | D1, neutral at 80 | O1, adversarial at 200 |
|---:|---:|---:|
| 5 | 72% [58-83] | 60% [46-73] |
| 15 | 78% [65-87] | 54% [40-67] |
| 25 | 52% [38-66] | 62% [48-74] |

D1 shows partial basin hardening. By step 25, the trajectory has more often committed to a dialog-state basin, and switching falls from 78% at step 15 to 52% at step 25. O1 is approximately flat across injection time. The contractive append operator integrates in-domain adversarial text regardless of when it arrives, while D1 becomes harder to redirect late in the trajectory.

![Figure 5. **Switching versus injection time.** Switching rate for injections at steps 5, 15, and 25 of a 30-step trajectory, with $n=50$ per cell and 95% Wilson confidence intervals. Source: `data/aggregated/perturbation_basin_hardening/basin_hardening.png`.](data/aggregated/perturbation_basin_hardening/basin_hardening.png)

---

### Phase C, cluster, granularity, and semantic robustness

### 5.7 Cluster stability and multi-granularity switching

The canonical basin partition is K-means with $k=12$ on PCA-10. To test whether this partition is an artefact of K-means at one value of $k$, we re-clustered publication-scale late-window clouds using HDBSCAN and spectral clustering, then compared partitions with adjusted Rand index. The result is moderate stability overall, with an important exception for O1.

| regime | median ARI vs K-means $k=12$ | HDBSCAN auto-detected $k$ | interpretation |
|---|---:|---:|---|
| O1 contractive | 0.53 | 2 | HDBSCAN sees O1 as one or two large density basins. K-means $k=12$ is a fine sub-partition of a contractive attractor. |
| O2 paraphrase replace | 0.58 | 16 | Replace-mode cluster structure is moderately stable. |
| O3 summarize-negate replace | 0.60 | 16 | Replace-mode cluster structure is moderately stable. |
| D1 dialog | 0.66 | 16 | Highest cross-method stability, but still partly method-dependent. |

For O1, this strengthens the attractor interpretation but qualifies the switching metric. A K-means $k=12$ switch can mean movement between sub-regions of a large contractive basin rather than escape from a HDBSCAN density basin. This is why §5.1 separates raw switching from persistent escape and tests persistence under multiple cluster definitions.

We also recomputed perturbation switching in the four diagnostic perturbation pilots under K-means $k=12$, K-means $k=4$, and HDBSCAN.

| pilot | condition | $k=12$ | $k=4$ | HDBSCAN | summary |
|---|---|---:|---:|---:|---|
| O1 | adversarial | 0.54 | 0.44 | 0.60 | robustly higher than OOD |
| O1 | neutral | 0.24 | 0.18 | 0.38 | low across all |
| O1 | lorem | 0.18 | 0.18 | 0.30 | low across all |
| O2 | adversarial | 0.94 | 0.72 | 1.00 | saturated except coarse $k=4$ |
| O2 | neutral | 1.00 | 1.00 | 1.00 | saturated |
| O2 | lorem | 1.00 | 1.00 | 1.00 | saturated |
| O3 | adversarial | 0.96 | 0.74 | 0.98 | saturated except coarse $k=4$ |
| O3 | neutral | 1.00 | 0.74 | 1.00 | high across all |
| O3 | lorem | 1.00 | 1.00 | 1.00 | saturated |
| D1 | adversarial | 0.60 | 0.50 | 0.40 | granularity-sensitive |
| D1 | neutral | 0.76 | 0.60 | 0.66 | granularity-sensitive |
| D1 | lorem | 0.56 | 0.46 | 0.44 | granularity-sensitive |

The O1 content asymmetry is robust: adversarial switching remains roughly 2-3 times neutral or lorem switching across granularities. O2/O3 overwrite-protocol switching remains high at fine granularities, with some collapse under coarse $k=4$. D1 is the most granularity-sensitive, consistent with its family-leakage and dialog-state dependence.

![Figure H. **Switching rates under alternative cluster granularities.** Perturbation switching rates for D1, O1, O2, and O3 recomputed with K-means $k=12$, K-means $k=4$, and HDBSCAN. Source: `data/aggregated/multi_granularity_switching.png`.](data/aggregated/multi_granularity_switching.png)

### 5.8 Per-cluster semantic inspection

We extracted representative trajectory text from each K-means cluster and had a separate held-out reasoning model characterize the clusters blind to the paper's regime labels. The detailed per-cluster tables are moved to §11.8. The main result is that the four canonical regimes are all multi-cluster at $k=12$, but the semantic axis of clustering differs by regime.

| regime | basin axis | mechanism | taxonomy implication |
|---|---|---|---|
| O1 | register and style | append-mode continuation contracts toward high-probability continuation registers, such as sentimental narrative, policy-discursive exposition, reflective empathic prose, and technical tutorial | label preserved, but specified as register-contractive rather than topic-contractive |
| O2 | seed family and local topic | paraphrase preserves meaning while sanding surface form into conventional paraphrase | period-2 dynamics remain, but basins are family-preserving rather than semantically absorbing |
| O3 | formal template | summarize-then-negate imposes a summary plus antithesis discourse shape while preserving seed-specific content | absorbing means template-absorbing, not content-convergent |
| D1 | dialogue state and recent-context capture | append-mode dialog drifts into conversational acts such as coaching, reassurance, recommendation, journaling, or creative feedback | better described as dialogue-state-driven multi-basin than purely stylistic multi-basin |

The semantic inspection preserves the regime taxonomy but sharpens the mechanism. O1 is the strongest true attractor case, with convergence along register rather than content. O2 and O3 are operator-shaped but content-preserving in different ways. D1 is governed by conversational state and recent-context capture rather than by a stable topic basin.

### 5.9 Per-family heterogeneity

The sparse O1 adversarial dose grid revealed substantial family-level heterogeneity. Each family-dose cell has $n=10$ trajectories, so the table is not a precise family-level ED50 estimate. It is a warning that the population curve mixes different local response profiles.

| family | dose 20 | dose 80 | dose 200 | dose 400 |
|---|---:|---:|---:|---:|
| philosophy_dialog | 0.10 | 0.40 | 0.90 | 0.50 |
| practical_dialog | 0.40 | 0.20 | 0.70 | 0.80 |
| creative_dialog | 0.20 | 0.40 | 0.30 | 0.60 |
| reflective | 0.30 | 0.30 | 0.40 | 0.40 |
| emotional | 0.30 | 0.40 | 0.40 | 0.10 |

`philosophy_dialog` shows a clear threshold-like increase up to dose 200. `practical_dialog` increases after dose 80. `creative_dialog` increases after dose 200. `reflective` is nearly flat, and `emotional` is non-monotone with a low 400-token endpoint. The dense rerun establishes a clean population-level raw dose response, but the wide family-cluster bootstrap interval is consistent with this underlying heterogeneity. Future replications should increase the number of prompt families rather than only the number of ICs per family.

![Figure I. **Per-family O1 adversarial dose-response.** Lines show switching rate versus adversarial dose for each prompt family in the sparse O1 dose experiment, with $n=10$ trajectories per family-dose cell. Source: `data/aggregated/per_family_ed50.png`.](data/aggregated/per_family_ed50.png)

---

### Phase D, embedder and cross-generator checks

### 5.10 Embedding-space invariance

The main measurements use `text-embedding-3-small`. We re-embedded 5,000-step subsamples of representative experiments under two alternatives: `text-embedding-3-large`, a within-vendor scale-up, and `all-mpnet-base-v2`, a local cross-architecture sentence-transformer. We then recomputed recurrence, late sharpness dimension, and basin predictability.

The rank-order result is selective. Basin predictability is the most embedder-invariant diagnostic, recurrence is partially invariant, and sharpness dimension is not invariant.

| diagnostic | Spearman rank correlation vs `text-embedding-3-large` | Spearman rank correlation vs `all-mpnet-base-v2` | interpretation |
|---|---:|---:|---|
| recurrence rate | +0.60 | +0.60 | high/low split between replace-mode and append/dialog regimes is preserved |
| basin predictability acc(k=10) | +0.80 | +1.00 | strongest embedder-invariant diagnostic |
| sharpness_dim_late | -0.40 | +0.00 | embedding-specific and not load-bearing |

The load-bearing taxonomy distinction between replace-mode regimes and append/dialog regimes survives embedder substitution. O2 and O3 remain high-recurrence and high-predictability relative to O1, D1, and D2. The fine-grained sharpness-dimension ordering should be interpreted only within the original `text-embedding-3-small` measurement pipeline.

![Figure 14. **Embedding-model ablation.** Bar plots compare three diagnostics across regimes after re-embedding subsamples with `text-embedding-3-small`, `text-embedding-3-large`, and `all-mpnet-base-v2`. Source: `data/aggregated/embedding_ablation/comparison.png`.](data/aggregated/embedding_ablation/comparison.png)

The n = 4 cross-metric correlations among recurrence, switching, sharpness, and lock-in are descriptive only and are reported in §11.13 rather than used as inferential evidence here.

### 5.11 Cross-model thesis verification

We also ran a cross-generator audit by substituting `gpt-4.1-nano` for `gpt-4o-mini` in the regime-level experiment set and evaluating six machine-checkable thesis predicates. This is a qualitative audit of the regime taxonomy, not a replication of the dense ED50 endpoint, the persistence endpoint, or the overwrite-versus-insert mechanism.

The regime-level predicates all passed on both generators:

| ID | audited claim | `gpt-4o-mini` | `gpt-4.1-nano` | verdict |
|---|---|---|---|---|
| T1 | recurrence ordering separates replace from append/dialog | O1 0.272, O2 0.834, O3 0.905, D1 0.146 | O1 0.393, O2 0.840, O3 0.866, D1 0.168 | PASS on both |
| T2 | replace-mode perturbation switching remains high under original overwrite protocol | O2 adv 0.94, O3 adv 0.96 | O2 adv 0.94, O3 adv 0.88 | PASS on both |
| T3 | O1 neutral and lorem remain in drift-floor band | control 0.00, neutral 0.24, lorem 0.18 | control 0.00, neutral 0.22, lorem 0.18 | PASS on both |
| T4 | O1 adversarial switching exceeds O1 lorem switching | adv 0.54 vs lorem 0.18 | adv 0.38 vs lorem 0.18 | PASS on both |
| T5 | D1 neutral switching exceeds 0.30 | neutral 0.76 | neutral 0.80, lorem 0.94 | PASS on both |
| T6 | publication-scale verdict labels match expected H1a/H1b tuples | expected tuples | identical tuples | PASS on both |

The structural taxonomy is preserved. Replace-mode regimes remain high-recurrence and high-switching under the original overwrite protocol. O1 remains content-sensitive, with adversarial text exceeding lorem text. D1 remains broadly susceptible to perturbation.

The magnitude shifts are also informative. `gpt-4.1-nano` has a smaller O1 adversarial-vs-lorem margin, +0.20 compared with +0.36 on `gpt-4o-mini`, suggesting shallower contractive basins. D1 lorem switching rises to 0.94 on `gpt-4.1-nano`, suggesting looser dialog-state anchoring.

The audit does **not** replicate the full headline endpoint. The following claims remain established only for the `gpt-4o-mini` experiments reported above:

| claim | replicated on `gpt-4.1-nano`? | status |
|---|---|---|
| dense O1 adversarial $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens | no | not rerun in the cross-generator thesis audit |
| O1 natural stochastic-divergence floor of 34.7% | no | not rerun in the cross-generator thesis audit |
| persistent escape not reaching 50% up to 400 tokens | no | not rerun in the cross-generator thesis audit |
| overwrite-versus-insert gap of 60-80 percentage points for O2/O3 | no | not rerun in the cross-generator thesis audit |
| V* density-landscape sensitivity and ordinal stability | no | not rerun in the cross-generator thesis audit |
| regime-level qualitative predicates T1-T6 | yes | passed on both generators |

The correct interpretation is therefore narrow but useful: the **regime-level qualitative claims** generalize to `gpt-4.1-nano`; the **dense endpoint calibration** remains a `gpt-4o-mini` result until rerun directly.

---

### Phase E, secondary analyses

### 5.12 Density landscapes are descriptive, not calibrated

The $V(x) = -\log \hat{\rho}(x)$ density-landscape analyses visualize where trajectory clouds spend time in a joint PCA-2 projection. They are useful descriptive summaries of geometry, but they are not calibrated barrier-height estimates and they do not validate the token ED50 values in §5.1.

The main limitation is parameter sensitivity. For the O1 perturbation pilot, we recomputed $V^\star$ across 45 combinations of KDE bandwidth, grid resolution, and basin count. Per-condition coefficients of variation ranged from 14% to 24%. A single numerical $V^\star$ value is therefore not stable enough to quote as a calibrated barrier.

The ordinal pattern was more stable. Across the 45 parameter combinations, control had the highest $V^\star$ in 98% of combinations, adversarial had the lowest $V^\star$ in 89%, and neutral and lorem occupied the middle. This supports a weak geometric statement: the density-landscape summaries preserve a robust rank ordering within the O1 perturbation pilot. It does not support a quantitative $V^\star$ to ED50 conversion.

This distinction is especially important for replace-mode regimes. O2 and O3 can show high geometric separation while also showing high overwrite-protocol switching, because the perturbation and memory policy can create or occupy a different basin rather than cross a pre-existing ridge. Full $V^\star$ tables, RG merge-distance tables, and the parameter-grid sensitivity outputs are moved to §11.11.

![Figure 6. **Representative PCA-2 density landscapes for the O1 perturbation pilot.** Panels show $V(x) = -\log \rho(x)$ for control, neutral, lorem, and adversarial conditions. Source: `data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png)

### 5.13 Why exactly five regimes?

The five-regime taxonomy is not recovered cleanly by unsupervised clustering of bulk diagnostics alone. We assembled five-dimensional diagnostic vectors containing recurrence rate, late sharpness dimension, late $\lambda_1$, basin-predictability accuracy at $k=10$, and adversarial switching rate. Internal validation indices did not select a single cluster count matching the five labels: silhouette favored two clusters, Calinski-Harabasz favored seven, and Davies-Bouldin favored six.

The substantive result is that bulk diagnostics separate O2 and O3 from the append/dialog regimes, but they do not cleanly separate O1 from D1. O1 and D1 have similar recurrence, contraction, and basin-predictability values at this diagnostic resolution. The perturbation protocol is what separates them: O1 shows content-dependent adversarial raw switching with out-of-distribution resistance, while D1 is broadly susceptible to dialog-state redirection and hardens with time. D2 is then distinguished by drill-down content gravity.

The five-way taxonomy is therefore supported by the union of bulk diagnostics and perturbation endpoints, not by either alone. Full unsupervised-clustering matrices, validation indices, and feature-space plots are moved to §11.12.

---

At matched reduced scope, D1 showed narrower temperature variation than O1: D1 basin predictability at $k=10$ stayed in a 0.57-0.61 band, while O1 ranged from 0.52 to 0.65. However, the O1 reduced-scope T=0.8 cell was 28 percentage points below the publication-scope T=0.8 anchor, 0.52 versus 0.80, so O1 absolute temperature values are scope-confounded. The full temperature sweep is retained as exploratory secondary material in §11.10.
