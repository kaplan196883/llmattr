# COST_ESTIMATE.md — exact token cost of cross-model replication

Computed from the on-disk trajectories of every existing experiment
in `data/exp_*/raw/steps.jsonl` (37 experiments, 464,906 step records). Token counts use `tiktoken o200k_base` (the GPT-4-family tokenizer); for non-OpenAI vendors
the count is an approximation but typically within ~10-15% on
English text since modern BPE vocabularies are similar in size.

**Grand totals**: 223,040,379 input tokens, 26,637,826 output
tokens, ratio in/out ≈ 8.4.

## Per-model replication cost (USD)

| experiment | steps | input M | output M | gpt-4.1-nano | gpt-4o-mini | MiniMax-M2.7 | claude-haiku-4.5 | claude-sonnet-4.6 | claude-opus-4.7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exp_pub_O1_continue | 108,180 | 93.08 | 12.09 | $14.1 | $21.2 | $42.4 | $154 | $461 | $768 |
| exp_pub_D1_dialog_curious_helpful_v2 | 18,000 | 13.88 | 0.67 | $1.65 | $2.48 | $4.96 | $17.2 | $51.6 | $86.0 |
| exp_perturb_O1_dose | 7,500 | 11.25 | 0.89 | $1.48 | $2.22 | $4.45 | $15.7 | $47.1 | $78.6 |
| exp_perturb_O1_dose_adversarial | 7,500 | 11.26 | 0.88 | $1.48 | $2.22 | $4.43 | $15.7 | $47.0 | $78.3 |
| exp_perturb_O1_pilot | 6,000 | 9.00 | 0.71 | $1.18 | $1.78 | $3.55 | $12.6 | $37.7 | $62.8 |
| exp_pub_O3_summarize_negate_replace | 108,000 | 4.94 | 3.19 | $1.77 | $2.66 | $5.31 | $20.9 | $62.7 | $104 |
| exp_pub_O1_Tsweep_T03 | 4,500 | 6.83 | 0.54 | $0.90 | $1.35 | $2.69 | $9.51 | $28.5 | $47.5 |
| exp_pub_O1_Tsweep_T08 | 4,500 | 6.81 | 0.54 | $0.90 | $1.34 | $2.69 | $9.49 | $28.5 | $47.5 |
| exp_pub_O1_Tsweep_T06 | 4,500 | 6.80 | 0.54 | $0.90 | $1.34 | $2.69 | $9.49 | $28.5 | $47.4 |
| exp_pub_O1_Tsweep_T12 | 4,500 | 6.73 | 0.54 | $0.89 | $1.33 | $2.66 | $9.41 | $28.2 | $47.1 |
| exp_pub_O2_paraphrase_replace | 108,000 | 3.64 | 1.89 | $1.12 | $1.68 | $3.36 | $13.1 | $39.2 | $65.4 |
| exp_perturb_O1_inject_t5 | 3,000 | 4.54 | 0.36 | $0.60 | $0.89 | $1.79 | $6.32 | $19.0 | $31.6 |
| exp_perturb_D1_dose | 7,500 | 4.57 | 0.30 | $0.58 | $0.86 | $1.73 | $6.06 | $18.2 | $30.3 |
| exp_perturb_O1_inject_t25 | 3,000 | 4.49 | 0.36 | $0.59 | $0.89 | $1.77 | $6.27 | $18.8 | $31.3 |
| exp_perturb_D1_pilot | 6,000 | 3.49 | 0.23 | $0.44 | $0.66 | $1.32 | $4.62 | $13.8 | $23.1 |
| exp_perturb_D2_exploratory | 2,500 | 3.49 | 0.15 | $0.41 | $0.61 | $1.23 | $4.24 | $12.7 | $21.2 |
| exp_pub_D1_dialog_curious_helpful | 9,000 | 3.30 | 0.31 | $0.46 | $0.68 | $1.37 | $4.87 | $14.6 | $24.3 |
| exp_perturb_D1_dose_fine | 6,000 | 3.34 | 0.22 | $0.42 | $0.63 | $1.26 | $4.43 | $13.3 | $22.1 |
| exp_noclip | 2,186 | 2.61 | 0.26 | $0.37 | $0.55 | $1.10 | $3.92 | $11.8 | $19.6 |
| exp_pub_D1_Tsweep_T12 | 4,500 | 2.62 | 0.17 | $0.33 | $0.49 | $0.99 | $3.46 | $10.4 | $17.3 |
| exp_pub_D1_Tsweep_T06 | 4,500 | 2.53 | 0.16 | $0.32 | $0.48 | $0.95 | $3.34 | $10.0 | $16.7 |
| exp_pub_D1_Tsweep_T03 | 4,500 | 2.52 | 0.16 | $0.32 | $0.47 | $0.95 | $3.32 | $9.97 | $16.6 |
| exp_long | 2,160 | 1.89 | 0.26 | $0.29 | $0.44 | $0.88 | $3.18 | $9.54 | $15.9 |
| exp_perturb_D1_inject_t5 | 3,000 | 1.75 | 0.11 | $0.22 | $0.33 | $0.66 | $2.31 | $6.93 | $11.5 |
| exp_D2_exploratory_drilldown | 1,250 | 1.76 | 0.08 | $0.21 | $0.31 | $0.62 | $2.14 | $6.41 | $10.7 |
| exp_perturb_D1_inject_t25 | 3,000 | 1.71 | 0.11 | $0.21 | $0.32 | $0.64 | $2.26 | $6.78 | $11.3 |
| exp_op_O1_continue | 1,440 | 1.26 | 0.17 | $0.20 | $0.29 | $0.59 | $2.12 | $6.37 | $10.6 |
| exp_op_O4_paraphrase_append | 1,440 | 0.75 | 0.05 | $0.10 | $0.15 | $0.29 | $1.02 | $3.07 | $5.12 |
| exp_default | 1,350 | 0.60 | 0.16 | $0.12 | $0.19 | $0.37 | $1.41 | $4.22 | $7.03 |
| exp_perturb_O3_pilot | 6,000 | 0.35 | 0.21 | $0.12 | $0.18 | $0.36 | $1.42 | $4.26 | $7.09 |
| exp_perturb_O2_pilot | 6,000 | 0.30 | 0.21 | $0.11 | $0.17 | $0.34 | $1.33 | $3.98 | $6.63 |
| exp_op_O3_summarize_negate | 1,440 | 0.47 | 0.04 | $0.06 | $0.09 | $0.18 | $0.65 | $1.94 | $3.24 |
| exp_dialog_D3_debate_advocate_skeptic | 360 | 0.24 | 0.02 | $0.03 | $0.05 | $0.10 | $0.36 | $1.07 | $1.78 |
| exp_dialog_D1_curious_helpful | 360 | 0.14 | 0.01 | $0.02 | $0.03 | $0.06 | $0.20 | $0.61 | $1.02 |
| exp_op_O3b_summarize_negate_replace | 1,440 | 0.06 | 0.03 | $0.02 | $0.03 | $0.06 | $0.22 | $0.66 | $1.10 |
| exp_op_O2_paraphrase_replace | 1,440 | 0.04 | 0.02 | $0.01 | $0.02 | $0.04 | $0.14 | $0.41 | $0.69 |
| exp_dialog_D2_replace_curious_helpful | 360 | 0.02 | 0.01 | $0.01 | $0.01 | $0.02 | $0.08 | $0.23 | $0.39 |
| **TOTAL (37 exp)** | **464,906** | **223.0** | **26.6** | **$33.0** | **$49.4** | **$98.9** | **$356** | **$1,069** | **$1,781** |

Plus **embeddings**: ~223.0M tokens at $0.020/M = $4.46 per model (`text-embedding-3-small` is held fixed across all cross-model runs; this cost applies once per replication, not per generator).

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
