## 3. Formal framework and hypotheses

This section defines the recursive-loop object studied in the paper, the perturbation estimands used to measure basin switching, and the operational criteria by which we call a regime attractor-like. Numerical ED50 estimates, pass/fail audits, and regime-specific measurements are results and are reported later. The only substantive structural claim retained here is the replace-vs-append distinction: replace mode admits a generation-budget access bound, whereas append mode motivates an injected-token accumulation conjecture.

### 3.1 State, generator, nudge

Every recursive loop studied here has two distinct moving parts. The **generator** is the model itself, which samples the next piece of text. The **nudge** is the memory policy that decides how that text is written back into the next prompt. Prior work often treats these as one object, but they play different roles: the generator determines what can be produced from a state, while the nudge determines what persists as state.

Let \(X_t \in \mathcal{C}\) denote the bounded visible context at step \(t\), where \(\mathcal{C}\) is the space of valid clipped contexts. In this paper, \(\mathcal{C}\) is instantiated as finite-length character strings produced by tail-clipping at 12,000 characters. Let \(f\) denote the content instruction and \(\eta\) the memory policy. The recurrence is

\[
Y_t \sim P_\theta(\cdot \mid X_t; f),
\qquad
X_{t+1} = \mathcal{N}_\eta(X_t, Y_t).
\]

Here \(P_\theta(\cdot \mid X_t; f)\) is the language-model generator under instruction \(f\), for example continuation, paraphrase, summarize-and-negate, or role-alternating dialog. The map \(\mathcal{N}_\eta : \mathcal{C} \times \mathcal{Y} \to \mathcal{C}\) is the nudge, or context-update operator. The pair \((f,\eta)\), not either component alone, defines the loop dynamics.

The canonical nudges used in the experiments are:

\[
\mathcal{N}_{\mathrm{append}}(X_t,Y_t)
=
\operatorname{clip}(X_t \Vert Y_t),
\]

\[
\mathcal{N}_{\mathrm{replace}}(X_t,Y_t)
=
\operatorname{clip}(Y_t),
\]

\[
\mathcal{N}_{\mathrm{dialog}}(X_t,Y_t)
=
\operatorname{clip}\!\left(X_t \Vert \operatorname{format\_turn}(r_t,Y_t)\right),
\]

where \(r_t\) is the role label assigned to the turn and alternates according to the dialog protocol.

| Formal nudge | Engineering analogue | Typical risk or behavior |
|---|---|---|
| Append: \(\operatorname{clip}(X_t \Vert Y_t)\) | Full transcript, rolling recent context, accumulated tool logs | Prior evidence remains as ballast; perturbations compete with accumulated state |
| Replace: \(\operatorname{clip}(Y_t)\) | Summarize-and-continue, scratchpad replacement, single-state whiteboard | Old state is discarded; whatever enters the replacement becomes privileged |
| Dialog: \(\operatorname{clip}(X_t \Vert \operatorname{format\_turn}(r_t,Y_t))\) | Role-structured chat state, multi-role agents, user/assistant/tool buffers | Recent role-local turns may dominate despite longer accumulated context |
| Hybrid pinned plus summary | Pinned issue, tests, policy, plus compressed older history | Robustness depends on which facts can be overwritten and which remain invariant |

In engineering terms, the nudge is the loop memory policy. It is therefore part of the system's robustness and security boundary, not merely an implementation detail. The hypotheses below use this factorization directly: changing the content instruction \(f\) can change the generator, while changing the nudge \(\eta\) can change which parts of the generated text become future state.

#### 3.1.1 Barrier height as a persistent-escape estimand

Let \(B_1,B_2 \subset \mathcal{C}\) be basin sets in the late-window basin partition defined operationally in the Methods. Let \(t_{\mathrm{inj}}\) be the injection step and let \(X_{t_{\mathrm{inj}}^-}\) denote the state immediately before injection. For an injected dose of \(\tau\) tokens, define the persistent-escape barrier from \(B_1\) to \(B_2\) as

\[
\mathrm{B}_{\mathrm{persist}}(B_1 \to B_2)
=
\inf\Bigl\{\tau:
\Pr\bigl[J_\tau(B_1\to B_2)=1,\ X_T\in B_2
\mid X_{t_{\mathrm{inj}}^-}\in B_1,\ \mathrm{inject}_\tau\bigr]
\ge \tfrac12
\Bigr\}.
\]

Here \(J_\tau(B_1\to B_2)\) is the operational injection-step jump indicator defined by the late-window basin partition. Without \(J_\tau\), the same formula defines a terminal raw-switching barrier, not a persistent-escape barrier.

