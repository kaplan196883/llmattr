## 7. Limitations

### 7.1 Scope of model coverage

The main experiments in this paper use a single generator,
`gpt-4o-mini`. The qualitative claims — especially the separation
between append, replace, and dialog regimes — may generalize because
they follow from the generator–nudge factorization rather than from
any one model family. Barrier heights, basin geometry, and even the
exact number of identifiable regimes may vary across models with
different decoding behavior, alignment tuning, or tokenizer
structure.

A within-vendor cross-generation replication on `gpt-4.1-nano` was
attempted: 37 experiment configurations were re-run end-to-end
through the same 4-phase pipeline (raw trajectories → embed → analyze
→ report). Audit artefacts are at:

- `COVERAGE_nano.csv` — file-presence matrix per cell.
- `RESULTS_nano.md` — per-cell numeric comparison vs gpt-4o-mini.
- `THESES_nano.md` — six paper-thesis predicates evaluated PASS/FAIL.
- `RESULTS_dual.md` — side-by-side per-cell tables.

**What the audit actually establishes (sober reading).**

The audit's strongest finding is on **the four pub-scale headline
cells** (`O1 continue`, `O2 paraphrase-replace`,
`O3 summarize-negate-replace`, `D1 dialog`): these preserve their
two-axis H1a / H1b verdicts on `gpt-4.1-nano`, with recurrence-rate
shifts in $[-0.040, +0.122]$ and basin-score shifts within $\pm 0.028$.
On the **six pre-registered thesis predicates** (regime ordering,
replace-mode capitulation, O1 drift-floor band, O1 adversarial >
out-of-distribution, D1 dialogue-state susceptibility, pub-scale verdict
labels), the result is **6/6 PASS on both gpt-4o-mini and
gpt-4.1-nano**. We treat these two findings — pub-scale verdicts
preserved + 6/6 predicates PASS — as the audit's load-bearing claim.

**What the audit does *not* establish.** Across the full 37-cell
sweep, only **19/37 cells** match both H1a and H1b verdicts exactly.
The other 18/37 cells do *not* fully agree, broken down as:

