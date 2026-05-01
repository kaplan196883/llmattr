# OpenAI second-pass peer review of ARTICLE.md (post-revision)

**Reviewer model:** `gpt-5.5` with `reasoning_effort: "high"`
**Date:** 2026-04-30 (after 8 rounds of revisions including dense-dose rerun)
**Source reviewed:** `ARTICLE.md` post-revision (uploaded as file-TGLojhNKgVaquhM92ds8fA)
**Prior review:** `paper/openai_review.md` (file-5aJgD5k67dG4RxiXAYxdLm)

---

## Bottom Line

**Revised verdict: weak reject for NeurIPS/ICML in current form, but much closer to a publishable paper.** The revision clears the original fatal "~150-token barrier" overclaim: §5.6.1 is a real confirmatory rerun, and it honestly reports a different result. The remaining central problem is that the paper still wants "barrier height" to mean attractor/basin escape, while its own best analyses show the measured ED50 is mostly **raw final-cluster disagreement on top of a 35% stochastic divergence floor**, and persistent basin escape is rare.

The strongest version of the paper is now: **recursive LLM loops under different nudges show robustly different perturbation sensitivities, especially O1 append/continue versus replace-mode overwrite regimes, and O1 has a reproducible raw-switching dose response to in-distribution injected text.** That is interesting. But it is not yet a clean token-valued attractor-barrier measurement.

---

## What changed since the first review

- **Old claim:** O1 had an approximately **150-token barrier** based on four sparse n=50 dose points.
  **New claim:** Dense rerun gives **raw-switching ED50 ≈ 36–52 tokens**, with a plateau near **0.67** and a **control-vs-control stochastic floor ≈0.35**. This is a major and honest correction.

- **Old claim:** Switching was treated as basin escape.
  **New evidence:** §5.10.9 shows only **8%** of O1 sparse-dose trajectories at dose 400 are "kicked at injection and persisted," versus **48%** final-cluster switching. This directly validates the original criticism and forces a weaker interpretation.

- **Old theory:** Lemma 1 incorrectly bounded injected-token barrier using generated-token budget.
  **New theory:** §3.1.2 separates injected-token cost τ from post-injection generation budget G_m. This is much cleaner.

- **Old taxonomy:** Five attractor regimes were presented too evenly.
  **New taxonomy:** D2 is demoted to exploratory; O1/O2/O3/D1 are evaluated against operational C1–C4 criteria; §5.10.8 also admits several labels were mechanistically wrong.

- **Old validation:** Basin predictability used ordinary stratified CV and likely leaked prompt-family identity.
  **New validation:** §5.10.5 uses GroupKFold and shows large leakage for O2/O3/D1, small leakage for O1. This materially strengthens O1 and weakens some earlier broad taxonomy claims.

- **Old geometric claim:** V* was framed as validating behavioral barriers.
  **New framing:** §5.10 now treats V* as descriptive, with parameter-grid sensitivity. This is appropriate.

---

## Top Strengths (revised)

1. **The dense-dose rerun is the single strongest new contribution.** The author committed to a larger confirmatory experiment and accepted that it falsified the old "~150 token" headline. §5.6.1 is unusually transparent: point estimates, family-cluster bootstrap uncertainty, plateau below 1, natural divergence floor.

2. **The O1 append/continue result is now genuinely defensible.** O1 survives group-aware CV better than the other regimes, has robust OOD-vs-in-distribution switching asymmetry across clustering granularities, and has a dense monotone raw-switching dose response.

3. **The paper now distinguishes several quantities that were previously conflated.** Text state, observable, embedding, cluster, basin candidate, attractor-like regime, switching, and persistent escape are separated in §2.6.

4. **The stress tests are unusually candid.** Group-aware CV, HDBSCAN/spectral checks, multi-granularity switching, semantic cluster inspection, per-family heterogeneity, persistence tests, and V* sensitivity all expose weaknesses rather than hiding them.

5. **The revised paper has a real "methodological spine."** §4.13 decision-grade endpoints, §5.0bis primary-results table, and §3.1.1.5 operational attractor criteria impose more hierarchy than the earlier lab-notebook version.

---

## Remaining Weaknesses (ranked by severity)

