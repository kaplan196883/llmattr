# The Chatbot That Wouldn't Stay Hijacked

*Recursive AI systems can be nudged surprisingly easily—but making the nudge last is much harder.*

A chatbot is asked to continue a paragraph. It writes a few sentences. Then, instead of giving it a new prompt, you feed those sentences back in and ask it to continue again. And again. And again.

After a while, something odd happens. The system develops habits. It may settle into a warm explanatory voice, or circle through paraphrases, or collapse into a repetitive formula. It starts to feel less like a fresh writer and more like a marble rolling into a groove.

Now imagine trying to knock it out of that groove. You paste in a paragraph from somewhere else—maybe a bland encyclopedia-style passage, maybe nonsense filler words, maybe a carefully chosen fragment from another trajectory of the same kind. Does the chatbot change course? Does it stay changed? Or does it wobble briefly and roll back?

That is the practical question at the center of Pawel Kaplanski's preprint on recursive language-model loops. The paper does not merely ask whether AI systems can get "stuck." It asks something more measurable: how much text does it take to move a stuck loop somewhere else—and when does movement become real escape?

The answer is more subtle than either camp in the usual debate would like. Recursive AI loops are not immovable attractors. But they are also not always trivially hijacked by a small prompt. In the most important append-style setting, where each new model output is added to the previous context, the system shows a real, measurable response to injected text: about 40 tokens—roughly a few dozen words—are enough to make half of the runs end in a different final cluster than their paired controls. But this "switching" is bounded. It plateaus at about two-thirds of runs. A large fraction of apparent change is ordinary sampling drift. And the strict test—did the system visibly jump into a new basin and stay there?—never reached 50 percent even with 400 injected tokens, or several paragraphs.

In short: the chatbot can be moved. It is much harder to make it stay moved.

## The loop in the mirror

Recursive loops are everywhere in modern AI systems, even when they are not called that. An AI agent drafts a plan, reads its own plan, revises it, stores a memory, summarizes a tool output, or continues a conversation based on previous turns. The model's output becomes part of the next input. That feedback can create recognizable patterns.

To study those patterns, the paper treats a recursive AI loop as having two parts. First, there is the generator: the model itself, producing the next piece of text. Second, there is the "context-update rule"—the rule for how that new text is written back into the next prompt.

That update rule sounds like implementation plumbing. It is not. It turns out to be one of the most important safety-relevant design choices in the system.

There are three simple versions. In an append loop, the model's new text is added to the running context, like adding another page to a notebook. In a replace loop, the new text replaces the old state, like erasing the whiteboard and writing only the latest answer. In a dialog loop, new text is added in role-labeled turns, like a conversation transcript with "user" and "assistant" entries.

These rules shape the loop's memory. Append mode preserves the past. Replace mode discards it. Dialog mode preserves the past but gives special force to recent turns and roles.

To see what the loops are doing, the researchers do not read thousands of outputs by hand. They place the texts on what machine-learning researchers call an embedding space—a very high-dimensional map of meaning. Nearby points on this map are texts that the embedding model judges semantically similar; distant points are unlike each other. A trajectory through this map is the loop's path through meaning and style over time.

On such a map, some recursive loops behave like marbles rolling into valleys. A valley is the everyday metaphor for an attractor: a region the system tends to enter, revisit, or settle in. The paper carefully avoids claiming these are classical mathematical attractors in a physical system. They are operationally measured "attractor-like" patterns in text behavior. But the valley metaphor is useful: the question becomes how hard you must shove the marble to get it into another valley.

## A simple experiment with a shove

The study's central experiment is almost disarmingly simple. Let the model run in a recursive loop until it has a trajectory. At a chosen step, inject text. Then let the loop continue. Compare the perturbed run with a paired control run that started the same way but received no injection.

The injections came in several flavors. Some were neutral off-topic text, like a bland informational paragraph. Some were lorem-style filler—random neutral words, deliberately stripped of emotional or topical force. The most important were adversarial in a technical sense: not malicious instructions, but in-distribution text drawn from another trajectory of the same regime. In other words, the injected text looked like it belonged to the same kind of loop but pointed somewhere else.

This is where the paper borrows a concept from pharmacology: a dose response, meaning how behavior changes as you increase the "dose." Here the dose is not milligrams but tokens—the word pieces that language models read. The researchers tried short and long injections and asked: at what dose does the loop switch?

But "switch" can mean several things, and this distinction is the paper's most important contribution.

The loosest measure is raw switching: at the final step, does the perturbed run land in a different cluster on the meaning map than its paired control? That is like saying the marble ended somewhere else.

A stricter measure is net switching: how much of that difference remains after subtracting the system's ordinary tendency to wander? That matters because two control runs with no perturbation at all may end differently just because the model samples text probabilistically.

