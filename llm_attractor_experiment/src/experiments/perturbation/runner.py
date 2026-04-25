"""
Perturbation-aware dialog trajectory runner.

Wraps the standard dialog trajectory, but at the designated `override_step`
replaces the current role's natural output with a supplied perturbation text.
This simulates "human intervention" — the perturbation is injected as if it
were one of the speakers saying something off-topic.

Everything else (roles, turn alternation, loop_mode, recording) is identical
to src.experiments.dialog.trajectory.run_dialog_trajectory — we just branch
at the override step.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from openai import OpenAI

from src.api.generator import generate_step, GenerationResult
from src.config import Config
from src.core.context import clip_context
from src.core.trajectory import RunIds
from src.experiments.dialog.trajectory import Role, _format_turn, _last_turn
from src.utils.logging import get_logger
from src.utils.text import sha1_short, truncate_for_display

log = get_logger(__name__)


def _synthetic_generation_result(text: str, model: str) -> GenerationResult:
    """Build a GenerationResult for a non-API 'output' (the perturbation text)."""
    return GenerationResult(
        output_text=text,
        model=model,
        response_id=f"perturbation:{sha1_short(text)}",
        latency_sec=0.0,
        retries=0,
        raw={"synthetic": True, "source": "perturbation_injection"},
    )


def _step_record(
    ids: RunIds,
    step: int,
    role: str,
    context_before: str,
    gen: GenerationResult,
    context_after: str,
    config: Config,
    loop_mode: str,
    perturbation_condition: str,
    perturbed_step: int,
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
        "perturbation_condition": perturbation_condition,
        "perturbed_step": perturbed_step,
        "is_perturbation_step": step == perturbed_step and perturbation_condition != "control",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_perturbed_dialog_trajectory(
    client: OpenAI,
    seed_utterance: str,
    config: Config,
    ids: RunIds,
    role_a: Role,
    role_b: Role,
    perturbation_condition: str,     # "control" | "neutral" | "lorem" | "adversarial"
    perturbation_text: str | None,   # None iff condition=="control"
    override_step: int,              # step at which to inject (e.g. 15)
    initiator: str = "role_b",
    loop_mode: str = "append",
    step_sink: Callable[[dict], None] | None = None,
) -> list[dict]:
    """Dialog trajectory with an optional override at `override_step`.

    At override_step, if perturbation_text is given, that text is substituted
    for the current role's normal API output. The LLM is NOT called for that
    step; subsequent steps see the injected text in the transcript.
    """
    if initiator not in ("role_a", "role_b"):
        raise ValueError(f"initiator must be 'role_a' or 'role_b', got {initiator!r}")
    if perturbation_condition != "control" and perturbation_text is None:
        raise ValueError("non-control condition requires perturbation_text")

    transcript = _format_turn(role_a.name, seed_utterance)
    records: list[dict] = []

    for step in range(config.steps_per_run):
        if initiator == "role_b":
            current = role_b if step % 2 == 0 else role_a
        else:
            current = role_a if step % 2 == 0 else role_b

        if loop_mode == "replace":
            send_ctx = _last_turn(transcript) or transcript
        else:
            send_ctx = transcript

        is_override = (step == override_step) and (perturbation_condition != "control")
        if is_override:
            gen = _synthetic_generation_result(perturbation_text, config.generation_model)
        else:
            gen = generate_step(
                client, send_ctx, config, system_prompt=current.system_prompt
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
            ids, step, current.name, send_ctx, gen, new_transcript,
            config, loop_mode, perturbation_condition, override_step,
        )
        records.append(rec)
        if step_sink is not None:
            step_sink(rec)

        tag = "PERT" if is_override else "    "
        log.info(
            "%s/%s %s[%s]/%s/%s/%s step %d (%s) out='%s'",
            perturbation_condition, tag,
            ids.regime, loop_mode,
            ids.prompt_family, ids.initial_condition_id, ids.run_id,
            step, current.name,
            truncate_for_display(gen.output_text, 70),
        )
        transcript = new_transcript

    return records


__all__ = ["run_perturbed_dialog_trajectory"]
