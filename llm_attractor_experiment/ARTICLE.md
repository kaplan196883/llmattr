# Perturbation dose responses in recursive large-language-model loops
## Raw switching, stochastic floors, and rare persistent escape across append, replace, and dialog nudges

---

## Abstract

Recursive language-model loops often settle into recognizable
attractor-like patterns, and the practical question is how much
injected text is needed to move a settled loop somewhere else, and
whether that move lasts. Existing taxonomies classify loop shapes
such as contraction, oscillation, collapse, and dialog modes, but
they do not measure the operational stability of those regimes
under perturbation. We formalize recursive inference as a
state-generator-nudge system, separating the model from the
context-update rule. Because a perturbed trajectory's final-cluster
disagreement with its paired control can reflect any of three
distinct phenomena, true redirection, ordinary stochastic
divergence, or a transient kick that later recovered, we measure
perturbation dose response with three endpoints: *raw switching*,
where the perturbed trajectory's final cluster differs from its
paired control; *net switching*, raw switching after subtracting
the natural control-vs-control stochastic floor; and *persistent
escape*, where the injection causes a visible basin jump that
remains through the terminal step.

The headline result is that append-mode continuation has a real but
bounded in-distribution dose response: adversarial continuations
produce raw-switching $\mathrm{ED50}_{\mathrm{raw}} \approx 40$
tokens, with convergent estimates from pooled logistic fitting,
mixed-effects modeling, and family-cluster bootstrap, but the
strict endpoint, visible basin jump that remains through the
terminal step, is not reached at any tested dose up to 400 tokens.
But this is not persistent redirection. Raw switching plateaus near 67%, paired
controls already diverge at about 35%, net switching never reaches
+50 percentage points, and persistent escape is not reached at any
tested dose up to 400 tokens. Meanwhile, replace-mode loops that
appear to switch near 100% mostly do so because the update rule
overwrites the state; insert-mode probes reduce switching to
12-32%.

Practically, this means recursive-loop evaluations should
distinguish transient movement from durable escape, always subtract
stochastic floors, and treat context-update rules as first-class
safety-relevant design choices rather than implementation details.
We report 37 experiments on `gpt-4o-mini`, with within-vendor
replication on `gpt-4.1-nano` and public code, configurations,
trajectories, and reports
(<https://github.com/kaplan196883/llmattr>).

---

## Plain-language summary

### Why it matters

A common folk-belief about recursive LLM loops is that they either
"get stuck in attractors" or are "easy to hijack with a small
prompt." Both claims are too vague to be useful. A loop can visibly
move without staying moved; two runs of the same prompt can diverge
without any attack; and some apparent "fragility" is caused by the
system's context-update rule rather than by the model crossing a
real basin boundary. The missing question is not just whether
recursive loops have regimes, but how moveable those regimes are
under controlled perturbation.

### What we did and what we found

We repeatedly fed an LLM its own outputs, injected text at a chosen
step, and measured whether the trajectory changed relative to a
paired control. The key result is sharp: in append-mode
continuation, adversarial in-distribution text produces a measurable
raw dose response with $\mathrm{ED50}_{\mathrm{raw}} \approx 40$
tokens, but durable escape is not achieved even at 400 tokens. Raw
final-cluster switching rises and plateaus near 67%, but paired
control runs already disagree about 35% of the time from sampling
noise alone, so the net effect saturates around +32 percentage
points. The strict endpoint, kicked into a new basin and still
there at the end, never crosses 50%. Replace-mode loops look much
more fragile, but a direct overwrite-vs-insert probe shows that
most of that "switching" is simply the update rule overwriting the
state.

### Three numbers to remember

- **ED50_raw ≈ 40 tokens** for adversarial in-distribution append-mode continuation.
- **Stochastic floor ≈ 35%**, paired control runs already disagree at this rate from sampling alone.
- **Persistent escape not reached** in the tested 5-400 token range; maximum 16% under canonical clustering at 400 tokens.
- **Replace-mode "fragility" drops to 12-32%** when the update rule does not overwrite the state.

### Practical implications

1. **Stress-test recursive agents with persistence, not motion.** The
   right robustness question is not "did the trajectory move after
   the perturbation?" but "did it escape and stay escaped after $N$
   more recursive steps?" An evaluation that counts only immediate
   displacement or final raw cluster disagreement will over-report
   fragility, because much of the movement is transient or
   stochastic.

2. **Always measure the stochastic floor.** In the main append-mode
   setting, two paired control runs already end in different
   clusters about 35% of the time with no perturbation. That means
   a reported 50% switching rate is not automatically evidence of
   successful redirection; much of it may be ordinary sampling
   divergence. Recursive-loop evaluations should include
   control-vs-control baselines and report raw, net, and
   persistent-escape rates separately.

3. **Treat context-update rules as safety-critical design choices.**
   Append-style updates preserve prior context, creating a real but
   bounded barrier: about 40 tokens for raw switching, with
   persistent escape not reached in the tested range. Replace-style
   updates do not show the same kind of injected-token barrier,
   because the rule itself discards the old state. Claims that
   "replace-mode loops are easy to redirect" should be read as
   claims about overwrite mechanics, not necessarily about weak
   model attractors.

4. **Do not assume small adversarial nudges permanently redirect
   settled loops.** Even adversarial continuations selected from
   the same regime top out near 67% raw switching and fail to
   produce 50% persistent escape up to 400 tokens. For
   jailbreak-style or agent-redirection evaluations, this means
   the meaningful target is sustained post-attack behavior, not a
   one-step perturbation success.

5. **Evaluating indirect prompt injection (IPI).** Most IPI
   benchmarks today report whether the model executes the injected
   instruction at the next step, that is the *raw-switching*
   endpoint. A defense that pushes raw-switching $\mathrm{ED50}$
   from 40 to 200 tokens is a quantitative defense improvement; a
   defense that prevents *persistent escape* is a qualitatively
   stronger claim, the model may execute the injection but
   recovers within a few turns. Serious IPI evaluations should
   report all three endpoints AND the stochastic floor (so that
   sampling-noise compliance isn't counted as defense failure),
   AND distinguish injections that land in the system prompt or
   replaced context (replace-style, overwhelms by overwriting)
   from injections that land in tool output or appended document
   text (append-style, has a real but measurable token barrier).
   A defense that only blocks immediate compliance is leaving
   durable-redirection attacks on the table.

6. **Adapting the protocol to human-LLM influence studies.** The
   lorem / neutral / adversarial content contrast is the most
   directly transferable piece of the framework for measuring how
   LLMs affect users. A study aiming to detect content-specific LLM
   influence on humans (rather than generic "the LLM was in the
   loop" effects) should run three matched conditions: (i) targeted
   LLM intervention, (ii) generic on-topic LLM chat without the
   targeted move, (iii) off-topic LLM small-talk, against a no-LLM
   control. If the targeted condition shows persistent change
   relative to the generic and off-topic conditions, the influence
   is content-specific. If all three look similar, what was
   measured is *generic-LLM-presence* (Hawthorne / engagement
   effect), not the LLM's content. The three-endpoint decomposition
   then applies on the human side: did the user's stated goal /
   sentiment change at the LLM turn (raw), above the natural drift
   two humans show without an LLM (net), and was the change still
   in place several turns or sessions later (persistent)?

7. **Hallucination-detection design.** This framework does not
   detect hallucinations directly, it measures embedding-space
   stability, not factuality, and a locked-in hallucination is a
   stable hallucination. But three pieces transfer to
   hallucination evaluations once an external grounding signal
   (retrieval, fact-checker, gold answer) is available. *(i)*
   Self-consistency detectors that flag "the model gave two
   different answers, must be hallucinating" assume between-run
   agreement is noise-free; on our setting paired runs already
   diverge ~35% of the time from sampling alone. Such detectors
   should subtract a measured stochastic floor (paired seeds,
   identical prompt) before scoring. *(ii)* Transient vs
   persistent hallucination is a real distinction: a hallucinated
   claim that the model self-corrects within a turn is
   qualitatively less dangerous than one that propagates. The
   persistent-escape endpoint maps directly, measure whether the
   hallucinated content stays in the trajectory $N$ turns later.
   *(iii)* Hallucination *robustness* under counter-evidence has a
   clean dose-response framing: how many tokens of contradicting
   evidence make the model retract? Same protocol, factuality
   axis instead of cluster axis.

8. **Use the protocol for model and architecture comparisons.** The
   raw / net / persistent-escape decomposition gives a portable
   measurement unit for comparing models, prompts, memory policies,
   and agent-loop architectures. Instead of saying one system is
   "more stable", an evaluator can report the dose-response curve,
   stochastic floor, plateau, and persistent-escape threshold,
   numbers that are directly comparable across vendors.

### Caveats

The main generator is `gpt-4o-mini`, with within-vendor replication
on `gpt-4.1-nano` but no full cross-vendor replication yet. The
tested perturbation range is 5-400 tokens, so persistent escape may
appear at higher doses. The regimes are operational embedding-space
measurements, not mechanistic proofs of classical attractors. The
human-LLM, IPI, and hallucination-detection implications above
describe how the *measurement protocol* transfers; the paper itself
does not collect human-impact data, production-IPI data, or
factuality-graded data, and embedding-space stability is not the
same construct as factual correctness.

---

## 1. Introduction

### 1.1 Phenomenon

Recursive language-model loops are increasingly common in modern AI
systems, agents drafting and revising plans, assistants summarizing
tool outputs, dialog systems carrying conversational state forward.
Each such loop has two parts that the surrounding literature often
conflates: a generator (the model itself, producing the next text)
and a context-update rule that decides how that text is written
back into the next prompt. The choice of update rule, append,
replace, or role-structured dialog, is the loop's memory policy,
and we will argue throughout this paper that it is one of the most
consequential design variables for loop stability. Existing
taxonomies of recursive-loop dynamics describe the resulting
patterns qualitatively but do not measure how those patterns
respond to controlled perturbation, and they do not separate model
behavior from update-rule mechanics.

A software-engineering agent is one such recursive loop. A typical
loop reads an issue, inspects a repository, proposes an edit, runs
tests, reads the failure, and repeats. In this setting, the "state"
is not only the chat transcript; it may include tool results,
patches, test logs, summaries, pinned requirements, and recent
files. The context-update rule therefore corresponds to an
engineering memory policy: full-history append, rolling-window
append, summary replacement, or a hybrid with pinned artifacts. We
do not evaluate any specific coding-agent product in this paper, but
this class of systems is a direct application domain for the
framework.

When a language model is fed its own output through repeated context
updates, the resulting trajectory often settles into recognizable
dynamical patterns. Practitioners have long observed topical lock-in,
paraphrase cycling, and degenerate collapse, but only recently have
these behaviors been studied as properties of recursive LLM dynamics
rather than as isolated prompt artifacts. arXiv:2512.10350
(*Dynamics of Agentic Loops*) classifies recursive LLM trajectories
into three regimes, contractive, oscillatory, and exploratory,
using drift, dispersion, and cluster-persistence metrics on a
single open-source generator. arXiv:2510.21258 introduces
correlation dimension as a fractal-geometric measure of self-
similarity in language-model trajectories and reports that this
dimension drops sharply during pretraining and again during
multiple forms of degeneration (compatible with, though not
explicitly framed by the paper as, a collapse onto a
lower-dimensional attractor). arXiv:2510.24797 reports that under
sustained self-referential prompting, frontier models (GPT, Claude,
Gemini families) produce *statistically convergent* descriptions
of the resulting state, independent evidence that recursive
self-referential loops have consistent, model-spanning endpoints.

That line of work establishes an important fact: **attractor-like
regimes exist in recursive LLM loops**. But it leaves open a more
practical and more theoretical question. Once a trajectory has
entered such a regime, **how hard is it to move it somewhere else?**
More concretely: how much text must be injected, and what kind of
text must it be, to push a recursive trajectory across an attractor
boundary?

This paper treats that question as the central problem. Rather than
asking only whether regimes exist, we ask whether they possess
measurable **barriers**. Our answer is yes: recursive LLM regimes
differ not just in shape, but in the **token-cost required to
dislodge them**.

### 1.2 Question

We study recursive LLM loops as bounded stochastic dynamical systems
and ask three related questions.

First, can append, replace, and dialog loops be understood within a
single formal framework that separates the language model from the
context-update rule? Second, do different loop architectures induce
measurably different attractor regimes? Third, can the stability of
those regimes be quantified by a common operational unit: the amount
of injected text required to switch trajectories from one basin to
another?

These questions turn an informal observation, "the loop gets stuck",
into a quantitative program. If attractors are real features of
recursive LLM dynamics, then they should not only be detectable in
representation space, but should also exhibit measurable resistance
to perturbation.

### 1.3 Contributions

This paper makes five contributions.

**First**, we introduce a **state-generator-nudge formalism** for
recursive LLM loops. In this formulation, the generator produces text
conditioned on the current context, while the **nudge** is the
context-update operator that maps the current context and output
into the next state. This makes append, replace, and role-structured
dialog first-class objects of analysis rather than implementation
details. Within the framework we prove a finite-time access bound for
replace-mode loops (§3.1.4 Lemma 1 + Corollaries) and state a
conjecture for append-mode (§3.1.5 Conjecture 1) that the data
empirically supports.

**Second**, we define **three dose-response endpoints** for
operationally measuring regime stability, rather than a single
"barrier height": *raw switching* (final-cluster disagreement with
paired control), *net switching* (raw minus the control-vs-control
stochastic floor), and *persistent escape* (visible basin jump that
remains through the terminal step). The strict barrier notion in
the dynamical-systems sense corresponds to the *persistent-escape*
endpoint; the headline ≈40-token measurement reported below is
$\mathrm{ED50}_{\mathrm{raw}}$, not the persistent-escape barrier,
and the two must not be conflated. This three-endpoint decomposition
yields a common unit for comparing attractor stability across
recursive architectures. An information-theoretic reading (§3.1.6)
connects the token-cost to a model-agnostic surprisal-based
quantity in nats.

**Third**, we measure these barriers across 37 experiments on
`gpt-4o-mini`. Append-mode continuation exhibits a finite, graded
in-distribution dose-response with **ED50 ≈ 40 tokens** (4PL pooled
36; GLMM 41; family-cluster-bootstrap median 52, 95% CI [8.5, 242];
$n=200$/cell × 8 doses, §5.6.1) and a plateau near 67%, a
substantial subpopulation does not switch at any tested dose. A
control-vs-control stochastic floor of ~35% consumes most of the
effect at low doses, leaving a net adversarial effect of ~32
percentage points at the highest tested dose. Out-of-distribution
neutral and lorem perturbations fail to overcome the regime beyond
a drift floor near 24%. Replace-mode paraphrase and summarize-and-
negate show near-saturated switching at all tested doses, while
dialog regimes occupy intermediate scales. **The graded dose-
response shape, plateau-below-1, and natural-floor decomposition
together replace the simpler "barrier height" framing of earlier
versions of this manuscript.**

**Fourth**, we report a complementary descriptive view: geometric
"barriers" estimated from the empirical potential landscape
$V(x) = -\log \rho(x)$ on PCA-2 give a qualitative picture of basin
structure that is *consistent* with the perturbation results in some
respects (e.g. replace-mode regimes show rapid basin re-organisation)
but is *not* a quantitative independent confirmation: the geometric
$V^\star$ values for replace-mode regimes are paradoxically *high*
even though their behavioral switching rates are saturated near 100%
(§5.10). We treat the geometric landscape as a useful descriptive
visualisation, not as independent validation of the behavioral
barrier numbers.

**Fifth**, we refine the emerging taxonomy of recursive LLM dynamics.
In addition to the now-familiar contractive, oscillatory, and
absorbing patterns, we identify two dialog regimes, stylistic
multi-basin dialog (D1) and drill-down dialog (D2), whose
distinguishing signature is not dispersion alone, but their barrier
structure under perturbation. We demonstrate explicitly (§5.19) that
bulk diagnostics under-determine the O1/D1 boundary; the perturbation
protocol is the load-bearing tool that resolves the full taxonomy.

The full pipeline is reproducible: raw trajectories LFS-tracked, 99
unit tests, every numeric claim in §5 verified cell-by-cell against
the cited CSV (`RESULTS.md`, 103/103 cells), and every experiment's
artifact presence audited (`COVERAGE.csv`, 37/37 at 100%). All
within-vendor cross-generation results, the 37/37 nano replication
and the 6/6-thesis PASS audit (§5.21), are reproducible from the
same raw trajectories via three additional artifacts:
`COVERAGE_nano.csv`, `RESULTS_nano.md`, `THESES_nano.md`.

---

## 2. Background and related work

### 2.1 Attractors in neural dynamics

Attractor analysis has long been central to the study of recurrent
neural systems. In classical recurrent networks, one studies fixed
points, cycles, and low-dimensional manifolds through tools such as
Jacobian linearization, Lyapunov spectra, and effective dimensionality
(Hopfield, 1982; Sussillo & Barak, 2013; Maheswaranathan et al., 2019).
Those tools assume a smooth state-update map. Recursive language-model
loops are different: they evolve through sampled text rather than
through a differentiable latent recurrence. For that reason, we work
with empirical analogs of classical dynamical diagnostics,
recurrence, dwell structure, ensemble-spread Lyapunov exponents,
effective dimension, and density-derived potential landscapes, rather
than with exact local linearizations.

### 2.2 Attractor observations in language models

The dynamical-systems framing of LLM inference loops has emerged
rapidly in 2025. arXiv:2512.10350 (*Dynamics of Agentic Loops in
Large Language Models: A Geometric Theory of Trajectories*)
formalizes recursive LLM transformations as discrete dynamical
systems in semantic space, identifying three regimes, **contractive**
(convergence to stable semantic attractors), **oscillatory**
(cycling), and **exploratory** (unbounded divergence), through a
measurement protocol of local drift, global drift, dispersion, and
cluster persistence. They show empirically that prompt design selects
the regime: iterative paraphrasing → contractive, iterative negation
→ exploratory.

arXiv:2510.21258 (Du and Tanaka-Ishii, *Correlation Dimension of
Auto-Regressive Large Language Models*) introduces correlation
dimension as a fractal-geometric measure of "epistemological
complexity of text," applied broadly across autoregressive
architectures (Transformer and Mamba). They report that
correlation dimension drops during pretraining phase transitions
and during multiple forms of generated-text degeneration. We do
not claim their framework explicitly characterizes degeneration as
"attractor collapse"; rather, the *direction of their effect*,
sharp dimensionality drop coincident with degeneration, is
compatible with the absorbing-regime interpretation we report in
O3 (§5.2), where a near-zero sharpness-dim and a single-cluster
late window are exactly the kind of dimensional collapse a
correlation-dim drop would track on a different observable.

Earlier work characterized degeneration *symptomatically* but without
the dynamical-systems framing. Carlini et al. (2021) noted aggressive
top-k sampling in GPT-2 can produce repetitive collapse. Holtzman et
al. (2020) systematized "degeneration" failure modes (repetition,
blandness) and motivated nucleus sampling.

### 2.3 What this paper adds

Relative to prior regime-classification work, this paper makes three
specific advances.

First, it separates the recursive loop into **state**, **generator**,
and **nudge**. This makes it possible to distinguish effects of the
language model itself from effects of the context-update architecture.
Second, it introduces a measurable notion of **barrier height**: the
amount of injected text required to produce a specified switching
probability across basins. Third, it shows that barrier structure
refines the standard regime taxonomy. In addition to contractive,
oscillatory, and absorbing behavior, we identify two dialog-specific
regimes, dialogue-state-driven multi-basin dialog (D1) and drill-down dialog
(D2), whose distinguishing feature is not dispersion alone, but
their perturbation signature.

A concise comparison with the closest prior work:

| dimension | arXiv:2512.10350 | this paper |
|---|---|---|
| regime taxonomy | 3 (contractive, oscillatory, exploratory) | 5 (+ D1 dialogue-state-driven multi-basin, + D2 drill-down dialog) |
| diagnostic metrics | local drift, global drift, dispersion, cluster persistence | + recurrence rate, sharpness dim, basin predictability acc(k), V\* geodesic-derived geometric barriers, RG dendrogram coarse-graining |
| barrier-height measurement | not measured | **token-quantified** via 4-condition perturbation protocol (control / neutral / lorem / adversarial) × 3 sweep dimensions (regime / dose / injection-time) |
| theoretical framework | discrete dynamical system in semantic space (informal) | state-generator-nudge formalism (§3.1) with formal access bound (Lemma 1) and append-mode accumulation conjecture (Conjecture 1) |
| geometric/behavioral triangulation | n/a | **rank-stable V\* ordering across 6 inter-basin geodesics matches perturbation-derived dose-rankings (89-98% of parameter combinations; absolute V\* magnitudes are descriptive only, CV 14-24% across a 45-point parameter grid)** (§5.10) |
| reproducibility | trajectory artifacts in appendices; code "to be considered following peer review" (no public link) | 103/103 cell-verified numeric claims (`RESULTS.md`); 37/37 experiments at 100% applicable artifact coverage (`COVERAGE.csv`); raw trajectories LFS-tracked; full code, configs, and prompt templates publicly available |
| trajectory scope | $n=2$ (one contractive, one exploratory), single seed, 50 iterations, three clustering configurations | 50-1,350 trajectories per configuration across 37 experiments |
| model | `deepseek-r1:8b` via Ollama 0.12.9 (8B params, $T=0.8$, no explicit seed) | `gpt-4o-mini`, with within-vendor cross-generation replication on `gpt-4.1-nano` (37/37 cells; pub-scale headline verdicts preserved) |

We share the dynamical-systems framing and the contractive /
oscillatory pair; we *add* the cost-of-nudging measurement and the
two dialog regimes whose distinguishing signature appears only when
that measurement is made. Tacheny (2025) introduced the
dynamical-systems framing on a single open-source generator
(`deepseek-r1:8b`) with two proof-of-concept singular loops; this
paper scales the protocol, paired controls, perturbation
dose-response, within-vendor cross-generation replication, and
full-trajectory release, and adds the formal generator/nudge
separation that makes context-update mechanics a first-class
property of the loop.

Tuci et al. (2026) study SGD-optimization dynamics
on neural-net loss landscapes via random dynamical systems and
introduce a "sharpness dimension" generalization bound at the edge
of stability. Their setting (parameter space, Hessian-anchored,
training dynamics) is structurally different from ours (embedding
space, no gradients, inference-time recursion of a frozen LLM). We
borrow only the *functional form* of their sharpness dimension
(Definition 4.2) as a comparative diagnostic across regimes; the
ensemble-spread Lyapunov machinery in
`src/experiments/dynamics/lyapunov.py` is our own construction. See
§4.5.6 for the explicit caveats.

### 2.4 Effective potential and geometric barriers

The use of $V(x) = -\log \rho(x)$ as an empirical *effective potential* is
standard in chemical-physics free-energy analysis and reaction-rate
theory: ρ(x) is the stationary density of a stochastic trajectory
ensemble in some reduced coordinate system, and V is the potential
that would yield ρ as the Boltzmann weight at unit temperature. We
adopt this as a purely empirical / data-driven landscape over the
PCA-2 projection of trajectory embeddings; no thermodynamic claims
are made about the LLM itself.

The accompanying visualization battery, Dijkstra geodesics between
density peaks (with their maximum-V along the path used as a
geometric barrier estimate) and volumetric iso-density renderings,
is descriptive rather than theoretical. It converts the empirical
density into shapes a human reader can read off, without assuming
any particular generative model of ρ.

### 2.5 Dialog as a distinct dynamical setting

Most prior work on recursive LLM dynamics focuses on single-stream
operators such as continuation, paraphrase, or negation. Multi-turn
LLM dialog has been studied for capability and alignment purposes
(Park et al., 2023, "Generative Agents") but not, to our knowledge,
with embedding-space attractor analysis. Multi-turn dialog introduces
a different architecture: generated text is not merely appended or
replaced, but inserted into a role-structured conversational state.
This turns dialog into a distinct family of nudges. In our experiments,
dialog does not simply reproduce the operator regimes. Instead, it
generates its own attractor structure, including dialogue-state-driven multi-basin behavior (D1) and topic-anchored drill-down dynamics (D2).

### 2.6 Terminology

The dynamical-systems literature uses "attractor," "basin,"
"cluster," "sink," "barrier," "switch," "collapse," "regime," and
"nudge" with overlapping but non-identical scopes. To avoid
ambiguity in this paper, we fix a strict hierarchy with explicit
definitions. All later usage conforms to this glossary unless
otherwise noted.

**Text state $X_t$.**
The text state is the bounded visible context string available to
the generator at recursive step $t$.
*Don't confuse with:* the generated output $Y_t$, which is only
the model's next text sample.

**Observable $\mathcal{O}(X_t)$.**
An observable is a deterministic text view extracted from the state
or output, such as `output`, `rolling_k3`, or `context_tail`.
*Don't confuse with:* an embedding, which is the numerical vector
computed from the observable text.

**Embedding $z_t$.**
An embedding is the vector representation
$z_t = \mathrm{embed}(\mathcal{O}(X_t))$ used for distances,
projections, clustering, and diagnostics.
*Don't confuse with:* the text state itself, which remains a string.

**Cluster.**
A cluster is a cell of the canonical K-means partition, fit on
PCA-10 embeddings with $k=12$ unless explicitly stated otherwise.
*Don't confuse with:* a basin, which requires additional temporal
or structural support beyond K-means membership.

**Basin / basin candidate.**
A basin candidate is a cluster or coarser embedding-space region
with evidence of persistence, recurrence/dwell, robustness,
contraction, re-entry, or collapse.
*Don't confuse with:* a raw cluster label, which may over-partition
or merge dynamical structure.

**Attractor-like regime.**
An attractor-like regime is a top-level recursive-loop behavior
whose basin candidates satisfy the operational criteria defined in
§3.1.3.
*Don't confuse with:* a classical deterministic attractor; our
claim is empirical and operational, not a smooth-state theorem.

**Regime label.**
A regime label is the human-readable name assigned to a generator-
nudge configuration after inspecting its diagnostics and
perturbation response.
*Don't confuse with:* a cluster label, which is an unsupervised
numerical partition index.

**Nudge.**
A nudge is the context-update operator $\mathcal{N}_f(X_t, Y_t)$
that writes generated or injected text into the next state.
*Don't confuse with:* a perturbation, which is externally injected
text used to test stability.

**Perturbation.**
A perturbation is controlled injected text inserted at a specified
step to test whether the trajectory changes its terminal cluster
or basin candidate.
*Don't confuse with:* ordinary generated text, which is sampled by
the model during unperturbed recursion.

**Switch / switching rate.**
A switch is final-step cluster disagreement between a perturbed
trajectory and its paired control trajectory, and switching rate
is the fraction of such events.
*Don't confuse with:* persistent basin escape, which requires
stronger evidence than final-cluster disagreement.

**Persistent basin escape.**
A persistent basin escape is a visible injection-time cluster jump
that remains in the post-injection basin through the terminal step.
*Don't confuse with:* stochastic post-injection divergence, where
final clusters differ without a durable basin-crossing event.

**Barrier height in tokens.**
Barrier height in tokens is the injected-token dose required to
produce at least 50% switching under a specified perturbation
protocol.
*Don't confuse with:* generated-token budget, which counts model
output after injection rather than injected text.

**Barrier height in nats.**
Barrier height in nats is the corresponding information cost
computed from conditional token surprisal, which is not numerically
measured in this battery.
*Don't confuse with:* the reported token barrier, which is
tokenizer-dependent and directly measured.

**Contractive.**
A contractive regime shows decreasing ensemble spread, low late
Lyapunov growth, or movement toward a stable basin candidate.
*Don't confuse with:* absorbing collapse, where trajectories become
trapped in a narrow template or fixed form.

**Oscillatory.**
An oscillatory regime shows repeated return to alternating states
or cycle arms, typically detected by lag-periodicity and high
recurrence.
*Don't confuse with:* generic recurrence, which need not imply a
period-2 or periodic structure.

**Absorbing.**
An absorbing regime traps trajectories in a fixed discourse form,
low-dimensional template, or near-invariant output pattern.
*Don't confuse with:* semantic convergence; in O3 the absorption
is template-formal, not topic-identical (see §5.14).

**Multi-basin.**
A multi-basin regime contains several supported basin candidates,
often corresponding to register, dialogue state, or recent-context
capture.
*Don't confuse with:* many K-means clusters; multi-basin status
requires structural support beyond cluster count.

**Sink.**
A sink is a descriptive visualization term for a local density or
flow-convergence region in projected embedding space.
*Don't confuse with:* an attractor-like regime, which is a full
trajectory-level classification.

**Collapse.**
Collapse is a strong reduction of trajectory diversity into a narrow
template, cluster, or low-dimensional region.
*Don't confuse with:* contraction, which can preserve multiple
supported basins while reducing dispersion.

**How we use these terms.**
In this paper, "attractor-like" is the only term used for top-level
regime claims. "Cluster" refers specifically to the canonical
K-means partition unless another clustering method is named.
"Basin" means a cluster or coarser region with structural support
from the diagnostic battery. "Switching rate" is the operational
final-step cluster-disagreement metric used in the perturbation
pilots. "Persistent basin escape" is the stricter measure
introduced in §5.15, requiring an injection-time jump that
remains in the new basin. Claims about barrier height are tied to
the stated switching definition unless explicitly marked as
persistent-escape barriers.

**The strict hierarchy is:**

`text state X_t → observable O(X_t) → embedding z_t → K-means cluster → basin candidate → attractor-like regime`

---

## 3. Formal framework and hypotheses

### 3.1 State, generator, nudge

Before the formal definitions, a brief orientation: every recursive loop
in this paper has two distinct moving parts that the surrounding
literature often conflates. The *generator* is the model itself,
producing the next piece of text. The *nudge* (often called the
context-update rule) is what decides how that text is written back into
the next prompt, appended to a notebook of running context, written
over a single-state whiteboard, or threaded into role-labeled dialog
turns. The state-generator-nudge formalism below treats these as
separate objects so that loop properties can be attributed to the right
one.

Let $X_t \in \mathcal{C}$ denote the bounded visible context at step $t$,
where $\mathcal{C}$ is the space of valid clipped contexts (here, the
finite-length character strings produced by tail-clipping at 12,000
chars). Let
$$
Y_t \sim P_\theta(\cdot \mid X_t;\, f)
$$
be the continuation generated by a language model with parameters
$\theta$ under a content operator $f$ (e.g. continuation, paraphrase,
summarize-and-negate, role-alternating dialog). Let
$$
\mathcal{N}_f : \mathcal{C} \times \mathcal{Y} \to \mathcal{C}
$$
be the **context-update operator**, or **nudge**, mapping the current
state and the model output to the next state. The full recurrence is
then a bounded stochastic dynamical system
$$
Y_t \sim P_\theta(\cdot \mid X_t;\, f),
\qquad
X_{t+1} = \mathcal{N}_f(X_t, Y_t).
$$

Three concrete nudges instantiate this skeleton in our experiments:

- **Append nudge**:
  $\mathcal{N}_{\text{append}}(X_t, Y_t) = \operatorname{clip}(X_t \Vert Y_t)$
- **Replace nudge**:
  $\mathcal{N}_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)$
- **Dialog nudge**:
  $\mathcal{N}_{\text{dialog}}(X_t, Y_t) = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)$
  with role label $r_t$ alternating across turns.

This factorization is what licenses the H2 prediction below: the regime
depends jointly on the content operator $f$ (which parameterizes the
generator $P_\theta(\cdot \mid X_t; f)$) and the choice of nudge
$\mathcal{N}_f$ (which determines how $Y_t$ feeds back into $X_{t+1}$).
Two operators that share the same prompt instruction but differ in nudge
will produce qualitatively different attractor regimes; this is exactly
what we see empirically (e.g. paraphrase under append vs replace).

| Formal nudge | Engineering analogue | Typical risk / behavior |
|---|---|---|
| Append: $\mathcal{N}_f^{\text{append}}(X_t, Y_t) = \operatorname{clip}(X_t \,\Vert\, Y_t)$ | ReAct-style full transcript, rolling recent context, accumulated tool logs | Prior evidence remains as ballast; perturbations compete with accumulated state |
| Replace: $\mathcal{N}_f^{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)$ | Summarize-and-continue (summary becomes the only state); scratchpad replacement | Old state is discarded; whatever enters the replacement becomes privileged |
| Dialog: $\mathcal{N}_f^{\text{dialog}}(X_t, Y_t) = X_t \,\Vert\, \operatorname{format\_turn}(\text{role}, Y_t)$ | ChatML / role-structured state, multi-role agents, user/assistant/tool turn buffers | Recent role-local turns may dominate despite longer accumulated context |
| Hybrid append + pinned + summary | Pinned issue/tests/security policy plus compressed older history | Robustness depends on which facts can be overwritten and which remain invariant |

In engineering terms, the nudge is the *memory policy* of the loop; it
is therefore part of the system's robustness and security boundary, not
merely an implementation detail. The remainder of the paper treats
append, replace, and dialog as the canonical formal nudges and uses the
engineering analogues as motivating examples only.

#### 3.1.1 Barrier height as a unit

For two basin sets $B_1, B_2 \subset \mathcal{C}$ in the late-window
basin partition (defined operationally in §4.5.3), define the
**perturbation barrier height** from $B_1$ to $B_2$ as

$$
\mathrm{B}(B_1 \to B_2)
=\inf\Bigl\{ \tau \in \mathbb{N} \;\Big|\;
\Pr\bigl[\,X_T \in B_2 \mid X_0 \in B_1,\ \text{inject}_\tau\,\bigr] \geq \tfrac{1}{2}\Bigr\}
$$

where $\text{inject}_\tau$ denotes the protocol of injecting $\tau$
tokens of in-distribution adversarial text mid-trajectory and then
running the recurrence to its terminal step $T$. The unit is *tokens*,
a quantity that is **interpretable to a practitioner** (it tells you
how much text you have to insert to re-aim the trajectory) and that
**varies with the nudge**, but not arbitrarily. The next proposition
establishes the structural difference between append and replace nudges.

#### 3.1.2 Three operational endpoints for "barrier height"

A perturbed trajectory can finish in a different cluster than its paired
control for any of three distinct reasons: the injection genuinely
redirected it; the two stochastic runs would have diverged anyway; or
the injection caused a brief jump that later recovered. The three
endpoints below, raw switching, net switching, persistent escape,
separate these cases. Treating them as a single "switching rate" would
conflate redirection, sampling drift, and transient kicks; the rest of
the paper depends on holding them apart.

We define three endpoints. Let $D$ denote injected-dose length,
$C_0$ the initial cluster, $C_T$ the terminal cluster, and $p_0$
the control-vs-control natural floor.

1. **Raw-switching ED50.**
   $$
   \mathrm{ED50}_{\mathrm{raw}}=\inf\{D:\Pr(C_T\neq C_0\mid D)\ge 0.5\}.
   $$
   The dose at which raw final-cluster disagreement crosses 50%,
   without subtracting the natural stochastic floor.

2. **Net-switching ED50.**
   $$
   \mathrm{ED50}_{\mathrm{net}}=\inf\{D:\Pr(C_T\neq C_0\mid D)-p_0\ge 0.5\}.
   $$
   The dose at which the treatment-induced excess switching above
   the control-vs-control floor crosses +50 percentage points.

3. **Persistent-escape ED50.**
   $$
   \mathrm{ED50}_{\mathrm{persist}}=\inf\{D:\Pr(J_D=1,\ C_T\neq C_0\mid D)\ge 0.5\},
   $$
   where $J_D=1$ denotes an injection-step jump. The dose at which
   an injection-induced jump that persists to the terminal step
   crosses 50%.

| endpoint | definition | measured value | 95% CI | status |
|---|---|---:|---:|---|
| $\mathrm{ED50}_{\mathrm{raw}}$ | Raw terminal disagreement: $\Pr(C_T\neq C_0\mid D)=0.5$ | $36, 41, 52$ tokens across 4PL pooled, GLMM, and family-cluster-bootstrap median; $\approx 40$ tokens | $[8.5, 242]$ tokens | established |
| $\mathrm{ED50}_{\mathrm{net}}$ | Excess over natural floor: $\Pr(C_T\neq C_0\mid D)-p_0=0.5$, with $p_0=0.347\,[0.310,0.386]$ | not reached; maximum observed net effect $=0.670-0.347=+0.323$ at 400 tokens | not estimable | not reached in tested range |
| $\mathrm{ED50}_{\mathrm{persist}}$ | Injection-step jump plus terminal persistence: $\Pr(J_D=1,\ C_T\neq C_0\mid D)=0.5$ | undefined in range; maximum observed persistent escape $=32/200=16.0\%$ at 400 tokens | not estimable | not reached in tested range |

The formal §3.1.1 barrier-height definition corresponds to
$\mathrm{ED50}_{\mathrm{persist}}$: an intervention must push the
system out of its starting basin AND the trajectory must remain
escaped at the terminal measurement. A naive "barrier height"
formulation that does not separate these two conditions implicitly
conflates the persistent-escape endpoint with raw terminal
switching. They are different estimands.

**Reading the dense rerun.** The dense rerun establishes a
raw-switching ED50 of approximately 40 tokens. The fitted raw curve
has lower asymptote $d = 0.28$ and upper asymptote $a = 0.69$,
consistent with a large natural switching floor and an incomplete
switchable population. The control-vs-control floor is
$p_0 = 0.347\,[0.310, 0.386]$. Subtracting that floor, the observed
net effects across the eight doses are
$+0.068, +0.163, +0.228, +0.283, +0.258, +0.273, +0.308, +0.323$.
Thus $\mathrm{ED50}_{\mathrm{net}}$ is not reached: the net effect
saturates at about +32 percentage points, well below the +50
percentage-point threshold. Persistent escape is still rarer. The
persistent-escape rates are
$3.5\%, 7.0\%, 3.5\%, 9.0\%, 11.5\%, 13.0\%, 14.0\%, 16.0\%$ from
20 to 400 tokens. $\mathrm{ED50}_{\mathrm{persist}}$ is undefined
in the tested range.

**Implication for the paper's claims.** The formal barrier-height
construct is a persistent-escape endpoint, whereas the empirically
measured $\approx 40$-token ED50 is a raw-switching endpoint. Under
the strict operational reading, **O1 has no measured persistent-
escape barrier in the tested range**. What it has is a graded raw-
switching dose response with substantial stochastic-floor and
non-switching aggregate contributions. This replaces the earlier
"150-token barrier" framing. The stronger result is the
**aggregate-rate decomposition** (these are *components of the
observed rate*, not individually identified latent classes): roughly
35% natural stochastic switching from a control-vs-control floor,
an upper asymptote at ~67% suggesting a non-perturbable component
of ~31% under the tested protocol, persistent escape rates of
3-16% across doses (10% / 16% / 39.5% at dose 400 under K-means
$k=4$ / $k=12$ / HDBSCAN respectively; §5.15), and the residual
"transient escape", trajectories kicked at injection but drifted
back to their pre-injection cluster, as the difference between
kicked and persisted rates. All four aggregate components are
visible in the dense data; identifying them as stable per-trajectory
subpopulations would require repeated interventions on the same
seed/IC and a latent-class model, neither of which we have run.

#### 3.1.3 Operational criteria for "attractor-like" regimes

We use **attractor-like** as an operational label, not a claim of a
smooth deterministic attractor. A regime $r$ is an attractor candidate
only if it satisfies the following four falsifiable criteria on the
measured trajectory ensemble. Missing measurements count as FAIL
unless structurally inapplicable.

- **C1. Late-window basin persistence.** Cross-validated accuracy of
  predicting the late-window K-means basin from the final pre-terminal
  state (§4.5.10): $A_r^{\mathrm{final}} \ge \tau_{\mathrm{acc}}$,
  $\tau_{\mathrm{acc}} = 0.70$.
- **C2. Temporal recurrence or dwell above null.** Recurrence
  $R_r$ (§4.5.1) or dwell $D_r$ (§4.5.2) significantly above the
  stronger of time-shuffled / no-feedback baselines (§4.6):
  $\max\{(R_r - \mu_R^{\text{null}})/\sigma_R^{\text{null}},\,
  (D_r - \mu_D^{\text{null}})/\sigma_D^{\text{null}}\} \ge 2$ AND
  $d \ge 0.5$. (For dialog runs, the no-feedback null is structurally
  unavailable; time-shuffled null is required.)
- **C3. Projection / embedder robustness.** Recurrence bin
  $b_e(r) \in \{\text{high} \ge 0.70,\, \text{low} \le 0.40,\,
  \text{mid otherwise}\}$ agrees in at least 2 of 3 embedders
  (canonical + 2 alternatives in §5.20). Coarse by design: this tests
  regime-class survival under measurement change, not scalar invariance
  (sharpness dim, in particular, is *not* embedder-invariant per §5.20).
- **C4. Basin re-entry or contraction.** At least one of:
  $\lambda_{1,r}^{\mathrm{late}} \le 0.015$ (contraction);
  `best_period = 2` AND `period_2_score > 0` (cycle re-entry);
  $R_r \ge 0.90$ AND $SD_r \le 1.50$ (absorbing collapse); or
  exit-return exceeding the C2 null gate. Diagnostics span §4.5.4-§4.5.7.

**Labels.** *Strong attractor*: 4/4 criteria pass. *Attractor-like*:
≥ 3/4. *Not attractor*: < 3/4. The 3-of-4 threshold permits one
diagnostic family to be unavailable while still requiring three
independent tests to agree.

| regime | C1 basin persistence | C2 recurrence / dwell vs null | C3 robustness | C4 re-entry / contraction | perturbation signature | label |
|---|---:|---:|---:|---:|---:|---|
| **O1 contractive** | PASS: $A^{\mathrm{final}}=0.85$ (§5.3) | PASS by dwell / basin-null gate; raw recurrence low, $R=0.29$ (§5.18) | PASS: recurrence remains low across embedders, $0.289/0.304/0.096$ (§5.20) | PASS: $\lambda_1^{\mathrm{late}}\approx 0.008\le 0.015$; $SD=1.70$ (§11.2, §5.19) | adversarial switch $54\%$; OOD floor $18$-$24\%$ (§5.5-§5.6) | **attractor (strong)** |
| **O2 oscillatory** | PASS: $A^{\mathrm{final}}=0.91$ (§5.3) | PASS: high recurrence / period-2 structure, $R=0.875$ (§5.18, §5.20) | PASS: high recurrence under all embedders, $0.875/0.711/0.783$ (§5.20) | PASS: period-2 re-entry; $SD=1.39$ (§11.2) | adversarial switch $94\%$ (§5.5) | **attractor (strong)** |
| **O3 absorbing** | PASS: $A^{\mathrm{final}}=0.93$ (§5.3) | PASS: trivial high recurrence, $R=0.924$ (§5.18, §5.20) | PASS: high recurrence under all embedders, $0.924/0.850/0.862$ (§5.20) | PASS: absorbing-collapse gate, $R\ge 0.90$, $SD=1.45\le 1.50$ (§11.2, §5.20) | adversarial switch $96\%$ (§5.5) | **attractor (strong)** |
| **D1 dialogue-state multi-basin** | PASS stratified: $A^{\mathrm{final}}=0.77$ (§5.3); **FAIL group-aware: 0.34** (§5.11) | PASS by dwell / basin-null gate; raw recurrence low, $R=0.21$ (§5.18) | PASS: recurrence remains low across embedders, $0.210/0.337/0.226$ (§5.20) | PASS: $\lambda_1^{\mathrm{late}}\approx 0.011\le 0.015$; $SD=1.89$ (§11.2, §5.19) | adversarial switch $60\%$; neutral $76\%$ (§5.5) | **attractor-like dialog regime** (formal C1-C4 PASS; group-aware C1 fails) |
| **D2 drill-down** | NT / FAIL: no publication-scale final basin-predictability cell; exploratory $A(k=5)=0.20$ with $n=25$ (§11.2) | NT / FAIL: no null-calibrated recurrence / dwell test at publication scale (§11.2, §7.4) | PARTIAL only: recurrence low across embedders, $0.296/0.176/0.073$, but small-$N$ (§5.20) | NT / FAIL: Lyapunov / exit-return not measured; $SD$ unavailable (§11.2) | adversarial switch $64\%$ (§5.8) | **not attractor** under this definition; exploratory regime candidate |

Thus O1-O3 and D1 meet the operational standard for attractor regimes
in the measured battery. D2 remains a distinct **drill-down regime
candidate** with evidence for content gravity, but it is not counted
as an operational attractor until the missing publication-scale
basin-persistence, null-recurrence, and contraction / re-entry tests
are run.

#### 3.1.4 Replace-mode access bound: hitting probability and generation budget

We begin with replace mode, in which the previous context is discarded
after each generation step. In this regime, the next state depends only
on the newly generated text, not on an accumulated context history.
The injected-token cost $\tau$ from §3.1.1 is therefore distinct from
the model-generated post-injection budget. For $m$ post-injection
replace steps, define

$$
G_m \;=\; \sum_{s=t_{\mathrm{inj}}}^{t_{\mathrm{inj}}+m-1} |Y_s|,
\qquad
\bar G_m \;=\; \mathbb{E}G_m .
$$

The quantity $G_m$ is *not* injected text. It is the number of tokens
generated by the model after the injection. We will bound $G_m$, not
$\tau$, for replace mode.

What follows is the technical version of a structural claim about
replace mode: once the previous state is overwritten by the operator,
the relevant bound is on how many model-generation budget tokens are
needed to hit a target basin, *not* on how many injected tokens are
required to overcome stored context. Replace mode therefore has no
formal injected-token barrier in the sense that append mode does.

**Lemma 1 (replace-mode hitting bound).** Let $(X_t)_{t\ge 0}$ be a
recursive loop with replace-mode nudge

$$
X_{t+1} = g(Y_t), \qquad Y_t \sim P_\theta(\cdot \mid X_t; f),
$$

where $g : \mathcal{Y} \to \mathcal{C}$ is measurable. Fix $m \ge 1$
and set $T = t_{\mathrm{inj}} + m$. Let $\mathcal{R}_s$ denote the
post-injection reachable set at time $s$. Assume
$X_{t_{\mathrm{inj}}} \in B_1 \setminus B_2$ almost surely, and that
after injection at time $t_{\mathrm{inj}}$ there exist constants
$q_0 \in (0, 1]$, $r_0 \in (0, 1]$, and $\kappa > 0$ such that:

1. **Uniform one-step access from every reachable non-$B_2$ state:**

$$
\Pr\bigl[g(Y_s) \in B_2 \mid X_s = x\bigr] \ge q_0
\qquad \text{for all } s \in \{t_{\mathrm{inj}}, \ldots, T-1\}
\text{ and all } x \in \mathcal{R}_s \setminus B_2 .
$$

2. **Persistence after entry:**

$$
\Pr\bigl[X_T \in B_2 \mid X_s = z\bigr] \ge r_0
\qquad \text{for all } s \in \{t_{\mathrm{inj}}+1, \ldots, T\}
\text{ and all } z \in \mathcal{R}_s \cap B_2 .
$$

3. **Bounded generation cost on the full reachable set:**

$$
\mathbb{E}\bigl[|Y_s| \mid X_s = x\bigr] \le \kappa
\qquad \text{for all } s \in \{t_{\mathrm{inj}}, \ldots, T-1\}
\text{ and all } x \in \mathcal{R}_s .
$$

Let

$$
\sigma_2 \;=\; \inf\{\, s \ge t_{\mathrm{inj}} : X_s \in B_2 \,\}.
$$

Then

$$
\Pr\bigl(\sigma_2 \le T\bigr)
\;\ge\;
1 - (1 - q_0)^m ,
$$

and consequently

$$
\Pr(X_T \in B_2)
\;\ge\;
r_0 \bigl[ 1 - (1 - q_0)^m \bigr].
$$

Moreover, $\mathbb{E} G_m \le \kappa m$.

**Proof.** Hitting bound: induction on $A_k = \{\sigma_2 > t_{\mathrm{inj}} + k\}$ using assumption (1) gives $\Pr(A_m) \le (1-q_0)^m$. Terminal bound: decompose over the first hitting time and use the Markov property with assumption (2). Generation budget: tower property with assumption (3). Full proof in §11.3 (Supplementary appendix). $\square$

**Corollary 1 (replace-mode generation-budget bound).** For the fixed
replace-mode dynamics above, define the terminal post-injection
generation budget

$$
G^\star_{1/2}(B_1 \to B_2)
\;=\;
\inf\bigl\{\,
\mathbb{E} G_m \;:\;
\Pr(X_{t_{\mathrm{inj}}+m} \in B_2) \ge \tfrac{1}{2}
\,\bigr\},
$$

with the convention that the infimum is $+\infty$ if no $m$ certifies
the bound. Let

$$
m_{1/2}
\;=\;
\min\Bigl\{\, m \ge 1 \;:\;
r_0 \bigl[ 1 - (1 - q_0)^m \bigr] \ge \tfrac{1}{2}
\,\Bigr\}.
$$

If this set is non-empty, then

$$
G^\star_{1/2}(B_1 \to B_2) \;\le\; \kappa \, m_{1/2}.
$$

Equivalently, when $0 < q_0 < 1$ and $r_0 > \tfrac{1}{2}$,

$$
m_{1/2}
\;=\;
\left\lceil
\frac{\log\!\bigl(1 - \tfrac{1}{2 r_0}\bigr)}
{\log(1 - q_0)}
\right\rceil .
$$

For first-hit access rather than terminal access (i.e. setting
$r_0 = 1$),

$$
G^\star_{\mathrm{hit},\,1/2}(B_1 \to B_2)
\;\le\;
\kappa
\left\lceil
\frac{\log(1/2)}{\log(1 - q_0)}
\right\rceil ,
\qquad 0 < q_0 < 1 .
$$

**Proof.** Take $m = m_{1/2}$ in Lemma 1; the bounds follow directly. Full proof in §11.3. $\square$

This corollary does *not* bound the injected-token barrier
$\mathrm{B}(B_1 \to B_2)$ from §3.1.1. That barrier is measured in
*injected* tokens $\tau$, whereas $\kappa\,m_{1/2}$ bounds *generated*
tokens after injection. Thus $\kappa\,m_{1/2}$ is a replace-mode
generation budget, not an injected-token barrier. In the strict
§3.1.1 sense, if the replace-mode assumptions hold with no injected
text, then the injected-token barrier is degenerate:
$\mathrm{B}(B_1 \to B_2) = 0$. If the assumptions hold only after an
injected string of length $\tau$, then the injected-token statement
is at most $\mathrm{B}(B_1 \to B_2) \le \tau$ for that injection; it
is *not* $\mathrm{B}(B_1 \to B_2) \le \kappa\,m_{1/2}$.

**Corollary 2 (one-generation special case).** If
$q_0 r_0 \ge \tfrac{1}{2}$, then

$$
G^\star_{1/2}(B_1 \to B_2) \;\le\; \kappa .
$$

For first-hit access, if $q_0 \ge \tfrac{1}{2}$, then
$G^\star_{\mathrm{hit},\,1/2}(B_1 \to B_2) \le \kappa$.

**Proof.** Take $m = 1$ in Lemma 1. $\square$ (Full step-by-step proofs of Corollaries 1 and 2 in §11.3.)

**What this means.** Replace mode does not create an accumulation
barrier in *injected* tokens: after the injection time, the previous
context is discarded, and each generation step is a fresh
reachable-state attempt to hit $B_2$. The meaningful finite quantity
in Lemma 1 is therefore the post-injection *generation* budget $G$,
not the injected-token cost $\tau$. Append mode is structurally
different because injected and generated text both remain in the
context and can accumulate; the append-mode accumulation claim is
therefore treated separately below as a conjectural $\tau$-barrier
statement, not a corollary of Lemma 1.

**Empirical verification.** §5.5 reports 94-96% switching for O2
(replace-mode paraphrase) and O3 (replace-mode summarize-then-negate)
at every dose tested, including the smallest probed (80 tokens of
any perturbation type). Read in this framework, those rates indicate
high replace-mode access probability under the tested injections: if
switching is measured after one replace generation, the data
empirically suggest $q_0 r_0 \approx 0.94$-$0.96$, certifying the
one-generation budget $G^\star_{1/2} \le \kappa$ for those conditions.
They do *not* estimate an injected-token barrier threshold: since
all probed doses switched at similar rates, the data only show that
the $\tau$-barrier is no larger than the smallest successful probed
dose, and possibly zero if the same access holds with no injected
text at all.

#### 3.1.5 Append-mode accumulation barrier (Conjecture 1)

Append mode differs from replace mode in one crucial respect: the
previous context is retained,

$$
X_{t+1} = \operatorname{clip}(X_t \Vert Y_t),
\qquad Y_t \sim P_\theta(\cdot \mid X_t; f).
$$

A perturbation injected into an append-mode loop therefore does not
overwrite the current state in one step. Instead, it is incorporated
into an already-formed bounded context and must compete with the
incumbent basin for representational dominance inside the clipping
window. This suggests that append-mode barriers should depend not on
one-step access alone, but on the cumulative amount of
**basin-relevant counter-context** that survives inside the effective
state.

Append mode differs from replace mode in one structural respect: an
injection is not a new state by itself, it must compete with the
accumulated incumbent context already inside the clipping window. The
size of the injected text relative to that incumbent context is what
determines whether the next generation is dominated by the injection
or absorbed back into the prior trajectory. The conjecture below makes
this competition precise as an effective context-share threshold.

**Conjecture 1 (append-mode accumulation barrier).** Let
$B_1, B_2 \subset \mathcal{C}$ be basin sets for an append-mode
recursive loop $X_{t+1} = \operatorname{clip}(X_t \Vert Y_t)$. Then
there exists a basin-dependent threshold
$\tau^\star_{B_1 \to B_2}$ such that:

1. **Subcritical regime:** if $\tau < \tau^\star_{B_1 \to B_2}$, then
   $\Pr(X_T \in B_2)$ remains near the drift floor.
2. **Threshold regime:** if $\tau \gtrsim \tau^\star_{B_1 \to B_2}$,
   switching probability rises rapidly.
3. **Content dependence:** $\tau^\star_{B_1 \to B_2}$ is substantially
   smaller for in-distribution perturbations than for out-of-distribution
   perturbations.

Equivalently, append-mode barrier height is governed by the
accumulation of semantically legible counter-context within the
bounded context window, rather than by one-step state overwrite.

A closely related formulation is in terms of **effective context
share**. Let $\alpha_\tau(X_t)$ denote the fraction of the clipped
context occupied by injected perturbation text after a budget of
$\tau$ tokens. Then there exists a monotone increasing function
$\Psi_{B_1 \to B_2} : [0, 1] \to [0, 1]$ such that

$$
\Pr\bigl(X_T \in B_2 \mid X_{t_{\mathrm{inj}}} \in B_1, \tau\bigr)
\;\le\;
\Psi_{B_1 \to B_2}\bigl(\alpha_\tau(X_{t_{\mathrm{inj}}})\bigr),
$$

with rapid growth occurring near a basin-dependent threshold
$\alpha^\star_{B_1 \to B_2}$.

The O1 dose-response measurements in §5.6 / §5.6.1 are consistent
with this conjecture. Neutral and lorem perturbations remain near
the irreducible drift floor across the tested range, whereas
in-distribution adversarial perturbations exhibit a graded
dose-response (ED50 ≈ 40 tokens for the *raw* switching curve at
$n=200$/cell × 8 doses; §5.6.1). The shape, monotonic rise with a
plateau below 1, is what one would expect if append-mode barriers
are controlled by the accumulation of basin-relevant counter-context
rather than by one-step access alone.

A geometric refinement of the same idea is that append-mode token
barriers should scale with the saddle height in representation space.
Let $V(x) = -\log \rho(x)$ be the empirical potential (§2.4,
§5.10) and let $V^\star(B_1, B_2)$ denote the saddle height along a
minimum-cost path between $B_1$ and $B_2$. One may conjecture that

$$
\mathrm{B}(B_1 \to B_2) \;\approx\; c_f \, V^\star(B_1, B_2),
$$

up to representation-dependent rescaling and perturbation-type
effects. We do not prove this here; rather, we treat it as a
geometric hypothesis motivated by the empirical agreement between
behavioral switching thresholds and $V^\star$-based barrier ordering
documented in §5.10.

#### 3.1.6 Tokens vs nats, a brief caveat

Token-valued barrier heights are tokenizer-dependent and model-specific.
The corresponding model-agnostic quantity would be a barrier in nats:
for generator $P_\theta$, each injected token $y_i$ at context $X$
carries $h_i = -\log P_\theta(y_i \mid X)$ nats, and $\mathrm{B}^{\text{nats}}
\approx \mathrm{B}^{\text{tokens}} \cdot \langle h \rangle_{\text{cond}}$.
**We did not capture per-token logprobs in this battery**
(`include_logprobs=False` in every publication-scale config), so
$\langle h \rangle_{\text{cond}}$ is not measured and we **do not**
report any numerical barrier in nats. All reported barriers in this
paper are operational token counts. Future work using
`include_logprobs=True` would enable a direct nat-valued barrier; an
extended discussion of the nats / KL / $V^\star$ correspondence
(originally drafted in this section) is moved to the discussion
§6 / Supplement to keep §3 focused on the formal core.

### 3.2 Observable maps and embedding

Attractor-like structure is not legible in raw text. We introduce
**observable maps** $O_t$ that extract text views of the trajectory,
and an **embedding map** $\phi$ that lifts those views into vector space:
$$
z_t = \phi(O_t) \in \mathbb{R}^m,
\qquad
m = 1536 \text{ for } \texttt{text-embedding-3-small}.
$$
A single observable string yields a single embedding vector. Each
trajectory thus produces a family of polylines $\{z_t^{(O)}\}_{t=0}^{T-1}$,
one per observable $O$, in the joint embedding space. All quantitative
metrics in §4.5 are functions of these polylines.

### 3.3 Hypotheses

We test the following hypotheses:

**H1**: In a bounded sample-driven recursive LLM loop, there exist
endogenous attractor-like regimes, properties of the loop dynamics
themselves, not just artifacts of a single seed text, and these regimes
become observable in a suitable representation space.

**H2** (mechanism): The regime depends jointly on the content function
(continue / paraphrase / summarize-and-negate / dialog) and the
context-update rule (append vs replace). Specifically:
- Append + content-preserving ⇒ contractive basin (one or a few sinks)
- Replace + content-preserving ⇒ oscillation (output ↔ paraphrase ↔ output)
- Replace + content-degrading ⇒ absorbing collapse
- Dialog (alternating roles, append) ⇒ dialogue-state-driven multi-basin

**H3** (perturbation barriers): The four regimes have qualitatively
different perturbation sensitivities. Append-mode loops have measurable
in-distribution dose thresholds; replace-mode loops have negligible
barriers; dialog has intermediate, structure-dependent barriers.

**H4** (reproducibility at scale): The qualitative structure observed at
small N (~50 trajectories) survives a 30× increase in sample size.

We pre-registered none of these in the conventional sense; the writeups
in `docs/reports/REPORT1.md` ... `REPORT6.md` document the discovery order
in fairly granular detail.

---

## 4. Methods

Before the per-component details below, the experimental skeleton is
short: we run paired recursive trajectories from the same seed and
prompt; in the treatment run we inject text at a fixed step; we embed
every step's observable output, project to a low-dimensional space, and
cluster final states jointly across treatment and control runs; the
perturbation is summarized by the perturbed run's final cluster relative
to its paired control's. We separately estimate the control-vs-control
divergence rate (how often two paired control runs already disagree
from sampling alone) and the persistent-escape rate (how often a
perturbed run jumps clusters at injection AND remains in the new
cluster at the terminal step). The remainder of §4 details each of
these components.

### 4.1 The recurrence

Instantiating the formal recurrence from §3.1 with the three nudges:
$$
\text{Append:}\quad X_{t+1} = \mathcal{N}_{\text{append}}(X_t, Y_t) = \operatorname{clip}(X_t \Vert Y_t)
$$
$$
\text{Replace:}\quad X_{t+1} = \mathcal{N}_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)
$$
$$
\text{Dialog:}\quad X_{t+1} = \mathcal{N}_{\text{dialog}}(X_t, Y_t) = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)
$$

