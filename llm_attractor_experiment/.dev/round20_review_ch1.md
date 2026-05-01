# Review of §1 Introduction

1. **Issue — The lede is buried; the central question does not arrive by paragraph 2.**  
   The opening begins with a general definition of recursive loops, then moves to update rules, then a coding-agent example, and only later asks: "how much text must be injected…?"  
   **Why it matters —** A Nature/Science-style introduction should tell the reader within the first 1–2 paragraphs what problem the paper solves and why the answer changes interpretation. Here the reader has to traverse architecture description and application framing before learning the actual scientific question.  
   **Concrete fix — Replace the first two paragraphs with a sharper problem/result opening:**  
   > Recursive LLM systems increasingly feed model outputs back into future prompts: agents revise plans, assistants summarize tool results, and dialog systems carry state forward. Such loops often appear to settle into attractor-like regimes, but an operational question remains unresolved: how many injected tokens are required to move a settled loop, and does that movement persist?  
   >  
   > We answer this by separating the generator from the context-update rule. In append-mode continuation, adversarial in-distribution perturbations produce a real raw dose response, with $\mathrm{ED50}_{\mathrm{raw}}\approx 40$ tokens, but paired controls already diverge about 35% of the time and persistent escape is not reached for doses up to 400 tokens. In replace-mode, apparent fragility is largely an overwrite effect of the update rule. Thus the stability of recursive loops is not a property of the model alone; it is jointly determined by model, memory policy, perturbation content, and persistence criterion.

2. **Issue — The software-engineering-agent paragraph interrupts the conceptual setup.**  
   The paragraph beginning "A software-engineering agent is one such recursive loop" is plausible but premature, especially because the paper does not evaluate coding agents.  
   **Why it matters —** It creates an expectation of empirical coding-agent results and delays the core claim. It also shifts the reader from the general phenomenon to a specific application before the measurement problem is stated.  
   **Concrete fix — Reduce to one motivating sentence after the main question, or move to Discussion.**  
   Suggested compressed version:  
   > The same distinction appears in coding agents, where the loop state may include tool logs, patches, summaries, pinned requirements, and recent files; the memory policy determines whether new information accumulates, overwrites, or is role-structured.  
   Delete the rest of that paragraph from §1.1.

3. **Issue — The existing-attractor literature is too detailed for §1 and reads like Related Work.**  
   The paragraph listing arXiv:2512.10350, arXiv:2510.21258, and arXiv:2510.24797 gives specific metrics, datasets, and interpretations before the paper's own gap is fully framed.  
   **Why it matters —** The introduction should use prior work to create the gap, not reproduce a mini-literature review. The current version slows the narrative and risks making the paper seem incremental: "another attractor taxonomy," rather than "a perturbation-dose measurement paper."  
   **Concrete fix — Trim this to a two-sentence bridge and move detailed summaries to §2.**  
   Replacement:  
   > Recent work has shown that recursive LLM trajectories can exhibit contractive, oscillatory, exploratory, degenerate, or convergent self-referential regimes. These studies establish that attractor-like structure is empirically visible, but they do not measure the perturbation dose required to move a trajectory between regimes, nor do they separate that dose from ordinary stochastic divergence or from update-rule overwrite mechanics.

4. **Issue — "Attractor boundary," "barrier," and "dislodge" are used before the endpoint distinction is made.**  
   Sentences such as "how much text must be injected… to push a recursive trajectory across an attractor boundary?" and "token-cost required to dislodge them" imply durable basin crossing. But the paper's main quantitative result is explicitly $\mathrm{ED50}_{\mathrm{raw}}$, not persistent escape.  
   **Why it matters —** This is the most important conceptual distinction in the paper. If the introduction uses "barrier" loosely, readers will conflate raw final-cluster switching with true persistent redirection.  
   **Concrete fix — Rephrase the question around three endpoints immediately.**  
   Replace:  
   > how much text must be injected… to push a recursive trajectory across an attractor boundary?  
   with:  
   > how many injected tokens are required to produce final-cluster switching, how much of that switching exceeds the stochastic control floor, and how often does the perturbation produce a visible basin jump that persists to the terminal step?  
   Replace "dislodge" with "move, net of stochastic divergence, and sustain that movement."

5. **Issue — §1.3 contributions are still partly framed as generic "we introduce/define/report/refine" contributions rather than claim-level takeaways.**  
   For example: "we introduce a state-generator-nudge formalism," "we define three dose-response endpoints," and "we report a complementary descriptive view."  
   **Why it matters —** Readers should be able to cite the introduction as a map of the scientific claims. "We introduce" is less informative than "update-rule choice changes apparent stability" or "raw switching and persistent escape dissociate."  
   **Concrete fix — Recast the five contributions as claims.**  
   Suggested structure:  
   > **Claim 1: recursive-loop stability is jointly determined by generator and update rule (§3).** Append, replace, and dialog loops differ because their context-update operators expose different histories to the model.  
   >  
   > **Claim 2: perturbation response decomposes into raw switching, net switching, and persistent escape (§3, §5).** These endpoints separate true redirection from sampling divergence and transient displacement.  
   >  
   > **Claim 3: append-mode continuation has a finite raw dose response but no observed persistent-escape threshold in the tested range (§5.6).**  
   >  
   > **Claim 4: replace-mode apparent fragility is largely update-rule overwrite, not necessarily weak attractor structure (§5.8–§5.10).**  
   >  
   > **Claim 5: perturbation response resolves regimes that bulk geometry alone cannot distinguish (§5.19).**