The unit of \(\mathrm{B}_{\mathrm{persist}}\) is injected tokens. This unit is intentionally operational: it asks how much text must be inserted into the loop, under a declared injection protocol, for an injection-step basin jump that persists to the terminal measurement to occur with probability at least one half. Because the nudge determines how injected text is retained, overwritten, or role-labeled, this token-valued barrier is expected to vary with \(\eta\).

The definition separates two events that are often conflated. A trajectory may terminate in \(B_2\) without an injection-step jump, because it would have drifted there under sampling noise. Conversely, a trajectory may jump at injection and later return to its reference basin. Persistent escape requires both the injection-step jump and the terminal outcome.

#### 3.1.2 Operational endpoints for switching and dose response

A perturbed trajectory can finish in a different cluster than its reference trajectory for several reasons: the injection genuinely redirected it, stochastic sampling would have produced a different terminal cluster anyway, or the injection caused a transient jump that later recovered. The following endpoints separate these cases.

Let \(C_{\mathrm{ref}}\) denote the declared reference basin for a perturbed trajectory: in this paper, the pre-injection basin of that same trajectory. Let \(C_T^{(D)}\) be the terminal basin after injected dose \(D\). Let \(p_0=\Pr(C_T^{(0,1)}\neq C_T^{(0,2)})\) be the control-vs-control natural switching floor under the same sampling protocol.

Define

\[
S_{\mathrm{raw}}(D)
=
\Pr(C_T^{(D)}\neq C_{\mathrm{ref}}),
\]

\[
S_{\mathrm{net}}(D)
=
S_{\mathrm{raw}}(D)-p_0,
\]

\[
S_{\mathrm{persist}}(D)
=
\Pr(J_D=1,\ C_T^{(D)}\neq C_{\mathrm{ref}}).
\]

The corresponding ED50 endpoints are

\[
\mathrm{ED50}_{\mathrm{raw}}
=
\inf\{D:S_{\mathrm{raw}}(D)\ge 0.5\},
\]

\[
\mathrm{ED50}_{\mathrm{net}}
=
\inf\{D:S_{\mathrm{net}}(D)\ge 0.5\},
\]

\[
\mathrm{ED50}_{\mathrm{persist}}
=
\inf\{D:S_{\mathrm{persist}}(D)\ge 0.5\}.
\]

If the relevant set is empty over the tested dose range, the corresponding endpoint is not reached in that range.

These endpoints are different estimands. \(S_{\mathrm{raw}}\) measures terminal disagreement from the declared reference basin. It includes natural stochastic divergence. \(S_{\mathrm{net}}\) subtracts the control-vs-control floor \(p_0\), so it estimates excess terminal switching above natural drift, but it is not itself a probability. \(S_{\mathrm{persist}}\) measures the stricter event used by the persistent-escape barrier: a jump at injection followed by terminal non-return to the reference basin.

This distinction is central to interpreting perturbation experiments. A raw-switching ED50 can be small if the natural switching floor is large. A persistent-escape ED50 can be unreached even when raw switching is substantial, if most injection-step jumps recover before terminal measurement or if terminal disagreement is dominated by sampling drift. The Results report these endpoints separately.

#### 3.1.3 Operational criteria for attractor-like regimes

The term **attractor-like** is used operationally. It does not assert the existence of a smooth deterministic attractor. A regime earns the label only by passing prespecified diagnostics on a measured trajectory ensemble.

> **Definition. Operational attractor-like regime.** Fix a trajectory ensemble, an observable map, an embedding map, a late-window basin partition, and a declared null ensemble. A regime \(r\) is evaluated by four binary criteria:
> C1 basin predictability; C2 recurrence or dwell above null; C3 embedder-robust recurrence class; C4 re-entry, contraction, or absorbing collapse.
> A strong attractor passes 4/4. An attractor-like regime passes at least 3/4. A regime passing fewer than 3/4 is not an operational attractor under this definition. Missing measurements count as failure unless the criterion is structurally inapplicable and this inapplicability is declared before evaluation.

The thresholds are:

**C1. Basin predictability.** Cross-validated accuracy for predicting the late-window basin from the final pre-terminal state must satisfy

\[
A_r^{\mathrm{final}} \ge \tau_{\mathrm{acc}},
\qquad
\tau_{\mathrm{acc}}=0.70.
\]

The basin partition and predictor protocol are fixed in the Methods. This criterion tests whether late-window basin identity is legible from the measured state rather than being arbitrary cluster noise.

**C2. Recurrence or dwell above null.** Let \(R_r\) be recurrence and \(D_r\) be dwell for regime \(r\). Let the declared null ensemble provide \((\mu_R^{\mathrm{null}},\sigma_R^{\mathrm{null}})\) and \((\mu_D^{\mathrm{null}},\sigma_D^{\mathrm{null}})\). The regime passes if

