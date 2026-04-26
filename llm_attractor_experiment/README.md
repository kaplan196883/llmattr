# LLM Attractor Experiment

Tests **Hypothesis 1**: in a bounded append-only recursive LLM loop, there exist
endogenous attractor-like regimes that become observable in a suitable
representation space.

The experiment runs many recursive trajectories:

```
Y_t ~ P_theta(. | X_t, N)
X_{t+1} = clip(X_t || Y_t)
```

and then builds embeddings for several observables, runs PCA, clustering,
recurrence / dwell / basin metrics, compares to baselines, and writes a
markdown report classifying the evidence as `not supported`, `weak`,
`moderate`, or `strong`.

## Install

```bash
pip install -r requirements.txt
cp .env.example .env      # then edit OPENAI_API_KEY
```

The code loads `.env` from the project root or any parent of the working
directory, so a key at `d:\ROOT\llmattr\.env` is picked up automatically.

## CLI

```bash
python -m src.main run      --config configs/default.yaml
python -m src.main embed    --config configs/default.yaml
python -m src.main analyze  --config configs/default.yaml
python -m src.main report   --config configs/default.yaml
python -m src.main all      --config configs/default.yaml
python -m src.main resume   --config configs/default.yaml
```

`all` runs `run -> embed -> analyze -> report` in sequence. `resume` picks up
trajectories not yet completed (checkpointed after each finished run).

## Output layout

```
data/<experiment_id>/
  config.yaml                # frozen snapshot of the config used
  raw/
    steps.jsonl              # one record per generation step
    manifest.json            # run_id -> status, step counts
  embeddings/
    <observable>/
      embeddings.npy
      metadata.parquet
  metrics/
    pca_<dim>_<observable>.csv
    recurrence.csv
    dwell.csv
    basin.csv
  reports/
    plots/*.png
    report.md
```

## Hard rules

- no server-side chat state; context is always rebuilt client-side
- PCA is fit jointly on all trajectories for a given observable, never per-run
- evidence requires at least two observables and at least one non-PCA-2 space
- baselines are mandatory

See `configs/default.yaml` for the full set of tunable parameters.

## Documentation

- `docs/DATA_INDEX.md` — catalog of every experiment under `data/` (Phase 0–3)
- `docs/REQ1_MAPPING.md` — original requirements traceability
- `docs/reports/REPORT1.md` … `REPORT6.md` — narrative writeups, one per project stage:
  - `REPORT1` — first run on `exp_default`, baseline classification
  - `REPORT2` — long-horizon + clipping ablations
  - `REPORT3` — dynamical-systems metrics (Lyapunov, sharpness)
  - `REPORT4` — operator regime classification
  - `REPORT5` — publication-scale verification of all four regimes
  - `REPORT6` — perturbation experiments and basin-hijacking

## Repository layout

```
llm_attractor_experiment/
├── README.md, requirements.txt
├── docs/                     # narrative writeups + data index
├── src/                      # library code (analysis, api, core, experiments, utils)
│   └── experiments/
│       ├── dialog/           # D1/D2/D3 dialog runners
│       ├── operators/        # O1–O4 operator runners
│       ├── dynamics/         # post-hoc dynamical-systems analysis CLIs
│       └── perturbation/     # perturbation runners + holographic-bulk plots
├── scripts/                  # standalone aggregators + config builders
├── configs/                  # entry-point configs + dialog/operators/perturbation/archive subdirs
├── tests/                    # pytest suite
└── data/                     # experiment artifacts (raw via LFS, derived gitignored)
    ├── exp_*/                # per-experiment dirs (see docs/DATA_INDEX.md)
    └── aggregated/           # cross-experiment outputs
```
