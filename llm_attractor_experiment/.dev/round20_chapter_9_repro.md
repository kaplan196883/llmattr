## 9. Data, code, and reproducibility

*The repository is organized so that the paper's claims can be traced from raw trajectories to embeddings, metrics, plots, ED50 fits, audit tables, and regenerated summary checks.*

### 9.1 Public trajectories, derived artefacts, and audit tables

Raw trajectories are released as public data and are stored in the repository layout under `data/exp_*/raw/steps.jsonl`, with large files tracked through LFS. The raw payload is 3.3 GB across 37 experiments. A Hugging Face dataset mirrors the trajectory release for direct download, while the GitHub release contains derived metrics, plots, perturbation visualizations, animations, aggregate tables, and ED50 fit artefacts.

Three audit files provide the main reproducibility map. `COVERAGE.csv` is a 37 × 60 matrix recording whether each experiment has each applicable artefact, with cells marked as present, absent, or structurally non-applicable. All 37 experiments are at 100% of their applicable artefacts. `EVIDENCE.md` maps substantive paper claims to backing data files, source-code functions, and regenerating commands. `RESULTS.md` verifies the numerical claims against the canonical aggregated CSVs; the current audit reports 103 / 103 cells reproducing within tolerance.

The experiment catalog is documented in `docs/DATA_INDEX.md`, which describes the purpose, scope, and supersession relationships of the 37 experiment directories. Six stage reports in `docs/reports/` record the discovery path from the first baseline classification runs through long-horizon ablations, dynamical-systems metrics, operator-regime classification, publication-scale verification, and perturbation experiments. These documents are not required to run the pipeline, but they make the provenance of the final design inspectable.

### 9.2 Codebase, licenses, and runtime environment

The codebase is available at <https://github.com/kaplan196883/llmattr>. The code is released under GPLv3, and the generated trajectories, embeddings, and analysis artefacts are released for reuse with attribution under the data license specified in the repository. The repository is intended to run under Python 3.11+ with a Conda environment; key dependencies include numpy, scipy, scikit-learn, scikit-image, matplotlib, pandas, and imageio-ffmpeg.

The top-level layout separates experiment definitions, executable scripts, reusable analysis code, tests, and data. `src/` contains the core analysis, API, experiment, report, and utility modules. `scripts/` contains configuration builders, aggregation tools, audit scripts, and figure-generation entry points. `configs/` stores per-experiment YAML files, `tests/` contains the pytest suite, and `data/` contains the 37 experiment directories plus aggregate outputs.

### 9.3 Bounded API and local-compute costs

Regenerating embeddings for the full 37-experiment set costs approximately $30 using OpenAI `text-embedding-3-small`. Regenerating all model generations costs approximately $200 using the original OpenAI generation path, but this is unnecessary if the LFS-tracked `steps.jsonl` files or the public trajectory dataset are used. Full local embed and analysis runs take approximately 2 hours wall-time on a 40-core machine; animations add additional plotting time.

A lower-cost path is to reuse the released raw trajectories and run only local analysis. Users can also substitute local sentence-transformer embeddings for exploratory replication or representation ablation, avoiding OpenAI embedding costs. Those runs should be interpreted as representation-specific replications rather than exact regenerations of the canonical embedding pipeline.

### 9.4 Automated tests and end-to-end claim verification

The analysis primitives and integration paths are covered by 99 pytest tests. The standard test command is `PYTHONPATH=. python -m pytest tests/ -q`, which reports 99 passing tests in approximately 13 seconds in the reference environment. These tests cover the reusable components, while the audit scripts check the paper-level claims against regenerated artefacts.

The pipeline is organized into four re-runnable stages: generate, embed, analyze, and aggregate. Generation produces `steps.jsonl`; embedding produces `embeddings/<observable>/embeddings.npy`; analysis produces metric CSVs and per-experiment reports; aggregation produces the cross-experiment tables under `data/aggregated/`. `python -m scripts.build_coverage` regenerates the 37 × 60 coverage matrix, and `python -m scripts.publication_summary` regenerates the 103 / 103 numeric-claim verification table, including the ED50 and audit-table checks. The tests, coverage matrix, evidence map, and regenerated results give an end-to-end path from each reported claim to the script that recreates it.
