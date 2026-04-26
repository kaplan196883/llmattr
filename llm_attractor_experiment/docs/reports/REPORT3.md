# REPORT 3 — The full dynamical taxonomy of recursive LLM loops

**Date:** 2026-04-23
**Scope:** unifies findings from REPORT1 (continue-append baseline), REPORT2
(operator × loop_mode grid), and the new dialog experiments (D1, D2, D3).
**Artifacts:** all experiments under `data/`, all configs under `configs/`,
analysis pipeline at `src/` + `src/experiments/`.
**Model under test:** `gpt-4o-mini`.
**Embedding model:** `text-embedding-3-small`.

## 1. One-sentence summary

Three axes of dynamical behavior (convergence, oscillation, divergence)
partition the observable space of recursive LLM loops; with gpt-4o-mini, the
operator, loop_mode, and dialog-pair jointly determine which axis fires —
producing in total **four regime outcomes** (fixed-point basin, 2-cycle,
absorbing state, and contractive dialog with multi-topic sub-basins) — and
**none of our experiments produced the exploratory/divergent regime** claimed
for some operators in the literature.

## 2. Experimental surface area

| experiment | loop | loop_mode | operator / personas | seeds | steps | trajectories |
|---|---|---|---|---|---:|---:|
| exp_default | single-LLM | append | continue | 3 families × 5 ICs × 3 runs | 15 | 135 |
| exp_long | single-LLM | append | continue | 3 × 3 × 3 | 40 | 54 |
| exp_noclip | single-LLM | append (no clip) | continue | 3 × 3 × 3 | 40 | 54 |
| exp_op_O1 | single-LLM | append | continue | 3 × 2 × 3 | 40 | 36 |
| exp_op_O2 | single-LLM | replace | paraphrase | 3 × 2 × 3 | 40 | 36 |
| exp_op_O3 | single-LLM | append | summarize+negate | 3 × 2 × 3 | 40 | 36 |
| exp_op_O3b | single-LLM | replace | summarize+negate | 3 × 2 × 3 | 40 | 36 |
| exp_op_O4 | single-LLM | append | paraphrase | 3 × 2 × 3 | 40 | 36 |
| exp_dialog_D1 | two-LLM | append | curious user + helpful agent | 3 × 2 × 3 | 20 | 18 |
| exp_dialog_D2 | two-LLM | replace | same as D1 | 3 × 2 × 3 | 20 | 18 |
| exp_dialog_D3 | two-LLM | append | advocate + skeptic (debate) | 3 × 2 × 3 | 20 | 18 |

Total: **~20,000 generation API calls**, cost under $5, wall time ~12 h
across 11 experiments.

## 3. Measurement pipeline — what we added beyond req1

REPORT1 used the original three-metric pipeline (recurrence, dwell, basin).
That was sufficient to identify the contractive regime but could not detect
cycles (the standard recurrence metric averages over even and odd lags, so a
strict 2-cycle produces recurrence ≈ 0.5 regardless). REPORT2 and REPORT3
used an extended pipeline:

| metric | added in | what it detects |
|---|---|---|
| recurrence | req1 (baseline) | generic within-trajectory closeness; can't distinguish contraction from cycling |
| dwell | req1 | time in a cluster; positive in contractive and oscillatory regimes |
| basin | req1 | cross-run convergence from same seed |
| late_recurrence | REPORT1 v2 | recurrence restricted to steps ≥ 0.5T — tests "does trajectory revisit *after* basin entry" |
| exit/return | REPORT1 v2 | exit count and return probability from the dominant cluster |
| basin_entry | REPORT1 v2 | first step where ≥70% of remaining steps are in target cluster |
| **period_2_score** | REPORT2 | `dist(lag=1) − dist(lag=2)` — positive → 2-cycle |
| **best_period** | REPORT2 | lag at which mean pairwise distance minimizes |
| **dispersion_growth** | REPORT2 | `std(second_half) − std(first_half)` — positive → diverging |
| **role-separated observables** | REPORT3 | `rolling_user_k3`, `rolling_agent_k3`, etc. — disentangle role alternation from content dynamics |

