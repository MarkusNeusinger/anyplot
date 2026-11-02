"""The plot pipeline: a code-bounded adapt, check, render, review and repair loop.

`run_pipeline` is the single node of the `plot_pipeline` workflow (`tools/session.py`).
It reads spec, library, dataset and bindings from server-set session state, never from
its input: `PipelineArgs` carries only `change_request`, `base` and `theme` (the one
theme to render; omitted, the theme `run_theme` picks, the site's unless the user
asked for one). The plot language (`session_state.plot_language`: the user's request for
the plot's text, else the language of the session's latest plot, else the session
language) is read once per run, so the adapter, which writes the plot's own text in it,
and the reviewer, which judges that text against it, share one value; each prompt gets it
fenced as `<plot_language>`. It runs at most
`AGENT_MAX_ATTEMPTS` attempts, two by default (the first and one repair round; the
eval harness may set one or three):

1. **adapt**: the library's adapter agent turns the working form into an `AdaptPlan`
   (`ctx.run_node`, under its own isolation scope so the root never reads its answer);
2. **check**: `edits.apply_plan` (which also keeps the protected theme statements
   intact; an answer that failed its check gets one retry in its round, and a plan
   whose only failure is drift of those statements, once that retry is spent, has
   them restored by `edits.restore_protected` and goes on, owner decision of
   2026-10-16), then the SECURITY validator (a finding rejects the code), the plan's
   literal budget (more than `MAX_NEW_LITERAL_CHARS` of new string literals, or
   `MAX_CHANGE_LITERAL_CHARS` on a change of a previous version, or more than
   `MAX_NEW_LITERAL_CHARS` against the catalogue code over all versions, rejects the
   code; dataset headers and cells are free) and the ADAPTATION validator (a finding
   of the runtime's `blocking_rules` rejects the code: a placeholder rule in every
   language, and in R and Julia a dataset package too; the other findings become defect lines
   with the runtime's targets but the code still renders); a change whose base version was written in another
   language than the plot language (`language_changed`, after the user asked for another one) rewrites every title,
   label and annotation, so its budget grows by `REWRITE_LITERAL_FACTOR` times the
   literal text the plan replaces, up to `MAX_NEW_LITERAL_CHARS`;
3. **render**: `normalise`, the loader substitution (the runtime's `loader_block`, typed
   from the parser's dtypes and the column kinds), then the one
   theme of the run (`run_theme`: the one the user asked for, else the site's) through the
   render backend, and the host gates (`render/gates.py`) on exactly that theme; a failed
   render's summary is the runtime's error grammar over the code that ran
   (`RuntimeAdapter.error_summary` with the run form, so Julia's names the working form's
   line past its 15-line loader);
4. **review**: on the first render that passes the host gates on the exact canvas
   (with `AGENT_GATE_REPAIR=first`: and either left no feedback or came from the last
   allowed attempt), and once more on the repaired render after a rejection
   (`MAX_REVIEWS` reviewer calls in all, every round with `AGENT_SHIP_BEST`); the
   reviewer agent sees the rendered theme's PNG, so each of its image defects is
   filed under that theme, whatever theme the reviewer named. A render on a runtime
   whose reviewer checks the requested texts (`RuntimeAdapter.review_texts`: every library
   but matplotlib, seaborn and plotnine, whose probes read their texts for the reply only)
   hands the review the requested texts, and each one it cannot find in the image is a miss
   like the probe's (`grounding.reviewed_misses`), in the same call;
5. **repair**: when an attempt left feedback (an answer that missed the schema or was
   cut off at the output limit, each with its own line, failed edits, validator
   findings, a failed render, a missed canvas, reviewer defects, and measured
   findings that the review left in the render) and another attempt is allowed, the
   next attempt gets it, with a full file allowed from attempt 2 on.

The other theme of a finished version is rendered later by the theme toggle
(`theme_render.py`) from the stored run form, without any model call.

Bounds: one adapter call and one render of one theme per attempt (two each by
default), `MAX_REVIEWS` reviewer calls. The budget is checked before every model call
(before a review with `REVIEW_RESERVE_TOKENS` left for it and the root's closing reply),
the soft deadline (`AGENT_SOFT_DEADLINE_S`) before every attempt after the first (each
needs `ADAPTER_P95_S` plus the runtime's `render_p95_s` left, so the first attempt has the rest of
the soft deadline) and for every render timeout;
the request deadline is `abort_signal` on the run. A render waits in the `run` lane of the render slot
(`render/serial.py`), ahead of every waiting theme toggle, so it waits only for the renders
of the other runs in flight (up to five since 2026-11-01, their starts at least 10 s apart);
its clamped timeout starts when it runs. The gates run in a worker thread, off the
event loop the other runs in flight share. The exported
code (`plot.py`, `plot.R`, `plot.jl`) names the rendered theme in its run line.

Every path that is not cancelled yields exactly one `Event(output=PlotResult)` as a
JSON dict. `ok` means the shipped render passed the host gates on the exact canvas,
has no measured finding left (no advisory gate line, no ADAPTATION finding), and the
reviewer passed exactly that render (in `catalogue` mode: at or above the ship bar,
`AGENT_STATUS_BAR` and `AGENT_STATUS_SCORE`); `needs_attention` ships a render with
residual defect lines (reviewer lines that no reviewed render fixed, adaptation
findings, every advisory gate line of the shipped render, such as clipped or
overlapping text, which no review score erases, a padded canvas, or no review because
the budget or the deadline ran out);
`failed` names its reason; `not_ready` comes before any model call and before the run
queue. A ready run first takes the turn's run-queue slot (`ledger.run_slot`, set by the
`/messages` route), so only a turn that renders waits in the queue; the soft deadline
starts after that wait. An `ok` or
`needs_attention` result is stored as the session's next version before it is
yielded, and carries that number as `version`. Its `changes` are the notes of every
adapter call up to the shipped render whose plan changed the code (`note_changes`), so
a proofread that changed nothing never replaces them. The runtime's `loader_notes` come
first among them: R reads integers beyond ±2^53 as the nearest double and Julia keeps a
timestamp to the millisecond, and the note names each column with its count (owner rule
of 2026-10-15, no silent loss). Owner
decision of 2026-10-29: the note goes into "what changed", not into the residual notes,
so it leaves the status as it is (`ok` stays `ok`). Each version keeps the change
requests it carries out (`CodeVersion.requests`); a change of it hands them to every
adapter call (adaptation, retry, proofread, repair) and to the reviewer as
`user_requests`, the user's standing decisions, which the prompts say to keep and never
to report as defects unless the current change request revisits them. Progress goes out
as content-free events with `custom_metadata={"anyplot_status": {"step", "attempt"}}`,
which the stream translator turns into `status` events and no model ever reads.

Every step also writes one content-free attribution line (`plugins/ledger.attribution`):
`pipeline_adapt` (the answer's outcome, `plan`, `schema`, `truncated` or
`full_code_refused`, the plan's shape, and the call's finish reason and output tokens),
`pipeline_check` (edit-apply failure count and kinds, outcome `drift_restored` with
the restored drift kinds, how many edits a tolerant matching tier applied, blocking
validator rule ids, the labels of banned imports (`validate.module_label`: a word of a closed vocabulary, or `?`), ADAPTATION rule
ids), `pipeline_render` (render, render-slot wait and wall time, the gate ids that
failed or reported, and the class a failed probe names, `grounding.probe_error`),
`pipeline_review` (the verdict, its defect ids and the call's
finish reason) and `pipeline_result` (status, reason, attempts, the `Stage` that ended
each attempt and the run, the shipped and the last reviewed attempt, the number of
reviewer calls, whether the shipped
render was padded or carries ADAPTATION or probe findings, the roles of its drawn texts
and whether its library reports them, and the exception class behind reason `error`
or `busy`, the latter a model quota or overload still refused after the SDK's retries,
`models.model_busy`; the innermost class, never ADK's wrapper). The eval harness (`agents/evals/matrix.py`) reads them per
case; they never carry code, data, column names or model text. `PlotResult.reason`
keeps its public vocabulary; the stage is only in the attribution line.
"""

import asyncio
import csv
import functools
import io
import json
import logging
import math
import secrets
import time
from collections import Counter
from collections.abc import AsyncGenerator, Callable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal, get_args

from google.adk import Context, Event
from google.adk.agents.llm.task._finish_task_tool import FINISH_TASK_SUCCESS_RESULT, FINISH_TASK_TOOL_NAME
from google.adk.workflow import node
from google.adk.workflow._errors import DynamicNodeFailError
from google.genai import types
from pydantic import ValidationError

from core.defects import DEFECT_RE, KNOWN_IDS

from . import telemetry
from .briefs import adapter_profile, profile_summary, spec_brief
from .code.edits import MAX_CHANGE_LITERAL_CHARS, MAX_NEW_LITERAL_CHARS, REWRITE_LITERAL_FACTOR
from .data.bindings import check_bindings
from .data.kinds import ColumnKinds, read_kinds
from .data.store import StoredDataset
from .dataset_context import dataset_context, file_name_for_models
from .grounding import (
    EXPECT_LINE_ID,
    UNVERIFIED_LINE,
    drawn_texts,
    expected_misses,
    plot_texts,
    probe_error,
    reviewed_misses,
)
from .language import DEFAULT_LANGUAGE, same_language
from .models import error_chain, model_busy
from .plugins.ledger import RequestLedger, attribution, budget_allows, ledger_for
from .policy import DATA_PREAMBLE, adapter_instruction, fence, prompt_hash
from .render.contract import RendererUnavailable, RenderJob, RuntimeAdapter, Theme
from .render.gates import data_rows, evaluate
from .render.runtimes import runtime_for
from .schemas import (
    EXPECTED_TEXT,
    MAX_CHANGE_CHARS,
    MAX_CHANGE_REQUEST_CHARS,
    MAX_CHANGES,
    MAX_EXPECTED_TEXTS,
    MAX_FEEDBACK,
    MAX_LINE_CHARS,
    MAX_NOTE_CHARS,
    MAX_NOTES,
    MAX_RESIDUAL_DEFECTS,
    MAX_ROUND_DEFECTS,
    MAX_USER_REQUESTS,
    MAX_USER_REQUESTS_CHARS,
    AdaptPlan,
    AdaptRequest,
    Binding,
    Defect,
    FailureReason,
    NotReadyReason,
    PipelineArgs,
    PlotResult,
    PlotShows,
    ReviewRequest,
    ReviewState,
    Round,
    RoundOutcome,
    RoundStep,
    ShownGroup,
    Verdict,
    artifact_names,
)
from .scoring import ScoreAnswer, ScoreError, mend_answer, parse_answer
from .services import PADDED_REASON, CodeVersion, Services, ThemeRender, get_services
from .session_state import (
    BINDINGS,
    PENDING_BINDINGS,
    PENDING_EXPECTED_TEXTS,
    PENDING_REQUEST,
    SessionView,
    plot_language,
    read_session,
)
from .settings import AgentSettings, get_settings
from .sub_agents.adapter import ADAPTERS, adapter_name
from .sub_agents.reviewer import REVIEWER_MODES, REVIEWER_NAME, use_reviewer_mode


logger = logging.getLogger(__name__)

