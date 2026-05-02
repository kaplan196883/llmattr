## ED50_raw

**First-use line:** 29

**Match:** `\mathrm{ED50}_{\mathrm{raw}}`

**Context (700 chars before, 200 after):**

```

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

```

---

## ED50_net

**First-use line:** 417

**Match:** `\mathrm{ED50}_{\mathrm{net}}`

**Context (700 chars before, 200 after):**

```
nts separate these cases.

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

If the relevant set is empty over the tested dose range, the correspond
```

---

## ED50_persist

**First-use line:** 245

**Match:** `\mathrm{ED50}_{\mathrm{persist}}`

**Context (700 chars before, 200 after):**

```
un moves immediately after injection, but whether it stays moved after subsequent recursive updates.

**Claim 3: append-mode continuation has a finite raw dose response but no observed persistent-escape threshold in the tested range (§5.6).** In the dense adversarial in-distribution append-mode rerun, $\mathrm{ED50}_{\mathrm{raw}}$ estimates are 36, 41, and 52 tokens under pooled four-parameter logistic fitting, mixed-effects logistic modeling, and family-cluster bootstrap, respectively. Raw switching rises with dose but plateaus near 67%, while paired controls already diverge about 35% of the time. The largest observed net effect is therefore about +32 percentage points at 400 tokens, and $\mathrm{ED50}_{\mathrm{persist}}$ is not reached for any tested dose from 5 to 400 tokens. Out-of-distribution neutral and lorem perturbations remain close to a drift floor rather than matching the adversarial continuation response.
```

---

## S_raw

**First-use line:** 391

**Match:** `S_{\mathrm{raw}}`

**Context (700 chars before, 200 after):**

```
nse

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

The corresponding ED5
```

---

## S_net

**First-use line:** 397

**Match:** `S_{\mathrm{net}}`

**Context (700 chars before, 200 after):**

```
 its reference trajectory for several reasons: the injection genuinely redirected it, stochastic sampling would have produced a different terminal cluster anyway, or the injection caused a transient jump that later recovered. The following endpoints separate these cases.

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
\inf\{D:S_{\mat
```

---

## S_persist

**First-use line:** 403

**Match:** `S_{\mathrm{persist}}`

**Context (700 chars before, 200 after):**

```
ection genuinely redirected it, stochastic sampling would have produced a different terminal cluster anyway, or the injection caused a transient jump that later recovered. The following endpoints separate these cases.

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
```

---

## V*

**First-use line:** 569

**Match:** `V^\star`

**Context (700 chars before, 200 after):**

```
ar_{B_1\to B_2}\) is a basin-pair threshold in effective context share. The word "semantically" is important: two injections with the same token count can have different \(a_\tau\) if one is in-distribution counter-context for \(B_2\) and the other is irrelevant or out-of-distribution text. This makes the conjecture falsifiable. It predicts dose dependence for append-mode in-distribution perturbations, weaker or absent dose response for semantically irrelevant perturbations at the same token count, and a threshold that shifts when the perturbation family changes.

A geometric refinement is possible. Let \(V(x)=-\log\rho(x)\) be an empirical potential over the representation space, and let \(V^\star(B_1,B_2)\) denote the saddle height along a minimum-cost path between basins. One may hypothesize that injected-token barriers in append mode scale with this saddle height up to representation and pe
```

---

## J_tau

**First-use line:** 370

**Match:** `J_\tau`

**Context (700 chars before, 200 after):**

```
ses below use this factorization directly: changing the content instruction \(f\) can change the generator, while changing the nudge \(\eta\) can change which parts of the generated text become future state.

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

Here \(J_\tau(B_1\to B_2)\) is the operational injection-step jump indicator defin
```

---

## C_ref

**First-use line:** 386

**Match:** `C_{\mathrm{ref}}`

**Context (700 chars before, 200 after):**

```
jectory may terminate in \(B_2\) without an injection-step jump, because it would have drifted there under sampling noise. Conversely, a trajectory may jump at injection and later return to its reference basin. Persistent escape requires both the injection-step jump and the terminal outcome.

#### 3.1.2 Operational endpoints for switching and dose response

A perturbed trajectory can finish in a different cluster than its reference trajectory for several reasons: the injection genuinely redirected it, stochastic sampling would have produced a different terminal cluster anyway, or the injection caused a transient jump that later recovered. The following endpoints separate these cases.

Let \(C_{\mathrm{ref}}\) denote the declared reference basin for a perturbed trajectory: in this paper, the pre-injection basin of that same trajectory. Let \(C_T^{(D)}\) be the terminal basin after injected dose \(D\). Le
```

---

## C_T

**First-use line:** 386

**Match:** `C_T`

**Context (700 chars before, 200 after):**

```
ump at injection and later return to its reference basin. Persistent escape requires both the injection-step jump and the terminal outcome.

#### 3.1.2 Operational endpoints for switching and dose response

A perturbed trajectory can finish in a different cluster than its reference trajectory for several reasons: the injection genuinely redirected it, stochastic sampling would have produced a different terminal cluster anyway, or the injection caused a transient jump that later recovered. The following endpoints separate these cases.

Let \(C_{\mathrm{ref}}\) denote the declared reference basin for a perturbed trajectory: in this paper, the pre-injection basin of that same trajectory. Let \(C_T^{(D)}\) be the terminal basin after injected dose \(D\). Let \(p_0=\Pr(C_T^{(0,1)}\neq C_T^{(0,2)})\) be the control-vs-control natural switching floor under the same sampling protocol.

Define

\[
S
```

---

## B_persist

**First-use line:** 367

**Match:** `\mathrm{B}_{\mathrm{persist}}`

**Context (700 chars before, 200 after):**

