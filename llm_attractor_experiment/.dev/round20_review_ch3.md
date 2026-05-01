# Review of §3 Formal framework and hypotheses

1. **Issue — §3 reads like several mini-papers rather than one theory chapter.**  
   The chapter mixes: formal dynamical definitions, endpoint taxonomy, empirical ED50 estimates, attractor audit results, a theorem with corollaries, and conjectural geometry.  
   **Why it matters —** Readers cannot tell which claims are definitions, which are hypotheses, which are proven structural facts, and which are results. This weakens the chapter's authority.  
   **Concrete fix —** Reorganize §3 around a strict "define, then hypothesize" spine. Suggested opening replacement:

   > This section defines the recursive-loop object studied in the paper, the perturbation estimands used to measure basin switching, and the operational criteria by which we call a regime attractor-like. Numerical ED50 estimates, pass/fail audits, and regime-specific measurements are results and are reported later. The only substantive structural claim retained here is the replace-vs-append distinction: replace mode admits a generation-budget access bound, whereas append mode motivates an injected-token accumulation conjecture.

   Then keep in §3 only: nudge formalism; endpoint definitions; C1–C4 definition; compressed replace proposition; append conjecture; observables; hypotheses.

2. **Issue — The formal barrier definition does not match the later claim that it is persistent escape.**  
   Current definition:
   \[
   \Pr[X_T\in B_2\mid X_0\in B_1,\text{inject}_\tau]\ge 1/2
   \]
   is terminal access only. It does not require an injection-step jump or persistence. Yet the text says it corresponds to \(\mathrm{ED50}_{\mathrm{persist}}\).  
   **Why it matters —** This is the most serious definitional inconsistency in §3. A reviewer can fairly say the main "barrier" estimand changes meaning mid-section.  
   **Concrete fix —** Either rename the current quantity terminal-redirection barrier, or redefine it as persistent escape. Recommended replacement:

   \[
   \mathrm{B}_{\mathrm{persist}}(B_1\to B_2)
   =
   \inf\Bigl\{\tau:
   \Pr\bigl[J_\tau(B_1\to B_2)=1,\ X_T\in B_2
   \mid X_{t_{\mathrm{inj}}^-}\in B_1,\ \mathrm{inject}_\tau\bigr]
   \ge \tfrac12
   \Bigr\}.
   \]

   Add immediately:

   > Here \(J_\tau(B_1\to B_2)\) is the operational injection-step jump indicator defined by the late-window basin partition. Without \(J_\tau\), the same formula defines a terminal raw-switching barrier, not a persistent-escape barrier.

3. **Issue — The raw/net/persistent endpoint definitions are conceptually strong but need cleaner reference-cluster notation.**  
   The prose says "different cluster than its paired control," but the formulas use \(C_T\neq C_0\), where \(C_0\) is called the initial cluster. Those are different estimands.  
   **Why it matters —** The endpoint taxonomy is one of the paper's main contributions; ambiguity here will propagate into every later result.  
   **Concrete fix —** Define the reference cluster once and use it consistently. For example:

   > Let \(C_{\mathrm{ref}}\) denote the declared reference basin for a perturbed trajectory: in this paper, the pre-injection basin of that same trajectory. Let \(C_T^{(D)}\) be the terminal basin after injected dose \(D\). Let \(p_0=\Pr(C_T^{(0,1)}\neq C_T^{(0,2)})\) be the control-vs-control natural switching floor under the same sampling protocol.

   Then write:

   \[
   S_{\mathrm{raw}}(D)=\Pr(C_T^{(D)}\neq C_{\mathrm{ref}}),
   \]
   \[
   S_{\mathrm{net}}(D)=S_{\mathrm{raw}}(D)-p_0,
   \]
   \[
   S_{\mathrm{persist}}(D)=\Pr(J_D=1,\ C_T^{(D)}\neq C_{\mathrm{ref}}).
   \]

   Add:

   > If the defining set is empty over the tested dose range, the ED50 is reported as not reached, not extrapolated.

