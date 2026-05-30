"""The recursive agent loop — model-agnostic; the Nudge is injected.
See docs/AGENTIC_MVP_SPEC.md §2.1.

One call to ``run_trajectory`` drives a single trajectory: it owns the
``messages`` list, calls the agent one turn at a time, executes tool
calls against the sandbox, optionally injects a perturbation at
``inject_step``, and hands the running state to the Nudge to assemble
the next visible state. Every step is recorded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.experiments.agentic.agent_client import AgentTurn, run_turn
from src.experiments.agentic.nudges import Nudge, NudgeContext
from src.experiments.agentic.sandbox import Sandbox
from src.experiments.agentic.tools import classify_tool_call, dispatch, tool_schemas
from src.utils.logging import get_logger

log = get_logger(__name__)

DEFAULT_SYSTEM = (
    "You are an autonomous coding agent working in a sandboxed project "
    "directory. You have file and shell tools. Work toward the stated GOAL: "
    "inspect the code, make the necessary edits, and run the tests to verify. "
    "Take one concrete step at a time. When the goal is fully accomplished "
    "and tests pass, state that you are done and stop calling tools."
)


@dataclass
class StepRecord:
    step: int
    reasoning_text: str
    tool_calls: list[dict]          # [{name, params, typed}]
    tool_results: list[str]         # truncated result text, aligned to calls
    tree_hash: str
    test_status: str
    injected: bool
    stop_reason: str
    usage: dict


@dataclass
class TrajectoryResult:
    run_id: str
    task_id: str
    nudge_id: str
    dose: int
    condition: str
    seed: int
    steps: list[StepRecord]
    terminal_step: int
    final_messages: list[dict]      # X_T (for survival detection)
    redirect_text: str | None
    error: str | None = None


# Injection callback: takes the assembled `messages` and returns them with
# the redirect interjected. Defined in inject.py; the loop just calls it.
InjectFn = Callable[[list[dict]], list[dict]]


def run_trajectory(
    *,
    client,
    model: str,
    nudge: Nudge,
    sandbox: Sandbox,
    goal: str,
    run_id: str,
    task_id: str,
    dose: int,
    condition: str,
    seed: int,
    tool_names: list[str],
    steps_per_run: int = 30,
    inject_step: int | None = None,
    inject_fn: InjectFn | None = None,
    redirect_text: str | None = None,
    max_output_tokens: int = 2048,
    temperature: float = 0.8,
    system_prompt: str = DEFAULT_SYSTEM,
) -> TrajectoryResult:
    # The A3 todo Nudge adds the todo_write tool to the agent's toolset.
    active_tools = list(tool_names)
    for extra in getattr(nudge, "extra_tools", []):
        if extra not in active_tools:
            active_tools.append(extra)
    schemas = tool_schemas(active_tools)

    messages = nudge.initial_messages(goal)
    shared_state: dict = {"todo": []}      # cross-tool state (A3 todo list)
    test_status = "(not run)"
    last_result_text = "(no result yet)"
    steps: list[StepRecord] = []
    terminal_step = steps_per_run
    error: str | None = None

    for t in range(steps_per_run):
        try:
            turn = run_turn(
                client, model, system_prompt, messages, schemas,
                max_tokens=max_output_tokens, temperature=temperature,
            )
        except Exception as exc:
            error = f"run_turn failed at step {t}: {exc}"
            log.error(error)
            terminal_step = t
            break

        # Execute tool calls against the sandbox
        tool_results: list[tuple[str, str]] = []   # (tool_use_id, text)
        call_records: list[dict] = []
        result_texts: list[str] = []
        for tc in turn.tool_calls:
            result = dispatch(tc.name, sandbox, tc.params, shared_state)
            tool_results.append((tc.id, result))
            result_texts.append(result[:1000])
            call_records.append({
                "name": tc.name,
                "params": tc.params,
                "typed": classify_tool_call(tc.name, tc.params),
            })
            # Track build/test status from pytest-class commands
            if classify_tool_call(tc.name, tc.params) == "run_bash:test":
                test_status = _summarize_test(result)
            last_result_text = result[:2000]

        injected_here = False
        steps.append(StepRecord(
            step=t,
            reasoning_text=turn.text,
            tool_calls=call_records,
            tool_results=result_texts,
            tree_hash=sandbox.tree_hash(),
            test_status=test_status,
            injected=False,        # set below if injection fires this step
            stop_reason=turn.stop_reason,
            usage=turn.usage,
        ))

        if turn.is_terminal:
            terminal_step = t
            # finalize the visible state as the terminal assistant turn
            messages = _append_assistant(messages, turn.raw_assistant_content)
            break

        # Assemble next visible state via the Nudge
        ctx = NudgeContext(
            goal=goal,
            messages=messages,
            assistant_content=turn.raw_assistant_content,
            tool_results=tool_results,
            tree_manifest=sandbox.manifest(),
            test_status=test_status,
            todo=shared_state.get("todo", []),
            last_result_text=last_result_text,
        )
        messages = nudge.assemble(ctx)

        # Injection: the redirect interjects at inject_step
        if (inject_step is not None and t == inject_step
                and inject_fn is not None):
            messages = inject_fn(messages)
            injected_here = True
            steps[-1].injected = True

    return TrajectoryResult(
        run_id=run_id, task_id=task_id, nudge_id=nudge.id, dose=dose,
        condition=condition, seed=seed, steps=steps,
        terminal_step=terminal_step, final_messages=messages,
        redirect_text=redirect_text, error=error,
    )


def _append_assistant(messages: list[dict], assistant_content) -> list[dict]:
    msgs = list(messages)
    msgs.append({"role": "assistant", "content": assistant_content})
    return msgs


def _summarize_test(result: str) -> str:
    """Compress a pytest result into a one-line status."""
    low = result.lower()
    import re
    m = re.search(r"(\d+) passed", low)
    f = re.search(r"(\d+) failed", low)
    e = re.search(r"(\d+) error", low)
    parts = []
    if m:
        parts.append(f"{m.group(1)} passed")
    if f:
        parts.append(f"{f.group(1)} failed")
    if e:
        parts.append(f"{e.group(1)} error")
    if parts:
        return ", ".join(parts)
    if "no tests ran" in low:
        return "no tests ran"
    return "(ran; status unclear)"
