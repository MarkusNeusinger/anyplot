"""ToolSafety: which agent may call which tool, with which arguments, and what comes back.

* `before_tool_callback`: a per-agent allowlist (the root's seven session tools and its
  `plot_pipeline` workflow; none for the adapters and the reviewer); Pydantic
  validation of the arguments (ADK
  leaves `FUNCTION_TOOL_ARG_VALIDATION` off; `prepare_data` takes at most five
  operations of the `Operation` union, `generate_data` the `generate.Generate`
  spec and `set_language` one value that matches `language.LANGUAGE_PATTERN`, as the
  language route does, and the `invalid_arguments` refusal of the first two carries
  the validation lines
  fenced as `errors`, like the tools' own refusals, so the model can fix the one
  field that was wrong); no link (a scheme such as
  `https://` or `data:image`, or `www.`) or file path in any string argument, as link
  hygiene; at most one `plot_pipeline` call per invocation (the "one repair round"
  bound).
  Personal data in a `change_request` (a name, an address, an e-mail address, a phone
  number, a web address without a scheme or `www.` such as `jana-novak.de`) passes:
  whether plot text is an advertisement or a message to other people is the scope
  judge's call, by intent. Two `prepare_data` arguments are exempt from the link rule
  by key (`DATA_ARGUMENT_KEYS`): a condition's `value` and a rename's `name`. They are
  data, not an instruction to follow: a value is compared with the cells of a column
  and a name becomes a column header, neither is resolved, fetched or run, and both
  may legitimately hold what the user's own table holds, such as a web address in a
  payee column to drop or a column renamed to one. A column reference (`column`,
  `columns`, `by`, `index`, ...) and the new names of a pivot stay under the rule, and
  so does every string of `generate_data`: its names and expressions never need a link.
* `after_tool_callback`: a key allowlist per tool and a size cap of 8 KB (24 KB for
  `get_current_code`, 16 KB for `get_dataset_profile`, `prepare_data`,
  `generate_data` and `plot_pipeline`); a result outside them becomes an error. The `plot_pipeline` result
  reaches the root with its model-written `changes` and `residual_defects` fenced as
  `<tool_notes>` under `notes`.
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

from ..data.generate import Generate
from ..data.prepare import MAX_OPERATIONS, Operation, validation_lines
from ..language import LANGUAGE_PATTERN, MAX_LANGUAGE_CHARS
from ..policy import DATA_PREAMBLE, fence
from ..schemas import MAX_COLUMNS, Binding, PipelineArgs, PlotResult
from .ledger import argument_hash, attribution, ledger_for


logger = logging.getLogger(__name__)

ROOT_AGENT = "anyplot"
PIPELINE_TOOL = "plot_pipeline"
PREPARE_TOOL = "prepare_data"
GENERATE_TOOL = "generate_data"
MAX_RESULT_BYTES = 8 * 1024
MAX_CODE_RESULT_BYTES = 24 * 1024
RESULT_LIMITS: dict[str, int] = {
    "get_current_code": MAX_CODE_RESULT_BYTES,
    # 50 column names of up to 64 characters fit even when the samples are trimmed away.
    "get_dataset_profile": 16 * 1024,
    # The new profile, trimmed like get_dataset_profile's, plus five change lines of at most 300 characters.
    PREPARE_TOOL: 16 * 1024,
    # The profile of at most 12 columns, the change line and one warning per series.
    GENERATE_TOOL: 16 * 1024,
    # A PlotResult at its schema maximum (16 lines of 640, 5 changes of 200) is about 12 KB.
    PIPELINE_TOOL: 16 * 1024,
}
DATA_ARGUMENT_KEYS: dict[str, frozenset[str]] = {PREPARE_TOOL: frozenset({"value", "name"})}
"""Per tool, the argument keys whose strings the link rule skips: data that is compared or written, never followed."""
NOTES_KEY = "notes"
PIPELINE_NOTE_FIELDS = ("changes", "residual_defects")

ErrorCode = str
_URL_OR_PATH = re.compile(
    r"(?i)\b(?:https?|ftp|file|data|javascript):(?=\S)|\bwww\.|(?:^|[\s'\"(])(?:~|\.{1,2})?/[\w.-]+/|[a-z]:\\|\\\\"
)
"""A link (a scheme with something after its colon, or `www.`) or a file path. A scheme word before a space,
as in the caption "Data: my tax return", is ordinary text, as in the sanitiser and the code validator."""


class _NoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _VersionArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=0, le=999)


class _BindingArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bindings: list[Binding] = Field(max_length=MAX_COLUMNS)


class _LanguageArgs(BaseModel):
    """`set_language`: a language name or code, the same pattern as `PUT /v1/sessions/{sid}/language`."""

    model_config = ConfigDict(extra="forbid")
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_CHARS, pattern=LANGUAGE_PATTERN)


class _PrepareArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operations: list[Operation] = Field(min_length=1, max_length=MAX_OPERATIONS)


ARGUMENTS: dict[str, type[BaseModel]] = {
    "get_dataset_profile": _NoArgs,
    "get_spec_brief": _NoArgs,
    "get_current_code": _VersionArgs,
    "set_bindings": _BindingArgs,
    "set_language": _LanguageArgs,
    PREPARE_TOOL: _PrepareArgs,
    GENERATE_TOOL: Generate,
    PIPELINE_TOOL: PipelineArgs,
}
ARGUMENT_ERROR_TOOLS = frozenset({PREPARE_TOOL, GENERATE_TOOL})
"""The tools whose `invalid_arguments` refusal carries the validation lines: arguments the model assembles field by field."""
ALLOWED_TOOLS: dict[str, frozenset[str]] = {ROOT_AGENT: frozenset(ARGUMENTS)}
_DATA_VERSION_KEYS = frozenset(
    {"status", "reason", "code", "message", "errors", "rows", "columns", "version", "changes", "profile", "truncated"}
)
"""The keys of a tool result that stores the next dataset version (`prepare_data`, `generate_data`)."""
RESULT_KEYS: dict[str, frozenset[str]] = {
    "get_dataset_profile": frozenset({"status", "reason", "code", "rows", "profile", "truncated"}),
    "get_spec_brief": frozenset({"status", "code", "brief"}),
    "get_current_code": frozenset({"status", "code", "version"}),
    "set_bindings": frozenset({"status", "reason", "code", "complete", "missing_roles", "errors"}),
    # No value: the root knows what it passed, and a result that echoed free text would need a fence.
    "set_language": frozenset({"status", "code", "source", "changed"}),
    PREPARE_TOOL: _DATA_VERSION_KEYS,
    GENERATE_TOOL: _DATA_VERSION_KEYS,
    # Every PlotResult field, so a field added to the schema (as `version` was) can never turn a
    # shipped plot into `invalid_result` for the root, plus the tool-error shape.
    PIPELINE_TOOL: frozenset(PlotResult.model_fields) | frozenset({"code", "result", "error"}),
}


def tool_error(code: ErrorCode) -> dict[str, Any]:
    return {"status": "error", "code": code}


def result_limit(tool_name: str) -> int:
    """The size cap of a tool's result in UTF-8 bytes of its JSON."""
    return RESULT_LIMITS.get(tool_name, MAX_RESULT_BYTES)


