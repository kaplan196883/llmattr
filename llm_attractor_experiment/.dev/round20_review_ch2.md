# Review of §2 Background and related work

1. **Issue — The gap is correct but buried in §2.3.**  
   The clearest statement of what the paper adds appears only after two subsections and a long comparison table: state/generator/nudge separation, token-quantified barriers, and dialog-specific regimes.

   **Why it matters** — Readers encounter §2 first as a sequence of adjacent literatures rather than as an argument. Nature/Science-style reviewing will ask: "What is the missing capability in the field?" That answer should frame the section from the start.

   **Concrete fix** — Add a short gap-setting paragraph at the beginning of §2, before §2.1, and then shorten §2.3 accordingly:

   > Existing work has begun to describe recursive LLM inference as a dynamical system, identifying convergence, cycling, divergence, and dimensional collapse in semantic space. What remains under-specified is the *mechanism of intervention*: which part of the loop is the model, which part is the context-update rule, and how much external text is required to move a trajectory between empirically supported basins. This section reviews the relevant attractor, degeneration, dimensionality, and dialog literatures, with emphasis on that gap: attractor-like behavior has been observed, but perturbation dose-response and token-scale barrier measurement have not been systematically measured.

2. **Issue — §2.3 reads partly like a contribution/results/reproducibility pitch, not background.**  
   The table includes rows such as "103/103 cell-verified numeric claims," "37/37 experiments," "raw trajectories LFS-tracked," "50–1,350 trajectories," and model-specific details.

   **Why it matters** — These are important, but in §2 they interrupt the scholarly positioning. They also risk sounding adversarial toward the closest prior work rather than analytically comparative.

   **Concrete fix** — Move the full table to the introduction, reproducibility section, or appendix. In §2.3 replace it with compact prose:

   > Relative to recent regime-classification studies of recursive LLM loops, this paper shifts the unit of analysis from trajectory shape alone to *intervention cost*. Prior work asks whether trajectories contract, cycle, or disperse. We ask how those regimes respond to controlled perturbations, whether switching probability scales with injected-token dose, and whether dialog-state updates create basin structure not captured by single-stream operators. The comparison is therefore not primarily one of model scale or dataset size, but of observable: perturbation dose-response rather than unperturbed trajectory geometry alone.

3. **Issue — Methods leakage is heavy in §2.3.**  
   Phrases such as "recurrence rate, sharpness dim, basin predictability acc(k), V\* geodesic-derived geometric barriers, RG dendrogram coarse-graining," "4-condition perturbation protocol," "3 sweep dimensions," and "rank-stable V\* ordering across 6 inter-basin geodesics…" belong to methods/results.

   **Why it matters** — Background should establish intellectual context, not pre-load the reader with implementation details before the formal framework. The current version blurs §2, §3, §4, and §5.

   **Concrete fix** — Replace the methods-heavy advance list with a conceptual version:

   > This paper makes three conceptual moves. First, it separates the recursive loop into the visible state, the generator, and the context-update nudge. Second, it treats perturbations as calibrated interventions rather than informal prompt changes, allowing barrier height to be operationalized as a dose-response quantity. Third, it treats dialog as a distinct update architecture, not merely as another prompt template, and tests whether role-structured state creates basin structure different from single-stream recursion.

4. **Issue — The claim "Tacheny (2025) introduced the dynamical-systems framing" is a priority-risk.**  
   The section says: "Tacheny (2025) introduced the dynamical-systems framing on a single open-source generator…" This is too strong unless the paper can defend priority against earlier dynamical-systems treatments of RNNs, agent loops, semantic trajectories, or LLM recursion.

   **Why it matters** — Priority claims attract reviewer scrutiny. A reader may object even if Tacheny is the closest direct LLM-loop precedent.

   **Concrete fix** — Use a narrower, safer attribution:

   > Tacheny (2025) is the closest recent precedent for treating recursive LLM text transformations as discrete dynamical systems in semantic space. That work demonstrates regime classification on a small set of proof-of-concept loops; the present paper extends the framing to perturbation dose-response, explicit generator/nudge separation, dialog-state updates, and larger paired-control trajectory batteries.

5. **Issue — The comparison with arXiv:2512.10350 is slightly dismissive and over-specified.**  
   The table labels its theoretical framework as "informal" and emphasizes "no public link," "single seed," and "n=2." These points may be true, but the tone is closer to competitive positioning than literature review.

   **Why it matters** — A background section should be fair-minded. Reviewers dislike rhetoric that appears to win by diminishing related work rather than by sharpening the gap.

   **Concrete fix** — Rephrase neutrally:

   > The closest regime-classification study identifies contractive, oscillatory, and exploratory behavior using drift, dispersion, and cluster-persistence measures. Our use of recurrence, dimensionality, density landscapes, and perturbation response is complementary: these diagnostics are introduced not to relabel the same regimes, but to estimate how robust basin membership is under controlled textual intervention.