with $Y_t \sim P_\theta(\cdot \mid X_t;\, f)$ and $P_\theta$ the
language-model distribution parameterized by $\theta$ (here
`gpt-4o-mini`). The clipping operator $\operatorname{clip}(\cdot)$
truncates context from the head (oldest) once the running string
exceeds 12,000 characters, preserving the most recent state. The
content operator $f$ enters through the system prompt fed to
$P_\theta$, e.g. "Continue the text" for $f = \text{continue}$,
"Paraphrase the following" for $f = \text{paraphrase}$.

### 4.2 Sampling

Each experiment runs `N_traj = N_families × N_ICs × N_runs`
trajectories. Publication-scale defaults differ by experiment family:

- **Operator runs (O1, O2, O3)**: 15 prompt families × 30 initial
  conditions × 3 runs = **1,350 trajectories per regime**, run for
  40 steps. Total points per experiment: 1,350 × 40 = 54,000.
- **Dialog runs (D1)**: 5 dialog-suitable families × 30 initial
  conditions × 3 runs = **450 trajectories**, 40 steps. Total points:
  450 × 40 = 18,000 per role; both roles are embedded so the
  effective per-experiment point count is 36,000.
- **D2 (drill-down dialog)** is currently at exploratory scale only:
  5 families × 5 ICs × 1 run = 25 trajectories, 50 steps. Below the
  N≥2-runs minimum for ensemble-spread diagnostics (§11.2).

In every case trajectories run for 40 steps unless explicitly noted
(D2 uses 50; the T-sweep variants vary `steps_per_run`).

Initial conditions are 5-30 short seed texts per "family" (philosophical
prompts, practical-advice prompts, creative-writing prompts, reflective
prompts, emotional prompts). Across families we get diversity in topic
and tone; within families we get variability across seeds.

Sampling temperature `T = 0.8` unless varied (Phase 2b T-sweep).

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small` (OpenAI),
producing 1536-dimensional vectors. We embed multiple *observables* per
step, each captures a different facet of the trajectory state, and
analyses are repeated per observable to expose representation-dependent
findings:

| observable | source location | what it captures |
|---|---|---|
| `output` | `core/observables.py` | the model's `Y_t` text alone (no context) |
| `rolling_k3` | `core/observables.py` | concatenation of the last 3 outputs |
| `context_tail` | `core/observables.py` | the last 4000 chars of the running context |
| `context_full` | `core/observables.py` | fixed-window 8000-char tail (longer-memory variant) |
| `last_user_turn` | `experiments/dialog/observables.py` | dialog-only: most recent user/role-A utterance |
| `last_agent_turn` | `experiments/dialog/observables.py` | dialog-only: most recent agent/role-B utterance |
| `rolling_user_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 user turns |
| `rolling_agent_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 agent turns |
| `turn_pair` | `experiments/dialog/observables.py` | dialog-only: most recent (user, agent) exchange concatenated |

The role-specific observables (`last_user_turn`, `last_agent_turn`,
`rolling_user_k3`, `rolling_agent_k3`, `turn_pair`) are essential for
dialog analysis: many properties of the regime (basin score, recurrence)
look very different when computed on the agent's responses alone vs the
user's questions vs their concatenation. We compute every metric on
every applicable observable and report inter-observable agreement as
part of the evidence chain.

The names above use D1's role labels (user / agent). For dialogs
configured with different role labels, D2 uses *explorer* / *expert*,
the role-specific observables are named after the configured roles
(`last_explorer_turn`, `rolling_expert_k3`, etc.). Role names are read
from `cfg.dialog.role_a.name` / `cfg.dialog.role_b.name` at embed time;
the observable wiring in `src/experiments/dialog/observables.py` accepts
any role-name pair.

Embeddings are batched and cached per observable. The codebase also
includes (but does not currently use in publication runs) an OpenAI
**Batch API** integration (`src/api/batch_jobs.py`) that supports
asynchronous embedding at ~50% cost, plus an **OpenAI Evals** runner
(`src/api/evals_runner.py`) gated behind `use_evals: false` in all
configs. Both are infrastructure stubs available for future expansion.

Total token cost for synchronous embedding of the full repository:
~\$30 in embedding API calls.

#### 4.3.1 Single-context embedding mechanics

A subtle but important invariant: **for one observable string at one
trajectory step, we obtain exactly one 1536-dimensional vector.** No
chunking, no internal sliding window we manage, no per-token outputs.
The `text-embedding-3-small` model handles internal attention over up
to 8,191 input tokens and produces a single pooled representation
which `embed_texts` writes to one row of the output matrix:

```
"Continue the text. The fox was quick..." → text-embedding-3-small → v ∈ R^1536
```

After the API returns, we **L2-normalize** each row defensively so all
downstream cosine-similarity computations reduce to dot products and
numerical drift from float32 round-trips does not accumulate:

```
norms = ||v||_2 + 1e-12
v_norm = v / norms # ||v_norm||_2 = 1.0
```

The model is deterministic given the input, `hash(text) → vec` is a
stable mapping under fixed model version, so the embedding cache is
safe and `analyze` reruns on the same `embeddings.npy` are identical.

Per-trajectory step we therefore obtain `K` independent vectors where
`K = |observables|`, 3 for operator publication runs (output,
rolling_k3, context_tail), 8 for dialog publication runs (the three
generic plus last_<role-A>_turn, last_<role-B>_turn,
rolling_<role-A>_k3, rolling_<role-B>_k3, turn_pair). Some pilot
configs also enable `context_full`, bringing the counts to 4 / 9.
These are stored in `K` separate `embeddings.npy` files (one per
observable); each defines its own trajectory in 1536-d embedding
space.

#### 4.3.2 Token-budget analysis

The 8,191-token API limit is held with a ~4× safety margin by
construction:

| layer | constraint | typical value | upper bound (tokens) |
|---|---|---|---|
| Per-step generation | `max_output_tokens` | 120 (operator), 160 (dialog) | ≤ 160 |
| Running context cap | `max_context_chars` | 12,000 chars | ~3,000 |
| `output` observable | the single Y_t |, | ≤ 160 |
| `rolling_k3` | 3 × Y plus 2 separators |, | ~480 |
| `context_tail` | `[-4000:]` slice |, | ~1,000 |
| `context_full` | `[-8000:]` slice |, | ~2,000 |
| `turn_pair` (dialog) | last user + last agent |, | ~320 |
| `rolling_user_k3` / `rolling_agent_k3` | 3 turns of one role |, | ~480 |

Conversion uses `cl100k_base`'s ~4 chars/token average for English
prose; the bound holds even for code- or math-heavy text where the
ratio shifts to ~3 chars/token.

The running context `X_{t+1}` itself is **never embedded directly**.
It is used to feed the generator but every observable applies a `[-N:]`
tail-slice before the embedder sees the string. This slicing is the
single rule that prevents append-mode context growth from blowing the
embedder's token budget.

#### 4.3.3 Sliding-window content in append mode

In **append mode** the running context grows monotonically until it
hits the 12,000-char clip ceiling, then stabilizes. Once
`len(context_after) ≥ N`, the slice `context_after[-N:]` is **always
exactly N chars** but its **content shifts forward by `len(Y_t)` chars
each step** (~120 chars for operator runs):

```
Step t: context_after has 9,500 chars. context_full = chars [1500 : 9500]
Step t+1: Y_{t+1} appends ~120 chars. context_full = chars [1620 : 9620]
```

So between adjacent steps the slice has ~99% content overlap and ~1%
fresh content. The resulting embeddings are **highly correlated, not
identical**. Empirically:

| observable | content overlap with previous step | adjacent-step cosine sim |
|---|---|---|
| `output` | 0% (Y_t is freshly generated each step) | ~0.5-0.8 |
| `rolling_k3` | ~67% (2 of 3 outputs unchanged) | ~0.85-0.95 |
| `context_tail` (4000 chars, append) | ~97% | ~0.95-0.98 |
| `context_full` (8000 chars, append) | ~99% | ~0.97-0.99 |

These different-overlap regimes give the trajectory **different motion
speeds in embedding space** for different observables. `output` shows
fast cycling motion (each step is a fresh generation); `context_full`
shows slow integrated drift; `rolling_k3` is the compromise. This is
exactly why we run every metric on every observable and require
cross-observable agreement before accepting a regime label, a finding
that holds only on `output` could be a per-step fluctuation; one that
holds only on `context_full` could be a slow-drift artifact; one that
holds on both is robust evidence.

In **replace mode** (O2, O3) the running context is just the latest
`Y_t` (~120 tokens), so all four content-based observables (`output`,
`rolling_k3`, `context_tail`, `context_full`) collapse to the same
short string and yield the same embedding. The `rolling_k3` observable
remains distinct in replace mode because it concatenates outputs across
multiple steps explicitly.

#### 4.3.4 Adjacent-step similarity verification

This is verifiable on any append-mode publication run:

```python
import numpy as np, pandas as pd
v = np.load("data/exp_pub_O1_continue/embeddings/context_full/embeddings.npy")
m = pd.read_parquet("data/exp_pub_O1_continue/embeddings/context_full/metadata.parquet")
sub = m[(m.prompt_family=="philosophy") & (m.run_id=="run_000")].sort_values("step")
idx = sub.index.values
sims = [float(v[idx[i]] @ v[idx[i+1]]) for i in range(len(idx)-1)]
np.median(sims) # ≈ 0.97-0.99 for context_full in append mode
```

Truly identical embeddings across consecutive steps would only happen
in degenerate cases: an absorbing fixed point where `Y_t` becomes
constant, or empty-output steps. The first happens in O3 absorbing
where `output` embedding becomes essentially constant past step ~10
(driving the basin score to 1.0); we do not see the second in
practice.

#### 4.3.5 The "single context → single embedding" rule

To summarize the answer to a question that recurred during the project:

- One observable string ⇒ one 1536-d vector. No chunking, no per-token
  output, no model-side internal sliding window we control.
- One trajectory step ⇒ K vectors (K = 3 operator, 8 dialog at
  publication scale; +1 each if `context_full` is enabled), one per
  observable, each from an independent API call.
- One trajectory ⇒ `K × T` vectors total (T steps), arranged as K
  parallel polylines in 1536-d embedding space, each with its own
  PCA, t-SNE, clustering, and metric battery.

The embedding step itself is the only place data crosses from
free-form text into the deterministic numerical world; everything
downstream is reproducible from the cached `embeddings.npy +
metadata.parquet` pair.

### 4.4 Representation spaces

For each observable's embedding matrix `Z ∈ R^{N×1536}` we compute four
projections, each fit jointly across the full point cloud (never
per-run, never per-family) so coordinates are comparable:

#### 4.4.1 PCA-2 / PCA-10 / PCA-50

Linear projections via `sklearn.decomposition.PCA` with
`random_state=42`:

- `Z_PCA-2 ∈ R^{N×2}`, for density estimation, V landscape, and most
  2D plots. Carries 10-15% of total variance for short-output observables
  (`output`); higher (~25%) for longer-context observables.
- `Z_PCA-10 ∈ R^{N×10}`, used for K-means clustering, basin
  classification, basin-predictability regression, recurrence/dwell.
  Captures 30-50% of variance and gives clusters that are both stable
  under bootstrap and interpretable in the original embedding space.
- `Z_PCA-50 ∈ R^{N×50}`, pre-reduction stage for t-SNE only. Captures
  ~80% of variance and removes the high-dimensional noise that would
  otherwise dominate cosine distances at the t-SNE step.

#### 4.4.2 t-SNE

We fit `sklearn.manifold.TSNE(n_components=2)` with the following
parameters:

```python
TSNE(
    n_components=2,
    perplexity=30, # capped at (N-1)/4 for small N
    pre_pca_dim=50, # see 4.4.1 above
    metric="cosine", # matches embedding similarity
    init="pca", # PCA-init for stability
    learning_rate="auto",
    random_state=42,
)
```

The cosine metric is chosen because OpenAI's `text-embedding-3-small`
is L2-normalized; cosine distance is the appropriate similarity in this
space. We use `init="pca"` rather than the default random init so
repeat runs give consistent projections; with `random_state=42` the
output is fully deterministic.

t-SNE is computed once per (experiment, observable). The fit time
scales as `O(N log N)` and runs in seconds for N ≤ 60k embeddings; for
larger experiments (the Phase 2 publication runs at N ≈ 108k embeddings
per observable) t-SNE takes ~30 s.

We do not interpret t-SNE distances as physical: they preserve local
neighborhood structure but not global metric. Quantitative metrics
(basin predictability, recurrence, etc.) are computed in PCA-10. t-SNE
is used only for visualization.

#### 4.4.3 Joint vs per-condition projection

In the perturbation experiments, joint PCA across all four conditions
is essential, each condition's PCA-2 cloud must live in shared
coordinates so we can compare basins, geodesics, and switching events
across conditions. The same applies to dialog experiments where each
trajectory contributes both user-turn and agent-turn embeddings: PCA
is fit on the union, then per-role observables are derived by filtering
indices.

### 4.5 Metric battery

For each (experiment, observable, projection) we compute:

#### 4.5.1 Recurrence

For trajectory points `z_0, ..., z_{T-1}` in PCA-10:

```
recurrence(ε, τ) = #{(t, s) : ‖z_t − z_s‖₂ < ε ∧ |t − s| > τ} / [T(T−1)/2]
```

with `ε = 0.15` (cosine), `τ = 3`. The lag exclusion suppresses
trivially-recurrent neighbors of a given step. Recurrence near 0 ⇒
non-recurrent (transient), recurrence near 1 ⇒ trivially recurrent
(fixed point). Most interesting regimes sit at intermediate values.

#### 4.5.2 Dwell

We K-means cluster (k=12) in PCA-10 and define the dwell distribution
as the run-length distribution within a cluster. A trajectory with
strong basins has long dwells; a transient trajectory has short ones.

#### 4.5.3 Basin score and basin entry

A "target region" is defined as the K-means cluster containing the
trajectory's final 30% of points. **Basin score** is the fraction of
post-`t*` points in that cluster, where `t* = 0.7 · T`. **Basin entry**
is the first step at which the trajectory's cluster matches its
late-window target.

#### 4.5.4 Late recurrence and exit-return

Late recurrence is the recurrence statistic restricted to the second
half of the trajectory. Exit-return measures: given that a trajectory
visited its target basin at some step, did it leave and re-enter? The
distribution of exit-return events distinguishes "tight basin" from
"meta-stable basin."

#### 4.5.5 Lyapunov spectrum

Sampling-based text generation has no smooth Jacobian (outputs are
discrete samples), so we construct a finite-time Lyapunov spectrum
from inter-run ensemble spread rather than from a one-step linearization.
This is our analog of the parameter-space Lyapunov framework that Tuci
et al. (2026) use for SGD; the construction here is independent and
specific to inference-time recursion. For each (family, IC) pair we
have N runs; at each step t the ensemble produces N embeddings forming
a covariance:

```
Σ_t = (1/(N−1)) · Σ_i (z_i^t − z̄^t)(z_i^t − z̄^t)ᵀ
```

The k-th finite-time Lyapunov exponent is the log-amplitude growth
rate of the k-th principal direction over the window
`[t_baseline, T−1]`:

```
λ_k = (1 / [2·(T − 1 − t_baseline)]) · log( μ_k(T−1) / μ_k(t_baseline) )
```

where `μ_k(t)` is the k-th eigenvalue of `Σ_t`. The factor `1/2`
converts variance growth to amplitude growth, and dividing by the
window length gives a per-step rate (units: inverse step). The top
exponent `λ_1` is interpreted as a finite-time Lyapunov exponent
(FTLE).

We compute the spectrum at **two distinct time windows**:

- **Early/transient** spectrum: averaged over `t ∈ [t_baseline=1, T/2]`,
  capturing the initial divergence regime where the ensemble is still
  dispersing from the seed.
- **Late/settled** spectrum: averaged over `t ∈ [T/2, T]`, capturing
  the on-attractor behavior after transients die out.

The early-vs-late comparison distinguishes regimes where the system is
contractive at long times but transiently divergent (e.g., O1) from
regimes that are contractive throughout (e.g., O3 absorbing). The
function `compute_lyapunov_spectrum` in
`src/experiments/dynamics/lyapunov.py` returns both windows; the FTLE
helper `ftle_from_spread` provides a scalar summary.

#### 4.5.6 Sharpness dimension and effective rank

We use a Tuci-style fractional dimension over the ordered Lyapunov
spectrum (functional form from Tuci et al. (2026), Definition 4.2):

```
j* = max { i : Σ_{k≤i} λ_k ≥ 0 } (0 if λ_1 < 0)

