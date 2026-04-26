# Data index

Catalog of every experiment under `data/`, organized by phase. Names are
historical and not always uniform (see "Naming notes" at the end). Each
experiment dir holds:

- `config.yaml` — frozen config snapshot used for the run
- `raw/steps.jsonl` — per-step trajectory records (LFS-tracked)
- `raw/manifest.json` — completion status per (family, ic, run)
- `embeddings/<observable>/{embeddings.npy,metadata.parquet}` — derived (gitignored, regen via `embed`)
- `metrics/`, `reports/` — analysis outputs (regen via `analyze`)

## Phase 0 — early one-offs

Pre-pipeline exploratory runs from REPORT1/2. Kept for historical comparison.

| dir | regime | notes |
|---|---|---|
| `exp_default/` | O1 continue (T=0.8) | First run; baseline that REPORT1 was written against |
| `exp_long/` | O1 continue, longer | 60-step horizon test (REPORT2) |
| `exp_noclip/` | O1 continue, no context clip | Ablation referenced in REPORT2 |

## Phase 1 — pilot dialog and operator experiments (`exp_dialog_*` / `exp_op_*`)

First proper runs of the full pipeline against the dialog-mode and
operator-mode regimes. Most are **superseded by Phase 2 publication runs**;
keep them only if you specifically need the smaller pilot cohort.

| dir | regime | superseded by |
|---|---|---|
| `exp_dialog_D1_curious_helpful/` | D1 free dialog | `exp_pub_D1_dialog_curious_helpful_v2/` |
| `exp_dialog_D2_replace_curious_helpful/` | D2-replace dialog (different from D2 drill-down!) | (none) |
| `exp_dialog_D3_debate_advocate_skeptic/` | D3 debate dialog | (none) |
| `exp_op_O1_continue/` | O1 continue (append) | `exp_pub_O1_continue/` |
| `exp_op_O2_paraphrase_replace/` | O2 paraphrase + replace | `exp_pub_O2_paraphrase_replace/` |
| `exp_op_O3_summarize_negate/` | O3 summarize + negate (no replace) | (none — distinct from O3b) |
| `exp_op_O3b_summarize_negate_replace/` | O3 summarize + negate + replace | `exp_pub_O3_summarize_negate_replace/` |
| `exp_op_O4_paraphrase_append/` | O4 paraphrase + append | (none) |

## Phase 2 — publication-scale runs (`exp_pub_*`)

Bigger sample (5 families × 30 ICs × 3 runs × 40 steps = 1350 trajectories
per regime) for the final attractor-classification figures. Source-of-truth
for the diagnostic four regimes.

**Diagnostic regimes:**

| dir | regime | notes |
|---|---|---|
| `exp_pub_D1_dialog_curious_helpful_v2/` | D1 dialog (free) | "v2" = REPORT5 anchor; v1 (`exp_pub_D1_dialog_curious_helpful`) was the smaller pilot |
| `exp_pub_O1_continue/` | O1 continue (append, contractive) | REPORT5 anchor |
| `exp_pub_O2_paraphrase_replace/` | O2 paraphrase + replace (oscillatory 2-cycle) | REPORT5 anchor |
| `exp_pub_O3_summarize_negate_replace/` | O3 summarize + negate + replace (absorbing) | REPORT5 anchor |

**Temperature sweeps (basin_predictability vs T):**

| dir | regime | T |
|---|---|---|
| `exp_pub_D1_Tsweep_T03/` | D1 dialog | 0.3 |
| `exp_pub_D1_Tsweep_T06/` | D1 dialog | 0.6 |
| `exp_pub_D1_Tsweep_T12/` | D1 dialog | 1.2 |
| `exp_pub_O1_Tsweep_T03/` | O1 continue | 0.3 |
| `exp_pub_O1_Tsweep_T06/` | O1 continue | 0.6 |
| `exp_pub_O1_Tsweep_T08/` | O1 continue | 0.8 |
| `exp_pub_O1_Tsweep_T12/` | O1 continue | 1.2 |

