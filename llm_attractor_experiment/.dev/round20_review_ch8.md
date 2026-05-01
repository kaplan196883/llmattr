# Review of §8 Future directions

1. **Add an explicit hypothesis box for each subsection.**  
   The section is much stronger after the round-19 consolidation, but several subsections still read as plausible next steps rather than experiments with falsifiable outcomes. Add 1–2 sentences at the start or end of each subsection in the form: "This experiment tests whether…". For example:  
   - **8.1:** "Hypothesis: append/replace/dialog regime ordering is invariant across model families under matched perturbation dose and memory policy."  
   - **8.2:** "Hypothesis: switching thresholds align more tightly with conditional surprisal than with token count."  
   - **8.3:** "Hypothesis: context-update rules, not only base models, determine persistent escape probability."  
   - **8.4:** "Hypothesis: dialog topology and agent scaffold introduce distinct susceptibility profiles not predicted by single-turn model behavior."  
   - **8.5:** "Hypothesis: persistent escape is separable from immediate compliance and should be measured as a multi-step recovery process."  
   This would make §8 read like a research program rather than a wishlist.

2. **Convert "publication-scale" into a concrete minimum viable study.**  
   §8.1 names vendors and gives an approximate N, but it should specify the design that would count as a successful replication. Add a compact paragraph or table listing: models/vendors, regimes, perturbation doses, number of seeds, controls, primary endpoint, and decision criterion. For example: "Primary success criterion: Spearman agreement in regime ordering across vendors, with append/replace/dialog ordering preserved in at least X of Y model families." This would help readers see what "publication-scale" means operationally and would make the proposal fundable.

3. **Separate primary endpoints from exploratory endpoints.**  
   Across §8, the endpoints accumulate: raw switching, net switching, ED50, recurrence, persistence, basin geometry, information barriers, recovery rate, pass/fail variation, etc. This breadth is scientifically useful but risks looking unfocused. For each subsection, designate one primary endpoint and 2–3 secondary endpoints. For instance, in §8.5 the primary endpoint should probably be **persistent escape after neutral continuation**, with raw escape and recovery rate as secondary. In §8.2, primary could be **surprisal-normalized ED50 versus token-normalized ED50**. This will make the future work more persuasive to grant reviewers and less vulnerable to "many metrics, no decision rule" criticism.

4. **Keep cross-vendor replication first, but add a rationale for the ordering.**  
   The current order is defensible: cross-vendor replication should come first because it tests whether the core regime structure is real rather than model-specific. However, the order should be justified explicitly. Add a short orienting paragraph before §8.1:  
   "The proposed program proceeds from external validity, to mechanistic measurement, to scaffold ablations, to applied agent and safety settings."  
   That framing explains why cross-vendor replication precedes memory-policy ablations and coding-agent benchmarks. Without it, some readers may argue that memory policy is the more actionable intervention and should come first.

5. **Make §8.3 more grant-ready by naming the experimental matrix.**  
   §8.3 is one of the strongest subsections conceptually, but it would benefit from a clearer factorial design. Specify something like:  
   - Memory policy: full append / rolling window / summary replacement / pinned-plus-rolling hybrid.  
   - Perturbation position: early context / latest turn / summary / pinned instruction / tool output.  
   - Perturbation type: irrelevant long text / misleading explanation / malicious package text / false log.  
   - Outcome: immediate switch, persistence, recovery, recurrence.  
   This would immediately read as a scaffold-ablation benchmark rather than a set of interesting possibilities. It would also make clear what kind of hire is needed: systems/agent-infrastructure rather than only model-evaluation labor.

6. **Tighten §8.4 by distinguishing dialog science from coding-agent engineering.**  
   Dialog topologies and SWE-Bench-style coding agents are both important, but they are different programs. The current combined subsection works structurally, but the transition should be sharper. Consider dividing the paragraph internally into "Dialog topology benchmark" and "Agent scaffold benchmark," even if they remain under one heading. Also specify whether coding-agent perturbations are meant to test model reasoning, memory handling, tool-trace contamination, or repository-grounding failures. Otherwise the coding-agent proposal may feel too broad: issue comments, package docs, logs, summaries, and files are all plausible injection sites, but they test different failure modes.

7. **Keep §8.5 scoped: emphasize measurement, not safety certification.**  
   §8.5 mostly avoids overclaim, but it comes close when it suggests that the design can determine whether alignment "creates or reshapes basins." That is a legitimate hypothesis, but the language should stay explicitly comparative and bounded. Add a sentence such as: "These experiments would not constitute a comprehensive safety evaluation; they would measure scaffold- and model-specific susceptibility to durable redirection under controlled perturbations." This prevents the section from implying that persistent-escape barriers alone certify instruction-injection robustness or model safety. The distinction between immediate escape and persistent escape is excellent and should remain central.

8. **Add deliverables and required capabilities at the end of the section.**  
   To make §8 useful for a follow-up grant or hiring plan, close with a short "Program deliverables" paragraph. Example deliverables:  
   - Cross-vendor benchmark suite with matched perturbation scripts.  
   - Memory-policy ablation harness with traceable context-update rules.  
   - Logprob-enabled barrier analysis when provider APIs permit.  
   - Dialog and coding-agent perturbation datasets.  
   - Public analysis code for recurrence, persistence, ED50, and basin geometry.  
   This would turn the future-directions section from an intellectual roadmap into an executable research program.

## Verdict

The restructured §8 is substantially improved: five grouped directions are readable, logically connected, and scientifically plausible. The main remaining weakness is not ambition but operational specificity. Each subsection should state the hypothesis it resolves, identify a primary endpoint, and define the minimum experiment that would count as success or failure. Cross-vendor replication should remain first, provided the section explicitly frames the sequence from external validity to mechanism to applied scaffolds and safety. §8.5 is appropriately important and mostly well scoped, but should add a limiting sentence to avoid implying broad safety certification.
