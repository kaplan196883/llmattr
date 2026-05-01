# FIXING.md — Line-by-line audit of `ARTICLE.md`

**Date:** 2026-05-01
**File audited:** `D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md` (5254 lines)
**Method:** Five parallel agents each verified ~1000-line slices for typos, numbering errors, broken cross-references, terminology drift (post-round-11 conventions), numerical-canonical-value drift, markdown formatting, and LaTeX/math balance. The article is read-only here — this file logs findings only.

---

## Coverage attestation

| Slice | Range | Lines | Sections covered | Issues | Status |
|---|---|---:|---|---:|---|
| 1 | 1 – 1100 | 1100 | front matter, §1, §2, §3.1.1–§3.3, §4.1–§4.3.1 (start) | 6 | done |
| 2 | 1101 – 2100 | 1000 | §4.3 (cont.), §4.4, §4.5, §4.6–§4.13 | 11 | done |
| 3 | 2101 – 3100 | 1000 | §5.0–§5.10.8 (taxonomy, basin pred, switching, dose-response, dense rerun, V*, group-aware, multi-granularity, semantic clusters) | 22 | done |
| 4 | 3101 – 4135 | 1035 | §5.10.9–§5.14, §6 Discussion, §7 Limitations | 8 | done |
| 5 | 4136 – 5254 | 1119 | §8 Future work, §9 Methods appendix, §10 Reproducibility, §11 Ack, §12 References, §13 Supplementary | 6 | done |
| **Total** | **1 – 5254** | **5254** | full document | **53** | **complete** |

---

## Master issue list (prioritized)

### Critical — substantive scientific or numerical errors

| # | Line(s) | Type | Issue | Fix |
|---|---|---|---|---|
| C1 | 3937 | numbering | `4-of-5 attractor criteria PASS` — §3.1.1.5 defines 4 criteria (C1–C4), not 5. D1 is "formal C1–C4 PASS" elsewhere. | `4-of-4 (formal C1–C4) attractor criteria PASS (§3.1.1.5)` |
| C2 | 5074–5078 | terminology / table contradiction | Closing sentence "only O1 is a strong attractor" silently re-promotes O1 to "strong attractor", contradicting both the §13.12 aggregate-verdict table (O1 = borderline 3/4 z-tested) and the "Honest reading" paragraph two lines above. | Rephrase to: under group-aware C1 only, O1 still passes C1; under combined group-aware C1 + z-tested C2, no regime achieves "strong attractor". |
| C3 | §13 ordering: 4960–5254 | numbering | §13 subsections appear as 13.1, 13.2, 13.4–13.9, **13.12, 13.13, 13.3, 13.10, 13.11** — non-monotone twice. §13.10 (viz toolkit) and §13.11 (repro commands) are normal numbered sections, not wrap-up. | Reorder to: 13.1, 13.2, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 13.12, 13.13, 13.3 (final pointers). |
| C4 | 2469 | xref | "the dense-dose rerun in §8" — §8 is "Future work"; the dense-dose rerun is in §5.6.1. | Change `§8` → `§5.6.1`. |
| C5 | 2485–2486, 2569 | numerical notation | `8 doses × n=200/cell × 5 families × 10 ICs × 4 runs = 1,800` does not literally equal 1,800 (the literal product is 320,000 / 1,600,000 in Figure K caption). The correct decomposition is `n=200 = 5 fams × 10 ICs × 4 runs`, with `9 cells × 200 = 1,800`. | Rephrase: `n=200/cell (= 5 families × 10 ICs × 4 runs); 8 doses + 1 control × 200 = 1,800 trajectories total`. Apply to both §5.6.1 prose and Figure K caption. |
| C6 | 922 | xref | `Let V(x) = -\log \rho(x) be the empirical potential (§2.3, §5.10)` — §2.3 is "What this paper adds"; the empirical potential is defined in §2.4. | Change `(§2.3, §5.10)` → `(§2.4, §5.10)`. |
| C7 | 1586 | xref | "Beyond the perturbation toolkit (4.9)" — §4.9 is flow-field; the perturbation toolkit is §4.10. | Change `(4.9)` → `(§4.10)`. |
| C8 | 5074 | typo | `The §3.1.1.5 §3.1.1.5 label rule` — duplicate token. | Delete one occurrence. |

### Important — terminology drift relative to round-11 conventions

