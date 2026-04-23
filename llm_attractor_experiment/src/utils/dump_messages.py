"""
Dump the full API message flow for a single trajectory so you can see
exactly what was sent to OpenAI at each step.

Usage:
    python -m src.utils.dump_messages \
        --experiment-id exp_op_O2_paraphrase_replace \
        --prompt-family reflective --ic ic_000 --run run_000 \
        [--regime recursive] [--max-steps 6] [--max-chars 600] [--output-dir data]

Prints:
    === STEP 0 ===
    [developer]  <system/operator prompt>
    [user]       <context_before>
    [assistant]  <output_text>   ← what the API returned
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Iterable

import yaml


def _iter_steps(steps_path: Path) -> Iterable[dict]:
    with steps_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _load_system_prompt(config_path: Path, family: str) -> str:
    if not config_path.exists():
        return "<config snapshot missing>"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    for fam in raw.get("prompt_families", []):
        if fam.get("name") == family:
            return fam.get("system_prompt", "<no system_prompt>")
    return "<family not found in snapshot>"


def _ellide(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return f"{head}\n… [elided {len(text) - max_chars} chars] …\n{tail}"


def dump(
    experiment_id: str,
    prompt_family: str,
    ic: str,
    run: str,
    regime: str = "recursive",
    max_steps: int | None = None,
    max_chars: int = 800,
    output_dir: str = "data",
) -> None:
    exp_dir = Path(output_dir) / experiment_id
    steps_path = exp_dir / "raw" / "steps.jsonl"
    cfg_path = exp_dir / "config.yaml"

    if not steps_path.exists():
        raise FileNotFoundError(f"No step log at {steps_path}")

    system_prompt = _load_system_prompt(cfg_path, prompt_family)

    matched = [
        s
        for s in _iter_steps(steps_path)
        if s["regime"] == regime
        and s["prompt_family"] == prompt_family
        and s["initial_condition_id"] == ic
        and s["run_id"] == run
    ]
    matched.sort(key=lambda s: s["step"])
    if max_steps is not None:
        matched = matched[:max_steps]

    print(f"# {experiment_id} | {regime} / {prompt_family} / {ic} / {run}")
    print(f"# system (developer) prompt: {system_prompt!r}")
    print(f"# {len(matched)} step(s) shown (of {len(matched) if max_steps is None else 'requested '+str(max_steps)})")
    print(f"# `assistant` text is what came back in the response, i.e. Y_t")
    print()

    for s in matched:
        print(f"=== STEP {s['step']} ===")
        print("[developer]")
        print(textwrap.indent(_ellide(system_prompt, max_chars), "    "))
        print("[user]")
        print(textwrap.indent(_ellide(s["context_before"], max_chars), "    "))
        print("[assistant]  (Y_t, appended to context for the next step)")
        print(textwrap.indent(_ellide(s["output_text"], max_chars), "    "))
        print(f"   (context_after len = {s['context_length_chars']} chars, "
              f"latency = {s.get('latency_sec', 0):.2f}s, retries = {s.get('retries', 0)})")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dump_messages")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--prompt-family", required=True)
    parser.add_argument("--ic", required=True, help="initial_condition_id, e.g. ic_000")
    parser.add_argument("--run", required=True, help="run_id, e.g. run_000")
    parser.add_argument("--regime", default="recursive")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--max-chars", type=int, default=800)
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args(argv)
    dump(
        experiment_id=args.experiment_id,
        prompt_family=args.prompt_family,
        ic=args.ic,
        run=args.run,
        regime=args.regime,
        max_steps=args.max_steps,
        max_chars=args.max_chars,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
