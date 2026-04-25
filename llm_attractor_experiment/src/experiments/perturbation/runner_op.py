"""
Operator-experiment perturbation runner — the operator analog of
src.experiments.perturbation.runner.

Mirrors src.experiments.operators.trajectory.run_trajectory_op but at the
designated `override_step` replaces the generated output with a supplied
perturbation text (no API call for that step). Subsequent steps see the
injected text via the normal context update path, so the effect depends on
loop_mode: for 'append' the perturbation is one paragraph among many in
the accumulated context; for 'replace' it becomes the entire state.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from openai import OpenAI

from src.api.generator import generate_step, GenerationResult
from src.config import Config
from src.core.trajectory import RunIds
from src.experiments.operators.context import update_context
from src.experiments.perturbation.runner import _synthetic_generation_result
from src.utils.logging import get_logger
from src.utils.text import sha1_short, truncate_for_display

log = get_logger(__name__)


def _step_record_op(
    ids: RunIds,
    step: int,
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


def run_perturbed_trajectory_op(
    client: OpenAI,
    initial_context: str,
    config: Config,
    ids: RunIds,
    perturbation_condition: str,
    perturbation_text: str | None,
    override_step: int,
    loop_mode: str,
    system_prompt: str | None = None,
    step_sink: Callable[[dict], None] | None = None,
) -> list[dict]:
    """Operator trajectory with an optional override at `override_step`."""
    if perturbation_condition != "control" and perturbation_text is None:
        raise ValueError("non-control condition requires perturbation_text")

    context = initial_context
    records: list[dict] = []
    for step in range(config.steps_per_run):
        send_ctx = context

        is_override = (step == override_step) and (perturbation_condition != "control")
        if is_override:
            gen = _synthetic_generation_result(perturbation_text, config.generation_model)
        else:
            gen = generate_step(client, send_ctx, config, system_prompt=system_prompt)

        new_context = update_context(
            context,
            gen.output_text,
            config.max_context_chars,
            rule=config.clip_rule,
            loop_mode=loop_mode,
        )
        rec = _step_record_op(
            ids, step, send_ctx, gen, new_context, config,
            loop_mode, perturbation_condition, override_step,
        )
        records.append(rec)
        if step_sink is not None:
            step_sink(rec)

        tag = "PERT" if is_override else "    "
        log.info(
            "%s/%s %s[%s]/%s/%s/%s step %d out='%s'",
            perturbation_condition, tag,
            ids.regime, loop_mode,
            ids.prompt_family, ids.initial_condition_id, ids.run_id,
            step, truncate_for_display(gen.output_text, 70),
        )
        context = new_context
    return records


__all__ = ["run_perturbed_trajectory_op"]
