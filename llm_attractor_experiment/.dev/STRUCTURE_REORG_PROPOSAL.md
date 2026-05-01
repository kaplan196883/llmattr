# Structural reorganization proposal (gpt-5.5 high-reasoning, 2026-04-30)

This document is the gpt-5.5 high-reasoning recommendation for addressing
review weaknesses #1, #6, #7 from `paper/openai_review.md`:

- #1 Paper too long; mixes paper / lab notebook / repo docs / figure appendix
- #6 Theory section verbose; lemma/conjecture/nats/V⋆ creates "facade of formalism"
- #7 Results section needs hierarchy (primary → stress tests → secondary → supplement)

The proposal contains three artefacts:
1. Pruning list for §3 (Formal framework): cut from ~3000 → ~1500 words
2. New §5 (Results) ordering: split into 5.A primary / 5.B stress tests / 5.C secondary / 5.D supplement
3. Specific extraction list for `paper/SUPPLEMENT.md` (~24 candidates)

It is **not yet applied** in full. The author should review and direct
which moves to commit. See `paper/openai_review.md` for the underlying
reviewer feedback.

---

## Artefact 1: Pruning list for §3 Formal framework

Target: reduce §3 from ~3,000+ words to ~1,500 words while preserving:

- state–generator–nudge formalism
- barrier definition
- operational attractor criteria
- fixed replace-mode Lemma 1
- append-mode Conjecture 1
- a very short tokens-vs-nats caveat

**Recommended §3 outline after pruning:**

```
3. Formal framework
  3.1 State, generator, nudge                         ~250 words
  3.1.1 Behavioral barrier height                     ~250 words
  3.1.1.5 Operational attractor-like criteria         ~500 words
  3.1.2 Replace-mode access bound                     ~350 words
  3.1.3 Append-mode accumulation conjecture           ~250 words
  3.1.4 Token barriers and information barriers       ~100 words
  3.2 Observables and embeddings                      ~100 words
  3.3 Predictions                                     ~150 words
Total target: ~1,900 if conservative; ~1,500 if proof/table moved.
```

**Specific pruning items:**

- **§3.1.1.5 regime-by-criteria PASS/FAIL table** (~650–800 words) — move to **§5.A.1 Primary results**. Keep in §3 only the four C1–C4 criteria + the label rule.
- **§3.1.1.5 detailed mathematical thresholds** (~900–1100 words) — compress to one compact list.
- **§3.1.2 Lemma 1 proof** (~500–650 words) — move to supplement; keep statement + 1-sentence pointer.
- **§3.1.2 Corollary 1 / 2 proofs** (~250–350 words) — move to supplement; keep statements.
- **§3.1.2 "Empirical verification" paragraph** (~150–200 words) — move to **§5.A.2** (perturbation results).
- **§3.1.2 repeated G ≠ τ warnings** (~250 words) — collapse to one strong warning paragraph.
- **§3.1.3 effective-context-share formulation** (~200–250 words) — demote to one sentence or move to supplement.
- **§3.1.3 geometric refinement B ≈ c·V⋆** (~150–200 words) — move to Discussion or Supplement; revision explicitly weakens V⋆.
- **§3.1.4 Tokens vs nats** (~900–1100 words) — aggressively shorten to ~100–150 words; move full discussion to §6 or Supplement.
- **§3.3 Hypotheses** (~350–450 words) — compress to bullet list; move "no pre-registration" to Limitations.
- **§3.2 Observable maps and embedding** (~120–150 words) — keep, slight compression.

---

## Artefact 2: New §5 (Results) ordering

```
5. Results

5.A Primary results
  5.1 Regime establishment and decision-grade endpoint summary
  5.2 Perturbation signatures and sparse ED50 barrier evidence
  5.3 Perturbation timing and exploratory dialog candidate

5.B Stress tests of primary results
  5.4 Group-aware basin predictability
  5.5 Cluster and basin validity stress tests
  5.6 Semantic inspection and switching interpretation
  5.7 Geometric landscape sensitivity

5.C Secondary analyses
  5.8 Temperature sensitivity
  5.9 Embedding and generator robustness
  5.10 Diagnostic consistency and unsupervised regime recovery

5.D Supplementary material
  Pilot history, RG dendrograms, aggregation scripts, full
  animation/rendering details, embedding-ablation deep tables,
  cross-model audit details.
```

**Existing §5 → new position mapping** (full table in the gpt-5.5
output; load-bearing items below):