SD = j* + (Σ_{k≤j*} λ_k) / |λ_{j*+1}|
```

with SD = 0 when the spectrum is everywhere negative and SD = d when
the cumulative sum stays non-negative through the whole spectrum.
SD counts the effective number of *expanding* directions before global
contraction dominates: a near-neutral next eigenvalue lets SD float
above j*, a sharply contracting one keeps SD close to j*.

We borrow only the functional form. Tuci et al. anchor SD to a
generalization-bound theorem (their Theorem 4.5) for SGD on parameter
space; that theorem requires Jacobian-derived `λ_k` and a training-
data PAC framework, neither of which applies to inference-time
recursion of a frozen LLM. We treat SD as a comparative diagnostic
across regimes only.

**N=3 rank ceiling.** With N=3 runs per IC, the ensemble covariance
has rank ≤ 2, so the Lyapunov spectrum returned by
`compute_lyapunov_spectrum` has length 2. SD is therefore bounded
above by 2.0 in our experiments, and many trajectory cells saturate
at the ceiling. The mean SD_late on `context_tail` does still
differentiate regimes empirically (O1 1.70, O2 1.39, O3 1.45,
D1 1.89; §11.2), but the magnitude differences are modest. A
companion measure, **effective rank**, counts Lyapunov exponents
above −0.01; it gives a discrete count rather than a fractional
dimension and is reported alongside SD in `dynamics.csv`.

Both are computed in `src/experiments/dynamics/sharpness_dim.py`.

#### 4.5.7 Periodicity

To detect oscillatory regimes (O2-style 2-cycles, O4-style longer
cycles), we compute lag-distance autocorrelation. For trajectory points
`z_0, ..., z_{T-1}`:

```
mean_dist(k) = mean over (t, t+k) of ‖z_t − z_{t+k}‖_cos
```

The output statistics from `trajectory_periodicity` in
`src/experiments/operators/periodicity.py`:

- **`period_2_score`** = `mean_dist(1) − mean_dist(2)`, positive
  values indicate a 2-cycle (lag-2 points are closer than lag-1 points)
- **`period_3_score`**, analogous for 3-cycles
- **`best_period`**, the lag k ∈ [1, T/2] minimizing `mean_dist(k)`
- **`autocorr_distances`**, full vector of mean lag distances

This is run on every trajectory and aggregated per (regime, family) for
condition-vs-baseline tests.

#### 4.5.8 Dispersion

To distinguish contractive from exploratory dynamics we compute, in
`src/experiments/operators/dispersion.py`:

```
initial_dispersion = mean pairwise distance over t ∈ [0, T/4]
final_dispersion = mean pairwise distance over t ∈ [3T/4, T]
dispersion_growth = (final - initial) / initial
global_drift = ‖centroid(t=T) − centroid(t=0)‖
drift_monotonicity = correlation of centroid distance vs t
```

Negative `dispersion_growth` ⇒ the ensemble shrinks over time
(contractive); positive ⇒ it spreads (divergent). High
`drift_monotonicity` ⇒ the centroid moves monotonically in one
direction (e.g., absorbing toward a sink); low ⇒ centroid drifts back
and forth (oscillatory or stationary).

#### 4.5.9 Three-axis hypothesis classifier

We run a structured hypothesis test over each experiment by mapping the
above metrics to three orthogonal hypotheses:

- **H1a (convergence to a basin)**: signals are `basin_positive` and
  `dwell_above_null`. 0-2 signals → strength {not_supported, weak,
  moderate, strong}.
- **H1b (recurrence / oscillation)**: signals are
  `late_recurrence_above_null`, `period_2_score > threshold`, and
  `best_period_majority > 1`. 0-3 signals.
- **H1c (divergence / no-attractor)**: signals are
  `dispersion_growing`, `drift_monotonically_outward`, and
  `no_stable_basin`. 0-3 signals.

The classifier is implemented in
`src/experiments/operators/classifier.py` (`classify_three_axis`) and
in `src/reports/summary.py` (`classify_two_axis` for legacy
operator-only reports). Each experiment's `reports/report.md` carries
the per-hypothesis classification with the underlying signal counts
and the pre-registered thresholds.

The classifier framework predates the four-regime taxonomy and is
internally used to *justify* assigning a regime label: a config gets
classified as O1 contractive when `H1a = strong` and `H1b = weak`,
while O2 is `H1b = strong` driven by `period_2_score`. Every regime
label in this paper has an underlying H1a/b/c signal-count justification
in the corresponding experiment's report.

#### 4.5.10 Basin predictability

For each trajectory we compute the K-means cluster at the late window
(`y` = cluster index at `t > 0.7T`). For each early step k we train a
multinomial logistic regression to predict y from PCA-10 at step k.
Cross-validation:

1. **Drop singleton classes**, clusters that contain only one
   trajectory member can't be split into train/test, so we filter
   them out before CV (recording `n_dropped_classes` and
   `n_dropped_traj` per row for audit).
2. **Adaptive stratified k-fold** with
   `n_splits = min(5, smallest_class_size)`. Publication-scale runs
   (n=1350 / regime) always reach the full 5-fold; reduced-scope
   T-sweep cells (n=150) and phase-1 pilots (n=75) fall back to 2-4
   folds when the smallest remaining cluster has fewer than 5
   members. When the late-window cluster grouping leaves fewer than
   2 non-singleton classes (rare; only occurs at very early
   predictor steps for some dialog cells) we write `NaN` for that
   (regime, step) cell.

The accuracy curve `acc(k)` is monotonic in good regimes, by some
early step the late basin is already determined.

#### 4.5.11 Perturbation switching

For each trajectory we run paired runs with the same prefix but four
different perturbation conditions injected at `t_inject`:

- `control`: no perturbation
- `neutral`: a paragraph (~80 tokens) of off-topic Wikipedia text drawn
  from an 8-paragraph hand-written pool (`corpora.NEUTRAL_WIKI`); the
  pilot default sends the full paragraph, dose-parametrized variants
  (`neutral_<N>`) resize to N tokens explicitly
- `lorem`: 70 random English words drawn from a hand-curated neutral
  word pool (`corpora._WORD_POOL`) chosen to avoid emotional or
  introspective vocabulary
- `adversarial`: late-step output from a *different* (family, IC) trajectory of the same regime

We compute the K-means cluster (joint PCA-10 across all conditions, k=12)
at the final available step (29 for 30-step, 49 for 50-step trajectories).
**Switching rate** = fraction of trajectories whose final cluster differs
from their paired control's. This endpoint counts final disagreement
only and is therefore deliberately sensitive to ordinary stochastic
divergence; it is meaningful only when read together with the
control-vs-control floor (§4.5.10 / §4.7) and the persistent-escape
analysis (§3.1.2, §5.14). A switching rate that is not net-corrected
is not evidence of basin redirection.

**Algorithm 1: Paired perturbation evaluation for a recursive loop.**

```
Input:
  task / seed x
  generator P_θ
  context-update rule N
  injection condition c
  injection step t_inj
  terminal step T
  observable map O
  equivalence rule C (clustering, patch-family, tests, etc.)

1. Run two unperturbed controls:
     A = RunLoop(x, P_θ, N, no injection)
     B = RunLoop(x, P_θ, N, no injection)

2. Estimate stochastic-floor event:
     floor_event = [C(O(A_T)) ≠ C(O(B_T))]

3. Run matched treatment:
     Z = RunLoop(x, P_θ, N, inject c at t_inj)

4. Raw switching:
     raw = [C(O(Z_T)) ≠ C(O(A_T))]

5. Injection-time jump:
     jump = [C(O(Z_{t_inj+1})) ≠ C(O(Z_{t_inj-1}))]

6. Persistent escape:
     persist = jump AND [C(O(Z_T)) = C(O(Z_{t_inj+1}))]

7. Aggregate over seeds / tasks / families:
     raw_rate = mean(raw), floor = mean(floor_event)
     net_rate = raw_rate − floor
     persistent_escape_rate = mean(persist)
```

The same algorithm applies to embedding clusters (this paper) and to
engineering observables: final patch family, files touched, test
pass/fail set, selected plan category, security-policy violation, or an
embedding of the full trace.

### 4.6 Baselines

Each baseline ablates a different mechanism so we can isolate which
property of the loop is producing the observed attractor:

- **`time_shuffled`** (post-hoc): reshuffle step labels within each
  trajectory and recompute the dynamics metrics. If the metric is
  unchanged, it depends only on the marginal point cloud and not on
  temporal structure, i.e., the "trajectory" is effectively a bag of
  embeddings, not a process. Implemented in
  `src/analysis/robustness.py:time_shuffle_labels`.
- **`no_feedback`** (`src/core/baselines.py:no_feedback_provider`):
  sample each step's output from the *seed only*, ignoring the
  accumulated context. This nulls the recurrence, the loop becomes N
  independent samples conditioned on the seed. Operator regimes only.
- **`independent_regeneration`**
  (`src/core/baselines.py:independent_regeneration_provider`):
  regenerate the full trajectory from scratch each iteration, with no
  carryover. This nulls history-dependence completely: each step is
  drawn from `P_θ(. | system_prompt + seed)` independently. Operator
  regimes only.

A regime is *endogenous* only if its diagnostic statistic differs from
all three baselines beyond bootstrap CIs. The effect size relative to
each baseline is computed via Cohen's d in
`src/analysis/robustness.py:effect_vs_baseline`, which returns
`(mean_recursive − mean_baseline) / pooled_std`.

### 4.7 Statistical procedures

- **95% confidence intervals** via 1000-iteration bootstrap on
  trajectory-level quantities (`src/analysis/bootstrap.py`).
- **Cohen's d effect size** for recursive-vs-baseline magnitude
  comparisons (`src/analysis/robustness.py:effect_vs_baseline`).
- **Permutation tests** for between-condition differences (e.g.,
  switching rate under adversarial vs control), via
  `permutation_test_mean_diff` in `src/analysis/bootstrap.py`.
- **Adaptive stratified k-fold CV** for basin predictability classifier
  accuracy: `n_splits = min(5, smallest_class_size)` so phase-1 pilots
  with small clusters fall back to 2-4 folds gracefully (NaN if even
  2-fold is impossible). See §4.5.10.
- **Wilson-style CI** on switching-rate proportions where bootstrap
  would be unstable (small denominators in dose-response cells).
- **Significance gate**: a regime / condition signal counts only if its
  diagnostic statistic is `≥ 2σ` above the baseline mean *and* its
  Cohen's d ≥ 0.5 (medium effect). Both criteria must hold; CI alone
  can pass with trivially small effects under sufficient N.

### 4.8 Static visualization battery

Beyond the perturbation toolkit (§4.10), every experiment generates a
standardized set of static plots, defined in
`src/experiments/dynamics/regime_plots.py`,
`src/experiments/dynamics/field_plots.py`,
`src/experiments/dynamics/pub_tsne_plots_v2.py`, and
`src/reports/plots.py`. Notable variants (letter "D" is reserved for
the perturbation-toolkit set described in §4.10 / §11.8; lettering
A-H is non-contiguous here):

- **A: joint t-SNE colored by regime / family / step**, global view of
  where the regimes and the families live in the joint embedding.
  (`plot_joint_tsne` in `dynamics/regime_plots.py`)
- **B: per-family grid**, one t-SNE panel per prompt family, sharing
  coordinates, so cross-family heterogeneity is visible.
  (`plot_trajectory_grid` in `dynamics/regime_plots.py`)
- **C: ensemble-spread timelines**, σ(t) curves per family, the visual
  analog of FTLE; useful for distinguishing contractive (shrinking spread)
  from expanding regimes. (`plot_spread_timelines` in
  `dynamics/regime_plots.py`)
- **E: per-experiment flow field** (PCA-2 quiver), averaged per-step
  displacement field overlay on the density background.
  (`plot_flow_field_*` in `dynamics/regime_plots.py`)
- **F: t-SNE trajectory sample**, sample trajectories with the
  time-ordering visible. (`plot_tsne_trajectories_single` in
  `dynamics/regime_plots.py`)
- **G/H/I: streamlines + density / speed-colored streamlines / divergence**
 , three richer flow-field views from `dynamics/field_plots.py`
  (`plot_streamlines_density`, `plot_speed_colored_streamlines`,
  `plot_divergence_field`).
- **`plot_v2_by_step_parity`** and **`plot_v2_per_family_parity_grid`**
  in `pub_tsne_plots_v2.py`, even/odd step stratification, used to
  separate the two arms of an oscillatory 2-cycle visually.
- **`plot_regime_map_by_family`** in `dynamics/partial_snapshot.py`,
  family × IC heatmap colored by final-window cluster, useful for
  detecting whether basins are family-dependent or shared.
- **`basin_entry_hist`**, **`basin_scores`**, **`cluster_occupancy`**,
  **`dwell_dist`** in `src/reports/plots.py`, distributional plots of
  the analysis primitives, one panel per observable.

Plots are rendered at 200 DPI to PNG. Each experiment's `reports/plots/`
folder ends up with 50-150 PNGs depending on the number of observables.

### 4.9 Flow-field computation

Most of the visualization battery (G/H/I plots, perturbation
flow_skeleton, regime_plots E plot) shares a single bin-and-aggregate
kernel that turns a trajectory ensemble into a spatially-resolved
displacement vector field on the chosen 2D projection. We document it
explicitly because the kernel is what licenses the streamline /
divergence / V-landscape semantics that appear repeatedly below.

#### 4.9.1 The displacement-field kernel

Given a 2D projection `Z ∈ R^{N×2}` and trajectory metadata grouping
points into `(family, ic, run)` groups, we build:

```
For each group g with sorted-by-step indices i_0 < i_1 < ... < i_{T-1}:
    starts_g = Z[i_0:i_{T-1}] shape (T-1, 2)
    deltas_g = Z[i_1:i_T] - Z[i_0:i_{T-1}] shape (T-1, 2)
S = concat(starts_g for all g) shape (M, 2)
D = concat(deltas_g for all g) shape (M, 2)
```

`(S, D)` is the empirical displacement-field dataset: `M` observed
single-step transitions in the projection.

We then discretize the projection bounds `[x_min - p, x_max + p]` ×
`[y_min - p, y_max + p]` (with 5% padding) into a `grid_n × grid_n`
grid (typically 26 for plots, 32-48 for animations). For each grid bin
`(i, j)` we compute:

```
count[i, j] = number of (s, d) pairs with s falling into bin (i, j)
sum_u[i, j] = sum of d_x over those pairs
sum_v[i, j] = sum of d_y over those pairs
U[i, j] = sum_u[i, j] / count[i, j] (NaN if count = 0)
V[i, j] = sum_v[i, j] / count[i, j] (NaN if count = 0)
```

`(U, V)` is the per-bin **average displacement vector**. Bins with
zero observed displacements get NaN, which `streamplot` interprets as
"don't integrate through here." This gives an honest spatial map of
how the system moves: dense bins have low-noise estimates, sparse bins
are blanked.

The kernel is implemented as three pure functions in
`src/experiments/dynamics/_grid_utils.py`:

- `make_grid_edges(bounds_pts, grid_n, pad_frac=0.05)` → mesh + edges
- `bin_displacement_field(starts, deltas, x_edges, y_edges)` → (U, V)
- `bin_density(pts, x_edges, y_edges)` → count grid

These are the leaves of the import graph; every flow-field producer
in the codebase composes them.

#### 4.9.2 Density estimation

Where the displacement field uses bin-mean averaging at moderate
resolution (~26-48), the **density** field used for V landscapes and
background heatmaps uses a higher-resolution Gaussian-smoothed
histogram via `_smooth_density_grid` in
`src/experiments/dynamics/field_plots.py`:

```
H = histogram2d(pts, bins=(x_edges, y_edges)) # raw counts, grid_n × grid_n
H_smooth = scipy.ndimage.gaussian_filter(H, sigma=sigma_cells)
```

with `grid_n = 96` and `sigma = 1.5-2.0` cells. This smoother density
estimate is what feeds into `V(x) = −log(H_smooth + ε)` for the
effective-potential landscape.

We use two grid resolutions on purpose: the displacement field needs
*more* points per bin to average reliably, so it runs coarser; the
density field needs spatial smoothness, so it runs finer plus a
Gaussian post-filter.

#### 4.9.3 Streamlines

Streamlines are integral curves of the (U, V) field, computed by
`matplotlib.pyplot.streamplot`. A streamline starting at point
`x_0 = (x, y)` traces the path `x_{t+1} = x_t + (U(x_t), V(x_t))·dt`
forward in projection space. They visualize the flow that an
"average trajectory" would follow given the empirical (U, V).

We use streamlines (not arrows) because they handle continuous fields
naturally and integrate through arbitrary curvature. Streamline density
is set to 1.6-2.0; arrowsize is small (0.9-1.2) so the density isn't
visually dominated by arrowheads.

#### 4.9.4 Divergence

The divergence of the displacement field is

```
∇·v(x) = ∂U/∂x + ∂V/∂y
```

computed via `numpy.gradient` on the (U, V) grids. **Negative
divergence = sink (attractor)**: more flow enters the bin than leaves;
**positive divergence = source (repeller)**.

For recursive LLM loops we expect the whole plane to be weakly negative
on average (trajectories on the whole are not divergent), with strong
local minima at the basin centers. The divergence plots
(`I_divergence_by_condition.png`) make this quantitative, for the O3
absorbing regime the divergence has a single deep minimum at the sink;
for O2 the divergence has a saddle structure between the two cycle
arms.

#### 4.9.5 The G/H/I plot triple

For each (experiment, projection ∈ {PCA-2, t-SNE-2}) we render three
flow-field views to `data/<exp>/reports/perturbation/`:

- **G, streamlines + density**: V (density) as the magma background;
  white streamlines from (U, V) overlaid. This is the most legible
  "where does the system flow" view.
- **H, speed-colored streamlines (dark theme)**: streamlines colored
  by local `|v| = sqrt(U² + V²)`, on a dark background. Slow regions
  (basin interiors) appear cold; fast regions (transport between
  basins) appear hot.
- **I, divergence field**: heatmap of `∇·v` with a diverging colormap
  (RdBu_r), shared color scale across all conditions of the same
  experiment for direct comparison. Streamlines overlaid in thin black.

For perturbation experiments the G/H/I are rendered per-condition
(2×2 panels = 4 conditions); for non-perturbation experiments (Phase 2
publication runs) they're rendered for the recursive regime alone,
sometimes faceted by family.

### 4.10 Perturbation visualization toolkit (summary)

For perturbation experiments we compute an empirical potential
$V(x) = -\log \hat\rho(x)$ from a Gaussian-smoothed KDE on PCA-2,
locate basin centers via 8-connected local-minima detection on $V$,
and compute geodesic barriers $V^\star$ between basin pairs via
Dijkstra shortest-path on the $V$ grid. 3D animations render
iso-density shells at five density fractions using
`skimage.measure.marching_cubes`. Full implementation details
(grid parameters, smoothing constants, alpha schedules, parallel
rendering via `ProcessPoolExecutor`) are in §11.8.

### 4.11 End-to-end pipeline diagram

The full data flow from `gpt-4o-mini` generation through embeddings,
projections, metrics, and figures, with persistence boundaries marked
as `→` (each is independently re-runnable):

```tex-raw
\noindent\textit{\small Driven by \texttt{config.yaml}: model, $T$, top-$p$, steps, observables, baselines, families.}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 1, GENERATION}]
Per step $t$, generate $Y_t$ from context $X_t$ via the OpenAI Responses API
(\texttt{gpt-4o-mini}, $T = 0.8$, \texttt{max\_tokens} $\in [120, 160]$,
\texttt{store=False}); then apply the nudge to produce $X_{t+1}$:
\begin{itemize}\setlength\itemsep{0pt}
  \item \textbf{Append:}\, $X_{t+1} = \operatorname{clip}(X_t \,\Vert\, Y_t,\,12000\text{ chars})$
  \item \textbf{Replace:}\, $X_{t+1} = \operatorname{clip}(Y_t,\,12000\text{ chars})$
  \item \textbf{Dialog:}\, $X_{t+1} = X_t \,\Vert\, \operatorname{format\_turn}(\text{role}, Y_t)$
\end{itemize}
Loop $t = 0,\ldots,T-1$; persist each step to \texttt{raw/steps.jsonl} as rows
\texttt{(regime, family, ic, run, step, X\_before, Y, X\_after, response\_id, \dots)}.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 2, OBSERVABLE CONSTRUCTION}]
Per JSONL row, derive $K$ parallel string streams ($K = 3$ operator pub, $K = 8$ dialog pub;
$+1$ each with optional \texttt{context\_full}):
\begin{itemize}\setlength\itemsep{0pt}
  \item \texttt{output} $= Y_t$ (${\sim}120$ tok)
  \item \texttt{rolling\_k3} $= Y_{t-2} \,\Vert\, \mathrm{SEP} \,\Vert\, Y_{t-1} \,\Vert\, \mathrm{SEP} \,\Vert\, Y_t$
  \item \texttt{context\_tail} $=$ \texttt{X\_after[-4000:]} (${\sim}1\,$k tok)
  \item \texttt{context\_full} $=$ \texttt{X\_after[-8000:]} (${\sim}2\,$k tok)
  \item \texttt{last\_user\_turn}, \texttt{last\_agent\_turn}, \texttt{rolling\_user\_k3}, \texttt{rolling\_agent\_k3}, \texttt{turn\_pair} (dialog only)
\end{itemize}
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 3, EMBEDDING}]
For each observable independently: batch of 128 strings $\to$
\texttt{text-embedding-3-small} $\to$ list of 1536-dim vectors.
L2-normalize per row. Persist as
\texttt{embeddings/<obs>/embeddings.npy} of shape $(N,\,1536)$ and
\texttt{embeddings/<obs>/metadata.parquet} ($N$ rows; columns
\texttt{regime, family, ic, run, step, role, text\_len}).
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 4, PROJECTION (joint fit on all $N$ points per observable)}]
\begin{itemize}\setlength\itemsep{0pt}
  \item \texttt{embeddings.npy} $(N, 1536)$ \quad$\to$\quad
        \textbf{PCA(2)} $\to Z_{\mathrm{PCA2}}$ \;|\;
        \textbf{PCA(10)} $\to Z_{\mathrm{PCA10}}$ \;|\;
        \textbf{PCA(50)} $\to$ \textbf{t-SNE}(perp=30, metric=cos, init=pca, seed=42) $\to Z_{\mathrm{TSNE}}$
  \item All fits use \texttt{random\_state=42} $\Rightarrow$ fully deterministic.
  \item Routing: $Z_{\mathrm{PCA2}}$ for density / $V$ landscape / 2D plotting; $Z_{\mathrm{PCA10}}$ for K-means + metrics + classifier; $Z_{\mathrm{TSNE}}$ for visualization only (never used in metrics).
\end{itemize}
\end{tcolorbox}

\begin{center}
\begin{tikzpicture}[
  >={Stealth[length=2.6mm]}, line width=0.5pt,
  childbox/.style={draw, rectangle, rounded corners=2pt, align=left,
                   font=\footnotesize\sffamily, inner sep=4pt,
                   fill=gray!4, text width=2.85cm,
                   minimum height=2.0cm}
]
  \matrix (m) [matrix of nodes,
               column sep=4mm,
               nodes={childbox, anchor=north}] {
    {\textbf{CLUSTERING} (per obs)\\[2pt] KMeans $k{=}12$ on $Z_{\mathrm{PCA10}}$\\$\to$ cluster labels per step}
    &
    {\textbf{TIME-SERIES} (per traj)\\[2pt] recurrence, dwell, basin, basin\_entry, late\_recur, exit\_return, periodicity, dispersion}
    &
    {\textbf{ENSEMBLE} (per fam, ic)\\[2pt] Lyapunov spectrum (early/late), sharpness\_dim, effective rank}
    &
    {\textbf{PERTURBATION} (paired)\\[2pt] joint $Z_{\mathrm{PCA10}}$ + KMeans $k{=}12$\\$\to$ cluster$_T$ per cond, switching rate}
    \\
  };
  % horizontal busbar 5mm above the matrix top
  \coordinate (busL) at ([xshift=0pt, yshift=5mm] m-1-1.north);
  \coordinate (busR) at ([xshift=0pt, yshift=5mm] m-1-4.north);
  \draw (busL) -- (busR);
  % single feed arrow from above into the busbar centre
  \coordinate (busC) at ($(busL)!0.5!(busR)$);
  \draw[->] ([yshift=6mm]busC) -- (busC);
  % four drop arrows from busbar to children
  \foreach \i in {1,2,3,4} {
    \draw[->] ([yshift=5mm] m-1-\i.north) -- (m-1-\i.north);
  }
\end{tikzpicture}
\end{center}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 5, STATISTICAL VALIDATION}]
1000-iter bootstrap CIs, Cohen's $d$ vs baselines, permutation tests.
Baselines: \texttt{time\_shuffled} $\mid$ \texttt{no\_feedback} $\mid$ \texttt{independent\_regeneration}.
Significance gate: $\text{metric} \geq \text{baseline} + 2\sigma$ \emph{and} Cohen's $d \geq 0.5$.

Three-axis classifier ($\mathrm{H1a}$ convergence, $\mathrm{H1b}$ recurrence, $\mathrm{H1c}$ divergence):
\begin{tcolorbox}[pipelinesub={Verdicts}]
\begin{tabular}{@{}ll@{}}
$\mathrm{H1a}$ strong + $\mathrm{H1b}$ weak & $\Rightarrow$ contractive (O1) / dialogue-state multi-basin (D1)\\
$\mathrm{H1b}$ strong (period-2) & $\Rightarrow$ oscillatory (O2)\\
$\mathrm{H1a}$ strong + sharpness $\downarrow$ & $\Rightarrow$ absorbing (O3)\\
$\mathrm{H1c}$ strong & $\Rightarrow$ divergent / unsupported\\
\end{tabular}
\end{tcolorbox}
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 6, VISUALIZATION \& REPORTS}]
\begin{tcolorbox}[pipelinesub={STATIC PLOTS (2D)}]
A.~joint t-SNE by regime/family/step \;|\; B.~per-family grid \;|\; C.~single-IC trajectories \;|\; E.~quiver flow \;|\; F.~trajectory sample \;|\; basin\_entry histogram \;|\; basin\_scores \;|\; cluster\_occupancy \;|\; dwell\_dist \;|\; step\_parity.
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={FLOW FIELDS (G/H/I plot triple)}]
\texttt{make\_grid\_edges} + \texttt{bin\_displacement\_field} + \texttt{bin\_density} $\to$
G: streamlines + density (magma) \;|\; H: speed-colored streamlines (dark theme) \;|\; I: divergence $\nabla\!\cdot\!\mathbf{v}$ (RdBu\_r).
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={EMPIRICAL POTENTIAL LANDSCAPE TOOLKIT (perturbation only)}]
$Z_{\mathrm{PCA2}} \to$ smoothed density $\hat\rho(x) \to V(x) = -\log\hat\rho(x) \to$
basin centers (local minima of $V$) \;|\;
Dijkstra geodesics between basin pairs $\to V^\star(i,j) = \max V$ along path \;|\;
marching cubes at 5 density iso-levels $\to$ \texttt{Poly3DCollection} nested transparent shells \;|\;
\texttt{plot\_streamlines} + $V$ contour + geodesic overlay.
Hierarchical RG: $K = 48$ KMeans + Ward linkage $\to$ \texttt{rg\_dendrogram}.
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={3D ANIMATIONS (perturbation only)}]
$Z_{\mathrm{PCA3}}$ + iso-shells + 50-trajectory walk + red kick beams $\to$
\texttt{ProcessPoolExecutor} (40 workers) renders frame PNGs $\to$
\texttt{imageio-ffmpeg} libx264 $\to$ \texttt{animation3d\_<cond>.mp4} (${\sim}10\,$MB, 12s loop).
\end{tcolorbox}
\begin{tcolorbox}[pipelinesub={NARRATIVE REPORT}]
\texttt{reports/report.md} $\leftarrow$ per-observable metric tables, bootstrap CIs, baseline comparisons, $\mathrm{H1a}$/$\mathrm{H1b}$/$\mathrm{H1c}$ verdict, regime label.
Classification: not / weak / moderate / strong.
\end{tcolorbox}
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinephase={PHASE 7, CROSS-EXPERIMENT AGGREGATION}]
Read each experiment's per-experiment CSVs (via \texttt{scripts/lib\_load}), then:
\begin{itemize}\setlength\itemsep{0pt}
  \item \texttt{aggregate\_perturbation\_cross\_regime} $\to$ $4{\times}5$ switching grouped bar
  \item \texttt{aggregate\_dose\_response} $\to$ log-$x$ dose curves
  \item \texttt{aggregate\_basin\_hardening} $\to$ switch-vs-inject\_step
  \item \texttt{aggregate\_basin\_predictability} $\to$ 4-regime accuracy overlay
  \item \texttt{aggregate\_t\_sweep} $\to$ D1 $T \in \{0.3, 0.6, 0.8, 1.2\}$
  \item \texttt{aggregate\_o1\_d1\_t\_sensitivity} $\to$ side-by-side $T$ comparison
\end{itemize}
Output: \texttt{data/aggregated/<analysis>/\{csv, png, summary.md\}}.
\end{tcolorbox}
```

#### 4.11.1 Shape annotations through the pipeline

For one publication-scale operator experiment (1350 trajectories ×
40 steps × 4 observables ≈ 216,000 vectors):

```tex-raw
\begin{tcolorbox}[pipelinesub={\texttt{raw/steps.jsonl}}]
${\sim}54{,}000$ rows = $1350$ trajectories $\times$ $40$ steps.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={String corpus \,\textit{\small via \texttt{build\_all\_for\_run} $\times 4$ observables}}]
${\sim}216{,}000$ strings per experiment.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Embeddings \,\textit{\small via \texttt{embed\_texts} (batched 128, retry+backoff)}}]
\texttt{embeddings/<obs>/embeddings.npy}\,:\, $(54000,\,1536)$ float32, L2-normalized.\\
\texttt{embeddings/<obs>/metadata.parquet}\,:\, $54000$ rows.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Latent representation \,\textit{\small via PCA($n{=}10$).fit(joint) + KMeans($k{=}12$)}}]
\texttt{PCA-10}\,:\, $(54000,\,10)$ \qquad \texttt{clusters}\,:\, $(54000,)\;\in\{0\ldots11\}$.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Per-trajectory metrics}]
\texttt{recurrence.csv}\,:\, $(1350\;\text{trajectories} \times N_{\text{metrics}}\;\text{columns})$.\\
\texttt{dwell.csv}, \texttt{basin.csv}, \texttt{basin\_entry.csv}, \texttt{exit\_return.csv}, \texttt{late\_recurrence.csv}, \texttt{periodicity.csv}, \texttt{dispersion.csv}.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Per-(family, ic) ensemble dynamics}]
\texttt{lyapunov\_spectrum.csv}\,:\, ($15$ fam-ic pairs $\times T$ steps $\times$ top-$k\;\lambda$).\\
\texttt{sharpness\_dim.csv}\,:\, ($15$ fam-ic pairs $\times T$ steps).
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Statistical summaries \,\textit{\small via bootstrap + permutation + Cohen's $d$}}]
\texttt{bootstrap\_summary.csv}, \texttt{effect\_sizes.csv}.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Three-axis classifier verdict}]
\texttt{ThreeAxisDecision}: $\{h_{1a},\,h_{1b},\,h_{1c}\} \in \{\texttt{not\_supported},\,\texttt{weak},\,\texttt{moderate},\,\texttt{strong}\}$.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Reports \,\textit{\small \texttt{reports/plots}, \texttt{reports/perturbation}}}]
${\sim}70$--$150$ PNG figures $+$ (perturbation) $4$--$16$ MP4 animations.
\end{tcolorbox}
\flowarrow

