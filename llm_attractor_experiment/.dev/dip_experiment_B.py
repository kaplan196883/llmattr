"""Experiment B - long-horizon trajectory continuation.

Test mechanism 5 (finite-horizon relaxation): extend high-dose trajectories
beyond step 29 to see if the destination-coherent persistence dip at dose
2000 fades when the loop has more time to settle.

Loads step-29 final context from the existing
exp_perturb_O1_ed50_higher_noclip experiment for doses 1500 / 2000 / 3000,
then generates 50 more steps using the same generator, sampling, and loop
parameters. Saves new step records to
data/exp_perturb_O1_ed50_higher_noclip_extended/raw/steps.jsonl.

After generation, run the same context_tail embedding pipeline on the
extended steps, then recompute destination-coherent persistence at terminal
steps {29, 40, 50, 60, 70, 80}. If S_dst(2000) at step 80 has caught up to
S_dst(1500) at step 80, mechanism 5 is supported.

Cost estimate: 5 fams x 10 ICs x 2 runs x 3 doses = 300 trajectories x 50
steps = 15,000 generation calls at gpt-4o-mini (~$0.0001/call) = ~$1.50.
Plus context_tail embedding for 15,000 step records at
text-embedding-3-small (~$0.0001 per 1K tokens, ~250 tokens per step) =
~$0.40. Total ~$2.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.openai_client import make_generation_client  # noqa: E402

DATA = ROOT / "data"
SRC_EXP_DIR = DATA / "exp_perturb_O1_ed50_higher_noclip"
DST_EXP_DIR = DATA / "exp_perturb_O1_ed50_higher_noclip_extended"
DST_RAW = DST_EXP_DIR / "raw"

TARGET_DOSES = (1500, 2000, 3000)
EXTRA_STEPS = 50  # extend from step 30 to step 79 inclusive
ORIGINAL_TERMINAL_STEP = 29
NEW_TERMINAL_STEP = ORIGINAL_TERMINAL_STEP + EXTRA_STEPS  # 79

GEN_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.8
TOP_P = 1.0
MAX_OUTPUT_TOKENS = 120
SYSTEM_PROMPT = "Continue the text naturally. Do not summarize or explain."
PARALLEL = 24


def _final_states_per_traj(steps_path: Path) -> list[dict]:
    """Yield, for each (regime in TARGET_DOSES, fam, ic, run), the step-29
    record. We need:
      - regime, prompt_family, initial_condition_id, run_id (identity)
      - context_after at step 29 (becomes the seed for step 30)
    """
    by_traj: dict[tuple, dict] = {}
    target_regimes = {f"adversarial_dose{d}" for d in TARGET_DOSES}
    with steps_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d["regime"] not in target_regimes:
                continue
            if d["step"] != ORIGINAL_TERMINAL_STEP:
                continue
            key = (d["regime"], d["prompt_family"], d["initial_condition_id"], d["run_id"])
            by_traj[key] = d
    return list(by_traj.values())


def _continue_one(spec: dict, client) -> list[dict]:
    """Generate steps 30..79 for one trajectory, append-mode."""
    out_steps: list[dict] = []
    context = spec["context_after"]
    for step in range(ORIGINAL_TERMINAL_STEP + 1, NEW_TERMINAL_STEP + 1):
        t0 = time.time()
        resp = client.chat.completions.create(
            model=GEN_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        latency = time.time() - t0
        output_text = resp.choices[0].message.content or ""
        new_context = context + output_text
        out_steps.append({
            "experiment_id": "exp_perturb_O1_ed50_higher_noclip_extended",
            "prompt_family": spec["prompt_family"],
            "initial_condition_id": spec["initial_condition_id"],
            "run_id": spec["run_id"],
            "regime": spec["regime"],
            "step": step,
            "context_before": context,
            "output_text": output_text,
            "context_after": new_context,
            "model": GEN_MODEL,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "latency_sec": latency,
            "loop_mode": "append",
            "is_perturbation_step": False,
            "perturbed_step": 15,
            "perturbation_condition": spec["regime"],
            "context_length_chars": len(context),
            "timestamp": time.time(),
        })
        context = new_context
    return out_steps


def cmd_run() -> None:
    DST_RAW.mkdir(parents=True, exist_ok=True)
    out_jsonl = DST_RAW / "steps.jsonl"
    seen_keys: set[tuple] = set()
    if out_jsonl.exists():
        with out_jsonl.open("r", encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                seen_keys.add((d["regime"], d["prompt_family"], d["initial_condition_id"],
                               d["run_id"], d["step"]))
        print(f"resuming: {len(seen_keys)} existing extended-step records found")

    src_steps = SRC_EXP_DIR / "raw" / "steps.jsonl"
    finals = _final_states_per_traj(src_steps)
    print(f"loaded {len(finals)} step-29 anchors across doses {TARGET_DOSES}")

    client = make_generation_client()  # default provider = OpenAI
    write_lock = threading.Lock()
    total_steps_written = 0
    failed = 0

    def _worker(spec: dict) -> tuple[str, int]:
        key = (spec["regime"], spec["prompt_family"],
               spec["initial_condition_id"], spec["run_id"])
        # Skip if all 50 extension steps already exist
        existing = sum(1 for s in range(ORIGINAL_TERMINAL_STEP + 1,
                                        NEW_TERMINAL_STEP + 1)
                       if (*key, s) in seen_keys)
        if existing == EXTRA_STEPS:
            return "skipped", 0
        try:
            new_steps = _continue_one(spec, client)
            with write_lock:
                with out_jsonl.open("a", encoding="utf-8") as fh:
                    for d in new_steps:
                        fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            return "completed", len(new_steps)
        except Exception as exc:
            print(f"FAIL {key}: {exc}")
            return "failed", 0

    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        futs = {ex.submit(_worker, s): s for s in finals}
        for i, fut in enumerate(as_completed(futs), 1):
            status, n = fut.result()
            total_steps_written += n
            if status == "failed":
                failed += 1
            if i % 25 == 0 or i == len(futs):
                print(f"  progress: {i}/{len(futs)} trajectories  "
                      f"steps_written={total_steps_written}  failed={failed}")

    print(f"\ndone. total extended-step records written: {total_steps_written}, "
          f"failed: {failed}")


def cmd_embed() -> None:
    """Embed context_tail of extended trajectories using text-embedding-3-small."""
    from src.api.openai_client import make_embedding_client  # noqa: WPS433

    out_jsonl = DST_RAW / "steps.jsonl"
    rows = []
    with out_jsonl.open("r", encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    print(f"loaded {len(df)} extended step records")

    # Build context_tail: last 4000 chars of context_after (matches the canonical
    # observable definition in the paper)
    df["text"] = df["context_after"].apply(lambda s: s[-4000:] if isinstance(s, str) else "")
    df = df.sort_values(["regime", "prompt_family", "initial_condition_id", "run_id", "step"]).reset_index(drop=True)

    client = make_embedding_client()
    texts = df["text"].tolist()
    print(f"embedding {len(texts)} texts (text-embedding-3-small) in batches of 100...")
    BATCH = 100
    chunks = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        resp = client.embeddings.create(model="text-embedding-3-small", input=batch)
        chunks.extend([d.embedding for d in resp.data])
        if (i // BATCH) % 10 == 0:
            print(f"  embedded {i + len(batch)}/{len(texts)}")
    X = np.asarray(chunks, dtype=np.float32)
    print(f"got embeddings: shape={X.shape}")

    obs_dir = DST_EXP_DIR / "embeddings" / "context_tail"
    obs_dir.mkdir(parents=True, exist_ok=True)
    np.save(obs_dir / "embeddings.npy", X)
    df[["regime", "prompt_family", "initial_condition_id", "run_id", "step"]].to_parquet(
        obs_dir / "metadata.parquet", index=False
    )
    print(f"wrote {obs_dir/'embeddings.npy'} and metadata.parquet")


def cmd_analyze() -> None:
    """Recompute destination-coherent persistence at multiple terminal steps.

    We need both the step-29 (immediate post-injection) cluster from the
    ORIGINAL experiment AND the terminal clusters from the EXTENDED
    experiment. To keep the cluster geometry consistent, we joint-fit
    PCA-10 + K-means k=12 on the union of the two embedding sets, then
    score persistence at terminal steps {29, 40, 50, 60, 70, 80}.
    """
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    print("=" * 70)
    print("Experiment B - persistence vs terminal step")
    print("=" * 70)

    # Load original (steps 0-29) and extended (steps 30-79) for high-dose regimes only
    target_regimes = {f"adversarial_dose{d}" for d in TARGET_DOSES}

    X_orig = np.load(SRC_EXP_DIR / "embeddings" / "context_tail" / "embeddings.npy")
    meta_orig = pd.read_parquet(SRC_EXP_DIR / "embeddings" / "context_tail" / "metadata.parquet")
    keep_orig = meta_orig["regime"].isin(target_regimes).to_numpy()
    X_orig = X_orig[keep_orig]
    meta_orig = meta_orig.loc[keep_orig].reset_index(drop=True)
    meta_orig["src"] = "orig"
    print(f"original: kept {len(meta_orig)} rows for high-dose regimes")

    X_ext = np.load(DST_EXP_DIR / "embeddings" / "context_tail" / "embeddings.npy")
    meta_ext = pd.read_parquet(DST_EXP_DIR / "embeddings" / "context_tail" / "metadata.parquet")
    meta_ext["src"] = "ext"
    print(f"extended: kept {len(meta_ext)} rows")

    X_all = np.vstack([X_orig, X_ext])
    meta_all = pd.concat([meta_orig, meta_ext], ignore_index=True)

    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X_all)
    km = KMeans(n_clusters=12, random_state=42, n_init=10)
    meta_all["cluster"] = km.fit_predict(Xp)

    pivot = meta_all.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    print(f"available terminal steps: {sorted(pivot.columns)}")

    test_steps = [29, 40, 50, 60, 70, 79]
    test_steps = [s for s in test_steps if s in pivot.columns]
    print(f"scoring at terminal steps: {test_steps}\n")

    print(f"{'dose':>5}  {'T':>3}  " + "  ".join(f"S^dst@{t:>2}" for t in test_steps))
    rows = []
    for dose in TARGET_DOSES:
        regime = f"adversarial_dose{dose}"
        sub = pivot[pivot.index.get_level_values("regime") == regime]
        line = f"{dose:>5}  "
        for t in test_steps:
            scores = []
            for idx, srow in sub.iterrows():
                pre = srow.get(14)
                post = srow.get(15)
                end = srow.get(t)
                if pd.isna(pre) or pd.isna(post) or pd.isna(end):
                    continue
                if int(post) == int(pre):
                    continue
                scores.append(int(end == post))
            if scores:
                p = float(np.mean(scores))
                rows.append({"dose": dose, "terminal_step": t, "S_dst": p,
                             "n_kicked": len(scores)})
                line += f"  {p:.3f}"
            else:
                line += "  --"
        print(line)

    df_out = pd.DataFrame(rows)
    out_dir = DATA / "aggregated" / "dip_mechanism_B"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_dir / "persistence_by_terminal_step.csv", index=False)
    print(f"\nwrote {out_dir/'persistence_by_terminal_step.csv'}")

    print("\n" + "=" * 70)
    print("VERDICT (mechanism 5: finite-horizon relaxation)")
    print("=" * 70)
    if df_out.empty:
        print("  no data; skipping verdict.")
        return
    pv = df_out.pivot(index="terminal_step", columns="dose", values="S_dst")
    print("\nDip magnitude vs terminal step:")
    print(f"{'T':>3}  {'S_1500':>8}  {'S_2000':>8}  {'S_3000':>8}  {'dip':>8}")
    for t in pv.index:
        if all(d in pv.columns for d in TARGET_DOSES):
            s1500, s2000, s3000 = pv.at[t, 1500], pv.at[t, 2000], pv.at[t, 3000]
            dip = s2000 - 0.5 * (s1500 + s3000)
            print(f"{t:>3}  {s1500:>8.3f}  {s2000:>8.3f}  {s3000:>8.3f}  {dip:>+8.3f}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["run", "embed", "analyze", "all"])
    args = p.parse_args()
    if args.command in ("run", "all"):
        cmd_run()
    if args.command in ("embed", "all"):
        cmd_embed()
    if args.command in ("analyze", "all"):
        cmd_analyze()
    return 0


if __name__ == "__main__":
    sys.exit(main())