4. **Issue — The C1–C4 attractor criteria are close to citable, but not yet packaged as a reusable definition.**  
   The current version mixes thresholds, measurement references, exceptions, and regime-specific commentary.  
   **Why it matters —** Other papers could cite this operational definition, but only if it is self-contained and separable from your results.  
   **Concrete fix —** Convert it into a boxed definition. Suggested structure:

   > **Definition. Operational attractor-like regime.** Fix a trajectory ensemble, an observable map, an embedding map, a late-window basin partition, and a declared null ensemble. A regime \(r\) is evaluated by four binary criteria:  
   > C1 basin predictability; C2 recurrence or dwell above null; C3 embedder-robust recurrence class; C4 re-entry, contraction, or absorbing collapse.  
   > A strong attractor passes 4/4. An attractor-like regime passes at least 3/4. A regime passing fewer than 3/4 is not an operational attractor under this definition. Missing measurements count as failure unless the criterion is structurally inapplicable and this inapplicability is declared before evaluation.

   Then put the exact thresholds below this definition.

5. **Issue — The regime audit table belongs in Results, not in the formal framework.**  
   The table reports measured values for O1–O3, D1, and D2 and assigns labels.  
   **Why it matters —** Including results inside §3 makes the hypotheses feel post hoc and blurs the distinction between framework and evidence. It also creates a problem for D1: "PASS stratified; FAIL group-aware" but still labeled attractor-like.  
   **Concrete fix —** Move the audit table to §5. In §3 replace it with:

   > The criteria above are applied to each experimental regime in the Results. The framework itself does not assume that any regime passes; the pass/fail audit is an empirical outcome.

   In the Results table, separate "primary criterion" from "robustness sensitivity" and explicitly state whether group-aware C1 is a gate or a diagnostic.

6. **Issue — Lemma 1 and the two corollaries are too long for the main theory chapter unless they are used quantitatively downstream.**  
   The theorem is mathematically fine, but its proof scaffolding interrupts the conceptual flow.  
   **Why it matters —** Nature/Science-style reviewers often tolerate main-text theorems only when they directly power later analysis. Here the key point is simpler: replace mode has a generated-token access bound, not an injected-token accumulation barrier.  
   **Concrete fix —** Compress §3.1.4 to one proposition and move the full lemma, corollaries, and proof to the Supplement. Main-text replacement:

   > **Proposition. Replace-mode access bound.** In replace mode, suppose every reachable non-target state has one-step probability at least \(q_0\) of generating a target-basin replacement, target entry persists to terminal measurement with probability at least \(r_0\), and expected generation length is at most \(\kappa\) per step. Then after \(m\) post-injection replace steps,
   > \[
   > \Pr(X_T\in B_2)\ge r_0[1-(1-q_0)^m],
   > \qquad
   > \mathbb{E}G_m\le \kappa m .
   > \]
   > This bounds post-injection generated tokens, not injected-token dose.

7. **Issue — The notation conflates content operator and nudge, and dialog violates the bounded-context convention.**  
   You write \(\mathcal{N}_f\), although \(f\) already denotes the content operator. Also:
   \[
   \mathcal{N}_{\text{dialog}}(X_t,Y_t)=X_t\Vert \operatorname{format\_turn}(r_t,Y_t)
   \]
   lacks clipping, despite \(\mathcal{C}\) being bounded clipped contexts.  
   **Why it matters —** This is a formal consistency problem at the foundation of the chapter.  
   **Concrete fix —** Use separate notation:

   > Let \(f\) denote the content instruction and \(\eta\) the memory policy. The recurrence is
   > \[
   > Y_t\sim P_\theta(\cdot\mid X_t;f),\qquad
   > X_{t+1}=\mathcal{N}_\eta(X_t,Y_t).
   > \]

   Define dialog as:

   \[
   \mathcal{N}_{\mathrm{dialog}}(X_t,Y_t)
   =
   \operatorname{clip}\!\left(X_t\Vert \operatorname{format\_turn}(r_t,Y_t)\right).
   \]