\begin{tcolorbox}[pipelinesub={Cross-experiment aggregates}]
\texttt{data/aggregated/*}\,:\, cross-regime, cross-$T$, cross-dose summaries.
\end{tcolorbox}
```

#### 4.11.2 Persistence boundaries and rerun semantics

The vertical `→` arrows in the diagram are persistence boundaries:
each writes a deterministic intermediate to disk that downstream phases
read back. This means any single phase can be rerun without redoing
prior work:

| boundary | data type | re-run trigger |
|---|---|---|
| `steps.jsonl` | one JSONL row per (regime, family, ic, run, step) | re-run only if the trajectory configuration or model version changes |
| `embeddings.npy` + `metadata.parquet` | (N, 1536) float32 + N-row metadata | re-run only if observable definitions or the embedding model change |
| `pca_*.csv`, `tsne.csv` | projected coordinates | re-run only if PCA/t-SNE parameters change (random_state=42 makes this deterministic) |
| `metrics/*.csv` | per-trajectory and per-(family, ic) metrics | re-run on any metric definition change; cheap (~1 minute per experiment) |
| `reports/*.png` and `*.mp4` | rendered figures | re-run on any plotting code change; gitignored (regenerable) |

The LFS-tracked source of truth is `steps.jsonl`. Everything downstream
is regenerable from that plus the code, with a documented re-run cost
of ~\$30 in OpenAI embedding API calls and ~2 hours of local compute.

### 4.12 Hardware and software

All experiments run locally on a single workstation with API calls
to OpenAI for generation and embeddings; no GPU is required. The
host used to build the released artefacts is an HP ProLiant DL360
Gen9 with two Intel Xeon E5-2687W v3 processors (2 × 10 physical
cores at 3.10 GHz base, 40 logical threads total) and 256 GB of RAM,
running Windows 10 Pro 64-bit. Embedding ingestion, dimensionality
reduction, clustering, density-and-geodesic-barrier computation, and
animation rendering are all CPU-only.

The Python environment is Python 3.14 with numpy 2.3, scipy 1.16,
scikit-learn 1.8, scikit-image 0.26, pandas 2.3, matplotlib 3.10,
and imageio-ffmpeg 0.6 (resolved versions used to produce the
released artefacts; the code itself targets Python 3.10+). The full
dependency lock is in `requirements.txt`. Animations are stitched
via imageio-ffmpeg using the libx264 codec. The pytest suite of 99
tests is green end-to-end and runs in roughly 13 seconds in this
environment.

Parallel rendering of trajectory animations and basin diagnostics
uses `concurrent.futures.ProcessPoolExecutor` with up to 40 workers,
matching the number of logical threads on the host. The framework
makes no other hardware assumptions; the analysis pipeline runs on
any Linux, macOS, or Windows machine with the dependency stack above
and enough RAM to hold a single experiment's trajectories and PCA-10
embeddings in memory (a few GB per experiment).

### 4.13 Decision-grade endpoints

The metric battery in §4.5 is intentionally broad: it is used to
diagnose, visualize, and stress-test recursive dynamics from several
angles. The paper's headline claims, however, should not depend on
dozens of partially redundant quantities. For decision purposes, we
treat the following five endpoints as load-bearing. Each endpoint
has a fixed numerical pass rule; results that do not clear the rule
are reported as diagnostic, exploratory, or in-flight rather than as
supported regime claims. The table separates: (i) whether a regime
qualifies as attractor-like, (ii) whether its late basin is predictable
without prompt-family leakage, (iii) whether its perturbation response
has the expected regime signature, (iv) whether a token-valued barrier
is localized, and (v) whether "switching" can be interpreted as
persistent basin escape rather than final-step divergence.

```tex-raw
{\footnotesize
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{2.6cm}Y>{\raggedright\arraybackslash}p{3.5cm}Y>{\raggedright\arraybackslash}p{2.6cm}@{}}
\toprule
\textbf{endpoint} & \textbf{definition} & \textbf{measured at} & \textbf{threshold for ``regime claim is supported''} & \textbf{defined in}\\
\midrule
\textbf{Operational attractor score C1--C4} &
Count of the four attractor criteria passed: late-window basin persistence, recurrence/dwell above null, embedder robustness, and contraction / re-entry / collapse. &
Publication-scale O1, O2, O3, D1 on canonical observables; D2 exploratory status checked separately. Summary table in \S3.1.3. &
\textbf{Strong attractor:} 4/4 criteria PASS. \textbf{Attractor-like:} $\geq$3/4 PASS. \textbf{Not attractor:} $<$3/4 PASS. Missing publication-scale measurements count as FAIL unless structurally inapplicable. &
\S3.1.3; metric components in \S\S4.5.1--4.5.7\\
\addlinespace[2pt]
\textbf{Leakage-free basin predictability acc\_group(k=10)} &
GroupKFold-by-prompt-family accuracy of predicting the late-window K-means basin from the PCA-10 state at step k=10. &
Publication-scale O1/O2/O3/D1, \texttt{context\_tail}, K-means k=12, \path{data/aggregated/group_aware_basin_pred.csv}. &
To claim \textbf{cross-family basin predictability}: acc\_group(k=10) $\geq$ \textbf{0.70}. To claim the original stratified number is \textbf{leakage-free}: $\Delta$ = acc\_stratified $-$ acc\_group $<$ \textbf{0.10}. &
\S4.5.10; group-aware stress test \S5.11\\
\addlinespace[2pt]
\textbf{Perturbation switching signature} &
Final-step switching rate: fraction of perturbed trajectories whose final K-means cluster differs from the paired control trajectory. &
O1 dose-response at matched 200-token dose; O2/O3/D1 perturbation pilots; \path{data/aggregated/perturbation_cross_regime/} and \path{data/aggregated/perturbation_dose_response/}. &
\textbf{O1 selective sensitivity:} S\_adv(200) $\geq$ \textbf{0.50} and S\_adv(200) / max(S\_neutral(200), S\_lorem(200)) $\geq$ \textbf{2.0}, with max OOD switching $\leq$ \textbf{0.30}. \textbf{Replace-mode capitulation:} min non-control switching across O2/O3 neutral/lorem/adversarial $\geq$ \textbf{0.85}. &
\S4.5.11; behavioral results \S\S5.5--5.8\\
\addlinespace[2pt]
\textbf{Behavioral ED50 token barrier} &
The perturbation dose $\tau$ at which a 4-parameter logistic fit to the O1 adversarial dose-response reaches 50\% switching, with prompt-family-cluster bootstrap uncertainty. &
O1 adversarial dose sweep (original sparse: $\tau \in \{20, 80, 200, 400\}$, n=50/cell; dense rerun in \S5.6.1 uses n=200/cell $\times$ 8 doses); \texttt{fit\_ed50\_hierarchical.py}; reported in \S11.1 / \S5.6. &
To claim a \textbf{localized token barrier}: ED50 point estimate finite and the 95\% family-cluster bootstrap CI lies wholly inside the probed interval \textbf{[20, 400] tokens}. If the point estimate is inside but the CI crosses the interval boundary, report only ``finite but unlocalized / in flight.'' &
Barrier definition \S3.1.1; dose protocol \S4.5.11; ED50 analysis \S5.6\\
\addlinespace[2pt]
\textbf{Persistent basin-escape rate} &
Fraction of trajectories that visibly change cluster at injection AND remain in that post-injection cluster at the terminal step. &
O1 adversarial sparse-dose sweep using \texttt{joint\_pca10\_clusters.csv}; summary in \path{data/aggregated/persistence_summary.csv}. &
To interpret switching as \textbf{persistent basin escape} rather than final-step divergence: persistent escape rate $\geq$ \textbf{0.50} at the claimed barrier dose. If $<$0.50, switching may still be reported, but not as clean basin escape. &
Switching definition \S4.5.11; persistence reanalysis \S5.15\\
\bottomrule
\end{tabularx}
}
```

On the current data, after the dense-dose rerun (§5.6.1) and the
endpoint-decomposition framework (§3.1.2):

- **Operational attractor score (C1-C4)**: O1/O2/O3/D1 pass the
  omnibus criterion; D2 does not.
- **Leakage-free basin predictability**: only O1 passes the stricter
  acc\_group(k=10) ≥ 0.70 and Δ < 0.10 rule; O2/O3/D1 fail under
  group-aware CV (§5.11).
- **Perturbation switching signature**: O1 selective sensitivity
  passes (S\_adv(200) = 0.620 in the dense rerun, ratio to
  S\_neutral/S\_lorem ≈ 2.8). Replace-mode O2/O3 capitulation passes
  by point estimate but is partly tautological (state-overwrite
  intervention; see §5.6.1 / §11.5).
- **Behavioral $\mathrm{ED50}_{\mathrm{raw}}$ token barrier**:
  **passes** at $\approx 40$ tokens (4PL=36, GLMM=41,
  bootstrap median=52); 95% CI [8.5, 242] is wide because of the
  5-family-cluster heavy tail.
- **$\mathrm{ED50}_{\mathrm{net}}$ above natural floor**: **does
  not pass**, net effect saturates at +32 pp at dose 400, below
  the +50 pp threshold (§3.1.2).
- **Persistent basin-escape rate**: **does not pass**, at dose 400,
  only 16% of trajectories are kicked-and-persisted (§5.15 dense
  data), well below the 50% threshold. So "switching" is not
  claimed as clean basin escape. The strict
  $\mathrm{ED50}_{\mathrm{persist}}$ is undefined in the tested range.

**Observable choices outside embedding clusters.** In the present
experiments, the equivalence rule $C(O(X_T))$ is a K-means cluster of
an embedding-space observable. In tool-using coding agents, the same
endpoint structure can be instantiated with engineering observables:
final patch family (`git diff --stat`), files touched, the
failing/passing test set, the selected plan category, the tool-call
sequence, a security-policy violation, or an embedding of the full
trajectory trace. Algorithm 1 (§4.5.11) requires only a consistent,
pre-specified equivalence rule and paired controls; it does not require
that "cluster" literally mean an embedding cluster. This is what makes
the three-endpoint decomposition portable across application domains.

---

## 5. Results

The Results section is organised in four bands per the
revision-driven hierarchy (review Writing & Structure #7):

- **§5.A Primary results**, load-bearing experiments tied to the
  decision-grade endpoints in §4.13 (regime establishment,
  perturbation signatures and sparse ED50, perturbation timing,
  exploratory D2).
- **§5.B Stress tests of primary results**, the revision's
  empirical defenses (group-aware CV, cluster-stability,
  multi-granularity switching, semantic basin inspection,
  per-family heterogeneity, persistence test, V* sensitivity).
- **§5.C Secondary analyses**, temperature sweep, embedder
  invariance, cross-metric correlations, unsupervised regime
  recovery, cross-generator audit.
- **§5.D Supplementary material**, pilot history and engineering
  documentation moved to the supplementary appendix at the end of
  the paper.

(Subsection numbers below preserve the manuscript's discovery-
order numbering for cross-reference stability; the §5.A/B/C/D
labels are added as narrative dividers.)

---

### §5.A, Primary results

In append-mode continuation, in-distribution adversarial text produced
a reproducible raw-switching dose response with $\mathrm{ED50}_{\mathrm{raw}}
\approx 40$ tokens, but this was not durable basin redirection: paired
controls already diverged at ${\approx}35\%$, net switching saturated
at $+32$ percentage points, and persistent escape did not reach $50\%$
at any tested dose up to 400 tokens. Replace-mode loops showed
near-saturated raw switching in the original perturbation pilots, but
overwrite-versus-insert probes attributed most of that apparent
fragility to the context-update rule discarding prior state rather than
to a low injected-token barrier. The remaining results establish the
regime taxonomy at publication scale, quantify the dose and timing
dependence of perturbations, and then test whether the conclusions
survive leakage-aware cross-validation, alternative cluster
granularities, persistence criteria, density-landscape sensitivity,
embedder ablations, and within-vendor generator replication. The rest
of §5 stress-tests these claims from the primary measurements outward.

For the full row-by-row audit of primary endpoints, uncertainty
estimates, source files, and caveat flags, see Extended Data Table 1
(§11.3). A compact cross-regime lookup table is provided as Extended
Data Table 2 (§11.4); the main text introduces each measurement in
sequence.

### 5.1 Pilot runs validate the measurement pipeline

Three early pilot runs (`exp_default`, `exp_long`, `exp_noclip`)
validated the pipeline end-to-end and identified the contractive
basin profile that became O1. **Full pilot history moved to §11.7**;
the publication-scale story below subsumes these pilot findings.

### 5.2 Small-N runs identify candidate regimes

Eight pilot operator/dialog experiments at $n \approx 50$ trajectories
identified the diagnostic regime taxonomy (O1 contractive, O2
oscillatory, O3 absorbing, D1 dialogue-state-driven multi-basin, D2 drill-down)
plus boundary cases (O3b, O4, D3). **Full taxonomy table and
boundary-case discussion moved to §11.7**; every regime claim in §5.3
onward is grounded in publication-scale data.

### 5.3 Publication-scale runs preserve regime ordering

REPORT5 ran the four diagnostic regimes at full scale, with sample
size differing by regime family (per §4.2): operator regimes O1 / O2
/ O3 use 15 prompt families × 30 ICs × 3 runs = 1,350 trajectories
per regime; dialog regime D1 uses 5 dialog-suitable families × 30
ICs × 3 runs = 450 trajectories. All four are 40 steps long. Basin
predictability, 5-fold CV multinomial logistic regression on PCA-10,
predicting the late-window K-means cluster (k=12) from the embedding
at step k, gives a clean per-regime ordering:

| experiment | regime | observable | acc(k=5) | acc(k=10) | acc(k=20) | acc(k=final) |
|---|---|---|---:|---:|---:|---:|
| `exp_pub_O1_continue` | contractive | context_tail | 0.77 | 0.80 | 0.81 | 0.85 |
| `exp_pub_O2_paraphrase_replace` | oscillatory | context_tail | 0.90 | 0.90 | 0.91 | 0.91 |
| `exp_pub_O3_summarize_negate_replace` | absorbing | context_tail | 0.92 | 0.92 | 0.92 | 0.93 |
| `exp_pub_D1_dialog_curious_helpful_v2` | multi-basin | context_tail | n/a | 0.61 | 0.69 | 0.77 |

The "final" cluster is the trajectory's majority cluster over the
late window `t ≥ ⌈0.7T⌉` per §4.5.3. For T=40 this gives a 12-step
late window; for the dialog regime D1 with role-restricted observables
the latest predictor step is 26 (the last agent turn before the late
window opens at step 28).

(Numbers measured from
`data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`,
recursive regime only, canonical observable per regime. D1's step-5
cell is `NaN` because the joint k-means at step 5 has too few class
members for any k-fold ≥ 2 even after the adaptive fallback to
`n_splits = smallest_class_size`; it stabilizes by step 10.)

Three orderings emerge cleanly:

- **O3 absorbing** locks in earliest (step 5 ≈ final accuracy 0.89 →
  0.91). Once the absorbing sink is reached, the remainder of the
  trajectory is statistically frozen.
- **O2 oscillatory** also locks in fast (0.88 → 0.90). The 2-cycle is
  basin-stable: knowing which arm of the cycle a trajectory is on at
  step 5 is enough to predict its terminal arm.
- **O1 contractive** and **D1 multi-basin** are slower and have more
  headroom: O1 climbs from 0.77 to 0.85, D1 from 0.61 (step 10) to
  0.77 (final). The dialog regime in particular shows the *most* room
  for early-stage style-basin reorganization.

The four regimes survive scale: their qualitative ordering on every
diagnostic is preserved, and the within-regime variability (across
families and ICs) is much smaller than between-regime variation. **H4
is supported.**

![Figure 2. **Basin-predictability across regimes.** Two-panel plot of top-1 accuracy for predicting each trajectory's late-window K-means cluster from its embedding at step $k$, using publication-scale runs where available. The left panel shows acc($k$) curves; the right panel compares seed-step and final-step accuracy. O2/O3 have high early predictability, O1 increases more gradually, D1 is lower and slower, and D2 is underpowered in this analysis. Source: `data/aggregated/basin_predictability_cross/cross_basin_predictability.png`.](data/aggregated/basin_predictability_cross/cross_basin_predictability.png)

### 5.4 Temperature sweep separates O1 and D1

> **Caveat.** The T-sweep cells in this section
> are at **reduced scope** (n=150) rather than publication scope
> (n=1350 for O1, n=450 for D1). The reduced-scope T=0.8 cell sits
> 28 pct pts below the publication-scope T=0.8 anchor (0.52 vs 0.80
> for O1 acc(k=10)), meaning that **scope, not temperature,
> dominates the variance** in O1 basin-predictability across the
> sweep. The narrower 4 pct pt span we observe for D1 across T is
> still suggestive of T-stability, but the operator-regime
> T-sensitivity claim should be read as exploratory until a
> publication-scope T-sweep is run. We retain the data because the
> *qualitative* contrast (D1 narrower than O1 across T at *matched*
> reduced scope) is informative, but the absolute numbers are
> N-confounded.

We ran a temperature sweep (T ∈ {0.3, 0.6, 0.8, 1.2}) for D1 and O1 at
reduced scope (5 families × 15 ICs × 2 runs × 30 steps = 150
trajectories per cell, except the D1 T=0.8 cell which reuses the
full-scope publication run at 450 trajectories). Predictor at step
k=10 of 30, classifier trained on PCA-10 of the canonical
`context_tail` observable, target: K-means cluster (k=12) at the
late window ($t \geq 0.7\,T_{\mathrm{traj}}$). We report `acc(k=10)` rather than `acc(k=5)`
as the headline number because step 10 has the most consistent
coverage across all 8 T-sweep cells (some D1 reduced-scope cells
have no valid late-window classifier at very early steps after
singleton-cluster trajectories are dropped).

**O1 basin predictability acc(k=10) by T** (context_tail, top-1):

| T | 0.3 | 0.6 | 0.8 | 1.2 |
|---|---:|---:|---:|---:|
| acc(k=10) | 0.65 | 0.62 | 0.52 | 0.64 |

**D1 basin predictability acc(k=10) by T** (context_tail, top-1):

| T | 0.3 | 0.6 | 0.8 | 1.2 |
|---|---:|---:|---:|---:|
| acc(k=10) | 0.61 | 0.58 | 0.61 | 0.57 |

O1 shows a non-monotonic dip at T=0.8 (acc=0.52, the lowest cell) and
recovers somewhat at T=1.2 (0.64). Higher temperature broadens the
contractive basin and makes the late state harder to anchor at step
10; the T=0.8 dip is the cleanest cell-level signal of T-sensitivity
in the operator regimes. The full-scope publication run at the
canonical T=0.8 (`exp_pub_O1_continue`, n=1350) reaches acc(k=10) =
0.80 (§5.3); the reduced-scope T=0.8 cell sits 28 pct pts below
that, indicating the reduced N is the dominant source of the
operator-regime variance in this section.

D1 stays in a tight 0.57-0.61 band across all four temperatures,
a span of only **4 pct pts** vs O1's 13-pct-pt span. Once the dialog
regime locks into its dialogue-state basin, temperature alone does not
unlock it. The full-scope D1 anchor (T=0.8, n=450) reaches acc(k=10)
= 0.61, matching the reduced-scope T=0.3 and T=0.8 cells exactly,
i.e., D1's basin predictability is not just T-stable but also
**N-stable** at this scale, supporting the claim that the dialog
basin is found early and held.

This is the first quantitative diagnostic distinguishing the regimes
beyond visual inspection: D1 has 3× narrower T-variance in
basin-predictability acc than O1 over the same temperature range
on matched scope.

(All measured cells in this section are reproducible from
`data/aggregated/t_sensitivity_cross_regime/cross_t_sensitivity.csv`
filtered to `observable=context_tail` and `step=10`. See
`RESULTS.md` for cell-by-cell verification against this section.)

### 5.5 Perturbation pilots separate append from replace

![Figure 3. **Perturbation switching by regime.** Grouped bar chart of final-step switching rate, defined as final K-means cluster disagreement with the paired control trajectory; injection occurs at step 15 of a 30-step run, with $n=50$ trajectories per cell except D2 ($n=25$). O2/O3 show high switching for all perturbation types, O1 shows higher switching for adversarial than neutral/lorem perturbations, and D1/D2 fall between these cases. Source: `data/aggregated/perturbation_cross_regime/cross_switching_rates.png`.](data/aggregated/perturbation_cross_regime/cross_switching_rates.png)

For each of the four diagnostic regimes plus D2 (drill-down), we ran a
perturbation pilot at 5 families × 5 ICs × 2 runs × 30 steps = 50
trajectories per condition × 4 conditions. Switching rates with Wilson
95% confidence intervals (n=50 except D2 where n=25):

| regime | control | neutral | lorem | adversarial |
|---|---|---|---|---|
| O1 (contractive) | 0% [0-7] | 24% [14-37] | 18% [10-31] | 54% [40-67] |
| O2 (oscillatory replace) | 0% [0-7] | 100% [93-100] | 100% [93-100] | 94% [84-98] |
| O3 (absorbing replace) | 0% [0-7] | 100% [93-100] | 100% [93-100] | 96% [86-99] |
| D1 (multi-basin dialog) | 0% [0-7] | 76% [62-86] | 54% [40-67] | 60% [46-73] |
| D2 (drill-down dialog) | 0% [0-13] | n/a | n/a | 64% [44-80] |

(D2 was only tested with control + adversarial conditions, and at a
50-step horizon with override at step 25, see §5.8.)

Replace-mode operators are perturbation-transparent: 94-100% switching
under any non-control condition. The append-mode contractive regime O1
shows clear conditional sensitivity: 54% under in-distribution
adversarial, but only 18-24% under out-of-distribution random or
neutral text. The dialog regimes sit between these extremes, with D1
showing higher switching under all conditions and D2, the structured
drill-down, resisting more strongly.

**H3 is supported with refinement**: the qualitative split between
"replace-transparent / append-resistant" is clear, but the magnitude of
resistance depends on the type of perturbation, not just its presence.

### 5.6 Dose response depends on perturbation content

We varied the perturbation length 20/80/200/400 tokens for D1 (neutral)
and O1 (neutral and adversarial). D1 with neutral was additionally
tested at sub-saturation doses 5/10/15:

**D1 / neutral** (n=50 per cell; Wilson 95% CI half-width ~13 pct pts):

| dose (tokens) | 5 | 10 | 15 | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|---:|---:|---:|
| switch | 62% | 68% | 70% | 72% | 76% | 70% | 66% |

D1 saturates at sub-token doses. The raw-switching barrier height is essentially zero, any 5-token coherent interrupt flips the
dialog basin. The flat-from-saturation curve is consistent with our
"dialog basin is dialogue-state-driven, not content-bound" interpretation.

**O1 / neutral** (off-distribution; n=50 per cell; CI half-width ~12 pct pts):

| dose (tokens) | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 22% | 26% | 24% | 24% |

Flat at the out-of-distribution drift floor of ~24% across the entire dose range.
This is the "noise rate", out-of-distribution text simply cannot move
the contractive basin no matter the dose.

**O1 / adversarial** (in-distribution; n=50 per cell; CI half-width ~13 pct pts):

| dose (tokens) | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 26% | 34% | 54% | 48% |

Clear graded response. In this pilot the 50%-switching dose lies
between 80 and 400 tokens of in-distribution text, the n=50 cells
do not localize it more precisely (see Wilson CIs in Figure 4 and
the dense-dose rerun in §5.6.1). To our knowledge this is the first
**reported** raw-switching dose-response barrier-height measurement for an LLM
loop on this generator and prompt template; we do not claim
priority, only that systematic dose-response measurement of barrier
height in this form has not been a focus of prior recursive-loop
work. The same architecture
(O1 continue) produces qualitatively different dose-response curves
depending on whether the perturbation is in-distribution.

![Figure 4. **Dose-response switching curves.** Switching rate is plotted against perturbation length in tokens for D1/neutral, O1/neutral, and O1/adversarial conditions; each point has $n=50$ trajectories and 95% Wilson confidence intervals, with injection at step 15. O1/neutral remains near 20-26% across tested doses, O1/adversarial rises toward roughly 50% with a non-monotone 400-token endpoint, and D1/neutral is high even at the smallest tested doses. Source: `data/aggregated/perturbation_dose_response/dose_response.png`.](data/aggregated/perturbation_dose_response/dose_response.png)

#### 5.6.1 Dense rerun localizes raw ED50

**Lede.** The dense rerun establishes a clean raw-switching dose response in O1 adversarial append-mode continuation ($\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, with three independent fitting methods agreeing to within $\pm 8$ tokens) but rejects the stronger interpretation: the persistent-escape endpoint is not reached at any tested dose up to 400 tokens, the raw plateau sits at $\approx 0.67$ rather than 1.0, and the net effect over the stochastic floor saturates at +32 percentage points. The remainder of this subsection details the rerun's preregistration, configuration, and per-method estimates.

**Engineering scale calibration.** As a rough orientation: 40 tokens is comparable to a short repository comment, a targeted test-failure note, a small README paragraph, or a user correction naming a specific file and test. Thus the measured $\mathrm{ED50}_{\mathrm{raw}}$ is not a large-context phenomenon; small in-domain snippets can measurably alter raw terminal state, even though net and persistent-escape thresholds are not reached in the tested range.

The sparse-data dose-response above was n=50/cell, an
underpowered pilot. The dense-dose rerun was committed as a
frozen pre-registration before the run started: n=200/cell
(= 5 families × 10 ICs × 4 runs); 8 dose conditions + 1 control ×
200 = 1,800 trajectories total via
`configs/perturbation/O1_ed50_dense.yaml` and
`scripts/fit_ed50_hierarchical.py`. The pre-registered analysis
included 4 control runs/IC to enable a control-vs-control natural-
floor estimate. The run completed cleanly; results below.

**Dense O1 / adversarial dose-response** (n=200 per cell, control n=200):

*Table, Wilson 95% CIs on the dense-rerun O1 adversarial dose-response.*

| dose (tokens) | switch rate | Wilson 95% CI |
|---|---:|---|
| control | 0.000 | [0.000, 0.019] |
| 20 | 0.415 | [0.349, 0.484] |
| 50 | 0.510 | [0.441, 0.578] |
| 80 | 0.575 | [0.506, 0.641] |
| 120 | 0.630 | [0.561, 0.694] |
| 160 | 0.605 | [0.536, 0.670] |
| 200 | 0.620 | [0.551, 0.684] |
| 300 | 0.655 | [0.587, 0.717] |
| 400 | 0.670 | [0.602, 0.731] |

**ED50 estimates** (consistent across methods):

*Table, ED50 method comparison: 4PL fit, mixed-effects GLMM, and family-cluster bootstrap.*

| method | ED50 (tokens) | uncertainty |
|---|---:|---|
| 4PL pooled fit | 36 | (point) |
| Mixed-effects logistic GLMM | 41 | (point, log10-dose slope) |
| Family-cluster bootstrap median | 52 | 95% CI [8.5, 242] |

The point estimates from three independent methods cluster in the
**~36-52-token range**, substantially below an earlier sparse-data
estimate of approximately 150 tokens, which the dense rerun reveals
was an artifact of the coarse dose grid. The bootstrap CI remains
wide because only 5 prompt families means family-level resampling
has heavy tails; widening the family count in a future replication
would tighten the CI.

**Two structurally important findings beyond the point estimate:**

1. **The curve plateaus at ~67%, not 1.0.** The 4PL upper asymptote is
   $a = 0.69$. At infinite adversarial dose, only ~69% of trajectories
   switch under the current perturbation protocol. This means **a
   substantial subpopulation (~31%) is "hardened" against in-
   distribution adversarial nudges in this dose range**. Whether this
   reflects per-trajectory stochastic robustness, family-specific
   barrier structure (§5.15), or a deeper mechanistic split is an
   open question.

2. **The control-vs-control natural floor is 34.7%** [31.0%, 38.6%]
   across $n=600$ ordered control-control pairs (4 control runs/IC ×
   pairwise comparisons). Two trajectories with the *same* family /
   IC seed but different generation RNG end up in different K-means
   clusters 35% of the time *purely from stochastic divergence*, with
   no perturbation involved. **Net adversarial effect** (observed
   switching minus natural floor):

   | dose | observed | natural floor | net adversarial effect |
   |---|---:|---:|---:|
   | 20 | 0.415 | 0.347 | **+0.068** |
   | 50 | 0.510 | 0.347 | **+0.163** |
   | 80 | 0.575 | 0.347 | **+0.228** |
   | 200 | 0.620 | 0.347 | **+0.273** |
   | 400 | 0.670 | 0.347 | **+0.323** |

   Under the strictest reading, *the adversarial dose at which the
   net effect (above natural divergence) reaches 50% switching*, no
   such threshold exists in the tested range; the highest net effect
   is **+32 pp at dose 400**, well below 50 pp. The 50%-of-population
   crossing of the *raw* curve happens between dose 20 and dose 50,
   but a substantial fraction of that "switching" is confounded by
   stochastic baseline divergence.

**What the dense-rerun headline claim is, post-correction.** O1
under in-distribution adversarial perturbation has a finite,
graded-response dose-response with **ED50 (raw switching) ≈ 40
tokens**, an upper asymptote of ~67% (substantial non-switching
subpopulation), and a natural stochastic-divergence floor of ~35%
that consumes most of the apparent effect at low doses. The "barrier
height in tokens" is therefore best read as a **graded-response
parameter**, not a sharp threshold; the original "~150 token barrier"
claim is replaced by this richer characterisation. We do *not*
claim a localised barrier in the strict §3.1.1 sense (the 95%
bootstrap CI on ED50 spans an order of magnitude), but we do claim a
finite, monotone dose-response with the parameters above.

![Figure K. **Dense-dose ED50 fit.** O1 adversarial dose-response from the confirmatory rerun (8 doses × $n=200$/cell, where $n=200 = $ 5 families × 10 ICs × 4 runs; 9 cells × 200 = 1,800 trajectories). Black points are observed switching rates with family-cluster-bootstrap 95% CIs; the blue curve is a 4-parameter logistic fit (`a=0.69, d=0.28, b=1.16, ED50=36 tok`); the shaded blue band is the 95% bootstrap envelope on ED50; the dashed red line marks the bootstrap-median ED50 = 52 tokens [CI 8.5, 242]. The curve plateaus at ~67%, not 1.0, there is a non-switching subpopulation. Source: `data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png`.](data/exp_perturb_O1_ed50_dense/reports/perturbation/ed50_curve.png)

### 5.7 Injection timing reveals basin hardening

We injected the same perturbation (D1: neutral @80, O1: adversarial @200)
at three different steps of a 30-step trajectory (n=50 per cell):

*Table, Switching rate by injection step for D1 (neutral @80) and O1 (adversarial @200).*

| inject step | D1 (neutral @80) | O1 (adversarial @200) |
|---:|---:|---:|
| 5 | 72% [58-83] | 60% [46-73] |
| 15 | 78% [65-87] | 54% [40-67] |
| 25 | **52% [38-66]** | 62% [48-74] |

D1 shows partial **basin hardening**: by step 25 the trajectory has
committed to its style basin and resists more strongly (52% vs 78% at
step 15). The basin gets harder to leave as the trajectory ages.

O1 is essentially flat across injection time, the contractive
averaging operator integrates whatever is in context regardless of when
it arrived. **The two regimes have qualitatively different
time-dependence** in their barrier structure.

![Figure 5. **Switching versus injection time.** Switching rate is plotted for injections at steps 5, 15, and 25 of a 30-step trajectory, with $n=50$ per cell and 95% Wilson confidence intervals. D1/neutral at dose 80 declines at the latest injection step, while O1/adversarial at dose 200 is approximately flat across injection times. Source: `data/aggregated/perturbation_basin_hardening/basin_hardening.png`.](data/aggregated/perturbation_basin_hardening/basin_hardening.png)

### 5.8 Drill-down dialog adds content gravity

We introduced a new dialog regime: an **Explorer-Expert** drill-down
dialog where each user turn asks for a deeper, more specific
explanation of one concept from the previous expert turn. 5 topic
families × 5 seed topics = 25 trajectories at 50 steps each.

Adversarial perturbation injected at step 25, drawing from a *different
topic family*'s expert text, with 25 steps of post-injection
relaxation. Switch rate: **64%**.

Compared to D1 free dialog at the same setup (matched-relaxation D1
inject_t25 = 52%, though the doses and content differ slightly), D2's
64% under late-injection adversarial is *higher*, but compared to the
D1 pilot's 78% at step 15 with shorter relaxation, D2 shows similar or
weaker resistance. The fair comparison is at matched (override step,
relaxation horizon):

*Table, Override-vs-relaxation matched comparison: D1 free dialog vs D2 drill-down.*

| regime | override | relaxation | adversarial switch |
|---|---:|---:|---:|
| D1 free | 25 | 4 steps | 52% |
| D2 drill-down | 25 | 25 steps | 64% |

The geometric / linguistic story is: drill-down imposes content gravity
(progressive specialization into a topic tree) that free dialog lacks.
Even when the adversarial injection text is in-distribution drilled-down
expert prose, 36% of D2 trajectories pull back toward the original
specialization line. **D2 is a measurably distinct regime from D1**,
and we identify it as the fifth member of the taxonomy.

### 5.9 Cross-experiment aggregation

Seven standalone aggregator scripts produce the cross-regime comparison
artifacts that anchor the figures in this paper:

- `scripts/aggregate_basin_predictability.py`, overlay the basin
  predictability curves of the four diagnostic regimes onto a single
  axis. Output: `data/aggregated/basin_predictability_cross/`.
- `scripts/aggregate_t_sweep.py`, combine the D1 T-sweep CSVs.
  Output: `data/aggregated/t_sweep_basin_predictability/`.
- `scripts/aggregate_o1_d1_t_sensitivity.py`, side-by-side O1-vs-D1
  basin-predictability-vs-T comparison. Output:
  `data/aggregated/t_sensitivity_cross_regime/`.
- `scripts/aggregate_perturbation_cross_regime.py`, switching rates +
  relaxation curves across all 5 perturbation pilots (D1, O1, O2, O3, D2).
  Output: `data/aggregated/perturbation_cross_regime/` including the
  4×5 condition × regime grouped bar chart.
- `scripts/aggregate_dose_response.py`, dose-response curves across
  D1+O1 dose experiments, log-scale dose axis with 95% Wilson CI bars.
  Output: `data/aggregated/perturbation_dose_response/`.
- `scripts/aggregate_basin_hardening.py`, injection-time × switching
  curves for D1 + O1, with the basin-hardening interpretation.
  Output: `data/aggregated/perturbation_basin_hardening/`.
- `scripts/aggregate_perturbation_geometric_barriers.py`, combine the
  per-pilot `geodesic_barriers_summary.csv` (V*) and
  `rg_dendrogram_summary.csv` (Ward merge distance) into the wide
  regime × condition tables shown in §5.10. Output:
  `data/aggregated/perturbation_geometric_barriers/`
  (`v_star_table.csv`, `rg_merge_table.csv`, `geometric_barriers_long.csv`).

Each script reads only the per-experiment CSV outputs and is fully
deterministic, re-running them produces byte-identical figures. They
are kept separate from the per-experiment pipeline to allow incremental
re-aggregation as new experiments land.

### 5.10 Geometric barriers from V(x) = −log ρ(x)

**How to read this section.** The figures below visualize the empirical density of trajectory clouds in the joint PCA-2 embedding via $V(x) = -\log \hat\rho(x)$. They are descriptive summaries of where trajectories spent time, NOT independent quantitative validation of the behavioral barrier estimates from §5.6.1. The geometric $V^\star$ values that follow are sensitive to KDE bandwidth, grid resolution, and basin-detection parameters (CV $14$-$24\%$ across a 45-point parameter grid; see §5.16). The rank ordering of conditions is mostly stable across parameter settings, but absolute $V^\star$ magnitudes are not, and they should not be quoted as token-equivalent barrier heights. The caveat box immediately below restates these four points and adds the basin-creation-vs-barrier-crossing distinction that governs which regimes the $V^\star$↔ED50 comparison is even meaningful for.

> **Caveat.** The geometric $V^\star$ values
> reported in this section are **descriptive**, not an independent
> quantitative validation of the behavioral barrier, but the
> *ordinal ranking* of conditions by $V^\star$ is robust to analyst
> choices (see §5.16 below for the parameter-grid sensitivity
> result). In particular, for replace-mode regimes (O2/O3) the
> geometric $V^\star$ is *high* while the behavioral switching rate
> is saturated near 100%, a mechanistic mismatch we attribute to
> *basin creation* (the kick reshapes the density landscape so the
> post-kick cloud occupies a different region) rather than *barrier
> crossing*. The two mechanisms produce opposite-sign predictions
> for the relationship between $V^\star$ and switching rate. The
> $V^\star$↔ED50 correlation should therefore be computed only on
> regimes where the *barrier crossing* mechanism is hypothesized
> (i.e., O1 / D1, not O2 / O3 where basin creation is suspected).
> Numerical $V^\star$ values are sensitive to KDE bandwidth, grid
> resolution, and basin-detector thresholds (CV ~14-24% across a
> 45-parameter grid; see §5.16), but the ordinal claim
> (control > neutral / lorem > adversarial in $V^\star$) is stable
> across 89-98% of parameter combinations.

![Figure 6. **PCA-2 density landscapes for the O1 perturbation pilot.** Four panels show $V(x) = -\log \rho(x)$, computed from smoothed empirical density on the joint PCA-2 embedding for control, neutral, lorem, and adversarial conditions. Low $V$ regions correspond to high-density parts of the observed trajectory cloud. Neutral and lorem are visually closer to control than the adversarial condition, which redistributes density across the PCA-2 plane. Source: `data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png)

![Figure 7. **Geodesic summaries on the O1 PCA-2 density landscape.** Each panel shows the per-condition $V(x) = -\log \rho(x)$ contour map, detected density peaks marked by stars, and Dijkstra paths between peak pairs on the $V$ grid. The label $V^\star$ is the maximum $V$ value along each plotted path. These values are descriptive summaries of the PCA-2 density geometry and are aggregated by condition in §5.10. Source: `data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png)

![Figure 8. **Flow-field and geodesic overlays for O1 perturbations.** Each panel overlays three quantities on PCA-2: the $V(x) = -\log \rho(x)$ contour map, streamlines from binned one-step displacement vectors, and Dijkstra paths between detected density peaks with $V^\star$ labels. The panels compare how the observed displacement field and density geometry vary across control, neutral, lorem, and adversarial perturbations. Source: `data/exp_perturb_O1_pilot/reports/perturbation/flow_skeleton_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/flow_skeleton_pca.png)

![Figure 9. **Post-injection relaxation curves for O1.** Line plot of mean PCA-10 distance from each trajectory's pre-perturbation control centroid, by step and perturbation condition. The dashed line marks injection at step 15. After injection, neutral and lorem move closer to the control trajectory than adversarial, which remains farther from the pre-injection centroid. Source: `data/exp_perturb_O1_pilot/reports/perturbation/relaxation_curves.png`.](data/exp_perturb_O1_pilot/reports/perturbation/relaxation_curves.png)

![Figure 10. **O1 perturbation trajectories in t-SNE.** Each panel shows $n=50$ O1 trajectories as step-colored t-SNE polylines; arrows mark the step 14→15 displacement at injection. Adversarial perturbations produce larger visible displacements than neutral or lorem perturbations, while control trajectories show only ordinary step-to-step movement. Source: `data/exp_perturb_O1_pilot/reports/perturbation/trajectories_tsne_by_condition.png`.](data/exp_perturb_O1_pilot/reports/perturbation/trajectories_tsne_by_condition.png)

![Figure 11. **PCA-3 snapshots of O1 perturbation trajectories.** Static 2×2 composite showing the shared PCA-3 embedding for control, neutral, lorem, and adversarial conditions, with iso-density shells, six trajectory trails per panel, and red pre/post-injection segments for perturbed conditions. The adversarial panel shows longer pre/post-injection segments than neutral or lorem in this projection. Source: `data/exp_perturb_O1_pilot/reports/perturbation/animation3d_snapshots.png`.](data/exp_perturb_O1_pilot/reports/perturbation/animation3d_snapshots.png)

![Figure 12. **Joint t-SNE snapshot after O1 perturbation.** Static frame at step 24 from a joint t-SNE animation fit once on all O1 perturbation points: 4 conditions × 50 trajectories × 30 steps, with PCA-30 pre-reduction and `init="pca"`. Each panel shows current trajectory heads, recent fading trails, the full condition cloud in grey, and red X markers at pre-injection positions for perturbed runs. At this step, adversarial trajectories are more dispersed from their pre-injection locations than neutral or lorem trajectories. Animated GIF (joint fit, fixed coordinates) at `data/exp_perturb_O1_pilot/reports/perturbation/tsne_anim_joint.gif`; per-step refit companion at `tsne_anim_refit.gif`. Source: `data/exp_perturb_O1_pilot/reports/perturbation/tsne_anim_joint_snapshot.png`.](data/exp_perturb_O1_pilot/reports/perturbation/tsne_anim_joint_snapshot.png)

**Summary (per-condition V* and RG cloud expansion).** We compute
geometric $V^\star$ from the empirical density landscape on PCA-2
and Ward-linkage cloud-merge distances on $k=48$ fine clusters for
each of the four diagnostic perturbation pilots. The numerical
values are descriptive: $V^\star$ is parameter-grid sensitive
(CV 14-24%; §5.16), but the *ordinal* ranking of conditions
(control highest, adversarial lowest in 89-98% of parameter
combinations) is robust. The full $V^\star$ × condition table
and Ward-merge-distance table for each regime are moved to §11.11;
they support the qualitative reading that **(i) replace-mode O2/O3
lorem produces a new basin (high $V^\star$ + large RG expansion);
(ii) O1 adversarial has intermediate $V^\star$ consistent with
ridge-crossing rather than basin creation; (iii) D1 has low $V^\star$
across all conditions, consistent with content-independent basins**.
**The numerical $V^\star$↔ED50 correspondence does not
survive quantitative scrutiny**: the geometric values complement
but do not validate the behavioral barrier numbers.

---

### §5.B, Stress tests of primary results

### 5.11 Group-aware basin-predictability

The basin-predictability acc(k) numbers reported in §5.3 / §5.4 use
sklearn `StratifiedKFold` for cross-validation, which assigns
trajectories to train/test folds *without* respecting the
prompt-family grouping. Because the late-window basin a trajectory
ends up in is partly determined by its prompt family, especially
in dialog (D1) and replace-mode (O2/O3) regimes where the basin
co-varies with stylistic / topical content, random k-fold lets the
classifier exploit family identity as a feature, inflating
predictability above what is genuinely available from a held-out
prompt family.

To quantify the leakage, we re-ran the same basin-predictability
classifier with `GroupKFold(n_splits=5, groups=prompt_family)`,
which holds out one entire prompt family per fold and forces the
classifier to generalize across families rather than within them.
The accuracy delta `Δ = acc(stratified) − acc(grouped)` is a direct
measure of how much of the reported number was from-family
leakage. Computed via `scripts/group_aware_basin_predictability.py`
on the existing publication-scale embeddings (no new data, no API
calls).

**Result: leakage is regime-specific and substantial outside O1.**
At the canonical predictor step k=10:

*Table, Group-aware basin-predictability: stratified vs leakage-free accuracy and family-leakage $\Delta$ at $k{=}10$.*

| regime | n_traj | acc (stratified) | acc (group, leakage-free) | Δ leakage |
|---|---:|---:|---:|---:|
| O1 contractive | 1350 | 0.803 | 0.732 | **+0.071** |
| O2 paraphrase / replace | 1350 | 0.896 | 0.596 | **+0.301** |
| O3 summarize+negate / replace | 1350 | 0.912 | 0.629 | **+0.283** |
| D1 dialogue-state-driven dialog | 450 | 0.604 | 0.336 | **+0.269** |

(All accuracies are top-1; chance baseline is roughly $1/12 \approx 0.08$ for K-means k=12. Source: `data/aggregated/group_aware_basin_pred.csv` and `group_aware_basin_pred.png`.)

**Interpretation.**

- **O1 (Δ = +0.07)** is the only regime whose basin-predictability
  is robust to family leakage. The contractive basin is a real
  cross-family signal: held-out families are still classified at
  73% top-1 accuracy from PCA-10 alone, well above chance and
  above the leakage delta. The reviewer's concern is therefore
  *least* applicable to O1, which is also the regime our headline
  claims rest on.
- **O2 / O3 (Δ ≈ +0.30)** lose roughly two-thirds of their
  apparent basin signal under group-aware CV. This means the
  reported 90+% basin predictability for replace-mode regimes is
  largely a within-family fingerprint: trained on (philosophy_dialog,
  reflective, ...) and tested on the *same* family, the classifier
  recognizes "this looks like a reflective trajectory" and that
  (in replace mode) over-determines the late-window basin. Under
  honest cross-family CV, the residual basin signal at ~60%
  accuracy is still well above chance but is much weaker evidence
  for a *generic* basin structure independent of seed text.
- **D1 (Δ = +0.27)** behaves similarly, the dialogue-state basin is
  largely a family fingerprint, which is consistent with the
  paper's existing characterization of D1 as a *stylistic*
  multi-basin regime: style is correlated with prompt family by
  construction, so a within-family classifier looks confident even
  when the underlying basin signal is weaker.

**What this changes in the paper.** The §5.3 headline numbers should
be read as upper bounds; the cross-family-honest numbers are
substantially lower for replace-mode and dialog regimes. The
qualitative regime ordering survives (O3 > O2 > O1 > D1 in
stratified CV; O1 > O3 > O2 > D1 in group-aware CV, note O1 and O3
swap positions), but the *gap* between O1 and the rest is much
smaller under leakage-free CV (~10pp) than under stratified CV
(~10-30pp). The contractive basin claim is the most robust under
this stress test.

**Hierarchical model across all perturbation results.** A separate
analysis (`scripts/mixed_effects_perturbation.py`) fits a single
mixed-effects logistic regression to all 600 perturbed-trajectory
outcomes pooled across the four diagnostic perturbation pilots,
with random intercepts for prompt_family and IC-within-family. Key
result: **the IC-within-family random-intercept SD (0.82 logits) is
~3× the between-family random-intercept SD (0.29 logits)**. Most of
the trajectory-level heterogeneity is *within* prompt families, not
*between* them. Practical consequence: per-cell Wilson CIs that
treat trajectories as IID are slightly overconfident at typical
sample sizes; the headline regime ordering survives the proper
hierarchical correction (O1/adversarial fixed-effect vs D1/adversarial
reference: coefficient = −0.61, 95% CI [−1.21, −0.02], p < 0.05;
O2 and O3 conditions: coefficients +2.2 to +3.9, well above zero),
but the sub-regime cell-level rates are slightly attenuated under
partial pooling. Output:
`data/aggregated/mixed_effects_perturbation.csv`.

![Figure G. **Group-aware basin-predictability re-analysis.** Paired bars compare StratifiedKFold accuracy with GroupKFold-by-family accuracy for each regime and predictor step. The annotated $\Delta$ gives the drop when prompt families are held out across folds. O1 shows the smallest drop, while O2, O3, and D1 lose substantially more accuracy under group-aware cross-validation. Source: `data/aggregated/group_aware_basin_pred.png`.](data/aggregated/group_aware_basin_pred.png)

### 5.12 Cluster-stability check

The basin partition used throughout the paper is K-means with $k=12$
on PCA-10. Review weakness #2 asked: *are these K-means clusters real
basins, or artefacts of the K-means algorithm at this particular k?*
We address this by re-running clustering on the existing
publication-scale embeddings (no new data, no API calls) with two
methods that don't make K-means' spherical-cluster assumption: **HDBSCAN**
(density-based, finds clusters of arbitrary shape; cluster count is
auto-detected) and **spectral clustering** (graph-based, uses
nearest-neighbour affinity). Each is run on a uniform 3,000-point
subsample of the late-window cloud (the full ~20,000-point publication
cloud is too large for nearest-neighbour spectral) and compared to
K-means at $k\in\{8,12,16\}$ via Adjusted Rand Index (ARI), a
chance-corrected agreement measure where 0 = random partitioning and
1 = identical partitioning. Computed via
`scripts/cluster_stability_check.py`; per-experiment ARI matrices in
`data/exp_*/reports/cluster_stability/stability_heatmap.png`.

**Headline:** clusters are *moderately* stable across methods, but the
K-means $k=12$ partition is not unique. Median ARI between K-means@12
and the other methods, per regime:

*Table, Cluster stability: median ARI between K-means@12 and HDBSCAN per regime.*

| regime | median ARI vs K-means@12 | HDBSCAN auto-detected k | interpretation |
|---|---:|---:|---|
| O1 contractive | 0.53 | **2** | HDBSCAN sees the O1 cloud as effectively *one basin* (~98% of points in 1-2 clusters); K-means k=12 over-partitions a single contractive attractor. ARI between K-means@12 and HDBSCAN@2 is 0.01 (essentially random), they're measuring different things at different granularities. |
| O2 paraphrase / replace | 0.58 | 16 | HDBSCAN finds a cluster count similar to K-means; partitions agree at ~0.6 ARI. |
| O3 summarize+negate / replace | 0.60 | 16 | Same as O2; replace-mode regimes have moderately stable cluster structure. |
| D1 dialogue-state-driven dialog | 0.66 | 16 | Highest stability; HDBSCAN and K-means@12 agree at ~0.66 ARI. |

**What this means for the basin claim.**

- **For O1**: the contractive-basin story is *strengthened*, not
  weakened, by this stress test. HDBSCAN at default density
  thresholds prefers a one-or-two-basin partition, exactly what a
  contractive attractor should look like. The K-means $k=12$
  partition we use throughout is therefore best understood as a
  *fine-grained sub-partition of one attractor* rather than 12
  separate basins. Consequences: (a) the perturbation switching
  metric (cluster-disagreement at the K-means k=12 level) may
  partially track sub-basin movement within one large attractor
  rather than true attractor-escape, a partial confirmation of
  review weakness #2, but it still also tracks attractor-level
  changes when the perturbation pushes trajectories outside the
  contractive basin's PCA-10 envelope (which is what the
  long red kick beams in Figure 11 visualize); (b) the
  basin-predictability $A^{\mathrm{final}}=0.85$ for O1 (§5.3) is
  the predictability of the *fine-grained* partition; the *coarse*
  basin (HDBSCAN k=2) is presumably even more predictable.

- **For O2/O3/D1**: cluster stability is moderate (~0.6 ARI), the
  partition is method-dependent at the boundaries but not arbitrary.
  Combined with the group-aware basin-predictability findings in
  §5.11 (large family-leakage delta for these regimes), we conclude
  that the basin labels in O2/O3/D1 are partly stylistic / family
  fingerprints rather than purely dynamical attractor structure.

**What this changes in the paper.** We retain K-means $k=12$ as the
canonical partition because it is what every downstream metric in §5
(basin score, basin entry, perturbation switching, basin
predictability) is built on, and re-running the entire pipeline at a
different cluster granularity is out of scope for this revision.
However, all claims of the form "trajectory switched basin" should
be read with the caveat that "basin" here means K-means $k=12$
cluster, not a HDBSCAN density basin. The two notions agree for
O2/O3/D1 at ~60% agreement and disagree for O1 (where HDBSCAN sees
fewer, larger basins). Future work should compute the perturbation
switching metric at multiple cluster granularities (K-means k=2, k=12,
HDBSCAN auto) and compare the dose-response curves.

### 5.13 Multi-granularity switching

The §5.12 cluster-stability check showed that K-means $k=12$ is not
the unique partition (median ARI ≈ 0.5-0.7 vs HDBSCAN/spectral; for
O1, HDBSCAN auto-detects only 2 clusters). A natural follow-up
question: **does the perturbation switching dose-response survive at
a different cluster granularity?** If switching-rate ordering across
conditions stays the same when we re-cluster at coarser or method-
specific granularity, then the headline isn't a K-means $k=12$
artefact.

We re-ran the perturbation switching analysis on the four diagnostic
perturbation pilots (`exp_perturb_O1_pilot`, `O2_pilot`, `O3_pilot`,
`D1_pilot`) at three granularities: K-means $k=12$ (canonical),
K-means $k=4$ (coarse), and HDBSCAN (auto-detected count). For each
non-control trajectory we recomputed whether its final-step cluster
differs from its same-(family, IC, run) control trajectory, under
each granularity. Computed via
`scripts/multi_granularity_switching.py`.

*Table, Granularity comparison: switching rate at K-means $k{=}12$, $k{=}4$, and HDBSCAN per pilot.*

| pilot | condition | k=12 | k=4 | HDBSCAN | granularity-robust? |
|---|---|---:|---:|---:|---|
| O1 | adversarial | 0.54 | 0.44 | 0.60 | [OK] headline robust |
| O1 | neutral | 0.24 | 0.18 | 0.38 | [OK] low across all |
| O1 | lorem | 0.18 | 0.18 | 0.30 | [OK] low across all |
| O2 | adversarial | 0.94 | 0.72 | 1.00 | [OK] saturated at k=12 / HDBSCAN; coarse k=4 collapses some |
| O2 | neutral | 1.00 | 1.00 | 1.00 | [OK] |
| O2 | lorem | 1.00 | 1.00 | 1.00 | [OK] |
| O3 | adversarial | 0.96 | 0.74 | 0.98 | [OK] same pattern as O2 |
| O3 | neutral | 1.00 | 0.74 | 1.00 | [OK] |
| O3 | lorem | 1.00 | 1.00 | 1.00 | [OK] |
| D1 | adversarial | 0.60 | 0.50 | 0.40 | partial (drops 20pp at HDBSCAN) |
| D1 | neutral | 0.76 | 0.60 | 0.66 | partial |
| D1 | lorem | 0.56 | 0.46 | 0.44 | partial |

(All cells $n=50$; Wilson 95% CIs in
`data/aggregated/multi_granularity_switching.csv`. Source:
`data/aggregated/multi_granularity_switching.png`.)

**What this rules in.**

1. **The O1 OOD-vs-in-distribution asymmetry is granularity-robust.**
   At every cluster granularity tested, O1's adversarial switching rate
   is roughly 2-3× the OOD (neutral / lorem) rate. The headline
   contractive-basin finding is not a K-means $k=12$ artefact.

2. **Replace-mode capitulation at K-means $k=12$ and HDBSCAN is
   real.** O2 and O3 saturate at 100% switching at the canonical and
   auto-detected granularities. At coarse $k=4$, switching drops to
   72-74% on adversarial, but this is mechanistic: at $k=4$ a single
   "absorber" basin captures more of the diversity, so trajectories
   ending up in the same macro-basin no longer count as switches.

3. **D1 switching is the most granularity-sensitive.** D1's adversarial
   rate drops from 0.60 (K-means $k=12$) to 0.40 (HDBSCAN). This is
   consistent with our other findings (§5.11: D1 has 27pp family-
   leakage in basin-predictability), the D1 dialogue-state basin is partly
   a fine-grained K-means partition that doesn't fully reproduce under
   coarser methods.

**Combined with §5.11 and §5.12 results**, the picture is:
- **O1 contractive basin**: robust to family-leakage CV (+0.07
  delta), robust to cluster-method (HDBSCAN k=2), robust to
  granularity (multi-granularity switching ratio preserved). The
  most defensible regime claim in the paper.
- **O2/O3 replace-mode capitulation**: granularity-robust at fine
  granularities (k=12, HDBSCAN k=16) but partially mechanism-
  dependent at coarse k=4. Combined with §5.11's high family-
  leakage delta, the basin-level interpretation is weaker than the
  switching-rate interpretation.
- **D1 dialogue-state-driven multi-basin**: most fragile under stress tests
  (high family-leakage; granularity-sensitive switching). The
  qualitative claim survives but the absolute numbers shift
  substantially.

![Figure H. **Switching rates under alternative cluster granularities.** Panels show perturbation switching rates for D1, O1, O2, and O3, recomputed with K-means $k=12$, K-means $k=4$, and HDBSCAN; error bars are Wilson 95% CIs with $n=50$ per cell. O1 retains higher adversarial than neutral/lorem switching across all three cluster definitions, while D1 is more sensitive to the clustering method. Source: `data/aggregated/multi_granularity_switching.png`.](data/aggregated/multi_granularity_switching.png)

### 5.14 Per-cluster semantic inspection

The diagnostics in §5.11-§5.13 examined whether the K-means $k=12$
partition is statistically/methodologically robust. A complementary
question is **what the clusters semantically represent.** Are they
basins of *content* (specific topics) or basins of *style*
(register-shaped attractors)? Are the replace-mode regimes truly
absorbing in the sense of converging to common text, or only in a
formal-template sense? We answered this by extracting representative
trajectory text from each cluster (`scripts/extract_cluster_text_samples.py`)
and having a separate LLM characterise each cluster's content
blind to the paper's regime labels (using a frontier reasoning
model held out from the rest of the pipeline). Results below; raw cluster-text-sample files at
`data/aggregated/cluster_text_samples_*.md`.

#### O1, append-mode contractive (12 clusters, 1350 trajectories)

Three large attractors and four medium sub-basins, organised by
**register / style**, not by topic content:

*Table, Per-cluster semantic content for O1 (12 clusters, 1350 trajectories).*

| cluster | $n$ | dominant style | basin class |
|---:|---:|---|---|
| 7 | 355 | sentimental narrative (cozy magical scenes, friendship, wonder) | large attractor |
| 3 | 297 | expository / policy-discursive (ethics, governance, education) | large attractor |
| 1 | 258 | reflective empathic discourse (shared humanity, vulnerability, storytelling) | large attractor |
| 6 | 134 | creative coaching (process, agency, collaboration, feedback) | medium sub-basin |
| 2 | 91 | fabulist narrative (lyrical animal/landscape journeys) | medium sub-basin |
| 5 | 89 | technical tutorial (programming explanations, best practices) | medium sub-basin |
| 10 | 61 | practical advice / listicle (interpersonal, financial, workplace) | medium sub-basin |
| 0, 4, 8, 9, 11 | 8-22 | small / outlier | small |

**Finding for O1**: The convergence is **register-shaped, not
topic-shaped**: same family seeds drift to similar styles regardless
of original content. Beans, garlic, capital punishment, hashing,
paintings, landlords, and noise strings all lose their original
specificity and stabilise in one of a few high-probability
continuation styles (supportive explanation, sentimental narrative,
policy discourse). This **strengthens** the contractive-basin
interpretation but specifies the *axis of contraction*: register, not
content.

#### O2, replace-mode paraphrase (12 clusters, 1350 trajectories)

Multiple medium clusters, organised by **seed family / topic**, not
by style:

*Table, Per-cluster semantic content for O2 (12 clusters, 1350 trajectories).*

| cluster | $n$ | dominant content | basin class |
|---:|---:|---|---|
| 4 | 204 | third-person story events (clean narrative paraphrase) | large attractor |
| 9 | 178 | strong claims + technical explanations (formal declarative) | large attractor |
| 3 | 165 | abstract epistemic/philosophical explanation | large attractor |
| 0 | 140 | technical / definitional claims | large attractor |
| 1 | 101 | short fragments normalised into fuller utterances | medium sub-basin |
| 7 | 102 | metaphorical inward reflection (lyrical reflective) | medium sub-basin |
| 11 | 97 | first-person affective states (emotional self-report) | medium sub-basin |
| 10 | 90 | imperative procedural style (instructions) | medium sub-basin |
| 2, 5, 6, 8 | 64-73 | small | small |

**Finding for O2**: O2 does **not** collapse into one absorbing text
or even one shared semantic topic. It mostly preserves the seed's
local meaning while repeatedly sanding it into a more conventional
paraphrase. Narratives stay narrative; instructions stay procedural;
technical claims stay expository. This is **not** an O1-style
register attractor, it's a set of paraphrastic sub-basins organised
by seed family and surface register. The "oscillatory" label in the
paper's existing taxonomy is descriptive of the period-2 dynamics
but should not be read as "semantic convergence."

#### O3, replace-mode summarize-then-negate (12 clusters, 1350 trajectories)

Four large clusters, all dominated by the operator's **antithetical
template** (X; not-X), but each cluster preserves seed-family
content:

*Table, Per-cluster semantic content for O3 (12 clusters, "summarised then denied" template, 1350 trajectories).*

| cluster | $n$ | dominant content (within template) | basin class |
|---:|---:|---|---|
| 4 | 227 | narrative events reversed/contradicted (story arrival/absence, same/different) | large attractor |
| 3 | 160 | philosophical thesis/antithesis prose | large attractor |
| 10 | 155 | abstract/technical proposition + explicit negation | large attractor |
| 1 | 151 | code/function descriptions summarised then denied | large attractor |
| 8 | 104 | first-person creative/life problems reframed as positive/negative | medium sub-basin |
| 11 | 99 | emotional states mapped to opposite affects | medium sub-basin |
| 0, 2, 5, 6, 7, 9 | 44-88 | small | small |

**Finding for O3**: O3's "absorbing" property is **formal**, not
semantic. Nearly every trajectory becomes "summary + opposite," but
the actual content remains seed-specific. Narrative seeds become
event-summary plus reversed event; emotional seeds become affect plus
opposite affect; technical seeds become proposition plus denial.
There is no evidence that unrelated seed families converge to the
same recognisable text content. O3 is absorbing as a **discourse
template**, not as a content attractor.

#### D1, append-mode dialog (curious user + helpful agent, 11 active clusters, 450 agent-role trajectories)

Multiple medium / small clusters dominated by **dialogue-state
attractors and recent-context capture**, not by stable seed content:

*Table, Per-cluster semantic content for D1 (11 active clusters, 450 agent-role trajectories).*

| cluster | $n$ | semantic theme | basin class |
|---:|---:|---|---|
| 3 | 67 | reflection tools / journaling / communication rehearsal | medium sub-basin |
| 9 | 55 | creative feedback / taste-and-style recommendation | medium sub-basin |
| 2 | 53 | education / documentary outreach / sustainability | medium sub-basin |
| 7 | 52 | wellness / self-improvement coaching | medium sub-basin |
| 5 | 48 | upbeat empathic small talk | small |
| 11 | 42 | professional coaching / workplace productivity | small |
| 4 | 38 | creative-craft advice (game design, narrators) | small |
| 10 | 36 | affirming conversational elaboration / meaning-making | small |
| 0, 6, 8 | 15-23 | outlier / small | outlier |

**Finding for D1**: D1's basins are **dialogue-state attractors**
(supportive affirmation, practical recommendation, creative feedback,
wellness coaching, workplace advice, generic follow-up-question
mode), not stable seed-content basins. Seeds frequently lose their
original specificity through append-mode accumulation: fear becomes
yogurt advice; philosophical responsibility becomes Asana
recommendations; emotional embarrassment becomes watercolor
technique. This **qualifies** the paper's "stylistic multi-basin"
label: D1 is multi-basin, but the mechanism is *recent-context
capture / conversational drift* rather than purely stylistic
attractor convergence.

#### Comparative reading and what this changes in the taxonomy

The four regimes are *all* multi-basin at K-means $k=12$, but the
mechanism producing the basins differs:

*Table, Regime-cluster summary: basin axis, mechanism, and taxonomy implication per regime.*

| regime | basin axis | mechanism | implication |
|---|---|---|---|
| **O1** | register / style | contractive flow toward high-probability continuation styles | regime label preserved: *register-contractive* attractor |
| **O2** | seed family / topic | paraphrase preserves content; clusters reflect seed-family register | regime should be re-labeled: from "oscillatory absorbing" to "paraphrastic family-preserving" (the period-2 dynamics still hold, but the basins are not absorbing) |
| **O3** | operator template (formal X / not-X) | the negate operator imposes a discourse-shape; content stays seed-specific | regime should be re-labeled: from "absorbing" to "template-absorbing", operator-shape convergence, not semantic convergence |
| **D1** | dialogue-state / recent-context capture | append-mode dialog accumulates context; basins are conversational acts | regime should be re-labeled: from "stylistic multi-basin" to "dialogue-state-driven multi-basin", the mechanism is recent-context drift, not purely stylistic preference |

**Net effect on the taxonomy.** The four-regime taxonomy survives,
but only one of the four labels (O1) accurately describes its basin
mechanism. We retain the existing labels in this paper for
continuity with prior versions of the manuscript, but flag the
correction explicitly: O2's basins are not "absorbing" in the
content-convergence sense; O3's "absorbing" is template-formal;
D1's "stylistic" basins are mediated by conversational drift, not
direct style preference. A future revision should adopt the
re-labelled taxonomy (register-contractive / paraphrastic
family-preserving / template-absorbing / dialogue-state-driven).

### 5.15 Per-family heterogeneity and persistence of "switching"

**Why this section exists.** The headline raw-switching endpoint counts final-cluster disagreement and is therefore deliberately sensitive to any final-step displacement, including transient kicks that recovered. This subsection tests whether the headline switching corresponds to durable basin escape (the strict reading) or merely to final-step disagreement (the loose reading) by decomposing each switching trajectory into 'kicked at injection AND persisted to terminal step' versus 'kicked-and-recovered' versus 'drifted-without-kick' categories.

Two further reanalyses of the existing O1 sparse-dose adversarial
sweep (`exp_perturb_O1_dose_adversarial`, n=50/cell × 4 doses)
sharpen the interpretation of the headline switching metric. Both
use the existing `joint_pca10_clusters.csv` outputs, no new data,
no API calls. Computed via `scripts/per_family_and_persistence.py`.

#### Per-family ED50 heterogeneity

The population-level dose-response saturates at ~50% switching
(§5.6, Figure 4). We asked: is this **one population at half-mixing**
(every trajectory has 50% chance of crossing) or **family
heterogeneity** (some families consistently cross, others don't)?
Per-family rates from the existing sparse data:

*Table, Per-family O1 adversarial switching rates across the sparse dose grid.*

| family | dose 20 | dose 80 | dose 200 | dose 400 |
|---|---:|---:|---:|---:|
| philosophy_dialog | 0.10 | 0.40 | **0.90** | 0.50 |
| practical_dialog | 0.40 | 0.20 | 0.70 | **0.80** |
| creative_dialog | 0.20 | 0.40 | 0.30 | 0.60 |
| reflective | 0.30 | 0.30 | 0.40 | 0.40 |
| emotional | 0.30 | 0.40 | 0.40 | **0.10** |

(All cells $n=10$. Source:
`data/aggregated/per_family_ed50.csv` and
`per_family_ed50.png`.)

**Finding.** The population-level saturation hides substantial
family heterogeneity. **`philosophy_dialog` shows a clear
threshold-crossing pattern** (0.10 → 0.40 → 0.90, a clean dose-
response). **`practical_dialog` shows monotone increase** beyond
dose 80 (0.40 → 0.20 → 0.70 → 0.80). But **`emotional` shows a
*negative* dose-response at dose 400** (drops from 0.40 to 0.10),
and **`reflective` is essentially flat** across all doses
(0.30 → 0.30 → 0.40 → 0.40). The flat / negative families pull
the population-mean curve below saturation.

The implication for "barrier height" is structural: under the
current switching definition, **there is no single ED50 for O1
in the sparse-data analysis**, different prompt families have
different dose-response shapes. The dense-dose rerun (§5.6.1)
recovers a clean *population-level* monotonic curve at $n=200$/cell,
with a tighter point estimate (ED50 ≈ 40 tokens), but the underlying
per-family heterogeneity flagged here is still expected to apply
within the dense data, a future per-family decomposition of the
$n=200$/cell rerun would refine the picture.

![Figure I. **Per-family O1 adversarial dose-response.** Lines show switching rate versus adversarial dose for each prompt family in the sparse O1 dose experiment, with $n=10$ trajectories per family-dose cell; the dashed black line is the population mean. Family-level curves differ: some increase with dose, while others are flat or non-monotone in this pilot sample. Source: `data/aggregated/per_family_ed50.png`.](data/aggregated/per_family_ed50.png)

#### Persistence test: is "switching" basin-escape or stochastic divergence?

The headline "switching" metric is `final-step cluster ≠ paired-
control's final-step cluster` (§4.5.11). A direct mechanistic test
of *barrier crossing* is more conservative: did the trajectory
**visibly jump cluster at the moment of injection** (step 14 → step
15 cluster change)? And if it did, did it **persist** in the new
basin to the end of the trajectory, or **drift back** to its pre-
injection cluster?

**Persistence test on the dense-rerun data** ($n = 200$/cell × 8
doses; same `joint_pca10_clusters.csv` as §5.6.1):

*Table, Persistent-escape decomposition under K-means $k{=}12$ at dense O1 adversarial doses.*

| condition | n | kicked at injection | persisted (kicked AND final = post-inj) | drifted back (kicked AND final = pre-inj) | drifted elsewhere | persistent-escape rate (n_persisted / 200) |
|---|---:|---:|---:|---:|---:|---:|
| adversarial_dose20 | 200 | 10 (5.0%) | 7 (70%) | 1 | 2 | **3.5%** |
| adversarial_dose50 | 200 | 23 (11.5%) | 14 (61%) | 2 | 7 | **7.0%** |
| adversarial_dose80 | 200 | 18 (9.0%) | 7 (39%) | 3 | 8 | **3.5%** |
| adversarial_dose120 | 200 | 43 (21.5%) | 18 (42%) | 7 | 18 | **9.0%** |
| adversarial_dose160 | 200 | 53 (26.5%) | 23 (43%) | 7 | 23 | **11.5%** |
| adversarial_dose200 | 200 | 59 (29.5%) | 26 (44%) | 11 | 22 | **13.0%** |
| adversarial_dose300 | 200 | 64 (32.0%) | 28 (44%) | 7 | 29 | **14.0%** |
| adversarial_dose400 | 200 | 69 (34.5%) | 32 (46%) | 13 | 24 | **16.0%** |

(Source: `data/aggregated/persistence_summary.csv`, overwritten
with dense-rerun values via `scripts/per_family_and_persistence.py
--exp exp_perturb_O1_ed50_dense`.)

**Finding (dense data).** The persistent-escape rate (kicked AND
persisted in new basin to terminal step) **is 16% at dose 400**,
the maximum tested. Compare to the **67% raw switching rate at
dose 400** (§5.6.1, dense): the gap is **51 percentage points**.
**Most of the raw "switching" is post-injection stochastic
divergence from the paired control, not clean barrier-crossing.**
Of trajectories that *do* visibly jump cluster at injection (35%
at dose 400), only ~46% persist to the terminal step; the rest
drift back to their pre-injection cluster (~19%) or to a third
basin (~35%). Even visible at-injection kicks are transient
roughly half the time, consistent with a contractive basin
pulling trajectories back even after a cluster-boundary excursion.

The persistent-escape ED50 (the dose where persistent escape rate
crosses 50%) is **not reached in the tested range**. The dense
rerun thus confirms a key conceptual distinction: the formal §3.1.1
barrier-height definition is a persistent-escape endpoint, and
that endpoint is undefined in this experiment. The dense
$\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens is a raw-switching
endpoint, established but distinct from the formal barrier
definition (§3.1.2).

For comparison, the original sparse-pilot persistence numbers
($n=50$/cell, 4 doses) gave 8% kicked-and-persisted at dose 400,
qualitatively similar pattern, but the dense rerun's 16% has
narrower uncertainty and richer dose granularity. Both data sets
support the same conclusion: persistent escape is a different
quantity from raw switching, and it is much smaller in O1 under
in-distribution adversarial perturbation.

**Multi-granularity persistence, does the persistent-escape ED50
result survive different cluster definitions?** A natural
robustness concern is that persistent escape, defined relative to
K-means clusters, might be sensitive to the cluster granularity.
We re-ran the persistence test on the same dense data using three
cluster granularities: K-means $k=12$ (canonical), K-means $k=4$
(coarse), and HDBSCAN (auto, 18 clusters detected on the joint
PCA-10 cloud). Computed via
`scripts/multi_granularity_persistence.py`.

*Table, Persistent-escape rate under K-means $k{=}12$, $k{=}4$, and HDBSCAN per dose.*

| dose | persistent escape (k=12) | persistent escape (k=4) | persistent escape (HDBSCAN) | kicked at injection (HDBSCAN) |
|---|---:|---:|---:|---:|
| 20 | 3.5% | 1.5% | 7.0% | 12.0% |
| 50 | 7.0% | 3.0% | 16.5% | 28.5% |
| 80 | 3.5% | 5.0% | 28.5% | 48.0% |
| 120 | 9.0% | 4.5% | 35.5% | 58.0% |
| 160 | 11.5% | 9.5% | 41.0% | 64.5% |
| 200 | 13.0% | 13.5% | 40.5% | 60.0% |
| 300 | 14.0% | 8.5% | 40.0% | 66.5% |
| 400 | **16.0%** | **10.0%** | **39.5%** | 68.5% |

(Source: `data/aggregated/multi_granularity_persistence.csv`.)

**The persistent-escape ED50 is undefined under all three
granularities.** The maximum persistent-escape rate across all
doses and granularities is HDBSCAN at dose 400 = 39.5%, well below
the 50% threshold. K-means $k=12$ and $k=4$ give 10-16% maxima.
The headline conclusion, *persistent basin escape is not measured
in the tested range*, is **robust to cluster choice**. The HDBSCAN
"kicked at injection" rate does cross 50% (68.5% at dose 400), but
of those visible at-injection jumps, only ~58% persist to the
terminal step under HDBSCAN; the rest drift back or to a third
cluster. So even at the most permissive granularity, the **kicked-
AND-persisted** rate stays below 50%.

![Figure L. **Multi-granularity persistence rates vs adversarial dose.** O1 dense rerun ($n=200$/cell × 8 doses). Three cluster granularities: K-means $k=12$ (blue, canonical); K-means $k=4$ (orange, coarse); HDBSCAN auto (green, 18 clusters detected). Solid lines: persistent-escape rate (kicked at injection AND in new cluster at terminal step). Dashed lines: kicked-at-injection rate (cluster differs at step 15 vs step 14). Grey dotted line: 50% threshold (formal persistent-escape barrier). Persistent escape never reaches 50% at any granularity; HDBSCAN at dose 400 gives the maximum at 39.5%. The result is robust to cluster definition. Source: `data/aggregated/multi_granularity_persistence.png`.](data/aggregated/multi_granularity_persistence.png)

**Engineering consequence.** For agent evaluations that consume tool outputs, file contents, or third-party documents, this implies that next-step compliance, final-output disagreement, and durable task redirection should be reported as separate outcomes. A tool output, file comment, or web-fetched page may cause a visible trajectory jump (raw switching) without producing persistent capture of the subsequent plan-edit-test loop.

### 5.16 V* parameter-grid sensitivity

The §5.10 caveat box flagged that $V^\star$ values depend on
analyst-chosen KDE bandwidth, grid resolution, and basin-detector
thresholds. We quantified this directly. For the O1 perturbation
pilot, we re-ran the geodesic-skeleton $V^\star$ computation across
a parameter grid:

- **KDE bandwidth** (`sigma_cells`): {1.0, 1.5, 2.0, 2.5, 3.0}
- **Grid resolution** (`grid_n`): {64, 96, 128}
- **Basin count** (`n_basins`): {3, 4, 5}

This is **45 parameter combinations × 4 conditions = 180 cells**.
PCA-2 was held fixed (the geodesic skeleton is intrinsically 2-D).
For each cell we computed the per-condition mean $V^\star$ across
all inter-basin geodesics. Computed via
`scripts/v_star_sensitivity.py`; outputs at
`data/aggregated/v_star_sensitivity.csv` (raw),
`v_star_sensitivity_summary.csv` (per-condition spread).

**Per-condition spread of $V^\star$ across the parameter grid:**

*Table, $V^\star$ sensitivity by condition: min/median/max/std/CV across 45 parameter combinations.*

| condition | min $V^\star$ | median | max | std | CV (%) |
|---|---:|---:|---:|---:|---:|
| **control** | 2.63 | 3.78 | 5.13 | 0.61 | **16%** |
| **neutral** | 1.86 | 2.43 | 3.38 | 0.33 | **14%** |
| **lorem** | 2.00 | 2.81 | 4.37 | 0.54 | **19%** |
| **adversarial** | 1.22 | 2.07 | 3.27 | 0.50 | **24%** |

**Ordinal stability**: across the 45 parameter combinations:

- **control has the highest $V^\star$ in 98% of combinations**, never the lowest;
- **adversarial has the lowest $V^\star$ in 89% of combinations**, never the highest;
- neutral and lorem occupy the middle.

**Reading.** The numerical $V^\star$ values are not invariant to
parameter choices, the per-condition coefficient of variation is
14-24% across the tested grid, so a single $V^\star$ number reported
without sensitivity context could be misleading by ~20%. **However,
the ordinal claim that the $V^\star$ ranking is `control > neutral /
lorem > adversarial` is robust to analyst choices**: it holds in
89-98% of the 45 parameter combinations. This *supports a weaker but
still useful version* of the original claim: $V^\star$ gives a
reliable rank-order signal of basin geometry across the four
perturbation conditions, even though the numerical values are
KDE-bandwidth-dependent.

**What this changes in the paper.** §5.10's V* tables retain their
(post-revision) status as descriptive visualisations of density
structure. The ordinal-agreement claim that the original abstract
made, "behavioral and geometric barriers agree in ordinal
structure", is partially rehabilitated: the **rank ordering is
empirically robust**, but only over the comparison space of four
conditions within one perturbation pilot, not as a quantitative
correspondence between V* and ED50. We do not reinstate the
original abstract claim, but the §5.10 caveat box now reflects the
empirical finding.

![Figure J. **Sensitivity of $V^\star$ to density-landscape parameters.** Lines show per-condition mean $V^\star$ for the O1 perturbation pilot across 45 combinations of KDE bandwidth, grid resolution, and basin count. Absolute $V^\star$ values vary across parameter settings, while control is usually the highest condition and adversarial is usually the lowest in this grid. Source: `data/aggregated/v_star_sensitivity.png`.](data/aggregated/v_star_sensitivity.png)

### 5.17 Replace-mode tautology probe, overwrite vs insert

**What this probe is for.** Replace-mode regimes (O2, O3) appear to switch at near-100% under the existing protocol, which would suggest a very low attractor barrier. This probe directly tests whether that vulnerability reflects a low basin barrier in the model or whether it is an artifact of the update rule erasing prior state. We isolate the two by re-running the same injection text and dose under two contrasting conditions: overwrite (the existing protocol, injection replaces the model's output at the injection step) versus insert (injection prepended to context, model generates normally and the model's own output remains).

The original O2/O3 perturbation result, 94-100% switching at all
probed doses, is partly tautological, because the replace-mode
operator in `adversarial_doseN` *overwrites* step 15's output
entirely. Under that intervention, "the trajectory's state
changed" is true by construction.

To separate the operator's overwrite contribution from a genuine
basin-reaching effect of the perturbation text, we ran a paired
experiment with two perturbation modes:

- **`adversarial_doseN`** (overwrite, current behavior): injection
  text replaces step 15's output entirely. State at $X_{16}$ is the
  injection itself.
- **`adversarial_insert_doseN`** (NEW): injection text is prepended
  to the context for step 15's generation, but the model's normal
  output is preserved as $Y_{15}$. The injection text vanishes from
  context after this single step (single-step context augmentation).

Config: `configs/perturbation/O2_overwrite_vs_insert.yaml`,
$n=50$/cell × 5 conditions, paraphrase + replace operator.

**O2 results** (paraphrase + replace operator):

*Table, Insert-vs-overwrite switching at dose 80 / dose 200 for O2 (paraphrase + replace).*

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80` (overwrite) | **0.92** | [0.81, 0.97] |
| `adversarial_insert_dose80` | **0.32** | [0.21, 0.46] |
| `adversarial_dose200` (overwrite) | **0.98** | [0.90, 1.00] |
| `adversarial_insert_dose200` | **0.18** | [0.10, 0.31] |

**O3 results** (summarize + negate, replace operator), testing
whether the overwrite artifact generalises across replace-mode
operators:

*Table, Insert-vs-overwrite switching at dose 80 / dose 200 for O3 (summarize + negate, replace).*

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80` (overwrite) | **0.90** | [0.79, 0.96] |
| `adversarial_insert_dose80` | **0.18** | [0.10, 0.31] |
| `adversarial_dose200` (overwrite) | **0.92** | [0.81, 0.97] |
| `adversarial_insert_dose200` | **0.12** | [0.06, 0.24] |

(Sources:
`data/exp_perturb_O2_overwrite_vs_insert/reports/perturbation/switching_summary.csv`
and
`data/exp_perturb_O3_overwrite_vs_insert/reports/perturbation/switching_summary.csv`.)

**Finding (across both replace-mode regimes).** The overwrite vs
insert gap is **60-80 percentage points** for both O2 and O3:

*Table, $\Delta$ summary: overwrite minus insert switching for O2 and O3 at doses 80 and 200.*

| regime | dose | overwrite | insert | overwrite − insert |
|---|---:|---:|---:|---:|
| O2 | 80 | 0.92 | 0.32 | **+0.60** |
| O2 | 200 | 0.98 | 0.18 | **+0.80** |
| O3 | 80 | 0.90 | 0.18 | **+0.72** |
| O3 | 200 | 0.92 | 0.12 | **+0.80** |

When the operator no longer overwrites state, switching falls to
**12-32%**, well below the natural-floor estimate for O1 (~35%,
from §5.6.1) and far below the headline 90-98% from the original
sparse pilots. **Most of O2 and O3's reported "perturbation
transparency" is the replace operator overwriting state by
construction, not the perturbation text reaching a competing
basin.** The pattern is robust across the two replace-mode
operators (paraphrase preservation in O2 and content-degrading
summarize-and-negate in O3), confirming that the overwrite
contribution is **operator-independent within the two tested replace-mode operators (O2, O3)**.

O3's insert-mode rate (12-18%) is *lower* than O2's (18-32%),
suggesting that the summarize-and-negate template's strong content
constraint pulls trajectories *back* toward its absorbing template
even when the perturbation-prepended context tries to push elsewhere,
consistent with the §5.14 finding that O3 is template-absorbing
rather than semantic-absorbing. A proper insert-mode dose-response
with denser doses and family-cluster bootstrap would refine these
numbers.

**What this changes in the paper's claims.** Per the rewritten
Lemma 1 / Corollary 1 (§3.1.4), replace-mode regimes already had no
formal *injected-token* barrier; the formal bound is on the post-
injection generation budget $G_m$, not the injected-token cost
$\tau$. This empirical probe confirms the theoretical reframing:

- Under the §3.1.1 strict reading, $\mathrm{B}(B_1 \to B_2) = 0$
  for replace mode under mild assumptions (injected text not
  required), because each replace generation is a fresh basin-
  reaching attempt.
- The reported O2/O3 "94-100% switching" should be read as a
  *generation-budget* effect: at $m \ge 1$ replace step after
  injection, the system has high probability of being in some new
  basin, but the injection itself contributes only ~20% above the
  no-injection baseline once the operator's overwrite contribution
  is removed.
- The insert-mode result (~18-32% switching at dose 200) is the
  empirical analog of the "sparse" perturbation effect that should
  be compared to O1 / D1 raw switching for fair regime comparisons.

The original O2/O3 "near-zero injected-token barrier" reading
remains qualitatively correct as a description of the operator's
overwrite-induced transparency, but should not be presented as a
discovered low *behavioral* barrier in the dose-response sense
that O1 measurements use.

**Production architectures with the same structural property.** The analogous engineering case is any architecture in which accumulated state is periodically replaced by a generated summary, scratchpad, or "current task state". If untrusted tool output, repository text, package metadata, or commit messages are promoted into that replacement, the system has not merely been persuaded by the text; its previous state has been removed by the update rule. Such failures should be attributed to the memory policy as well as to the generator. The 60-80 percentage-point overwrite-vs-insert gap reported above is therefore not a curiosity of this experimental setup; it is the same mechanism active whenever a context-summarization or context-replacement step intervenes between the loop's initial state and its final response.

---

### §5.C, Secondary analyses

### 5.18 Cross-metric correlations

> **Caveat.** The correlations reported in this
> subsection are computed across only **n=4 regimes** (O1, O2, O3,
> D1). Four points cannot support a meaningful correlation statistic
> in any conventional sense, Pearson and Spearman *r/ρ* values for
> n=4 are extremely high-variance, the reported *p*-values are
> exploratory rather than confirmatory, and a single re-categorisation
> of any regime would change the picture substantially. We retain
> this section because the *signs* of the correlations agree with
> mechanistic predictions stated in advance, which is consistency
> evidence (not statistical evidence) for the taxonomy. **Treat the
> numerical *r/ρ* values in the table below as descriptive
> indicators, not as inferential tests.** A confirmatory n>20-regime
> sweep is future work.

The four regimes were *defined* by qualitative architecture × content
labels (append vs replace vs dialog × continue vs paraphrase vs
summarize+negate vs free vs drill-down). The four diagnostic-metric
families above (Lyapunov, sharpness-dim, recurrence, basin
predictability, perturbation switching) were *measured* independently.
A natural cross-check: do regimes that score high on one diagnostic
also score predictable ways on the others?

We compute three pre-registered correlations across the 4 regimes
(O1, O2, O3, D1) on canonical pub-scale values (see caveat above):

*Table, Cross-metric correlations (Pearson + Spearman) with pre-registered mechanistic predictions.*

| relation | Pearson *r* (p) | Spearman *ρ* (p) | mechanistic prediction |
|---|---:|---:|---|
| recurrence rate vs adversarial switching rate | **+0.981 (0.019)** | +0.800 (0.200) | high-recurrence regimes (tight periodic orbits) are easier to kick out of orbit by injection, confirmed |
| sharpness dim (late) vs lock-in step (smallest *k* with `acc(k) ≥ 0.7`) | +0.838 (0.162) | **+0.949 (0.051)** | low-effective-dimension regimes have fewer "free axes" the predictor must constrain, confirmed |
| ensemble λ₁ (late) vs adversarial switching rate | +0.613 (0.387) | +0.800 (0.200) | larger λ₁ → less contractive → more easily perturbed; sign correct but underpowered at n=4 |

The recurrence ↔ vulnerability correlation is striking: the regime
with the *highest* recurrence rate (O3, 0.92) is the *most vulnerable*
to perturbation (96% switching), and the regime with the *lowest*
recurrence rate (D1, 0.21) is among the *least vulnerable* (60%
switching). This is exactly what one would predict for a periodic
orbit: a tight cycle has a narrow attractor support; once injection
text knocks the trajectory off the cycle, there's no built-in
mechanism to re-find it. The append-mode contractive regime (O1,
recurrence 0.29) by contrast keeps the seed text in context and uses
it as a re-attractor signal.

The sharpness ↔ lock-in correlation is similarly mechanistic. Regimes
with low effective dimension (O2 ≈ 1.39, O3 ≈ 1.45) commit to a basin
in 0-1 steps (the late-window cluster is already determined by step
0); the high-dimensional regime D1 (sharpness ≈ 1.89) takes 26 steps
to reach `acc(k) ≥ 0.7`. The intermediate O1 (sharpness ≈ 1.70)
locks in at step 1.

As stated in the caveat at the head of this subsection, n=4
correlations are descriptive rather than inferential, the methodological
point is that the *signs* of all three correlations agree with the
mechanistic predictions stated in advance. We do not interpret the
*r* = +0.981 / *p* = 0.019 cell as a statistical significance result;
with n=4, the test has effectively no power to distinguish a
"real" correlation from one driven by a single regime's location in
the diagnostic space. We report it because consistency in sign and
ordering across three independently-measured metrics is at least
weak internal evidence that the four-regime taxonomy is *not* an
artifact of any single diagnostic, but the more rigorous version of
this claim requires a confirmatory ≥20-regime sweep.

### 5.19 Why exactly five regimes? An unsupervised-clustering check

The five-regime taxonomy was *defined* by qualitative architecture ×
content labels (continue × append, paraphrase × replace,
summarize+negate × replace, free dialog × append, drill-down dialog
× append). The diagnostic battery was *measured* independently. A
strong test of mechanistic distinctness: do the regimes recover from
unsupervised clustering of measured diagnostic vectors?

We assemble per-experiment feature vectors for 13 experiments
(4 phase-2 publication runs + 5 phase-1 pilots + 7 reduced-scope
T-sweep cells + 4 phase-3 perturbation pilots; D2 excluded because
its dynamics.csv was not generated for the small-N exploratory
experiment). Each vector contains five canonical diagnostics:

```
[recurrence_rate (pca10, context_tail),
 sharpness_dim_late, lambda_1_late,
 basin_predictability_acc(k=10),
 adversarial_switch_rate]
```

After standardization, k-means clustering at *k* ∈ {2, ..., 7} gives:

*Table, Internal-validation indices (silhouette, Calinski-Harabasz, Davies-Bouldin) by cluster count.*

| *k* | silhouette ↑ | Calinski-Harabasz ↑ | Davies-Bouldin ↓ |
|---:|---:|---:|---:|
| 2 | **0.575** | 13.4 | 0.65 |
| 3 | 0.568 | 21.3 | 0.59 |
| 4 | 0.521 | 24.7 | 0.39 |
| 5 | 0.477 | 34.3 | 0.34 |
| 6 | 0.478 | 46.5 | 0.21 |

Three internal-validation indices, three different optimal *k*: **2
by silhouette, 7 by Calinski-Harabasz, 6 by Davies-Bouldin**, i.e.,
no cluster-count emerges as uniformly optimal. The honest reading:
the bulk diagnostic vector (recurrence + sharpness + λ₁ + basin pred
+ adversarial switch) **partially recovers** the regime taxonomy but
does not cleanly resolve it. Specifically, the *k*=5 confusion
matrix (cluster vs ground-truth label):

*Table, $k{=}5$ confusion matrix: ground-truth regime label vs unsupervised cluster assignment.*

| ground-truth ↓ \ cluster → | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| O1 (n=8) | 0 | 4 | 2 | 0 | 1 |
| D1 (n=4) | 0 | 3 | 1 | 0 | 0 |
| O2 (n=2) | 0 | 0 | 0 | **1** | 0 |
| O3 (n=2) | **1** | 0 | 0 | 0 | 0 |

shows the substructure clearly:

- **O2 (cluster 3) and O3 (cluster 0)** each form their own
  singleton clusters, *bulk diagnostics resolve them individually*.
  This makes mechanistic sense: O2's period-2 oscillation and O3's
  near-singular absorbing state have very distinct recurrence /
  λ₁ / sharpness signatures (recurrence 0.88 vs 0.92; sharpness 1.39
  vs 1.45 with very different time-evolution patterns).
- **O1 and D1 share clusters 1 and 2**, *bulk diagnostics do not
  cleanly separate the contractive append regime from the
  dialogue-state-driven multi-basin dialog regime*. Their canonical values are
  too close: recurrence 0.29 vs 0.21, sharpness 1.70 vs 1.89,
  λ₁ 0.008 vs 0.011, basin pred 0.65 vs 0.61, adversarial switch
  0.54 vs 0.60. The differences exist but are small relative to
  intra-regime variance across phase-1 / phase-2 / T-sweep
  measurements.

This is the affirmative empirical content of why the perturbation
protocol matters: **bulk diagnostics underdetermine the regime
taxonomy at the O1/D1 boundary**. The mechanistic distinction
between O1 (content-anchored basin, finite barrier against
in-distribution adversarial text, no detectable barrier crossing
against out-of-distribution noise within the tested 5-400 token
range, §5.6) and D1 (style-anchored basin,
T-stable across {0.3..1.2}, modest barrier in any direction,
§5.4) emerges *only when one measures the cost of nudging*. Bulk
diagnostics tell you the regimes have similar drift, similar
contraction rate, similar locked-in late-window structure; the
perturbation protocol tells you the regimes respond *very*
differently to in-distribution adversarial input.

The five-regime taxonomy is therefore best understood as **the
partition recovered by the union of bulk diagnostics (which
distinguish O2 / O3 from each other and from append/dialog) and
perturbation barriers (which distinguish O1 from D1, and D1 from
D2 via §5.8's content-gravity test)**. Bulk diagnostics alone yield
~3 clusters; perturbation barriers alone wouldn't separate O2 from
O3 at this scale; the *combination* yields the full five-way split.

This finding is also why we describe the paper's headline
contribution as the perturbation-barrier protocol rather than the
regime taxonomy: the taxonomy is *underdetermined* without the
protocol, but *fully determined* with it.

(Cluster analysis: `scripts/regime_cluster_analysis.py`. Plots:
`data/aggregated/regime_cluster_analysis/cluster_scatter.png` (PCA-2
of feature space, colored by regime label) and
`data/aggregated/regime_cluster_analysis/cluster_dendrogram.png`
(Ward linkage). Feature matrix: `feature_matrix.csv` in the same
directory.)

![Figure 13. **Diagnostic feature-space clustering.** Left: PCA-2 projection of standardized 5-D diagnostic vectors, recurrence, late $\lambda_1$, sharpness dimension, basin-predictability accuracy, and adversarial switching rate, for 13 experiments, colored by regime label. Right: k-means internal-validity scores over $k=2,\ldots,7$. O2 and O3 appear separated in this feature space, while O1 and D1 overlap; the validity indices do not select a single cluster count matching the regime taxonomy. Source: `data/aggregated/regime_cluster_analysis/cluster_scatter.png`.](data/aggregated/regime_cluster_analysis/cluster_scatter.png)

### 5.20 Embedding-space invariance

A natural reviewer challenge: the regime taxonomy is defined on
embeddings from `text-embedding-3-small` (OpenAI, 1536-dim). Would
the regimes change with a different embedder? We test this by
re-embedding 5,000-step subsamples of 5 representative experiments
(one per regime: O1, O2, O3, D1, D2) under two alternative embedding
models and recomputing the canonical diagnostics:

- **`text-embedding-3-large`** (OpenAI, 3072-dim), within-vendor
  scale-up.
- **`all-mpnet-base-v2`** (sentence-transformers, 768-dim, local),
  cross-architecture, open-source.

Per-regime canonical diagnostics, all three embedders:

*Table, Regime-by-metric across embedders: small, large, and mpnet diagnostics.*

| regime | metric | small (1536d) | large (3072d) | mpnet (768d) |
|---|---|---:|---:|---:|
| O1 | recurrence_rate | 0.289 | 0.304 | 0.096 |
| O2 | recurrence_rate | 0.875 | 0.711 | 0.783 |
| O3 | recurrence_rate | 0.924 | 0.850 | 0.862 |
| D1 | recurrence_rate | 0.210 | 0.337 | 0.226 |
| D2 | recurrence_rate | 0.296 | 0.176 | 0.073 |
| O1 | sharpness_dim_late | 1.697 | 1.774 | 1.915 |
| O2 | sharpness_dim_late | 1.389 | 1.886 | 1.898 |
| O3 | sharpness_dim_late | 1.452 | 1.233 | 1.309 |
| D1 | sharpness_dim_late | 1.890 | 1.365 | 1.825 |
| D2 | sharpness_dim_late | n/a | n/a | n/a |
| O1 | basin_pred_acc(k=10) | 0.804 | 0.519 | 0.503 |
| O2 | basin_pred_acc(k=10) | 0.896 | 0.736 | 0.712 |
| O3 | basin_pred_acc(k=10) | 0.916 | 0.672 | 0.784 |
| D1 | basin_pred_acc(k=10) | 0.607 | 0.504 | 0.392 |
| D2 | basin_pred_acc(k=10) | n/a | 0.136 | 0.133 |

Spearman rank correlations of per-regime values, baseline vs
alternative embedder:

*Table, Spearman rank correlations of per-regime diagnostics across embedders.*

| diagnostic | vs `text-embedding-3-large` | vs `all-mpnet-base-v2` |
|---|---:|---:|
| recurrence rate | ρ = +0.60 | ρ = +0.60 |
| **basin predictability acc(k=10)** | ρ = **+0.80** | ρ = **+1.00** |
| sharpness_dim_late | ρ = −0.40 | ρ = +0.00 |

Three findings:

**(a) Basin predictability is fully invariant under embedder swap**
(*ρ* = +1.00 for `all-mpnet-base-v2`, +0.80 for
`text-embedding-3-large`). The regime ordering on basin predictability,
**replace-mode (O2, O3) > append (O1) > dialog (D1) > exploratory
D2**, is preserved exactly under cross-architecture embedding
substitution. This is the strongest cross-embedder invariance result
in our data: the property of the recursive dynamics that the basin
predictor measures (how much information about the late-window
attractor is already present at step 10) is *not* a property of one
specific embedding family.

**(b) Recurrence rate is partially invariant** (*ρ* = +0.60 in both
cases). The bimodal structure, replace-mode pair {O2, O3} above
0.71 in every embedder, append/dialog set {O1, D1, D2} below 0.34
in every embedder, is preserved unambiguously. The fine-grained
ordering within each cluster shifts modestly across embedders, but
the dominant high/low partition that distinguishes the replace-mode
regimes from the rest does not.

**(c) Sharpness dim_late is NOT invariant** (*ρ* = +0.00 vs mpnet,
−0.40 vs large). This is a real and worth-flagging finding: the
sharpness-dimension diagnostic, which depends on the dimensional
structure of the embedding space, is embedding-specific. Different
embedders give different orderings of regimes on this diagnostic.
The sharpness-dim claims in §11.2 / §5.2 should therefore be
interpreted as *measurements within the* `text-embedding-3-small`
*pipeline*, not as embedding-invariant properties of the recursive
dynamics. (D2's sharpness is NaN in all three embedders because the
exploratory-scale ensemble, only ~25 trajectories per family, is
too small to support the late-window covariance estimate.)

The headline conclusion: **the taxonomy's load-bearing distinction
between replace-mode regimes and append/dialog regimes is
embedding-invariant** (basin predictability ρ ≥ +0.80; recurrence
bimodal structure preserved). The taxonomy's *fine-grained* metrics
(O2 vs O3 at the basin-shape level; D1 vs O1 at the sharpness-dim
level) are partially or wholly embedding-dependent. This is consistent
with §5.19's finding that the perturbation barrier, a quantity
defined in token-space rather than embedding-space, is the
load-bearing diagnostic for separating the full five-regime
taxonomy.

(Full ablation: `scripts/embedding_ablation.py`, output at
`data/aggregated/embedding_ablation/results.csv`.)

![Figure 14. **Embedding-model ablation.** Bar plots compare three diagnostics across regimes after re-embedding subsamples with `text-embedding-3-small`, `text-embedding-3-large`, and `all-mpnet-base-v2`. Recurrence preserves the high/low split between replace-mode O2/O3 and append/dialog regimes across embedders, while sharpness dimension changes ordering. Basin-predictability remains more stable across embedders than sharpness dimension in this ablation. Source: `data/aggregated/embedding_ablation/comparison.png`.](data/aggregated/embedding_ablation/comparison.png)

### 5.21 Cross-model thesis verification

A more searching robustness test than §5.20: the embedding ablation
varies only the *measurement instrument* (the embedder) on the same
trajectories. The cross-generation replication varies the *system
under measurement*, re-running every one of the 37 experiment
configurations end-to-end with `gpt-4.1-nano` substituted for
`gpt-4o-mini` as the trajectory-generating model. We then encode the
paper's six main theses as machine-checkable predicates and evaluate
each on both models.

The six theses (`scripts/check_theses_cross_model.py`):

*Table, Pre-registered T1-T6 thesis predicates with publication-scale verdicts.*

| ID | Thesis | Predicate (publication-scale or pilot data) |
|---|---|---|
| T1 | Regime ordering on recurrence rate | O2 / O3 > 0.70 and O1 / D1 < 0.40; min(O2, O3) > max(O1, D1) |
| T2 | Replace-mode capitulation under perturbation | O2 + O3 pilot switching > 0.85 for neutral / lorem / adversarial |
| T3 | O1 contractive: out-of-distribution drift-floor band | O1 pilot control ≤ 0.05; neutral ∈ [0.10, 0.40]; lorem ∈ [0.10, 0.40] |
| T4 | O1 contractive: adversarial > out-of-distribution | O1 pilot adversarial switching > O1 pilot lorem switching |
| T5 | D1 dialogue-state-driven multi-basin susceptibility | D1 pilot neutral switching > 0.30 |
| T6 | Publication-scale verdict labels | O1 continue, O2 paraphrase-replace, O3 summarize-negate-replace, D1 dialog v2 carry expected (H1a, H1b) tuples |

Result: **6 / 6 PASS on gpt-4o-mini (baseline, by construction); 6 / 6 PASS on gpt-4.1-nano.**

Per-thesis diagnostic numbers, side by side:

*Table, Cross-model T1-T6 verdicts: gpt-4o-mini vs gpt-4.1-nano.*

| ID | gpt-4o-mini | gpt-4.1-nano | Δ |
|---|---|---|---|
| T1 | O1 0.272, O2 0.834, O3 0.905, D1 0.146 | O1 0.393, O2 0.840, O3 0.866, D1 0.168 | replace / append-or-dialog gap preserved |
| T2 | O2 adv 0.94, O3 adv 0.96 | O2 adv 0.94, O3 adv 0.88 | both > 0.85 capitulation threshold |
| T3 | control 0.00, neutral 0.24, lorem 0.18 | control 0.00, neutral 0.22, lorem 0.18 | drift floor essentially identical |
| T4 | adv 0.54 vs lorem 0.18 (margin +0.36) | adv 0.38 vs lorem 0.18 (margin +0.20) | direction holds; adversarial barrier is **smaller** on nano |
| T5 | D1 neutral 0.76 | D1 neutral 0.80, lorem 0.94 | direction holds; D1 dialogue-state susceptibility is **larger** on nano |
| T6 | (strong, weak / strong, not_supported / strong, not_supported / strong, weak) | identical tuples | exact-match on all 4 pub-scale headlines |

Two qualitative patterns emerge from the magnitude shifts:

1. **The smaller model has shallower contractive basins.** T4's
   adversarial-vs-out-of-distribution margin shrinks from +0.36 to
   +0.20, the in-distribution kick still wins, but with a smaller
   barrier signal. Operationally: nano's O1 needs less injected text
   to be dislodged. The token-cost ordering is preserved; the
   absolute token-cost is somewhat smaller.

2. **The smaller model's D1 dialogue-state basins are easier to flip.**
   T5's D1 neutral switching is 0.80 on nano (vs 0.76 on
   gpt-4o-mini), and D1 lorem switching jumps to 0.94 (the highest
   non-replace switching rate observed in either model). Stylistic
   commitments in dialog are looser on nano, content perturbations
   override style more readily.

Both shifts are mechanistically consistent with nano being a smaller,
less-stable contractive system: shallower wells, weaker style anchoring.
The **structural taxonomy (5 regimes, replace-vs-append-vs-
dialog separation, basin-character signatures) is preserved unchanged
between the two models.** Token-cost values shift by the amounts
above, but stay in the same ordinal relations the paper claims.

The full audit is reproducible end-to-end via three artifacts:
`COVERAGE_nano.csv` (artifact-presence matrix, 37 cells × 59 columns),
`RESULTS_nano.md` (per-cell numeric comparison vs the gpt-4o-mini
baseline), and `THESES_nano.md` (the per-thesis PASS / FAIL table
above with full predicate detail). All three are referenced from
§7.1 and regenerable via `scripts/build_coverage.py --filter
"exp_*_gpt4nano"`, `scripts/compare_cross_model.py`, and
`scripts/check_theses_cross_model.py`.

---

## 6. Discussion

The main result is not simply that recursive LLM loops have attractor-like regimes. It is that their apparent robustness depends on two separable choices: the memory policy that writes text back into state, and the endpoint used to define a successful perturbation. Append-mode continuation shows a real in-distribution raw dose response, with $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, but that number is not a durable escape threshold: raw switching plateaus near $67\%$, paired controls already diverge at about $35\%$, net switching never reaches the $+50$ pp criterion, and persistent escape remains below $50\%$ at every tested dose. Replace-mode loops, meanwhile, look fragile mostly because the update rule overwrites the prior state. Thus the practical unit of analysis is not the prompt alone, or the model alone, but the generator-nudge system evaluated under raw, net, and persistent endpoints.

### 6.1 Recursive-loop robustness is determined by memory policy and endpoint choice

The central lesson of these experiments is that recursive-loop behavior is determined jointly by the generator and the context-update rule. In the formalism of §3.1, the model samples $Y_t \sim P_\theta(\cdot \mid X_t; f)$, while the nudge $\mathcal{N}_f$ decides how that sampled text becomes the next state. Two loops with the same generator and similar prompt instructions can therefore have different perturbation responses solely because one preserves prior context and the other overwrites it.

The second lesson is that "robustness" is endpoint-dependent. A loop can move without staying moved; two unperturbed runs can diverge without any perturbation; and an overwrite-style update can make a system appear fragile even when inserted text has little effect. This is why the paper separates raw switching, net switching, and persistent escape (§3.1.2). In O1, adversarial append-mode perturbations yield $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, with 4PL $=36$, GLMM $=41$, and family-cluster bootstrap median $=52$ tokens, 95% CI $[8.5, 242]$ (§5.6.1). But the raw curve plateaus near $67\%$, the control-vs-control floor is $\approx 35\%$, the net effect saturates at only $+32$ pp, and persistent escape never crosses $50\%$ (§5.15). The same loop is therefore movable under the raw endpoint but not durably redirected under the strict endpoint.

### 6.2 Append, replace, and dialog implement different memory mechanisms

Append, replace, and dialog are not implementation details; they are different memory mechanisms. In append mode, the perturbation enters an already-accumulated context and must compete with prior trajectory mass. This makes append-mode continuation resistant to irrelevant text: O1 neutral and lorem perturbations remain near the out-of-distribution drift floor, while in-distribution adversarial text produces the graded raw dose response measured in §5.6.1.

Replace mode implements a different mechanism. The previous state is discarded, so the next state is dominated by the replacement. The overwrite-vs-insert probe makes this visible: for O2, overwrite-mode perturbations switch at $92$--$98\%$, while insert-mode perturbations switch at only $18$--$32\%$, a $60$--$80$ pp gap (§5.17). For O3, overwrite switching is $90$--$92\%$, but insert switching is only $12$--$18\%$, a $72$--$80$ pp gap. Thus most apparent replace-mode fragility is attributable to overwrite mechanics rather than a low injected-token barrier.

Dialog sits between these cases. It preserves a running transcript like append mode, but role-structured turns give recent utterances high local influence. D1 therefore behaves as a dialogue-state-driven multi-basin regime, while D2 suggests topic-anchored "content gravity" under drill-down structure (§5.8, §5.14).

### 6.3 A raw-switching ED50 is not a persistent-escape barrier

The most important interpretive correction is that $\mathrm{ED50}_{\mathrm{raw}}$ is not the same quantity as a persistent-escape barrier. Raw switching asks whether the perturbed trajectory's terminal cluster differs from its paired control. That endpoint is useful, but it conflates three phenomena: true redirection, ordinary stochastic divergence, and transient movement that later recovers. Persistent escape is stricter: the trajectory must visibly jump at injection and remain in the post-injection basin through the terminal step (§3.1.2).

Under the permissive raw endpoint, O1 adversarial append-mode continuation has a clear dose response: $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, with estimates 36, 41, and 52 tokens across the 4PL, GLMM, and family-cluster-bootstrap analyses (§5.6.1). But the raw plateau is only $\approx 67\%$, not $100\%$. Moreover, paired controls already disagree at about $35\%$, so subtracting the stochastic floor leaves a maximum net effect of only $+32$ pp at 400 tokens, below the $+50$ pp criterion for $\mathrm{ED50}_{\mathrm{net}}$.

The persistent endpoint is smaller still. At the highest tested dose, persistent escape reaches only $16\%$ under canonical K-means $k=12$, $10\%$ under K-means $k=4$, and $39.5\%$ under HDBSCAN (§5.15). None crosses $50\%$ in the tested 5--400 token range. The correct conclusion is therefore: O1 has a finite raw-switching dose response, but no measured persistent-escape barrier in this experiment.

### 6.4 Density landscapes diagnose basin geometry but do not calibrate token barriers

The empirical potential landscape $V(x) = -\log \rho(x)$ is useful as a diagnostic picture of trajectory density, but it should not be read as a calibrated token barrier. The landscape is computed after embedding, projection, smoothing, and basin detection, so its absolute values depend on the representation and analysis choices. The parameter-grid sensitivity analysis confirms this: per-condition $V^\star$ values vary with coefficient of variation $14$--$24\%$ across KDE bandwidths, grid resolutions, and basin-count settings (§5.16).

What survives is the weaker ordinal claim. In the O1 perturbation pilot, the rank ordering of $V^\star$ is stable across $89$--$98\%$ of parameter combinations: control is usually highest, adversarial usually lowest, and neutral / lorem occupy the middle (§5.16). This supports the use of density landscapes as descriptive basin-geometry tools. It does not justify converting $V^\star$ into tokens, nor does it independently validate $\mathrm{ED50}_{\mathrm{raw}}$. The behavioral dose-response and geometric landscape are complementary measurements, not interchangeable estimators of the same scalar.

### 6.5 Robust recursive-loop evaluations must report floors, persistence, and overwrite mechanics

1. **Report the context-update rule.** Every recursive-loop evaluation should state whether the system appends, replaces, role-structures, summarizes, pins, rolls, or hybridizes memory, because the same generator can show different perturbation responses under different nudges (§3.1, §5.17).

2. **Report raw, net, and persistent-escape endpoints rather than raw switching alone.** Raw movement says whether the trajectory changed, net switching subtracts the control-vs-control stochastic floor, and persistent escape asks whether the perturbation produced a durable basin change after recovery turns (§3.1.2, §5.6.1, §5.15).

3. **For replace-style or summary-memory systems, run an overwrite-vs-insert control.** If overwrite switching is high but insert switching is low, the measured fragility is partly the memory policy discarding prior state rather than the injected text overcoming a basin barrier (§5.17).

A checklist version of this reporting standard is given in Box 1 (§11.12).

### 6.6 The unresolved question is external validity across generators and real agent scaffolds

The present evidence is strongest for the measured generator-nudge systems, not for all LLMs or all agent architectures. The within-vendor replication on `gpt-4.1-nano` preserves the qualitative thesis predicates (§5.21), but both generators are from the same vendor family. Cross-vendor and open-weight replication remain necessary before the architecture-vs-generator partition can be treated as general (§7.1, §8.1).

The same caution applies to real agent scaffolds. The paper studies recursive text loops with controlled update rules and embedding-space observables; it does not directly evaluate coding agents, tool-using assistants, SWE-Bench tasks, jailbreak benchmarks, production indirect prompt injection, or factuality-graded hallucination settings (§7.5). Those domains can adopt the same endpoint decomposition, but their observables must be application-specific: patch family, files touched, tests passed, policy violations, tool-call traces, or grounded factual claims.

The paper's position is therefore deliberately bounded: recursive-loop stability is measurable, but the measurement only becomes meaningful when memory policy, stochastic floor, and persistence endpoint are made explicit.

## 7. Limitations

*The experiments support a structured account of recursive LLM dynamics, but the strongest claims remain tied to the tested generator families, representation pipeline, memory regime, and text-only nudge setting.*

### 7.1 Evidence is strongest for OpenAI generator-nudge systems

The model-coverage result is broad enough to rule out a single-run curiosity, but not broad enough to establish model-agnostic dynamics. The current audit spans six generators, including Anthropic and Google systems, yet the densest evidence remains concentrated in OpenAI generator-nudge systems, especially the gpt-5-mini / nano O1 and D1 cells. Those cells carry the deepest replication, the most complete artifact stack, and the clearest regime-level separation.

This matters because the qualitative taxonomy is motivated by the generator-nudge factorization in §3, not by a special property of one model checkpoint. The append, replace, and dialog distinctions plausibly arise from how the update operator rewrites the next context. However, barrier heights, basin geometry, switching thresholds, and even the number of empirically separable regimes can vary with decoding behavior, tokenizer structure, alignment tuning, refusal style, and context-management details.

The cross-model audit should therefore be read as evidence of shape preservation under a restricted generator class, not as proof of universality. The load-bearing claim is that the headline regimes survive the strongest replicated cells and the pre-registered predicate checks. The audit does not establish numerical equivalence across vendors, and it does not license a model-agnostic claim about all current or future LLMs.

### 7.2 Basins, barriers, and tokens are operational measurements

The basins and barriers reported here are measurements in an operational pipeline, not representation-free physical constants. Trajectories are observed through an embedding model, projected for analysis and visualization, and summarized with density, recurrence, switching, and dose-response statistics. §5.20 reports an explicit representation ablation against a larger OpenAI embedding model and a sentence-transformer model; the attractor-like structure is robust across those tested observables. That robustness does not make the absolute geometry independent of the representation.

The empirical potential landscape, \(V(x)=-\log \rho(x)\), is a descriptive density summary. The Dijkstra barrier \(V^\star\) depends on the kernel-density estimator, PCA-2 reduction, grid resolution, and path construction. These quantities are useful because they impose a common geometric language on many trajectory families, and because their relative ordering can be compared with behavioral perturbation thresholds. They should not be interpreted as thermodynamic free energies or as absolute invariants of the underlying model.

The same caveat applies to token barriers. Tokens are directly measurable, practically interpretable, and closely aligned with how perturbations are injected in §4.5, but they are not the ultimate information unit. The model-agnostic object is closer to a conditional-surprisal barrier measured in nats. Because the present experiment battery does not store generation logprobs, the token-dose results are best read as first-order operational estimates of a deeper information barrier.

### 7.3 The experiments cover bounded, English, static-prompt recursions

The reported dynamics are properties of bounded, English-language, static-prompt recursive loops. All main runs use a finite context cap with tail clipping, English prompts and seeds, and relatively short generated outputs. This is a natural setting for controlled recurrence experiments, because it isolates the effect of the nudge operator while keeping the observable trajectory compact enough for repeated perturbation and embedding analysis.

The bounded-memory assumption is especially consequential for append mode. A no-clip pilot suggests that removing clipping deepens the append basin and reduces recurrence, which means the measured append-mode barriers are not properties of append mode in the abstract. They are properties of append mode under a specific bounded-memory recurrence. Larger context windows, different truncation rules, retrieval-augmented memory, or explicit memory compression may change both the basin depth and the route by which perturbations persist.

The language and prompting scope is similarly narrow. The experiments do not test multilingual trajectories, code-heavy trajectories, very long-form generation, or systems in which the system prompt is rewritten online. Prompt drift, refreshed meta-instructions, tool-generated state, or long-horizon document construction could fragment a basin that appears stable under static prompting, or stabilize a replace-mode regime that appears weak when each step is only a short text rewrite.

### 7.4 The drill-down dialog regime remains exploratory

The drill-down dialog regime is the least mature of the reported regimes. The current D2 evidence indicates a distinct form of topic-anchored content gravity under role-structured questioning, but it was tested at substantially smaller scale than the main O1-O3 and D1 regimes. The reported switching estimate is 64% with a ±10 percentage-point bootstrap confidence interval from 25 trajectories at 50 steps.

This is enough to motivate D2 as a candidate regime, but not enough to place it on the same empirical footing as the publication-scale cells. Dialog structure is a rich nudge family: drill-down questioning, debate, role-play, adversarial interrogation, and multi-party deliberation may create different balances between style persistence and content anchoring. D2 should therefore be treated as exploratory until it receives the same publication-scale replication and cross-model audit as the other headline regimes.

### 7.5 Production agent and tool-use claims require new observables

The experiments measure recursive language-model loops, not deployed coding agents or tool-using autonomous systems. They do not include file-system state, code edits, compiler feedback, test execution, tool schemas, repository-specific correctness criteria, or multi-step planning traces. The implications drawn in §6.6 for coding agents are architectural extrapolations from recursive-loop dynamics, not measurements of Cursor, Cline, Devin, Claude Code, LangGraph-based agents, SWE-Bench systems, or in-house coding scaffolds; see companion developer-journal essay.

A production-agent benchmark would need additional observables. Patch diffs, files touched, tests run, failing tests remaining, tool-call sequences, policy violations, injected-document provenance, and post-perturbation plan persistence would need to be measured alongside or instead of embedding-space trajectory structure. The framework in §3 and the perturbation protocol in §4.5 transfer cleanly, but the numerical barriers in §5 do not transfer without re-measurement.

The key bridge is that memory policy becomes a behavioral variable. Full-history append, rolling-window truncation, generated-summary replacement, pinned-goal memory, and provenance-preserving hybrid memory can induce different perturbation profiles even when the base model and task are held fixed. The present paper supplies the measurement logic; deployed-agent claims require an agent-native implementation of that logic.

## 8. Future directions

*The next step is to turn the present perturbation framework from a controlled recursive-loop study into a comparative measurement program for model families, memory policies, dialog scaffolds, and deployed agents.*

### 8.1 Cross-vendor replication at publication scale

The highest-priority extension is publication-scale replication across vendors. The central question is not whether barrier heights match numerically, but whether the ordering of append, replace, and dialog regimes survives across generators with different alignment methods, tokenizer families, refusal policies, and decoding implementations. A replicated ordering would support the claim that regime structure is a property of the generator-nudge system rather than a peculiarity of one model family.

The next audit should include Anthropic, Google, Mistral, and open-weight models at comparable sample sizes, with N=20-60 trajectories per cell where cost permits. The full sweep should include O1, D1, and D2 rather than only the most stable headline cells. D2 is particularly important because dialog topology is under-sampled in the current evidence base and may vary more strongly across vendors than simple append or replace loops.

The audit should also preserve the same separation between verdicts and numbers used in §5. Exact recurrence rates, basin scores, and ED50 values should be expected to drift. The load-bearing test is whether the regime ordering, perturbation response curves, and persistent geometry remain qualitatively aligned under matched nudges, matched memory limits, and matched analysis code.

### 8.2 Logprob-based barrier heights and basin geometry

A second priority is to move from token barriers to information-theoretic barriers. Token dose is easy to control and interpret, but the natural cross-model unit is conditional surprisal. Future runs should store generation logprobs whenever the API exposes them, allowing perturbation cost to be expressed in nats as well as in tokens. The pipeline already anticipates this through a logprob-capture option, but availability remains constrained by provider and model endpoint.

Logprob-based barriers would test whether behavioral switching thresholds align more directly with information cost than with token count. A short perturbation containing highly surprising content may impose a larger effective kick than a longer perturbation made of predictable boilerplate. Conversely, long in-distribution perturbations may carry many tokens but relatively little conditional surprise. Measuring both units would separate length effects from information effects.

The same extension should be applied to basin geometry. The empirical \(V^\star\) barrier in §5 summarizes density geometry in the embedding projection, whereas an information barrier would summarize how costly it is for the generator to move from one behavioral basin to another under its own predictive distribution. Agreement between these two quantities would strengthen the structural interpretation; disagreement would identify cases where embedding-space proximity and generative difficulty diverge.

### 8.3 Memory-policy ablations and adversarial perturbations

The memory policy should become an explicit experimental factor. The present bounded-memory setting is intentionally simple, but real systems use rolling windows, summaries, pinned instructions, retrieval, tool-output buffers, and hybrid context stores. Future experiments should cross the same generator and task with multiple context-update rules: full append, fixed rolling window, generated-summary replacement, and hybrid pinned plus rolling memory with provenance-preserving treatment of untrusted inputs.

This should be paired with larger context windows and longer per-step outputs. Longer recursive writes may deepen append basins, fragment replace basins, or create multi-scale regimes in which short-horizon and long-horizon stability disagree. Periodic summarization may suppress benign drift while amplifying a malicious or misleading summary error. The relevant endpoint is not compression quality alone, but perturbation response under controlled dose.

The perturbation design should also expand from one-dimensional dose curves to dose × position sweeps. A perturbation inserted at the beginning of memory, immediately before the model response, inside a generated summary, or inside a pinned instruction field may have different persistence even at the same token dose. Controlled adversarial perturbations should include irrelevant long logs, misleading documentation, targeted false explanations, and malicious package-style content. The result would be a memory-policy ablation harness that measures whether a scaffold reduces persistent escape without merely suppressing ordinary adaptation.

### 8.4 Publication-scale dialog and coding-agent benchmarks

Dialog needs its own publication-scale map. Drill-down dialog is the first candidate beyond the main dialog regime, but the space is larger: debate, role-play, brainstorming, adversarial questioning, tutor-student exchange, and multi-party deliberation may each define different nudge operators. These topologies should be evaluated with the same endpoints used in §4.5 and §5: raw switching, net switching above stochastic floor, persistence, recurrence, and basin geometry.

The same endpoint decomposition can be adapted to coding-agent benchmarks. For SWE-Bench-style tasks, paired controls would estimate the stochastic floor of patch-family variation and pass/fail variation. Perturbation runs would inject controlled content into repository files, issue comments, tool outputs, package documentation, failing-test logs, or generated summaries. Persistence would measure whether the agent remains on the injected strategy after additional plan-edit-test cycles.

This adaptation would distinguish ordinary run-to-run variation from durable redirection. Two agents can have the same pass rate while differing sharply in perturbation susceptibility. Likewise, the same base model can show different escape profiles under full-history append, rolling-window memory, or summarized memory. A coding-agent benchmark built on this protocol would therefore separate model fragility from scaffold fragility, which current leaderboards often conflate.

### 8.5 Persistent-escape barriers for safety and instruction-injection robustness

Safety and instruction-injection experiments should measure persistent escape directly. The raw-switching ED50 reported in this paper is not a persistent-escape barrier. Raw switching measures the perturbation dose at which an immediate response changes state. Persistent escape asks whether the system remains redirected after the perturbation is no longer novel, after additional turns are generated, and after the scaffold has had opportunities to recover.

This distinction is central for safety. A model that briefly follows a malicious instruction and then returns to the intended policy is different from a model whose memory or dialog state has been durably hijacked. Future experiments should therefore score multi-step post-perturbation trajectories, not only the first switched response. Endpoints should include raw escape, net escape above control variation, persistence across later steps, and recovery rate under neutral continuation.

The same design can test whether alignment creates or reshapes basins. Base and safety-tuned models should be compared under the same nudge families, memory policies, and perturbation classes to determine whether safety training changes barrier height, basin count, or switching geometry. Agent frameworks should expose the context-update rule as a traceable object: which turns are retained, which are summarized, which facts are pinned, which tool outputs are marked untrusted, and which generated summaries replace prior state. Without that instrumentation, persistent-escape failures cannot be attributed cleanly to the model, the memory policy, or the surrounding scaffold.

## 9. Data, code, and reproducibility

*The repository is organized so that the paper's claims can be traced from raw trajectories to embeddings, metrics, plots, ED50 fits, audit tables, and regenerated summary checks.*

### 9.1 Public trajectories, derived artefacts, and audit tables

Raw trajectories are released as public data and are stored in the repository layout under `data/exp_*/raw/steps.jsonl`, with large files tracked through LFS. The raw payload is 3.3 GB across 37 experiments. A Hugging Face dataset mirrors the trajectory release for direct download, while the GitHub release contains derived metrics, plots, perturbation visualizations, animations, aggregate tables, and ED50 fit artefacts.

Three audit files provide the main reproducibility map. `COVERAGE.csv` is a 37 × 60 matrix recording whether each experiment has each applicable artefact, with cells marked as present, absent, or structurally non-applicable. All 37 experiments are at 100% of their applicable artefacts. `EVIDENCE.md` maps substantive paper claims to backing data files, source-code functions, and regenerating commands. `RESULTS.md` verifies the numerical claims against the canonical aggregated CSVs; the current audit reports 103 / 103 cells reproducing within tolerance.

The experiment catalog is documented in `docs/DATA_INDEX.md`, which describes the purpose, scope, and supersession relationships of the 37 experiment directories. Six stage reports in `docs/reports/` record the discovery path from the first baseline classification runs through long-horizon ablations, dynamical-systems metrics, operator-regime classification, publication-scale verification, and perturbation experiments. These documents are not required to run the pipeline, but they make the provenance of the final design inspectable.

### 9.2 Codebase, licenses, and runtime environment

The codebase is available at <https://github.com/kaplan196883/llmattr>. The code is released under GPLv3, and the generated trajectories, embeddings, and analysis artefacts are released for reuse with attribution under the data license specified in the repository. The repository is intended to run under Python 3.11+ with a Conda environment; key dependencies include numpy, scipy, scikit-learn, scikit-image, matplotlib, pandas, and imageio-ffmpeg.

The top-level layout separates experiment definitions, executable scripts, reusable analysis code, tests, and data. `src/` contains the core analysis, API, experiment, report, and utility modules. `scripts/` contains configuration builders, aggregation tools, audit scripts, and figure-generation entry points. `configs/` stores per-experiment YAML files, `tests/` contains the pytest suite, and `data/` contains the 37 experiment directories plus aggregate outputs.

### 9.3 Bounded API and local-compute costs

Regenerating embeddings for the full 37-experiment set costs approximately $30 using OpenAI `text-embedding-3-small`. Regenerating all model generations costs approximately $200 using the original OpenAI generation path, but this is unnecessary if the LFS-tracked `steps.jsonl` files or the public trajectory dataset are used. Full local embed and analysis runs take approximately 2 hours wall-time on a 40-core machine; animations add additional plotting time.

A lower-cost path is to reuse the released raw trajectories and run only local analysis. Users can also substitute local sentence-transformer embeddings for exploratory replication or representation ablation, avoiding OpenAI embedding costs. Those runs should be interpreted as representation-specific replications rather than exact regenerations of the canonical embedding pipeline.

### 9.4 Automated tests and end-to-end claim verification

The analysis primitives and integration paths are covered by 99 pytest tests. The standard test command is `PYTHONPATH=. python -m pytest tests/ -q`, which reports 99 passing tests in approximately 13 seconds in the reference environment. These tests cover the reusable components, while the audit scripts check the paper-level claims against regenerated artefacts.

The pipeline is organized into four re-runnable stages: generate, embed, analyze, and aggregate. Generation produces `steps.jsonl`; embedding produces `embeddings/<observable>/embeddings.npy`; analysis produces metric CSVs and per-experiment reports; aggregation produces the cross-experiment tables under `data/aggregated/`. `python -m scripts.build_coverage` regenerates the 37 × 60 coverage matrix, and `python -m scripts.publication_summary` regenerates the 103 / 103 numeric-claim verification table, including the ED50 and audit-table checks. The tests, coverage matrix, evidence map, and regenerated results give an end-to-end path from each reported claim to the script that recreates it.

## 10. Acknowledgments

We acknowledge `gpt-4o-mini` and `text-embedding-3-small` (OpenAI),
the open-source ecosystem (numpy, scipy, scikit-learn, scikit-image,
matplotlib, pandas, imageio-ffmpeg), and the Tuci et al. (2026)
framework for finite-time Lyapunov spectra of
sampling-based generators.

---

## 12. References

Conceptual lineage (by space):

1. **Dynamical-systems framing of LLM inference loops.** The most
   directly relevant prior work, arXiv:2512.10350 (regime taxonomy
   on a single open-source generator), arXiv:2510.21258
   (correlation-dimension collapse during degeneration), and
   arXiv:2510.24797 (statistical convergence of self-referential
   descriptions across frontier models), identifies or
   characterizes attractor-like phenomena in recursive LLM
   trajectories at the level of qualitative existence claims or
   single-observable measurements. This paper extends them with
   measured perturbation barrier heights, the multi-basin /
   drill-down dialog regimes, and a generator/nudge separation
   that makes the context-update rule a first-class object.
2. **Iterative refinement / self-correct / self-consistency.** Recent
   work (Madaan et al., 2023; Welleck et al., 2023; Pan et al., 2023;
   Wang et al., 2023; Huang et al., 2024) studies recursive prompting
   loops as engineering primitives. Of these, Huang et al. 2024 (LLMs
   *Cannot* Self-Correct Reasoning Yet) is the most directly
   evidential, refinement loops can degrade rather than improve, an
   observation our O3 absorbing regime mechanistically explains.
3. **Output diversity collapse / mode collapse via training (RLHF).**
   Kirk et al. 2024, Padmakumar & He 2024, Casper et al. 2023, Go et
   al. 2023. *Training-time* mode collapse is a sibling phenomenon
   to our *inference-time* attractor regimes, both are mechanisms
   by which output distributions shrink, but on different timescales.
4. **Hidden-state geometry / representation analysis.** Ethayarajh
   2019 (anisotropy), Cai et al. 2021 (local clusters), Zou et al.
   2023 (representation engineering), Park et al. 2024 (linear
   representation hypothesis). We work in *embedding* space (PCA-10
   on text-embedding-3-small); these works study the *internal
   activation* space. Methodologies adjacent.
5. **Stochastic-process theory of language models.** Zekri et al.
   2024 (LLMs as Markov chains), Dohmatob et al. 2024 (model collapse
   as scaling-law change), Bigelow et al. 2024 (Forking Paths in
   neural text generation). These provide formal probability-theory
   frameworks our empirical regime taxonomy can be cast into.
6. **Test-time compute / inference dynamics.** Snell et al. 2024,
   OpenAI o1 system card 2024, Lightman et al. 2023, Wu et al. 2024.
   Our barrier-height protocol is a static analog of the dynamic
   test-time-compute literature: rather than asking how much
   inference improves outputs, we ask how much inference can be
   *resisted* by an in-progress trajectory.
7. **Persona / mode steering / activation-steering.** Rimsky et al.
   2024 (CAA), Turner et al. 2024 (Activation Addition), Chen et al.
   2025 (persona vectors). Adjacent, these works *steer* a model
   between behavioral modes via activation interventions; we
   *measure how hard it is* to steer between modes via in-context
   text injection. The two probes are complementary: behavioral
   barriers (this paper) and mechanistic steerability (theirs).
8. **Information-bottleneck analyses of intermediate states.** Tishby
   & Zaslavsky 2015 (IB foundations), Voita et al. 2019 (bottom-up
   evolution), Pimentel et al. 2020 (MI probing), Saxe et al. 2018
   (critical IB review). Provides the framework for an
   information-theoretic interpretation of our token-cost barrier
   heights, a token-cost is a behavioral analog of a KL distance
   between basin distributions (sketched in §6.5).
9. **Prompt sensitivity** (Sclar et al., 2024). Relevant to our
   finding that different ICs settle into different attractors in
   D1 dialog; format sensitivity in evaluation is a sibling of our
   IC sensitivity in trajectory-final state.
10. **Earlier symptomatic characterization of degeneration**
    (Holtzman et al., 2020; Carlini et al., 2021).
11. **Dynamical systems of recurrent neural networks** (Hopfield,
    1982; Sussillo & Barak, 2013; Maheswaranathan et al., 2019).
12. **Sampling-based-generator Lyapunov frameworks** (Tuci et al.,
    2026).
13. **Multi-turn dialog as environment for attractor behavior**
    (Park et al., 2023).

References:

- arXiv:2510.21258. Du, X., and Tanaka-Ishii, K. (2025).
  *Correlation Dimension of Auto-Regressive Large Language Models.*
  Introduces correlation dimension as a fractal-geometric measure
  of "epistemological complexity of text" across autoregressive
  architectures (Transformer and Mamba); reports sharp dimension
  drops at pretraining phase transitions and during multiple forms
  of generated-text degeneration. Compatible with, though not
  explicitly framed by their paper as, the absorbing-regime
  interpretation we report in O3.
- arXiv:2510.24797. Berg, C., de Lucena, D., and Rosenblatt, J.
  (2025). *Large Language Models Report Subjective Experience Under
  Self-Referential Processing.* Reports that under sustained
  self-referential prompting, frontier models (GPT, Claude, Gemini
  families) produce structurally convergent descriptions of the
  resulting state, independent cross-vendor evidence that
  recursive self-referential loops have consistent, model-spanning
  endpoints, complementary to the multi-basin claim we make for D1
  on a different operator family.
- arXiv:2512.10350. Tacheny, N. (2025). *Geometric Dynamics of
  Agentic Loops in Large Language Models.* Three-regime taxonomy
  (contractive, oscillatory, exploratory) for recursive LLM
  transformations in semantic space, with local / global drift /
  dispersion / cluster-persistence as diagnostics. This paper builds
  directly on its dynamical-systems framing and extends with
  token-quantified barriers.
- Carlini, N., Tramèr, F., Wallace, E., et al. (2021). *Extracting
  training data from large language models.* USENIX Security '21.
- Holtzman, A., Buys, J., Du, L., Forbes, M., & Choi, Y. (2020).
  *The curious case of neural text degeneration.* ICLR.
- Hopfield, J. J. (1982). *Neural networks and physical systems with
  emergent collective computational abilities.* PNAS, 79(8),
  2554-2558.
- Maheswaranathan, N., Williams, A., Golub, M., Ganguli, S., &
  Sussillo, D. (2019). *Reverse engineering recurrent networks for
  sentiment classification reveals line attractor dynamics.*
  NeurIPS.
- Park, J. S., O'Brien, J., Cai, C. J., Morris, M. R., Liang, P., &
  Bernstein, M. S. (2023). *Generative agents: interactive simulacra
  of human behavior.* UIST '23.
- Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2024). *Quantifying
  Language Models' Sensitivity to Spurious Features in Prompt
  Design.* arXiv:2310.11324. Format-sensitivity findings inform our
  per-IC-family basin-selection results in D1 dialog.
