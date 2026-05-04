"""Audit every experiment for clipping exposure.

For each experiment in data/, read its config snapshot and determine:
  - loop_mode (replace-mode is immune to the clip; append-mode may not be)
  - max_context_chars (the buffer size)
  - steps_per_run (does trajectory cross the buffer?)
  - max perturbation dose (does perturbation overflow buffer at injection?)
  - whether clipping kicks in during the experiment

Then classify each experiment as:
  - SAFE: clip never kicks in OR loop_mode is replace
  - PARTIAL: clip kicks in late in trajectory; depends on whether claims use post-clip steps
  - AT-RISK: clip materially affects the experiment (long trajectories AND append-mode AND perturbation)
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Empirical chars/step from F3 control measurement (gpt-4o-mini, max_output_tokens=120)
CHARS_PER_STEP = 600
SEED_CHARS = 100

experiments = []
for exp_dir in sorted(DATA.glob("exp_*")):
    if not exp_dir.is_dir():
        continue
    cfg_path = exp_dir / "config.yaml"
    if not cfg_path.exists():
        continue
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    except Exception as e:
        experiments.append({"experiment": exp_dir.name, "error": str(e)})
        continue
    loop_mode = cfg.get("loop_mode", "?")
    if cfg.get("dialog"):  # dialog experiments use dialog nudge
        loop_mode = f"dialog/{loop_mode}"
    steps = cfg.get("steps_per_run", 0)
    max_ctx = cfg.get("max_context_chars", 0)
    is_dialog = bool(cfg.get("dialog"))
    # Estimate max trajectory length without clipping
    # For dialog, two roles each generate per turn; rough estimate same scale
    est_max_chars = SEED_CHARS + steps * CHARS_PER_STEP
    # Find max perturbation dose
    perturb_block = cfg.get("perturbation") or {}
    conditions = perturb_block.get("conditions", []) or []
    max_dose = 0
    for cond in conditions:
        if "_dose" in cond:
            try:
                d = int(cond.split("_dose")[-1])
                if d > max_dose:
                    max_dose = d
            except ValueError:
                pass
    # Buffer-overflow check: at injection step (typically 15), trajectory + perturbation chars
    # vs max_context_chars.
    inject_step = int(perturb_block.get("override_step", 15))
    traj_at_inject = SEED_CHARS + inject_step * CHARS_PER_STEP
    perturb_chars = max_dose * 4
    overflow_at_inject = traj_at_inject + perturb_chars > max_ctx
    # Clipping during run: when does trajectory itself reach the buffer?
    if loop_mode.startswith("replace"):
        clip_status = "REPLACE-MODE (clip irrelevant)"
        risk = "SAFE"
    elif est_max_chars <= max_ctx:
        clip_status = f"trajectory stays under buffer ({est_max_chars} <= {max_ctx})"
        risk = "SAFE"
    elif overflow_at_inject and max_dose > 0:
        clip_status = f"perturbation overflows at inject ({traj_at_inject}+{perturb_chars} > {max_ctx})"
        risk = "AT-RISK"
    else:
        # Trajectory exceeds buffer at some step. Find which step.
        clip_step = max(1, (max_ctx - SEED_CHARS) // CHARS_PER_STEP)
        clip_status = f"trajectory exceeds buffer at step ~{clip_step} (of {steps})"
        risk = "PARTIAL"
    experiments.append({
        "experiment": exp_dir.name,
        "loop_mode": loop_mode,
        "steps": steps,
        "max_ctx": max_ctx,
        "max_dose": max_dose,
        "est_max_chars": est_max_chars,
        "clip_status": clip_status,
        "risk": risk,
    })

# Sort by risk, then by name
risk_order = {"SAFE": 0, "PARTIAL": 1, "AT-RISK": 2, "?": 3}
experiments.sort(key=lambda r: (risk_order.get(r.get("risk", "?"), 9), r["experiment"]))

# Print summary
print(f"=== Audit of {len(experiments)} experiments ===\n")
for risk in ("SAFE", "PARTIAL", "AT-RISK"):
    matching = [e for e in experiments if e.get("risk") == risk]
    print(f"--- {risk}: {len(matching)} experiments ---")
    for e in matching:
        if "error" in e:
            print(f"  {e['experiment']:50s} ERROR: {e['error']}")
            continue
        print(f"  {e['experiment']:50s} mode={e['loop_mode']:18s} steps={e['steps']:3d}"
              f" buf={e['max_ctx']:6d} max_dose={e['max_dose']:5d}"
              f" est_max={e['est_max_chars']:6d}  | {e['clip_status']}")
    print()
