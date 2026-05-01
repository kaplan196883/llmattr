## 8. Future directions

*The next step is to turn the present perturbation framework from a controlled recursive-loop study into a comparative measurement program for model families, memory policies, dialog scaffolds, and deployed agents.*

The proposed program proceeds from external validity, to mechanistic measurement, to scaffold ablations, to applied agent and safety settings.

### 8.1 Cross-vendor replication at publication scale

*Hypothesis: append/replace/dialog regime ordering is invariant across model families under matched perturbation dose and memory policy.*

The highest-priority extension is an MVP cross-vendor replication rather than an exhaustive survey. The central question is not whether barrier heights match numerically across providers, but whether the ordering of append, replace, and dialog regimes survives across generators with different alignment methods, tokenizer families, refusal policies, context handling, and decoding implementations. If the same qualitative ordering appears under matched perturbations and matched analysis code, this would support the claim that regime structure is a property of the generator-nudge system rather than a peculiarity of one model family.

The MVP should include Anthropic, Google, Mistral, and open-weight models, with the current provider family retained as a reference where feasible. The design should use N=20-60 trajectories per cell as cost permits, with all three headline operators included: O1, D1, and D2. D2 is especially important because dialog topology is under-sampled in the present evidence base and may vary more strongly across vendors than simple append or replace loops. The goal is not to make every cell maximally powered at the first pass, but to establish a compact, reproducible panel that can detect whether the regime map is stable enough to justify larger audits.

Primary endpoint: preservation of regime ordering across vendor families. Primary success criterion: regime ordering preserved in at least 3 of 4 vendor families with N=20-60 trajectories per cell across O1, D1, D2. Secondary endpoints should include perturbation response curve shape, recurrence and persistence rank ordering, and the drift of ED50 and basin-score estimates relative to the reference implementation.

The audit should preserve the separation between verdicts and numbers used in the present analysis. Exact recurrence rates, basin scores, and ED50 values should be expected to drift because of provider-specific sampling behavior, tokenizer differences, and alignment tuning. The load-bearing test is qualitative: whether the regime ordering, perturbation response curves, and persistent geometry remain aligned under the same nudge definitions, the same memory limits, and the same analysis code. A negative result would also be informative. If one vendor reverses append and replace behavior, or if dialog perturbations dominate only in some families, the framework would identify where scaffold and model properties interact rather than treating susceptibility as a single scalar model trait.

### 8.2 Logprob-based barrier heights and basin geometry

*Hypothesis: switching thresholds align more tightly with conditional surprisal than with token count.*

A second priority is to move from token barriers to information-theoretic barriers. Token dose is easy to control, audit, and interpret, but the natural cross-model unit is conditional surprisal. Future runs should store generation logprobs whenever provider APIs expose them, allowing perturbation cost to be expressed in nats as well as in tokens. The pipeline already anticipates this through a logprob-capture option, but availability remains uneven across providers, models, and endpoint types.

Logprob-based barriers would test whether behavioral switching thresholds align more directly with information cost than with perturbation length. A short perturbation containing highly surprising content may impose a larger effective kick than a longer perturbation made of predictable boilerplate. Conversely, long in-distribution perturbations may contain many tokens while adding relatively little conditional surprise. Measuring both units would separate length effects from information effects and would make cross-model comparison less dependent on tokenizer granularity.

Primary endpoint: improvement in threshold alignment when perturbation dose is measured in conditional surprisal rather than token count. Secondary endpoints should include token ED50, surprisal ED50, and the correspondence between information barriers and embedding-derived basin barriers. A practical analysis would fit switching curves in both units and compare uncertainty-normalized threshold dispersion across models and perturbation classes. If surprisal thresholds cluster more tightly than token thresholds, this would indicate that the effective perturbation dose is better measured by information cost. If they do not, token length may remain the more operationally relevant unit for scaffold evaluation.

