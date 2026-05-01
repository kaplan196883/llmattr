## 5. Results

The Results section is organised in four bands per the
revision-driven hierarchy (review Writing & Structure #7):

- **§5.A Primary results**, load-bearing experiments tied to the
  decision-grade endpoints in §4.13 (regime establishment,
  perturbation signatures and sparse ED50, perturbation timing,
  exploratory D2).
- **§5.B Stress tests of primary results**, the revision's
  empirical defenses (group-aware CV, cluster-stability,
  multi-granularity switching, semantic basin inspection,
  per-family heterogeneity, persistence test, V* sensitivity).
- **§5.C Secondary analyses**, temperature sweep, embedder
  invariance, cross-metric correlations, unsupervised regime
  recovery, cross-generator audit.
- **§5.D Supplementary material**, pilot history and engineering
  documentation moved to the supplementary appendix at the end of
  the paper.

(Subsection numbers below preserve the manuscript's discovery-
order numbering for cross-reference stability; the §5.A/B/C/D
labels are added as narrative dividers.)

---

### §5.A, Primary results

In append-mode continuation, in-distribution adversarial text produced
a reproducible raw-switching dose response with $\mathrm{ED50}_{\mathrm{raw}}
\approx 40$ tokens, but this was not durable basin redirection: paired
controls already diverged at ${\approx}35\%$, net switching saturated
at $+32$ percentage points, and persistent escape did not reach $50\%$
at any tested dose up to 400 tokens. Replace-mode loops showed
near-saturated raw switching in the original perturbation pilots, but
overwrite-versus-insert probes attributed most of that apparent
fragility to the context-update rule discarding prior state rather than
to a low injected-token barrier. The remaining results establish the
regime taxonomy at publication scale, quantify the dose and timing
dependence of perturbations, and then test whether the conclusions
survive leakage-aware cross-validation, alternative cluster
granularities, persistence criteria, density-landscape sensitivity,
embedder ablations, and within-vendor generator replication. The rest
of §5 stress-tests these claims from the primary measurements outward.

For the full row-by-row audit of primary endpoints, uncertainty
estimates, source files, and caveat flags, see Extended Data Table 1
(§11.3). A compact cross-regime lookup table is provided as Extended
Data Table 2 (§11.4); the main text introduces each measurement in
sequence.

### 5.1 Pilot runs validate the measurement pipeline

Three early pilot runs (`exp_default`, `exp_long`, `exp_noclip`)
validated the pipeline end-to-end and identified the contractive
basin profile that became O1. **Full pilot history moved to §11.7**;
the publication-scale story below subsumes these pilot findings.

### 5.2 Small-N runs identify candidate regimes

Eight pilot operator/dialog experiments at $n \approx 50$ trajectories
identified the diagnostic regime taxonomy (O1 contractive, O2
oscillatory, O3 absorbing, D1 dialogue-state-driven multi-basin, D2 drill-down)
plus boundary cases (O3b, O4, D3). **Full taxonomy table and
boundary-case discussion moved to §11.7**; every regime claim in §5.3
onward is grounded in publication-scale data.

### 5.3 Publication-scale runs preserve regime ordering

REPORT5 ran the four diagnostic regimes at full scale, with sample
size differing by regime family (per §4.2): operator regimes O1 / O2
/ O3 use 15 prompt families × 30 ICs × 3 runs = 1,350 trajectories
per regime; dialog regime D1 uses 5 dialog-suitable families × 30
ICs × 3 runs = 450 trajectories. All four are 40 steps long. Basin
predictability, 5-fold CV multinomial logistic regression on PCA-10,
predicting the late-window K-means cluster (k=12) from the embedding
at step k, gives a clean per-regime ordering:

| experiment | regime | observable | acc(k=5) | acc(k=10) | acc(k=20) | acc(k=final) |
|---|---|---|---:|---:|---:|---:|
| `exp_pub_O1_continue` | contractive | context_tail | 0.77 | 0.80 | 0.81 | 0.85 |
| `exp_pub_O2_paraphrase_replace` | oscillatory | context_tail | 0.90 | 0.90 | 0.91 | 0.91 |
| `exp_pub_O3_summarize_negate_replace` | absorbing | context_tail | 0.92 | 0.92 | 0.92 | 0.93 |
| `exp_pub_D1_dialog_curious_helpful_v2` | multi-basin | context_tail | n/a | 0.61 | 0.69 | 0.77 |

The "final" cluster is the trajectory's majority cluster over the
late window `t ≥ ⌈0.7T⌉` per §4.5.3. For T=40 this gives a 12-step
late window; for the dialog regime D1 with role-restricted observables
the latest predictor step is 26 (the last agent turn before the late
window opens at step 28).

(Numbers measured from
`data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`,
recursive regime only, canonical observable per regime. D1's step-5
cell is `NaN` because the joint k-means at step 5 has too few class
members for any k-fold ≥ 2 even after the adaptive fallback to
`n_splits = smallest_class_size`; it stabilizes by step 10.)

Three orderings emerge cleanly:

- **O3 absorbing** locks in earliest (step 5 ≈ final accuracy 0.89 →
  0.91). Once the absorbing sink is reached, the remainder of the
  trajectory is statistically frozen.
- **O2 oscillatory** also locks in fast (0.88 → 0.90). The 2-cycle is
  basin-stable: knowing which arm of the cycle a trajectory is on at
  step 5 is enough to predict its terminal arm.
- **O1 contractive** and **D1 multi-basin** are slower and have more
  headroom: O1 climbs from 0.77 to 0.85, D1 from 0.61 (step 10) to
  0.77 (final). The dialog regime in particular shows the *most* room
  for early-stage style-basin reorganization.

The four regimes survive scale: their qualitative ordering on every
diagnostic is preserved, and the within-regime variability (across
families and ICs) is much smaller than between-regime variation. **H4
is supported.**

![Figure 2. **Basin-predictability across regimes.** Two-panel plot of top-1 accuracy for predicting each trajectory's late-window K-means cluster from its embedding at step $k$, using publication-scale runs where available. The left panel shows acc($k$) curves; the right panel compares seed-step and final-step accuracy. O2/O3 have high early predictability, O1 increases more gradually, D1 is lower and slower, and D2 is underpowered in this analysis. Source: `data/aggregated/basin_predictability_cross/cross_basin_predictability.png`.](data/aggregated/basin_predictability_cross/cross_basin_predictability.png)

### 5.4 Temperature sweep separates O1 and D1

> **Caveat.** The T-sweep cells in this section
> are at **reduced scope** (n=150) rather than publication scope
> (n=1350 for O1, n=450 for D1). The reduced-scope T=0.8 cell sits
> 28 pct pts below the publication-scope T=0.8 anchor (0.52 vs 0.80
> for O1 acc(k=10)), meaning that **scope, not temperature,
> dominates the variance** in O1 basin-predictability across the
> sweep. The narrower 4 pct pt span we observe for D1 across T is
> still suggestive of T-stability, but the operator-regime
> T-sensitivity claim should be read as exploratory until a
> publication-scope T-sweep is run. We retain the data because the
> *qualitative* contrast (D1 narrower than O1 across T at *matched*
> reduced scope) is informative, but the absolute numbers are
> N-confounded.

We ran a temperature sweep (T ∈ {0.3, 0.6, 0.8, 1.2}) for D1 and O1 at
reduced scope (5 families × 15 ICs × 2 runs × 30 steps = 150
trajectories per cell, except the D1 T=0.8 cell which reuses the
full-scope publication run at 450 trajectories). Predictor at step
k=10 of 30, classifier trained on PCA-10 of the canonical
`context_tail` observable, target: K-means cluster (k=12) at the
late window ($t \geq 0.7\,T_{\mathrm{traj}}$). We report `acc(k=10)` rather than `acc(k=5)`
as the headline number because step 10 has the most consistent
coverage across all 8 T-sweep cells (some D1 reduced-scope cells
have no valid late-window classifier at very early steps after
singleton-cluster trajectories are dropped).

**O1 basin predictability acc(k=10) by T** (context_tail, top-1):

| T | 0.3 | 0.6 | 0.8 | 1.2 |
|---|---:|---:|---:|---:|
| acc(k=10) | 0.65 | 0.62 | 0.52 | 0.64 |

**D1 basin predictability acc(k=10) by T** (context_tail, top-1):

| T | 0.3 | 0.6 | 0.8 | 1.2 |
|---|---:|---:|---:|---:|
| acc(k=10) | 0.61 | 0.58 | 0.61 | 0.57 |

O1 shows a non-monotonic dip at T=0.8 (acc=0.52, the lowest cell) and
recovers somewhat at T=1.2 (0.64). Higher temperature broadens the
contractive basin and makes the late state harder to anchor at step
10; the T=0.8 dip is the cleanest cell-level signal of T-sensitivity
in the operator regimes. The full-scope publication run at the
canonical T=0.8 (`exp_pub_O1_continue`, n=1350) reaches acc(k=10) =
0.80 (§5.3); the reduced-scope T=0.8 cell sits 28 pct pts below
that, indicating the reduced N is the dominant source of the
operator-regime variance in this section.

D1 stays in a tight 0.57-0.61 band across all four temperatures,
a span of only **4 pct pts** vs O1's 13-pct-pt span. Once the dialog
regime locks into its dialogue-state basin, temperature alone does not
unlock it. The full-scope D1 anchor (T=0.8, n=450) reaches acc(k=10)
= 0.61, matching the reduced-scope T=0.3 and T=0.8 cells exactly,
i.e., D1's basin predictability is not just T-stable but also
**N-stable** at this scale, supporting the claim that the dialog
basin is found early and held.

This is the first quantitative diagnostic distinguishing the regimes
beyond visual inspection: D1 has 3× narrower T-variance in
basin-predictability acc than O1 over the same temperature range
on matched scope.

(All measured cells in this section are reproducible from
`data/aggregated/t_sensitivity_cross_regime/cross_t_sensitivity.csv`
filtered to `observable=context_tail` and `step=10`. See
`RESULTS.md` for cell-by-cell verification against this section.)

### 5.5 Perturbation pilots separate append from replace

![Figure 3. **Perturbation switching by regime.** Grouped bar chart of final-step switching rate, defined as final K-means cluster disagreement with the paired control trajectory; injection occurs at step 15 of a 30-step run, with $n=50$ trajectories per cell except D2 ($n=25$). O2/O3 show high switching for all perturbation types, O1 shows higher switching for adversarial than neutral/lorem perturbations, and D1/D2 fall between these cases. Source: `data/aggregated/perturbation_cross_regime/cross_switching_rates.png`.](data/aggregated/perturbation_cross_regime/cross_switching_rates.png)

For each of the four diagnostic regimes plus D2 (drill-down), we ran a
perturbation pilot at 5 families × 5 ICs × 2 runs × 30 steps = 50
trajectories per condition × 4 conditions. Switching rates with Wilson
95% confidence intervals (n=50 except D2 where n=25):

| regime | control | neutral | lorem | adversarial |
|---|---|---|---|---|
| O1 (contractive) | 0% [0-7] | 24% [14-37] | 18% [10-31] | 54% [40-67] |
| O2 (oscillatory replace) | 0% [0-7] | 100% [93-100] | 100% [93-100] | 94% [84-98] |
| O3 (absorbing replace) | 0% [0-7] | 100% [93-100] | 100% [93-100] | 96% [86-99] |
| D1 (multi-basin dialog) | 0% [0-7] | 76% [62-86] | 54% [40-67] | 60% [46-73] |
| D2 (drill-down dialog) | 0% [0-13] | n/a | n/a | 64% [44-80] |

(D2 was only tested with control + adversarial conditions, and at a
50-step horizon with override at step 25, see §5.8.)

Replace-mode operators are perturbation-transparent: 94-100% switching
under any non-control condition. The append-mode contractive regime O1
shows clear conditional sensitivity: 54% under in-distribution
adversarial, but only 18-24% under out-of-distribution random or
neutral text. The dialog regimes sit between these extremes, with D1
showing higher switching under all conditions and D2, the structured
drill-down, resisting more strongly.

**H3 is supported with refinement**: the qualitative split between
"replace-transparent / append-resistant" is clear, but the magnitude of
resistance depends on the type of perturbation, not just its presence.

### 5.6 Dose response depends on perturbation content

We varied the perturbation length 20/80/200/400 tokens for D1 (neutral)
and O1 (neutral and adversarial). D1 with neutral was additionally
tested at sub-saturation doses 5/10/15:

**D1 / neutral** (n=50 per cell; Wilson 95% CI half-width ~13 pct pts):

| dose (tokens) | 5 | 10 | 15 | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|---:|---:|---:|
| switch | 62% | 68% | 70% | 72% | 76% | 70% | 66% |

D1 saturates at sub-token doses. The raw-switching barrier height is essentially zero, any 5-token coherent interrupt flips the
dialog basin. The flat-from-saturation curve is consistent with our
"dialog basin is dialogue-state-driven, not content-bound" interpretation.

**O1 / neutral** (off-distribution; n=50 per cell; CI half-width ~12 pct pts):

| dose (tokens) | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 22% | 26% | 24% | 24% |

Flat at the out-of-distribution drift floor of ~24% across the entire dose range.
This is the "noise rate", out-of-distribution text simply cannot move
the contractive basin no matter the dose.

**O1 / adversarial** (in-distribution; n=50 per cell; CI half-width ~13 pct pts):

| dose (tokens) | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 26% | 34% | 54% | 48% |

Clear graded response. In this pilot the 50%-switching dose lies
between 80 and 400 tokens of in-distribution text, the n=50 cells
do not localize it more precisely (see Wilson CIs in Figure 4 and
the dense-dose rerun in §5.6.1). To our knowledge this is the first
**reported** raw-switching dose-response barrier-height measurement for an LLM
loop on this generator and prompt template; we do not claim
priority, only that systematic dose-response measurement of barrier
height in this form has not been a focus of prior recursive-loop
work. The same architecture
(O1 continue) produces qualitatively different dose-response curves
depending on whether the perturbation is in-distribution.

![Figure 4. **Dose-response switching curves.** Switching rate is plotted against perturbation length in tokens for D1/neutral, O1/neutral, and O1/adversarial conditions; each point has $n=50$ trajectories and 95% Wilson confidence intervals, with injection at step 15. O1/neutral remains near 20-26% across tested doses, O1/adversarial rises toward roughly 50% with a non-monotone 400-token endpoint, and D1/neutral is high even at the smallest tested doses. Source: `data/aggregated/perturbation_dose_response/dose_response.png`.](data/aggregated/perturbation_dose_response/dose_response.png)

#### 5.6.1 Dense rerun localizes raw ED50

**Lede.** The dense rerun establishes a clean raw-switching dose response in O1 adversarial append-mode continuation ($\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, with three independent fitting methods agreeing to within $\pm 8$ tokens) but rejects the stronger interpretation: the persistent-escape endpoint is not reached at any tested dose up to 400 tokens, the raw plateau sits at $\approx 0.67$ rather than 1.0, and the net effect over the stochastic floor saturates at +32 percentage points. The remainder of this subsection details the rerun's preregistration, configuration, and per-method estimates.

**Engineering scale calibration.** As a rough orientation: 40 tokens is comparable to a short repository comment, a targeted test-failure note, a small README paragraph, or a user correction naming a specific file and test. Thus the measured $\mathrm{ED50}_{\mathrm{raw}}$ is not a large-context phenomenon; small in-domain snippets can measurably alter raw terminal state, even though net and persistent-escape thresholds are not reached in the tested range.

The sparse-data dose-response above was n=50/cell, an
underpowered pilot. The dense-dose rerun was committed as a
frozen pre-registration before the run started: n=200/cell
(= 5 families × 10 ICs × 4 runs); 8 dose conditions + 1 control ×
200 = 1,800 trajectories total via
`configs/perturbation/O1_ed50_dense.yaml` and
`scripts/fit_ed50_hierarchical.py`. The pre-registered analysis
included 4 control runs/IC to enable a control-vs-control natural-
floor estimate. The run completed cleanly; results below.

**Dense O1 / adversarial dose-response** (n=200 per cell, control n=200):

*Table, Wilson 95% CIs on the dense-rerun O1 adversarial dose-response.*

| dose (tokens) | switch rate | Wilson 95% CI |
|---|---:|---|
| control | 0.000 | [0.000, 0.019] |
| 20 | 0.415 | [0.349, 0.484] |
| 50 | 0.510 | [0.441, 0.578] |
| 80 | 0.575 | [0.506, 0.641] |
| 120 | 0.630 | [0.561, 0.694] |
| 160 | 0.605 | [0.536, 0.670] |
| 200 | 0.620 | [0.551, 0.684] |
| 300 | 0.655 | [0.587, 0.717] |
| 400 | 0.670 | [0.602, 0.731] |

**ED50 estimates** (consistent across methods):

*Table, ED50 method comparison: 4PL fit, mixed-effects GLMM, and family-cluster bootstrap.*

| method | ED50 (tokens) | uncertainty |
|---|---:|---|
| 4PL pooled fit | 36 | (point) |
| Mixed-effects logistic GLMM | 41 | (point, log10-dose slope) |
| Family-cluster bootstrap median | 52 | 95% CI [8.5, 242] |

The point estimates from three independent methods cluster in the
**~36-52-token range**, substantially below an earlier sparse-data
estimate of approximately 150 tokens, which the dense rerun reveals
was an artifact of the coarse dose grid. The bootstrap CI remains
wide because only 5 prompt families means family-level resampling
has heavy tails; widening the family count in a future replication
would tighten the CI.

**Two structurally important findings beyond the point estimate:**

1. **The curve plateaus at ~67%, not 1.0.** The 4PL upper asymptote is
   $a = 0.69$. At infinite adversarial dose, only ~69% of trajectories
   switch under the current perturbation protocol. This means **a
   substantial subpopulation (~31%) is "hardened" against in-
   distribution adversarial nudges in this dose range**. Whether this
   reflects per-trajectory stochastic robustness, family-specific
   barrier structure (§5.15), or a deeper mechanistic split is an
   open question.

2. **The control-vs-control natural floor is 34.7%** [31.0%, 38.6%]
   across $n=600$ ordered control-control pairs (4 control runs/IC ×
   pairwise comparisons). Two trajectories with the *same* family /
   IC seed but different generation RNG end up in different K-means
   clusters 35% of the time *purely from stochastic divergence*, with
   no perturbation involved. **Net adversarial effect** (observed
   switching minus natural floor):

   | dose | observed | natural floor | net adversarial effect |
   |---|---:|---:|---:|
   | 20 | 0.415 | 0.347 | **+0.068** |
   | 50 | 0.510 | 0.347 | **+0.163** |
   | 80 | 0.575 | 0.347 | **+0.228** |
   | 200 | 0.620 | 0.347 | **+0.273** |
   | 400 | 0.670 | 0.347 | **+0.323** |

   Under the strictest reading, *the adversarial dose at which the
   net effect (above natural divergence) reaches 50% switching*, no
   such threshold exists in the tested range; the highest net effect
   is **+32 pp at dose 400**, well below 50 pp. The 50%-of-population
   crossing of the *raw* curve happens between dose 20 and dose 50,
   but a substantial fraction of that "switching" is confounded by
   stochastic baseline divergence.

**What the dense-rerun headline claim is, post-correction.** O1
under in-distribution adversarial perturbation has a finite,
graded-response dose-response with **ED50 (raw switching) ≈ 40
tokens**, an upper asymptote of ~67% (substantial non-switching
subpopulation), and a natural stochastic-divergence floor of ~35%
that consumes most of the apparent effect at low doses. The "barrier
height in tokens" is therefore best read as a **graded-response
parameter**, not a sharp threshold; the original "~150 token barrier"
claim is replaced by this richer characterisation. We do *not*
claim a localised barrier in the strict §3.1.1 sense (the 95%
bootstrap CI on ED50 spans an order of magnitude), but we do claim a
finite, monotone dose-response with the parameters above.

![Figure K. **Dense-dose ED50 fit.** O1 adversarial dose-response from the confirmatory rerun (8 doses × $n=200$/cell, where $n=200 = $ 5 families × 10 ICs × 4 runs; 9 cells × 200 = 1,800 trajectories). Black points are observed switching rates with family-cluster-bootstrap 95% CIs; the blue curve is a 4-parameter logistic fit (`a=0.69, d=0.28, b=1.16, ED50=36 tok`); the shaded blue band is the 95% bootstrap envelope on ED50; the dashed red line marks the bootstrap-median ED50 = 52 tokens [CI 8.5, 242]. The curve plateaus at ~67%, not 1.0, there is a non-switching subpopulation. Source: `data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png`.](data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png)

### 5.7 Injection timing reveals basin hardening

We injected the same perturbation (D1: neutral @80, O1: adversarial @200)
at three different steps of a 30-step trajectory (n=50 per cell):

*Table, Switching rate by injection step for D1 (neutral @80) and O1 (adversarial @200).*

| inject step | D1 (neutral @80) | O1 (adversarial @200) |
|---:|---:|---:|
| 5 | 72% [58-83] | 60% [46-73] |
| 15 | 78% [65-87] | 54% [40-67] |
| 25 | **52% [38-66]** | 62% [48-74] |

D1 shows partial **basin hardening**: by step 25 the trajectory has
committed to its style basin and resists more strongly (52% vs 78% at
step 15). The basin gets harder to leave as the trajectory ages.

O1 is essentially flat across injection time, the contractive
averaging operator integrates whatever is in context regardless of when
it arrived. **The two regimes have qualitatively different
time-dependence** in their barrier structure.

![Figure 5. **Switching versus injection time.** Switching rate is plotted for injections at steps 5, 15, and 25 of a 30-step trajectory, with $n=50$ per cell and 95% Wilson confidence intervals. D1/neutral at dose 80 declines at the latest injection step, while O1/adversarial at dose 200 is approximately flat across injection times. Source: `data/aggregated/perturbation_basin_hardening/basin_hardening.png`.](data/aggregated/perturbation_basin_hardening/basin_hardening.png)

### 5.8 Drill-down dialog adds content gravity

We introduced a new dialog regime: an **Explorer-Expert** drill-down
dialog where each user turn asks for a deeper, more specific
explanation of one concept from the previous expert turn. 5 topic
families × 5 seed topics = 25 trajectories at 50 steps each.

Adversarial perturbation injected at step 25, drawing from a *different
topic family*'s expert text, with 25 steps of post-injection
relaxation. Switch rate: **64%**.

Compared to D1 free dialog at the same setup (matched-relaxation D1
inject_t25 = 52%, though the doses and content differ slightly), D2's
64% under late-injection adversarial is *higher*, but compared to the
D1 pilot's 78% at step 15 with shorter relaxation, D2 shows similar or
weaker resistance. The fair comparison is at matched (override step,
relaxation horizon):

*Table, Override-vs-relaxation matched comparison: D1 free dialog vs D2 drill-down.*

| regime | override | relaxation | adversarial switch |
|---|---:|---:|---:|
| D1 free | 25 | 4 steps | 52% |
| D2 drill-down | 25 | 25 steps | 64% |

The geometric / linguistic story is: drill-down imposes content gravity
(progressive specialization into a topic tree) that free dialog lacks.
Even when the adversarial injection text is in-distribution drilled-down
expert prose, 36% of D2 trajectories pull back toward the original
specialization line. **D2 is a measurably distinct regime from D1**,
and we identify it as the fifth member of the taxonomy.

### 5.9 Cross-experiment aggregation

Seven standalone aggregator scripts produce the cross-regime comparison
artifacts that anchor the figures in this paper:

- `scripts/aggregate_basin_predictability.py`, overlay the basin
  predictability curves of the four diagnostic regimes onto a single
  axis. Output: `data/aggregated/basin_predictability_cross/`.
- `scripts/aggregate_t_sweep.py`, combine the D1 T-sweep CSVs.
  Output: `data/aggregated/t_sweep_basin_predictability/`.
- `scripts/aggregate_o1_d1_t_sensitivity.py`, side-by-side O1-vs-D1
  basin-predictability-vs-T comparison. Output:
  `data/aggregated/t_sensitivity_cross_regime/`.
- `scripts/aggregate_perturbation_cross_regime.py`, switching rates +
  relaxation curves across all 5 perturbation pilots (D1, O1, O2, O3, D2).
  Output: `data/aggregated/perturbation_cross_regime/` including the
  4×5 condition × regime grouped bar chart.
- `scripts/aggregate_dose_response.py`, dose-response curves across
  D1+O1 dose experiments, log-scale dose axis with 95% Wilson CI bars.
  Output: `data/aggregated/perturbation_dose_response/`.
- `scripts/aggregate_basin_hardening.py`, injection-time × switching
  curves for D1 + O1, with the basin-hardening interpretation.
  Output: `data/aggregated/perturbation_basin_hardening/`.
- `scripts/aggregate_perturbation_geometric_barriers.py`, combine the
  per-pilot `geodesic_barriers_summary.csv` (V*) and
  `rg_dendrogram_summary.csv` (Ward merge distance) into the wide
  regime × condition tables shown in §5.10. Output:
  `data/aggregated/perturbation_geometric_barriers/`
  (`v_star_table.csv`, `rg_merge_table.csv`, `geometric_barriers_long.csv`).

Each script reads only the per-experiment CSV outputs and is fully
deterministic, re-running them produces byte-identical figures. They
are kept separate from the per-experiment pipeline to allow incremental
re-aggregation as new experiments land.

### 5.10 Geometric barriers from V(x) = −log ρ(x)

**How to read this section.** The figures below visualize the empirical density of trajectory clouds in the joint PCA-2 embedding via $V(x) = -\log \hat\rho(x)$. They are descriptive summaries of where trajectories spent time, NOT independent quantitative validation of the behavioral barrier estimates from §5.6.1. The geometric $V^\star$ values that follow are sensitive to KDE bandwidth, grid resolution, and basin-detection parameters (CV $14$-$24\%$ across a 45-point parameter grid; see §5.16). The rank ordering of conditions is mostly stable across parameter settings, but absolute $V^\star$ magnitudes are not, and they should not be quoted as token-equivalent barrier heights. The caveat box immediately below restates these four points and adds the basin-creation-vs-barrier-crossing distinction that governs which regimes the $V^\star$↔ED50 comparison is even meaningful for.

> **Caveat.** The geometric $V^\star$ values
> reported in this section are **descriptive**, not an independent
> quantitative validation of the behavioral barrier, but the
> *ordinal ranking* of conditions by $V^\star$ is robust to analyst
> choices (see §5.16 below for the parameter-grid sensitivity
> result). In particular, for replace-mode regimes (O2/O3) the
> geometric $V^\star$ is *high* while the behavioral switching rate
> is saturated near 100%, a mechanistic mismatch we attribute to
> *basin creation* (the kick reshapes the density landscape so the
> post-kick cloud occupies a different region) rather than *barrier
> crossing*. The two mechanisms produce opposite-sign predictions
> for the relationship between $V^\star$ and switching rate. The
> $V^\star$↔ED50 correlation should therefore be computed only on
> regimes where the *barrier crossing* mechanism is hypothesized
> (i.e., O1 / D1, not O2 / O3 where basin creation is suspected).
> Numerical $V^\star$ values are sensitive to KDE bandwidth, grid
> resolution, and basin-detector thresholds (CV ~14-24% across a
> 45-parameter grid; see §5.16), but the ordinal claim
> (control > neutral / lorem > adversarial in $V^\star$) is stable
> across 89-98% of parameter combinations.

![Figure 6. **PCA-2 density landscapes for the O1 perturbation pilot.** Four panels show $V(x) = -\log \rho(x)$, computed from smoothed empirical density on the joint PCA-2 embedding for control, neutral, lorem, and adversarial conditions. Low $V$ regions correspond to high-density parts of the observed trajectory cloud. Neutral and lorem are visually closer to control than the adversarial condition, which redistributes density across the PCA-2 plane. Source: `data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png)

![Figure 7. **Geodesic summaries on the O1 PCA-2 density landscape.** Each panel shows the per-condition $V(x) = -\log \rho(x)$ contour map, detected density peaks marked by stars, and Dijkstra paths between peak pairs on the $V$ grid. The label $V^\star$ is the maximum $V$ value along each plotted path. These values are descriptive summaries of the PCA-2 density geometry and are aggregated by condition in §5.10. Source: `data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png)

![Figure 8. **Flow-field and geodesic overlays for O1 perturbations.** Each panel overlays three quantities on PCA-2: the $V(x) = -\log \rho(x)$ contour map, streamlines from binned one-step displacement vectors, and Dijkstra paths between detected density peaks with $V^\star$ labels. The panels compare how the observed displacement field and density geometry vary across control, neutral, lorem, and adversarial perturbations. Source: `data/exp_perturb_O1_pilot/reports/perturbation/flow_skeleton_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/flow_skeleton_pca.png)

![Figure 9. **Post-injection relaxation curves for O1.** Line plot of mean PCA-10 distance from each trajectory's pre-perturbation control centroid, by step and perturbation condition. The dashed line marks injection at step 15. After injection, neutral and lorem move closer to the control trajectory than adversarial, which remains farther from the pre-injection centroid. Source: `data/exp_perturb_O1_pilot/reports/perturbation/relaxation_curves.png`.](data/exp_perturb_O1_pilot/reports/perturbation/relaxation_curves.png)

![Figure 10. **O1 perturbation trajectories in t-SNE.** Each panel shows $n=50$ O1 trajectories as step-colored t-SNE polylines; arrows mark the step 14→15 displacement at injection. Adversarial perturbations produce larger visible displacements than neutral or lorem perturbations, while control trajectories show only ordinary step-to-step movement. Source: `data/exp_perturb_O1_pilot/reports/perturbation/trajectories_tsne_by_condition.png`.](data/exp_perturb_O1_pilot/reports/perturbation/trajectories_tsne_by_condition.png)

![Figure 11. **PCA-3 snapshots of O1 perturbation trajectories.** Static 2×2 composite showing the shared PCA-3 embedding for control, neutral, lorem, and adversarial conditions, with iso-density shells, six trajectory trails per panel, and red pre/post-injection segments for perturbed conditions. The adversarial panel shows longer pre/post-injection segments than neutral or lorem in this projection. Source: `data/exp_perturb_O1_pilot/reports/perturbation/animation3d_snapshots.png`.](data/exp_perturb_O1_pilot/reports/perturbation/animation3d_snapshots.png)

![Figure 12. **Joint t-SNE snapshot after O1 perturbation.** Static frame at step 24 from a joint t-SNE animation fit once on all O1 perturbation points: 4 conditions × 50 trajectories × 30 steps, with PCA-30 pre-reduction and `init="pca"`. Each panel shows current trajectory heads, recent fading trails, the full condition cloud in grey, and red X markers at pre-injection positions for perturbed runs. At this step, adversarial trajectories are more dispersed from their pre-injection locations than neutral or lorem trajectories. Animated GIF (joint fit, fixed coordinates) at `data/exp_perturb_O1_pilot/reports/perturbation/tsne_anim_joint.gif`; per-step refit companion at `tsne_anim_refit.gif`. Source: `data/exp_perturb_O1_pilot/reports/perturbation/tsne_anim_joint_snapshot.png`.](data/exp_perturb_O1_pilot/reports/perturbation/tsne_anim_joint_snapshot.png)

**Summary (per-condition V* and RG cloud expansion).** We compute
geometric $V^\star$ from the empirical density landscape on PCA-2
and Ward-linkage cloud-merge distances on $k=48$ fine clusters for
each of the four diagnostic perturbation pilots. The numerical
values are descriptive: $V^\star$ is parameter-grid sensitive
(CV 14-24%; §5.16), but the *ordinal* ranking of conditions
(control highest, adversarial lowest in 89-98% of parameter
combinations) is robust. The full $V^\star$ × condition table
and Ward-merge-distance table for each regime are moved to §11.11;
they support the qualitative reading that **(i) replace-mode O2/O3
lorem produces a new basin (high $V^\star$ + large RG expansion);
(ii) O1 adversarial has intermediate $V^\star$ consistent with
ridge-crossing rather than basin creation; (iii) D1 has low $V^\star$
across all conditions, consistent with content-independent basins**.
**The numerical $V^\star$↔ED50 correspondence does not
survive quantitative scrutiny**: the geometric values complement
but do not validate the behavioral barrier numbers.

---

### §5.B, Stress tests of primary results

### 5.11 Group-aware basin-predictability

The basin-predictability acc(k) numbers reported in §5.3 / §5.4 use
sklearn `StratifiedKFold` for cross-validation, which assigns
trajectories to train/test folds *without* respecting the
prompt-family grouping. Because the late-window basin a trajectory
ends up in is partly determined by its prompt family, especially
in dialog (D1) and replace-mode (O2/O3) regimes where the basin
co-varies with stylistic / topical content, random k-fold lets the
classifier exploit family identity as a feature, inflating
predictability above what is genuinely available from a held-out
prompt family.

To quantify the leakage, we re-ran the same basin-predictability
classifier with `GroupKFold(n_splits=5, groups=prompt_family)`,
which holds out one entire prompt family per fold and forces the
classifier to generalize across families rather than within them.
The accuracy delta `Δ = acc(stratified) − acc(grouped)` is a direct
measure of how much of the reported number was from-family
leakage. Computed via `scripts/group_aware_basin_predictability.py`
on the existing publication-scale embeddings (no new data, no API
calls).

**Result: leakage is regime-specific and substantial outside O1.**
At the canonical predictor step k=10:

*Table, Group-aware basin-predictability: stratified vs leakage-free accuracy and family-leakage $\Delta$ at $k{=}10$.*

| regime | n_traj | acc (stratified) | acc (group, leakage-free) | Δ leakage |
|---|---:|---:|---:|---:|
| O1 contractive | 1350 | 0.803 | 0.732 | **+0.071** |
| O2 paraphrase / replace | 1350 | 0.896 | 0.596 | **+0.301** |
| O3 summarize+negate / replace | 1350 | 0.912 | 0.629 | **+0.283** |
| D1 dialogue-state-driven dialog | 450 | 0.604 | 0.336 | **+0.269** |

(All accuracies are top-1; chance baseline is roughly $1/12 \approx 0.08$ for K-means k=12. Source: `data/aggregated/group_aware_basin_pred.csv` and `group_aware_basin_pred.png`.)

**Interpretation.**

- **O1 (Δ = +0.07)** is the only regime whose basin-predictability
  is robust to family leakage. The contractive basin is a real
  cross-family signal: held-out families are still classified at
  73% top-1 accuracy from PCA-10 alone, well above chance and
  above the leakage delta. The reviewer's concern is therefore
  *least* applicable to O1, which is also the regime our headline
  claims rest on.
- **O2 / O3 (Δ ≈ +0.30)** lose roughly two-thirds of their
  apparent basin signal under group-aware CV. This means the
  reported 90+% basin predictability for replace-mode regimes is
  largely a within-family fingerprint: trained on (philosophy_dialog,
  reflective, ...) and tested on the *same* family, the classifier
  recognizes "this looks like a reflective trajectory" and that
  (in replace mode) over-determines the late-window basin. Under
  honest cross-family CV, the residual basin signal at ~60%
  accuracy is still well above chance but is much weaker evidence
  for a *generic* basin structure independent of seed text.
- **D1 (Δ = +0.27)** behaves similarly, the dialogue-state basin is
  largely a family fingerprint, which is consistent with the
  paper's existing characterization of D1 as a *stylistic*
  multi-basin regime: style is correlated with prompt family by
  construction, so a within-family classifier looks confident even
  when the underlying basin signal is weaker.

**What this changes in the paper.** The §5.3 headline numbers should
be read as upper bounds; the cross-family-honest numbers are
substantially lower for replace-mode and dialog regimes. The
qualitative regime ordering survives (O3 > O2 > O1 > D1 in
stratified CV; O1 > O3 > O2 > D1 in group-aware CV, note O1 and O3
swap positions), but the *gap* between O1 and the rest is much
smaller under leakage-free CV (~10pp) than under stratified CV
(~10-30pp). The contractive basin claim is the most robust under
this stress test.

**Hierarchical model across all perturbation results.** A separate
analysis (`scripts/mixed_effects_perturbation.py`) fits a single
mixed-effects logistic regression to all 600 perturbed-trajectory
outcomes pooled across the four diagnostic perturbation pilots,
with random intercepts for prompt_family and IC-within-family. Key
result: **the IC-within-family random-intercept SD (0.82 logits) is
~3× the between-family random-intercept SD (0.29 logits)**. Most of
the trajectory-level heterogeneity is *within* prompt families, not
*between* them. Practical consequence: per-cell Wilson CIs that
treat trajectories as IID are slightly overconfident at typical
sample sizes; the headline regime ordering survives the proper
hierarchical correction (O1/adversarial fixed-effect vs D1/adversarial
reference: coefficient = −0.61, 95% CI [−1.21, −0.02], p < 0.05;
O2 and O3 conditions: coefficients +2.2 to +3.9, well above zero),
but the sub-regime cell-level rates are slightly attenuated under
partial pooling. Output:
`data/aggregated/mixed_effects_perturbation.csv`.

![Figure G. **Group-aware basin-predictability re-analysis.** Paired bars compare StratifiedKFold accuracy with GroupKFold-by-family accuracy for each regime and predictor step. The annotated $\Delta$ gives the drop when prompt families are held out across folds. O1 shows the smallest drop, while O2, O3, and D1 lose substantially more accuracy under group-aware cross-validation. Source: `data/aggregated/group_aware_basin_pred.png`.](data/aggregated/group_aware_basin_pred.png)

### 5.12 Cluster-stability check

The basin partition used throughout the paper is K-means with $k=12$
on PCA-10. Review weakness #2 asked: *are these K-means clusters real
basins, or artefacts of the K-means algorithm at this particular k?*
We address this by re-running clustering on the existing
publication-scale embeddings (no new data, no API calls) with two
methods that don't make K-means' spherical-cluster assumption: **HDBSCAN**
(density-based, finds clusters of arbitrary shape; cluster count is
auto-detected) and **spectral clustering** (graph-based, uses
nearest-neighbour affinity). Each is run on a uniform 3,000-point
subsample of the late-window cloud (the full ~20,000-point publication
cloud is too large for nearest-neighbour spectral) and compared to
K-means at $k\in\{8,12,16\}$ via Adjusted Rand Index (ARI), a
chance-corrected agreement measure where 0 = random partitioning and
1 = identical partitioning. Computed via
`scripts/cluster_stability_check.py`; per-experiment ARI matrices in
`data/exp_*/reports/cluster_stability/stability_heatmap.png`.

**Headline:** clusters are *moderately* stable across methods, but the
K-means $k=12$ partition is not unique. Median ARI between K-means@12
and the other methods, per regime:

*Table, Cluster stability: median ARI between K-means@12 and HDBSCAN per regime.*

| regime | median ARI vs K-means@12 | HDBSCAN auto-detected k | interpretation |
|---|---:|---:|---|
| O1 contractive | 0.53 | **2** | HDBSCAN sees the O1 cloud as effectively *one basin* (~98% of points in 1-2 clusters); K-means k=12 over-partitions a single contractive attractor. ARI between K-means@12 and HDBSCAN@2 is 0.01 (essentially random), they're measuring different things at different granularities. |
| O2 paraphrase / replace | 0.58 | 16 | HDBSCAN finds a cluster count similar to K-means; partitions agree at ~0.6 ARI. |
| O3 summarize+negate / replace | 0.60 | 16 | Same as O2; replace-mode regimes have moderately stable cluster structure. |
| D1 dialogue-state-driven dialog | 0.66 | 16 | Highest stability; HDBSCAN and K-means@12 agree at ~0.66 ARI. |

**What this means for the basin claim.**

- **For O1**: the contractive-basin story is *strengthened*, not
  weakened, by this stress test. HDBSCAN at default density
  thresholds prefers a one-or-two-basin partition, exactly what a
  contractive attractor should look like. The K-means $k=12$
  partition we use throughout is therefore best understood as a
  *fine-grained sub-partition of one attractor* rather than 12
  separate basins. Consequences: (a) the perturbation switching
  metric (cluster-disagreement at the K-means k=12 level) may
  partially track sub-basin movement within one large attractor
  rather than true attractor-escape, a partial confirmation of
  review weakness #2, but it still also tracks attractor-level
  changes when the perturbation pushes trajectories outside the
  contractive basin's PCA-10 envelope (which is what the
  long red kick beams in Figure 11 visualize); (b) the
  basin-predictability $A^{\mathrm{final}}=0.85$ for O1 (§5.3) is
  the predictability of the *fine-grained* partition; the *coarse*
  basin (HDBSCAN k=2) is presumably even more predictable.

- **For O2/O3/D1**: cluster stability is moderate (~0.6 ARI), the
  partition is method-dependent at the boundaries but not arbitrary.
  Combined with the group-aware basin-predictability findings in
  §5.11 (large family-leakage delta for these regimes), we conclude
  that the basin labels in O2/O3/D1 are partly stylistic / family
  fingerprints rather than purely dynamical attractor structure.

**What this changes in the paper.** We retain K-means $k=12$ as the
canonical partition because it is what every downstream metric in §5
(basin score, basin entry, perturbation switching, basin
predictability) is built on, and re-running the entire pipeline at a
different cluster granularity is out of scope for this revision.
However, all claims of the form "trajectory switched basin" should
be read with the caveat that "basin" here means K-means $k=12$
cluster, not a HDBSCAN density basin. The two notions agree for
O2/O3/D1 at ~60% agreement and disagree for O1 (where HDBSCAN sees
fewer, larger basins). Future work should compute the perturbation
switching metric at multiple cluster granularities (K-means k=2, k=12,
HDBSCAN auto) and compare the dose-response curves.

### 5.13 Multi-granularity switching

The §5.12 cluster-stability check showed that K-means $k=12$ is not
the unique partition (median ARI ≈ 0.5-0.7 vs HDBSCAN/spectral; for
O1, HDBSCAN auto-detects only 2 clusters). A natural follow-up
question: **does the perturbation switching dose-response survive at
a different cluster granularity?** If switching-rate ordering across
conditions stays the same when we re-cluster at coarser or method-
specific granularity, then the headline isn't a K-means $k=12$
artefact.

We re-ran the perturbation switching analysis on the four diagnostic
perturbation pilots (`exp_perturb_O1_pilot`, `O2_pilot`, `O3_pilot`,
`D1_pilot`) at three granularities: K-means $k=12$ (canonical),
K-means $k=4$ (coarse), and HDBSCAN (auto-detected count). For each
non-control trajectory we recomputed whether its final-step cluster
differs from its same-(family, IC, run) control trajectory, under
each granularity. Computed via
`scripts/multi_granularity_switching.py`.

*Table, Granularity comparison: switching rate at K-means $k{=}12$, $k{=}4$, and HDBSCAN per pilot.*

| pilot | condition | k=12 | k=4 | HDBSCAN | granularity-robust? |
|---|---|---:|---:|---:|---|
| O1 | adversarial | 0.54 | 0.44 | 0.60 | [OK] headline robust |
| O1 | neutral | 0.24 | 0.18 | 0.38 | [OK] low across all |
| O1 | lorem | 0.18 | 0.18 | 0.30 | [OK] low across all |
| O2 | adversarial | 0.94 | 0.72 | 1.00 | [OK] saturated at k=12 / HDBSCAN; coarse k=4 collapses some |
| O2 | neutral | 1.00 | 1.00 | 1.00 | [OK] |
| O2 | lorem | 1.00 | 1.00 | 1.00 | [OK] |
| O3 | adversarial | 0.96 | 0.74 | 0.98 | [OK] same pattern as O2 |
| O3 | neutral | 1.00 | 0.74 | 1.00 | [OK] |
| O3 | lorem | 1.00 | 1.00 | 1.00 | [OK] |
| D1 | adversarial | 0.60 | 0.50 | 0.40 | partial (drops 20pp at HDBSCAN) |
| D1 | neutral | 0.76 | 0.60 | 0.66 | partial |
| D1 | lorem | 0.56 | 0.46 | 0.44 | partial |

(All cells $n=50$; Wilson 95% CIs in
`data/aggregated/multi_granularity_switching.csv`. Source:
`data/aggregated/multi_granularity_switching.png`.)

**What this rules in.**

1. **The O1 OOD-vs-in-distribution asymmetry is granularity-robust.**
   At every cluster granularity tested, O1's adversarial switching rate
   is roughly 2-3× the OOD (neutral / lorem) rate. The headline
   contractive-basin finding is not a K-means $k=12$ artefact.

2. **Replace-mode capitulation at K-means $k=12$ and HDBSCAN is
   real.** O2 and O3 saturate at 100% switching at the canonical and
   auto-detected granularities. At coarse $k=4$, switching drops to
   72-74% on adversarial, but this is mechanistic: at $k=4$ a single
   "absorber" basin captures more of the diversity, so trajectories
   ending up in the same macro-basin no longer count as switches.

3. **D1 switching is the most granularity-sensitive.** D1's adversarial
   rate drops from 0.60 (K-means $k=12$) to 0.40 (HDBSCAN). This is
   consistent with our other findings (§5.11: D1 has 27pp family-
   leakage in basin-predictability), the D1 dialogue-state basin is partly
   a fine-grained K-means partition that doesn't fully reproduce under
   coarser methods.

**Combined with §5.11 and §5.12 results**, the picture is:
- **O1 contractive basin**: robust to family-leakage CV (+0.07
  delta), robust to cluster-method (HDBSCAN k=2), robust to
  granularity (multi-granularity switching ratio preserved). The
  most defensible regime claim in the paper.
- **O2/O3 replace-mode capitulation**: granularity-robust at fine
  granularities (k=12, HDBSCAN k=16) but partially mechanism-
  dependent at coarse k=4. Combined with §5.11's high family-
  leakage delta, the basin-level interpretation is weaker than the
  switching-rate interpretation.
- **D1 dialogue-state-driven multi-basin**: most fragile under stress tests
  (high family-leakage; granularity-sensitive switching). The
  qualitative claim survives but the absolute numbers shift
  substantially.

![Figure H. **Switching rates under alternative cluster granularities.** Panels show perturbation switching rates for D1, O1, O2, and O3, recomputed with K-means $k=12$, K-means $k=4$, and HDBSCAN; error bars are Wilson 95% CIs with $n=50$ per cell. O1 retains higher adversarial than neutral/lorem switching across all three cluster definitions, while D1 is more sensitive to the clustering method. Source: `data/aggregated/multi_granularity_switching.png`.](data/aggregated/multi_granularity_switching.png)

### 5.14 Per-cluster semantic inspection

The diagnostics in §5.11-§5.13 examined whether the K-means $k=12$
partition is statistically/methodologically robust. A complementary
question is **what the clusters semantically represent.** Are they
basins of *content* (specific topics) or basins of *style*
(register-shaped attractors)? Are the replace-mode regimes truly
absorbing in the sense of converging to common text, or only in a
formal-template sense? We answered this by extracting representative
trajectory text from each cluster (`scripts/extract_cluster_text_samples.py`)
and having a separate LLM characterise each cluster's content
blind to the paper's regime labels (using a frontier reasoning
model held out from the rest of the pipeline). Results below; raw cluster-text-sample files at
`data/aggregated/cluster_text_samples_*.md`.

#### O1, append-mode contractive (12 clusters, 1350 trajectories)

Three large attractors and four medium sub-basins, organised by
**register / style**, not by topic content:

*Table, Per-cluster semantic content for O1 (12 clusters, 1350 trajectories).*

| cluster | $n$ | dominant style | basin class |
|---:|---:|---|---|
| 7 | 355 | sentimental narrative (cozy magical scenes, friendship, wonder) | large attractor |
| 3 | 297 | expository / policy-discursive (ethics, governance, education) | large attractor |
| 1 | 258 | reflective empathic discourse (shared humanity, vulnerability, storytelling) | large attractor |
| 6 | 134 | creative coaching (process, agency, collaboration, feedback) | medium sub-basin |
| 2 | 91 | fabulist narrative (lyrical animal/landscape journeys) | medium sub-basin |
| 5 | 89 | technical tutorial (programming explanations, best practices) | medium sub-basin |
| 10 | 61 | practical advice / listicle (interpersonal, financial, workplace) | medium sub-basin |
| 0, 4, 8, 9, 11 | 8-22 | small / outlier | small |

**Finding for O1**: The convergence is **register-shaped, not
topic-shaped**: same family seeds drift to similar styles regardless
of original content. Beans, garlic, capital punishment, hashing,
paintings, landlords, and noise strings all lose their original
specificity and stabilise in one of a few high-probability
continuation styles (supportive explanation, sentimental narrative,
policy discourse). This **strengthens** the contractive-basin
interpretation but specifies the *axis of contraction*: register, not
content.

#### O2, replace-mode paraphrase (12 clusters, 1350 trajectories)

Multiple medium clusters, organised by **seed family / topic**, not
by style:

*Table, Per-cluster semantic content for O2 (12 clusters, 1350 trajectories).*

| cluster | $n$ | dominant content | basin class |
|---:|---:|---|---|
| 4 | 204 | third-person story events (clean narrative paraphrase) | large attractor |
| 9 | 178 | strong claims + technical explanations (formal declarative) | large attractor |
| 3 | 165 | abstract epistemic/philosophical explanation | large attractor |
| 0 | 140 | technical / definitional claims | large attractor |
| 1 | 101 | short fragments normalised into fuller utterances | medium sub-basin |
| 7 | 102 | metaphorical inward reflection (lyrical reflective) | medium sub-basin |
| 11 | 97 | first-person affective states (emotional self-report) | medium sub-basin |
| 10 | 90 | imperative procedural style (instructions) | medium sub-basin |
| 2, 5, 6, 8 | 64-73 | small | small |

**Finding for O2**: O2 does **not** collapse into one absorbing text
or even one shared semantic topic. It mostly preserves the seed's
local meaning while repeatedly sanding it into a more conventional
paraphrase. Narratives stay narrative; instructions stay procedural;
technical claims stay expository. This is **not** an O1-style
register attractor, it's a set of paraphrastic sub-basins organised
by seed family and surface register. The "oscillatory" label in the
paper's existing taxonomy is descriptive of the period-2 dynamics
but should not be read as "semantic convergence."

#### O3, replace-mode summarize-then-negate (12 clusters, 1350 trajectories)

Four large clusters, all dominated by the operator's **antithetical
template** (X; not-X), but each cluster preserves seed-family
content:

*Table, Per-cluster semantic content for O3 (12 clusters, "summarised then denied" template, 1350 trajectories).*

| cluster | $n$ | dominant content (within template) | basin class |
|---:|---:|---|---|
| 4 | 227 | narrative events reversed/contradicted (story arrival/absence, same/different) | large attractor |
| 3 | 160 | philosophical thesis/antithesis prose | large attractor |
| 10 | 155 | abstract/technical proposition + explicit negation | large attractor |
| 1 | 151 | code/function descriptions summarised then denied | large attractor |
| 8 | 104 | first-person creative/life problems reframed as positive/negative | medium sub-basin |
| 11 | 99 | emotional states mapped to opposite affects | medium sub-basin |
| 0, 2, 5, 6, 7, 9 | 44-88 | small | small |

**Finding for O3**: O3's "absorbing" property is **formal**, not
semantic. Nearly every trajectory becomes "summary + opposite," but
the actual content remains seed-specific. Narrative seeds become
event-summary plus reversed event; emotional seeds become affect plus
opposite affect; technical seeds become proposition plus denial.
There is no evidence that unrelated seed families converge to the
same recognisable text content. O3 is absorbing as a **discourse
template**, not as a content attractor.

#### D1, append-mode dialog (curious user + helpful agent, 11 active clusters, 450 agent-role trajectories)

Multiple medium / small clusters dominated by **dialogue-state
attractors and recent-context capture**, not by stable seed content:

*Table, Per-cluster semantic content for D1 (11 active clusters, 450 agent-role trajectories).*

| cluster | $n$ | semantic theme | basin class |
|---:|---:|---|---|
| 3 | 67 | reflection tools / journaling / communication rehearsal | medium sub-basin |
| 9 | 55 | creative feedback / taste-and-style recommendation | medium sub-basin |
| 2 | 53 | education / documentary outreach / sustainability | medium sub-basin |
| 7 | 52 | wellness / self-improvement coaching | medium sub-basin |
| 5 | 48 | upbeat empathic small talk | small |
| 11 | 42 | professional coaching / workplace productivity | small |
| 4 | 38 | creative-craft advice (game design, narrators) | small |
| 10 | 36 | affirming conversational elaboration / meaning-making | small |
| 0, 6, 8 | 15-23 | outlier / small | outlier |

**Finding for D1**: D1's basins are **dialogue-state attractors**
(supportive affirmation, practical recommendation, creative feedback,
wellness coaching, workplace advice, generic follow-up-question
mode), not stable seed-content basins. Seeds frequently lose their
original specificity through append-mode accumulation: fear becomes
yogurt advice; philosophical responsibility becomes Asana
recommendations; emotional embarrassment becomes watercolor
technique. This **qualifies** the paper's "stylistic multi-basin"
label: D1 is multi-basin, but the mechanism is *recent-context
capture / conversational drift* rather than purely stylistic
attractor convergence.

#### Comparative reading and what this changes in the taxonomy

The four regimes are *all* multi-basin at K-means $k=12$, but the
mechanism producing the basins differs:

*Table, Regime-cluster summary: basin axis, mechanism, and taxonomy implication per regime.*

| regime | basin axis | mechanism | implication |
|---|---|---|---|
| **O1** | register / style | contractive flow toward high-probability continuation styles | regime label preserved: *register-contractive* attractor |
| **O2** | seed family / topic | paraphrase preserves content; clusters reflect seed-family register | regime should be re-labeled: from "oscillatory absorbing" to "paraphrastic family-preserving" (the period-2 dynamics still hold, but the basins are not absorbing) |
| **O3** | operator template (formal X / not-X) | the negate operator imposes a discourse-shape; content stays seed-specific | regime should be re-labeled: from "absorbing" to "template-absorbing", operator-shape convergence, not semantic convergence |
| **D1** | dialogue-state / recent-context capture | append-mode dialog accumulates context; basins are conversational acts | regime should be re-labeled: from "stylistic multi-basin" to "dialogue-state-driven multi-basin", the mechanism is recent-context drift, not purely stylistic preference |

**Net effect on the taxonomy.** The four-regime taxonomy survives,
but only one of the four labels (O1) accurately describes its basin
mechanism. We retain the existing labels in this paper for
continuity with prior versions of the manuscript, but flag the
correction explicitly: O2's basins are not "absorbing" in the
content-convergence sense; O3's "absorbing" is template-formal;
D1's "stylistic" basins are mediated by conversational drift, not
direct style preference. A future revision should adopt the
re-labelled taxonomy (register-contractive / paraphrastic
family-preserving / template-absorbing / dialogue-state-driven).

### 5.15 Per-family heterogeneity and persistence of "switching"

**Why this section exists.** The headline raw-switching endpoint counts final-cluster disagreement and is therefore deliberately sensitive to any final-step displacement, including transient kicks that recovered. This subsection tests whether the headline switching corresponds to durable basin escape (the strict reading) or merely to final-step disagreement (the loose reading) by decomposing each switching trajectory into 'kicked at injection AND persisted to terminal step' versus 'kicked-and-recovered' versus 'drifted-without-kick' categories.

Two further reanalyses of the existing O1 sparse-dose adversarial
sweep (`exp_perturb_O1_dose_adversarial`, n=50/cell × 4 doses)
sharpen the interpretation of the headline switching metric. Both
use the existing `joint_pca10_clusters.csv` outputs, no new data,
no API calls. Computed via `scripts/per_family_and_persistence.py`.

#### Per-family ED50 heterogeneity

The population-level dose-response saturates at ~50% switching
(§5.6, Figure 4). We asked: is this **one population at half-mixing**
(every trajectory has 50% chance of crossing) or **family
heterogeneity** (some families consistently cross, others don't)?
Per-family rates from the existing sparse data:

*Table, Per-family O1 adversarial switching rates across the sparse dose grid.*

| family | dose 20 | dose 80 | dose 200 | dose 400 |
|---|---:|---:|---:|---:|
| philosophy_dialog | 0.10 | 0.40 | **0.90** | 0.50 |
| practical_dialog | 0.40 | 0.20 | 0.70 | **0.80** |
| creative_dialog | 0.20 | 0.40 | 0.30 | 0.60 |
| reflective | 0.30 | 0.30 | 0.40 | 0.40 |
| emotional | 0.30 | 0.40 | 0.40 | **0.10** |

(All cells $n=10$. Source:
`data/aggregated/per_family_ed50.csv` and
`per_family_ed50.png`.)

**Finding.** The population-level saturation hides substantial
family heterogeneity. **`philosophy_dialog` shows a clear
threshold-crossing pattern** (0.10 → 0.40 → 0.90, a clean dose-
response). **`practical_dialog` shows monotone increase** beyond
dose 80 (0.40 → 0.20 → 0.70 → 0.80). But **`emotional` shows a
*negative* dose-response at dose 400** (drops from 0.40 to 0.10),
and **`reflective` is essentially flat** across all doses
(0.30 → 0.30 → 0.40 → 0.40). The flat / negative families pull
the population-mean curve below saturation.

The implication for "barrier height" is structural: under the
current switching definition, **there is no single ED50 for O1
in the sparse-data analysis**, different prompt families have
different dose-response shapes. The dense-dose rerun (§5.6.1)
recovers a clean *population-level* monotonic curve at $n=200$/cell,
with a tighter point estimate (ED50 ≈ 40 tokens), but the underlying
per-family heterogeneity flagged here is still expected to apply
within the dense data, a future per-family decomposition of the
$n=200$/cell rerun would refine the picture.

![Figure I. **Per-family O1 adversarial dose-response.** Lines show switching rate versus adversarial dose for each prompt family in the sparse O1 dose experiment, with $n=10$ trajectories per family-dose cell; the dashed black line is the population mean. Family-level curves differ: some increase with dose, while others are flat or non-monotone in this pilot sample. Source: `data/aggregated/per_family_ed50.png`.](data/aggregated/per_family_ed50.png)

#### Persistence test: is "switching" basin-escape or stochastic divergence?

The headline "switching" metric is `final-step cluster ≠ paired-
control's final-step cluster` (§4.5.11). A direct mechanistic test
of *barrier crossing* is more conservative: did the trajectory
**visibly jump cluster at the moment of injection** (step 14 → step
15 cluster change)? And if it did, did it **persist** in the new
basin to the end of the trajectory, or **drift back** to its pre-
injection cluster?

**Persistence test on the dense-rerun data** ($n = 200$/cell × 8
doses; same `joint_pca10_clusters.csv` as §5.6.1):

*Table, Persistent-escape decomposition under K-means $k{=}12$ at dense O1 adversarial doses.*

| condition | n | kicked at injection | persisted (kicked AND final = post-inj) | drifted back (kicked AND final = pre-inj) | drifted elsewhere | persistent-escape rate (n_persisted / 200) |
|---|---:|---:|---:|---:|---:|---:|
| adversarial_dose20 | 200 | 10 (5.0%) | 7 (70%) | 1 | 2 | **3.5%** |
| adversarial_dose50 | 200 | 23 (11.5%) | 14 (61%) | 2 | 7 | **7.0%** |
| adversarial_dose80 | 200 | 18 (9.0%) | 7 (39%) | 3 | 8 | **3.5%** |
| adversarial_dose120 | 200 | 43 (21.5%) | 18 (42%) | 7 | 18 | **9.0%** |
| adversarial_dose160 | 200 | 53 (26.5%) | 23 (43%) | 7 | 23 | **11.5%** |
| adversarial_dose200 | 200 | 59 (29.5%) | 26 (44%) | 11 | 22 | **13.0%** |
| adversarial_dose300 | 200 | 64 (32.0%) | 28 (44%) | 7 | 29 | **14.0%** |
| adversarial_dose400 | 200 | 69 (34.5%) | 32 (46%) | 13 | 24 | **16.0%** |

(Source: `data/aggregated/persistence_summary.csv`, overwritten
with dense-rerun values via `scripts/per_family_and_persistence.py
--exp exp_perturb_O1_ed50_dense`.)

**Finding (dense data).** The persistent-escape rate (kicked AND
persisted in new basin to terminal step) **is 16% at dose 400**,
the maximum tested. Compare to the **67% raw switching rate at
dose 400** (§5.6.1, dense): the gap is **51 percentage points**.
**Most of the raw "switching" is post-injection stochastic
divergence from the paired control, not clean barrier-crossing.**
Of trajectories that *do* visibly jump cluster at injection (35%
at dose 400), only ~46% persist to the terminal step; the rest
drift back to their pre-injection cluster (~19%) or to a third
basin (~35%). Even visible at-injection kicks are transient
roughly half the time, consistent with a contractive basin
pulling trajectories back even after a cluster-boundary excursion.

The persistent-escape ED50 (the dose where persistent escape rate
crosses 50%) is **not reached in the tested range**. The dense
rerun thus confirms a key conceptual distinction: the formal §3.1.1
barrier-height definition is a persistent-escape endpoint, and
that endpoint is undefined in this experiment. The dense
$\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens is a raw-switching
endpoint, established but distinct from the formal barrier
definition (§3.1.2).

For comparison, the original sparse-pilot persistence numbers
($n=50$/cell, 4 doses) gave 8% kicked-and-persisted at dose 400,
qualitatively similar pattern, but the dense rerun's 16% has
narrower uncertainty and richer dose granularity. Both data sets
support the same conclusion: persistent escape is a different
quantity from raw switching, and it is much smaller in O1 under
in-distribution adversarial perturbation.

**Multi-granularity persistence, does the persistent-escape ED50
result survive different cluster definitions?** A natural
robustness concern is that persistent escape, defined relative to
K-means clusters, might be sensitive to the cluster granularity.
We re-ran the persistence test on the same dense data using three
cluster granularities: K-means $k=12$ (canonical), K-means $k=4$
(coarse), and HDBSCAN (auto, 18 clusters detected on the joint
PCA-10 cloud). Computed via
`scripts/multi_granularity_persistence.py`.

*Table, Persistent-escape rate under K-means $k{=}12$, $k{=}4$, and HDBSCAN per dose.*

| dose | persistent escape (k=12) | persistent escape (k=4) | persistent escape (HDBSCAN) | kicked at injection (HDBSCAN) |
|---|---:|---:|---:|---:|
| 20 | 3.5% | 1.5% | 7.0% | 12.0% |
| 50 | 7.0% | 3.0% | 16.5% | 28.5% |
| 80 | 3.5% | 5.0% | 28.5% | 48.0% |
| 120 | 9.0% | 4.5% | 35.5% | 58.0% |
| 160 | 11.5% | 9.5% | 41.0% | 64.5% |
| 200 | 13.0% | 13.5% | 40.5% | 60.0% |
| 300 | 14.0% | 8.5% | 40.0% | 66.5% |
| 400 | **16.0%** | **10.0%** | **39.5%** | 68.5% |

(Source: `data/aggregated/multi_granularity_persistence.csv`.)

**The persistent-escape ED50 is undefined under all three
granularities.** The maximum persistent-escape rate across all
doses and granularities is HDBSCAN at dose 400 = 39.5%, well below
the 50% threshold. K-means $k=12$ and $k=4$ give 10-16% maxima.
The headline conclusion, *persistent basin escape is not measured
in the tested range*, is **robust to cluster choice**. The HDBSCAN
"kicked at injection" rate does cross 50% (68.5% at dose 400), but
of those visible at-injection jumps, only ~58% persist to the
terminal step under HDBSCAN; the rest drift back or to a third
cluster. So even at the most permissive granularity, the **kicked-
AND-persisted** rate stays below 50%.

![Figure L. **Multi-granularity persistence rates vs adversarial dose.** O1 dense rerun ($n=200$/cell × 8 doses). Three cluster granularities: K-means $k=12$ (blue, canonical); K-means $k=4$ (orange, coarse); HDBSCAN auto (green, 18 clusters detected). Solid lines: persistent-escape rate (kicked at injection AND in new cluster at terminal step). Dashed lines: kicked-at-injection rate (cluster differs at step 15 vs step 14). Grey dotted line: 50% threshold (formal persistent-escape barrier). Persistent escape never reaches 50% at any granularity; HDBSCAN at dose 400 gives the maximum at 39.5%. The result is robust to cluster definition. Source: `data/aggregated/multi_granularity_persistence.png`.](data/aggregated/multi_granularity_persistence.png)

**Engineering consequence.** For agent evaluations that consume tool outputs, file contents, or third-party documents, this implies that next-step compliance, final-output disagreement, and durable task redirection should be reported as separate outcomes. A tool output, file comment, or web-fetched page may cause a visible trajectory jump (raw switching) without producing persistent capture of the subsequent plan-edit-test loop.

### 5.16 V* parameter-grid sensitivity

The §5.10 caveat box flagged that $V^\star$ values depend on
analyst-chosen KDE bandwidth, grid resolution, and basin-detector
thresholds. We quantified this directly. For the O1 perturbation
pilot, we re-ran the geodesic-skeleton $V^\star$ computation across
a parameter grid:

- **KDE bandwidth** (`sigma_cells`): {1.0, 1.5, 2.0, 2.5, 3.0}
- **Grid resolution** (`grid_n`): {64, 96, 128}
- **Basin count** (`n_basins`): {3, 4, 5}

This is **45 parameter combinations × 4 conditions = 180 cells**.
PCA-2 was held fixed (the geodesic skeleton is intrinsically 2-D).
For each cell we computed the per-condition mean $V^\star$ across
all inter-basin geodesics. Computed via
`scripts/v_star_sensitivity.py`; outputs at
`data/aggregated/v_star_sensitivity.csv` (raw),
`v_star_sensitivity_summary.csv` (per-condition spread).

**Per-condition spread of $V^\star$ across the parameter grid:**

*Table, $V^\star$ sensitivity by condition: min/median/max/std/CV across 45 parameter combinations.*

| condition | min $V^\star$ | median | max | std | CV (%) |
|---|---:|---:|---:|---:|---:|
| **control** | 2.63 | 3.78 | 5.13 | 0.61 | **16%** |
| **neutral** | 1.86 | 2.43 | 3.38 | 0.33 | **14%** |
| **lorem** | 2.00 | 2.81 | 4.37 | 0.54 | **19%** |
| **adversarial** | 1.22 | 2.07 | 3.27 | 0.50 | **24%** |

**Ordinal stability**: across the 45 parameter combinations:

- **control has the highest $V^\star$ in 98% of combinations**, never the lowest;
- **adversarial has the lowest $V^\star$ in 89% of combinations**, never the highest;
- neutral and lorem occupy the middle.

**Reading.** The numerical $V^\star$ values are not invariant to
parameter choices, the per-condition coefficient of variation is
14-24% across the tested grid, so a single $V^\star$ number reported
without sensitivity context could be misleading by ~20%. **However,
the ordinal claim that the $V^\star$ ranking is `control > neutral /
lorem > adversarial` is robust to analyst choices**: it holds in
89-98% of the 45 parameter combinations. This *supports a weaker but
still useful version* of the original claim: $V^\star$ gives a
reliable rank-order signal of basin geometry across the four
perturbation conditions, even though the numerical values are
KDE-bandwidth-dependent.

**What this changes in the paper.** §5.10's V* tables retain their
(post-revision) status as descriptive visualisations of density
structure. The ordinal-agreement claim that the original abstract
made, "behavioral and geometric barriers agree in ordinal
structure", is partially rehabilitated: the **rank ordering is
empirically robust**, but only over the comparison space of four
conditions within one perturbation pilot, not as a quantitative
correspondence between V* and ED50. We do not reinstate the
original abstract claim, but the §5.10 caveat box now reflects the
empirical finding.

![Figure J. **Sensitivity of $V^\star$ to density-landscape parameters.** Lines show per-condition mean $V^\star$ for the O1 perturbation pilot across 45 combinations of KDE bandwidth, grid resolution, and basin count. Absolute $V^\star$ values vary across parameter settings, while control is usually the highest condition and adversarial is usually the lowest in this grid. Source: `data/aggregated/v_star_sensitivity.png`.](data/aggregated/v_star_sensitivity.png)

### 5.17 Replace-mode tautology probe, overwrite vs insert

**What this probe is for.** Replace-mode regimes (O2, O3) appear to switch at near-100% under the existing protocol, which would suggest a very low attractor barrier. This probe directly tests whether that vulnerability reflects a low basin barrier in the model or whether it is an artifact of the update rule erasing prior state. We isolate the two by re-running the same injection text and dose under two contrasting conditions: overwrite (the existing protocol, injection replaces the model's output at the injection step) versus insert (injection prepended to context, model generates normally and the model's own output remains).

The original O2/O3 perturbation result, 94-100% switching at all
probed doses, is partly tautological, because the replace-mode
operator in `adversarial_doseN` *overwrites* step 15's output
entirely. Under that intervention, "the trajectory's state
changed" is true by construction.

To separate the operator's overwrite contribution from a genuine
basin-reaching effect of the perturbation text, we ran a paired
experiment with two perturbation modes:

- **`adversarial_doseN`** (overwrite, current behavior): injection
  text replaces step 15's output entirely. State at $X_{16}$ is the
  injection itself.
- **`adversarial_insert_doseN`** (NEW): injection text is prepended
  to the context for step 15's generation, but the model's normal
  output is preserved as $Y_{15}$. The injection text vanishes from
  context after this single step (single-step context augmentation).

Config: `configs/perturbation/O2_overwrite_vs_insert.yaml`,
$n=50$/cell × 5 conditions, paraphrase + replace operator.

**O2 results** (paraphrase + replace operator):

*Table, Insert-vs-overwrite switching at dose 80 / dose 200 for O2 (paraphrase + replace).*

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80` (overwrite) | **0.92** | [0.81, 0.97] |
| `adversarial_insert_dose80` | **0.32** | [0.21, 0.46] |
| `adversarial_dose200` (overwrite) | **0.98** | [0.90, 1.00] |
| `adversarial_insert_dose200` | **0.18** | [0.10, 0.31] |

**O3 results** (summarize + negate, replace operator), testing
whether the overwrite artifact generalises across replace-mode
operators:

*Table, Insert-vs-overwrite switching at dose 80 / dose 200 for O3 (summarize + negate, replace).*

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80` (overwrite) | **0.90** | [0.79, 0.96] |
| `adversarial_insert_dose80` | **0.18** | [0.10, 0.31] |
| `adversarial_dose200` (overwrite) | **0.92** | [0.81, 0.97] |
| `adversarial_insert_dose200` | **0.12** | [0.06, 0.24] |

(Sources:
`data/exp_perturb_O2_overwrite_vs_insert/reports/perturbation/switching_summary.csv`
and
`data/exp_perturb_O3_overwrite_vs_insert/reports/perturbation/switching_summary.csv`.)

**Finding (across both replace-mode regimes).** The overwrite vs
insert gap is **60-80 percentage points** for both O2 and O3:

*Table, $\Delta$ summary: overwrite minus insert switching for O2 and O3 at doses 80 and 200.*

| regime | dose | overwrite | insert | overwrite − insert |
|---|---:|---:|---:|---:|
| O2 | 80 | 0.92 | 0.32 | **+0.60** |
| O2 | 200 | 0.98 | 0.18 | **+0.80** |
| O3 | 80 | 0.90 | 0.18 | **+0.72** |
| O3 | 200 | 0.92 | 0.12 | **+0.80** |

When the operator no longer overwrites state, switching falls to
**12-32%**, well below the natural-floor estimate for O1 (~35%,
from §5.6.1) and far below the headline 90-98% from the original
sparse pilots. **Most of O2 and O3's reported "perturbation
transparency" is the replace operator overwriting state by
construction, not the perturbation text reaching a competing
basin.** The pattern is robust across the two replace-mode
operators (paraphrase preservation in O2 and content-degrading
summarize-and-negate in O3), confirming that the overwrite
contribution is **operator-independent within the two tested replace-mode operators (O2, O3)**.

O3's insert-mode rate (12-18%) is *lower* than O2's (18-32%),
suggesting that the summarize-and-negate template's strong content
constraint pulls trajectories *back* toward its absorbing template
even when the perturbation-prepended context tries to push elsewhere,
consistent with the §5.14 finding that O3 is template-absorbing
rather than semantic-absorbing. A proper insert-mode dose-response
with denser doses and family-cluster bootstrap would refine these
numbers.

**What this changes in the paper's claims.** Per the rewritten
Lemma 1 / Corollary 1 (§3.1.4), replace-mode regimes already had no
formal *injected-token* barrier; the formal bound is on the post-
injection generation budget $G_m$, not the injected-token cost
$\tau$. This empirical probe confirms the theoretical reframing:

- Under the §3.1.1 strict reading, $\mathrm{B}(B_1 \to B_2) = 0$
  for replace mode under mild assumptions (injected text not
  required), because each replace generation is a fresh basin-
  reaching attempt.
- The reported O2/O3 "94-100% switching" should be read as a
  *generation-budget* effect: at $m \ge 1$ replace step after
  injection, the system has high probability of being in some new
  basin, but the injection itself contributes only ~20% above the
  no-injection baseline once the operator's overwrite contribution
  is removed.
- The insert-mode result (~18-32% switching at dose 200) is the
  empirical analog of the "sparse" perturbation effect that should
  be compared to O1 / D1 raw switching for fair regime comparisons.

The original O2/O3 "near-zero injected-token barrier" reading
remains qualitatively correct as a description of the operator's
overwrite-induced transparency, but should not be presented as a
discovered low *behavioral* barrier in the dose-response sense
that O1 measurements use.

**Production architectures with the same structural property.** The analogous engineering case is any architecture in which accumulated state is periodically replaced by a generated summary, scratchpad, or "current task state". If untrusted tool output, repository text, package metadata, or commit messages are promoted into that replacement, the system has not merely been persuaded by the text; its previous state has been removed by the update rule. Such failures should be attributed to the memory policy as well as to the generator. The 60-80 percentage-point overwrite-vs-insert gap reported above is therefore not a curiosity of this experimental setup; it is the same mechanism active whenever a context-summarization or context-replacement step intervenes between the loop's initial state and its final response.

---

### §5.C, Secondary analyses

### 5.18 Cross-metric correlations

> **Caveat.** The correlations reported in this
> subsection are computed across only **n=4 regimes** (O1, O2, O3,
> D1). Four points cannot support a meaningful correlation statistic
> in any conventional sense, Pearson and Spearman *r/ρ* values for
> n=4 are extremely high-variance, the reported *p*-values are
> exploratory rather than confirmatory, and a single re-categorisation
> of any regime would change the picture substantially. We retain
> this section because the *signs* of the correlations agree with
> mechanistic predictions stated in advance, which is consistency
> evidence (not statistical evidence) for the taxonomy. **Treat the
> numerical *r/ρ* values in the table below as descriptive
> indicators, not as inferential tests.** A confirmatory n>20-regime
> sweep is future work.

The four regimes were *defined* by qualitative architecture × content
labels (append vs replace vs dialog × continue vs paraphrase vs
summarize+negate vs free vs drill-down). The four diagnostic-metric
families above (Lyapunov, sharpness-dim, recurrence, basin
predictability, perturbation switching) were *measured* independently.
A natural cross-check: do regimes that score high on one diagnostic
also score predictable ways on the others?

We compute three pre-registered correlations across the 4 regimes
(O1, O2, O3, D1) on canonical pub-scale values (see caveat above):

*Table, Cross-metric correlations (Pearson + Spearman) with pre-registered mechanistic predictions.*

| relation | Pearson *r* (p) | Spearman *ρ* (p) | mechanistic prediction |
|---|---:|---:|---|
| recurrence rate vs adversarial switching rate | **+0.981 (0.019)** | +0.800 (0.200) | high-recurrence regimes (tight periodic orbits) are easier to kick out of orbit by injection, confirmed |
| sharpness dim (late) vs lock-in step (smallest *k* with `acc(k) ≥ 0.7`) | +0.838 (0.162) | **+0.949 (0.051)** | low-effective-dimension regimes have fewer "free axes" the predictor must constrain, confirmed |
| ensemble λ₁ (late) vs adversarial switching rate | +0.613 (0.387) | +0.800 (0.200) | larger λ₁ → less contractive → more easily perturbed; sign correct but underpowered at n=4 |

The recurrence ↔ vulnerability correlation is striking: the regime
with the *highest* recurrence rate (O3, 0.92) is the *most vulnerable*
to perturbation (96% switching), and the regime with the *lowest*
recurrence rate (D1, 0.21) is among the *least vulnerable* (60%
switching). This is exactly what one would predict for a periodic
orbit: a tight cycle has a narrow attractor support; once injection
text knocks the trajectory off the cycle, there's no built-in
mechanism to re-find it. The append-mode contractive regime (O1,
recurrence 0.29) by contrast keeps the seed text in context and uses
it as a re-attractor signal.

The sharpness ↔ lock-in correlation is similarly mechanistic. Regimes
with low effective dimension (O2 ≈ 1.39, O3 ≈ 1.45) commit to a basin
in 0-1 steps (the late-window cluster is already determined by step
0); the high-dimensional regime D1 (sharpness ≈ 1.89) takes 26 steps
to reach `acc(k) ≥ 0.7`. The intermediate O1 (sharpness ≈ 1.70)
locks in at step 1.

As stated in the caveat at the head of this subsection, n=4
correlations are descriptive rather than inferential, the methodological
point is that the *signs* of all three correlations agree with the
mechanistic predictions stated in advance. We do not interpret the
*r* = +0.981 / *p* = 0.019 cell as a statistical significance result;
with n=4, the test has effectively no power to distinguish a
"real" correlation from one driven by a single regime's location in
the diagnostic space. We report it because consistency in sign and
ordering across three independently-measured metrics is at least
weak internal evidence that the four-regime taxonomy is *not* an
artifact of any single diagnostic, but the more rigorous version of
this claim requires a confirmatory ≥20-regime sweep.

### 5.19 Why exactly five regimes? An unsupervised-clustering check

The five-regime taxonomy was *defined* by qualitative architecture ×
content labels (continue × append, paraphrase × replace,
summarize+negate × replace, free dialog × append, drill-down dialog
× append). The diagnostic battery was *measured* independently. A
strong test of mechanistic distinctness: do the regimes recover from
unsupervised clustering of measured diagnostic vectors?

We assemble per-experiment feature vectors for 13 experiments
(4 phase-2 publication runs + 5 phase-1 pilots + 7 reduced-scope
T-sweep cells + 4 phase-3 perturbation pilots; D2 excluded because
its dynamics.csv was not generated for the small-N exploratory
experiment). Each vector contains five canonical diagnostics:

```
[recurrence_rate (pca10, context_tail),
 sharpness_dim_late, lambda_1_late,
 basin_predictability_acc(k=10),
 adversarial_switch_rate]
```

After standardization, k-means clustering at *k* ∈ {2, ..., 7} gives:

*Table, Internal-validation indices (silhouette, Calinski-Harabasz, Davies-Bouldin) by cluster count.*

| *k* | silhouette ↑ | Calinski-Harabasz ↑ | Davies-Bouldin ↓ |
|---:|---:|---:|---:|
| 2 | **0.575** | 13.4 | 0.65 |
| 3 | 0.568 | 21.3 | 0.59 |
| 4 | 0.521 | 24.7 | 0.39 |
| 5 | 0.477 | 34.3 | 0.34 |
| 6 | 0.478 | 46.5 | 0.21 |

Three internal-validation indices, three different optimal *k*: **2
by silhouette, 7 by Calinski-Harabasz, 6 by Davies-Bouldin**, i.e.,
no cluster-count emerges as uniformly optimal. The honest reading:
the bulk diagnostic vector (recurrence + sharpness + λ₁ + basin pred
+ adversarial switch) **partially recovers** the regime taxonomy but
does not cleanly resolve it. Specifically, the *k*=5 confusion
matrix (cluster vs ground-truth label):

*Table, $k{=}5$ confusion matrix: ground-truth regime label vs unsupervised cluster assignment.*

| ground-truth ↓ \ cluster → | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| O1 (n=8) | 0 | 4 | 2 | 0 | 1 |
| D1 (n=4) | 0 | 3 | 1 | 0 | 0 |
| O2 (n=2) | 0 | 0 | 0 | **1** | 0 |
| O3 (n=2) | **1** | 0 | 0 | 0 | 0 |

shows the substructure clearly:

- **O2 (cluster 3) and O3 (cluster 0)** each form their own
  singleton clusters, *bulk diagnostics resolve them individually*.
  This makes mechanistic sense: O2's period-2 oscillation and O3's
  near-singular absorbing state have very distinct recurrence /
  λ₁ / sharpness signatures (recurrence 0.88 vs 0.92; sharpness 1.39
  vs 1.45 with very different time-evolution patterns).
- **O1 and D1 share clusters 1 and 2**, *bulk diagnostics do not
  cleanly separate the contractive append regime from the
  dialogue-state-driven multi-basin dialog regime*. Their canonical values are
  too close: recurrence 0.29 vs 0.21, sharpness 1.70 vs 1.89,
  λ₁ 0.008 vs 0.011, basin pred 0.65 vs 0.61, adversarial switch
  0.54 vs 0.60. The differences exist but are small relative to
  intra-regime variance across phase-1 / phase-2 / T-sweep
  measurements.

This is the affirmative empirical content of why the perturbation
protocol matters: **bulk diagnostics underdetermine the regime
taxonomy at the O1/D1 boundary**. The mechanistic distinction
between O1 (content-anchored basin, finite barrier against
in-distribution adversarial text, no detectable barrier crossing
against out-of-distribution noise within the tested 5-400 token
range, §5.6) and D1 (style-anchored basin,
T-stable across {0.3..1.2}, modest barrier in any direction,
§5.4) emerges *only when one measures the cost of nudging*. Bulk
diagnostics tell you the regimes have similar drift, similar
contraction rate, similar locked-in late-window structure; the
perturbation protocol tells you the regimes respond *very*
differently to in-distribution adversarial input.

The five-regime taxonomy is therefore best understood as **the
partition recovered by the union of bulk diagnostics (which
distinguish O2 / O3 from each other and from append/dialog) and
perturbation barriers (which distinguish O1 from D1, and D1 from
D2 via §5.8's content-gravity test)**. Bulk diagnostics alone yield
~3 clusters; perturbation barriers alone wouldn't separate O2 from
O3 at this scale; the *combination* yields the full five-way split.

This finding is also why we describe the paper's headline
contribution as the perturbation-barrier protocol rather than the
regime taxonomy: the taxonomy is *underdetermined* without the
protocol, but *fully determined* with it.

(Cluster analysis: `scripts/regime_cluster_analysis.py`. Plots:
`data/aggregated/regime_cluster_analysis/cluster_scatter.png` (PCA-2
of feature space, colored by regime label) and
`data/aggregated/regime_cluster_analysis/cluster_dendrogram.png`
(Ward linkage). Feature matrix: `feature_matrix.csv` in the same
directory.)

![Figure 13. **Diagnostic feature-space clustering.** Left: PCA-2 projection of standardized 5-D diagnostic vectors, recurrence, late $\lambda_1$, sharpness dimension, basin-predictability accuracy, and adversarial switching rate, for 13 experiments, colored by regime label. Right: k-means internal-validity scores over $k=2,\ldots,7$. O2 and O3 appear separated in this feature space, while O1 and D1 overlap; the validity indices do not select a single cluster count matching the regime taxonomy. Source: `data/aggregated/regime_cluster_analysis/cluster_scatter.png`.](data/aggregated/regime_cluster_analysis/cluster_scatter.png)

### 5.20 Embedding-space invariance

A natural reviewer challenge: the regime taxonomy is defined on
embeddings from `text-embedding-3-small` (OpenAI, 1536-dim). Would
the regimes change with a different embedder? We test this by
re-embedding 5,000-step subsamples of 5 representative experiments
(one per regime: O1, O2, O3, D1, D2) under two alternative embedding
models and recomputing the canonical diagnostics:

- **`text-embedding-3-large`** (OpenAI, 3072-dim), within-vendor
  scale-up.
- **`all-mpnet-base-v2`** (sentence-transformers, 768-dim, local),
  cross-architecture, open-source.

Per-regime canonical diagnostics, all three embedders:

*Table, Regime-by-metric across embedders: small, large, and mpnet diagnostics.*

| regime | metric | small (1536d) | large (3072d) | mpnet (768d) |
|---|---|---:|---:|---:|
| O1 | recurrence_rate | 0.289 | 0.304 | 0.096 |
| O2 | recurrence_rate | 0.875 | 0.711 | 0.783 |
| O3 | recurrence_rate | 0.924 | 0.850 | 0.862 |
| D1 | recurrence_rate | 0.210 | 0.337 | 0.226 |
| D2 | recurrence_rate | 0.296 | 0.176 | 0.073 |
| O1 | sharpness_dim_late | 1.697 | 1.774 | 1.915 |
| O2 | sharpness_dim_late | 1.389 | 1.886 | 1.898 |
| O3 | sharpness_dim_late | 1.452 | 1.233 | 1.309 |
| D1 | sharpness_dim_late | 1.890 | 1.365 | 1.825 |
| D2 | sharpness_dim_late | n/a | n/a | n/a |
| O1 | basin_pred_acc(k=10) | 0.804 | 0.519 | 0.503 |
| O2 | basin_pred_acc(k=10) | 0.896 | 0.736 | 0.712 |
| O3 | basin_pred_acc(k=10) | 0.916 | 0.672 | 0.784 |
| D1 | basin_pred_acc(k=10) | 0.607 | 0.504 | 0.392 |
| D2 | basin_pred_acc(k=10) | n/a | 0.136 | 0.133 |

Spearman rank correlations of per-regime values, baseline vs
alternative embedder:

*Table, Spearman rank correlations of per-regime diagnostics across embedders.*

| diagnostic | vs `text-embedding-3-large` | vs `all-mpnet-base-v2` |
|---|---:|---:|
| recurrence rate | ρ = +0.60 | ρ = +0.60 |
| **basin predictability acc(k=10)** | ρ = **+0.80** | ρ = **+1.00** |
| sharpness_dim_late | ρ = −0.40 | ρ = +0.00 |

Three findings:

**(a) Basin predictability is fully invariant under embedder swap**
(*ρ* = +1.00 for `all-mpnet-base-v2`, +0.80 for
`text-embedding-3-large`). The regime ordering on basin predictability,
**replace-mode (O2, O3) > append (O1) > dialog (D1) > exploratory
D2**, is preserved exactly under cross-architecture embedding
substitution. This is the strongest cross-embedder invariance result
in our data: the property of the recursive dynamics that the basin
predictor measures (how much information about the late-window
attractor is already present at step 10) is *not* a property of one
specific embedding family.

**(b) Recurrence rate is partially invariant** (*ρ* = +0.60 in both
cases). The bimodal structure, replace-mode pair {O2, O3} above
0.71 in every embedder, append/dialog set {O1, D1, D2} below 0.34
in every embedder, is preserved unambiguously. The fine-grained
ordering within each cluster shifts modestly across embedders, but
the dominant high/low partition that distinguishes the replace-mode
regimes from the rest does not.

**(c) Sharpness dim_late is NOT invariant** (*ρ* = +0.00 vs mpnet,
−0.40 vs large). This is a real and worth-flagging finding: the
sharpness-dimension diagnostic, which depends on the dimensional
structure of the embedding space, is embedding-specific. Different
embedders give different orderings of regimes on this diagnostic.
The sharpness-dim claims in §11.2 / §5.2 should therefore be
interpreted as *measurements within the* `text-embedding-3-small`
*pipeline*, not as embedding-invariant properties of the recursive
dynamics. (D2's sharpness is NaN in all three embedders because the
exploratory-scale ensemble, only ~25 trajectories per family, is
too small to support the late-window covariance estimate.)

The headline conclusion: **the taxonomy's load-bearing distinction
between replace-mode regimes and append/dialog regimes is
embedding-invariant** (basin predictability ρ ≥ +0.80; recurrence
bimodal structure preserved). The taxonomy's *fine-grained* metrics
(O2 vs O3 at the basin-shape level; D1 vs O1 at the sharpness-dim
level) are partially or wholly embedding-dependent. This is consistent
with §5.19's finding that the perturbation barrier, a quantity
defined in token-space rather than embedding-space, is the
load-bearing diagnostic for separating the full five-regime
taxonomy.

(Full ablation: `scripts/embedding_ablation.py`, output at
`data/aggregated/embedding_ablation/results.csv`.)

![Figure 14. **Embedding-model ablation.** Bar plots compare three diagnostics across regimes after re-embedding subsamples with `text-embedding-3-small`, `text-embedding-3-large`, and `all-mpnet-base-v2`. Recurrence preserves the high/low split between replace-mode O2/O3 and append/dialog regimes across embedders, while sharpness dimension changes ordering. Basin-predictability remains more stable across embedders than sharpness dimension in this ablation. Source: `data/aggregated/embedding_ablation/comparison.png`.](data/aggregated/embedding_ablation/comparison.png)

### 5.21 Cross-model thesis verification

A more searching robustness test than §5.20: the embedding ablation
varies only the *measurement instrument* (the embedder) on the same
trajectories. The cross-generation replication varies the *system
under measurement*, re-running every one of the 37 experiment
configurations end-to-end with `gpt-4.1-nano` substituted for
`gpt-4o-mini` as the trajectory-generating model. We then encode the
paper's six main theses as machine-checkable predicates and evaluate
each on both models.

The six theses (`scripts/check_theses_cross_model.py`):

*Table, Pre-registered T1-T6 thesis predicates with publication-scale verdicts.*

| ID | Thesis | Predicate (publication-scale or pilot data) |
|---|---|---|
| T1 | Regime ordering on recurrence rate | O2 / O3 > 0.70 and O1 / D1 < 0.40; min(O2, O3) > max(O1, D1) |
| T2 | Replace-mode capitulation under perturbation | O2 + O3 pilot switching > 0.85 for neutral / lorem / adversarial |
| T3 | O1 contractive: out-of-distribution drift-floor band | O1 pilot control ≤ 0.05; neutral ∈ [0.10, 0.40]; lorem ∈ [0.10, 0.40] |
| T4 | O1 contractive: adversarial > out-of-distribution | O1 pilot adversarial switching > O1 pilot lorem switching |
| T5 | D1 dialogue-state-driven multi-basin susceptibility | D1 pilot neutral switching > 0.30 |
| T6 | Publication-scale verdict labels | O1 continue, O2 paraphrase-replace, O3 summarize-negate-replace, D1 dialog v2 carry expected (H1a, H1b) tuples |

Result: **6 / 6 PASS on gpt-4o-mini (baseline, by construction); 6 / 6 PASS on gpt-4.1-nano.**

Per-thesis diagnostic numbers, side by side:

*Table, Cross-model T1-T6 verdicts: gpt-4o-mini vs gpt-4.1-nano.*

| ID | gpt-4o-mini | gpt-4.1-nano | Δ |
|---|---|---|---|
| T1 | O1 0.272, O2 0.834, O3 0.905, D1 0.146 | O1 0.393, O2 0.840, O3 0.866, D1 0.168 | replace / append-or-dialog gap preserved |
| T2 | O2 adv 0.94, O3 adv 0.96 | O2 adv 0.94, O3 adv 0.88 | both > 0.85 capitulation threshold |
| T3 | control 0.00, neutral 0.24, lorem 0.18 | control 0.00, neutral 0.22, lorem 0.18 | drift floor essentially identical |
| T4 | adv 0.54 vs lorem 0.18 (margin +0.36) | adv 0.38 vs lorem 0.18 (margin +0.20) | direction holds; adversarial barrier is **smaller** on nano |
| T5 | D1 neutral 0.76 | D1 neutral 0.80, lorem 0.94 | direction holds; D1 dialogue-state susceptibility is **larger** on nano |
| T6 | (strong, weak / strong, not_supported / strong, not_supported / strong, weak) | identical tuples | exact-match on all 4 pub-scale headlines |

Two qualitative patterns emerge from the magnitude shifts:

1. **The smaller model has shallower contractive basins.** T4's
   adversarial-vs-out-of-distribution margin shrinks from +0.36 to
   +0.20, the in-distribution kick still wins, but with a smaller
   barrier signal. Operationally: nano's O1 needs less injected text
   to be dislodged. The token-cost ordering is preserved; the
   absolute token-cost is somewhat smaller.

2. **The smaller model's D1 dialogue-state basins are easier to flip.**
   T5's D1 neutral switching is 0.80 on nano (vs 0.76 on
   gpt-4o-mini), and D1 lorem switching jumps to 0.94 (the highest
   non-replace switching rate observed in either model). Stylistic
   commitments in dialog are looser on nano, content perturbations
   override style more readily.

Both shifts are mechanistically consistent with nano being a smaller,
less-stable contractive system: shallower wells, weaker style anchoring.
The **structural taxonomy (5 regimes, replace-vs-append-vs-
dialog separation, basin-character signatures) is preserved unchanged
between the two models.** Token-cost values shift by the amounts
above, but stay in the same ordinal relations the paper claims.

The full audit is reproducible end-to-end via three artifacts:
`COVERAGE_nano.csv` (artifact-presence matrix, 37 cells × 59 columns),
`RESULTS_nano.md` (per-cell numeric comparison vs the gpt-4o-mini
baseline), and `THESES_nano.md` (the per-thesis PASS / FAIL table
above with full predicate detail). All three are referenced from
§7.1 and regenerable via `scripts/build_coverage.py --filter
"exp_*_gpt4nano"`, `scripts/compare_cross_model.py`, and
`scripts/check_theses_cross_model.py`.

---
