# Review of §6 Discussion

1. **Make the opening punch harder as an interpretive claim, not a compressed Results recap.**  
   - **Issue:** The opening paragraph states the main result clearly, but then immediately packs in many numerical findings: raw ED50, plateau, control divergence, net criterion, persistent escape, replace-mode overwrite.  
   - **Why it matters:** A Nature/Science-style Discussion should first tell readers what conceptual boundary has shifted. Here the conceptual advance is strong — robustness is a property of a *closed generator–memory system*, not of a prompt or model alone — but the numbers crowd it.  
   - **Concrete fix:** Add one high-level sentence before the statistics, e.g.: "The implication is that perturbation resistance in recursive LLM systems is not a scalar model property but an emergent property of how generated text is re-entered, retained, or overwritten." Then move most numerical detail to §§6.1–6.3 or reduce the opening to only the headline ED50 and persistence contrast.

2. **Reduce repetition of the O1 dose-response numbers across the lead, §6.1, and §6.3.**  
   - **Issue:** The same quantitative story appears three times: ED50_raw around 40 tokens, raw plateau near 67%, control floor around 35%, net saturation around +32 pp, persistent escape below 50%.  
   - **Why it matters:** In a short Discussion, repetition makes the section feel compressed yet circular. The reader receives the same result repeatedly rather than progressing from result → interpretation → implication.  
   - **Concrete fix:** Keep the full numerical bundle in §6.3, where it is central. In the opening and §6.1, compress to one sentence: "Although O1 showed a finite raw-switching dose response, that endpoint did not translate into net or persistent escape." This frees space for interpretation.

3. **Sharpen the endpoint taxonomy into a practical decision framework.**  
   - **Issue:** Raw, net, and persistent endpoints are correctly distinguished, but the Discussion could do more to tell readers when each endpoint matters.  
   - **Why it matters:** The paper's most reusable contribution is not only the empirical finding but the endpoint decomposition. Readers working on agent safety, prompt injection, or coding agents need to know which endpoint maps to which risk question.  
   - **Concrete fix:** Add a sentence in §6.1 or §6.5: "Raw switching is appropriate for detecting sensitivity; net switching estimates perturbation effect above stochastic drift; persistent escape is the relevant endpoint when the safety concern is durable redirection after recovery turns." This turns the taxonomy into a reporting standard.

4. **Make §6.2 more predictive, not merely descriptive.**  
   - **Issue:** §6.2 nicely explains append, replace, and dialog as memory mechanisms, but much of it restates the observed overwrite-vs-insert gaps.  
   - **Why it matters:** A strong Discussion should generalize from the experiments to expectations for future systems. The current text says what happened; it could say what memory-policy signatures to look for.  
   - **Concrete fix:** Add a compact mechanistic summary: "The expected signatures differ: append should show specificity and graded dose response; replace should show a large overwrite–insert gap; dialog should show recency and role sensitivity; summary or pinned-memory systems should be tested for what information survives compression." This would make §6.2 more broadly useful.

5. **Clarify that persistent escape is operationally strict, not universally the only valid endpoint.**  
   - **Issue:** §6.3 correctly argues that ED50_raw is not a persistent-escape barrier, but the language risks implying persistent escape is always the superior endpoint.  
   - **Why it matters:** In some applications, transient movement is itself safety-relevant — for example, a single unsafe tool call, one leaked secret, or one malicious code edit. The paper should not overcorrect from raw switching to persistence-only evaluation.  
   - **Concrete fix:** Add a caveat: "Persistent escape is the appropriate strict endpoint for durable basin change, but transient raw switching may still matter in applications where a single action is consequential." This would help bridge to real agents without overreach.

6. **Strengthen §6.4 by saying what density landscapes are good for, not only what they cannot do.**  
   - **Issue:** The section is careful in rejecting token-barrier calibration, but the positive role of the landscape is somewhat underdeveloped.  
   - **Why it matters:** Otherwise the reader may wonder why the landscape analysis belongs in the paper if it cannot estimate barriers.  
   - **Concrete fix:** Add one affirmative sentence: "Their value is diagnostic: they show whether trajectories occupy one or several basins, whether perturbations move mass toward alternative density regions, and whether basin structure is stable under analysis choices." Then retain the warning that \(V^\star\) is ordinal/descriptive, not a calibrated energy or token cost.

7. **Make §6.5 a stronger bridge to Box 1 / Supplementary §11.12.**  
   - **Issue:** The current bridge — "A checklist version of this reporting standard is given in Box 1 (§11.12)" — is serviceable but abrupt. It does not tell the reader what Box 1 adds beyond the three bullets.  
   - **Why it matters:** If Box 1 is meant to be the portable reporting standard, the Discussion should explicitly position it as an operational deliverable of the paper.  
   - **Concrete fix:** Revise the final sentence of §6.5 to something like: "Box 1 in Supplementary §11.12 operationalizes these points as a minimum reporting checklist, including memory policy, perturbation insertion mode, stochastic floor, endpoint definition, recovery horizon, and overwrite-vs-insert controls." This makes the bridge concrete and useful.

8. **Turn §6.6 from a defensive limitation into an open research agenda.**  
   - **Issue:** §6.6 is accurate but reads partly like a disclaimer: same-vendor replication only; not coding agents, tool assistants, SWE-Bench, jailbreaks, IPI, or factuality.  
   - **Why it matters:** A Discussion should acknowledge limits while inviting the next experiments. The current version protects against overclaiming but could more strongly state what the field should now test.  
   - **Concrete fix:** Reframe the paragraph around "next tests" rather than "not studied." For example: "The next step is to ask which parts of this decomposition survive in full agent scaffolds: cross-vendor generators, persistent tool state, retrieval memory, code repositories, and policy-constrained actions." Then list the application-specific observables.

9. **Bridge to agent safety and indirect prompt injection more explicitly, but with bounded claims.**  
   - **Issue:** The section says real domains can adopt the endpoint decomposition, but it does not quite spell out the safety implication.  
   - **Why it matters:** Readers interested in IPI, coding agents, and tool use need to see how the paper changes evaluation practice without claiming direct evidence in those domains.  
   - **Concrete fix:** Add a careful bridge sentence in §6.6: "For indirect prompt injection or coding agents, the analogous question is not whether the transcript topic changes, but whether an injected artifact produces action-level divergence above a no-injection floor and whether that divergence persists through subsequent planning or repair steps." This connects the paper to agent safety while preserving scope.

10. **Remove or define residual metaphorical language that may feel orphaned after deletion of §6.7.**  
    - **Issue:** There is no obvious orphaned "spiritual-bliss" content left, which is good. However, phrases such as "content gravity," "basin," and "visible jump" are evocative and may feel underdefined if the deleted interpretive subsection previously carried that explanatory load.  
    - **Why it matters:** In a short Discussion, unexplained metaphors can make the argument seem more speculative than it is.  
    - **Concrete fix:** Either define these terms in operational language when first used — e.g. "topic-anchored content gravity, meaning repeated return to the same semantic cluster despite local perturbation" — or replace them with plainer terms such as "topic anchoring" and "cluster transition."

## Verdict

This Discussion is substantially improved: it is short, organized around real conceptual claims, and avoids the earlier risk of speculative overinterpretation. Its main weakness is now compression-by-results: the strongest ideas are present, but too much space is spent re-citing the same numerical findings rather than converting them into a reusable framework. With modest expansion and sharper bridges to Box 1 and real agent evaluations, §6 can punch at the level expected for a high-impact paper.