```
and security boundary, not merely an implementation detail. The hypotheses below use this factorization directly: changing the content instruction \(f\) can change the generator, while changing the nudge \(\eta\) can change which parts of the generated text become future state.

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

Here \(J_\tau(B_1\to B_2)\) is the
```

---

## p_0

**First-use line:** 386

**Match:** `p_0`

**Context (700 chars before, 200 after):**

```
t escape requires both the injection-step jump and the terminal outcome.

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
S_
```

---

## C1

**First-use line:** 439

**Match:** `C1`

**Context (700 chars before, 200 after):**

```
bstantial, if most injection-step jumps recover before terminal measurement or if terminal disagreement is dominated by sampling drift. The Results report these endpoints separately.

#### 3.1.3 Operational criteria for attractor-like regimes

The term **attractor-like** is used operationally. It does not assert the existence of a smooth deterministic attractor. A regime earns the label only by passing prespecified diagnostics on a measured trajectory ensemble.

> **Definition. Operational attractor-like regime.** Fix a trajectory ensemble, an observable map, an embedding map, a late-window basin partition, and a declared null ensemble. A regime \(r\) is evaluated by four binary criteria:
> C1 basin predictability; C2 recurrence or dwell above null; C3 embedder-robust recurrence class; C4 re-entry, contraction, or absorbing collapse.
> A strong attractor passes 4/4. An attractor-like regim
```

---

## C2

**First-use line:** 439

**Match:** `C2`

**Context (700 chars before, 200 after):**

```
ion-step jumps recover before terminal measurement or if terminal disagreement is dominated by sampling drift. The Results report these endpoints separately.

#### 3.1.3 Operational criteria for attractor-like regimes

The term **attractor-like** is used operationally. It does not assert the existence of a smooth deterministic attractor. A regime earns the label only by passing prespecified diagnostics on a measured trajectory ensemble.

> **Definition. Operational attractor-like regime.** Fix a trajectory ensemble, an observable map, an embedding map, a late-window basin partition, and a declared null ensemble. A regime \(r\) is evaluated by four binary criteria:
> C1 basin predictability; C2 recurrence or dwell above null; C3 embedder-robust recurrence class; C4 re-entry, contraction, or absorbing collapse.
> A strong attractor passes 4/4. An attractor-like regime passes at least 3/4. A 
```

---

## C3

**First-use line:** 439

**Match:** `C3`

**Context (700 chars before, 200 after):**

```
nal measurement or if terminal disagreement is dominated by sampling drift. The Results report these endpoints separately.

#### 3.1.3 Operational criteria for attractor-like regimes

The term **attractor-like** is used operationally. It does not assert the existence of a smooth deterministic attractor. A regime earns the label only by passing prespecified diagnostics on a measured trajectory ensemble.

> **Definition. Operational attractor-like regime.** Fix a trajectory ensemble, an observable map, an embedding map, a late-window basin partition, and a declared null ensemble. A regime \(r\) is evaluated by four binary criteria:
> C1 basin predictability; C2 recurrence or dwell above null; C3 embedder-robust recurrence class; C4 re-entry, contraction, or absorbing collapse.
> A strong attractor passes 4/4. An attractor-like regime passes at least 3/4. A regime passing fewer than 3/4 is no
```

---

## C4

**First-use line:** 439

**Match:** `C4`

**Context (700 chars before, 200 after):**

```
eement is dominated by sampling drift. The Results report these endpoints separately.

#### 3.1.3 Operational criteria for attractor-like regimes

The term **attractor-like** is used operationally. It does not assert the existence of a smooth deterministic attractor. A regime earns the label only by passing prespecified diagnostics on a measured trajectory ensemble.

> **Definition. Operational attractor-like regime.** Fix a trajectory ensemble, an observable map, an embedding map, a late-window basin partition, and a declared null ensemble. A regime \(r\) is evaluated by four binary criteria:
> C1 basin predictability; C2 recurrence or dwell above null; C3 embedder-robust recurrence class; C4 re-entry, contraction, or absorbing collapse.
> A strong attractor passes 4/4. An attractor-like regime passes at least 3/4. A regime passing fewer than 3/4 is not an operational attractor under this
```

---

## C1-C4

**First-use line:** 589

**Match:** `C1-C4`

**Context (700 chars before, 200 after):**

```
edding-3-small`. A trajectory therefore produces one or more embedded polylines \(\{z_t^{(O)}\}_{t=0}^{T-1}\), depending on the observable family.

Observable maps are post-hoc measurement functions; they do not feed back into the recurrence unless explicitly used as part of a nudge. Thus \(X_t\) is the dynamical state, \(Y_t\) is the sampled continuation, \(O_t=h(X_t,Y_t,\mathrm{metadata})\) is the text view selected for measurement, and \(z_t=\phi(O_t)\) is the vector representation used for clustering, recurrence, dwell, and basin-predictability metrics. The Methods section fixes the observable family, embedding normalization, clustering procedures, and null ensembles before applying the C1-C4 criteria.

This separation matters for interpretation. The loop dynamics are defined by \((P_\theta,f,\mathcal{N}_\eta)\). The observables and embeddings define the measurement apparatus. A claimed a
```

---

## O1

**First-use line:** 618

**Match:** `O1`

**Context (700 chars before, 200 after):**

```
icient for a headline claim unless they enter one of the five endpoints defined operationally in §4.13.

The five primary endpoints are:

