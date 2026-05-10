# Memory policy and persistent redirection in agentic coding loops

*Continuation of "Perturbation dose responses in recursive large-language-model loops" (Kaplanski, 2026; hereafter **the parent paper**). Theoretical part only; experimental sections will be added in subsequent rounds.*

---

## Abstract

The parent paper studied recursive language-model loops on free-form text, separating the model from the context-update rule (the "nudge"), and found that persistent redirection in append-mode loops is memory-policy-conditioned: the same generator, same perturbation, and same horizon produce qualitatively different durable-redirect rates depending on whether the loop appends, paraphrases-replaces, summarizes-and-replaces, or alternates roles. This paper lifts the same state-generator-nudge formalism to **agentic coding loops** — recursive systems in which a language model emits *tool calls* whose results are fed back into the next prompt, and where the loop's "state" extends beyond text to include a working tree, git history, and build/test status.

The lift is not trivial. The agent's per-turn output $Y_t = (r_t, A_t, O_t)$ now carries reasoning text $r_t$, a list of tool calls $A_t$, and tool results $O_t$ produced by an external transition $E_{t+1} = T(E_t, A_t)$ on a hybrid state $E_t = (W_t, G_t, b_t)$ that the model does not see directly. The Nudge Operator $\mathcal{N}_\eta(X_t, Y_t, E_{t+1}) \to X_{t+1}$ now decides not only how to update text but also *what to surface from the external state*. Six Nudge variants — append, summarize-replace, todo-replace, state-replace, dialog, reflection-replace — produce six qualitatively different memory architectures, each implementable in a few hundred lines of code and each corresponding to a real system in the wild.

The central theoretical claim is that **each Nudge defines a different selectivity profile for which kinds of perturbations durably redirect the agent**. Append-mode is selective for any perturbation that fits in the visible window. Summarize-replace is selective for perturbations the summarizer chooses to keep — the summarizer is a *learnable filter*, simultaneously a defensive abstraction and an attack surface. Todo-replace is selective for perturbations the planner commits to a task list. State-replace is selective only for perturbations that produce observable side effects on the working tree. The same dose-response and persistent-escape machinery developed in the parent paper applies under each Nudge, but with three distinct ED50 endpoints — redirect-survival, success-degradation, and redirect-compliance — that need not coincide. Predictions and falsification criteria are pre-specified in §4. The experimental battery (a minimal Python harness driving the Anthropic API + Claude Agent SDK, evaluated on SWE-bench-Lite-style coding tasks) is described in subsequent sections, to be added.

---

## Plain-language summary

### A quick glossary