- 13/18 are perturbation-experiment reporting artefacts where the
  H1a/H1b classifier was never designed to run on multi-condition
  reports (the classifier expects a single regime-vs-baseline
  comparison; perturbation experiments produce 4 conditions that
  don't fit that schema). These are *known classifier-output
  artefacts*, not evidence of regime-level drift, but the
  cross-model pipeline does not separately validate the four
  perturbation conditions on `gpt-4.1-nano` at the geometric or
  basin-predictability level.
- 2/18 are smaller pub-scale configurations (D1 v1 narrower-scope
  dialog and the T=0.6 temperature-sweep cell) with borderline
  `weak_support` ↔ `not_supported` shifts on the recurrence axis —
  these *are* genuine cell-level disagreements at finite sample
  size, not classifier artefacts.
- 3/18 are pilot-scale (small N) cells with finite-sample borderline
  shifts in the same direction.

Honest interpretation:

1. **Pub-scale verdicts are preserved within-vendor.** The four
   load-bearing pub-scale cells and the six pre-registered
   predicates pass on both models.
2. **Smaller-N cells show genuine numerical drift.** Mean recurrence
   rate is within $\pm 0.05$ for only 12/24 non-perturbation cells;
   mean basin score within $\pm 0.05$ for 17/24. This is consistent
   with finite-sample noise but is not a strong claim of numerical
   invariance — the cross-model audit shows shape preservation, not
   numerical equivalence, and even shape preservation is conditional
   on a specific list of pub-scale cells.
3. **Cross-vendor replication is the missing piece.** Both
   generators are OpenAI; both share tokenizer family, alignment
   pipeline, and likely architecture-class. A genuine cross-vendor
   audit (Claude / Llama / Qwen / Mistral) would be needed before
   any model-agnostic claim can be sustained. We do *not* make such
   a claim.
4. **The geometric visualization toolkit was not re-run.** V
   landscapes, Dijkstra geodesics, 3D animations, and the basin
   predictability classifier are separate scripts that were not
   regenerated for `gpt-4.1-nano`. The audit only validates the core
   4-phase pipeline outputs.

In short: the within-vendor audit is **suggestive evidence** for
generator-class robustness of the headline regimes, not proof of
generality. The reader should treat the 6/6 predicate result as a
necessary-but-not-sufficient check.

### 7.2 Dependence on representation choice

Our results are observed through one embedding family,
`text-embedding-3-small`, together with PCA and t-SNE projections. We
do check robustness across observables and across several projection
spaces, and §5.20 reports an explicit embedding-space invariance
ablation against `text-embedding-3-large` (within-vendor scale-up)
and `all-mpnet-base-v2` (cross-architecture, sentence-transformers).
The attractor-like structure appears robust within the tested
representation models, but absolute geometric barrier estimates derived
from $V(x) = -\log \rho(x)$ should be interpreted as descriptive
measurements internal to a specific embedding pipeline, not as
representation-free constants.

### 7.3 Bounded-memory regime only

All loops are run under a 12,000-character context cap with tail
clipping. This is a natural bounded-memory setting for recursive LLM
loops, but it is still only one memory regime. The append-mode
contractive basin in particular appears sensitive to clipping: a
no-clip pilot suggests that removing clipping deepens the basin and
reduces recurrence. We therefore treat the reported append-mode
barriers as properties of a bounded-memory recurrence, not of append
mode in the abstract.

### 7.4 Language and length constraints

All prompts, seeds, and generated trajectories are English-only, and
each step produces relatively short outputs (~120–160 tokens). We do
not yet know whether the same taxonomy persists under multilingual
settings, code-heavy trajectories, or long-form generation in which
each recursive step adds substantially more text. These regimes could
alter both the geometry of the embedded trajectories and the
effective token-cost of perturbation.

### 7.5 Static prompting

The experiments hold system prompts fixed throughout a trajectory.
This isolates the recursive dynamics cleanly, but it also excludes
an important class of systems in which high-level instructions drift,
refresh, or are rewritten online. A contractive basin under static
prompting may weaken or fragment under prompt drift, and a
replace-mode regime may become more structured if anchored by
repeated meta-instructions. Those possibilities remain open.

### 7.6 Geometric barriers are descriptive

The empirical potential landscape $V(x) = -\log \rho(x)$ is a useful
summary of trajectory density, not a derived physical free energy.
Likewise, the Dijkstra barrier $V^\star$ depends on the
kernel-density estimator, the PCA-2 reduction, and the grid
discretization. For that reason, we interpret the geometric barriers
primarily through their **relative ordering** across conditions and
regimes, not through their absolute magnitudes. The agreement between
geometric and behavioral barriers is therefore evidence of structural
consistency, not proof of an underlying thermodynamic law.

### 7.7 D2 is still exploratory

Among the five reported regimes, D2 is the least mature empirically.
It was tested at much smaller scale than O1–O3 and D1 (25
trajectories at 50 steps; 64% adversarial switching rate with
±10-pct-pt bootstrap CI). The current results strongly suggest that
drill-down dialog induces a distinct form of topic-anchored content
gravity, but publication-scale replication is still needed before D2
should be treated as equally established.

### 7.8 Tokens are operational, not ultimate

Our headline barrier unit is tokens, because token-cost is directly
measurable and practically meaningful. But tokens are only an
operational approximation to a deeper information quantity. As
discussed in §3.1.6, the model-agnostic object is closer to a barrier
in surprisal or nats. Because the current 37-experiment battery does
not store logprobs, we cannot yet report that quantity directly. The
token barriers in this paper should therefore be read as the most
interpretable first-order estimate of a deeper information barrier.

### 7.9 No tool-using coding-agent benchmark

The experiments in this paper do not include file-system state, code edits, compiler / test feedback, tool schemas, or repository-specific correctness criteria. The "agent" loops we measure are recursive language-model loops with a fixed nudge — append, replace, or dialog — operating on text observables and embedding-space clusters. The implications drawn in §6.6 for coding agents (Cursor, Cline, Devin, Claude Code, LangGraph-based loops, in-house agentic coding systems, SWE-Bench-style benchmarks) are therefore architectural extrapolations from recursive-loop dynamics, not measurements of any specific coding agent or coding benchmark. In coding-agent applications, additional engineering observables — patch diffs, files touched, tests run, failing tests remaining, security-policy violations, tool-call sequences — would need to be measured alongside (or instead of) embedding-space trajectory structure. The framework of §3, the protocol of §4, and the three endpoints of §3.1.2 transfer; the headline numerical values do not transfer without re-measurement.

---

## 8. Future work

The natural next step is to turn the present framework from a
single-model demonstration into a comparative science of recursive
LLM dynamics.

### 8.1 Cross-model replication

The first priority is replication across model families. The most
important question is not whether the exact barrier heights transfer
numerically, but whether the **ordering** of append, replace, and
dialog regimes survives across generators with different alignment
and tokenization properties. A replicated ordering would strongly
support the claim that regime structure is a property of the
generator–nudge system rather than of one model alone. The
within-vendor scale-down to `gpt-4.1-nano` is complete (37/37 cells,
pub-scale verdicts preserved; see §7.1); cross-vendor replication on
Claude Haiku and on a non-OpenAI generator is the natural Tier-3
extension.

### 8.2 Barrier height in nats

A second priority is to move from token barriers to information
barriers. Future experiments should capture generation logprobs
(`Config.include_logprobs=True` is already supported by the pipeline)
so that perturbation cost can be reported not only in tokens, but
also in conditional surprisal. That would let us estimate barrier
height in nats directly and test more rigorously the proposed link
(§3.1.6) between behavioral switching thresholds and geometric
quantities such as $V^\star$.

### 8.3 Larger memory and longer outputs

The present experiments study short recursive steps in a
bounded-memory setting. A natural extension is to increase both the
per-step output length and the context budget. Longer recursive
writes may deepen some basins, fragment others, or create new
multi-scale regimes in which short-horizon and long-horizon
stability diverge. This is particularly important for append mode,
where memory capacity is part of the mechanism.

### 8.4 Mixed and hybrid nudges

The current taxonomy studies clean nudge families: append, replace,
and role-structured dialog. Real systems often mix them. Hybrid
operators such as append-then-summarize, paraphrase-then-append, or
periodic memory compression may interpolate between the regimes
found here or create new ones altogether. These are especially
interesting because they turn nudge design into a controllable
engineering space rather than a fixed experimental condition.

> Hybrid memory policies should be evaluated not only by compression quality but by perturbation response. In particular, future work should compare abstractive summaries, extractive summaries, pinned user goals, pinned acceptance tests, pinned safety constraints, and provenance-preserving summaries of untrusted tool output. The key endpoint is whether these mechanisms reduce *persistent escape* under adversarial in-distribution perturbations without merely suppressing benign adaptation. A natural follow-up is a *memory-policy ablation harness* — four memory configurations (full append, rolling window, generated-summary replacement, hybrid pinned + rolling + provenance-preserving) crossed with five perturbation classes (neutral repo content, irrelevant long log, targeted misleading docstring, misleading failing-test explanation, malicious package documentation), measured with patch-family raw / net / persistent endpoints plus tests, files touched, and policy violations. This would turn the paper's strongest architectural claim — memory policy is a behavioral variable — into a directly executable agent-engineering benchmark.

### 8.5 Publication-scale D2 and broader dialog topologies

D2 should be replicated at publication scale (5 families × 30 ICs ×
3 runs × 50 steps) before being fully incorporated into the stable
taxonomy. More broadly, the dialog results suggest that dialog
architecture itself is a rich nudge design space. Drill-down,
debate, role-play, brainstorming, adversarial questioning, and
multi-party deliberation may each induce different balances between
style stability and content gravity. Extending the framework to
those dialog topologies is likely to produce a more complete map of
conversational attractor regimes.

### 8.6 Perturbation as a general evaluation tool

The perturbation protocol developed here is useful beyond
recursive-loop taxonomy. It provides a generic way to measure the
stability of an LLM behavior under controlled contextual kicks. That
makes it a candidate tool for studying persona persistence, jailbreak
resistance, agent redirection, and other in-context robustness
questions. In that broader setting, barrier height would serve not
only as a descriptive statistic, but as a practical robustness
metric.

### 8.7 Safety and alignment basins

One particularly important application is safety training. If
alignment or refusal tuning creates new attractor basins, then
perturbation-barrier methods should be able to detect them. This
suggests a concrete program: compare base and safety-tuned models
under the same recursive nudge families and test whether alignment
changes barrier height, basin count, or the geometry of switching.
That would connect attractor analysis directly to current questions
in alignment and model control.

### 8.8 Coding-agent benchmark adaptation

A direct next step is to adapt the raw / net / persistent-escape endpoint decomposition to coding-agent benchmarks. For SWE-Bench-style tasks, paired controls would estimate patch-family and pass/fail stochastic floors; perturbation runs would inject controlled text into repository files, tool outputs, issue comments, package documentation, or test logs; persistence would measure whether the agent remains on the injected strategy after additional plan-edit-test cycles. This protocol would distinguish ordinary run-to-run patch variance from durable redirection, which today's leaderboards conflate. It would also separate model fragility from scaffold fragility: identical models under different memory policies (full-history append, summarize-and-continue, hybrid pinned + rolling) on identical tasks would yield different perturbation profiles even when their pass rates agree.

### 8.9 Framework-level memory-policy instrumentation

Agent frameworks should expose the context-update rule as a traceable, configurable, and inspectable object: which raw turns are retained, which are summarized, which facts are pinned, which tool outputs are marked untrusted, and which generated summaries replace prior state. A measurement suite could then compare append, replace, rolling-window, and hybrid policies under identical tasks and perturbations, attributing observed robustness differences to the memory policy rather than to the model. The formalism of §3.1 treats nudges as first-class objects; agent-framework instrumentation would make that first-class status operational in production traces and audit logs.

---

## 9. Methods appendix

### 9.1 Exact metric definitions (executable form)
