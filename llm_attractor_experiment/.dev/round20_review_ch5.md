# Review of §5 Results

1. **Issue — The headline result is still buried at §5.6/§5.15/§5.17.**  
   **Why it matters:** The paper's most important contribution is not the regime taxonomy; it is the corrected perturbation endpoint: raw ED50 ≈ 40 tokens, stochastic floor ≈ 35%, persistent escape not reached, and replace-mode switching largely explained by overwrite mechanics. At present, the reader reaches the dense ED50 only after pilots, temperature sweep, perturbation pilots, and aggregation machinery, and only understands its real interpretation nine subsections later in §5.15 and §5.17.  
   **Concrete fix:** Reorder §5 so the first substantive Results subsection is a combined primary endpoint: **"Adversarial append perturbations produce raw switching but not persistent escape."** Merge the dense ED50 result from §5.6.1 with the dense persistence analysis from §5.15. Immediately follow with **"Replace-mode switching is mostly overwrite, not injected-token barrier crossing"** using §5.17. Then present regime establishment. This makes the paper read as: *what was discovered → why the naive interpretation is wrong → how the regimes contextualize it*.

2. **Issue — §5.5 currently overstates replace-mode "perturbation transparency" before §5.17 retracts much of it.**  
   **Why it matters:** §5.5 says O2/O3 are "perturbation-transparent" at 94–100% switching. §5.17 later shows that, under insert rather than overwrite, switching drops to 12–32%. That is not a minor robustness check; it changes the mechanism. A reviewer will read §5.5 as a claim that is later partially contradicted.  
   **Concrete fix:** Either move §5.17 directly after §5.5, or rewrite §5.5 so the first mention of replace-mode switching already says: "These near-saturated rates are later decomposed in §5.17 and are mostly attributable to the overwrite update rule." Ideally, collapse §5.5 and §5.17 into a single subsection titled **"Replace-mode fragility is primarily a memory-policy effect."**

3. **Issue — The leakage caveat appears too late.**  
   **Why it matters:** §5.3 reports acc(k=10) values such as O1 = 0.80, O2 = 0.90, O3 = 0.92, D1 = 0.61. §5.11 later reveals that O2/O3/D1 suffer 27–30 percentage points of family leakage under StratifiedKFold. The first table is therefore not wrong, but it is an upper-bound result that needs to be labelled at first exposure.  
   **Concrete fix:** In §5.3, add group-aware accuracy columns directly beside the stratified values, at least for k=10: O1 0.803→0.732, O2 0.896→0.596, O3 0.912→0.629, D1 0.604→0.336. Change the §5.3 claim from "basin predictability gives a clean ordering" to "stratified basin predictability gives an upper-bound ordering; leakage-free generalization preserves above-chance signal but changes the ordering." Then shorten §5.11 to a stress-test elaboration rather than the first disclosure.

4. **Issue — The dense ED50 and persistence endpoint should be one result, not separated across §5.6.1 and §5.15.**  
   **Why it matters:** The key scientific point is the contrast between raw switching and durable escape. Presenting raw ED50 in §5.6.1 and the persistence failure much later invites readers to remember only "ED50 ≈ 40 tokens," which is exactly the over-simple interpretation the revision is trying to avoid.  
   **Concrete fix:** Create a single table with four columns: dose, raw switch rate, net effect above natural floor, persistent-escape rate. The headline should be: **raw ED50 ≈ 40 tokens; net effect never reaches +50 pp; persistent escape never reaches 50% up to 400 tokens.** Put the persistence figure immediately after the ED50 curve.

5. **Issue — The sparse dose-response pilots are placed before the confirmatory dense result and still carry too much interpretive weight.**  
   **Why it matters:** §5.6 describes the n=50 sparse grid and says the 50% switching dose lies between 80 and 400 tokens, then §5.6.1 shows this was a coarse-grid artifact and localizes raw ED50 near 40 tokens. The narrative asks the reader to learn a preliminary result and then revise it.  
   **Concrete fix:** Lead with the dense rerun. Recast the sparse dose-response as historical breadth: "The sparse pilot motivated the dense rerun and showed content-specificity, but its ED50 estimate was not retained." Move the sparse tables to Extended Data or make them a short paragraph after the dense result.

6. **Issue — §5.10 geometric barriers and §5.16 V\* sensitivity duplicate each other and risk confusing the main claim.**  
   **Why it matters:** §5.10 already says V\* is descriptive, not quantitative validation; §5.16 then proves parameter sensitivity. The combined effect is lengthy and somewhat circular. Worse, readers may still search for a V\*↔ED50 validation even though the text says it does not survive quantitative scrutiny.  
   **Concrete fix:** Merge §5.10 and §5.16 into one compact secondary subsection: **"Density-landscape summaries are descriptive and ordinal only."** Keep one representative figure, one sentence on parameter-grid CV 14–24%, and one sentence on ordinal stability. Move the multiple PCA/t-SNE/flow/animation figures, V\* tables, and sensitivity grid to §11 as Extended Data.

