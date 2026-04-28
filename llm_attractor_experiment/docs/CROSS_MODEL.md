# Cross-model validation

How to drive the same experimental pipeline against a non-default
generation model — e.g. `gpt-4o` instead of `gpt-4o-mini`, or a
different vendor like MiniMax.

## What stays fixed, what changes

| layer | behavior |
|---|---|
| **Generation model** | configurable per experiment via `generation_model` + `generation_provider` |
| **Embedding model** | **always** OpenAI `text-embedding-3-small` — the geometric space is held fixed across cross-model runs so PCA-10 / cluster / V\* comparisons remain meaningful |
| **All metrics + plots** | identical pipeline; the model swap is a pure independent-variable change |

## Two example configs (`configs/cross_model/`)

- **`O1_gpt4o.yaml`** — same family as baseline (`gpt-4o-mini`), full
  scale (`gpt-4o`). Tests "does the regime taxonomy survive scale
  within a vendor?". Uses OpenAI native Responses API (no provider
  block changes from default behavior, only the model name).
- **`O1_minimax.yaml`** — different vendor entirely. MiniMax-Text-01
  (456B sparse-MoE), accessed via OpenAI-compatible Chat Completions
  API. Tests "does the regime taxonomy survive cross-architecture?".

Each is a copy of the baseline `O1_Tsweep_T08` config (reduced scope,
n=150 trajectories, ~$15 per cell on `gpt-4o-mini`) with only the
model + provider lines changed.

## YAML schema for `generation_provider`

```yaml
generation_provider:
  name: minimax              # arbitrary tag; used only in logs
  base_url: https://api.minimaxi.chat/v1
  api_key_env: MINIMAX_API_KEY
  api: chat_completions      # "responses" | "chat_completions"
```

| field | purpose | default |
|---|---|---|
| `name` | label that appears in logs / config snapshots | `openai` |
| `base_url` | full OpenAI-compatible endpoint (`None` = OpenAI default) | `None` |
| `api_key_env` | env-var name to read the API key from | `OPENAI_API_KEY` |
| `api` | which generation API to use; OpenAI native is `responses`, every other vendor is `chat_completions` | `responses` |

The block is **optional** — every existing `exp_pub_*` config in this
repo lacks it and continues to work because the defaults reproduce
the OpenAI native Responses path.

## Running a cross-model cell

```bash
# 1. Set the relevant API key in .env at the repo root
echo "MINIMAX_API_KEY=sk-..." >> .env

# 2. Run the pipeline normally — all CLI tools accept --config:
python -m src.experiments.operators.main --config configs/cross_model/O1_minimax.yaml run
python -m src.main      --config configs/cross_model/O1_minimax.yaml embed
python -m src.main      --config configs/cross_model/O1_minimax.yaml analyze
python -m src.main      --config configs/cross_model/O1_minimax.yaml report

# 3. The output lands in data/exp_xmodel_O1_minimax/ following the
#    exact same directory layout as every other experiment.
```

## Cost estimates (4 regimes × full pub scope)

| model | output tokens / run | $ / 1M out | full pub-scope cost |
|---|---|---|---|
| `gpt-4o-mini` (baseline) | 24M | $0.60 | ~$15 |
| `gpt-4o` | 24M | $10.00 | ~$240 |
| `MiniMax-Text-01` | 24M | ~$2.00 | ~$50 |

The reduced-scope cells (n=150 like the T-sweep) are 9× cheaper, so
a "phase-2-lite" cross-model pass over O1 + D1 only is ~$2 / model
on `gpt-4o-mini`-equivalents and ~$30 on `gpt-4o`. That's the
recommended cheap-first-look.

## What to expect

The four regimes (O1 contractive, O2 oscillatory, O3 absorbing, D1
stylistic-multi-basin) are predictions about *recursive-feedback
dynamics*, not about a specific tokenizer / training distribution.
If they survive a model swap, that's strong evidence the taxonomy is
about the *coupling* (state-generator-nudge in §3.1) rather than
about the generator. Diagnostics worth eyeballing first:

1. `recurrence_rate` (`pca10`, `context_tail`) — should be
   ~0.05–0.30 for O1, ~0.85–0.95 for O2, ~0.90+ for O3, low for D1.
2. `sharpness_dim_late` — O1 ≈ 1.5–2.0, D1 ≈ 1.8–2.0, O2/O3 ≈ 1.4–1.5.
3. Adversarial-perturbation switch rate — O1 modest (0.4–0.6), O2/O3
   high (>0.9), D1 modest (0.5–0.7).

If the model swap shifts these by more than a few pct pts, document
it as an open question rather than re-tuning thresholds.

## Verification

After running a cross-model experiment, regenerate `RESULTS.md` to
make sure the baseline §5 cells still verify (they should be
unaffected — the cross-model run lands under a new `exp_xmodel_*`
prefix and doesn't disturb the baseline data):

```bash
python -m scripts.publication_summary
```
