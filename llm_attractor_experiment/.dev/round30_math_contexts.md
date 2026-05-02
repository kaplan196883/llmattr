## D01 (line 323)

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

---

## D02 (line 333)

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

---

## D03 (line 339)

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

---

## D04 (line 345)

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

---

## D05 (line 366)

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

---

## D06 (line 390)

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

---

## D07 (line 396)

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

---

## D08 (line 402)

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

---

## D09 (line 410)

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

---

## D10 (line 416)

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

---

## D11 (line 422)

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

---

## D12 (line 446)

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

---

## D13 (line 456)

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

---

## D14 (line 472)

\]

When both time-shuffled and no-feedback nulls are available, the stronger null gate is used. For dialog runs, the no-feedback null is structurally unavailable; the time-shuffled null is required.

**C3. Embedder-robust recurrence class.** Recurrence is assigned to a coarse bin

\[
b_e(r)\in
\{\text{high}\ge 0.70,\ \text{low}\le 0.40,\ \text{mid otherwise}\}
\]

for each embedding map \(e\). The criterion passes if the recurrence bin agrees in at least two of three embedders: the canonical embedder plus two alternatives. This criterion tests survival of the regime class under measurement change. It does not require scalar invariance of all diagnostics.

**C4. Re-entry, contraction, or absorbing collapse.** The regime passes if at least one of the following holds:

---

## D15 (line 481)

\]

for each embedding map \(e\). The criterion passes if the recurrence bin agrees in at least two of three embedders: the canonical embedder plus two alternatives. This criterion tests survival of the regime class under measurement change. It does not require scalar invariance of all diagnostics.

**C4. Re-entry, contraction, or absorbing collapse.** The regime passes if at least one of the following holds:

\[
\lambda_{1,r}^{\mathrm{late}}\le 0.015
\]

for late-window contraction;