### 1. The central "barrier height" claim is still not the same as measured persistent basin escape
**Type:** Previously raised, only partially addressed.
**What's wrong:** §3.1.1 defines barrier height as injected-token dose for 50% switching from one basin to another. But the best current O1 evidence decomposes as: raw final-cluster switching crosses 50% around 40–50 tokens (§5.6.1); control-vs-control stochastic divergence is already ~35%; net adversarial effect reaches only +32 pp at dose 400; persistent injection-time basin escape is only 8% at dose 400 in the sparse analysis (§5.10.9). The dense ED50 is a **raw final-cluster-disagreement ED50**, not an attractor-boundary barrier.
**Concrete fix:** Define and consistently report three separate endpoints: (1) Raw-switching ED50, (2) Net-switching effect (raw minus floor), (3) Persistent-escape ED50. State plainly which are established.

### 2. Several primary-results tables are stale or internally inconsistent after the dense rerun
**Type:** New issue introduced by revision layering.
**What's wrong:** §5.6.1 reports the dense rerun: ED50 36/41/52, switching @200=0.620, @400=0.670. But §5.0bis still reports sparse O1 values: switching @200=0.54, @400=0.48, ED50=83 tokens, status "dense-rerun in flight." §4.13 decision-grade endpoints similarly stale. There's also an old test-count inconsistency: §10.7 says 99 pytest tests, but a code block elsewhere may still reference 94.
**Concrete fix:** Global "dense-rerun reconciliation pass." Every table/abstract/result summary should use one of three labels: sparse pilot, dense confirmatory, or stress-test reanalysis.

### 3. The dense-dose modeling needs a clearer statistical interpretation
**Type:** Partly new, partly continuation of original concern.
**What's wrong:** §5.6.1 reports 4PL pooled ED50=36, GLMM=41, bootstrap median=52, with d=0.28 lower asymptote and a=0.69 upper asymptote. But "ED50" could mean: raw p(switch)=0.5; 4PL inflection between asymptotes; net effect=0.5; or 50% of perturbable subpopulation. These are different given nonzero floor and <1 plateau.
**Concrete fix:** Add a short statistical subsection defining p_raw, p_floor, p_net, p_cond. Report ED50 separately for each. Fit hierarchical model with floor parameter informed by control-control pairs.

### 4. Persistent-escape analysis is decisive but still only sparse-pilot scale
**Type:** Previously raised, partially addressed.
**What's wrong:** §5.10.9 applies persistence test to sparse n=50/cell data, not dense n=200/cell.
**Concrete fix:** Run persistence analysis on dense rerun. Report per dose: injection-time jump rate, kicked-and-persisted, kicked-and-returned, final-disagreement-without-jump rates, under k=12, k=4, HDBSCAN.

### 5. Replace-mode perturbation remains mostly an overwrite artifact
**Type:** Previously raised, insufficiently addressed empirically.
**What's wrong:** Theory is now correctly scoped (G_m vs τ), but O2/O3 perturbation results still use overwrite intervention. 94–100% switching is largely built into the intervention.
**Concrete fix:** Run the planned `adversarial_insert_doseN` vs overwrite for O2/O3 (runner code already in place from round 5). Report: overwrite switching, insert switching, no-op floor, period-2 recurrence re-establishment.

### 6. The operational attractor criteria are improved but still partly post-hoc and uneven
**Type:** Previously raised, partially addressed.
**What's wrong:** §3.1.1.5 C1–C4 table issues: C1 uses basin predictability machinery shown to leak family identity; C2 shows "PASS by dwell/basin-null gate" without the actual null means/z-scores in table; C3 recurrence-bin agreement is coarse; C4 mixes contraction, period-2, absorbing collapse, exit-return.
**Concrete fix:** Add compact attractor-criteria appendix table with actual numeric values for C1–C4 under both stratified and group-aware variants. Consider downgrading D1 from "strong" to "attractor-like dialog regime" unless dwell/null numbers are clearly strong.

### 7. D1 is still fragile relative to the strength of its label
**Type:** Previously raised, partially addressed.
**What's wrong:** D1 passes C1–C4 but: group-aware basin predictability k=10 = 0.34; switching is granularity-sensitive; semantic inspection says basins are dialogue-state capture; neutral switching is higher than adversarial in pilot; T-stability is reduced-scope.
**Concrete fix:** Reframe D1 as a "dialogue-state capture regime" with weaker basin predictability and higher granularity sensitivity. Don't overstate attractor strength.

### 8. V* is now better framed, but its evidential role remains marginal
**Type:** Previously raised, mostly addressed; remaining issue is scope.
**What's wrong:** §5.10.10 sensitivity grid is only for O1, but original V* tables cover O1/O2/O3/D1. Sensitivity not shown for the regimes where mechanism mismatch is largest.
**Concrete fix:** Move most V* material to supplement or limit main-text claim to: "O1's adversarial condition has lower descriptive density ridges than controls under a range of KDE settings."

