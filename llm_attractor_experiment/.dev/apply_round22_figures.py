"""Round-22: apply figure-placement plan from GPT-5.5.

Strategy:
1. Read ARTICLE.md.
2. Strip all existing markdown figure blocks (![...](...png)) from main body
   AND from §11 supplementary that overlap with our re-allocation.
3. Insert 15 main-body figures (Fig 1-15) at specified anchor strings.
4. Insert 12 Extended Data figures (ED Fig 1-12) at specified §11 anchors.
5. Write back.

Figure caption format: `![Fig N. **Title.** caption-prose Source: \`path\`.](path)`
Extended Data format: `![ED Fig N. **Title.** caption-prose Source: \`path\`.](path)`
"""
from __future__ import annotations

import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")


# ===== Main-body figures =====
# Each entry: (fig_num, title, caption, source, anchor_text)
# The figure block is INSERTED IMMEDIATELY AFTER the anchor_text in the file.

MAIN_FIGURES = [
    (1, "Headline perturbation dose response",
     "Summary dose-response view for recursive-loop perturbations, emphasizing that raw switching, stochastic floor, and persistent escape are distinct endpoints. The figure orients the reader before the formal endpoint definitions.",
     "data/aggregated/perturbation_dose_response/dose_response.png",
     "is jointly determined by model, memory policy, perturbation content, and persistence criterion."),
    (2, "Dense O1 adversarial ED50 fit",
     "O1 append-mode adversarial dose response from the dense confirmatory rerun, with 8 doses x $n=200$ per cell. Black points are observed switching rates with family-cluster bootstrap 95% CIs; the blue curve is a 4-parameter logistic fit (`a=0.69, d=0.28, b=1.16, ED50=36 tok`); the dashed red line marks the bootstrap-median ED50 = 52 tokens [CI 8.5, 242].",
     "data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png",
     "| Family-cluster bootstrap median | 52 | 95% CI [8.5, 242] |"),
    (3, "Persistent escape under cluster granularity",
     "Persistent-escape rates recomputed under K-means $k=12$, K-means $k=4$, and HDBSCAN. No clustering convention reaches the 50% persistent-escape threshold up to 400 injected tokens.",
     "data/aggregated/multi_granularity_persistence.png",
     "| 400 | 16.0% | 10.0% | 39.5% | 68.5% |"),
    (4, "Post-perturbation relaxation and recovery",
     "Relaxation curves after perturbation show that many trajectories move transiently but do not remain in the injected post-jump basin. The curves support the distinction between raw switching and durable escape.",
     "data/aggregated/perturbation_cross_regime/cross_relaxation_curves.png",
     "Even among trajectories that visibly jump at injection, roughly half do not remain in the post-injection basin."),
    (5, "Cross-regime perturbation switching",
     "Final-cluster switching rates across append, replace, and dialog perturbation pilots. Replace-mode O2/O3 saturation should be read as overwrite-protocol sensitivity, not as a clean injected-token barrier.",
     "data/aggregated/perturbation_cross_regime/cross_switching_rates.png",
     "| D2, drill-down dialog | 0% [0-13] | n/a | n/a | 64% [44-80] |"),
    (6, "Leakage-aware basin predictability",
     "Group-aware basin-predictability with prompt families held out across folds. O1 remains the strongest leakage-free predictability result, while O2, O3, and D1 drop substantially under family-held-out validation.",
     "data/aggregated/group_aware_basin_pred.png",
     "| `exp_pub_D1_dialog_curious_helpful_v2` | D1, dialogue-state multi-basin | n/a | 0.604 | 0.336 | +0.269 | 0.69 | 0.77 |"),
    (7, "Cross-experiment dynamics map",
     "Regime-level map in late-window $\\lambda_1$ versus sharpness-dimension space, showing broad separation of replace, append, and dialog regimes. The plot is diagnostic rather than endpoint-defining.",
     "data/aggregated/dynamics_plots/regime_map_rolling_k3.png",
     "The qualitative regime separation survives. O3 and O2 remain high-recurrence replace-mode regimes, O1 remains a cross-family contractive append regime, and D1 remains a slower, more family-sensitive dialog regime. The main correction is evidential: stratified accuracies should be read as upper bounds, and the leakage-aware columns are the relevant values for cross-family generalization."),
    (8, "Basin hardening by injection time",
     "Switching rates for early, middle, and late injections in O1 and D1, with $n=50$ per cell and 95% Wilson confidence intervals. D1 shows partial late hardening, whereas O1 adversarial append perturbations remain approximately flat across injection time.",
     "data/aggregated/perturbation_basin_hardening/basin_hardening.png",
     "while D1 becomes harder to redirect late in the trajectory."),
    (9, "Switching under alternative basin granularities",
     "Perturbation switching recomputed under K-means $k=12$, K-means $k=4$, and HDBSCAN. The O1 adversarial-versus-OOD contrast is robust across granularities, while D1 is more granularity-sensitive.",
     "data/aggregated/multi_granularity_switching.png",
     "D1 is the most granularity-sensitive, consistent with its family-leakage and dialog-state dependence."),
    (10, "Per-family O1 adversarial dose response",
     "Family-level sparse O1 adversarial dose curves with $n=10$ trajectories per family-dose cell. Heterogeneity behind the population-level ED50 explains the wide family-cluster bootstrap interval.",
     "data/aggregated/per_family_ed50.png",
     "Future replications should increase the number of prompt families rather than only the number of ICs per family."),
    (11, "Embedding-model ablation",
     "Diagnostics recomputed under `text-embedding-3-small`, `text-embedding-3-large`, and `all-mpnet-base-v2`. Basin predictability and coarse recurrence ordering are more stable than sharpness dimension.",
     "data/aggregated/embedding_ablation/comparison.png",
     "The fine-grained sharpness-dimension ordering should be interpreted only within the original `text-embedding-3-small` measurement pipeline."),
    (12, "V* parameter-grid sensitivity",
     "Sensitivity of empirical potential-barrier summaries across KDE bandwidth, grid resolution, and basin-count settings. The ordinal pattern is more stable than the absolute $V^\\star$ values, so density landscapes remain descriptive rather than calibrated.",
     "data/aggregated/v_star_sensitivity.png",
     "A single numerical $V^\\star$ value is therefore not stable enough to quote as a calibrated barrier."),
    (13, "Regime clustering in diagnostic space",
     "Scatter view of regime diagnostic vectors used in the unsupervised five-regime check. Bulk geometry separates replace-mode regimes from append/dialog regimes but does not by itself recover the full five-way taxonomy.",
     "data/aggregated/regime_cluster_analysis/cluster_scatter.png",
     "O1 and D1 have similar recurrence, contraction, and basin-predictability values at this diagnostic resolution."),
    (14, "Regime-clustering dendrogram",
     "Hierarchical clustering of regime-level diagnostic summaries. The dendrogram reinforces that the five-regime taxonomy is not obtained from bulk diagnostics alone and requires perturbation endpoints for separation.",
     "data/aggregated/regime_cluster_analysis/cluster_dendrogram.png",
     "The perturbation protocol is what separates them: O1 shows content-dependent adversarial raw switching with out-of-distribution resistance, while D1 is broadly susceptible to dialog-state redirection and hardens with time. D2 is then distinguished by drill-down content gravity."),
    (15, "Cross-experiment temperature sensitivity",
     "Temperature-sensitivity summary across reduced-scope cells. These results remain explicitly secondary because absolute O1 values are scope-confounded relative to the publication-scale anchor.",
     "data/aggregated/t_sensitivity_cross_regime/cross_t_sensitivity.png",
     "so O1 absolute temperature values are scope-confounded. The full temperature sweep is retained as exploratory secondary material in the released aggregate tables."),
]


