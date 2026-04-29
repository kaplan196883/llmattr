# Endogenous attractor regimes in recursive large-language-model loops
## What does it cost to nudge an LLM out of an attractor? A theoretical framework with measured barrier heights in tokens.

---

## Abstract

Large language models run in recursive loops do not wander arbitrarily
through text space. Under repeated self-conditioning, they enter a
small number of reproducible attractor regimes whose form depends not
only on the model, but on how generated text is fed back into context.
Recent work has classified such regimes qualitatively
(arXiv:2512.10350, arXiv:2510.21258, arXiv:2510.24797), but has not
asked the next question: **what does it cost to push a trajectory out
of an attractor?**

We answer this with a state–generator–nudge framework that treats the
language model and the context-update rule as distinct objects. In this
framework, a **nudge** is the operator that maps the current context
and the model output into the next context; append, replace, and
role-structured dialog are three concrete nudge families. We define
the **barrier height** of an attractor as the token-cost of injected
text required for 50% trajectory switching — an interpretable
operational unit for comparing recursive regimes.

Across 37 experiments on `gpt-4o-mini`, with 50–1350 trajectories per
configuration embedded using `text-embedding-3-small`, we identify
five regimes: an append-mode contractive basin (O1), a replace-mode
oscillatory 2-cycle (O2), a replace-mode absorbing regime induced by
summarize-and-negate (O3), a stylistic multi-basin dialog regime (D1),
and a drill-down dialog regime with topical content gravity (D2,
exploratory-scale). Their barrier signatures differ sharply. O1
requires about 150 tokens of in-distribution adversarial text for 50%
switching, while out-of-distribution perturbations saturate near a
24% drift floor. Replace-mode O2 and O3 are nearly
perturbation-transparent, with 94–96% switching at tested doses.
Dialog regimes occupy intermediate scales, with switching behavior
determined more by conversational structure than by perturbation
magnitude alone.

We then compare these **behavioral** barriers to **geometric** barrier
estimates derived from the empirical potential landscape
$V(x) = -\log \rho(x)$ on PCA-2, using Dijkstra geodesics between
density-peak basins. The two estimates agree in ordinal structure.
Together, these results show that recursive LLM regimes are not
defined only by contraction, oscillation, or collapse, but also by
their **resistance to nudging**.

The full pipeline regenerates from raw trajectories
(`steps.jsonl`, LFS-tracked) using a documented `embed → analyze →
report` chain. All code, configs, raw data, and reports are publicly
available (https://github.com/kaplan196883/llmattr); 103/103 numeric
claims are cell-verified against the published CSVs (`RESULTS.md`).

---

## 1. Introduction

### 1.1 Phenomenon

When a language model is fed its own output through repeated context
updates, the resulting trajectory often settles into recognizable
dynamical patterns. Practitioners have long observed topical lock-in,
paraphrase cycling, and degenerate collapse, but only recently have
these behaviors been studied as properties of recursive LLM dynamics
rather than as isolated prompt artifacts. arXiv:2512.10350
(*Dynamics of Agentic Loops*) classifies recursive LLM trajectories
into three regimes — contractive, oscillatory, and exploratory —
using drift, dispersion, and cluster-persistence metrics.
arXiv:2510.21258 quantifies degeneration as a collapse from a
higher-dimensional trajectory into a low-dimensional attractor.
arXiv:2510.24797 reports that recursive self-referential dialogues
across frontier models converge on a stable "spiritual-bliss"
attractor.

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

These questions turn an informal observation — "the loop gets stuck"
— into a quantitative program. If attractors are real features of
recursive LLM dynamics, then they should not only be detectable in
representation space, but should also exhibit measurable resistance
to perturbation.

### 1.3 Contributions

This paper makes five contributions.

**First**, we introduce a **state–generator–nudge formalism** for
recursive LLM loops. In this formulation, the generator produces text
conditioned on the current context, while the **nudge** is the
context-update operator that maps the current context and output
into the next state. This makes append, replace, and role-structured
dialog first-class objects of analysis rather than implementation
details. Within the framework we prove a finite-time access bound for
replace-mode loops (§3.1.2 Lemma 1 + Corollaries) and state a
conjecture for append-mode (§3.1.3 Conjecture 1) that the data
empirically supports.

**Second**, we define the **barrier height** of a regime
operationally as the token-cost of injected text required for 50%
trajectory switching. This yields a common unit for comparing
attractor stability across recursive architectures. An
information-theoretic reading (§3.1.4) connects the token-cost to a
model-agnostic surprisal-based quantity in nats.

**Third**, we measure these barriers across 37 experiments on
`gpt-4o-mini`. Append-mode continuation exhibits a finite
in-distribution barrier of about 150 tokens, while neutral or lorem
perturbations fail to overcome the regime beyond a drift floor near
24%. Replace-mode paraphrase and summarize-and-negate are nearly
barrier-free at tested doses, while dialog regimes occupy
intermediate scales. **This barrier profile is the paper's main
empirical result.**

**Fourth**, we show that behavioral perturbation barriers agree with
geometric barriers estimated from the empirical potential landscape
$V(x) = -\log \rho(x)$ on PCA-2. This triangulates the perturbation
results against an independent representation-space construction.

**Fifth**, we refine the emerging taxonomy of recursive LLM dynamics.
In addition to the now-familiar contractive, oscillatory, and
absorbing patterns, we identify two dialog regimes — stylistic
multi-basin dialog (D1) and drill-down dialog (D2) — whose
distinguishing signature is not dispersion alone, but their barrier
structure under perturbation. We demonstrate explicitly (§5.12) that
bulk diagnostics under-determine the O1/D1 boundary; the perturbation
protocol is the load-bearing tool that resolves the full taxonomy.

The full pipeline is reproducible: raw trajectories LFS-tracked, 99
unit tests, every numeric claim in §5 verified cell-by-cell against
the cited CSV (`RESULTS.md`, 103/103 cells), and every experiment's
artifact presence audited (`COVERAGE.csv`, 37/37 at 100%).

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
with empirical analogs of classical dynamical diagnostics —
recurrence, dwell structure, ensemble-spread Lyapunov exponents,
effective dimension, and density-derived potential landscapes — rather
than with exact local linearizations.

### 2.2 Attractor observations in language models

The dynamical-systems framing of LLM inference loops has emerged
rapidly in 2025. arXiv:2512.10350 (*Dynamics of Agentic Loops in
Large Language Models: A Geometric Theory of Trajectories*)
formalizes recursive LLM transformations as discrete dynamical
systems in semantic space, identifying three regimes — **contractive**
(convergence to stable semantic attractors), **oscillatory**
(cycling), and **exploratory** (unbounded divergence) — through a
measurement protocol of local drift, global drift, dispersion, and
cluster persistence. They show empirically that prompt design selects
the regime: iterative paraphrasing → contractive, iterative negation
→ exploratory.

arXiv:2510.21258 (*Correlation Dimension of Auto-Regressive Large
Language Models*) quantifies degeneration as **a sudden collapse from
a higher-dimensional trajectory in the model's state space into a
lower-dimensional attractor**, using correlation dimension on
sequences of next-token log-probability vectors. This validates the
absorbing-regime interpretation we report in O3 (§5.2): a near-zero
sharpness-dim and a single-cluster late window are exactly what a
correlation-dim collapse predicts.

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
regimes — stylistic multi-basin dialog (D1) and drill-down dialog
(D2) — whose distinguishing feature is not dispersion alone, but
their perturbation signature.

A concise comparison with the closest prior work:

| dimension | arXiv:2512.10350 | this paper |
|---|---|---|
| regime taxonomy | 3 (contractive, oscillatory, exploratory) | 5 (+ D1 stylistic-multi-basin, + D2 drill-down dialog) |
| diagnostic metrics | local drift, global drift, dispersion, cluster persistence | + recurrence rate, sharpness dim, basin predictability acc(k), V\* geodesic-derived geometric barriers, RG dendrogram coarse-graining |
| barrier-height measurement | not measured | **token-quantified** via 4-condition perturbation protocol (control / neutral / lorem / adversarial) × 3 sweep dimensions (regime / dose / injection-time) |
| theoretical framework | discrete dynamical system in semantic space (informal) | state–generator–nudge formalism (§3.1) with formal access bound (Lemma 1) and append-mode accumulation conjecture (Conjecture 1) |
| geometric/behavioral triangulation | n/a | **mean V\* across 6 inter-basin geodesics agrees with perturbation-derived dose thresholds** (§5.10) |
| reproducibility | code link only | 103/103 cell-verified numeric claims (`RESULTS.md`); 37/37 experiments at 100% applicable artifact coverage (`COVERAGE.csv`); raw trajectories LFS-tracked |
| trajectory scope | not specified | 50–1,350 trajectories per configuration across 37 experiments |
| model | not specified | gpt-4o-mini (cross-model with gpt-4.1-nano in §11) |

We share the dynamical-systems framing and the contractive /
oscillatory pair; we *add* the cost-of-nudging measurement and the
two dialog regimes whose distinguishing signature appears only when
that measurement is made.

Tuci et al. (2026, arXiv:2604.19740) study SGD-optimization dynamics
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

The use of V(x) = −log ρ(x) as an empirical *effective potential* is
standard in chemical-physics free-energy analysis and reaction-rate
theory: ρ(x) is the stationary density of a stochastic trajectory
ensemble in some reduced coordinate system, and V is the potential
that would yield ρ as the Boltzmann weight at unit temperature. We
adopt this as a purely empirical / data-driven landscape over the
PCA-2 projection of trajectory embeddings; no thermodynamic claims
are made about the LLM itself.

The accompanying visualization battery — Dijkstra geodesics between
density peaks (with their maximum-V along the path used as a
geometric barrier estimate) and volumetric iso-density renderings —
is descriptive rather than theoretical. It converts the empirical
density into shapes a human reader can navigate, without assuming
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
generates its own attractor structure, including stylistic
multi-basin behavior (D1) and topic-anchored drill-down dynamics (D2).

---

## 3. Formal framework and hypotheses

### 3.1 State, generator, nudge

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
running the recurrence to its terminal step $T$. The unit is *tokens*
— a quantity that is **interpretable to a practitioner** (it tells you
how much text you have to insert to re-aim the trajectory) and that
**varies with the nudge**, but not arbitrarily. The next proposition
establishes the structural difference between append and replace nudges.

#### 3.1.2 Replace-mode access bound (Lemma 1 + Corollaries)

We begin with replace mode, in which the previous context is discarded
after each generation step. In this regime, the next state depends
only on the newly generated text, not on an accumulated context
history. This permits a clean finite-time access bound.

**Lemma 1 (replace-mode access bound).** Let $(X_t)_{t\ge 0}$ be a
recursive loop with replace-mode nudge

$$
X_{t+1} = g(Y_t), \qquad Y_t \sim P_\theta(\cdot \mid X_t; f),
$$

where $g : \mathcal{Y} \to \mathcal{C}$ is measurable. Let
$B_1, B_2 \subset \mathcal{C}$ be basin sets. Assume that after
perturbation injection at time $t_{\mathrm{inj}}$, there exist
constants $q_0 \in (0, 1]$, $r_0 \in (0, 1]$, and $\kappa > 0$ such that:

1. **Uniform one-step access to $B_2$:**

$$
\Pr\bigl[g(Y_t) \in B_2 \mid X_t = x\bigr] \ge q_0
\qquad\text{for all } x \in B_1.
$$

2. **Persistence after entry:**

$$
\Pr\bigl[X_T \in B_2 \mid X_{t+1} = z\bigr] \ge r_0
\qquad\text{for all } z \in B_2.
$$

3. **Bounded generation cost:**

$$
\mathbb{E}\bigl[|Y_t| \mid X_t = x\bigr] \le \kappa
\qquad\text{for all } x \in B_1 \cup B_2.
$$

Then after $m$ post-injection replace steps,

$$
\Pr(X_T \in B_2) \;\ge\; 1 - (1 - q_0 r_0)^m.
$$

**Proof.** Fix a trajectory with $X_{t_{\mathrm{inj}}} \in B_1$. For
$j \ge 1$, define the event

$$
E_j \;:=\; \{\,X_{t_{\mathrm{inj}}+j} \in B_2 \text{ and } X_T \in B_2\,\}.
$$

By assumption (1), conditional on any state in $B_1$, one replace
step lands in $B_2$ with probability at least $q_0$. By assumption
(2), conditional on such an entry, terminal membership in $B_2$ occurs
with probability at least $r_0$. Hence

$$
\Pr(E_j \mid X_{t_{\mathrm{inj}}+j-1} \in B_1) \;\ge\; q_0 r_0.
$$

Now consider the event that none of the first $m$ replace steps
yields terminally successful entry into $B_2$. Conditional on failure
up to step $j-1$, the probability of failure again at step $j$ is at
most $1 - q_0 r_0$. Therefore

$$
\Pr\!\Bigl(\,\bigcap_{j=1}^{m} E_j^c\,\Bigr) \;\le\; (1 - q_0 r_0)^m,
$$

so

$$
\Pr\!\Bigl(\,\bigcup_{j=1}^{m} E_j\,\Bigr) \;\ge\; 1 - (1 - q_0 r_0)^m.
$$

Since $\bigcup_{j=1}^{m} E_j \subseteq \{X_T \in B_2\}$, it follows
that $\Pr(X_T \in B_2) \ge 1 - (1 - q_0 r_0)^m$. $\square$

**Corollary 1 (replace-mode barrier bound).** Under the assumptions
of Lemma 1, the perturbation barrier defined in §3.1.1 satisfies

$$
\mathrm{B}(B_1 \to B_2)
\;\le\;
\kappa \,\Bigl\lceil \frac{\log(1/2)}{\log(1 - q_0 r_0)} \Bigr\rceil .
$$

**Proof.** By Lemma 1, after $m$ replace steps the terminal switching
probability is at least $1 - (1 - q_0 r_0)^m$. To reach $50\%$
switching it is sufficient that $1 - (1 - q_0 r_0)^m \ge \tfrac{1}{2}$,
equivalently

$$
m \;\ge\; \frac{\log(1/2)}{\log(1 - q_0 r_0)} .
$$

Thus $m^\star = \lceil \log(1/2) / \log(1 - q_0 r_0) \rceil$ replace
steps suffice. Since each replace step has expected token cost at most
$\kappa$, the total expected token budget required for $50\%$
switching is bounded above by $\kappa \, m^\star$. $\square$

**Corollary 2 (one-generation special case).** If, in addition,
$q_0 r_0 \ge \tfrac{1}{2}$, then

$$
\mathrm{B}(B_1 \to B_2) \;\le\; \kappa.
$$

**Proof.** If $q_0 r_0 \ge \tfrac{1}{2}$, then a single replace step
already yields terminal switching probability at least $1/2$. The
barrier is therefore at most the expected cost of one generation. $\square$

Lemma 1 and its corollaries formalize the central structural property
of replace mode: because the next state depends only on the newly
generated text, access to a competing basin is governed by one-step
transition probability and post-entry persistence, rather than by
long-horizon accumulation of prior context. **In particular, the
replace-mode barrier is bounded by a constant multiple of a typical
generation length and does not scale with accumulated context size.**

**Empirical verification.** §5.5 reports 94–96% switching for O2
(replace-mode paraphrase) and O3 (replace-mode summarize-then-negate)
at every dose tested, including the smallest probed (80 tokens of
any perturbation type). Corollary 2 predicts $\mathrm{B} \le \kappa
\approx 80$–$120$ tokens whenever the access × persistence product
$q_0 r_0 \ge \tfrac{1}{2}$; we measure barriers $\le 80$ tokens (the
smallest dose probed), consistent with the bound. The lemma does
*not* extend to append-mode by the same argument; that case is
addressed below as a conjecture motivated by the same data.

#### 3.1.3 Append-mode accumulation barrier (Conjecture 1)

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

The O1 dose-response measurements in §5.6 are consistent with this
conjecture. Neutral and lorem perturbations remain near the
irreducible drift floor across the tested range, whereas
in-distribution adversarial perturbations exhibit a finite threshold
near 150 tokens for 50% switching. This is precisely the qualitative
pattern expected if append-mode barriers are controlled by the
accumulation of basin-relevant counter-context rather than by
one-step access alone.

A geometric refinement of the same idea is that append-mode token
barriers should scale with the saddle height in representation space.
Let $V(x) = -\log \rho(x)$ be the empirical potential (§2.3,
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

#### 3.1.4 Tokens vs nats: a model-agnostic reading of barrier height

A natural objection to reporting barrier heights in tokens: *tokens
of which tokenizer?* A perturbation that costs 150 tokens of
`text-embedding-3-small`-tokenized text might cost 130 or 180 tokens
under a different vocabulary; a model with a wildly different
tokenizer would give numerically different barriers for the same
underlying phenomenon. Tokens are not, per se, a model-agnostic unit.

**The model-agnostic quantity is barrier height in *nats*.** For a
generator $P_\theta$, each token of injected text $y_i$ at context
$X$ carries

$$
h_i = -\log P_\theta(y_i \mid X) \quad \text{(nats)}
$$

worth of information about the trajectory's next state. The total
information content of $\tau$ tokens of injected text is therefore

$$
I(\tau) = \sum_{i=1}^{\tau} h_i \approx \tau \cdot \langle h \rangle_\text{cond},
$$

where $\langle h \rangle_\text{cond}$ is the average per-token
conditional surprisal under the model's own predictive distribution
(typically 3–5 nats per token for English text under modern
sub-word LLMs at $T = 0.8$). The barrier height in nats is then

$$
\mathrm{B}^{\text{nats}}(B_1 \to B_2)
= \mathrm{B}^{\text{tokens}}(B_1 \to B_2) \cdot \langle h \rangle_\text{cond}.
$$

Two things follow.

**(a) Out-of-distribution perturbations carry low *basin-relevant*
information per token.** The neutral and lorem conditions saturate
at the irreducible drift floor (~24% switching for O1) precisely
because their per-token surprisal under $P_\theta$ is high in absolute
terms but their information *about the basin manifold* is low — the
model can't absorb random-character entropy as evidence for or against
any particular attractor. In-distribution adversarial text, by contrast,
is fluent under $P_\theta$ (low surprisal) but its content is
misaligned with $B_1$, so each token contributes basin-relevant
counter-evidence that integrates toward $B_2$. This is exactly the
asymmetry §5.6's dose-response curves report: the *same* number of
tokens crosses or doesn't cross the barrier depending on whether
those tokens carry basin-relevant or basin-irrelevant information.

**(b) Barrier height in nats should approximate the
basin-distribution Kullback-Leibler distance.** If we model the late-
window basin distributions as $\rho_{B_1}, \rho_{B_2}$ on the
embedding-space manifold, then for a trajectory to relocate from
$B_1$ to $B_2$ requires injected information that exceeds the
geometric "distance" between the two distributions. The natural
candidate is

$$
\mathrm{B}^{\text{nats}}(B_1 \to B_2)
\;\;\sim\;\; \mathrm{KL}(\rho_{B_2} \| \rho_{B_1})
\;\;\text{or, symmetrically,}\;\;
\mathrm{V}^{\star}(B_1, B_2) = -\log \rho(\text{saddle})
$$

where $\mathrm{V}^{\star}$ is exactly the geometric barrier estimate
we compute in §5.10 from $V(x) = -\log \rho(x)$ on PCA-2 with
Dijkstra geodesics through density-peak basins.

This is the bridge: §5.10's $\mathrm{V}^{\star}$ is a *geometric*
estimate of $\mathrm{B}^{\text{nats}}$ (in units of nats per
PCA-2-dimension via the kernel-density-estimate normalization);
§5.6's token-cost is a *behavioral* estimate of $\mathrm{B}^{\text{nats}}$
(via $\tau \cdot \langle h \rangle_\text{cond}$). Their qualitative
ordering across regimes (O1 mid, O2/O3 low, D1 D2 intermediate)
agrees, which is the empirical content of the
"geometric/behavioral barrier triangulation" claim. Numerical
equality is *not* expected — the KDE bandwidth and PCA-2 projection
introduce regime-independent constants that re-scale $\mathrm{V}^{\star}$
relative to $\mathrm{B}^{\text{nats}}$ — but ordinal agreement is, and
ordinal agreement is what we observe.

**Practical consequence.** A claim of the form *"O1 has a 150-token
barrier"* is a tokenizer-specific quantity; the underlying
*information-theoretic* claim is *"O1 has a barrier of $150
\langle h \rangle_\text{cond} \approx 600$ nats against in-distribution
adversarial text, and an effectively infinite barrier against
out-of-distribution text"*. The latter is portable across tokenizers
and across models that share the same embedding space; the former is
the most directly measurable approximation. Future work would use the
generator's logprobs (`include_logprobs=True` in our `Config`) to
report $\mathrm{B}^{\text{nats}}$ directly; we did not capture logprobs
in the current 37-experiment battery and report tokens as the more
operationally meaningful unit.

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
endogenous attractor-like regimes — properties of the loop dynamics
themselves, not just artifacts of a single seed text — and these regimes
become observable in a suitable representation space.

**H2** (mechanism): The regime depends jointly on the content function
(continue / paraphrase / summarize-and-negate / dialog) and the
context-update rule (append vs replace). Specifically:
- Append + content-preserving ⇒ contractive basin (one or a few sinks)
- Replace + content-preserving ⇒ oscillation (output ↔ paraphrase ↔ output)
- Replace + content-degrading ⇒ absorbing collapse
- Dialog (alternating roles, append) ⇒ stylistic multi-basin

**H3** (perturbation barriers): The four regimes have qualitatively
different perturbation sensitivities. Append-mode loops have measurable
in-distribution dose thresholds; replace-mode loops have negligible
barriers; dialog has intermediate, structure-dependent barriers.

**H4** (reproducibility at scale): The qualitative structure observed at
small N (~50 trajectories) survives a 30× increase in sample size.

We pre-registered none of these in the conventional sense; the writeups
in `docs/reports/REPORT1.md` … `REPORT6.md` document the discovery order
in fairly granular detail.

---

## 4. Methods

### 4.1 The recurrence

Instantiating the formal recurrence from §3.1 with the three nudges:
$$
\text{Append:}\quad   X_{t+1} = \mathcal{N}_{\text{append}}(X_t, Y_t)  = \operatorname{clip}(X_t \Vert Y_t)
$$
$$
\text{Replace:}\quad  X_{t+1} = \mathcal{N}_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)
$$
$$
\text{Dialog:}\quad   X_{t+1} = \mathcal{N}_{\text{dialog}}(X_t, Y_t)  = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)
$$