(D1 v2 covers T=0.8; O1_continue covers T=0.8 as well.)

## Phase 3 — perturbation experiments (`exp_perturb_*`)

REPORT6 work: inject text mid-trajectory to test whether basins can be
hijacked. Each has 4 conditions (`control`, `neutral`, `lorem`,
`adversarial`) unless noted.

**Diagnostic pilots (override at step 15):**

| dir | regime | conditions |
|---|---|---|
| `exp_perturb_D1_pilot/` | D1 dialog | 4 |
| `exp_perturb_O1_pilot/` | O1 continue | 4 |
| `exp_perturb_O2_pilot/` | O2 paraphrase replace | 4 |
| `exp_perturb_O3_pilot/` | O3 sum-negate replace | 4 |

**Dose-response (perturbation amount):**

| dir | base regime | doses (tokens) |
|---|---|---|
| `exp_perturb_D1_dose/` | D1 / neutral | 20, 80, 200, 400 |
| `exp_perturb_D1_dose_fine/` | D1 / neutral | 5, 10, 15 (sub-token-saturation regime) |
| `exp_perturb_O1_dose/` | O1 / neutral | 20, 80, 200, 400 |
| `exp_perturb_O1_dose_adversarial/` | O1 / adversarial | 20, 80, 200, 400 |

**Injection-time sweep (basin hardening):**

| dir | base regime | inject step |
|---|---|---|
| `exp_perturb_D1_inject_t5/` | D1 / neutral @80 | 5 |
| `exp_perturb_D1_inject_t25/` | D1 / neutral @80 | 25 |
| `exp_perturb_O1_inject_t5/` | O1 / adversarial @200 | 5 |
| `exp_perturb_O1_inject_t25/` | O1 / adversarial @200 | 25 |

(Step 15 baselines come from the pilots above.)

**Drill-down dialog (D2 exploratory):**

| dir | regime | notes |
|---|---|---|
| `exp_D2_exploratory_drilldown/` | D2 drill-down dialog (50 steps) | Base run; source for adversarial perturbation in `exp_perturb_D2_exploratory` |
| `exp_perturb_D2_exploratory/` | D2 drill-down + perturb | 50 steps, override at 25, 25-step relaxation; control + adversarial only |

## Aggregated cross-experiment outputs

Under `data/aggregated/` (also gitignored, regenerable):

- `dynamics_plots/`, `dynamics_cross_experiment.csv` — cross-experiment dynamical-systems metrics
- `basin_predictability_cross/` — cross-regime basin-predictability comparison
- `t_sweep_basin_predictability/` — D1 T-sweep comparison
- `t_sensitivity_cross_regime/` — O1 vs D1 T-sweep comparison
- `perturbation_cross_regime/` — switching rates + relaxation curves across O1/O2/O3/D1/D2
- `perturbation_dose_response/` — dose-response curves (D1 + O1)
- `perturbation_basin_hardening/` — injection-time vs switching curves

## Naming notes

The naming is **historically inconsistent** because the experiment phases
were added incrementally:

- Phase 0 (`exp_default`, `exp_long`, `exp_noclip`) — no prefix beyond `exp_`
- Phase 1 (`exp_dialog_*`, `exp_op_*`) — phase-implied-by-regime prefix
- Phase 2 (`exp_pub_*`) — explicit phase prefix
- Phase 3 (`exp_perturb_*`) — explicit phase prefix
- Outlier: `exp_D2_exploratory_drilldown` (no `pub_` prefix despite being
  publication-grade — added late in the project)

Renaming is technically possible but would require updating LFS objects,
30+ embedded `experiment_id` fields in config snapshots, multiple scripts,
and several REPORT references. The cost-reward of renaming ~10 dirs for
prefix uniformity is not currently worth it. **Use this index instead.**
