"""
Embedding-space invariance ablation.

For each of 5 representative experiments (one per regime: O1, O2, O3,
D1, D2) and 2 alternative embedding models (`text-embedding-3-large`
via OpenAI, `all-mpnet-base-v2` via sentence-transformers), we re-embed
a 5,000-step subsample (stratified by prompt_family × initial_condition_id)
and recompute the 3 canonical diagnostics:

    - recurrence_rate (PCA-10, cosine, ε=0.15, τ=3)
    - sharpness_dim_late (from ensemble PCA-10 spread covariance)
    - basin_predictability_acc(k=10) (KMeans k=12 on late window;
      LR predict from PCA-10 at step 10; 5-fold CV with singleton drop)

Question: does the regime taxonomy (4-regime ordering on each
diagnostic) survive the embedding-model swap?

Outputs:
  data/aggregated/embedding_ablation/results.csv          per-cell metrics
  data/aggregated/embedding_ablation/comparison.md         human-readable
  data/aggregated/embedding_ablation/comparison.png        bar plot

Usage:
    python -m scripts.embedding_ablation
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT_DIR = DATA / "aggregated" / "embedding_ablation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Subsample size per experiment (stratified by family × IC)
N_SAMPLE = 5000

EXPERIMENTS = [
    ("O1", "exp_pub_O1_continue"),
    ("O2", "exp_pub_O2_paraphrase_replace"),
    ("O3", "exp_pub_O3_summarize_negate_replace"),
    ("D1", "exp_pub_D1_dialog_curious_helpful_v2"),
    ("D2", "exp_perturb_D2_exploratory"),
]


def load_steps_subsample(exp_id: str, n_sample: int = N_SAMPLE,
                         regime_filter: str | None = None) -> pd.DataFrame:
    """Load step records as a DataFrame, subsampled stratified by
    (prompt_family, initial_condition_id) to n_sample rows total."""
    p = DATA / exp_id / "raw" / "steps.jsonl"
    if not p.exists():
        raise FileNotFoundError(p)
    rows = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if regime_filter and r.get("regime") != regime_filter:
                continue
            rows.append(r)
    df = pd.DataFrame(rows)
    if len(df) <= n_sample:
        return df
    # Stratified subsample: take a proportional share from each
    # (prompt_family, initial_condition_id, run_id) group, preserving
    # all steps within a sampled trajectory so observable-rolling
    # logic stays well-defined.
    if "run_id" in df.columns:
        traj_keys = df.groupby(["prompt_family", "initial_condition_id", "run_id"]).size()
        steps_per_traj = int(traj_keys.median())
        n_trajs = max(1, n_sample // max(steps_per_traj, 1))
        keys = traj_keys.index.tolist()
        rng = np.random.default_rng(42)
        chosen = rng.choice(len(keys), size=min(n_trajs, len(keys)), replace=False)
        chosen_keys = set(keys[i] for i in chosen)
        mask = df.apply(
            lambda r: (r.prompt_family, r.initial_condition_id, r.run_id) in chosen_keys,
            axis=1,
        )
        return df[mask].reset_index(drop=True)
    # fallback: uniform
    return df.sample(n_sample, random_state=42).reset_index(drop=True)


def build_context_tail(df: pd.DataFrame, tail_chars: int = 4000) -> list[str]:
    """Build the canonical context_tail observable string per step."""
    return [
        (row.get("context_after") or "")[-tail_chars:] or " "
        for _, row in df.iterrows()
    ]


def embed_local(texts: list[str], model_name: str,
                batch_size: int = 64) -> np.ndarray:
    """Encode with a sentence-transformers model. Returns
    (n, d) float32, L2-normalized to match OpenAI's normalization."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    arr = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return arr.astype(np.float32)


def embed_openai_alt(texts: list[str], model_name: str) -> np.ndarray:
    """Embed via OpenAI API with a specific model (e.g.,
    text-embedding-3-large). Bypasses src.config to allow per-call
    model override."""
    import os
    from src.api.openai_client import _load_env
    _load_env()
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    out = []
    BATCH = 128
    for i in range(0, len(texts), BATCH):
        batch = [t or " " for t in texts[i:i + BATCH]]
        resp = client.embeddings.create(model=model_name, input=batch)
        out.extend([np.array(d.embedding, dtype=np.float32) for d in resp.data])
    arr = np.stack(out)
    norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return (arr / norms).astype(np.float32)