The classifier now produces a three-axis verdict (H1a / H1b / H1c) instead
of the original single-label one. See `src/experiments/operators/classifier.py`.

## 4. Full results

### 4.1 Three-axis verdict matrix

| experiment | H1a convergence | H1b orbit | H1c divergence | regime classification |
|---|---|---|---|---|
| exp_default (15 steps) | strong | none | none | contractive |
| exp_long (40 steps) | strong | none | none | contractive |
| exp_noclip (40 steps) | strong | none | none | contractive |
| O1 continue/append | strong | none | none | contractive |
| **O2 paraphrase/replace** | **strong** | **moderate** | none | **oscillatory (2-cycle)** |
| O3 summarize+negate/append | strong | none | none | contractive (absorbing state) |
| O3b summarize+negate/replace | strong | none | none | contractive (absorbing state) |
| O4 paraphrase/append | strong | none | none (weak artifact¹) | contractive |
| D1 curious+helpful/append | strong | none | none | contractive dialog |
| D2 curious+helpful/replace | strong | none (content)² | none | contractive dialog |
| D3 debate/append | strong (0.931) | none | none | contractive debate (TIGHTER than cooperative dialog) |

¹ `drift_monotonicity` fires in append mode because context_tail grows; `dispersion_growth` (unconfounded) shows contraction.
² D2 shows mechanical label-alternation cycle in mixed-role observables, NOT content-level oscillation. Role-separated observables confirm the underlying content is still contractive.

### 4.2 The four observed regimes

**Regime I — contractive / fixed-point basin** (7 experiments)

Canonical signature:
- `best_period_median = 1` (consecutive points closest)
- `period_2_score < 0` (lag-1 < lag-2; smooth drift)
- `dispersion_growth < 0` (trajectory tightens)
- `basin_score ~ 0.94–1.00` (same seed → same late cluster)
- `recurrence < time_shuffled` (smoothness suppresses recurrence below null)

This is the "attractor basin with drift-to-fixed-point" described in REPORT1
and confirmed by the Agentic Loops paper (arXiv 2512.10350) for the contractive
class.

**Regime II — oscillatory / 2-cycle attractor** (1 experiment: O2)

Canonical signature:
- `best_period_median = 2` in 100% of runs (context_tail and output)
- `period_2_score > 0` (lag-2 < lag-1)
- basin ~ 0.94 (runs still converge, but to the *cycle* not to a point)

Observed only in paraphrase-in-replace-mode. First independent replication of
arXiv 2502.15208 with our instrumentation.

**Regime III — absorbing state** (2 experiments: O3, O3b — both loop_modes)

Distinct from regime I because the fixed point is reached algebraically on
step 1 and the trajectory emits byte-identical output forever thereafter.
Canonical signature:
- `dispersion_growth` strongly negative (-0.04 to -0.06)
- `best_period = 1` but for a degenerate reason: lag-1 = lag-2 = lag-3 = … = 0
- basin = 0.91 — runs may land on different identical-pairs but each run's
  own trajectory is static

Not an H1a success in the usual sense (a narrow region of state space) but a
single algebraic fixed point. The operator "(X + ¬X)" reaches the
self-consistent two-sentence pair in one step; the model correctly recognizes
the pair is closed under the operator and sits there. A fourth distinct kind
of attractor behavior not previously catalogued.

**Regime IV — contractive dialog with multi-topic sub-basins** (2 experiments: D1, D2)

Appears in two-LLM dialogs. Canonical signature:
- `H1a strong` per the coarse classifier (basin ~ 0.85)
- BUT manual inspection shows three different runs from the same seed reach
  three semantically unrelated destinations (philosophy seed → marketing /
  dream interpretation / legal rights)

The classifier reports convergence because K-means on 360 points with k=8
produces coarse clusters that capture conversational *style/register* more
than topical content. All three trajectories sound stylistically similar
(helpful, 1–2 sentences, cooperative exchanges) so they share a cluster.