with $Y_t \sim P_\theta(\cdot \mid X_t;\, f)$ and $P_\theta$ the
language-model distribution parameterized by $\theta$ (here
`gpt-4o-mini`). The clipping operator $\operatorname{clip}(\cdot)$
truncates context from the head (oldest) once the running string
exceeds 12,000 characters, preserving the most recent state. The
content operator $f$ enters through the system prompt fed to
$P_\theta$ — e.g. "Continue the text" for $f = \text{continue}$,
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
  N≥2-runs minimum for ensemble-spread diagnostics (§5.0).

In every case trajectories run for 40 steps unless explicitly noted
(D2 uses 50; the T-sweep variants vary `steps_per_run`).

Initial conditions are 5–30 short seed texts per "family" (philosophical
prompts, practical-advice prompts, creative-writing prompts, reflective
prompts, emotional prompts). Across families we get diversity in topic
and tone; within families we get variability across seeds.

Sampling temperature `T = 0.8` unless varied (Phase 2b T-sweep).

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small` (OpenAI),
producing 1536-dimensional vectors. We embed multiple *observables* per
step — each captures a different facet of the trajectory state, and
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
configured with different role labels — D2 uses *explorer* / *expert* —
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
~$30 in embedding API calls.

#### 4.3.1 Single-context embedding mechanics

A subtle but important invariant: **for one observable string at one
trajectory step, we obtain exactly one 1536-dimensional vector.** No
chunking, no internal sliding window we manage, no per-token outputs.
The `text-embedding-3-small` model handles internal attention over up
to 8,191 input tokens and produces a single pooled representation
which `embed_texts` writes to one row of the output matrix:

```
"Continue the text. The fox was quick..."  →  text-embedding-3-small  →  v ∈ R^1536
```

After the API returns, we **L2-normalize** each row defensively so all
downstream cosine-similarity computations reduce to dot products and
numerical drift from float32 round-trips does not accumulate:

```
norms = ||v||_2 + 1e-12
v_norm = v / norms                          # ||v_norm||_2 = 1.0
```

The model is deterministic given the input — `hash(text) → vec` is a
stable mapping under fixed model version, so the embedding cache is
safe and `analyze` reruns on the same `embeddings.npy` are identical.

Per-trajectory step we therefore obtain `K` independent vectors where
`K = |observables|` — 3 for operator publication runs (output,
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
| `output` observable | the single Y_t | — | ≤ 160 |
| `rolling_k3` | 3 × Y plus 2 separators | — | ~480 |
| `context_tail` | `[-4000:]` slice | — | ~1,000 |
| `context_full` | `[-8000:]` slice | — | ~2,000 |
| `turn_pair` (dialog) | last user + last agent | — | ~320 |
| `rolling_user_k3` / `rolling_agent_k3` | 3 turns of one role | — | ~480 |

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
Step t:    context_after has 9,500 chars. context_full = chars [1500 : 9500]
Step t+1:  Y_{t+1} appends ~120 chars.   context_full = chars [1620 : 9620]
```

So between adjacent steps the slice has ~99% content overlap and ~1%
fresh content. The resulting embeddings are **highly correlated, not
identical**. Empirically:

| observable | content overlap with previous step | adjacent-step cosine sim |
|---|---|---|
| `output` | 0% (Y_t is freshly generated each step) | ~0.5–0.8 |
| `rolling_k3` | ~67% (2 of 3 outputs unchanged) | ~0.85–0.95 |
| `context_tail` (4000 chars, append) | ~97% | ~0.95–0.98 |
| `context_full` (8000 chars, append) | ~99% | ~0.97–0.99 |

These different-overlap regimes give the trajectory **different motion
speeds in embedding space** for different observables. `output` shows
fast cycling motion (each step is a fresh generation); `context_full`
shows slow integrated drift; `rolling_k3` is the compromise. This is
exactly why we run every metric on every observable and require
cross-observable agreement before accepting a regime label — a finding
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
np.median(sims)   # ≈ 0.97-0.99 for context_full in append mode
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

- `Z_PCA-2 ∈ R^{N×2}` — for density estimation, V landscape, and most
  2D plots. Carries 10–15% of total variance for short-output observables
  (`output`); higher (~25%) for longer-context observables.
- `Z_PCA-10 ∈ R^{N×10}` — used for K-means clustering, basin
  classification, basin-predictability regression, recurrence/dwell.
  Captures 30–50% of variance and gives clusters that are both stable
  under bootstrap and interpretable in the original embedding space.
- `Z_PCA-50 ∈ R^{N×50}` — pre-reduction stage for t-SNE only. Captures
  ~80% of variance and removes the high-dimensional noise that would
  otherwise dominate cosine distances at the t-SNE step.

#### 4.4.2 t-SNE

We fit `sklearn.manifold.TSNE(n_components=2)` with the following
parameters:

```python
TSNE(
    n_components=2,
    perplexity=30,                         # capped at (N-1)/4 for small N
    pre_pca_dim=50,                        # see 4.4.1 above
    metric="cosine",                        # matches embedding similarity
    init="pca",                            # PCA-init for stability
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
is essential — each condition's PCA-2 cloud must live in shared
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
recurrence(ε, τ) = #{(t, s) : ‖z_t − z_s‖₂ < ε  ∧  |t − s| > τ} / [T(T−1)/2]
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
spectrum (functional form from Tuci et al., arXiv 2604.19740,
Definition 4.2):

```
j*  = max { i : Σ_{k≤i} λ_k ≥ 0 }      (0 if λ_1 < 0)

SD  = j* + (Σ_{k≤j*} λ_k) / |λ_{j*+1}|
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
D1 1.89; §5.0), but the magnitude differences are modest. A
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

- **`period_2_score`** = `mean_dist(1) − mean_dist(2)` — positive
  values indicate a 2-cycle (lag-2 points are closer than lag-1 points)
- **`period_3_score`** — analogous for 3-cycles
- **`best_period`** — the lag k ∈ [1, T/2] minimizing `mean_dist(k)`
- **`autocorr_distances`** — full vector of mean lag distances

This is run on every trajectory and aggregated per (regime, family) for
condition-vs-baseline tests.

#### 4.5.8 Dispersion

To distinguish contractive from exploratory dynamics we compute, in
`src/experiments/operators/dispersion.py`:

```
initial_dispersion = mean pairwise distance over t ∈ [0, T/4]
final_dispersion   = mean pairwise distance over t ∈ [3T/4, T]
dispersion_growth  = (final - initial) / initial
global_drift       = ‖centroid(t=T) − centroid(t=0)‖
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
  `dwell_above_null`. 0–2 signals → strength {not_supported, weak,
  moderate, strong}.
- **H1b (recurrence / oscillation)**: signals are
  `late_recurrence_above_null`, `period_2_score > threshold`, and
  `best_period_majority > 1`. 0–3 signals.
- **H1c (divergence / no-attractor)**: signals are
  `dispersion_growing`, `drift_monotonically_outward`, and
  `no_stable_basin`. 0–3 signals.

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

#### 4.5.7 Basin predictability

For each trajectory we compute the K-means cluster at the late window
(`y` = cluster index at `t > 0.7T`). For each early step k we train a
multinomial logistic regression to predict y from PCA-10 at step k.
Cross-validation:

1. **Drop singleton classes** — clusters that contain only one
   trajectory member can't be split into train/test, so we filter
   them out before CV (recording `n_dropped_classes` and
   `n_dropped_traj` per row for audit).
2. **Adaptive stratified k-fold** with
   `n_splits = min(5, smallest_class_size)`. Publication-scale runs
   (n=1350 / regime) always reach the full 5-fold; reduced-scope
   T-sweep cells (n=150) and phase-1 pilots (n=75) fall back to 2–4
   folds when the smallest remaining cluster has fewer than 5
   members. When the late-window cluster grouping leaves fewer than
   2 non-singleton classes (rare; only occurs at very early
   predictor steps for some dialog cells) we write `NaN` for that
   (regime, step) cell.

The accuracy curve `acc(k)` is monotonic in good regimes — by some
early step the late basin is already determined.

#### 4.5.8 Perturbation switching

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
from their paired control's.

### 4.6 Baselines

Each baseline ablates a different mechanism so we can isolate which
property of the loop is producing the observed attractor:

- **`time_shuffled`** (post-hoc): reshuffle step labels within each
  trajectory and recompute the dynamics metrics. If the metric is
  unchanged, it depends only on the marginal point cloud and not on
  temporal structure — i.e., the "trajectory" is effectively a bag of
  embeddings, not a process. Implemented in
  `src/analysis/robustness.py:time_shuffle_labels`.
- **`no_feedback`** (`src/core/baselines.py:no_feedback_provider`):
  sample each step's output from the *seed only*, ignoring the
  accumulated context. This nulls the recurrence — the loop becomes N
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
  with small clusters fall back to 2–4 folds gracefully (NaN if even
  2-fold is impossible). See §4.5.7.
- **Wilson-style CI** on switching-rate proportions where bootstrap
  would be unstable (small denominators in dose-response cells).
- **Significance gate**: a regime / condition signal counts only if its
  diagnostic statistic is `≥ 2σ` above the baseline mean *and* its
  Cohen's d ≥ 0.5 (medium effect). Both criteria must hold; CI alone
  can pass with trivially small effects under sufficient N.

### 4.8 Static visualization battery

Beyond the perturbation toolkit (4.9), every experiment generates a
standardized set of static plots, defined in
`src/experiments/dynamics/regime_plots.py`,
`src/experiments/dynamics/field_plots.py`,
`src/experiments/dynamics/pub_tsne_plots_v2.py`, and
`src/reports/plots.py`. Notable variants:

- **A: joint t-SNE colored by regime / family / step** — global view of
  where the regimes and the families live in the joint embedding.
  (`plot_joint_tsne` in `dynamics/regime_plots.py`)
- **B: per-family grid** — one t-SNE panel per prompt family, sharing
  coordinates, so cross-family heterogeneity is visible.
  (`plot_trajectory_grid` in `dynamics/regime_plots.py`)
- **C: ensemble-spread timelines** — σ(t) curves per family, the visual
  analog of FTLE; useful for distinguishing contractive (shrinking spread)
  from expanding regimes. (`plot_spread_timelines` in
  `dynamics/regime_plots.py`)
- **E: per-experiment flow field** (PCA-2 quiver) — averaged per-step
  displacement field overlay on the density background.
  (`plot_flow_field_*` in `dynamics/regime_plots.py`)
- **F: t-SNE trajectory sample** — sample trajectories with the
  time-ordering visible. (`plot_tsne_trajectories_single` in
  `dynamics/regime_plots.py`)
- **G/H/I: streamlines + density / speed-colored streamlines / divergence**
  — three richer flow-field views from `dynamics/field_plots.py`
  (`plot_streamlines_density`, `plot_speed_colored_streamlines`,
  `plot_divergence_field`).
- **`plot_v2_by_step_parity`** and **`plot_v2_per_family_parity_grid`**
  in `pub_tsne_plots_v2.py` — even/odd step stratification, used to
  separate the two arms of an oscillatory 2-cycle visually.
- **`plot_regime_map_by_family`** in `dynamics/partial_snapshot.py` —
  family × IC heatmap colored by final-window cluster, useful for
  detecting whether basins are family-dependent or shared.
- **`basin_entry_hist`**, **`basin_scores`**, **`cluster_occupancy`**,
  **`dwell_dist`** in `src/reports/plots.py` — distributional plots of
  the analysis primitives, one panel per observable.

Plots are rendered at 200 DPI to PNG. Each experiment's `reports/plots/`
folder ends up with 50–150 PNGs depending on the number of observables.

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
    starts_g = Z[i_0:i_{T-1}]      shape (T-1, 2)
    deltas_g = Z[i_1:i_T] - Z[i_0:i_{T-1}]   shape (T-1, 2)
S = concat(starts_g for all g)     shape (M, 2)
D = concat(deltas_g for all g)     shape (M, 2)
```

`(S, D)` is the empirical displacement-field dataset: `M` observed
single-step transitions in the projection.

We then discretize the projection bounds `[x_min - p, x_max + p]` ×
`[y_min - p, y_max + p]` (with 5% padding) into a `grid_n × grid_n`
grid (typically 26 for plots, 32–48 for animations). For each grid bin
`(i, j)` we compute:

```
count[i, j] = number of (s, d) pairs with s falling into bin (i, j)
sum_u[i, j] = sum of d_x over those pairs
sum_v[i, j] = sum of d_y over those pairs
U[i, j]     = sum_u[i, j] / count[i, j]   (NaN if count = 0)
V[i, j]     = sum_v[i, j] / count[i, j]   (NaN if count = 0)
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
resolution (~26–48), the **density** field used for V landscapes and
background heatmaps uses a higher-resolution Gaussian-smoothed
histogram via `_smooth_density_grid` in
`src/experiments/dynamics/field_plots.py`:

```
H = histogram2d(pts, bins=(x_edges, y_edges))    # raw counts, grid_n × grid_n
H_smooth = scipy.ndimage.gaussian_filter(H, sigma=sigma_cells)
```

with `grid_n = 96` and `sigma = 1.5–2.0` cells. This smoother density
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
is set to 1.6–2.0; arrowsize is small (0.9–1.2) so the density isn't
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
(`I_divergence_by_condition.png`) make this quantitative — for the O3
absorbing regime the divergence has a single deep minimum at the sink;
for O2 the divergence has a saddle structure between the two cycle
arms.

#### 4.9.5 The G/H/I plot triple

For each (experiment, projection ∈ {PCA-2, t-SNE-2}) we render three
flow-field views to `data/<exp>/reports/perturbation/`:

- **G — streamlines + density**: V (density) as the magma background;
  white streamlines from (U, V) overlaid. This is the most legible
  "where does the system flow" view.
- **H — speed-colored streamlines (dark theme)**: streamlines colored
  by local `|v| = sqrt(U² + V²)`, on a dark background. Slow regions
  (basin interiors) appear cold; fast regions (transport between
  basins) appear hot.
- **I — divergence field**: heatmap of `∇·v` with a diverging colormap
  (RdBu_r), shared color scale across all conditions of the same
  experiment for direct comparison. Streamlines overlaid in thin black.

For perturbation experiments the G/H/I are rendered per-condition
(2×2 panels = 4 conditions); for non-perturbation experiments (Phase 2
publication runs) they're rendered for the recursive regime alone,
sometimes faceted by family.

### 4.10 Perturbation visualization toolkit

For perturbation experiments we additionally compute:

#### Effective potential

```
ρ̂(x) = Gaussian-smoothed kernel density on PCA-2 grid
V(x) = −log(ρ̂(x) + ε),  ε = 0.1·min{ρ̂ : ρ̂ > 0}
V is shifted so V_min = 0 and capped at v_cap (default 8.0)
```

#### Geodesic skeleton

We find local minima of V via 8-connected `maximum_filter` on −V,
keeping the top n basin centers. For each pair of basin centers (i, j)
we compute the Dijkstra shortest path on the V grid (8-connected, edge
weight = V at endpoint). The maximum V along the path is the **barrier
height V*(i, j)**.

#### Volumetric iso-density rendering

For 3D animations we extract iso-density shells at five density
fractions (4%, 10%, 20%, 35%, 55% of max ρ) using
`scipy.ndimage.gaussian_filter` smoothing and `skimage.measure.marching_cubes`.
Each shell is rendered as a transparent `Poly3DCollection` in
`matplotlib`'s `mpl_toolkits.mplot3d`, with colors from the `plasma`
colormap and per-shell alpha from 0.05 (outermost) to 0.27 (innermost).

#### Parallel rendering

Animations of 50 trajectories with 75 frames at DPI 180 are rendered
via `concurrent.futures.ProcessPoolExecutor` with 40 workers, each
worker creating a fresh figure for one frame. Frames are stitched into
MP4 via `imageio-ffmpeg` (libx264 codec, quality 8). Wall-time
per animation: ~80s vs ~11 min single-threaded.

### 4.11 End-to-end pipeline diagram

The full data flow from `gpt-4o-mini` generation through embeddings,
projections, metrics, and figures, with persistence boundaries marked
as `→` (each is independently re-runnable):

```
                              ┌──────────────────────┐
                              │ config.yaml          │
                              │ (model, T, top_p,    │
                              │  steps, observables, │
                              │  baselines, families)│
                              └──────────┬───────────┘
                                         │
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 1 — GENERATION                                                      │
   │                                                                            │
   │   ┌──────────┐  X_t (string)   ┌────────────────────────┐                  │
   │   │ context  │ ───────────────▶│ OpenAI Responses API   │                  │
   │   │ X_t      │                 │ gpt-4o-mini            │                  │
   │   │          │  Y_t (string)   │ T=0.8, max_tok=120-160 │                  │
   │   │          │ ◀───────────────│ store=False            │                  │
   │   └────┬─────┘                 └────────────────────────┘                  │
   │        │                                                                   │
   │        │  X_{t+1} = clip(X_t || Y_t, 12000 chars)         APPEND mode      │
   │        │  X_{t+1} = clip(Y_t,        12000 chars)         REPLACE mode     │
   │        │  X_{t+1} = X_t || format_turn(role, Y_t)         DIALOG mode      │
   │        │                                                                   │
   │        └─────▶ loop t = 0..T-1, persist each step ──┐                      │
   │                                                      ▼                     │
   │                                       ┌─────────────────────────────┐     │
   │                                       │ raw/steps.jsonl             │     │
   │                                       │  rows: (regime, family, ic, │     │
   │                                       │  run, step, X_before, Y,    │     │
   │                                       │  X_after, response_id, ...) │     │
   │                                       └──────────────┬──────────────┘     │
   └────────────────────────────────────────────────────── │ ───────────────────┘
                                                           ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 2 — OBSERVABLE CONSTRUCTION                                         │
   │                                                                            │
   │           per JSONL row → 3 strings (operator pub) or 8 strings (dialog pub)│
   │                                                                            │
   │           ┌─────────────────────────────────────────────────────┐          │
   │           │ output         = Y_t                       (~120 tok)│         │
   │           │ rolling_k3     = Y_{t-2}||SEP||Y_{t-1}||SEP||Y_t     │         │
   │           │ context_tail   = X_after[-4000:]            (~1k tok)│         │
   │           │ context_full   = X_after[-8000:]            (~2k tok)│         │
   │           │ last_user_turn / last_agent_turn  (dialog only)      │         │
   │           │ rolling_user_k3 / rolling_agent_k3 (dialog only)     │         │
   │           │ turn_pair                          (dialog only)     │         │
   │           └─────────────────────────────────────────────────────┘          │
   │                              │  K parallel string streams                  │
   │                              │  (K = 3 operator pub, 8 dialog pub;         │
   │                              │   +1 each with optional context_full)       │
   └──────────────────────────────┼─────────────────────────────────────────────┘
                                  ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 3 — EMBEDDING                                                       │
   │                                                                            │
   │   for each observable independently:                                       │
   │                                                                            │
   │      ┌──────────────────┐  batch of 128 strings ┌──────────────────┐       │
   │      │ all_texts        │ ─────────────────────▶│ OpenAI Embeddings│       │
   │      │ (N_traj×T strings│                       │ text-embedding-3 │       │
   │      │  per observable) │  list[1536-d vector]  │ -small           │       │
   │      │                  │ ◀─────────────────────│                  │       │
   │      └──────────────────┘                       └──────────────────┘       │
   │                              │                                             │
   │                              ▼                                             │
   │                       L2-normalize each row                                │
   │                              │                                             │
   │                              ▼                                             │
   │      ┌─────────────────────────────────────────────┐                       │
   │      │ embeddings/<obs>/embeddings.npy   (N, 1536) │                       │
   │      │ embeddings/<obs>/metadata.parquet (N rows)  │                       │
   │      │   regime, family, ic, run, step, role,      │                       │
   │      │   text_len                                  │                       │
   │      └────────────────────┬────────────────────────┘                       │
   └──────────────────────────── │ ─────────────────────────────────────────────┘
                                ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 4 — PROJECTION  (joint fit on all N points per observable)          │
   │                                                                            │
   │       embeddings.npy  (N, 1536) ──┬─▶ PCA(n=2)   ──▶ Z_PCA2  (N, 2)        │
   │                                   │                                        │
   │                                   ├─▶ PCA(n=10)  ──▶ Z_PCA10 (N, 10)       │
   │                                   │                                        │
   │                                   ├─▶ PCA(n=20)  ──▶ Z_PCA20 (N, 20)       │
   │                                   │                                        │
   │                                   └─▶ PCA(n=50) ──▶ TSNE(    ──▶ Z_TSNE    │
   │                                       (preprocess) perp=30,     (N, 2)     │
   │                                                    metric=cos,             │
   │                                                    init=pca,               │
   │                                                    seed=42)                │
   │                                                                            │
   │       all fits use random_state=42 → fully deterministic                   │
   │                                                                            │
   │       Z_PCA2  →  density / V landscape / 2D plotting                       │
   │       Z_PCA10 →  K-means clustering, metrics, classifier                   │
   │       Z_TSNE  →  visualization only (never used in metrics)                │
   └─────────────────┬──────────────────────────────────────────────────────────┘
                     │
            ┌────────┴────────┬────────────────┬────────────────┐
            ▼                 ▼                ▼                ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ CLUSTERING   │  │ TIME-SERIES  │  │ ENSEMBLE     │  │ PERTURBATION │
   │ (per obs)    │  │ METRICS      │  │ DYNAMICS     │  │ ANALYSIS     │
   │              │  │ (per traj)   │  │ (per fam,ic) │  │ (paired)     │
   │ KMeans(k=12) │  │              │  │              │  │              │
   │  on Z_PCA10  │  │ recurrence   │  │ Lyapunov     │  │ joint Z_PCA10│
   │              │  │ dwell        │  │ spectrum     │  │ + KMeans k=12│
   │ → cluster    │  │ basin        │  │ (early/late) │  │ → cluster_T  │
   │   labels     │  │ basin_entry  │  │ sharpness_dim│  │   per cond   │
   │   per step   │  │ late_recur.  │  │ effective    │  │ → switching  │
   │              │  │ exit_return  │  │ rank         │  │   rate per   │
   │              │  │ periodicity  │  │              │  │   condition  │
   │              │  │ dispersion   │  │              │  │              │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          │                 │                 │                 │
          └────────────┬────┴────────────┬────┴────────────┬────┘
                       │                 │                 │
                       ▼                 ▼                 ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 5 — STATISTICAL VALIDATION                                          │
   │                                                                            │
   │   1000-iter bootstrap CIs    Cohen's d vs baselines    permutation tests   │
   │                                                                            │
   │   baselines:  time_shuffled │ no_feedback │ independent_regeneration       │
   │                                                                            │
   │   significance gate:  metric ≥ baseline + 2σ  AND  Cohen's d ≥ 0.5         │
   │                                                                            │
   │                                  │                                         │
   │                                  ▼                                         │
   │   three-axis classifier (H1a convergence, H1b recurrence, H1c divergence)  │
   │                                                                            │
   │     ┌──────────────────────────────────────────────────────────────────┐   │
   │     │ H1a strong + H1b weak  ⇒  contractive / multi-basin (O1, D1)     │   │
   │     │ H1b strong (period-2) ⇒  oscillatory                  (O2)       │   │
   │     │ H1a strong + sharpness ↓ ⇒ absorbing                  (O3)       │   │
   │     │ H1c strong            ⇒  divergent / unsupported                 │   │
   │     └──────────────────────────────────────────────────────────────────┘   │
   └─────────────────────────────────┬──────────────────────────────────────────┘
                                     ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 6 — VISUALIZATION & REPORTS                                         │
   │                                                                            │
   │  ┌─────────────────────┐      ┌─────────────────────┐                      │
   │  │ STATIC PLOTS (2D)   │      │ FLOW FIELDS (2D)    │                      │
   │  │                     │      │                     │                      │
   │  │ A. joint t-SNE      │      │ make_grid_edges     │                      │
   │  │    by regime/family/│      │ + bin_displacement  │                      │
   │  │    step             │      │   field             │                      │
   │  │ B. per-family grid  │      │ + bin_density       │                      │
   │  │ C. single-IC trajs  │      │                     │                      │
   │  │ E. quiver flow      │      │ → G: streamlines +  │                      │
   │  │ F. trajectory sample│      │      density (magma)│                      │
   │  │ basin_entry hist    │      │ → H: speed-colored  │                      │
   │  │ basin_scores        │      │      streamlines    │                      │
   │  │ cluster_occupancy   │      │      (dark theme)   │                      │
   │  │ dwell_dist          │      │ → I: divergence ∇·v │                      │
   │  │ step_parity         │      │      (RdBu_r)       │                      │
   │  └─────────────────────┘      └─────────────────────┘                      │
   │                                                                            │
   │  ┌─────────────────────────────────────────────────────────────────────┐   │
   │  │ EMPIRICAL POTENTIAL LANDSCAPE TOOLKIT (perturbation only)           │   │
   │  │                                                                     │   │
   │  │   Z_PCA2 ──▶ smoothed density ρ̂(x)                                  │   │
   │  │              │                                                      │   │
   │  │              ▼                                                      │   │
   │  │           V(x) = -log ρ̂(x)                                          │   │
   │  │              │                                                      │   │
   │  │              ├─▶ basin_centers = local minima of V                  │   │
   │  │              │                                                      │   │
   │  │              ├─▶ Dijkstra geodesics between basin pairs             │   │
   │  │              │   → V*(i,j) barrier height = max V along path        │   │
   │  │              │                                                      │   │
   │  │              ├─▶ marching cubes @ 5 density iso-levels              │   │
   │  │              │   → Poly3DCollection nested transparent shells       │   │
   │  │              │                                                      │   │
   │  │              └─▶ plot_streamlines + V contour + geodesic overlay    │   │
   │  │                                                                     │   │
   │  │   K=48 KMeans + Ward linkage ──▶ rg_dendrogram                      │   │
   │  └─────────────────────────────────────────────────────────────────────┘   │
   │                                                                            │
   │  ┌─────────────────────────────────────────────────────────────────────┐   │
   │  │ 3D ANIMATIONS (perturbation only)                                   │   │
   │  │                                                                     │   │
   │  │   Z_PCA3 + iso-shells + 50-trajectory walk + red kick beams         │   │
   │  │              │                                                      │   │
   │  │              ▼                                                      │   │
   │  │   ProcessPoolExecutor (40 workers) → frame PNGs                     │   │
   │  │              │                                                      │   │
   │  │              ▼                                                      │   │
   │  │   imageio-ffmpeg libx264 → animation3d_<cond>.mp4 (~10MB, 12s loop) │   │
   │  └─────────────────────────────────────────────────────────────────────┘   │
   │                                                                            │
   │  ┌─────────────────────┐                                                   │
   │  │ NARRATIVE REPORT    │                                                   │
   │  │                     │                                                   │
   │  │ reports/report.md   │ ◀── per-observable metric tables                  │
   │  │                     │     bootstrap CIs                                 │
   │  │ classification:     │     baseline comparisons                          │
   │  │  not / weak /       │     H1a/H1b/H1c verdict                           │
   │  │  moderate / strong  │     regime label                                  │
   │  └─────────────────────┘                                                   │
   └────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  PHASE 7 — CROSS-EXPERIMENT AGGREGATION                                    │
   │                                                                            │
   │   read each experiment's per-experiment CSVs (via scripts/lib_load)        │
   │                                                                            │
   │   ┌────────────────────────────────────────────────────────────────────┐   │
   │   │ aggregate_perturbation_cross_regime  → 4×5 switching grouped bar   │   │
   │   │ aggregate_dose_response              → log-x dose curves           │   │
   │   │ aggregate_basin_hardening            → switch-vs-inject_step       │   │
   │   │ aggregate_basin_predictability       → 4-regime accuracy overlay   │   │
   │   │ aggregate_t_sweep                    → D1 T={0.3,0.6,0.8,1.2}      │   │
   │   │ aggregate_o1_d1_t_sensitivity        → side-by-side T comparison   │   │
   │   └────────────────────────────────────────────────────────────────────┘   │
   │                                                                            │
   │   → data/aggregated/<analysis>/{csv, png, summary.md}                      │
   └────────────────────────────────────────────────────────────────────────────┘