def compute_recurrence(emb: np.ndarray, df: pd.DataFrame,
                       eps: float = 0.15, tau: int = 3) -> float:
    """Per-trajectory cosine recurrence rate, averaged across
    trajectories. Cosine similarity within trajectory; pairs with
    |i-j| >= tau and similarity >= 1-eps count as recurrent."""
    rates = []
    for _, traj in df.groupby(["prompt_family", "initial_condition_id", "run_id"]):
        idxs = traj.index.to_numpy()
        if len(idxs) < 2 * tau + 2:
            continue
        v = emb[idxs]
        # cosine = dot since vectors are unit-normalized
        sim = v @ v.T
        n = len(idxs)
        # mask of valid pairs (i,j) with j > i + tau
        ii, jj = np.indices((n, n))
        mask = jj > ii + tau
        if not mask.any():
            continue
        recurrent = (sim >= 1 - eps) & mask
        n_pairs = int(mask.sum())
        n_rec = int(recurrent.sum())
        rates.append(n_rec / max(n_pairs, 1))
    return float(np.mean(rates)) if rates else float("nan")


def compute_sharpness_dim_late(emb: np.ndarray, df: pd.DataFrame,
                                pca_dim: int = 10,
                                late_fraction: float = 0.7) -> float:
    """Late-window ensemble sharpness dimension. For each (family,
    IC) ensemble of trajectories, compute PCA-10 spread covariance
    over the late window's first 5 steps, return effective rank
    (Shannon-entropy-equivalent dimension)."""
    pca = PCA(n_components=min(pca_dim, emb.shape[0] - 1, emb.shape[1]))
    Z = pca.fit_transform(emb)
    sds = []
    for (fam, ic), grp in df.groupby(["prompt_family", "initial_condition_id"]):
        # Get trajectories in this ensemble
        traj_steps_per = []
        for run_id, traj in grp.groupby("run_id"):
            traj_sorted = traj.sort_values("step")
            traj_steps_per.append(Z[traj_sorted.index.to_numpy()])
        if len(traj_steps_per) < 2:
            continue
        T = min(len(t) for t in traj_steps_per)
        if T < 5:
            continue
        late_start = int(late_fraction * T)
        if late_start >= T - 4:
            late_start = max(0, T - 5)
        # Stack late window (n_traj, late_steps, pca_dim)
        late = np.stack([t[late_start:late_start + 5] for t in traj_steps_per])
        # Per-step covariance averaged across late steps
        cov_acc = np.zeros((Z.shape[1], Z.shape[1]))
        for step_idx in range(late.shape[1]):
            X = late[:, step_idx, :]
            mu = X.mean(axis=0)
            cov_acc += (X - mu).T @ (X - mu) / max(X.shape[0] - 1, 1)
        cov_acc /= late.shape[1]
        eigs = np.linalg.eigvalsh(cov_acc)
        eigs = eigs[eigs > 1e-12]
        if len(eigs) == 0:
            continue
        p = eigs / eigs.sum()
        # Effective rank (entropy-based dimension)
        H = -(p * np.log(p)).sum()
        sds.append(np.exp(H))
    return float(np.mean(sds)) if sds else float("nan")


def compute_basin_predictability_k10(emb: np.ndarray, df: pd.DataFrame,
                                      pca_dim: int = 10,
                                      n_clusters: int = 12,
                                      late_fraction: float = 0.7,
                                      k_predictor: int = 10) -> float:
    """basin_pred acc(k=10): cluster trajectories' late-window
    centroids; classify from PCA-10 at step k=10."""
    pca = PCA(n_components=min(pca_dim, emb.shape[0] - 1, emb.shape[1]))
    Z = pca.fit_transform(emb)
    # Per-trajectory: late centroid + step-10 vector
    late_centroids = []
    early_vecs = []
    traj_keys = []
    for traj_key, traj in df.groupby(["prompt_family", "initial_condition_id", "run_id"]):
        ts = traj.sort_values("step")
        idxs = ts.index.to_numpy()
        if len(idxs) < k_predictor + 2:
            continue
        Zt = Z[idxs]
        T = len(Zt)
        late_start = int(late_fraction * T)
        if late_start >= T - 1:
            late_start = max(0, T - 2)
        late_centroid = Zt[late_start:].mean(axis=0)
        # Step k_predictor (or closest available)
        steps_array = ts.step.to_numpy()
        if k_predictor not in steps_array:
            # closest
            diffs = np.abs(steps_array - k_predictor)
            k_idx = int(np.argmin(diffs))
        else:
            k_idx = int(np.where(steps_array == k_predictor)[0][0])
        early_vec = Zt[k_idx]
        late_centroids.append(late_centroid)
        early_vecs.append(early_vec)
        traj_keys.append(traj_key)
    if len(late_centroids) < n_clusters:
        return float("nan")
    LC = np.stack(late_centroids)
    EV = np.stack(early_vecs)
    # Cluster the late centroids
    km = KMeans(n_clusters=n_clusters, n_init=20, random_state=42).fit(LC)
    y = km.labels_
    # Drop singleton classes
    unique, counts = np.unique(y, return_counts=True)
    keep = unique[counts >= 2]
    keep_mask = np.isin(y, keep)
    if keep_mask.sum() < n_clusters or len(keep) < 2:
        return float("nan")
    X = EV[keep_mask]
    yk = y[keep_mask]
    n_splits = min(5, int(np.unique(yk, return_counts=True)[1].min()))
    if n_splits < 2:
        return float("nan")
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    accs = []
    for tr, te in kf.split(X, yk):
        clf = LogisticRegression(max_iter=2000, n_jobs=-1, C=1.0).fit(X[tr], yk[tr])
        accs.append(float(clf.score(X[te], yk[te])))
    return float(np.mean(accs))


