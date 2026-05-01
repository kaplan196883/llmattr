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
