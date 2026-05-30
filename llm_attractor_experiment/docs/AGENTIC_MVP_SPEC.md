# Agentic coding loop — MVP experiment spec

*Operationalizes §4 (Methods) of `ARTICLE_CODING.md` for a minimal first
run. Goal: get a fast, cheap signal on the headline hypothesis **H1
(memory policy matters)** before committing to the full battery (H1–H7,
five perturbation classes, three perturbation surfaces, cross-model
invariance).*

The theory (state–generator–nudge factorization lifted to hybrid state,
six Nudge operators, three persistence endpoints, the selectivity
profile) is already specified in `ARTICLE_CODING.md` §3. This document
specifies **what to build and run first** and nothing beyond it.

---

## 1. MVP scope — what is and isn't in the first run

**In scope (the headline slice):**

- **One perturbation class:** `redirect` (a mid-task user message asking
  for a different fix). This is the direct analog of the parent paper's
  text injection and the cleanest endpoint to measure.
- **One perturbation surface:** *in-context* (inject the redirect into
  `X_t` via the user role). External and mediated surfaces are deferred.
- **Four memory Nudges:** `A1 append-full`, `A2 summarize-replace`,
  `A3 todo-replace`, `A4 state-replace`. (D1 dialog, D2 reflection
  deferred — they don't bear on H1.)
- **One workhorse model:** `claude-haiku-4-5` (cheap, fast, reliable
  tool use). Sonnet/Opus reserved for the H7 cross-scale check, not run
  in the MVP.
- **One endpoint computed for the headline:** `redirect-survival`
  (Endpoint 1, §3.3) — a property of the Nudge alone, requires no task
  oracle, cheapest to compute. `redirect-compliance` (Endpoint 3) is
  logged but computed as a secondary diagnostic.
- **Small curated task set:** 5 synthetic self-contained coding tasks
  with deterministic pass/fail oracles (see §4). SWE-bench-Lite deferred
  to the full run.
- **Dose grid:** 6 doses spanning the predicted ED50 (H1 predicts
  append-full ED50 ≈ 50–200 tokens): `0 (control), 25, 50, 100, 200,
  400` tokens of redirect text.

**Out of scope for the MVP (deferred to the full battery):**

- Perturbation classes `tool-error`, `stale-state`, `misleading-test`,
  `poison-doc` (§3.4).
- External + mediated perturbation surfaces (§3.6).
- Nudges D1 (dialog), D2 (reflection).
- Cross-model invariance H7 (Sonnet, Opus).
- Summarizer-prompt sensitivity H2 (MVP runs ONE summarizer prompt;
  the conservative/aggressive contrast is the full run).
- SWE-bench-Lite task suite (MVP uses synthetic tasks).
- Patch-distance basin maps, tool-trace cluster enumeration (§5.8–5.9).

**MVP success gate:** if the redirect-survival rate at the top dose
(400 tokens) differs between `A1 append-full` and `A4 state-replace` by
≥ 30 percentage points with non-overlapping Wilson intervals, the
memory-policy effect is real and the full battery is worth the spend.
H4 predicts `A4 state-replace` survival ≤ 10% at all doses; if that
holds and `A1` clears 50%, we have the headline.

---

## 2. The harness architecture

A minimal Python harness. The Nudge is a **pluggable component** — this
is the whole point, since the Nudge is the experimental IV and
off-the-shelf agents don't let you swap it.

```
src/experiments/agentic/
  __init__.py
  loop.py          # the recursive agent loop (model-agnostic)
  nudges.py        # Nudge operators: A1, A2, A3, A4 (D1, D2 stubbed)
  tools.py         # sandboxed tool dispatch (read/write/edit/bash/search)
  sandbox.py       # per-run isolated working-tree + command jail
  tasks.py         # task suite loader + pass/fail oracle
  inject.py        # perturbation injection (redirect class, in-context)
  endpoints.py     # Surv / Succ / Comp computation
  runner.py        # config → trajectories → JSONL (mirrors perturbation/runner.py)
  judge.py         # basin / compliance labeling via judge model
```

### 2.1 The loop (one trajectory)

```
init: X_0 = render(system_prompt, goal, initial working-tree manifest)
for t in 0 .. steps_per_run-1:
    Y_t = MODEL.call(X_t, tools)          # (reasoning r_t, tool_calls A_t)
    O_t, E_{t+1} = SANDBOX.execute(A_t)   # run tools, mutate working tree
    if t == inject_step and condition != control:
        # in-context redirect: inject as a user message into the turn
        Y_t, X_t = INJECT.redirect(Y_t, X_t, dose)
    X_{t+1} = NUDGE.assemble(X_t, Y_t, E_{t+1})   # ← the IV
    record(t, X_t, Y_t, A_t, O_t, E_{t+1}, basin_label)
    if Y_t.is_terminal: break
finalize: run task oracle on E_T → pass/fail; compute Surv/Comp
```

### 2.2 Tools (sandboxed, 5 total for the MVP)

| tool | params | sandbox behavior |
|---|---|---|
| `read_file` | path | read within sandbox root only |
| `write_file` | path, content | write within sandbox root only |
| `edit_file` | path, old, new | string-replace within sandbox root |
| `run_bash` | command | run in jailed subprocess, CWD = sandbox root, no network, wall-clock timeout, output truncated |
| `search` | pattern, glob | ripgrep within sandbox root |

All paths are resolved against the per-run sandbox root and rejected if
they escape it. `run_bash` is the only execution surface and is the one
that needs the tightest jail (see §5).

### 2.3 The four Nudge operators (MVP)

Each implements `assemble(X_t, Y_t, E_{t+1}) -> X_{t+1}` per §3.2:

- **A1 append-full** (`loop_mode: append`, `tail_clip: inf`): standard
  chat-history accumulation. Also support `tail_clip: 12000` to recover
  the parent paper's bounded-memory regime as a sub-condition.
- **A2 summarize-replace** (`summarizer_model`, `threshold_chars`): when
  context exceeds threshold, replace history with a model-generated
  summary; Goal preserved verbatim as anchor. MVP uses ONE summarizer
  prompt (`preserve_user_instructions: true`, i.e. the conservative
  variant) — the conservative/aggressive contrast is H2, deferred.
- **A3 todo-replace**: drop history; render Goal + maintained Todo list
  (mutated only via a `todo_write` tool, added to the toolset for this
  Nudge) + working-tree manifest + last tool result.
- **A4 state-replace**: drop everything except Goal + working-tree
  manifest + build/test status + last tool result. Markov on E.

### 2.4 What gets logged (JSONL, one row per step)

Mirror `data/<experiment_id>/...` layout from the perturbation runner so
the existing aggregation/plotting pipeline can be pointed at it. Per
step: `run_id, family/task_id, ic_id, nudge, dose, step, reasoning_text,
tool_calls (typed), tool_results (truncated), working_tree_hash,
test_status, basin_label, is_terminal`. Per run: `task_pass,
redirect_survival, redirect_compliance, terminal_step`.

---

## 3. Models needed

| role | model | why | MVP cost driver |
|---|---|---|---|
| **agent (system under test)** | `claude-haiku-4-5` | cheap, fast, reliable tool use; H7 anchor low end | the bulk of spend |
| **summarizer σ** (A2 only) | `claude-haiku-4-5` | same family; cheap; fired only when context > threshold | low |
| **judge** (basin + compliance labels) | `claude-sonnet-4-6` | stronger than agent so labels aren't the weak link; validate vs human sample | moderate |
| **embedding** (secondary diagnostic only) | `text-embedding-3-small` | continuity with parent pipeline; conversation-tail clusters are NOT load-bearing here (§1.3) | negligible |

No GPU. All via Anthropic API (agent + summarizer + judge) + OpenAI API
(embeddings only). The full battery adds `claude-sonnet-4-6` and
`claude-opus-4-7` as agent models for H7.

### 3.1 Cost estimate (MVP)

- Cells: 4 Nudges × 6 doses × 5 tasks × 4 seeds = **480 trajectories**
  (control dose shared across Nudges where the Nudge doesn't act
  pre-injection, but budget for the full 480 to be safe).
- ~30 steps/trajectory, agentic context (manifest + history + tool
  output) ≈ 8–15K in / 1–2K out per step.
- ≈ 480 × 30 × ~12K in ≈ 170M input tokens, ~22M output tokens on
  Haiku 4.5.
- Plus summarizer fires (A2 only) + judge labeling (480 × 30 steps).
- **Estimated MVP total: roughly USD 80–150.** Under $150 to learn
  whether the headline effect exists.

---

## 4. Task suite (MVP — 5 synthetic tasks)

Self-contained, deterministic oracle, no external dependencies, each
solvable by Haiku 4.5 in < 30 steps at baseline. Each task ships as a
sandbox seed directory + a hidden test the oracle runs at termination.

1. **bugfix-offbyone** — fix an off-by-one in a `paginate()` function;
   oracle = pytest on a hidden test file.
2. **add-validation** — add input validation to a `parse_config()`;
   oracle = pytest.
3. **refactor-extract** — extract a duplicated block into a helper;
   oracle = pytest (behavior preserved) + a duplication check.
4. **implement-stub** — implement a documented-but-empty `merge_intervals`;
   oracle = pytest.
5. **fix-failing-test** — a repo with one failing test; make it pass
   without breaking the others; oracle = full pytest run.

The **redirect** perturbation for each task is a plausible-but-different
coding instruction (e.g. "actually, stop — rewrite this in a functional
style with no mutation" or "switch the data structure to a heap
instead"), scaled to the dose token budget. The redirect is *in
distribution* (a thing a real user might say), matching the parent
paper's in-distribution-perturbation design.

Per-task **stochastic floor**: two paired control runs (no injection,
different seed) disagree from sampling alone; net survival/compliance
subtracts this per-task floor (§3.5, parent §net-switching).

---

## 5. Sandbox & safety

The MVP redirect class is benign (alternative coding instructions), so
no destructive payloads are involved. The sandbox still matters because
`run_bash` executes model-emitted commands.

- **Filesystem jail:** per-run temp dir as sandbox root; all tool paths
  resolved against it and rejected on escape (`..`, absolute paths
  outside root, symlink traversal).
- **Command jail:** `run_bash` runs in a subprocess with CWD = sandbox
  root, `network disabled`, a wall-clock timeout (e.g. 30 s), output
  truncated to N KB, and a denylist for obviously out-of-scope commands
  (`curl`, `wget`, `ssh`, package installs) — the MVP tasks need none of
  these.
- **No real secrets, no network egress.** Even though the redirect class
  is benign, the harness is built network-off from day one so the later
  `poison-doc` / exfiltration-style classes (full battery) inherit the
  jail rather than bolting it on.
- **Intent-vs-action:** for later destructive classes, measure the tool
  call the agent *attempts* against a simulated sink — never real
  damage. Designed in now, used later.

This sandbox design feeds directly into the Broader Impact statement
already drafted for the parent paper's TMLR submission.

---

## 6. Analysis (MVP)

- **Primary:** redirect-survival rate vs dose, one curve per Nudge;
  logistic fit → ED50 per Nudge; Wilson 95% CI per (Nudge, dose) cell;
  family-cluster bootstrap (cluster = task) for ED50 CIs. Headline plot:
  four dose-response curves on one axis.
- **H1 test:** max pairwise ED50 ratio across the four Nudges ≥ 3.0 with
  bootstrap CI above 1.5 (§3.8 endpoint 1).
- **H4 spot-check:** A4 state-replace survival ≤ 10% at all doses.
- **Secondary diagnostics (logged, not load-bearing):**
  redirect-compliance rate, task-success delta, conversation-tail
  embedding clusters (reuse parent PCA+KMeans), tool-trace transition
  counts.

Reuse `src/experiments/perturbation/analyze.py` machinery where the data
schema matches; add agentic-specific endpoint computation in
`endpoints.py`.

---

## 7. Build order

1. `sandbox.py` + `tools.py` — jailed working tree + 5 tools. Unit-test
   the path/command jail first.
2. `loop.py` + `nudges.py` (A1 only) — get one trajectory running
   end-to-end on task 1 with append-full, no injection.
3. `tasks.py` + oracle — verify baseline pass rate on all 5 tasks.
4. `inject.py` — redirect injection at `inject_step`, dose-scaled.
5. `nudges.py` A2/A3/A4 — the other three memory policies.
6. `endpoints.py` + `judge.py` — Surv (primary) + Comp (diagnostic).
7. `runner.py` — config → 480 trajectories → JSONL.
8. Smoke run: 1 task × 4 Nudges × 2 doses × 1 seed = 8 trajectories,
   eyeball the traces, then scale to the full 480.

---

## 8. Open decisions for the user

1. **Agent model for the MVP** — spec assumes `claude-haiku-4-5`. (The
   parent paper used OpenAI gpt-4o-mini/4.1-nano; if you want continuity
   you could run the MVP on an OpenAI tool-calling model instead. The
   theory doc §4 commits to the Anthropic stack, so the spec follows
   that.)
2. **Task substrate** — spec uses 5 synthetic tasks for speed/clean
   oracles. Alternative: jump straight to 5 hand-picked SWE-bench-Lite
   tasks for realism at higher cost and noisier baselines.
3. **Judge vs embed-cluster** for the basin label — spec uses a judge
   model (cleaner categorical basins); the embed+cluster path reuses the
   parent pipeline verbatim but is noisier on short agentic reasoning
   text.