1. **Operational attractor score**, based on the C1-C4 attractor criteria: late-window basin persistence, recurrence or dwell above null, embedder robustness, and contraction, re-entry, or collapse.
2. **Group-aware basin predictability**, measured by predicting the late basin from early PCA-10 state while holding out prompt families.
3. **Perturbation switching signature**, measured by paired treatment-control final-cluster disagreement, interpreted alongside the paired control-control stochastic floor.
4. **Behavioral ED50**, the token dose at which the O1 adversarial perturbation reaches 50% raw switching, with uncertainty estimated by family-cluster bootstrap and model-based fits.
5. **Persistent escape**, the strict event in which a perturbation ind
```

---

## O2

**First-use line:** 661

**Match:** `O2`

**Context (700 chars before, 200 after):**

```
n two roles and retains the conversation history subject to the same context-management principles. These three update rules define the operator families used throughout the experiments.

### 4.2 Sampling

Each experiment runs

\[
N_{\text{traj}}=N_{\text{families}}\times N_{\text{ICs}}\times N_{\text{runs}}
\]

trajectories, where \(N_{\text{families}}\) is the number of distinct prompt families, \(N_{\text{ICs}}\) is the number of initial conditions per family, and \(N_{\text{runs}}\) is the number of independent runs per (family, IC) cell. Publication-scale defaults differ by experiment family:

| experiment family | design | steps | point count |
|---|---:|---:|---:|
| Operator runs O1, O2, O3 | 15 prompt families x 30 initial conditions x 3 runs = 1,350 trajectories per regime | 40 | 54,000 points per experiment |
| Dialog run D1 | 5 dialog-suitable families x 30 initial conditions x 
```

---

## O3

**First-use line:** 661

**Match:** `O3`

**Context (700 chars before, 200 after):**

```
o roles and retains the conversation history subject to the same context-management principles. These three update rules define the operator families used throughout the experiments.

### 4.2 Sampling

Each experiment runs

\[
N_{\text{traj}}=N_{\text{families}}\times N_{\text{ICs}}\times N_{\text{runs}}
\]

trajectories, where \(N_{\text{families}}\) is the number of distinct prompt families, \(N_{\text{ICs}}\) is the number of initial conditions per family, and \(N_{\text{runs}}\) is the number of independent runs per (family, IC) cell. Publication-scale defaults differ by experiment family:

| experiment family | design | steps | point count |
|---|---:|---:|---:|
| Operator runs O1, O2, O3 | 15 prompt families x 30 initial conditions x 3 runs = 1,350 trajectories per regime | 40 | 54,000 points per experiment |
| Dialog run D1 | 5 dialog-suitable families x 30 initial conditions x 3 ru
```

---

## D1

**First-use line:** 283

**Match:** `D1`

**Context (700 chars before, 200 after):**

```
, and the context-update nudge. Second, it treats perturbations as calibrated interventions rather than informal prompt changes, allowing barrier height to be operationalized as a dose-response quantity. Third, it treats dialog as a distinct update architecture, not merely as another prompt template, and tests whether role-structured state creates basin structure different from single-stream recursion.

Our labels are not a one-to-one replacement for the contractive/oscillatory/exploratory taxonomy. We retain contractive and oscillatory as comparable high-level behaviors, treat absorbing collapse as a distinct low-diversity endpoint observed under specific recursive operators, and introduce D1/D2 as dialog-specific regimes whose definition depends on perturbation response and state-update structure rather than dispersion alone.

Tacheny (2025) is the closest recent precedent for treating r
```

---

## D2

**First-use line:** 283

**Match:** `D2`

**Context (700 chars before, 200 after):**

```
nd the context-update nudge. Second, it treats perturbations as calibrated interventions rather than informal prompt changes, allowing barrier height to be operationalized as a dose-response quantity. Third, it treats dialog as a distinct update architecture, not merely as another prompt template, and tests whether role-structured state creates basin structure different from single-stream recursion.

Our labels are not a one-to-one replacement for the contractive/oscillatory/exploratory taxonomy. We retain contractive and oscillatory as comparable high-level behaviors, treat absorbing collapse as a distinct low-diversity endpoint observed under specific recursive operators, and introduce D1/D2 as dialog-specific regimes whose definition depends on perturbation response and state-update structure rather than dispersion alone.

Tacheny (2025) is the closest recent precedent for treating recu
```

---

## H1

**First-use line:** 595

**Match:** `H1`

**Context (700 chars before, 200 after):**

```
lity metrics. The Methods section fixes the observable family, embedding normalization, clustering procedures, and null ensembles before applying the C1-C4 criteria.

This separation matters for interpretation. The loop dynamics are defined by \((P_\theta,f,\mathcal{N}_\eta)\). The observables and embeddings define the measurement apparatus. A claimed attractor-like regime must therefore survive not only within one projection, but also under the robustness checks in C3. Conversely, failure under one observable does not by itself imply absence of structure in the text dynamics; it implies that the declared measurement battery did not certify the operational definition.

### 3.3 Hypotheses

**H1.** At least one recursive-loop regime passes the operational attractor-like definition under the declared observable, embedding, basin partition, and null ensemble.

**H2.** The pass/fail pattern and
```

---

## H2

**First-use line:** 597

**Match:** `H2`

**Context (700 chars before, 200 after):**

```
 separation matters for interpretation. The loop dynamics are defined by \((P_\theta,f,\mathcal{N}_\eta)\). The observables and embeddings define the measurement apparatus. A claimed attractor-like regime must therefore survive not only within one projection, but also under the robustness checks in C3. Conversely, failure under one observable does not by itself imply absence of structure in the text dynamics; it implies that the declared measurement battery did not certify the operational definition.

### 3.3 Hypotheses

**H1.** At least one recursive-loop regime passes the operational attractor-like definition under the declared observable, embedding, basin partition, and null ensemble.

