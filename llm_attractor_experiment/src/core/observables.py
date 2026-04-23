from __future__ import annotations

import re

ROLLING_SEP = "\n<SEP>\n"

_ROLLING_RE = re.compile(r"^rolling(?:_k(\d+))?$")


def observable_output(step: dict) -> str:
    return step["output_text"]


def observable_rolling(steps: list[dict], t: int, k: int = 3, sep: str = ROLLING_SEP) -> str:
    start = max(0, t - k + 1)
    return sep.join(s["output_text"] for s in steps[start : t + 1])


def observable_context_tail(step: dict, max_chars: int = 4000) -> str:
    return step["context_after"][-max_chars:]


def observable_context_full(step: dict, max_chars: int = 8000) -> str:
    """
    Fixed-size tail of the accumulated context at step t+1. Always slices
    `context_after[-max_chars:]` so every step feeds the embedder a
    same-length window (once the context has grown past max_chars). Early
    steps where ctx < max_chars naturally return the full short context.

    Rationale: keeping the window fixed across steps removes text length
    as a confound when comparing embeddings across time.
    """
    ctx = step["context_after"]
    return ctx[-max_chars:]


def build_all_for_run(
    steps: list[dict],
    observable_types: list[str],
    k: int,
    tail_chars: int,
    full_chars: int = 8000,
) -> dict[str, list[str]]:
    """
    Given the ordered steps of a single run, produce {observable_name -> [text per step]}.

    Supported names:
      - 'output'                 — Y_t
      - 'rolling' | 'rolling_k3' — rolling window of size k (default 3 when unspecified)
      - 'rolling_k<N>'           — rolling window of size <N> for any int N
      - 'context_tail'           — last `tail_chars` of X_{t+1}
    """
    out: dict[str, list[str]] = {}
    for name in observable_types:
        if name == "output":
            out[name] = [observable_output(s) for s in steps]
        elif name == "context_tail":
            out[name] = [observable_context_tail(s, max_chars=tail_chars) for s in steps]
        elif name == "context_full":
            out[name] = [observable_context_full(s, max_chars=full_chars) for s in steps]
        else:
            m = _ROLLING_RE.match(name)
            if not m:
                raise ValueError(f"unknown observable: {name}")
            k_used = int(m.group(1)) if m.group(1) else k
            out[name] = [observable_rolling(steps, t, k=k_used) for t in range(len(steps))]
    return out