| # | Line | Issue | Fix |
|---|---|---|---|
| T1 | 257 | D1 = "stylistic multi-basin dialog" | → "dialogue-state-driven multi-basin dialog" |
| T2 | 265 | Table cell "+ D1 stylistic-multi-basin" | → "+ D1 dialogue-state-driven multi-basin" |
| T3 | 321 | "stylistic / multi-basin behavior (D1)" | → "dialogue-state-driven multi-basin behavior (D1)" |
| T4 | 983 | H2 hypothesis: `Dialog ⇒ stylistic multi-basin` | → "dialogue-state-driven multi-basin" |
| T5 | 1906 | Pipeline diagram: `H1a strong + H1b weak ⇒ contractive / multi-basin (O1, D1)` | Split D1: "contractive / multi-basin (O1); dialogue-state-driven multi-basin (D1)" |
| T6 | 2244 | §5.0 row label `**D1** multi-basin` (no qualifier) | → `**D1** dialogue-state-driven multi-basin` |
| T7 | 2256 | "D2 adds content gravity beyond D1's stylistic basins" | → "...beyond D1's dialogue-state basins (see §5.10.8)" |
| T8 | 2384 | "Once the dialog regime locks into a stylistic basin..." | → "Once the dialog regime locks into its dialogue-state basin..." |
| T9 | 2447–2448 | `"dialog basin is stylistic, not content-bound"` | → `"dialog basin is dialogue-state-driven, not content-bound"` |
| T10 | 2747 | Table row label `D1 stylistic dialog` | → `D1 dialogue-state-driven dialog` |
| T11 | 2835 | Cluster-stability row `D1 stylistic dialog` | → `D1 dialogue-state-driven dialog` |
| T12 | 2241 | `ED50 ≈ 40 tok` unscoped | → `ED50_raw ≈ 40 tok` |
| T13 | 2445 | "The barrier height (in this dose sense) is essentially zero" | → "The raw-switching barrier height is essentially zero" |
| T14 | 2470 | "first reported dose-response barrier-height measurement" | → "first reported raw-switching dose-response barrier-height measurement" |
| T15 | 3372 | "the overwrite contribution is **operator-independent**" | → "...operator-independent **within the two tested replace-mode operators (O2, O3)**" |
| T16 | 3876, 3881–3884 | §6.4 "Barrier height ... once measured in tokens" — pre-round-11 single-number framing | Reframe via §3.1.1bis three-endpoint decomposition; emphasize ED50_raw ≈ 40 reached but ED50_net and ED50_persist not reached. |
| T17 | 3901–3903 | "before the dynamics re-aim" — ambiguous endpoint | Qualify which endpoint, or drop bolded conclusion. |
| T18 | 3911 | "geodesic barrier estimates ... align with behavioral switching thresholds" overstates §5.10.10 (only ordinal/rank-stability survives, 14–24% CV) | Replace `align with` → `rank-correlate with` / `have the same ordinal structure as`. |
| T19 | 3922–3923 | "barrier height as a real structural property" — pre-round-11 framing | Qualify endpoint or refer to "rank-ordering of barrier endpoints". |
| T20 | 3935 | §6.6 row 1: unqualified `dense-dose ED50 ≈ 40 tokens` | → `dense-dose ED50_raw ≈ 40 tokens; ED50_net and ED50_persist not reached in tested 5–400 token range` |
| T21 | 3936 | §6.6 row 2: "the contribution is operator-independent" | → "...operator-independent within the two tested replace-mode operators (O2, O3)" |
| T22 | 3963–3965 | §6.7: "barrier height is the operational bridge" | → "barrier-endpoint structure (raw / net / persistent-escape, §3.1.1bis) is the operational bridge" |

### Minor — formatting, references, ambiguity