**H2.** The pass/fail pattern and attractor subtype depend on both content operator \(f\) and nudge \(\eta\); changing \(\eta\) while holding content approximately fixed changes the measured regime class.
```

---

## H3

**First-use line:** 599

**Match:** `H3`

**Context (700 chars before, 200 after):**

```
ust therefore survive not only within one projection, but also under the robustness checks in C3. Conversely, failure under one observable does not by itself imply absence of structure in the text dynamics; it implies that the declared measurement battery did not certify the operational definition.

### 3.3 Hypotheses

**H1.** At least one recursive-loop regime passes the operational attractor-like definition under the declared observable, embedding, basin partition, and null ensemble.

**H2.** The pass/fail pattern and attractor subtype depend on both content operator \(f\) and nudge \(\eta\); changing \(\eta\) while holding content approximately fixed changes the measured regime class.

**H3.** Perturbation sensitivity differs by nudge: append mode exhibits a dose-dependent in-distribution raw-switching curve above the stochastic floor; replace mode reaches high switching at the smallest
```

---

## H4

**First-use line:** 601

**Match:** `H4`

**Context (700 chars before, 200 after):**

```
3 Hypotheses

**H1.** At least one recursive-loop regime passes the operational attractor-like definition under the declared observable, embedding, basin partition, and null ensemble.

**H2.** The pass/fail pattern and attractor subtype depend on both content operator \(f\) and nudge \(\eta\); changing \(\eta\) while holding content approximately fixed changes the measured regime class.

**H3.** Perturbation sensitivity differs by nudge: append mode exhibits a dose-dependent in-distribution raw-switching curve above the stochastic floor; replace mode reaches high switching at the smallest tested dose or without dose; dialog lies between these extremes and depends on role/state structure.

**H4.** The qualitative regime labels and endpoint ordering observed in small-N exploration remain unchanged under the large-N battery within declared uncertainty.

## 4. Methods

Before the per-component
```

---

## lambda_1

**First-use line:** 479

**Match:** `\lambda_{1,r}`

**Context (700 chars before, 200 after):**

```
ed and no-feedback nulls are available, the stronger null gate is used. For dialog runs, the no-feedback null is structurally unavailable; the time-shuffled null is required.

**C3. Embedder-robust recurrence class.** Recurrence is assigned to a coarse bin

\[
b_e(r)\in
\{\text{high}\ge 0.70,\ \text{low}\le 0.40,\ \text{mid otherwise}\}
\]

for each embedding map \(e\). The criterion passes if the recurrence bin agrees in at least two of three embedders: the canonical embedder plus two alternatives. This criterion tests survival of the regime class under measurement change. It does not require scalar invariance of all diagnostics.

**C4. Re-entry, contraction, or absorbing collapse.** Let \(\lambda_{1,r}^{\mathrm{late}}\) be the top finite-time ensemble-spread exponent for regime \(r\) computed in the late window (defined in §4.5.2), let \(R_r\) and \(SD_r\) denote regime-mean recurrence and sharpnes
```

---

## SD

**First-use line:** 846

**Match:** `SD`

**Context (700 chars before, 200 after):**

```
ow from \(t_{\mathrm{baseline}}\) to \(T-1\) is

\[
\lambda_k=
\frac{1}{2(T-1-t_{\mathrm{baseline}})}
\log\left(\frac{\mu_k(T-1)}{\mu_k(t_{\mathrm{baseline}})}\right).
\]

The factor \(1/2\) converts variance growth to amplitude growth. We compute early and late windows. The early window captures transient divergence as runs move away from the seed. The late window captures on-attractor or post-transient behavior.

We also compute sharpness dimension and effective rank as secondary diagnostics. Sharpness dimension uses the ordered spectrum and the Tuci-style fractional form

\[
j^*=\max\left\{i:\sum_{k\leq i}\lambda_k\geq0\right\}
\]

with \(j^*=0\) if \(\lambda_1<0\), and

\[
\operatorname{SD}=j^*+
\frac{\sum_{k\leq j^*}\lambda_k}{|\lambda_{j^*+1}|}.
\]

If the spectrum is everywhere negative, SD is 0. If the cumulative sum remains non-negative through the full spectrum, SD is \(d\). Effe
```

---

## 4PL

**First-use line:** 1057

**Match:** `4PL`

**Context (700 chars before, 200 after):**

```
, 0.717] | +0.308 | 0.140 |
| 400 | 0.670 | [0.602, 0.731] | +0.323 | 0.160 |

The control-control natural floor is 34.7% [31.0%, 38.6%] across $n=600$ ordered control-control pairs. Thus two trajectories with the same family and IC seed but different generation RNG end in different K-means clusters 35% of the time without any perturbation. The raw 50% crossing occurs between 20 and 50 tokens, but much of that apparent switching is baseline stochastic divergence. Under the stricter net endpoint, the curve does not reach +50 percentage points within the tested range.

Three independent ED50 estimates agree on the raw-switching scale:

| method | ED50 (tokens) | uncertainty |
|---|---:|---|
| 4PL pooled fit | 36 | point estimate |
| Mixed-effects logistic GLMM | 41 | point estimate, log10-dose slope |
| Family-cluster bootstrap median | 52 | 95% CI [8.5, 242] |

