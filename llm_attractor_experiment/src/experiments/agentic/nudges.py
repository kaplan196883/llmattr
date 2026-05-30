"""The Nudge operators — the experimental IV. See ARTICLE_CODING.md §3.2
and docs/AGENTIC_MVP_SPEC.md §2.3.

A Nudge owns the construction of the next visible state (the Anthropic
``messages`` list) from the running history, the agent's last turn, the
tool results, and the post-tool external state. The loop calls
``nudge.assemble(...)`` once per step.

Each Nudge subclasses ``Nudge`` and implements ``assemble``. The four
MVP Nudges:

  A1 append-full      — accumulate full chat history (optional tail clip)
  A2 summarize-replace — compact history to a summary past a threshold
  A3 todo-replace      — drop history; render goal + todo + tree + last result
  A4 state-replace     — drop everything except goal + tree + status + last result

D1 dialog and D2 reflection are stubbed for the full battery.

`messages` invariant: a list of {"role","content"} dicts in Anthropic
Messages form. The assistant turn is the raw content blocks from the
agent; tool results are user-role messages with tool_result blocks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.experiments.agentic.agent_client import AgentTurn, simple_completion

if TYPE_CHECKING:
    import anthropic


def make_tool_result_message(tool_results: list[tuple[str, str]]) -> dict:
    """Build the user-role message carrying tool_result blocks for the
    tool calls executed this turn. `tool_results` is a list of
    (tool_use_id, result_text)."""
    return {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": tid, "content": text}
            for tid, text in tool_results
        ],
    }


@dataclass
class NudgeContext:
    """Everything a Nudge may read when assembling the next state."""
    goal: str
    messages: list[dict]                 # running history (pre-this-turn)
    assistant_content: list              # this turn's assistant blocks
    tool_results: list[tuple[str, str]]  # (tool_use_id, text) this turn
    tree_manifest: str
    test_status: str
    todo: list[str]
    last_result_text: str


class Nudge:
    id: str = "base"
    extra_tools: list[str] = []          # tool names this Nudge adds

    def initial_messages(self, goal: str) -> list[dict]:
        """The starting `messages` list given the task goal."""
        return [{"role": "user", "content": goal}]

    def assemble(self, ctx: NudgeContext) -> list[dict]:
        raise NotImplementedError


class AppendFull(Nudge):
    """A1. Accumulate the full conversation; optional tail clip on the
    serialized character length (tail_clip_chars=None → infinite, the
    full-history regime; 12000 recovers the parent paper's bounded
    memory)."""

    def __init__(self, tail_clip_chars: int | None = None):
        self.id = "A1_append_full"
        self.tail_clip_chars = tail_clip_chars

    def assemble(self, ctx: NudgeContext) -> list[dict]:
        msgs = list(ctx.messages)
        msgs.append({"role": "assistant", "content": ctx.assistant_content})
        if ctx.tool_results:
            msgs.append(make_tool_result_message(ctx.tool_results))
        if self.tail_clip_chars is not None:
            msgs = _tail_clip(msgs, self.tail_clip_chars)
        return msgs


class SummarizeReplace(Nudge):
    """A2. Append until the serialized history exceeds threshold_chars,
    then replace the middle of the history with a model-generated
    summary. The goal (first user message) and the most recent turn are
    preserved verbatim as anchors."""

    _CONSERVATIVE = (
        "You are compacting an AI coding agent's conversation history so it "
        "fits in a smaller context. Preserve, verbatim or near-verbatim, ANY "
        "explicit user instructions or requests (including mid-task changes "
        "of direction), the current task goal, what files have been changed, "
        "and the latest test status. Drop redundant tool output and "
        "exploration. Output only the summary.")
    _AGGRESSIVE = (
        "Compress this AI coding agent's history into the shortest possible "
        "status note: just the current goal and the single most recent "
        "action. Omit everything else. Output only the note.")

    def __init__(self, client: "anthropic.Anthropic", summarizer_model: str,
                 threshold_chars: int = 24000,
                 summarizer_prompt: str = "preserve_user_instructions"):
        self.id = "A2_summarize_replace"
        self.client = client
        self.summarizer_model = summarizer_model
        self.threshold_chars = threshold_chars
        self.summarizer_prompt = summarizer_prompt

    def _system(self) -> str:
        return (self._AGGRESSIVE if self.summarizer_prompt == "compact_aggressively"
                else self._CONSERVATIVE)

    def assemble(self, ctx: NudgeContext) -> list[dict]:
        msgs = list(ctx.messages)
        msgs.append({"role": "assistant", "content": ctx.assistant_content})
        if ctx.tool_results:
            msgs.append(make_tool_result_message(ctx.tool_results))
        if _serialized_len(msgs) <= self.threshold_chars:
            return msgs
        # Compact: keep first user (goal) + summarize the middle + keep the
        # last assistant/tool-result pair.
        head = msgs[0]
        tail_keep = _trailing_turn(msgs)
        middle = msgs[1:len(msgs) - len(tail_keep)] if tail_keep else msgs[1:]
        transcript = _render_transcript(middle)
        summary = simple_completion(
            self.client, self.summarizer_model, self._system(),
            f"GOAL: {ctx.goal}\n\nHISTORY TO COMPACT:\n{transcript}",
            max_tokens=1024, temperature=0.0,
        )
        compacted = [
            head,
            {"role": "assistant",
             "content": f"[history compacted]\n{summary}"},
        ]
        compacted.extend(tail_keep)
        return compacted


class TodoReplace(Nudge):
    """A3. Drop conversation history at every turn; render goal + the
    maintained todo list (mutated via the todo_write tool) + a working
    tree manifest + the last tool result. The agent re-derives reasoning
    from this structured state each turn."""

    extra_tools = ["todo_write"]

    def __init__(self):
        self.id = "A3_todo_replace"

    def initial_messages(self, goal: str) -> list[dict]:
        return [{"role": "user", "content": _render_todo_state(
            goal, [], "(working tree not yet inspected)", "(no result yet)")}]

    def assemble(self, ctx: NudgeContext) -> list[dict]:
        content = _render_todo_state(
            ctx.goal, ctx.todo, ctx.tree_manifest, ctx.last_result_text)
        return [{"role": "user", "content": content}]


class StateReplace(Nudge):
    """A4. Markov on the external state. Drop everything except goal +
    working-tree manifest + build/test status + last tool result. The
    strongest no-memory regime; approximately immune to in-context
    perturbation because the agent never re-sees an injected user
    message at t+1."""

    def __init__(self):
        self.id = "A4_state_replace"

    def initial_messages(self, goal: str) -> list[dict]:
        return [{"role": "user", "content": _render_markov_state(
            goal, "(working tree not yet inspected)", "(unknown)",
            "(no result yet)")}]

    def assemble(self, ctx: NudgeContext) -> list[dict]:
        content = _render_markov_state(
            ctx.goal, ctx.tree_manifest, ctx.test_status, ctx.last_result_text)
        return [{"role": "user", "content": content}]


# ---------------------------------------------------------------------------
# rendering + serialization helpers
# ---------------------------------------------------------------------------

def _render_todo_state(goal: str, todo: list[str], manifest: str,
                       last_result: str) -> str:
    todo_str = "\n".join(f"  - {t}" for t in todo) or "  (empty — set one with todo_write)"
    return (
        f"GOAL:\n{goal}\n\n"
        f"YOUR TODO LIST:\n{todo_str}\n\n"
        f"{manifest}\n\n"
        f"LAST TOOL RESULT:\n{last_result}\n\n"
        f"Decide the next action. Keep your todo list current with "
        f"todo_write. When the goal is complete, say so and stop."
    )


def _render_markov_state(goal: str, manifest: str, test_status: str,
                         last_result: str) -> str:
    return (
        f"GOAL:\n{goal}\n\n"
        f"{manifest}\n\n"
        f"BUILD/TEST STATUS: {test_status}\n\n"
        f"LAST TOOL RESULT:\n{last_result}\n\n"
        f"Decide the single next action to advance the goal. When the goal "
        f"is complete, say so and stop."
    )


def _serialized_len(messages: list[dict]) -> int:
    total = 0
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            total += len(c)
        elif isinstance(c, list):
            for block in c:
                if isinstance(block, dict):
                    total += len(str(block.get("text", "")))
                    total += len(str(block.get("content", "")))
                    total += len(str(block.get("input", "")))
    return total


def _render_transcript(messages: list[dict]) -> str:
    lines: list[str] = []
    for m in messages:
        role = m.get("role", "?")
        c = m.get("content")
        if isinstance(c, str):
            lines.append(f"[{role}] {c}")
        elif isinstance(c, list):
            for block in c:
                if not isinstance(block, dict):
                    continue
                bt = block.get("type")
                if bt == "text":
                    lines.append(f"[{role}] {block.get('text','')}")
                elif bt == "tool_use":
                    lines.append(f"[{role} calls {block.get('name')}] "
                                 f"{block.get('input')}")
                elif bt == "tool_result":
                    lines.append(f"[tool_result] {block.get('content','')}")
    return "\n".join(lines)


def _trailing_turn(messages: list[dict]) -> list[dict]:
    """The most recent assistant turn + its tool-result message (if any),
    kept verbatim across a compaction."""
    if not messages:
        return []
    keep: list[dict] = []
    # Walk backwards to grab the last assistant message and any following
    # tool_result user message.
    i = len(messages) - 1
    # last message may be a tool_result (user role) following the assistant
    if messages[i].get("role") == "user" and _is_tool_result(messages[i]):
        keep.insert(0, messages[i])
        i -= 1
    if i >= 0 and messages[i].get("role") == "assistant":
        keep.insert(0, messages[i])
    return keep


def _is_tool_result(message: dict) -> bool:
    c = message.get("content")
    return isinstance(c, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in c)


def _tail_clip(messages: list[dict], max_chars: int) -> list[dict]:
    """Keep the first message (goal) and as many trailing messages as fit
    in max_chars. Never split a message. Preserves the assistant/
    tool_result pairing at the boundary by dropping a dangling
    tool_result whose assistant turn was clipped."""
    if not messages:
        return messages
    head = messages[0]
    tail: list[dict] = []
    budget = max_chars - _serialized_len([head])
    for m in reversed(messages[1:]):
        ln = _serialized_len([m])
        if budget - ln < 0 and tail:
            break
        tail.insert(0, m)
        budget -= ln
    # Drop a leading dangling tool_result (its assistant turn was clipped)
    while tail and tail[0].get("role") == "user" and _is_tool_result(tail[0]):
        tail.pop(0)
    return [head] + tail


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------

def build_nudge(spec: dict, *, client=None, summarizer_model: str | None = None
                ) -> Nudge:
    """Instantiate a Nudge from a config entry (see AC1_mvp.yaml `nudges`).

    The config's ``id`` overrides the Nudge's default id, so multiple
    variants of the same kind (e.g. a conservative and an aggressive
    A2 summarize-replace) get distinct run ids and aggregate separately.
    """
    kind = spec["kind"]
    if kind == "append":
        nudge: Nudge = AppendFull(tail_clip_chars=spec.get("tail_clip_chars"))
    elif kind == "summarize_replace":
        nudge = SummarizeReplace(
            client=client,
            summarizer_model=summarizer_model or spec.get("summarizer_model"),
            threshold_chars=spec.get("threshold_chars", 24000),
            summarizer_prompt=spec.get("summarizer_prompt",
                                       "preserve_user_instructions"),
        )
    elif kind == "todo_replace":
        nudge = TodoReplace()
    elif kind == "state_replace":
        nudge = StateReplace()
    else:
        raise ValueError(f"unknown nudge kind: {kind!r}")
    if spec.get("id"):
        nudge.id = spec["id"]
    return nudge
