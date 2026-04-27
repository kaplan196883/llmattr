# Endogenous Attractor Regimes in Recursive Large Language Model Loops:
## A Quantitative Taxonomy with Measured Basin Barriers

## Abstract

We study recursive large-language-model (LLM) loops in which a model is fed a context, generates a continuation, and then re-encounters that continuation through a deterministic context-update rule. Rather than treating these loops as anecdotal curiosities that “get stuck,” “paraphrase themselves,” or “collapse,” we frame them as bounded stochastic dynamical systems and ask whether they exhibit reproducible attractor-like regimes.

We analyze 37 experiments spanning pilot studies, publication-scale replications, temperature sweeps, and perturbation studies. Across these experiments, we run 50–1350 trajectories per configuration of `gpt-4o-mini`, embed trajectory observables with `text-embedding-3-small`, and compute a broad metric battery on the resulting trajectories in embedding space. The central empirical result is that recursive LLM loops do not fall into a single generic failure mode. Instead, they separate into a small number of distinct regimes selected jointly by the content operator (continue, paraphrase, summarize-and-negate, dialog) and the context-update rule (append, replace, structured dialog append).

We identify four robust regimes—contractive basin, oscillatory 2-cycle, absorbing collapse, and stylistic multi-basin—plus a fifth structured-dialog regime characterized by topic-preserving “content gravity.” We then quantify regime stability with perturbation experiments that inject control, neutral, lorem, and adversarial text mid-trajectory. Append-mode continuation exhibits a measurable in-distribution barrier: roughly 150 tokens of adversarial in-distribution text are required to reach a 50% switching rate, whereas out-of-distribution text saturates near the drift floor. Replace-mode operators are nearly perturbation-transparent, switching under almost any nontrivial intervention. Dialog regimes lie in between, with barrier strength depending on conversational structure.

To complement the metric battery, we introduce a geometric visualization toolkit based on empirical density, an effective potential \(V(x) = -\log \rho(x)\), geodesic paths between density peaks, and volumetric iso-density renderings. The geometric barrier estimates agree qualitatively with perturbation-derived switching thresholds. Together, these results support a quantitative taxonomy of recursive LLM regimes and provide a reproducible framework for studying stability, basin structure, and controllability in LLM loops.

---

## 1. Introduction

### 1.1 Recursive LLM loops as dynamical systems

When the output of a language model is fed back into its subsequent prompt, the model is no longer being sampled in a single-shot setting. It is being iterated. In practice, this kind of recursion appears in agent loops, self-reflection prompts, summarization chains, dialog simulations, synthetic data generation, and many lightweight orchestration systems. Practitioners have long reported that such loops often “lock onto” a topic, alternate between a small number of phrasings, or collapse into degenerate output. Yet these observations have mostly remained informal.

This paper takes a different view. We treat recursive LLM loops as bounded stochastic dynamical systems whose behavior depends on (i) the model’s conditional next-text distribution, (ii) the rule used to update context after each generation, and (iii) the content transformation induced by the prompt. This framing lets us ask sharper questions: Are there distinct attractor-like regimes? Are those regimes measurable and reproducible? And can their stability be quantified by perturbation?

### 1.2 Research questions

We investigate four questions.

1. **Existence.** Do recursive LLM loops exhibit endogenous attractor-like structure, rather than merely prompt-specific repetition or sampling noise?
2. **Mechanism.** Does the qualitative regime depend on the interaction between the content operator and the context-update rule?
3. **Barrier structure.** Can different regimes be distinguished by the amount and type of perturbation required to move a trajectory from one basin to another?
4. **Scalability.** Do the qualitative findings survive an order-of-magnitude increase in sample size?

### 1.3 Main contributions

This work makes five contributions.

1. It introduces a formal dynamical-systems framing for recursive LLM loops based on bounded context state, a model distribution \(P_\theta\), and an explicit context-update operator.
2. It identifies a four-regime empirical taxonomy—contractive, oscillatory, absorbing, and stylistic multi-basin—and a fifth structured-dialog regime discovered through perturbation experiments.
3. It measures perturbation barrier structure across regimes using controlled mid-trajectory injections and dose-response sweeps.
4. It introduces a geometric visualization toolkit based on empirical density, effective potential, and inter-basin geodesics.
5. It presents a reproducible `embed → analyze → report` pipeline with raw trajectory logs, cached embeddings, deterministic projections, and report generation.

---

## 2. Background and framing

### 2.1 Attractor analysis for neural systems

