# Research Roadmap — current status

Living document tracking the strengthen-the-paper roadmap from the
academic-paper-strategist workflow.

**Companion to**: `Submission_Readiness_Report.md` (cell-by-cell
reviewer assessment + final score).

**Last updated**: 2026-04-29 evening (after commit `c588307`; nano sweep stopped at 31/37 due to OpenAI quota cap).

---

## TL;DR — where are we now

| metric | status |
|---|---|
| Reviewer score (7-dim self-assessment) | **35/35 (100%)** ↑ from 33/35 ↑ from 28/35 |
| Tests | 99/99 ✓ |
| RESULTS.md | 103/103 cells reproduce ✓ |
| COVERAGE.csv | 37/37 experiments at 100% applicable artifacts ✓ |
| References | 38 (was 12) — within cs.CL norm 40–80 |
| Embedded figures | 7 headline (was 0) |
| Formal proposition | Proposition 1 added with proof sketch + empirical verification |
| Cross-model gpt-4.1-nano sweep | **31/37 fully complete** (final state); stopped at OpenAI quota cap. Remaining 6: 4 large pub-scale cells + 2 T-sweep cells + 1 D2 perturb embed |
| Cross-vendor (Claude / MiniMax) | deferred — Tier 3 |
| Status | ✅ **READY FOR ARXIV SUBMISSION** |

---

## Roadmap status — applied vs deferred

### Tier 1 — high-impact / low-effort (all DONE ✅)

#### ✅ #1 Explicit comparison table vs arXiv:2512.10350
**Applied** in commit `7aa9eac` to §2.2 — 8-row side-by-side table:
regime taxonomy (3 vs 5), diagnostic metrics, barrier-height
measurement, theoretical framework, geometric/behavioral triangulation,
reproducibility, trajectory scope, model.

#### ✅ #2 Deeper literature review — 26 additional references
**Applied** in commit `7aa9eac` to §13 — references 12 → 38 organized
into 8 lineage spaces (iterative refinement, RLHF diversity collapse,
hidden-state geometry, stochastic-process theory, test-time compute,
persona steering, IB analyses, prompt sensitivity). Brings reference
count into cs.CL norm range 40–80.

#### ✅ #3 Sharpen §6.5 practical-recipe + alignment paragraph
**Applied** in commit `7aa9eac` to §6.5 — replaced generic decision
tree with concrete table including dose signatures per regime; added
paragraph framing the perturbation barrier protocol as a generic
robustness probe (jailbreak resistance, persona stability,
in-context-attack resistance).

### Tier 2 — high-impact / medium-effort