- **Agentic coding loop.** A recursive system in which a language model is asked to fix a bug or add a feature, and is given tools — read a file, edit a file, run a shell command, search the codebase — that the system invokes on the model's behalf. The model emits a tool call; the system runs it; the result becomes part of the next prompt. Repeat until the model says it's done. Claude Code, Aider, OpenHands, and the leaked Claude Code source all implement variants of this.
- **State.** What the agent's loop carries from one turn to the next. In a text-only recursive loop (the parent paper) the state is just the running prompt. In an agentic loop the state is hybrid: the running prompt **plus** the current working tree, the git history, and the test-pass status — but the model only ever sees what the loop *renders* into the next prompt.
- **Nudge.** The rule that builds the next prompt from the current prompt + the model's last turn (assistant text + tool calls + tool results). Six rules are studied here:
  - *append* (full conversation history, like Claude Code's default),
  - *summarize-replace* (compact the history when it fills, like Claude Code's auto-compaction),
  - *todo-replace* (drop the history; render only the task list, the working tree, and the last result),
  - *state-replace* (drop everything except the goal and the current working-tree state — the agent runs Markov-style),
  - *dialog* (alternating turns with a simulated user),
  - *reflection-replace* (drop reasoning; keep a generated reflection on what was attempted).
- **Perturbation.** A mid-task user message that asks the agent to do something different — a redirect. We measure how many tokens of redirect are needed to durably move the agent.
- **Selectivity profile.** Each Nudge keeps some kinds of perturbations and drops others. Append keeps everything that fits. Summarize-replace keeps what the summarizer thinks is important. Todo-replace keeps what the planner committed to a list. State-replace keeps only what changed the working tree. The selectivity profile is the dose-response curve under one Nudge.

### Five expected numbers (predictions ahead of data)

These are pre-specified predictions, not findings. The experiments described in subsequent sections are designed to falsify them.

1. **Append-mode redirect-survival ED50 ≈ 50-200 tokens** under full-history. Bounded-memory append (12K tail-clip) plateaus below 50%, like the parent paper.
2. **Summarize-replace under conservative summarization will have *lower* ED50 than append** — summarizers reinforce explicit "user said" content. Under aggressive summarization, ED50 will be *higher* and possibly non-monotonic.
3. **Todo-replace will be bimodal**: redirects either commit to the Todo (very low ED50) or are ignored (effectively infinite ED50). No middle ground.
4. **State-replace ED50 is undefined for text-only redirects** — the agent never sees them. The same Nudge will have a *very low* ED50 for environmental perturbations (file mutation, fake test failure).
5. **Task-success degradation ED50 will diverge from redirect-survival ED50** under summarize-replace and append, but will collapse onto it under todo-replace. This decoupling is the signature of the Nudge's selectivity profile.

### What this paper is *not*

It is not a benchmark of how good Claude Code is at SWE-bench. It is not an evaluation of agent capability. It is the lift of a memory-policy-conditioned dose-response framework from text-only recursive loops onto agentic coding loops, treating the Nudge as a first-class design surface and asking *which kinds of perturbations each Nudge lets through*.

---

## 1. Introduction

### 1.1 Motivation

A recursive language-model loop's behavior depends not only on the model and the input but on the rule that updates the loop's state between turns. The parent paper made this rule — the **Nudge Operator** $\mathcal{N}_\eta$ — a first-class variable: it factorized recursive text generation into state $X_t$, generator $P_\theta$, and nudge $\mathcal{N}_\eta$, and showed that under the same generator and the same perturbation, *changing the nudge changes whether the loop is redirectable, by how much, and for how long*. The headline finding was that under append-mode with full history, the half-effect dose for durable redirection is on the order of a thousand tokens; under bounded memory it never reaches half-effect because the perturbation is clipped out within ten to fifteen post-injection turns; under replace-mode, "switching" is mostly state-write tautology; under dialog, basin structure depends on the role partition.

Practically all coding agents in active use are recursive loops in this sense. They emit tool calls whose results become future context. Their context-update rules are heterogeneous: some keep full history (Aider's default), some auto-compact (Claude Code), some operate from a maintained Todo list (some research scaffolds), some are nearly Markov-on-the-working-tree (constrained patch agents). The rule chosen has the same kind of structural consequence here as in the text-only setting — but the consequences are richer because the loop's state extends into the file system. A perturbation injected as a user message might be summarized into the next prompt, or might be paraphrased away, or might commit to a Todo entry, or might be lost the moment the conversation history is reset to the working tree. The selectivity profile of an agentic Nudge is the dose-response curve of *what the Nudge lets through*.

This paper develops the theoretical framework for studying that selectivity profile. It does not replace the parent paper's framework — it generalizes it. The state-generator-nudge factorization, the three-way split into raw / net / persistent endpoints, the dose-response formalism, and the persistent-escape definitions all carry over. What changes is that $X_t$ is no longer a free-floating text trajectory; it is a *render* of a hybrid state, and the Nudge has more degrees of freedom in how it does the rendering.

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

1. **Hybrid state.** $X_t$ is now constructed by the Nudge from both the prior text $X_{t-1}$ and the external state $E_t = (W_t, G_t, b_t)$. The agent never sees $E_t$ directly. The Nudge decides what slice of $E_t$ enters $X_{t+1}$. This means the perturbation can be injected into $X_t$ (as a redirect message), into $E_t$ (as a stale file or fake test failure), or both — and the Nudge filters them differently.
2. **Discrete, parameterized actions.** $Y_t$ contains tool calls $A_t = [(a_t^{(i),\text{type}}, a_t^{(i),\text{params}})]$. The action space is discrete and parameterized — Read this file, Bash this command. Treating the action sequence as a Euclidean trajectory in embedding space is a category mistake; the action channel needs sequence-aware methods (Markov / HMM / sequence-edit-distance / process-mining transition graphs). Tool *parameters* matter — Read README differs strategically from Read failing\_test — and need typed abstraction (file role, command class, edit type) rather than literal-string explosion.
3. **Goal-directedness.** The agent is solving a task. "Convergence" no longer means "the trajectory settled into a basin"; it means "the agent emitted a terminal turn." Attractors in the agentic setting are *strategy basins* (terminal success, edit-test-debug loop, planning-without-editing, premature done) more than *embedding basins*. Persistent escape needs a corresponding redefinition: a redirect "works" if it durably reroutes the agent's *strategy*, observable through tool-trace clusters, patch-distance basins, and task-success deltas — not necessarily through conversation-tail embedding clusters.

These three differences imply that the *measurement layer* must be redesigned even though the *experimental logic* of the parent paper survives intact. Embedding-space PCA-and-K-means on conversation tails is now a *secondary diagnostic*, not the primary analysis. Primary analyses live on tool-call sequences, patch-distance basins, and per-task task-success curves.

### 1.4 Originality at a glance

> Prior work on agentic coding evaluates *capability* (SWE-bench, AgentBench) or *robustness to attack* (AgentDojo, BIPIA, ToolEmu). This paper measures *memory-policy-conditioned redirectability*: how much perturbation is needed to durably move an agentic coding loop, separated by Nudge variant (append / summarize-replace / todo-replace / state-replace / dialog / reflection-replace) and decomposed into three endpoint families (redirect-survival, success-degradation, redirect-compliance). The framework is the parent paper's recursive-loop machinery lifted to hybrid state; the headline contribution is the **selectivity profile** of each Nudge — what kinds of perturbation each memory architecture lets persist into the agent's behavior. The summarizer in auto-compacting agents is identified as a *learnable safety filter and a learnable attack surface*. Memory policy in agents is a first-class safety-relevant design choice rather than an implementation detail.

---

## 2. Related work

### 2.1 Coding-agent benchmarks

SWE-bench (Jimenez et al., 2024) and SWE-bench Lite are the standard task suite for evaluating LLM-driven coding agents on real GitHub issues with passing test suites. SWE-agent and Aider score well on Lite; Claude Code is the most widely used commercial harness. AgentBench, ToolBench, and τ-bench evaluate broader agent skills. None of these benchmarks treat the *Nudge* as a controlled variable. Our work treats the harness's context-update rule as the experimental factor, holding model and task fixed.

### 2.2 Agent scaffolds

ReAct (Yao et al., 2023) interleaves reasoning and tool calls; Reflexion (Shinn et al., 2023) feeds a generated self-reflection into the next attempt; Tree of Thoughts (Yao et al., 2023b) performs test-time search over generated reasoning. These scaffolds map onto the Nudge taxonomy directly: ReAct is a flavor of $\mathcal{N}_\text{append}$ with structured tool-result framing, Reflexion is $\mathcal{N}_\text{reflect}$, and Tree of Thoughts is a multi-trajectory variant outside the scope of this paper. Our contribution is to study the partition itself rather than to add to it.

### 2.3 Indirect prompt injection and tool-output attacks

Indirect prompt injection benchmarks — Greshake et al. (2023), BIPIA (Yi et al., 2024), AgentDojo (Debenedetti et al., 2024) — measure whether an agent follows malicious instructions hidden in tool output. They typically score *immediate compliance* at the next step. The parent paper introduced a *durable-redirect* endpoint, distinguishing transient compliance from persistent strategy change. The agentic lift makes the durable-redirect endpoint particularly relevant for IPI: a redirect that survives one summarization is more dangerous than one that compels a single noncompliant tool call. Our overwrite-vs-insert decomposition (parent paper §5.2) further isolates state-write mechanics from model behavior; the same decomposition applies here but in a richer state space.

### 2.4 Memory architectures for LLM agents

MemGPT (Packer et al., 2023) manages tiered context buffers via explicit paging. Letta and similar systems route between an in-context working memory and an external KV store. Retrieval-augmented generation is a structurally similar Nudge variant where $X_{t+1}$ pulls from a vector database keyed by relevance. All of these are concrete instantiations of one or another Nudge in the taxonomy here. We do not study them all; we study the canonical six.

### 2.5 Model collapse and recursive training

Shumailov et al. (2024) and Alemohammad et al. (2024) document training-time model collapse under recursive synthesis. Our setting is *inference-time* recursion of a frozen agent, identical to the parent paper's frame. The two settings share the question of whether recursive self-feeding produces convergence; we focus on intervention cost within a single inference loop, not parameter drift across training rounds.

### 2.6 What this paper adds, relative to the above

Existing work answers "how good are agents?" or "can agents be hijacked at the next step?" Our contribution is to ask: *given two agents that differ only in their context-update rule, how do their selectivity profiles for durable redirection differ?* The answer, we predict, is by an order of magnitude or more. The Nudge is treated as a controlled experimental variable, the dose-response framework from the parent paper is the primary analytical machinery, and the contribution is empirical and methodological — not a new agent, not a new benchmark, but a *measurement framework* for agent memory architectures.

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

- $X_t$ is the *visible state* — the text passed to the model at turn $t$ (system + user + assistant + tool messages, in chat-API form);
- $Y_t$ is the model's per-turn output, comprising the assistant text $r_t$, an ordered list of tool calls $A_t$, and the ordered list of tool results $O_t$ produced by executing $A_t$ against $E_t$;
- $E_t = (W_t, G_t, b_t)$ is the *external state* — the working tree, git state, and build/test status — which evolves under the tool transition $T$;
- $P_\theta(\cdot \mid X_t; f)$ is the LLM-plus-tool-dispatch generator parameterized by content instruction $f$ (the system prompt and goal);
- $\mathcal{N}_\eta$ is the **Nudge Operator** parameterized by $\eta$, mapping the visible state, turn output, and post-tool external state to the next visible state.

The trajectory is the sequence $\{(X_t, Y_t, E_t)\}_{t=0}^{T}$ for some terminal turn $T$. The agent does **not** observe $E_t$ directly — only what $\mathcal{N}_\eta$ chooses to render. This is the key formal departure from the parent paper, where $X_t$ was the entire state of the loop.

### 3.2 Six Nudge Operators

Six concrete instantiations of $\mathcal{N}_\eta$ define the regimes studied here. Each is implementable in a few hundred lines of code. Each corresponds to a real coding-agent system in the wild.

**A1 — Append (full-history).** $\mathcal{N}_\text{append}^L$ parameterized by tail-clip length $L \in \mathbb{N} \cup \{\infty\}$:

$$
\mathcal{N}_\text{append}^L(X_t, Y_t, E_{t+1}) = \mathrm{tail}_L\bigl(X_t \,\Vert\, \mathrm{enc}(Y_t)\bigr)
$$

where $\mathrm{enc}(Y_t)$ serializes the structured turn output into the standard chat-API format (assistant message containing $r_t$ and `tool_use` blocks for each $a_t^{(i)}$, followed by `tool_result` messages carrying $o_t^{(i)}$). $\mathrm{tail}_L$ retains the last $L$ characters; $L = \infty$ recovers full-history. $L = 12{,}000$ recovers the parent paper's bounded-memory regime. This is the default of Claude Code and Aider.

**A2 — Summarize-replace.** $\mathcal{N}_\text{summary}^{\sigma, \tau}$ parameterized by a summarizer model $\sigma$ and a trigger threshold $\tau$:

$$
\mathcal{N}_\text{summary}^{\sigma, \tau}(X_t, Y_t, E_{t+1}) = \begin{cases}
X_t \,\Vert\, \mathrm{enc}(Y_t) & \text{if } |X_t \,\Vert\, \mathrm{enc}(Y_t)| \le \tau \\
\sigma(X_t \,\Vert\, \mathrm{enc}(Y_t),\, \text{Goal}) & \text{otherwise}
\end{cases}
$$

The summarizer $\sigma$ is itself a language-model invocation with its own system prompt; the Goal is preserved across summarizations as an anchor. This formalizes Claude Code's auto-compaction. Variants include *every-turn* replacement (no threshold; replace at every turn), *threshold-fired* replacement (compact only when context exceeds $\tau$), and *manual* replacement (user-triggered).

**A3 — Todo-replace.** $\mathcal{N}_\text{todo}$ replaces the visible state with a structured rendering of a maintained Todo list, a working-tree manifest, and the last tool result:

$$
\mathcal{N}_\text{todo}(X_t, Y_t, E_{t+1}) = \mathrm{render}_\text{todo}\bigl(\text{Goal},\, \mathrm{Todo}_{t+1},\, M(W_{t+1}),\, o_t^{(\text{last})}\bigr)
$$

where $\mathrm{Todo}_t$ is a maintained task list mutated only via a designated `TodoWrite` tool (one of the elements of $A_t$), $M(W)$ is a manifest of the working tree (file paths, sizes; not file contents), and $o_t^{(\text{last})}$ is the last tool result. The conversation history is dropped at every turn; the agent re-derives reasoning from the structured state. This is a stylized version of agent scaffolds that maintain explicit state objects.

**A4 — State-replace (Markov).** $\mathcal{N}_\text{state}$ retains no conversation memory at all:

$$
\mathcal{N}_\text{state}(X_t, Y_t, E_{t+1}) = \mathrm{render}_\text{state}\bigl(\text{Goal},\, M(W_{t+1}),\, b_{t+1},\, o_t^{(\text{last})}\bigr)
$$

The agent operates as a Markov chain on the post-tool external state, conditioning only on the static goal, the working-tree manifest, the build/test status, and the last tool result. Strongest no-memory regime; closest to a pure-environment agent.

**D1 — Agentic dialog.** $\mathcal{N}_\text{dialog}$ alternates agent turns with simulated-user turns:

$$
\mathcal{N}_\text{dialog}(X_t, Y_t, E_{t+1}) = X_t \,\Vert\, \mathrm{enc}(Y_t) \,\Vert\, u_{t+1}, \qquad u_{t+1} \sim P_\text{user}(\cdot \mid X_t, Y_t, \text{Persona})
$$

where $P_\text{user}$ is a separate language-model instance with its own persona prompt that emits a new user message each turn. Direct analog of the parent paper's D1.

**D2 — Reflection-replace.** $\mathcal{N}_\text{reflect}$ replaces the agent's reasoning with a generated reflection:

$$
\mathcal{N}_\text{reflect}(X_t, Y_t, E_{t+1}) = X_t \,\Vert\, \mathrm{enc}(Y_t) \,\Vert\, \rho_t, \qquad \rho_t = \mathrm{reflect}(Y_t, b_{t+1}, o_t^{(\text{last})})
$$

A reflector model summarizes what was attempted and what should be done differently next; the agent sees that, not its own raw reasoning. Reflexion-style.

### 3.3 Three persistence endpoints

The parent paper's persistent-escape endpoint splits into three quantitatively distinct ED50 measures in the agentic setting. The key is that "the perturbation persisted" can mean three different things, and each Nudge has a different relationship between them.

Let $\pi$ denote a perturbation of dose $d$ (tokens of redirect text) injected at turn $t^* < T$. Let the trajectory under $\pi$ be $\{X_t^\pi, Y_t^\pi, E_t^\pi\}$ and under a paired control (same task, same seed, no $\pi$) be $\{X_t^c, Y_t^c, E_t^c\}$.

**Endpoint 1: redirect-survival.** Define $\mathrm{Surv}(\pi, T) = 1$ if the perturbation tokens — verbatim or above a cosine-similarity threshold to a paraphrase — appear in $X_T^\pi$, and 0 otherwise. The redirect-survival ED50 is the dose at which $\Pr[\mathrm{Surv}(\pi, T) = 1] = 0.5$. This is a property of the Nudge alone: *did the memory architecture preserve the perturbation into the terminal context?*

**Endpoint 2: success-degradation.** Define $\Delta\mathrm{Succ}(\pi) = \Pr[\text{task pass} \mid \pi] - \Pr[\text{task pass} \mid c]$. The success-degradation ED50 is the dose at which $\Delta\mathrm{Succ}(\pi)$ drops to $-0.5$. This is a property of the agent's *capability* under perturbation, not of the memory architecture.

**Endpoint 3: redirect-compliance.** Define $\mathrm{Comp}(\pi, T) = 1$ if the agent durably enacts the redirect — meaning either (a) the post-perturbation tool-trace cluster differs from the pre-perturbation tool-trace cluster *and* matches an "executes the redirect" cluster, or (b) the working tree at $T$ contains an observable trace of the redirect being addressed (a new file, a specific function, etc.). Redirect-compliance ED50 is the dose at which $\Pr[\mathrm{Comp}(\pi, T) = 1] = 0.5$. This is the strictest endpoint and the most safety-relevant.

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
- **Persisted (loose)** — *retained source-basin escape*: the terminal cluster differs from the pre-perturbation cluster. The agent *left* its starting strategy basin and remained outside through to the terminal turn.
- **Persisted (strict)** — *destination-coherent persistence*: the terminal cluster equals the post-perturbation cluster. The agent committed to a specific new strategy basin.

These are exactly the parent paper's two persistent-escape endpoints (parent §5.1.3), with "cluster" reinterpreted as a tool-trace or patch-state cluster rather than a context-tail embedding cluster. The corresponding lessons from the parent paper apply: the loose endpoint is a property of *durable departure from initial strategy*, the strict endpoint is a property of *commitment to a specific alternative strategy*, and the strict endpoint can be non-monotonic at high doses for finite-horizon-and-cluster-granularity reasons (parent §5.1.3) that we predict will reappear here.

### 3.6 Hybrid state and the perturbation surface

In the parent paper the perturbation surface was one-dimensional: inject text into $X_{t^*}$. In the agentic setting it is three-dimensional:

- **In-context perturbation:** inject a redirect message into $X_{t^*}$ via the user role. Direct analog of the parent paper.
- **External perturbation:** mutate $E_{t^*}$ between turns — modify a file out-of-band, alter a test, change an environment variable. The agent learns about this only via its tool calls.
- **Mediated perturbation:** alter $O_{t^*}$ — the tool result for a tool the agent already called. (This is what indirect prompt injection does: the agent reads a file whose content has been corrupted; the perturbation enters $X_{t^*+1}$ via the tool-result mechanism.)

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

## 4. (placeholder for §4-§9: Methods, Results, Discussion, Limitations, Future Work, Reproducibility)

Subsequent sections will be added as the experimental battery completes:

- **§4 Methods.** The minimal Python harness driving the Anthropic API + Claude Agent SDK; tool dispatch and sandboxing; the SWE-bench-Lite-derived task suite (curated subset of ~30 tasks for the methodology paper, with the full 300-task run as a supplement); per-task baseline calibration; stochastic-floor estimation; perturbation injection via mid-task user messages, tool-error injection, stale-state mutation, misleading-test injection, and poison-doc injection; cluster definitions on tool-trace sequences and patch-distance basins; family-cluster bootstrap for ED50 confidence intervals.
- **§5 Results.** Per-Nudge dose-response curves under the redirect class (§5.1-§5.5); per-Nudge selectivity profile across perturbation classes (§5.6); cross-model invariance check (§5.7); patch-distance basin analysis under each Nudge (§5.8); tool-trace clusters and strategy-basin enumeration (§5.9); a long-horizon analog of the parent paper's frozen-canonical-basis time-evolution analysis if budget permits (§5.10).
- **§6 Discussion.** Implications for agent architecture (memory policy as safety design); implications for indirect prompt injection (durable-redirect endpoint as a complement to immediate-compliance benchmarks); summarization as a learnable filter and attack surface.
- **§7 Limitations.** External validity: one model family; one task suite; bounded perturbation classes; hosted-model reproducibility; per-task heterogeneity in stochastic floors; the post-hoc design status of all hypotheses (predictions are pre-specified ahead of data collection but were designed after observing the parent paper's results, so confirmatory inference is bounded).
- **§8 Future work.** Cross-vendor MVP (OpenAI, Google, Mistral, open-weight); broader perturbation taxonomy (structured exploits, multi-turn redirects, dialog-injected perturbations); tighter coupling to indirect prompt injection benchmarks; live-Claude-Code instrumentation as ground truth.
- **§9 Reproducibility.** Code, configurations, sandbox specs, model versions, and per-replicate traces released with the paper.

---

## 13. References (selected; full list with §13 of subsequent revisions)

- Kaplanski, P. (2026). *Perturbation dose responses in recursive large-language-model loops.* arXiv preprint. (the parent paper)
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., Narasimhan, K. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024.
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., Cao, Y. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* arXiv:2210.03629.
- Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T. L., Cao, Y., Narasimhan, K. (2023b). *Tree of Thoughts: Deliberate Problem Solving with Large Language Models.* arXiv:2305.10601.
- Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., Yao, S. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* arXiv:2303.11366.
- Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., Gonzalez, J. E. (2023). *MemGPT: Towards LLMs as Operating Systems.* arXiv:2310.08560.
- Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., Fritz, M. (2023). *Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.* arXiv:2302.12173.
- Yi, J., Xie, Y., Zhu, B., Kiciman, E., Sun, G., Xie, X., Wu, F. (2024). *Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models.* arXiv:2312.14197.
- Debenedetti, E., Zhang, J., Balunovic, M., Beurer-Kellner, L., Fischer, M., Tramèr, F. (2024). *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* arXiv:2406.13352.
- Shumailov, I., Shumaylov, Z., Zhao, Y., Papernot, N., Anderson, R., Gal, Y. (2024). *AI models collapse when trained on recursively generated data.* Nature.
- Alemohammad, S., Casco-Rodriguez, J., Luzi, L., Humayun, A. I., Babaei, H., LeJeune, D., Siahkoohi, A., Baraniuk, R. G. (2024). *Self-Consuming Generative Models Go MAD.* arXiv:2307.01850.
- Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* arXiv:2303.17651.
