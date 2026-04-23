from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from src.utils.io import ensure_dir
from src.utils.logging import get_logger

log = get_logger(__name__)


def build_embedding_batch_file(
    path: Path,
    texts: list[str],
    custom_ids: list[str],
    model: str,
) -> Path:
    """Write a JSONL file for Batch API /v1/embeddings requests."""
    if len(texts) != len(custom_ids):
        raise ValueError("texts and custom_ids must have the same length")
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for cid, t in zip(custom_ids, texts):
            rec = {
                "custom_id": cid,
                "method": "POST",
                "url": "/v1/embeddings",
                "body": {"model": model, "input": t or " "},
            }
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")
    return path


def upload_batch_file(client: OpenAI, path: Path) -> str:
    with path.open("rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    log.info("uploaded batch input file id=%s", uploaded.id)
    return uploaded.id


def create_batch(client: OpenAI, input_file_id: str, endpoint: str = "/v1/embeddings") -> str:
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint=endpoint,
        completion_window="24h",
    )
    log.info("created batch id=%s endpoint=%s", batch.id, endpoint)
    return batch.id


def poll_batch(client: OpenAI, batch_id: str, poll_interval: float = 30.0) -> Any:
    while True:
        batch = client.batches.retrieve(batch_id)
        status = batch.status
        log.info("batch %s status=%s", batch_id, status)
        if status in ("completed", "failed", "expired", "cancelled"):
            return batch
        time.sleep(poll_interval)


def download_batch_output(client: OpenAI, output_file_id: str, dest: Path) -> Path:
    ensure_dir(dest.parent)
    content = client.files.content(output_file_id)
    # SDK returns an HTTPXBinaryResponseContent-like object with .read() / .text
    try:
        data = content.read()
    except AttributeError:
        data = content.text.encode("utf-8")  # type: ignore[attr-defined]
    dest.write_bytes(data)
    return dest


def parse_embedding_batch_output(path: Path) -> dict[str, list[float]]:
    """Read a batch output JSONL and return {custom_id -> embedding vector}."""
    out: dict[str, list[float]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            cid = rec.get("custom_id")
            body = (rec.get("response") or {}).get("body") or {}
            data = body.get("data") or []
            if cid and data:
                out[cid] = data[0]["embedding"]
    return out
