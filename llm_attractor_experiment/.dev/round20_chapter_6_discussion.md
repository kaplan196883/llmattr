## 6. Discussion

The main result is not simply that recursive LLM loops have attractor-like regimes. It is that their apparent robustness depends on two separable choices: the memory policy that writes text back into state, and the endpoint used to define a successful perturbation. Append-mode continuation shows a real in-distribution raw dose response, with $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, but that number is not a durable escape threshold: raw switching plateaus near $67\%$, paired controls already diverge at about $35\%$, net switching never reaches the $+50$ pp criterion, and persistent escape remains below $50\%$ at every tested dose. Replace-mode loops, meanwhile, look fragile mostly because the update rule overwrites the prior state. Thus the practical unit of analysis is not the prompt alone, or the model alone, but the generator-nudge system evaluated under raw, net, and persistent endpoints.

### 6.1 Recursive-loop robustness is determined by memory policy and endpoint choice

The central lesson of these experiments is that recursive-loop behavior is determined jointly by the generator and the context-update rule. In the formalism of §3.1, the model samples $Y_t \sim P_\theta(\cdot \mid X_t; f)$, while the nudge $\mathcal{N}_f$ decides how that sampled text becomes the next state. Two loops with the same generator and similar prompt instructions can therefore have different perturbation responses solely because one preserves prior context and the other overwrites it.

The second lesson is that "robustness" is endpoint-dependent. A loop can move without staying moved; two unperturbed runs can diverge without any perturbation; and an overwrite-style update can make a system appear fragile even when inserted text has little effect. This is why the paper separates raw switching, net switching, and persistent escape (§3.1.2). In O1, adversarial append-mode perturbations yield $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, with 4PL $=36$, GLMM $=41$, and family-cluster bootstrap median $=52$ tokens, 95% CI $[8.5, 242]$ (§5.6.1). But the raw curve plateaus near $67\%$, the control-vs-control floor is $\approx 35\%$, the net effect saturates at only $+32$ pp, and persistent escape never crosses $50\%$ (§5.15). The same loop is therefore movable under the raw endpoint but not durably redirected under the strict endpoint.

### 6.2 Append, replace, and dialog implement different memory mechanisms

Append, replace, and dialog are not implementation details; they are different memory mechanisms. In append mode, the perturbation enters an already-accumulated context and must compete with prior trajectory mass. This makes append-mode continuation resistant to irrelevant text: O1 neutral and lorem perturbations remain near the out-of-distribution drift floor, while in-distribution adversarial text produces the graded raw dose response measured in §5.6.1.

Replace mode implements a different mechanism. The previous state is discarded, so the next state is dominated by the replacement. The overwrite-vs-insert probe makes this visible: for O2, overwrite-mode perturbations switch at $92$--$98\%$, while insert-mode perturbations switch at only $18$--$32\%$, a $60$--$80$ pp gap (§5.17). For O3, overwrite switching is $90$--$92\%$, but insert switching is only $12$--$18\%$, a $72$--$80$ pp gap. Thus most apparent replace-mode fragility is attributable to overwrite mechanics rather than a low injected-token barrier.

Dialog sits between these cases. It preserves a running transcript like append mode, but role-structured turns give recent utterances high local influence. D1 therefore behaves as a dialogue-state-driven multi-basin regime, while D2 suggests topic-anchored "content gravity" under drill-down structure (§5.8, §5.14).

### 6.3 A raw-switching ED50 is not a persistent-escape barrier

The most important interpretive correction is that $\mathrm{ED50}_{\mathrm{raw}}$ is not the same quantity as a persistent-escape barrier. Raw switching asks whether the perturbed trajectory's terminal cluster differs from its paired control. That endpoint is useful, but it conflates three phenomena: true redirection, ordinary stochastic divergence, and transient movement that later recovers. Persistent escape is stricter: the trajectory must visibly jump at injection and remain in the post-injection basin through the terminal step (§3.1.2).

