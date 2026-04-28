# COST_ESTIMATE.md — exact token cost of cross-model replication

Computed from the on-disk trajectories of every existing experiment
in `data/exp_*/raw/steps.jsonl` (37 experiments, 464,906 step records). Token counts use `tiktoken o200k_base` (the GPT-4-family tokenizer); for non-OpenAI vendors
the count is an approximation but typically within ~10-15% on
English text since modern BPE vocabularies are similar in size.

**Grand totals**: 223,040,379 input tokens, 26,637,826 output
tokens, ratio in/out ≈ 8.4.

## Per-model replication cost (USD)

| experiment | steps | input M | output M | gpt-4.1-nano | gpt-4o-mini | gpt-4.1-mini | gpt-4o | MiniMax-M2.7 | MiniMax-01 | abab6.5-chat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exp_pub_O1_continue | 108,180 | 93.08 | 12.09 | $14.1 | $21.2 | $56.6 | $354 | $42.4 | $31.9 | $21.0 |
| exp_pub_D1_dialog_curious_helpful_v2 | 18,000 | 13.88 | 0.67 | $1.65 | $2.48 | $6.62 | $41.4 | $4.96 | $3.51 | $2.91 |
| exp_perturb_O1_dose | 7,500 | 11.25 | 0.89 | $1.48 | $2.22 | $5.93 | $37.1 | $4.45 | $3.23 | $2.43 |
| exp_perturb_O1_dose_adversarial | 7,500 | 11.26 | 0.88 | $1.48 | $2.22 | $5.91 | $37.0 | $4.43 | $3.22 | $2.43 |
| exp_perturb_O1_pilot | 6,000 | 9.00 | 0.71 | $1.18 | $1.78 | $4.74 | $29.6 | $3.55 | $2.58 | $1.94 |
| exp_pub_O3_summarize_negate_replace | 108,000 | 4.94 | 3.19 | $1.77 | $2.66 | $7.08 | $44.3 | $5.31 | $4.50 | $1.63 |
| exp_pub_O1_Tsweep_T03 | 4,500 | 6.83 | 0.54 | $0.90 | $1.35 | $3.59 | $22.4 | $2.69 | $1.96 | $1.47 |
| exp_pub_O1_Tsweep_T08 | 4,500 | 6.81 | 0.54 | $0.90 | $1.34 | $3.58 | $22.4 | $2.69 | $1.95 | $1.47 |
| exp_pub_O1_Tsweep_T06 | 4,500 | 6.80 | 0.54 | $0.90 | $1.34 | $3.58 | $22.4 | $2.69 | $1.95 | $1.47 |
| exp_pub_O1_Tsweep_T12 | 4,500 | 6.73 | 0.54 | $0.89 | $1.33 | $3.55 | $22.2 | $2.66 | $1.94 | $1.45 |
| exp_pub_O2_paraphrase_replace | 108,000 | 3.64 | 1.89 | $1.12 | $1.68 | $4.48 | $28.0 | $3.36 | $2.81 | $1.11 |
| exp_perturb_O1_inject_t5 | 3,000 | 4.54 | 0.36 | $0.60 | $0.89 | $2.39 | $14.9 | $1.79 | $1.30 | $0.98 |
| exp_perturb_D1_dose | 7,500 | 4.57 | 0.30 | $0.58 | $0.86 | $2.30 | $14.4 | $1.73 | $1.24 | $0.97 |
| exp_perturb_O1_inject_t25 | 3,000 | 4.49 | 0.36 | $0.59 | $0.89 | $2.37 | $14.8 | $1.77 | $1.29 | $0.97 |
| exp_perturb_D1_pilot | 6,000 | 3.49 | 0.23 | $0.44 | $0.66 | $1.76 | $11.0 | $1.32 | $0.95 | $0.74 |
| exp_perturb_D2_exploratory | 2,500 | 3.49 | 0.15 | $0.41 | $0.61 | $1.64 | $10.2 | $1.23 | $0.86 | $0.73 |
| exp_pub_D1_dialog_curious_helpful | 9,000 | 3.30 | 0.31 | $0.46 | $0.68 | $1.82 | $11.4 | $1.37 | $1.01 | $0.72 |
| exp_perturb_D1_dose_fine | 6,000 | 3.34 | 0.22 | $0.42 | $0.63 | $1.68 | $10.5 | $1.26 | $0.91 | $0.71 |
| exp_noclip | 2,186 | 2.61 | 0.26 | $0.37 | $0.55 | $1.46 | $9.15 | $1.10 | $0.81 | $0.58 |
| exp_pub_D1_Tsweep_T12 | 4,500 | 2.62 | 0.17 | $0.33 | $0.49 | $1.32 | $8.22 | $0.99 | $0.71 | $0.56 |
| exp_pub_D1_Tsweep_T06 | 4,500 | 2.53 | 0.16 | $0.32 | $0.48 | $1.27 | $7.94 | $0.95 | $0.68 | $0.54 |
| exp_pub_D1_Tsweep_T03 | 4,500 | 2.52 | 0.16 | $0.32 | $0.47 | $1.26 | $7.90 | $0.95 | $0.68 | $0.54 |
| exp_long | 2,160 | 1.89 | 0.26 | $0.29 | $0.44 | $1.17 | $7.30 | $0.88 | $0.66 | $0.43 |
| exp_perturb_D1_inject_t5 | 3,000 | 1.75 | 0.11 | $0.22 | $0.33 | $0.88 | $5.49 | $0.66 | $0.47 | $0.37 |
| exp_D2_exploratory_drilldown | 1,250 | 1.76 | 0.08 | $0.21 | $0.31 | $0.82 | $5.15 | $0.62 | $0.43 | $0.37 |
| exp_perturb_D1_inject_t25 | 3,000 | 1.71 | 0.11 | $0.21 | $0.32 | $0.86 | $5.37 | $0.64 | $0.46 | $0.36 |
| exp_op_O1_continue | 1,440 | 1.26 | 0.17 | $0.20 | $0.29 | $0.78 | $4.88 | $0.59 | $0.44 | $0.29 |
| exp_op_O4_paraphrase_append | 1,440 | 0.75 | 0.05 | $0.10 | $0.15 | $0.39 | $2.42 | $0.29 | $0.21 | $0.16 |
| exp_default | 1,350 | 0.60 | 0.16 | $0.12 | $0.19 | $0.50 | $3.11 | $0.37 | $0.30 | $0.15 |
| exp_perturb_O3_pilot | 6,000 | 0.35 | 0.21 | $0.12 | $0.18 | $0.48 | $3.01 | $0.36 | $0.31 | $0.11 |
| exp_perturb_O2_pilot | 6,000 | 0.30 | 0.21 | $0.11 | $0.17 | $0.45 | $2.80 | $0.34 | $0.29 | $0.10 |
| exp_op_O3_summarize_negate | 1,440 | 0.47 | 0.04 | $0.06 | $0.09 | $0.24 | $1.53 | $0.18 | $0.13 | $0.10 |
| exp_dialog_D3_debate_advocate_skeptic | 360 | 0.24 | 0.02 | $0.03 | $0.05 | $0.13 | $0.83 | $0.10 | $0.07 | $0.05 |
| exp_dialog_D1_curious_helpful | 360 | 0.14 | 0.01 | $0.02 | $0.03 | $0.08 | $0.48 | $0.06 | $0.04 | $0.03 |
| exp_op_O3b_summarize_negate_replace | 1,440 | 0.06 | 0.03 | $0.02 | $0.03 | $0.08 | $0.47 | $0.06 | $0.05 | $0.02 |
| exp_op_O2_paraphrase_replace | 1,440 | 0.04 | 0.02 | $0.01 | $0.02 | $0.05 | $0.30 | $0.04 | $0.03 | $0.01 |
| exp_dialog_D2_replace_curious_helpful | 360 | 0.02 | 0.01 | $0.01 | $0.01 | $0.03 | $0.16 | $0.02 | $0.02 | $0.01 |
| **TOTAL (37 exp)** | **464,906** | **223.0** | **26.6** | **$33.0** | **$49.4** | **$132** | **$824** | **$98.9** | **$73.9** | **$49.9** |

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