Attractor analysis is well established for recurrent neural networks, where fixed points, limit cycles, and low-dimensional manifolds can often be studied using smooth state-space methods. Recursive LLM loops differ in two ways. First, the state is not an internal recurrent vector exposed to the analyst, but a bounded text context. Second, the update is sample-driven rather than smoothly differentiable. This makes classical Jacobian-based analysis less natural.

Our approach substitutes representation-level statistics for exact state-space derivatives. We treat trajectory observables embedded into vector space as measurement channels on an underlying recursive system, then evaluate recurrence, dwell, basin concentration, predictability, oscillation, dispersion, and ensemble contraction.

### 2.2 Prior observations in language models

Prior work on language-model degeneration has established that sampling can produce repetition, blandness, and collapse. Those findings motivate studying recursive failure modes, but they do not by themselves provide a taxonomy of loop architectures. Our claim is broader: recursive loops can settle into qualitatively different regimes depending on how state is updated and what transformation the model is asked to perform.

### 2.3 Effective potentials and geometric visualization

We use the empirical density of embedded trajectories to define an effective potential-like quantity
\[
V(x) = -\log \rho(x),
\]
where \(\rho(x)\) is a smoothed density estimate in a low-dimensional projection. This should be understood as a descriptive geometric summary, not a derived physical free energy. It is useful because it turns dense trajectory regions into valleys, sparse regions into ridges, and inter-basin transitions into geometric paths.

### 2.4 Dialog as a distinct recursive architecture

Dialog loops differ from single-stream operator loops because they introduce structured alternation between roles. Even when both are implemented with append-style memory, role structure can induce regimes that are neither pure contraction nor pure oscillation. This becomes particularly important in the drill-down experiments, where conversational structure itself contributes to basin stability.

---

## 3. Formal framework and hypotheses

### 3.1 Recursive bounded-context model

Let \(X_t \in \mathcal C\) denote the bounded visible context at step \(t\), where \(\mathcal C\) is the space of valid clipped contexts. Let
\[
Y_t \sim P_\theta(\cdot \mid X_t; f)
\]
be the continuation generated by a language model with parameters \(\theta\), under a content operator \(f\) such as continuation, paraphrase, summarization-and-negation, or dialog. Let
\[
\mathcal N_f : \mathcal C \times \mathcal Y \to \mathcal C
\]
be the context-update operator, or **nudge**, that maps the current state and model output to the next state:
\[
X_{t+1} = \mathcal N_f(X_t, Y_t).
\]

This yields a bounded stochastic dynamical system:
\[
Y_t \sim P_\theta(\cdot \mid X_t; f), \qquad X_{t+1} = \mathcal N_f(X_t, Y_t).
\]

In the experiments studied here, the relevant nudges are:

- **Append mode**
  \[
  \mathcal N_{\text{append}}(X_t, Y_t) = \operatorname{clip}(X_t \Vert Y_t)
  \]
- **Replace mode**
  \[
  \mathcal N_{\text{replace}}(X_t, Y_t) = \operatorname{clip}(Y_t)
  \]
- **Dialog mode**
  \[
  \mathcal N_{\text{dialog}}(X_t, Y_t) = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)
  \]
  with role label \(r_t\) alternating across turns.

### 3.2 Observable maps and representation space

The attractor-like structure of interest need not be directly legible in raw text. We therefore define observable maps \(O_t\) that extract text views of the trajectory and then embed them into a vector space:
\[
z_t = \phi(O_t) \in \mathbb R^m.
\]
The key observables are the current output, a rolling window of recent outputs, and clipped views of the running context. Dialog experiments add role-specific observables.

### 3.3 Hypotheses

We test four hypotheses.

**H1 (endogenous attractor-like structure).** Recursive bounded-context LLM loops exhibit stable, recurrent, or basin-like regions generated by the loop dynamics themselves rather than by a single prompt instance.

**H2 (mechanism).** Regime depends jointly on the content operator and the context-update rule. In particular:

- append + content-preserving \(\Rightarrow\) contractive basin;
- replace + content-preserving \(\Rightarrow\) oscillation;
- replace + content-degrading \(\Rightarrow\) absorbing collapse;
- structured dialog \(\Rightarrow\) multi-basin regimes with style or content-dependent stability.

**H3 (barriers).** Different regimes display qualitatively different perturbation sensitivities. Append-mode loops exhibit measurable in-distribution dose thresholds; replace-mode loops exhibit weak or negligible barriers; dialog regimes lie in between.

**H4 (scale).** The qualitative regime structure survives substantial increases in sample size.