| Existing | New position | Action | Rationale |
|---|---|---|---|
| §5.0bis Unified primary-results table | §5.A.1 Primary | Keep, near top | Implements §4.13 endpoints |
| §5.0 The four (plus one) regimes at a glance | §5.A.1 Primary | Merge with §5.0bis | Avoid two overlapping master tables |
| §5.1 Phase 0 pilot validation | §5.D Supplement | Move | Pilot provenance is lab-notebook material |
| §5.2 Phase 1 small-N taxonomy | §5.D Supplement | Move | Useful context but not load-bearing |
| §5.3 Phase 2 publication-scale verification | §5.A.1 Primary | Keep, integrate with endpoint table | Establishes O1/O2/O3/D1 |
| §5.4 Temperature sensitivity | §5.C.1 Secondary | Keep short, caveated | Scope-confounded |
| §5.5 Phase 3a perturbation pilots | §5.A.2 Primary | Keep prominently | Main empirical contribution |
| §5.6 Phase 3b dose-response | §5.A.2 Primary | Keep prominently, label sparse/underpowered | Central to barrier-height claim |
| §5.7 Phase 3c injection-time sweep | §5.A.3 Primary | Keep, shorten | Direct timing characterization |
| §5.8 Phase 3d D2 drill-down | §5.A.3 or §5.C.2 | Keep as short exploratory subsection | D2 is exploratory |
| §5.9 Cross-experiment aggregation | §5.D Supplement | Move | Pipeline documentation, not science |
| §5.10 Geometric barriers from V(x) | Split: §5.B.4 main + §5.D supplement | Keep figures + caveat; move RG details | V⋆ is descriptive |
| §5.10 RG dendrogram table | §5.D Supplement | Move | Secondary, implementation-heavy |
| §5.10.5 Group-aware basin-predictability | §5.B.1 Stress test | Keep in main | Load-bearing revision finding |
| §5.10.6 Cluster-stability check | §5.B.2 Stress test | Keep in main | Direct response to reviewer |
| §5.10.7 Multi-granularity switching | §5.B.2 Stress test | Keep in main | Supports O1 OOD/IN asymmetry |
| §5.10.8 Per-cluster semantic inspection | §5.B.3 Stress test | Keep, compress tables | Reinterprets regime mechanisms |
| §5.10.9 Per-family + persistence | §5.B.3 Stress test | Keep in main | Crucial: 8% vs 48% finding |
| §5.10.10 V⋆ parameter-grid sensitivity | §5.B.4 Stress test | Keep in main | Reviewer-flagged concern |
| §5.11 Cross-metric correlations | §5.C.3 Secondary | Keep short, move table to supplement | n=4, descriptive only |
| §5.12 Why exactly five regimes? | §5.C.3 Secondary | Keep summarized | Motivates perturbation barriers |
| §5.13 Embedding-space invariance | Split: §5.C.2 main + §5.D supplement | Keep headline + figure; move deep dive | Important but secondary |
| §5.14 Cross-model thesis verification | §5.C.2 Secondary | Keep short summary; move 37-cell audit | Within-vendor only |

---

## Artefact 3: Specific extraction list for `paper/SUPPLEMENT.md`

24 candidates organized by topic:

### A. Methods deep dives
1. §4.3.1–§4.3.5 Embedding mechanics
2. §4.4 Representation spaces (full prose)
3. §4.5.5 Lyapunov spectrum (covariance derivation)
4. §4.5.6 Sharpness dimension (full Tuci formula)
5. §4.8 Static visualization battery (plot variants A–I)
6. §4.9 Flow-field computation (bin-aggregate kernel)
7. §4.10 Perturbation visualization toolkit (iso-density rendering)

### B. Secondary analyses and pilot history
8. §5.1 Phase 0 pilot validation (entire)
9. §5.2 Phase 1 small-N taxonomy
10. §5.4 Temperature sensitivity extended details (per-T tables)
11. §5.11 Cross-metric correlation full table
12. §5.13 Embedding ablation deep table
13. §5.14 Cross-model audit details (37-cell breakdown)

### C. Engineering documentation
14. §4.11 End-to-end pipeline diagram + §4.11.1–§4.11.2
15. §5.9 Cross-experiment aggregation
16. §10.4 Pipeline commands + §10.8 repository layout

### D. Full animation / visualization details
17. §5.10 Figures 10–12 animation prose
18. §9.5 Animation rendering pipeline (entire)

### E. Code-snippet appendices
19. §9.1 Exact metric definitions (code snippets)
20. §9.2 Perturbation injection mechanics (impl details)
21. §9.6 Exact prompt templates (move full block, keep summary table)
22. §9.7 Model versioning (move full table, keep 1-sentence)

