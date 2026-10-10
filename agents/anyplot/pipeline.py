"""The plot pipeline: a code-bounded adapt, check, render, review and repair loop.

`run_pipeline` is the single node of the `plot_pipeline` workflow (`tools/session.py`).
It reads spec, library, dataset and bindings from server-set session state, never from
its input: `PipelineArgs` carries only `change_request`, `base` and `theme` (the one
theme to render; omitted, a change keeps the previous version's theme and a new plot
is light). It runs at most two attempts:

1. **adapt**: the library's adapter agent turns the working form into an `AdaptPlan`
   (`ctx.run_node`, under its own isolation scope so the root never reads its answer);
2. **check**: `edits.apply_plan` (which also keeps the protected theme statements
   intact), then the SECURITY validator (a finding rejects the code), the plan's
   literal budget (more than `MAX_NEW_LITERAL_CHARS` of new string literals rejects
   the code) and the ADAPTATION validator (a placeholder finding rejects the code;
   the other findings become defect lines but the code still renders);
3. **render**: `normalise`, the loader substitution (`to_run_form`), then the one
   theme the call asks for (`PipelineArgs.theme`, light by default) through the
   render backend, and the host gates (`render/gates.py`) on exactly that theme;
4. **review**: at most once, on the first render that passes the host gates on the
   exact canvas; the reviewer agent sees the rendered theme's PNG, so each of its
   image defects is filed under that theme, whatever theme the reviewer named;
5. **repair**: when attempt 1 left feedback (failed edits, validator findings, a
   failed render, gate defects, reviewer defects), attempt 2 gets it, with a full
   file allowed.

The other theme of a finished version is rendered later by the theme toggle
(`theme_render.py`) from the stored run form, without any model call.

Bounds: two adapter calls, one reviewer call, two renders of one theme. The budget
is checked before every model call, the soft deadline (`AGENT_SOFT_DEADLINE_S`)
before the second attempt (which needs `ADAPTER_P95_S` plus `RENDER_P95_S` left, so
the first attempt has the rest of the soft deadline) and for every render timeout;
the request deadline is `abort_signal` on the run. A render waits in the `run` lane of the render slot
(`render/serial.py`), ahead of every waiting theme toggle, so it waits for at most
the render in progress; its clamped timeout starts when it runs. The exported
`plot.py` names the rendered theme in its run line.

Every path that is not cancelled yields exactly one `Event(output=PlotResult)` as a
JSON dict. `ok` means the shipped render passed the host gates on the exact canvas
and the reviewer passed exactly that render; `needs_attention` ships a render with
residual defect lines (reviewer lines that no reviewed render fixed, adaptation
findings, a padded canvas, or no review because the budget or the deadline ran out);
`failed` names its reason; `not_ready` comes before any model call. An `ok` or
`needs_attention` result is stored as the session's next version before it is
yielded, and carries that number as `version`. Progress goes out
as content-free events with `custom_metadata={"anyplot_status": {"step", "attempt"}}`,
which the stream translator turns into `status` events and no model ever reads.

Every step also writes one content-free attribution line (`plugins/ledger.attribution`):
`pipeline_adapt` (the answer's outcome, `plan`, `schema`, `truncated` or
`full_code_refused`, the plan's shape, and the call's finish reason and output tokens),
`pipeline_check` (edit-apply failure count and kinds, blocking validator rule ids,
ADAPTATION rule ids), `pipeline_render` (render and wall time, the gate ids that
failed or reported), `pipeline_review` (the verdict, its defect ids and the call's
finish reason) and `pipeline_result` (status, reason, attempts, the `Stage` that ended
each attempt and the run, the shipped and the reviewed attempt, whether the shipped
render was padded or carries ADAPTATION or probe findings, and the exception class
behind reason `error`). The eval harness (`agents/evals/matrix.py`) reads them per
case; they never carry code, data, column names or model text. `PlotResult.reason`
keeps its public vocabulary; the stage is only in the attribution line.
"""

import json
import logging
import secrets
import time
from collections import Counter
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from google.adk import Context, Event
from google.adk.agents.llm.task._finish_task_tool import FINISH_TASK_SUCCESS_RESULT, FINISH_TASK_TOOL_NAME
from google.adk.workflow import node
from google.adk.workflow._errors import DynamicNodeFailError
from google.genai import types
from pydantic import ValidationError