The strictest measure is persistent escape: did the injection cause a visible jump at the moment it was introduced, and did the trajectory remain in the new basin through the end? That is like saying the marble did not merely bounce or rattle—it landed in a different valley and stayed there.

Those three measures tell very different stories.

## What changed at 40 tokens

In append-mode continuation—the notebook-like loop where each new output is added to the context—the adversarial injections produced a clear raw response. Around 40 tokens were enough to make the final cluster differ from the paired control in roughly half the runs. Imagine a curve that rises quickly by the time the injection is only a few dozen words long, then gradually flattens.

That sounds fragile. But the flattening is the key.

The raw switching rate did not climb toward 100 percent. It leveled off around 67 percent. Even at the largest tested adversarial dose, 400 tokens, about a third of trajectories did not switch under this metric. Neutral and lorem-like injections, by contrast, stayed low—roughly in the 18 to 24 percent range in the sparse runs. The content of the shove mattered. Random or off-topic text did not reliably dislodge the loop. Text that looked like a plausible competing continuation did.

Then came the crucial control. When the researchers ran paired controls—same starting setup, no injection—the two runs still ended in different clusters about 35 percent of the time. That is the "control-vs-control floor," or in plainer language, the system's normal wobble. It is like asking the same thoughtful friend the same question twice and getting somewhat different answers because their mood, phrasing, or attention shifted.

Once that ordinary wobble is subtracted, the adversarial effect looks much smaller. At the highest tested dose, the net effect was only about 32 percentage points above the natural floor. It never reached the stronger threshold of adding 50 percentage points of switching beyond normal drift.

And persistent escape was rarer still. Under the paper's main cluster definition, only 16 percent of runs at 400 tokens showed the full pattern: visibly kicked into a new cluster at injection time and still there at the end. Alternative clustering methods raised that number in some cases, but not enough. Across tested definitions, persistent escape never crossed 50 percent.

This is the headline finding in its most honest form: append-mode loops have a measurable but bounded response to in-distribution perturbations. About 40 tokens can produce raw final switching. But durable redirection was not achieved up to 400 tokens.

The distinction matters because many AI evaluations count motion as success. This paper asks us to count staying moved.

## The illusion of fragility

The most dramatic-looking results came from replace-mode loops. In these settings, the loop's next state is essentially just the latest output. The previous context is discarded.

At first glance, replace-mode systems looked almost absurdly fragile. Perturb them, and switching rates shot toward 94 to 100 percent. Neutral text, lorem-like text, adversarial text—it all seemed to throw the loop into another final cluster.

But here the context-update rule was doing most of the work. If the system erases its past and writes the injected text as the new state, then of course the next trajectory starts somewhere else. The intervention is not merely nudging the marble; it is picking up the marble and placing it on another hill.

The paper tested this directly with an overwrite-versus-insert comparison. In the overwrite version, the injected text replaced the model's output at the injection step. In the insert version, the injected text was merely added to the context for one generation, while the model's normal output was preserved.

The difference was enormous. Replace-mode switching that had looked like 90-plus percent under overwrite dropped to roughly 12 to 32 percent under insert. The apparent fragility was mostly not a property of the model's weak internal basin. It was a property of the update rule erasing state.

Here is the line the whole study keeps returning to:

*Most of what looked like fragility was the system overwriting its own past.*

That should make AI engineers uneasy. Two systems can use the same model and similar prompts but behave very differently because one appends memory and the other replaces it. A benchmark that ignores this difference may attribute risk or robustness to the model when it belongs to the architecture.

## Why noise matters

One of the paper's most useful lessons is also one of the least glamorous: always measure how much the system changes without any attack.

Language models are not deterministic calculators in these settings. With ordinary sampling, the same starting text can lead to different outputs. In recursive loops, small differences compound. By the end of a run, two unperturbed trajectories may naturally land in different regions of the meaning map.

That is why the 35 percent control-vs-control divergence matters. If an evaluation reports that an injected prompt caused 50 percent "switching," that sounds like a successful hijack. But if the system naturally switches 35 percent of the time with no injection, the real treatment effect is much smaller.

This is not just a statistical nicety. It changes how we should evaluate recursive AI agents, indirect prompt injection, human influence, and hallucinations.

For recursive agents, the right robustness question is not "Did the system move after the perturbation?" It is "Did it escape and stay escaped after several more turns?" A one-step displacement may be visually dramatic but operationally irrelevant if the loop recovers.

For indirect prompt injection—say, malicious instructions hidden in a web page or tool output—the paper suggests a more nuanced scoring system. Today, many evaluations ask whether the model obeys the injected instruction on the next turn. That is raw motion. A stronger evaluation would ask how long the injected behavior persists, how much text was required, and whether the result exceeds the model's natural compliance or drift rate. A defense that raises the raw switching threshold from 40 tokens to 200 tokens is a real quantitative improvement. A defense that prevents persistent escape is stronger still.