![Fig 2. **Dense O1 adversaria
```

---

## GLMM

**First-use line:** 1058

**Match:** `GLMM`

**Context (700 chars before, 200 after):**

```
323 | 0.160 |

The control-control natural floor is 34.7% [31.0%, 38.6%] across $n=600$ ordered control-control pairs. Thus two trajectories with the same family and IC seed but different generation RNG end in different K-means clusters 35% of the time without any perturbation. The raw 50% crossing occurs between 20 and 50 tokens, but much of that apparent switching is baseline stochastic divergence. Under the stricter net endpoint, the curve does not reach +50 percentage points within the tested range.

Three independent ED50 estimates agree on the raw-switching scale:

| method | ED50 (tokens) | uncertainty |
|---|---:|---|
| 4PL pooled fit | 36 | point estimate |
| Mixed-effects logistic GLMM | 41 | point estimate, log10-dose slope |
| Family-cluster bootstrap median | 52 | 95% CI [8.5, 242] |

![Fig 2. **Dense O1 adversarial ED50 fit.** O1 append-mode adversarial dose response from the d
```

---

## CV

**First-use line:** 1919

**Match:** `CV`

**Context (700 chars before, 200 after):**

```
ting whether
the endpoint has been re-validated under the revision's
leakage-aware / cluster-aware analyses.

**Sample sizes (frozen).** Operator regimes (O1, O2, O3): n =
15 prompt families × 30 ICs × 3 runs = 1,350 trajectories per
regime, 40 steps. Dialog regime D1: n = 5 dialog-suitable families
× 30 ICs × 3 runs = 450 trajectories per regime, 40 steps (see
§4.2 for the per-regime IC selection rule). Perturbation pilots
(O1/O2/O3/D1 + D2): reduced scope, n = 50 trajectories per
condition (5 fams × 5 ICs × 2 runs).

| regime | endpoint | value | 95% CI / uncertainty | source | status |
|---|---|---|---|---|---|
| O1 | basin predictability acc(k=10), stratified | **0.80** | n=1350, 5-fold CV | §5.3, `basin_pred.csv` | [!] **inflated by family leakage; group-aware = 0.73** |
| O1 | basin predictability acc(k=10), group-aware | **0.73** | family-cluster GroupKFold | §5.11 (this revision) |
```

---

## CI

**First-use line:** 1040

**Match:** `CI`

**Context (700 chars before, 200 after):**

```
y.
2. **Net switching:** raw switching minus the control-control stochastic-divergence floor.
3. **Persistent escape:** the trajectory visibly changes cluster at injection and remains in the post-injection cluster to the terminal step.

The dense rerun was pre-registered before execution: $n=200$ per cell, equal to 5 families × 10 ICs × 4 runs, with 8 adversarial dose conditions plus one control condition, for 1,800 trajectories total. The configuration was `configs/perturbation/O1_ed50_dense.yaml`; the analysis script was `scripts/fit_ed50_hierarchical.py`.

**Dense O1 adversarial dose response, separating raw, net, and persistent endpoints**

| dose (tokens) | raw switch rate | Wilson 95% CI | net over natural floor | persistent escape, K-means $k=12$ |
|---:|---:|---|---:|---:|
| 20 | 0.415 | [0.349, 0.484] | +0.068 | 0.035 |
| 50 | 0.510 | [0.441, 0.578] | +0.163 | 0.070 |
| 80 | 0.575
```

---

## Wilson CI

**First-use line:** 1109

**Match:** `Wilson CI`

**Context (700 chars before, 200 after):**

```
e-negate replace | 100% [93-100] | 100% [93-100] | 96% [86-99] |

Read alone, these numbers suggest that replace-mode regimes have almost zero injected-token barriers. The overwrite-versus-insert probe shows that this is mostly a memory-policy effect. We re-ran O2 and O3 with the same adversarial doses under two intervention modes:

- **Overwrite:** the original protocol. The injection replaces step 15's output entirely.
- **Insert:** the injected text is prepended to the context for step 15, but the model's own generated output is preserved as the state. The injected text does not remain as the state by construction.

The O2 paraphrase-replace results were:

| condition | switch rate | 95% Wilson CI |
|---|---:|---|
| control | 0.00 | [0.00, 0.07] |
| `adversarial_dose80`, overwrite | 0.92 | [0.81, 0.97] |
| `adversarial_insert_dose80` | 0.32 | [0.21, 0.46] |
| `adversarial_dose200`, overwrite |
```

---

## PCA-2

**First-use line:** 776

**Match:** `PCA-2`

**Context (700 chars before, 200 after):**

```
aw\_rate}-\operatorname{floor}
   \]
   \[
   \operatorname{persistent\_escape\_rate}=\mathbb{E}[\operatorname{persist}]
   \]

This same endpoint decomposition applies to non-embedding observables in engineering settings, including final patch family, files touched, test pass/fail sets, tool-call sequences, plan categories, security-policy violations, or embeddings of full traces.

### 4.5 Representation spaces and metric battery

For each observable's embedding matrix \(Z\in\mathbb{R}^{N\times1536}\), we compute joint projections across the full point cloud. Projections are never fit per-run or per-family, because coordinates must be comparable across trajectories, conditions, and roles.

PCA-2 is used for density estimation, potential landscapes, and two-dimensional plots. For short-output observables it typically carries 10% to 15% of total variance; for longer-context observables it can 
```

---

## PCA-3

**First-use line:** 969

**Match:** `PCA-3`

**Context (700 chars before, 200 after):**

```
on visualization toolkit

Perturbation experiments additionally generate an empirical-potential and barrier-visualization toolkit. PCA-2 coordinates are converted into a smoothed density estimate \(\hat\rho(x)\), then into an effective potential \(V(x)=-\log \hat\rho(x)\). Basin centers are detected as local minima on the potential grid. Geodesic barriers between basin pairs are computed by shortest-path search on the grid, with the barrier height defined by the maximum potential encountered along the path.

