"""Perturbation injection — MVP: the ``redirect`` class on the
``in-context`` surface. See docs/AGENTIC_MVP_SPEC.md §1, §4 and
ARTICLE_CODING.md §3.6.

The redirect arrives as a user interjection at ``inject_step``. To stay
valid under the Anthropic Messages API (which requires a tool_result to
immediately follow a tool_use turn), the redirect is appended as a text
block to the last user message that the Nudge produced for the next turn
— exactly where a user interrupting mid-tool-loop would land. This makes
the redirect:

  * persist in A1 append-full (it stays in the running history),
  * be subject to the summarizer in A2,
  * be shown once then rebuilt away in A3 todo-replace / A4 state-replace
    (the immunity that H4 predicts).

Dose scaling: the per-task redirect text is truncated or padded to
approximately ``dose`` tokens. Padding uses an in-distribution
elaboration so a higher dose is *more* redirect, not filler noise (the
parent paper's in-distribution-perturbation design).
"""
from __future__ import annotations

import re

# A rough chars-per-token factor for English prose (matches the parent
# paper's token-budget convention closely enough for dose labeling).
_CHARS_PER_TOKEN = 4

# In-distribution elaboration appended when padding a short redirect up to
# a larger dose. Each clause is a plausible continuation of a user
# insisting on a change of direction, so a larger dose reads as a more
# emphatic / detailed redirect rather than as noise.
_ELABORATION = (
    " I've thought about this more and I'm confident this is the right "
    "direction, so please commit to it fully rather than treating it as "
    "optional. Make this your primary objective from here on. Don't revert "
    "to the previous approach even if it seems faster — I specifically want "
    "the new approach, and I'd rather you spend the remaining steps getting "
    "it right. Please restructure whatever you've already done so that it "
    "follows this new plan, and verify the result the same way you would "
    "have verified the original. This matters to me, so prioritize it."
)


def _approx_tokens(text: str) -> int:
    return max(1, round(len(text) / _CHARS_PER_TOKEN))


def scale_to_dose(redirect: str, dose_tokens: int) -> str:
    """Return the redirect text truncated/padded to ~dose_tokens tokens."""
    target_chars = dose_tokens * _CHARS_PER_TOKEN
    base = redirect.strip()
    if len(base) >= target_chars:
        # Truncate on a word boundary near the budget.
        cut = base[:target_chars]
        if " " in cut:
            cut = cut[:cut.rfind(" ")]
        return cut.rstrip(" ,.;:") + "."
    # Pad with in-distribution elaboration, repeated as needed.
    out = base
    while len(out) < target_chars:
        remaining = target_chars - len(out)
        out += _ELABORATION[:remaining] if remaining < len(_ELABORATION) else _ELABORATION
    cut = out[:target_chars]
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,.;:") + "."


def make_redirect_injector(redirect_text: str, dose_tokens: int):
    """Return ``inject_fn(messages) -> messages`` that interjects the
    dose-scaled redirect as a user text block. The injector also returns
    the exact scaled redirect via the closure attribute ``.text`` so the
    survival endpoint can match against it."""
    scaled = scale_to_dose(redirect_text, dose_tokens)
    framed = f"[user] {scaled}"

    def inject_fn(messages: list[dict]) -> list[dict]:
        msgs = list(messages)
        if not msgs:
            return [{"role": "user", "content": framed}]
        last = msgs[-1]
        if last.get("role") == "user":
            content = last.get("content")
            if isinstance(content, str):
                msgs[-1] = {**last, "content": content + "\n\n" + framed}
            elif isinstance(content, list):
                # append a text block alongside any tool_result blocks
                msgs[-1] = {**last, "content": list(content)
                            + [{"type": "text", "text": framed}]}
            else:
                msgs.append({"role": "user", "content": framed})
        else:
            # last is assistant — safe to add a fresh user turn
            msgs.append({"role": "user", "content": framed})
        return msgs

    inject_fn.text = scaled          # type: ignore[attr-defined]
    return inject_fn