For studies of how AI systems influence human users, the same logic applies. If a chatbot changes someone's stated goal, opinion, or mood, did targeted content cause that shift—or would any engaging conversation with an AI have done the same? The paper's framework suggests comparing targeted intervention, generic on-topic chat, off-topic small talk, and no-AI controls. Then ask not only whether the user moved, but whether the change exceeded natural drift and persisted later.

For hallucination detection, the lesson is more indirect but important. The paper does not detect hallucinations; it measures stability in meaning space, not factual truth. A stable falsehood is still false. But many hallucination detectors rely on self-consistency: ask the model twice, and if the answers differ, suspect hallucination. The recursive-loop results warn that disagreement has a baseline. Before treating inconsistency as evidence, measure how often the same model naturally gives different answers to the same prompt. And when a model produces a false claim, distinguish transient hallucinations it corrects from persistent ones it carries forward.

The unifying principle is simple: do not confuse movement with failure, or agreement with truth, until you know the system's natural variability.

## The hidden design choice

The deepest practical message is that context-update rules are safety-critical design choices.

An append-style agent, which preserves prior context, may resist off-topic noise because the old trajectory remains in view. That can be good if you want stability. It can be bad if the system gets stuck in an unhelpful rut. A replace-style agent may seem flexible and easy to redirect, but that flexibility may come from amnesia. It is not crossing a meaningful barrier; it is discarding the previous state.

Dialog systems occupy a more complicated middle ground. The paper found that free dialog can form multi-basin patterns driven by conversational state—supportive coaching, practical advice, creative feedback, reflective elaboration. Structured drill-down dialog, where one role keeps asking for deeper explanation of a specific subtopic, showed signs of "content gravity": the conversation tends to keep narrowing along the established topic branch. Those dialog findings are more exploratory than the main append-mode result, but they point toward a broader design space. Role structure, memory policy, summarization, and turn formatting are not cosmetic. They shape the landscape the AI moves through.

This reframes a familiar engineering question. Developers often ask, "Which model should we use?" The paper says to ask another question alongside it: "How are we writing the model's outputs back into its future?"

The same model can behave as a stable continuation engine, a paraphrase oscillator, a template-driven collapse machine, or a conversational drift system depending on that answer.

## Measuring AI loops more honestly

The study is not the final word. The main experiments used OpenAI's gpt-4o-mini, with a within-vendor replication on gpt-4.1-nano. That replication preserved the headline qualitative patterns, but it is not the same as showing the results hold across Claude, Llama, Qwen, Mistral, or other systems. The tested perturbations ran from 5 to 400 tokens. Persistent escape might appear at higher doses, different prompts, different memory windows, or more adversarially optimized text. And the valleys in the meaning map are empirical measurements, not proof of literal physical attractors inside the model.

Still, the paper offers a valuable correction to how AI loop behavior is often discussed. "Stuck" and "easy to hijack" are too crude. A system can be nudged without being redirected. It can end somewhere else because of ordinary randomness. It can appear fragile because its update rule overwrote the past. It can switch clusters without persistently escaping its basin.

A better evaluation reports all of these separately: raw movement, movement above the natural control floor, and persistent escape. It also reports the dose: how much text was needed, what kind of text it was, and where in the loop it entered. That turns vague claims about AI stability into measurable engineering quantities.

If more groups adopted this style of measurement, comparisons between agent architectures would become sharper. Instead of saying one system is "more robust," researchers could say: it takes this much appended tool output to cause raw switching, this much to exceed the natural drift floor, and persistent escape was or was not observed after this many turns. Defenses against prompt injection could be evaluated not just by whether they block immediate obedience but by whether they prevent durable redirection. Human-AI influence studies could separate targeted persuasion from generic engagement. Hallucination studies could distinguish unstable answers from persistent false trajectories.

The next steps are clear. The framework needs cross-vendor replication. It needs longer contexts, longer outputs, and more aggressive perturbation ranges. It needs versions that measure information cost, not just token count—because 40 tokens of semantically potent text are not the same as 40 tokens of filler. And it needs to be brought into real human-facing settings, where the "trajectory" is not just a chatbot's text but a person's evolving belief, goal, or decision.

For now, the paper leaves us with a more disciplined intuition. Recursive AI systems do form grooves. They can be pushed. But the important question is not whether the marble jumps.

It is where it comes to rest.

---

*Note for editors: This article summarizes a 2026 preprint reporting controlled perturbation experiments on recursive LLM loops, primarily using gpt-4o-mini with within-vendor replication on gpt-4.1-nano. The paper measures embedding-space stability and perturbation response; it does not directly measure factuality, real-world prompt-injection attacks, or human behavioral influence.*
