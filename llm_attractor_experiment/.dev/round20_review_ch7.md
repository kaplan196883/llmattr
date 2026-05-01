# Review of §7 Limitations

1. **Issue: The opening frames the section a little defensively rather than as a clean boundary statement.**  
   **Why:** Phrases such as "strongest claims remain tied to…" and "rule out a single-run curiosity" sound like rebuttal language. For a Nature/Science-style limitations section, the stronger posture is: *these are the experimental conditions under which the claims are supported*.  
   **Fix:** Rewrite the lead sentence to state the positive scope first. For example: "The results establish dose-response and regime-separation behavior for bounded, English, text-only recursive loops under the tested generator–nudge families. They do not establish universality across model vendors, memory policies, languages, or deployed tool-using agents." This makes the limitation genuine rather than defensive.

2. **Issue: §7.1 should distinguish model coverage from vendor concentration more crisply.**  
   **Why:** The current wording says the audit spans six generators, including Anthropic and Google, but that the densest evidence is OpenAI-heavy. That is the right limitation, but it should specify exactly what transfers and what does not: qualitative regime shape versus numerical thresholds.  
   **Fix:** Add one sentence making the claim hierarchy explicit: "The cross-model evidence supports preservation of the append/replace/dialog qualitative pattern under the tested generator class; it does not support equality of barrier heights, switching probabilities, basin counts, or token-dose thresholds across vendors." This would prevent readers from over-reading the cross-model audit while preserving the main contribution.

3. **Issue: Numerical caveats from §5 are not yet carried through with enough specificity, especially for D1 basin predictability.**  
   **Why:** §7.2 gives a good general warning that basins and barriers are operational measurements, but it does not remind the reader of the strongest statistical caveats from the results section. If §5 showed that D1 basin predictability depends on group-aware evaluation, split structure, or trajectory grouping, that belongs in the limitations. Otherwise the reader may retain the stronger impression that basin membership is generically predictable.  
   **Fix:** Add a short paragraph to §7.2 or §7.1: "Where basin assignment was modeled predictively, the relevant performance estimates should be read under the group-aware validation design reported in §5; in particular, D1 predictability is evidence for structured separation within the sampled trajectory families, not for arbitrary out-of-family generalization." If there are exact §5 values for ordinary versus group-aware splits, include them.

4. **Issue: §7.2 usefully demotes barriers from physical constants, but the "conditional-surprisal barrier" sentence overreaches beyond the measured data.**  
   **Why:** Saying the model-agnostic object is "closer to a conditional-surprisal barrier measured in nats" is plausible, but because logprobs were not stored, it becomes an unmeasured theoretical assertion inside a limitations section. That slightly weakens the section's empirical discipline.  
   **Fix:** Recast it as future work rather than a claim: "A more model-comparable version of these perturbation barriers would likely use conditional surprisal or log-probability cost; because generation logprobs were not stored, the present token-dose results should be treated as operational proxies." This keeps the insight without implying evidence the paper does not have.

5. **Issue: §7.3 is strong, but it should give the bounded-memory condition more concrete experimental parameters.**  
   **Why:** The limitation is central: append-mode behavior is especially dependent on clipping, context length, and memory policy. But the section currently names these qualitatively. A reader should not have to search earlier methods to know what "bounded" means.  
   **Fix:** Add a parenthetical or one compact sentence with the actual cap/truncation policy and output-length regime: e.g., "In the main experiments, contexts were capped at [N tokens/turns] with tail clipping and outputs constrained to [range]." Also state whether the no-clip pilot was exploratory and not included in the main inferential claims. This makes the memory-policy caveat more concrete and less rhetorical.

6. **Issue: §7.4 appropriately labels D2 exploratory, but the paper should ensure that this status is reflected everywhere else.**  
   **Why:** The limitation is candid: 25 trajectories, 50 steps, 64% switching, ±10 pp bootstrap interval. That is good. But if D2 is treated elsewhere as a co-equal "headline regime," this limitation will look like a late-stage hedge.  
   **Fix:** Add a cross-consistency note: "Accordingly, D2 is treated as hypothesis-generating in the present taxonomy." Then verify that the abstract, figures, conclusion, and regime table do not give D2 equal evidentiary weight with O1–O3 and D1 unless clearly marked as exploratory.

7. **Issue: §7.5's "companion developer-journal essay" reference is likely distracting in a primary research limitations section.**  
   **Why:** Nature/Science readers may see this as a promotional or informal forward-link, especially because the paragraph already says production-agent claims are extrapolations rather than measurements. Unless the companion essay is a formal supplement, registered analysis, or peer-reviewed companion, it weakens the clean boundary being drawn.  
   **Fix:** Remove the reference from the main text, or move it to a footnote/supplementary note only if editorially necessary. The sentence can simply read: "The implications for coding agents are architectural extrapolations from recursive-loop dynamics, not measurements of deployed coding systems." That is sharper and more authoritative.

8. **Issue: The section is even-handed overall, but it could end with a more affirmative statement of what remains valid.**  
   **Why:** The current final paragraph usefully says the framework and perturbation protocol transfer, while numerical barriers do not. That is the right balance. However, after many caveats, the reader needs one concise restatement of the durable contribution.  
   **Fix:** Strengthen the final sentence: "Thus, the transferable contribution is the measurement logic—factorizing generator, nudge, memory, and perturbation dose—not the specific numerical thresholds measured in the present text-only loops." This closes the section with scope discipline rather than apology.

## Verdict

This is a much stronger limitations chapter after the round-19 consolidation. The five thematic subsections read mostly as genuine scope boundaries, not evasive disclaimers. The main improvements needed are to carry over the key §5 numerical/statistical caveats more explicitly, especially group-aware D1 basin predictability; remove or demote the companion-essay forward-link; and sharpen the distinction between transferable qualitative structure and non-transferable numerical thresholds. With those changes, §7 will feel appropriately candid without over-hedging the paper's central claims.
