"""
Dialog trajectory: two LLMs alternating turns with their own personas.

- One shared, growing, speaker-labeled transcript.
- Each step is one turn by one role. Roles alternate based on `initiator`.
- Step 0 = `initiator` role responds to the seed (which is treated as the
  initiator's counterpart's opening utterance).
- Each turn's system prompt is the current role's persona.

Isolated from the main pipeline so the original experiments stay untouched.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from openai import OpenAI

from src.api.generator import generate_step, GenerationResult
from src.config import Config
from src.core.context import clip_context
from src.core.trajectory import RunIds, make_jsonl_sink
from src.utils.logging import get_logger
from src.utils.text import sha1_short, truncate_for_display

log = get_logger(__name__)


@dataclass
class Role:
    name: str              # e.g. "user" or "agent"
    system_prompt: str     # the persona


def _format_turn(role_name: str, text: str) -> str:
    # Speaker-labeled turn format. Double newline separates turns for readability.
    return f"[{role_name.title()}]: {text.strip()}\n\n"


def _step_record(
    ids: RunIds,
    step: int,
    role: str,
    context_before: str,
    gen: GenerationResult,
    context_after: str,
    config: Config,
    loop_mode: str,
) -> dict:
    return {
        "experiment_id": ids.experiment_id,
        "prompt_family": ids.prompt_family,
        "initial_condition_id": ids.initial_condition_id,
        "run_id": ids.run_id,
        "regime": ids.regime,
        "step": step,
        "role": role,
        "context_before": context_before,
        "output_text": gen.output_text,
        "context_after": context_after,
        "context_length_chars": len(context_after),
        "context_before_hash": sha1_short(context_before),
        "output_hash": sha1_short(gen.output_text),
        "model": gen.model,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_output_tokens": config.max_output_tokens,
        "response_id": gen.response_id,
        "latency_sec": gen.latency_sec,
        "retries": gen.retries,
        "loop_mode": loop_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_dialog_trajectory(
    client: OpenAI,
    seed_utterance: str,
    config: Config,
    ids: RunIds,
    role_a: Role,
    role_b: Role,
    initiator: str = "role_b",
    loop_mode: str = "append",
    step_sink: Callable[[dict], None] | None = None,
) -> list[dict]:
    """
    Args:
        seed_utterance: initial user-style opener. Added to the transcript as
            role_a's first turn before any generation happens.
        role_a, role_b: the two personas.
        initiator: which role generates first (step 0). Default 'role_b' — so
            the seed is treated as role_a's opening and role_b responds first.
        loop_mode: 'append' (accumulating transcript) or 'replace' (amnesic).

    Emits one step record per generated turn.
    """
    if initiator not in ("role_a", "role_b"):
        raise ValueError(f"initiator must be 'role_a' or 'role_b', got {initiator!r}")

    # Start the transcript with the seed as role_a's utterance.
    transcript = _format_turn(role_a.name, seed_utterance)

    records: list[dict] = []
    for step in range(config.steps_per_run):
        # Pick the role whose turn this is.
        if initiator == "role_b":
            current = role_b if step % 2 == 0 else role_a
        else:
            current = role_a if step % 2 == 0 else role_b

        # In replace mode we only send the latest turn (the other role's response).
        if loop_mode == "replace":
            send_ctx = _last_turn(transcript) or transcript
        else:
            send_ctx = transcript

        gen = generate_step(
            client,
            send_ctx,
            config,
            system_prompt=current.system_prompt,
        )

        new_turn = _format_turn(current.name, gen.output_text)
        if loop_mode == "replace":
            new_transcript = clip_context(new_turn, config.max_context_chars, rule=config.clip_rule)
        elif loop_mode == "append":
            new_transcript = clip_context(
                transcript + new_turn,
                config.max_context_chars,
                rule=config.clip_rule,
            )
        else:
            raise ValueError(f"unknown loop_mode: {loop_mode}")

        rec = _step_record(
            ids, step, current.name, send_ctx, gen, new_transcript, config, loop_mode
        )
        records.append(rec)
        if step_sink is not None:
            step_sink(rec)

        log.info(
            "%s[%s]/%s/%s/%s step %d (%s) out='%s'",
            ids.regime,
            loop_mode,
            ids.prompt_family,
            ids.initial_condition_id,
            ids.run_id,
            step,
            current.name,
            truncate_for_display(gen.output_text, 80),
        )
        transcript = new_transcript

    return records


def _last_turn(transcript: str) -> str:
    """Return the last complete `[Label]: ...` block from the transcript."""
    stripped = transcript.rstrip()
    if not stripped:
        return ""
    parts = stripped.split("\n\n")
    return parts[-1] + "\n\n" if parts else ""


__all__ = ["Role", "run_dialog_trajectory", "make_jsonl_sink"]