STATUS_KEY = "anyplot_status"
SELF_REVIEW_LINE = (
    "Self-review: the attached image is the render of the current code with the user's data. Before it goes "
    "to the reviewer, check it against each technical criterion of the rubric in your instructions (VQ, SC, DQ) "
    "and against the spec: fix what falls short. When the notes also name the previous round's findings, check "
    "that your changes fixed them in the image. What the change request and the earlier requests set stays as "
    "the user asked, whatever the rubric says. If nothing needs fixing, answer with an empty edit list. Your "
    "`changes` list only what this answer fixes, never again what the code already did: the user already has "
    "the notes of the first answer."
)
"""The feedback of the self-review attempt (`AGENT_SELF_REVIEW`); the render itself is attached by the adapter's callback."""
MEASURED_LINE = (
    "Measured: the server's checks found the lines below in this render's code or image; fix each of them, "
    "or the plot goes to a repair round."
)
"""Heads the measured findings the self-review gets with `AGENT_GATE_REPAIR=review`."""
SELF_REVIEW_HIGHLIGHT_LINE = (
    "Design: most plots need no highlight, and none is the default. Add one only when the image shows something "
    "a reader would likely miss or that changes how the data reads (a clear outlier, a break or turning point, "
    "one group far apart from the rest), and pointing it out plainly makes the plot more useful. An ordinary "
    "maximum or the last value is not enough on its own. Then add exactly one: a short annotation or one "
    "emphasised mark, position and text computed from df, existing colors, inside the canvas, not covering data, "
    "and name it in `changes`."
)
"""The design part of the self-review with `AGENT_HIGHLIGHTS=data`: an explicit task, not a permission (2026-10-13:
with the permission alone the adapter added a highlight to 2 of 20 plots)."""
ADAPTER_P95_S = 60.0
"""Seconds a repair attempt's adapter call is budgeted at when checking the soft deadline.

Gemini's plan calls in spike X took about 62 s at the 95th percentile (Claude's whole
runs about 25 s)."""
RENDER_P95_S = 15.0
"""Seconds a Python repair attempt's render is budgeted at when checking the soft deadline: the Python row's
`render_p95_s` of the renderer's command table (`agents/renderer/commands.py`), which the runtime carries
(`RuntimeAdapter.render_p95_s`); the Julia runtime reserves more.

Spike X measured renders at 5.5 s at the 95th percentile and 10.2 s at most. With
`ADAPTER_P95_S` a repair attempt needs 75 s, which leaves the first attempt 65 s
of the 140 s soft deadline; reserving the whole 60 s render timeout left it 35 s,
less than a typical Gemini plan call. The render's own timeout is still clamped to
what remains of the soft deadline."""
REVIEWER_P95_S = 30.0
"""Seconds the review is budgeted at; with less left of the soft deadline the render ships unreviewed."""
MAX_REVIEWS = 2
"""Reviewer calls per run: the first review, and one more of the repaired render after a rejection.

Without the second one a repaired render could never end `ok`: in the rerun of spike X
on main, 39 of 244 runs shipped a repaired render unreviewed (`not_rereviewed`)."""
REVIEW_RESERVE_TOKENS = 60_000
"""Cost-weighted tokens a review needs left of every token budget, for itself and the root's closing reply.

60,000 since 2026-10-13 (35,000 before): the catalogue reviewer reads the rubric, about 26,000
tokens that a cold cache writes at weight 1.25, and answers with about 2,500 at weight 5. The
old checklist's numbers follow.

In the rerun of spike X (Claude Haiku 5.5) a review on a cold prompt cache weighed at
most 28,099 and the closing reply at most 5,022. With less left, the render ships
unreviewed. This is the measured need, not an upper bound: the reviewer's and the root's
output caps alone could cost 2 x 4,096 x 5 weighted tokens, so the guarantee that a
shipped plot is never answered with the `budget` refusal is structural instead: once
`ledger.plot_shipped` is set, the Budget plugin exempts the root's next call, once and
without tools, so it can only be the closing reply."""
PADDED_LINE = "canvas padded after render ({theme})"
"""The residual line of a shipped render whose canvas was padded; it names the rendered theme."""
NOT_REVIEWED_LINE = "the plot was not reviewed ({why})"
LOW_SCORE_LINE = "the review scored the plot {score} of 100, below the ship score of {bar}"
"""The residual line of a render that meets the ship bar but not `AGENT_STATUS_SCORE`."""
VISIBLE_DEFECT_IDS = frozenset({"AR-09", "VQ-01", "VQ-02", "VQ-05"})
"""Review ids of a defect the user sees at a glance: text cut off at the canvas edge (AR-09), unreadable text
(VQ-01, owner decision of 2026-10-16), overlapping text or marks (VQ-02), and a layout that cuts or crams the plot
(VQ-05). The reviewer's twins of the measured gate lines G3 and G7, which no review score waives either
(`AGENT_GATE_REPAIR=review`).

A review that names one of them sends the round to the repair even when its points pass the review bar
(`AGENT_REVIEW_BAR`, 0.95 of the technical points: two lost points pass): live test round 7 of 2026-10-16 shipped
a heatmap after the first try with its axis label at the right edge and a crammed colorbar, and the reply listed
them. Such a render is not clean for `AGENT_SHIP_BEST` (`_clean`), so a clean repair a few points lower ships
over it, and a render that ships with such lines carries them as notes (`needs_attention`) at any score, like a
measured finding (review of #12204: the forced repair had been dropped silently for a 96 that clipped a label)."""
ADAPTATION_IDS = {"rng": "DQ-03", "literal-data": "DQ-03", "palette-prefix": "VQ-07"}
"""The rubric id an ADAPTATION finding is reported under as a defect line.

Which findings reject the code (`RuntimeAdapter.blocking_rules`) and the target of each soft
one (`RuntimeAdapter.adaptation_targets`) are the runtime's since 2026-10-29: the Python
values moved unchanged to `runtimes/python.py`, and R adds `dataset-package` to the blocking
set and writes its targets in R."""
DEFAULT_ADAPTATION_TARGET = "derive it from df"
"""The target of a soft ADAPTATION finding the runtime gives none."""
# Feedback only ever reaches a repair attempt (attempt 2 or later), and each allows a full file, so the lines say so.
SCHEMA_MISS_LINE = (
    "the previous answer did not match the plan schema → answer with one JSON object: edits or full_code "
    "(this attempt allows a full file), title and changes, each within its limits"
)
CUT_OFF_LINE = (
    "the previous answer was cut off at the output limit before the plan was complete → send a shorter plan: "
    "fewer and shorter edits, or full_code when the edits would be long (this attempt allows a full file). "
    "Likely cause: a long plan, or long reasoning before it."
)
FULL_CODE_REFUSED_LINE = (
    "the previous answer sent full_code, which the first attempt does not allow → this attempt allows edits or "
    "full_code"
)

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
    "self_review",
]
"""Where an attempt, or the run, stopped (content-free, for the attribution log only).

`adapter_schema`: the answer failed the plan schema; `adapter_truncated`: it was cut
off at the output limit; `adapter_full_code`: a full file where none was allowed;
`edit_apply`: an edit did not apply; `validator`: a blocking validator finding or the
literal budget; `loader`: the code could not take the data loader; `render`: the host
gates R1 or R2 failed; `gates`: the render passed them but its canvas, probe or
ADAPTATION findings went to the repair (or the canvas was padded); `not_rereviewed`:
a repaired render shipped without another review because the run had made its
`MAX_REVIEWS` reviewer calls; `reviewer_*`: the outcome of the attempt's review, the
first or the second; `budget`, `deadline`: a limit stopped the run before an attempt
or before a review; `error`: an exception."""
AdaptOutcome = Literal["schema", "truncated"]


@dataclass(frozen=True)
class AdaptMiss:
    """An adapter answer that yielded no plan: it failed the schema or was cut off at the output limit."""

    outcome: AdaptOutcome

    @property
    def stage(self) -> Stage:
        return "adapter_truncated" if self.outcome == "truncated" else "adapter_schema"

    @property
    def line(self) -> str:
        """The repair's feedback line: a cut-off answer needs a shorter plan, a schema miss the schema."""
        return CUT_OFF_LINE if self.outcome == "truncated" else SCHEMA_MISS_LINE


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
    status_ok: bool | None = None
    """The review found it good enough to show without notes (`ReviewOutcome.status_ok`)."""
    render_id: str | None = None
    adaptation_rules: list[str] = field(default_factory=list)
    """The ADAPTATION validator rule ids behind `adaptation_lines`, for the attribution log."""
    advisory_gates: list[str] = field(default_factory=list)
    """The advisory probe gate ids (`G3`, `G5`, `G7`, `G8`, `G9`, `G10`, `G11`, `G12`) behind `advisory_lines`, for the
    attribution log."""
    review_score: int | None = None
    """The catalogue review's score of this render, when it had one (`AGENT_REVIEWER_MODE=catalogue`)."""
    review_lines: list[str] = field(default_factory=list)
    """This render's own review lines, so a best-scored earlier render ships with its own notes."""
    visible_lines: list[str] = field(default_factory=list)
    """The review lines of this render under `VISIBLE_DEFECT_IDS`, whatever its points: such a render is no clean
    one for `ship_compare`, and shipped it carries them as notes (review of #12204)."""
    changes: list[str] = field(default_factory=list)
    """What this render's code changed, for `PlotResult.changes`: the notes of every adapter call of the run
    up to this render that changed the code (`Run.changes`), so a best-scored earlier render reports its own."""
    texts: dict[ShownGroup, list[str]] | None = None
    """This render's drawn texts by role (`grounding.plot_texts`), for `PlotShows`; None without probe labels, which
    the root never sees (`tool_safety.fence_pipeline_notes`)."""
    expect_lines: list[str] = field(default_factory=list)
    """The requested texts and number formats this render does not show (`grounding.expected_misses`), as lines."""
    expect_misses: list[str] = field(default_factory=list)
    """The same misses as the requested texts themselves, for `PlotShows.requested_not_found`."""
    expect_note: str | None = None
    """`grounding.UNVERIFIED_LINE` when the run had requested texts but no drawn texts checked them, and no readable
    review of this render answered for them (`expect_review`)."""
    expect_review: bool = False
    """The requested texts go to this render's review, since its runtime's reviewer checks them
    (`RuntimeAdapter.review_texts`): a readable review replaces `expect_note` with the misses it reports
    (`grounding.reviewed_misses`), as `expect_lines` and `expect_misses`."""