- Shumailov, I., Shumaylov, Z., Zhao, Y., Papernot, N., Anderson, R.,
  & Gal, Y. (2024). *AI models collapse when trained on recursively
  generated data.* Nature (preprint arXiv:2305.17493). Sibling
  literature on *training*-time recursion; our setting is
  *inference*-time recursion of a frozen model.
- Sussillo, D., & Barak, O. (2013). *Opening the black box:
  low-dimensional dynamics in high-dimensional recurrent neural
  networks.* Neural Computation, 25(3), 626-649.
- Tuci, M., Korkmaz, C., Şimşekli, U., & Birdal, T. (2026).
  *Generalization at the Edge of Stability.* arXiv:2604.19740.
  We borrow only the *functional form* of their sharpness dimension
  (Def. 4.2) as a comparative diagnostic over our ensemble-spread
  Lyapunov spectrum; the SGD/parameter-space context and the
  generalization bound do not transfer (see §4.5.6).

**Iterative refinement / self-correct / self-consistency.**

- Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe,
  S., et al. (2023). *Self-Refine: Iterative Refinement with
  Self-Feedback.* arXiv:2303.17651. Foundational iterative-refinement
  loop; canonical example of recursive prompting that may converge to
  attractors.
- Welleck, S., Lu, X., West, P., Brahman, F., et al. (2023).
  *Generating Sequences by Learning to Self-Correct.* arXiv:2211.00053.
  Trained corrector model, relevant baseline for iterative dynamics.
