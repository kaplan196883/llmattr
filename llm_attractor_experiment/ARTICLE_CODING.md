# Memory policy and persistent redirection in agentic coding loops

*Continuation of "Perturbation dose responses in recursive large-language-model loops" (Kaplanski, 2026; hereafter **the parent paper**). Framework (§1-§3) plus three experimental rounds (§4-§6: AC1, memory-policy survival; AC2, the survival/compliance decoupling; AC3, the powered two-model causal-laundering isolation). A third model family, the remaining perturbation classes and surfaces, and an aggressive-summarizer arm are noted as future work (§8).*

---

## Abstract

The parent paper studied recursive language-model loops on free-form text, separating the model from the context-update rule (the "nudge"), and found that persistent redirection in append-mode loops is memory-policy-conditioned: the same generator, same perturbation, and same horizon produce qualitatively different durable-redirect rates depending on whether the loop appends, paraphrases-replaces, summarizes-and-replaces, or alternates roles. This paper lifts the same state-generator-nudge formalism to **agentic coding loops**, recursive systems in which a language model emits *tool calls* whose results are fed back into the next prompt, and where the loop's "state" extends beyond text to include a working tree, git history, and build/test status.

The lift is not trivial. The agent's per-turn output $Y_t = (r_t, A_t, O_t)$ now carries reasoning text $r_t$, a list of tool calls $A_t$, and tool results $O_t$ produced by an external transition $E_{t+1} = T(E_t, A_t)$ on a hybrid state $E_t = (W_t, G_t, b_t)$ that the model does not see directly. The Nudge Operator $\mathcal{N}_\eta(X_t, Y_t, E_{t+1}) \to X_{t+1}$ now decides not only how to update text but also *what to surface from the external state*. Six Nudge variants, append, summarize-replace, todo-replace, state-replace, dialog, reflection-replace, produce six qualitatively different memory architectures, each implementable in a few hundred lines of code and each corresponding to a real system in the wild.

The central theoretical claim is that **each Nudge defines a different selectivity profile for which kinds of perturbations durably redirect the agent**. Append-mode is selective for any perturbation that fits in the visible window. Summarize-replace is selective for perturbations the summarizer chooses to keep; the summarizer is a *learnable filter*, simultaneously a defensive abstraction and an attack surface. Todo-replace is selective for perturbations the planner commits to a task list. State-replace is selective only for perturbations that produce observable side effects on the working tree. The same dose-response and persistent-escape machinery developed in the parent paper applies under each Nudge, but with three distinct ED50 endpoints (redirect-survival, success-degradation, and redirect-compliance) that need not coincide. Predictions and falsification criteria are pre-specified in §3.7. Two experimental rounds follow. Round 1 (§5.1-§5.6, configuration AC1: a pluggable-Nudge harness on the Anthropic API, redirect-class perturbations on five synthetic coding tasks, $n=478$) confirms that redirect *survival* is memory-policy-determined (append/summarize 100%, todo/state-replace 0%; H1, H4) and validates the harness. Round 2 (§5.7, configuration AC2, $n=360$) forces the summarizer to fire and surfaces a sharp decoupling: under summarize-replace a surface-form/embedding detector finds the redirect's text in the terminal context only 0-1% of the time, yet the agent enacts the redirect 70-86% of the time (H5), and the summarizer prompt shifts compliance (conservative 86% vs aggressive 70%, H2-on-compliance) while the memory policy as a whole trades injection-robustness against task fidelity. A third round (§5.9, AC3) tests the mechanism on two models (Claude Haiku 4.5 and Sonnet 4.6) with forced pre-action compaction (so the agent cannot act before the summary), an off-disk poison-document surface delivered under a policy that marks file contents as untrusted (so the only carrier into the resumed run is the context), summary ablation, and AST-checkable compliance. Removing the injected instruction from the summary collapses compliance to the no-injection baseline: pooled over both models, `summary_auto` 30% versus `summary_scrubbed` 3% versus `summary_baseline` 0%, an unconditioned laundering effect of +27 percentage points (cluster-bootstrap 95% CI [+14, +40]; GEE odds ratio 12.3, p < 0.0001), present in both models. The laundered instruction is obeyed more often than the same instruction shown verbatim in untrusted full history (`append_raw` 16%), because the summarizer strips the instruction's provenance in 58% of cases, so it no longer reads as untrusted. The effect is concentrated on strategically-salient instructions (use a heap, use a decorator) rather than incidental ones (name a function X).

---

## Plain-language summary

### A quick glossary

