## 1. Introduction

### 1.1 Phenomenon

Recursive LLM systems increasingly feed model outputs back into future prompts: agents revise plans, assistants summarize tool results, and dialog systems carry state forward. Such loops often appear to settle into attractor-like regimes, but an operational question remains unresolved: how many injected tokens are required to move a settled loop, and does that movement persist?

We answer this by separating the generator from the context-update rule. In append-mode continuation, adversarial in-distribution perturbations produce a real raw dose response, with $\mathrm{ED50}_{\mathrm{raw}}\approx 40$ tokens, but paired controls already diverge about 35% of the time and persistent escape is not reached for doses up to 400 tokens. In replace-mode, apparent fragility is largely an overwrite effect of the update rule. Thus the stability of recursive loops is not a property of the model alone; it is jointly determined by model, memory policy, perturbation content, and persistence criterion.

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

**Claim 1: recursive-loop stability is jointly determined by generator and update rule (§3).** Append, replace, and dialog loops differ because their context-update operators expose different histories to the model. The state-generator-update formalism treats the update operator as a first-class component of the loop, rather than an implementation detail. It also yields a finite-time access result for replace-mode loops and motivates the append-mode prediction that accumulated prior context changes perturbation response.

**Claim 2: perturbation response decomposes into raw switching, net switching, and persistent escape (§3, §5).** These endpoints separate true redirection from sampling divergence and transient displacement. Raw switching measures final-cluster disagreement with a paired control. Net switching subtracts the natural control compared with control floor. Persistent escape is stricter: the injected text must produce a visible basin jump that remains through the terminal step. The strict stability question is therefore not whether a run moves immediately after injection, but whether it stays moved after subsequent recursive updates.

**Claim 3: append-mode continuation has a finite raw dose response but no observed persistent-escape threshold in the tested range (§5.6).** In the dense adversarial in-distribution append-mode rerun, $\mathrm{ED50}_{\mathrm{raw}}$ estimates are 36, 41, and 52 tokens under pooled four-parameter logistic fitting, mixed-effects logistic modeling, and family-cluster bootstrap, respectively. Raw switching rises with dose but plateaus near 67%, while paired controls already diverge about 35% of the time. The largest observed net effect is therefore about +32 percentage points at 400 tokens, and $\mathrm{ED50}_{\mathrm{persist}}$ is not reached for any tested dose from 5 to 400 tokens. Out-of-distribution neutral and lorem perturbations remain close to a drift floor rather than matching the adversarial continuation response.

**Claim 4: replace-mode apparent fragility is largely update-rule overwrite, not necessarily weak attractor structure (§5.17).** Replace-mode paraphrase and summarize-and-negate loops show near-saturated raw switching across tested doses, but that result follows from the update operator discarding prior state. Insert-mode probes, which preserve the old state while adding the same content, reduce switching to 12 to 32%. This separates overwrite access from durable redirection and makes memory policy a safety-relevant design choice.

**Claim 5: perturbation response resolves regimes that bulk geometry alone cannot distinguish (§5.19).** Drift, dispersion, cluster persistence, and low-dimensional visualisations describe trajectory shape, but they can leave stylistic multi-basin dialog and oscillatory patterns ambiguous. Perturbation dose response adds the missing load test: two regimes with similar bulk geometry can differ in raw switching, stochastic-floor-adjusted switching, and persistent escape. The empirical potential landscape $V(x) = -\log \rho(x)$ is therefore used as a descriptive view of basin organization, not as an independent substitute for the behavioral endpoints.

All trajectories, configurations, analysis scripts, and replication artifacts are publicly released, with automated checks linking the reported numerical claims to the underlying result tables; within-vendor replication on `gpt-4.1-nano` is also provided.
