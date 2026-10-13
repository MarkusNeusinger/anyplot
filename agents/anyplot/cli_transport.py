"""The `claude-cli` transport: Claude calls through the local Claude Code CLI, for experiments only.

With `AGENT_TRANSPORT=claude-cli` (development and test only, `settings.py`), the agents'
Claude calls run through `claude -p` on the developer's own Claude subscription instead
of Vertex AI, so experiments with changed agents, models or agent combinations cost no
Vertex budget while everything else stays the live code: the same ADK agents, prompts,
schemas, plugins, pipeline, validator, renderer and gates. Only the HTTP transport is
replaced, below ADK: `ClaudeCliClient` answers `client.messages.create(**kwargs)` with the
same keyword arguments the Anthropic SDK takes and returns an `anthropic.types.Message`,
so `VertexClaude`, the judge and the offline scorer use it unchanged.

What the CLI can answer, it answers; the rest goes to the fallback client (Vertex AI):

* **Structured calls** (the adapter, the reviewer, the judge, the transcriber): every turn
  is the user's, no tools, `output_config.format` carries the JSON schema. The CLI gets
  the schema as `--json-schema` and the answer comes back as the text block the API's
  structured output writes.
* **Single-tool calls** (the offline scorer's `submit_score`): the tool's input schema is
  the `--json-schema`, and the answer comes back as a `tool_use` block. A retry
  conversation (an assistant turn and a correction) is asked again from its first user
  message, because the CLI cannot replay an assistant turn.
* **Everything else** (the root: chat with several tools and tool results in its
  history) goes to the fallback. Without one, `CliUnsupported` is raised.

Per call the CLI runs with the system prompt replaced (`--system-prompt-file`), no tools,
no settings files, from an empty directory outside the checkout, at the request's
`output_config.effort` (`--effort`). `max_tokens` and the thinking parameters are not
passed: the CLI decides its own thinking, which is the known difference to the live calls.
Usage comes from the CLI's result event, so the budgets and the reports count real tokens;
their dollar figures are list-price equivalents, not money spent.
"""

import asyncio
import json
import logging
import shutil
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

CLI_MODELS: tuple[str, ...] = ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5")
"""Models an experiment may pick per agent kind on this transport (thinking is the CLI's own)."""
EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
DEFAULT_CONCURRENCY = 3
CALL_TIMEOUT_S = 600.0
BLOCK_KEYS: dict[str, tuple[str, ...]] = {"text": ("type", "text"), "image": ("type", "source")}
"""The keys of a content block the CLI's stream-json input takes (no `cache_control`)."""


class CliTransportError(RuntimeError):
    """The CLI did not answer: not installed, not logged in, a usage limit, a timeout, no structured output."""


class CliUnsupported(CliTransportError):
    """A request the CLI cannot answer (tools, an assistant turn) and no fallback client is set."""


def _blocks(content: Any) -> list[dict[str, Any]] | None:
    """A message's content as CLI blocks, or None when it holds a block the CLI cannot take."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}] if content else []
    blocks: list[dict[str, Any]] = []
    for block in content or []:
        item = block if isinstance(block, dict) else block.model_dump(exclude_none=True)
        keys = BLOCK_KEYS.get(item.get("type", ""))
        if keys is None:
            return None
        blocks.append({key: item[key] for key in keys if key in item})
    return blocks


def _system(system: Any) -> str:
    if isinstance(system, str):
        return system
    parts = [block["text"] if isinstance(block, dict) else block.text for block in system or []]
    return "\n\n".join(part for part in parts if part)


def plan_call(kwargs: dict[str, Any]) -> dict[str, Any] | None:
    """How the CLI answers one `messages.create` call, or None when it cannot.

    The result names the model, effort, system prompt, user blocks, the JSON schema (or
    None for free text) and the tool name when the answer is a `tool_use` block.
    """
    tools = list(kwargs.get("tools") or [])
    messages = list(kwargs.get("messages") or [])
    if len(tools) > 1:
        return None
    tool = tools[0] if tools else None
    if tool is not None:
        # A retry conversation of a single-tool call is asked again from its first user message.
        messages = messages[:1]
    if not messages or any(message.get("role") != "user" for message in messages):
        return None
    blocks: list[dict[str, Any]] = []
    for message in messages:
        converted = _blocks(message.get("content"))
        if converted is None:
            return None
        blocks.extend(converted)
    output_config = kwargs.get("output_config") or {}
    if tool is not None:
        schema = tool.get("input_schema")
    else:
        schema = (output_config.get("format") or {}).get("schema")
    effort = output_config.get("effort")
    return {
        "model": kwargs["model"],
        "effort": effort if effort in EFFORTS else None,
        "system": _system(kwargs.get("system")),
        "blocks": blocks,
        "schema": schema,
        "tool": tool.get("name") if tool is not None else None,
    }


def result_event(stdout: str) -> dict[str, Any]:
    """The CLI's final `result` event; raises `CliTransportError` when it is missing or an error."""
    result: dict[str, Any] | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            result = event
    if result is None:
        raise CliTransportError("the CLI wrote no result event")
    if result.get("is_error"):
        raise CliTransportError(f"the CLI reported an error: {str(result.get('result'))[:300]}")
    return result


