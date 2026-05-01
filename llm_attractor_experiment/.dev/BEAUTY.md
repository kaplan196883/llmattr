# BEAUTY.md — Visual quality audit of `paper.pdf`

**Date:** 2026-05-01
**File audited:** `D:\ROOT\llmattr\llm_attractor_experiment\paper\paper.pdf` (80 pages, 11.8 MB)
**Method:** Five parallel agents reviewed PNG renders (120 DPI) of all 80 pages for typography overflow, page-break problems, table layout, figure quality, math rendering, color discrimination, and overall publication-readiness.

---

## Coverage attestation

| Slice | Pages | Sections covered | Issues | Status |
|---|---|---|---:|---|
| 1 | 1–16 | front matter, §1, §2, §3 (start), §4.1–§4.3.1 | 6 substantive | done |
| 2 | 17–32 | §3 tail, §4 (incl. §4.11 pipeline & §4.11.1 shape diagrams) | 8 | done |
| 3 | 33–48 | §5 results: Figures 1–12 + K | 14 | done |
| 4 | 49–64 | §5 tail (Fig G, 14), §6 Discussion, §7 Limitations | 16 | done |
| 5 | 65–80 | §8–§13 supplementary, references | 11 | done |
| **Total** | **1–80** | full document | **~55** | **complete** |

---

## CRITICAL — bugs / data loss / broken rendering

These must be fixed before submission. Reader-facing failures.

### B1. Page 71, §11.3 — unescaped `$` signs throw text into math mode (DATA CORRUPTION)
**Symptom:** The "Compute and cost" bullet renders as garbled mojibake:
> `30inOpenAItext − embedding − 3 − smallAPIcallsforthefull37 − experimentset.∗∗Generationregeneration∗∗: 200 in gpt-4o-mini API calls`

Spaces collapsed, hyphens rendered as math minus signs, model name `text-embedding-3-small` corrupted, `**bold**` markers rendered as literal `∗∗`.

**Cause:** Markdown source has bare `$30` and `$200`; pdflatex enters math mode at the first `$`, exits at the second, eating everything between as math.

**Fix:** Escape both dollar signs in the source — `\$30` and `\$200`. Search the markdown for any other unescaped `$N` patterns.

### B2. Page 66 — wide table overflows page bottom, rows are clipped (DATA LOSS)
**Symptom:** The "if you want / choose / what we measured / not directly tested" table extends past the page footer and bottom of page (y≈1320 px past the y≈1246 footer line). The bottom rows ("collapse (degenerate output)" / "publication-scale validation" / D2 row) are clipped. Page 67 starts directly with `§8 Limitations` — there is **no table continuation**, so the lost rows are gone from the rendered PDF.

**Fix:** Convert the table to `longtable` so it spans pages, or rebalance column widths and shorten column-3 prose so the whole block fits one page.

### B3. Pages 8 and 10 — three bullets all labeled "1." (Markdown→LaTeX bug)
**Symptom:** Numbered lists in the §3.1.1bis endpoint definitions and §3.1.3 conjecture statement render as 1./1./1. instead of 1./2./3.

**Cause:** Each numbered item is a separate `enumerate` environment instead of a single one with three items.

**Fix:** Audit `build_paper_tex.py`'s list rewriter — likely each list item starts a fresh `enumerate`. Merge consecutive numbered items into one environment, or detect numeric prefixes and continue the same `enumerate`.

### B4. Page 54 endpoint summary table — `ED50_raw/net/persist` subscripts not rendering as math
**Symptom:** Table cells contain literal text `ED50_raw`, `ED50_net`, `ED50_persist` with the underscore visible as a character, not as math subscript.

**Cause:** The round-12 terminology fix wrote these as plain markdown `ED50_raw` (which builds escape `_` to `\_` outside math mode), but the canonical scoped form is `$\mathrm{ED50}_{\mathrm{raw}}$` (etc.).

**Fix:** Replace all `ED50_raw` / `ED50_net` / `ED50_persist` occurrences in the source markdown with the math-mode form. Apply across the §6.6 table, §6 Discussion prose, and §7 Limitations narrative.