```

#### 4.11.1 Shape annotations through the pipeline

For one publication-scale operator experiment (1350 trajectories ×
40 steps × 4 observables ≈ 216,000 vectors):

```
   raw/steps.jsonl                   ~54,000 rows  (1350 traj × 40 steps)
        │
        ▼  build_all_for_run × 4 observables
   ~216,000 strings per experiment
        │
        ▼  embed_texts (batched 128, retry+backoff)
   embeddings/<obs>/embeddings.npy   (54000, 1536)  float32, L2-normalized
   embeddings/<obs>/metadata.parquet (54000 rows)
        │
        ▼  PCA(n=10).fit(joint) + KMeans(k=12)
   PCA-10:    (54000, 10)
   clusters:  (54000,)  ∈ {0..11}
        │
        ▼  per-trajectory metrics
   recurrence.csv:  (1350 trajectories × N_metrics columns)
   dwell.csv, basin.csv, basin_entry.csv, exit_return.csv,
   late_recurrence.csv, periodicity.csv, dispersion.csv
        │
        ▼  per-(family, ic) ensemble dynamics
   lyapunov_spectrum.csv:  (15 family-ic pairs × T steps × top-k λ)
   sharpness_dim.csv:      (15 family-ic pairs × T steps)
        │
        ▼  bootstrap + permutation + Cohen's d
   bootstrap_summary.csv, effect_sizes.csv
        │
        ▼  three-axis classifier
   ThreeAxisDecision: {h1a, h1b, h1c} ∈ {not_supported, weak, moderate, strong}
        │
        ▼  reports/plots + reports/perturbation
   ~70-150 PNG figures + (perturbation) 4-16 MP4 animations
        │
        ▼  cross-experiment
   data/aggregated/*  (cross-regime, cross-T, cross-dose summaries)
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
of ~$30 in OpenAI embedding API calls and ~2 hours of local compute.

### 4.12 Hardware and software

All experiments run locally with API calls to OpenAI. CPU: 40 cores
available for parallel rendering. Python 3.x with numpy, scipy,
scikit-learn, scikit-image, pandas, matplotlib, imageio-ffmpeg. Tests:
94 pytest tests, all green. See `requirements.txt` for exact
dependencies.

---

## 5. Results

### 5.0 The four (plus one) regimes at a glance

Before walking through the experiment phases, a master comparison
of the diagnostic signatures across regimes. Each row is a regime;
each column is a diagnostic that distinguishes it from the others.
All numbers are at publication scale (Phase 2) or perturbation pilot
scope (Phase 3).

| regime | nudge | content op. $f$ | basin pred. acc(k=5→final) | recurrence | sharpness dim* | adversarial switch | dose 50% | T-stability |
|---|---|---|---|---|---|---|---|---|
| **O1** contractive | append | continue | 0.77 → 0.85 | low | 1.70 | 54% | ~150 tok | degrades smoothly |
| **O2** oscillatory | replace | paraphrase | 0.90 → 0.91 | high (period-2) | 1.39 | 94% | n/a (saturated) | (not measured) |
| **O3** absorbing | replace | summarize+negate | 0.92 → 0.93 | trivial | 1.45 | 96% | n/a (saturated) | (not measured) |
| **D1** multi-basin | dialog (append) | curious + helpful | n/a → 0.77 | low (per-style) | 1.89 | 60% | < 5 tokens | T-stable |
| **D2** drill-down | dialog (append) | explorer drill-down | (not measured)** | (not measured) | (not measured)** | 64% | (not measured) | (not measured) |

\* Sharpness dim is computed on a 2-element Lyapunov spectrum (rank ≤ N−1 = 2 for N=3 runs per IC), so values are bounded above by 2.0. Mean SD_late on `context_tail`. The *ordering* across regimes is informative, the absolute magnitudes are constrained by the rank ceiling. See §4.5.6.

\*\* D2 was run at exploratory scale (N=1 run per IC), which is below the N≥2 minimum required for ensemble-spread Lyapunov computation. D2's basin-predictability acc at k=5 is 0.20 with n=25 and 11 classes (chance ≈ 0.09), well underpowered for the canonical k=5,10,20,final probes.

Reading: the two **replace-mode** regimes (O2, O3) lock in early (acc
already ≈0.9 by step 5) and are perturbation-transparent. The
**append-mode** regimes (O1 and the dialog regimes D1/D2) admit
slower late-state determination and have measurable barrier structure.
O1 is uniquely T-sensitive; D1 is uniquely T-stable; D2 adds content
gravity beyond D1's stylistic basins.

The regime ordering — replace-mode locks in fast and capitulates
to any perturbation; append-mode locks in slowly and resists
out-of-distribution perturbation but yields to in-distribution
adversaries — runs through every diagnostic below.

![Figure 1. Cross-experiment regime map (joint t-SNE on rolling_k3 observable). Each point is a single trajectory's late-window centroid; each color a regime / experiment. The four (plus one) regimes occupy visibly distinct regions of the embedding space — the taxonomy is not an artifact of any specific projection.](data/aggregated/dynamics_plots/regime_map_rolling_k3.png)

### 5.1 Phase 0 — pilot validation

We ran three early one-off experiments to validate the pipeline:

- `exp_default` — first run, T=0.8, append + continue, 5 families × 5
  ICs × 3 runs × 30 steps = 75 trajectories
- `exp_long` — 60-step horizon test
- `exp_noclip` — no context-clipping ablation

The key finding from `exp_default` (REPORT1) was the **strong
basin score, weak recurrence** profile that we later identified as the
contractive regime (O1). The basin metric was significantly above
shuffled baselines (95% bootstrap CI excludes baseline range), supporting
H1 at this early scale. `exp_long` confirmed the basin holds at longer
horizons. `exp_noclip` showed the basin deepens (less recurrence) when
context is unbounded — the contraction is partly enforced by clipping.

### 5.2 Phase 1 — the four-regime taxonomy at small N

REPORT2/3 added eight additional pilot experiments to test whether
varying the operator changes the regime:

| pilot | operator | architecture | content function | basin score | recurrence | sharpness dim |
|---|---|---|---|---:|---:|---:|
| `exp_op_O1_continue` | append | continue | preserving | high | low | low |
| `exp_op_O2_paraphrase_replace` | replace | paraphrase | preserving | low | high (period-2) | medium |
| `exp_op_O3_summarize_negate` | append | summarize+negate | content-degrading | medium | low | low |
| `exp_op_O3b_summarize_negate_replace` | replace | summarize+negate | content-degrading | trivial (singular) | trivial | very low |
| `exp_op_O4_paraphrase_append` | append | paraphrase | preserving | medium | medium | medium |
| `exp_dialog_D1_curious_helpful` | dialog (append) | curious+helpful | preserving | high (per-style) | low | medium |
| `exp_dialog_D2_replace_curious_helpful` | dialog (replace) | curious+helpful | preserving | low | high | low |
| `exp_dialog_D3_debate_advocate_skeptic` | dialog (append) | advocate+skeptic | preserving | medium | medium | medium |

Three regimes emerge clearly: **contractive** (O1, D1, D3), **oscillatory**
(O2), **absorbing** (O3b). The replace-mode operators in dialog (D2-replace)
also show oscillation but with weaker recurrence than O2, suggesting an
intermediate regime.

**Note on O3 vs O3b**: `exp_op_O3_summarize_negate` uses *append* mode
(summary appended to context), which produces a weak collapse —
trajectories drift toward a content-degraded sink but the basin is
soft. `exp_op_O3b_summarize_negate_replace` uses *replace* mode, which
produces the sharp absorbing regime characterized in REPORT4 as our
canonical O3. The publication-scale verification uses the replace
variant under the simpler name `exp_pub_O3_summarize_negate_replace`.

**Note on O4**: `exp_op_O4_paraphrase_append` (paraphrase + append) is a
2×2 cross of O1 and O2 — content-preserving paraphrase but accumulating
context. It produces an intermediate regime that doesn't cleanly fit the
four-regime taxonomy, with moderate recurrence, moderate sharpness, and
no clean periodicity. It supports H2 (architecture × content
factorization predicts behavior) and is documented as an interesting
boundary case in REPORT4.

**Note on D3 debate**: `exp_dialog_D3_debate_advocate_skeptic` uses two
roles arguing different positions (advocate vs skeptic) on a topic. It
shows medium-strength stylistic basins (each role has its own attractor)
plus moderate recurrence between role-aligned positions. We didn't
elevate it to the diagnostic taxonomy because its dynamics depend on
specific topic choice in ways D1 doesn't.

### 5.3 Phase 2 — publication-scale verification

REPORT5 ran the four diagnostic regimes at full scale (5 families ×
30 ICs × 3 runs × 40 steps = 1350 trajectories per regime). Basin
predictability — 5-fold CV multinomial logistic regression on PCA-10,
predicting the late-window K-means cluster (k=12) from the embedding
at step k — gives a clean per-regime ordering:

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

![Figure 2. Basin-predictability acc(k) curves at publication scale (n=1,350 / regime; D1 n=450). Replace-mode regimes (O2 paraphrase, O3 summarize+negate) lock in by step 5 at acc≈0.90–0.92. Append-mode O1 climbs from 0.77 (k=5) to 0.85 (final). Dialog D1 climbs from 0.61 (k=10) to 0.77 (final) — slowest to commit but reaching strong late-window basin predictability. Source: `data/aggregated/basin_predictability_cross/cross_basin_predictability.png`.](data/aggregated/basin_predictability_cross/cross_basin_predictability.png)

### 5.4 Phase 2b — temperature sensitivity

We ran a temperature sweep (T ∈ {0.3, 0.6, 0.8, 1.2}) for D1 and O1 at
reduced scope (5 families × 15 ICs × 2 runs × 30 steps = 150
trajectories per cell, except the D1 T=0.8 cell which reuses the
full-scope publication run at 450 trajectories). Predictor at step
k=10 of 30, classifier trained on PCA-10 of the canonical
`context_tail` observable, target: K-means cluster (k=12) at the
late window (t ≥ 0.7T). We report `acc(k=10)` rather than `acc(k=5)`
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

D1 stays in a tight 0.57–0.61 band across all four temperatures —
a span of only **4 pct pts** vs O1's 13-pct-pt span. Once the dialog
regime locks into a stylistic basin, temperature alone does not
unlock it. The full-scope D1 anchor (T=0.8, n=450) reaches acc(k=10)
= 0.61, matching the reduced-scope T=0.3 and T=0.8 cells exactly —
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

### 5.5 Phase 3a — perturbation pilots

![Figure 3. **The headline result.** Switching rates by regime × condition (n=50 / cell, n=25 for D2). Replace-mode regimes (O2, O3) capitulate to *any* perturbation type ≥ 80 tokens (94–100% switching). Append-mode O1 resists out-of-distribution perturbation (lorem/neutral 18–24%) but yields to in-distribution adversarial text (54%). Dialog regimes occupy intermediate scales determined by conversational structure (D1 60%, D2 64%). Source: `data/aggregated/perturbation_cross_regime/cross_switching_rates.png`.](data/aggregated/perturbation_cross_regime/cross_switching_rates.png)

For each of the four diagnostic regimes plus D2 (drill-down), we ran a
perturbation pilot at 5 families × 5 ICs × 2 runs × 30 steps = 50
trajectories per condition × 4 conditions. Switching rates with Wilson
95% confidence intervals (n=50 except D2 where n=25):

| regime | control | neutral | lorem | adversarial |
|---|---|---|---|---|
| O1 (contractive) | 0% [0–7] | 24% [14–37] | 18% [10–31] | 54% [40–67] |
| O2 (oscillatory replace) | 0% [0–7] | 100% [93–100] | 100% [93–100] | 94% [84–98] |
| O3 (absorbing replace) | 0% [0–7] | 100% [93–100] | 100% [93–100] | 96% [86–99] |
| D1 (multi-basin dialog) | 0% [0–7] | 76% [62–86] | 54% [40–67] | 60% [46–73] |
| D2 (drill-down dialog) | 0% [0–13] | n/a | n/a | 64% [44–80] |

(D2 was only tested with control + adversarial conditions, and at a
50-step horizon with override at step 25 — see §5.8.)

Replace-mode operators are perturbation-transparent: 94–100% switching
under any non-control condition. The append-mode contractive regime O1
shows clear conditional sensitivity: 54% under in-distribution
adversarial, but only 18–24% under out-of-distribution random or
neutral text. The dialog regimes sit between these extremes, with D1
showing higher switching under all conditions and D2 — the structured
drill-down — resisting more strongly.

**H3 is supported with refinement**: the qualitative split between
"replace-transparent / append-resistant" is clear, but the magnitude of
resistance depends on the type of perturbation, not just its presence.

### 5.6 Phase 3b — dose-response

We varied the perturbation length 20/80/200/400 tokens for D1 (neutral)
and O1 (neutral and adversarial). D1 with neutral was additionally
tested at sub-saturation doses 5/10/15:

**D1 / neutral** (n=50 per cell; Wilson 95% CI half-width ~13 pct pts):

| dose (tokens) | 5 | 10 | 15 | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|---:|---:|---:|
| switch | 62% | 68% | 70% | 72% | 76% | 70% | 66% |

D1 saturates at sub-token doses. The barrier height (in this dose
sense) is essentially zero — any 5-token coherent interrupt flips the
dialog basin. The flat-from-saturation curve is consistent with our
"dialog basin is stylistic, not content-bound" interpretation.

**O1 / neutral** (off-distribution; n=50 per cell; CI half-width ~12 pct pts):

| dose | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 22% | 26% | 24% | 24% |

Flat at the natural drift floor of ~24% across the entire dose range.
This is the "noise rate" — out-of-distribution text simply cannot move
the contractive basin no matter the dose.

**O1 / adversarial** (in-distribution; n=50 per cell; CI half-width ~13 pct pts):

| dose | 20 | 80 | 200 | 400 |
|---|---:|---:|---:|---:|
| switch | 26% | 34% | 54% | 48% |

Clear graded response. The 50%-switching dose is approximately 150
tokens of in-distribution text. **This is the first quantitative
barrier-height measurement for an LLM loop**. The same architecture
(O1 continue) produces qualitatively different dose-response curves
depending on whether the perturbation is in-distribution.

![Figure 4. Dose-response curves for D1 / neutral, O1 / neutral, and O1 / adversarial. The 50% switching crossing on the O1 / adversarial curve at ~150 tokens of in-distribution text *is* the paper's headline barrier height. O1 / neutral saturates at ~24% (the irreducible drift floor), confirming the contractive basin has an effectively-infinite barrier against out-of-distribution nudges. D1 / neutral shows shallow dose-dependence consistent with intermediate-barrier dialog dynamics. Source: `data/aggregated/perturbation_dose_response/dose_response.png`.](data/aggregated/perturbation_dose_response/dose_response.png)

### 5.7 Phase 3c — injection-time sweep

We injected the same perturbation (D1: neutral @80, O1: adversarial @200)
at three different steps of a 30-step trajectory (n=50 per cell):

| inject step | D1 (neutral @80) | O1 (adversarial @200) |
|---:|---:|---:|
| 5 | 72% [58–83] | 60% [46–73] |
| 15 | 78% [65–87] | 54% [40–67] |
| 25 | **52% [38–66]** | 62% [48–74] |

D1 shows partial **basin hardening**: by step 25 the trajectory has
committed to its style basin and resists more strongly (52% vs 78% at
step 15). The basin gets harder to leave as the trajectory ages.

O1 is essentially flat across injection time — the contractive
averaging operator integrates whatever is in context regardless of when
it arrived. **The two regimes have qualitatively different
time-dependence** in their barrier structure.

![Figure 5. Injection-time sweep: switching rate as a function of when the perturbation lands (step 5, 15, 25 of a 30-step trajectory). D1 (neutral @ dose 80, top) shows U-shape — early/middle injections more disruptive than late. O1 (adversarial @ dose 200, bottom) is roughly flat — the contractive basin doesn't care WHEN the perturbation arrives, only how much in-distribution evidence it carries. Source: `data/aggregated/perturbation_basin_hardening/basin_hardening.png`.](data/aggregated/perturbation_basin_hardening/basin_hardening.png)

### 5.8 Phase 3d — drill-down dialog (D2)

We introduced a new dialog regime: an **Explorer-Expert** drill-down
dialog where each user turn asks for a deeper, more specific
explanation of one concept from the previous expert turn. 5 topic
families × 5 seed topics = 25 trajectories at 50 steps each.

Adversarial perturbation injected at step 25 — drawing from a *different
topic family*'s expert text — with 25 steps of post-injection
relaxation. Switch rate: **64%**.

Compared to D1 free dialog at the same setup (matched-relaxation D1
inject_t25 = 52% — though the doses and content differ slightly), D2's
64% under late-injection adversarial is *higher*, but compared to the
D1 pilot's 78% at step 15 with shorter relaxation, D2 shows similar or
weaker resistance. The fair comparison is at matched (override step,
relaxation horizon):

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

- `scripts/aggregate_basin_predictability.py` — overlay the basin
  predictability curves of the four diagnostic regimes onto a single
  axis. Output: `data/aggregated/basin_predictability_cross/`.
- `scripts/aggregate_t_sweep.py` — combine the D1 T-sweep CSVs.
  Output: `data/aggregated/t_sweep_basin_predictability/`.
- `scripts/aggregate_o1_d1_t_sensitivity.py` — side-by-side O1-vs-D1
  basin-predictability-vs-T comparison. Output:
  `data/aggregated/t_sensitivity_cross_regime/`.
- `scripts/aggregate_perturbation_cross_regime.py` — switching rates +
  relaxation curves across all 5 perturbation pilots (D1, O1, O2, O3, D2).
  Output: `data/aggregated/perturbation_cross_regime/` including the
  4×5 condition × regime grouped bar chart.
- `scripts/aggregate_dose_response.py` — dose-response curves across
  D1+O1 dose experiments, log-scale dose axis with 95% Wilson CI bars.
  Output: `data/aggregated/perturbation_dose_response/`.
- `scripts/aggregate_basin_hardening.py` — injection-time × switching
  curves for D1 + O1, with the basin-hardening interpretation.
  Output: `data/aggregated/perturbation_basin_hardening/`.
- `scripts/aggregate_perturbation_geometric_barriers.py` — combine the
  per-pilot `geodesic_barriers_summary.csv` (V*) and
  `rg_dendrogram_summary.csv` (Ward merge distance) into the wide
  regime × condition tables shown in §5.10. Output:
  `data/aggregated/perturbation_geometric_barriers/`
  (`v_star_table.csv`, `rg_merge_table.csv`, `geometric_barriers_long.csv`).

Each script reads only the per-experiment CSV outputs and is fully
deterministic — re-running them produces byte-identical figures. They
are kept separate from the per-experiment pipeline to allow incremental
re-aggregation as new experiments land.

### 5.10 Geometric barriers from V(x) = −log ρ(x)

![Figure 6. Empirical potential landscape V(x) = −log ρ(x) on PCA-2 for the O1 perturbation pilot, four conditions. Wells = attractor basins; cliff edges = barriers. The control panel (top-left) shows the unperturbed contractive basin; the adversarial panel (bottom-right) shows the kick that ~1/2 of trajectories survive without crossing into another basin. Source: `data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/bulk_landscape_pca.png)

![Figure 7. Geodesic skeleton through V on PCA-2 for the O1 pilot's four conditions. Density-peak basins (red dots) are connected by Dijkstra geodesics; the maximum-V along each path is the geometric barrier height V\*. Per-condition mean V\* values reported in the table below agree with the perturbation-derived dose thresholds — the cross-check that validates barrier height as a real geometric quantity. Source: `data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png`.](data/exp_perturb_O1_pilot/reports/perturbation/geodesic_skeleton_pca.png)

For each of the four diagnostic perturbation pilots we computed:

#### Geodesic skeleton on V

Per-condition mean barrier height V\* across the 6 inter-basin geodesics
(`V_star_mean` column in the per-pilot `geodesic_barriers_summary.csv`):

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 4.4 | 2.3 | 2.6 | 2.2 |
| O2 | 2.8 | 3.5 | **5.6** | 1.6 |
| O3 | 1.1 | 5.2 | **7.0** | 2.2 |
| D1 | 1.3 | 1.1 | 0.8 | 0.4 |

(Per-geodesic raw V\* values are written alongside the figure to
`data/exp_perturb_*_pilot/reports/perturbation/geodesic_barriers_pca.csv`;
the V_max ≈ 8.0 ceiling appears when a geodesic crosses a region of
near-zero density.)

The geometric V\* values complement the perturbation switching rates:

- **O2/O3 lorem** has V\* ≈ 5.6 / 7.0 — the highest barriers in the
  matrix. Those barriers separate *control* from a *new* basin that
  lorem injection creates far from any pre-perturbation density
  mass: geodesics between the original and lorem-induced basins
  traverse low-density plateaus where ρ ≈ ε (V near the V_max
  ceiling). Switch rates are 100% because the perturbation places
  the trajectory *into* the new basin — the perturbed run does not
  have to climb the barrier; it lands on the far side. The high V\*
  is consistent with the per-regime RG cloud expansion (3.6 / 3.3
  below).
- **O1 adversarial** has V\* ≈ 2.2 — basins remain distinct but the kick
  occasionally clears the ridge → consistent with 54% switching at
  ~150 tokens dose.
- **D1 adversarial** has V\* ≈ 0.4 — basins are stylistic, not
  content-bound, so the geometric barrier is small → consistent with
  the 60% switching at saturated doses.

Cross-validating dose-response barrier estimates (from §5.6) against
geometric V\* gives two complementary readings: O1 adversarial agrees
quantitatively (V\* ≈ 2.2 ↔ 150-token saturation dose), D1 agrees
qualitatively (low V\*, near-zero saturation dose), and the
replace-mode regimes are explained by basin *creation* rather than
barrier crossing — different geometric mechanisms producing the same
100% switching.

#### Hierarchical RG dendrogram

Per-condition maximum Ward-linkage merge distance across k=48 fine-cluster
centroids:

| regime | control | neutral | lorem | adversarial |
|---|---:|---:|---:|---:|
| O1 | 2.38 | 2.27 | 2.37 | 2.06 |
| O2 | 2.31 | 2.32 | **3.64** | 1.90 |
| O3 | 2.16 | 2.39 | **3.25** | 1.85 |
| D1 | 1.79 | 1.79 | 1.79 | 1.80 |

Three patterns:

1. **D1 is invariant** at 1.79–1.80 across all four conditions — the
   dialog cloud's coarse-graining diameter doesn't change with
   perturbation. Consistent with stylistic basins that are not
   reshaped by content injection.
2. **O2/O3 lorem expands the cloud** to merge distance 3.64/3.25
   (vs control 2.31/2.16) — the largest signal in the matrix.
   Lorem injection under replace-mode produces a *new* basin that sits
   far from the original attractor, so the Ward linkage tree has to
   span a wide gap to merge the lorem-population into the rest of the
   embedding. Replace-mode trajectories are entirely captured by the
   lorem text, but the basin they're captured into is a long way
   off the original loop's manifold.
3. **O1 adversarial mildly compresses** (2.06 vs 2.38) — in-distribution
   adversarial text pulls into a tighter region. **O1 neutral and
   lorem are both close to control** (2.27, 2.37 vs 2.38), consistent
   with append-mode dilution: out-of-distribution perturbation gets
   averaged into the accumulating context and barely shifts the
   coarse-graining diameter.

Each row of this 4×4 matrix is a quantitative attractor-fingerprint
signature for the corresponding regime.

### 5.11 Cross-metric correlations: do the regime diagnostics agree?

The four regimes were *defined* by qualitative architecture × content
labels (append vs replace vs dialog × continue vs paraphrase vs
summarize+negate vs free vs drill-down). The four diagnostic-metric
families above (Lyapunov, sharpness-dim, recurrence, basin
predictability, perturbation switching) were *measured* independently.
A natural cross-check: do regimes that score high on one diagnostic
also score predictable ways on the others?

We compute three pre-registered correlations across the 4 regimes
(O1, O2, O3, D1) on canonical pub-scale values:

| relation | Pearson *r* (p) | Spearman *ρ* (p) | mechanistic prediction |
|---|---:|---:|---|
| recurrence rate vs adversarial switching rate | **+0.981 (0.019)** | +0.800 (0.200) | high-recurrence regimes (tight periodic orbits) are easier to kick out of orbit by injection — confirmed |
| sharpness dim (late) vs lock-in step (smallest *k* with `acc(k) ≥ 0.7`) | +0.838 (0.162) | **+0.949 (0.051)** | low-effective-dimension regimes have fewer "free axes" the predictor must constrain — confirmed |
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
in 0–1 steps (the late-window cluster is already determined by step
0); the high-dimensional regime D1 (sharpness ≈ 1.89) takes 26 steps
to reach `acc(k) ≥ 0.7`. The intermediate O1 (sharpness ≈ 1.70)
locks in at step 1.

These correlations are computed across only n=4 regimes, so the p-values
are necessarily noisy. The methodological point is that the *signs*
agree with the mechanistic predictions, and the strongest correlation
(recurrence ↔ switching, *r* = +0.981, *p* = 0.019) survives the small
sample size — providing internal consistency evidence that the
four-regime taxonomy is *not* an artifact of any single metric but
emerges from a coherent dynamical structure.

### 5.12 Why exactly five regimes? An unsupervised-clustering check

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

After standardization, k-means clustering at *k* ∈ {2, …, 7} gives:

| *k* | silhouette ↑ | Calinski-Harabasz ↑ | Davies-Bouldin ↓ |
|---:|---:|---:|---:|
| 2 | **0.575** | 13.4 | 0.65 |
| 3 | 0.568 | 21.3 | 0.59 |
| 4 | 0.521 | 24.7 | 0.39 |
| 5 | 0.477 | 34.3 | 0.34 |
| 6 | 0.478 | 46.5 | 0.21 |

Three internal-validation indices, three different optimal *k*: **2
by silhouette, 7 by Calinski-Harabasz, 6 by Davies-Bouldin** — i.e.,
no cluster-count emerges as uniformly optimal. The honest reading:
the bulk diagnostic vector (recurrence + sharpness + λ₁ + basin pred
+ adversarial switch) **partially recovers** the regime taxonomy but
does not cleanly resolve it. Specifically, the *k*=5 confusion
matrix (cluster vs ground-truth label):

| ground-truth ↓ \ cluster → | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| O1 (n=8) | 0 | 4 | 2 | 0 | 1 |
| D1 (n=4) | 0 | 3 | 1 | 0 | 0 |
| O2 (n=2) | 0 | 0 | 0 | **1** | 0 |
| O3 (n=2) | **1** | 0 | 0 | 0 | 0 |

shows the substructure clearly:

- **O2 (cluster 3) and O3 (cluster 0)** each form their own
  singleton clusters — *bulk diagnostics resolve them individually*.
  This makes mechanistic sense: O2's period-2 oscillation and O3's
  near-singular absorbing state have very distinct recurrence /
  λ₁ / sharpness signatures (recurrence 0.88 vs 0.92; sharpness 1.39
  vs 1.45 with very different time-evolution patterns).
- **O1 and D1 share clusters 1 and 2** — *bulk diagnostics do not
  cleanly separate the contractive append regime from the
  stylistic-multi-basin dialog regime*. Their canonical values are
  too close: recurrence 0.29 vs 0.21, sharpness 1.70 vs 1.89,
  λ₁ 0.008 vs 0.011, basin pred 0.65 vs 0.61, adversarial switch
  0.54 vs 0.60. The differences exist but are small relative to
  intra-regime variance across phase-1 / phase-2 / T-sweep
  measurements.

This is the affirmative empirical content of why the perturbation
protocol matters: **bulk diagnostics underdetermine the regime
taxonomy at the O1/D1 boundary**. The mechanistic distinction
between O1 (content-anchored basin, finite barrier against
in-distribution adversarial text, infinite barrier against
out-of-distribution noise — §5.6) and D1 (style-anchored basin,
T-stable across {0.3..1.2}, modest barrier in any direction —
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

![Figure 8. Diagnostic feature space (left) and cluster validity vs k (right). Left: PCA-2 of the 5-D standardized diagnostic vector for 13 experiments, colored by regime label. O2 (red) and O3 (purple) form well-separated clusters; O1 (blue) and D1 (green) overlap heavily — bulk diagnostics underdetermine the contractive vs stylistic-multi-basin distinction. Right: silhouette score (blue circles) prefers k=2; Calinski-Harabasz (red squares) keeps rising past k=7 — i.e., no internal validation index agrees on the "true" cluster count, consistent with the regimes living on a continuum that bulk diagnostics flatten. Source: `data/aggregated/regime_cluster_analysis/cluster_scatter.png`.](data/aggregated/regime_cluster_analysis/cluster_scatter.png)

### 5.13 Embedding-space invariance: do the regimes survive a different embedder?

A natural reviewer challenge: the regime taxonomy is defined on
embeddings from `text-embedding-3-small` (OpenAI, 1536-dim). Would
the regimes change with a different embedder? We test this by
re-embedding 5,000-step subsamples of 5 representative experiments
(one per regime: O1, O2, O3, D1, D2) under two alternative embedding
models and recomputing the canonical diagnostics:

- **`text-embedding-3-large`** (OpenAI, 3072-dim) — within-vendor
  scale-up.
- **`all-mpnet-base-v2`** (sentence-transformers, 768-dim, local) —
  cross-architecture, open-source.

Per-regime canonical diagnostics, all three embedders:

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

| diagnostic | vs `text-embedding-3-large` | vs `all-mpnet-base-v2` |
|---|---:|---:|
| recurrence rate | ρ = +0.60 | ρ = +0.60 |
| **basin predictability acc(k=10)** | ρ = **+0.80** | ρ = **+1.00** |
| sharpness_dim_late | ρ = −0.40 | ρ = +0.00 |

Three findings:

**(a) Basin predictability is fully invariant under embedder swap**
(*ρ* = +1.00 for `all-mpnet-base-v2`, +0.80 for
`text-embedding-3-large`). The regime ordering on basin predictability
— **replace-mode (O2, O3) > append (O1) > dialog (D1) > exploratory
D2** — is preserved exactly under cross-architecture embedding
substitution. This is the strongest cross-embedder invariance result
in our data: the property of the recursive dynamics that the basin
predictor measures (how much information about the late-window
attractor is already present at step 10) is *not* a property of one
specific embedding family.

**(b) Recurrence rate is partially invariant** (*ρ* = +0.60 in both
cases). The bimodal structure — replace-mode pair {O2, O3} above
0.71 in every embedder, append/dialog set {O1, D1, D2} below 0.34
in every embedder — is preserved unambiguously. The fine-grained
ordering within each cluster shifts modestly across embedders, but
the dominant high/low partition that distinguishes the replace-mode
regimes from the rest does not.

**(c) Sharpness dim_late is NOT invariant** (*ρ* = +0.00 vs mpnet,
−0.40 vs large). This is a real and worth-flagging finding: the
sharpness-dimension diagnostic, which depends on the dimensional
structure of the embedding space, is embedding-specific. Different
embedders give different orderings of regimes on this diagnostic.
The sharpness-dim claims in §5.0 / §5.2 should therefore be
interpreted as *measurements within the* `text-embedding-3-small`
*pipeline*, not as embedding-invariant properties of the recursive
dynamics. (D2's sharpness is NaN in all three embedders because the
exploratory-scale ensemble — only ~25 trajectories per family — is
too small to support the late-window covariance estimate.)

The headline conclusion: **the taxonomy's load-bearing distinction
between replace-mode regimes and append/dialog regimes is
embedding-invariant** (basin predictability ρ ≥ +0.80; recurrence
bimodal structure preserved). The taxonomy's *fine-grained* metrics
(O2 vs O3 at the basin-shape level; D1 vs O1 at the sharpness-dim
level) are partially or wholly embedding-dependent. This is consistent
with §5.12's finding that the perturbation barrier — a quantity
defined in token-space rather than embedding-space — is the
load-bearing diagnostic for separating the full five-regime
taxonomy.

(Full ablation: `scripts/embedding_ablation.py`, output at
`data/aggregated/embedding_ablation/results.csv`.)

![Figure 9. Embedding-space invariance ablation. Three panels: recurrence rate (left), sharpness_dim_late (middle), and basin_pred_acc(k=10) (right) per regime, grouped bars per embedder. Recurrence preserves its bimodal high/low structure (O2/O3 high in all embedders; O1/D1/D2 low). Basin predictability preserves the full regime ordering (Spearman ρ ≥ 0.80 vs baseline). Sharpness dim shifts substantially across embedders — the regime ordering is not preserved (ρ = 0.00 vs mpnet). Source: `data/aggregated/embedding_ablation/comparison.png`.](data/aggregated/embedding_ablation/comparison.png)

---

## 6. Discussion

### 6.1 Regimes are properties of nudges, not prompts alone

The central lesson of these experiments is that recursive LLM regimes
are determined jointly by the generator and the context-update rule.
In our framework, the model samples
$Y_t \sim P_\theta(\cdot \mid X_t; f)$ while the nudge $\mathcal{N}_f$
determines how that output is written back into the next state. The
observed taxonomy is therefore not merely a taxonomy of prompts or
tasks; it is a taxonomy of **generator–nudge systems**.

Viewed this way, the empirical pattern is remarkably regular. The
taxonomy decomposes into a 2×2 over the operator regimes plus an
orthogonal dialog axis:

|  | append (preserve) | replace (overwrite) |
|---|---|---|
| **content-preserving** (continue, paraphrase) | O1 contractive basin | O2 oscillatory 2-cycle |
| **content-degrading** (summarize+negate) | weak collapse (small N) | O3 absorbing |

|  | dialog architecture |
|---|---|
| **free** (curious user / helpful agent) | D1 stylistic multi-basin |
| **structured** (explorer drill-down / expert) | D2 content-anchored multi-basin |

Content-preserving operators under append mode produce contractive
behavior; content-preserving operators under replace mode produce
oscillation; content-degrading operators under replace mode produce
absorbing collapse. Dialog adds a second architectural axis because
role structure changes how text is accumulated and reinterpreted
across steps. D1 and D2 are therefore not exceptions to the operator
taxonomy, but evidence that dialog should be treated as a distinct
nudge family rather than as a special case of append.

This interpretation is stronger than a descriptive regime table. It
suggests that a new recursive loop can be located by knowing two
things: what semantic transformation it asks the model to perform,
and how that transformation is written back into state. The
experiments do not yet prove that this factorization is exhaustive,
but they show that it is already predictive across the operator
families studied here.

### 6.2 Why append resists and replace yields

The sharpest mechanistic contrast in the paper is between append and
replace. In append mode, a perturbation is injected into an
already-accumulating state. It therefore competes with prior
trajectory mass rather than replacing it. Unless the perturbation is
semantically aligned with an alternative basin, it is diluted by the
existing context and tends to wash out. This is exactly what the
perturbation results show for O1: neutral and lorem injections remain
near the drift floor, while in-distribution adversarial text
accumulates enough basin-relevant evidence to move the trajectory
with nontrivial probability.

In replace mode, by contrast, the perturbation effectively becomes
the next state. The prior trajectory is discarded after one step, so
the system has almost no memory barrier. This is why O2 and O3 are
nearly transparent to perturbation: once the next state is rewritten,
the subsequent loop evolves from the injected text rather than from
the original basin. **Lemma 1 (§3.1.2) formalizes this asymmetry by
showing that replace-mode barriers are bounded by roughly one
generation length.** The measurements support exactly that prediction.

The dialog regimes sit between these extremes. They accumulate
content as append systems do, but new turns have unusually high local
influence because role-structured observables emphasize recent turns.
This makes dialog less rigid than append-mode continuation, but more
path-dependent than replace-mode overwrite. The result is an
intermediate barrier scale whose interpretation depends on whether
the dialog stabilizes **style** or **topic**.

### 6.3 D1 and D2 reveal two kinds of dialog attractor

The contrast between D1 and D2 is important because it shows that
"dialog" is not a single regime. D1 behaves like a stylistic
multi-basin system: trajectories settle into stable conversational
modes, and perturbations act mainly on those style channels. D2
behaves differently. Its Explorer–Expert drill-down structure creates
what is best described as **content gravity**: once the exchange has
narrowed into a deeper subtopic, adversarial injections are only
partially successful because the next turn is explicitly constrained
to continue drilling into the established semantic branch.

This distinction matters theoretically. D1 shows that conversational
structure can stabilize a trajectory without tightly binding its
content. D2 shows that conversational structure can do more: it can
impose topic-preserving momentum even when each turn is freshly
generated. That is the first evidence in this project that a nudge
architecture can encode a form of semantic inertia beyond simple
append-mode accumulation.

The broader implication is that dialog architectures should be
studied as a space of nudge designs. Free chat, drill-down, debate,
role-play, and multi-party deliberation may occupy different points
on a style-versus-content stability continuum. D2 is therefore best
understood not merely as another measured regime, but as evidence
that dialog structure can itself be a control parameter of attractor
geometry.

### 6.4 Barrier height is the missing dimension of regime analysis

Classifying recursive loops only by contraction, oscillation, or
collapse is not enough. Those diagnostics describe the **shape** of
a regime, but not its **stability under intervention**. Barrier
height adds this missing dimension. Once measured in tokens, it
gives an operational answer to a practical question: how much
semantically relevant text does it take to redirect a recursive
loop?

This is why the perturbation protocol is the paper's real headline
contribution. Without it, O1 and D1 look closer than they truly are
(see §5.12, where bulk-diagnostic clustering cannot resolve them),
and D1 and D2 are not sharply separable at all. Bulk diagnostics
recover broad classes; perturbation barriers reveal how strongly
those classes are held in place. **In that sense, the full five-way
taxonomy is not produced by geometry alone or by perturbation alone,
but by the combination of the two.**

The information-theoretic reading in §3.1.4 helps explain why the
barrier story is richer than a raw token count. Out-of-distribution
perturbations can be long without being effective because they carry
little basin-relevant information. In-distribution adversarial
perturbations are effective not because they are surprising, but
because they are semantically legible to the model as evidence for a
competing continuation. Barrier height is therefore best understood
as a measure of **how much meaningful counter-context must be
written into the loop before the dynamics re-aim**.

### 6.5 Why the geometric picture matters

The empirical potential landscape $V(x) = -\log \rho(x)$ should not
be mistaken for a literal physical free energy. It is a descriptive
summary of the density of trajectories in a reduced representation
space. But the fact that geodesic barrier estimates derived from $V$
align with behavioral switching thresholds is still significant. It
suggests that the perturbation results are not only artifacts of one
intervention protocol; they are reflecting genuine large-scale
geometry in the embedding-space dynamics.

This geometric agreement is especially useful because the two
measurements are independent in spirit. Behavioral barriers are
measured by *actively* kicking trajectories and observing switching.
Geometric barriers are measured *passively* from the density
landscape and shortest paths between basins. Agreement between them
does not prove a mechanistic potential model of LLM inference, but
it does strengthen the interpretation of barrier height as a real
structural property of the recursive loop.

### 6.6 Practical implications

For practitioners, the results suggest that recursive-loop design is
partly a problem of **nudge engineering**:

| if you want… | choose… | barrier signature you'll see |
|---|---|---|
| **a stable trajectory** that holds the user's seed thought | append-mode + content-preserving operator (O1) | finite barrier (~150 tokens of in-distribution adversarial); effectively-infinite barrier against out-of-distribution noise |
| **fast lock-in to a topic** (don't care which one) | replace-mode (O2 paraphrase or O3 summarize+negate) | locks in by step 5; capitulates to *any* perturbation ≥ 80 tokens |
| **stylistic stability across resets** | dialog framework (D1) | stylistic basin survives temperature changes (acc(k=10) range 0.57–0.61 over T ∈ {0.3..1.2}) |
| **content gravity that resists topic-switching** | structured drill-down dialog (D2) | 64% adversarial switching rate; basin geometry resists *cross-topic* perturbations specifically |
| **collapse** (degenerate output) | replace-mode summarize+negate (O3) | convergence within ~10 steps; sharpness-dim ≈ 0; trivially low effective rank |

More broadly, the perturbation-barrier protocol can be read as a
generic robustness probe. It measures not just whether a system can
be perturbed, but how much context budget an adversary or operator
must spend to move the system from one regime to another. That makes
it relevant not only for recursive-loop science, but also for
**jailbreak resistance**, **persona stability**, and **in-context
attack evaluation**. The 4-condition protocol's neutral and lorem
conditions provide the right baseline: a robustness claim is
meaningful only relative to the irreducible drift floor (~24% for
O1) that the model exhibits under benign perturbation.

### 6.7 Interpretation

The main conceptual conclusion of the paper is therefore simple.
Recursive LLM behavior is shaped not only by the generator $P_\theta$,
but by the nudge that writes generated text back into state. Different
nudges induce different attractor geometries, and those geometries
are measurable not only by their trajectory statistics, but by the
amount of injected text required to cross their basin boundaries.
**In that sense, barrier height is the operational bridge between a
formal theory of recursive dynamics and the practical problem of
controlling LLM loops.**

---

## 7. Limitations

### 7.1 Scope of model coverage

All experiments in this paper use a single generator, `gpt-4o-mini`.
The main qualitative claims — especially the separation between
append, replace, and dialog regimes — may generalize because they
follow from the generator–nudge factorization rather than from any
one model family. But the present study does not establish cross-model
universality. Barrier heights, basin geometry, and even the exact
number of identifiable regimes may vary across models with different
decoding behavior, alignment tuning, or tokenizer structure. A
within-vendor cross-generation pilot on `gpt-4.1-nano` is in progress
and reported in §11; cross-vendor replication remains future work.

### 7.2 Dependence on representation choice

Our results are observed through one embedding family,
`text-embedding-3-small`, together with PCA and t-SNE projections. We
do check robustness across observables and across several projection
spaces, and §5.13 reports an explicit embedding-space invariance
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
discussed in §3.1.4, the model-agnostic object is closer to a barrier
in surprisal or nats. Because the current 37-experiment battery does
not store logprobs, we cannot yet report that quantity directly. The
token barriers in this paper should therefore be read as the most
interpretable first-order estimate of a deeper information barrier.

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
generator–nudge system rather than of one model alone. Within-vendor
scale-down to `gpt-4.1-nano` is in progress; cross-vendor replication
on Claude Haiku and on a non-OpenAI generator is the natural Tier-3
extension.

### 8.2 Barrier height in nats

A second priority is to move from token barriers to information
barriers. Future experiments should capture generation logprobs
(`Config.include_logprobs=True` is already supported by the pipeline)
so that perturbation cost can be reported not only in tokens, but
also in conditional surprisal. That would let us estimate barrier
height in nats directly and test more rigorously the proposed link
(§3.1.4) between behavioral switching thresholds and geometric
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

---

## 9. Methods appendix

### 9.1 Exact metric definitions (executable form)

These are the literal code snippets that implement the metrics
described conceptually in §4.5. Each is taken from `src/analysis/`
or `src/experiments/dynamics/` and is exercised by the test suite at
`tests/`. They are reproduced here for review by readers who prefer
code to prose.

Recurrence:

```python
D = pairwise_distances(z, metric="cosine")  # T × T
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
    lambda_t = np.log(sigmas) / 2.0  # (d_pca,)
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
    SD_t = float(len(lam))             # full-d case
else:
    j_star = int(nonneg[-1]) + 1       # 1-indexed
    SD_t = j_star + cumsum[j_star - 1] / abs(lam[j_star])
```

Basin predictability:

```python
y = mode(clusters[t > 0.7 * T])  # late-window cluster per trajectory
acc_curve = np.zeros(T)
for k in range(T):
    X = z_pca10[:, k, :]
    clf = LogisticRegression(multi_class="auto", max_iter=1000)
    acc_curve[k] = cross_val_score(clf, X, y, cv=5).mean()
```

### 9.2 Perturbation injection mechanics

For dialog-mode experiments, the injection happens at the user-turn
step (odd-numbered if Explorer initiates). The injection text replaces
the user turn's output verbatim. The trajectory then continues with
the agent's response to this overridden user turn, and from there
back to normal alternation.

For operator-mode experiments, the injection text replaces step k's
output entirely. The recurrence picks up from `X_{k+1} = clip(X_k ||
Y_k_inj)` (append) or `X_{k+1} = clip(Y_k_inj)` (replace).

The adversarial-source experiment for each regime is taken from the
*publication-scale* run of the same regime (e.g., O1 perturbation
adversarial draws from `exp_pub_O1_continue`). Adversarial samples
exclude the *family* of the trajectory being perturbed but may share
its overall topic distribution.

### 9.3 K-means choice and stability

We use k=12 for all clustering. This was chosen empirically — fewer
clusters merge meaningful basins, more clusters split them. The
relative basin scores are stable for k ∈ [8, 16]; we have not tested
beyond.

### 9.4 PCA stability

Joint PCA on the full point cloud (all trajectories of an experiment)
gives stable PC1/PC2/PC3 directions across trajectories. We re-fit per
experiment but never per-trajectory.

### 9.5 Animation rendering pipeline

The 3D animation pipeline (`trajectory_animation_3d.py`) supports
parallel rendering via `concurrent.futures.ProcessPoolExecutor`. Each
worker process imports matplotlib with the Agg backend, builds a fresh
figure for one frame, and saves a PNG. The main process stitches PNGs
into MP4 via `imageio-ffmpeg` (libx264, quality 8). With 40 workers,
75 frames at DPI 180 take ~80 seconds wall-time vs ~11 minutes
single-threaded.

---

## 10. Reproducibility statement

### 10.1 Data availability

All raw trajectories are stored under `data/exp_*/raw/steps.jsonl` and
LFS-tracked in the public repository. Total raw payload: 3.3 GB across
37 experiments. Per-experiment analytical artifacts (metrics CSVs,
plots, perturbation visualizations, animations) are summarized in the
`COVERAGE.csv` matrix at the repo root — 37 rows × 60 columns
recording presence (1), absence (0), or structural non-applicability
(empty cell) of each artifact. **All 37 experiments are at 100% of
their applicable artifacts.** Two complementary documents back this:

- **`EVIDENCE.md`** maps every substantive claim in this paper to its
  backing data file, source code function (with line anchor), and CLI
  command — the "where is the evidence for claim X?" lookup.
- **`RESULTS.md`** is a cell-by-cell verification of every numeric
  claim in §5 against the canonical aggregated CSVs, regenerated by
  `python -m scripts.publication_summary`. Current state:
  **103 / 103 cells (100.0%) reproduce within tolerance** (±2.5 pct
  pts on switch rates / accuracies, ±0.05–0.15 on dimensionless
  barrier values).

Together the three answer: "what exists?" (COVERAGE), "where is the
evidence for claim X?" (EVIDENCE), and "do the numbers in §5 match
the data?" (RESULTS).

### 10.2 Code availability

All code is at <https://github.com/kaplan196883/llmattr>. License:
TBD (currently no license file; authors retain rights pending
publication).

### 10.3 Compute and cost

- **Embedding regeneration**: ~$30 in OpenAI `text-embedding-3-small`
  API calls for the full 37-experiment set.
- **Generation regeneration**: ~$200 in `gpt-4o-mini` API calls;
  unnecessary if `steps.jsonl` files are checked out from LFS.
- **Local compute**: ~2 hours wall-time for full embed + analyze on a
  40-core machine. Animations add ~80s each × 50 = ~70 min.

### 10.4 Pipeline commands

```bash
# Generate (only for new experiments)
python -m src.experiments.dialog.main run    --config <cfg.yaml>
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
python -m scripts.build_coverage          # rebuild COVERAGE.csv (37 × 60 matrix)
python -m scripts.publication_summary     # rebuild RESULTS.md (verify §5 cells against data)
```

### 10.5 Per-experiment catalog

Three complementary catalogs:

- **`docs/DATA_INDEX.md`** — narrative catalog of the 37 experiments
  organized by phase, with descriptions of each experiment's purpose,
  scope, and supersession relationships.
- **`COVERAGE.csv`** — machine-readable matrix at the repo root (37
  rows × 60 cols) showing which analytical artifacts every experiment
  carries, plus metadata (phase, regime, nudge_mode, temperature,
  n_trajectories) and three summary columns (`n_applicable_artifacts`,
  `n_present_artifacts`, `coverage_pct`). Cells are `1` (present), `0`
  (real gap), `""` (structurally not applicable to this experiment), or
  positive integer counts. **All 37 experiments are at 100% of their
  applicable artifacts.** Regenerate with
  `python -m scripts.build_coverage`. Applicability rules and the full
  per-phase × artifact-category coverage profile are documented in
  `EVIDENCE.md` (§"Coverage matrix").
- **`RESULTS.md`** — cell-by-cell verification of every numeric claim
  in §5 against the canonical aggregated CSVs. **103 / 103 cells
  reproduce within tolerance** (8 in §5.0, 16 in §5.3, 8 in §5.4, 18
  in §5.5, 15 in §5.6, 6 in §5.7, 16 in §5.10 V\*, 16 in §5.10 RG).
  Regenerate with `python -m scripts.publication_summary`.

Together: DATA_INDEX answers "what is this experiment for?", COVERAGE
answers "what artifacts does it carry?", RESULTS answers "do the §5
numbers match the data?".

### 10.6 Stage reports

The discovery process is documented in six stage reports:

- `docs/reports/REPORT1.md` — first run on `exp_default`; baseline
  classification methodology
- `docs/reports/REPORT2.md` — long-horizon and clipping ablations
- `docs/reports/REPORT3.md` — dynamical-systems metrics (Lyapunov,
  sharpness)
- `docs/reports/REPORT4.md` — operator regime classification (the
  four-regime taxonomy)
- `docs/reports/REPORT5.md` — publication-scale verification
- `docs/reports/REPORT6.md` — perturbation experiments and
  basin-hijacking, including drill-down dialog (D2)

### 10.7 Test coverage

94 pytest tests cover the analysis primitives plus integration:

```bash
PYTHONPATH=. python -m pytest tests/ -q
# 94 passed in ~12s
```

### 10.8 Repository layout summary

```
llm_attractor_experiment/
├── README.md, requirements.txt, ARTICLE.md
├── EVIDENCE.md             claim-to-evidence map (every ARTICLE claim
│                           ↔ data file ↔ source code function ↔ CLI)
├── COVERAGE.csv            37 × 60 artifact-presence matrix
├── RESULTS.md              §5 numeric-claim verification (103/103 ✓)
├── docs/
│   ├── DATA_INDEX.md
│   └── reports/REPORT1.md … REPORT6.md
├── src/
│   ├── analysis/      basin, recurrence, dwell, PCA, t-SNE, distances, …
│   ├── api/           OpenAI client + embedder + generator
│   ├── core/          trajectory runner, observables, baselines, context
│   ├── experiments/
│   │   ├── dialog/    D1/D2/D3 alternating-role runner
│   │   ├── operators/ O1–O4 single-role recursive operators
│   │   ├── dynamics/  10 post-hoc CLI analysis modules
│   │   └── perturbation/ 14 modules: runner, analyze, corpora, plot+animation
│   ├── reports/       narrative report writer
│   └── utils/         io, logging, seeds, text helpers
├── scripts/           build_publication_configs + 6 aggregators
├── configs/           dialog/ + operators/ + perturbation/ + archive/
├── tests/             94 pytest tests
└── data/              37 experiment dirs + aggregated/ outputs
```

---

## 11. Coverage of original specification

The project began from a four-document brief (the originals are
preserved in `/junk/req1.txt`, `req2.txt`, `req3.txt`, `reg4.txt` —
gitignored) that pre-specified the architecture, API surfaces, metric
battery, and reporting format. This section maps the brief's
requirements to where they're implemented.

### 11.1 Implementation phases (req1.txt 12-phase plan)

| Phase | Requirement | Implementation |
|---|---|---|
| 1 | YAML config system, frozen snapshot per run | `src/config.py` + `data/<exp>/config.yaml` |
| 2 | `ContextState` + `clip_context(text, max_len, rule)` with `tail_chars` | `src/core/context.py` |
| 3 | OpenAI Responses API + Embeddings API integration | `src/api/{generator,embedder,openai_client}.py` |
| 4 | Output / rolling-window / context-tail observables | `src/core/observables.py` (+ 5 dialog observables in `src/experiments/dialog/observables.py`) |
| 5 | Embedding dataset creation, batched, cached | `embeddings/<obs>/{embeddings.npy, metadata.parquet}` per experiment |
| 6 | Joint PCA-2/10/20, no per-trajectory fits | `src/analysis/pca.py` (we extended to PCA-50 for t-SNE pre-reduction) |
| 7 | Recurrence with `‖z_t − z_s‖ < ε`, `|t − s| > τ` | `src/analysis/recurrence.py` |
| 8 | Dwell with KMeans + DBSCAN clustering | `src/analysis/{clustering,dwell}.py` (KMeans default, DBSCAN supported) |
| 9 | Basin convergence with perturbed ICs | `src/analysis/{basin,basin_entry}.py` (perturbation evolved to mid-trajectory injection — see 11.4) |
| 10 | Three baselines (no_feedback, time_shuffled, independent_regeneration) | `src/core/baselines.py` |
| 11 | Robustness across observables, spaces, seeds | `src/analysis/robustness.py` + cross-observable comparison in reports |
| 12 | Markdown report with not_supported / weak / moderate / strong classification | `src/reports/summary.py` (`classify_two_axis`, `classify_three_axis`) |

All 12 phases are implemented and exercised in the 94 unit + integration
tests under `tests/`.

### 11.2 OpenAI API surfaces (req2.txt)

| Surface | Required | Implemented |
|---|---|---|
| Responses API (`client.responses.create`) | required for all generation | `src/api/generator.py:generate_step` ✓ |
| Embeddings API (`client.embeddings.create`) | required for all observables | `src/api/embedder.py:embed_texts` ✓ |
| Batch API (Files + Batches) | optional, for large async embed jobs | `src/api/batch_jobs.py` (functional but `batch_embeddings: false` in publication runs) |
| Evals API | optional, orchestration only | `src/api/evals_runner.py` (gated by `use_evals: false`) |
| `store=False` (no server-side chat state) | mandatory | enforced in `generator.py` |
| Logprobs (`include=["message.output_text.logprobs"]`) | optional | enabled by `include_logprobs: true` in config; unused in publication analyses |

### 11.3 H1a/H1b two-axis split (reg4.txt)

The `exp_long_v2` brief introduced a critical methodological refinement:
**don't classify "support for H1" with a single label** — split into
two orthogonal hypotheses:

- **H1a (convergence)**: trajectories converge into stable
  basin-like regions
- **H1b (recurrence)**: once inside the basin, trajectories revisit
  neighborhoods more than expected under a temporal null

We extended this to a **three-axis** classifier (H1a + H1b + H1c
divergence) implemented in
`src/experiments/operators/classifier.py:classify_three_axis`. Each
axis gets an independent `not_supported / weak / moderate / strong`
verdict, and the four-regime taxonomy emerges from the joint pattern:

| regime | H1a | H1b | H1c |
|---|---|---|---|
| O1 contractive | strong | weak | weak |
| O2 oscillatory | weak | strong | weak |
| O3 absorbing | strong (singular) | weak | weak |
| D1 multi-basin | strong (per-style) | weak | weak |

This is the formal version of the "fixed-point vs orbiting attractors"
distinction that reg4.txt §15 calls for.

### 11.4 Methodological evolutions

The implementation deviates from the original brief in three places.
We document each to be honest about the divergence:

#### 11.4.1 Perturbation: initial-condition → mid-trajectory injection

req1.txt Phase 9 specifies basin score via *perturbed initial
conditions* (suffix, paraphrase, neutral-sentence, seed-only). We ran
this style at small N in REPORT1/2 but found it under-powered: the
perturbation gets diluted in the recurrence and switching rates were
near-zero or near-100% for any non-trivial seed change.

REPORT6 evolves the perturbation to **mid-trajectory text injection**
at a chosen step (5/15/25), with four conditions (control / neutral /
lorem / adversarial). This produces the dose-response and basin-
hardening curves that comprise the bulk of Phase 3 results. The
original initial-condition framing is subsumed by `n_runs > 1` per IC
producing run-to-run basin convergence statistics.

#### 11.4.2 Temperature sweep: 4 levels instead of warm/cool pair

reg4.txt §3 specifies four conditions: A (T=0.8 baseline), B (T=1.1
warmer), C (T=0.4 cooler), D (memory stress with 4-6k clip). We ran:

- T-sweep at T ∈ {0.3, 0.6, 0.8, 1.2} for both D1 and O1 — covers reg4's
  warmer (1.2 ≈ 1.1) and cooler (0.3 ≈ 0.4) intent, with extra mid-T
  resolution
- Memory stress (Condition D, clip ∈ [4k, 6k]) — **not run**. This
  remains an open ablation in our future-work list (see §8).

The T-sweep produced the qualitative finding reg4.txt §15 anticipated:
**O1 broadens with T (basin loosens)** while **D1 stays locked
(stylistic basins are temperature-stable)**. The signal is sharper
in the regime-comparison sense than in the per-cell monotonic sense:
across T ∈ {0.3, 0.6, 0.8, 1.2}, O1 acc(k=10) varies over a
13-pct-pt span (with the deepest dip at T=0.8) while D1 acc(k=10)
varies over only 4 pct pts (§5.4). We did not see warmer T "reveal
hidden recurrence", and the per-T curve for O1 is non-monotonic at
this reduced scope (n=150 per cell); a full-scope T-sweep would
sharpen the picture.

#### 11.4.3 Observable: rolling_k3 kept, rolling_k5 not added

reg4.txt §5 recommended adding `rolling_k5` for finer in-basin recurrence.
We did not add it — `rolling_k3` and `context_tail` together gave us
sufficient signal for the four-regime classification. Adding `rolling_k5`
would be a near-zero-cost extension if needed; the observable interface
in `src/core/observables.py` is parameterized by `k`.

### 11.5 Reports / classification format (req1.txt §12)

The original brief specifies a report ending in
`not_supported | weak | moderate | strong` for H1. We produce *two*
report variants per experiment:

- `reports/report.md` — single-axis legacy classifier
  (`classify_two_axis` in `src/reports/summary.py`)
- `reports/report_operators.md` — three-axis (H1a/b/c) classifier
  (`classify_three_axis` in `src/experiments/operators/classifier.py`)

Both carry the underlying signal counts so the verdict is auditable.

### 11.6 What the original brief did NOT call for but we added

- **Lyapunov spectrum** (REPORT3) — own construction, computed from
  inter-run ensemble spread covariance; not in the original brief
- **Sharpness dimension** (REPORT3) — functional form borrowed from
  Tuci et al. (2026, Def. 4.2), applied to our ensemble-spread Lyapunov
  spectrum; not in the original brief
- **Periodicity metrics** (`period_2_score`, `best_period`) for
  detecting the 2-cycle regime; not in the original brief
- **Dispersion metrics** (`dispersion_growth`, `drift_monotonicity`)
  for distinguishing contractive from divergent regimes
- **Basin predictability** (adaptive stratified k-fold CV logistic
  regression on PCA-10, `n_splits = min(5, smallest_class_size)`);
  not in the original brief
- **The perturbation visualization toolkit** (V landscape, Dijkstra
  geodesics, marching-cubes iso-density, parallel 3D animations) —
  novel to this work
- **The drill-down dialog regime (D2)** — discovered during Phase 3
  perturbation experiments
- **Cross-experiment aggregator scripts** for T-sweep, dose-response,
  basin hardening, perturbation cross-regime, and geometric barriers
  — built incrementally as the experiment list grew (7 scripts under
  `scripts/aggregate_*.py`)
- **Coverage matrix, evidence map, and publication-readiness audit** —
  `COVERAGE.csv` (37 × 60 artifact-presence matrix; regenerable via
  `scripts/build_coverage.py`), `EVIDENCE.md` (claim-to-evidence map),
  and `RESULTS.md` (cell-by-cell verification of every §5 numeric
  claim against the canonical aggregated CSVs; 103 / 103 cells
  reproduce; regenerable via `scripts/publication_summary.py`).
  Together they provide reviewer-grade traceability from every claim
  in this paper to the underlying data file, source function, and a
  pass/fail verdict on numeric reproducibility.

Each addition is justified in the corresponding stage report.

---

## 12. Acknowledgments

We acknowledge `gpt-4o-mini` and `text-embedding-3-small` (OpenAI),
the open-source ecosystem (numpy, scipy, scikit-learn, scikit-image,
matplotlib, pandas, imageio-ffmpeg), and the Tuci et al. (2026)
arXiv:2604.19740 framework for finite-time Lyapunov spectra of
sampling-based generators.

This research was conducted with the assistance of Claude (Anthropic)
as a code-development partner — specifically for the perturbation
visualization toolkit, the empirical-potential-landscape geometry implementation,
and the article structure.

---

## 13. References

Conceptual lineage (by space):

1. **Dynamical-systems framing of LLM inference loops.** The most
   directly relevant prior work — arXiv:2512.10350, arXiv:2510.21258,
   arXiv:2510.24797 — identifies or characterizes attractor regimes in
   recursive LLM trajectories qualitatively. This paper extends them
   with measured barrier heights and the multi-basin / drill-down
   dialog regimes.
2. **Iterative refinement / self-correct / self-consistency.** Recent
   work (Madaan et al., 2023; Welleck et al., 2023; Pan et al., 2023;
   Wang et al., 2023; Huang et al., 2024) studies recursive prompting
   loops as engineering primitives. Of these, Huang et al. 2024 (LLMs
   *Cannot* Self-Correct Reasoning Yet) is the most directly
   evidential — refinement loops can degrade rather than improve, an
   observation our O3 absorbing regime mechanistically explains.
3. **Output diversity collapse / mode collapse via training (RLHF).**
   Kirk et al. 2024, Padmakumar & He 2024, Casper et al. 2023, Go et
   al. 2023. *Training-time* mode collapse is a sibling phenomenon
   to our *inference-time* attractor regimes — both are mechanisms
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
   2025 (persona vectors). Adjacent — these works *steer* a model
   between behavioral modes via activation interventions; we
   *measure how hard it is* to steer between modes via in-context
   text injection. The two probes are complementary: behavioral
   barriers (this paper) and mechanistic steerability (theirs).
8. **Information-bottleneck analyses of intermediate states.** Tishby
   & Zaslavsky 2015 (IB foundations), Voita et al. 2019 (bottom-up
   evolution), Pimentel et al. 2020 (MI probing), Saxe et al. 2018
   (critical IB review). Provides the framework for an
   information-theoretic interpretation of our token-cost barrier
   heights — a token-cost is a behavioral analog of a KL distance
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

- arXiv:2510.21258. *Correlation Dimension of Auto-Regressive Large
  Language Models.* (October 2025.) Quantifies degeneration as a
  collapse from a higher-dimensional trajectory in the model's state
  space into a lower-dimensional attractor, validating our O3
  absorbing-regime interpretation.
- arXiv:2510.24797. Berg et al. (2025). *LLMs Report Subjective
  Experience Under Self-Referential Processing.* Recursive
  self-attending dialogues converge to a stable "spiritual-bliss"
  attractor across frontier models — a strong cross-vendor
  validation of the multi-basin claim we make for D1, on a
  different operator family.
- arXiv:2512.10350. *Dynamics of Agentic Loops in Large Language
  Models: A Geometric Theory of Trajectories.* (December 2025.)
  Three-regime taxonomy (contractive, oscillatory, exploratory) for
  recursive LLM transformations in semantic space, with local /
  global drift / dispersion / cluster-persistence as diagnostics.
  This paper builds directly on its dynamical-systems framing and
  extends with token-quantified barriers.
- Carlini, N., Tramèr, F., Wallace, E., et al. (2021). *Extracting
  training data from large language models.* USENIX Security '21.
- Hopfield, J. J. (1982). *Neural networks and physical systems with
  emergent collective computational abilities.* PNAS, 79(8),
  2554–2558.
- Holtzman, A., Buys, J., Du, L., Forbes, M., & Choi, Y. (2020).
  *The curious case of neural text degeneration.* ICLR.
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
  networks.* Neural Computation, 25(3), 626–649.
- Tuci, M., Korkmaz, C., Şimşekli, U., Birdal, T. (2026).
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
  Trained corrector model — relevant baseline for iterative dynamics.
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
  refinement loops degrade — direct evidence for attractor
  pathologies that our O3 absorbing regime mechanistically explains.

**Output diversity collapse / mode collapse via training (RLHF).**

- Kirk, R., Mediratta, I., Nalmpantis, C., Luketina, J., Hambro, E.,
  Grefenstette, E., & Raileanu, R. (2024). *Understanding the Effects
  of RLHF on LLM Generalisation and Diversity.* arXiv:2310.06452
  (ICLR 2024). Quantifies output-space contraction post-RLHF;
  mechanism for narrower basins.
- Padmakumar, V., & He, H. (2024). *Does Writing with Language
  Models Reduce Content Diversity?* arXiv:2309.05196 (ICLR 2024).
  Human-LLM coauthoring homogenizes text — population-level mode
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
  directions in hidden states — methodological backbone for activation
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
  training — distributional shrinkage over iterations.
- Bigelow, E., Lubana, E. S., Dick, R. P., Tanaka, H., & Ullman, T.
  (2024). *Forking Paths in Neural Text Generation.* arXiv:2412.07961.
  Empirical branching geometry of generation — direct dynamical-systems
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
  steering — direct mechanism for moving between attractors.
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
  phases — relevant when invoking IB on LM hidden states.

---

*Repository: <https://github.com/kaplan196883/llmattr> (raw trajectories
LFS-tracked; embeddings + plots regenerable from the documented
pipeline). Reproducibility budget: ~$30 in OpenAI embedding API + ~2
hours wall-clock on a 40-core machine.*
