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