8. **Issue — The effective-context-share conjecture is currently too weak.**  
   The statement
   \[
   \Pr(X_T\in B_2\mid \tau)\le \Psi(\alpha_\tau)
   \]
   with \(\Psi\) monotone is nearly vacuous: \(\Psi\equiv1\) always works.  
   **Why it matters —** This is meant to be the mechanistic conjecture for append-mode barriers; it should make a testable prediction.  
   **Concrete fix —** Replace the upper-bound formulation with a response-curve formulation:

   > Let \(a_\tau\) be the semantically weighted share of the clipped context occupied by basin-relevant injected text. Append-mode accumulation predicts a nondecreasing switching curve
   > \[
   > S_{B_1\to B_2}(\tau)
   > =
   > \Pr(X_T\in B_2\mid X_{t_{\mathrm{inj}}}\in B_1,\tau)
   > \approx
   > p_{\mathrm{floor}}+
   > (p_{\max}-p_{\mathrm{floor}})
   > F(a_\tau-\alpha^\star_{B_1\to B_2}),
   > \]
   > where \(F\) is increasing and the threshold \(\alpha^\star\) is lower for in-distribution counter-context than for out-of-distribution text.

9. **Issue — §3.2 is too thin relative to how much later analysis depends on observables and embeddings.**  
   It says all metrics are functions of polylines, but does not clarify that observables are measurement maps, not parts of the loop dynamics.  
   **Why it matters —** Readers may confuse the state \(X_t\), the generated text \(Y_t\), the observable \(O_t\), and the embedded point \(z_t\).  
   **Concrete fix —** Add this bridge paragraph:

   > Observable maps are post-hoc measurement functions; they do not feed back into the recurrence unless explicitly used as part of a nudge. Thus \(X_t\) is the dynamical state, \(Y_t\) is the sampled continuation, \(O_t=h(X_t,Y_t,\mathrm{metadata})\) is the text view selected for measurement, and \(z_t=\phi(O_t)\) is the vector representation used for clustering, recurrence, dwell, and basin-predictability metrics. The Methods section fixes the observable family, embedding normalization, clustering procedures, and null ensembles before applying the C1–C4 criteria.

10. **Issue — H1–H4 are partly written as expectations rather than falsifiable predicates.**  
    Phrases such as "there exist endogenous attractor-like regimes," "qualitatively different perturbation sensitivities," and "survives a 30× increase" need operational pass/fail conditions.  
    **Why it matters —** The hypotheses should connect directly to the criteria and endpoints just defined.  
    **Concrete fix —** Rewrite them as:

    > **H1.** At least one recursive-loop regime passes the operational attractor-like definition under the declared observable, embedding, basin partition, and null ensemble.  
    > **H2.** The pass/fail pattern and attractor subtype depend on both content operator \(f\) and nudge \(\eta\); changing \(\eta\) while holding content approximately fixed changes the measured regime class.  
    > **H3.** Perturbation sensitivity differs by nudge: append mode exhibits a dose-dependent in-distribution raw-switching curve above the stochastic floor; replace mode reaches high switching at the smallest tested dose or without dose; dialog lies between these extremes and depends on role/state structure.  
    > **H4.** The qualitative regime labels and endpoint ordering observed in small-\(N\) exploration remain unchanged under the large-\(N\) battery within declared uncertainty.

## Verdict

§3 contains the right theoretical ingredients, but it is currently overloaded and insufficiently separated into definitions, structural claims, conjectures, and results. The highest-priority fixes are to resolve the barrier/persistent-escape mismatch, make C1–C4 a clean reusable definition, and move empirical audit material out of the framework chapter. After those changes, §3 can read as a coherent formal foundation rather than a dense compilation of five adjacent arguments.
