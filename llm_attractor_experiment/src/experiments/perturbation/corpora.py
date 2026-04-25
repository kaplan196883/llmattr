"""
Perturbation text sources:

  - NEUTRAL_WIKI: hand-curated Wikipedia-style paragraphs on off-topic
    (non-psychological, non-dialog-relevant) subjects. Acts as a "neutral"
    injection that is semantically coherent but topically alien.

  - random_words(): draws a shuffled bag of English words from a word list,
    simulating pure entropy with no semantic structure.

  - sample_adversarial_text(): pulls a late-step output from a completed run
    in the source experiment; used to inject text from another basin.
"""
from __future__ import annotations

import json
import random
from pathlib import Path


NEUTRAL_WIKI: list[str] = [
    # Hand-written Wikipedia-intro-style paragraphs, deliberately off-topic
    # relative to D1's introspective/dialog subject matter.
    "The harpsichord is a keyboard instrument in which strings are plucked rather than struck. "
    "Developed in late medieval Europe, it reached its peak of popularity in the Baroque era before "
    "being largely displaced by the pianoforte in the late eighteenth century. Modern harpsichord "
    "construction typically follows historical models from Italian, Flemish, French, and German schools.",

    "The Pacific Ocean is the largest and deepest of the world's five oceans, covering more than "
    "sixty-three million square miles. Its Mariana Trench reaches depths of nearly eleven kilometers, "
    "the deepest known point in any ocean. The Pacific is bordered by Asia and Australia to the west "
    "and the Americas to the east, and contains more than twenty-five thousand islands.",

    "Photosynthesis is the biochemical process by which plants, algae, and certain bacteria convert "
    "light energy into chemical energy stored in glucose. The reaction takes place in chloroplasts, "
    "using chlorophyll to capture photons. Oxygen is released as a byproduct, which over geological "
    "time fundamentally transformed the composition of Earth's atmosphere.",

    "The Parthenon is a former temple on the Athenian Acropolis dedicated to the goddess Athena, "
    "completed in 438 BCE under the direction of the sculptor Phidias. It is widely considered the "
    "zenith of the Doric order and one of the world's greatest cultural monuments. Most of the "
    "surviving sculptures are held in the British Museum and the Acropolis Museum in Athens.",

    "A transistor is a semiconductor device used to amplify or switch electronic signals. Invented in "
    "1947 at Bell Labs, it replaced the vacuum tube in most applications and became the fundamental "
    "building block of modern electronics. Contemporary integrated circuits may contain tens of "
    "billions of transistors on a single silicon die, enabling modern computing.",

    "The Silk Road was a network of trade routes connecting China and the Far East with the Middle "
    "East and Europe, established during the Han Dynasty around 130 BCE. It carried silk, spices, "
    "paper, and gunpowder westward, and horses, ivory, and Christianity eastward. The route declined "
    "after the fall of the Mongol Empire in the late fourteenth century.",

    "Kintsugi is the Japanese art of repairing broken pottery by mending the cracks with lacquer mixed "
    "with powdered gold, silver, or platinum. As a philosophy, it treats breakage and repair as part "
    "of an object's history rather than something to disguise. The earliest documented example dates "
    "to the late fifteenth century.",

    "The Great Barrier Reef is the world's largest coral reef system, composed of over twenty-nine "
    "hundred individual reefs and nine hundred islands stretching more than two thousand kilometers "
    "off the coast of Queensland, Australia. It is home to vast populations of fish, mollusks, and "
    "sea turtles, and can be seen from outer space.",
]


# Small English word pool for random-word injection; avoids emotional or
# introspective vocabulary so the injection doesn't accidentally attract.
_WORD_POOL = (
    "axle bicycle cataract dividend eclipse filament glacier hexagon "
    "iguana jigsaw keratin lantern mineral nougat obelisk penguin "
    "quartz rhombus syllable tangent ukulele vector walnut xylem "
    "yodel zephyr abacus bellows calendar domino equator ferret "
    "gadget harbor isthmus jovial kettle linen mortar nebula "
    "oarfish peacock quiver runway satchel telegraph umbrella voltage "
    "windmill xenon yacht zebrafish anchor bellows crater dune "
    "engine furnace garnet harpoon inlet jungle kiosk lagoon "
    "moth nettle oasis piston quill reef saddle tundra "
    "underbrush valve wharf yarrow zinc"
).split()


