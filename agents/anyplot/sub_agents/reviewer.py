"""The reviewer: a tool-less single-turn agent that judges the two renders once.

Its static instruction is `policy.reviewer_instruction` (the reduced checklist, the
defect grammar, the catalogue's theme-readability check and the style guide). The
pipeline passes a fenced `ReviewRequest` as node input; the `before_model_callback`
keeps only that content and appends the light and the dark PNG as ordinary image
parts, loaded by `render_id` (from the request ledger) out of the session's
`RenderStore`. No image ever travels through session state or a tool. The answer is
bound to `Verdict`.
"""

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from ..models import make_content_config, make_model
from ..plugins.ledger import ledger_for
from ..policy import reviewer_instruction
from ..schemas import Verdict
from ..services import get_services
from .adapter import keep_last_content


REVIEWER_NAME = "reviewer"


class RenderMissing(RuntimeError):
    """The render to review is not in the session's render store."""


async def reviewer_before_model(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    keep_last_content(llm_request)
    render_id = ledger_for(callback_context.invocation_id).review_render_id
    stored = get_services().renders.get(render_id, callback_context.session.id) if render_id else None
    if stored is None or "light" not in stored.pngs or "dark" not in stored.pngs:
        raise RenderMissing("the render to review is not available")
    parts = [
        types.Part(text="Light render (plot-light.png):"),
        types.Part.from_bytes(data=stored.pngs["light"], mime_type="image/png"),
        types.Part(text="Dark render (plot-dark.png):"),
        types.Part.from_bytes(data=stored.pngs["dark"], mime_type="image/png"),
    ]
    if llm_request.contents:
        last = llm_request.contents[-1]
        last.parts = [*(last.parts or []), *parts]
    else:
        llm_request.contents = [types.Content(role="user", parts=parts)]
    return None


reviewer = Agent(
    name=REVIEWER_NAME,
    description="Reviews the light and dark render of an adapted plot once; answers with a Verdict.",
    model=make_model("reviewer"),
    generate_content_config=make_content_config("reviewer"),
    static_instruction=reviewer_instruction(),
    mode="single_turn",
    include_contents="none",
    output_schema=Verdict,
    before_model_callback=reviewer_before_model,
)