def to_message(plan: dict[str, Any], result: dict[str, Any]) -> Any:
    """The CLI's answer as the `anthropic.types.Message` the API would have returned."""
    from anthropic.types import Message

    if plan["schema"] is not None:
        output = result.get("structured_output")
        if not isinstance(output, dict):
            raise CliTransportError("the CLI answer carries no structured output")
        if plan["tool"] is not None:
            content: list[dict[str, Any]] = [
                {"type": "tool_use", "id": f"toolu_cli_{uuid.uuid4().hex[:20]}", "name": plan["tool"], "input": output}
            ]
            stop_reason = "tool_use"
        else:
            content, stop_reason = [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}], "end_turn"
    else:
        content, stop_reason = [{"type": "text", "text": str(result.get("result") or "")}], "end_turn"
    usage = result.get("usage") or {}
    return Message.model_validate(
        {
            "id": f"msg_cli_{uuid.uuid4().hex[:20]}",
            "type": "message",
            "role": "assistant",
            "model": plan["model"],
            "content": content,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": int(usage.get("input_tokens") or 0),
                "output_tokens": int(usage.get("output_tokens") or 0),
                "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens") or 0),
                "cache_read_input_tokens": int(usage.get("cache_read_input_tokens") or 0),
            },
        }
    )


Runner = Callable[[list[str], bytes, str], Any]
"""Runs the CLI: (argv, stdin, cwd) → awaitable stdout text. Tests pass a fake."""


async def run_cli(argv: list[str], stdin: bytes, cwd: str) -> str:
    process = await asyncio.create_subprocess_exec(
        *argv, cwd=cwd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(stdin), CALL_TIMEOUT_S)
    except TimeoutError:
        await _reap(process)
        raise CliTransportError(f"the CLI did not answer within {CALL_TIMEOUT_S:.0f} s") from None
    except asyncio.CancelledError:
        # A caller's shorter budget (the judge's) cancelled the call: no orphaned CLI keeps working.
        await asyncio.shield(_reap(process))
        raise
    return stdout.decode("utf-8", "replace")


async def _reap(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        process.kill()
        await process.wait()


class _Messages:
    def __init__(self, owner: "ClaudeCliClient") -> None:
        self._owner = owner

    async def create(self, **kwargs: Any) -> Any:
        return await self._owner.create(**kwargs)


class ClaudeCliClient:
    """An Anthropic-SDK-shaped client whose `messages.create` runs `claude -p` (see the module docstring)."""

    def __init__(
        self,
        *,
        fallback: Any = None,
        concurrency: int = DEFAULT_CONCURRENCY,
        runner: Runner | None = None,
        executable: str | None = None,
        call_log: Path | None = None,
    ) -> None:
        self.fallback = fallback
        self.messages = _Messages(self)
        self._gate = asyncio.Semaphore(concurrency)
        self._runner: Runner = runner or run_cli
        self._executable = executable
        self.call_log = call_log

    def _argv(self, plan: dict[str, Any], system_file: Path) -> list[str]:
        executable = self._executable or shutil.which("claude")
        if executable is None:
            raise CliTransportError("the `claude` CLI is not on PATH")
        argv = [executable, "-p", "--verbose", "--model", plan["model"]]
        if plan["effort"]:
            argv += ["--effort", plan["effort"]]
        argv += ["--system-prompt-file", str(system_file), "--tools", "", "--setting-sources", ""]
        if plan["schema"] is not None:
            argv += ["--json-schema", json.dumps(plan["schema"])]
        return [*argv, "--input-format", "stream-json", "--output-format", "stream-json"]

    async def create(self, **kwargs: Any) -> Any:
        if kwargs.get("stream"):
            raise CliUnsupported("the claude-cli transport does not stream")
        plan = plan_call(kwargs)
        if plan is None:
            if self.fallback is None:
                raise CliUnsupported("the CLI cannot answer a call with tools or an assistant turn")
            return await self.fallback.messages.create(**kwargs)
        message = json.dumps({"type": "user", "message": {"role": "user", "content": plan["blocks"]}}) + "\n"
        async with self._gate:
            started = time.monotonic()
            with tempfile.TemporaryDirectory(prefix="anyplot-cli-") as scratch:
                system_file = Path(scratch) / "system.md"
                system_file.write_text(plan["system"], encoding="utf-8")
                ok = False
                try:
                    stdout = await self._runner(self._argv(plan, system_file), message.encode("utf-8"), scratch)
                    answer = to_message(plan, result_event(stdout))
                    ok = True
                    return answer
                finally:
                    self._log(plan, time.monotonic() - started, ok)

    def _log(self, plan: dict[str, Any], seconds: float, ok: bool) -> None:
        logger.info("claude-cli call: model=%s effort=%s ok=%s %.1fs", plan["model"], plan["effort"], ok, seconds)
        if self.call_log is None:
            return
        entry = {"model": plan["model"], "effort": plan["effort"], "seconds": round(seconds, 1), "ok": ok}
        with self.call_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
