"""
Operator-experiment trajectory runner. Mirrors src/core/trajectory.run_trajectory
but calls the local update_context so the loop_mode can be swapped to 'replace'.
The original src/core/trajectory.py stays untouched.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from openai import OpenAI

from src.api.generator import generate_step, GenerationResult
from src.config import Config
from src.core.trajectory import RunIds, make_jsonl_sink  # reuse shared types/sinks
from src.experiments.operators.context import update_context
from src.utils.logging import get_logger
from src.utils.text import sha1_short, truncate_for_display

log = get_logger(__name__)


def _step_record(
    ids: RunIds,
    step: int,
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


def run_trajectory_op(
    client: OpenAI,
    initial_context: str,
    config: Config,
    ids: RunIds,
    loop_mode: str,
    system_prompt: str | None = None,
    step_sink: Callable[[dict], None] | None = None,
    context_provider: Callable[[int, str, str], str] | None = None,
) -> list[dict]:
    """
    Mirror of core.trajectory.run_trajectory that respects `loop_mode`.
    """
    context = initial_context
    records: list[dict] = []
    for step in range(config.steps_per_run):
        send_ctx = (
            context_provider(step, context, initial_context)
            if context_provider is not None
            else context
        )
        gen = generate_step(client, send_ctx, config, system_prompt=system_prompt)
        new_context = update_context(
            context,
            gen.output_text,
            config.max_context_chars,
            rule=config.clip_rule,
            loop_mode=loop_mode,
        )
        rec = _step_record(ids, step, send_ctx, gen, new_context, config, loop_mode)
        records.append(rec)
        if step_sink is not None:
            step_sink(rec)
        log.info(
            "%s[%s]/%s/%s/%s step %d out='%s'",
            ids.regime,
            loop_mode,
            ids.prompt_family,
            ids.initial_condition_id,
            ids.run_id,
            step,
            truncate_for_display(gen.output_text, 80),
        )
        context = new_context
    return records


__all__ = ["run_trajectory_op", "make_jsonl_sink"]
