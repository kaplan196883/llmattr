# Review of §4 Methods

1. **Issue — The chapter lacks a front-loaded "methods contract."**  
   **Why it matters:** Readers must traverse recurrence, sampling, embedding, projections, 11 metrics, baselines, visualization, and hardware before learning which measurements are actually decision-grade. This makes §4 feel like an implementation inventory rather than a designed experiment.  
   **Concrete fix:** Move a compressed version of §4.13 to the start, immediately after the opening skeleton, as "4.0 Primary endpoints and inferential contract." Keep the full endpoint table near the end only if needed. Suggested opening prose:  
   > "Before listing implementation details, we pre-specify five primary endpoints used for claims: operational attractor score, group-aware basin predictability, perturbation switching signature, behavioral ED50, and persistent escape. All other quantities in §4.5 are diagnostic or visualization-support metrics unless explicitly mapped to one of these endpoints."  
   This gives readers the hierarchy before the metric battery.

2. **Issue — Experimental design and metric implementation are mixed throughout §4.5.**  
   **Why it matters:** §4.5 currently contains both design elements, e.g. perturbation conditions and Algorithm 1, and downstream metrics, e.g. recurrence, dwell, Lyapunov spectrum. This obscures what was manipulated versus what was measured.  
   **Concrete fix:** Split "design" from "measurement." Move the paired perturbation protocol, perturbation conditions, injection timing, dose definitions, and Algorithm 1 out of §4.5.11 into a new design subsection before embedding/projection, e.g. **4.3 Perturbation materials and paired-run protocol**. Then §4.5.11 can be shortened to define only the derived quantities: raw switching, floor, net switching, injection jump, persistent escape.

3. **Issue — §4.5 is a flat metric catalog rather than an inferential map.**  
   **Why it matters:** Eleven sub-subsections of equal visual weight imply all metrics are equally claim-bearing. But the paper itself distinguishes primary endpoints, support diagnostics, robustness checks, and visual summaries.  
   **Concrete fix:** Reorganize §4.5 by inferential role. For example:  
   - **4.5.1 Regime-structure diagnostics:** recurrence, dwell, basin score/entry, late recurrence, exit-return, periodicity, dispersion.  
   - **4.5.2 Ensemble-spread diagnostics:** Lyapunov spectrum, sharpness dimension, effective rank.  
   - **4.5.3 Predictability endpoint:** basin predictability, including group-aware variant if central.  
   - **4.5.4 Perturbation-response endpoints:** raw switching, stochastic floor, net switching, persistent escape, ED50.  
   - **4.5.5 Classifier summary:** three-axis hypothesis classifier.  
   This would make the chapter read as a measurement system rather than a list of functions.

4. **Issue — The perturbation corpora taxonomy is misplaced if housed inside Embedding.**  
   **Why it matters:** Neutral/wiki/lorem/adversarial materials are experimental interventions, not embedding observables. Placing them in §4.3 makes the perturbation design look secondary or representational, when it is central to the paper.  
   **Concrete fix:** Create a standalone subsection after Sampling:  
   > **4.3 Perturbation materials, corpora, and injection protocol**  
   Include the corpora taxonomy table, perturbation conditions, dose resizing, adversarial-source rule, injection step, paired-control design, and exclusion rules. Then rename the current embedding section to **4.4 Embedding and observables**. The current §4.5.11 should refer back to this subsection rather than reintroducing the protocol.

5. **Issue — Code-level snippets in main Methods are too granular for the main text.**  
   **Why it matters:** The main-body methods should be reproducible but not read like inline documentation. Blocks such as the adjacent-step similarity verification Python snippet, literal `TSNE(...)` constructor, and long TikZ pipeline source interrupt the scientific narrative. Since full implementations live in the Supplement, these details dilute the main method.  
   **Concrete fix:** Keep equations, parameter values, and file paths where necessary; move executable snippets to §11. Replace code blocks with compact parameter tables. Example replacement for t-SNE:  
   > "t-SNE was fit after PCA-50 pre-reduction using cosine distance, perplexity 30 capped at \((N-1)/4\), PCA initialization, automatic learning rate, and random seed 42."  
   Then add:  
   > "Exact constructor calls and verification snippets are provided in Supplementary §11."

6. **Issue — §4.3 Embedding is doing too many jobs.**  
   **Why it matters:** It currently explains observables, embedding model mechanics, token budgets, append-mode overlap, adjacent-step similarity, caching, cost, Batch API/Evals stubs, and sometimes perturbation corpora. These are not all equally necessary for main Methods.  
   **Concrete fix:** Split into three levels:  
   - Main text: observables table, embedding model, normalization, one-vector-per-observable invariant, token-budget assurance.  
   - Supplement: adjacent-step similarity verification, Batch API/Evals stubs, detailed caching mechanics, cost estimates, degenerate identical-embedding cases.  
   - Perturbation materials: move to separate design subsection as above.  
   A concise main subsection could be titled **Embedding observables and numerical representation**, with the implementation mechanics compressed to 3–4 paragraphs.