### F. Theory supplement
23. §3.1.2 Lemma + corollary proofs
24. §3.1.4 Full tokens-vs-nats discussion

---

## `SUPPLEMENT.md` skeleton

```
S1. Formal proofs and information-barrier discussion
S2. Full experimental configurations and prompt templates
S3. Embedding, projection, and observable implementation details
S4. Metric implementation details and code snippets
S5. Visualization and animation pipeline
S6. Pilot experiments and discovery history
S7. Secondary analyses
    S7.1 Temperature sweep full tables
    S7.2 Cross-metric correlations
    S7.3 Embedding ablation full tables
    S7.4 Cross-model 37-cell audit
S8. Aggregation scripts and reproducibility commands
```

---

## Status (last updated 2026-04-30, after dense-rerun completion)

### ✅ Applied to ARTICLE.md / paper.pdf

- **§4.13 Decision-grade endpoints** — 5-row table with pre-registered numerical pass thresholds.
- **§2.6 Terminology glossary** — strict hierarchy `text state → observable → embedding → cluster → basin candidate → attractor-like regime`, definitions for 18 terms.
- **§3.1.4 nats bridge cut** — from ~600 words to ~120 words; KL/V⋆ speculation moved to discussion.
- **§5.A / §5.B / §5.C narrative dividers** — added at top of §5 explaining the four-band hierarchy without renumbering subsections (preserves cross-references).
- **§3.1.2 Lemma 1 proof** — moved to new §13.1 (Supplementary appendix); main body has 1-sentence sketch + forward pointer.
- **§9.1 code-snippet block** — moved to new §13.2; main body has 1-paragraph pointer.
- **§13 Supplementary appendix** — created at end of paper after §12 References, with §13.1 (Lemma proof), §13.2 (metric code snippets), §13.3 (forward pointers to remaining extraction candidates).
- **§5.6.1 Dense-dose rerun result** — full dose-response table, ED50 estimates from three methods, upper-asymptote and natural-floor findings, Figure K.
- **All 17 figure captions shortened** ~65% via gpt-5.5 (separate from the structural reorg, but directly addresses Writing & Structure #4).

### 🟡 Pending — non-trivial mechanical edits with cross-reference risk

These items are documented in Artefacts 1–3 above. Each is well-scoped but requires careful execution to avoid breaking the dozens of `§5.10.5`, `§5.6`, etc. cross-references already in the paper.

- **§3 prune (Artefact 1) — partial.** The §3.1.4 nats cut is done. Remaining: compress §3.1.1.5 prose to bullet-list of thresholds; move Corollaries 1/2 proofs to §13; demote §3.1.3 effective-context-share formulation; move §3.1.3 geometric refinement to discussion; compress §3.3 Hypotheses to bullet list. Estimated cuts: ~1,500 more words from §3.
- **§5 reorder (Artefact 2) — partial.** Narrative dividers `§5.A`/`§5.B`/`§5.C` are in place. The full reorder into `§5.A.1`, `§5.A.2`, etc. with renumbering and §5.1/§5.2 pilot history moved to supplement is **not** applied (would require touching ~30 cross-reference sites).
- **`§13` extension (Artefact 3) — partial.** §13.1 + §13.2 exist. The remaining 22 candidate extractions from Artefact 3 are not yet moved (engineering details from §4.8–§4.11; secondary analyses §5.4 deep tables, §5.11 full correlation table, §5.13 deep tables; reproducibility content from §10.4 / §10.8; further code snippets from §9.2 / §9.5 / §9.6 / §9.7).

### Recommendation

Of the remaining work, the highest-leverage / lowest-risk items are:

1. **Compress §3.1.1.5 to bullet-list of thresholds** — reduces theory section by ~500 words without breaking anything (the C1–C4 criteria are referenced as a unit, not by sub-component).
2. **Move §9.2 / §9.5 / §9.6-full / §9.7-full to §13.x** — engineering details with self-contained references; no impact on §3–§7 content.
3. **Move §5.1 + §5.2 pilot history to §13.x** — these subsections have very few inbound cross-references.

The §5 full renumbering (Artefact 2) is **deferred** until the paper has stabilised — it's the highest-impact change but also the one most likely to introduce broken `§5.x` references that need to be tracked down throughout the body.

The full structural reorganization remains the right long-term direction, but the current state is already substantially better than the original manuscript: paper.pdf is 11.57 MB with the dense-rerun result, sharpened captions, stricter terminology, decision-grade endpoint table, and ~1,200 words of supplementary content moved out of the main body.