Under the permissive raw endpoint, O1 adversarial append-mode continuation has a clear dose response: $\mathrm{ED50}_{\mathrm{raw}} \approx 40$ tokens, with estimates 36, 41, and 52 tokens across the 4PL, GLMM, and family-cluster-bootstrap analyses (§5.6.1). But the raw plateau is only $\approx 67\%$, not $100\%$. Moreover, paired controls already disagree at about $35\%$, so subtracting the stochastic floor leaves a maximum net effect of only $+32$ pp at 400 tokens, below the $+50$ pp criterion for $\mathrm{ED50}_{\mathrm{net}}$.

The persistent endpoint is smaller still. At the highest tested dose, persistent escape reaches only $16\%$ under canonical K-means $k=12$, $10\%$ under K-means $k=4$, and $39.5\%$ under HDBSCAN (§5.15). None crosses $50\%$ in the tested 5--400 token range. The correct conclusion is therefore: O1 has a finite raw-switching dose response, but no measured persistent-escape barrier in this experiment.

### 6.4 Density landscapes diagnose basin geometry but do not calibrate token barriers

The empirical potential landscape $V(x) = -\log \rho(x)$ is useful as a diagnostic picture of trajectory density, but it should not be read as a calibrated token barrier. The landscape is computed after embedding, projection, smoothing, and basin detection, so its absolute values depend on the representation and analysis choices. The parameter-grid sensitivity analysis confirms this: per-condition $V^\star$ values vary with coefficient of variation $14$--$24\%$ across KDE bandwidths, grid resolutions, and basin-count settings (§5.16).

What survives is the weaker ordinal claim. In the O1 perturbation pilot, the rank ordering of $V^\star$ is stable across $89$--$98\%$ of parameter combinations: control is usually highest, adversarial usually lowest, and neutral / lorem occupy the middle (§5.16). This supports the use of density landscapes as descriptive basin-geometry tools. It does not justify converting $V^\star$ into tokens, nor does it independently validate $\mathrm{ED50}_{\mathrm{raw}}$. The behavioral dose-response and geometric landscape are complementary measurements, not interchangeable estimators of the same scalar.

### 6.5 Robust recursive-loop evaluations must report floors, persistence, and overwrite mechanics

1. **Report the context-update rule.** Every recursive-loop evaluation should state whether the system appends, replaces, role-structures, summarizes, pins, rolls, or hybridizes memory, because the same generator can show different perturbation responses under different nudges (§3.1, §5.17).

2. **Report raw, net, and persistent-escape endpoints rather than raw switching alone.** Raw movement says whether the trajectory changed, net switching subtracts the control-vs-control stochastic floor, and persistent escape asks whether the perturbation produced a durable basin change after recovery turns (§3.1.2, §5.6.1, §5.15).

3. **For replace-style or summary-memory systems, run an overwrite-vs-insert control.** If overwrite switching is high but insert switching is low, the measured fragility is partly the memory policy discarding prior state rather than the injected text overcoming a basin barrier (§5.17).

A checklist version of this reporting standard is given in Box 1 (§11.12).

### 6.6 The unresolved question is external validity across generators and real agent scaffolds

The present evidence is strongest for the measured generator-nudge systems, not for all LLMs or all agent architectures. The within-vendor replication on `gpt-4.1-nano` preserves the qualitative thesis predicates (§5.21), but both generators are from the same vendor family. Cross-vendor and open-weight replication remain necessary before the architecture-vs-generator partition can be treated as general (§7.1, §8.1).

The same caution applies to real agent scaffolds. The paper studies recursive text loops with controlled update rules and embedding-space observables; it does not directly evaluate coding agents, tool-using assistants, SWE-Bench tasks, jailbreak benchmarks, production indirect prompt injection, or factuality-graded hallucination settings (§7.5). Those domains can adopt the same endpoint decomposition, but their observables must be application-specific: patch family, files touched, tests passed, policy violations, tool-call traces, or grounded factual claims.

The paper's position is therefore deliberately bounded: recursive-loop stability is measurable, but the measurement only becomes meaningful when memory policy, stochastic floor, and persistence endpoint are made explicit.
