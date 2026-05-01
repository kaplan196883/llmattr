# Round-20 review summary — GPT-5.5 advice across §1-§9

This is a consolidated, priority-ranked digest of GPT-5.5's chapter-by-chapter
review of the paper. Full per-chapter reviews live in
`round20_review_ch1.md` through `round20_review_ch9.md`. The summary focuses on
**actionable** items, ranked by paper-wide impact rather than per-chapter
prominence.

---

## Tier 1 — Headline structural fixes (highest leverage)

These are the changes most likely to raise the paper from "audit-grade
preprint" to "Nature/Science-style submission."

1. **Re-sequence §5 Results around the headline endpoint, not the discovery
   chronology.** [§5 review #1, #4, #12]  
   The most important contribution is the corrected dose-response endpoint:
   raw ED50 ≈ 40 tokens, stochastic floor ≈ 35%, **persistent escape never
   reaches 50%**, and **replace-mode "fragility" is largely overwrite**.
   Currently this is delivered across §5.6.1, §5.15, and §5.17 — separated
   by 9 subsections of pilots, temperature sweep, and aggregation machinery.
   **Fix:** reorder to lead with one combined "primary endpoint" subsection
   merging dense ED50 + persistence failure + overwrite-vs-insert mechanics.
   Then present regime establishment. Discovery-order pilots → §11
   Extended Data.

2. **Resolve the formal-barrier vs persistent-escape definitional mismatch in
   §3.** [§3 review #2]  
   The current barrier definition `Pr[X_T∈B_2|...]≥1/2` is *terminal access
   only* and does not require an injection-step jump. Yet the text labels it
   ED50_persist. **This is the most serious definitional inconsistency in
   §3** and a reviewer will flag it. **Fix:** either rename to
   "terminal-redirection barrier" or re-define with the injection-jump
   indicator J_τ as part of the formal predicate.

3. **Front-load §4 Methods with a "primary-endpoints contract."** [§4 review #1, #2, #10]  
   §4.13 (Decision-grade endpoints) currently sits at the END of methods,
   after 11 metric subsections. **Fix:** promote a compressed §4.13 to the
   START as §4.0 Primary endpoints. Reorganize §4.5 from a flat metric
   catalog into inferential-role groups (regime-structure / ensemble-spread /
   predictability endpoint / perturbation-response endpoints / classifier).
   Add a metric→baseline→pass-rule mapping table so each metric's null
   comparison is co-located with its definition.

4. **Lead §1 Introduction with the perturbation-dose problem and three-endpoint
   split.** [§1 review #1, #4, #6]  
   The current opening defines recursive loops, then update rules, then a
   coding-agent example, before stating the question. **Fix:** replace the
   first 2 paragraphs with a sharp problem/result opening that names raw,
   net, and persistent endpoints up front, and uses
   `ED50_raw`-specific language every time the headline number is cited
   (never bare "ED50" — always endpoint-labelled).

5. **Move the regime-audit table out of §3 and into §5.** [§3 review #5, §5 review #3]  
   §3 currently audits O1/O2/O3/D1/D2 against C1-C4. **Empirical audit
   results inside the formal framework chapter make hypotheses look post hoc.**
   **Fix:** move the audit table to §5; in §3, replace with one sentence
   ("the criteria are applied to each regime in Results"). Also: in §5.3,
   pair stratified accuracies with group-aware accuracies side-by-side at
   first exposure (currently group-aware caveat appears 8 subsections later
   in §5.11, which reads as belated correction).

---

## Tier 2 — Conceptual sharpening (high leverage, smaller surface)

6. **Recast §1.3 contributions as scientific claims, not "we introduce/define"
   verbs.** [§1 review #5]  
   E.g., "Claim 3: Append-mode continuation has a finite raw dose response
   but no observed persistent-escape threshold (§5.6)" instead of "we
   define three dose-response endpoints."

7. **Make C1-C4 a citable reusable definition, not implementation-tied prose.**
   [§3 review #4]  
   Box the operational-attractor definition so other papers can adopt it.
   Currently mixed with thresholds, exception clauses, and regime-specific
   commentary.

8. **Compress §3.1.4 Lemma 1 + corollaries to one main-text Proposition; full
   proof to §11.** [§3 review #6]  
   Theorems in main text only when they directly power downstream analysis.
   Replace-mode access bound's downstream use is qualitative; the math
   belongs in Supplement.

9. **Strengthen the "effective-context-share" conjecture from a vacuous
   upper-bound to a testable response curve.** [§3 review #8]  
   Current `Pr ≤ Ψ(α_τ)` with monotone Ψ is satisfied by Ψ ≡ 1. Replace with
   a 4PL-style threshold formulation that predicts ordering between
   in-distribution and out-of-distribution counter-context.

10. **Disambiguate "nudge" terminology.** [§1 review #7]  
    Readers conflate "nudge" (formal term for context-update operator) with
    "perturbation" (injected text). **Fix:** use "state-generator-update" in
    prose §1; reserve "nudge" for the formal section if at all.

11. **Make §5.5 not contradict its own §5.17.** [§5 review #2]  
    §5.5 currently labels O2/O3 as "perturbation-transparent at 94-100%
    switching" before §5.17 reveals 12-32% under insert-mode. **Fix:** either
    move §5.17 directly after §5.5, or merge into one subsection
    "Replace-mode fragility is primarily a memory-policy effect."

12. **Make §6 Discussion punch above its short length.** [§6 review #1, #3, #4, #8]  
    Currently §6 repeats the O1 dose-response numbers across the lead, §6.1,
    and §6.3 (compression-by-results). **Fix:** open with a single
    interpretive sentence ("robustness in recursive LLM systems is not a
    scalar model property but emergent from how generated text is
    re-entered, retained, or overwritten"). Add a memory-policy signature
    paragraph in §6.2 ("append → graded dose response; replace → large
    overwrite-insert gap; dialog → recency + role sensitivity"). Reframe §6.6
    from defensive disclaimer to research agenda.

---

## Tier 3 — Tightening and trimming

13. **Move §2.4 (effective potential) and §2.5 (dialog) implementation
    detail to §4 Methods.** [§2 review #7, #8]  
    They currently leak forward into background. Background should motivate
    the gap, not preview the analysis pipeline.

14. **Move §2.6 Terminology glossary to a §11 boxed glossary.** [§2 review #10]  
    Glossary at the end of §2 slows the transition into §3 framework.
    Keep only a 4-sentence hierarchy in §2.

15. **Soften the comparison with arXiv:2512.10350 (closest prior work).**
    [§2 review #5]  
    Current table calls their framework "informal" and emphasizes "no public
    link." Reads as competitive positioning. **Fix:** replace with neutral
    "this work is complementary; we measure perturbation cost rather than
    trajectory shape."

16. **Move 5+ §5 subsections to §11 Extended Data.** [§5 review #6, #7, #9]  
    Candidates: §5.1, §5.2 (pilot history); §5.9 (aggregation scripts);
    §5.10+§5.16 (geometric V*, merge into one paragraph: "ordinal-only,
    descriptive"); §5.18 (n=4 correlations); §5.19 (unsupervised
    clustering — keep only the conclusion); §5.14 cluster-by-cluster
    inventories.

17. **Move §4.11 TikZ pipeline diagram to §11.** [§4 review #8]  
    Replace with a one-page schematic.

18. **Tighten code-snippet density in §4 main body.** [§4 review #5, #6, #9]  
    Inline Python (`TSNE(...)`) and visualization params (DPI, alpha schedules,
    marching cubes, worker counts) belong in §11. Methods main body should
    have equations, parameter values, and file paths — not implementation
    code.

19. **Move §4.12 Hardware/software detail to §11 reproducibility appendix.**
    [§4 review #12]  
    Just expanded in round-19 with concrete HP ProLiant specs / 40 logical
    threads / Python 3.14 / dep versions. GPT recommends a 1-paragraph main
    summary + supplementary detail. *(Reviewer's note: I'd push back here —
    we just expanded §4.12 specifically to fix the broken page-29 layout.
    Keep most of it.)*

20. **Compress §9 Data/code/repro from 8 audit-style numbers to 2 headline
    numbers.** [§9 review #1, #2]  
    Keep "37 experiments, 3.3 GB raw trajectories, 103/103 audit cells."
    Demote "37×60 matrix", "99 pytest in 13 seconds", "60 artefacts" to
    repository README/supplement.

21. **Replace inline GitHub URL with archival DOI (Zenodo / Software Heritage).**
    [§9 review #5]  
    Nature/Science prefers immutable code citations.

---

## Tier 4 — Even-handedness and tone

22. **§7.5 — Remove "see companion developer-journal essay" forward-link.**
    [§7 review #7]  
    Reads as promotional in a primary-research limitations section.

23. **§7 — Reframe opening from defensive ("strongest claims remain tied
    to") to scope-positive ("the results establish X under Y conditions; they
    do not establish Z").** [§7 review #1]

24. **§7.2 — Recast the "conditional-surprisal barrier in nats" claim as
    future work, not a limitations-section assertion.** [§7 review #4]  
    Logprobs were not stored, so the nat-barrier statement is
    speculative-in-a-limitations-section.

25. **§8 — Add explicit hypothesis box to each §8.X subsection.** [§8 review #1]  
    Each future-direction should state "this experiment tests whether…" with
    falsifiable outcome. Currently several read as wishlist.

26. **§8.5 — Add bounded-claim sentence: "These experiments would not
    constitute comprehensive safety evaluation; they would measure
    susceptibility to durable redirection."** [§8 review #7]  
    Prevents safety-certification overclaim.

27. **§8 — Add closing "Program deliverables" paragraph (cross-vendor benchmark
    suite / memory-policy ablation harness / logprob-enabled barrier analysis /
    dialog-and-coding-agent perturbation datasets).** [§8 review #8]  
    Turns §8 from intellectual roadmap into executable research program.

---

## Tier 5 — Discretionary

28. Soften the priority-claim "Tacheny (2025) introduced the dynamical-systems
    framing" to "closest recent precedent." [§2 review #4]
29. Decouple the Du and Tanaka-Ishii paragraph from the §2 invocation of this
    paper's O3 result. [§2 review #6]
30. Define terms like "content gravity" and "basin" operationally on first
    use in §6 (now that interpretive §6.7 was deleted in round-18).
    [§6 review #10]

---

## Aggregate verdict from GPT-5.5

Across 9 chapters, the paper is **substantially stronger after rounds 17-19**
(which restructured §5, §6, and §7-§12). The remaining gap to a Nature/Science
submission is mostly **structural**, not substantive:

- §1 buries the question; §3 mixes definitions/results/theorems; §4 is an
  implementation manual rather than an experimental design; §5 sequences by
  discovery rather than evidence. Each chapter's headline claim is correct
  but not yet front-loaded.
- The endpoint taxonomy (raw / net / persistent) is the paper's most
  reusable contribution and should be more aggressively promoted as such —
  in §1 (claim-level contributions), §3 (clean definitions), §6 (decision
  framework), and §8 (primary-endpoint specification).
- Audit-grade detail (37×60 coverage, 99 pytests, exhaustive metric
  catalog, n=4 correlation tables, sparse pilot history) is a strength but
  currently competes for attention with the headline. Move much of it to
  §11 Extended Data.
- The paper's most serious technical issue is the §3 barrier-definition
  mismatch (Tier 1, item #2). Everything else is editorial.

A round-21 implementing Tier 1+2 fixes (≈ 12 changes) would likely
transform the paper from "comprehensive preprint" to "Nature/Science
submission candidate." Tier 3-5 are valuable but lower marginal return.