| # | Line(s) | Issue | Fix |
|---|---|---|---|
| M1 | 293 | `V(x) = −log ρ(x)` raw Unicode, not LaTeX-wrapped | Change to `$V(x) = -\log \rho(x)$` |
| M2 | 1593–1622 | Static-viz battery letters skip **D** (A, B, C, E, F, G/H/I) | Re-letter contiguously, or document the gap |
| M3 | 1857 | Pipeline diagram references `Z_PCA20`, but §4.4.1 only documents PCA-2 / -10 / -50 | Either add PCA-20 to §4.4.1, or remove from diagram |
| M4 | 2085 | Endpoint table cell uses pilot `n=50`, 4 doses while same row text on 2098 cites dense rerun (n=200, 8 doses) | Annotate cell with "(original sparse sweep; dense rerun in §5.6.1 uses n=200/cell × 8 doses)", or split rows |
| M5 | 2456 | "natural drift floor of ~24%" (OOD-flat O1 neutral) reuses terminology of dense-rerun "natural floor" 0.347 | → `out-of-distribution drift floor of ~24%` |
| M6 | §5.10 | §5.10 followed by §5.10.5 (no §5.10.1–4 anywhere) | Renumber §5.10.5–§5.10.11 → §5.10.1–§5.10.7, OR add explanatory note |
| M7 | 2247–2249 | Orphaned `**` footnote — anchor missing in table | Add `**` markers to relevant D2 cells, or rephrase |
| M8 | 2354 | Overloaded `T` (just used for temperature, here means trajectory length) | Write `(t ≥ 0.7 T_traj)` or use different symbol |
| M9 | 2470 | "first reported ... we do not claim priority" — mild self-contradiction | Rephrase to "Systematic dose-response measurement ... has not, to our knowledge, been a focus of prior work" |
| M10 | 2802 | "p < 0.05" with 95% CI [-1.21, -0.02] (just barely excludes 0) — reporting both is redundant | Drop p-value or report exact (e.g., `p = 0.04`) |
| M11 | 2241 | `54% (sparse) / 62% (dense, n=200)` confusing — mixes dose-200 and dose-400 | Disambiguate: `54% (sparse, dose 200) / 62% (dense, dose 200) / 67% (dense, dose 400)` |
| M12 | 2453, 2463 vs 2441 | Dose-table headers inconsistent (`dose` vs `dose (tokens)`) | Use `dose (tokens)` everywhere |
| M13 | 2964 | `gpt-5.5` model identifier — verify it's the actual model ID, not placeholder. String appears 5 times (2964, 3192, 3208, 3337, 4962). | Confirm or fix all 5 occurrences |
| M14 | 4546 | `Tuci, M., Korkmaz, C., Şimşekli, U., Birdal, T. (2026).` — missing `&` before last author | → `..., U., & Birdal, T. (2026).` |
| M15 | 4522–4525 | Hopfield (1982) before Holtzman (2020); "Hol" < "Hop" alphabetically | Swap order |
| M16 | 5147 | `§3.1.3 effective-context-share formulation, §3.1.3 geometric refinement` — both correct but reads as duplicate | Consolidate: `§3.1.3 effective-context-share formulation and geometric refinement` |
| M17 | 2469 | "first **reported** ... do not claim priority" plus chained xrefs in single parenthetical | Once §8→§5.6.1 fix is applied, smooth the parenthetical |
| M18 | 2583, 2605 | Matched-relaxation comparison D1-neutral-25 vs D2-adversarial-25 — condition mismatch (already conceded but easy to miss) | Make condition mismatch explicit |

### Cosmetic — style, consistency

| # | Line | Issue | Fix |
|---|---|---|---|
| S1 | 1623–1624 vs 2031 | "50–150 PNGs" vs "70–150 PNGs" | Pick one |
| S2 | 1693 | "sigma" plain text where elsewhere `σ` | Optional: → `σ = 1.5–2.0 cells` |
| S3 | 1810 | ASCII-art alignment: `│` at end of line not padded | Cosmetic |
| S4 | 1989 | `T={0.3,0.6,0.8,1.2}` — no spaces after commas | Cosmetic |
| S5 | 2031 | Hyphen `-` instead of en-dash `–` in "70-150" | Cosmetic |
| S6 | 2060 | "Python 3.x" too vague for methods | → `Python ≥ 3.10` (pin to actual `requirements.txt`) |
| S7 | 2061–2062 | "99 pytest tests, all green" — verify count is current at submission time | Verify before submission |
| S8 | 1379 | "absorbing" / "absorbing fixed point" used interchangeably | Style note only |

---

## Per-chunk detailed audit logs

### Chunk 1 — Lines 1–1100 (front matter, §1, §2, §3, §4.1–§4.3.1 start)

**Issues found:** 6 (4 terminology, 1 math/format, 1 xref).
**Verified clean ranges:** lines 1–256, 258–290, 291–292, 294–320, 322–471, 472–921, 923–982, 984–1100.

