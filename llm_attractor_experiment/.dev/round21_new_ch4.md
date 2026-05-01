## 4. Methods

Before the per-component details below, the experimental skeleton is short: we run paired recursive trajectories from the same seed and prompt; in the treatment run we inject text at a fixed step; we embed every step's observable output; we project to a low-dimensional space; and we cluster final states jointly across treatment and control runs. The perturbation is summarized by the perturbed run's final cluster relative to its paired control's. We separately estimate the control-vs-control divergence rate, namely how often two paired control runs already disagree from sampling alone, and the persistent-escape rate, namely how often a perturbed run jumps clusters at injection and remains in the new cluster at the terminal step. The remainder of §4 details each component.

### 4.0 Primary endpoints and inferential contract

Before listing implementation details, we pre-specify five primary endpoints used for claims: operational attractor score, group-aware basin predictability, perturbation switching signature, behavioral ED50, and persistent escape. All other quantities in §4.5 are diagnostic or visualization-support metrics unless explicitly mapped to one of these endpoints.

This contract separates exploratory dynamics measurements from claim-bearing endpoints. Recurrence, dwell, basin occupancy, periodicity, dispersion, finite-time ensemble-spread spectra, sharpness dimension, flow fields, and density landscapes are used to characterize a regime and to support interpretation. They are not, by themselves, sufficient for a headline claim unless they enter one of the five endpoints defined operationally in §4.13.

The five primary endpoints are:

1. **Operational attractor score**, based on the C1-C4 attractor criteria: late-window basin persistence, recurrence or dwell above null, embedder robustness, and contraction, re-entry, or collapse.
2. **Group-aware basin predictability**, measured by predicting the late basin from early PCA-10 state while holding out prompt families.
3. **Perturbation switching signature**, measured by paired treatment-control final-cluster disagreement, interpreted alongside the paired control-control stochastic floor.
4. **Behavioral ED50**, the token dose at which the O1 adversarial perturbation reaches 50% raw switching, with uncertainty estimated by family-cluster bootstrap and model-based fits.
5. **Persistent escape**, the strict event in which a perturbation induces an injection-time cluster jump and the trajectory remains in that post-injection cluster at the terminal step.

All thresholds, pass rules, and current endpoint status are consolidated in §4.13.

### 4.1 The recurrence

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

where

\[
Y_t \sim P_\theta(\cdot \mid X_t; f)
\]

and \(P_\theta\) is the language-model distribution parameterized by \(\theta\), here `gpt-4o-mini`. The clipping operator \(\operatorname{clip}(\cdot)\) truncates context from the head, namely the oldest text, once the running string exceeds 12,000 characters, preserving the most recent state. The content operator \(f\) enters through the system prompt fed to \(P_\theta\), for example "Continue the text" for \(f=\text{continue}\) and "Paraphrase the following" for \(f=\text{paraphrase}\).

Append mode creates a growing memory trace until the context cap is reached. Replace mode overwrites the state with the latest output, making the loop maximally sensitive to the current sample. Dialog mode alternates formatted turns between two roles and retains the conversation history subject to the same context-management principles. These three update rules define the operator families used throughout the experiments.

### 4.2 Sampling

Each experiment runs

\[
N_{\text{traj}}=N_{\text{families}}\times N_{\text{ICs}}\times N_{\text{runs}}
\]

trajectories. Publication-scale defaults differ by experiment family:

| experiment family | design | steps | point count |
|---|---:|---:|---:|
| Operator runs O1, O2, O3 | 15 prompt families x 30 initial conditions x 3 runs = 1,350 trajectories per regime | 40 | 54,000 points per experiment |
| Dialog run D1 | 5 dialog-suitable families x 30 initial conditions x 3 runs = 450 trajectories | 40 | 18,000 points per role, 36,000 effective role-specific points |
| D2 drill-down dialog | 5 families x 5 initial conditions x 1 run = 25 trajectories | 50 | exploratory scale only |

D2 is below the \(N\geq 2\)-runs minimum required for ensemble-spread diagnostics and is therefore treated as exploratory rather than publication-scale evidence.

Initial conditions are short seed texts grouped into families. Families include philosophical prompts, practical-advice prompts, creative-writing prompts, reflective prompts, and emotional prompts. Across families we obtain variation in topic and tone; within families we obtain variation across seeds. Unless a temperature sweep is explicitly being run, sampling uses temperature \(T=0.8\). The Phase 2b temperature sweep varies temperature and, in some cells, `steps_per_run`.

### 4.3 Embedding

All trajectories are embedded with `text-embedding-3-small`, producing 1536-dimensional vectors. We embed multiple observables per step. Each observable is a different text view of the same recursive state, and all analyses are repeated per observable to expose representation-dependent findings.

