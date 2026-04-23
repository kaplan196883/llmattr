from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ClusteringConfig:
    method: str = "dbscan"
    dbscan: dict = field(default_factory=lambda: {"eps": 0.35, "min_samples": 4})
    kmeans: dict = field(default_factory=lambda: {"n_clusters": 6})


@dataclass
class RecurrenceConfig:
    metric: str = "cosine"
    epsilon: float = 0.25
    tau: int = 3


@dataclass
class DwellConfig:
    space: str = "pca10"


@dataclass
class BasinEntryConfig:
    enabled: bool = False
    late_fraction: float = 0.3           # late window used to identify the target cluster
    fraction_after: float = 0.7          # fraction of steps after entry that must be in target


@dataclass
class LateRecurrenceConfig:
    enabled: bool = False
    start_fraction: float = 0.7          # used when not anchoring to basin entry
    use_basin_entry: bool = True         # if true and basin_entry is enabled, start at entry step


@dataclass
class ExitReturnConfig:
    enabled: bool = False
    start_fraction: float = 0.0          # 0.0 = use full trajectory, >0 = only after that fraction
    use_basin_entry: bool = True


@dataclass
class BootstrapConfig:
    enabled: bool = False
    n_resamples: int = 1000
    confidence: float = 0.95


@dataclass
class TSNEConfig:
    enabled: bool = False
    perplexity: float = 30.0
    pre_pca_dim: int | None = 50
    metric: str = "cosine"
    include_in_metrics: bool = False
    recurrence_epsilon_std_frac: float = 0.08
    cluster_in_tsne: bool = False


@dataclass
class BasinConfig:
    target_region_late_fraction: float = 0.3
    target_step_fraction: float = 0.7
    perturbations: list[str] = field(
        default_factory=lambda: ["suffix", "neutral_sentence", "seed_only"]
    )
    perturbation_suffix: str = " (Let the thought continue.)"
    neutral_sentence: str = " A brief pause preceded the next thought."


@dataclass
class PromptFamily:
    name: str
    system_prompt: str
    initial_conditions: list[str]


@dataclass
class Config:
    experiment_id: str
    generation_model: str
    embedding_model: str

    steps_per_run: int
    runs_per_condition: int
    initial_conditions_per_family: int

    max_output_tokens: int
    temperature: float
    top_p: float
    include_logprobs: bool

    clip_rule: str
    max_context_chars: int

    rolling_window_k: int
    context_tail_chars: int
    context_full_chars: int
    observables: list[str]

    pca_dims: list[int]

    clustering: ClusteringConfig
    recurrence: RecurrenceConfig
    dwell: DwellConfig
    basin: BasinConfig
    tsne: TSNEConfig
    basin_entry: BasinEntryConfig
    late_recurrence: LateRecurrenceConfig
    exit_return: ExitReturnConfig
    bootstrap: BootstrapConfig

    baseline_modes: list[str]

    batch_embeddings: bool
    use_evals: bool

    seed: int
    parallel_trajectories: int

    output_dir: str

    prompt_families: list[PromptFamily]

    raw_dict: dict = field(default_factory=dict, repr=False)

    @property
    def experiment_dir(self) -> Path:
        return Path(self.output_dir) / self.experiment_id

    @property
    def raw_dir(self) -> Path:
        return self.experiment_dir / "raw"

    @property
    def embeddings_dir(self) -> Path:
        return self.experiment_dir / "embeddings"

    @property
    def metrics_dir(self) -> Path:
        return self.experiment_dir / "metrics"

    @property
    def reports_dir(self) -> Path:
        return self.experiment_dir / "reports"

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_dict", None)
        return d


