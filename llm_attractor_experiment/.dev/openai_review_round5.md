# OpenAI fifth-pass peer review of ARTICLE.md (post-round-11)

**Reviewer model:** `gpt-5.5` with `reasoning_effort: "high"`
**Date:** 2026-04-30 (after round 11 — C1-C4 audit table, D1 consistency, V⋆ compression)
**Source reviewed:** `ARTICLE.md` post-round-11 (uploaded as file-7c4hFwKW7S8FWuMYKwBeLq)

---

## Bottom Line

**Yes — ready for TMLR submission.** Round 11 adequately addresses the three round-4 final-polish items; no further empirical revision is needed.

---

## Did round 11 fully address the round-4 priorities?

| Round-4 priority | Status | Comment |
|---|---|---|
| **1. Add C1–C4 audit appendix table** | **Fully addressed** | §13.12 is exactly the right fix. It does not overclaim: states that under strict group-aware C1 + z-tested recurrence C2, no regime cleanly gets 4/4 "strong attractor," and that O1/O2/O3 are best read as attractor-like while D1 is borderline / caveated. Turns a potential reviewer objection into an explicit limitation. |
| **2. Make D1 terminology consistent** | **Fully addressed** | The D1 label is now appropriately framed as **dialogue-state-driven multi-basin / attractor-like dialog regime**, not an unqualified stylistic or strong attractor. Group-aware C1 failure is explicit. |
| **3. Compress / demote V⋆** | **Fully addressed** | §5.10 is now proportionate: V⋆ is described as a descriptive PCA-2 density-landscape analysis with ordinal stability, not a quantitative validation of behavioral barriers. |

---

## Are there NEW issues introduced by round 11?

No new scientific issues. The C1–C4 audit table makes the paper's attractor terminology more constrained — which is good. The V⋆ compression improves the evidential hierarchy: behavioral dose response and persistence are clearly primary; geometry is secondary/descriptive.

---

## Remaining issues

**None — submit as-is.**

If the author has time for one final mechanical copyediting pass, search for residual phrases like "strong attractor", "barrier height", "stylistic multi-basin", "operator-independent" — ensure each is scoped exactly as now intended:

- "strong" only under explicitly stated non-stress-tested criteria, otherwise "attractor-like";
- "barrier" reserved for persistent escape unless qualified as raw-switching ED50;
- D1 as dialogue-state-driven / recent-context capture;
- "operator-independent" only "within the two tested replace-mode operators."

But I would not delay submission for another analysis round.

---

## Final verdict

**Yes: TMLR-ready.**

The best submission framing:

> This paper introduces perturbation dose-response analysis for recursive LLM loops. Its main empirical finding is not that LLM attractor barriers are simply measurable in tokens, but that apparent switching decomposes into distinct endpoints: raw final-cluster disagreement, stochastic divergence above a natural floor, and rare persistent basin escape. Append-mode continuation shows a reproducible raw-switching ED50 around 40 tokens but no measured persistent-escape barrier in the tested range; replace-mode near-100% switching is mostly an operator-overwrite artifact, confirmed by overwrite-vs-insert probes in both tested replace operators.

That framing is honest, technically novel, and well matched to TMLR.