**Finer-grained interpretation:** dialog has a *branching* dynamic near the
seed. Each run's sampling noise determines which topical sub-basin it lands in.
All basins share the same *stylistic* attractor (RLHF-aligned cooperative
concrete register), but the topical destination varies.

This is distinct from single-LLM contractive regime (I), where same-seed runs
reliably land in the same topical basin.

**The missing regime — exploratory / divergent (H1c)**

Not observed in **any of the 11 experiments**, including the D3 debate
experiment designed specifically to provoke it. D3's basin score (0.931) is
the *highest* of any dialog experiment — explicit disagreement between
personas produced **tighter**, not looser, contraction. Each side drifted
smoothly through new arguments, but all their arguments supported their
fixed position, and the overall trajectory stayed in an extremely tight
"debate about this specific claim" region of embedding space.

**Tentative conclusion: H1c may be empirically unachievable with gpt-4o-mini.**
RLHF training appears to bias all trajectories toward *some* form of stable
dynamical state — basin (I), cycle (II), absorbing point (III), or
stylistic attractor (IV) — but never unbounded divergence. To get H1c one
would likely need:
- a non-aligned / base model, or
- an operator with explicit randomization / entropy injection each step, or
- a temperature high enough (T >> 1) to overcome alignment bias.

Possible causes for the original arXiv 2512.10350 exploratory finding for
`summarize+negate` are now further constrained: since the operator produces
an absorbing state (III) in both loop_modes with gpt-4o-mini, the reported
exploratory regime must have been specific to their weaker/non-aligned
model (deepseek-r1:8b) rather than to the operator itself.

## 5. Novel claims

### 5.1 Loop_mode × operator is a non-trivial interaction

The published literature (arXiv 2502.15208, 2512.10350) treats the operator as
the sole determinant of the regime. Our O2/O4 comparison falsifies this:

| | replace | append |
|---|---|---|
| paraphrase | **2-cycle (regime II)** | **fixed-point (regime I)** |

Same model, same seeds, same temperature, same persona — only the update rule
differs, and the regime flips entirely. The accumulating context in append mode
*suppresses* the 2-cycle. Mechanism: in replace mode, each step only sees
Y_{t-1}, so the output Y_t is always a paraphrase of a paraphrase — two such
paraphrases form a closed orbit. In append mode, step t's context contains all
prior paraphrases; the model must produce a paraphrase consistent with the
full set, which anchors it on a fixed point.

### 5.2 Role-separated observables disentangle mechanical from semantic dynamics

In D2 (replace-mode dialog), the `context_tail` and `output` observables both
show `best_period = 2`, superficially suggesting oscillation. The role-
separated observables (`rolling_user_k3`, `rolling_agent_k3`) filter out role
alternation and confirm the "cycle" is mechanical — the same role's own
trajectory drifts contractively. **Without this disentanglement, 19% of runs
in D2 would have been misclassified as oscillatory.**

This methodological contribution is new relative to the two cited papers.

### 5.3 Dialogs have multi-topic sub-basins

In single-LLM experiments, same-seed runs reliably land in the same topical
region (basin ~ 0.99). In two-LLM dialogs, same-seed runs converge
stylistically but may land in topically unrelated content regions (basin ~
0.85, but inspection reveals the basin is style not topic).

This matches practical observations in dialog systems — long conversations
with helpful-assistant LLMs drift toward concrete actionable content
regardless of seed topic, a phenomenon sometimes called "conversational
drift". We quantify it for the first time with basin metrics and show it
coexists with a stylistic attractor.

### 5.4 The absorbing-state regime is a fourth attractor class

O3 and O3b found an operator with an algebraic fixed point (the pair
"X + ¬X" is closed under "summarize+negate"). A sufficiently capable model
reaches this in one step and emits byte-identical output forever. This is
distinct from a "small basin" (regime I) in both mechanism and topology —
it's a single point, not a region. The literature's three-regime taxonomy
does not distinguish this case.