6. **Issue — The Du and Tanaka-Ishii paragraph over-interprets the relation to this paper's O3 result.**  
   The sentence "the direction of their effect… is compatible with the absorbing-regime interpretation we report in O3…" imports this paper's result into the literature review.

   **Why it matters** — This weakens the review/method/results boundary and makes the background sound like post-hoc validation. The relation is useful, but should be stated as motivation, not evidence.

   **Concrete fix** — Replace with:

   > Du and Tanaka-Ishii use correlation dimension to quantify geometric complexity in generated text and report dimensionality drops during training transitions and degeneration. Their observable differs from ours, but their result motivates treating dimensional collapse as a relevant diagnostic when recursive loops become repetitive or template-bound. We therefore use dimensionality measures as one component of the attractor-like diagnostic battery, without equating correlation dimension with our basin definitions.

7. **Issue — §2.4 is mostly methods, not background.**  
   The sentences on "Dijkstra geodesics between density peaks," "maximum-V along the path," and "volumetric iso-density renderings" describe this paper's implementation.

   **Why it matters** — Effective potential is valid background, but the current subsection previews the exact analysis pipeline. That material belongs in §4 methods or §5 results.

   **Concrete fix** — Trim §2.4 to conceptual background:

   > Empirical density landscapes are often summarized by an effective potential \(V(x)=-\log \rho(x)\), where \(\rho\) is an estimated stationary density in a chosen coordinate system. In physical systems this construction is tied to free-energy analysis; here it is used only as a descriptive transformation of trajectory density in embedding space. The resulting landscape can suggest wells, ridges, and low-density separations between frequently visited regions, but its numerical scale depends on the projection, density estimator, and smoothing choices. We therefore treat potential-derived barriers as descriptive geometric summaries, not as thermodynamic quantities or direct estimates of model-internal energy.

8. **Issue — §2.5 states the paper's findings inside the background.**  
   The sentence "In our experiments, dialog does not simply reproduce the operator regimes. Instead, it generates its own attractor structure…" is a result claim.

   **Why it matters** — The background should motivate why dialog may differ, not announce the empirical conclusion before the framework and experiments.

   **Concrete fix** — Revise §2.5 as a gap statement:

   > Most recursive-LLM dynamics studies focus on single-stream operators such as continuation, paraphrase, or negation. Multi-turn dialog differs because generated text is written into a role-structured conversational state rather than merely appended or replaced as a homogeneous string. This makes dialog a natural test case for whether the context-update rule itself can shape basin structure. Although multi-agent and generative-agent work has studied dialog for capability, memory, and alignment, embedding-space attractor analysis of role-structured recursive dialog remains comparatively undeveloped.

9. **Issue — The regime taxonomy comparison is not fully clean.**  
   §2.3 says prior work has contractive/oscillatory/exploratory, while this paper has "5 (+ D1, + D2)," but elsewhere the paper emphasizes contractive, oscillatory, absorbing, D1, D2. It is unclear whether "absorbing" replaces "exploratory," is a fourth regime, or is specific to a subset of operators.

   **Why it matters** — Taxonomy confusion undercuts the claimed advance. Readers need to know whether the paper extends prior regimes, refines them, or uses a different classification axis.

   **Concrete fix** — Add a clarifying sentence:

   > Our labels are not a one-to-one replacement for the contractive/oscillatory/exploratory taxonomy. We retain contractive and oscillatory as comparable high-level behaviors, treat absorbing collapse as a distinct low-diversity endpoint observed under specific recursive operators, and introduce D1/D2 as dialog-specific regimes whose definition depends on perturbation response and state-update structure rather than dispersion alone.

10. **Issue — §2.6 Terminology is too long for a background subsection.**  
    The glossary contains many repeated "Don't confuse with" entries and defines terms that are not all needed before §3.

    **Why it matters** — The section becomes a manual rather than a literature review. It may be useful for reproducibility, but it slows the reader just when the paper should be transitioning from background to framework.

    **Concrete fix** — Move the full glossary to a boxed glossary, appendix, or end of §3. Keep only a short hierarchy in §2:

    > We use "attractor-like" operationally rather than as a claim about a smooth deterministic system. The analysis proceeds from visible text state \(X_t\), to an observable text view \(\mathcal{O}(X_t)\), to an embedding \(z_t\), to clusters, basin candidates, and finally regime labels. A "nudge" is the context-update rule that writes text into the next state; a "perturbation" is externally injected text used to test stability. A "switch" denotes final-cluster disagreement under the stated perturbation protocol, whereas "persistent escape" requires a durable post-injection basin change.

## Verdict

§2 contains the right ingredients and identifies a real gap, but it currently mixes background, contribution framing, methods, results, and reproducibility claims. The highest-value revision is to make the gap explicit at the start, neutralize the closest-prior-work comparison, and move detailed diagnostics/protocols/results out of §2. A shorter, cleaner §2 would better prepare the reader for the formal state-generator-nudge framework in §3.