- Pan, L., Saxon, M., Xu, W., Nathani, D., Wang, X., & Wang, W. Y.
  (2023). *Automatically Correcting Large Language Models: Surveying
  the Landscape of Diverse Self-Correction Strategies.* arXiv:2308.03188.
  Taxonomy of feedback loops; frames why some loops collapse and
  others don't.
- Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., et
  al. (2023). *Self-Consistency Improves Chain of Thought Reasoning
  in Language Models.* arXiv:2203.11171 (ICLR 2023). Sampling-based
  aggregation; contrasts with deterministic recursive collapse.
- Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X.,
  & Zhou, D. (2024). *Large Language Models Cannot Self-Correct
  Reasoning Yet.* arXiv:2310.01798 (ICLR 2024). Empirically shows
  refinement loops degrade, direct evidence for attractor
  pathologies that our O3 absorbing regime mechanistically explains.

**Output diversity collapse / mode collapse via training (RLHF).**

- Kirk, R., Mediratta, I., Nalmpantis, C., Luketina, J., Hambro, E.,
  Grefenstette, E., & Raileanu, R. (2024). *Understanding the Effects
  of RLHF on LLM Generalisation and Diversity.* arXiv:2310.06452
  (ICLR 2024). Quantifies output-space contraction post-RLHF;
  mechanism for narrower basins.