## 6. Coverage vs the literature

| paper prediction | our observation | match |
|---|---|---|
| arXiv 2502.15208 — successive paraphrasing → 2-cycle | O2 confirms with 100% of runs at best_period=2 | ✓ |
| arXiv 2512.10350 — "contractive" regime for rewrite-style operators | confirmed in O1, exp_long, exp_noclip | ✓ |
| arXiv 2512.10350 — "exploratory" regime for summarize+negate | refuted in O3/O3b under both loop_modes; gpt-4o-mini reaches absorbing state instead | ✗ |
| arXiv 2512.10350 — operator alone determines regime | refuted by O2/O4 comparison — loop_mode matters equally | ✗ |
| arXiv 2510.01171 — typicality bias drives mode collapse | consistent with our regime-IV finding (dialogs drift toward RLHF-preferred register) | consistent (not tested directly) |

## 7. What every user of LLMs can take from this

1. **Your opening matters more than your follow-ups.** Single-LLM loops reach
   their basin in ≤2 steps; follow-up turns can barely steer once the basin
   is entered.
2. **"Keep going" doesn't mean "keep exploring."** Iteration narrows, not
   widens. For variety, prefer independent prompts over long continuations.
3. **The operator choice is structural.** Continue ≠ paraphrase ≠ summarize+negate
   in dynamical terms; pick the operator whose attractor structure matches
   your goal.
4. **The update rule matters.** Accumulating context stabilizes (suppresses
   cycles); replace mode allows short cycles to form. "Don't show the model
   its own history" is a bigger intervention than it looks.
5. **Two-agent dialogs drift toward cooperative-helpful register regardless
   of seed.** Expect philosophy conversations to end in practical advice.
   RLHF training biases both agents toward the same stylistic attractor.
6. **Some operators have algebraic fixed points.** If the operator applied to
   its own output produces the same output, a sufficiently competent LLM will
   detect this and stop evolving. Summarize+negate is such an operator.

## 8. Limitations

1. **Single model.** Everything tested on `gpt-4o-mini`. The Attractor Cycles
   paper claims attractors are "a statistical optimum multiple LLMs gravitate
   toward"; confirming that across gpt-4o, claude-haiku, etc., is a clear
   single-day follow-up.
2. **Single temperature.** T=0.8 throughout. Higher temperatures might expose
   orbits in operators that show fixed points at 0.8.
3. **Short trajectories for dialog.** 20 turns (10 per role) is thin for
   periodicity detection; the 19% of D2 runs with best_period > 1 could reach
   higher fractions with longer runs.
4. **No true H1c experiment yet.** We haven't empirically produced the
   exploratory regime. If it exists for gpt-4o-mini at all, we haven't found
   the operator that triggers it.
5. **Multi-topic sub-basins not decomposed.** Regime IV is characterized but
   not broken down into its constituent sub-basins. A topic-model (LDA) layer
   on dialog transcripts would resolve this.
6. **The basin metric is style-biased for dialog data.** Even at k=16 or k=32,
   RLHF-aligned models generate text in a narrow stylistic band that clusters
   together regardless of topic.

## 9. Recommended next experiments

**Cheap / post-hoc (< $0.50, no regen):**
- Re-analyze D1 at k=16, k=32, k=64 to see if multi-topic sub-basins emerge in
  the cluster-level basin score.
- LDA topic modeling on D1 transcripts — quantify topic drift explicitly.
- Test absorbing-state sensitivity: apply the O3 operator with varying
  temperatures (T ∈ {0.1, 0.5, 1.2}) to find the temperature at which the
  algebraic fixed point breaks.

**Mid-cost (< $2, a few hours):**
- Replicate O1/O2/O3 on gpt-4o, claude-haiku, and o-series reasoning models.
  Tests the cross-model universality claim.
- D4 dialog with identical personas (self-to-self conversation). Does homophily
  produce faster convergence? Smaller basin?