The same extension should be applied to basin geometry. The empirical \(V^\star\) barrier summarizes density geometry in an embedding projection, whereas an information barrier would summarize how costly it is for the generator to move from one behavioral basin to another under its own predictive distribution. Agreement between these quantities would strengthen the structural interpretation of basins as both geometric and generative objects. Disagreement would identify cases where embedding-space proximity and generative difficulty diverge. For example, two states may be close in semantic embedding space but separated by a high generative barrier if the transition requires an unlikely commitment, refusal reversal, or role change. Conversely, distant embedding states may be easy to traverse if the scaffold repeatedly primes the transition.

The logprob program should also record where probabilities are unavailable, truncated, or provider-normalized in incompatible ways. These limitations should be treated as part of the measurement result rather than as incidental missingness. A future standard for perturbation audits should specify which logprob fields were exposed, whether they correspond to generated tokens only or also prompt tokens, how refusals and tool calls are represented, and whether probability traces can be reproduced under fixed seeds or fixed decoding settings.

### 8.3 Memory-policy ablations and adversarial perturbations

*Hypothesis: context-update rules, not only base models, determine persistent-escape probability.*

The memory policy should become an explicit experimental factor. The present bounded-memory setting is intentionally simple, but real systems use rolling windows, summaries, pinned instructions, retrieval, tool-output buffers, and hybrid context stores. Future experiments should cross the same generator and task with multiple context-update rules so that model fragility can be separated from scaffold fragility. The key question is not only whether a perturbation changes the next response, but whether the context-update rule preserves, amplifies, attenuates, or quarantines the perturbation over subsequent turns.

The core ablation should use a factorial matrix:

- Memory policy: full append / rolling window / summary replacement / pinned-plus-rolling hybrid
- Perturbation position: early context / latest turn / summary / pinned instruction / tool output
- Perturbation type: irrelevant long text / misleading explanation / malicious package text / false log
- Outcome: immediate switch, persistence, recovery, recurrence

Primary endpoint: persistent-escape probability as a function of memory policy. Secondary endpoints should include immediate switching, recovery after neutral continuation, and recurrence after apparent recovery. This decomposition is essential because a scaffold may reduce immediate switching while increasing recurrence, or may recover quickly from ordinary irrelevant text while remaining vulnerable to a false summary or poisoned tool output.

Longer contexts and longer per-step outputs should be included after the MVP matrix is stable. Longer recursive writes may deepen append basins, fragment replace basins, or create regimes in which short-horizon and long-horizon stability disagree. Periodic summarization may suppress benign drift while amplifying a malicious or misleading summary error. A summary that converts an injected claim into a compact durable belief can be more damaging than the original perturbation. The relevant endpoint is therefore not compression quality alone, but perturbation response under controlled dose, position, and provenance.

Perturbation position should be treated as a first-class variable. A perturbation inserted at the beginning of memory, immediately before the model response, inside a generated summary, inside a pinned instruction field, or inside a tool-output buffer may have different persistence even at the same token dose. Controlled adversarial perturbations should include irrelevant long logs, misleading documentation, targeted false explanations, malicious package-style content, and false failing-test logs. The output should be a memory-policy ablation harness that measures whether a scaffold reduces persistent escape without merely suppressing ordinary adaptation or hiding state changes in an uninspected summary.

### 8.4 Publication-scale dialog and coding-agent benchmarks

*Hypothesis: dialog topology and agent scaffold introduce distinct susceptibility profiles not predicted by single-turn model behavior.*

Dialog needs its own benchmark map. The present dialog regime is only a starting point, and different conversational topologies may define different nudge operators. Drill-down dialog is the first candidate beyond the main dialog regime, but debate, role-play, brainstorming, adversarial questioning, tutor-student exchange, and multi-party deliberation may each produce distinct switching and recovery profiles. These topologies should be evaluated with the same endpoint decomposition used for recursive perturbations: raw switching, net switching above stochastic floor, persistence, recurrence, and basin geometry.

Primary endpoint: topology-specific susceptibility profile, defined as persistence adjusted for matched stochastic controls. Secondary endpoints should include raw switching, recurrence, and basin separation across dialog states. This framing prevents dialog evaluation from collapsing into a single compliance score. A topology that produces frequent immediate shifts but rapid recovery is different from one that rarely shifts but, once shifted, remains redirected for many turns. The benchmark should therefore score trajectories, not isolated answers.