Key findings:
- 4× "stylistic multi-basin" → "dialogue-state-driven multi-basin" (T1–T4 above)
- Line 293 raw Unicode V(x) instead of LaTeX (M1 above)
- Line 922 §2.3 → §2.4 (C6 above)
- All canonical numerical values (ED50 36/41/52, plateau 0.67, floor 0.347, 1,800 traj design, 13–24% CVs) are internally consistent.
- All Lemma 1 / Conjecture 1 / Corollary 1, 2 cross-references resolve to defined objects.
- Section numbering 1.1–3.3 and 4.1–4.3.1 sequential without skips.
- "Strong attractor" usages limited to the explicit 4/4-criteria definition context (acceptable).

### Chunk 2 — Lines 1101–2100 (§4.3 tail, §4.4, §4.5, §4.6–§4.13)

**Issues found:** 11 (1 critical xref, 1 important terminology, 9 minor/cosmetic).
**Note on scope:** Range ended mid-§4.13, NOT at §5 as the audit prompt anticipated. §4.12 (Hardware/software) and §4.13 (Decision-grade endpoints) appear after §4.11 and run past 2100. §5 begins later.
**Verified clean ranges:** lines 1101–1235, 1237–1300, 1302–1340, 1341–1420, 1422–1490, 1492–1535, 1536–1582, 1626–1754, 1756–1766, 1768–1994, 1996–2054, 2056–2100 (apart from flagged items).

Key findings:
- C7 (line 1586) §4.9 → §4.10 cross-ref bug
- T5 (line 1906) D1 missing dialogue-state qualifier in pipeline diagram
- M2 (1593–1622) static-viz letters skip D
- M3 (line 1857) PCA-20 introduced without definition
- M4 (line 2085) sparse vs dense dose-sweep ambiguity
- S6 (line 2060) "Python 3.x" too vague

### Chunk 3 — Lines 2101–3100 (§5.0 through §5.10.8)

**Issues found:** 22 — includes the most prominent set: stale §8 xref, sample-size-arithmetic notation, residual "stylistic" framings, unscoped "barrier height" usages.
**Verified clean ranges:** lines 2101–2115, 2116–2143, 2157–2228, 2231–2261 (with flagged exceptions), 2263–2331, 2332–2399, 2401–2432, 2480–2520, 2521–2570, 2571–2592, 2593–2622, 2623–2657, 2658–2712, 2713–2785, 2786–2806, 2807–2876, 2877–2952, 2953–3097.

Key critical/important findings:
- C4 (line 2469) §8 → §5.6.1
- C5 (lines 2485–2486, 2569) sample-size arithmetic notation
- T6–T11 (lines 2244, 2256, 2384, 2447–2448, 2747, 2835) D1 "stylistic" → "dialogue-state-driven"
- T12–T14 (lines 2241, 2445, 2470) unscoped "barrier height" / "ED50"
- M5 (line 2456) "natural drift floor" terminology collision
- M6 (§5.10 numbering jump from §5.10 to §5.10.5)
- M7 (orphan footnote at 2247–2249)
- M8 (overloaded `T` at 2354)
- M11 (confusing 54%/62% mix at 2241)
- M13 (gpt-5.5 model ID — appears 5×)
- All canonical numerical values verified consistent.

### Chunk 4 — Lines 3101–4135 (§5.10.9–§5.14, §6 Discussion, §7 Limitations)

**Issues found:** 8 — clustered in §6 Discussion and §6.6 table. §5 portion (3101–3735) is clean.
**Verified clean ranges:** lines 3101–3146, 3147–3206, 3207–3240, 3242–3300, 3302–3408, 3409–3475, 3477–3575, 3577–3667, 3669–3735, 3738–3817, 3818–3847, 3848–3874, 3925–3954, 3969–4054, 4056–4068, 4070–4079, 4081–4089, 4091–4099, 4101–4111, 4113–4121, 4123–4133.