def result_size(result: dict[str, Any]) -> int:
    return len(json.dumps(result, ensure_ascii=False, default=str).encode("utf-8"))


def fence_pipeline_notes(result: dict[str, Any]) -> dict[str, Any]:
    """The PlotResult as the root reads it: the model-written lists fenced as data.

    `changes` (the adapter's) and `residual_defects` (partly the reviewer's) are
    model-written text, so they reach the root inside one `<tool_notes>` block after
    the data preamble instead of as bare strings.
    """
    if not any(result.get(key) for key in PIPELINE_NOTE_FIELDS):
        return {key: value for key, value in result.items() if key not in PIPELINE_NOTE_FIELDS}
    notes = {key: result.get(key) or [] for key in PIPELINE_NOTE_FIELDS}
    fenced = {key: value for key, value in result.items() if key not in PIPELINE_NOTE_FIELDS}
    fenced[NOTES_KEY] = DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(notes, ensure_ascii=False))
    return fenced


def _strings(value: Any, skip: frozenset[str] = frozenset()) -> list[str]:
    """Every string in `value`, except under a dict key in `skip` (at any depth)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for key, item in value.items() if key not in skip for text in _strings(item, skip)]
    if isinstance(value, list | tuple):
        return [text for item in value for text in _strings(item, skip)]
    return []


def has_url_or_path(arguments: dict[str, Any], skip: frozenset[str] = frozenset()) -> bool:
    """Whether any string argument holds a link or a path; the strings under a key in `skip` are not read."""
    return any(_URL_OR_PATH.search(text) for text in _strings(arguments, skip))


def argument_errors(tool_name: str, arguments: dict[str, Any]) -> str:
    """The validation lines of a refused `prepare_data` or `generate_data` call, fenced: they quote the model's own values."""
    try:
        ARGUMENTS[tool_name].model_validate(arguments)
    except ValidationError as exc:
        lines = validation_lines(exc)
    else:
        lines = []
    return DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(lines, ensure_ascii=False))


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
            verdict = self.check(tool.name, tool_args, agent)
            if verdict is None and tool.name == PIPELINE_TOOL:
                if ledger.pipeline_calls >= 1:
                    verdict = "one_pipeline_per_turn"
                else:
                    ledger.pipeline_calls += 1
            attribution(
                "tool", ledger, agent=agent, tool=tool.name, args=argument_hash(tool_args), verdict=verdict or "allowed"
            )
            if verdict is None:
                return None
            refusal = tool_error(verdict)
            if verdict == "invalid_arguments" and tool.name in ARGUMENT_ERROR_TOOLS:
                refusal["errors"] = argument_errors(tool.name, tool_args)
            return refusal
        except Exception as exc:
            logger.warning("tool check failed: %s", type(exc).__name__)
            return tool_error("internal")

    @staticmethod
    def check(name: str, arguments: dict[str, Any], agent: str) -> ErrorCode | None:
        """The refusal code for a call, or None: allowlist, arguments, no URL or path (also used by Budget)."""
        if name not in ALLOWED_TOOLS.get(agent, frozenset()):
            return "tool_not_allowed"
        try:
            ARGUMENTS[name].model_validate(arguments)
        except ValidationError:
            return "invalid_arguments"
        if has_url_or_path(arguments, DATA_ARGUMENT_KEYS.get(name, frozenset())):
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
            replaced = fence_pipeline_notes(result) if tool.name == PIPELINE_TOOL else None
            if result_size(replaced or result) > result_limit(tool.name):
                return tool_error("result_too_large")
            return replaced
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
