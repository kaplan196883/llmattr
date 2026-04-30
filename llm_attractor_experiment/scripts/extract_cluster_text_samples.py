"""
Extract representative trajectory text per cluster, for each
publication-scale regime. Supports the per-cluster semantic
inspection (review weakness #2 follow-up): what does each "basin"
actually contain, semantically?

Outputs a markdown summary per regime listing N representative
trajectories from each cluster, including their seed text (initial
condition), a mid-trajectory snippet, and a late-window snippet.

Inputs:
  data/<exp>/raw/steps.jsonl
  data/<exp>/metrics/clusters_<observable>_pca10.csv

Output:
  data/aggregated/cluster_text_samples_<exp>.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent

DEFAULT_EXPERIMENTS = [
    "exp_pub_O1_continue",
    "exp_pub_O2_paraphrase_replace",
    "exp_pub_O3_summarize_negate_replace",
    "exp_pub_D1_dialog_curious_helpful_v2",
]


def _load_steps(exp_dir: Path) -> pd.DataFrame:
    p = exp_dir / "raw" / "steps.jsonl"
    rows = []
    with open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return pd.DataFrame(rows)


def _load_clusters(exp_dir: Path, observable: str) -> pd.DataFrame:
    p = exp_dir / "metrics" / f"clusters_{observable}_pca10.csv"
    return pd.read_csv(p)


def _final_cluster_per_traj(clusters: pd.DataFrame) -> pd.DataFrame:
    """Mode cluster across late window per trajectory."""
    n_steps = int(clusters["step"].max()) + 1
    cutoff = int(n_steps * 0.7)
    late = clusters[clusters["step"] >= cutoff]
    return (
        late.groupby(["regime", "prompt_family", "initial_condition_id", "run_id"])
        ["cluster"].agg(lambda s: s.mode().iat[0]).reset_index()
        .rename(columns={"cluster": "final_cluster"})
    )


def _truncate(text: str, n: int = 280) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) > n:
        text = text[: n - 1] + "…"
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", nargs="+", default=DEFAULT_EXPERIMENTS)
    ap.add_argument("--observable", default="context_tail")
    ap.add_argument("--n-per-cluster", type=int, default=4,
                    help="number of representative trajectories per cluster")
    args = ap.parse_args()

    out_dir = REPO / "data" / "aggregated"
    out_dir.mkdir(parents=True, exist_ok=True)

    for exp in args.experiments:
        exp_dir = REPO / "data" / exp
        if not exp_dir.is_dir():
            print(f"skip {exp}: not found")
            continue
        print(f"\n=== {exp} ===")
        try:
            steps = _load_steps(exp_dir)
        except Exception as e:
            print(f"  failed to load steps.jsonl: {e}")
            continue
        try:
            clusters = _load_clusters(exp_dir, args.observable)
        except Exception as e:
            print(f"  failed to load clusters: {e}")
            continue
        # Restrict to recursive regime (drop baselines if any).
        steps = steps[steps["regime"] == "recursive"]
        clusters = clusters[clusters["regime"] == "recursive"]
        print(f"  {len(steps)} step rows, {len(clusters)} cluster rows")

        # Pick the agent role for dialog runs.
        if "role" in steps.columns:
            roles = sorted(steps["role"].dropna().unique())
            target = "agent" if "agent" in roles else (roles[-1] if roles else None)
            if target:
                steps = steps[steps["role"] == target]

        finals = _final_cluster_per_traj(clusters)
        print(f"  {len(finals)} trajectories, "
              f"{finals['final_cluster'].nunique()} unique final clusters")

        # For each cluster, sample N trajectories.
        rng = np.random.default_rng(42)
        out_lines = [
            f"# Cluster text samples — {exp}",
            "",
            f"Observable: `{args.observable}` | Cluster method: K-means k=12 (canonical) | "
            f"Sampled at random (seed=42), N per cluster = {args.n_per_cluster}.",
            "",
            "Each entry shows the seed text (initial condition), a mid-step snippet "
            f"(~step round(T/2) of the trajectory), and the final-step output text. "
            "Sample size per cluster shown as `n=…`.",
            "",
        ]

        n_steps = int(steps["step"].max()) + 1
        mid_step = n_steps // 2
        late_step = n_steps - 1

        for cluster_id, grp in finals.groupby("final_cluster"):
            n_in_cluster = len(grp)
            sampled = grp.sample(
                n=min(args.n_per_cluster, n_in_cluster),
                random_state=int(rng.integers(0, 1_000_000)),
            )
            out_lines.append(
                f"## cluster {cluster_id} (n_trajectories={n_in_cluster})"
            )
            out_lines.append("")
            for _, r in sampled.iterrows():
                fam = r["prompt_family"]
                ic = r["initial_condition_id"]
                run = r["run_id"]
                key = (fam, ic, run)
                seed = steps[
                    (steps["prompt_family"] == fam)
                    & (steps["initial_condition_id"] == ic)
                    & (steps["run_id"] == run)
                    & (steps["step"] == 0)
                ]["context_before"].values
                seed_t = _truncate(seed[0] if len(seed) else "", 200)
                mid = steps[
                    (steps["prompt_family"] == fam)
                    & (steps["initial_condition_id"] == ic)
                    & (steps["run_id"] == run)
                    & (steps["step"] == mid_step)
                ]["output_text"].values
                mid_t = _truncate(mid[0] if len(mid) else "", 280)
                late = steps[
                    (steps["prompt_family"] == fam)
                    & (steps["initial_condition_id"] == ic)
                    & (steps["run_id"] == run)
                    & (steps["step"] == late_step)
                ]["output_text"].values
                late_t = _truncate(late[0] if len(late) else "", 280)
                out_lines.append(f"- **{fam} / {ic} / {run}**")
                out_lines.append(f"  - **seed**: {seed_t}")
                out_lines.append(f"  - **step {mid_step}**: {mid_t}")
                out_lines.append(f"  - **step {late_step}**: {late_t}")
            out_lines.append("")

        out_path = out_dir / f"cluster_text_samples_{exp}.md"
        out_path.write_text("\n".join(out_lines), encoding="utf-8")
        print(f"  wrote {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
