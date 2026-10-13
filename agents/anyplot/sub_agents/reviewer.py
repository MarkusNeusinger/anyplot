"""The reviewer: a tool-less single-turn agent that judges a render in its one rendered theme.

The pipeline calls it on the first render that passes the host gates and once more on
the repaired render after a rejection (`pipeline.MAX_REVIEWS`); each call is fresh and
sees only that render.

Its static instruction is `policy.reviewer_instruction` (the reduced checklist, the
defect grammar, the catalogue's theme-readability check and the style guide). The
pipeline passes a fenced `ReviewRequest` as node input; the `before_model_callback`
keeps only that content and appends the PNG of every theme the render holds (a
pipeline run renders one, so the reviewer sees exactly the theme the user asked for)
as ordinary image parts, each after a fixed label naming its theme, loaded by
`render_id` (from the request ledger) out of the session's `RenderStore`. No image
ever travels through session state or a tool. The answer is bound to `Verdict`;
`schema_guard` mends an answer that misses only a formal rule (`schemas.repair_verdict`:
a text over its limit, more than five defects, an `ok` that contradicts the defects,
a defect whose id is outside the checklist, dropped when a usable defect remains or
the verdict passed the render) and blanks one that still fails, such as a rejection
that names only ids outside the checklist, which the pipeline reports as an unread
review.
"""

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from ..models import make_content_config, make_model
from ..plugins.ledger import ledger_for
from ..policy import catalogue_reviewer_instruction, reviewer_instruction
from ..render.contract import THEMES
from ..schemas import Verdict, repair_verdict
from ..scoring import ScoreAnswer
from ..services import get_services
from ..settings import get_settings
from .adapter import keep_last_content, schema_guard


REVIEWER_NAME = "reviewer"


class RenderMissing(RuntimeError):
    """The render to review is not in the session's render store."""


async def reviewer_before_model(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    keep_last_content(llm_request)
    render_id = ledger_for(callback_context.invocation_id).review_render_id
    stored = get_services().renders.get(render_id, callback_context.session.id) if render_id else None
    themes = [theme for theme in THEMES if stored is not None and theme in stored.pngs]
    if stored is None or not themes:
        raise RenderMissing("the render to review is not available")
    parts: list[types.Part] = []
    for theme in themes:
        parts += [
            types.Part(text=f"{theme.capitalize()} render (plot-{theme}.png):"),
            types.Part.from_bytes(data=stored.pngs[theme], mime_type="image/png"),
        ]
    if llm_request.contents:
        last = llm_request.contents[-1]
        last.parts = [*(last.parts or []), *parts]
    else:
        llm_request.contents = [types.Content(role="user", parts=parts)]
    return None


def make_reviewer() -> Agent:
    """The reviewer of the configured mode: the checklist (live) or the catalogue rubric (`AGENT_REVIEWER_MODE`).

    In `catalogue` mode the agent is the offline scorer's twin: the same rubric, answered as a
    `ScoreAnswer`, which the pipeline checks with `scoring.parse_answer` and turns into a verdict
    by code (`ScoreResult.passes`).
    """
    if get_settings().reviewer_mode == "catalogue":
        return Agent(
            name=REVIEWER_NAME,
            description="Scores the render of an adapted plot with the catalogue rubric; answers with a ScoreAnswer.",
            model=make_model("reviewer"),
            generate_content_config=make_content_config("reviewer"),
            static_instruction=catalogue_reviewer_instruction(),
            mode="single_turn",
            include_contents="none",
            output_schema=ScoreAnswer,
            before_model_callback=reviewer_before_model,
            after_model_callback=schema_guard(ScoreAnswer),
        )
    return Agent(
        name=REVIEWER_NAME,
        description="Reviews the render of an adapted plot once, in the theme it was rendered in; answers with a Verdict.",
        model=make_model("reviewer"),
        generate_content_config=make_content_config("reviewer"),
        static_instruction=reviewer_instruction(),
        mode="single_turn",
        include_contents="none",
        output_schema=Verdict,
        before_model_callback=reviewer_before_model,
        after_model_callback=schema_guard(Verdict, repair_verdict),
    )


reviewer = make_reviewer()
