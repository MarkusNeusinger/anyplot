"""The plot pipeline: a code-bounded adapt, check, render, review and repair loop.

`run_pipeline` is the single node of the `plot_pipeline` workflow (`tools/session.py`).
It reads spec, library, dataset and bindings from server-set session state, never from
its input (`PipelineArgs` carries only `change_request` and `base`), and runs at most
two attempts:

1. **adapt**: the library's adapter agent turns the working form into an `AdaptPlan`
   (`ctx.run_node`, under its own isolation scope so the root never reads its answer);
2. **check**: `edits.apply_plan`, then the SECURITY validator (a finding rejects the
   code) and the ADAPTATION validator (a placeholder finding rejects the code; the
   other findings become defect lines but the code still renders);
3. **render**: `normalise`, the loader substitution (`to_run_form`), then both themes
   through the render backend, and the host gates (`render/gates.py`);
4. **review**: at most once, on the first render that passes the host gates on the
   exact canvas; the reviewer agent sees both PNGs;
5. **repair**: when attempt 1 left feedback (failed edits, validator findings, a
   failed render, gate defects, reviewer defects), attempt 2 gets it, with a full
   file allowed.

Bounds: two adapter calls, one reviewer call, two renders of two themes. The budget
is checked before every model call, the soft deadline (`AGENT_SOFT_DEADLINE_S`)
before the second attempt and for every render timeout; the request deadline is
`abort_signal` on the run.

Every path that is not cancelled yields exactly one `Event(output=PlotResult)` as a
JSON dict. `ok` means the shipped render passed the host gates on the exact canvas
and the reviewer passed exactly that render; `needs_attention` ships a render with
residual defect lines (reviewer lines that no reviewed render fixed, adaptation
findings, a padded canvas, or no review because the budget or the deadline ran out);
`failed` names its reason; `not_ready` comes before any model call. Progress goes out
as content-free events with `custom_metadata={"anyplot_status": {"step", "attempt"}}`,
which the stream translator turns into `status` events and no model ever reads.
"""

import logging
import secrets
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field

from google.adk import Context, Event
from google.adk.workflow import node
from pydantic import ValidationError

from .briefs import profile_summary, spec_brief
from .code.edits import apply_plan
from .code.export import export_code
from .code.regions import find_regions
from .code.validate import validate_adaptation, validate_security
from .data.bindings import check_bindings
from .data.store import StoredDataset
from .plugins.ledger import budget_allows, ledger_for
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
    ArtifactName,
    FailureReason,
    PipelineArgs,
    PlotResult,
    ReviewRequest,
    Verdict,
)
from .services import CodeVersion, Services, get_services
from .session_state import SessionView, read_session
from .settings import AgentSettings, get_settings
from .sub_agents.adapter import ADAPTERS
from .sub_agents.reviewer import reviewer


logger = logging.getLogger(__name__)

STATUS_KEY = "anyplot_status"
ADAPTER_P95_S = 45.0
"""Seconds the second attempt's adapter call is budgeted at when checking the soft deadline."""
ARTIFACTS: list[ArtifactName] = ["plot-light.png", "plot-dark.png", "plot.py", "data.csv"]
PADDED_LINE = "canvas padded after render"
NOT_REVIEWED_LINE = "the plot was not reviewed ({why})"
BLOCKING_RULES = frozenset({"placeholder-count", "placeholder-use", "syntax", "size", "encoding"})
"""ADAPTATION findings that keep the code from running: without one placeholder there is no loader."""
ADAPTATION_IDS = {"rng": "DQ-03", "literal-data": "DQ-03", "palette-prefix": "VQ-07"}
"""The rubric id an ADAPTATION finding is reported under as a defect line."""


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


@dataclass
class Run:
    """The pipeline's bookkeeping for one call."""

    view: SessionView
    dataset: StoredDataset
    attempts: int = 0
    best: Candidate | None = None
    padded: Candidate | None = None
    reviewed: bool = False
    review_lines: list[str] = field(default_factory=list)
    reason: FailureReason | None = None
    rendered: bool = False
    unreviewed_why: str | None = None


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
    """The adapter's node input: the request as fenced text."""
    lines = [
        f"Library: {view.library}",
        spec_brief(view),
        "",
        DATA_PREAMBLE,
        fence("catalogue_code", request.code),
        fence("user_data", request.profile.model_dump_json(exclude={"warnings"})),
        "",
        "Bindings (role -> column):",
        *[f"- {binding.role} -> {_quoted(binding.column)}" for binding in request.bindings],
        "Loader columns: " + ", ".join(_quoted(column) for column in request.loader_columns),
    ]
    if request.hints:
        lines += ["Hints:", *[f"- {hint}" for hint in request.hints]]
    if request.change_request:
        lines += ["Change request:", fence("user_message", request.change_request)]
    if request.feedback:
        lines += ["Feedback on the previous attempt:", *[f"- {item}" for item in request.feedback]]
    if request.previous_plan is not None:
        lines += ["Previous plan (failed validation):", request.previous_plan.model_dump_json()]
    lines.append(f"allow_full: {'true' if request.allow_full else 'false'}")
    return "\n".join(lines)