### 9. The paper remains too long and still reads partly like a repository audit
**Type:** Previously raised, partially addressed.
**What's wrong:** Main paper should be: (1) Formal framework, (2) Regime establishment, (3) O1 dense perturbation result, (4) Stress tests, (5) Discussion. Move embedding mechanics, flow-field kernels, visualization battery, animation rendering, CLI commands, repository layout to supplement.

### 10. Cross-model evidence remains useful but not central
**Type:** Previously raised, mostly addressed.
**What's wrong:** §5.14/§7.1 spend a lot of space on 37/37 or 6/6 predicate-style audit language.
**Concrete fix:** Compress to one table in main text. State: "The qualitative append/replace contrast replicated on gpt-4.1-nano; barrier magnitudes shifted."

---

## Did the revision overcorrect?

**In a few places, yes.**

1. **O1 is now under-sold in some local caveats.** The O1 append/continue result is genuinely strong if stated correctly: reproducible monotone in-distribution raw-switching dose response; OOD perturbations near a lower drift floor; group-aware basin predictability remains high; effect robust across cluster granularities. That is enough for a solid claim.

2. **The paper can confidently claim the old "150-token" estimate was wrong and replaced.** The dense rerun is not "in flight" and should not be treated as tentative. Raw-switching ED50 is around tens of tokens, not hundreds.

3. **Replace-mode overwrite transparency is still a valid engineering observation.** It is tautological as an attractor-barrier claim, but not useless. Real recursive systems do erase prior state. Present this as a design property of replace nudges, not as a discovered low barrier.

4. **D2 demotion is appropriate, not overcorrection.**

The main overcorrection risk: the author now buries the strongest finding under caveats. The right framing is not "we failed to measure barriers"; it is: **we measured raw switching robustly, and discovered that raw switching decomposes into stochastic divergence, partial perturbable subpopulation, and rare persistent basin escape.**

---

## Was the dense-dose rerun result honestly characterised?

**Mostly yes.** §5.6.1 is one of the best sections in the revised manuscript. It correctly: reports the original ~150-token story was wrong; gives all three ED50 estimates; reports plateau below 1; reports control-vs-control natural floor; explicitly says net adversarial effect never reaches 50 pp; says "barrier height" should be read as a graded-response parameter, not a sharp threshold.

**Remaining problem is terminology.** The section itself is careful, but the broader manuscript still uses "barrier height" as if raw ED50 were the central object. With a 35% natural floor and 67% plateau, "ED50" needs precise definition. **Honest characterization locally; still insufficiently propagated globally.**

---

## Section-by-section issues

**Abstract / Introduction:** Improved but still rhetorically leads with "barrier height" while strongest result is raw-switching susceptibility with large stochastic floor. "Measured barrier heights in tokens" should become "measured raw-switching dose response in tokens" unless persistent-escape barriers are added.

**§2 Terminology / Background:** §2.6 glossary useful but long; consider compressing in main text. Background still has some self-favorable comparison-table language.

**§3 Formal Framework:** Lemma 1 basically fixed. §3.1.1 barrier definition still too strong relative to measurement — add explicit notation for raw switching vs persistent escape directly in formal section. §3.1.1.5 needs numeric audit table with null statistics.

**§4 Methods:** §4.13 must be updated after dense rerun. Perturbation mechanics should put overwrite vs insert distinction in main methods.

**§5 Results:** §5.0bis is currently stale relative to §5.6.1 — most urgent consistency problem. §5.6.1 should be moved earlier or made centerpiece. §5.10.9 persistence analysis is crucial and should be elevated, not buried in stress tests. §5.11 n=4 correlations expendable.

**§6 Discussion:** Much more sober. §6.1 still slightly overstates "nudge sets regime, generator sets magnitude."

**§7 Limitations:** §7.1 cross-model audit now honest. §7.8 tokens-vs-nats appropriately cautious. Add explicit limitation: "Current dense ED50 is not a persistent-escape barrier."

**§10 / §13 Reproducibility:** Strong overall. Fix 99-vs-94 test-count inconsistency. Code snippets should be checked again against actual implementations.

---

## Suggested next-revision priorities

1. **Globally reconcile all primary numbers with the dense rerun.** Update §4.13, §5.0bis, abstract, intro, discussion, and any "in flight" language. Make one authoritative claim table. **✅ DONE 2026-04-30** — §5.0bis O1 rows now show dense values (switching @200=0.620, @400=0.670; ED50 36-52 with CI [8.5, 242]; upper asymptote 0.69; natural floor 0.347; net-effect not reached; persistent-escape undefined). §4.13 closing paragraph updated. Status legend simplified to drop "in flight".