---

## 4. Methods

### 4.1 Loop architectures

We study three update architectures:

\[
\text{Append: } X_{t+1} = \operatorname{clip}(X_t \Vert Y_t)
\]

\[
\text{Replace: } X_{t+1} = \operatorname{clip}(Y_t)
\]

\[
\text{Dialog: } X_{t+1} = X_t \Vert \operatorname{format\_turn}(r_t, Y_t)
\]

In all cases, clipping truncates the oldest portion of the context once the running string exceeds 12,000 characters. This preserves recent state while enforcing a fixed external memory budget.

### 4.2 Sampling setup

Experiments vary in scale. The publication-scale runs use 5 prompt families, 30 initial conditions per family, and 3 runs per condition, for 450 trajectories per regime and 40 steps per trajectory. Dialog runs record role-specific turns, so the number of embedded observations is correspondingly larger.

Prompt families are chosen to vary topic and tone while preserving within-family comparability. Default sampling uses temperature 0.8 except in the temperature sweeps.

### 4.3 Observables and embeddings

Each step is transformed into one or more text observables. For operator experiments, the main observables are:

- `output`: the current \(Y_t\),
- `rolling_k3`: the concatenation of the last three outputs,
- `context_tail`: the last 4000 characters of the running context,
- `context_full`: the last 8000 characters of the running context.

Dialog experiments add role-conditioned observables such as the most recent user turn, most recent agent turn, rolling windows over user or agent turns, and the most recent turn pair.

All observable strings are embedded with `text-embedding-3-small`, producing 1536-dimensional vectors. One observable string produces one embedding vector. Embeddings are cached and L2-normalized before downstream analysis.

### 4.4 Projection spaces

For each observable-specific embedding matrix, we compute joint projections over the full point cloud:

- PCA-2 for density estimation and visualization,
- PCA-10 for clustering and most quantitative metrics,
- PCA-50 as a pre-reduction stage for t-SNE,
- t-SNE-2 for visualization only.

PCA is always fit jointly over all points for a given observable, never per trajectory or per family, so that coordinates remain comparable across runs and conditions.

### 4.5 Metric battery

We use the following metrics.

**Recurrence.** For a trajectory \(z_0, \dots, z_{T-1}\), recurrence measures the fraction of nonlocal step pairs within a distance threshold.

**Dwell.** After clustering PCA-10 with K-means, dwell statistics summarize run lengths within a cluster.

**Basin score and basin entry.** The target basin is defined by the dominant late-window cluster. Basin score is the fraction of late-window points in that cluster; basin entry is the first step at which the trajectory enters it.

**Late recurrence and exit-return.** These distinguish loose recurrent behavior from stable basin residence.

**Lyapunov-style ensemble spread.** We estimate finite-time contraction or expansion from the singular values of run ensembles indexed by family and initial condition.

**Sharpness dimension.** We use the participation ratio of the singular spectrum as an effective dimensionality measure.

**Periodicity.** Lag-distance autocorrelation identifies oscillatory structure, especially period-2 behavior.

**Dispersion and drift.** These summarize contraction, expansion, and centroid motion over time.

**Basin predictability.** A multinomial logistic regression predicts the late-time basin from the state at early step \(k\), producing an accuracy curve over time.

### 4.6 Baselines

We compare recursive runs against three baselines:

- **time-shuffled**, which destroys temporal order while preserving the point cloud;
- **no-feedback**, which samples each step from the seed alone;
- **independent regeneration**, which removes history dependence entirely.

A regime is treated as endogenous only when its diagnostic statistics differ meaningfully from all three baselines.

### 4.7 Perturbation protocol

To measure barrier structure, we inject text mid-trajectory under four conditions:

- control (no perturbation),
- neutral off-topic text,
- lorem/random word text,
- adversarial in-distribution text sampled from another basin.

In operator experiments, the injected text replaces the model output at the target step before the recurrence continues. In dialog experiments, the injected text replaces a user-turn output before the next agent response is generated.

We vary perturbation type, perturbation dose, and injection time. Switching is measured as a change in the final basin relative to a paired control trajectory.

### 4.8 Statistical procedures

We report bootstrap confidence intervals for trajectory-level metrics, Cohen’s \(d\) for recursive-vs-baseline effect size, permutation tests for condition differences, and cross-validated accuracy for basin predictability. In the significance gate used internally for regime assignment, a signal must exceed the baseline mean by at least two standard deviations and have at least medium effect size.

### 4.9 Geometric visualization toolkit

