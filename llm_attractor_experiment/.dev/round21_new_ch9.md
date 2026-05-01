## 9. Data, code, and reproducibility

### 9.1 Public trajectories, artefacts, and audit trail

The repository is organized so that the paper's claims can be traced from released trajectories through embeddings, per-experiment metrics, aggregate tables, figures, ED50 fits, and audit checks. The public release contains 37 experiments and 3.3 GB of raw trajectories. These trajectories are the canonical input for reproducing the numerical results reported in the paper.

Because hosted generation APIs may change, exact reproduction of the paper's numerical results should use the released `steps.jsonl` trajectories; regeneration of model outputs is provided as a procedural replication path rather than a bitwise reproduction path. This distinction is important: the released trajectories fix the model responses used for the paper, while rerunning generation tests whether the same experimental protocol produces comparable outcomes under the currently available hosted models.

The repository includes three audit documents that provide the main reproducibility map. `COVERAGE.csv` records which expected artefacts are present for each experiment. `EVIDENCE.md` links substantive claims to backing data files, source-code functions, and regenerating commands. `RESULTS.md` checks reported numerical claims against the canonical aggregate tables and currently reports 103/103 numerical-claim audit cells reproducing within tolerance. Additional repository documentation describes the experiment catalogue, supersession relationships among runs, and the analysis history that led to the final design.

### 9.2 Codebase, licences, and runtime environment

Code is available in the public repository <https://github.com/kaplan196883/llmattr> and archived at [Zenodo DOI to be assigned at acceptance], corresponding to the release tagged for this manuscript. Code is released under GPLv3. Trajectories, embeddings, and derived analysis artefacts are released for reuse with attribution; OpenAI-generated outputs and embeddings are subject to the provider's terms.

The project is intended to run under Python 3.11+ in a Conda-managed environment. Core dependencies include numerical, statistical, plotting, image-processing, and video-generation libraries such as numpy, scipy, scikit-learn, scikit-image, matplotlib, pandas, and imageio-ffmpeg. The repository separates reusable analysis modules, experiment definitions, command-line scripts, configuration files, tests, raw data, derived artefacts, and aggregate outputs. This separation is intended to make it possible to inspect or rerun individual components without executing the full pipeline.

The codebase contains the primitives used for embedding management, dynamical-systems metrics, perturbation analyses, aggregate summaries, ED50 fitting, plotting, and audit generation. The scripts directory contains the command-line entry points used to rebuild the paper-level outputs. Configuration files define experiment-specific parameters, while the data directory stores the released trajectories and regenerated outputs when the pipeline is rerun locally.

### 9.3 Approximate cost and runtime

At the time of analysis, regenerating canonical OpenAI embeddings cost approximately US$30, while regenerating model generations cost approximately US$200; these estimates depend on provider pricing and model availability. These costs are not required to verify the paper's numerical claims if the released trajectories and derived embeddings are used. They are provided to make the computational scale of a full procedural rerun transparent.

A lower-cost exact-reproduction path is to download the released trajectories and rerun local embedding-dependent and downstream analyses from those fixed inputs. Users who wish to avoid hosted embedding APIs can substitute local sentence-transformer embeddings for exploratory replication or representation ablation. Such runs should be interpreted as representation-specific replications, not exact regenerations of the canonical embedding pipeline.

Full local embedding and analysis on the released trajectories took approximately 2 hours wall-time on a 40-core reference machine in the authors' environment. This is a benchmark for scale, not a reproducibility guarantee. Runtime will vary with storage bandwidth, CPU count, memory, embedding backend, plotting options, and whether animations or perturbation visualizations are regenerated.

### 9.4 Tests and claim verification

The analysis primitives and integration paths are covered by 99 pytest tests. The standard test command is `PYTHONPATH=. python -m pytest tests/ -q`. These tests exercise reusable components and integration behavior, while the audit scripts check the paper-level claims against regenerated artefacts and aggregate tables.

The canonical reproduction path is: download raw trajectories; compute or load embeddings; run per-experiment analyses; aggregate cross-experiment tables; run the coverage and numerical-claim audits. This schematic path is implemented by the repository scripts and can be executed at different levels of completeness depending on whether the user wants to verify the published numbers, regenerate selected figures, or procedurally rerun the full experimental workflow.

Two audit entry points are load-bearing for the claim trace. `python -m scripts.build_coverage` regenerates the artefact-coverage audit, and `python -m scripts.publication_summary` regenerates the numerical-claim verification table, including ED50 and summary-table checks. Together with the released trajectories, tests, evidence map, and aggregate outputs, these scripts provide the end-to-end path from each reported claim to the code and data used to recreate it.
