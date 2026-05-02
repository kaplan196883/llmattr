=== Abstract ===
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

Practi
...[truncated]

=== Plain-language summary ===
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

1. **Stress-test recursive agents with persis
...[truncated]

=== Introduction (§1) ===
## 1. Introduction

### 1.1 Phenomenon

Recursive LLM systems increasingly feed model outputs back into future prompts: agents revise plans, assistants summarize tool results, and dialog systems carry state forward. Such loops often appear to settle into attractor-like regimes, but an operational question remains unresolved: how many injected tokens are required to move a settled loop, and does that movement persist?

We answer this by separating the generator from the context-update rule. In append-mode continuation, adversarial in-distribution perturbations produce a real raw dose response, with $\mathrm{ED50}_{\mathrm{raw}}\approx 40$ tokens, but paired controls already diverge about 35% of the time and persistent escape is not reached for doses up to 400 tokens. In replace-mode, apparent fragility is largely an overwrite effect of the update rule. Thus the stability of recursive loops is not a property of the model alone; it is jointly determined by model, memory policy, perturbation content, and persistence criterion.

![Fig 1. **Headline perturbation dose response.** Summary dose-response view for recursive-loop perturbations, emphasizing that raw switching, stochastic floor, and persistent escape are distinct endpoints. The figure orients the reader before the formal endpoint definitions. Source: `data/aggregated/perturbation_dose_response/dose_response.png`.[^Fig1]](data/aggregated/perturbation_dose_response/dose_response.png)


The same distinction appears in coding agents, where the loop state may include tool logs, patches, summaries, pinned requirements, and recent files; the memory policy determines whether new information accumulates, overwrites, or is role-structured.

The state-generator-update view makes this distinction explicit: the state is the prompt-visible memory at the current step, the generator is the stochastic language model, and the update rule maps state and output into the next state. If the term context-update nudge is used, it denotes this update operation, not a separate intervention inside the model.

Recent work has shown that recursive LLM trajectories can exhibit contractive, oscillatory, exploratory, degenerate, or convergent self-referential regimes. These studies establish that attractor-like structure is empirically visible, but they do not measure the perturbation dose required to move a trajectory between regimes, nor do they separate that dose from ordinary stochastic divergence or from update-rule overwrite mechanics.

The resulting measurement problem has three parts. For a settled recursive trajectory, how many injected tokens are required to produce final-cluster switching, how much of that switching exceeds the stochastic control floor, and how often does the perturbation produce a visible basin jump that persists to the terminal step? A single final disagreement cannot answer this, because it may reflect real redirection, unperturbed sampling divergence, or a transient displacement followed by recovery.

### 1.2 Question

We study recursive LLM loops as bounded stochastic systems under a state-generator-update decomposition. The same generator can behave differently under append, replace, and dialog updates because those updates expose different histories, role structures, and memory contents to the next sampling step.

1. **Architecture:** How do append, replace, and dialog update rules alter the accessible loop state?
2. **Dose response:** For a settled trajectory, how does switching probability vary with injected-token dose and perturbation type?
3. **Persistence:** Which apparent switches exceed the stochastic control floor and remain through the terminal step?

These questions convert "the loop gets stuck" into measurable quantities: raw switching, net switching, and persistent escape. Raw switching is terminal cluster disagreement between a perturbed trajectory and its paired control. Net switching subtracts the measured control compared with control stochastic floor. Persistent escape requires a visible basin jump after injection that remains present at the terminal step.

### 1.3 Contributions

The paper's contributions are best stated as five claim-level takeaways.

**Claim 1: recursive-loop stability is jointly determined by generator and update rule (§3).** Append, replace, and dialog loops differ because their context-update operators expose different histories to the model. The state-generator-update formalism treats the update operator as a first-class 
...[truncated]