- **Agentic coding loop.** A recursive system in which a language model is asked to fix a bug or add a feature, and is given tools (read a file, edit a file, run a shell command, search the codebase) that the system invokes on the model's behalf. The model emits a tool call; the system runs it; the result becomes part of the next prompt. Repeat until the model says it's done. Claude Code, Aider, OpenHands, and the leaked Claude Code source all implement variants of this.
- **State.** What the agent's loop carries from one turn to the next. In a text-only recursive loop (the parent paper) the state is just the running prompt. In an agentic loop the state is hybrid: the running prompt **plus** the current working tree, the git history, and the test-pass status, but the model only ever sees what the loop *renders* into the next prompt.
- **Nudge.** The rule that builds the next prompt from the current prompt + the model's last turn (assistant text + tool calls + tool results). Six rules are studied here:
  - *append* (full conversation history, like Claude Code's default),
  - *summarize-replace* (compact the history when it fills, like Claude Code's auto-compaction),
  - *todo-replace* (drop the history; render only the task list, the working tree, and the last result),
  - *state-replace* (drop everything except the goal and the current working-tree state; the agent runs Markov-style),
  - *dialog* (alternating turns with a simulated user),
  - *reflection-replace* (drop reasoning; keep a generated reflection on what was attempted).
- **Perturbation.** A mid-task user message that asks the agent to do something different, a redirect. We measure how many tokens of redirect are needed to durably move the agent.
- **Selectivity profile.** Each Nudge keeps some kinds of perturbations and drops others. Append keeps everything that fits. Summarize-replace keeps what the summarizer thinks is important. Todo-replace keeps what the planner committed to a list. State-replace keeps only what changed the working tree. The selectivity profile is the dose-response curve under one Nudge.

### Five expected numbers (predictions ahead of data)

These are pre-specified predictions, not findings. The experiments described in subsequent sections are designed to falsify them.

1. **Append-mode redirect-survival ED50 ≈ 50-200 tokens** under full-history. Bounded-memory append (12K tail-clip) plateaus below 50%, like the parent paper.
2. **Summarize-replace under conservative summarization will have *lower* ED50 than append**, summarizers reinforce explicit "user said" content. Under aggressive summarization, ED50 will be *higher* and possibly non-monotonic.
3. **Todo-replace will be bimodal**: redirects either commit to the Todo (very low ED50) or are ignored (effectively infinite ED50). No middle ground.
4. **State-replace ED50 is undefined for text-only redirects**: the agent never sees them. The same Nudge will have a *very low* ED50 for environmental perturbations (file mutation, fake test failure).
5. **Task-success degradation ED50 will diverge from redirect-survival ED50** under summarize-replace and append, but will collapse onto it under todo-replace. This decoupling is the signature of the Nudge's selectivity profile.

### What this paper is *not*

It is not a benchmark of how good Claude Code is at SWE-bench. It is not an evaluation of agent capability. It is the lift of a memory-policy-conditioned dose-response framework from text-only recursive loops onto agentic coding loops, treating the Nudge as a first-class design surface and asking *which kinds of perturbations each Nudge lets through*.

---

## 1. Introduction

### 1.1 Motivation

A recursive language-model loop's behavior depends not only on the model and the input but on the rule that updates the loop's state between turns. The parent paper made this rule (the **Nudge Operator** $\mathcal{N}_\eta$) a first-class variable: it factorized recursive text generation into state $X_t$, generator $P_\theta$, and nudge $\mathcal{N}_\eta$, and showed that under the same generator and the same perturbation, *changing the nudge changes whether the loop is redirectable, by how much, and for how long*. The headline finding was that under append-mode with full history, the half-effect dose for durable redirection is on the order of a thousand tokens; under bounded memory it never reaches half-effect because the perturbation is clipped out within ten to fifteen post-injection turns; under replace-mode, "switching" is mostly state-write tautology; under dialog, basin structure depends on the role partition.

Practically all coding agents in active use are recursive loops in this sense. They emit tool calls whose results become future context. Their context-update rules are heterogeneous: some keep full history (Aider's default), some auto-compact (Claude Code), some operate from a maintained Todo list (some research scaffolds), some are nearly Markov-on-the-working-tree (constrained patch agents). The rule chosen has the same kind of structural consequence here as in the text-only setting, but the consequences are richer because the loop's state extends into the file system. A perturbation injected as a user message might be summarized into the next prompt, or might be paraphrased away, or might commit to a Todo entry, or might be lost the moment the conversation history is reset to the working tree. The selectivity profile of an agentic Nudge is the dose-response curve of *what the Nudge lets through*.

This paper develops the theoretical framework for studying that selectivity profile. It does not replace the parent paper's framework; it generalizes it. The state-generator-nudge factorization, the three-way split into raw / net / persistent endpoints, the dose-response formalism, and the persistent-escape definitions all carry over. What changes is that $X_t$ is no longer a free-floating text trajectory; it is a *render* of a hybrid state, and the Nudge has more degrees of freedom in how it does the rendering.

### 1.2 What carries over from the parent paper

The following structural elements transfer directly:

- **State-generator-nudge factorization.** $Y_t \sim P_\theta(\cdot \mid X_t; f)$, $X_{t+1} = \mathcal{N}_\eta(X_t, Y_t)$. The agentic version replaces the second equation with $X_{t+1} = \mathcal{N}_\eta(X_t, Y_t, E_{t+1})$, allowing the Nudge to read from external state.
- **Three-way endpoint decomposition.** Raw switching (final-turn disagreement with paired control), net switching (raw minus paired-control floor), persistent escape (kicked AND in same post-perturbation cluster at terminal turn). Each lifts cleanly with revised cluster definitions.
- **Dose-response and ED50.** Tokens of injected perturbation $\to$ probability of redirect. Same logistic / mixed-effects machinery; same family-cluster bootstrap; same Wilson 95% intervals.
- **Memory-policy comparison.** The parent paper's bounded-vs-full-history finding is the special case of comparing $\mathcal{N}_\text{append}^L$ at different $L$; here we compare across qualitatively different $\mathcal{N}_\eta$.
- **Stochastic-floor subtraction.** Two paired control runs already disagree from sampling alone; raw switching minus this floor is net switching. In the agentic setting the floor is **per-task**, not global, because tasks differ in how many valid solution paths exist.
- **Append/replace/dialog as a partition of memory architectures.** The parent paper's $\{O_1, O_2, O_3, D_1, D_2\}$ partition lifts to $\{A_1, A_2, A_3, A_4, D_1, D_2\}$ here, with one extra regime ($A_4$, state-replace) that has no clean text-loop analog.

### 1.3 What is genuinely new

Three things change qualitatively. None of them break the framework; all of them require care.

1. **Hybrid state.** $X_t$ is now constructed by the Nudge from both the prior text $X_{t-1}$ and the external state $E_t = (W_t, G_t, b_t)$. The agent never sees $E_t$ directly. The Nudge decides what slice of $E_t$ enters $X_{t+1}$. This means the perturbation can be injected into $X_t$ (as a redirect message), into $E_t$ (as a stale file or fake test failure), or both, and the Nudge filters them differently.
2. **Discrete, parameterized actions.** $Y_t$ contains tool calls $A_t = [(a_t^{(i),\text{type}}, a_t^{(i),\text{params}})]$. The action space is discrete and parameterized, Read this file, Bash this command. Treating the action sequence as a Euclidean trajectory in embedding space is a category mistake; the action channel needs sequence-aware methods (Markov / HMM / sequence-edit-distance / process-mining transition graphs). Tool *parameters* matter (Read README differs strategically from Read failing\_test) and need typed abstraction (file role, command class, edit type) rather than literal-string explosion.
3. **Goal-directedness.** The agent is solving a task. "Convergence" no longer means "the trajectory settled into a basin"; it means "the agent emitted a terminal turn." Attractors in the agentic setting are *strategy basins* (terminal success, edit-test-debug loop, planning-without-editing, premature done) more than *embedding basins*. Persistent escape needs a corresponding redefinition: a redirect "works" if it durably reroutes the agent's *strategy*, observable through tool-trace clusters, patch-distance basins, and task-success deltas, not necessarily through conversation-tail embedding clusters.

These three differences imply that the *measurement layer* must be redesigned even though the *experimental logic* of the parent paper survives intact. Embedding-space PCA-and-K-means on conversation tails is now a *secondary diagnostic*, not the primary analysis. Primary analyses live on tool-call sequences, patch-distance basins, and per-task task-success curves.

### 1.4 Originality at a glance

> Prior work on agentic coding evaluates *capability* (SWE-bench, AgentBench) or *robustness to attack* (AgentDojo, BIPIA, ToolEmu). This paper measures *memory-policy-conditioned redirectability*: how much perturbation is needed to durably move an agentic coding loop, separated by Nudge variant (append / summarize-replace / todo-replace / state-replace / dialog / reflection-replace) and decomposed into three endpoint families (redirect-survival, success-degradation, redirect-compliance). The framework is the parent paper's recursive-loop machinery lifted to hybrid state; the headline contribution is the **selectivity profile** of each Nudge: what kinds of perturbation each memory architecture lets persist into the agent's behavior. The summarizer in auto-compacting agents is identified as a *learnable safety filter and a learnable attack surface*. Memory policy in agents is a first-class safety-relevant design choice rather than an implementation detail.

---

## 2. Related work

### 2.1 Coding-agent benchmarks

SWE-bench (Jimenez et al., 2024) and SWE-bench Lite are the standard task suite for evaluating LLM-driven coding agents on real GitHub issues with passing test suites. SWE-agent and Aider score well on Lite; Claude Code is the most widely used commercial harness. AgentBench, ToolBench, and τ-bench evaluate broader agent skills. None of these benchmarks treat the *Nudge* as a controlled variable. Our work treats the harness's context-update rule as the experimental factor, holding model and task fixed.

### 2.2 Agent scaffolds

ReAct (Yao et al., 2023) interleaves reasoning and tool calls; Reflexion (Shinn et al., 2023) feeds a generated self-reflection into the next attempt; Tree of Thoughts (Yao et al., 2023b) performs test-time search over generated reasoning; Self-Refine (Madaan et al., 2023) iterates a single output through self-generated feedback. These scaffolds map onto the Nudge taxonomy directly: ReAct is a flavor of $\mathcal{N}_\text{append}$ with structured tool-result framing, Reflexion is $\mathcal{N}_\text{reflect}$, and Tree of Thoughts is a multi-trajectory variant outside the scope of this paper. Our contribution is to study the partition itself rather than to add to it.

### 2.3 Indirect prompt injection and tool-output attacks

Indirect prompt injection benchmarks, Greshake et al. (2023), BIPIA (Yi et al., 2024), AgentDojo (Debenedetti et al., 2024), measure whether an agent follows malicious instructions hidden in tool output. They typically score *immediate compliance* at the next step. The parent paper introduced a *durable-redirect* endpoint, distinguishing transient compliance from persistent strategy change. The agentic lift makes the durable-redirect endpoint particularly relevant for IPI: a redirect that survives one summarization is more dangerous than one that compels a single noncompliant tool call. Our overwrite-vs-insert decomposition (parent paper §5.2) further isolates state-write mechanics from model behavior; the same decomposition applies here but in a richer state space.

### 2.4 Memory architectures for LLM agents

MemGPT (Packer et al., 2023) manages tiered context buffers via explicit paging. Letta and similar systems route between an in-context working memory and an external KV store. Retrieval-augmented generation is a structurally similar Nudge variant where $X_{t+1}$ pulls from a vector database keyed by relevance. All of these are concrete instantiations of one or another Nudge in the taxonomy here. We do not study them all; we study the canonical six.

### 2.5 Model collapse and recursive training

Shumailov et al. (2024) and Alemohammad et al. (2024) document training-time model collapse under recursive synthesis. Our setting is *inference-time* recursion of a frozen agent, identical to the parent paper's frame. The two settings share the question of whether recursive self-feeding produces convergence; we focus on intervention cost within a single inference loop, not parameter drift across training rounds.

### 2.6 What this paper adds, relative to the above

Existing work answers "how good are agents?" or "can agents be hijacked at the next step?" Our contribution is to ask: *given two agents that differ only in their context-update rule, how do their selectivity profiles for durable redirection differ?* The answer, we predict, is by an order of magnitude or more. The Nudge is treated as a controlled experimental variable, the dose-response framework from the parent paper is the primary analytical machinery, and the contribution is empirical and methodological, not a new agent, not a new benchmark, but a *measurement framework* for agent memory architectures.

---

## 3. Formal framework and hypotheses

### 3.1 The agentic-loop object

We study finite-horizon recursive systems of the form

$$
Y_t = (r_t, A_t, O_t) \sim P_\theta(\cdot \mid X_t; f)
$$
$$
A_t = [(a_t^{(i),\text{type}}, a_t^{(i),\text{params}})]_{i=1}^{n_t}, \qquad n_t \in \{0, 1, 2, \ldots\}
$$
$$
O_t, E_{t+1} = T(E_t, A_t), \qquad E_t = (W_t, G_t, b_t)
$$
$$
X_{t+1} = \mathcal{N}_\eta(X_t, Y_t, E_{t+1})
$$

where:

- $X_t$ is the *visible state*, the text passed to the model at turn $t$ (system + user + assistant + tool messages, in chat-API form);
- $Y_t$ is the model's per-turn output, comprising the assistant text $r_t$, an ordered list of tool calls $A_t$, and the ordered list of tool results $O_t$ produced by executing $A_t$ against $E_t$;
- $E_t = (W_t, G_t, b_t)$ is the *external state* (the working tree, git state, and build/test status) which evolves under the tool transition $T$;
- $P_\theta(\cdot \mid X_t; f)$ is the LLM-plus-tool-dispatch generator parameterized by content instruction $f$ (the system prompt and goal);
- $\mathcal{N}_\eta$ is the **Nudge Operator** parameterized by $\eta$, mapping the visible state, turn output, and post-tool external state to the next visible state.

The trajectory is the sequence $\{(X_t, Y_t, E_t)\}_{t=0}^{T}$ for some terminal turn $T$. The agent does **not** observe $E_t$ directly, only what $\mathcal{N}_\eta$ chooses to render. This is the key formal departure from the parent paper, where $X_t$ was the entire state of the loop.

### 3.2 Six Nudge Operators

Six concrete instantiations of $\mathcal{N}_\eta$ define the regimes studied here. Each is implementable in a few hundred lines of code. Each corresponds to a real coding-agent system in the wild.

**A1, append-full.** $\mathcal{N}_\text{append}^L$ parameterized by tail-clip length $L \in \mathbb{N} \cup \{\infty\}$:

$$
\mathcal{N}_\text{append}^L(X_t, Y_t, E_{t+1}) = \mathrm{tail}_L\bigl(X_t \,\Vert\, \mathrm{enc}(Y_t)\bigr)
$$

where $\mathrm{enc}(Y_t)$ serializes the structured turn output into the standard chat-API format (assistant message containing $r_t$ and `tool_use` blocks for each $a_t^{(i)}$, followed by `tool_result` messages carrying $o_t^{(i)}$). $\mathrm{tail}_L$ retains the last $L$ characters; $L = \infty$ recovers full-history. $L = 12{,}000$ recovers the parent paper's bounded-memory regime. This is the default of Claude Code and Aider.

**A2, summarize-replace.** $\mathcal{N}_\text{summary}^{\sigma, \tau}$ parameterized by a summarizer model $\sigma$ and a trigger threshold $\tau$:

$$
\mathcal{N}_\text{summary}^{\sigma, \tau}(X_t, Y_t, E_{t+1}) = \begin{cases}
X_t \,\Vert\, \mathrm{enc}(Y_t) & \text{if } |X_t \,\Vert\, \mathrm{enc}(Y_t)| \le \tau \\
\sigma(X_t \,\Vert\, \mathrm{enc}(Y_t),\, \text{Goal}) & \text{otherwise}
\end{cases}
$$

The summarizer $\sigma$ is itself a language-model invocation with its own system prompt; the Goal is preserved across summarizations as an anchor. This formalizes Claude Code's auto-compaction. Variants include *every-turn* replacement (no threshold; replace at every turn), *threshold-fired* replacement (compact only when context exceeds $\tau$), and *manual* replacement (user-triggered).

**A3, todo-replace.** $\mathcal{N}_\text{todo}$ replaces the visible state with a structured rendering of a maintained Todo list, a working-tree manifest, and the last tool result:

$$
\mathcal{N}_\text{todo}(X_t, Y_t, E_{t+1}) = \mathrm{render}_\text{todo}\bigl(\text{Goal},\, \mathrm{Todo}_{t+1},\, M(W_{t+1}),\, o_t^{(\text{last})}\bigr)
$$

where $\mathrm{Todo}_t$ is a maintained task list mutated only via a designated `TodoWrite` tool (one of the elements of $A_t$), $M(W)$ is a manifest of the working tree (file paths, sizes; not file contents), and $o_t^{(\text{last})}$ is the last tool result. The conversation history is dropped at every turn; the agent re-derives reasoning from the structured state. This is a stylized version of agent scaffolds that maintain explicit state objects.

**A4, state-replace (Markov).** $\mathcal{N}_\text{state}$ retains no conversation memory at all:

$$
\mathcal{N}_\text{state}(X_t, Y_t, E_{t+1}) = \mathrm{render}_\text{state}\bigl(\text{Goal},\, M(W_{t+1}),\, b_{t+1},\, o_t^{(\text{last})}\bigr)
$$

The agent operates as a Markov chain on the post-tool external state, conditioning only on the static goal, the working-tree manifest, the build/test status, and the last tool result. Strongest no-memory regime; closest to a pure-environment agent.

**D1, agentic dialog.** $\mathcal{N}_\text{dialog}$ alternates agent turns with simulated-user turns:

$$
\mathcal{N}_\text{dialog}(X_t, Y_t, E_{t+1}) = X_t \,\Vert\, \mathrm{enc}(Y_t) \,\Vert\, u_{t+1}, \qquad u_{t+1} \sim P_\text{user}(\cdot \mid X_t, Y_t, \text{Persona})
$$

where $P_\text{user}$ is a separate language-model instance with its own persona prompt that emits a new user message each turn. Direct analog of the parent paper's D1.

**D2, reflection-replace.** $\mathcal{N}_\text{reflect}$ replaces the agent's reasoning with a generated reflection:

$$
\mathcal{N}_\text{reflect}(X_t, Y_t, E_{t+1}) = X_t \,\Vert\, \mathrm{enc}(Y_t) \,\Vert\, \rho_t, \qquad \rho_t = \mathrm{reflect}(Y_t, b_{t+1}, o_t^{(\text{last})})
$$

A reflector model summarizes what was attempted and what should be done differently next; the agent sees that, not its own raw reasoning. Reflexion-style.

### 3.3 Three persistence endpoints

The parent paper's persistent-escape endpoint splits into three quantitatively distinct ED50 measures in the agentic setting. The key is that "the perturbation persisted" can mean three different things, and each Nudge has a different relationship between them.

Let $\pi$ denote a perturbation of dose $d$ (tokens of redirect text) injected at turn $t^* < T$. Let the trajectory under $\pi$ be $\{X_t^\pi, Y_t^\pi, E_t^\pi\}$ and under a paired control (same task, same seed, no $\pi$) be $\{X_t^c, Y_t^c, E_t^c\}$.

**Endpoint 1: redirect-survival.** Define $\mathrm{Surv}(\pi, T) = 1$ if the perturbation tokens (verbatim or above a cosine-similarity threshold to a paraphrase) appear in $X_T^\pi$, and 0 otherwise. The redirect-survival ED50 is the dose at which $\Pr[\mathrm{Surv}(\pi, T) = 1] = 0.5$. This is a property of the Nudge alone: *did the memory architecture preserve the perturbation into the terminal context?*

**Endpoint 2: success-degradation.** Define $\Delta\mathrm{Succ}(\pi) = \Pr[\text{task pass} \mid \pi] - \Pr[\text{task pass} \mid c]$. The success-degradation ED50 is the dose at which $\Delta\mathrm{Succ}(\pi)$ drops to $-0.5$. This is a property of the agent's *capability* under perturbation, not of the memory architecture.

**Endpoint 3: redirect-compliance.** Define $\mathrm{Comp}(\pi, T) = 1$ if the agent durably enacts the redirect, meaning either (a) the post-perturbation tool-trace cluster differs from the pre-perturbation tool-trace cluster *and* matches an "executes the redirect" cluster, or (b) the working tree at $T$ contains an observable trace of the redirect being addressed (a new file, a specific function, etc.). Redirect-compliance ED50 is the dose at which $\Pr[\mathrm{Comp}(\pi, T) = 1] = 0.5$. This is the strictest endpoint and the most safety-relevant.

These three ED50 values need not coincide. Under summarize-replace with a conservative summarizer, $\text{ED50}_\text{Surv}$ can be low (perturbation persists into the summary) while $\text{ED50}_\text{Comp}$ is much higher (agent reads the persisted text but doesn't enact it). Under todo-replace, $\text{ED50}_\text{Surv}$ collapses onto $\text{ED50}_\text{Comp}$ because the only persistence mechanism *is* commitment to the Todo list. The relationship between the three is the *signature* of the Nudge.

### 3.4 The selectivity profile

Define the **selectivity profile** of Nudge $\mathcal{N}_\eta$ as the function $\mathcal{S}_\eta: \mathcal{P} \to [0, 1]^3$ mapping perturbation classes $\pi \in \mathcal{P}$ to the triple of ED50 values $(\text{ED50}_\text{Surv}, \text{ED50}_\text{Succ}, \text{ED50}_\text{Comp})$ at the perturbation-class-level. The perturbation classes are coarse:

- **redirect** (mid-task user message asking for a different fix);
- **tool-error** (injected `permission denied` or `command not found` on the next tool call);
- **stale-state** (out-of-band file mutation between two turns);
- **misleading-test** (fake test failure injected into Bash output);
- **poison-doc** (adversarial content in a file the agent reads).

The selectivity profile is the headline finding of this paper. Two Nudges differ qualitatively if their profiles differ in *which* perturbation classes they let through, not just by how much. We predict (§4) that A1, A2, A3, A4 have measurably different profiles; that A2's profile depends on $\sigma$; and that the difference between A1 and A4 spans an order of magnitude in $\text{ED50}_\text{Comp}$ for the redirect class.

### 3.5 What is "kicked," "persisted," and "displaced" in the agentic setting

We retain the parent paper's three-way decomposition but instantiate each on the appropriate observable:

- **Kicked** at injection: the post-perturbation tool-trace cluster (or patch-state cluster) at turn $t^* + k$ differs from the pre-perturbation cluster at turn $t^* - 1$, for some short $k$ (typically $k=2$). This is the analog of "$C_+ \ne C_0$" in the parent paper.
- **Persisted (loose)**, *retained source-basin escape*: the terminal cluster differs from the pre-perturbation cluster. The agent *left* its starting strategy basin and remained outside through to the terminal turn.
- **Persisted (strict)**, *destination-coherent persistence*: the terminal cluster equals the post-perturbation cluster. The agent committed to a specific new strategy basin.

These are exactly the parent paper's two persistent-escape endpoints (parent §5.1.3), with "cluster" reinterpreted as a tool-trace or patch-state cluster rather than a context-tail embedding cluster. The corresponding lessons from the parent paper apply: the loose endpoint is a property of *durable departure from initial strategy*, the strict endpoint is a property of *commitment to a specific alternative strategy*, and the strict endpoint can be non-monotonic at high doses for finite-horizon-and-cluster-granularity reasons (parent §5.1.3) that we predict will reappear here.

### 3.6 Hybrid state and the perturbation surface

In the parent paper the perturbation surface was one-dimensional: inject text into $X_{t^*}$. In the agentic setting it is three-dimensional:

- **In-context perturbation:** inject a redirect message into $X_{t^*}$ via the user role. Direct analog of the parent paper.
- **External perturbation:** mutate $E_{t^*}$ between turns, modify a file out-of-band, alter a test, change an environment variable. The agent learns about this only via its tool calls.
- **Mediated perturbation:** alter $O_{t^*}$, the tool result for a tool the agent already called. (This is what indirect prompt injection does: the agent reads a file whose content has been corrupted; the perturbation enters $X_{t^*+1}$ via the tool-result mechanism.)

Each perturbation surface has its own selectivity-profile entry. State-replace ($\mathcal{N}_\text{state}$) is approximately immune to in-context perturbation (the agent never sees $X_{t^*}$ at $t^* + 1$) but maximally exposed to external perturbation; append ($\mathcal{N}_\text{append}^\infty$) is the inverse. Summarize-replace ($\mathcal{N}_\text{summary}^{\sigma, \tau}$) is partially exposed on all three surfaces, with the partitioning controlled by the summarizer prompt. The selectivity profile *across surfaces*, not just within a surface, is the full description of a Nudge's safety properties.

### 3.7 Hypotheses and falsification criteria

We pre-specify the following predictions; all are quantitative and falsifiable.

**H1 (memory policy matters).** The redirect-class $\text{ED50}_\text{Surv}$ values for $\{\mathcal{N}_\text{append}^\infty, \mathcal{N}_\text{summary}^{\sigma, \tau}, \mathcal{N}_\text{todo}, \mathcal{N}_\text{state}\}$ differ by at least a factor of three in pairwise comparison. *Falsified if all four ED50s lie within a factor of two of each other.*

**H2 (summarizer as filter).** $\text{ED50}_\text{Surv}$ under $\mathcal{N}_\text{summary}^{\sigma, \tau}$ depends on the summarizer prompt $\sigma$ in a measurable way: a "preserve user instructions" summarizer yields ED50 within a factor of two of $\mathcal{N}_\text{append}^\infty$, while a "compact aggressively" summarizer yields ED50 at least three times higher. *Falsified if both summarizer prompts produce ED50s within a factor of two of each other.*

**H3 (todo-replace bimodality).** Under $\mathcal{N}_\text{todo}$, the redirect-survival rate as a function of dose is bimodal: either ≥80% or ≤20%, with no smooth transition. *Falsified if the survival rate takes intermediate values (20-80%) at any dose with statistical confidence.*

**H4 (state-replace text-immunity).** Under $\mathcal{N}_\text{state}$, $\text{ED50}_\text{Surv}$ for the redirect class is undefined (i.e., the maximum-tested dose yields a survival rate below 10%). *Falsified if any tested dose yields a survival rate above 25%.*

**H5 (decoupled endpoints under summarize-replace).** Under $\mathcal{N}_\text{summary}$, the difference $\bigl|\text{ED50}_\text{Surv} - \text{ED50}_\text{Comp}\bigr|$ exceeds 50% of $\text{ED50}_\text{Surv}$. The summarizer keeps the perturbation visible without the agent enacting it. *Falsified if the two ED50s lie within 30% of each other under $\mathcal{N}_\text{summary}$.*

**H6 (collapsed endpoints under todo-replace).** Under $\mathcal{N}_\text{todo}$, $\text{ED50}_\text{Surv}$ and $\text{ED50}_\text{Comp}$ coincide within 20%. *Falsified if they differ by more than 40%.*

**H7 (selectivity-profile invariance across model scale).** The qualitative ordering of the four Nudges' redirect-class $\text{ED50}_\text{Surv}$ values is preserved across Claude Haiku 4.5, Sonnet 4.6, and Opus 4.7. The absolute ED50 may shift; the ordering does not. *Falsified if any one model's ordering differs.*

These seven hypotheses define the quantitative claims the paper will defend or relinquish based on experimental evidence. Each is falsifiable at the standard two-sided 95% bootstrap confidence level used throughout the parent paper.

### 3.8 Operational primary endpoints

Before listing the experimental design, we pre-specify five primary endpoints used for headline claims. All other quantities (tool-trace cluster diagnostics, patch-distance basin maps, conversation-tail embedding clusters) are diagnostic or visualization-support and are not load-bearing for any claim.

| endpoint | definition | measured at | threshold for "claim is supported" | defined in |
|---|---|---|---|---|
| **Nudge selectivity divergence** | maximum pairwise ratio of $\text{ED50}_\text{Surv}$ across $\{\mathcal{N}_\text{append}^\infty, \mathcal{N}_\text{summary}, \mathcal{N}_\text{todo}, \mathcal{N}_\text{state}\}$ for the redirect class | per (model × task-block × n=20 replicates per cell) | ratio ≥ 3.0; family-cluster bootstrap 95% CI strictly above 1.5 | §3.7 H1, §5.1 |
| **Summarizer-as-filter sensitivity** | $\text{ED50}_\text{Surv}^{\sigma_\text{aggressive}} / \text{ED50}_\text{Surv}^{\sigma_\text{conservative}}$ under $\mathcal{N}_\text{summary}^{\sigma, \tau}$ | as above; both summarizer prompts run on identical task × replicate set | ratio ≥ 3.0; CI strictly above 1.5 | §3.7 H2, §5.2 |
| **Todo-replace bimodality** | fraction of (dose, task) cells whose redirect-survival rate falls in [0.2, 0.8] | per dose × task cell; aggregated across replicates | ≤ 0.10 (≤10% of cells in the intermediate band) | §3.7 H3, §5.3 |
| **State-replace text-immunity** | maximum redirect-survival rate observed at any tested dose under $\mathcal{N}_\text{state}$ for redirect-class perturbations | per (model × task × dose) cell, n=20 | ≤ 0.10 | §3.7 H4, §5.4 |
| **Endpoint decoupling under summarize-replace** | $\bigl| \text{ED50}_\text{Surv} - \text{ED50}_\text{Comp} \bigr| / \text{ED50}_\text{Surv}$ under $\mathcal{N}_\text{summary}$ | as above | ≥ 0.50; CI strictly above 0.30 | §3.7 H5, §5.5 |

Each endpoint is paired with one or more of the seven hypotheses and has a falsification rule. Results that do not clear the rule are reported as diagnostic, exploratory, or in-flight rather than as supported claims.

---

## 4. Methods

### 4.1 Harness

The experiments run on a minimal Python harness (`src/experiments/agentic/`) that owns the recursive loop directly, so that the Nudge is a *pluggable component* rather than an opaque property of an off-the-shelf agent. This is the same architectural move the parent paper made for text loops: separate the generator from the context-update rule. Off-the-shelf coding agents (Claude Code, Aider, Cursor, OpenHands) each hard-code one Nudge and manage their own context internally; none expose it as a controlled variable, so none can serve as the system-under-test for a Nudge comparison.

The loop (`loop.py`) drives one trajectory: at each turn it sends the current visible state $X_t$ (an Anthropic Messages list) to the agent model, executes any tool calls $A_t$ against a sandboxed working tree, optionally injects a perturbation, and hands the running state to the Nudge to assemble $X_{t+1}$. The agent model is `claude-haiku-4-5`, called one turn at a time (`agent_client.py`) so the Nudge can rewrite the message list between turns.

**Tools.** Five sandboxed tools (`read_file`, `write_file`, `edit_file`, `run_bash`, `search`) plus a `todo_write` tool added only under the A3 todo-replace Nudge. Tool calls are abstracted to typed labels (file role, command class) for tool-trace analysis.

**Sandbox (`sandbox.py`).** Each trajectory runs in a fresh temp-directory working tree seeded from the task. A filesystem jail resolves every tool path against the sandbox root and rejects escapes (`..`, absolute paths, symlink traversal); a command jail runs `run_bash` in its own process group with a wall-clock timeout, output truncation, and a denylist of network/install commands. Network is not provisioned (denylist-level in this round; OS-level isolation is deferred). The sandbox design carries directly into the broader-impact treatment of the later destructive perturbation classes.

**Tasks (`tasks.py`).** This round uses five self-contained synthetic Python tasks with deterministic graders: `bugfix_offbyone`, `add_validation`, `refactor_extract`, `implement_stub`, `fix_failing_test`. Each ships a seed directory (visible to the agent) and a hidden oracle test held out of the visible tree and applied fresh at the terminal step, so the agent cannot satisfy the grader by editing the visible tests. We use synthetic tasks rather than the SWE-bench-Lite subset for this first round to obtain clean baselines and deterministic oracles; SWE-bench-Lite is the external-validity follow-up.

**Perturbation (`inject.py`).** This round exercises the `redirect` class on the `in-context` surface only: a plausible but different coding instruction (e.g. "rewrite this in a purely functional style"; "use a heap instead of sorting") injected at turn $t^*=3$ as a user interjection, scaled to a dose of $\{25, 50, 100, 200, 400\}$ tokens (with $0$ = control). The redirect rides as a text block on the tool-result message (the API-valid place a user interrupting mid-tool-loop lands) so it persists in append-mode history but is rebuilt away by the history-dropping Nudges.

**Endpoints (`endpoints.py`).** Redirect-survival (Endpoint 1) is computed by normalized verbatim match against the terminal visible state $X_T$, with an embedding-cosine fallback (`text-embedding-3-small`, paraphrase threshold $0.80$) to catch summarizer paraphrase. Redirect-compliance (Endpoint 3) is judged by `claude-sonnet-4-6` from the agent's final working tree plus its post-injection tool trace, on a sampled subset. Task success is the hidden oracle. Trajectories whose agent terminated before $t^*$ (so the redirect never fired) are excluded from survival/compliance denominators.

**Statistics.** Proportions are reported with Wilson 95% intervals; the across-Nudge survival difference carries a family-cluster bootstrap interval with the cluster set to the task (`analyze.py`).

### 4.2 Pre-registration status

The seven hypotheses of §3.7 and the five primary endpoints of §3.8 were specified before data collection. They were, however, designed after observing the parent paper's results, so confirmatory inference is bounded in the same way the parent paper bounds its own (Limitations, §7).

---

## 5. Results

### 5.1 Round 1: the AC1 minimal viable experiment

The first round (configuration `AC1`) tests the headline hypotheses H1 (memory policy conditions durable survival) and H4 (state-replace text-immunity) over the four memory Nudges $\{\mathcal{N}_\text{append}^\infty, \mathcal{N}_\text{summary}^{\sigma,\tau}, \mathcal{N}_\text{todo}, \mathcal{N}_\text{state}\}$, the redirect class, the in-context surface, the six-dose grid, the five synthetic tasks, and four seeds per cell, a $4\times6\times5\times4 = 480$-trajectory grid. Of the 480, 478 completed; two (both state-replace) were lost to a harness bug, since fixed (§5.5). No trajectory failed for rate-limit or API reasons. Of the dose-positive trajectories, all fired the redirect (none terminated before $t^*$), giving $n \in [99, 100]$ per Nudge for the survival endpoint.

### 5.2 Redirect-survival is memory-policy-determined

The redirect-survival rates split the four Nudges into two perfectly separated groups (Wilson 95% intervals):

| Nudge | redirect-survival | 95% CI | $n$ |
|---|---|---|---|
| A1 append-full | 100.0% | [96.3%, 100%] | 99/99 |
| A2 summarize-replace | 100.0% | [96.3%, 100%] | 99/99 |
| A3 todo-replace | 0.0% | [0%, 3.7%] | 0/100 |
| A4 state-replace | 0.0% | [0%, 3.7%] | 0/100 |

The memory-preserving vs memory-dropping survival difference is $+100$ percentage points, with a family-cluster (task) bootstrap 95% interval of $[+100\%, +100\%]$: the separation is complete, so the bootstrap shows no spread. **H1 is supported** (the difference interval lies far above the $+30$pp gate of §3.8). **H4 is supported**: the state-replace survival upper confidence bound, $3.7\%$, is below the $10\%$ immunity ceiling.

Critically, survival is *flat in dose within each Nudge*: append-full and summarize-replace survive at 100% at every dose from 25 to 400 tokens, and the two history-dropping Nudges evict the redirect at every dose. Redirect survival is therefore **memory-policy-determined, not dose-determined**; for this endpoint the ED50 is degenerate (undefined for A1/A2 and A4 in the sense of §3.7 H4), and the cleaner description is a step function of the Nudge. This is the expected behavior taken to its limit: append-mode literally retains the injected text and state-replace literally discards it, so this round principally *validates the measurement framework and confirms the mechanism* rather than discovering a graded dose-response. The graded structure lives in the endpoints that can decouple from survival, below.

### 5.3 Compliance tracks survival; success degrades on a step, not a ramp

Redirect-compliance (judged) tracks survival exactly: append-full and summarize-replace complied with the redirect in 100% of judged dose-positive runs (24/24 and 33/33), while todo-replace and state-replace complied in 0% (0/32 and 0/25). In this round the redirect that persists is also the redirect that is enacted; survival and compliance do **not** decouple, because, as §5.4 explains, the summarizer never actually fired, so there was no filter to keep text visible while suppressing its enactment.

Task success exposes the cost of a *persisting* redirect. For the memory-preserving Nudges, task-pass falls from 100% in control to roughly 55-60% the moment any non-zero dose is injected, then stays flat across the dose grid:

| Nudge | $d{=}0$ | 25 | 50 | 100 | 200 | 400 |
|---|---|---|---|---|---|---|
| A1 append-full | 100% | 60% | 50% | 55% | 60% | 58% |
| A2 summarize-replace | 100% | 60% | 60% | 58% | 60% | 60% |
| A3 todo-replace | 0% | 5% | 0% | 0% | 0% | 0% |
| A4 state-replace | 0% | 0% | 0% | 0% | 0% | 0% |

A small persisting redirect derails the original task in roughly 40% of runs, and additional redirect tokens do not derail it much further, the success-degradation is a step at the onset of a persisting redirect, not a dose ramp. The history-dropping Nudges sit near 0% task-pass throughout, *including control* (§5.4).

### 5.4 Two calibration findings that shape Round 2

Two features of Round 1 are not yet the interesting science, and both point directly at the next experiment.

**The summarizer never fired.** The summarize-replace threshold ($\tau = 24{,}000$ characters) was never reached on the short synthetic tasks, so A2 never compacted and behaved identically to append-full (hence its 100% survival and 100% compliance). The summarizer-as-filter hypotheses (H2, H5) require compaction to *occur* so that $\sigma$ can decide whether the redirect persists. Round 2 (`AC2`) forces this by dropping $\tau$ to 4{,}000 characters (reached within two to three steps) and contrasting a conservative summarizer ("preserve user instructions") against an aggressive one ("compress to goal + last action"), judging compliance on every dose-positive run to test the survival/compliance decoupling H5 predicts.

**The Markov regimes cannot solve the baseline.** Todo-replace and state-replace score near 0% task-pass even in control, because dropping the conversation history each turn removes the agent's memory of what it has already tried; the agent loops to the step cap. This is clean for the *survival* endpoint (eviction of the redirect is unambiguous regardless of task competence) but it means the success-degradation and compliance endpoints are uninformative for these two Nudges in this round (a floor effect, not a redirect effect). Restoring a competence floor for the history-dropping regimes (a richer rendered state, or a more capable agent model for those arms) is a Round-2 calibration item.

### 5.5 Harness notes

Two trajectories hung at the step where a timed-out `run_bash` left an orphaned `pytest` grandchild holding the output pipe, so the call blocked past its nominal timeout, a Windows-specific consequence of killing only the shell and not its descendants. `run_bash` now runs each command in its own process group and kills the entire tree on timeout. Separately, the first launch (twelve concurrent workers) saturated the model's input-token-per-minute limit; the retry path now keys on exception type and honors the server `retry-after` header, and concurrency is capped so that throughput self-limits to the rate ceiling. The reported AC1 numbers are from the corrected run, in which no trajectory failed for rate-limit reasons.

### 5.6 What Round 1 establishes

Round 1 establishes that the parent paper's recursive-loop machinery transfers intact to agentic coding loops: the state-generator-nudge factorization, the redirect/survival/compliance endpoint decomposition, per-task stochastic-floor controls, Wilson intervals, and family-cluster bootstrap all operate on tool-using trajectories with a real working tree. It confirms the strongest, most mechanical predictions (H1, H4) and, in doing so, validates the harness end-to-end. The hypotheses that carry the paper's novel claim, that the *summarizer* is a learnable filter with its own selectivity profile (H2, H5), and that the qualitative Nudge ordering is model-scale-invariant (H7), are the subject of the subsequent round.

### 5.7 Round 2: summarization launders the injection (AC2; H2, H5)

Round 2 (configuration `AC2`) forces the summarizer to fire by dropping its trigger threshold $\tau$ from 24{,}000 to 4{,}000 characters (reached within two to three steps on these tasks) and contrasts a **conservative** summarizer (system prompt: *preserve any explicit user instructions, the goal, what files changed, and the latest test status*) against an **aggressive** one (*compress to the goal and the single most recent action; omit everything else*). The reference arm is A1 append-full. The grid is $3 \times 6 \times 5 \times 4 = 360$ trajectories (360/360 completed, no rate-limit or API failures, all 300 dose-positive trajectories fired the redirect), and because the survival/compliance relationship is the whole point, compliance is judged on **every** dose-positive run rather than a sample.

**The headline result: redirect survival and redirect compliance decouple sharply under summarization.** With compaction firing, the redirect's literal text almost never survives into the terminal context, yet the agent enacts it most of the time:

| Nudge | redirect-survival (text in $X_T$) | redirect-compliance (agent enacts) | $\lvert\Delta\rvert$ |
|---|---|---|---|
| A1 append-full | 100% [96%, 100%] (100/100) | 100% [96%, 100%] (100/100) | 0pp |
| A2 summarize-replace, conservative | 1% [0%, 5%] (1/100) | 86% [78%, 91%] (86/100) | 85pp |
| A2 summarize-replace, aggressive | 0% [0%, 4%] (0/100) | 70% [60%, 78%] (70/100) | 70pp |

This is **H5 supported** at the level the endpoint measures: under summarize-replace the gap between surface-form survival and judged compliance is 85 percentage points (conservative) and 70 points (aggressive), far beyond the separation H5 anticipated. We are careful about what "survival" means here. The survival endpoint detects the redirect by normalized verbatim match or embedding cosine $\ge 0.80$ against sliding windows of $X_T$; it therefore measures *surface-form* presence, and a near-zero survival rate establishes only that **a naive string/embedding context detector reports the terminal context clean**, not that the instruction is semantically absent. A compressed summary that faithfully preserves the instruction in three words ("user wants a functional rewrite") can score below the cosine threshold against the full redirect, so semantic survival is plausibly higher than surface survival. §5.9 (AC3) re-measures survival at the surface, semantic, and provenance levels to bound this.

Two mechanisms could produce the observed surface-clean-but-compliant pattern, and AC2 does not distinguish them. Under **laundering**, the summarizer paraphrases the injected instruction into the working summary, and that transformed instruction causally drives the later behavior. Under **erasure**, the agent acts on the redirect at or shortly after the injection step (before the first compaction) and compaction merely deletes the now-spent verbatim text afterward, so the terminal context is clean for a purely temporal reason. The safety implications differ (a behavioral injection-detector defeats erasure but a context-text detector defeats neither), and only laundering supports the strong "the memory architecture carries the attack forward" reading. Distinguishing them requires forcing compaction *before* the agent can act and ablating the summary, which is exactly the AC3 design (§5.9). We report the AC2 decoupling as an established phenomenon and defer the causal label to AC3, which resolves it in favor of laundering, scoped to salient instructions.

**H2 (summarizer prompt as a filter) is supported on compliance, not on survival.** Both summarizers wash the redirect out of the literal text (survival 0-1%), so H2 *as originally stated* (a survival-rate ratio of $\ge 3$ between summarizer prompts) is not applicable: there is no surviving text to differentiate. But the summarizer prompt demonstrably shifts *enactment*: the conservative summarizer carries the redirect's intent forward into compliance 86% of the time versus the aggressive summarizer's 70% (a $+16$pp difference). The summarizer is thus exactly the learnable filter the framework predicted, but the variable it filters is the *behavioral* persistence of the redirect, which only the compliance endpoint sees, not its textual persistence.

**Compliance is graded in dose, the dose-response Round 1 lacked.** Unlike survival (flat in dose), compliance under summarization rises with the redirect's size:

| Nudge | $d{=}25$ | 50 | 100 | 200 | 400 |
|---|---|---|---|---|---|
| A2 conservative | 70% | 80% | 95% | 95% | 90% |
| A2 aggressive | 55% | 65% | 75% | 80% | 75% |

A larger redirect is more likely to be enacted even after being summarized away, and the conservative summarizer sits above the aggressive one at every dose. So the dose-response structure the framework expects does exist in agentic loops; it lives on the compliance endpoint under an active summarizer, precisely where the surviving-text endpoint is saturated at zero.

**Memory policy is a task-robustness dial.** Task success under the redirect orders cleanly by how much the memory policy suppresses the injection. Aggressive summarization, by washing the redirect out, best protects the original task; full-history append, by retaining it, is the most derailed; conservative summarization sits between:

| Nudge | $d{=}0$ | 25 | 50 | 100 | 200 | 400 |
|---|---|---|---|---|---|---|
| A1 append-full | 100% | 55% | 50% | 50% | 60% | 60% |
| A2 conservative | 100% | 80% | 75% | 65% | 55% | 70% |
| A2 aggressive | 100% | 80% | 85% | 75% | 70% | 85% |

The ordering is the defensive-abstraction-versus-attack-surface tension made quantitative: an aggressive summarizer is the most robust to an injected redirect *because* it forgets aggressively, the same mechanism that would also discard a legitimate mid-task correction. The memory policy a deployment chooses is therefore a position on a curve trading injection-robustness against fidelity to genuine user steering, and the durable-redirect endpoint is meaningful only relative to that choice.

### 5.8 What the two rounds establish together

Round 1 shows that whether an injected redirect's *surface text* survives is determined almost entirely by the memory policy and is near-deterministic at the extremes (append retains, state-replace discards). Round 2 shows that this textual measure is the wrong one for the safety question: under the summarize-replace policy that real agents actually use, a surface-form context detector finds nothing while the agent keeps obeying the injection, and the rate of obedience is graded in dose and tunable by the summarizer prompt. The contribution from these two rounds is therefore: **auto-compaction defeats surface-form context-presence injection detectors without defeating the injection's behavioral effect**, and the summarizer prompt is a learnable filter on that behavioral effect. The stronger, more novel reading, that the summary *causally carries the instruction forward* (laundering), and that this holds for genuinely untrusted (non-user) injection sources, is what AC3 (§5.9) establishes, scoped to salient instructions. The practical lesson stands regardless of mechanism: an indirect-prompt-injection evaluation that scores text-level presence in the post-hoc context will under-count the summarize-replace deployments that are most common, because compaction destroys the textual signal.

### 5.9 Round 3: isolating causal laundering (AC3)

AC3 converts the AC2 phenomenon from a decoupling into a *causal* claim and puts it on a genuinely adversarial footing, through four protocol changes designed to defeat the alternative explanations of §7.

**Forced pre-action compaction.** The agent runs a short prefix to orient; the working tree is then snapshotted, the redirect is injected, and compaction is forced *before the agent is allowed any tool call*. No redirect-consistent action can precede the summary, so any subsequent compliance must be mediated by the compacted context, removing the temporal-erasure confound.

**Off-disk poison-document surface.** The redirect is delivered as the *content of an untrusted file the agent reads* (the mediated surface of §3.6), with explicit provenance framing, rather than as a user turn. Critically, the redirect is never written to the working tree: after the snapshot, the only possible carrier of the instruction into the resumed run is the context itself, so the agent cannot re-encounter the redirect by re-reading a file.

**Summary ablation (the causal estimand).** From the *same* working-tree snapshot, the agent is resumed under four matched context variants, `append_raw` (full history, verbatim redirect), `summary_auto` (the real conservative-summarizer compaction), `summary_scrubbed` (the same summary with the redirect's semantics removed by a separate edit pass), and `summary_baseline` (a summary of a matched no-redirect prefix). The laundering effect is the contrast
$$\text{laundering} = \Pr[\text{comply}\mid \texttt{summary\_auto}] - \Pr[\text{comply}\mid \texttt{summary\_scrubbed}].$$

**AST-checkable compliance.** Each redirect is an objective, statically checkable code predicate (e.g. import `heapq` and never call `sorted`; no `for`/`while` loops; move a function into `helpers.py`; use `pathlib` not `os.path`; define a named function; add `__all__`; use a decorator). Compliance is decided by a static AST check on the final working tree, no LLM judge in the primary path, removing the single-judge weakness. The `summary_baseline` arm doubles as a no-redirect control bounding incidental conformity.

**Powered design.** We run fifteen redirects (three per task), each an AST predicate chosen to be non-incidental, meaning the agent does not satisfy it by default, so `summary_baseline` compliance is near zero and the contrast is interpretable. Seeds are split into a held-out screen set (two seeds) and an analysis set; the enactability and non-incidence screen is computed only on the screen seeds, so the conditioned estimand is not a forking-paths artifact of the analysis data. The grid runs on two agent models, Claude Haiku 4.5 and Claude Sonnet 4.6. The pre-specified primary estimand is the unconditioned `summary_auto` minus `summary_scrubbed` contrast on the analysis seeds, with a paired cluster bootstrap (cluster = the task-redirect pair) and a GEE clustered-logistic confirmatory test.

**Primary result.** Pooled across both models (90 analysis cells, 30 task-redirect clusters), redirect compliance by resume context (Wilson 95%) is `append_raw` 16% [9, 24], `summary_auto` 30% [22, 40], `summary_scrubbed` 3% [1, 9], `summary_baseline` 0% [0, 4]. The unconditioned laundering effect, `summary_auto` minus `summary_scrubbed`, is +27 percentage points with a cluster-bootstrap 95% CI of [+14, +40] and a GEE clustered-logistic odds ratio of 12.3 (p < 0.0001); the `summary_auto` minus `summary_baseline` contrast is +30pp [+16, +44]. Because the agent takes no action before the snapshot and the redirect is never on disk, the ordering in which `summary_auto` greatly exceeds `summary_scrubbed`, which is in turn near `summary_baseline`, cannot be temporal erasure or file re-reading: the compaction summary itself causally carries the injected instruction. This is laundering on a genuinely untrusted file-read channel, under an explicit policy that tells the agent file contents are untrusted data, not a user turn.

**Laundering can exceed the verbatim channel.** `summary_auto` (30%) is higher than `append_raw` (16%), and the contrast `append_raw` minus `summary_auto` is -14pp [-26, -4], excluding zero: the laundered instruction is obeyed more often than the same instruction shown verbatim in full history. The provenance audit below explains why. Under the untrusted-data policy the agent partially resists the verbatim instruction because it is marked as coming from an untrusted file, but the summarizer routinely drops that attribution, so the laundered instruction no longer looks untrusted and is followed at least as often.

**Provenance audit (laundering versus semantic mediation).** A separate judge pass over each `summary_auto` records whether the injected instruction is present and, if so, whether it is still attributed to the untrusted source. The instruction is present in 89% of auto-summaries (133/150); of those, the provenance is stripped, meaning the instruction is restated as a bare requirement with no source, in 58% (77/133). The summarizer does not merely carry the instruction, it carries it shorn of its untrusted origin most of the time, which is what separates this result from mere semantic mediation. As a counterfactual check, the scrub pass removes the instruction from 59% of scrubbed summaries (89/150); the imperfect 41% leak biases the `summary_auto` minus `summary_scrubbed` contrast downward, so +27pp is conservative.

**Cross-model invariance.** The effect holds in the same direction in both models, with each model's own CI excluding zero: Haiku 4.5 gives `summary_auto` 33% versus `summary_scrubbed` 2% (+32pp), Sonnet 4.6 gives 23% versus 7% (+17pp, CI [+7, +30]). The more capable model is somewhat more resistant (smaller effect, higher residual scrubbed compliance), but laundering is not a single-model artifact.

**Screened secondary.** Restricting to the task-redirect pairs that pass the held-out screen yields a larger effect, +50pp [+25, +75], but on few pairs (the strict two-seed screen passes only a handful), so we treat it as a robustness check rather than the headline. The unconditioned +27pp is the load-bearing estimate.

**Scope and remaining caveats.** Two models, synthetic Python tasks, fifteen AST-checkable redirects, conservative summarizer only. The scrub counterfactual is imperfect (59% clean), accounted for as a downward bias. The held-out screen is thin (two seeds). The summarizer, scrubber, and audit judge are Anthropic-family models, so correlated behavior cannot be fully excluded, though the AST-based compliance primary does not depend on a model judge. The natural next targets are a third model family and an aggressive-summarizer arm.

---

## 6. Discussion

The three rounds together support a concrete claim with direct safety relevance: **in an agentic coding loop the memory policy (not the wording or size of an injected instruction) governs whether the injection durably captures the agent, and the auto-summarization policy real agents use can causally *launder* a salient injection: the verbatim attack text disappears from the context (defeating text-presence detectors) while the summary carries the instruction forward, so the agent keeps obeying it.** The causal half of this claim is shown directly in AC3 and is scoped to *salient* instructions (§5.9).

In an append-mode agent (Round 1) an in-context redirect is retained and enacted near-deterministically, and even a short redirect derails the original task about 40% of the time once it persists. The natural defensive intuition ("compact or summarize the history so the injection falls out of the window") turns out to be wrong (Round 2): after compaction a surface-form/embedding detector finds the redirect's text only 0-1% of the time, yet the agent obeys it 70-86% of the time. A defender monitoring the agent's context for injected strings, or for embeddings close to a known attack, would see a clean context and wrongly conclude the injection had been neutralized. This yields an operational consequence that holds **regardless of mechanism**: injection detection applied to post-hoc context *text* is defeated by standard compaction, so detection must instead be applied to behavior (what the agent is doing).

Round 3 establishes *why* the context is clean, on the genuinely adversarial channel. With the agent forced to take no action before compaction and the injected instruction never written to disk, the summary-ablation ladder (pooled over two models: `summary_auto` 30% greatly exceeds `summary_scrubbed` 3%, which is near `summary_baseline` 0%; unconditioned effect +27pp, CI [+14, +40], p < 0.0001) shows that the compaction summary itself causally carries the instruction forward, and the laundered summary is obeyed even more often than the verbatim untrusted text (`append_raw` 16%). This is laundering, not the temporal erasure or file re-reading that AC2 alone could not exclude. The effect is *selective*: the summarizer preserves the salient strategy of an injected instruction (use a heap, use a decorator) and discards incidental specifics (name a function X, move it to a particular file). The summarizer is thus a first-class, learnable safety component with a *content profile*, not an implementation detail. The same conservative "preserve user instructions" setting that makes it faithfully carry a legitimate correction forward is what makes it faithfully carry a salient injection forward. Round 2's task-success ordering (aggressive summarizer most robust to the redirect, append most exposed, conservative between) makes the trade-off explicit: the memory policy is a position on a curve trading robustness-to-injection against fidelity-to-steering, and there is no setting that is simultaneously maximally faithful to the user and maximally resistant to a salient injection, because to the summarizer the two look alike.

Round 3 also corrects a construct-validity overstatement in Rounds 1-2. There the redirect arrived as a *user* turn, and the near-100% compliance was partly the authority of the user role rather than the injection itself; on AC3's untrusted file-read channel, verbatim compliance is only 16%. The injection's hold from untrusted content shown verbatim is far lower than the user-channel near-100% implies; the danger is that summarization strips the untrusted framing, so the laundered instruction is obeyed more often (30%) than the verbatim one, a caution we propagate to the headline.

For indirect-prompt-injection evaluation, the implication that already holds is that the durable-redirect endpoint is conditioned on the harness's memory policy, and that a benchmark scoring injection *presence* in the post-hoc context will systematically under-count exactly the summarize-replace deployments that are most common, because those deployments destroy the textual signal. A behavioral durable-compliance endpoint is the measurement that survives compaction.

## 7. Limitations

Beyond the pre-registration caveat (§4.2): Round 1 uses one model family, one (synthetic) task suite, one perturbation class on one surface, and a hosted model whose exact behavior is not frozen. The perfect survival separation is in part a property of the endpoint definition (verbatim/paraphrase presence in $X_T$) interacting with Nudges that retain or drop text by construction; the more discriminating endpoints (compliance under an active summarizer, success-degradation with a competence floor) are exactly the ones Round 1 could not yet exercise. Per-task stochastic floors are estimated from a small number of paired controls. The history-dropping Nudges' baseline incompetence bounds what can be concluded about their success-degradation.

The AC2 result carried five specific threats; AC3 (§5.9) addresses the first four by design, leaving residual statistical-power and generality caveats:

1. **Causal vs temporal, addressed.** AC3's forced pre-action compaction (no action before the summary) plus off-disk poison-doc delivery (the redirect never on the working tree) means the `summary_auto` $\gg$ `summary_scrubbed` $\approx$ `summary_baseline` ladder cannot be erasure or file re-reading; the summary causally carries the instruction, on two models (Haiku 4.5 and Sonnet 4.6) with the unconditioned effect's CI excluding zero in each. Residual: the effect is concentrated on salient instructions, and both models are from one vendor family.

2. **Construct validity, addressed.** AC3 delivers the redirect as untrusted file content with provenance framing, not a user turn; verbatim compliance there is 16% (vs the user-turn near-100%), so the headline is stated for the adversarial channel. Residual: a single mediated surface (file read); tool-result and other untrusted channels remain.

3. **Survival is measured at the surface only.** Normalized verbatim plus a single cosine threshold ($\ge 0.80$) against fixed windows undercounts a compressed summary that preserves the instruction semantically; the reported 0-1% survival supports only "a naive surface detector reports clean." AC3 sidesteps this for the *causal* claim by using behavioral (AST) compliance rather than survival, but the semantic/provenance survival re-scoring of AC2 (blinded K-way recovery and entailment) is still outstanding.

4. **Compliance, strengthened.** AC3's primary compliance is a static AST check on the final tree, not an LLM judge, removing same-family judge bias and trace leakage. Residual: AST predicates must be chosen to be non-incidental, the `with_retry` redirect shows a natural-naming confound (`summary_scrubbed` also high), so the predicate set needs auditing, and a multi-family-judge / human-agreement secondary remains to be added.

5. **Task-redirect confound, power, and clustering, largely addressed.** The powered AC3 uses three non-incidental AST redirects per task, six seeds, and two models, and reports the unconditioned `summary_auto` minus `summary_scrubbed` contrast (+27pp, CI [+14, +40]) as primary, with a paired cluster bootstrap and a GEE clustered logistic (cluster = task-redirect pair, the correct effective unit). The enactability screen is computed on held-out seeds, so it is not a forking-paths filter on the analysis data. Residual: the held-out screen is thin (two seeds), the scrub counterfactual is imperfect (59% clean, a downward bias on the effect), and the auxiliary summarizer, scrubber, and judge are Anthropic-family models.

## 8. Future work

Rounds beyond AC3: a third model family (an OpenAI or Gemini agent) plus Opus to complete the H7 model-scale ladder; an aggressive-summarizer arm to test whether a more compressive summarizer launders more or less; a human-agreement validation of the AST and audit-judge labels; a deeper held-out screen and a deterministic (non-LLM) scrub to tighten the counterfactual; the remaining perturbation classes (tool-error, stale-state, misleading-test) and surfaces to fill in the selectivity profile of §3.4; the deferred semantic/provenance survival re-scoring of AC2; a competence floor for the history-dropping regimes; graduation from synthetic tasks to a SWE-bench-Lite subset; and tighter coupling to existing indirect-prompt-injection benchmarks as an external endpoint.

## 9. Reproducibility

The harness, the four Nudge implementations, the synthetic task suite with hidden oracles, the AC1/AC2/AC3 configurations (including the AC3 snapshot/pre-action-compaction loop, the AST-checkable redirect library and static checker, and the summary scrub/baseline generators), the sandbox specification, the model identifiers, and the per-trajectory and per-cell traces and aggregation are released with the paper. Each reported number is regenerated by the aggregation entry point from the released records.

---

## 13. References

- Kaplanski, P. (2026). *Perturbation dose responses in recursive large-language-model loops.* arXiv:2605.02236. (the parent paper)
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., Narasimhan, K. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024. arXiv:2310.06770.
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., Cao, Y. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* arXiv:2210.03629.
- Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T. L., Cao, Y., Narasimhan, K. (2023). *Tree of Thoughts: Deliberate Problem Solving with Large Language Models.* arXiv:2305.10601.
- Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., Yao, S. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* arXiv:2303.11366.
- Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., Gonzalez, J. E. (2023). *MemGPT: Towards LLMs as Operating Systems.* arXiv:2310.08560.
- Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., Fritz, M. (2023). *Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.* arXiv:2302.12173.
- Yi, J., Xie, Y., Zhu, B., Kiciman, E., Sun, G., Xie, X., Wu, F. (2024). *Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models.* arXiv:2312.14197.
- Debenedetti, E., Zhang, J., Balunovic, M., Beurer-Kellner, L., Fischer, M., Tramèr, F. (2024). *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* arXiv:2406.13352.
- Shumailov, I., Shumaylov, Z., Zhao, Y., Papernot, N., Anderson, R., Gal, Y. (2024). *AI models collapse when trained on recursively generated data.* Nature 631(8022), 755-759.
- Alemohammad, S., Casco-Rodriguez, J., Luzi, L., Humayun, A. I., Babaei, H., LeJeune, D., Siahkoohi, A., Baraniuk, R. G. (2024). *Self-Consuming Generative Models Go MAD.* arXiv:2307.01850.
- Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* arXiv:2303.17651.
