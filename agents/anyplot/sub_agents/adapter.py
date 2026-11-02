"""The adapter agents: one single-turn agent per enabled library, run only by the pipeline.

Each adapter has a constant static instruction (`policy.adapter_instruction`: the
adapter prompt plus the verbatim catalogue sources for its library), so its prompt
prefix stays cacheable, and it never sees the conversation: `include_contents='none'`
and the `before_model_callback` keeps only the last content, the fenced
`AdaptRequest` the pipeline passes as node input. (ADK 2.13 also prepends the
invocation's user message to a single-turn agent that runs under its own isolation
scope; the callback removes it, so the adapter reads nothing but the request.)

The answer is bound to `AdaptPlan` (`output_schema`); on Claude the model factory
turns that into a structured-output format (`models.structured_output_format`), whose
grammar enforces the shape but not the lengths and counts. `schema_guard` mends an
answer that misses only such a formal rule (`schemas.repair_plan`) and blanks one that
still fails the schema, so
the pipeline repairs it instead of ADK ending the run. On the second
attempt, when a full file is allowed, the callback widens the request through
`models.allow_full_file`: the output cap rises to `ADAPTER_FULL_MAX_OUTPUT_TOKENS`
(16,384) on Claude and `GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS` (12,288) on Gemini, where
the thinking level also drops to LOW.
"""

import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.utils._schema_utils import validate_schema
from google.genai import types
from pydantic import BaseModel, ValidationError

from ..models import allow_full_file, make_content_config, make_model
from ..plugins.ledger import attribution, ledger_for
from ..policy import adapter_instruction
from ..schemas import AdaptPlan, repair_plan
from ..settings import get_settings


logger = logging.getLogger(__name__)

Repair = Callable[[Any], Any]
MAX_LOGGED_ERRORS = 8
"""Schema errors one attribution line names; an answer that breaks more rules is rarely mendable anyway."""
_LOC_PART = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,40}$")
_FENCE = re.compile(r"^```[A-Za-z0-9_-]*\s*\n?(.*?)\n?```$", re.DOTALL)


def schema_errors(exc: Exception) -> list[str]:
    """The broken rules of a failed answer as `<loc>:<type>` (for example `defects.0.observed:string_too_long`).

    Content-free: a location part is a list index or a schema field name (a part that
    looks like anything else is written `?`, a rule on the whole answer `answer`), and
    the type is pydantic's error code, never its message, which can quote the answer.
    """
    if not isinstance(exc, ValidationError):
        return [f"answer:{type(exc).__name__}"]
    rules = []
    for error in exc.errors()[:MAX_LOGGED_ERRORS]:
        parts = [str(part) if isinstance(part, int) or _LOC_PART.match(str(part)) else "?" for part in error["loc"]]
        rules.append(f"{'.'.join(parts) or 'answer'}:{error['type']}")
    return rules


def _answer_json(text: str) -> Any:
    """The answer's JSON value (a code fence around it is dropped, as ADK's own parse does), or None."""
    stripped = text.strip()
    fenced = _FENCE.match(stripped)
    try:
        return json.loads(fenced.group(1) if fenced else stripped)
    except ValueError:
        return None


def _repaired(schema: type[BaseModel], repair: Repair | None, text: str) -> str | None:
    """The answer mended by `repair` as JSON text, if the mended answer passes the strict schema."""
    data = _answer_json(text)
    if repair is None or data is None:
        return None
    try:
        return schema.model_validate(repair(data)).model_dump_json()
    except ValidationError, ValueError:
        return None


def schema_guard(
    schema: type[BaseModel], repair: Repair | None = None
) -> Callable[[CallbackContext, LlmResponse], Awaitable[LlmResponse | None]]:
    """An `after_model_callback` that mends or blanks an answer which fails `schema`, and blanks a cut-off one.

    ADK validates a single-turn agent's answer itself (`_llm_agent_wrapper.py`) and
    does not catch the failure: the run would end as an error with no repair, and
    ADK's node runner would log the exception text, which quotes the model's answer,
    at ERROR level. So the guard checks the same way first. An answer that fails is
    given to `repair` (`schemas.repair_verdict`, `schemas.repair_plan`), which mends
    only formal misses; when the mended answer passes the strict schema it replaces
    the answer, otherwise the answer is blanked, which makes ADK's output None and
    the pipeline turns into repair feedback (adapter) or an unread review (reviewer).
    Either way one content-free `answer_schema` attribution line names the agent, the
    outcome (`repaired` or `refused`) and the broken rules (`schema_errors`).

    An answer that ended at the output limit (`FinishReason.MAX_TOKENS`) is blanked
    without a check: every field of `AdaptPlan` has a default, so an answer cut off and
    then mended to `{}` or to its first edits would pass as a plan that silently drops
    the rest. The pipeline reads the finish reason from the request ledger and tells the
    repair the answer was cut off.
    """

    async def guard(callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse | None:
        content = llm_response.content
        if llm_response.partial or content is None or not content.parts:
            return None
        text = "".join(part.text for part in content.parts if part.text and not part.thought)
        if not text.strip():
            return None
        agent = callback_context.agent_name
        role = content.role or "model"
        if llm_response.finish_reason == types.FinishReason.MAX_TOKENS:
            logger.warning("%s answer was cut off at the output limit", agent)
            llm_response.content = types.Content(role=role, parts=[types.Part(text="")])
            return None
        try:
            validate_schema(schema, text)
            return None
        except (ValidationError, ValueError) as exc:
            errors = schema_errors(exc)
        mended = _repaired(schema, repair, text)
        attribution(
            "answer_schema",
            ledger_for(callback_context.invocation_id),
            agent=agent,
            outcome="refused" if mended is None else "repaired",
            errors=errors,
        )
        if mended is None:
            logger.warning("%s answer failed its schema: %s", agent, ", ".join(errors))
        llm_response.content = types.Content(role=role, parts=[types.Part(text=mended or "")])
        return None

    return guard


def keep_last_content(llm_request: LlmRequest) -> None:
    """Drop everything but the last content: the node input of a single-turn agent."""
    if llm_request.contents:
        llm_request.contents = llm_request.contents[-1:]


async def adapter_before_model(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    keep_last_content(llm_request)
    ledger = ledger_for(callback_context.invocation_id)
    if ledger.adapter_allow_full:
        allow_full_file(llm_request.config)
    if ledger.adapter_renders:
        # Renders the adapter sees once, each after its label: the current render in a self-review
        # (`AGENT_SELF_REVIEW`), and the reviewed render before a repair (`AGENT_REPAIR_SEES_RENDER`).
        from ..services import get_services

        renders, ledger.adapter_renders = ledger.adapter_renders, []
        parts: list[types.Part] = []
        for label, render_id in renders:
            stored = get_services().renders.get(render_id, callback_context.session.id)
            for theme, png in stored.pngs.items() if stored is not None else []:
                parts += [
                    types.Part(text=f"{label} (plot-{theme}.png):"),
                    types.Part.from_bytes(data=png, mime_type="image/png"),
                ]
        if parts and llm_request.contents:
            last = llm_request.contents[-1]
            last.parts = [*(last.parts or []), *parts]
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
        after_model_callback=schema_guard(AdaptPlan, repair_plan),
    )


# The settings refuse a library without a runtime, so every enabled library gets its adapter.
ADAPTERS: dict[str, Agent] = {library: make_adapter(library) for library in get_settings().libraries}
