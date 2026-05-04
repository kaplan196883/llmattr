# COST_ESTIMATE.md — exact token cost of cross-model replication

Computed from the on-disk trajectories of every existing experiment
in `data/exp_*/raw/steps.jsonl` (37 experiments, 467,764 step records). Token counts use `tiktoken o200k_base` (the GPT-4-family tokenizer); for non-OpenAI vendors
the count is an approximation but typically within ~10-15% on
English text since modern BPE vocabularies are similar in size.

**Grand totals**: 225,359,442 input tokens, 26,831,639 output
tokens, ratio in/out ≈ 8.4.

## Per-model replication cost (USD)

| experiment | steps | input M | output M | gpt-4.1-nano | gpt-4o-mini | gpt-5.4-nano | gpt-5-mini | gpt-4.1-mini | gpt-5.4-mini | gpt-5.1 | gpt-5.2 | gpt-4.1 | gpt-5.4 | gpt-4o |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exp_pub_O1_continue | 108,180 | 93.08 | 12.09 | $14.1 | $21.2 | $33.7 | $47.5 | $56.6 | $124 | $237 | $332 | $283 | $414 | $354 |
| exp_pub_D1_dialog_curious_helpful_v2 | 18,000 | 13.88 | 0.67 | $1.65 | $2.48 | $3.61 | $4.80 | $6.62 | $13.4 | $24.0 | $33.6 | $33.1 | $44.7 | $41.4 |
| exp_perturb_O1_dose | 7,500 | 11.25 | 0.89 | $1.48 | $2.22 | $3.37 | $4.60 | $5.93 | $12.5 | $23.0 | $32.2 | $29.6 | $41.5 | $37.1 |
| exp_perturb_O1_dose_adversarial | 7,500 | 11.26 | 0.88 | $1.48 | $2.22 | $3.35 | $4.58 | $5.91 | $12.4 | $22.9 | $32.0 | $29.6 | $41.4 | $37.0 |
| exp_perturb_O1_pilot | 6,000 | 9.00 | 0.71 | $1.18 | $1.78 | $2.69 | $3.67 | $4.74 | $9.95 | $18.4 | $25.7 | $23.7 | $33.2 | $29.6 |
| exp_pub_O3_summarize_negate_replace | 108,000 | 4.94 | 3.19 | $1.77 | $2.66 | $4.98 | $7.62 | $7.08 | $18.1 | $38.1 | $53.3 | $35.4 | $60.2 | $44.3 |
| exp_pub_O1_Tsweep_T03 | 4,500 | 6.83 | 0.54 | $0.90 | $1.35 | $2.04 | $2.78 | $3.59 | $7.53 | $13.9 | $19.5 | $17.9 | $25.1 | $22.4 |
| exp_pub_O1_Tsweep_T08 | 4,500 | 6.81 | 0.54 | $0.90 | $1.34 | $2.03 | $2.77 | $3.58 | $7.52 | $13.9 | $19.4 | $17.9 | $25.1 | $22.4 |
| exp_pub_O1_Tsweep_T06 | 4,500 | 6.80 | 0.54 | $0.90 | $1.34 | $2.03 | $2.77 | $3.58 | $7.52 | $13.9 | $19.4 | $17.9 | $25.1 | $22.4 |
| exp_pub_O1_Tsweep_T12 | 4,500 | 6.73 | 0.54 | $0.89 | $1.33 | $2.02 | $2.75 | $3.55 | $7.46 | $13.8 | $19.3 | $17.7 | $24.9 | $22.2 |
| exp_pub_O2_paraphrase_replace | 108,000 | 3.64 | 1.89 | $1.12 | $1.68 | $3.09 | $4.69 | $4.48 | $11.2 | $23.4 | $32.8 | $22.4 | $37.4 | $28.0 |
| exp_perturb_O1_inject_t5 | 3,000 | 4.54 | 0.36 | $0.60 | $0.89 | $1.35 | $1.85 | $2.39 | $5.01 | $9.24 | $12.9 | $11.9 | $16.7 | $14.9 |
| exp_perturb_D1_dose | 7,500 | 4.57 | 0.30 | $0.58 | $0.86 | $1.29 | $1.74 | $2.30 | $4.77 | $8.69 | $12.2 | $11.5 | $15.9 | $14.4 |
| exp_perturb_O1_inject_t25 | 3,000 | 4.49 | 0.36 | $0.59 | $0.89 | $1.34 | $1.83 | $2.37 | $4.97 | $9.17 | $12.8 | $11.8 | $16.6 | $14.8 |
| exp_perturb_D1_pilot | 6,000 | 3.49 | 0.23 | $0.44 | $0.66 | $0.98 | $1.32 | $1.76 | $3.63 | $6.62 | $9.26 | $8.78 | $12.1 | $11.0 |
| exp_perturb_D2_exploratory | 2,500 | 3.49 | 0.15 | $0.41 | $0.61 | $0.89 | $1.17 | $1.64 | $3.29 | $5.87 | $8.21 | $8.18 | $11.0 | $10.2 |
| exp_pub_D1_dialog_curious_helpful | 9,000 | 3.30 | 0.31 | $0.46 | $0.68 | $1.05 | $1.45 | $1.82 | $3.89 | $7.26 | $10.2 | $9.11 | $13.0 | $11.4 |
| exp_perturb_D1_dose_fine | 6,000 | 3.34 | 0.22 | $0.42 | $0.63 | $0.94 | $1.27 | $1.68 | $3.48 | $6.34 | $8.88 | $8.42 | $11.6 | $10.5 |
| exp_noclip | 2,186 | 2.61 | 0.26 | $0.37 | $0.55 | $0.85 | $1.18 | $1.46 | $3.14 | $5.88 | $8.24 | $7.32 | $10.5 | $9.15 |
| exp_pub_D1_Tsweep_T12 | 4,500 | 2.62 | 0.17 | $0.33 | $0.49 | $0.73 | $0.99 | $1.32 | $2.72 | $4.95 | $6.93 | $6.58 | $9.06 | $8.22 |
| exp_pub_D1_Tsweep_T06 | 4,500 | 2.53 | 0.16 | $0.32 | $0.48 | $0.71 | $0.96 | $1.27 | $2.63 | $4.78 | $6.69 | $6.36 | $8.75 | $7.94 |
| exp_pub_D1_Tsweep_T03 | 4,500 | 2.52 | 0.16 | $0.32 | $0.47 | $0.70 | $0.95 | $1.26 | $2.61 | $4.75 | $6.65 | $6.32 | $8.71 | $7.90 |
| exp_long | 2,160 | 1.89 | 0.26 | $0.29 | $0.44 | $0.70 | $0.99 | $1.17 | $2.58 | $4.94 | $6.92 | $5.84 | $8.59 | $7.30 |
| exp_perturb_D1_inject_t5 | 3,000 | 1.75 | 0.11 | $0.22 | $0.33 | $0.49 | $0.66 | $0.88 | $1.82 | $3.31 | $4.63 | $4.40 | $6.05 | $5.49 |
| exp_D2_exploratory_drilldown | 1,250 | 1.76 | 0.08 | $0.21 | $0.31 | $0.45 | $0.59 | $0.82 | $1.66 | $2.95 | $4.14 | $4.12 | $5.53 | $5.15 |
| exp_perturb_D1_inject_t25 | 3,000 | 1.71 | 0.11 | $0.21 | $0.32 | $0.48 | $0.65 | $0.86 | $1.78 | $3.24 | $4.54 | $4.30 | $5.93 | $5.37 |
| exp_D2_exploratory_drilldown_gpt4nano | 1,250 | 1.73 | 0.07 | $0.20 | $0.30 | $0.43 | $0.57 | $0.80 | $1.61 | $2.86 | $4.00 | $4.02 | $5.37 | $5.02 |
| exp_op_O1_continue | 1,440 | 1.26 | 0.17 | $0.20 | $0.29 | $0.47 | $0.66 | $0.78 | $1.72 | $3.30 | $4.62 | $3.91 | $5.74 | $4.88 |
| exp_op_O4_paraphrase_append | 1,440 | 0.75 | 0.05 | $0.10 | $0.15 | $0.22 | $0.30 | $0.39 | $0.81 | $1.48 | $2.08 | $1.94 | $2.69 | $2.42 |
| exp_default | 1,350 | 0.60 | 0.16 | $0.12 | $0.19 | $0.32 | $0.47 | $0.50 | $1.18 | $2.36 | $3.31 | $2.49 | $3.92 | $3.11 |
| exp_default_gpt4nano | 1,161 | 0.46 | 0.11 | $0.09 | $0.13 | $0.23 | $0.33 | $0.36 | $0.83 | $1.64 | $2.30 | $1.78 | $2.75 | $2.22 |
| exp_perturb_O3_pilot | 6,000 | 0.35 | 0.21 | $0.12 | $0.18 | $0.34 | $0.52 | $0.48 | $1.22 | $2.58 | $3.61 | $2.41 | $4.08 | $3.01 |
| exp_perturb_O2_pilot | 6,000 | 0.30 | 0.21 | $0.11 | $0.17 | $0.32 | $0.49 | $0.45 | $1.15 | $2.43 | $3.40 | $2.24 | $3.83 | $2.80 |
| exp_op_O3_summarize_negate | 1,440 | 0.47 | 0.04 | $0.06 | $0.09 | $0.14 | $0.19 | $0.24 | $0.51 | $0.95 | $1.32 | $1.22 | $1.71 | $1.53 |
| exp_dialog_D3_debate_advocate_skeptic | 360 | 0.24 | 0.02 | $0.03 | $0.05 | $0.08 | $0.11 | $0.13 | $0.28 | $0.53 | $0.75 | $0.66 | $0.95 | $0.83 |
| exp_dialog_D1_curious_helpful | 360 | 0.14 | 0.01 | $0.02 | $0.03 | $0.04 | $0.06 | $0.08 | $0.16 | $0.30 | $0.43 | $0.38 | $0.54 | $0.48 |
| exp_dialog_D1_curious_helpful_gpt4nano | 360 | 0.11 | 0.01 | $0.01 | $0.02 | $0.03 | $0.05 | $0.06 | $0.12 | $0.23 | $0.32 | $0.29 | $0.41 | $0.36 |
| exp_op_O3b_summarize_negate_replace | 1,440 | 0.06 | 0.03 | $0.02 | $0.03 | $0.05 | $0.08 | $0.08 | $0.19 | $0.39 | $0.55 | $0.38 | $0.63 | $0.47 |
| exp_op_O2_paraphrase_replace | 1,440 | 0.04 | 0.02 | $0.01 | $0.02 | $0.03 | $0.05 | $0.05 | $0.12 | $0.24 | $0.34 | $0.24 | $0.39 | $0.30 |
| exp_dialog_D2_replace_curious_helpful | 360 | 0.02 | 0.01 | $0.01 | $0.01 | $0.02 | $0.03 | $0.03 | $0.07 | $0.14 | $0.20 | $0.13 | $0.23 | $0.16 |
| exp_D2_exploratory_drilldown_text01 | 87 | 0.02 | 0.01 | $0.01 | $0.01 | $0.01 | $0.02 | $0.02 | $0.05 | $0.11 | $0.15 | $0.10 | $0.17 | $0.13 |
| **TOTAL (37 exp)** | **467,764** | **225.4** | **26.8** | **$33.3** | **$49.9** | **$78.6** | **$110** | **$133** | **$290** | **$550** | **$770** | **$665** | **$966** | **$832** |

Plus **embeddings**: ~225.4M tokens at $0.020/M = $4.51 per model (`text-embedding-3-small` is held fixed across all cross-model runs; this cost applies once per replication, not per generator).

## Methodology

- For each step record we count input = `len(encode(system_prompt))`
  + `len(encode(context_before))`, output = `len(encode(output_text))`.
- Dialog experiments use the longer of the two role system prompts
  as a per-turn proxy (each turn sends exactly one role's system).
- Embedding cost assumes one embedding pass per step record (the
  baseline pipeline's `cmd_embed` behavior). Multi-observable
  experiments may embed 2–3× per step; treat the embedding line
  as a lower bound.
- Cross-vendor token counts use `o200k_base` as a proxy. For
  precise MiniMax / DeepSeek estimates, multiply the values above
  by ~1.10 as a conservative buffer.

Regenerate with:
```
python -m scripts.token_cost_estimator \
    --price gpt-4o-mini=0.15:0.60 \
    --price gpt-4o=2.50:10.00 \
    --price MiniMax-Text-01=0.20:1.10
```

(Verify per-model rates against current `openai.com/api/pricing`
and `minimaxi.com/pricing` before committing budget.)