# ===== Extended Data figures (in §11) =====
# (ed_num, title, caption, source, anchor_text)

ED_FIGURES = [
    (1, "Joint t-SNE regime map",
     "Joint t-SNE visualization of all publication-scale experiments colored by regime. The view supports qualitative inspection of regime separation but is not used for quantitative endpoint claims.",
     "data/aggregated/dynamics_plots/A_joint_tsne_rolling_k3.png",
     "These are reference implementations only; the executable, test-\ncovered code lives at `src/analysis/` and `src/experiments/dynamics/`."),
    (2, "Per-family trajectory grid",
     "Shared-coordinate trajectory grid by prompt family. The figure supports visual inspection of family-level heterogeneity without serving as a primary endpoint.",
     "data/aggregated/dynamics_plots/B_trajectory_grid_rolling_k3.png",
     "ED-FIG-1-PLACEHOLDER"),
    (3, "Ensemble-spread timeline",
     "Ensemble spread over recursive steps, grouped by regime. The plot supplements the finite-time ensemble-spread diagnostics used in the attractor audit.",
     "data/aggregated/dynamics_plots/C_spread_timeline_rolling_k3.png",
     "ED-FIG-2-PLACEHOLDER"),
    (4, "Combined PCA flow fields",
     "Combined empirical PCA-2 flow-field summary across regimes. Flow fields are useful qualitative checks on local motion but are not primary decision endpoints.",
     "data/aggregated/dynamics_plots/E_flow_fields_rolling_k3.png",
     "Wall-time per animation: ~80s vs ~11 min single-threaded."),
    (5, "Combined t-SNE flow fields",
     "t-SNE-space flow-field visualization used for qualitative comparison with the PCA-2 flow summaries.",
     "data/aggregated/dynamics_plots/E_tsne_flow_fields_rolling_k3.png",
     "ED-FIG-4-PLACEHOLDER"),
    (6, "Original stratified basin-predictability curves",
     "Stratified-CV basin-predictability curves are retained for audit but should be interpreted alongside the leakage-aware GroupKFold results in main-text Fig 6.",
     "data/aggregated/basin_predictability_cross/cross_basin_predictability.png",
     "Source: §11.1, `data/aggregated/group_aware_basin_pred.csv`."),
    (7, "Basin-predictability grid",
     "Per-experiment basin-predictability panels showing how predictability varies across regimes and observables. The grid expands the main leakage-aware summary without replacing it.",
     "data/aggregated/basin_predictability_cross/cross_basin_predictability_grid.png",
     "ED-FIG-6-PLACEHOLDER"),
    (8, "Temperature-sweep basin predictability",
     "Basin predictability as a function of sampling temperature. These reduced-scope cells are exploratory and are not used as primary evidence for temperature effects.",
     "data/aggregated/t_sweep_basin_predictability/t_sweep_basin_predictability.png",
     "ED-FIG-7-PLACEHOLDER"),
    (9, "Representative O1 perturbation potential landscapes",
     "PCA-2 density landscapes for the O1 perturbation pilot under control, neutral, lorem, and adversarial conditions. The landscapes are descriptive geometry, not calibrated token barriers.",
     "data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png",
     "Per-geodesic raw values are written\nalongside the figures to `geodesic_barriers_pca.csv`. Reading:"),
    (10, "Representative O1 geodesic skeleton",
     "Geodesic minimum-cost paths between detected basin centers for the O1 perturbation pilot. The figure illustrates how $V^\\star$ summaries are constructed.",
     "data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png",
     "ED-FIG-9-PLACEHOLDER"),
    (11, "Representative O1 RG dendrogram",
     "Ward-merge cloud-expansion dendrogram for the O1 perturbation pilot. The figure supplements the geometric-barrier table with an independent view of condition-wise cloud expansion.",
     "data/exp_perturb_O1_pilot/reports/perturbation/rg_dendrogram_pca.png",
     "**O1 adversarial mildly\ncompresses** (2.06 vs 2.38) - in-distribution adversarial text\npulls into a tighter region."),
    (12, "Seed determinism versus temperature",
     "Control-control divergence as a function of temperature, used to contextualize stochastic floors. The figure supports the endpoint rule that raw switching must be interpreted against paired controls.",
     "data/aggregated/t_sensitivity_cross_regime/seed_determinism_vs_T.png",
     "ED-FIG-8-PLACEHOLDER"),
]


