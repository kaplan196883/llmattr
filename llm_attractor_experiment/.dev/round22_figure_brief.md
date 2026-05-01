# Figure-usage brief for round-22

## Currently referenced figures (9)
| Section | Tag | Path |
|---|---|---|
| §11.2 (Supp Extended Data Table 2) | Figure 1 | data/aggregated/dynamics_plots/regime_map_rolling_k3.png |
| §5.3 | Figure 2 | data/aggregated/basin_predictability_cross/cross_basin_predictability.png |
| §5.4 | Figure 3 | data/aggregated/perturbation_cross_regime/cross_switching_rates.png |
| §5.6 | Figure 5 | data/aggregated/perturbation_basin_hardening/basin_hardening.png |
| §5.12 | Figure 6 | data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png |
| §5.7 | Figure H | data/aggregated/multi_granularity_switching.png |
| §5.9 | Figure I | data/aggregated/per_family_ed50.png |
| §5.1 | Figure K | data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png |
| §5.10 | Figure 14 | data/aggregated/embedding_ablation/comparison.png |

Numbering is currently inconsistent (1,2,3,5,6,14,H,I,K). Should be renumbered cleanly.

## Available aggregate figures NOT yet referenced (30 candidates)

### Cross-experiment dynamics
- A_joint_tsne_rolling_k3.png — joint t-SNE of all experiments colored by regime
- B_trajectory_grid_rolling_k3.png — per-family trajectory grid (one panel per family)
- C_spread_timeline_rolling_k3.png — ensemble-spread (sigma_t) over steps, one curve per regime
- spread_trajectories_rolling_k3.png — sampled trajectories with spread bands

### Flow fields (per-regime PCA-2 vector fields)
- E_flow_fields_rolling_k3.png — combined flow-field summary
- E_flow_exp_dialog_D1_curious_helpful_rolling_k3.png
- E_flow_exp_dialog_D3_debate_advocate_skeptic_rolling_k3.png
- E_flow_exp_long_rolling_k3.png
- E_flow_exp_op_O2_paraphrase_replace_rolling_k3.png
- E_flow_exp_op_O3_summarize_negate_rolling_k3.png

### t-SNE flow fields (per-regime)
- E_tsne_flow_fields_rolling_k3.png — combined
- E_tsne_flow_exp_dialog_D1_*.png, _D3_*.png, _long_*.png, _op_O2_*.png, _op_O3_*.png

### t-SNE trajectories (per-regime)
- F_tsne_trajectories_*.png — 5 per-regime files (D1, D3, long, O2, O3)

### Predictability
- cross_basin_predictability_grid.png — basin-predictability grid (per-experiment panels)
- group_aware_basin_pred.png — leakage-aware basin predictability (THE leakage-free key result)
- t_sweep_basin_predictability.png — basin predictability as function of temperature

### Perturbation response
- dose_response.png — clean dose-response curve (the headline)
- cross_relaxation_curves.png — relaxation after perturbation
- multi_granularity_persistence.png — persistence under cluster granularity (key for §5.1)
- v_star_sensitivity.png — V* parameter-grid sensitivity (key for §5.12)

### Regime clustering and stability
- cluster_dendrogram.png — regime clustering dendrogram
- cluster_scatter.png — regime cluster scatter
- cross_t_sensitivity.png — cross-experiment temperature sensitivity
- seed_determinism_vs_T.png — control-control divergence vs T

## Per-experiment perturbation plots (also available in data/exp_*/reports/perturbation/)
For each of ~12 perturbation experiments, available figures include:
- bulk_landscape_pca.png — V(x) potential landscape per condition
- flow_skeleton_pca.png — flow with basin centers
- geodesic_skeleton_pca.png — geodesic minimum-cost paths between basins
- rg_dendrogram_pca.png — Ward-merge cloud-expansion dendrogram

