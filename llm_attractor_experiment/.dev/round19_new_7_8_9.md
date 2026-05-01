## 7. Limitations

*The experiments support a structured account of recursive LLM dynamics, but the strongest claims remain tied to the tested generator families, representation pipeline, memory regime, and text-only nudge setting.*

### 7.1 Evidence is strongest for OpenAI generator–nudge systems

The model-coverage result is broad enough to rule out a single-run curiosity, but not broad enough to establish model-agnostic dynamics. The current audit spans six generators, including Anthropic and Google systems, yet the densest evidence remains concentrated in OpenAI generator–nudge systems, especially the gpt-5-mini / nano O1 and D1 cells. Those cells carry the deepest replication, the most complete artifact stack, and the clearest regime-level separation.

This matters because the qualitative taxonomy is motivated by the generator–nudge factorization in §3, not by a special property of one model checkpoint. The append, replace, and dialog distinctions plausibly arise from how the update operator rewrites the next context. However, barrier heights, basin geometry, switching thresholds, and even the number of empirically separable regimes can vary with decoding behavior, tokenizer structure, alignment tuning, refusal style, and context-management details.

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

The drill-down dialog regime is the least mature of the reported regimes. The current D2 evidence indicates a distinct form of topic-anchored content gravity under role-structured questioning, but it was tested at substantially smaller scale than the main O1–O3 and D1 regimes. The reported switching estimate is 64% with a ±10 percentage-point bootstrap confidence interval from 25 trajectories at 50 steps.

This is enough to motivate D2 as a candidate regime, but not enough to place it on the same empirical footing as the publication-scale cells. Dialog structure is a rich nudge family: drill-down questioning, debate, role-play, adversarial interrogation, and multi-party deliberation may create different balances between style persistence and content anchoring. D2 should therefore be treated as exploratory until it receives the same publication-scale replication and cross-model audit as the other headline regimes.

### 7.5 Production agent and tool-use claims require new observables

The experiments measure recursive language-model loops, not deployed coding agents or tool-using autonomous systems. They do not include file-system state, code edits, compiler feedback, test execution, tool schemas, repository-specific correctness criteria, or multi-step planning traces. The implications drawn in §6.6 for coding agents are architectural extrapolations from recursive-loop dynamics, not measurements of Cursor, Cline, Devin, Claude Code, LangGraph-based agents, SWE-Bench systems, or in-house coding scaffolds; see companion developer-journal essay.

A production-agent benchmark would need additional observables. Patch diffs, files touched, tests run, failing tests remaining, tool-call sequences, policy violations, injected-document provenance, and post-perturbation plan persistence would need to be measured alongside or instead of embedding-space trajectory structure. The framework in §3 and the perturbation protocol in §4.5 transfer cleanly, but the numerical barriers in §5 do not transfer without re-measurement.

The key bridge is that memory policy becomes a behavioral variable. Full-history append, rolling-window truncation, generated-summary replacement, pinned-goal memory, and provenance-preserving hybrid memory can induce different perturbation profiles even when the base model and task are held fixed. The present paper supplies the measurement logic; deployed-agent claims require an agent-native implementation of that logic.

## 8. Future directions

*The next step is to turn the present perturbation framework from a controlled recursive-loop study into a comparative measurement program for model families, memory policies, dialog scaffolds, and deployed agents.*

### 8.1 Cross-vendor replication at publication scale

The highest-priority extension is publication-scale replication across vendors. The central question is not whether barrier heights match numerically, but whether the ordering of append, replace, and dialog regimes survives across generators with different alignment methods, tokenizer families, refusal policies, and decoding implementations. A replicated ordering would support the claim that regime structure is a property of the generator–nudge system rather than a peculiarity of one model family.

The next audit should include Anthropic, Google, Mistral, and open-weight models at comparable sample sizes, with N=20–60 trajectories per cell where cost permits. The full sweep should include O1, D1, and D2 rather than only the most stable headline cells. D2 is particularly important because dialog topology is under-sampled in the current evidence base and may vary more strongly across vendors than simple append or replace loops.

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

Dialog needs its own publication-scale map. Drill-down dialog is the first candidate beyond the main dialog regime, but the space is larger: debate, role-play, brainstorming, adversarial questioning, tutor–student exchange, and multi-party deliberation may each define different nudge operators. These topologies should be evaluated with the same endpoints used in §4.5 and §5: raw switching, net switching above stochastic floor, persistence, recurrence, and basin geometry.

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

The pipeline is organized into four re-runnable stages: generate, embed, analyze, and aggregate. Generation produces `steps.jsonl`; embedding produces `embeddings/<observable>/embeddings.npy`; analysis produces metric CSVs and per-experiment reports; aggregation produces the cross-experiment tables under `data/aggregated/`. `python -m scripts.build_coverage` regenerates the 37 × 60 coverage matrix, and `python -m scripts.publication_summary` regenerates the 103 / 103 numeric-claim verification table, including the ED50 and audit-table checks. Together, the tests, coverage matrix, evidence map, and regenerated results provide an end-to-end path from each reported claim to the script that recreates it.