Key findings:
- C1 (line 3937) `4-of-5` → `4-of-4`
- T15 (line 3372) "operator-independent" needs scoping
- T16–T19 (lines 3876, 3881–3884, 3901–3903, 3911, 3922–3923) §6.4/§6.5 pre-round-11 single-number "barrier height" framing
- T20–T22 (lines 3935, 3936, 3963–3965) §6.6 / §6.7 same
- §6.1 retention-of-legacy-labels notice (lines 3812–3813) makes §6.3 legacy "stylistic multi-basin" usage acceptable.
- §7 Limitations clean and correctly hedged throughout.
- All §5 numerical claims verified (16% / 10% / 39.5% persistence; O2 60–80 pp / O3 72–80 pp insert-vs-overwrite gaps; CV 14–24% V*; T1–T6 cross-model audit).

### Chunk 5 — Lines 4136–5254 (§8–§13 supplementary)

**Issues found:** 6 (1 critical ordering, 1 critical typo, 1 critical text/table contradiction, 3 minor).
**Verified clean ranges:** lines 4136–4220, 4223–4294, 4297–4415, 4419–4430, 4434–4498, 4500–4521, 4526–4545, 4547–4686, 4690–4693, 4697–4759, 4760–4816, 4818–4846, 4848–4856, 4858–4913, 4915–4930, 4932–4958, 4960–5073, 5079, 5080–5136, 5138–5146, 5148–5151, 5153–5189, 5191–5254.

Key findings:
- C3 (lines 4960–5254) §13 ordering bug: 13.1, 13.2, 13.4–13.9, 13.12, 13.13, 13.3, 13.10, 13.11 (non-monotone twice).
- C8 (line 5074) duplicate `§3.1.1.5 §3.1.1.5`
- C2 (lines 5074–5078) prose "only O1 is a strong attractor" contradicts §13.12 audit table.
- M14 (line 4546) Tuci entry missing `&`
- M15 (lines 4522–4525) Hopfield/Holtzman alphabetical order
- M16 (line 5147) cosmetic §3.1.3 / §3.1.3 phrasing
- §13.1 Lemma 1 full proof math is consistent with §3.1.2 statement; all `$$ ... $$` blocks balanced.
- All §-cross-references, code-fence balance, V*/RG numerical claims, and reference-list citation–entry round-trips check out.
- D1 in §13.8 (phase-0 pilot) uses post-round-11 "dialogue-state-driven multi-basin" — correct.

---

## Recommended fix order

If applying changes, the lowest-risk-highest-payoff sequence:

1. **Critical-numbering / critical-xref first (C1, C4, C6, C7, C8):** five trivial single-line edits that fix outright errors.
2. **Critical text/table contradictions (C2):** one paragraph rewrite at lines 5074–5078.
3. **§13 reorder (C3):** one block move (5153–5254 → before 4960). Verify cross-refs to §13.10/§13.11 still resolve.
4. **C5 sample-size arithmetic (lines 2485–2486, 2569):** rephrase to make `1,800` parse correctly. This shows up in the abstract / §5.6.1 / Figure K caption — apply consistently.
5. **Terminology pass T1–T22:** straightforward search-and-replace plus a few §6 paragraph-level rewrites.
6. **Minor (M1–M18) and cosmetic (S1–S8):** polish pass.

After every batch, recompile `paper.tex` via `scripts/build_paper_tex.py` and inspect the affected pages.

---

## Audit notes

- Numerical canonicals verified intact across the document: ED50_raw ≈ 36/41/52 tok with 95% CI [8.5, 242]; plateau ≈ 0.67; natural floor ≈ 0.347; logistic params a=0.69, d=0.28, b=1.16; design n=200/cell × 8 doses + control × (5 fams × 10 ICs × 4 runs) = 1,800 trajectories; persistence max 16% (k=12), 10% (k=4), 39.5% (HDBSCAN); O2/O3 overwrite-vs-insert gaps 60–80 pp / 72–80 pp; CV 14–24%; ordinal stability 89–98%.
- Figures 1–14 + G, H, I, J, K, L all introduced and referenced consistently; the audit-table figure-numbering sequence matches in-text mentions.
- `gpt-5.5` model identifier (5 occurrences) flagged for confirmation but not modified.
- No major math errors: all `$ ... $` and `$$ ... $$` blocks balanced; Lemma 1 / Corollary 1 / Corollary 2 / Conjecture 1 statements internally consistent between §3 and §13.1.
- Code-fence balance (Python and bash blocks in §13.2, §13.10, §13.11) clean.
- Reference list (§12) round-trips with all citation-keys used in body modulo M14 (Tuci `&`) and M15 (Hopfield/Holtzman ordering).