The toolkit also produces streamlines over potential contours, geodesic overlays, condition-wise flow-field panels, and three-dimensional density-shell animations. The 3D animations use PCA-3 coordinates, iso-density shells, sampled trajectory walks, and visual markers for perturbation events. These visualizations are interpretive aids for the perturbation endpoint analyses. Full grid par
```

---

## PCA-10

**First-use line:** 616

**Match:** `PCA-10`

**Context (700 chars before, 200 after):**

```
-bearing endpoints. Recurrence, dwell, basin occupancy, periodicity, dispersion, finite-time ensemble-spread spectra, sharpness dimension, flow fields, and density landscapes are used to characterize a regime and to support interpretation. They are not, by themselves, sufficient for a headline claim unless they enter one of the five endpoints defined operationally in §4.13.

The five primary endpoints are:

1. **Operational attractor score**, based on the C1-C4 attractor criteria: late-window basin persistence, recurrence or dwell above null, embedder robustness, and contraction, re-entry, or collapse.
2. **Group-aware basin predictability**, measured by predicting the late basin from early PCA-10 state while holding out prompt families.
3. **Perturbation switching signature**, measured by paired treatment-control final-cluster disagreement, interpreted alongside the paired control-control sto
```

---

## PCA-50

**First-use line:** 776

**Match:** `PCA-50`

**Context (700 chars before, 200 after):**

```
ngs of full traces.

### 4.5 Representation spaces and metric battery

For each observable's embedding matrix \(Z\in\mathbb{R}^{N\times1536}\), we compute joint projections across the full point cloud. Projections are never fit per-run or per-family, because coordinates must be comparable across trajectories, conditions, and roles.

PCA-2 is used for density estimation, potential landscapes, and two-dimensional plots. For short-output observables it typically carries 10% to 15% of total variance; for longer-context observables it can carry approximately 25%. PCA-10 is used for K-means clustering, basin classification, basin predictability, recurrence, dwell, and most endpoint-level metrics. PCA-50 is used only as a pre-reduction stage before t-SNE.

t-SNE is fit after PCA-50 pre-reduction using cosine distance, perplexity 30 capped at \((N-1)/4\) for small \(N\), PCA initialization, automatic 
```

---

## t-SNE

**First-use line:** 776

**Match:** `t-SNE`

**Context (700 chars before, 200 after):**

```
nd metric battery

For each observable's embedding matrix \(Z\in\mathbb{R}^{N\times1536}\), we compute joint projections across the full point cloud. Projections are never fit per-run or per-family, because coordinates must be comparable across trajectories, conditions, and roles.

PCA-2 is used for density estimation, potential landscapes, and two-dimensional plots. For short-output observables it typically carries 10% to 15% of total variance; for longer-context observables it can carry approximately 25%. PCA-10 is used for K-means clustering, basin classification, basin predictability, recurrence, dwell, and most endpoint-level metrics. PCA-50 is used only as a pre-reduction stage before t-SNE.

t-SNE is fit after PCA-50 pre-reduction using cosine distance, perplexity 30 capped at \((N-1)/4\) for small \(N\), PCA initialization, automatic learning rate, and random seed 42. t-SNE is compute
```

---

## HDBSCAN

**First-use line:** 1073

**Match:** `HDBSCAN`

**Context (700 chars before, 200 after):**

```
cluster, and 24 drifted elsewhere. Even among trajectories that visibly jump at injection, roughly half do not remain in the post-injection basin.

![Fig 3. **Post-perturbation relaxation and recovery.** Relaxation curves after perturbation show that many trajectories move transiently but do not remain in the injected post-jump basin. The curves support the distinction between raw switching and durable escape. Source: `data/aggregated/perturbation_cross_regime/cross_relaxation_curves.png`.[^Fig3]](data/aggregated/perturbation_cross_regime/cross_relaxation_curves.png)


Because persistence is cluster-defined, we also recomputed it under three granularities: K-means $k=12$, K-means $k=4$, and HDBSCAN. The formal persistent-escape ED50, the dose at which persistent escape reaches 50%, is not reached under any of the three definitions.

| dose | persistent escape, $k=12$ | persistent escape, $k=4$ 
```

---

## K-means

**First-use line:** 724

**Match:** `K-means`

**Context (700 chars before, 200 after):**

```
ing; if the terminal step is missing for any member; if embeddings or cluster labels are unavailable for the selected observable; if the adversarial source violates the source rule; if the perturbation text is empty after tokenization; or if the run does not match the configured injection step and terminal horizon. Exclusions are applied before endpoint computation and are counted in audit tables.

#### Algorithm 1: paired perturbation evaluation

Input: seed or task \(x\), generator \(P_\theta\), context-update rule \(\mathcal{N}\), injection condition \(c\), injection step \(t_{\mathrm{inj}}\), terminal step \(T\), observable map \(O\), and equivalence rule \(C\). In this paper \(C\) is a K-means cluster in joint PCA-10 space, but the algorithm only requires a pre-specified equivalence rule.

