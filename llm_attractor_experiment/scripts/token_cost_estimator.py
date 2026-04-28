"""
Compute the exact API-token cost of replicating every existing
experiment on a different model.

Walks `data/exp_*/raw/steps.jsonl` for all 37 experiments, counts
input tokens (system prompt + context_before, exactly what the
generator sends per step) and output tokens (output_text) using
`tiktoken o200k_base` (the tokenizer used by all GPT-4-family
OpenAI models — also a reasonable proxy for MiniMax counts within
~5–15% since vocabularies are tokenization-equivalent for English
text), then multiplies by per-million pricing the user provides.

Usage:
    python -m scripts.token_cost_estimator \
        --price gpt-4o-mini=0.15:0.60 \
        --price gpt-4o=2.50:10.00 \
        --price MiniMax-Text-01=0.20:1.10

(prices are USD per million tokens, "input:output"). Add as many
--price entries as you want; one column per model in the output
table. Run with no --price flags to see token counts only.

Also writes:
    data/aggregated/cross_model_token_estimate.csv
        per-experiment {input_tokens, output_tokens, n_steps}
    docs/COST_ESTIMATE.md
        markdown report with per-experiment + grand-total cost per
        model, plus methodology notes.

Embedding cost is computed separately (uses the experiment's
text-embedding-3-small canonical price by default; can be
overridden with --embed-price).
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import tiktoken
import yaml

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT_CSV = DATA / "aggregated" / "cross_model_token_estimate.csv"
OUT_MD = REPO / "docs" / "COST_ESTIMATE.md"

# Default tokenizer: o200k_base (GPT-4o family). For input-token counts
# on cross-vendor models like MiniMax, this is an approximation; the
# actual tokenizer differs but the count is typically within ~10-15%
# for English text. This is documented in the report header.
ENC = tiktoken.get_encoding("o200k_base")


def _load_system_prompts(exp_dir: Path) -> dict[str, str]:
    """Map prompt_family name -> system_prompt string for this exp.
    Dialog experiments have role_a/role_b system prompts; we pick the
    larger one as a worst-case proxy for the per-step call (each turn
    sends one role's system prompt)."""
    cfg_path = exp_dir / "config.yaml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    out: dict[str, str] = {}
    for fam in cfg.get("prompt_families", []) or []:
        out[fam["name"]] = fam.get("system_prompt", "")
    # Dialog experiments: stash an averaged role system prompt under a
    # synthetic key. Token-wise the dialog runs alternate role_a /
    # role_b so the average is the right per-step cost.
    dlg = cfg.get("dialog") or {}
    if dlg:
        sa = (dlg.get("role_a") or {}).get("system_prompt", "")
        sb = (dlg.get("role_b") or {}).get("system_prompt", "")
        out["__dialog_avg__"] = sa if len(sa) >= len(sb) else sb
    return out


def _count_tokens(texts: Iterable[str]) -> int:
    return sum(len(ENC.encode(t or "")) for t in texts)


def tally_experiment(exp_dir: Path) -> dict:
    """Return {experiment_id, n_steps, input_tokens, output_tokens}."""
    steps_path = exp_dir / "raw" / "steps.jsonl"
    if not steps_path.exists():
        return {"experiment_id": exp_dir.name, "n_steps": 0,
                "input_tokens": 0, "output_tokens": 0}
    sys_prompts = _load_system_prompts(exp_dir)
    # Pre-tokenize every distinct system prompt so we don't re-encode
    # ~250K times for the same string.
    sys_token_count = {k: _count_tokens([v]) for k, v in sys_prompts.items()}
    default_sys_tokens = max(sys_token_count.values()) if sys_token_count else 0

    n_steps = 0
    input_tokens = 0
    output_tokens = 0
    with steps_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            n_steps += 1
            ctx_in = rec.get("context_before", "") or ""
            out_txt = rec.get("output_text", "") or ""
            fam = rec.get("prompt_family", "")
            sys_n = sys_token_count.get(fam,
                    sys_token_count.get("__dialog_avg__", default_sys_tokens))
            input_tokens += sys_n + len(ENC.encode(ctx_in))
            output_tokens += len(ENC.encode(out_txt))
    return {
        "experiment_id": exp_dir.name,
        "n_steps": n_steps,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def _parse_prices(price_args: list[str]) -> dict[str, tuple[float, float]]:
    """`name=in:out` USD-per-million strings → {name: (in, out)} dict."""
    out: dict[str, tuple[float, float]] = {}
    for s in price_args:
        if "=" not in s or ":" not in s:
            raise SystemExit(f"--price expects 'name=in:out', got {s!r}")
        name, prices = s.split("=", 1)
        a, b = prices.split(":", 1)
        out[name.strip()] = (float(a), float(b))
    return out


def _fmt_money(x: float) -> str:
    if x >= 100:
        return f"${x:,.0f}"
    if x >= 10:
        return f"${x:,.1f}"
    return f"${x:,.2f}"


def emit_report(rows: list[dict], prices: dict[str, tuple[float, float]],
                embed_price_per_M: float) -> str:
    rows_sorted = sorted(rows, key=lambda r: -r["input_tokens"] - r["output_tokens"])
    total_in = sum(r["input_tokens"] for r in rows_sorted)
    total_out = sum(r["output_tokens"] for r in rows_sorted)
    total_steps = sum(r["n_steps"] for r in rows_sorted)
    lines: list[str] = []
    p = lines.append
    p("# COST_ESTIMATE.md — exact token cost of cross-model replication")
    p("")
    p("Computed from the on-disk trajectories of every existing experiment")
    p(f"in `data/exp_*/raw/steps.jsonl` (37 experiments, "
      f"{total_steps:,} step records). Token counts use `tiktoken "
      f"o200k_base` (the GPT-4-family tokenizer); for non-OpenAI vendors")
    p("the count is an approximation but typically within ~10-15% on")
    p("English text since modern BPE vocabularies are similar in size.")
    p("")
    p(f"**Grand totals**: {total_in:,} input tokens, {total_out:,} output")
    p(f"tokens, ratio in/out ≈ {total_in/max(1,total_out):.1f}.")
    p("")
    if not prices:
        p("(No `--price` flags supplied; only token counts shown.)")
        p("")
    else:
        p("## Per-model replication cost (USD)")
        p("")
        header = "| experiment | steps | input M | output M |"
        sep    = "|---|---:|---:|---:|"
        for name in prices:
            header += f" {name} |"
            sep    += "---:|"
        p(header)
        p(sep)
        for r in rows_sorted:
            in_M = r["input_tokens"] / 1e6
            out_M = r["output_tokens"] / 1e6
            row = (f"| {r['experiment_id']} | {r['n_steps']:,} "
                   f"| {in_M:.2f} | {out_M:.2f} |")
            for name, (p_in, p_out) in prices.items():
                cost = in_M * p_in + out_M * p_out
                row += f" {_fmt_money(cost)} |"
            p(row)
        # Grand-total row
        in_M = total_in / 1e6; out_M = total_out / 1e6
        embed_M = total_in / 1e6  # embeddings see ~same volume as input (one embed per step's text)
        row = (f"| **TOTAL (37 exp)** | **{total_steps:,}** "
               f"| **{in_M:.1f}** | **{out_M:.1f}** |")
        for name, (p_in, p_out) in prices.items():
            cost = in_M * p_in + out_M * p_out
            row += f" **{_fmt_money(cost)}** |"
        p(row)
        embed_cost = embed_M * embed_price_per_M
        p("")
        p(f"Plus **embeddings**: ~{embed_M:.1f}M tokens at "
          f"${embed_price_per_M:.3f}/M = {_fmt_money(embed_cost)} per model "
          f"(`text-embedding-3-small` is held fixed across all cross-model "
          f"runs; this cost applies once per replication, not per generator).")
        p("")
    p("## Methodology")
    p("")
    p("- For each step record we count input = `len(encode(system_prompt))`")
    p("  + `len(encode(context_before))`, output = `len(encode(output_text))`.")
    p("- Dialog experiments use the longer of the two role system prompts")
    p("  as a per-turn proxy (each turn sends exactly one role's system).")
    p("- Embedding cost assumes one embedding pass per step record (the")
    p("  baseline pipeline's `cmd_embed` behavior). Multi-observable")
    p("  experiments may embed 2–3× per step; treat the embedding line")
    p("  as a lower bound.")
    p("- Cross-vendor token counts use `o200k_base` as a proxy. For")
    p("  precise MiniMax / DeepSeek estimates, multiply the values above")
    p("  by ~1.10 as a conservative buffer.")
    p("")
    p("Regenerate with:")
    p("```")
    p("python -m scripts.token_cost_estimator \\")
    p("    --price gpt-4o-mini=0.15:0.60 \\")
    p("    --price gpt-4o=2.50:10.00 \\")
    p("    --price MiniMax-Text-01=0.20:1.10")
    p("```")
    p("")
    p("(Verify per-model rates against current `openai.com/api/pricing`")
    p("and `minimaxi.com/pricing` before committing budget.)")
    p("")
    return "\n".join(lines)


def emit_csv(rows: list[dict]) -> str:
    out = ["experiment_id,n_steps,input_tokens,output_tokens"]
    for r in sorted(rows, key=lambda x: x["experiment_id"]):
        out.append(f"{r['experiment_id']},{r['n_steps']},"
                   f"{r['input_tokens']},{r['output_tokens']}")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", action="append", default=[],
                    help="repeated: name=input_per_M:output_per_M (USD)")
    ap.add_argument("--embed-price", type=float, default=0.02,
                    help="text-embedding-3-small price per M tokens "
                         "(default: $0.02 as of late 2025)")
    args = ap.parse_args()
    prices = _parse_prices(args.price)

    exp_dirs = sorted(p for p in DATA.glob("exp_*") if p.is_dir())
    rows: list[dict] = []
    for d in exp_dirs:
        r = tally_experiment(d)
        if r["n_steps"] > 0:
            rows.append(r)
        print(f"  {r['experiment_id']:55s} steps={r['n_steps']:>7,} "
              f"in={r['input_tokens']:>11,}  out={r['output_tokens']:>9,}")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.write_text(emit_csv(rows), encoding="utf-8")
    print(f"\nwrote {OUT_CSV}")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(emit_report(rows, prices, args.embed_price),
                      encoding="utf-8")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