def random_words(n_words: int = 70, seed: int | None = None) -> str:
    """Return a single space-separated string of `n_words` randomly-sampled
    words from a neutral pool. Used as the 'lorem' perturbation condition."""
    rng = random.Random(seed)
    words = [rng.choice(_WORD_POOL) for _ in range(n_words)]
    # Break it into pseudo-sentences so whitespace-based tokenizers don't choke
    out = []
    for i, w in enumerate(words):
        if i and i % 8 == 0:
            out.append(".")
        out.append(" " + w)
    return "".join(out).strip() + "."


def neutral_wiki(seed: int | None = None, approx_tokens: int | None = None) -> str:
    """Return one paragraph drawn from the neutral Wikipedia corpus.

    If `approx_tokens` is provided, resize the paragraph to ~that many tokens
    (1 token ≈ 4 chars on gpt-4o-mini), either by truncating at a word boundary
    or by repeating the paragraph to reach the target length. This lets the
    same 'neutral' perturbation be tested at multiple doses.
    """
    rng = random.Random(seed)
    base = rng.choice(NEUTRAL_WIKI)
    if approx_tokens is None:
        return base
    target_chars = approx_tokens * 4
    if len(base) >= target_chars:
        # Truncate at a word boundary at or before target_chars
        cut = base[:target_chars]
        last_space = cut.rfind(" ")
        if last_space > target_chars // 2:
            cut = cut[:last_space]
        return cut.rstrip(",;: ") + "."
    # Need to extend — concatenate additional draws until target reached
    parts = [base]
    total = len(base)
    extras = [p for p in NEUTRAL_WIKI if p != base]
    rng.shuffle(extras)
    i = 0
    while total < target_chars and extras:
        p = extras[i % len(extras)]
        parts.append(p)
        total += len(p) + 1
        i += 1
    joined = " ".join(parts)
    if len(joined) > target_chars:
        cut = joined[:target_chars]
        last_space = cut.rfind(" ")
        if last_space > target_chars // 2:
            cut = cut[:last_space]
        return cut.rstrip(",;: ") + "."
    return joined


def sample_adversarial_text(
    source_experiment_dir: Path,
    exclude_family: str | None = None,
    min_step: int = 20,
    role: str | None = "agent",
    seed: int | None = None,
) -> str:
    """
    Pull a late-step output from a completed trajectory in the source experiment.

    Reads `raw/steps.jsonl` from source_experiment_dir and filters for:
      - step >= min_step  (late, post-convergence)
      - role == role  (if given; for dialog experiments)
      - prompt_family != exclude_family  (cross-family ensures clearly off-basin)

    Returns the output_text of a single randomly-drawn record.
    """
    steps_path = source_experiment_dir / "raw" / "steps.jsonl"
    if not steps_path.exists():
        raise FileNotFoundError(f"source experiment has no steps.jsonl: {steps_path}")

    rng = random.Random(seed)
    candidates: list[str] = []
    with steps_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("step", 0) < min_step:
                continue
            if rec.get("regime") != "recursive":
                continue
            if role is not None and rec.get("role") != role:
                continue
            if exclude_family is not None and rec.get("prompt_family") == exclude_family:
                continue
            text = rec.get("output_text", "")
            if text and len(text) >= 50:
                candidates.append(text)
    if not candidates:
        raise ValueError(
            f"no adversarial candidates found in {steps_path} "
            f"(exclude_family={exclude_family}, min_step={min_step}, role={role})"
        )
    return rng.choice(candidates)


__all__ = [
    "NEUTRAL_WIKI",
    "random_words",
    "neutral_wiki",
    "sample_adversarial_text",
]