def render_review_request(request: ReviewRequest) -> str:
    """The reviewer's node input: the request as fenced text (the images are added by its callback)."""
    lines = [
        request.spec_brief,
        "",
        DATA_PREAMBLE,
        fence("plot_code", request.code),
        fence("user_data", request.profile_summary),
        "Bindings (role -> column):",
        *[f"- {binding.role} -> {_quoted(binding.column)}" for binding in request.bindings],
    ]
    if request.change_request:
        lines += ["Change request:", fence("user_message", request.change_request)]
    if request.gate_notes:
        lines += ["Gate notes:", *[f"- {note}" for note in request.gate_notes]]
    return "\n".join(lines)


def _quoted(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _clip_feedback(lines: list[str]) -> list[str]:
    unique = list(dict.fromkeys(_line(line) for line in lines if line.strip()))
    return unique[:MAX_FEEDBACK]


def _check(working: str, *, library: str, palette: list[str]) -> tuple[bool, list[str], list[str]]:
    """Validate a working form: (may render, blocking lines, adaptation defect lines)."""
    security = validate_security(working, library=library)
    adaptation = validate_adaptation(working, original_palette=palette)
    blocking = [f"validator {f.rule}" + (f" (line {f.line})" if f.line else "") + f": {f.message}" for f in security]
    blocking += [
        f"validator {f.rule}" + (f" (line {f.line})" if f.line else "") + f": {f.message}"
        for f in adaptation
        if f.rule in BLOCKING_RULES
    ]
    defects = [
        f"{ADAPTATION_IDS.get(f.rule, 'SC-03')} (code): {f.message}"
        + (f" at line {f.line}" if f.line else "")
        + f" → derive it from df and the Imprint palette. Likely cause: the adaptation ({f.rule})."
        for f in adaptation
        if f.rule not in BLOCKING_RULES
    ]
    return not blocking, blocking, defects


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
        residual.append(PADDED_LINE)
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
        artifacts=list(ARTIFACTS),
        changes=changes,
        residual_defects=residual,
    )


def _store_version(ctx: Context, services: Services, run: Run, result: PlotResult) -> None:
    shipped = run.best or run.padded
    if shipped is None or result.status not in ("ok", "needs_attention"):
        return
    session_id = ctx.session.id
    render_id = shipped.render_id or services.renders.put(session_id, shipped.pngs)
    snapshot = run.view.snapshot
    services.versions.add(
        session_id,
        CodeVersion(
            number=services.versions.next_number(session_id),
            working=shipped.working,
            run_form=shipped.run_form,
            export=export_code(
                shipped.run_form,
                spec_id=snapshot.spec_id,
                library=run.view.library,
                library_version=snapshot.library_version,
            ),
            data_csv=run.dataset.csv,
            render_id=render_id,
            result=result,
            plan=shipped.plan,
            title=shipped.plan.title,
        ),
    )


async def _adapt(ctx: Context, scope: str, request_text: str, library: str) -> AdaptPlan | str:
    """One adapter call: the plan, or a feedback line when the answer does not parse."""
    agent = ADAPTERS.get(library)
    if agent is None:
        raise RendererUnavailable(f"no adapter for {library}")
    raw = await ctx.run_node(agent, node_input=request_text, override_isolation_scope=scope)
    try:
        return AdaptPlan.model_validate(raw)
    except ValidationError:
        return "the previous answer did not match the plan schema; answer with edits, title and changes"