from .briefs import profile_summary, spec_brief
from .code.edits import MAX_NEW_LITERAL_CHARS, apply_plan, new_literal_chars
from .code.export import export_code
from .code.regions import find_regions
from .code.validate import validate_adaptation, validate_security
from .data.bindings import check_bindings
from .data.store import StoredDataset
from .plugins.ledger import RequestLedger, attribution, budget_allows, ledger_for
from .policy import DATA_PREAMBLE, fence
from .render.contract import RendererUnavailable, RenderJob, Theme
from .render.gates import data_rows, evaluate
from .render.runtimes.python import PythonRuntime
from .schemas import (
    MAX_CHANGE_CHARS,
    MAX_CHANGES,
    MAX_FEEDBACK,
    MAX_LINE_CHARS,
    MAX_NOTE_CHARS,
    MAX_NOTES,
    MAX_RESIDUAL_DEFECTS,
    AdaptPlan,
    AdaptRequest,
    Binding,
    Defect,
    FailureReason,
    PipelineArgs,
    PlotResult,
    ReviewRequest,
    Verdict,
    artifact_names,
)
from .services import PADDED_REASON, CodeVersion, Services, ThemeRender, get_services
from .session_state import SessionView, read_session
from .settings import AgentSettings, get_settings
from .sub_agents.adapter import ADAPTERS, adapter_name
from .sub_agents.reviewer import REVIEWER_NAME, reviewer


logger = logging.getLogger(__name__)

STATUS_KEY = "anyplot_status"
ADAPTER_P95_S = 60.0
"""Seconds the second attempt's adapter call is budgeted at when checking the soft deadline.

Gemini's plan calls in spike X took about 62 s at the 95th percentile (Claude's whole
runs about 25 s)."""
RENDER_P95_S = 15.0
"""Seconds the second attempt's render is budgeted at when checking the soft deadline.

Spike X measured renders at 5.5 s at the 95th percentile and 10.2 s at most. With
`ADAPTER_P95_S` the second attempt needs 75 s, which leaves the first attempt 65 s
of the 140 s soft deadline; reserving the whole 60 s render timeout left it 35 s,
less than a typical Gemini plan call. The render's own timeout is still clamped to
what remains of the soft deadline."""
REVIEWER_P95_S = 30.0
"""Seconds the review is budgeted at; with less left of the soft deadline the render ships unreviewed."""
PADDED_LINE = "canvas padded after render ({theme})"
"""The residual line of a shipped render whose canvas was padded; it names the rendered theme."""
NOT_REVIEWED_LINE = "the plot was not reviewed ({why})"
BLOCKING_RULES = frozenset({"placeholder-count", "placeholder-use", "syntax", "size", "encoding"})
"""ADAPTATION findings that keep the code from running: without one placeholder there is no loader."""
ADAPTATION_IDS = {"rng": "DQ-03", "literal-data": "DQ-03", "palette-prefix": "VQ-07"}
"""The rubric id an ADAPTATION finding is reported under as a defect line."""
SCHEMA_MISS_LINE = "the previous answer did not match the plan schema; answer with edits, title and changes"

Stage = Literal[
    "budget",
    "deadline",
    "error",
    "adapter_schema",
    "adapter_truncated",
    "adapter_full_code",
    "edit_apply",
    "validator",
    "loader",
    "render",
    "gates",
    "not_rereviewed",
    "reviewer_unreadable",
    "reviewer_defects",
    "reviewer_ok",
]
"""Where an attempt, or the run, stopped (content-free, for the attribution log only).

`adapter_schema`: the answer failed the plan schema; `adapter_truncated`: it was cut
off at the output limit; `adapter_full_code`: a full file where none was allowed;
`edit_apply`: an edit did not apply; `validator`: a blocking validator finding or the
literal budget; `loader`: the code could not take the data loader; `render`: the host
gates R1 or R2 failed; `gates`: the render passed them but its canvas, probe or
ADAPTATION findings went to the repair (or the canvas was padded); `not_rereviewed`:
the repaired render shipped without a second review; `reviewer_*`: the review's
outcome; `budget`, `deadline`: a limit stopped the run before an attempt or before the
review; `error`: an exception."""
AdaptOutcome = Literal["schema", "truncated"]


@dataclass(frozen=True)
class AdaptMiss:
    """An adapter answer that yielded no plan: it failed the schema or was cut off at the output limit."""

    outcome: AdaptOutcome

    @property
    def stage(self) -> Stage:
        return "adapter_truncated" if self.outcome == "truncated" else "adapter_schema"