\[
\max\left\{
\frac{R_r-\mu_R^{\mathrm{null}}}{\sigma_R^{\mathrm{null}}},
\frac{D_r-\mu_D^{\mathrm{null}}}{\sigma_D^{\mathrm{null}}}
\right\}
\ge 2
\quad
\text{and}
\quad
d\ge 0.5.
\]

When both time-shuffled and no-feedback nulls are available, the stronger null gate is used. For dialog runs, the no-feedback null is structurally unavailable; the time-shuffled null is required.

**C3. Embedder-robust recurrence class.** Recurrence is assigned to a coarse bin

\[
b_e(r)\in
\{\text{high}\ge 0.70,\ \text{low}\le 0.40,\ \text{mid otherwise}\}
\]

for each embedding map \(e\). The criterion passes if the recurrence bin agrees in at least two of three embedders: the canonical embedder plus two alternatives. This criterion tests survival of the regime class under measurement change. It does not require scalar invariance of all diagnostics.

**C4. Re-entry, contraction, or absorbing collapse.** The regime passes if at least one of the following holds:

\[
\lambda_{1,r}^{\mathrm{late}}\le 0.015
\]

for late-window contraction;

\[
\texttt{best\_period}=2
\quad\text{and}\quad
\texttt{period\_2\_score}>0
\]

for period-two re-entry;

\[
R_r\ge 0.90
\quad\text{and}\quad
SD_r\le 1.50
\]

for absorbing collapse; or exit-return exceeds the C2 null gate. These alternatives allow different geometric signatures to qualify while still requiring a measured return, contraction, or collapse property.

The criteria above are applied to each experimental regime in the Results. The framework itself does not assume that any regime passes; the pass/fail audit is an empirical outcome.

#### 3.1.4 Replace-mode access bound

Replace mode discards the previous context after each generation step. In this regime, the next state depends on the newly generated replacement rather than on an accumulated transcript. This makes the injected-token dose \(\tau\) distinct from the post-injection model-generation budget.

For \(m\) post-injection replace steps, define

\[
G_m
=
\sum_{s=t_{\mathrm{inj}}}^{t_{\mathrm{inj}}+m-1} |Y_s|,
\qquad
\bar G_m=\mathbb{E}G_m.
\]

The quantity \(G_m\) is not injected text. It is the number of tokens generated by the model after the injection.

**Proposition. Replace-mode access bound.** In replace mode, suppose every reachable non-target state has one-step probability at least \(q_0\) of generating a target-basin replacement, target entry persists to terminal measurement with probability at least \(r_0\), and expected generation length is at most \(\kappa\) per step. Then after \(m\) post-injection replace steps,

\[
\Pr(X_T\in B_2)\ge r_0[1-(1-q_0)^m],
\qquad
\mathbb{E}G_m\le \kappa m .
\]

This bounds post-injection generated tokens, not injected-token dose. Full lemma, corollaries, and proof in §11.3.

The proposition captures the structural distinction between replace and append memory. In replace mode, once the loop reaches a state from which target-basin replacement is accessible, repeated replacement attempts accumulate probability through generation steps. The relevant finite quantity in the proposition is \(\mathbb{E}G_m\), the expected post-injection generation budget. It is not \(\tau\), the length of the injected string.

Consequently, the proposition should not be read as an injected-token barrier bound. If the access assumptions hold only after a particular injected string of length \(\tau\), then the injection protocol may certify an injected-dose upper bound of at most that \(\tau\) under those conditions. The factor \(\kappa m\) certifies only the generated-token budget after injection. If comparable access holds without injected text, then replace-mode switching is better understood as endogenous reachability of the replacement dynamics rather than as evidence of a positive injected-token barrier.

#### 3.1.5 Append-mode accumulation conjecture

Append mode retains prior context:

\[
X_{t+1}
=
\operatorname{clip}(X_t \Vert Y_t),
\qquad
Y_t\sim P_\theta(\cdot\mid X_t;f).
\]

A perturbation injected into an append-mode loop therefore does not overwrite the current state in one step. Instead, it is incorporated into an already formed bounded context and must compete with incumbent basin evidence that remains visible until displaced by clipping. The injected text, subsequent model outputs, and pre-existing context all coexist inside the same clipped state.

This motivates an injected-token accumulation conjecture rather than a generation-budget theorem. Let \(B_1,B_2\subset\mathcal{C}\) be basin sets for an append-mode loop. There is no reason to expect a one-step overwrite bound analogous to replace mode. Instead, switching should depend on how much basin-relevant counter-context survives inside the effective context window.

