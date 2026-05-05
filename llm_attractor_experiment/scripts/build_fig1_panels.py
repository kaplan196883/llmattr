"""Build the 2-panel Fig 1 used in the paper.

Panel A: existing headline raw-switching dose response across regime x content
         types (D1/neutral, O1/neutral, O1/adversarial), doses 5-400 tokens,
         clipped data (canonical bounded-memory loop).

Panel B: persistent-escape rate vs dose under context_tail observable. Three
         curves: bounded memory (12K clip, strict persist@inj measure),
         full-history strict (kicked AND in same post-injection cluster at
         terminal), and full-history loose (kicked AND not returned to
         pre-injection cluster). The strict-vs-loose decomposition resolves
         the apparent non-monotonic dip at high doses (heterogeneous large
         perturbations scatter trajectories across multiple post-injection
         clusters; trajectories ARE leaving the original basin durably,
         they just don't all land in the same destination).

Output: data/aggregated/perturbation_dose_response/dose_response_2panel.png
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _wilson(p, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _decompose_persistence(exp_name: str) -> pd.DataFrame:
    """Compute strict (persist@inj) and loose (kicked & not returned) per dose
    under context_tail observable for a given experiment."""
    exp_dir = DATA / exp_name
    X = np.load(exp_dir / "embeddings" / "context_tail" / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / "context_tail" / "metadata.parquet")
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=12, random_state=42, n_init=10)
    df = meta.copy()
    df["cluster"] = km.fit_predict(Xp)
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    final = int(df["step"].max())
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre, post, end = srow.get(14), srow.get(15), srow.get(final)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        rows.append({
            "regime": regime,
            "kicked": int(post != pre),
            "persisted_strict": int(end == post and post != pre),  # in same post-injection cluster
            "displaced_loose": int(end != pre and post != pre),    # kicked AND not returned to original
        })
    df_p = pd.DataFrame(rows)

    def dose(s):
        m = re.match(r"adversarial_dose(\d+)$", s)
        return int(m.group(1)) if m else None

    summary = df_p.groupby("regime").agg(
        n_total=("regime", "count"),
        n_strict=("persisted_strict", "sum"),
        n_loose=("displaced_loose", "sum"),
    ).reset_index()
    summary["dose"] = summary["regime"].map(dose)
    summary["pct_strict"] = summary["n_strict"] / summary["n_total"]
    summary["pct_loose"] = summary["n_loose"] / summary["n_total"]
    ci_strict = summary.apply(
        lambda r: _wilson(r["pct_strict"], int(r["n_total"])), axis=1, result_type="expand"
    )
    summary["strict_lo"] = ci_strict[0]
    summary["strict_hi"] = ci_strict[1]
    ci_loose = summary.apply(
        lambda r: _wilson(r["pct_loose"], int(r["n_total"])), axis=1, result_type="expand"
    )
    summary["loose_lo"] = ci_loose[0]
    summary["loose_hi"] = ci_loose[1]
    return summary.dropna(subset=["dose"]).sort_values("dose")


def _compute_panel_a_from_embeddings(exp_id: str) -> pd.DataFrame:
    """Recompute the raw switching summary directly from this experiment's
    context_tail embeddings + metadata. Replaces a now-missing
    switching_summary.csv that lived under data/exp_*/reports/.

    Switch rate per condition = fraction of (family, ic, run) trajectories
    whose terminal-step cluster differs from the matched control trajectory's
    terminal-step cluster. Joint PCA-10 + K-means k=12 is fit per experiment
    (matches the canonical pipeline).
    """
    exp_dir = DATA / exp_id
    emb_path = exp_dir / "embeddings" / "context_tail" / "embeddings.npy"
    meta_path = exp_dir / "embeddings" / "context_tail" / "metadata.parquet"
    if not emb_path.exists() or not meta_path.exists():
        return pd.DataFrame()
    X = np.load(emb_path)
    meta = pd.read_parquet(meta_path).copy()
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=12, random_state=42, n_init=10)
    meta["cluster"] = km.fit_predict(Xp)

    final_step = int(meta["step"].max())
    terminal = meta[meta["step"] == final_step][[
        "regime", "prompt_family", "initial_condition_id", "run_id", "cluster"
    ]].copy()
    if "control" not in set(terminal["regime"]):
        return pd.DataFrame()
    control = terminal[terminal["regime"] == "control"][
        ["prompt_family", "initial_condition_id", "run_id", "cluster"]
    ].rename(columns={"cluster": "control_cluster"})
    perturbed = terminal[terminal["regime"] != "control"]
    merged = perturbed.merge(
        control, on=["prompt_family", "initial_condition_id", "run_id"], how="inner"
    )
    merged["switched"] = (merged["cluster"] != merged["control_cluster"]).astype(int)
    rows = []
    for cond, grp in merged.groupby("regime"):
        rows.append({
            "condition": cond,
            "n_total": len(grp),
            "n_switched": int(grp["switched"].sum()),
            "switch_rate": float(grp["switched"].mean()),
        })
    return pd.DataFrame(rows)


def _load_panel_a():
    """Reproduce the existing Fig 1 panel: D1/neutral, O1/neutral, O1/adversarial.

    Computes from embeddings (the upstream switching_summary.csv files
    were stripped from the working tree). Returns one combined DataFrame
    spanning all three series.
    """
    rows = []
    for exp_id, regime_label, ptype in [
        ("exp_perturb_D1_dose",             "D1 dialog",   "neutral"),
        ("exp_perturb_D1_dose_fine",        "D1 dialog",   "neutral"),
        ("exp_perturb_O1_dose",             "O1 continue", "neutral"),
        ("exp_perturb_O1_dose_adversarial", "O1 continue", "adversarial"),
    ]:
        df = _compute_panel_a_from_embeddings(exp_id)
        if df.empty:
            continue
        df["regime_label"] = regime_label
        df["perturbation_type"] = ptype
        df["dose"] = df["condition"].apply(
            lambda c: int(c.split("_dose")[-1]) if "_dose" in c else None
        )
        rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _load_panel_b():
    """Pull persistence under context_tail from clipped + full-history data.

    The aggregate `long.csv` was wiped along with the rest of data/aggregated
    by the data-strip; this function previously read it. We retain the same
    interface but the canonical Panel B path now goes through
    `_decompose_persistence` per-experiment (called inline in main()), which
    needs only the embeddings + metadata that survive in the working tree.
    Returns an empty DataFrame so that downstream consumers fall through to
    the per-experiment path.
    """
    return pd.DataFrame()


def main() -> None:
    out_dir = DATA / "aggregated" / "perturbation_dose_response"
    out_dir.mkdir(parents=True, exist_ok=True)

    panel_a = _load_panel_a()
    panel_b = _load_panel_b()

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.2))

    # ---- Panel A: raw switching dose response (orientation) ----
    series = [
        ("D1 dialog",   "neutral",     "#2ca02c", "o"),
        ("O1 continue", "neutral",     "#1f77b4", "s"),
        ("O1 continue", "adversarial", "#d62728", "^"),
    ]
    def _wilson(p, n, z=1.959963984540054):
        if n == 0:
            return (float("nan"), float("nan"))
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
        return (max(0.0, center - half), min(1.0, center + half))

    for regime, ptype, color, marker in series:
        sub = panel_a[(panel_a["regime_label"] == regime) &
                      (panel_a["perturbation_type"] == ptype)].copy()
        sub = sub.dropna(subset=["dose"]).sort_values("dose")
        if sub.empty:
            continue
        x = sub["dose"].to_numpy()
        y = sub["switch_rate"].to_numpy()
        # Compute Wilson CI from n_switched / n_total
        cis = [_wilson(p, int(n)) for p, n in zip(y, sub["n_total"])]
        lo = np.array([c[0] for c in cis])
        hi = np.array([c[1] for c in cis])
        label = f"{regime.split()[0]} / {ptype}"
        ax_a.errorbar(x, y, yerr=[y - lo, hi - y], fmt=f"{marker}-",
                      color=color, lw=1.6, markersize=6, capsize=3, label=label)
    ax_a.axhline(0.5, color="grey", linestyle=":", lw=0.8, zorder=0)
    ax_a.set_xscale("log")
    ax_a.set_xticks([5, 10, 20, 50, 80, 200, 400])
    ax_a.set_xticklabels(["5", "10", "20", "50", "80", "200", "400"])
    ax_a.set_xlabel("perturbation dose (tokens) - log scale")
    ax_a.set_ylabel("fraction of trajectories switching basin")
    ax_a.set_ylim(0, 1.0)
    ax_a.grid(axis="y", linestyle=":", alpha=0.4)
    ax_a.set_title("(A) Raw switching dose response (bounded-memory, doses 5-400)",
                   fontsize=10)
    ax_a.legend(fontsize=9, loc="upper left")

    # ---- Panel B: persistence dose response, three curves ----
    # Combine the two full-history experiments into one dataset (same protocol;
    # only per-cell N differs).
    bounded = _decompose_persistence("exp_perturb_O1_ed50_dense")
    fh_low  = _decompose_persistence("exp_perturb_O1_ed50_dense_noclip")
    fh_high = _decompose_persistence("exp_perturb_O1_ed50_higher_noclip")
    full_history = pd.concat([fh_low, fh_high], ignore_index=True).sort_values("dose")

    # Bounded memory, strict measure
    x = bounded["dose"].to_numpy()
    y = bounded["pct_strict"].to_numpy()
    lo = bounded["strict_lo"].to_numpy()
    hi = bounded["strict_hi"].to_numpy()
    ax_b.errorbar(x, y, yerr=[y - lo, hi - y], fmt="s-",
                  color="#1f77b4", lw=1.6, markersize=6, capsize=3,
                  label="bounded memory, destination-coherent")

    # Full-history, strict measure
    x = full_history["dose"].to_numpy()
    y = full_history["pct_strict"].to_numpy()
    lo = full_history["strict_lo"].to_numpy()
    hi = full_history["strict_hi"].to_numpy()
    ax_b.errorbar(x, y, yerr=[y - lo, hi - y], fmt="o-",
                  color="#d62728", lw=1.6, markersize=6, capsize=3,
                  label="full-history, destination-coherent")

    # Full-history, loose measure (kicked & not returned to original)
    x = full_history["dose"].to_numpy()
    y = full_history["pct_loose"].to_numpy()
    lo = full_history["loose_lo"].to_numpy()
    hi = full_history["loose_hi"].to_numpy()
    ax_b.errorbar(x, y, yerr=[y - lo, hi - y], fmt="^-",
                  color="#9467bd", lw=1.6, markersize=6, capsize=3,
                  label="full-history, retained source-basin escape")

    # Step-79 overlay: same destination-coherent metric, but scored 50 steps
    # later (T=79 instead of T=29). Three points at doses 1500/2000/3000 from
    # the long-horizon continuation, frozen canonical PCA + K-means basis.
    # Visualizes the §5.1.3 finding that the canonical-T=29 dip closes by T=79.
    step79_path = DATA / "aggregated" / "dip_mechanism_B" / "persistence_by_terminal_step_v2.csv"
    if step79_path.exists():
        step79 = pd.read_csv(step79_path)
        sub = step79[(step79["basis"] == "frozen") &
                     (step79["terminal_step"] == 79)].sort_values("dose")
        if not sub.empty:
            x79 = sub["dose"].to_numpy()
            y79 = sub["S_dst"].to_numpy()
            lo79 = np.array([
                _wilson(p, int(n))[0] for p, n in zip(y79, sub["n_kicked"])
            ])
            hi79 = np.array([
                _wilson(p, int(n))[1] for p, n in zip(y79, sub["n_kicked"])
            ])
            ax_b.errorbar(x79, y79, yerr=[y79 - lo79, hi79 - y79], fmt="D-",
                          color="#d62728", markerfacecolor="white",
                          markeredgewidth=1.8, markersize=8, lw=1.0,
                          capsize=3, alpha=0.95,
                          label=("full-history, destination-coherent at T=79\n"
                                 "(frozen canonical basis; the canonical T=29\n"
                                 "dip largely closes — see Fig 6)"))

    ax_b.axhline(0.5, color="grey", linestyle=":", lw=0.9, zorder=0,
                 label="50% half-effect threshold")
    ax_b.axvline(1500, color="black", linestyle="--", lw=0.7, alpha=0.5, zorder=0)
    ax_b.text(1500, 0.96, "1500", ha="center", va="bottom", fontsize=8, color="black",
              alpha=0.6)
    ax_b.set_xscale("log")
    ax_b.set_xticks([20, 80, 200, 400, 1000, 2000, 3000])
    ax_b.set_xticklabels(["20", "80", "200", "400", "1000", "2000", "3000"])
    ax_b.set_xlabel("perturbation dose (tokens) - log scale")
    ax_b.set_ylabel("persistent-escape rate (Wilson 95% CI)")
    ax_b.set_ylim(0, 1.0)
    ax_b.grid(axis="y", linestyle=":", alpha=0.4)
    ax_b.set_title(
        "(B) Persistent escape, O1 adversarial - the bounded-memory plateau\n"
        "is a memory-policy artifact (context_tail observable)",
        fontsize=10,
    )
    ax_b.legend(fontsize=8, loc="upper left")

    fig.tight_layout()
    out_png = out_dir / "dose_response_2panel.png"
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