class SoftDeadline:
    """Seconds left of the pipeline's soft deadline."""

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._end = clock() + seconds

    def remaining(self) -> float:
        return max(0.0, self._end - self._clock())

    def allows(self, seconds: float) -> bool:
        return self.remaining() >= seconds

    def clamp(self, seconds: float) -> float:
        return max(1.0, min(seconds, self.remaining()))


@dataclass
class Candidate:
    """A render that passed R1 and R2, with what it would ship as."""

    working: str
    run_form: str
    pngs: dict[Theme, bytes]
    plan: AdaptPlan
    attempt: int
    padded: bool = False
    canvas_line: str | None = None
    adaptation_lines: list[str] = field(default_factory=list)
    advisory_lines: list[str] = field(default_factory=list)
    reviewed_ok: bool | None = None
    render_id: str | None = None
    adaptation_rules: list[str] = field(default_factory=list)
    """The ADAPTATION validator rule ids behind `adaptation_lines`, for the attribution log."""
    advisory_gates: list[str] = field(default_factory=list)
    """The advisory probe gate ids (`G3`, `G5`, `G7`, `G8`) behind `advisory_lines`, for the attribution log."""


@dataclass
class Run:
    """The pipeline's bookkeeping for one call."""

    view: SessionView
    dataset: StoredDataset
    theme: Theme = "light"
    attempts: int = 0
    best: Candidate | None = None
    padded: Candidate | None = None
    reviewed: bool = False
    review_lines: list[str] = field(default_factory=list)
    reason: FailureReason | None = None
    rendered: bool = False
    unreviewed_why: str | None = None
    error_type: str | None = None
    """The exception class that ended the run with reason `error` (content-free, for the attribution log)."""
    stage: Stage | None = None
    """What stopped the run: the last attempt's stage, or a limit before the next attempt."""
    stages: list[Stage] = field(default_factory=list)
    """The stage that ended each attempt, in order."""
    reviewed_attempt: int | None = None
    """The attempt whose render the reviewer was called on, read or not."""


def _end_attempt(run: Run, stage: Stage) -> None:
    run.stages.append(stage)
    run.stage = stage


def _call_fields(ledger: RequestLedger, agent: str) -> dict[str, Any]:
    """The content-free facts of `agent`'s latest model call for an attribution line."""
    call = ledger.last_calls.get(agent)
    if call is None:
        return {"finish_reason": None, "candidates": 0, "thoughts": 0}
    return {"finish_reason": call.finish_reason, "candidates": call.candidates, "thoughts": call.thoughts}