7. **Issue — Several current main-text subsections are supplementary by Nature/Science standards.**  
   **Why it matters:** The chapter is audit-grade, but the main Results section is overburdened. The most important claims compete with scripts, aggregation details, pilot history, sensitivity grids, n=4 correlations, and exploratory clustering. This dilutes the headline.  
   **Concrete fix:** Move or compress as follows:  
   - Move §5.1 and §5.2 fully to §11; retain one sentence that pilots motivated the taxonomy.  
   - Move §5.9 aggregation scripts to Methods/Data availability or §11.  
   - Move §5.16 into Extended Data after merging its conclusion into §5.10.  
   - Move §5.18 n=4 cross-metric correlations to §11 or Discussion as "consistency checks."  
   - Move most of §5.19 unsupervised clustering to §11, retaining only the conclusion that bulk diagnostics alone do not resolve O1/D1.  
   This would leave the main Results focused on endpoints, regime establishment, perturbation mechanisms, and essential robustness.

8. **Issue — §5.4 temperature sweep is over-positioned relative to its evidential strength.**  
   **Why it matters:** The subsection itself says the O1 temperature claim is N-confounded and exploratory. Yet it appears early in primary results, before the perturbation dose-response, and claims to be the "first quantitative diagnostic distinguishing the regimes." That is too strong given the caveat.  
   **Concrete fix:** Move §5.4 to secondary analyses or compress it to a short paragraph after the primary perturbation results. Change the claim to: "At matched reduced scope, D1 showed narrower temperature variation than O1, but O1 absolute values are scope-confounded." Do not let this precede the ED50/persistence/overwrite findings.

9. **Issue — §5.14 semantic inspection is valuable but too long for main Results.**  
   **Why it matters:** The semantic inspection materially improves the taxonomy: O1 is register-contractive, O2 family-preserving, O3 template-absorbing, D1 dialogue-state-driven. But the long per-cluster tables consume disproportionate space and interrupt the statistical robustness sequence.  
   **Concrete fix:** Keep a concise main-text summary table with four rows: regime, basin axis, mechanism, taxonomy implication. Move the cluster-by-cluster inventories to Extended Data. This preserves the interpretive correction without overwhelming the Results section.

10. **Issue — §5.21 cross-model verification is coherent in form but misaligned with the revised headline.**  
    **Why it matters:** The six thesis predicates largely test the older taxonomy/pilot claims: recurrence ordering, replace-mode capitulation, O1 OOD band, O1 adversarial > lorem, D1 susceptibility, publication labels. They do not directly test the round-20 headline: dense ED50, stochastic floor, persistent-escape failure, and overwrite-vs-insert gap. As written, "6/6 PASS" sounds stronger than the actual replication of the core endpoint.  
    **Concrete fix:** Reframe §5.21 as **"cross-generator audit of regime-level qualitative claims,"** not full replication of the endpoint. Add a short table saying which headline claims were and were not replicated on gpt-4.1-nano. If dense ED50/persistence/overwrite were not rerun, state that explicitly. If possible, add predicates for overwrite-vs-insert and persistent escape; otherwise, lower the rhetoric from "thesis verification" to "cross-model consistency check."

11. **Issue — Numerical claim density is too high for reader retention.**  
    **Why it matters:** Many subsections include full tables, Wilson intervals, file paths, scripts, caveat boxes, figure paths, and interpretive prose. The auditability is excellent, but the main text becomes hard to parse. A reviewer may conclude that the authors are burying the clean result under verification machinery.  
    **Concrete fix:** For each main subsection, enforce a one-claim structure: one headline sentence, one compact estimate/effect size, one figure or table, one caveat if needed. Move source paths, script names, exhaustive CIs, and row-by-row audit details to Extended Data or Methods. Preserve reproducibility, but separate it from narrative results.

12. **Issue — The current §5.A/§5.B/§5.C hierarchy is good, but the subsection numbering still reflects discovery order rather than evidential order.**  
    **Why it matters:** The reader does not need to experience the project chronology. They need to see the causal evidential chain: primary endpoint → corrected mechanism → regime context → robustness → secondary checks. Discovery-order numbering makes pilots and exploratory analyses appear more central than they are.  
    **Concrete fix:** Consider renumbering the main Results around an evidential sequence, even if old anchors are preserved in §11. A strong order would be:  
    1. Dense O1 adversarial dose-response and persistence failure.  
    2. Replace-mode overwrite-vs-insert mechanism.  
    3. Publication-scale regime establishment with leakage-aware basin predictability.  
    4. Perturbation content, timing, and D2 content gravity.  
    5. Cluster/granularity/semantic robustness.  
    6. Embedder and cross-generator checks.  
    7. Secondary/supplementary analyses.

## Verdict

The chapter now contains the right scientific corrections, but the main result is still not sequenced with maximum force. The highest-priority editorial move is to put raw ED50, stochastic floor, persistence failure, and overwrite mechanics at the front, then demote geometric, correlation, unsupervised, pilot, and aggregation material to Extended Data. With that restructuring, §5 would read less like a lab audit and more like a decisive Results section while preserving the paper's unusually strong reproducibility trail.
