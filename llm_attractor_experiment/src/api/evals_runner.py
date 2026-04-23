from __future__ import annotations

from typing import Any

from openai import OpenAI

from src.utils.logging import get_logger

log = get_logger(__name__)


def create_eval(client: OpenAI, definition: dict) -> str:
    """Thin wrapper around client.evals.create. Optional management layer."""
    ev = client.evals.create(**definition)
    log.info("created eval id=%s", ev.id)
    return ev.id


def run_eval(client: OpenAI, eval_id: str, run_config: dict) -> str:
    run = client.evals.runs.create(eval_id=eval_id, **run_config)
    log.info("created eval run id=%s eval_id=%s", run.id, eval_id)
    return run.id


def retrieve_eval_run(client: OpenAI, eval_id: str, run_id: str) -> Any:
    return client.evals.runs.retrieve(eval_id=eval_id, run_id=run_id)