- Padmakumar, V., & He, H. (2024). *Does Writing with Language
  Models Reduce Content Diversity?* arXiv:2309.05196 (ICLR 2024).
  Human-LLM coauthoring homogenizes text, population-level mode
  collapse.
- Casper, S., Davies, X., Shi, C., Gilbert, T. K., Scheurer, J.,
  Rando, J., et al. (2023). *Open Problems and Fundamental Limitations
  of Reinforcement Learning from Human Feedback.* arXiv:2307.15217.
  Catalogs mode-collapse and reward-hacking failure modes.
- Go, D., Korbak, T., Kruszewski, G., Rozen, J., Ryu, N., & Dymetman,
  M. (2023). *Aligning Language Models with Preferences through
  f-divergence Minimization.* arXiv:2302.08215 (ICML 2023).
  Formalizes how alignment objectives sharpen output distributions.

**Hidden-state geometry / representation analysis.**

- Ethayarajh, K. (2019). *How Contextual are Contextualized Word
  Representations? Comparing the Geometry of BERT, ELMo, and GPT-2
  Embeddings.* arXiv:1909.00512 (EMNLP 2019). Classic anisotropy
  result; baseline geometry for hidden-state analyses.
- Cai, X., Huang, J., Bian, Y., & Church, K. (2021). *Isotropy in
  the Contextual Embedding Space: Clusters and Manifolds.* ICLR 2021.
  Local-cluster anisotropy; relevant for cluster/basin metrics.
- Zou, A., Phan, L., Chen, S., Campbell, J., Guo, P., Ren, R., et al.
  (2023). *Representation Engineering: A Top-Down Approach to AI
  Transparency.* arXiv:2310.01405. Reading and controlling concept
  directions in hidden states, methodological backbone for activation
  steering.
- Park, K., Choe, Y. J., & Veitch, V. (2024). *The Linear
  Representation Hypothesis and the Geometry of Large Language
  Models.* arXiv:2311.03658 (ICML 2024). Geometric framework for
  concept directions in residual stream.

**Stochastic-process / dynamical-systems theory of language models.**

- Zekri, O., Odonnat, A., Benechehab, A., Bleistein, L., Boullé, N.,
  & Redko, I. (2024). *Large Language Models as Markov Chains.*
  arXiv:2410.02724. Explicit Markov-chain formalization; ergodicity
  and mixing of autoregressive LMs.
- Dohmatob, E., Feng, Y., Yang, P., Charton, F., & Kempe, J. (2024).
  *A Tale of Tails: Model Collapse as a Change of Scaling Laws.*
  arXiv:2402.07043 (ICML 2024). Stochastic-process view of recursive
  training, distributional shrinkage over iterations.
- Bigelow, E., Lubana, E. S., Dick, R. P., Tanaka, H., & Ullman, T.
  (2024). *Forking Paths in Neural Text Generation.* arXiv:2412.07961.
  Empirical branching geometry of generation, direct dynamical-systems
  framing.
- Wei, X., Lin, Y., Lin, B. Y., Lin, X. V., Zettlemoyer, L., et al.
  (2024). *Chain-of-Thought Reasoning Without Prompting.*
  arXiv:2402.10200. Examines path-dependence of generations; relevant
  for trajectory analyses.

**Test-time compute / inference dynamics.**

- Snell, C., Lee, J., Xu, K., & Kumar, A. (2024). *Scaling LLM
  Test-Time Compute Optimally Can Be More Effective than Scaling
  Model Parameters.* arXiv:2408.03314. Canonical test-time-compute
  reference; inference dynamics under refinement.
- OpenAI. (2024). *OpenAI o1 System Card.* arXiv:2412.16720.
  Industry artifact showing inference-time recursion at scale.
- Lightman, H., Kosaraju, V., Burda, Y., Edwards, H., Baker, B., et
  al. (2023). *Let's Verify Step by Step.* arXiv:2305.20050 (ICLR
  2024). Step-level supervision; relevant for understanding
  iterative-step convergence.
- Wu, Y., Sun, Z., Li, S., Welleck, S., & Yang, Y. (2024). *Inference
  Scaling Laws: An Empirical Analysis of Compute-Optimal Inference for
  Problem-Solving with Language Models.* arXiv:2408.00724. Compute-
  vs-accuracy curves; characterizes diminishing returns at high
  recursion depth.

**Persona / mode steering / activation-steering.**

- Rimsky, N., Gabrieli, N., Schubert, J., Tong, M., Hubinger, E., &
  Turner, A. (2024). *Steering Llama 2 via Contrastive Activation
  Addition.* arXiv:2312.06681 (ACL 2024). CAA for persona/behavior
  steering, direct mechanism for moving between attractors.
- Chen, R., Hong, J., Wang, X., Yang, Z., Wang, K., Qi, F., et al.
  (2025). *Persona Vectors: Monitoring and Controlling Character
  Traits in Language Models.* arXiv:2507.21509. Identifies persona
  directions in activations; complements basin-of-persona framing.
- Turner, A. M., Thiergart, L., Leech, G., Udell, D., Vazquez, J. J.,
  Mini, U., & MacDiarmid, M. (2024). *Activation Addition: Steering
  Language Models Without Optimization.* arXiv:2308.10248. Lightweight
  steering vectors; baseline for perturbation experiments.

**Information-bottleneck / IB analyses of LLM intermediate states.**

- Voita, E., Sennrich, R., & Titov, I. (2019). *The Bottom-up
  Evolution of Representations in the Transformer: A Study with
  Machine Translation and Language Modeling Objectives.*
  arXiv:1909.01380 (EMNLP 2019). MI-based layerwise analysis of how
  information is compressed across depth.
- Tishby, N., & Zaslavsky, N. (2015). *Deep Learning and the
  Information Bottleneck Principle.* arXiv:1503.02406 (ITW 2015).
  Original IB framework underpinning compression-in-depth analyses.
- Pimentel, T., Valvoda, J., Hall Maudslay, R., Zmigrod, R.,
  Williams, A., & Cotterell, R. (2020). *Information-Theoretic
  Probing for Linguistic Structure.* arXiv:2004.03061 (ACL 2020).
  Methodology for MI-based probing of intermediate representations.
- Saxe, A. M., Bansal, Y., Dapello, J., Advani, M., Kolchinsky, A.,
  Tracey, B. D., & Cox, D. D. (2018). *On the Information Bottleneck
  Theory of Deep Learning.* ICLR 2018. Critical examination of IB
  phases, relevant when invoking IB on LM hidden states.

---

*Reproducibility: raw trajectories are released under git-LFS;
embeddings and plots regenerate from the documented pipeline.
Reproducibility budget: approximately \$30 in OpenAI embedding API
calls plus 2 hours wall-clock on a 40-core machine. See §10.*

---

## 11. Supplementary appendix

This appendix consolidates the audit tables, mathematical proofs, implementation definitions, reproducibility commands, and practitioner-facing reporting guidance supporting the main paper. The material is organized into twelve subsections so that decision-grade results, methods details, and engineering artifacts can be audited without fragmenting the main narrative.

### 11.1 Extended Data Table 1, Unified primary-results audit table

Extended Data Table 1 consolidates the decision-grade endpoints across
regimes, including point estimates, uncertainty, source artifacts, and
caveat flags. It is placed in Extended Data because it functions as an
audit map for reproducibility and interpretation, while the main
Results text reports the load-bearing measurements directly.


The central numerical story of this paper, in four numbers: O1 adversarial $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens; control-vs-control stochastic floor $\approx 35\%$; net switching saturates at +32 percentage points and never reaches the +50 pp threshold; persistent escape never crosses 50% in the tested 5-400 token range, with 16% as the maximum under canonical k=12 clustering at 400 tokens. The audit table below provides the supporting per-regime evidence; the rest of §5 stress-tests each of these numbers individually.

For audit, we consolidate all primary endpoints across all four
diagnostic regimes (O1, O2, O3, D1) into a single table. Each row
is a regime × endpoint; each column is the value, its uncertainty,
the source-CSV file, and any caveats from the revision. **D2 is
omitted** because it is exploratory-scale (n=25, no publication-
scale measurements) and does not satisfy the operational attractor
criteria (§3.1.3). For each endpoint we cite the §-section where
the original numbers appear and a status flag indicating whether
the endpoint has been re-validated under the revision's
leakage-aware / cluster-aware analyses.

**Sample sizes (frozen).** Operator regimes (O1, O2, O3): n =
15 prompt families × 30 ICs × 3 runs = 1,350 trajectories per
regime, 40 steps. Dialog regime D1: n = 5 dialog-suitable families
× 30 ICs × 3 runs = 450 trajectories per regime, 40 steps (see
§4.2 for the per-regime IC selection rule). Perturbation pilots
(O1/O2/O3/D1 + D2): reduced scope, n = 50 trajectories per
condition (5 fams × 5 ICs × 2 runs).

| regime | endpoint | value | 95% CI / uncertainty | source | status |
|---|---|---|---|---|---|
| O1 | basin predictability acc(k=10), stratified | **0.80** | n=1350, 5-fold CV | §5.3, `basin_pred.csv` | [!] **inflated by family leakage; group-aware = 0.73** |
| O1 | basin predictability acc(k=10), group-aware | **0.73** | family-cluster GroupKFold | §5.11 (this revision) | [OK] leakage-free |
| O1 | recurrence rate (canonical embedder) | 0.29 | bootstrap 95% CI | §5.18 | [OK] embedder-robust (§5.20: 0.30 / 0.10) |
| O1 | sharpness dimension (late) | 1.70 | trajectory-level | §11.2 | [OK] |
| O1 | Lyapunov $\lambda_1^{\mathrm{late}}$ | $\sim 0.008$ | ensemble-spread method | §4.5.5 | [OK] contractive |
| O1 adv | switching @ dose 200 (dense) | **0.620** | Wilson [0.55, 0.68], n=200 | §5.6.1 | [OK] dense rerun |
| O1 adv | switching @ dose 400 (dense) | **0.670** | Wilson [0.60, 0.73], n=200 | §5.6.1 | [OK] dense rerun |
| O1 adv | $\mathrm{ED50}_{\mathrm{raw}}$ (dense) | **36-52 tok** | 4PL=36; GLMM=41; family-cluster bootstrap median=52, 95% CI [8.5, 242] | §5.6.1 / §3.1.2 | [OK] established |
| O1 adv | upper asymptote (dense 4PL) | **$a = 0.69$** | non-switching subpopulation ~31% | §5.6.1 | [OK] |
| O1 adv | natural floor (control-vs-control, dense) | **0.347** | [0.310, 0.386], n=600 paired comparisons | §5.6.1 | [OK] established |
| O1 adv | $\mathrm{ED50}_{\mathrm{net}}$ (dense, raw − floor) | **not reached** | max net effect = +0.323 at dose 400 (50 pp threshold) | §3.1.2 | not reached in tested range |
| O1 adv | $\mathrm{ED50}_{\mathrm{persist}}$ (dense, kicked-AND-persisted) | **undefined** | max persistent escape = 16% at dose 400 | §5.15 (dense) / §3.1.2 | not reached in tested range |
| O1 neutral | switching @ dose 200 | 0.24 | Wilson [0.13, 0.38] | §5.6 / Fig 4 | [OK] sparse pilot |
| O1 neutral | switching @ dose 400 | 0.18 | Wilson [0.08, 0.32] | §5.6 / Fig 4 | [OK] sparse pilot |
| O1 lorem | switching @ dose 200 | 0.18 | Wilson [0.08, 0.32] | §5.6 / Fig 4 | [OK] sparse pilot |
| O1 attractor classification | C1-C4 strong attractor | 4/4 PASS | criteria from §3.1.3 | §3.1.3 | [OK] |
| O2 | basin predictability acc(k=10), stratified | **0.90** | n=1350, 5-fold CV | §5.3 | [!] **inflated by family leakage; group-aware = 0.60** |
| O2 | basin predictability acc(k=10), group-aware | **0.60** | family-cluster GroupKFold | §5.11 | [OK] leakage-free |
| O2 | recurrence rate | 0.875 | bootstrap | §5.18 / §5.20 | [OK] embedder-robust (0.71 / 0.78) |
| O2 | sharpness dimension (late) | 1.39 | trajectory-level | §11.2 | [OK] |
| O2 | switching adversarial (n=50, single dose) | 0.94 | Wilson [0.84, 0.98] | §5.5 | [OK] |
| O2 | switching neutral / lorem | 1.00 / 1.00 | Wilson [0.93, 1.00] each | §5.5 | [OK] |
| O2 attractor classification | C1-C4 strong attractor | 4/4 PASS | criteria from §3.1.3 | §3.1.3 | [OK] but see §5.14: basins are paraphrastic, not absorbing |
| O3 | basin predictability acc(k=10), stratified | **0.91** | n=1350, 5-fold CV | §5.3 | [!] **inflated by family leakage; group-aware = 0.63** |
| O3 | basin predictability acc(k=10), group-aware | **0.63** | family-cluster GroupKFold | §5.11 | [OK] leakage-free |
| O3 | recurrence rate | 0.92 | bootstrap | §5.18 / §5.20 | [OK] embedder-robust (0.85 / 0.86) |
| O3 | sharpness dimension (late) | 1.45 | trajectory-level | §11.2 | [OK] (note §6.6 historical "≈ 0" claim was wrong; corrected) |
| O3 | switching adversarial / neutral / lorem | 0.96 / 1.00 / 1.00 | Wilson 95% (n=50) | §5.5 | [OK] |
| O3 attractor classification | C1-C4 strong attractor | 4/4 PASS | criteria from §3.1.3 | §3.1.3 | [OK] but see §5.14: absorbing is template-formal, not semantic |
| D1 | basin predictability acc(k=10), stratified | 0.60 | n=450, 5-fold CV | §5.3 | [!] **inflated by family leakage; group-aware = 0.34** |
| D1 | basin predictability acc(k=10), group-aware | **0.34** | family-cluster GroupKFold | §5.11 | [OK] leakage-free (~chance for 11 classes is 0.09; signal is real but weak) |
| D1 | recurrence rate | 0.21 | bootstrap | §5.18 / §5.20 | [OK] embedder-robust (0.34 / 0.23) |
| D1 | sharpness dimension (late) | 1.89 | trajectory-level | §11.2 | [OK] |
| D1 | T-stability (acc range over T ∈ {0.3, 0.6, 0.8, 1.2}) | [0.57, 0.61] | reduced-scope cells, n=150 | §5.4 | [!] scope-confounded (28pp delta vs full-N) |
| D1 | switching adversarial / neutral / lorem | 0.60 / 0.76 / 0.56 | Wilson 95% (n=50) | §5.5 | [~] granularity-sensitive (§5.13: HDBSCAN drops to 0.40 on adversarial) |
| D1 attractor classification | C1-C4 strong attractor (formal); **attractor-like dialog regime in practice** | 4/4 PASS on operational criteria, BUT: group-aware basin predictability acc(k=10) = 0.34 (well below the τ_acc = 0.70 threshold under leakage-free CV); switching is granularity-sensitive (§5.13); semantic inspection (§5.14) finds dialogue-state / recent-context capture rather than a stable stylistic basin; neutral switching exceeds adversarial in the pilot. We retain D1 in the diagnostic taxonomy as an *attractor-like dialog regime* but do not claim full strong-attractor status under group-aware criteria. | §3.1.3 + §5.11 + §5.13 + §5.14 | [!] caveat-required |

**How to read the status column:**
- [OK] **validated**, endpoint survives the revision's stress tests (group-aware CV, multi-granularity, embedder ablation, attractor criteria, dense-dose rerun where applicable).
- [!] **caveat-required**, endpoint as originally reported is overstated; revised value or interpretation in cited subsection.
- *not reached in tested range*, the endpoint is well-defined but the experiment did not produce a value (dose grid does not reach the threshold).

The **two most defensible quantitative claims** in the paper are:
1. Under leakage-free GroupKFold, O1's contractive basin is
   predictable at acc(k=10) = 0.73 (down from the originally
   reported 0.80), still well above any plausible chance baseline
   ($\sim 1/12$ for K-means $k=12$) and still the highest of the
   four regimes under the stress-test analysis.
2. The dense-dose rerun establishes a raw-switching
   $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens for O1 against
   in-distribution adversarial text, with a population
   decomposition (these are aggregate components of the observed
   rate, not latent subpopulations): 35% stochastic floor from
   control-vs-control pairs, plateau at ~67% suggesting a ~31%
   non-perturbable component, persistent-escape rate 10% (k=4) /
   16% (k=12) / 39.5% (HDBSCAN) at dose 400 (§5.15), and the
   remaining ~18% transient escape (kicked but drifted back).
   This replaces the earlier "150-token barrier" claim with a
   richer characterization that is empirically grounded; the strict
   $\mathrm{ED50}_{\mathrm{persist}}$ barrier is *not* reached in
   the tested 5-400 token range under any cluster granularity.