def load_config(path: str | Path) -> Config:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    clustering_raw = raw.get("clustering", {}) or {}
    clustering = ClusteringConfig(
        method=clustering_raw.get("method", "dbscan"),
        dbscan=clustering_raw.get("dbscan", {"eps": 0.35, "min_samples": 4}),
        kmeans=clustering_raw.get("kmeans", {"n_clusters": 6}),
    )
    recurrence_raw = raw.get("recurrence", {}) or {}
    recurrence = RecurrenceConfig(
        metric=recurrence_raw.get("metric", "cosine"),
        epsilon=float(recurrence_raw.get("epsilon", 0.25)),
        tau=int(recurrence_raw.get("tau", 3)),
    )
    dwell_raw = raw.get("dwell", {}) or {}
    dwell = DwellConfig(space=dwell_raw.get("space", "pca10"))
    be_raw = raw.get("basin_entry", {}) or {}
    be_cfg = BasinEntryConfig(
        enabled=bool(be_raw.get("enabled", False)),
        late_fraction=float(be_raw.get("late_fraction", 0.3)),
        fraction_after=float(be_raw.get("fraction_after", 0.7)),
    )
    lr_raw = raw.get("late_recurrence", {}) or {}
    lr_cfg = LateRecurrenceConfig(
        enabled=bool(lr_raw.get("enabled", False)),
        start_fraction=float(lr_raw.get("start_fraction", 0.7)),
        use_basin_entry=bool(lr_raw.get("use_basin_entry", True)),
    )
    er_raw = raw.get("exit_return", {}) or {}
    er_cfg = ExitReturnConfig(
        enabled=bool(er_raw.get("enabled", False)),
        start_fraction=float(er_raw.get("start_fraction", 0.0)),
        use_basin_entry=bool(er_raw.get("use_basin_entry", True)),
    )
    bs_raw = raw.get("bootstrap", {}) or {}
    bs_cfg = BootstrapConfig(
        enabled=bool(bs_raw.get("enabled", False)),
        n_resamples=int(bs_raw.get("n_resamples", 1000)),
        confidence=float(bs_raw.get("confidence", 0.95)),
    )
    tsne_raw = raw.get("tsne", {}) or {}
    tsne_cfg = TSNEConfig(
        enabled=bool(tsne_raw.get("enabled", False)),
        perplexity=float(tsne_raw.get("perplexity", 30.0)),
        pre_pca_dim=(int(tsne_raw["pre_pca_dim"]) if tsne_raw.get("pre_pca_dim") else None),
        metric=str(tsne_raw.get("metric", "cosine")),
        include_in_metrics=bool(tsne_raw.get("include_in_metrics", False)),
        recurrence_epsilon_std_frac=float(tsne_raw.get("recurrence_epsilon_std_frac", 0.08)),
        cluster_in_tsne=bool(tsne_raw.get("cluster_in_tsne", False)),
    )
    basin_raw = raw.get("basin", {}) or {}
    basin = BasinConfig(
        target_region_late_fraction=float(basin_raw.get("target_region_late_fraction", 0.3)),
        target_step_fraction=float(basin_raw.get("target_step_fraction", 0.7)),
        perturbations=list(basin_raw.get("perturbations", ["suffix", "neutral_sentence", "seed_only"])),
        perturbation_suffix=basin_raw.get("perturbation_suffix", " (Let the thought continue.)"),
        neutral_sentence=basin_raw.get("neutral_sentence", " A brief pause preceded the next thought."),
    )

    families = []
    for f_raw in raw.get("prompt_families", []):
        families.append(
            PromptFamily(
                name=f_raw["name"],
                system_prompt=f_raw.get(
                    "system_prompt",
                    "Continue the text naturally. Do not summarize or explain.",
                ),
                initial_conditions=list(f_raw["initial_conditions"]),
            )
        )

    cfg = Config(
        experiment_id=str(raw["experiment_id"]),
        generation_model=str(raw["generation_model"]),
        embedding_model=str(raw["embedding_model"]),
        steps_per_run=int(raw["steps_per_run"]),
        runs_per_condition=int(raw["runs_per_condition"]),
        initial_conditions_per_family=int(raw.get("initial_conditions_per_family", 0)) or None,  # type: ignore
        max_output_tokens=int(raw["max_output_tokens"]),
        temperature=float(raw["temperature"]),
        top_p=float(raw["top_p"]),
        include_logprobs=bool(raw.get("include_logprobs", False)),
        clip_rule=str(raw.get("clip_rule", "tail_chars")),
        max_context_chars=int(raw.get("max_context_chars", 12000)),
        rolling_window_k=int(raw.get("rolling_window_k", 3)),
        context_tail_chars=int(raw.get("context_tail_chars", 4000)),
        context_full_chars=int(raw.get("context_full_chars", 8000)),
        observables=list(raw.get("observables", ["output", "rolling_k3", "context_tail"])),
        pca_dims=list(raw.get("pca_dims", [2, 10])),
        clustering=clustering,
        recurrence=recurrence,
        dwell=dwell,
        basin=basin,
        tsne=tsne_cfg,
        basin_entry=be_cfg,
        late_recurrence=lr_cfg,
        exit_return=er_cfg,
        bootstrap=bs_cfg,
        baseline_modes=list(raw.get("baseline_modes", ["no_feedback"])),
        batch_embeddings=bool(raw.get("batch_embeddings", False)),
        use_evals=bool(raw.get("use_evals", False)),
        seed=int(raw.get("seed", 42)),
        parallel_trajectories=int(raw.get("parallel_trajectories", 1)),
        output_dir=str(raw.get("output_dir", "data")),
        prompt_families=families,
        raw_dict=raw,
    )
    if cfg.initial_conditions_per_family is None:
        # default: use all provided initial conditions
        cfg.initial_conditions_per_family = max(
            len(f.initial_conditions) for f in families
        ) if families else 0
    return cfg


def save_config_snapshot(cfg: Config, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.raw_dict, f, sort_keys=False, allow_unicode=True)


def limit_initial_conditions(family: PromptFamily, limit: int) -> list[str]:
    return family.initial_conditions[:limit] if limit else family.initial_conditions