- O1 at T=1.2 and T=0.2 (the scaffolded conditions B and C from reg4.txt).

**Large / methodological:**
- Verbalized-sampling operator (arXiv 2510.01171) as a regime-breaking
  intervention. Does explicit enumeration of alternatives escape the
  contractive basin?
- Real-world dialog corpus replication: instead of synthetic two-LLM dialog,
  score existing customer-service / tutoring transcripts for the same
  attractor metrics. Do human-LLM dialogs also show stylistic attractors?

## 10. Where to find everything

```
llm_attractor_experiment/
├── REPORT1.md                    ← 15/40-step exp_default findings
├── REPORT2.md                    ← operator × loop_mode (O1–O4, O3b)
├── REPORT3.md                    ← THIS FILE
├── REQ1_MAPPING.md               ← req1 → source verification
│
├── src/
│   ├── main.py                   ← single-LLM CLI (cmd_run/embed/analyze/report/compare)
│   ├── core/{context,trajectory,observables,baselines}.py
│   ├── api/{generator,embedder,openai_client,batch_jobs,evals_runner}.py
│   ├── analysis/
│   │   ├── pca,clustering,recurrence,dwell,basin         ← req1 baseline
│   │   ├── basin_entry,late_recurrence,exit_return       ← REPORT1 v2
│   │   ├── bootstrap,robustness,tsne                     ← REPORT1 v2
│   │
│   └── experiments/                                       ← ISOLATED follow-ups
│       ├── operators/                                     ← REPORT2
│       │   ├── context,trajectory,main                    ← loop_mode=append|replace
│       │   ├── periodicity,dispersion,classifier          ← three-axis metrics
│       │   └── analyze_ext                                ← post-hoc analysis CLI
│       └── dialog/                                        ← REPORT3
│           ├── trajectory,main                            ← two-LLM alternating loop
│           └── observables                                ← role-separated
│
├── configs/
│   ├── default.yaml, deterministic.yaml, stochastic.yaml, basin.yaml
│   ├── long.yaml, long_v2_replay.yaml, noclip.yaml
│   ├── long_v2/{A,B,C,D}.yaml                            ← scaffolded; not run
│   ├── operators/{O1,O2,O3,O3b,O4}.yaml                  ← REPORT2 inputs
│   └── dialog/{D1,D1_replay,D2_replace,D3_debate}.yaml   ← REPORT3 inputs
│
├── data/
│   ├── exp_default, exp_long, exp_noclip
│   ├── exp_op_O1, ..., exp_op_O4, exp_op_O3b
│   ├── exp_dialog_D1..D3
│   └── each with: raw/steps.jsonl, embeddings/<obs>/*, metrics/*.csv,
│                  reports/{report.md, report_operators.md, plots/*.png}
│
└── tests/                                                 ← 73 tests, all passing
```

## 11. The table the classifier should produce (ideal)

Given the data we now have, the classifier could be refined to produce a
fifth verdict "absorbing" distinguishing regime III from regime I. Current
output conflates them. Suggested rule: if `dispersion_growth < -0.04` AND
`std(output across late steps) < 0.001` (i.e. byte-identical late outputs),
classify as absorbing instead of contractive.

## 12. References

- arXiv 2502.15208 — Unveiling Attractor Cycles in LLMs: A Dynamical Systems
  View of Successive Paraphrasing (ACL 2025)
- arXiv 2512.10350 — Geometric Dynamics of Agentic Loops (Dec 2025)
- arXiv 2510.01171 — Verbalized Sampling: Mitigating Mode Collapse
- arXiv 2505.18949 — The Price of Format: Diversity Collapse in LLMs
- arXiv 2509.04796 — Knowledge Collapse in LLMs under Recursive Synthetic Training
- Nature 2024 — AI models collapse when trained on recursively generated data

---

**Status:** complete. D3 (debate) finished; result confirms the "no H1c in
gpt-4o-mini" thesis with basin 0.931 (tighter than cooperative dialog).
Adversarial prompting produces *more* focused contraction, not divergence.
