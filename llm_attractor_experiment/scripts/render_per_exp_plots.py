"""
Render per-experiment t-SNE flow field + trajectory plots for a single
publication-scale experiment. Designed to be launched once per experiment so
multiple can run concurrently (each is ~10-15 min of single-threaded t-SNE).

Usage:
    python -m scripts.render_per_exp_plots --experiment exp_pub_O2_paraphrase_replace
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.experiments.dynamics.regime_plots import (
    plot_flow_field_single,
    plot_flow_field_tsne_single,
    plot_tsne_trajectories_single,
)
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="render_per_exp_plots")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out-dir", default="data/pub_dynamics_plots")
    parser.add_argument("--observable", default="rolling_k3")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)

    log.info("=== %s ===", args.experiment)
    plot_flow_field_single(args.experiment, data_dir, out_dir, observable=args.observable)
    plot_flow_field_tsne_single(args.experiment, data_dir, out_dir, observable=args.observable)
    plot_tsne_trajectories_single(args.experiment, data_dir, out_dir, observable=args.observable)
    log.info("done: %s", args.experiment)
    return 0


if __name__ == "__main__":
    sys.exit(main())
