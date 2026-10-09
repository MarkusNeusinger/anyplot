"""The adapter agents: one single-turn agent per enabled library, run only by the pipeline.

Each adapter has a constant static instruction (`policy.adapter_instruction`: the
adapter prompt plus the verbatim catalogue sources for its library), so its prompt
prefix stays cacheable, and it never sees the conversation: `include_contents='none'`
and the `before_model_callback` keeps only the last content, the fenced
`AdaptRequest` the pipeline passes as node input. (ADK 2.11 also prepends the
invocation's user message to a single-turn agent that runs under its own isolation
scope; the callback removes it, so the adapter reads nothing but the request.)

The answer is bound to `AdaptPlan` (`output_schema`); on Claude the model factory
turns that into a forced tool call. `schema_guard` blanks an answer that fails the
schema, so the pipeline repairs it instead of ADK ending the run. On the second
attempt, when a full file is allowed, the callback raises the output cap to
`ADAPTER_FULL_MAX_OUTPUT_TOKENS`.
"""

import logging
from collections.abc import Awaitable, Callable

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.utils._schema_utils import validate_schema
from google.genai import types
from pydantic import BaseModel, ValidationError

from ..models import ADAPTER_FULL_MAX_OUTPUT_TOKENS, make_content_config, make_model
from ..plugins.ledger import ledger_for
from ..policy import adapter_instruction
from ..schemas import AdaptPlan
from ..settings import get_settings


logger = logging.getLogger(__name__)


def schema_guard(schema: type[BaseModel]) -> Callable[[CallbackContext, LlmResponse], Awaitable[LlmResponse | None]]:
    """An `after_model_callback` that blanks an answer which fails `schema`.

    ADK validates a single-turn agent's answer itself (`_llm_agent_wrapper.py`) and
    does not catch the failure: the run would end as an error with no repair, and
    ADK's node runner would log the exception text, which quotes the model's answer,
    at ERROR level. Checking the same way first and blanking an invalid answer makes
    ADK's output None, which the pipeline turns into repair feedback (adapter) or an
    unread review (reviewer). Only the error type is logged.
    """

    async def guard(callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse | None:
        content = llm_response.content
        if llm_response.partial or content is None or not content.parts:
            return None
        text = "".join(part.text for part in content.parts if part.text and not part.thought)
        if not text.strip():
            return None
        try:
            validate_schema(schema, text)
        except (ValidationError, ValueError) as exc:
            logger.warning("%s answer failed its schema: %s", callback_context.agent_name, type(exc).__name__)
            llm_response.content = types.Content(role=content.role or "model", parts=[types.Part(text="")])
        return None

    return guard


def keep_last_content(llm_request: LlmRequest) -> None:
    """Drop everything but the last content: the node input of a single-turn agent."""
    if llm_request.contents:
        llm_request.contents = llm_request.contents[-1:]


async def adapter_before_model(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    keep_last_content(llm_request)
    if ledger_for(callback_context.invocation_id).adapter_allow_full:
        llm_request.config.max_output_tokens = ADAPTER_FULL_MAX_OUTPUT_TOKENS
    return None


def adapter_name(library: str) -> str:
    return f"adapter_{library}"


def make_adapter(library: str) -> Agent:
    return Agent(
        name=adapter_name(library),
        description=f"Adapts {library} catalogue code to the user's dataset; answers with an AdaptPlan.",
        model=make_model("adapter"),
        generate_content_config=make_content_config("adapter"),
        static_instruction=adapter_instruction(library),
        mode="single_turn",
        include_contents="none",
        output_schema=AdaptPlan,
        before_model_callback=adapter_before_model,
        after_model_callback=schema_guard(AdaptPlan),
    )


# The settings refuse a library without a runtime, so every enabled library gets its adapter.
ADAPTERS: dict[str, Agent] = {library: make_adapter(library) for library in get_settings().libraries}
