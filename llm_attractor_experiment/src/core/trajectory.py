from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from openai import OpenAI

from src.api.generator import generate_step, GenerationResult
from src.config import Config
from src.core.context import append_only_update
from src.utils.io import append_jsonl
from src.utils.logging import get_logger
from src.utils.text import sha1_short, truncate_for_display

log = get_logger(__name__)


@dataclass
class RunIds:
    experiment_id: str
    prompt_family: str
    initial_condition_id: str
    run_id: str
    regime: str = "recursive"  # or a baseline mode name


def _step_record(
    ids: RunIds,
    step: int,
    context_before: str,
    gen: GenerationResult,
    context_after: str,
    config: Config,
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_trajectory(
    client: OpenAI,
    initial_context: str,
    config: Config,
    ids: RunIds,
    system_prompt: str | None = None,
    step_sink: Callable[[dict], None] | None = None,
    context_provider: Callable[[int, str, str], str] | None = None,
) -> list[dict]:
    """
    Execute an append-only trajectory of length config.steps_per_run.

    context_provider(step, current_context, initial_context) -> context_to_send.
    Default (None) uses the current recursive context. Used by baselines to
    override context selection (e.g. no_feedback always sends initial_context).
    """
    context = initial_context
    records: list[dict] = []
    for step in range(config.steps_per_run):
        if context_provider is not None:
            send_ctx = context_provider(step, context, initial_context)
        else:
            send_ctx = context
        gen = generate_step(client, send_ctx, config, system_prompt=system_prompt)
        new_context = append_only_update(
            context, gen.output_text, config.max_context_chars, rule=config.clip_rule
        )
        rec = _step_record(ids, step, send_ctx, gen, new_context, config)
        records.append(rec)
        if step_sink is not None:
            step_sink(rec)
        log.info(
            "%s/%s/%s/%s step %d out='%s'",
            ids.regime,
            ids.prompt_family,
            ids.initial_condition_id,
            ids.run_id,
            step,
            truncate_for_display(gen.output_text, 80),
        )
        context = new_context
    return records


def make_jsonl_sink(path: Path):
    def _sink(rec: dict) -> None:
        append_jsonl(path, [rec])
    return _sink