def make_figure_block(num: int, title: str, caption: str, source: str,
                      ed: bool = False) -> str:
    prefix = f"ED Fig {num}" if ed else f"Fig {num}"
    text = (
        f"![{prefix}. **{title}.** {caption} "
        f"Source: `{source}`.]({source})"
    )
    return text


def main() -> int:
    text = ARTICLE.read_text(encoding="utf-8")

    # === Step 1: strip all existing figure blocks ===
    pat = re.compile(r"!\[Figure[^\]]*\]\([^)]+\.png\)\n*", re.DOTALL)
    n_before = len(pat.findall(text))
    text = pat.sub("", text)
    print(f"stripped {n_before} existing figure blocks")

    # Collapse multiple blank lines that may result
    text = re.sub(r"\n{3,}", "\n\n", text)

    # === Step 2: insert main-body figures by anchor ===
    # Insert in REVERSE order so earlier anchors don't shift later anchors
    # (they don't shift if anchors are unique strings, but reverse-order is
    # safe in any case).
    inserted_main = 0
    placeholders: list[tuple[int, str]] = []  # (fig_num, search_anchor)
    for fig_num, title, caption, source, anchor in MAIN_FIGURES:
        block = make_figure_block(fig_num, title, caption, source, ed=False)
        i = text.find(anchor)
        if i == -1:
            print(f"WARN main Fig {fig_num} anchor not found: {anchor[:80]!r}")
            continue
        # Insert AFTER the anchor + a paragraph break
        insertion = f"\n\n{block}\n"
        text = text[:i + len(anchor)] + insertion + text[i + len(anchor):]
        # Save unique placeholder anchor for ED figures that depend on this
        placeholders.append((fig_num, block))
        inserted_main += 1
    print(f"inserted {inserted_main}/{len(MAIN_FIGURES)} main-body figures")

    # === Step 3: insert ED figures by anchor ===
    # Some ED figures use placeholders that point to previously-inserted ED
    # figures' block text. Resolve those.
    ed_block_by_num: dict[int, str] = {}
    inserted_ed = 0
    for ed_num, title, caption, source, anchor in ED_FIGURES:
        block = make_figure_block(ed_num, title, caption, source, ed=True)
        ed_block_by_num[ed_num] = block

        # Resolve placeholder anchors
        if anchor.startswith("ED-FIG-") and anchor.endswith("-PLACEHOLDER"):
            ref_num = int(anchor.replace("ED-FIG-", "").replace("-PLACEHOLDER", ""))
            anchor = ed_block_by_num.get(ref_num, "")
            if not anchor:
                print(f"WARN ED Fig {ed_num} placeholder ED-FIG-{ref_num} not yet inserted")
                continue

        i = text.find(anchor)
        if i == -1:
            print(f"WARN ED Fig {ed_num} anchor not found: {anchor[:80]!r}")
            continue
        insertion = f"\n\n{block}\n"
        text = text[:i + len(anchor)] + insertion + text[i + len(anchor):]
        inserted_ed += 1
    print(f"inserted {inserted_ed}/{len(ED_FIGURES)} ED figures")

    # === Step 4: cleanup multiple blank lines ===
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    ARTICLE.write_text(text, encoding="utf-8")

    # === Verification ===
    n_main = len(re.findall(r"!\[Fig \d+\.", text))
    n_ed = len(re.findall(r"!\[ED Fig \d+\.", text))
    print(f"\nVerification: {n_main} main-body figures, {n_ed} ED figures")
    print(f"Total: {n_main + n_ed} figures (target: 27)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