**Conjecture. Append-mode accumulation barrier.** For append-mode loops, basin switching from \(B_1\) to \(B_2\) is governed by the accumulated share of semantically legible counter-context inside the clipped state. In particular, there exists a basin-dependent threshold such that subthreshold injections remain near the stochastic floor, while injections that supply sufficient basin-relevant counter-context produce a rising switching curve.

A testable response-curve formulation is as follows. Let \(a_\tau\) be the semantically weighted share of the clipped context occupied by basin-relevant injected text. Append-mode accumulation predicts a nondecreasing switching curve

\[
S_{B_1\to B_2}(\tau)
=
\Pr(X_T\in B_2\mid X_{t_{\mathrm{inj}}}\in B_1,\tau)
\approx
p_{\mathrm{floor}}+
(p_{\max}-p_{\mathrm{floor}})
F(a_\tau-\alpha^\star_{B_1\to B_2}),
\]

where \(F\) is increasing and the threshold \(\alpha^\star\) is lower for in-distribution counter-context than for out-of-distribution text.

Here \(p_{\mathrm{floor}}\) is the relevant stochastic floor, \(p_{\max}\) is the attainable upper switching level under the protocol, and \(\alpha^\star_{B_1\to B_2}\) is a basin-pair threshold in effective context share. The word "semantically" is important: two injections with the same token count can have different \(a_\tau\) if one is in-distribution counter-context for \(B_2\) and the other is irrelevant or out-of-distribution text. This makes the conjecture falsifiable. It predicts dose dependence for append-mode in-distribution perturbations, weaker or absent dose response for semantically irrelevant perturbations at the same token count, and a threshold that shifts when the perturbation family changes.

A geometric refinement is possible. Let \(V(x)=-\log\rho(x)\) be an empirical potential over the representation space, and let \(V^\star(B_1,B_2)\) denote the saddle height along a minimum-cost path between basins. One may hypothesize that injected-token barriers in append mode scale with this saddle height up to representation and perturbation-family factors. This geometric relation is not used as a theorem in the framework. It is a secondary hypothesis to be evaluated empirically.

All barrier quantities in this section are operational token counts unless explicitly stated otherwise. Token-valued barriers are tokenizer-dependent and model-specific. A model-normalized alternative would measure injected information in nats using per-token conditional log probabilities under \(P_\theta\). That requires log-probability capture during generation. The present framework therefore treats nat-valued barriers as a future measurement target rather than as reported quantities.

### 3.2 Observable maps and embedding

Attractor-like structure is not measured directly from raw recurrence definitions alone. We introduce observable maps that select text views of the trajectory, and embedding maps that lift those views into vector space. Let

\[
O_t=h(X_t,Y_t,\mathrm{metadata})
\]

be an observable string selected from the state, generation, and recorded metadata. Let

\[
z_t=\phi(O_t)\in\mathbb{R}^m
\]

be its vector representation. For the canonical embedding used in the main battery, \(m=1536\) for `text-embedding-3-small`. A trajectory therefore produces one or more embedded polylines \(\{z_t^{(O)}\}_{t=0}^{T-1}\), depending on the observable family.

Observable maps are post-hoc measurement functions; they do not feed back into the recurrence unless explicitly used as part of a nudge. Thus \(X_t\) is the dynamical state, \(Y_t\) is the sampled continuation, \(O_t=h(X_t,Y_t,\mathrm{metadata})\) is the text view selected for measurement, and \(z_t=\phi(O_t)\) is the vector representation used for clustering, recurrence, dwell, and basin-predictability metrics. The Methods section fixes the observable family, embedding normalization, clustering procedures, and null ensembles before applying the C1-C4 criteria.

This separation matters for interpretation. The loop dynamics are defined by \((P_\theta,f,\mathcal{N}_\eta)\). The observables and embeddings define the measurement apparatus. A claimed attractor-like regime must therefore survive not only within one projection, but also under the robustness checks in C3. Conversely, failure under one observable does not by itself imply absence of structure in the text dynamics; it implies that the declared measurement battery did not certify the operational definition.

### 3.3 Hypotheses

**H1.** At least one recursive-loop regime passes the operational attractor-like definition under the declared observable, embedding, basin partition, and null ensemble.

**H2.** The pass/fail pattern and attractor subtype depend on both content operator \(f\) and nudge \(\eta\); changing \(\eta\) while holding content approximately fixed changes the measured regime class.

**H3.** Perturbation sensitivity differs by nudge: append mode exhibits a dose-dependent in-distribution raw-switching curve above the stochastic floor; replace mode reaches high switching at the smallest tested dose or without dose; dialog lies between these extremes and depends on role/state structure.

**H4.** The qualitative regime labels and endpoint ordering observed in small-N exploration remain unchanged under the large-N battery within declared uncertainty.