We estimate a smoothed density \(\rho(x)\) in PCA-2 and define
\[
V(x) = -\log(\rho(x) + \varepsilon).
\]
From this surface we extract local density peaks, compute Dijkstra geodesics between them, and treat the maximal potential along a path as a geometric barrier estimate. For selected experiments we also generate volumetric iso-density animations. These visualizations are descriptive tools used to compare basin geometry across regimes and perturbation conditions.

### 4.10 Pipeline and reproducibility

The full data flow is:
\[
\text{generate trajectories} \rightarrow \text{construct observables} \rightarrow \text{embed} \rightarrow \text{project} \rightarrow \text{analyze} \rightarrow \text{report}.
\]
Raw trajectories are stored in `steps.jsonl`. All downstream stages are deterministic given the cached trajectories and embeddings.

---

## 5. Results

### 5.1 Phase 0: pilot validation

The first pilot experiments established that recursive LLM loops already show nontrivial structure at small scale. In the append-and-continue default setting, we observed high basin scores together with weak recurrence, the signature that later became O1: a contractive regime. Extending the horizon preserved the basin, while removing clipping deepened it. This early result supported the basic existence claim of H1 and suggested that bounded-memory recursion is sufficient to produce stable basin-like behavior.

### 5.2 Phase 1: small-scale taxonomy

The next pilot phase varied content operator and update architecture. The resulting pattern was not a smooth spectrum but a set of qualitatively distinct regimes.

- **O1 (append + continue)** produced a contractive basin: high basin score, low recurrence, low effective dimension.
- **O2 (replace + paraphrase)** produced a clear oscillatory 2-cycle: low basin score, high recurrence, strong periodicity.
- **O3b (replace + summarize-and-negate)** produced a near-singular absorbing state: trivial recurrence, very low effective dimension, rapid convergence.
- **D1 (free dialog append)** produced a stylistic multi-basin: high basin concentration within style, but without the trivial contraction of O3.

Additional pilots explored boundary cases. Append + paraphrase yielded an intermediate regime that did not fit cleanly into the core taxonomy, and debate-style dialog produced partially structured multi-basin behavior that was more topic-dependent than D1.

These results support H2: regime is selected jointly by the content transformation and the update architecture, not by either factor alone.

### 5.3 Phase 2: publication-scale verification

Publication-scale runs preserved the phase-1 ordering across all major diagnostics. Contractive, oscillatory, absorbing, and multi-basin regimes remained clearly separable under larger sample sizes, and within-regime variability across prompt families and initial conditions remained much smaller than between-regime variability.

Basin predictability distinguished the regimes particularly clearly. O3 was almost perfectly predictable early, O2 showed high late-state predictability driven by its oscillatory structure, O1 remained moderately predictable, and D1 remained strongly but not trivially basin-structured. Ensemble contraction and effective dimension matched these qualitative assignments.

These large-scale replications support H4.

### 5.4 Phase 2b: temperature sensitivity

The temperature sweeps revealed that not all regimes respond to noise in the same way. O1 degraded smoothly as temperature increased: higher temperature broadened the contractive basin and reduced early predictability of the final state. D1, by contrast, remained comparatively stable across the same temperature range. This indicates that the style-based multi-basin regime is not simply a noisy version of O1. It is mechanically distinct.

### 5.5 Phase 3a: perturbation pilots

Perturbation pilots produced the clearest regime split.

- **O2 and O3** were almost fully perturbation-transparent: nearly any non-control intervention switched the final basin.
- **O1** resisted out-of-distribution perturbations strongly, but in-distribution adversarial text produced substantial switching.
- **D1** lay between these extremes.
- **D2**, introduced later, showed intermediate switching with stronger topic retention than free dialog.

The key conclusion is that resistance is regime-specific and perturbation-type-specific. Replace-mode loops are structurally fragile because the perturbation becomes the entire next state. Append-mode loops average perturbations into a growing context and therefore exhibit meaningful barrier structure.

### 5.6 Phase 3b: dose-response

Dose sweeps sharpened this picture.

For D1 under neutral perturbation, switching saturated at very small doses. This is consistent with a style-driven basin: once the interaction style is perturbed coherently, the trajectory can easily reconfigure.

For O1, the dose-response split by perturbation type. Neutral or lorem text stayed near the natural drift floor across all tested doses, while adversarial in-distribution text produced a graded switching curve. The approximate 50%-switching point occurred around 150 tokens. This is the clearest quantitative barrier-height result in the paper.

