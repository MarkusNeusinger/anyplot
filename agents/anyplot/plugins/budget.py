"""Budget: request, user-day and global-day limits on model calls, tokens and pipeline runs.

* `before_model_callback` halts **only the root** with the fixed `budget` reply when
  the request has spent `AGENT_MAX_LLM_CALLS` calls or `AGENT_REQUEST_TOKEN_BUDGET`
  cost-weighted tokens (`ledger.BUDGET_WEIGHTS`), or the user or the service has spent
  its daily ones. A halt inside the adapter or the reviewer would break their schema
  parsing, so the pipeline checks `ledger.budget_allows` before each `run_node` and
  finishes with `PlotResult(failed, reason=budget)` instead. Before a review it keeps
  room for the review and the root's closing reply (`pipeline.REVIEW_RESERVE_TOKENS`,
  the measured need), and once a plot has shipped in the invocation
  (`ledger.plot_shipped`) the root's next call is exempt from the halt, once and with
  its tools stripped, so it can only be the closing reply and a shipped plot is never
  answered with the `budget` refusal; that reply is bounded by the root's output cap,
  and any further root call is checked again.
* `after_model_callback` books every response's tokens (prompt + candidates +
  thoughts + tool-use prompt; cached tokens are counted separately and never twice)
  and their cost-weighted sum (`ledger.budget_tokens`, which the request and daily
  budgets count; the attribution line carries it as `budget`), the call and the
  `model_version`, keeps the call's finish reason and output tokens in
  `ledger.last_calls` for the pipeline, and writes one content-free attribution line
  with the token counts by kind (`ledger.usage_breakdown`), which the eval harness
  prices (`agents/evals/pricing.py`), and the finish reason by its enum name
  (`STOP`, `MAX_TOKENS`).
* `before_tool_callback` on `plot_pipeline` counts the user's daily pipeline runs
  and refuses the call with `{"status": "error", "code": "budget"}` past
  `AGENT_DAILY_PIPELINE_RUNS`. A second call in the same invocation, and a call
  ToolSafety's own check refuses (invalid arguments, a URL), are left to ToolSafety
  and never counted.

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
from .ledger import (
    CallFacts,
    RequestLedger,
    attribution,
    budget_allows,
    budget_tokens,
    finish_name,
    ledger_for,
    usage_breakdown,
    usage_tokens,
)
from .tool_safety import ToolSafetyPlugin


logger = logging.getLogger(__name__)

ROOT_AGENT = "anyplot"
PIPELINE_TOOL = "plot_pipeline"


def budget_response(text: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]), turn_complete=True)


def strip_tools(llm_request: LlmRequest) -> None:
    """Leave the call without tools, so the model can only answer: both providers read these two fields."""
    llm_request.config.tools = None
    llm_request.config.tool_config = None
    llm_request.tools_dict = {}


def book_response(ledger: RequestLedger, agent_name: str, session_user: str, llm_response: LlmResponse) -> None:
    """Book one model response's tokens, call and model version, and write its attribution line.

    The plugin's `after_model_callback` books every call ADK makes; a call made outside ADK's
    flow (the reply-language plugin's one re-ask) books itself through this function too.
    """
    billable, cached = usage_tokens(llm_response.usage_metadata)
    weighted = budget_tokens(llm_response.usage_metadata)
    ledger.llm_calls += 1
    ledger.tokens += billable
    ledger.cached_tokens += cached
    ledger.budget_tokens += weighted
    if llm_response.model_version:
        ledger.model_versions.add(llm_response.model_version)
    user = ledger.user_id or session_user
    get_services().usage.add_tokens(user, weighted)
    breakdown = usage_breakdown(llm_response.usage_metadata)
    finish = finish_name(llm_response.finish_reason)
    ledger.last_calls[agent_name] = CallFacts(finish, breakdown["candidates"], breakdown["thoughts"])
    # The usage telemetry's tokens per step (`telemetry.step_tokens`): counts and the model id only.
    ledger.book_step(agent_name, model=llm_response.model_version, usage=breakdown, cached=cached)
    attribution(
        "model",
        ledger,
        agent=agent_name,
        billable=billable,
        cached=cached,
        budget=weighted,
        **breakdown,
        model_version=llm_response.model_version,
        finish_reason=finish,
    )


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
            if ledger.plot_shipped:
                ledger.plot_shipped = False  # one call only, and without tools: the closing reply
                strip_tools(llm_request)
                attribution("budget_exempt", ledger, agent=callback_context.agent_name)
                return None
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
            book_response(ledger, callback_context.agent_name, callback_context.session.user_id, llm_response)
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
            if ToolSafetyPlugin.check(tool.name, tool_args, tool_context.agent_name) is not None:
                return None  # ToolSafety refuses an invalid call; it is not a run either
            usage = get_services().usage
            user = ledger.user_id or tool_context.session.user_id
            if not usage.runs_ok(user, get_settings(), ledger.tier):
                attribution("budget_pipeline", ledger, verdict="refused")
                return {"status": "error", "code": "budget"}
            usage.add_pipeline_run(user)
            return None
        except Exception as exc:
            logger.warning("pipeline budget failed: %s", type(exc).__name__)
            return {"status": "error", "code": "budget"}
