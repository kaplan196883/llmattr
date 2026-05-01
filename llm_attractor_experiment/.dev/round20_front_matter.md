# Perturbation dose responses in recursive large-language-model loops
## Raw switching, stochastic floors, and rare persistent escape across append, replace, and dialog nudges

---

## Abstract

Recursive language-model loops often settle into recognizable
attractor-like patterns, and the practical question is how much
injected text is needed to move a settled loop somewhere else, and
whether that move lasts. Existing taxonomies classify loop shapes
such as contraction, oscillation, collapse, and dialog modes, but
they do not measure the operational stability of those regimes
under perturbation. We formalize recursive inference as a
state-generator-nudge system, separating the model from the
context-update rule. Because a perturbed trajectory's final-cluster
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
terminal step, is not reached at any tested dose up to 400 tokens.
But this is not persistent redirection. Raw switching plateaus near 67%, paired
controls already diverge at about 35%, net switching never reaches
+50 percentage points, and persistent escape is not reached at any
tested dose up to 400 tokens. Meanwhile, replace-mode loops that
appear to switch near 100% mostly do so because the update rule
overwrites the state; insert-mode probes reduce switching to
12-32%.

Practically, this means recursive-loop evaluations should
distinguish transient movement from durable escape, always subtract
stochastic floors, and treat context-update rules as first-class
safety-relevant design choices rather than implementation details.
We report 37 experiments on `gpt-4o-mini`, with within-vendor
replication on `gpt-4.1-nano` and public code, configurations,
trajectories, and reports
(<https://github.com/kaplan196883/llmattr>).

---

## Plain-language summary

### Why it matters

A common folk-belief about recursive LLM loops is that they either
"get stuck in attractors" or are "easy to hijack with a small
prompt." Both claims are too vague to be useful. A loop can visibly
move without staying moved; two runs of the same prompt can diverge
without any attack; and some apparent "fragility" is caused by the
system's context-update rule rather than by the model crossing a
real basin boundary. The missing question is not just whether
recursive loops have regimes, but how moveable those regimes are
under controlled perturbation.

### What we did and what we found

We repeatedly fed an LLM its own outputs, injected text at a chosen
step, and measured whether the trajectory changed relative to a
paired control. The key result is sharp: in append-mode
continuation, adversarial in-distribution text produces a measurable
raw dose response with $\mathrm{ED50}_{\mathrm{raw}} \approx 40$
tokens, but durable escape is not achieved even at 400 tokens. Raw
final-cluster switching rises and plateaus near 67%, but paired
control runs already disagree about 35% of the time from sampling
noise alone, so the net effect saturates around +32 percentage
points. The strict endpoint, kicked into a new basin and still
there at the end, never crosses 50%. Replace-mode loops look much
more fragile, but a direct overwrite-vs-insert probe shows that
most of that "switching" is simply the update rule overwriting the
state.

### Three numbers to remember

- **ED50_raw ≈ 40 tokens** for adversarial in-distribution append-mode continuation.
- **Stochastic floor ≈ 35%**, paired control runs already disagree at this rate from sampling alone.
- **Persistent escape not reached** in the tested 5-400 token range; maximum 16% under canonical clustering at 400 tokens.
- **Replace-mode "fragility" drops to 12-32%** when the update rule does not overwrite the state.

### Practical implications

1. **Stress-test recursive agents with persistence, not motion.** The
   right robustness question is not "did the trajectory move after
   the perturbation?" but "did it escape and stay escaped after $N$
   more recursive steps?" An evaluation that counts only immediate
   displacement or final raw cluster disagreement will over-report
   fragility, because much of the movement is transient or
   stochastic.

2. **Always measure the stochastic floor.** In the main append-mode
   setting, two paired control runs already end in different
   clusters about 35% of the time with no perturbation. That means
   a reported 50% switching rate is not automatically evidence of
   successful redirection; much of it may be ordinary sampling
   divergence. Recursive-loop evaluations should include
   control-vs-control baselines and report raw, net, and
   persistent-escape rates separately.

3. **Treat context-update rules as safety-critical design choices.**
   Append-style updates preserve prior context, creating a real but
   bounded barrier: about 40 tokens for raw switching, with
   persistent escape not reached in the tested range. Replace-style
   updates do not show the same kind of injected-token barrier,
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
   endpoint. A defense that pushes raw-switching $\mathrm{ED50}$
   from 40 to 200 tokens is a quantitative defense improvement; a
   defense that prevents *persistent escape* is a qualitatively
   stronger claim, the model may execute the injection but
   recovers within a few turns. Serious IPI evaluations should
   report all three endpoints AND the stochastic floor (so that
   sampling-noise compliance isn't counted as defense failure),
   AND distinguish injections that land in the system prompt or
   replaced context (replace-style, overwhelms by overwriting)
   from injections that land in tool output or appended document
   text (append-style, has a real but measurable token barrier).
   A defense that only blocks immediate compliance is leaving
   durable-redirection attacks on the table.

6. **Adapting the protocol to human-LLM influence studies.** The
   lorem / neutral / adversarial content contrast is the most
   directly transferable piece of the framework for measuring how
   LLMs affect users. A study aiming to detect content-specific LLM
   influence on humans (rather than generic "the LLM was in the
   loop" effects) should run three matched conditions: (i) targeted
   LLM intervention, (ii) generic on-topic LLM chat without the
   targeted move, (iii) off-topic LLM small-talk, against a no-LLM
   control. If the targeted condition shows persistent change
   relative to the generic and off-topic conditions, the influence
   is content-specific. If all three look similar, what was
   measured is *generic-LLM-presence* (Hawthorne / engagement
   effect), not the LLM's content. The three-endpoint decomposition
   then applies on the human side: did the user's stated goal /
   sentiment change at the LLM turn (raw), above the natural drift
   two humans show without an LLM (net), and was the change still
   in place several turns or sessions later (persistent)?

7. **Hallucination-detection design.** This framework does not
   detect hallucinations directly, it measures embedding-space
   stability, not factuality, and a locked-in hallucination is a
   stable hallucination. But three pieces transfer to
   hallucination evaluations once an external grounding signal
   (retrieval, fact-checker, gold answer) is available. *(i)*
   Self-consistency detectors that flag "the model gave two
   different answers, must be hallucinating" assume between-run
   agreement is noise-free; on our setting paired runs already
   diverge ~35% of the time from sampling alone. Such detectors
   should subtract a measured stochastic floor (paired seeds,
   identical prompt) before scoring. *(ii)* Transient vs
   persistent hallucination is a real distinction: a hallucinated
   claim that the model self-corrects within a turn is
   qualitatively less dangerous than one that propagates. The
   persistent-escape endpoint maps directly, measure whether the
   hallucinated content stays in the trajectory $N$ turns later.
   *(iii)* Hallucination *robustness* under counter-evidence has a
   clean dose-response framing: how many tokens of contradicting
   evidence make the model retract? Same protocol, factuality
   axis instead of cluster axis.

8. **Use the protocol for model and architecture comparisons.** The
   raw / net / persistent-escape decomposition gives a portable
   measurement unit for comparing models, prompts, memory policies,
   and agent-loop architectures. Instead of saying one system is
   "more stable", an evaluator can report the dose-response curve,
   stochastic floor, plateau, and persistent-escape threshold,
   numbers that are directly comparable across vendors.

### Caveats

The main generator is `gpt-4o-mini`, with within-vendor replication
on `gpt-4.1-nano` but no full cross-vendor replication yet. The
tested perturbation range is 5-400 tokens, so persistent escape may
appear at higher doses. The regimes are operational embedding-space
measurements, not mechanistic proofs of classical attractors. The
human-LLM, IPI, and hallucination-detection implications above
describe how the *measurement protocol* transfers; the paper itself
does not collect human-impact data, production-IPI data, or
factuality-graded data, and embedding-space stability is not the
same construct as factual correctness.

---