\[

---

## D16 (line 487)

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

---

## D17 (line 495)

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

---

## D18 (line 511)

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

---

## D19 (line 523)

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

---

## D20 (line 539)

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

---

## D21 (line 555)

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

---

## D22 (line 577)

All barrier quantities in this section are operational token counts unless explicitly stated otherwise. Token-valued barriers are tokenizer-dependent and model-specific. A model-normalized alternative would measure injected information in nats using per-token conditional log probabilities under \(P_\theta\). That requires log-probability capture during generation. The present framework therefore treats nat-valued barriers as a future measurement target rather than as reported quantities.

### 3.2 Observable maps and embedding

Attractor-like structure is not measured directly from raw recurrence definitions alone. We introduce observable maps that select text views of the trajectory, and embedding maps that lift those views into vector space. Let

\[
O_t=h(X_t,Y_t,\mathrm{metadata})
\]

be an observable string selected from the state, generation, and recorded metadata. Let

\[

---

## D23 (line 583)

\[
O_t=h(X_t,Y_t,\mathrm{metadata})
\]

be an observable string selected from the state, generation, and recorded metadata. Let

\[
z_t=\phi(O_t)\in\mathbb{R}^m
\]

be its vector representation. For the canonical embedding used in the main battery, \(m=1536\) for `text-embedding-3-small`. A trajectory therefore produces one or more embedded polylines \(\{z_t^{(O)}\}_{t=0}^{T-1}\), depending on the observable family.

Observable maps are post-hoc measurement functions; they do not feed back into the recurrence unless explicitly used as part of a nudge. Thus \(X_t\) is the dynamical state, \(Y_t\) is the sampled continuation, \(O_t=h(X_t,Y_t,\mathrm{metadata})\) is the text view selected for measurement, and \(z_t=\phi(O_t)\) is the vector representation used for clustering, recurrence, dwell, and basin-predictability metrics. The Methods section fixes the observable family, embedding normalization, clustering procedures, and null ensembles before applying the C1-C4 criteria.

---

## D24 (line 627)

All thresholds, pass rules, and current endpoint status are consolidated in §4.13.

### 4.1 The recurrence

We instantiate the formal recurrence from §3.1 with three context-update rules:

\[
\text{Append:}\quad X_{t+1}=\mathcal{N}_{\text{append}}(X_t,Y_t)=\operatorname{clip}(X_t\Vert Y_t)
\]

\[
\text{Replace:}\quad X_{t+1}=\mathcal{N}_{\text{replace}}(X_t,Y_t)=\operatorname{clip}(Y_t)
\]

---

## D25 (line 631)

We instantiate the formal recurrence from §3.1 with three context-update rules:

\[
\text{Append:}\quad X_{t+1}=\mathcal{N}_{\text{append}}(X_t,Y_t)=\operatorname{clip}(X_t\Vert Y_t)
\]

\[
\text{Replace:}\quad X_{t+1}=\mathcal{N}_{\text{replace}}(X_t,Y_t)=\operatorname{clip}(Y_t)
\]

\[
\text{Dialog:}\quad X_{t+1}=\mathcal{N}_{\text{dialog}}(X_t,Y_t)=X_t\Vert \operatorname{format\_turn}(r_t,Y_t)
\]

---

## D26 (line 635)

\]

\[
\text{Replace:}\quad X_{t+1}=\mathcal{N}_{\text{replace}}(X_t,Y_t)=\operatorname{clip}(Y_t)
\]

\[
\text{Dialog:}\quad X_{t+1}=\mathcal{N}_{\text{dialog}}(X_t,Y_t)=X_t\Vert \operatorname{format\_turn}(r_t,Y_t)
\]

where

\[

---

## D27 (line 641)

\[
\text{Dialog:}\quad X_{t+1}=\mathcal{N}_{\text{dialog}}(X_t,Y_t)=X_t\Vert \operatorname{format\_turn}(r_t,Y_t)
\]

where

\[
Y_t \sim P_\theta(\cdot \mid X_t; f)
\]

and \(P_\theta\) is the language-model distribution parameterized by \(\theta\), here `gpt-4o-mini`. The clipping operator \(\operatorname{clip}(\cdot)\) truncates context from the head, namely the oldest text, once the running string exceeds 12,000 characters, preserving the most recent state. The content operator \(f\) enters through the system prompt fed to \(P_\theta\), for example "Continue the text" for \(f=\text{continue}\) and "Paraphrase the following" for \(f=\text{paraphrase}\).

Append mode creates a growing memory trace until the context cap is reached. Replace mode overwrites the state with the latest output, making the loop maximally sensitive to the current sample. Dialog mode alternates formatted turns between two roles and retains the conversation history subject to the same context-management principles. These three update rules define the operator families used throughout the experiments.

---

## D28 (line 653)

Append mode creates a growing memory trace until the context cap is reached. Replace mode overwrites the state with the latest output, making the loop maximally sensitive to the current sample. Dialog mode alternates formatted turns between two roles and retains the conversation history subject to the same context-management principles. These three update rules define the operator families used throughout the experiments.

### 4.2 Sampling

Each experiment runs

\[
N_{\text{traj}}=N_{\text{families}}\times N_{\text{ICs}}\times N_{\text{runs}}
\]

trajectories. Publication-scale defaults differ by experiment family:

| experiment family | design | steps | point count |

---

## D29 (line 727)


#### Algorithm 1: paired perturbation evaluation

Input: seed or task \(x\), generator \(P_\theta\), context-update rule \(\mathcal{N}\), injection condition \(c\), injection step \(t_{\mathrm{inj}}\), terminal step \(T\), observable map \(O\), and equivalence rule \(C\). In this paper \(C\) is a K-means cluster in joint PCA-10 space, but the algorithm only requires a pre-specified equivalence rule.

1. Run two unperturbed controls:
   \[
   A=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{no injection})
   \]
   \[
   B=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{no injection})
   \]


---

## D30 (line 730)

Input: seed or task \(x\), generator \(P_\theta\), context-update rule \(\mathcal{N}\), injection condition \(c\), injection step \(t_{\mathrm{inj}}\), terminal step \(T\), observable map \(O\), and equivalence rule \(C\). In this paper \(C\) is a K-means cluster in joint PCA-10 space, but the algorithm only requires a pre-specified equivalence rule.

1. Run two unperturbed controls:
   \[
   A=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{no injection})
   \]
   \[
   B=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{no injection})
   \]

2. Estimate the stochastic-floor event:
   \[
   \operatorname{floor}=\left[C(O(A_T))\neq C(O(B_T))\right]

---

## D31 (line 735)

   \]
   \[
   B=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{no injection})
   \]