def run_one_cell(regime: str, exp_id: str, model_tag: str) -> dict:
    """Run one (experiment × alternative-model) ablation cell.
    Returns a row dict for the results CSV."""
    print(f"[{regime} / {model_tag}] loading & subsampling…", flush=True)
    df = load_steps_subsample(exp_id, regime_filter="recursive" if "perturb" not in exp_id else "control")
    if len(df) == 0:
        # fall back: any regime
        df = load_steps_subsample(exp_id, regime_filter=None)
    print(f"  loaded {len(df)} steps after subsample (filter recursive/control)", flush=True)
    texts = build_context_tail(df, tail_chars=4000)
    print(f"  embedding {len(texts)} texts with {model_tag}…", flush=True)
    t0 = time.monotonic()
    if model_tag == "text-embedding-3-large":
        emb = embed_openai_alt(texts, "text-embedding-3-large")
    elif model_tag == "all-mpnet-base-v2":
        emb = embed_local(texts, "sentence-transformers/all-mpnet-base-v2")
    else:
        raise ValueError(f"unknown model_tag {model_tag}")
    embed_t = time.monotonic() - t0
    print(f"  embeddings shape {emb.shape}, {embed_t:.1f}s", flush=True)
    rec = compute_recurrence(emb, df)
    sd = compute_sharpness_dim_late(emb, df)
    bp = compute_basin_predictability_k10(emb, df)
    print(f"  rec={rec:.3f}  sd_late={sd:.3f}  basin_pred(k=10)={bp:.3f}", flush=True)
    return {
        "regime": regime,
        "experiment_id": exp_id,
        "embedding_model": model_tag,
        "embedding_dim": int(emb.shape[1]),
        "n_steps": int(len(df)),
        "embed_seconds": round(embed_t, 1),
        "recurrence_rate": rec,
        "sharpness_dim_late": sd,
        "basin_pred_acc_k10": bp,
    }


def baseline_row(regime: str, exp_id: str) -> dict:
    """Read the 3 canonical diagnostics for the baseline
    (text-embedding-3-small) from the existing on-disk CSVs."""
    # recurrence_rate
    rec_path = DATA / exp_id / "metrics" / "recurrence.csv"
    rec = float("nan")
    if rec_path.exists():
        df = pd.read_csv(rec_path)
        canonical_regime = "control" if "perturb" in exp_id else "recursive"
        sub = df[(df.observable == "context_tail") & (df.space == "pca10") & (df.regime == canonical_regime)]
        if len(sub):
            rec = float(sub.recurrence_rate.mean())

    # sharpness_dim_late
    dyn_path = DATA / exp_id / "metrics" / "dynamics.csv"
    sd = float("nan")
    if dyn_path.exists():
        df = pd.read_csv(dyn_path)
        canonical_regime = "control" if "perturb" in exp_id else "recursive"
        sub = df[(df.observable == "context_tail") & (df.regime == canonical_regime)]
        if len(sub):
            sd = float(sub.sharpness_dim_late.mean())

    # basin_pred_acc(k=10)
    bp_path = DATA / exp_id / "reports" / "basin_predictability" / "basin_predictability.csv"
    bp = float("nan")
    if bp_path.exists():
        df = pd.read_csv(bp_path)
        canonical_regime = "control" if "perturb" in exp_id else "recursive"
        sub = df[(df.observable == "context_tail") & (df.regime == canonical_regime) & (df.step == 10)]
        if len(sub) and not pd.isna(sub.top1.iloc[0]):
            bp = float(sub.top1.iloc[0])

    return {
        "regime": regime,
        "experiment_id": exp_id,
        "embedding_model": "text-embedding-3-small",
        "embedding_dim": 1536,
        "n_steps": -1,
        "embed_seconds": 0,
        "recurrence_rate": rec,
        "sharpness_dim_late": sd,
        "basin_pred_acc_k10": bp,
    }