2. **Reframe the central endpoint taxonomy.** Separate raw-switching ED50, net-above-floor effect, and persistent-escape barrier. State which are established. **✅ DONE 2026-04-30** — new §3.1.1bis "Three operational endpoints for 'barrier height'" drafted by gpt-5.5 high-reasoning, applied. Defines $\mathrm{ED50}_{\mathrm{raw}}$, $\mathrm{ED50}_{\mathrm{net}}$, $\mathrm{ED50}_{\mathrm{persist}}$ formally, reports each on dense data, and explicitly states the formal §3.1.1 barrier corresponds to the persistent-escape endpoint (which is undefined in the tested range).

3. **Run persistence and multi-granularity analyses on the dense rerun.** This is the highest-leverage empirical addition. **✅ DONE 2026-04-30 (persistence)** — `scripts/per_family_and_persistence.py --exp exp_perturb_O1_ed50_dense` produced dense persistence numbers: 16% kicked-and-persisted at dose 400 (vs 67% raw switching, 51 pp gap). §5.10.9 updated with full 8-dose dense table. Multi-granularity on dense data still 🔴 TODO.

4. **Run overwrite-versus-insert perturbations for O2/O3.** Cheap (~$5, ~2 hr). Resolves the replace-mode tautology objection. **✅ DONE 2026-04-30 — major confirming finding.** Results: dose 80: overwrite 92% vs insert 32% (60 pp gap). Dose 200: overwrite 98% vs insert 18% (80 pp gap). **The 60–80 percentage-point overwrite-vs-insert gap is the operator-overwrite tautology contribution.** When the operator no longer overwrites state, switching falls to 18-32% — well below O1's 62-67% raw switching. New §5.10.11 + §6.6 practical-implications row updated. The reviewer's tautology concern is now empirically validated, not just theoretically reframed.

5. **Shorten and restructure the main paper.** Lead with O1 dense-dose + stress tests. Move flow fields, animation tooling, CLI details, most V* visualizations, n=4 correlations, and long repository documentation to supplement. **🟡 PARTIAL** — round 8 of revisions moved most engineering content to §13 supplement (§13.1 Lemma proof, §13.2 metric code, §13.4 perturbation mechanics, §13.5 animation pipeline, §13.6 prompt templates, §13.7 model versioning, §13.8 Phase-0 pilot, §13.9 Phase-1 taxonomy, §13.10 visualization toolkit, §13.11 commands+layout). Additional restructuring per gpt-5.5's recommendation (lead with §5.6.1, demote §5.11) still 🔴 TODO.

## Round-9 fix status (post-2026-04-30 round)

| gpt-5.5 round-2 priority | Status |
|---|---|
| #1 Reconcile primary numbers globally | ✅ DONE |
| #2 Three-endpoint framework (§3.1.1bis) | ✅ DONE — drafted by gpt-5.5 high-reasoning |
| #3 Persistence on dense rerun | ✅ DONE — 16% kicked-AND-persisted at dose 400 |
| #4 Insert vs overwrite experiment | ✅ DONE — **major confirming finding** |
| #5 Test count 94→99 inconsistency | ✅ DONE — final code-block bumped 94 → 99 |
| Sub-priority 6 (Attractor criteria audit table with null statistics) | 🔴 TODO |
| Sub-priority 7 (D1 reframe to dialogue-state regime) | 🔴 TODO |
| Sub-priority 8 (V* sensitivity for O2/O3/D1) | 🔴 TODO |
| Sub-priority 9 (Further structural shortening) | 🔴 partial via round 8 |
| Sub-priority 10 (Cross-model compression) | 🔴 TODO |

---

## Updated verdict at top venues

**NeurIPS / ICML full submission:** Still likely reject in current form, but no longer because the work is unserious. Central term "barrier height" remains overextended relative to evidence. The dense rerun establishes raw-switching susceptibility, not persistent attractor escape. Paper still too long and internally inconsistent in key tables.

**TMLR:** Potentially viable after one more substantial revision. May be more receptive to careful empirical methodology paper, especially with strong reproducibility. Methodology reviewers will object if "barrier" is not operationally aligned with measured endpoint.

**Workshop or arXiv-only:** Strong as arXiv paper or workshop submission now, once stale tables are fixed. Strongest claim to lead with:

> In append-mode continuation loops, in-distribution injected text produces a reproducible raw-switching dose response with ED50 around tens of tokens, but most apparent switching sits on a large stochastic divergence floor and rarely constitutes persistent basin escape.