2. Estimate the stochastic-floor event:
   \[
   \operatorname{floor}=\left[C(O(A_T))\neq C(O(B_T))\right]
   \]

3. Run the matched treatment:
   \[
   Z=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{inject }c\text{ at }t_{\mathrm{inj}})

---

## D32 (line 740)

2. Estimate the stochastic-floor event:
   \[
   \operatorname{floor}=\left[C(O(A_T))\neq C(O(B_T))\right]
   \]

3. Run the matched treatment:
   \[
   Z=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{inject }c\text{ at }t_{\mathrm{inj}})
   \]

4. Define raw switching:
   \[
   \operatorname{raw}=\left[C(O(Z_T))\neq C(O(A_T))\right]

---

## D33 (line 745)

3. Run the matched treatment:
   \[
   Z=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{inject }c\text{ at }t_{\mathrm{inj}})
   \]

4. Define raw switching:
   \[
   \operatorname{raw}=\left[C(O(Z_T))\neq C(O(A_T))\right]
   \]

5. Define the injection-time jump:
   \[
   \operatorname{jump}=\left[C(O(Z_{t_{\mathrm{inj}}+1}))\neq C(O(Z_{t_{\mathrm{inj}}-1}))\right]

---

## D34 (line 750)

4. Define raw switching:
   \[
   \operatorname{raw}=\left[C(O(Z_T))\neq C(O(A_T))\right]
   \]

5. Define the injection-time jump:
   \[
   \operatorname{jump}=\left[C(O(Z_{t_{\mathrm{inj}}+1}))\neq C(O(Z_{t_{\mathrm{inj}}-1}))\right]
   \]

6. Define persistent escape:
   \[
   \operatorname{persist}=\operatorname{jump}\wedge

---

## D35 (line 755)

5. Define the injection-time jump:
   \[
   \operatorname{jump}=\left[C(O(Z_{t_{\mathrm{inj}}+1}))\neq C(O(Z_{t_{\mathrm{inj}}-1}))\right]
   \]

6. Define persistent escape:
   \[
   \operatorname{persist}=\operatorname{jump}\wedge
   \left[C(O(Z_T))=C(O(Z_{t_{\mathrm{inj}}+1}))\right]
   \]

7. Aggregate over seeds, tasks, and families:
   \[
   \operatorname{raw\_rate}=\mathbb{E}[\operatorname{raw}],\quad

---

## D36 (line 761)

   \[
   \operatorname{persist}=\operatorname{jump}\wedge
   \left[C(O(Z_T))=C(O(Z_{t_{\mathrm{inj}}+1}))\right]
   \]

7. Aggregate over seeds, tasks, and families:
   \[
   \operatorname{raw\_rate}=\mathbb{E}[\operatorname{raw}],\quad
   \operatorname{floor}=\mathbb{E}[\operatorname{floor}],\quad
   \operatorname{net\_rate}=\operatorname{raw\_rate}-\operatorname{floor}
   \]
   \[
   \operatorname{persistent\_escape\_rate}=\mathbb{E}[\operatorname{persist}]
   \]


---

## D37 (line 766)

7. Aggregate over seeds, tasks, and families:
   \[
   \operatorname{raw\_rate}=\mathbb{E}[\operatorname{raw}],\quad
   \operatorname{floor}=\mathbb{E}[\operatorname{floor}],\quad
   \operatorname{net\_rate}=\operatorname{raw\_rate}-\operatorname{floor}
   \]
   \[
   \operatorname{persistent\_escape\_rate}=\mathbb{E}[\operatorname{persist}]
   \]

This same endpoint decomposition applies to non-embedding observables in engineering settings, including final patch family, files touched, test pass/fail sets, tool-call sequences, plan categories, security-policy violations, or embeddings of full traces.

### 4.5 Representation spaces and metric battery

---

## D38 (line 788)

#### 4.5.1 Regime-structure diagnostics

**Definition.** Regime-structure diagnostics summarize the temporal organization of a single trajectory or a set of trajectories in PCA-10 cluster space.

Recurrence for trajectory points \(z_0,\ldots,z_{T-1}\) is

\[
\operatorname{recurrence}(\epsilon,\tau)=
\frac{\#\{(t,s):\lVert z_t-z_s\rVert_2<\epsilon\ \wedge\ |t-s|>\tau\}}
{T(T-1)/2}
\]

with \(\epsilon=0.15\) and \(\tau=3\). The lag exclusion suppresses trivially nearby adjacent steps.

Dwell is computed after K-means clustering with \(k=12\) in PCA-10. It is the run-length distribution within a cluster. Long dwell times indicate basin persistence; short dwell times indicate transience or rapid cycling.

---

## D39 (line 804)

A target region is defined as the K-means cluster containing the trajectory's final 30% of points. Basin score is the fraction of post-\(t^*\) points in that cluster, with \(t^*=0.7T\). Basin entry is the first step at which the trajectory's cluster matches its late-window target.

Late recurrence restricts the recurrence statistic to the second half of the trajectory. Exit-return asks whether a trajectory that has visited its target basin subsequently leaves and re-enters it. This separates tight basins from metastable basins.

Periodicity is measured by lag-distance autocorrelation. For lag \(k\),

\[
\operatorname{mean\_dist}(k)=
\mathbb{E}_t\left[\lVert z_t-z_{t+k}\rVert_{\cos}\right].
\]

The period-2 score is \(\operatorname{mean\_dist}(1)-\operatorname{mean\_dist}(2)\). Positive values indicate that lag-2 points are closer than lag-1 points. Analogous scores are computed for period 3, and the best period is the lag \(k\in[1,T/2]\) minimizing the mean distance.

Dispersion compares ensemble spread early and late in the trajectory. Initial dispersion is the mean pairwise distance over \(t\in[0,T/4]\). Final dispersion is the mean pairwise distance over \(t\in[3T/4,T]\). Dispersion growth is \((\operatorname{final}-\operatorname{initial})/\operatorname{initial}\). Global drift is the distance between the centroid at the terminal step and the centroid at the initial step. Drift monotonicity is the correlation between centroid distance and step.

---

## D40 (line 823)

#### 4.5.2 Ensemble-spread diagnostics

**Definition.** We compute a finite-time ensemble-spread spectrum from multiple runs sharing the same family and initial condition. We use the term finite-time Lyapunov-like exponent for an ensemble-spread growth rate, not for a Jacobian-derived exponent of a smooth map.

For each family-initial-condition cell with \(N\) runs, the embeddings at step \(t\) define a covariance matrix

\[
\Sigma_t=\frac{1}{N-1}\sum_i (z_i^t-\bar z^t)(z_i^t-\bar z^t)^\top .
\]

Let \(\mu_k(t)\) be the \(k\)-th eigenvalue of \(\Sigma_t\). The \(k\)-th finite-time ensemble-spread exponent over a window from \(t_{\mathrm{baseline}}\) to \(T-1\) is

\[

---

## D41 (line 829)

\[
\Sigma_t=\frac{1}{N-1}\sum_i (z_i^t-\bar z^t)(z_i^t-\bar z^t)^\top .
\]

Let \(\mu_k(t)\) be the \(k\)-th eigenvalue of \(\Sigma_t\). The \(k\)-th finite-time ensemble-spread exponent over a window from \(t_{\mathrm{baseline}}\) to \(T-1\) is

\[
\lambda_k=
\frac{1}{2(T-1-t_{\mathrm{baseline}})}
\log\left(\frac{\mu_k(T-1)}{\mu_k(t_{\mathrm{baseline}})}\right).
\]

The factor \(1/2\) converts variance growth to amplitude growth. We compute early and late windows. The early window captures transient divergence as runs move away from the seed. The late window captures on-attractor or post-transient behavior.

We also compute sharpness dimension and effective rank as secondary diagnostics. Sharpness dimension uses the ordered spectrum and the Tuci-style fractional form

---

## D42 (line 839)

\]

The factor \(1/2\) converts variance growth to amplitude growth. We compute early and late windows. The early window captures transient divergence as runs move away from the seed. The late window captures on-attractor or post-transient behavior.

We also compute sharpness dimension and effective rank as secondary diagnostics. Sharpness dimension uses the ordered spectrum and the Tuci-style fractional form

\[
j^*=\max\left\{i:\sum_{k\leq i}\lambda_k\geq0\right\}
\]

with \(j^*=0\) if \(\lambda_1<0\), and

\[

---

## D43 (line 845)

\[
j^*=\max\left\{i:\sum_{k\leq i}\lambda_k\geq0\right\}
\]

with \(j^*=0\) if \(\lambda_1<0\), and

\[
\operatorname{SD}=j^*+
\frac{\sum_{k\leq j^*}\lambda_k}{|\lambda_{j^*+1}|}.
\]

If the spectrum is everywhere negative, SD is 0. If the cumulative sum remains non-negative through the full spectrum, SD is \(d\). Effective rank counts exponents above \(-0.01\).

**Use in claims.** The late ensemble-spread spectrum contributes to the contraction component of the operational attractor score. A negative or shrinking late spread supports a contractive or absorbing interpretation. A positive early exponent combined with late contraction indicates transient divergence followed by settling. Sharpness dimension and effective rank are reported as secondary diagnostics, not as primary endpoints.

---

## D44 (line 866)

Two cross-validation schemes are reported. The first is stratified \(k\)-fold cross-validation after dropping singleton classes that cannot be split into train and test folds. The number of folds is adaptive: \(n_{\mathrm{splits}}=\min(5,\text{smallest class size})\). If fewer than two non-singleton classes remain, the cell is recorded as missing. The second is group-aware cross-validation with prompt family held out as the grouping variable. This GroupKFold analysis tests whether predictability generalizes across prompt families rather than exploiting family identity.

Audit columns record the number of dropped singleton classes and trajectories. Publication-scale runs usually reach 5 stratified folds. Reduced-scope sweeps and pilots can fall back to 2 to 4 folds.

**Use in claims.** Group-aware basin predictability is one of the five primary endpoints. To claim cross-family basin predictability, accuracy at step \(k=10\) must satisfy

\[
\operatorname{acc}_{\mathrm{group}}(k=10)\geq0.70.
\]

To claim that the original stratified estimate is leakage-free, the difference

\[

---

## D45 (line 872)

\[
\operatorname{acc}_{\mathrm{group}}(k=10)\geq0.70.
\]

To claim that the original stratified estimate is leakage-free, the difference

\[
\Delta=\operatorname{acc}_{\mathrm{stratified}}-\operatorname{acc}_{\mathrm{group}}
\]

must be below 0.10. Stratified accuracy is reported as a diagnostic, but it is not sufficient for the leakage-free endpoint.

**Rationale or limitation.** A high stratified accuracy can arise because prompt families occupy different regions of embedding space. Group-aware splitting is therefore the stricter test: the model must predict the late basin for held-out families. This endpoint is intentionally conservative. It can fail even when within-family predictability is high, because the claim is cross-family generalization.

---

## D46 (line 951)

Flow-field visualizations share a bin-and-aggregate kernel that converts a trajectory ensemble into a spatially resolved displacement field on a two-dimensional projection. For each trajectory group, points are sorted by step. Each adjacent pair contributes a start location and a displacement vector. The collection of starts and displacements is binned over the projection plane.

For each grid bin, the average displacement vector is computed from all transitions whose start point falls inside the bin. Empty bins are left undefined, so streamline integration does not pass through unsupported regions. This produces an empirical vector field \(v(x)=(U(x),V(x))\) that represents the average one-step projected motion observed in that region.

Density fields use a higher-resolution two-dimensional histogram followed by Gaussian smoothing. The smoothed density \(\hat\rho(x)\) is used as a background heatmap and, in perturbation analyses, as the basis for the effective potential

\[
V(x)=-\log(\hat\rho(x)+\epsilon).
\]

Streamlines are integral curves of the empirical vector field. Divergence is computed as

\[

---

## D47 (line 957)

\[
V(x)=-\log(\hat\rho(x)+\epsilon).
\]

Streamlines are integral curves of the empirical vector field. Divergence is computed as

\[
\nabla\cdot v(x)=\frac{\partial U}{\partial x}+\frac{\partial V}{\partial y}.
\]

Negative divergence indicates sink-like behavior, while positive divergence indicates source-like behavior. For recursive LLM loops, we expect weakly negative average divergence in contractive regimes, strong local minima at absorbing sinks, and saddle-like structure in oscillatory regimes. Implementation details and grid parameters are provided in Supplementary §11.8.

### 4.10 Perturbation visualization toolkit

---