### B5. Pages 49–52 — section numbering anomaly (§6.20–§6.27 before §7 Discussion header)
**Symptom:** Subsections numbered §6.20 through §6.27 appear *before* the actual `7 Discussion` header on page 63. Reader sees Discussion-numbered subsections inside what should still be Results.

**Diagnosis:** Either the §6 Discussion top-level header is missing entirely, OR these subsections should be §5.20–§5.27 (final Results subsections).

**Fix:** Audit the markdown source structure — likely a missed `## 6 Discussion` header somewhere before §6.20, or these are mis-nested subsections that should remain in §5. Re-audit and renumber.

### B6. Pages 55–62 — large blocks of tables without captions
**Symptom:** Roughly 20+ tables across pages 55–62 appear without any `\caption{}` — including the T1–T6 thesis-verdict table on page 62 (the "audit-style table with checkboxes" the original task flagged), the regime-cluster summary tables on p.57–58, and the multi-table stack on page 56 (six tables, all un-captioned).

**Fix:** Wrap each in a `table` float with `\caption{}` and a `\label{}`, then cross-reference from the §5/§6 narrative. For sub-tables, group with a single parent caption + `(a)/(b)/(c)` subpanel labels.

### B7. Page 27 — multi-column threshold/defined-in table overflows
**Symptom:** 5-column table with mid-word hyphenation ("Attractor- like", "non- control", "neu- tral"), long file paths in the rightmost column crowding neighbors, last row extending close to / past the bottom margin.

**Fix:**
1. Move to `tabularx` or `tabulary` with `>{\raggedright\arraybackslash}p{...}` columns
2. Wrap long paths in `\path{...}` or `\seqsplit`
3. Consider rotating to landscape via `sidewaystable` if still too dense
4. Shrink to `\footnotesize` for body text

---

## IMPORTANT — visible polish issues

These don't break content but visibly degrade publication quality.

### Margin overflow / monospace wrapping (recurrent across the paper)

| Page(s) | Issue |
|---|---|
| 5 | Dialog templates (`alternate`, `single`, etc.) tight near right margin |
| 13–16 | Long file paths (`loop_text01.config_text01.exp_default_...`) wrap awkwardly in tables |
| 19 | `src/analysis/robustness.py:effect_vs_baseline` clipped near right margin (colon suppresses break) |
| 27 | Long source paths in 5th-col cells (see B7 above) |
| 35–36 | §6.12 `scripts/aggregate_basin_predictability.py` paths bleed close to margin |
| 38, 46 | §6.16/§6.17 CLI examples and config paths |
| 49 | `adversarial_dose_overwrite`, `adversarial_insert_dose80` overshoot right margin |
| 53 | Two `.../tables/.../perturb_O3a/b_summarize_negate_replace.csv` paths near margin |

**Universal fix:** In the build pipeline, route inline `\texttt{path/like/this}` through `\path{}` (from `url` package) or `\seqsplit{}` (from `seqsplit` package) to allow breaks at `/`, `_`, `.` characters. Could be done in `build_paper_tex.py`'s inline-code converter when the content matches a path-like pattern.

### Section-heading orphans / page-break tightness

| Page | Section | Issue |
|---|---|---|
| 3 | §2 Background | Heading near page bottom; only 1–2 lines before break |
| 5 | §3 Formal framework | Heading + opening "Let..." line only; rest spills to p.6 |
| 11 | §4.3.3 Append-mode | Heading + 2 lines, then break |
| 44 | §6.19 (or §5.19) | Heading at page bottom; verify next-page content begins cleanly |
| 50 | §6.21 / §6.22 | Stacked headings with very short bodies between |
| 75 | §13.9 | Heading near page bottom |
| 76 | Repository tree | Block split mid-entry across 76→77 (open parenthesis on 76, closing on 77) |

**Universal fix:** Add `\needspace{6\baselineskip}` (from `needspace` package) before each `\section`/`\subsection`. Consider increasing `\clubpenalty` and `\widowpenalty` to suppress short orphan lines.

### Page balance / forced page breaks