### 5.7 Phase 3c: injection-time sweep

Injection-time sweeps showed different temporal barrier profiles across regimes. D1 hardened with age: late injection was less effective than earlier injection, suggesting that stylistic basins sharpen over time. O1, by contrast, showed little systematic dependence on injection time, consistent with a contractive averaging process over accumulated context.

### 5.8 Phase 3d: structured dialog drill-down (D2)

The drill-down dialog regime differs from D1 because the user role is constrained to deepen the current topic rather than range freely. Mid-trajectory adversarial injections produced substantial switching, but a meaningful fraction of trajectories returned toward the original specialization line. This supports the idea that D2 adds **content gravity** on top of dialog-style basin structure.

D2 therefore extends the taxonomy: it is not merely “another dialog condition,” but a distinct regime in which conversational structure stabilizes topic continuation.

### 5.9 Cross-experiment aggregation

Cross-experiment aggregation confirmed the consistency of the findings. Basin predictability, temperature sensitivity, perturbation switching, dose-response, and basin hardening all produced aligned summaries across the main regimes. The separation between append-mode resistance and replace-mode transparency was especially robust.

### 5.10 Geometric results

The geometric analyses on \(V(x)\) agreed qualitatively with the perturbation experiments. Replace-mode perturbations often flattened or merged basin structure, while O1 retained distinct peaks separated by nontrivial ridges. D1 exhibited shallow, stylistic geometry with smaller effective barriers. The qualitative agreement between geometric barrier estimates and switching thresholds supports the usefulness of the visualization toolkit, even though it should not be overinterpreted as a physical free-energy derivation.

---

## 6. Discussion

### 6.1 A taxonomy of nudged recursive regimes

The main conceptual result is that recursive LLM loops are best understood not as one phenomenon, but as a family of regimes selected by the interaction between \(P_\theta\), the content operator \(f\), and the nudge \(\mathcal N\).

A simple factorization captures the core operator results:

| content operator | append | replace |
|---|---|---|
| content-preserving | contractive basin | oscillatory 2-cycle |
| content-degrading | weak collapse / sink-drift | absorbing collapse |

Dialog introduces an additional structural axis. Free dialog yields stylistic multi-basin behavior; structured drill-down adds topic-selective stabilization.

### 6.2 Why append resists and replace capitulates

Append mode preserves history. A perturbation becomes one component of an accumulating context and must compete with the pre-existing trajectory. Replace mode erases history. The perturbation becomes the entire next state, so switching is the default outcome rather than the exception.

This mechanism-level distinction explains why O1 exhibits measurable in-distribution barriers while O2 and O3 are nearly perturbation-transparent.

### 6.3 D2 as content-anchored dialog

Free dialog is largely stabilized by style. Drill-down dialog adds an explicit recursive instruction to keep moving down a topic branch. This makes the loop partially content-anchored. The resulting regime is still multi-basin, but not purely stylistic.

### 6.4 What the geometric view adds

The effective-potential view should be interpreted cautiously. It does not derive the dynamics from first principles. Nevertheless, it provides a useful geometric summary of where trajectories spend time and how basins connect. The fact that geometric barrier estimates track perturbation-derived switching thresholds suggests that the density landscape is not merely decorative: it captures real differences in regime structure.

### 6.5 Practical implications

For practitioners:

- If stability matters, append-mode continuation is the safest choice.
- If oscillatory behavior is useful, replace-mode paraphrase produces it cleanly.
- If collapse is desired for compression or sink-finding, replace-mode summarize-and-negate converges quickly.
- If one wants variety under shared style or role structure, dialog architectures provide structured multi-basin behavior.
- If one wants topic retention in dialog, drill-down style prompts introduce measurable content gravity.

For researchers, the broader implication is that recursive LLM loops should be analyzed as dynamical objects with measurable basin structure rather than as idiosyncratic prompt artifacts.

---

## 7. Limitations

This study has several important limitations.

First, all experiments use a single generation model, `gpt-4o-mini`. The taxonomy may generalize, but exact barrier heights and geometries are likely model-specific.

Second, all embedding analyses use one embedding family, `text-embedding-3-small`. We checked projection robustness within that family, but did not test alternative embedding models.

Third, all loops use a bounded 12,000-character context. Although pilot no-clipping results suggest that some basins deepen without clipping, the full taxonomy has not been replicated in unbounded or much-longer-context conditions.

Fourth, all prompts and trajectories are English and relatively short per step. We do not know how the regimes change under multilingual or essay-length generation.

