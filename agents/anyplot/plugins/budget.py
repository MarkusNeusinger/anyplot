"""Budget: request, user-day and global-day limits on model calls, tokens and pipeline runs.

* `before_model_callback` halts **only the root** with the fixed `budget` reply when
  the request has spent `AGENT_MAX_LLM_CALLS` calls or `AGENT_REQUEST_TOKEN_BUDGET`
  tokens, or the user or the service has spent its daily tokens. A halt inside the
  adapter or the reviewer would break their schema parsing, so the pipeline checks
  `ledger.budget_allows` before each `run_node` and finishes with
  `PlotResult(failed, reason=budget)` instead.
* `after_model_callback` books every response's tokens (prompt + candidates +
  thoughts + tool-use prompt; cached tokens are counted separately and never twice),
  the call and the `model_version`, and writes one content-free attribution line.
* `before_tool_callback` on `plot_pipeline` counts the user's daily pipeline runs
  and refuses the call with `{"status": "error", "code": "budget"}` past
  `AGENT_DAILY_PIPELINE_RUNS`. A second call in the same invocation is left to
  ToolSafety, which refuses it, so it is never counted.

The plugin never raises; an internal failure halts the root like an exhausted budget.
"""

import logging
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from ..policy import refusal
from ..services import get_services
from ..settings import get_settings
from .ledger import attribution, budget_allows, ledger_for, usage_tokens


logger = logging.getLogger(__name__)

ROOT_AGENT = "anyplot"
PIPELINE_TOOL = "plot_pipeline"


def budget_response(text: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]), turn_complete=True)


class BudgetPlugin(BasePlugin):
    """Counts and caps model calls, tokens and pipeline runs."""

    def __init__(self, name: str = "anyplot_budget") -> None:
        super().__init__(name=name)

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        ledger = ledger_for(callback_context.invocation_id)
        if callback_context.agent_name != ROOT_AGENT:
            return None
        try:
            settings = get_settings()
            if not ledger.user_id:
                ledger.user_id = callback_context.session.user_id
            if budget_allows(ledger, get_services().usage, settings):
                return None
        except Exception as exc:
            logger.warning("budget check failed: %s", type(exc).__name__)
        text = refusal("budget", ledger.lang)
        ledger.refuse("budget", text)
        attribution("budget_halt", ledger, agent=callback_context.agent_name)
        return budget_response(text)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        try:
            ledger = ledger_for(callback_context.invocation_id)
            if llm_response.partial:
                return None
            billable, cached = usage_tokens(llm_response.usage_metadata)
            ledger.llm_calls += 1
            ledger.tokens += billable
            ledger.cached_tokens += cached
            if llm_response.model_version:
                ledger.model_versions.add(llm_response.model_version)
            user = ledger.user_id or callback_context.session.user_id
            get_services().usage.add_tokens(user, billable)
            attribution(
                "model",
                ledger,
                agent=callback_context.agent_name,
                billable=billable,
                cached=cached,
                model_version=llm_response.model_version,
                finish_reason=str(llm_response.finish_reason) if llm_response.finish_reason else None,
            )
        except Exception as exc:
            logger.warning("budget booking failed: %s", type(exc).__name__)
        return None

    async def before_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext
    ) -> dict[str, Any] | None:
        if tool.name != PIPELINE_TOOL:
            return None
        try:
            ledger = ledger_for(tool_context.invocation_id)
            if ledger.pipeline_calls:
                return None  # ToolSafety refuses the second call; it is not a run
            usage = get_services().usage
            user = ledger.user_id or tool_context.session.user_id
            if not usage.runs_ok(user, get_settings()):
                attribution("budget_pipeline", ledger, verdict="refused")
                return {"status": "error", "code": "budget"}
            usage.add_pipeline_run(user)
            return None
        except Exception as exc:
            logger.warning("pipeline budget failed: %s", type(exc).__name__)
            return {"status": "error", "code": "budget"}