| Page | Issue | Suggested fix |
|---|---|---|
| 1 | Title page: large blank band below abstract; title breaks awkwardly across 3 lines (colon at end of line 1) | Manual `\\` line break, recenter title block, or shorten title |
| 2 | Top margin compressed: running header sits very close to abstract continuation | `\headsep` increase |
| 26 | ~75% blank from forced break before §5.11.2 table on p.27 | `\enlargethispage` or move bullets up |
| 65 | ~50% blank below §7.7 close before §8 starts on p.67 | Allow §8 first paragraph to flow up, or accept |
| 80 | ~30% blank at bottom (final page) | Acceptable for closing page |

### Shape & pipeline diagram polish

| Page | Issue | Fix |
|---|---|---|
| 23 | PHASE 4 fan-out: 4 child boxes have unequal heights (TIME-SERIES tallest) | Add `equal height group=phase4-children` to the four child tcolorboxes |
| 23 | Vertical arrows between PHASE 4→5 and 5→6 sit very close to next phase header bar | Add ~2pt `\vspace*` around arrows |
| 24–25 | Shape-annotations diagram splits across page break without "(continued)" cue | Either tighten so it ends on p.24, or add a `\subsubsection*{... (continued)}` at top of p.25 |

### Typos / wording

| Page | Issue | Fix |
|---|---|---|
| 63 | §7.1 heading: "Regime are properties of nudges, not prompts alone" | "Regime**s** are properties..." |
| 63 | §7.2 heading: "Why append exists and replace yields" reads as truncated | Verify intended phrasing — likely "Why append exists and replace yields capitulation" or similar |

### Bibliography URL breaking

| Page | Issue | Fix |
|---|---|---|
| 80 | Multiple references break URLs after `https:` instead of after `/` | Wrap all bibliography URLs in `\url{}` and increase `\Urlmuskip` for safer break points |

### Cell wrap orphans in audit tables

| Page | Table | Issue | Fix |
|---|---|---|---|
| 77 | C2 audit, O3 row | `recursive > null (z »` / `2)` — `2)` orphaned on its own line | Rephrase to "recursive > null, z >> 2" |
| 78 | C4 audit, O2 row | `2 (period_2_score >` / `0)` — `0)` orphaned | Rephrase to "period_2_score positive" |
| 78 | C4 audit, D2 row | `n.t. (insufficient` / `data)` — `data)` orphaned | Rephrase to "n.t., insufficient data" |

---

## MINOR / COSMETIC

| Topic | Pages | Notes |
|---|---|---|
| Color crowding in dose-response figures (D1+O1 = 12 series) | Figs 4 (p.33), 17 (p.46) | Consider 2-panel split (D1 / O1) or per-family line styles (solid/dashed/dotted) for greyscale-print safety |
| Small markers in t-SNE 3×2 grids | Figs 10–12 (pp.41–43) | Increase marker / arrow size in source figure script |
| Stacked figures cramped | Figs 13 + 15 on p.44 | Give each its own page or `\subfloat` side-by-side |
| Cyan/lavender pair near color-discrimination boundary | Fig 18 (p.47) | Optional: shift to higher-contrast palette |
| Decimal alignment in V*/RG tables | p.79 | Use `siunitx` `S` columns or `dcolumn` for true decimal alignment |
| Caption line length on figures with long source paths | Figs G (p.51), 14 (p.52), 4 (p.33) | Wrap source paths in `\path{}` to permit safer slash breaking |
| Legend placement inside plot competes with data series | Fig 5 (p.35) | Move legend to upper-right or below plot |
| Stacked headings (multiple subsections with very short bodies) | p.50 (§6.21+§6.22) | Either merge or add bridging sentence |
| Display-equation tuple wraps tight | p.12 `EDPM_O = (FDM, FDR, FAR, ...)` | Multi-line `align*` environment |
| Header tone: "if you want…" / "choose…" reads conversational in p.66 table | p.66 | Rename to "Goal / Recommended operator / Measured outcome / Not directly tested" |

---

## Strengths (what works well)

These are publication-quality and should NOT be touched:

- **§4.11 pipeline diagram (pages 22–24)** — the new tcolorbox+TikZ rendering is a major improvement over the prior ASCII art. Phase boxes have consistent width matching the text block, dark-gray titles with strong contrast, clean centered down-arrows between phases. The PHASE 4 fan-out busbar tree (single feed → horizontal busbar → 4 drop arrows → 4 child boxes) reads correctly. Two-level hierarchy (outer phase + nested sub-box) is visually distinct.
- **§4.11.1 shape-annotations diagram (pages 24–25)** — uniform 10-box sequential pipeline, matching widths, aligned edges, identical title-bar style, consistent arrows. No clipping or overflow.
- **§13.1 Lemma 1 proof (pages 72–73)** — math display is clean across pages. Display equations centered, no horizontal overflow. Subscripts (`t_inj+k`, `A_k`, `q_0`), filtrations (`F_s`), indicators (`1_{A_k}`), conditional probabilities, expectations all legible. Three `\square` end-of-proof markers all present and correctly placed.
- **§13.2 / §13.10 / §13.11 code blocks** — uniformly legible monospace, no overflow, character substitution issues, or mojibake. Comments visible. Shell line continuation handled cleanly.
- **§13.11 repository tree (page 77)** — uses ASCII `+--`, `|` glyphs (not Unicode box-drawing), most portable choice; renders consistently with clear indentation.
- **§13.12 C1–C4 audit tables (pages 77–78)** — fit textwidth, alignment good, headers with two-line wraps work cleanly.
- **Best figure pages** — Figure 6 (p.37, V* 3D landscapes), Figure 7 (p.38, contours), Figure 9 (p.40, relaxation curves), Figure 14 (p.52, embedding ablation).
- **§7 Discussion prose flow (pages 63–64)** — clean per-subsection structure with thesis sentence + short evidence paragraph.
- **§13.1 / §13.13 / §12 References** — clean structure, consistent formatting, math-display correct.

---

## Recommended fix order

If applying changes, lowest-risk-highest-payoff sequence:

1. **B1 (page 71 `$N` math-mode bug)** — single-line search/replace; biggest reader-facing damage.
2. **B3 (1/1/1 list bug)** — likely a `build_paper_tex.py` enumerate-merge fix; affects multiple pages.
3. **B4 (`ED50_raw` subscripts)** — search/replace `ED50_raw` → `$\mathrm{ED50}_{\mathrm{raw}}$` etc., then rebuild.
4. **B2 (page 66 table overflow)** — convert to `longtable`.
5. **B5 (§6.x numbering anomaly)** — audit markdown source for missing `## 6 Discussion` header or mis-nested subsections.
6. **B6 (un-captioned tables)** — bulk pass adding `\caption{}` + `\label{}` to ~20 tables across pages 55–62.
7. **B7 (page 27 table overflow)** — `tabularx` rebuild + `\path{}` for paths.
8. **Margin-overflow fixes** — global `\path{}`/`\seqsplit` wrapper in `build_paper_tex.py` for path-like content.
9. **Section-heading orphans** — `\needspace{6\baselineskip}` before each `\section`/`\subsection`.
10. **Polish items** (typos, bibliography URLs, fan-out equal-height, cell-wrap orphans, page-balance tweaks).
11. **Cosmetic items** (figure color/marker tweaks, decimal alignment, legend placement).

After every batch, recompile via `scripts/build_paper_tex.py` and inspect the affected pages.

---

## Summary verdict

The paper is at **publication-ready quality once the 7 critical bugs are fixed**. The §4.11 pipeline diagram conversion was successful — that visual element alone is now the strongest "above-the-fold" technical-aesthetic improvement. The body math, code blocks, references, and audit tables in the supplementary are clean. The dominant issues are:

1. **Three rendering bugs** that are reader-facing and must be fixed (B1 dollar signs, B3 list numbering, B4 subscripts).
2. **One layout bug causing data loss** (B2 page-66 table clipping).
3. **One structural bug** (B5 §6.x numbering anomaly).
4. **A bulk caption pass needed** for un-captioned tables (B6).
5. **A global path-wrapping pass** to eliminate margin overflow (recurrent across many pages).

Once the 7 criticals plus the global path-wrapping are applied, the paper visual quality will be comfortably TMLR-submission grade.
