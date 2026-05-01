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