def make_comparison_plot(df: pd.DataFrame) -> None:
    """3 panels (rec, sd_late, basin_pred), grouped bars per regime
    × embedding model."""
    metrics = ["recurrence_rate", "sharpness_dim_late", "basin_pred_acc_k10"]
    titles = ["Recurrence rate (PCA-10)", "Sharpness dim_late", "Basin pred acc(k=10)"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    regimes = ["O1", "O2", "O3", "D1", "D2"]
    models = ["text-embedding-3-small", "text-embedding-3-large", "all-mpnet-base-v2"]
    colors = ["#4a90e2", "#e24a4a", "#5fa85f"]
    width = 0.27
    x = np.arange(len(regimes))
    for ax, metric, title in zip(axes, metrics, titles):
        for i, model in enumerate(models):
            vals = []
            for r in regimes:
                row = df[(df.regime == r) & (df.embedding_model == model)]
                vals.append(float(row[metric].iloc[0]) if len(row) else float("nan"))
            ax.bar(x + (i - 1) * width, vals, width=width, label=model, color=colors[i])
        ax.set_xticks(x)
        ax.set_xticklabels(regimes)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "comparison.png", dpi=120)
    plt.close(fig)


def _load_existing(out_path: Path) -> list[dict]:
    if not out_path.exists():
        return []
    try:
        existing = pd.read_csv(out_path)
        return existing.to_dict("records")
    except Exception:
        return []


def _save_rows(rows: list[dict], out_path: Path) -> None:
    pd.DataFrame(rows).to_csv(out_path, index=False)


def main() -> int:
    out_csv = OUT_DIR / "results.csv"
    rows = _load_existing(out_csv)
    done = {(r["regime"], r["embedding_model"]) for r in rows}
    print(f"=== Resume from existing results.csv ({len(rows)} rows already saved) ===")

    print("=== Loading baseline (text-embedding-3-small) from existing CSVs ===")
    for regime, exp_id in EXPERIMENTS:
        if (regime, "text-embedding-3-small") in done:
            print(f"  skip {regime} / text-embedding-3-small (already saved)")
            continue
        rows.append(baseline_row(regime, exp_id))
        _save_rows(rows, out_csv)

    alt_models = ["text-embedding-3-large", "all-mpnet-base-v2"]
    for model_tag in alt_models:
        print(f"\n=== Running {model_tag} ablation ===")
        for regime, exp_id in EXPERIMENTS:
            if (regime, model_tag) in done:
                print(f"  skip {regime} / {model_tag} (already saved)")
                continue
            try:
                row = run_one_cell(regime, exp_id, model_tag)
            except Exception as e:
                print(f"  [{regime} / {model_tag}] FAILED: {type(e).__name__}: {e}")
                row = {
                    "regime": regime, "experiment_id": exp_id,
                    "embedding_model": model_tag, "embedding_dim": -1,
                    "n_steps": 0, "embed_seconds": 0,
                    "recurrence_rate": float("nan"),
                    "sharpness_dim_late": float("nan"),
                    "basin_pred_acc_k10": float("nan"),
                }
            rows.append(row)
            _save_rows(rows, out_csv)
            print(f"  saved {len(rows)} rows so far")

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"\nwrote {OUT_DIR / 'results.csv'}")

    # Comparison plot
    make_comparison_plot(df)
    print(f"wrote {OUT_DIR / 'comparison.png'}")

    # Markdown comparison
    pivot = df.pivot_table(
        index="regime",
        columns="embedding_model",
        values=["recurrence_rate", "sharpness_dim_late", "basin_pred_acc_k10"],
    ).round(3)
    md_lines = ["# Embedding-space invariance ablation",
                "",
                "Per-regime canonical diagnostics under three embedding models:",
                "- `text-embedding-3-small` (1536-dim, OpenAI) — baseline (from existing on-disk metrics)",
                "- `text-embedding-3-large` (3072-dim, OpenAI) — within-vendor scale-up",
                "- `all-mpnet-base-v2` (768-dim, sentence-transformers, local) — cross-architecture",
                "",
                "## Results", "",
                pivot.to_markdown(),
                ""]
    (OUT_DIR / "comparison.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"wrote {OUT_DIR / 'comparison.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