1. Run two unperturbed controls:
   \[
   A=\operatorname{RunLoop}(x,P_\theta,\mathcal{N},\text{no in
```

---

## KDE

**First-use line:** 1341

**Match:** `KDE`

**Context (700 chars before, 200 after):**

```
 narrow but useful: the **regime-level qualitative claims** generalize to `gpt-4.1-nano`; the **dense endpoint calibration** remains a `gpt-4o-mini` result until rerun directly.

---

### Phase E, secondary analyses

### 5.12 Density landscapes are descriptive, not calibrated

The $V(x) = -\log \hat{\rho}(x)$ density-landscape analyses visualize where trajectory clouds spend time in a joint PCA-2 projection. They are useful descriptive summaries of geometry, but they are not calibrated barrier-height estimates and they do not validate the token ED50 values in §5.1.

The main limitation is parameter sensitivity. For the O1 perturbation pilot, we recomputed $V^\star$ across 45 combinations of KDE bandwidth, grid resolution, and basin count. Per-condition coefficients of variation ranged from 14% to 24%. A single numerical $V^\star$ value is therefore not stable enough to quote as a calibrated
```

---

## rolling_k3

**First-use line:** 676

**Match:** `rolling_k3`

**Context (700 chars before, 200 after):**

```
within families we obtain variation across seeds. Unless a temperature sweep is explicitly being run, sampling uses temperature \(T=0.8\). The Phase 2b temperature sweep varies temperature and, in some cells, `steps_per_run`.

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small`, producing 1536-dimensional vectors. We embed multiple observables per step. Each observable is a different text view of the same recursive state, and all analyses are repeated per observable to expose representation-dependent findings.

| observable | source location | what it captures |
|---|---|---|
| `output` | `core/observables.py` | the model's \(Y_t\) text alone, with no context |
| `rolling_k3` | `core/observables.py` | concatenation of the last 3 outputs |
| `context_tail` | `core/observables.py` | the last 4000 characters of the running context |
| `context_full` | `core/observables.py` 
```

---

## context_tail

**First-use line:** 677

**Match:** `context_tail`

**Context (700 chars before, 200 after):**

```
 explicitly being run, sampling uses temperature \(T=0.8\). The Phase 2b temperature sweep varies temperature and, in some cells, `steps_per_run`.

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small`, producing 1536-dimensional vectors. We embed multiple observables per step. Each observable is a different text view of the same recursive state, and all analyses are repeated per observable to expose representation-dependent findings.

| observable | source location | what it captures |
|---|---|---|
| `output` | `core/observables.py` | the model's \(Y_t\) text alone, with no context |
| `rolling_k3` | `core/observables.py` | concatenation of the last 3 outputs |
| `context_tail` | `core/observables.py` | the last 4000 characters of the running context |
| `context_full` | `core/observables.py` | fixed-window 8000-character tail, used in longer-memory pilot configurations |

```

---

## turn_pair

**First-use line:** 683

**Match:** `turn_pair`

**Context (700 chars before, 200 after):**

```
atenation of the last 3 outputs |
| `context_tail` | `core/observables.py` | the last 4000 characters of the running context |
| `context_full` | `core/observables.py` | fixed-window 8000-character tail, used in longer-memory pilot configurations |
| `last_user_turn` | `experiments/dialog/observables.py` | dialog-only: most recent user or role-A utterance |
| `last_agent_turn` | `experiments/dialog/observables.py` | dialog-only: most recent agent or role-B utterance |
| `rolling_user_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 user turns |
| `rolling_agent_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 agent turns |
| `turn_pair` | `experiments/dialog/observables.py` | dialog-only: most recent user-agent exchange concatenated |

The role-specific observables are essential for dialog analysis because basin scores, recurrence,
```

---

## RG

**First-use line:** 1348

**Match:** `RG`

**Context (700 chars before, 200 after):**

```
cross the 45 parameter combinations, control had the highest $V^\star$ in 98% of combinations, adversarial had the lowest $V^\star$ in 89%, and neutral and lorem occupied the middle. This supports a weak geometric statement: the density-landscape summaries preserve a robust rank ordering within the O1 perturbation pilot. It does not support a quantitative $V^\star$ to ED50 conversion.

This distinction is especially important for replace-mode regimes. O2 and O3 can show high geometric separation while also showing high overwrite-protocol switching, because the perturbation and memory policy can create or occupy a different basin rather than cross a pre-existing ridge. Full $V^\star$ tables, RG merge-distance tables, and the parameter-grid sensitivity outputs are moved to §11.11.

### 5.13 Why exactly five regimes?

The five-regime taxonomy is not recovered cleanly by unsupervised clusterin
```

---

## IPI

**First-use line:** 128

**Match:** `IPI`

**Context (700 chars before, 200 after):**

```
 kind of injected-token barrier,
   because the rule itself discards the old state. Claims that
   "replace-mode loops are easy to redirect" should be read as
   claims about overwrite mechanics, not necessarily about weak
   model attractors.

4. **Do not assume small adversarial nudges permanently redirect
   settled loops.** Even adversarial continuations selected from
   the same regime top out near 67% raw switching and fail to
   produce 50% persistent escape up to 400 tokens. For
   jailbreak-style or agent-redirection evaluations, this means
   the meaningful target is sustained post-attack behavior, not a
   one-step perturbation success.

5. **Evaluating indirect prompt injection (IPI).** Most IPI
   benchmarks today report whether the model executes the injected
   instruction at the next step, that is the *raw-switching*
   endpoint. A defense that pushes raw-switching $\mathrm{
```

---

## LFS

**First-use line:** 1877

**Match:** `LFS`

**Context (700 chars before, 200 after):**

```
ttleneck Principle.* arXiv:1503.02406 (ITW 2015).
  Original IB framework underpinning compression-in-depth analyses.
- Pimentel, T., Valvoda, J., Hall Maudslay, R., Zmigrod, R.,
  Williams, A., & Cotterell, R. (2020). *Information-Theoretic
  Probing for Linguistic Structure.* arXiv:2004.03061 (ACL 2020).
  Methodology for MI-based probing of intermediate representations.
- Saxe, A. M., Bansal, Y., Dapello, J., Advani, M., Kolchinsky, A.,
  Tracey, B. D., & Cox, D. D. (2018). *On the Information Bottleneck
  Theory of Deep Learning.* ICLR 2018. Critical examination of IB
  phases, relevant when invoking IB on LM hidden states.

---

*Reproducibility: raw trajectories are released under git-LFS;
embeddings and plots regenerate from the documented pipeline.
Reproducibility budget: approximately \$30 in OpenAI embedding API
calls plus 2 hours wall-clock on a 40-core machine. See §10.*

---

#
```

---

## API

**First-use line:** 687

**Match:** `API`

**Context (700 chars before, 200 after):**

```
 concatenated |

The role-specific observables are essential for dialog analysis because basin scores, recurrence, and predictability can differ strongly when computed on the user's questions, the agent's answers, or the concatenated exchange. D1 uses user and agent labels. D2 uses explorer and expert labels. Role names are read from `cfg.dialog.role_a.name` and `cfg.dialog.role_b.name` at embed time, so the observable wiring accepts any configured role-name pair.

For one observable string at one trajectory step, we obtain exactly one 1536-dimensional vector. There is no user-managed chunking, no per-token output, and no sliding window internal to the analysis pipeline. After the embedding API returns, each row is L2-normalized so downstream cosine similarities reduce to dot products. Thus one operator publication trajectory yields 3 vectors per step for `output`, `rolling_k3`, and `contex
```

---

## OOD

**First-use line:** 1230

**Match:** `OOD`

**Context (700 chars before, 200 after):**

```
oss-method stability, but still partly method-dependent. |

For O1, this strengthens the attractor interpretation but qualifies the switching metric. A K-means $k=12$ switch can mean movement between sub-regions of a large contractive basin rather than escape from a HDBSCAN density basin. This is why §5.1 separates raw switching from persistent escape and tests persistence under multiple cluster definitions.

We also recomputed perturbation switching in the four diagnostic perturbation pilots under K-means $k=12$, K-means $k=4$, and HDBSCAN.

| pilot | condition | $k=12$ | $k=4$ | HDBSCAN | summary |
|---|---|---:|---:|---:|---|
| O1 | adversarial | 0.54 | 0.44 | 0.60 | robustly higher than OOD |
| O1 | neutral | 0.24 | 0.18 | 0.38 | low across all |
| O1 | lorem | 0.18 | 0.18 | 0.30 | low across all |
| O2 | adversarial | 0.94 | 0.72 | 1.00 | saturated except coarse $k=4$ |
| O2 | neutral 
```

---

## MVP

**First-use line:** 1489

**Match:** `MVP`

**Context (700 chars before, 200 after):**

```
e, not the specific numerical thresholds measured in the present text-only loops.

## 8. Future directions

*The next step is to turn the present perturbation framework from a controlled recursive-loop study into a comparative measurement program for model families, memory policies, dialog scaffolds, and deployed agents.*

The proposed program proceeds from external validity, to mechanistic measurement, to scaffold ablations, to applied agent and safety settings.

### 8.1 Cross-vendor replication at publication scale

*Hypothesis: append/replace/dialog regime ordering is invariant across model families under matched perturbation dose and memory policy.*

The highest-priority extension is an MVP cross-vendor replication rather than an exhaustive survey. The central question is not whether barrier heights match numerically across providers, but whether the ordering of append, replace, and dia
```

---

## UTC

_(not found in ARTICLE.md)_

---

## RAM

**First-use line:** 991

**Match:** `RAM`

**Context (700 chars before, 200 after):**

```
sistence-boundary table, and rerun semantics live in Supplementary §11.9.

The source of truth is `steps.jsonl`. Embeddings, projections, metrics, figures, and reports are regenerable from that file plus the code and configuration. In routine development, metric and plotting changes can be rerun without additional model-generation calls.

### 4.12 Hardware and software

All experiments run locally on a single workstation with API calls to OpenAI for generation and embeddings; no GPU is required. The host used to build the released artefacts is an HP ProLiant DL360 Gen9 with two Intel Xeon E5-2687W v3 processors (2 x 10 physical cores at 3.10 GHz base, 40 logical threads total) and 256 GB of RAM, running Windows 10 Pro 64-bit. Embedding ingestion, dimensionality reduction, clustering, density-and-geodesic-barrier computation, and animation rendering are all CPU-only.

The Python environment 
```

---

## CPU

**First-use line:** 991

**Match:** `CPU`

**Context (700 chars before, 200 after):**

```
re regenerable from that file plus the code and configuration. In routine development, metric and plotting changes can be rerun without additional model-generation calls.

### 4.12 Hardware and software

All experiments run locally on a single workstation with API calls to OpenAI for generation and embeddings; no GPU is required. The host used to build the released artefacts is an HP ProLiant DL360 Gen9 with two Intel Xeon E5-2687W v3 processors (2 x 10 physical cores at 3.10 GHz base, 40 logical threads total) and 256 GB of RAM, running Windows 10 Pro 64-bit. Embedding ingestion, dimensionality reduction, clustering, density-and-geodesic-barrier computation, and animation rendering are all CPU-only.

The Python environment is Python 3.14 with numpy 2.3, scipy 1.16, scikit-learn 1.8, scikit-image 0.26, pandas 2.3, matplotlib 3.10, and imageio-ffmpeg 0.6 (resolved versions used to produce th
```

---

## GPU

**First-use line:** 991

**Match:** `GPU`

**Context (700 chars before, 200 after):**

```
orts | per-experiment `reports/` directories |

Each phase writes a deterministic intermediate, allowing downstream analyses to be rerun without regenerating trajectories. The full TikZ source, shape annotations, persistence-boundary table, and rerun semantics live in Supplementary §11.9.

The source of truth is `steps.jsonl`. Embeddings, projections, metrics, figures, and reports are regenerable from that file plus the code and configuration. In routine development, metric and plotting changes can be rerun without additional model-generation calls.

### 4.12 Hardware and software

All experiments run locally on a single workstation with API calls to OpenAI for generation and embeddings; no GPU is required. The host used to build the released artefacts is an HP ProLiant DL360 Gen9 with two Intel Xeon E5-2687W v3 processors (2 x 10 physical cores at 3.10 GHz base, 40 logical threads total) a
```

---

## OS

_(not found in ARTICLE.md)_

---