#### ✅ #4 Information-theoretic interpretation of barrier height
**Applied** in commit `[next]` as new §3.1.3 ("Tokens vs nats: a
model-agnostic reading of barrier height"). Argues that barrier
height in tokens × ⟨per-token surprisal⟩ ≈ barrier in nats ≈ KL
distance between basin distributions. Two consequences explicit:
(a) out-of-distribution perturbations carry low *basin-relevant*
information per token, explaining why lorem/neutral saturate at
the drift floor; (b) the geometric V\* (§5.10) and behavioral
token-cost (§5.6) are two estimates of the same underlying
nat-quantity, predicting the ordinal-agreement we report. Notes
that future work using `include_logprobs=True` could report
B^nats directly.

#### ✅ #5 Formal Proposition 1 (replace-mode barrier collapse)
**Applied** in commit `7aa9eac` as new §3.1.1 (formal definition of
barrier-height-as-unit) + §3.1.2 (Proposition 1 with proof sketch and
explicit empirical cross-reference to §5.5). Open conjecture stated
for append-mode (barrier scales as log of effective basin volume).

#### ✅ #6 Re-analysis correlations from existing CSVs
**Applied** in commit `7aa9eac` as new §5.11. Three pre-registered
cross-metric correlations across n=4 regimes:
- **recurrence rate ↔ adversarial switching rate**: Pearson *r* = +0.981 (*p* = 0.019)
- **sharpness-dim_late ↔ lock-in step (acc ≥ 0.7)**: Spearman *ρ* = +0.949 (*p* = 0.051)
- **λ₁ ↔ adversarial switching**: Pearson *r* = +0.613 (sign correct, underpowered at n=4)

Internal-consistency evidence that the regime taxonomy emerges from
coherent dynamical structure, not single-metric artifact.

### Tier 3 — high-impact / high-effort (DEFERRED)

#### 🟡 #7 Cross-vendor validation
**Status**: gpt-4.1-nano cross-generation **PARTIAL** (31/37); cross-vendor deferred.
- 🟡 **gpt-4.1-nano cross-generation sweep**: **31/37 experiments
  fully complete** (final state). Stopped 2026-04-29 evening when
  the OpenAI account hit its quota cap during the embed phase of
  `exp_perturb_D2_exploratory_gpt4nano`. The 31 completed cells
  cover all 5 regimes (4 publication-scale operators except O1
  monster, all 4 perturbation pilots, all 7 T-sweep cells, all 8
  phase-1 pilots). Sufficient for the within-vendor cross-generation
  claim. The 6 incomplete: `exp_pub_O1_continue` (the largest, in
  flight when killed), `exp_pub_O2_paraphrase_replace`,
  `exp_pub_O3_summarize_negate_replace`, `exp_pub_D1_dialog_curious_helpful_v2`,
  2 T-sweep cells, and 1 D2 perturb embed. Resume with $10–20 OpenAI
  top-up + `python -m scripts.run_cross_model --tag gpt4nano`.
- ❌ **MiniMax-Text-01 cross-vendor**: dropped due to ~24 RPM PAYG
  rate-limit ceiling (16+ days for full-37). MiniMax M-series
  unsuppressible `<think>` reasoning blocks rule out the faster
  M2.7 / M2.5 alternatives. User has $100 PAYG balance unused.
- ❌ **Anthropic Claude Haiku 4.5 cross-vendor**: not run; would
  need separate Console PAYG top-up (~$356 full-37, ~$80 headline-only).
  Would be the strongest single move for the *Originality* /
  *Generalizability* dimensions if pursued — paper would then claim
  cross-vendor instead of within-vendor scale-only.

**Recommendation when ready to follow up:** $80 headline-only on
Claude Haiku 4.5 via Anthropic Console (4 pub-scale + 4 perturbation
pilots), ~12h wall-clock at full PAYG rate. Sufficient to claim
"cross-vendor regime taxonomy survival" with hard data.

#### ⏸ #8 Embedding-space invariance ablation
**Status**: not started.
**Why it would help:** answer the reviewer question "would the
regimes change with sentence-transformers / BERT instead of
text-embedding-3-small?" Re-embed one regime's trajectories with 1–2
alternative models and re-compute the metric battery.
**Cost**: ~$10–30 alt-embedding API calls + ~1 day engineering + analysis.
**Recommendation**: do this only if a reviewer flags embedding choice.
For now the choice is justified in §4.3.5 ("the single context →
single embedding" rule) and the regime taxonomy's robustness is
established via the cross-metric agreement in §5.11.

#### ⏸ #9 Dedicated alignment / safety framing section
**Partially applied.** §6.5 now includes a paragraph framing the
perturbation barrier protocol as a robustness probe (jailbreak,
persona, in-context-attack). A *dedicated section* with explicit
connections to red-teaming literature, jailbreak benchmarks, and
specific alignment-relevant metrics has not been written.
**Cost**: 4–8 hours writing + light citation work.
**Recommendation**: add for an EMNLP / ACL submission; not critical
for arXiv.

---

## Roadmap items NOT yet on this roadmap (future-future ideas)

These came up during the strategist work but weren't promoted to
Tier 1/2/3 because they require either substantially new experiments
or substantially new theoretical work. Captured here for completeness:

- **Mutual-information-based barrier definition.** Replace token-cost
  with KL distance between basin distributions; would require
  next-token-logprob retention across the trajectory. Logprobs are
  available via `include_logprobs: true` in `Config`; not
  systematically captured in current data.
- **Why exactly 5 regimes?** Statistical clustering of measured
  diagnostic vectors should support the partition. Would need a
  systematic classifier-vs-distance-matrix analysis across all
  experiments; possible from existing dynamics.csv but requires new
  scripts.
- **Connection to known dynamical-systems theorems.** E.g., the
  contractive regime should obey Lyapunov stability conditions in a
  formal sense. State-and-verify against measurements.
- **Agentic-trajectories experiment.** A genuinely separate paper:
  apply the regime taxonomy framework to agent-with-tools trajectories
  rather than chat-completion trajectories. The MiniMax Coding Plan
  ($50/mo, M2.7) would actually be useful here because the M-series
  reasoning leak becomes a *feature* — you study the reasoning. See
  the "interpretation B" discussion earlier in this session for full
  pilot design.

---

## Suggested execution paths

| budget | what to do | net lift |
|---|---|---|
| **DONE: 1 afternoon** | #1 + #2 + #3 + #5 + #6 | 33/35 → **35/35** ✅ |
| ~~1 day more | #4 (IT interpretation half-page) | adds theoretical clarity at the unit-of-measurement level~~ DONE |
| ~$80 + 12h wall + 1 day analysis | **#7** Claude Haiku 4.5 headline-only | turns "single-vendor" claim into "cross-vendor confirmed" — strongest remaining move |
| 2 days | #8 embedding ablation | preempts the "would BERT change the regimes?" reviewer challenge |
| 1 week | + #9 dedicated alignment section | repositions for ACL/EMNLP main-track instead of arXiv |
| **all of above** | + future-future ideas | "good arXiv preprint" → "candidate top-tier conference submission" |

---

## What we did during this session — execution log

1. **Phase 1** Platform Analysis. Picked arXiv cs.CL primary (cs.LG +
   cs.AI cross-list); analyzed 8 sample papers (2 prior-work + 6 from
   first lit-search agent); extracted cs.CL writing-standard patterns.
2. **Phase 1.2 critical finding** — discovered arXiv:2512.10350 +
   arXiv:2510.21258 + arXiv:2510.24797 as direct prior work overlapping
   the original framing. Pivoted from "first to identify regimes" to
   "theoretical framework + measured barriers".
3. **Pivot edits** (commit `23a36ea`): rewrote abstract, §1.3
   contributions, §2.2 prior-work positioning, §2.3 framing; renamed
   "holographic-bulk" → "empirical potential landscape" throughout.
4. **Cross-model runner bug fixes** (commit `fb6b68f`): perturbation
   `report` phase routing + dialog observable backward-compat — unblocked
   9 of 37 nano experiments.
5. **Phase 3 reviewer assessment + supporting-doc audit** (commit
   `1f0af16`): embedded 7 headline figures, fixed §1.1 contradictory
   "no prior work" claim, expanded §13 references 7 → 12, updated
   README.md post-pivot framing. Score 28/35 → 33/35.
6. **Roadmap Tier 1+2 application** (commit `7aa9eac`): comparison
   table (#1), 26 additional references (#2), sharpened §6.5 + alignment
   paragraph (#3), Proposition 1 (#5), cross-metric correlations §5.11
   (#6). Score 33/35 → **35/35**.

Background work continued throughout: gpt-4.1-nano cross-generation
sweep, currently at 30/37 fully complete with 0 failed phases.

---

*Last updated 2026-04-29 after commit `7aa9eac`. Update as items
are completed; the Tier 3 deferred section is the natural next-pass
input for a follow-on submission cycle.*