@dataclass
class Run:
    """The pipeline's bookkeeping for one call."""

    view: SessionView
    dataset: StoredDataset
    theme: Theme = "light"
    theme_asked: bool = False
    """The user asked for `theme` (`run_theme`); the shipped version keeps it as `CodeVersion.theme_asked`."""
    language: str = DEFAULT_LANGUAGE
    """The plot language (`session_state.plot_language`), read once per run: the adapter writes the plot text in it,
    the reviewer judges it."""
    attempts: int = 0
    best: Candidate | None = None
    padded: Candidate | None = None
    reviewed: bool = False
    review_lines: list[str] = field(default_factory=list)
    reason: FailureReason | None = None
    rendered: bool = False
    unreviewed_why: str | None = None
    error_type: str | None = None
    """The exception class that ended the run with reason `error` or `busy` (content-free, for the attribution log)."""
    stage: Stage | None = None
    """What stopped the run: the last attempt's stage, or a limit before the next attempt."""
    stages: list[Stage] = field(default_factory=list)
    """The stage that ended each attempt, in order."""
    reviewed_attempt: int | None = None
    """The attempt whose render the reviewer was last called on, read or not."""
    reviews: int = 0
    """Reviewer calls so far, at most `MAX_REVIEWS`."""
    rounds: list[Round] = field(default_factory=list)
    """How each attempt ended, in the page's vocabulary (`ROUND_OUTCOMES`), for `PlotResult.rounds`."""
    step: RoundStep | None = None
    """The progress step the current attempt is in, the last one `_status` reported."""
    best_scored: Candidate | None = None
    """The canvas-clean render with the highest catalogue review score (`AGENT_SHIP_BEST`)."""
    self_reviewed: bool = False
    """The adapter has looked at its own render at least once (`AGENT_SELF_REVIEW`)."""
    reviewed_render_id: str | None = None
    """The render id of the last rejected review, which a repair and its proofreading may see."""
    same_round_after: list[int] = field(default_factory=list)
    """The attempts whose next attempt stays in their round (`round_number`): the ones a self-review
    followed, and the one whose answer failed its check and got the round's retry."""
    retried_rounds: set[int] = field(default_factory=set)
    """The rounds that used their one retry after an answer failed its check (`RETRY_STAGES`)."""
    proofread_rounds: set[int] = field(default_factory=set)
    """The rounds whose self-review has started (`AGENT_SELF_REVIEW`): a check retry of the proofread
    answer stays the proofread, so a round never proofreads twice."""
    repair_hints: list[str] = field(default_factory=list)
    """The latest render's measured targets for a repair (`GateReport.repair_hints`), added to
    the hints of every repair attempt after it; they never start a repair themselves."""
    change_request: str = ""
    """The run's own change request, stored with the version among its `requests`."""
    user_requests: list[str] = field(default_factory=list)
    """The base version's change requests (`standing_requests`): the user's standing decisions."""
    changes: list[str] = field(default_factory=list)
    """The `changes` notes of every adapter call so far whose plan changed the code, in order (`note_changes`)."""
    expected_texts: list[str] = field(default_factory=list)
    """The texts and number formats the user asked to see (`PipelineArgs.expected_texts`), checked per render."""
    base: Literal["catalogue", "previous"] = "catalogue"
    round_scores: dict[int, int] = field(default_factory=dict)
    """The catalogue review score of each reviewed round's latest review, by round: the telemetry's score buckets."""
    forced_ids: set[str] = field(default_factory=set)
    """Review ids under `VISIBLE_DEFECT_IDS` that forced a repair round."""
    review_ids: set[str] = field(default_factory=set)
    """Every review id any review of the run named."""
    gate_ids: set[str] = field(default_factory=set)
    """Every gate id any render of the run failed (`GateReport.failed_gates`)."""
    sandbox_failures: set[str] = field(default_factory=set)
    """The closed classes of the renders that failed in the sandbox (`telemetry.sandbox_failure`)."""
    drift_restored: bool = False
    """A plan whose only failure was drift of the protected theme statements had them restored
    (`edits.restore_protected`) after the round's check retry was spent."""
    stage_s: dict[str, float] = field(default_factory=dict)
    """Seconds spent in `adapt`, `check`, `render` and `review`, summed over the attempts."""
    loader_notes: list[str] = field(default_factory=list)
    """What the runtime's loader changes when it reads the run's `data.csv` (`RuntimeAdapter.loader_notes`): the first
    `changes` of every shipped render, so a value the plot shows rounded is never unannounced; never a residual note,
    so the status stays as the render earns it (owner decision of 2026-10-29)."""
    loader_codes: list[str] = field(default_factory=list)
    """The kinds of cells behind `loader_notes` (`loader_codes`), for the usage telemetry: never the notes, which name
    columns and counts."""
    data_json: str | None = None
    """The run's table as typed JSON for a runtime whose code reads no `data.csv` (`RuntimeAdapter.data_json`:
    JavaScript), built once per run; every render job of the run and the shipped version carry it."""
    edit_failures: set[str] = field(default_factory=set)
    """The `edits.FAILURE_KINDS` of every plan whose edits failed and ended its attempt."""
    validator_rules: set[str] = field(default_factory=set)
    """The rule ids that rejected a plan's code in any check of the run (`CheckResult.blocking_rules`)."""
    adaptation_rules: set[str] = field(default_factory=set)
    """The soft ADAPTATION rule ids of any check of the run (`CheckResult.adaptation_rules`)."""

    def timed(self, stage: str, seconds: float) -> None:
        self.stage_s[stage] = self.stage_s.get(stage, 0.0) + seconds


ROUND_OUTCOMES: dict[Stage, RoundOutcome] = {
    "reviewer_ok": "ok",
    "self_review": "measured",
    "reviewer_defects": "review",
    "gates": "measured",
    "render": "render_failed",
    "edit_apply": "check_failed",
    "validator": "check_failed",
    "loader": "check_failed",
    "adapter_schema": "answer_unusable",
    "adapter_truncated": "answer_unusable",
    "adapter_full_code": "answer_unusable",
    "not_rereviewed": "unreviewed",
    "reviewer_unreadable": "unreviewed",
    "budget": "unreviewed",
    "deadline": "unreviewed",
    "error": "error",
}
"""The page's name for the stage that ended an attempt; the stage itself stays in the attribution log."""

RETRY_STAGES: frozenset[Stage] = frozenset(
    {"adapter_schema", "adapter_truncated", "adapter_full_code", "edit_apply", "validator", "loader", "render"}
)
"""Stages where the adapter's answer failed its check: each round retries once before the miss ends it."""


def _end_attempt(run: Run, stage: Stage, feedback: Sequence[str] = ()) -> None:
    """Record what ended the current attempt, at the step it was in, with the lines it passes on.

    `findings` counts `feedback` as the next attempt reads it: deduplicated and capped
    by `_clip_feedback`.
    """
    run.stages.append(stage)
    run.stage = stage
    if stage == "self_review":
        # The adapter proofreading its own render is part of the round, never a round of its own.
        run.same_round_after.append(run.attempts)
        return
    current = round_number(run, run.attempts)
    if stage in RETRY_STAGES and _retry_left(run):
        # An answer that failed its check (edits that do not apply, a validator finding, a broken
        # schema, code that crashes) gets one more adapter call in the same round, which may send a
        # full file: a round never ends unfinished for a formal miss (owner rule, 2026-10-13).
        run.retried_rounds.add(current)
        run.same_round_after.append(run.attempts)
        return
    clipped = _clip_feedback(list(feedback))
    run.rounds.append(
        Round(
            attempt=max(round_number(run, run.attempts), 1),
            outcome=ROUND_OUTCOMES[stage],
            findings=len(clipped),
            step=run.step,
            defects=[found for found in _defect_ids(clipped) if found in KNOWN_IDS][:MAX_ROUND_DEFECTS],
        )
    )


def _retry_left(run: Run) -> bool:
    """Whether a failed check of the current attempt's answer still gets the round's one retry (`RETRY_STAGES`)."""
    return get_settings().check_retry and round_number(run, run.attempts) not in run.retried_rounds


def round_number(run: Run, attempt: int) -> int:
    """The round an attempt belongs to on the page: a self-review or a retry stays in the round it follows."""
    return attempt - sum(1 for earlier in run.same_round_after if earlier < attempt)


def _call_fields(ledger: RequestLedger, agent: str) -> dict[str, Any]:
    """The content-free facts of `agent`'s latest model call for an attribution line."""
    call = ledger.last_calls.get(agent)
    if call is None:
        return {"finish_reason": None, "candidates": 0, "thoughts": 0}
    return {"finish_reason": call.finish_reason, "candidates": call.candidates, "thoughts": call.thoughts}