7. **Issue — The chapter does not consistently distinguish "what was measured" from "why that choice was made."**  
   **Why it matters:** Methods should first define the measurement operationally, then briefly justify it. In the current draft, rationale often precedes or interrupts definitions, e.g. why cosine is appropriate, why streamlines are used, why observables differ, why SD is borrowed from Tuci et al.  
   **Concrete fix:** Apply a repeated mini-structure to metric subsections:  
   1. **Definition:** exact quantity and input space.  
   2. **Use in claims:** primary endpoint, secondary diagnostic, or visualization only.  
   3. **Rationale/limitation:** one short paragraph.  
   For example, under recurrence:  
   > "Definition. Recurrence is computed in PCA-10 as…"  
   > "Use. This contributes to the operational attractor score but is not a standalone endpoint."  
   > "Rationale. The lag exclusion removes adjacent-step triviality; recurrence is interpreted only relative to baselines."

8. **Issue — §4.11's TikZ pipeline diagram is not load-bearing in its current form.**  
   **Why it matters:** The diagram is far too detailed for a main Methods chapter and duplicates prose already present in §§4.1–4.10. It also includes implementation routing, file names, plot families, and aggregation scripts, which are useful for audit but not necessary for understanding the experimental design.  
   **Concrete fix:** Replace §4.11 in the main text with a one-page schematic figure or compact flow table: Generation → Observables → Embeddings → Joint projections → Metrics/endpoints → Baselines/statistics → Reports. Move the full TikZ source, shape annotations, persistence-boundary table, and rerun semantics to Supplement. Keep only the persistence principle in main text:  
   > "Each phase writes a deterministic intermediate, allowing downstream analyses to be rerun without regenerating trajectories."

9. **Issue — Visualization methods occupy disproportionate main-text space relative to claim-bearing analyses.**  
   **Why it matters:** §§4.8–4.10 are valuable for reproducibility, but many visualization details—plot lettering, DPI, specific filenames, alpha schedules, marching cubes, worker counts—do not affect the inferential validity of the results. They compete for attention with the primary endpoints.  
   **Concrete fix:** Condense visualization in main Methods to:  
   - which projections were visualized,  
   - which plots support qualitative inspection,  
   - which visualizations are explicitly non-quantitative,  
   - where full rendering details live.  
   Move plot inventories, letter codes, implementation functions, and animation details to Supplement. Keep flow-field computation only if divergence/streamline interpretations are used as evidence; otherwise classify it as visualization support.

10. **Issue — Baselines and statistical gates are separated from the metrics they validate.**  
    **Why it matters:** A metric's meaning depends on its null comparison. Recurrence, dwell, basin score, and dispersion are not interpretable without knowing the relevant baseline and significance gate. Currently the reader sees metric definitions first and only later learns the criteria for counting a signal.  
    **Concrete fix:** Add a short "Validation rule" sentence to each metric family or insert a table after §4.5 mapping metrics to baselines:  
    | Metric family | Null/baseline | Claim use | Pass rule |  
    |---|---|---|---|  
    | Recurrence/dwell | time-shuffled, no-feedback, independent regeneration | attractor score | ≥ baseline + 2σ and d ≥ 0.5 |  
    | Switching | paired control-control floor | perturbation signature | raw, net, persistent reported separately |  
    | Predictability | GroupKFold by family | basin predictability | acc_group(k=10) ≥ 0.70 |  
    This would make §4.6–4.7 feel integrated rather than appended.

11. **Issue — The Lyapunov/sharpness subsection risks overclaiming by proximity to formal dynamical-systems language.**  
    **Why it matters:** The current text does state that the spectrum is ensemble-spread-based and not Jacobian-derived, but the terminology "Lyapunov spectrum" and "sharpness dimension" carries strong mathematical expectations. Reviewers may challenge whether these are true Lyapunov exponents.  
    **Concrete fix:** Rename or qualify consistently in headings and tables: **finite-time ensemble-spread spectrum** rather than simply "Lyapunov spectrum." Suggested edit:  
    > "We use the term finite-time Lyapunov-like exponent for an ensemble-spread growth rate, not for a Jacobian-derived exponent of a smooth map."  
    Also mark SD/effective rank as secondary diagnostics, not decision-grade endpoints, unless they directly enter the attractor score.

12. **Issue — Hardware/software details are useful but too specific for the main evidentiary path.**  
    **Why it matters:** Concrete workstation specs and exact package versions improve reproducibility, but they are not conceptually important to the methods unless runtime or determinism depends on them. The expanded §4.12 may feel like repository documentation.  
    **Concrete fix:** Keep a short reproducibility paragraph in main text: CPU-only, OpenAI API models, Python/scikit-learn/numpy stack, deterministic seeds, no GPU required. Move exact CPU model, RAM, OS, package versions, pytest count, and ProcessPoolExecutor worker count to a reproducibility appendix or environment file reference. Main text can say:  
    > "Exact package versions, hardware specifications, and test-suite status are reported in Supplementary §11 and `requirements.txt`."

## Verdict

§4 is impressively auditable, but it currently reads more like a combined methods, implementation manual, and reproducibility appendix than a sharply organized Methods chapter. The most important revision is structural: front-load the primary endpoint contract, separate perturbation design from metric definitions, and demote code-level and visualization implementation detail to the Supplement. This will make the chapter more persuasive without sacrificing reproducibility.