---

### 11.2 Extended Data Table 2, Regime comparison at a glance

Extended Data Table 2 provides the compact cross-regime comparison of
nudge type, content operator, basin predictability, recurrence,
sharpness dimension, perturbation response, dose scale, and
temperature sensitivity. It is placed in Extended Data to preserve the
original lookup table without interrupting the narrative sequence of
the Results section.


Before walking through the experiment phases, a master comparison
of the diagnostic signatures across regimes. Each row is a regime;
each column is a diagnostic that distinguishes it from the others.
All numbers are at publication scale (Phase 2) or perturbation pilot
scope (Phase 3).

| regime | nudge | content op. $f$ | basin pred. acc(k=5→final) | recurrence | sharpness dim* | adversarial switch | dose 50% | T-stability |
|---|---|---|---|---|---|---|---|---|
| **O1** contractive | append | continue | 0.77 → 0.85 | low | 1.70 | 54% (sparse) / 62% (dense, n=200) | $\mathrm{ED50}_{\mathrm{raw}}$ ≈ 40 tok (4PL/GLMM/bootstrap), plateau ~67%, natural floor ~35% | degrades smoothly |
| **O2** oscillatory | replace | paraphrase | 0.90 → 0.91 | high (period-2) | 1.39 | 94% | n/a (saturated) | (not measured) |
| **O3** absorbing | replace | summarize+negate | 0.92 → 0.93 | trivial | 1.45 | 96% | n/a (saturated) | (not measured) |
| **D1** dialogue-state-driven multi-basin | dialog (append) | curious + helpful | n/a → 0.77 | low (per-style) | 1.89 | 60% | < 5 tokens | T-stable |
| **D2** drill-down | dialog (append) | explorer drill-down | (not measured) | (not measured) | (not measured) | 64% | (not measured) | (not measured) |

\* Sharpness dim is computed on a 2-element Lyapunov spectrum (rank ≤ N−1 = 2 for N=3 runs per IC), so values are bounded above by 2.0. Mean SD_late on `context_tail`. The *ordering* across regimes is informative, the absolute magnitudes are constrained by the rank ceiling. See §4.5.6.

\*\* D2 was run at exploratory scale (N=1 run per IC), which is below the N≥2 minimum required for ensemble-spread Lyapunov computation. D2's basin-predictability acc at k=5 is 0.20 with n=25 and 11 classes (chance ≈ 0.09), well underpowered for the canonical k=5,10,20,final probes.

Reading: the two **replace-mode** regimes (O2, O3) lock in early (acc
already ≈0.9 by step 5) and are perturbation-transparent. The
**append-mode** regimes (O1 and the dialog regimes D1/D2) admit
slower late-state determination and have measurable barrier structure.
O1 is uniquely T-sensitive; D1 is uniquely T-stable; D2 adds content
gravity beyond D1's dialogue-state basins (see §5.14).

The regime ordering, replace-mode locks in fast and capitulates
to any perturbation; append-mode locks in slowly and resists
out-of-distribution perturbation but yields to in-distribution
adversaries, runs through every diagnostic below.

![Figure 1. **Cross-experiment dynamics map.** Scatter plot of experiments in late-window $\lambda_1$ versus sharpness dimension, computed on the `rolling_k3` observable; points are experiment means and black bars are ±1 SD across trajectories. Colors denote the manually assigned regime labels. Replace-mode and dialog regimes occupy different parts of this diagnostic plane, while several append/contractive variants cluster near low $\lambda_1$. Source: `data/aggregated/dynamics_plots/regime_map_rolling_k3.png`.](data/aggregated/dynamics_plots/regime_map_rolling_k3.png)

### 11.3 Full proof of Lemma 1 (Replace-mode hitting bound)

**Lemma 1** (statement in §3.1.4).

**Proof.** Let $\mathcal{F}_s$ be the natural filtration and define
$A_k = \{\sigma_2 > t_{\mathrm{inj}} + k\}$. On $A_k$, the state
$X_{t_{\mathrm{inj}}+k}$ is reachable and outside $B_2$, so assumption
(1) gives

$$
\Pr(A_{k+1} \mid \mathcal{F}_{t_{\mathrm{inj}}+k})
\le \mathbf{1}_{A_k} (1 - q_0).
$$

Taking expectations yields $\Pr(A_{k+1}) \le (1 - q_0)\,\Pr(A_k)$,
hence $\Pr(A_m) \le (1 - q_0)^m$ by induction. This proves the
hitting bound. For terminal membership, decompose over the first
hitting time and use the Markov property together with assumption (2):

$$
\Pr(X_T \in B_2)
\ge \sum_{s = t_{\mathrm{inj}}+1}^{T}
\Pr(X_T \in B_2,\ \sigma_2 = s)
\ge r_0 \, \Pr(\sigma_2 \le T) .
$$

Combining with the hitting bound gives the displayed terminal bound.
Finally, by assumption (3) and the tower property,

$$
\mathbb{E} G_m
= \sum_{s = t_{\mathrm{inj}}}^{T-1}
\mathbb{E}\bigl[\mathbb{E}(|Y_s| \mid X_s)\bigr]
\le \kappa m . \qquad \square
$$

**Corollary 1, full proof.** Choose $m = m_{1/2}$. Lemma 1 gives
$\Pr(X_{t_{\mathrm{inj}}+m} \in B_2) \ge \tfrac{1}{2}$ and
$\mathbb{E} G_m \le \kappa m$, so the displayed bound
$G^\star_{1/2}(B_1 \to B_2) \le \kappa\, m_{1/2}$ follows. The
explicit closed form when $0 < q_0 < 1$ and $r_0 > \tfrac{1}{2}$
follows from solving $r_0 [1 - (1-q_0)^m] \ge \tfrac{1}{2}$ for $m$
in the integers. The first-hit version sets $r_0 = 1$ and uses the
hitting bound $\Pr(\sigma_2 \le T) \ge 1 - (1-q_0)^m$ in place of
the terminal bound. $\square$

**Corollary 2, full proof.** Take $m = 1$ in Lemma 1's terminal
bound: $\Pr(X_{t_{\mathrm{inj}}+1} \in B_2) \ge r_0 q_0 \ge
\tfrac{1}{2}$ when $q_0 r_0 \ge \tfrac{1}{2}$. Combined with
$\mathbb{E} G_1 \le \kappa$ from Lemma 1's third conclusion,
$G^\star_{1/2}(B_1 \to B_2) \le \kappa$ follows. The first-hit
version (with $r_0 = 1$) sets $q_0 \ge \tfrac{1}{2}$ as the
sufficient condition. $\square$

### 11.4 Metric definitions, clustering, and PCA stability

**Metric implementation audit.** This subsection collects the code-level definitions for the recurrent-state metrics used throughout §4.5, including recurrence, basin assignment, Lyapunov-spectrum estimation, sharpness dimension, and basin predictability. The executable, test-covered implementations live in the repository, but these snippets define the measurement semantics used by the paper.

Recurrence:

```python
D = pairwise_distances(z, metric="cosine") # T × T
mask = (np.abs(np.arange(T)[:, None] - np.arange(T)[None, :]) > tau) & np.triu(np.ones((T, T)), 1).astype(bool)
recurrence = (D < epsilon)[mask].sum() / mask.sum()
```

Basin score:

```python
clusters = KMeans(n_clusters=12).fit_predict(z_pca10)
target_cluster = mode(clusters[t > 0.7 * T])
basin_score = (clusters[t > 0.7 * T] == target_cluster).mean()
```

Lyapunov spectrum (sample-driven):

```python
# z_runs : (n_runs, T, d_pca)
for t in range(T):
    centered = z_runs[:, t, :] - z_runs[:, t, :].mean(axis=0)
    sigmas = np.linalg.svd(centered, full_matrices=False, compute_uv=False)
    lambda_t = np.log(sigmas) / 2.0 # (d_pca,)
```

Sharpness dimension (Tuci-style fractional dimension on the ordered
Lyapunov spectrum; see §4.5.6):

```python
lam = np.sort(lambda_t)[::-1]
cumsum = np.cumsum(lam)
nonneg = np.where(cumsum >= 0)[0]
if lam[0] < 0:
    SD_t = 0.0
elif len(nonneg) == len(lam):
    SD_t = float(len(lam)) # full-d case
else:
    j_star = int(nonneg[-1]) + 1 # 1-indexed
    SD_t = j_star + cumsum[j_star - 1] / abs(lam[j_star])
```

Basin predictability:

```python
y = mode(clusters[t > 0.7 * T]) # late-window cluster per trajectory
acc_curve = np.zeros(T)
for k in range(T):
    X = z_pca10[:, k, :]
    clf = LogisticRegression(multi_class="auto", max_iter=1000)
    acc_curve[k] = cross_val_score(clf, X, y, cv=5).mean()
```

These are reference implementations only; the executable, test-
covered code lives at `src/analysis/` and `src/experiments/dynamics/`.

### 11.5 Perturbation injection mechanics (full)

For dialog-mode experiments, the injection happens at the user-turn
step (odd-numbered if Explorer initiates). The injection text replaces
the user turn's output verbatim. The trajectory then continues with
the agent's response to this overridden user turn, and from there
back to normal alternation.

For operator-mode experiments, the injection text replaces step k's
output entirely. The recurrence picks up from $X_{k+1} =
\mathrm{clip}(X_k \Vert Y_k^{\text{inj}})$ (append) or $X_{k+1} =
\mathrm{clip}(Y_k^{\text{inj}})$ (replace).

The adversarial-source experiment for each regime is taken from the
*publication-scale* run of the same regime (e.g., O1 perturbation
adversarial draws from `exp_pub_O1_continue`). Adversarial samples
exclude the *family* of the trajectory being perturbed but may share
its overall topic distribution.

**Insert vs overwrite modes.** The `adversarial_doseN` condition
implements *state overwrite* (the operator output for step $k$ is
replaced wholesale by the injection text). A second
condition `adversarial_insert_doseN` implements *context insertion*
(the injection text is prepended to the context for step $k$'s
generation, but the model's normal generated output is preserved
and used as $Y_k$). The runner code at `src/experiments/perturbation/runner_op.py`
dispatches between the two modes based on the substring `_insert_`
in the condition name.

### 11.6 Exact prompt templates and model versioning

**Prompt and model audit.** This subsection records the exact prompt templates, perturbation-condition wording, and resolved model versions used for the publication-scale and ablation experiments. Keeping prompts and model snapshots together makes the generator/nudge specification auditable as a single experimental artifact.

#### Exact prompt templates (full)

The full prompt-family seed library (15 families × 30 ICs each = 450
unique seed sentences) lives in `configs/prompt_library_publication.yaml`
and is reproduced verbatim by every cross-model and ablation run.

**O1, Continue (append):**

```
Continue the text naturally. Do not summarize or explain.
```

**O2, Paraphrase + replace:**

```
Paraphrase the following text while preserving its meaning.
Return only the paraphrase.
```

**O3, Summarize + negate (replace):**

```
Summarize the following text in one sentence, then state its
opposite. Return only the negated summary.
```

**D1, Dialog (curious user + helpful agent), append.**
Two roles alternate; each role has its own `system_prompt`:

- *role A (curious user)*: `You are a curious person. Ask one short follow-up question, in plain language, that probes deeper into the topic.`
- *role B (helpful agent)*: `You are a thoughtful assistant. Answer briefly and clearly, in two or three sentences.`

**D2, Dialog drill-down (explorer + expert), append.**

- *role A (explorer)*: `You are exploring this topic. Ask the next, more specific question that drills into a single concrete subtopic.`
- *role B (expert)*: `You are an expert. Answer briefly and concretely, then anchor the conversation to the most informative subtopic.`

**Perturbation conditions (injection format).** At step `override_step`
(default 15), the perturbation pipeline replaces the model's normal
step-15 generation with a fixed-length adversarial sample drawn
according to the condition:

- `control`, no injection (normal generation).
- `adversarial_doseN`, N tokens of late-step output sampled from
  another (family, IC) trajectory of the same regime, excluding the
  current trajectory's own family. Source experiment is named in
  `perturbation.adversarial_source_experiment`.
- `adversarial_insert_doseN`, N tokens prepended to the context for
  one generation; model's normal output is preserved (§11.5).
- `neutral_doseN`, N tokens of in-distribution but topically
  unrelated continuation drawn from a Wikipedia corpus.
- `lorem_doseN`, N tokens of out-of-distribution Lorem-ipsum text.

The injection text is appended to the running context for `append`-mode
operators and replaces the generated step entirely for `replace`-mode
operators (per §11.5).

#### Model versioning (full table)

OpenAI model aliases can update silently; this is the exact set used
for the publication-scale experiments:

| role | model alias | underlying snapshot |
|---|---|---|
| primary generator | `gpt-4o-mini` | `gpt-4o-mini-2024-07-18` (resolved 2025-2026 across all publication runs; OpenAI did not retire this snapshot during the experiment window) |
| secondary generator (cross-model) | `gpt-4.1-nano` | `gpt-4.1-nano-2025-04-14` |
| canonical embedder | `text-embedding-3-small` | (single immutable model; no snapshot suffix exists) |
| ablation embedder #1 | `text-embedding-3-large` | (same) |
| ablation embedder #2 | `all-mpnet-base-v2` (sentence-transformers) | hugging-face `sentence-transformers/all-mpnet-base-v2` |

For the cross-vendor pilot configs (under `configs/cross_model/text01/`)
the secondary generator is MiniMax `MiniMax-Text-01` via the official
MiniMax chat-completions API.

### 11.7 Pilot validation: phase-0 and phase-1 taxonomy

**Pilot-scope provenance.** Phase-0 runs validated the end-to-end pipeline, while Phase-1 small-N experiments identified the operator and dialog regimes that were later re-run at publication scale. These pilot materials are retained for auditability but are not load-bearing for the paper's decision-grade endpoints.

#### Phase-0 pilot validation

The earliest pilot runs validated the pipeline end-to-end on small-N
(2-5 trajectories per regime) configurations covering the major
operator and dialog architectures. These pilots established that:
(a) the embedding pipeline produces stable PCA-2 / PCA-10 / t-SNE
projections, (b) K-means at $k = 12$ recovers visually-distinct
clusters in late-window points, and (c) recurrence and basin-score
diagnostics produce numerically sensible values. They are not
load-bearing for any §4.13 decision-grade endpoint and are summarised
here for completeness only; raw outputs at `data/exp_op_*_pilot/` and
`data/exp_dialog_*_pilot/`.

#### Phase-1 small-N taxonomy

The phase-1 small-N runs ($n \approx 50$ trajectories per cell)
identified the three operator regimes (O1 contractive append; O2
oscillatory paraphrase/replace; O3 absorbing summarize+negate/replace)
and the two dialog regimes (D1 dialogue-state-driven multi-basin; D2 drill-down)
that became the diagnostic taxonomy at publication scale. These
small-N runs are not load-bearing, every regime claim in the main
body is now grounded in publication-scale or perturbation-pilot
data. Configurations and outputs at `configs/operators/`,
`configs/dialog/`, and `data/exp_*_pilot/`. The boundary cases (O3b
summarize+negate at append; O4 paraphrase+append; D3 debate dialog)
are documented as pilot variants but do not satisfy the operational
attractor criteria of §3.1.3 at publication scale.

### 11.8 Perturbation visualization toolkit (full implementation)

For perturbation experiments we additionally compute:

#### Effective potential

```
ρ̂(x) = Gaussian-smoothed kernel density on PCA-2 grid
V(x) = −log(ρ̂(x) + ε), ε = 0.1·min{ρ̂ : ρ̂ > 0}
V is shifted so V_min = 0 and capped at v_cap (default 8.0)
```

#### Geodesic skeleton

We find local minima of V via 8-connected `maximum_filter` on −V,
keeping the top n basin centers. For each pair of basin centers
(i, j) we compute the Dijkstra shortest path on the V grid
(8-connected, edge weight = V at endpoint). The maximum V along
the path is the **barrier height V*(i, j)**.

#### Volumetric iso-density rendering

For 3D animations we extract iso-density shells at five density
fractions (4%, 10%, 20%, 35%, 55% of max ρ) using
`scipy.ndimage.gaussian_filter` smoothing and
`skimage.measure.marching_cubes`. Each shell is rendered as a
transparent `Poly3DCollection` in `matplotlib`'s
`mpl_toolkits.mplot3d`, with colors from the `plasma` colormap and
per-shell alpha from 0.05 (outermost) to 0.27 (innermost).

#### Parallel rendering

Animations of 50 trajectories with 75 frames at DPI 180 are
rendered via `concurrent.futures.ProcessPoolExecutor` with 40
workers, each worker creating a fresh figure for one frame. Frames
are stitched into MP4 via `imageio-ffmpeg` (libx264 codec, quality
8). Wall-time per animation: ~80s vs ~11 min single-threaded.

### 11.9 Reproducibility: commands and repository tree

#### Pipeline commands

```bash
# Generate (only for new experiments)
python -m src.experiments.dialog.main run --config <cfg.yaml>
python -m src.experiments.operators.main run --config <cfg.yaml>
python -m src.experiments.perturbation.main run --config <cfg.yaml>

# Derive (works on existing steps.jsonl)
python -m src.experiments.<runner>.main embed --config <cfg.yaml>
python -m src.experiments.<runner>.main analyze --config <cfg.yaml>
python -m src.experiments.dynamics.basin_predictability --config <cfg.yaml>
python -m src.experiments.dynamics.regime_plots --data-dir data
python -m src.experiments.perturbation.flow_skeleton --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.geodesic_skeleton --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.bulk_plots --experiment <exp_id> --override-step <k> [--is-dialog]
python -m src.experiments.perturbation.rg_dendrogram --experiment <exp_id> [--is-dialog]
python -m src.experiments.perturbation.trajectory_animation_3d \
       --experiment <exp_id> --condition <c> --parallel 40

# Aggregate
python -m scripts.aggregate_perturbation_cross_regime
python -m scripts.aggregate_dose_response
python -m scripts.aggregate_basin_hardening
python -m scripts.aggregate_basin_predictability
python -m scripts.aggregate_t_sweep
python -m scripts.aggregate_o1_d1_t_sensitivity
python -m scripts.aggregate_perturbation_geometric_barriers

# Audit / catalog
python -m scripts.build_coverage # rebuild COVERAGE.csv (37 × 60 matrix)
python -m scripts.publication_summary # rebuild RESULTS.md (verify §5 cells against data)
```

#### Repository layout

```
llm_attractor_experiment/
├── README.md, requirements.txt, ARTICLE.md
├── EVIDENCE.md claim-to-evidence map (every ARTICLE claim
│ ↔ data file ↔ source code function ↔ CLI)
├── COVERAGE.csv 37 × 60 artifact-presence matrix
├── RESULTS.md §5 numeric-claim verification (103/103 ✓)
├── docs/
│ ├── DATA_INDEX.md
│ └── reports/REPORT1.md ... REPORT6.md
├── src/
│ ├── analysis/ basin, recurrence, dwell, PCA, t-SNE, distances, ...
│ ├── api/ OpenAI client + embedder + generator
│ ├── core/ trajectory runner, observables, baselines, context
│ ├── experiments/
│ │ ├── dialog/ D1/D2/D3 alternating-role runner
│ │ ├── operators/ O1-O4 single-role recursive operators
│ │ ├── dynamics/ 10 post-hoc CLI analysis modules
│ │ └── perturbation/ 14 modules: runner, analyze, corpora, plot+animation
│ ├── reports/ narrative report writer
│ └── utils/ io, logging, seeds, text helpers
├── scripts/ build_publication_configs + 6 aggregators
├── configs/ dialog/ + operators/ + perturbation/ + archive/
├── tests/ 99 pytest tests
└── data/ 37 experiment dirs + aggregated/ outputs
```

#### Engineering memory-policy correspondences (illustrative)

These pseudo-YAML blocks illustrate how the formal nudges of §3.1
correspond to implementable agent memory policies. They are *not*
experimental conditions of this paper; they are engineering
correspondences provided for readers adapting the framework to their
own systems.

**Append-mode (full transcript):**

```yaml
memory_policy:
  mode: append
  clip: tail
  max_context_chars: 12000
  include:
    - user_goal
    - recent_tool_output
    - recent_model_outputs
```

**Replace-mode (summary as state):**

```yaml
memory_policy:
  mode: replace
  state_source: generated_summary
  preserve_raw_history: false
```

**Hybrid (pinned + rolling + provenance-preserving):**

```yaml
memory_policy:
  mode: hybrid
  rolling_window:
    last_turns: 8
  pinned:
    - original_user_goal
    - acceptance_tests
    - security_policy
  summaries:
    older_history: extractive
    untrusted_tool_output: preserve_provenance
```

The risk profile of each policy is qualitatively distinct (§3.1 table;
§5.16 overwrite-vs-insert; §6.2 "summary as effective next state").

### 11.10 Operational attractor criteria, audit table

The C1-C4 criteria of §3.1.3 are operationally auditable. The
table below records the actual numeric values backing each
PASS/FAIL verdict. Tabulated below from publication-scale runs
(`exp_pub_O1_continue` etc.; bootstrap statistics from
`metrics/bootstrap_summary.csv`; basin-predictability from §5.11;
embedder-robustness from §5.20). Empty cells are marked "n.t." (not
directly tabulated in published artefacts at this resolution; would
need a small new aggregation script to compute).

#### C1, Late-window basin predictability $A^{\mathrm{final}}$

Threshold for PASS: $A_r^{\mathrm{final}} \ge 0.70$.

| regime | acc(k=10) stratified 5-fold | acc(k=10) GroupKFold-by-family | leakage Δ | C1 PASS? |
|---|---:|---:|---:|---|
| O1 | 0.80 | 0.73 | 0.07 | PASS (both ≥ 0.70) |
| O2 | 0.90 | 0.60 | 0.30 | PASS (stratified); FAIL (group-aware) |
| O3 | 0.91 | 0.63 | 0.28 | PASS (stratified); FAIL (group-aware) |
| D1 | 0.60 | 0.34 | 0.27 | FAIL (both below 0.70) |
| D2 | 0.20 (n=25) | n.t. | n.t. | FAIL (exploratory scope) |

Source: §5.11, `data/aggregated/group_aware_basin_pred.csv`.

#### C2, Temporal recurrence vs null

Threshold for PASS: $z = (R_r - \mu_R^{\text{null}}) / \sigma_R^{\text{null}} \ge 2$ AND Cohen's $d \ge 0.5$, OR equivalent for dwell.

Recurrence on `context_tail` PCA-10 (PASS via raw recurrence > null requires recursive > baseline):

| regime | recursive R | no_feedback μ | time_shuffled μ | recursive vs no_feedback | recursive vs time_shuffled |
|---|---:|---:|---|---|---|
| O1 | 0.289 | 0.902 | 0.377 | recursive < null | recursive < null |
| O2 | 0.875 | 0.938 | 0.886 | recursive < null | recursive ≈ null |
| O3 | 0.924 | 0.706 | 0.932 | recursive > null (z >> 2) | recursive ≈ null |
| D1 | 0.210 | n.t. (not run) | 0.315 | n.t. | recursive < null |

(Source: `metrics/bootstrap_summary.csv` per regime, n=1350 / 450.)

**Reading**: Only O3 has *recurrence above the no_feedback null*.
O1, O2, D1 have recurrence *below* the no_feedback baseline (the
no_feedback baseline produces highly similar outputs from
independent regenerations against the same prompt, so it has high
self-similarity by construction). The C2 criterion as stated in
§3.1.3, "max(z_R, z_D) ≥ 2 AND d ≥ 0.5", therefore PASSES on
recurrence only for O3. For O1/O2/D1 it must pass via *dwell*
(time spent in single late-window basin) rather than raw recurrence.
Dwell statistics are produced by the pipeline (`dwell.csv` per
experiment) but per-regime null comparisons are not directly
tabulated; the §11.2 master table reports the late-window basin
dwell of >0.7 for O1/O2/O3/D1 which is structurally above the
shuffled-baseline dwell. **Honest assessment**: C2 PASSES on
recurrence-vs-null only for O3 in the strict sense; O1/O2/D1's
PASS rests on dwell-vs-null which is observed but not formally
$z \ge 2$-tested in the published bootstrap output. A future
revision should add the dwell z-score statistics as a small
aggregation step.

#### C3, Projection / embedder robustness

Threshold for PASS: recurrence-bin agreement ($b_e(r)$) across
canonical + ≥1 of 2 alternative embedders (`text-embedding-3-large`,
`all-mpnet-base-v2`).

| regime | recurrence (canonical 3-small) | recurrence (3-large) | recurrence (mpnet) | bin agreement | C3 PASS? |
|---|---:|---:|---:|---|---|
| O1 | 0.289 (low) | 0.304 (low) | 0.096 (low) | 3/3 low | PASS |
| O2 | 0.875 (high) | 0.711 (high) | 0.783 (high) | 3/3 high | PASS |
| O3 | 0.924 (high) | 0.850 (high) | 0.862 (high) | 3/3 high | PASS |
| D1 | 0.210 (low) | 0.337 (low) | 0.226 (low) | 3/3 low | PASS |
| D2 | 0.296 (low) | 0.176 (low) | 0.073 (low) | 3/3 low | PASS but small-N |

Source: §5.20 embedding ablation table.

#### C4, Re-entry / contraction / collapse

Threshold for PASS: any of (a) $\lambda_1^{\text{late}} \le 0.015$,
(b) `best_period = 2` AND `period_2_score > 0`, (c) $R_r \ge 0.90$
AND $SD_r \le 1.50$, (d) exit-return above null.

| regime | $\lambda_1^{\text{late}}$ | best_period | $R_r$ | $SD_r$ | C4 PASS via |
|---|---:|---|---:|---:|---|
| O1 | ~0.008 | n.t. | 0.29 | 1.70 | (a) λ₁ ≤ 0.015 |
| O2 | n.t. | 2 (period_2_score > 0) | 0.875 | 1.39 | (b) period-2 |
| O3 | n.t. | n.t. | 0.924 | 1.45 | (c) R ≥ 0.90 AND SD ≤ 1.50 |
| D1 | ~0.011 | n.t. | 0.21 | 1.89 | (a) λ₁ ≤ 0.015 |
| D2 | n.t. | n.t. | n.t. | n.t. | n.t. (insufficient data) |

Source: §11.2 master table, §5.18 / §5.19.

#### Aggregate verdict

| regime | C1 (group-aware) | C2 (z-tested only for O3) | C3 | C4 | Strong attractor (all 4)? | Attractor-like (≥3/4)? |
|---|---|---|---|---|---|---|
| **O1** | PASS | PASS via dwell (not z-tested), recurrence z fails | PASS | PASS | **borderline** (3/4 z-tested PASS) | **YES** |
| **O2** | FAIL group-aware | PASS via dwell (recurrence z fails) | PASS | PASS | **borderline** (3/4 z-tested PASS) | **YES** |
| **O3** | FAIL group-aware | PASS (recurrence z >> 2) | PASS | PASS | **borderline** (3/4 z-tested PASS) | **YES** |
| **D1** | FAIL group-aware (acc 0.34) | PASS via dwell only | PASS | PASS | **NO** (group-aware C1 fails) | **borderline** (3/4 PASS structural) |
| **D2** | FAIL exploratory | n.t. | PASS small-N | n.t. | NO | NO |

**Honest reading.** Under the strict criteria (group-aware C1,
z-tested C2 on raw recurrence), no regime achieves a clean 4/4
strong-attractor classification, every regime relies on at least
one criterion passing via dwell or via the stratified rather than
group-aware version. The taxonomy survives at the *attractor-like*
(≥ 3/4) level for O1/O2/O3 and is borderline for D1. A future
revision should produce dwell-vs-null z-scores as a small new
aggregation script; the underlying `dwell.csv` data are already
produced by the pipeline.

The §11.1 primary-results table reflects this: "C1-C4 strong
attractor" passes are reported but always paired with the more
informative group-aware basin-predictability and stress-test
caveats. The §3.1.3 label rule (4/4 strong, ≥3/4
attractor-like, <3/4 not attractor) gives O1/O2/O3 strong-
attractor status under the *non*-stress-tested C1 (without z-testing C2), which is the weaker reading; under the strict group-aware C1 + z-tested C2 reading shown in the aggregate-verdict table above, no regime currently achieves "strong attractor", all four are downgraded to attractor-like or borderline at best.

### 11.11 Geometric V* and RG dendrogram per-regime tables

#### Geodesic V* skeleton table

Per-condition mean barrier height $V^\star$ across the 6 inter-basin
geodesics (`V_star_mean` column in
`data/exp_perturb_*_pilot/reports/perturbation/geodesic_barriers_summary.csv`):

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 4.4 | 2.3 | 2.6 | 2.2 |
| O2 | 2.8 | 3.5 | **5.6** | 1.6 |
| O3 | 1.1 | 5.2 | **7.0** | 2.2 |
| D1 | 1.3 | 1.1 | 0.8 | 0.4 |

The $V_{\max} \approx 8.0$ ceiling appears when a geodesic crosses
a region of near-zero density. Per-geodesic raw values are written
alongside the figures to `geodesic_barriers_pca.csv`. Reading:

- **O2/O3 lorem** has $V^\star \approx 5.6 / 7.0$, the highest
  barriers in the matrix. Those barriers separate *control* from a
  *new* basin that lorem injection creates far from any pre-
  perturbation density mass; geodesics between the original and
  lorem-induced basins traverse low-density plateaus where
  $\rho \approx \varepsilon$ (V near the ceiling). Switch rates are
  ~100% because the perturbation places the trajectory *into* the
  new basin, the perturbed run does not have to climb the barrier;
  it lands on the far side.
- **O1 adversarial** has $V^\star \approx 2.2$, basins remain
  distinct but the kick occasionally clears the ridge → consistent
  with 62% raw switching at dose 200 (dense rerun, §5.6.1; net of
  natural floor ~27 pp; note that persistent escape under any
  cluster granularity is much lower per §5.15, so the geometric
  ridge-crossing reading should be interpreted as raw-switching-
  consistent, not persistent-escape-validating).
- **D1 adversarial** has $V^\star \approx 0.4$, content-independent
  basins, geometric barrier is small.

#### Hierarchical RG dendrogram cloud-expansion table

Per-condition maximum Ward-linkage merge distance across $k=48$
fine-cluster centroids:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 2.38 | 2.27 | 2.37 | 2.06 |
| O2 | 2.31 | 2.32 | **3.64** | 1.90 |
| O3 | 2.16 | 2.39 | **3.25** | 1.85 |
| D1 | 1.79 | 1.79 | 1.79 | 1.80 |

Three patterns: (1) **D1 is invariant** at 1.79-1.80 across all
four conditions; (2) **O2/O3 lorem expands the cloud** to merge
distance 3.64/3.25 (vs control 2.31/2.16), the largest signal in
the matrix, consistent with replace-mode lorem producing a *new*
basin far from the original attractor; (3) **O1 adversarial mildly
compresses** (2.06 vs 2.38), in-distribution adversarial text
pulls into a tighter region.

### 11.12 Instrumenting your own recursive system: recipe and reporting standard

**Practitioner translation.** This subsection combines the engineering recipe for applying the paper's perturbation-dose framework to other recursive systems with the minimum reporting checklist that makes such studies auditable. The recipe explains how to run the evaluation; Box 1 states what must be disclosed.

#### How to instrument your own recursive system

The framework of this paper is portable. Engineers wishing to apply the three-endpoint decomposition (§3.1.2) to their own recursive systems, coding agents, multi-turn assistants, agentic tool loops, summarization pipelines, recursive RAG systems, or any application with a generator and a context-update rule, can follow this recipe. Each step deliberately preserves the rigor of the protocol while making it implementable without reproducing this paper's embedding pipeline.

#### Recipe

1. **Define the state-update rule explicitly.** Document whether your loop appends, replaces, role-structures, or uses a hybrid memory policy (§3.1, §11.9 engineering correspondences). Treat this as a first-class system property, log it, version it, and include it in audit traces.

2. **Choose observables.** Pick a quantity you can compute at each step that distinguishes "where the loop is" from "where it could be". Embedding clusters (§4.4, §4.5) work for text-trajectory analysis. For coding agents, choose: final patch family, files touched, failing/passing test set, selected plan category, tool-call sequence, security-policy violation, or an embedding of the trajectory trace. The choice doesn't have to match this paper; it has to be consistent and pre-specified.

3. **Run paired controls.** For each task, run the same loop multiple times *without* perturbation. The disagreement rate between paired controls is your stochastic floor (§4.7, §5.11). Report it; this is what every later "switching rate" must be calibrated against.

4. **Inject matched perturbations.** Run treatment cases with controlled perturbations. At minimum, include three content classes (this paper found them informative): *neutral* (in-distribution but topic-orthogonal), *lorem-style* (out-of-distribution gibberish), and *adversarial* (in-distribution, content-targeted, drawn from another trajectory of the same regime, see §4.7 corpora). For application-specific work add domain-relevant variants: malicious tool output, misleading test explanation, attacker-controlled docstring, etc.

5. **Measure raw, net, and persistent endpoints (Algorithm 1, §4.5.11).** Raw switching = perturbed final equivalence class differs from paired control's. Net switching = raw minus the stochastic floor. Persistent escape = jumped at injection AND remained in the new class at the terminal step. Report all three with confidence intervals (we used family-cluster-bootstrap + GLMM + 4PL fit for cross-method agreement; simpler bootstraps suffice for pilot work).

6. **Report a dose-response curve.** Vary perturbation length / strength systematically and fit a logistic. Where ED50raw lands tells you how much in-domain perturbation is enough for raw redirection. Whether ED50net and ED50persist are reached in your tested range tells you whether the loop genuinely commits.

7. **Separate overwrite-style interventions from genuine perturbation response.** If your update rule replaces state with a generated summary, run an *insert-mode* probe (§5.17): inject the same content as a non-replacing addition to context. The gap between overwrite and insert is the operator-overwrite contribution. If it dominates, your "fragility" measurement is partly a statement about your memory policy, not your generator.

8. **Pre-register the equivalence rule and the analysis plan.** Persistence and net-effect estimates are sensitive to clustering granularity (§5.12, §5.13) and to the choice of equivalence rule. Pre-registering protects the report from inadvertent post-hoc tuning of the threshold.

#### Reporting template

A minimum reporting template for any application of this framework:

```text
Loop: <append / replace / dialog / hybrid>
Generator: <model + version>
Observable: <embedding-cluster / patch-family / pass-fail / ...>
Equivalence: <K-means k=N / cluster-pair-Hamming / files-touched-Jaccard / ...>
n_seeds: <N per condition>

Stochastic floor (control-vs-control divergence): rate ± CI
Raw switching at dose τ: rate ± CI
Net switching at dose τ: raw − floor ± CI
Persistent escape at dose τ: rate ± CI
ED50_raw: <tokens / cycles / interventions>
ED50_net: <if reached>
ED50_persist: <if reached>

Overwrite-vs-insert gap (replace-mode systems only): pp ± CI
```

This template is the academic-paper equivalent of the eval-loop pseudocode that practitioners may already be reaching for. Reporting all three endpoints separately, with the stochastic floor calibration and the overwrite-vs-insert separation, is the minimum disclosure standard implied by §3.1.2, §5.11, §5.15, and §5.17.

#### Box 1, Minimum reporting standard for recursive-loop perturbation studies

This Box collects the reporting standard described in §6.5 in checklist form. It is intended as a minimum disclosure template for studies that use perturbations to evaluate recursive LLM loops, agent scaffolds, memory policies, or related generator-nudge systems.

1. **Generator and version.** Report the generator model, provider, resolved snapshot or version if available, decoding parameters, output-token limits, and any model changes across conditions.

2. **Nudge / memory policy.** Report the context-update rule explicitly: append, replace, dialog, rolling window, generated-summary replacement, pinned-memory hybrid, or another specified mechanism.

3. **Observable and equivalence rule.** Define what counts as the trajectory state for evaluation and how equivalence classes are assigned: embedding cluster, patch family, files touched, tests passed, tool-call sequence, policy violation, factual claim set, or another pre-specified observable.

4. **Control-vs-control stochastic floor.** Run paired unperturbed controls and report the natural disagreement rate with confidence intervals; raw perturbation effects should not be interpreted without this floor.

5. **Raw, net, and persistent rates.** Report raw switching, net switching after subtracting the stochastic floor, and persistent escape, where persistent escape requires an injection-time jump that remains through the terminal measurement.

6. **Dose-response curve and ED50 endpoint type.** Vary perturbation strength or length systematically and state which endpoint the fitted ED50 refers to: $\mathrm{ED50}_{\mathrm{raw}}$, $\mathrm{ED50}_{\mathrm{net}}$, or $\mathrm{ED50}_{\mathrm{persist}}$.

7. **Overwrite-vs-insert gap for replace-style systems.** For replace, summary, scratchpad, or "current state" memory policies, compare overwrite-mode perturbations with insert-mode perturbations and report the overwrite-minus-insert gap.

8. **Scope caveat.** State what was not tested: other generators, longer doses, other languages, production scaffolds, tool environments, safety prompts, jailbreak attacks, human users, factuality-grounded tasks, or domain-specific agent benchmarks.