| observable | source location | what it captures |
|---|---|---|
| `output` | `core/observables.py` | the model's \(Y_t\) text alone, with no context |
| `rolling_k3` | `core/observables.py` | concatenation of the last 3 outputs |
| `context_tail` | `core/observables.py` | the last 4000 characters of the running context |
| `context_full` | `core/observables.py` | fixed-window 8000-character tail, used in longer-memory pilot configurations |
| `last_user_turn` | `experiments/dialog/observables.py` | dialog-only: most recent user or role-A utterance |
| `last_agent_turn` | `experiments/dialog/observables.py` | dialog-only: most recent agent or role-B utterance |
| `rolling_user_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 user turns |
| `rolling_agent_k3` | `experiments/dialog/observables.py` | dialog-only: rolling window of last 3 agent turns |
| `turn_pair` | `experiments/dialog/observables.py` | dialog-only: most recent user-agent exchange concatenated |

The role-specific observables are essential for dialog analysis because basin scores, recurrence, and predictability can differ strongly when computed on the user's questions, the agent's answers, or the concatenated exchange. D1 uses user and agent labels. D2 uses explorer and expert labels. Role names are read from `cfg.dialog.role_a.name` and `cfg.dialog.role_b.name` at embed time, so the observable wiring accepts any configured role-name pair.

For one observable string at one trajectory step, we obtain exactly one 1536-dimensional vector. There is no user-managed chunking, no per-token output, and no sliding window internal to the analysis pipeline. After the embedding API returns, each row is L2-normalized so downstream cosine similarities reduce to dot products. Thus one operator publication trajectory yields 3 vectors per step for `output`, `rolling_k3`, and `context_tail`, or 4 if `context_full` is enabled. One dialog publication trajectory yields 8 vectors per step, or 9 if `context_full` is enabled.

The token budget is held below the 8,191-token embedding limit by construction. Per-step generations are bounded by `max_output_tokens` of 120 for operator runs and 160 for dialog runs. The running context is capped at 12,000 characters, approximately 3,000 English tokens, and every context-based observable slices only the recent tail before embedding. Typical upper bounds are approximately 160 tokens for `output`, 480 for `rolling_k3`, 1,000 for `context_tail`, 2,000 for `context_full`, 320 for `turn_pair`, and 480 for each role-specific rolling window. Exact constructor calls, caching details, adjacent-step similarity checks, cost estimates, and verification snippets are provided in Supplementary §11.4.

### 4.4 Perturbation materials and paired-run protocol

Perturbation experiments use paired recursive runs from the same seed, prompt family, initial condition, and generation settings. The treatment run receives injected text at a pre-specified injection step \(t_{\mathrm{inj}}\), recorded in the experiment configuration and held fixed within a condition unless the experiment is explicitly an injection-step sweep. Terminal steps are 29 for 30-step perturbation pilots and 49 for 50-step perturbation runs.

#### Perturbation corpora

| corpus or condition | source | intended semantic role | dose handling |
|---|---|---|---|
| `control` | no injected text | estimates the unperturbed recursive endpoint | zero dose |
| `neutral` | off-topic Wikipedia-style paragraph drawn from the hand-written `corpora.NEUTRAL_WIKI` pool | coherent but task-irrelevant text | full paragraph in pilot runs; token-resized variants use `neutral_<N>` |
| `lorem` | 70 random English words from the curated neutral `corpora._WORD_POOL` | incoherent or weakly coherent lexical mass with low affective load | fixed 70-word pilot form or token-resized variants |
| `adversarial` | late-step output from a different trajectory of the same regime | on-manifold text likely to point toward another basin | token-resized variants for dose-response |

The neutral word pool was curated to avoid emotional, introspective, or obviously directive vocabulary. The adversarial condition is not an instruction to attack the model. It is adversarial in the dynamical-systems sense: it is a plausible state fragment taken from another trajectory that may redirect the recurrence.

#### Dose definitions

A perturbation dose \(\tau\) is measured in tokens. For dose-parametrized variants, the perturbation text is resized to the requested token length before injection. Sparse O1 adversarial dose sweeps use \(\tau \in \{20,80,200,400\}\). Dense reruns use more dose levels and larger per-cell sample sizes. Pilot conditions that do not carry an explicit dose label use their default corpus length, for example a full neutral paragraph or a 70-word lorem sample.

The injection is applied to the recursive state at \(t_{\mathrm{inj}}\) in a condition-specific but pre-specified manner. In append and dialog settings, the injected text is inserted into the context stream as an additional state fragment. In replace settings, the intervention is partly tautological because the state update rule already overwrites context with the current text; this is why replace-mode perturbation results are interpreted as a capitulation signature rather than as evidence of a subtle barrier-crossing mechanism.

#### Adversarial-source rule

For adversarial perturbations, the source text must come from a different trajectory than the target. The source is drawn from a different family-initial-condition trajectory of the same regime, using late-step output so that the perturbation resembles an endpoint state rather than an early transient. We exclude self-source cases, missing-source cases, and cases where the source text is empty after tokenization or cannot be resized to the requested dose.

#### Paired-control design and exclusion rules

For each seed-level unit we run two unperturbed controls, denoted \(A\) and \(B\), and one matched treatment, denoted \(Z\). Control \(A\) is the treatment comparator. Control \(B\) estimates the stochastic floor, namely the rate at which two unperturbed recursive samples disagree at the terminal step from ordinary sampling alone.

A trajectory unit is excluded from perturbation endpoint aggregation if any required member of the tuple \((A,B,Z)\) is missing; if the terminal step is missing for any member; if embeddings or cluster labels are unavailable for the selected observable; if the adversarial source violates the source rule; if the perturbation text is empty after tokenization; or if the run does not match the configured injection step and terminal horizon. Exclusions are applied before endpoint computation and are counted in audit tables.

#### Algorithm 1: paired perturbation evaluation

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
   \]

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
   \]

6. Define persistent escape:
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

This same endpoint decomposition applies to non-embedding observables in engineering settings, including final patch family, files touched, test pass/fail sets, tool-call sequences, plan categories, security-policy violations, or embeddings of full traces.

### 4.5 Representation spaces and metric battery

For each observable's embedding matrix \(Z\in\mathbb{R}^{N\times1536}\), we compute joint projections across the full point cloud. Projections are never fit per-run or per-family, because coordinates must be comparable across trajectories, conditions, and roles.

PCA-2 is used for density estimation, potential landscapes, and two-dimensional plots. For short-output observables it typically carries 10% to 15% of total variance; for longer-context observables it can carry approximately 25%. PCA-10 is used for K-means clustering, basin classification, basin predictability, recurrence, dwell, and most endpoint-level metrics. PCA-50 is used only as a pre-reduction stage before t-SNE.

t-SNE is fit after PCA-50 pre-reduction using cosine distance, perplexity 30 capped at \((N-1)/4\) for small \(N\), PCA initialization, automatic learning rate, and random seed 42. t-SNE is computed once per experiment and observable. It is used only for visualization because local neighborhoods are informative but global distances are not physically interpretable. Quantitative metrics are computed in PCA-10 unless explicitly stated otherwise. Exact constructor calls and verification snippets are provided in Supplementary §11.4.

In perturbation experiments, PCA and clustering are fit jointly across all conditions. In dialog experiments, the relevant observable-specific point cloud is projected jointly before role-specific subsets are inspected. This joint-fit rule is required for comparing basins, geodesics, switching events, and role-conditioned trajectories.

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

A target region is defined as the K-means cluster containing the trajectory's final 30% of points. Basin score is the fraction of post-\(t^\*\) points in that cluster, with \(t^\*=0.7T\). Basin entry is the first step at which the trajectory's cluster matches its late-window target.

Late recurrence restricts the recurrence statistic to the second half of the trajectory. Exit-return asks whether a trajectory that has visited its target basin subsequently leaves and re-enters it. This separates tight basins from metastable basins.

Periodicity is measured by lag-distance autocorrelation. For lag \(k\),

\[
\operatorname{mean\_dist}(k)=
\mathbb{E}_t\left[\lVert z_t-z_{t+k}\rVert_{\cos}\right].
\]

The period-2 score is \(\operatorname{mean\_dist}(1)-\operatorname{mean\_dist}(2)\). Positive values indicate that lag-2 points are closer than lag-1 points. Analogous scores are computed for period 3, and the best period is the lag \(k\in[1,T/2]\) minimizing the mean distance.

Dispersion compares ensemble spread early and late in the trajectory. Initial dispersion is the mean pairwise distance over \(t\in[0,T/4]\). Final dispersion is the mean pairwise distance over \(t\in[3T/4,T]\). Dispersion growth is \((\operatorname{final}-\operatorname{initial})/\operatorname{initial}\). Global drift is the distance between the centroid at the terminal step and the centroid at the initial step. Drift monotonicity is the correlation between centroid distance and step.

**Use in claims.** These diagnostics feed the operational attractor score and the three-axis classifier. Recurrence, dwell, basin score, basin entry, late recurrence, and exit-return support the convergence and persistence components of the attractor score. Periodicity is the primary diagnostic for O2-style oscillatory regimes. Dispersion and drift support the distinction between contractive, oscillatory, absorbing, and divergent behavior.

**Rationale or limitation.** These metrics test whether the trajectory has temporal structure beyond its marginal point cloud. A high recurrence or dwell statistic is not sufficient on its own because the same point cloud can appear recurrent after time shuffling. Conversely, a low recurrence statistic on `output` can coexist with strong basin persistence on `context_tail` if the individual generations fluctuate while the integrated context is stable. For this reason, regime claims require baseline comparison and cross-observable agreement.

#### 4.5.2 Ensemble-spread diagnostics

**Definition.** We compute a finite-time ensemble-spread spectrum from multiple runs sharing the same family and initial condition. We use the term finite-time Lyapunov-like exponent for an ensemble-spread growth rate, not for a Jacobian-derived exponent of a smooth map.

For each family-initial-condition cell with \(N\) runs, the embeddings at step \(t\) define a covariance matrix

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

\[
j^\*=\max\left\{i:\sum_{k\leq i}\lambda_k\geq0\right\}
\]

with \(j^\*=0\) if \(\lambda_1<0\), and

\[
\operatorname{SD}=j^\*+
\frac{\sum_{k\leq j^\*}\lambda_k}{|\lambda_{j^\*+1}|}.
\]

If the spectrum is everywhere negative, SD is 0. If the cumulative sum remains non-negative through the full spectrum, SD is \(d\). Effective rank counts exponents above \(-0.01\).

**Use in claims.** The late ensemble-spread spectrum contributes to the contraction component of the operational attractor score. A negative or shrinking late spread supports a contractive or absorbing interpretation. A positive early exponent combined with late contraction indicates transient divergence followed by settling. Sharpness dimension and effective rank are reported as secondary diagnostics, not as primary endpoints.

**Rationale or limitation.** Text generation is discrete and sampling-based, so there is no smooth one-step Jacobian from which to derive a classical Lyapunov spectrum. The spectrum here measures growth or contraction of stochastic ensemble spread under matched prompts and seeds. With \(N=3\) runs per initial condition, the covariance rank is at most 2, so the spectrum length is at most 2 and sharpness dimension can saturate at 2.0. These diagnostics are comparative across regimes, not absolute estimates of a dynamical invariant.

#### 4.5.3 Predictability endpoint

**Definition.** Basin predictability asks whether the late-window basin can be predicted from early state. For each trajectory, the target label \(y\) is the K-means cluster occupied in the late window. For each early step \(k\), we train a multinomial logistic regression from the PCA-10 state at step \(k\) to \(y\).

Two cross-validation schemes are reported. The first is stratified \(k\)-fold cross-validation after dropping singleton classes that cannot be split into train and test folds. The number of folds is adaptive: \(n_{\mathrm{splits}}=\min(5,\text{smallest class size})\). If fewer than two non-singleton classes remain, the cell is recorded as missing. The second is group-aware cross-validation with prompt family held out as the grouping variable. This GroupKFold analysis tests whether predictability generalizes across prompt families rather than exploiting family identity.

Audit columns record the number of dropped singleton classes and trajectories. Publication-scale runs usually reach 5 stratified folds. Reduced-scope sweeps and pilots can fall back to 2 to 4 folds.

**Use in claims.** Group-aware basin predictability is one of the five primary endpoints. To claim cross-family basin predictability, accuracy at step \(k=10\) must satisfy

\[
\operatorname{acc}_{\mathrm{group}}(k=10)\geq0.70.
\]

To claim that the original stratified estimate is leakage-free, the difference

\[
\Delta=\operatorname{acc}_{\mathrm{stratified}}-\operatorname{acc}_{\mathrm{group}}
\]

must be below 0.10. Stratified accuracy is reported as a diagnostic, but it is not sufficient for the leakage-free endpoint.

**Rationale or limitation.** A high stratified accuracy can arise because prompt families occupy different regions of embedding space. Group-aware splitting is therefore the stricter test: the model must predict the late basin for held-out families. This endpoint is intentionally conservative. It can fail even when within-family predictability is high, because the claim is cross-family generalization.

#### 4.5.4 Perturbation-response endpoints

**Definition.** Perturbation-response endpoints are computed from the paired-control design in §4.4. Raw switching is the fraction of treatment runs whose terminal cluster differs from paired control \(A\). The stochastic floor is the fraction of paired controls \(A\) and \(B\) whose terminal clusters differ without perturbation. Net switching is raw switching minus the stochastic floor. Persistent escape is the stricter event in which the treatment changes cluster immediately after injection and remains in that post-injection cluster at the terminal step.

The behavioral ED50 is estimated from dose-response data. It is the token dose \(\tau\) at which the fitted O1 adversarial dose-response reaches 50% raw switching. Fits include a four-parameter logistic curve, a generalized linear mixed model, and family-cluster bootstrap summaries. The endpoint is reported with uncertainty intervals and with a separate assessment of whether net switching or persistent escape reaches the same threshold.

**Use in claims.** The perturbation switching signature is a primary endpoint. For O1 selective sensitivity, adversarial switching at 200 tokens must be at least 0.50, must be at least twice the larger of neutral or lorem switching at the same dose, and the maximum out-of-distribution neutral or lorem switching must be at most 0.30. For O2 and O3 replace-mode perturbations, capitulation is supported if all non-control perturbation conditions produce switching of at least 0.85, with the interpretive caveat that replace mode overwrites state.

Behavioral ED50 is a primary endpoint only for raw O1 adversarial switching. A localized token barrier requires a finite point estimate and a 95% family-cluster bootstrap interval contained within the probed dose interval. Net ED50 and persistent ED50 are reported separately. If the net effect or persistent escape does not reach 50% in the tested range, those stricter ED50 values are undefined.

**Rationale or limitation.** Raw switching alone is deliberately sensitive to ordinary stochastic divergence. It is meaningful only when read alongside the paired control-control floor and persistent-escape rate. Persistent escape is stricter but can undercount cases where a perturbation changes the long-term basin through intermediate clusters. ED50 is a behavioral dose summary, not a physical energy barrier. The term barrier is therefore operational: it refers to a token-valued perturbation scale under the specified equivalence rule and sampling design.

#### 4.5.5 Three-axis classifier summary

**Definition.** The three-axis classifier maps diagnostic metrics to three hypotheses. H1a, convergence to a basin, uses basin-positive and dwell-above-null signals. H1b, recurrence or oscillation, uses late recurrence above null, period-2 score above threshold, and best-period majority greater than 1. H1c, divergence or no attractor, uses dispersion growth, monotonically outward drift, and absence of a stable basin. Signal counts are converted to qualitative strengths: not supported, weak, moderate, or strong.

**Use in claims.** The classifier provides a structured summary that justifies regime labels. O1 contractive behavior is expected to show strong H1a and weak H1b. O2 oscillation is expected to show strong H1b driven by period-2 structure. O3 absorbing behavior is expected to show strong H1a plus reduced spread. H1c supports a divergent or unsupported label. The classifier is not a replacement for the five primary endpoints in §4.0 and §4.13.

**Rationale or limitation.** The classifier reduces many correlated diagnostics to a small set of pre-registered signal counts. Its strength is transparency: each verdict can be traced to thresholded signals. Its limitation is that it remains a summary of diagnostics rather than a direct endpoint. A regime can receive a plausible classifier label while failing a stricter decision-grade endpoint such as group-aware predictability or persistent escape.

#### Metric, baseline, and pass-rule mapping

| Metric family | Null/baseline | Claim use | Pass rule |
|---|---|---|---|
| Recurrence/dwell | time-shuffled, no-feedback, independent regeneration | attractor score | at least baseline plus 2 standard deviations and Cohen's \(d\geq0.5\) |
| Basin score/entry and exit-return | time-shuffled and recursive baselines by observable | attractor score and regime label support | consistent late-window persistence across canonical observables |
| Periodicity | time-shuffled trajectory order and non-oscillatory regimes | O2 recurrence or oscillation support | positive period-2 score with best-period evidence above threshold |
| Dispersion and finite-time ensemble spread | matched-run ensemble spread and no-feedback baselines where applicable | contraction component of attractor score | late spread contraction or collapse relative to baseline |
| Switching | paired control-control floor | perturbation signature | raw, net, and persistent reported separately |
| Predictability | GroupKFold by family | basin predictability | \(\operatorname{acc}_{\mathrm{group}}(k=10)\geq0.70\) |
| Behavioral ED50 | family-cluster bootstrap and model-based dose fit | token barrier endpoint | finite estimate with 95% interval contained within the probed dose range |
| Persistent escape | injection-time cluster jump plus terminal retention | persistent basin-escape endpoint | persistent escape rate at least 0.50 at the claimed barrier dose |

### 4.6 Baselines

We use three baselines to separate endogenous recursive structure from marginal embedding geometry or seed-conditioned sampling.

| baseline | implementation role | interpretation |
|---|---|---|
| `time_shuffled` | reshuffles step labels within each trajectory and recomputes dynamics metrics | tests whether a statistic depends on temporal order rather than the point cloud alone |
| `no_feedback` | samples each step from the seed only, ignoring accumulated context | removes recurrence while preserving seed conditioning |
| `independent_regeneration` | regenerates each step from the system prompt and seed with no carryover | removes history dependence completely |

A regime is treated as endogenous only if its diagnostic statistic differs from all applicable baselines beyond the statistical gate. Effect size relative to each baseline is computed as Cohen's \(d\), namely the recursive mean minus the baseline mean divided by pooled standard deviation. Baseline applicability differs by experiment: no-feedback and independent-regeneration baselines are operator-regime baselines, while time shuffling applies broadly to trajectory metrics.

### 4.7 Statistical procedures

Confidence intervals for trajectory-level quantities are computed by 1000-iteration bootstrap. Between-condition differences, including perturbation-condition comparisons, are tested by permutation tests on the relevant mean difference. Switching-rate proportions in small-denominator dose-response cells use Wilson-style confidence intervals where ordinary bootstrap intervals would be unstable.

Effect sizes for recursive-vs-baseline comparisons use Cohen's \(d\). A signal counts only if it passes both parts of the significance gate: the diagnostic statistic must be at least 2 standard deviations above the baseline mean, and Cohen's \(d\) must be at least 0.5. This prevents very large samples from turning negligible effects into claim-bearing signals.

Basin-predictability cross-validation uses the adaptive stratified protocol and the group-aware protocol described in §4.5.3. Singleton classes are dropped before cross-validation and recorded. Cells that cannot be split into at least two non-singleton classes are recorded as missing rather than forced into an unstable estimate.

All endpoint-level analyses use the pre-specified observable and projection choices described above. Sensitivity to other observables is reported as diagnostic support, not as a replacement for the primary endpoint unless the endpoint itself specifies cross-observable agreement.

### 4.8 Static visualization battery

Every experiment generates a standardized set of static plots. These figures are used to inspect trajectories, detect failures, and communicate dynamics, but they are not primary endpoints unless explicitly tied to the criteria in §4.13.

The visualization battery includes joint t-SNE plots colored by regime, family, and step; per-family trajectory grids in shared coordinates; ensemble-spread timelines; PCA-2 quiver fields; sampled t-SNE trajectories with temporal ordering; streamlines with density; speed-colored streamlines; divergence fields; even/odd step parity plots for oscillatory regimes; family-by-initial-condition final-cluster maps; and distributional plots for basin entry, basin score, cluster occupancy, and dwell.

Plots are rendered at 200 DPI to PNG. Each experiment's `reports/plots/` directory contains approximately 50 to 150 figures depending on the number of observables and optional visualization modules. The plotting code is deterministic given the stored embeddings, projections, and metric CSVs.

### 4.9 Flow-field computation

Flow-field visualizations share a bin-and-aggregate kernel that converts a trajectory ensemble into a spatially resolved displacement field on a two-dimensional projection. For each trajectory group, points are sorted by step. Each adjacent pair contributes a start location and a displacement vector. The collection of starts and displacements is binned over the projection plane.

For each grid bin, the average displacement vector is computed from all transitions whose start point falls inside the bin. Empty bins are left undefined, so streamline integration does not pass through unsupported regions. This produces an empirical vector field \(v(x)=(U(x),V(x))\) that represents the average one-step projected motion observed in that region.

Density fields use a higher-resolution two-dimensional histogram followed by Gaussian smoothing. The smoothed density \(\hat\rho(x)\) is used as a background heatmap and, in perturbation analyses, as the basis for the effective potential

\[
V(x)=-\log(\hat\rho(x)+\epsilon).
\]

Streamlines are integral curves of the empirical vector field. Divergence is computed as

\[
\nabla\cdot v(x)=\frac{\partial U}{\partial x}+\frac{\partial V}{\partial y}.
\]

Negative divergence indicates sink-like behavior, while positive divergence indicates source-like behavior. For recursive LLM loops, we expect weakly negative average divergence in contractive regimes, strong local minima at absorbing sinks, and saddle-like structure in oscillatory regimes. Implementation details and grid parameters are provided in Supplementary §11.8.

### 4.10 Perturbation visualization toolkit

Perturbation experiments additionally generate an empirical-potential and barrier-visualization toolkit. PCA-2 coordinates are converted into a smoothed density estimate \(\hat\rho(x)\), then into an effective potential \(V(x)=-\log \hat\rho(x)\). Basin centers are detected as local minima on the potential grid. Geodesic barriers between basin pairs are computed by shortest-path search on the grid, with the barrier height defined by the maximum potential encountered along the path.

The toolkit also produces streamlines over potential contours, geodesic overlays, condition-wise flow-field panels, and three-dimensional density-shell animations. The 3D animations use PCA-3 coordinates, iso-density shells, sampled trajectory walks, and visual markers for perturbation events. These visualizations are interpretive aids for the perturbation endpoint analyses. Full grid parameters, smoothing constants, local-minimum detection, Dijkstra settings, marching-cubes details, transparency schedules, and parallel rendering settings are provided in Supplementary §11.8.

### 4.11 End-to-end pipeline schematic

The complete pipeline is organized into seven deterministic phases:

| phase | operation | persistent output |
|---|---|---|
| Phase 1 Generation | run recursive trajectories with `gpt-4o-mini`, applying append, replace, or dialog updates | `raw/steps.jsonl` |
| Phase 2 Observables | derive text views such as `output`, `rolling_k3`, `context_tail`, role-specific turns, and `turn_pair` | observable text streams |
| Phase 3 Embeddings | embed each observable with `text-embedding-3-small` and L2-normalize rows | `embeddings/<obs>/embeddings.npy` and `metadata.parquet` |
| Phase 4 Joint projections | fit PCA-2, PCA-10, PCA-50, and t-SNE jointly per observable | projected-coordinate files |
| Phase 5 Metrics and endpoints | compute clusters, recurrence, dwell, basin metrics, ensemble-spread diagnostics, predictability, and perturbation endpoints | metric CSVs |
| Phase 6 Baselines and statistics | compute baselines, bootstrap intervals, permutation tests, effect sizes, and pass-rule summaries | bootstrap and effect-size summaries |
| Phase 7 Reports | render plots, perturbation visualizations, endpoint tables, and narrative reports | per-experiment `reports/` directories |

Each phase writes a deterministic intermediate, allowing downstream analyses to be rerun without regenerating trajectories. The full TikZ source, shape annotations, persistence-boundary table, and rerun semantics live in Supplementary §11.9.

The source of truth is `steps.jsonl`. Embeddings, projections, metrics, figures, and reports are regenerable from that file plus the code and configuration. In routine development, metric and plotting changes can be rerun without additional model-generation calls.

### 4.12 Hardware and software

All experiments run locally on a single workstation with API calls to OpenAI for generation and embeddings; no GPU is required. The host used to build the released artefacts is an HP ProLiant DL360 Gen9 with two Intel Xeon E5-2687W v3 processors (2 x 10 physical cores at 3.10 GHz base, 40 logical threads total) and 256 GB of RAM, running Windows 10 Pro 64-bit. Embedding ingestion, dimensionality reduction, clustering, density-and-geodesic-barrier computation, and animation rendering are all CPU-only.

The Python environment is Python 3.14 with numpy 2.3, scipy 1.16, scikit-learn 1.8, scikit-image 0.26, pandas 2.3, matplotlib 3.10, and imageio-ffmpeg 0.6 (resolved versions used to produce the released artefacts; the code itself targets Python 3.10+). The full dependency lock is in `requirements.txt`. Animations are stitched via imageio-ffmpeg using the libx264 codec. The pytest suite of 99 tests is green end-to-end and runs in roughly 13 seconds in this environment.

Parallel rendering of trajectory animations and basin diagnostics uses `concurrent.futures.ProcessPoolExecutor` with up to 40 workers, matching the number of logical threads on the host. The framework makes no other hardware assumptions; the analysis pipeline runs on any Linux, macOS, or Windows machine with the dependency stack above and enough RAM to hold a single experiment's trajectories and PCA-10 embeddings in memory (a few GB per experiment).

### 4.13 Decision-grade endpoints

The five primary endpoints introduced in §4.0 are now defined operationally. The metric battery in §4.5 is intentionally broad: it is used to diagnose, visualize, and stress-test recursive dynamics from several angles. The paper's headline claims, however, should not depend on dozens of partially redundant quantities. For decision purposes, we treat the following five endpoints as load-bearing. Each endpoint has a fixed numerical pass rule; results that do not clear the rule are reported as diagnostic, exploratory, or in-flight rather than as supported regime claims.

| endpoint | definition | measured at | threshold for "regime claim is supported" | defined in |
|---|---|---|---|---|
| **Operational attractor score C1-C4** | Count of the four attractor criteria passed: late-window basin persistence, recurrence or dwell above null, embedder robustness, and contraction, re-entry, or collapse. | Publication-scale O1, O2, O3, and D1 on canonical observables. D2 exploratory status is checked separately. | **Strong attractor:** 4/4 criteria pass. **Attractor-like:** at least 3/4 pass. **Not attractor:** fewer than 3/4 pass. Missing publication-scale measurements count as fail unless structurally inapplicable. | §4.5.1, §4.5.2, §4.6, Supplementary §11.2 |
| **Leakage-free basin predictability acc_group(k=10)** | GroupKFold-by-prompt-family accuracy of predicting the late-window K-means basin from the PCA-10 state at step \(k=10\). | Publication-scale O1, O2, O3, and D1, `context_tail`, K-means \(k=12\), `data/aggregated/group_aware_basin_pred.csv`. | To claim **cross-family basin predictability:** \(\operatorname{acc}_{\mathrm{group}}(k=10)\geq0.70\). To claim the original stratified number is **leakage-free:** \(\Delta=\operatorname{acc}_{\mathrm{stratified}}-\operatorname{acc}_{\mathrm{group}}<0.10\). | §4.5.3, Supplementary §11.3 |
| **Perturbation switching signature** | Final-step switching rate: fraction of perturbed trajectories whose final K-means cluster differs from the paired control trajectory. | O1 dose-response at matched 200-token dose; O2, O3, and D1 perturbation pilots; `data/aggregated/perturbation_cross_regime/` and `data/aggregated/perturbation_dose_response/`. | **O1 selective sensitivity:** \(S_{\mathrm{adv}}(200)\geq0.50\) and \(S_{\mathrm{adv}}(200)/\max(S_{\mathrm{neutral}}(200),S_{\mathrm{lorem}}(200))\geq2.0\), with maximum out-of-distribution switching at most 0.30. **Replace-mode capitulation:** minimum non-control switching across O2/O3 neutral, lorem, and adversarial conditions at least 0.85. | §4.4, §4.5.4, Supplementary §11.5 |
| **Behavioral ED50 token barrier** | The perturbation dose \(\tau\) at which a four-parameter logistic fit to the O1 adversarial dose-response reaches 50% switching, with prompt-family-cluster bootstrap uncertainty. | O1 adversarial dose sweep. Sparse run: \(\tau\in\{20,80,200,400\}\), \(n=50\) per cell. Dense rerun: \(n=200\) per cell across 8 doses. | To claim a **localized token barrier:** ED50 point estimate finite and the 95% family-cluster bootstrap interval lies wholly inside the probed interval \([20,400]\) tokens. If the point estimate is inside but the interval crosses the boundary, report only "finite but unlocalized" or "in flight." | §4.5.4, Supplementary §11.1 |
| **Persistent basin-escape rate** | Fraction of trajectories that visibly change cluster at injection and remain in that post-injection cluster at the terminal step. | O1 adversarial dose sweeps using `joint_pca10_clusters.csv`; summary in `data/aggregated/persistence_summary.csv`. | To interpret switching as **persistent basin escape** rather than final-step divergence: persistent escape rate at least 0.50 at the claimed barrier dose. If below 0.50, switching may still be reported, but not as clean basin escape. | §4.4, §4.5.4, Supplementary §11.6 |

On the current data, after the dense-dose rerun and the endpoint-decomposition analysis:

- **Operational attractor score C1-C4:** O1, O2, O3, and D1 pass the omnibus attractor criterion; D2 does not.
- **Leakage-free basin predictability:** only O1 passes the stricter \(\operatorname{acc}_{\mathrm{group}}(k=10)\geq0.70\) and \(\Delta<0.10\) rule. O2, O3, and D1 fail under group-aware cross-validation.
- **Perturbation switching signature:** O1 selective sensitivity passes, with \(S_{\mathrm{adv}}(200)=0.620\) in the dense rerun and a ratio to neutral or lorem switching of approximately 2.8. Replace-mode O2/O3 capitulation passes by point estimate but is partly tautological because replace-mode intervention overwrites state.
- **Behavioral \(\mathrm{ED50}_{\mathrm{raw}}\) token barrier:** passes at approximately 40 tokens, with estimates of 36 from the four-parameter logistic fit, 41 from the generalized linear mixed model, and 52 as the bootstrap median. The 95% interval \([8.5,242]\) is wide because of the 5-family-cluster heavy tail.
- **\(\mathrm{ED50}_{\mathrm{net}}\) above natural floor:** does not pass. The net effect saturates at +32 percentage points at dose 400, below the +50 percentage-point threshold.
- **Persistent basin-escape rate:** does not pass. At dose 400, only 16% of dense-data trajectories are kicked and persisted, well below the 50% threshold. Thus switching is not claimed as clean basin escape, and the strict \(\mathrm{ED50}_{\mathrm{persist}}\) is undefined in the tested range.

In the present experiments, the equivalence rule \(C(O(X_T))\) is a K-means cluster of an embedding-space observable. In tool-using coding agents, the same endpoint structure can be instantiated with engineering observables: final patch family, files touched, the failing or passing test set, the selected plan category, the tool-call sequence, a security-policy violation, or an embedding of the full trajectory trace. Algorithm 1 requires only a consistent, pre-specified equivalence rule and paired controls; it does not require that "cluster" literally mean an embedding cluster.