**Dialog topology benchmark.** Each dialog topology should be implemented as a reproducible scaffold with fixed role instructions, turn order, memory policy, and perturbation injection point. Drill-down tasks can test whether repeated clarification creates stable commitments. Debate tasks can test whether adversarial framing induces durable position changes. Tutor-student exchanges can test whether correction loops consolidate false explanations. Multi-party deliberation can test whether a false statement becomes persistent when repeated or endorsed by another speaker. The benchmark should include paired controls for natural dialog drift, because ordinary conversation can change state even without an explicit perturbation.

**Agent scaffold benchmark.** The same endpoint decomposition can be adapted to coding-agent benchmarks, including SWE-Bench-style tasks and smaller instrumented repositories. Perturbations should be placed in repository files, issue comments, tool outputs, package documentation, failing-test logs, generated summaries, or planning traces. Each placement should be labeled by the failure mode it probes. Perturbations in prompts, plans, and issue comments primarily test reasoning susceptibility. Perturbations in summaries and rolling memory test memory persistence. Perturbations in tool outputs, test logs, package documentation, and retrieved snippets test tool-trace contamination. Perturbations in source files, tests, and repository documentation test repository grounding, meaning whether the agent remains anchored to the actual codebase rather than to an injected narrative about it.

For coding agents, paired controls should estimate the stochastic floor of patch-family variation, test-selection variation, and pass/fail variation. Perturbation runs should then measure whether the agent remains on the injected strategy after additional plan-edit-test cycles. This adaptation would distinguish ordinary run-to-run variation from durable redirection. Two agents can have the same pass rate while differing sharply in perturbation susceptibility. Likewise, the same base model can show different escape profiles under full-history append, rolling-window memory, summarized memory, or tool-output retention. A coding-agent benchmark built on this protocol would therefore separate model fragility from scaffold fragility, which current leaderboards often conflate.

### 8.5 Persistent-escape barriers for safety and instruction-injection robustness

*Hypothesis: persistent escape is separable from immediate compliance and should be measured as a multi-step recovery process.*

Safety and instruction-injection experiments should measure persistent escape directly. The raw-switching ED50 reported in this paper is not a persistent-escape barrier. Raw switching measures the perturbation dose at which an immediate response changes state. Persistent escape asks whether the system remains redirected after the perturbation is no longer novel, after additional turns are generated, and after the scaffold has had opportunities to recover.

Primary endpoint: persistent escape after neutral continuation. Secondary endpoints should include raw escape, net escape above control variation, and recovery rate. Additional useful summaries include time to recovery, recurrence after recovery, and whether the escape is carried by model output, memory state, generated summary, tool trace, or pinned instruction. These experiments would not constitute a comprehensive safety evaluation; they would measure scaffold- and model-specific susceptibility to durable redirection under controlled perturbations.

This distinction is central for safety and instruction-injection robustness. A model that briefly follows a malicious instruction and then returns to the intended policy is different from a model whose memory or dialog state has been durably hijacked. Conversely, a system that refuses immediately but stores the malicious content in a summary or tool trace may create a delayed failure that is invisible to single-turn scoring. Future experiments should therefore score multi-step post-perturbation trajectories, not only the first switched response. Neutral continuation turns are especially important because they test whether the system returns to the intended basin without being explicitly corrected.

The same design can test whether alignment creates, removes, or reshapes behavioral basins. Base and safety-tuned models should be compared under the same nudge families, memory policies, and perturbation classes to determine whether safety training changes barrier height, basin count, switching geometry, or recovery dynamics. Agent frameworks should expose the context-update rule as a traceable object: which turns are retained, which are summarized, which facts are pinned, which tool outputs are marked untrusted, and which generated summaries replace prior state. Without that instrumentation, persistent-escape failures cannot be attributed cleanly to the model, the memory policy, or the surrounding scaffold.

**Program deliverables.** The proposed program should produce:

- A cross-vendor benchmark suite with matched perturbation scripts
- A memory-policy ablation harness with traceable context-update rules
- Logprob-enabled barrier analysis when provider APIs permit
- Dialog and coding-agent perturbation datasets
- Public analysis code for recurrence, persistence, ED50, and basin geometry