def _line(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"


def _status(run: Run, step: RoundStep, attempt: int, previous: Round | None = None) -> Event:
    """A progress event, noted as the run's current step; a repair round's first one says how the round before ended."""
    run.step = step
    status: dict[str, Any] = {"step": step, "attempt": round_number(run, attempt)}
    if previous is not None:
        status.update(outcome=previous.outcome, findings=previous.findings, defects=list(previous.defects))
    return Event(custom_metadata={STATUS_KEY: status})


def _result_event(result: PlotResult) -> Event:
    return Event(output=result.model_dump(mode="json"))


def load_inputs(
    ctx: Context, services: Services
) -> tuple[SessionView | None, StoredDataset | None, NotReadyReason | None]:
    """The session view and dataset, or the `not_ready` reason.

    `no_dataset`, `incomplete_bindings`, or `data_unconfirmed`: the user has not confirmed
    the dataset with its bindings in the data panel (step 1 of two), so neither the model
    nor a stale page can start a plot on data the user has not looked at.
    """
    view = read_session(ctx.state)
    if view is None:
        return None, None, "no_dataset"
    dataset = services.datasets.get(view.dataset_id, ctx.session.id) if view.dataset_id else None
    if dataset is None:
        return view, None, "no_dataset"
    check = check_bindings(view.bindings, view.snapshot.roles(), dataset.profile)
    if not check.complete:
        return view, dataset, "incomplete_bindings"
    if not view.data_confirmed:
        return view, dataset, "data_unconfirmed"
    return view, dataset, None


PENDING_REASONS: frozenset[str] = frozenset({"data_unconfirmed", "incomplete_bindings"})
"""The `not_ready` reasons a first plot's request waits through: the user confirms or binds, then plots again."""


def keep_pending_request(state: Any, args: PipelineArgs, reason: NotReadyReason | None) -> bool:
    """Keep a first plot's `change_request` that stopped on `reason` for the next run (`PENDING_REQUEST`);
    whether this run's own request or texts were kept (`PlotResult.request_kept`).

    A live test of 2026-10-15: the user's step-2 note ("only co2_per_capita, title ...") made
    the root change the bindings, which asked for `.confirm()` again; the plot stopped on
    `data_unconfirmed`, and the title never reached the plot that the next `.create_plot()`
    drew. A change of an existing version (`base="previous"`) is not kept: it names a plot
    that is there, and the root repeats it once the reason is gone.

    Live round 9 of 2026-10-16: a title asked for before `.confirm()` is the same case, and the root
    keeps it only through this path (`root.md`); the result's `request_kept` says that it did.
    """
    if reason not in PENDING_REASONS or args.base == "previous" or not (args.change_request or args.expected_texts):
        return False
    hold_request(state, args)
    return True


def hold_request(state: Any, args: PipelineArgs) -> None:
    """Keep a first plot's `change_request` for the next run, joined to one kept already (`merged_request`).

    Also the path of a run that passed the check but got no slot in the run queue (`capacity`,
    or a cancelled wait): its note waits for the next `.create_plot()` like a blocked one's.
    """
    if (args.change_request or args.expected_texts) and args.base != "previous":
        state[PENDING_REQUEST] = merged_request(state.get(PENDING_REQUEST), args.change_request) or None
        state[PENDING_EXPECTED_TEXTS] = chosen_texts(state.get(PENDING_EXPECTED_TEXTS), args) or None
        # The bindings the note was written for: a later binding change that only fills roles open then keeps it.
        bindings = state.get(BINDINGS)
        state[PENDING_BINDINGS] = list(bindings) if isinstance(bindings, list) else []


def kept_texts(value: object) -> list[str]:
    """The stored `expected_texts` that pass the same validator as `PipelineArgs.expected_texts`, item by item,
    without repeats and at most `MAX_EXPECTED_TEXTS`; anything else stored there is dropped."""
    texts: list[str] = []
    for item in value if isinstance(value, list) else []:
        try:
            text = EXPECTED_TEXT.validate_python(item, strict=True)
        except ValidationError:
            continue
        if text not in texts:
            texts.append(text)
    return texts[:MAX_EXPECTED_TEXTS]


def chosen_texts(pending: object, args: PipelineArgs) -> list[str]:
    """The texts a run checks: its own when it brings a request or texts of its own, else the kept ones.

    Review of 2026-10-15: the root never sees the kept texts, so joining them to a run's own kept
    a text the user had since withdrawn or replaced ("call it 'Study time'" after "Lernzeit"),
    which then counted as a miss and started a repair. A run that brings its own word replaces
    them; only a bare run (`.create_plot()`) fills in the kept ones.
    """
    if args.change_request or args.expected_texts:
        return list(args.expected_texts)
    return kept_texts(pending)


MIN_KEPT_NOTE_CHARS = 40
"""The least of a kept request worth keeping, cut, in front of a new one that leaves too little room."""


def merged_request(pending: object, own: str) -> str:
    """A kept request and a new one as one `change_request` of at most `MAX_CHANGE_REQUEST_CHARS`.

    The kept one comes first. When both do not fit, the kept one is cut with `…` to the room the
    new one leaves (review of 2026-10-15: dropping it silently lost the user's title), unless less
    than `MIN_KEPT_NOTE_CHARS` would remain; then the new one, the user's latest word, stands
    alone. A new one the kept one already holds as a line adds nothing. A kept value that is no
    text is ignored.
    """
    own = own.strip()
    if not isinstance(pending, str) or not pending.strip():
        return own
    pending = pending.strip()[:MAX_CHANGE_REQUEST_CHARS]
    if not own or own in pending.split("\n"):
        return pending
    if len(pending) + 1 + len(own) <= MAX_CHANGE_REQUEST_CHARS:
        return f"{pending}\n{own}"
    room = MAX_CHANGE_REQUEST_CHARS - len(own) - 2  # the `…` and the line break
    if room < MIN_KEPT_NOTE_CHARS:
        return own
    return f"{pending[:room].rstrip()}…\n{own}"


def take_pending_request(state: Any, args: PipelineArgs) -> PipelineArgs:
    """The run's arguments with a kept request (`keep_pending_request`) in front of its own.

    A run on the catalogue plot without a request of its own (the bare `.create_plot()`) takes
    the kept one; one with its own request takes both (`merged_request`); a change of an
    existing version takes none. The state keeps the request until the run ends
    (`settle_pending_request`), so a run that fails loses no note (review of 2026-10-15).
    """
    pending = state.get(PENDING_REQUEST)
    texts = state.get(PENDING_EXPECTED_TEXTS)
    if (pending is None and texts is None) or args.base == "previous":
        return args
    # Validated like the root's own arguments: a stored value never reaches the run unchecked.
    joined = {
        **args.model_dump(),
        "change_request": merged_request(pending, args.change_request),
        "expected_texts": chosen_texts(texts, args),
    }
    try:
        return PipelineArgs.model_validate(joined)
    except ValidationError:
        return args


PENDING_KEYS = (PENDING_REQUEST, PENDING_EXPECTED_TEXTS, PENDING_BINDINGS)


def settle_pending_request(state: Any, args: PipelineArgs, shipped: bool) -> None:
    """After a run, the kept note as the run leaves it; only a first-plot run touches it, as only it took it.

    A shipped first plot used the kept request and texts, so they go. A first-plot run that
    shipped nothing keeps what it ran with (`take_pending_request` joined the kept and its own)
    for the next one. A change of an existing version (`base="previous"`) took nothing, so it
    leaves the note as it is (review of 2026-10-15), except that stored texts that no longer
    pass the validator are cleaned (`kept_texts`).
    """
    if args.base == "previous":
        stored = state.get(PENDING_EXPECTED_TEXTS)
        if stored is not None and kept_texts(stored) != stored:
            state[PENDING_EXPECTED_TEXTS] = kept_texts(stored) or None
        return
    if shipped:
        for key in PENDING_KEYS:
            if state.get(key) is not None:
                state[key] = None
    elif args.change_request or args.expected_texts:
        state[PENDING_REQUEST] = args.change_request or None
        state[PENDING_EXPECTED_TEXTS] = list(args.expected_texts) or None


def render_adapt_request(request: AdaptRequest, view: SessionView) -> str:
    """The adapter's node input: the request as fenced text.

    Outside a fence stand only fixed headings, the validated library id and
    `allow_full`; the plot language, a user-chosen value bounded by a pattern, stands
    inside its own `<plot_language>` fence, and the reply language, when it differs, inside
    `<reply_language>` (the `changes` notes are written in it). The notes on the attempt go into one
    `<tool_notes>` block as JSON, the way the `plot_pipeline` result reaches the root:
    the readiness hints quote catalogue lines, the feedback quotes model-written code
    (failed edits, validator findings) or is model-written (reviewer lines), and the
    previous plan is model-written and can copy catalogue or dataset text;
    `language_changed` says that the base version's text is in another language. The profile is the first
    version of `trimmed_profiles` within `MAX_ADAPTER_PROFILE_BYTES` (`adapter_profile`):
    50 text columns of long values make it about 28,000 characters in full (stress case
    `stress-cap-profile`), more than the rest of the request.
    """
    profile_text, trimmed = adapter_profile(request.profile)
    lines = [
        f"Library: {view.library}",
        "",
        DATA_PREAMBLE,
        "Spec brief:",
        fence("spec_text", spec_brief(view)),
        fence("catalogue_code", request.code),
        "Dataset profile (shortened: fewer sample rows or top values):" if trimmed else "Dataset profile:",
        fence("user_data", profile_text),
        "Bindings and loader columns:",
        fence("user_data", _columns_json(request.bindings, request.loader_columns)),
        "Plot language:",
        fence("plot_language", request.plot_language),
    ]
    if request.reply_language is not None:
        lines += [REPLY_LANGUAGE_HEADING, fence("reply_language", request.reply_language)]
    lines += _context_lines(request.dataset_context, request.file_name)
    lines += _requests_lines(request.user_requests, request.change_request)
    if request.expected_texts:
        lines += [EXPECTED_HEADING, fence("user_message", "\n".join(request.expected_texts))]
    notes: dict[str, Any] = {}
    if request.hints:
        notes["hints"] = request.hints
    if request.feedback:
        notes["feedback"] = request.feedback
    if request.previous_plan is not None:
        notes["previous_plan"] = request.previous_plan.model_dump(mode="json")
    if request.language_changed:
        notes["language_changed"] = True
    if notes:
        lines += ["Notes on this attempt:", fence("tool_notes", json.dumps(notes, ensure_ascii=False))]
    lines.append(f"allow_full: {'true' if request.allow_full else 'false'}")
    return "\n".join(lines)


def render_review_request(request: ReviewRequest) -> str:
    """The reviewer's node input: the request as fenced text (the images are added by its callback).

    The gate notes are host-written, but they go into a `<tool_notes>` block too, and the
    plot language into its own `<plot_language>` block, so nothing but fixed headings
    stands outside a fence.
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
        "Plot language:",
        fence("plot_language", request.plot_language),
    ]
    lines += _context_lines(request.dataset_context, request.file_name)
    lines += _requests_lines(request.user_requests, request.change_request)
    lines += _review_expected_lines(request.expected_texts, catalogue=False)
    if request.gate_notes:
        lines += ["Gate notes:", fence("tool_notes", json.dumps(request.gate_notes, ensure_ascii=False))]
    return "\n".join(lines)


REPLY_LANGUAGE_HEADING = "Reply language (the user chats in it; write the `changes` notes in it):"
EARLIER_REQUESTS_HEADING = "Earlier requests (the user's standing decisions, oldest first):"
EXPECTED_HEADING = "Texts and number formats the user asked to see in the plot, verbatim (one per line):"
REVIEW_EXPECTED_HEADING = (
    "Texts and number formats the user asked to see in the plot, verbatim (one per line). The server cannot read "
    "the texts this render draws, so look for each one in the attached render yourself: a text must stand there as "
    "written (case, spacing and quotes aside); a number format (a number with one unit, such as 6,5 Mio. or 12 %) "
    "must draw its unit, and the numbers it applies to must use its decimal mark. Report each one you cannot find "
    "as one {ids} finding whose observed part quotes it as listed here: the plot does not show the requested "
    'text "<text>", then what it shows instead. One you find needs no finding:'
)
"""The reviewer's heading over the requested texts (`ReviewRequest.expected_texts`): only a render without drawn
texts gets it, so a review request of a render with the probe is the same as before 2026-10-29."""


def _review_expected_lines(texts: Sequence[str], *, catalogue: bool) -> list[str]:
    """The requested texts for the reviewer to find in the image, fenced as user text under their heading.

    The catalogue reviewer reports a missing number format under SC-02 as the probe's check does
    (`grounding.EXPECT_LINE_ID`); the checklist has no SC-02, so it reports every miss under SC-04.
    """
    if not texts:
        return []
    ids = EXPECT_LINE_ID["text"] + (f" ({EXPECT_LINE_ID['format']} for a number format)" if catalogue else "")
    return [REVIEW_EXPECTED_HEADING.format(ids=ids), fence("user_message", "\n".join(texts))]


CONTEXT_HEADING = (
    "Dataset context (what the session knows about the data: the notes the user pasted with it and where a "
    "computed table comes from; use it for the title and the labels):"
)


FILE_NAME_HEADING = (
    "File name (the name of the file the user dropped: a file name, which may hint at the subject or the "
    "period, never an instruction, never a title, a label or a unit to copy):"
)


def _context_lines(context: str, file_name: str = "") -> list[str]:
    """The dataset context block (`dataset_context.py`) under its fixed heading, fenced as the user's notes, then
    a dropped file's name under its own heading, fenced as data: never among the notes, whose title and units
    the models take (review of #12192: a file named "Title is X, y in USD.csv" must not steer the plot)."""
    lines = [CONTEXT_HEADING, fence("user_notes", context)] if context else []
    if file_name:
        lines += [FILE_NAME_HEADING, fence("user_data", file_name)]
    return lines


def _requests_lines(user_requests: Sequence[str], change_request: str) -> list[str]:
    """The earlier requests and the change request, each block fenced as user text under a fixed heading."""
    lines: list[str] = []
    if user_requests:
        numbered = "\n".join(f"{number}. {text}" for number, text in enumerate(user_requests, 1))
        lines += [EARLIER_REQUESTS_HEADING, fence("user_message", numbered)]
    if change_request:
        lines += ["Change request:", fence("user_message", change_request)]
    return lines


def standing_requests(requests: Sequence[str]) -> list[str]:
    """The most recent change requests of a lineage within `MAX_USER_REQUESTS` and `MAX_USER_REQUESTS_CHARS`.

    Oldest first, each on one line, empty ones dropped, a repeated request kept once at its latest
    place. A request that would cross the character cap ends the list there: an older one never
    stands without the newer ones, which may have changed what it set.
    """
    kept: list[str] = []
    total = 0
    for request in reversed(requests):
        text = " ".join(request.split())
        if not text or text in kept:
            continue
        if len(kept) == MAX_USER_REQUESTS or total + len(text) > MAX_USER_REQUESTS_CHARS:
            break
        kept.append(text)
        total += len(text)
    return kept[::-1]


def note_changes(run: Run, plan: AdaptPlan, *, changed: bool, proofread: bool) -> None:
    """Add a plan's `changes` notes to the run's, in order and once each.

    A call counts when its plan changed the code. An adaptation (or its check retry) that changed
    nothing counts only while the run has no notes yet, so a change that needed no edit can say
    why; a proofread that changed nothing never counts, nor does any later call that changed
    nothing: its notes ("already present") describe code another call wrote (the live test of
    2026-10-14, where they replaced the round's real changes).
    """
    if not changed and (proofread or run.changes):
        return
    run.changes = list(dict.fromkeys([*run.changes, *(" ".join(note.split()) for note in plan.changes)]))


def summarise_changes(notes: Sequence[str], limit: int = MAX_CHANGES) -> list[str]:
    """At most `limit` notes: the first ones (the adaptation that carried out the request) and the latest.

    A run's calls may write more notes than `PlotResult` holds; keeping only the earliest would hide what a
    later repair or proofread changed in the shipped code (#12170 review), keeping only the latest would hide
    the request itself. The notes in between are left out. `limit` is below `MAX_CHANGES` when the runtime's
    loader notes take places first (`finish`).
    """
    if limit <= 0:
        return []
    if len(notes) <= limit:
        return list(notes)
    head = limit // 2 + 1
    return [*notes[:head], *notes[len(notes) - (limit - head) :]]


def _columns_json(bindings: list[Binding], loader_columns: list[str] | None = None) -> str:
    """Bindings (and the loader's columns) as JSON: column names are the user's headers, so they go in a fence."""
    payload: dict[str, Any] = {"bindings": [{"role": item.role, "column": item.column} for item in bindings]}
    if loader_columns is not None:
        payload["loader_columns"] = loader_columns
    return json.dumps(payload, ensure_ascii=False)


def _repair_hints(hints: list[str], run: Run) -> list[str]:
    """A repair attempt's hints: the latest render's measured targets first, then the base hints, within `MAX_NOTES`."""
    extra = [_note(line) for line in run.repair_hints if line not in hints]
    return [*extra, *hints][:MAX_NOTES]


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
    banned_imports: list[str] = field(default_factory=list)
    """The module labels of the `banned-import` findings (`validate.module_label`), at most `MAX_LOGGED_MODULES`."""


MAX_LOGGED_MODULES = 8
"""Banned module labels one `pipeline_check` line names; a plan that imports more is rare and says enough."""


def _data_texts(data_csv: str) -> frozenset[str]:
    """Every header and non-empty cell of the canonical data.csv."""
    return frozenset(cell for row in csv.reader(io.StringIO(data_csv)) for cell in row if cell)


def column_kinds_of(dataset: StoredDataset) -> ColumnKinds | None:
    """The value kinds of a dataset's canonical `data.csv` (`data.kinds.read_kinds`), read once per run.

    None when the CSV does not fit its own typing, which the parser never writes: the Python
    loader reads the dtypes alone and runs as before, and R's loader, which needs the kinds,
    refuses the run form, so the attempt ends as `loader`.
    """
    try:
        return read_kinds(dataset.csv, dataset.column_dtypes, dataset.parse_dates)
    except ValueError:
        return None


LOADER_CODES: tuple[str, ...] = ("inexact", "submillisecond", "offset")
"""The `ColumnKinds` fields of the cells a loader may change (`telemetry.LoaderNote`), in the order the line lists them."""


def loader_codes(runtime: RuntimeAdapter, kinds: ColumnKinds | None) -> list[str]:
    """The kinds of cells the runtime's loader changes when it reads this data, for the usage telemetry.

    The runtime is asked, not a table: each kind the data holds goes alone to `RuntimeAdapter.loader_notes`, and the
    kind counts when the runtime announces a note for it (R: `inexact`, `offset`; Julia: `submillisecond`, `offset`;
    Python: none). Only the code leaves this function, never the note, which names columns and counts.
    """
    if kinds is None:
        return []
    empty: dict[str, dict[str, int]] = {code: {} for code in LOADER_CODES}
    return [
        code
        for code in LOADER_CODES
        if getattr(kinds, code) and runtime.loader_notes(replace(kinds, **{**empty, code: getattr(kinds, code)}))
    ]


def _check(
    working: str,
    *,
    library: str,
    palette: list[str],
    base: str,
    literal_budget: int = MAX_NEW_LITERAL_CHARS,
    rewrite: bool = False,
    origin: str | None = None,
    data_texts: frozenset[str] = frozenset(),
    runtime: RuntimeAdapter | None = None,
) -> CheckResult:
    """Validate a working form against its base: may it render, the blocking lines, the adaptation defect lines.

    The two validator profiles, the literal diff, the ADAPTATION rules that reject the code and the
    targets of the others are the runtime's (`RuntimeAdapter.security`, `adaptation`, `new_literals`,
    `blocking_rules`, `adaptation_targets`); `runtime` defaults to the registry's for `library`.

    Besides the two validator profiles, the plan's new string literals (`edits.new_literals`)
    must fit `literal_budget`; on a `rewrite` (a change that writes the base's text in another
    language) the budget grows by `REWRITE_LITERAL_FACTOR` times the literal text the plan drops
    from the base, up to `MAX_NEW_LITERAL_CHARS`, so a translation fits and new text on top of it
    still meets the caller's budget. All new literals of the working form against `origin`
    (the catalogue code) `MAX_NEW_LITERAL_CHARS`, so text cannot pile up turn by turn; a
    literal that is a header or a cell of the dataset (`data_texts`) is free in both. The
    budget bounds how much text the model writes, not what it says: personal data the
    user asked for (a name, an address, an e-mail address) is ordinary plot text.
    """
    runtime = runtime if runtime is not None else runtime_for(library)
    security = runtime.security(working)
    adaptation = runtime.adaptation(working, original_palette=palette)
    rejecting = runtime.blocking_rules
    # Both profiles parse the code, so an unparseable file is one `syntax` finding, not two.
    blocking_findings = list(dict.fromkeys([*security, *(f for f in adaptation if f.rule in rejecting)]))
    blocking = [
        f"validator {f.rule}" + (f" (line {f.line})" if f.line else "") + f": {f.message}" for f in blocking_findings
    ]
    blocking_rules = [f.rule for f in blocking_findings]
    literals = runtime.new_literals(base, working)
    added = sum(len(text) for text in literals if text not in data_texts)
    if rewrite:
        # The base literals the plan no longer holds: the old-language text the translation replaces.
        dropped = sum(len(text) for text in runtime.new_literals(working, base) if text not in data_texts)
        literal_budget = min(MAX_NEW_LITERAL_CHARS, literal_budget + math.ceil(REWRITE_LITERAL_FACTOR * dropped))
    if added > literal_budget:
        blocking_rules.append("literal-budget")
        blocking.append(
            f"validator literal-budget: the plan adds {added} characters of new string literals, "
            f"{added - literal_budget} over the limit of {literal_budget} → derive text and values "
            "from df instead of writing them out. Likely cause: data or long text written into the code."
        )
    if origin is not None and origin != base:
        total = sum(len(text) for text in runtime.new_literals(origin, working) if text not in data_texts)
        if total > MAX_NEW_LITERAL_CHARS:
            if "literal-budget" not in blocking_rules:
                blocking_rules.append("literal-budget")
            blocking.append(
                f"validator literal-budget: the plot holds {total} characters of string literals the catalogue "
                f"code does not, {total - MAX_NEW_LITERAL_CHARS} over the limit of {MAX_NEW_LITERAL_CHARS} for "
                "all versions together → shorten or drop text added earlier instead of adding more. "
                "Likely cause: text added turn by turn."
            )
    soft = [f for f in adaptation if f.rule not in rejecting]
    targets = runtime.adaptation_targets
    defects = [
        f"{ADAPTATION_IDS.get(f.rule, 'SC-03')} (code): {f.message}"
        + (f" at line {f.line}" if f.line else "")
        + f" → {targets.get(f.rule, DEFAULT_ADAPTATION_TARGET)}. Likely cause: the adaptation ({f.rule})."
        for f in soft
    ]
    modules = list(dict.fromkeys(f.module for f in blocking_findings if f.rule == "banned-import" and f.module))
    return CheckResult(
        not blocking, blocking, defects, blocking_rules, [f.rule for f in soft], modules[:MAX_LOGGED_MODULES]
    )


def shipped_candidate(run: Run) -> Candidate | None:
    """The render a run ships: the last canvas-clean one, or with `AGENT_SHIP_BEST` the best-scored one
    when the last has no higher (or no) review score; a padded render only when nothing else exists."""
    best = run.best
    scored = run.best_scored
    if ship_best(get_settings()) and scored is not None and best is not scored:
        if best is None or best.review_score is None or ship_compare(scored, best) > 0:
            best = scored
    return best or run.padded


def _clean(candidate: Candidate) -> bool:
    """No measured finding (no advisory gate line, no ADAPTATION finding, no requested text missing) and no
    review line for a visible defect (`VISIBLE_DEFECT_IDS`): a clipped label is not clean at any score."""
    return not (
        candidate.advisory_lines or candidate.adaptation_lines or candidate.expect_lines or candidate.visible_lines
    )


def ship_compare(a: Candidate, b: Candidate) -> int:
    """How `AGENT_SHIP_BEST` orders two reviewed renders: 1 when `a` ships over `b`, -1 the other way, 0 a tie.

    A render without measured findings (clipped or overlapping text) wins over one with them when it
    meets the ship bar (`AGENT_STATUS_BAR`) or scores at most `AGENT_SHIP_CLEAN_MARGIN` points below it
    (owner, 2026-10-14). Otherwise the higher score ships, with its measured findings as notes: a clean
    render of 60 never replaces an 88 that has one overlapping label.
    """
    score_a, score_b = a.review_score or 0, b.review_score or 0
    if _clean(a) != _clean(b):
        clean, other = (a, b) if _clean(a) else (b, a)
        margin = get_settings().ship_clean_margin
        if clean.status_ok is True or (clean.review_score or 0) >= (other.review_score or 0) - margin:
            return 1 if clean is a else -1
    return (score_a > score_b) - (score_a < score_b)


def ship_best(settings: AgentSettings) -> bool:
    return settings.ship_best and settings.reviewer_mode == "catalogue"


def finish(run: Run) -> PlotResult:
    """The `PlotResult` of a finished run (see the module docstring for the status rules)."""
    shipped = shipped_candidate(run)
    if shipped is None:
        reason: FailureReason
        if run.reason in ("budget", "deadline", "busy", "error"):
            reason = run.reason
        else:
            reason = "render" if run.rendered else "validation"
        return PlotResult(
            status="failed", reason=reason, attempts=round_number(run, run.attempts), rounds=list(run.rounds)
        )
    residual: list[str] = []
    if shipped.padded:
        residual.append(PADDED_LINE.format(theme=run.theme))
        if shipped.canvas_line:
            residual.append(shipped.canvas_line)
    # The measured findings are facts of the shipped render, reviewed or not: the ADAPTATION findings and
    # every advisory gate line (clipping G3, annotations outside G5, overlap G7, G8, G9, missing glyphs G10,
    # crowded per-mark labels G11, the plot language's decimal mark G12).
    # No review score hides them (until 2026-10-14 only G10 stayed above the ship bar).
    residual += shipped.adaptation_lines
    residual += shipped.advisory_lines
    # A visible defect the review named stays a note at any score, as a measured one does: the repair round
    # was spent on it, and the render that ships still shows it (review of #12204).
    residual += shipped.visible_lines
    # A requested text or number format the shipped render does not show: the reply must say so.
    residual += shipped.expect_lines
    if shipped.expect_note:
        residual.append(shipped.expect_note)
    # The review's notes are left out when the render meets the ship bar (`AGENT_STATUS_BAR` and
    # `AGENT_STATUS_SCORE`; a checklist pass), although the review may still have asked for a repair:
    # the owner's rule is no review notes above the bar. The review bar decides the repair only, so a
    # pass below the ship bar keeps its notes.
    meets_bar = shipped.reviewed_ok if shipped.status_ok is None else shipped.status_ok
    status_score = get_settings().status_score
    if meets_bar is True and shipped.review_score is not None and shipped.review_score < status_score:
        # Every technical point the bar asks for, but a lower total (Design Excellence) than the ship score.
        residual.append(LOW_SCORE_LINE.format(score=shipped.review_score, bar=status_score))
    elif meets_bar is not True:
        if shipped.review_score is not None and shipped.review_lines:
            residual += shipped.review_lines
        elif run.review_lines:
            residual += run.review_lines
        elif not run.reviewed or shipped.reviewed_ok is None:
            # The shipped render itself was never reviewed, even when an earlier one was: a repair of
            # measured findings after a passing review, whose own review was unreadable or skipped.
            residual.append(NOT_REVIEWED_LINE.format(why=run.unreviewed_why or "the repair round left defects"))
    residual = list(dict.fromkeys(_line(line) for line in residual))[:MAX_RESIDUAL_DEFECTS]
    # The shipped render's own notes: every call up to it that changed the code, never a no-op proofread's. The
    # loader's notes come first, so the cap never drops them (owner decision of 2026-10-29: "what changed").
    loader = run.loader_notes[:MAX_CHANGES]
    adapted = summarise_changes(shipped.changes, limit=MAX_CHANGES - len(loader))
    changes = [change[:MAX_CHANGE_CHARS] for change in [*loader, *adapted]]
    return PlotResult(
        status="needs_attention" if residual else "ok",
        attempts=max(round_number(run, run.attempts), 1),
        artifacts=artifact_names([run.theme], runtime_for(run.view.library).code_artifact),
        changes=changes,
        residual_defects=residual,
        # The shipped render may come from an earlier round than the last (a repair that failed its check).
        rounds=[
            round_.model_copy(update={"shipped": round_.attempt == round_number(run, shipped.attempt)})
            for round_ in run.rounds
        ],
        shows=PlotShows(
            texts=shipped.texts,
            review=_review_state(shipped, meets_bar),
            score=shipped.review_score,
            requested_not_found=shipped.expect_misses,
        ),
    )


def _review_state(shipped: Candidate, meets_bar: bool | None) -> ReviewState:
    """The review's verdict on exactly the shipped render, for `PlotShows.review`."""
    if shipped.reviewed_ok is None:
        return "not_reviewed"
    return "passed" if meets_bar is True else "findings"


def _store_version(ctx: Context, services: Services, run: Run, result: PlotResult) -> PlotResult:
    """Store a shipped result as the session's next version; the result comes back with its `version`.

    The number travels in the `plot` event, so a client addresses the artifact and theme
    toggle routes by the server's number instead of counting the events it received.
    """
    shipped = shipped_candidate(run)
    if shipped is None or result.status not in ("ok", "needs_attention"):
        return result
    session_id = ctx.session.id
    render_id = shipped.render_id or services.renders.put(session_id, shipped.pngs)
    snapshot = run.view.snapshot
    number = services.versions.next_number(session_id)
    result = PlotResult.model_validate({**result.model_dump(), "version": number})
    runtime = runtime_for(run.view.library)
    services.versions.add(
        session_id,
        CodeVersion(
            number=number,
            working=shipped.working,
            run_form=shipped.run_form,
            export=runtime.export(
                shipped.run_form, spec_id=snapshot.spec_id, library_version=snapshot.library_version, theme=run.theme
            ),
            code_artifact=runtime.code_artifact,
            data_csv=run.dataset.csv,
            data_json=run.data_json,
            render_id=render_id,
            result=result,
            plan=shipped.plan,
            title=shipped.plan.title,
            library=run.view.library,
            theme=run.theme,
            theme_asked=run.theme_asked,
            language=run.language,
            requests=standing_requests([*run.user_requests, run.change_request]),
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


@dataclass(frozen=True)
class ReviewOutcome:
    """A read review in either mode: the verdict, the defect lines for the repair, their ids, the score."""

    ok: bool
    """No repair needed: the technical points at the review bar (`AGENT_REVIEW_BAR`) and no defect line under
    `VISIBLE_DEFECT_IDS`, or the checklist passed."""
    lines: list[str]
    ids: list[str]
    score: int | None = None
    technical: float | None = None
    status_ok: bool | None = None
    """Good enough to show without notes (`AGENT_STATUS_BAR`, the owner's ship bar); None means `ok`."""
    visible: list[str] = field(default_factory=list)
    """The defect lines under `VISIBLE_DEFECT_IDS`: the render is not clean (`Candidate.visible_lines`)."""
    requested: list[tuple[str, str]] = field(default_factory=list)
    """The requested texts the review could not find in the image, each with the line that says so
    (`grounding.reviewed_misses`); empty when the request carried none (`ReviewRequest.expected_texts`)."""


async def _review(ctx: Context, scope: str, request: ReviewRequest, theme: Theme) -> ReviewOutcome | None:
    ledger_for(ctx.invocation_id).last_calls.pop(REVIEWER_NAME, None)
    catalogue = get_settings().reviewer_mode == "catalogue"
    text = render_score_request(request) if catalogue else render_review_request(request)
    try:
        agent = use_reviewer_mode(get_settings().reviewer_mode)
        raw = await ctx.run_node(agent, node_input=text, override_isolation_scope=scope)
        if not catalogue:
            verdict = Verdict.model_validate(raw)
            lines = [_on_theme(defect, theme).as_line() for defect in verdict.defects]
            requested = reviewed_misses(request.expected_texts, lines)
            return ReviewOutcome(
                verdict.ok and not _repairs_miss(requested),
                lines,
                [defect.id for defect in verdict.defects],
                requested=requested,
            )
        result = parse_answer(mend_answer(ScoreAnswer.model_validate(raw).model_dump()))
    except (ValidationError, DynamicNodeFailError) as exc:
        _reraise_unless_schema(exc)
        return None
    except ScoreError as exc:
        # The message names criteria and ranges only, never content.
        logger.warning("catalogue review answer is not a complete score: %s", exc)
        return None
    settings = get_settings()
    ok = result.passes(settings.review_bar)
    # The two bars are independent settings: an experiment may set the review bar below the ship bar.
    status_ok = result.passes(settings.status_bar)
    if not (ok and status_ok) and not result.defects:
        # Points lost without a line to say why: no ship-bar notes and nothing for the repair to fix.
        logger.warning("catalogue review deducted without defect lines: %s", ", ".join(result.silent))
        return None
    ids = sorted({found for line in result.defects if (m := DEFECT_RE.match(line)) for found in m["ids"].split(", ")})
    visible = [
        line
        for line in result.defects
        if (m := DEFECT_RE.match(line)) and VISIBLE_DEFECT_IDS & set(m["ids"].split(", "))
    ]
    # A requested text the review could not find in the image (a render without drawn texts), read from every
    # line whatever the points: a repair finding as the probe's miss is under `AGENT_EXPECT_CHECK=repair`.
    requested = reviewed_misses(request.expected_texts, result.defects)
    if visible or _repairs_miss(requested):
        # A visible defect gets the repair round whatever the points (`VISIBLE_DEFECT_IDS`); the ship bar stays.
        ok = False
    return ReviewOutcome(
        ok,
        [] if ok and status_ok else result.defects,
        ids,
        result.score,
        round(result.technical_share, 3),
        status_ok=status_ok,
        visible=visible,
        requested=requested,
    )


def _repairs_miss(requested: Sequence[tuple[str, str]]) -> bool:
    """A requested text the review reports missing sends the round to the repair (`AGENT_EXPECT_CHECK=repair`)."""
    return bool(requested) and get_settings().expect_check == "repair"


def render_score_request(request: ReviewRequest) -> str:
    """The catalogue reviewer's node input: the scorer's request (`scoring.user_text`) with the
    gate notes and the change request added, every value fenced; the image follows from the callback."""
    lines = [
        DATA_PREAMBLE,
        fence("spec_text", request.spec_brief),
        fence("plot_code", request.code),
        fence("user_data", request.profile_summary),
        fence("user_data", json.dumps([item.model_dump() for item in request.bindings], ensure_ascii=False)),
        fence("plot_language", request.plot_language),
    ]
    if request.dataset_context or request.file_name:
        lines.append("\n".join(_context_lines(request.dataset_context, request.file_name)))
    lines += _requests_lines(request.user_requests, request.change_request)
    lines += _review_expected_lines(request.expected_texts, catalogue=True)
    if request.gate_notes:
        lines += ["Gate notes:", fence("tool_notes", json.dumps(request.gate_notes, ensure_ascii=False))]
    return "\n\n".join(lines)


def _reraise_unless_schema(exc: Exception) -> None:
    """Backstop of `schema_guard`: a sub-agent answer that failed its schema inside ADK is not an error."""
    if isinstance(exc, DynamicNodeFailError) and not isinstance(exc.error, ValidationError | ValueError):
        raise exc
    logger.warning("sub-agent answer failed its schema: %s", type(exc).__name__)


def run_theme(asked: Theme | None, site: Theme | None, previous: CodeVersion | None) -> tuple[Theme, bool]:
    """The one theme a run renders, and whether the user asked for it (`CodeVersion.theme_asked`).

    In order: the theme the root passed (`PipelineArgs.theme`), which the user asked for in the chat; on a
    change, the theme of the version it changes (`previous`) when the user asked for that one, because the root
    leaves `theme` out of a refinement and a dark plot asked for must not silently come back light; the site
    theme the page sent with the turn (`RequestLedger.site_theme`; owner decision of 2026-11-01: a user on the
    dark site gets a dark plot, the other theme one click away on the toggle), so a change after a switch of the
    site theme follows the switch; without a page (`adk web`, the evals) the version it changes, else light.
    """
    if asked is not None:
        return asked, True
    if previous is not None and previous.theme_asked:
        return previous.theme, True
    if site is not None:
        return site, False
    return (previous.theme if previous is not None else "light"), False


@node(name="run_pipeline", rerun_on_resume=True)
async def run_pipeline(ctx: Context, node_input: PipelineArgs) -> AsyncGenerator[Event, None]:
    """Adapt, check, render, review and repair; yields status events and one PlotResult."""
    services = get_services()
    settings = get_settings()
    ledger = ledger_for(ctx.invocation_id)
    view, dataset, not_ready = load_inputs(ctx, services)
    language = plot_language(view, services.versions.latest_language(ctx.session.id)) if view is not None else None
    if not_ready is not None or view is None or dataset is None:
        kept = keep_pending_request(ctx.state, node_input, not_ready)
        # An attempted plot the data was not ready for is a run of its own in the telemetry: the funnel sees it.
        index = telemetry.run_index(ctx.session.id, ctx.invocation_id)
        telemetry.write(
            telemetry.PipelineRun,
            ledger,
            attempt=f"run{index}",
            run_index=index,
            base=node_input.base,
            status="not_ready",
            reason=not_ready or "no_dataset",
            plot_language=telemetry.plot_language(language),
            readiness=telemetry.readiness(view.readiness) if view is not None else None,
            lane=ledger.tier,
        )
        yield _result_event(PlotResult.not_ready(not_ready or "no_dataset", request_kept=kept))
        return
    ledger.pipeline_active = True
    if ledger.run_slot is not None and not await ledger.run_slot():
        # No slot: the route failed the turn with `capacity`, or the user cancelled the wait. Either way the run is
        # aborted, a cancelled path, so no result: the stream ends with the error, or with `done` after a cancel.
        # A kept request stays for the next run, and this run's own joins it, so neither is lost.
        hold_request(ctx.state, node_input)
        ledger.pipeline_active = False
        return
    # Taken only once the run has its slot: a run that never starts leaves the user's note for the next one.
    node_input = take_pending_request(ctx.state, node_input)
    previous = (
        services.versions.latest_rendered(ctx.session.id, library=view.library)
        if node_input.base == "previous"
        else None
    )
    theme, theme_asked = run_theme(node_input.theme, ledger.site_theme, previous)
    run = Run(
        view=view,
        dataset=dataset,
        theme=theme,
        theme_asked=theme_asked,
        language=language or view.language,
        change_request=node_input.change_request,
        expected_texts=list(node_input.expected_texts),
        base=node_input.base,
    )
    started = time.monotonic()
    scope = f"pipeline-{secrets.token_hex(6)}"
    try:
        async for event in _attempts(ctx, services, settings, run, node_input, scope):
            yield event
    except Exception as exc:  # every failure ends in a PlotResult; the type is logged, never the message
        logger.warning("pipeline failed: %s", type(exc).__name__)
        busy = model_busy(exc)  # a quota or overload after the SDK's retries: try again shortly, not a fault
        run.reason = "busy" if busy else "error"
        # The innermost class, not ADK's `DynamicNodeFailError` around a sub-agent's failure (Flash review, 2026-11-01).
        run.error_type = type(error_chain(exc)[-1]).__name__
        run.unreviewed_why = run.unreviewed_why or (
            "the model service was busy" if busy else "an internal error stopped the run"
        )
        if len(run.stages) < run.attempts:
            _end_attempt(run, "error")
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
        result = PlotResult(
            status="failed", reason="error", attempts=round_number(run, run.attempts), rounds=list(run.rounds)
        )
        run.error_type = run.error_type or type(exc).__name__
        run.stage = "error"
    # From here on the root's closing reply is never the budget refusal (plugins/budget.py).
    ledger.plot_shipped = result.status in ("ok", "needs_attention")
    settle_pending_request(ctx.state, node_input, ledger.plot_shipped)
    _attribute_result(ledger, run, result)
    _telemetry_run(ledger, ctx.session.id, ctx.invocation_id, run, result, time.monotonic() - started)
    yield close_scope(scope)
    yield _result_event(result)


def _attribute_result(ledger: RequestLedger, run: Run, result: PlotResult) -> None:
    """The content-free outcome line of one pipeline run: what the eval harness's pass and gate counts read.

    `padded`, `adaptation` (ADAPTATION rule ids) and `advisory` (probe gate ids) describe
    the shipped render; a failed run has none. `texts` names the roles of the drawn texts
    `PlotShows.texts` reports for the shipped render (`title`, `x tick labels`, ...; role
    names only, never a text), or is None when its probe reported none, and `texts_expected`
    says whether the library's render reports them (`RuntimeAdapter.text_probe`): the eval
    harness counts a shipped run without texts where they are expected (`agents/evals/report.py`,
    `untexted`). `error` is the exception class behind
    reason `error` (for example `RendererUnavailable`, which the harness treats as an
    outage rather than a model failure) or `busy` (a `RateLimitError` or an `OverloadedError`),
    the innermost class of `models.error_chain`, never its message. `stage` names what stopped
    the run and `stages` what ended each attempt (`Stage`); `shipped_attempt` and
    `reviewed_attempt` name the attempt whose render shipped and the one the reviewer
    was last called on, and `reviews` counts the reviewer calls.
    """
    # The render that actually shipped: with `AGENT_SHIP_BEST` the best-ranked one, not always the last.
    shipped = shipped_candidate(run) if result.status in ("ok", "needs_attention") else None
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
        reviews=run.reviews,
        theme=run.theme,
        reviewed=run.reviewed,
        padded=bool(shipped and shipped.padded),
        adaptation=list(shipped.adaptation_rules) if shipped else [],
        advisory=list(shipped.advisory_gates) if shipped else [],
        texts=sorted(shipped.texts) if shipped and shipped.texts is not None else None,
        texts_expected=runtime_for(run.view.library).text_probe,
        residual=len(result.residual_defects),
        error=run.error_type if result.reason in ("error", "busy") else None,
    )


def _defect_ids(lines: Sequence[str]) -> list[str]:
    """The review ids of defect lines (`DEFECT_RE`); a line without the grammar names none."""
    return sorted({found for line in lines if (m := DEFECT_RE.match(line)) for found in m["ids"].split(", ")})


def _telemetry_run(
    ledger: RequestLedger, session_id: str, invocation_id: str, run: Run, result: PlotResult, seconds: float
) -> None:
    """The usage telemetry's `pipeline_run` line (`telemetry.py`): ids, buckets, counts and times, never text.

    One line per run: `run_index` is the session's run number for this invocation, so a node ADK re-runs
    writes the same idempotency key and the BigQuery base view keeps one row. The stages, rule ids and failure kinds
    are closed by `telemetry.closed`, `closed_list` and `closed_set` (`other` for an id the closed set does not know
    yet), so a new stage or rule never drops the line.
    """
    shipped = shipped_candidate(run) if result.status in ("ok", "needs_attention") else None
    index = telemetry.run_index(session_id, invocation_id)
    settings = get_settings()
    rule_ids = get_args(telemetry.ValidatorRule)
    stage_ids = get_args(telemetry.PipelineStage)
    telemetry.write(
        telemetry.PipelineRun,
        ledger,
        attempt=f"run{index}",
        run_index=index,
        base=run.base,
        status=result.status,
        reason=result.reason,
        stage=telemetry.closed(run.stage, stage_ids),
        attempts=run.attempts,  # every adapter call, retries and proofreads included; `rounds` is what the page shows
        rounds=len(run.rounds),
        reviews=run.reviews,
        score_round1=telemetry.score_bucket(run.round_scores.get(1)),
        score_round2=telemetry.score_bucket(run.round_scores.get(2)),
        shipped_attempt=shipped.attempt if shipped else None,
        shipped_round=round_number(run, shipped.attempt) if shipped else None,
        version=telemetry.version_number(result.version),
        shipped_score=telemetry.score_bucket(shipped.review_score) if shipped else None,
        forced_repair=sorted(run.forced_ids),
        gates_failed=sorted(run.gate_ids),
        reviewer_defects=sorted(run.review_ids),
        residual_defects=_defect_ids(result.residual_defects),
        sandbox_failures=sorted(run.sandbox_failures),
        drift_restored=run.drift_restored,
        stages=telemetry.closed_list(run.stages, stage_ids),
        round_scores=_round_scores(run),
        plot_language=telemetry.plot_language(run.language),
        readiness=telemetry.readiness(run.view.readiness),
        loader_notes=list(run.loader_codes),
        edit_failures=telemetry.closed_set(run.edit_failures, get_args(telemetry.EditFailure)),
        validator_rules=telemetry.closed_set(run.validator_rules, rule_ids),
        adaptation_rules=telemetry.closed_set(run.adaptation_rules, rule_ids),
        reviewer_mode=settings.reviewer_mode,
        ship_best=settings.ship_best,
        self_review=settings.self_review,
        repair_self_review=settings.repair_self_review,
        **_prompt_hashes(run.view.library, settings.reviewer_mode),
        adapt_ms=telemetry.ms(run.stage_s.get("adapt", 0.0)),
        check_ms=telemetry.ms(run.stage_s.get("check", 0.0)),
        render_ms=telemetry.ms(run.stage_s.get("render", 0.0)),
        review_ms=telemetry.ms(run.stage_s.get("review", 0.0)),
        total_ms=telemetry.ms(seconds),
        steps=telemetry.step_tokens(ledger.steps, steps=("adapter", "reviewer")),
        # Whether anyone waits long or comes close to a limit (owner, 2026-11-01): buckets and bounded numbers of
        # the queue and the usage book, never the user they were counted for.
        lane=ledger.tier,
        queue_wait_ms=telemetry.ms(ledger.queue_wait_s) if ledger.queue_wait_s is not None else None,
        queue_position=ledger.queue_position,
        user_runs_today=telemetry.runs_today_bucket(ledger.user_runs_today),
        user_tokens_today=telemetry.tokens_today_bucket(ledger.user_tokens_share),
    )


def _round_scores(run: Run) -> list[str]:
    """The bucket of every round's latest review score, round 1 first, `unscored` for a round without one; up to the
    last round that ended or was scored, so position `n - 1` is round `n`."""
    last = max(len(run.rounds), max(run.round_scores, default=0))
    return [telemetry.score_bucket(run.round_scores.get(number)) or "unscored" for number in range(1, last + 1)]


def _prompt_hashes(library: str, reviewer_mode: str) -> dict[str, str]:
    """The hashes of the run's adapter and reviewer instructions (`policy.prompt_hash`), as the telemetry line's
    `adapter_prompt` and `reviewer_prompt`; none when an instruction cannot be built, since telemetry never breaks
    a run."""
    try:
        return {
            "adapter_prompt": prompt_hash(adapter_instruction(library)),
            "reviewer_prompt": prompt_hash(REVIEWER_MODES[reviewer_mode]["instruction"]()),
        }
    except Exception as exc:
        logger.warning("telemetry prompt hashes skipped: %s", type(exc).__name__)
        return {}


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
    runtime = runtime_for(view.library, cpu_seconds=settings.render_timeout_s)
    deadline = SoftDeadline(settings.soft_deadline_s)
    previous = (
        services.versions.latest_rendered(ctx.session.id, library=view.library) if args.base == "previous" else None
    )
    working = previous.working if previous is not None else view.normalised
    # What the user asked of the base version's lineage stands: every adapter call and the reviewer see it.
    run.user_requests = standing_requests(previous.requests) if previous is not None else []
    # The base version's text is in another language than the plot language (the user asked for another one since,
    # maybe in another library): the adapter rewrites it.
    language_changed = previous is not None and not same_language(previous.language, run.language)
    # A change on a previous version adds a little text; adapting the catalogue code renames much. A change
    # that rewrites the text in another language keeps the change's budget plus the text it replaces (`_check`).
    budget = MAX_CHANGE_LITERAL_CHARS if previous is not None else MAX_NEW_LITERAL_CHARS
    data_texts = _data_texts(dataset.csv)
    regions = runtime.regions(view.normalised)
    palette = list(regions.imprint.entries) if regions.imprint else []
    hints = view.hints[:MAX_NOTES] if previous is None else []
    columns = [column.name for column in dataset.profile.columns]
    kinds = column_kinds_of(dataset)
    run.loader_notes = runtime.loader_notes(kinds) if kinds is not None else []
    run.loader_codes = loader_codes(runtime, kinds)
    try:
        run.data_json = runtime.data_json(dataset.csv, kinds)
    except ValueError:
        # A cell the typed table cannot hold: without the kinds the loader refuses the run form and says why.
        kinds = None
    feedback: list[str] = []
    previous_plan: AdaptPlan | None = None
    rows = data_rows(dataset.csv)
    # The screened notes pasted with the data and where a computed table comes from, for the title and labels.
    context = dataset_context(dataset.context_lines, dataset.source)
    # A dropped file's name travels apart from the notes, fenced as data under its own heading.
    file_name = file_name_for_models(dataset.file_name)

    adapter = adapter_name(view.library)
    # A round is one adapter attempt and, with `AGENT_SELF_REVIEW`, the adapter proofreading its render
    # once before the review, and with `AGENT_CHECK_RETRY` one more call when an answer fails its check:
    # neither is a repair or a round of its own (owner, 2026-10-13), so a run has at most
    # `AGENT_MAX_ATTEMPTS` rounds and up to three adapter calls per round.
    rounds = settings.max_attempts
    calls = rounds * (1 + int(settings.self_review) + int(settings.check_retry))
    # Ship the best-scored version (`AGENT_SHIP_BEST`, catalogue reviews only): every round is reviewed.
    max_reviews = rounds if ship_best(settings) else MAX_REVIEWS

    for attempt in range(1, calls + 1):
        if round_number(run, attempt) > rounds:
            break
        # The proofread, or its retry after a failed check, is this round's last adapter call.
        proofreading = round_number(run, attempt) in run.proofread_rounds
        # A repair round proofreads only with `AGENT_REPAIR_SELF_REVIEW`: the review re-checks it anyway.
        self_review_due = (
            settings.self_review
            and not proofreading
            and (round_number(run, attempt) == 1 or settings.repair_self_review)
        )
        # This call and the root's closing reply: a plot may ship from any attempt, and ADK's
        # call cap would refuse the reply the Budget plugin's exemption cannot admit.
        if not budget_allows(ledger, services.usage, settings, next_calls=2):
            run.reason, run.unreviewed_why, run.stage = "budget", "the usage limit was reached", "budget"
            return
        if attempt > 1 and not deadline.allows(ADAPTER_P95_S + runtime.render_p95_s):
            run.reason, run.unreviewed_why, run.stage = "deadline", "the time limit was reached", "deadline"
            return
        run.attempts = attempt
        if round_number(run, attempt) == 1:
            yield _status(run, "adapting", attempt)
        elif proofreading:
            # Proofreading a repair is still that round's repairing step on the page.
            yield _status(run, "repairing", attempt)
        else:
            yield _status(run, "repairing", attempt, run.rounds[-1] if run.rounds else None)
        request = AdaptRequest(
            code=working,
            profile=dataset.profile,
            bindings=view.bindings,
            loader_columns=columns,
            hints=_repair_hints(hints, run) if round_number(run, attempt) > 1 else hints,
            change_request=args.change_request,
            user_requests=run.user_requests,
            feedback=_clip_feedback(feedback),
            previous_plan=previous_plan,
            allow_full=attempt >= 2,
            plot_language=run.language,
            language_changed=language_changed,
            # The notes explain the plot to the user, so they follow the language the user chats in.
            reply_language=None if same_language(view.language, run.language) else view.language,
            expected_texts=run.expected_texts,
            dataset_context=context,
            file_name=file_name,
        )
        ledger.adapter_allow_full = request.allow_full
        started = time.monotonic()
        answer = await _adapt(ctx, scope, render_adapt_request(request, view), view.library)
        run.timed("adapt", time.monotonic() - started)
        call = _call_fields(ledger, adapter)
        if isinstance(answer, AdaptMiss):
            attribution("pipeline_adapt", ledger, attempt=attempt, outcome=answer.outcome, **call)
            feedback, previous_plan = [answer.line], None
            _end_attempt(run, answer.stage, feedback)
            continue
        plan = answer
        if plan.full_code is not None and not request.allow_full:
            attribution("pipeline_adapt", ledger, attempt=attempt, outcome="full_code_refused", **call)
            feedback, previous_plan = [FULL_CODE_REFUSED_LINE], None
            _end_attempt(run, "adapter_full_code", feedback)
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

        yield _status(run, "checking", attempt)
        started = time.monotonic()
        applied = runtime.apply_plan(working, plan)
        # Drift of the protected theme statements alone, once the round's retry is spent: put the base's
        # statements back and check the rest as usual (owner decision, 2026-10-16), instead of ending the round.
        restored = (
            runtime.restore_protected(working, applied.drifted)
            if applied.code is None and applied.drifted is not None and not _retry_left(run)
            else None
        )
        if restored is not None:
            run.drift_restored = True
        code = applied.code if applied.code is not None else restored
        if code is None:
            run.timed("check", time.monotonic() - started)
            run.edit_failures.update(applied.kinds)
            attribution(
                "pipeline_check",
                ledger,
                attempt=attempt,
                outcome="edits_failed",
                edit_failures=len(applied.failures),
                edit_failure_kinds=dict(sorted(Counter(applied.kinds).items())),
                edit_tolerant=dict(sorted(Counter(applied.tolerant).items())),
            )
            feedback, previous_plan = applied.failures, plan
            _end_attempt(run, "edit_apply", feedback)
            continue
        check = _check(
            code,
            library=view.library,
            palette=palette,
            base=working,
            literal_budget=budget,
            rewrite=language_changed,
            origin=view.normalised,
            data_texts=data_texts,
            runtime=runtime,
        )
        run.timed("check", time.monotonic() - started)
        run.validator_rules.update(check.blocking_rules)
        run.adaptation_rules.update(check.adaptation_rules)
        adaptation_lines = check.defects
        # A restored plan is logged once, by the drift kinds it had: `drift_restored`, or `rejected` when the
        # restored code then failed the validator.
        drift_fields = {"drift_restored": dict(sorted(Counter(applied.kinds).items()))} if restored is not None else {}
        attribution(
            "pipeline_check",
            ledger,
            attempt=attempt,
            outcome=("drift_restored" if restored is not None else "ok") if check.may_render else "rejected",
            edit_failures=0,
            edit_tolerant=dict(sorted(Counter(applied.tolerant).items())),
            validator=check.blocking_rules,
            banned_imports=check.banned_imports,
            adaptation=check.adaptation_rules,
            **drift_fields,
        )
        if not check.may_render:
            feedback, previous_plan = check.blocking, plan
            _end_attempt(run, "validator", feedback)
            continue
        note_changes(run, plan, changed=code != working, proofread=proofreading)
        working, previous_plan = code, None
        try:
            run_form = runtime.loader_block(
                runtime.normalise(working, view.library),
                columns=columns,
                dtypes=dict(dataset.column_dtypes),
                parse_dates=list(dataset.parse_dates),
                kinds=dict(kinds.kinds) if kinds is not None else {},
            )
        except ValueError as exc:
            attribution("pipeline_check", ledger, attempt=attempt, outcome="loader_failed", edit_failures=0)
            feedback = [_line(f"the code could not take the data loader: {exc}")]
            _end_attempt(run, "loader", feedback)
            continue

        yield _status(run, "rendering", attempt)
        job = RenderJob(
            job_id=secrets.token_hex(8),
            language=runtime.language,
            library=view.library,
            source=run_form,
            data_csv=dataset.csv,
            themes=(run.theme,),
            timeout_s=deadline.clamp(settings.render_timeout_s),
            data_json=run.data_json,
        )
        started = time.monotonic()
        rendered = await services.backend.render(job)
        render_s = time.monotonic() - started
        run.timed("render", render_s)
        # The gates decode and scan the PNGs, CPU work of up to a second: in a worker thread, so the other runs in
        # flight (five in the admin lane) keep streaming meanwhile, as the watermark does (`main._served_png`).
        report = await asyncio.to_thread(
            evaluate,
            rendered,
            themes=job.themes,
            library=view.library,
            rows=rows,
            plot_language=run.language,
            # The adapter edits the working form: a runtime whose loader shifts the lines maps them back.
            summarise=functools.partial(runtime.error_summary, run_form=run_form),
        )
        run.gate_ids.update(report.failed_gates)
        for theme_output in rendered.outputs.values():
            failure = telemetry.sandbox_failure(theme_output)
            if failure is not None:
                run.sandbox_failures.add(failure)
        if report.passed_host_gates:
            run.repair_hints = list(report.repair_hints)
        attribution(
            "pipeline_render",
            ledger,
            attempt=attempt,
            theme=run.theme,
            render_s=round(render_s, 3),
            slot_wait_s=round(rendered.slot_wait_s, 3),
            wall_s={theme: round(output.wall_s, 3) for theme, output in rendered.outputs.items()},
            passed=report.passed_host_gates,
            canvas_ok=report.canvas_ok,
            gates=report.failed_gates,
            # A probe that failed names its class (a text probe drops its labels then): the log of a best-effort step.
            probe_error=probe_error(probed.probe) if (probed := rendered.outputs.get(run.theme)) is not None else None,
        )
        run.rendered = True
        if not report.passed_host_gates:
            feedback = [*report.blocking, *adaptation_lines]
            _end_attempt(run, "render", feedback)
            continue
        output = rendered.outputs.get(run.theme)
        # `shows` gets the clipped summary of every drawn text the probe reports.
        drawn = drawn_texts(output.probe if output is not None else None)
        texts = plot_texts(drawn)
        checking = settings.expect_check != "off" and bool(run.expected_texts)
        # The requested texts are checked against matplotlib's drawn texts; where the runtime's reviewer checks them
        # (`review_texts`: every library without matplotlib), its probe's texts ground the reply alone.
        measured_texts = None if runtime.review_texts else drawn
        misses = expected_misses(run.expected_texts, measured_texts) if checking else []
        expect_lines = [miss.line(run.theme) for miss in misses]
        # No drawn texts to check against: a note, never a pass. Where the runtime says so, the review finds the texts
        # in the image instead, and only its answer lifts the note.
        unverified = checking and measured_texts is None
        expect_note = UNVERIFIED_LINE.format(theme=run.theme) if unverified else None
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
            changes=list(run.changes),
            texts=texts,
            expect_lines=expect_lines,
            expect_misses=[miss.expected for miss in misses],
            expect_note=expect_note,
            expect_review=unverified and runtime.review_texts,
        )
        if report.canvas_ok:
            run.best = candidate
        else:
            run.padded = candidate
        # A requested text the render does not show is measured like a gate line (`AGENT_EXPECT_CHECK=repair`).
        repair_expect = expect_lines if settings.expect_check == "repair" else []
        feedback = [*report.defects, *adaptation_lines, *repair_expect]
        # The render's measured findings: what the code, not a model, found in it.
        measured = [*report.advisory, *adaptation_lines, *repair_expect]
        # A missed canvas always goes to the next attempt before any review. With
        # `AGENT_GATE_REPAIR=first` the measured findings do too while an attempt is allowed;
        # with `review` they go to the self-review and the review, and a round whose render
        # still has them after the review is repaired with them (below). A render is reviewed
        # again after a rejection, up to the review limit.
        gates_first = settings.gate_repair == "first"
        if not report.canvas_ok or (gates_first and feedback and round_number(run, attempt) < rounds):
            _end_attempt(run, "gates", feedback)
            continue
        if self_review_due and attempt < calls:
            # The adapter proofreads its render once per round before the review: after the first
            # version, and after a repair with that repair's findings, to see whether its changes worked.
            run.self_reviewed = True
            run.proofread_rounds.add(round_number(run, attempt))
            current = services.renders.put(ctx.session.id, candidate.pngs)
            before = run.reviewed_render_id if settings.repair_sees_render and round_number(run, attempt) > 1 else None
            ledger.adapter_renders = [
                *([("Render before your repair, which the review's findings describe", before)] if before else []),
                ("Render of the current code" + (", after your repair" if before else ""), current),
            ]
            round_findings = [line for line in request.feedback if not line.startswith("Self-review:")]
            feedback = [
                SELF_REVIEW_LINE,
                *([SELF_REVIEW_HIGHLIGHT_LINE] if settings.highlights == "data" else []),
                # This render's measured findings first: they are facts of the image the adapter sees.
                *([MEASURED_LINE, *measured] if measured and not gates_first else []),
                *round_findings,
            ]
            _end_attempt(run, "self_review", feedback)
            continue
        if run.reviews >= max_reviews:
            # Every review used, and either no feedback or no attempt left for it: the run ends
            # here, since another attempt would have nothing to repair.
            _end_attempt(run, "not_rereviewed")
            return

        if not budget_allows(ledger, services.usage, settings, next_calls=2, reserve=REVIEW_RESERVE_TOKENS):
            run.unreviewed_why = "the usage limit was reached"
            _end_attempt(run, "budget")
            return
        if not deadline.allows(REVIEWER_P95_S):
            run.unreviewed_why = "the time limit was reached"
            _end_attempt(run, "deadline")
            return
        yield _status(run, "reviewing", attempt)
        candidate.render_id = services.renders.put(ctx.session.id, candidate.pngs)
        ledger.review_render_id = candidate.render_id
        run.reviewed_attempt = attempt
        run.reviews += 1
        review_request = ReviewRequest(
            render_id=ledger.review_render_id,
            code=run_form,
            bindings=view.bindings,
            profile_summary=profile_summary(dataset.profile),
            spec_brief=spec_brief(view),
            change_request=args.change_request,
            user_requests=run.user_requests,
            # Every measured finding, the ADAPTATION ones too, so the review sees what the repair will get.
            gate_notes=[_note(line) for line in measured][:MAX_NOTES],
            plot_language=run.language,
            dataset_context=context,
            file_name=file_name,
            expected_texts=run.expected_texts if candidate.expect_review else [],
        )
        started = time.monotonic()
        verdict = await _review(ctx, scope, review_request, run.theme)
        run.timed("review", time.monotonic() - started)
        if verdict is None and settings.check_retry and deadline.allows(REVIEWER_P95_S):
            # An unreadable review is asked once more before the render ships unreviewed (owner rule:
            # never unfinished for a formal miss; one in 26 Vertex runs on 2026-10-14).
            attribution(
                "pipeline_review",
                ledger,
                attempt=attempt,
                verdict="unreadable_retry",
                **_call_fields(ledger, REVIEWER_NAME),
            )
            started = time.monotonic()
            verdict = await _review(ctx, scope, review_request, run.theme)
            run.timed("review", time.monotonic() - started)
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
            defects=verdict.ids,
            **({"score": verdict.score, "technical": verdict.technical} if verdict.score is not None else {}),
            **review_call,
        )
        run.reviewed = True
        run.review_ids.update(verdict.ids)
        run.forced_ids.update(set(_defect_ids(verdict.visible)) & VISIBLE_DEFECT_IDS)
        if verdict.score is not None:
            run.round_scores[round_number(run, attempt)] = verdict.score
        candidate.reviewed_ok = verdict.ok
        candidate.status_ok = verdict.ok if verdict.status_ok is None else verdict.status_ok
        candidate.review_score = verdict.score
        candidate.review_lines = [] if verdict.ok and candidate.status_ok else list(verdict.lines)
        candidate.visible_lines = list(verdict.visible)
        if candidate.expect_review:
            # The review answered for the requested texts: the ones it could not find stay, with its own lines, as a
            # measured miss does (residual, not clean), and no unverified note is left.
            candidate.expect_lines = list(dict.fromkeys(line for _, line in verdict.requested))
            candidate.expect_misses = [text for text, _ in verdict.requested]
            candidate.expect_note = None
        if verdict.score is not None and (run.best_scored is None or ship_compare(candidate, run.best_scored) >= 0):
            run.best_scored = candidate
        # The latest review's lines only: a passing review clears an earlier round's, so a later
        # unreviewed render never ships with notes that describe another render.
        run.review_lines = [] if verdict.ok else list(verdict.lines)
        # A measured finding the review passed over still gets the repair (`AGENT_GATE_REPAIR=review`):
        # a measurement is code, not a verdict, so no review score waives it.
        open_measured = [] if gates_first else measured
        if verdict.ok and not (open_measured and round_number(run, attempt) < rounds):
            _end_attempt(run, "reviewer_ok")
            return
        # The review passed but measured findings are left: the repair gets those alone.
        feedback = [*open_measured, *run.review_lines]
        run.reviewed_render_id = candidate.render_id
        if settings.repair_sees_render and candidate.render_id:
            # The repair sees the render its findings describe (`AGENT_REPAIR_SEES_RENDER`).
            what = "the server's measurements" if verdict.ok else "the review's findings"
            ledger.adapter_renders = [(f"Render {what} describe, before your repair", candidate.render_id)]
        _end_attempt(run, "gates" if verdict.ok else "reviewer_defects", feedback)


def _on_theme(defect: Defect, theme: Theme) -> Defect:
    """The reviewer saw one theme: an image defect names it, even when the reviewer wrote `both` or the other one."""
    return defect if defect.theme in ("code", theme) else defect.model_copy(update={"theme": theme})


def _note(line: str) -> str:
    return line if len(line) <= MAX_NOTE_CHARS else line[: MAX_NOTE_CHARS - 1] + "…"