async def _review(ctx: Context, scope: str, request: ReviewRequest) -> Verdict | None:
    raw = await ctx.run_node(reviewer, node_input=render_review_request(request), override_isolation_scope=scope)
    try:
        return Verdict.model_validate(raw)
    except ValidationError:
        return None


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
    run = Run(view=view, dataset=dataset)
    try:
        async for event in _attempts(ctx, services, settings, run, node_input):
            yield event
    except Exception as exc:  # every failure ends in a PlotResult; the type is logged, never the message
        logger.warning("pipeline failed: %s", type(exc).__name__)
        run.reason = "error"
    finally:
        ledger.pipeline_active = False
        ledger.adapter_allow_full = False
        ledger.review_render_id = None
    result = finish(run)
    _store_version(ctx, services, run, result)
    yield _result_event(result)


async def _attempts(
    ctx: Context, services: Services, settings: AgentSettings, run: Run, args: PipelineArgs
) -> AsyncGenerator[Event, None]:
    view, dataset = run.view, run.dataset
    ledger = ledger_for(ctx.invocation_id)
    runtime = PythonRuntime(cpu_seconds=settings.render_timeout_s)
    deadline = SoftDeadline(settings.soft_deadline_s)
    scope = f"pipeline-{secrets.token_hex(6)}"
    previous = services.versions.latest_rendered(ctx.session.id) if args.base == "previous" else None
    working = previous.working if previous is not None else view.normalised
    regions = find_regions(view.normalised)
    palette = list(regions.imprint.entries) if regions.imprint else []
    hints = view.hints[:MAX_NOTES] if previous is None else []
    columns = [column.name for column in dataset.profile.columns]
    feedback: list[str] = []
    previous_plan: AdaptPlan | None = None
    rows = data_rows(dataset.csv)

    for attempt in (1, 2):
        if not budget_allows(ledger, services.usage, settings):
            run.reason, run.unreviewed_why = "budget", "the usage limit was reached"
            return
        if attempt == 2 and not deadline.allows(ADAPTER_P95_S + settings.render_timeout_s):
            run.reason, run.unreviewed_why = "deadline", "the time limit was reached"
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
        if isinstance(answer, str):
            feedback, previous_plan = [answer], None
            continue
        plan = answer
        if plan.full_code is not None and not request.allow_full:
            feedback, previous_plan = ["full_code is allowed only on the second attempt; send edits instead"], None
            continue

        yield _status("checking", attempt)
        applied = apply_plan(working, plan)
        if applied.code is None:
            feedback, previous_plan = applied.failures, plan
            continue
        may_render, blocking, adaptation_lines = _check(applied.code, library=view.library, palette=palette)
        if not may_render:
            feedback, previous_plan = blocking, plan
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
            feedback = [_line(f"the code could not take the data loader: {exc}")]
            continue

        yield _status("rendering", attempt)
        job = RenderJob(
            job_id=secrets.token_hex(8),
            language=runtime.language,
            library=view.library,
            source=run_form,
            data_csv=dataset.csv,
            timeout_s=deadline.clamp(settings.render_timeout_s),
        )
        report = evaluate(await services.backend.render(job), library=view.library, rows=rows)
        run.rendered = True
        if not report.passed_host_gates:
            feedback = [*report.blocking, *adaptation_lines]
            continue
        candidate = Candidate(
            working=working,
            run_form=run_form,
            pngs=report.pngs if report.canvas_ok else report.padded_pngs,
            plan=plan,
            attempt=attempt,
            padded=not report.canvas_ok,
            canvas_line=report.canvas_defects[0] if report.canvas_defects else None,
            adaptation_lines=adaptation_lines,
            advisory_lines=list(report.advisory),
        )
        if report.canvas_ok:
            run.best = candidate
        else:
            run.padded = candidate
        feedback = [*report.defects, *adaptation_lines]
        # Attempt 1 spends its feedback on the repair before any review; attempt 2 is reviewed
        # once if nothing was reviewed yet, with the advisory lines kept as gate notes.
        if run.reviewed or not report.canvas_ok or (feedback and attempt == 1):
            continue

        if not budget_allows(ledger, services.usage, settings):
            run.unreviewed_why = "the usage limit was reached"
            return
        yield _status("reviewing", attempt)
        candidate.render_id = services.renders.put(ctx.session.id, candidate.pngs)
        ledger.review_render_id = candidate.render_id
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
        run.reviewed = True
        if verdict is None:
            run.review_lines = ["the review answer could not be read"]
            return
        candidate.reviewed_ok = verdict.ok
        if verdict.ok:
            return
        run.review_lines = [defect.as_line() for defect in verdict.defects]
        feedback = list(run.review_lines)


def _note(line: str) -> str:
    return line if len(line) <= MAX_NOTE_CHARS else line[: MAX_NOTE_CHARS - 1] + "…"