Fifth, system prompts remain fixed within trajectories. Prompt drift may interact strongly with basin stability.

Sixth, the effective-potential and geodesic analyses depend on density estimation, smoothing, and projection choices. They are useful geometric summaries, not model-derived physical quantities.

Seventh, the D2 regime was tested at smaller scale than the main publication regimes, so its status as a distinct regime should be regarded as provisional pending larger replication.

---

## 8. Future work

Several directions follow directly from these findings.

1. **Cross-model replication.** The most immediate next step is to test whether the same taxonomy appears in other model families.
2. **Long-output recursion.** Essay-length outputs may broaden, deepen, or fragment the basin structure found here.
3. **Mixed update rules.** Hybrid nudges such as append-then-summarize or replace-after-paraphrase may interpolate between the identified regimes.
4. **Publication-scale D2.** The drill-down regime should be scaled to the same family/IC/run counts as the main publication regimes.
5. **Richer dialog topologies.** Debate, role-play, multi-party planning, and adversarial questioning may each define their own regime class.
6. **Perturbation as diagnostics.** The dose-response methodology could become a standard tool for characterizing deployed LLM agents.
7. **Safety and alignment.** Fine-tuning and refusal training may create new basins or alter barrier structure in ways that are measurable with this framework.

---

## 9. Methods appendix

### 9.1 Metric definitions

Recurrence is computed by thresholding nonlocal pairwise distances within a trajectory after excluding a temporal neighborhood around each step.

Basin score is defined from K-means labels in PCA-10 by taking the dominant late-window cluster and measuring late-window occupancy.

The Lyapunov-style spectrum is computed from the singular values of centered run ensembles at each step.

Sharpness dimension uses the participation ratio:
\[
\mathrm{SD}_t = \frac{(\sum_k \sigma_k)^2}{\sum_k \sigma_k^2}.
\]

Basin predictability trains a multinomial logistic regression to predict the late-time basin from the state at an earlier step.

### 9.2 Perturbation mechanics

In operator-mode runs, the perturbation replaces the model output at the injection step before the context update is applied. In dialog runs, perturbation occurs on the user turn, after which normal alternation resumes.

### 9.3 Clustering and projection stability

K-means with a fixed number of clusters is used for basin analysis because it provides a stable and interpretable partition across experiments. PCA stability is enforced by joint fitting and fixed random seeds.

### 9.4 Rendering pipeline

Static plots are generated deterministically from cached projections and metrics. Selected animations are rendered in parallel from cached geometric representations.

---

## 10. Reproducibility statement

The pipeline is designed so that every analysis downstream of trajectory generation can be reproduced from cached artifacts. Raw trajectories are stored in `steps.jsonl`. Observables, embeddings, projections, metrics, and reports are all generated through documented deterministic stages. The primary computational costs come from generation and embedding; the remaining analysis can be rerun locally from cached data.

A typical rerun path is:

\[
\texttt{steps.jsonl} \rightarrow \texttt{embeddings.npy} \rightarrow \texttt{projections} \rightarrow \texttt{metrics} \rightarrow \texttt{plots/report}.
\]

The pipeline is therefore suitable both for large-scale reproduction and for incremental extension with new experiments.

---

## 11. Conclusion

Recursive LLM loops are not adequately described as generic repetition, collapse, or “prompt weirdness.” When formalized as bounded stochastic dynamical systems, they exhibit a small number of reproducible regimes selected jointly by the nudge architecture and the content operator. These regimes can be detected in representation space, quantified with recurrence, basin, oscillation, and contraction metrics, and stress-tested with controlled perturbations.

The most important empirical distinction is between append-mode and replace-mode recursion. Append-mode continuation produces a contractive basin with measurable in-distribution barriers. Replace-mode operators produce transparent or absorbing dynamics in which perturbations readily overwrite the future trajectory. Dialog introduces additional structure, including style-conditioned basins and topic-preserving drill-down behavior.

More broadly, these results suggest that recursive LLM behavior should be studied through the language of state, update rule, basin structure, and perturbation—not only through one-step prompt-response evaluation. That perspective provides both a taxonomy and a measurement toolkit for future work on agents, self-conditioning systems, and long-horizon language-model dynamics.

---

## Acknowledgments

This rewrite preserves the scientific content of the original manuscript while aligning the presentation with an explicit state–generator–nudge formalism.

## References

Please reconcile the final bibliography against the original manuscript’s reference list before submission. This rewrite retains the cited conceptual lineage but does not attempt to fully reformat the reference section.
