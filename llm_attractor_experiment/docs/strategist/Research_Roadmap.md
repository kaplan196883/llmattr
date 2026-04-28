# Research Roadmap — strengthening the paper beyond 33/35

After the academic-paper-strategist Phase 3 audit brought the paper to
33/35 (94%) reviewer score, this document captures concrete moves to
strengthen it further. Sorted by impact-per-hour.

**Companion to**: `Submission_Readiness_Report.md` (which captures the
already-applied optimizations).

---

## Tier 1 — High-impact / low-effort (1–4 hours each)

### #1 Explicit comparison table vs the closest prior work

§2.2 currently cites arXiv:2512.10350 in prose. Reviewers usually want
*side-by-side*. Add a single table early in §2.2:

| dimension | arXiv:2512.10350 | this paper |
|---|---|---|
| regime taxonomy | 3 (contractive, oscillatory, exploratory) | 5 (+ D1 stylistic-multi-basin, D2 drill-down) |
| diagnostic metrics | local/global drift, dispersion, cluster persistence | + recurrence, sharpness dim, basin pred., V\* geometry |
| barrier heights | not measured | tokens of injected text for 50% switching |
| triangulation | n/a | geometric V\* ↔ behavioral dose-response |
| reproducibility | code link | 103/103 cell-verified, 37/37 artifacts, LFS-tracked raw |

Lifts *Originality expression* and *Argument completeness* by half a
point each.

### #2 Deeper literature review — 20–30 more references

12 references currently; cs.CL norm 40–80. Spaces to search:

- Iterative refinement / self-refine / self-consistency (Madaan 2023, Yang 2023, Pan 2023)
- LLM diversity collapse via RLHF (Kirk 2024 *Understanding the effects of RLHF on LLM generalisation and diversity*)
- LLM hidden-state geometry (representation analysis papers; Gardner, Tenney)
- Stochastic-process theory of language models (Jiao 2024, Wang 2024)
- Test-time compute / inference dynamics (Snell 2024, OpenAI o1 paper)
- Persona / mode steering literature
- Information-bottleneck / IB analyses of LLM intermediate states

Spawn an agent — yields ~25 references in ~10 minutes.

### #3 Sharpen the practical-recipe section in §6.5

Current §6.5 is generic. Sharpen to a concrete decision tree:

```
Want a stable trajectory  → append-mode + content-preserving (O1).
                            Resists ~150 tokens of in-distribution perturbation.
Want fast lock-in         → replace-mode (O2/O3).
                            Locks by step 5 but capitulates to ANY noise.
Want stylistic stability  → dialog framework (D1).
                            Stylistic basin survives temperature changes.
Want to test robustness   → measure barrier height in tokens via 4-cond protocol.
```

Plus a paragraph on alignment relevance: perturbation barrier height
as a *robustness probe* for jailbreak / red-teaming.

---

## Tier 2 — High-impact / medium-effort (4–12 hours each)

### #4 Information-theoretic interpretation of barrier height

Reviewer challenge: "tokens of *what* tokenizer? Different models would
give different barriers." Counter with:

- barrier height in tokens × ⟨log P(token | basin)⟩ ≈ barrier in nats
- mutual-information-based barriers are model-agnostic
- our token-cost is proportional (under reasonable assumptions) to a
  KL distance between basin distributions

Half a page turns "an empirical measurement" into "an empirical
measurement of an interpretable theoretical quantity".

### #5 A formal proposition with proof sketch

The state-generator-nudge framework is currently *defined*, not
*theorematic*. Add a proposition the data verifies:

> **Proposition 1** (replace-mode barrier collapse). For any nudge
> 𝒩_f where the next-step context depends only on the current
> generation Y_t (i.e., "replace mode"), the trajectory has at most
> one degree of freedom per step in the basin coordinate, so the
> barrier height between any two basins is bounded by the natural
> width of P_θ(Y | X) for a single context.

Turns the paper from "we measured" to "we measured *and predicted from
theory*".

### #6 Re-analysis of existing data for novel correlations

The dynamics / recurrence / basin-predictability CSVs have more signal
than the paper currently reports. Three predicted correlations:

| correlation | data source | predicted |
|---|---|---|
| ensemble λ_1 vs barrier height | dynamics.csv + switching rates | smaller-λ_1 regimes (contractive) → higher barriers |
| sharpness-dim vs lock-in step | dynamics.csv + basin_pred.csv | low-dim regimes lock in faster |
| recurrence rate vs adversarial robustness | recurrence.csv + dose_response.csv | high-recurrence (O2) most fragile to *any* perturbation |

Each is a 50-line script → table → 2-paragraph addition. If
correlations hold, that's published *additional empirical evidence*
that the regimes are mechanistically distinct.

---

## Tier 3 — High-impact / high-effort (1+ days each)

### #7 Cross-vendor validation with Claude Haiku 4.5

Already costed: ~$356 full-37 on Anthropic Console PAYG. The paper is
"single-vendor" right now; one swap → "cross-vendor confirmed".
Strongest single move for *Originality* / *Generalizability*.

Cheaper alternative: Path B (~$80) headline-only on Haiku 4.5 (4
pub-scale + 4 perturbation pilots). Sufficient to claim "cross-vendor
regime taxonomy survival".

### #8 Ablation: embedding-space invariance

Currently regime taxonomy defined on `text-embedding-3-small`.
Reviewer: "would regimes change with sentence-transformers / BERT?"
Re-embed one regime's trajectories with 1–2 alternative embedding
models and recompute the metric battery. If regimes invariant, strong
robustness claim.

~$10–30 alternative-embedding API costs + ~1 day engineering.

### #9 Alignment / safety framing section

The perturbation barrier protocol *is* a robustness probe. Same
machinery measures jailbreak resistance, in-context-attack resistance,
persona-stability. Reframe a §6 subsection to make this explicit.
Connects paper to alignment literature without changing data.

---

## Suggested execution paths

| budget | what to do | net lift |
|---|---|---|
| 1 afternoon | #1 + #2 | 33/35 → ~34.5/35 |
| 1 week | + #5 + #6 | empirical-only → theory-+empirical |
| 2 weeks | + #7 | single biggest move for generalization claim |
| commit-everything | all 9 above | "good arXiv preprint" → "candidate ACL/EMNLP main-track" |

---

## What we're doing now (option a)

1. Spawn literature-search agent for #2 (in background)
2. Work through #1 (comparison table) interactively
3. Work through #3 (practical-recipe sharpening)
4. Work through #5 (formal proposition)
5. Work through #6 (re-analysis correlations)
6. Update the Submission_Readiness_Report.md with new score

---

*Generated 2026-04-29 alongside the strategist's
`Submission_Readiness_Report.md`. Update as items are completed.*
