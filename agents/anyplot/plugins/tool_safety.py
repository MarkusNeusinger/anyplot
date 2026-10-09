"""ToolSafety: which agent may call which tool, with which arguments, and what comes back.

* `before_tool_callback`: a per-agent allowlist (the root's five session tools; none
  for the adapters and the reviewer); Pydantic validation of the arguments (ADK
  leaves `FUNCTION_TOOL_ARG_VALIDATION` off); no URL or file path in any string
  argument; at most one `plot_pipeline` call per invocation (the "one repair round"
  bound).
* `after_tool_callback`: a key allowlist per tool and a size cap of 8 KB (24 KB for
  `get_current_code`); a result outside them becomes an error.
* `on_tool_error_callback`: any exception becomes `{"status": "error", "code": ...}`
  with a fixed code; the exception text never reaches the model.

Every refusal is `{"status": "error", "code": <enum>}`. The plugin never raises.
"""

import json
import logging
import re
from typing import Any

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..schemas import MAX_COLUMNS, Binding, PipelineArgs
from .ledger import argument_hash, attribution, ledger_for


logger = logging.getLogger(__name__)

ROOT_AGENT = "anyplot"
PIPELINE_TOOL = "plot_pipeline"
MAX_RESULT_BYTES = 8 * 1024
MAX_CODE_RESULT_BYTES = 24 * 1024

ErrorCode = str
_URL_OR_PATH = re.compile(
    r"(?i)\b(?:https?|ftp|file|data|javascript):|\bwww\.|(?:^|[\s'\"(])(?:~|\.{1,2})?/[\w.-]+/|[a-z]:\\|\\\\"
)


class _NoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _VersionArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=0, le=999)


class _BindingArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bindings: list[Binding] = Field(max_length=MAX_COLUMNS)


ARGUMENTS: dict[str, type[BaseModel]] = {
    "get_dataset_profile": _NoArgs,
    "get_spec_brief": _NoArgs,
    "get_current_code": _VersionArgs,
    "set_bindings": _BindingArgs,
    PIPELINE_TOOL: PipelineArgs,
}
ALLOWED_TOOLS: dict[str, frozenset[str]] = {ROOT_AGENT: frozenset(ARGUMENTS)}
RESULT_KEYS: dict[str, frozenset[str]] = {
    "get_dataset_profile": frozenset({"status", "reason", "code", "rows", "profile"}),
    "get_spec_brief": frozenset({"status", "code", "brief"}),
    "get_current_code": frozenset({"status", "code", "version"}),
    "set_bindings": frozenset({"status", "reason", "code", "complete", "missing_roles", "errors"}),
    PIPELINE_TOOL: frozenset(
        {"status", "reason", "attempts", "artifacts", "changes", "residual_defects", "code", "result", "error"}
    ),
}


def tool_error(code: ErrorCode) -> dict[str, Any]:
    return {"status": "error", "code": code}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list | tuple):
        return [text for item in value for text in _strings(item)]
    return []


def has_url_or_path(arguments: dict[str, Any]) -> bool:
    return any(_URL_OR_PATH.search(text) for text in _strings(arguments))


def error_code(error: Exception) -> ErrorCode:
    """A fixed code for a tool exception; the exception text is never used."""
    if isinstance(error, ValidationError | ValueError | TypeError | KeyError):
        return "invalid_arguments"
    if isinstance(error, TimeoutError):
        return "timeout"
    return "internal"


class ToolSafetyPlugin(BasePlugin):
    """Allowlists tools per agent, validates arguments, caps results and maps errors."""

    def __init__(self, name: str = "anyplot_tool_safety") -> None:
        super().__init__(name=name)

    async def before_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext
    ) -> dict[str, Any] | None:
        try:
            ledger = ledger_for(tool_context.invocation_id)
            agent = tool_context.agent_name
            verdict = self._check(tool.name, tool_args, agent)
            if verdict is None and tool.name == PIPELINE_TOOL:
                if ledger.pipeline_calls >= 1:
                    verdict = "one_pipeline_per_turn"
                else:
                    ledger.pipeline_calls += 1
            attribution(
                "tool", ledger, agent=agent, tool=tool.name, args=argument_hash(tool_args), verdict=verdict or "allowed"
            )
            return tool_error(verdict) if verdict else None
        except Exception as exc:
            logger.warning("tool check failed: %s", type(exc).__name__)
            return tool_error("internal")

    @staticmethod
    def _check(name: str, arguments: dict[str, Any], agent: str) -> ErrorCode | None:
        if name not in ALLOWED_TOOLS.get(agent, frozenset()):
            return "tool_not_allowed"
        try:
            ARGUMENTS[name].model_validate(arguments)
        except ValidationError:
            return "invalid_arguments"
        if has_url_or_path(arguments):
            return "url_or_path_not_allowed"
        return None

    async def after_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext, result: dict[str, Any]
    ) -> dict[str, Any] | None:
        try:
            if not isinstance(result, dict):
                return tool_error("invalid_result")
            allowed = RESULT_KEYS.get(tool.name)
            if allowed is None:
                return tool_error("tool_not_allowed")
            if set(result) - allowed:
                return tool_error("invalid_result")
            limit = MAX_CODE_RESULT_BYTES if tool.name == "get_current_code" else MAX_RESULT_BYTES
            if len(json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")) > limit:
                return tool_error("result_too_large")
            return None
        except Exception as exc:
            logger.warning("tool result check failed: %s", type(exc).__name__)
            return tool_error("internal")

    async def on_tool_error_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext, error: Exception
    ) -> dict[str, Any] | None:
        code = error_code(error)
        try:
            attribution("tool_error", ledger_for(tool_context.invocation_id), tool=tool.name, code=code)
        except Exception:
            logger.warning("tool error attribution failed")
        return tool_error(code)