def _line(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"


def _status(step: str, attempt: int) -> Event:
    return Event(custom_metadata={STATUS_KEY: {"step": step, "attempt": attempt}})


def _result_event(result: PlotResult) -> Event:
    return Event(output=result.model_dump(mode="json"))


def load_inputs(ctx: Context, services: Services) -> tuple[SessionView | None, StoredDataset | None, str | None]:
    """The session view and dataset, or the `not_ready` reason (`no_dataset`, `incomplete_bindings`)."""
    view = read_session(ctx.state)
    if view is None:
        return None, None, "no_dataset"
    dataset = services.datasets.get(view.dataset_id, ctx.session.id) if view.dataset_id else None
    if dataset is None:
        return view, None, "no_dataset"
    check = check_bindings(view.bindings, view.snapshot.roles(), dataset.profile)
    if not check.complete:
        return view, dataset, "incomplete_bindings"
    return view, dataset, None


def render_adapt_request(request: AdaptRequest, view: SessionView) -> str:
    """The adapter's node input: the request as fenced text.

    Outside a fence stand only fixed headings, the validated library id and
    `allow_full`. The notes on the attempt go into one `<tool_notes>` block as JSON,
    the way the `plot_pipeline` result reaches the root: the readiness hints quote
    catalogue lines, the feedback quotes model-written code (failed edits, validator
    findings) or is model-written (reviewer lines), and the previous plan is
    model-written and can copy catalogue or dataset text.
    """
    lines = [
        f"Library: {view.library}",
        "",
        DATA_PREAMBLE,
        "Spec brief:",
        fence("spec_text", spec_brief(view)),
        fence("catalogue_code", request.code),
        "Dataset profile:",
        fence("user_data", request.profile.model_dump_json(exclude={"warnings"})),
        "Bindings and loader columns:",
        fence("user_data", _columns_json(request.bindings, request.loader_columns)),
    ]
    if request.change_request:
        lines += ["Change request:", fence("user_message", request.change_request)]
    notes: dict[str, Any] = {}
    if request.hints:
        notes["hints"] = request.hints
    if request.feedback:
        notes["feedback"] = request.feedback
    if request.previous_plan is not None:
        notes["previous_plan"] = request.previous_plan.model_dump(mode="json")
    if notes:
        lines += ["Notes on this attempt:", fence("tool_notes", json.dumps(notes, ensure_ascii=False))]
    lines.append(f"allow_full: {'true' if request.allow_full else 'false'}")
    return "\n".join(lines)


def render_review_request(request: ReviewRequest) -> str:
    """The reviewer's node input: the request as fenced text (the images are added by its callback).

    The gate notes are host-written, but they go into a `<tool_notes>` block too, so
    nothing but fixed headings stands outside a fence.
    """
    lines = [
        DATA_PREAMBLE,
        "Spec brief:",
        fence("spec_text", request.spec_brief),
        fence("plot_code", request.code),
        "Dataset summary:",
        fence("user_data", request.profile_summary),
        "Bindings:",
        fence("user_data", _columns_json(request.bindings)),
    ]
    if request.change_request:
        lines += ["Change request:", fence("user_message", request.change_request)]
    if request.gate_notes:
        lines += ["Gate notes:", fence("tool_notes", json.dumps(request.gate_notes, ensure_ascii=False))]
    return "\n".join(lines)


def _columns_json(bindings: list[Binding], loader_columns: list[str] | None = None) -> str:
    """Bindings (and the loader's columns) as JSON: column names are the user's headers, so they go in a fence."""
    payload: dict[str, Any] = {"bindings": [{"role": item.role, "column": item.column} for item in bindings]}
    if loader_columns is not None:
        payload["loader_columns"] = loader_columns
    return json.dumps(payload, ensure_ascii=False)


def _clip_feedback(lines: list[str]) -> list[str]:
    unique = list(dict.fromkeys(_line(line) for line in lines if line.strip()))
    return unique[:MAX_FEEDBACK]


@dataclass(frozen=True)
class CheckResult:
    """The validator verdict on a working form: its lines for the repair, and its rule ids for the attribution log."""

    may_render: bool
    blocking: list[str]
    defects: list[str]
    blocking_rules: list[str]
    adaptation_rules: list[str]


def _check(working: str, *, library: str, palette: list[str], base: str) -> CheckResult:
    """Validate a working form against its base: may it render, the blocking lines, the adaptation defect lines."""
    security = validate_security(working, library=library)
    adaptation = validate_adaptation(working, original_palette=palette)
    # Both profiles parse the code, so an unparseable file is one `syntax` finding, not two.
    blocking_findings = list(dict.fromkeys([*security, *(f for f in adaptation if f.rule in BLOCKING_RULES)]))
    blocking = [
        f"validator {f.rule}" + (f" (line {f.line})" if f.line else "") + f": {f.message}" for f in blocking_findings
    ]
    blocking_rules = [f.rule for f in blocking_findings]
    added = new_literal_chars(base, working)
    if added > MAX_NEW_LITERAL_CHARS:
        blocking_rules.append("literal-budget")
        blocking.append(
            f"validator literal-budget: the plan adds {added} characters of new string literals, "
            f"{added - MAX_NEW_LITERAL_CHARS} over the limit of {MAX_NEW_LITERAL_CHARS} → derive text and values "
            "from df instead of writing them out. Likely cause: data or long text written into the code."
        )
    soft = [f for f in adaptation if f.rule not in BLOCKING_RULES]
    defects = [
        f"{ADAPTATION_IDS.get(f.rule, 'SC-03')} (code): {f.message}"
        + (f" at line {f.line}" if f.line else "")
        + f" → derive it from df and the Imprint palette. Likely cause: the adaptation ({f.rule})."
        for f in soft
    ]
    return CheckResult(not blocking, blocking, defects, blocking_rules, [f.rule for f in soft])


def finish(run: Run) -> PlotResult:
    """The `PlotResult` of a finished run (see the module docstring for the status rules)."""
    shipped = run.best or run.padded
    if shipped is None:
        reason: FailureReason
        if run.reason in ("budget", "deadline", "error"):
            reason = run.reason
        else:
            reason = "render" if run.rendered else "validation"
        return PlotResult(status="failed", reason=reason, attempts=run.attempts)
    residual: list[str] = []
    if shipped.padded:
        residual.append(PADDED_LINE.format(theme=run.theme))
        if shipped.canvas_line:
            residual.append(shipped.canvas_line)
    residual += shipped.adaptation_lines
    if shipped.reviewed_ok is not True:
        residual += shipped.advisory_lines
        if run.review_lines:
            residual += run.review_lines
        elif not run.reviewed:
            residual.append(NOT_REVIEWED_LINE.format(why=run.unreviewed_why or "the repair round left defects"))
    residual = list(dict.fromkeys(_line(line) for line in residual))[:MAX_RESIDUAL_DEFECTS]
    changes = [change[:MAX_CHANGE_CHARS] for change in shipped.plan.changes][:MAX_CHANGES]
    return PlotResult(
        status="needs_attention" if residual else "ok",
        attempts=max(run.attempts, 1),
        artifacts=artifact_names([run.theme]),
        changes=changes,
        residual_defects=residual,
    )


def _store_version(ctx: Context, services: Services, run: Run, result: PlotResult) -> PlotResult:
    """Store a shipped result as the session's next version; the result comes back with its `version`.

    The number travels in the `plot` event, so a client addresses the artifact and theme
    toggle routes by the server's number instead of counting the events it received.
    """
    shipped = run.best or run.padded
    if shipped is None or result.status not in ("ok", "needs_attention"):
        return result
    session_id = ctx.session.id
    render_id = shipped.render_id or services.renders.put(session_id, shipped.pngs)
    snapshot = run.view.snapshot
    number = services.versions.next_number(session_id)
    result = PlotResult.model_validate({**result.model_dump(), "version": number})
    services.versions.add(
        session_id,
        CodeVersion(
            number=number,
            working=shipped.working,
            run_form=shipped.run_form,
            export=export_code(
                shipped.run_form,
                spec_id=snapshot.spec_id,
                library=run.view.library,
                library_version=snapshot.library_version,
                theme=run.theme,
            ),
            data_csv=run.dataset.csv,
            render_id=render_id,
            result=result,
            plan=shipped.plan,
            title=shipped.plan.title,
            library=run.view.library,
            theme=run.theme,
            themes={run.theme: ThemeRender("needs_attention", PADDED_REASON) if shipped.padded else ThemeRender("ok")},
        ),
    )
    return result


async def _adapt(ctx: Context, scope: str, request_text: str, library: str) -> AdaptPlan | AdaptMiss:
    """One adapter call: the plan, or the miss when the answer does not parse.

    The call's finish reason (`ledger.last_calls`, written by the Budget plugin) tells a
    cut-off answer from a schema miss; the entry is dropped first, so a call that
    raised before it finished never reads the previous attempt's facts.
    """
    agent = ADAPTERS.get(library)
    if agent is None:
        raise RendererUnavailable(f"no adapter for {library}")
    ledger = ledger_for(ctx.invocation_id)
    ledger.last_calls.pop(agent.name, None)
    try:
        raw = await ctx.run_node(agent, node_input=request_text, override_isolation_scope=scope)
        return AdaptPlan.model_validate(raw)
    except (ValidationError, DynamicNodeFailError) as exc:
        _reraise_unless_schema(exc)
        call = ledger.last_calls.get(agent.name)
        return AdaptMiss("truncated" if call is not None and call.finish_reason == "MAX_TOKENS" else "schema")


async def _review(ctx: Context, scope: str, request: ReviewRequest) -> Verdict | None:
    ledger_for(ctx.invocation_id).last_calls.pop(REVIEWER_NAME, None)
    try:
        raw = await ctx.run_node(reviewer, node_input=render_review_request(request), override_isolation_scope=scope)
        return Verdict.model_validate(raw)
    except (ValidationError, DynamicNodeFailError) as exc:
        _reraise_unless_schema(exc)
        return None


def _reraise_unless_schema(exc: Exception) -> None:
    """Backstop of `schema_guard`: a sub-agent answer that failed its schema inside ADK is not an error."""
    if isinstance(exc, DynamicNodeFailError) and not isinstance(exc.error, ValidationError | ValueError):
        raise exc
    logger.warning("sub-agent answer failed its schema: %s", type(exc).__name__)


def _default_theme(services: Services, session_id: str, library: str, base: str) -> Theme:
    """An omitted theme keeps the previous version's theme on a change; a new plot is light.

    The root may leave `theme` out of a refinement call, so a dark plot must not
    silently come back light.
    """
    if base == "previous":
        previous = services.versions.latest_rendered(session_id, library=library)
        if previous is not None:
            return previous.theme
    return "light"


@node(name="run_pipeline", rerun_on_resume=True)
async def run_pipeline(ctx: Context, node_input: PipelineArgs) -> AsyncGenerator[Event, None]:
    """Adapt, check, render, review and repair; yields status events and one PlotResult."""
    services = get_services()
    settings = get_settings()
    ledger = ledger_for(ctx.invocation_id)
    view, dataset, not_ready = load_inputs(ctx, services)
    if not_ready is not None or view is None or dataset is None:
        yield _result_event(
            PlotResult.not_ready("incomplete_bindings" if not_ready == "incomplete_bindings" else "no_dataset")
        )
        return
    ledger.pipeline_active = True
    theme = node_input.theme or _default_theme(services, ctx.session.id, view.library, node_input.base)
    run = Run(view=view, dataset=dataset, theme=theme)
    scope = f"pipeline-{secrets.token_hex(6)}"
    try:
        async for event in _attempts(ctx, services, settings, run, node_input, scope):
            yield event
    except Exception as exc:  # every failure ends in a PlotResult; the type is logged, never the message
        logger.warning("pipeline failed: %s", type(exc).__name__)
        run.reason = "error"
        run.error_type = type(exc).__name__
        run.unreviewed_why = run.unreviewed_why or "an internal error stopped the run"
        if len(run.stages) < run.attempts:
            run.stages.append("error")
        run.stage = "error"
    finally:
        ledger.pipeline_active = False
        ledger.adapter_allow_full = False
        ledger.review_render_id = None
    result = finish(run)
    try:
        result = _store_version(ctx, services, run, result)
    except Exception as exc:  # a result whose artifacts cannot be stored is not shippable
        logger.warning("storing the version failed: %s", type(exc).__name__)
        result = PlotResult(status="failed", reason="error", attempts=run.attempts)
        run.error_type = run.error_type or type(exc).__name__
        run.stage = "error"
    _attribute_result(ledger, run, result)
    yield close_scope(scope)
    yield _result_event(result)


def _attribute_result(ledger: RequestLedger, run: Run, result: PlotResult) -> None:
    """The content-free outcome line of one pipeline run: what the eval harness's pass and gate counts read.

    `padded`, `adaptation` (ADAPTATION rule ids) and `advisory` (probe gate ids) describe
    the shipped render; a failed run has none. `error` is the exception class behind
    reason `error` (for example `RendererUnavailable`, which the harness treats as an
    outage rather than a model failure), never its message. `stage` names what stopped
    the run and `stages` what ended each attempt (`Stage`); `shipped_attempt` and
    `reviewed_attempt` name the attempt whose render shipped and the one the reviewer
    was called on.
    """
    shipped = (run.best or run.padded) if result.status in ("ok", "needs_attention") else None
    attribution(
        "pipeline_result",
        ledger,
        status=result.status,
        reason=result.reason,
        attempts=result.attempts,
        stage=run.stage,
        stages=list(run.stages),
        shipped_attempt=shipped.attempt if shipped else None,
        reviewed_attempt=run.reviewed_attempt,
        theme=run.theme,
        reviewed=run.reviewed,
        padded=bool(shipped and shipped.padded),
        adaptation=list(shipped.adaptation_rules) if shipped else [],
        advisory=list(shipped.advisory_gates) if shipped else [],
        residual=len(result.residual_defects),
        error=run.error_type if result.reason == "error" else None,
    )


def close_scope(scope: str) -> Event:
    """The event that ends the sub-agents' isolation scope.

    ADK treats a scope that no `finish_task` response closed as a paused task
    (`runners._find_active_task_scope`): it would stamp the user's next message with
    the scope, hide it from the unscoped root and reuse this invocation id, so the
    next `plot_pipeline` call would replay this run's result. The event is scoped,
    so the root never reads it, and it is not authored by the root, so the stream
    translator drops it. An aborted run needs none: ADK closes the scopes of an
    aborted invocation itself.
    """
    response = types.FunctionResponse(name=FINISH_TASK_TOOL_NAME, response={"result": FINISH_TASK_SUCCESS_RESULT})
    return Event(
        isolation_scope=scope, content=types.Content(role="user", parts=[types.Part(function_response=response)])
    )


async def _attempts(
    ctx: Context, services: Services, settings: AgentSettings, run: Run, args: PipelineArgs, scope: str
) -> AsyncGenerator[Event, None]:
    view, dataset = run.view, run.dataset
    ledger = ledger_for(ctx.invocation_id)
    runtime = PythonRuntime(cpu_seconds=settings.render_timeout_s)
    deadline = SoftDeadline(settings.soft_deadline_s)
    previous = (
        services.versions.latest_rendered(ctx.session.id, library=view.library) if args.base == "previous" else None
    )
    working = previous.working if previous is not None else view.normalised
    regions = find_regions(view.normalised)
    palette = list(regions.imprint.entries) if regions.imprint else []
    hints = view.hints[:MAX_NOTES] if previous is None else []
    columns = [column.name for column in dataset.profile.columns]
    feedback: list[str] = []
    previous_plan: AdaptPlan | None = None
    rows = data_rows(dataset.csv)

    adapter = adapter_name(view.library)

    for attempt in (1, 2):
        if not budget_allows(ledger, services.usage, settings):
            run.reason, run.unreviewed_why, run.stage = "budget", "the usage limit was reached", "budget"
            return
        if attempt == 2 and not deadline.allows(ADAPTER_P95_S + RENDER_P95_S):
            run.reason, run.unreviewed_why, run.stage = "deadline", "the time limit was reached", "deadline"
            return
        run.attempts = attempt
        yield _status("adapting" if attempt == 1 else "repairing", attempt)
        request = AdaptRequest(
            code=working,
            profile=dataset.profile,
            bindings=view.bindings,
            loader_columns=columns,
            hints=hints,
            change_request=args.change_request,
            feedback=_clip_feedback(feedback),
            previous_plan=previous_plan,
            allow_full=attempt == 2,
        )
        ledger.adapter_allow_full = request.allow_full
        answer = await _adapt(ctx, scope, render_adapt_request(request, view), view.library)
        call = _call_fields(ledger, adapter)
        if isinstance(answer, AdaptMiss):
            attribution("pipeline_adapt", ledger, attempt=attempt, outcome=answer.outcome, **call)
            feedback, previous_plan = [SCHEMA_MISS_LINE], None
            _end_attempt(run, answer.stage)
            continue
        plan = answer
        if plan.full_code is not None and not request.allow_full:
            attribution("pipeline_adapt", ledger, attempt=attempt, outcome="full_code_refused", **call)
            feedback, previous_plan = ["full_code is allowed only on the second attempt; send edits instead"], None
            _end_attempt(run, "adapter_full_code")
            continue
        attribution(
            "pipeline_adapt",
            ledger,
            attempt=attempt,
            outcome="plan",
            edits=len(plan.edits),
            full_code=plan.full_code is not None,
            **call,
        )

        yield _status("checking", attempt)
        applied = apply_plan(working, plan)
        if applied.code is None:
            attribution(
                "pipeline_check",
                ledger,
                attempt=attempt,
                outcome="edits_failed",
                edit_failures=len(applied.failures),
                edit_failure_kinds=dict(sorted(Counter(applied.kinds).items())),
            )
            feedback, previous_plan = applied.failures, plan
            _end_attempt(run, "edit_apply")
            continue
        check = _check(applied.code, library=view.library, palette=palette, base=working)
        adaptation_lines = check.defects
        attribution(
            "pipeline_check",
            ledger,
            attempt=attempt,
            outcome="ok" if check.may_render else "rejected",
            edit_failures=0,
            validator=check.blocking_rules,
            adaptation=check.adaptation_rules,
        )
        if not check.may_render:
            feedback, previous_plan = check.blocking, plan
            _end_attempt(run, "validator")
            continue
        working, previous_plan = applied.code, None
        try:
            run_form = runtime.loader_block(
                runtime.normalise(working, view.library),
                columns=columns,
                dtypes=dict(dataset.column_dtypes),
                parse_dates=list(dataset.parse_dates),
            )
        except ValueError as exc:
            attribution("pipeline_check", ledger, attempt=attempt, outcome="loader_failed", edit_failures=0)
            feedback = [_line(f"the code could not take the data loader: {exc}")]
            _end_attempt(run, "loader")
            continue

        yield _status("rendering", attempt)
        job = RenderJob(
            job_id=secrets.token_hex(8),
            language=runtime.language,
            library=view.library,
            source=run_form,
            data_csv=dataset.csv,
            themes=(run.theme,),
            timeout_s=deadline.clamp(settings.render_timeout_s),
        )
        started = time.monotonic()
        rendered = await services.backend.render(job)
        render_s = time.monotonic() - started
        report = evaluate(rendered, themes=job.themes, library=view.library, rows=rows)
        attribution(
            "pipeline_render",
            ledger,
            attempt=attempt,
            theme=run.theme,
            render_s=round(render_s, 3),
            wall_s={theme: round(output.wall_s, 3) for theme, output in rendered.outputs.items()},
            passed=report.passed_host_gates,
            canvas_ok=report.canvas_ok,
            gates=report.failed_gates,
        )
        run.rendered = True
        if not report.passed_host_gates:
            feedback = [*report.blocking, *adaptation_lines]
            _end_attempt(run, "render")
            continue
        candidate = Candidate(
            working=working,
            run_form=run_form,
            pngs=report.shipped_pngs,
            plan=plan,
            attempt=attempt,
            padded=not report.canvas_ok,
            canvas_line=report.canvas_defects[0] if report.canvas_defects else None,
            adaptation_lines=adaptation_lines,
            advisory_lines=list(report.advisory),
            adaptation_rules=check.adaptation_rules,
            advisory_gates=[gate for gate in report.failed_gates if gate.startswith("G")],
        )
        if report.canvas_ok:
            run.best = candidate
        else:
            run.padded = candidate
        feedback = [*report.defects, *adaptation_lines]
        # Attempt 1 spends its feedback on the repair before any review; attempt 2 is reviewed
        # once if nothing was reviewed yet, with the advisory lines kept as gate notes.
        if not report.canvas_ok or (feedback and attempt == 1):
            _end_attempt(run, "gates")
            continue
        if run.reviewed:
            _end_attempt(run, "not_rereviewed")
            continue

        if not budget_allows(ledger, services.usage, settings):
            run.unreviewed_why = "the usage limit was reached"
            _end_attempt(run, "budget")
            return
        if not deadline.allows(REVIEWER_P95_S):
            run.unreviewed_why = "the time limit was reached"
            _end_attempt(run, "deadline")
            return
        yield _status("reviewing", attempt)
        candidate.render_id = services.renders.put(ctx.session.id, candidate.pngs)
        ledger.review_render_id = candidate.render_id
        run.reviewed_attempt = attempt
        verdict = await _review(
            ctx,
            scope,
            ReviewRequest(
                render_id=ledger.review_render_id,
                code=run_form,
                bindings=view.bindings,
                profile_summary=profile_summary(dataset.profile),
                spec_brief=spec_brief(view),
                change_request=args.change_request,
                gate_notes=[_note(line) for line in report.advisory][:MAX_NOTES],
            ),
        )
        review_call = _call_fields(ledger, REVIEWER_NAME)
        if verdict is None:
            attribution("pipeline_review", ledger, attempt=attempt, verdict="unreadable", **review_call)
            run.unreviewed_why = "the review answer could not be read"
            _end_attempt(run, "reviewer_unreadable")
            return
        attribution(
            "pipeline_review",
            ledger,
            attempt=attempt,
            verdict="ok" if verdict.ok else "defects",
            defects=[defect.id for defect in verdict.defects],
            **review_call,
        )
        run.reviewed = True
        candidate.reviewed_ok = verdict.ok
        if verdict.ok:
            _end_attempt(run, "reviewer_ok")
            return
        run.review_lines = [_on_theme(defect, run.theme).as_line() for defect in verdict.defects]
        feedback = list(run.review_lines)
        _end_attempt(run, "reviewer_defects")


def _on_theme(defect: Defect, theme: Theme) -> Defect:
    """The reviewer saw one theme: an image defect names it, even when the reviewer wrote `both` or the other one."""
    return defect if defect.theme in ("code", theme) else defect.model_copy(update={"theme": theme})


def _note(line: str) -> str:
    return line if len(line) <= MAX_NOTE_CHARS else line[: MAX_NOTE_CHARS - 1] + "…"