6. **Issue — The headline numerical claims need endpoint labels every time they appear.**  
   The introduction gives "ED50 ≈ 40 tokens" and later explains this is raw, but some sentences still risk ambiguity, e.g. "measure these barriers" followed by "ED50 ≈ 40 tokens."  
   **Why it matters —** The central result is subtle: raw switching reaches an ED50, net switching does not reach +50 percentage points, and persistent escape is not achieved. Any shorthand "ED50" will be read as the barrier unless labeled.  
   **Concrete fix — Use full endpoint-specific language throughout §1.**  
   Replace:  
   > Append-mode continuation exhibits a finite, graded in-distribution dose-response with ED50 ≈ 40 tokens…  
   with:  
   > Append-mode continuation exhibits a finite raw-switching dose response, with $\mathrm{ED50}_{\mathrm{raw}}$ estimates of 36 tokens by pooled 4PL, 41 tokens by GLMM, and 52 tokens by family-cluster bootstrap median. This is not a persistent-escape threshold: persistent escape remains below 50% for all tested doses, 5–400 tokens.  
   Also add the plateau/floor numbers in the same sentence cluster:  
   > Raw switching plateaus near 67%, while paired controls disagree near 35%, leaving a maximum net effect of roughly +32 percentage points.

7. **Issue — "Nudge" is terminologically confusing because the paper also studies perturbations/injections.**  
   The phrase "state-generator-nudge formalism" defines "nudge" as the context-update operator, but ordinary readers will likely interpret "nudge" as the injected perturbation.  
   **Why it matters —** This creates avoidable ambiguity at the exact point where the paper must separate generator, update rule, and injected text.  
   **Concrete fix — Prefer "state-generator-update" in prose, or define the term defensively.**  
   If the formal term must remain, write:  
   > We use "nudge" in a technical sense for the context-update operator, not for the injected perturbation; operationally, it is the memory policy that maps the current context and model output into the next state.  
   Better still, in §1 use:  
   > state-generator-update formalism  
   and reserve "nudge" for the formal section if needed.

8. **Issue — §1.2 repeats the program rather than sharpening the research questions.**  
   The section says: "First, can append, replace, and dialog loops be understood… Second… Third…" and then restates: "These questions turn an informal observation…"  
   **Why it matters —** This section should be the reader's clean conceptual contract. Currently it mixes framework, taxonomy, and measurement in prose that partly duplicates §1.1 and §1.3.  
   **Concrete fix — Convert §1.2 into three precise questions tied to measurable endpoints.**  
   Replacement:  
   > We ask three operational questions.  
   > 1. **Architecture:** How do append, replace, and dialog update rules alter the accessible loop state?  
   > 2. **Dose response:** For a settled trajectory, how does switching probability vary with injected-token dose and perturbation type?  
   > 3. **Persistence:** Which apparent switches exceed the stochastic control floor and remain through the terminal step?  
   >  
   > These questions convert "the loop gets stuck" into measurable quantities: raw switching, net switching, and persistent escape.

9. **Issue — The empirical contribution paragraph is over-dense and mixes main result, methods, controls, and interpretation.**  
   The third contribution includes 4PL, GLMM, bootstrap, sample size, plateau, stochastic floor, OOD perturbations, replace-mode, dialog regimes, and a note about earlier manuscript framing.  
   **Why it matters —** The reader may miss the hierarchy of results: append raw dose response is the headline; persistence failure is the conceptual punchline; replace-mode overwrite is the architectural lesson.  
   **Concrete fix — Split into two shorter claim paragraphs.**  
   Suggested rewrite:  
   > Empirically, the main append-mode result is a bounded raw dose response. Across $n=200$ runs per cell and eight doses, adversarial in-distribution perturbations yield convergent $\mathrm{ED50}_{\mathrm{raw}}$ estimates of 36–52 tokens, depending on estimator. Raw switching plateaus near 67%, while control-vs-control disagreement is about 35%, so the maximum net effect is roughly +32 percentage points. Persistent escape does not reach 50% for any tested dose up to 400 tokens.  
   >  
   > The architecture comparison changes the interpretation of fragility. Replace-mode paraphrase and summarize-and-negate appear to switch at near-saturated rates, but insert-mode probes show that much of this effect comes from overwriting the previous state rather than crossing a durable attractor boundary.

10. **Issue — The reproducibility audit paragraph is too granular for the introduction.**  
    The final paragraph lists "99 unit tests," "103/103 cells," "37/37 at 100%," `COVERAGE_nano.csv`, `RESULTS_nano.md`, `THESES_nano.md`, and "6/6-thesis PASS audit."  
    **Why it matters —** This is valuable, but in §1 it reads like an internal QA report rather than scientific framing. It also competes with the main claims at the end of the introduction.  
    **Concrete fix — Compress to one sentence and leave audit details to the reproducibility section or appendix.**  
    Replacement:  
    > All trajectories, configurations, analysis scripts, and replication artifacts are publicly released, with automated checks linking the reported numerical claims to the underlying result tables.  
    If desired, add one precise replication statement:  
    > We also provide within-vendor replication on `gpt-4.1-nano`.

## Verdict

The introduction contains the right ingredients but is not yet doing Nature/Science-level work: it buries the central question, over-invests in literature and audit detail, and risks conflating raw switching with durable escape. The fix is mostly structural, not substantive: lead with the perturbation-dose problem and headline endpoint split, trim the prior-work and application digressions, and rewrite the contributions as claim-level takeaways with endpoint-specific numbers.
