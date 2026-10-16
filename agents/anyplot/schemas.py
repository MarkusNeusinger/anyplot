"""Pydantic contracts of the plot pipeline (docs/concepts/agent-network.md, "Contracts").

The limits are part of the contract: a value outside them is a validation error
where it enters, never a silent truncation further down. Two families:

* Server-built values and tool inputs (`ColumnProfile`, `DatasetProfile`, `Binding`,
  `PipelineArgs`, `AdaptRequest`, `ReviewRequest`, `PlotResult`) forbid unknown
  fields, so neither a model nor an injected string can add a spec, library or
  dataset field to a pipeline call.
* Model outputs written under a response schema (`Edit`, `AdaptPlan`, `Defect`,
  `Verdict`) ignore unknown fields, so a stray key never fails a whole adapter or
  reviewer call; only the declared fields are ever read.

Lengths are counted in characters (`24 KiB` is 24,576 characters). Rules that need
more than one value from outside the model, such as "`find` matches the working
form exactly once" or "`full_code` only from attempt 2 on", belong to the code that
holds that context (the edit applier and the pipeline), not to these schemas.

A model answer that misses a purely formal rule is mended rather than discarded:
`repair_verdict` and `repair_plan` clip a text to its limit, keep the allowed number
of items and derive a verdict's `ok` from its defects. `sub_agents/adapter.schema_guard`
runs them only after the strict check failed, validates the result against the same
strict schema and logs which rule each miss broke, so no repair is silent. Nothing
that carries meaning is repaired: an edit stays exactly as the model wrote it, and a
verdict that rejects without a usable defect stays unread.
"""

import json
import re
import unicodedata
from collections.abc import Iterable
from typing import Annotated, Any, Literal, Self, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    TypeAdapter,
    ValidationInfo,
    field_validator,
    model_validator,
)

from .language import DEFAULT_LANGUAGE, LANGUAGE_PATTERN


# Limits from the design doc, named once so the parser, the tools and the tests share them.
MAX_ROWS = 20_000
MAX_COLUMNS = 50
MAX_COLUMN_NAME_CHARS = 64
MAX_CELL_CHARS = 40
MAX_SAMPLE_ROWS = 5
MAX_TOP_VALUES = 5
MAX_LISTED_VALUES = 12
"""A text or boolean column with at most this many distinct values lists every one of them in its profile's `top`
(`listed_values`); a column with more lists its `MAX_TOP_VALUES` most frequent. Live test round 8 of 2026-10-16:
the profile of a six-row energy mix listed five sources, the root never saw `Übrige` and told the user the plot
had added it to fill the ring."""
MAX_CHANGE_REQUEST_CHARS = 600
MAX_USER_REQUESTS = 8
"""Earlier change requests of a plot's lineage that a change run carries as the user's standing decisions."""
MAX_USER_REQUESTS_CHARS = 2_400
"""Their characters together: the most recent ones are kept within it (four requests at the 600-character cap)."""
MAX_EDITS = 20
MAX_FULL_CODE_CHARS = 24 * 1024
MAX_TITLE_CHARS = 120
MAX_CHANGES = 5
MAX_DEFECTS = 5
# Limits the design doc leaves open, decided here.
MAX_CODE_CHARS = 48 * 1024  # the SECURITY validator parses at most 48 KB
MAX_EDIT_CHARS = 8 * 1024  # per `find` or `replace`; a whole edit call is capped at 8,192 output tokens
MAX_WARNINGS = 2 * MAX_COLUMNS  # a rename and a date-order warning per column
MAX_NOTES = 20  # readiness hints, gate notes
MAX_FEEDBACK = 16  # defect and validator lines handed to the next repair attempt
MAX_ATTEMPTS = 3  # the most adapter attempts a run may make; `AGENT_MAX_ATTEMPTS` is 1 to this, 2 by default
MAX_RESIDUAL_DEFECTS = 16  # 5 reviewer lines, 6 advisory probe gates, canvas padding, adaptation findings
MAX_NOTE_CHARS = 300
MAX_CHANGE_CHARS = 200
MAX_MESSAGE_CHARS = 2_000
"""The longest chat message the `/v1` route takes, and the longest the notes pasted with a table
(`ParsedDataset.context_lines`, all lines together) may be: they reach the root as user text too."""
MAX_DEFECT_TEXT_CHARS = 200
# Every rendered defect line is also a feedback or residual `Line`, so a `Line` must hold
# the longest `Defect.as_line()`: three texts of 200 characters plus 35 of grammar.
MAX_LINE_CHARS = 640

ColumnName = Annotated[str, Field(min_length=1, max_length=MAX_COLUMN_NAME_CHARS)]
Cell = Annotated[str, Field(max_length=MAX_CELL_CHARS)]
Note = Annotated[str, Field(min_length=1, max_length=MAX_NOTE_CHARS)]
Line = Annotated[str, Field(min_length=1, max_length=MAX_LINE_CHARS)]
ChangeNote = Annotated[str, Field(min_length=1, max_length=MAX_CHANGE_CHARS)]
UserRequest = Annotated[str, Field(min_length=1, max_length=MAX_CHANGE_REQUEST_CHARS)]
DefectText = Annotated[str, Field(min_length=1, max_length=MAX_DEFECT_TEXT_CHARS)]
MAX_EXPECTED_TEXTS = 5
MAX_EXPECTED_TEXT_CHARS = 120


def _visible_text(text: str) -> str:
    """An expected text holds something to find in the render: not only whitespace, no control character."""
    if not text.strip():
        raise ValueError("an expected text is not only whitespace")
    if any(unicodedata.category(char) == "Cc" for char in text):
        raise ValueError("an expected text has no control character")
    return text


ExpectedText = Annotated[str, Field(min_length=1, max_length=MAX_EXPECTED_TEXT_CHARS), AfterValidator(_visible_text)]
EXPECTED_TEXTS: TypeAdapter[list[ExpectedText]] = TypeAdapter(list[ExpectedText])
"""Validates `expected_texts` read back from session state the way `PipelineArgs` validates them from the root."""
EXPECTED_TEXT: TypeAdapter[ExpectedText] = TypeAdapter(ExpectedText)
MAX_DATASET_CONTEXT_CHARS = 1_600
"""The dataset context block (`dataset_context.MAX_CONTEXT_CHARS`, 1,500) with room to spare."""
MAX_FILE_NAME_CHARS = 80
"""A dropped file's name as the session keeps it (`opening.source_name` cuts it to this)."""
MAX_SHOWN_TEXT_CHARS = 80
"""One drawn text in `PlotShows.texts`."""

ColumnDtype = Literal["integer", "number", "datetime", "boolean", "text"]
SourceFormat = Literal[
    "csv",
    "tsv",
    "semicolon",
    "pipe",
    "whitespace",
    "json_records",
    "json_lines",
    "json_columns",
    "json_pairs",
    "json_stat",
]

# The reviewer's reduced checklist: the rubric criteria it scores plus AR-09 for clipping.
DefectId = Literal["VQ-01", "VQ-02", "VQ-03", "VQ-06", "VQ-07", "SC-01", "SC-03", "SC-04", "DQ-03", "AR-09"]
DefectTheme = Literal["light", "dark", "both", "code"]
Theme = Literal["light", "dark"]
"""A render theme; `render/contract.py` re-exports it with the `THEMES` order."""

PlotStatus = Literal["ok", "needs_attention", "failed", "not_ready"]
FailureReason = Literal["validation", "render", "deadline", "budget", "error"]
NotReadyReason = Literal["no_dataset", "incomplete_bindings", "data_unconfirmed"]
"""`data_unconfirmed`: the dataset and its bindings are there, but the user has not confirmed
them in the data panel yet (step 1 of two, owner rule of 2026-10-11)."""
ArtifactName = Literal["plot-light.png", "plot-dark.png", "plot.py", "data.csv"]

FAILURE_REASONS: frozenset[str] = frozenset(get_args(FailureReason))
NOT_READY_REASONS: frozenset[str] = frozenset(get_args(NotReadyReason))
PNG_ARTIFACTS: dict[str, ArtifactName] = {"light": "plot-light.png", "dark": "plot-dark.png"}
"""The PNG artifact of each theme, in the order artifacts are listed."""


def artifact_names(themes: Iterable[str]) -> list[ArtifactName]:
    """A version's artifacts: the PNG of every rendered theme (light first), then `plot.py` and `data.csv`."""
    rendered = set(themes)
    names: list[ArtifactName] = [name for theme, name in PNG_ARTIFACTS.items() if theme in rendered]
    code_and_data: list[ArtifactName] = ["plot.py", "data.csv"]
    return names + code_and_data


# A role is matched against the spec's `## Data` bullets later; the pattern only keeps
# arbitrary text out. Digits and capitals are allowed because 21 of 325 specs name
# roles such as `log2_fold_change`, `lower_95` or `temperature_K`.
ROLE_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]{0,31}$"
RENDER_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"

_WHITESPACE = re.compile(r"\s+")
ELLIPSIS = "…"


def _defect_text(text: str, field_name: str) -> str:
    """A defect text on one line; in `observed`, an arrow becomes `->` (the first `→` starts the target)."""
    text = _WHITESPACE.sub(" ", text).strip()
    return text.replace("→", "->") if field_name == "observed" else text


def _clip(text: str, limit: int) -> str:
    """`text` cut to at most `limit` characters, the last of them an ellipsis when it was longer."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + ELLIPSIS


class _ServerContract(BaseModel):
    """Built by the server or validated tool input: unknown fields are an error."""

    model_config = ConfigDict(extra="forbid")


class _ModelOutput(BaseModel):
    """Written by a model under a response schema: unknown fields are dropped."""

    model_config = ConfigDict(extra="ignore")


# --- Parse -----------------------------------------------------------------------------


class ColumnProfile(_ServerContract):
    """One column of the pasted dataset, as the deterministic parser profiled it.

    `mean` and `median` are set for integer and number columns only (six significant
    digits), so the root can say what a column holds, such as values that sum to 100.
    The rounding is for the model only: the page never shows them, and `data.csv` keeps
    every value (owner decision of 2026-10-15). An integer column's `min` and `max` are
    exact; past 2^53 the browser's float64 numbers lose their last digits, which only
    touches the binding hint that names a negative minimum (kept, owner decision).

    `months` is set for a text column whose every cell names a month (`Jan`, `März`;
    `data/months.named_months`): the months it holds, 1 to 12 ascending, so the root states
    the range from them and not from the five `top` values (live test round 4 of
    2026-10-15: "Jan bis Mai" for a column of Jan to Jun).

    `top` holds a text or boolean column's values by frequency: every distinct value when
    the column has at most `MAX_LISTED_VALUES` of them, otherwise the `MAX_TOP_VALUES`
    most frequent (`listed_values`), so `unique` above the number listed says the list is
    partial. A profile cut to fit a cap (`briefs.trimmed_profiles`) may list fewer.
    """

    name: ColumnName
    dtype: ColumnDtype
    missing: NonNegativeInt
    unique: NonNegativeInt
    min: int | float | Cell | None = None  # an integer column's exactly: a float rounds past 2**53
    max: int | float | Cell | None = None
    mean: float | None = None
    median: float | None = None
    top: list[Cell] = Field(default_factory=list, max_length=MAX_LISTED_VALUES)
    months: list[Annotated[int, Field(ge=1, le=12)]] | None = Field(default=None, max_length=12)


def listed_values(distinct: int) -> int:
    """How many values a column with `distinct` distinct values lists in `ColumnProfile.top`: all of them up to
    `MAX_LISTED_VALUES`, else `MAX_TOP_VALUES`."""
    return distinct if distinct <= MAX_LISTED_VALUES else MAX_TOP_VALUES


class DatasetProfile(_ServerContract):
    """What the root and the adapter learn about the dataset; never the raw data.

    The sample rows are rendered inside a `<user_data>` fence by the tool layer,
    which escapes the delimiters; the schema only bounds their size.

    `list_columns` is set when the paste was JSON records whose list fields expanded into
    one row per value (`data/parse._records`): the columns that came from those lists, the
    points of each record's curve. Every other column holds one value per record, a
    parameter or a label of the curve (live test round 4 of 2026-10-15: three curves'
    `temperatur_c` went to x). `data/bindings.py` reads it; a re-parse of a later version
    (`prepare_data`) does not know it and leaves it unset, while the bindings carry over.
    """

    rows: int = Field(ge=1, le=MAX_ROWS)
    columns: list[ColumnProfile] = Field(min_length=1, max_length=MAX_COLUMNS)
    sample: list[Annotated[list[Cell], Field(max_length=MAX_COLUMNS)]] = Field(
        default_factory=list, max_length=MAX_SAMPLE_ROWS
    )
    source_format: SourceFormat
    decimal: Literal[".", ","] = "."
    warnings: list[Note] = Field(default_factory=list, max_length=MAX_WARNINGS)
    list_columns: list[ColumnName] | None = Field(default=None, max_length=MAX_COLUMNS)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        names = [column.name for column in self.columns]
        if len(set(names)) != len(names):
            raise ValueError("column names must be unique")
        for row in self.sample:
            if len(row) != len(names):
                raise ValueError(f"every sample row needs {len(names)} cells, one per column")
        if len(self.sample) > self.rows:
            raise ValueError("the sample cannot have more rows than the dataset")
        return self


class Binding(_ServerContract):
    """A spec data role bound to one dataset column."""

    role: str = Field(pattern=ROLE_PATTERN)
    column: ColumnName


# --- Adapt -----------------------------------------------------------------------------


class PipelineArgs(_ServerContract):
    """The `plot_pipeline` tool input. Spec, library and dataset come from server state.

    `theme` is the one theme the run renders and the reviewer sees. Omitted (None), a
    change on `base="previous"` keeps the previous version's theme and a new plot is
    light; the root passes `dark` only when the user asks for a dark plot. The other
    theme of a finished version is rendered on demand by the theme toggle route,
    without any model call.
    """

    change_request: str = Field(default="", max_length=MAX_CHANGE_REQUEST_CHARS)
    base: Literal["catalogue", "previous"] = "catalogue"
    theme: Theme | None = None
    expected_texts: list[ExpectedText] = Field(default_factory=list, max_length=MAX_EXPECTED_TEXTS)
    """The texts and number formats the user asked to see in the plot, verbatim (a title they wrote out, a unit,
    a format example such as `6,5 Mio.`): the pipeline checks the render's drawn texts for each (`grounding.py`)."""


class KeepRequestArgs(_ServerContract):
    """The `keep_plot_request` tool input: a request for the first plot, kept without running anything.

    Live round 9 of 2026-10-16: a title asked for before `.confirm()`, and a plot wish in the pasted notes,
    reached no plot, because the bare `.create_plot()` carries no request. The tool stores it as the kept note
    (`pipeline.hold_request`) that the next first-plot run takes.
    """

    change_request: str = Field(default="", max_length=MAX_CHANGE_REQUEST_CHARS)
    expected_texts: list[ExpectedText] = Field(default_factory=list, max_length=MAX_EXPECTED_TEXTS)

    @model_validator(mode="after")
    def _something_to_keep(self) -> Self:
        if not self.change_request.strip() and not self.expected_texts:
            raise ValueError("a kept request needs a change_request or expected_texts")
        return self


class Edit(_ModelOutput):
    """One search-and-replace hunk; the applier requires exactly one match of `find`."""

    find: str = Field(min_length=1, max_length=MAX_EDIT_CHARS)
    replace: str = Field(max_length=MAX_EDIT_CHARS)


class AdaptPlan(_ModelOutput):
    """The adapter's answer: edits to the working form, or a full file from attempt 2 on."""

    edits: list[Edit] = Field(default_factory=list, max_length=MAX_EDITS)
    full_code: str | None = Field(default=None, min_length=1, max_length=MAX_FULL_CODE_CHARS)
    title: str = Field(default="", max_length=MAX_TITLE_CHARS)
    changes: list[ChangeNote] = Field(default_factory=list, max_length=MAX_CHANGES)

    @model_validator(mode="after")
    def _edits_or_full_code(self) -> Self:
        if self.full_code is not None and self.edits:
            raise ValueError("a plan carries edits or full_code, never both")
        return self


class AdaptRequest(_ServerContract):
    """Everything one adapter call sees, assembled by the pipeline from server state."""

    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)
    profile: DatasetProfile
    bindings: list[Binding] = Field(max_length=MAX_COLUMNS)
    loader_columns: list[ColumnName] = Field(max_length=MAX_COLUMNS)
    hints: list[Note] = Field(default_factory=list, max_length=MAX_NOTES)
    change_request: str = Field(default="", max_length=MAX_CHANGE_REQUEST_CHARS)
    user_requests: list[UserRequest] = Field(default_factory=list, max_length=MAX_USER_REQUESTS)
    """The earlier change requests the base version carries out, oldest first: the user's standing decisions."""
    feedback: list[Line] = Field(default_factory=list, max_length=MAX_FEEDBACK)
    previous_plan: AdaptPlan | None = None
    allow_full: bool = False
    plot_language: str = Field(default=DEFAULT_LANGUAGE, pattern=LANGUAGE_PATTERN)
    """The session language, which the plot's own text (title, axis titles, legend, annotations) is written in."""
    language_changed: bool = False
    """The base version's plot text is in another language than `plot_language`: rewrite it."""
    expected_texts: list[ExpectedText] = Field(default_factory=list, max_length=MAX_EXPECTED_TEXTS)
    """The texts and number formats the user asked to see in the plot (`PipelineArgs.expected_texts`)."""
    dataset_context: str = Field(default="", max_length=MAX_DATASET_CONTEXT_CHARS)
    """The screened notes pasted with the data and the source of a computed table (`dataset_context.py`)."""
    file_name: str = Field(default="", max_length=MAX_FILE_NAME_CHARS)
    """The screened name of the file the data was dropped from (`StoredDataset.file_name`), empty when none or
    withheld: a hint at the subject, fenced on its own as data, never among the notes."""


# --- Review ----------------------------------------------------------------------------


class ReviewRequest(_ServerContract):
    """What the tool-less reviewer gets; the two PNGs are attached by `render_id`."""

    render_id: str = Field(pattern=RENDER_ID_PATTERN)
    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)
    bindings: list[Binding] = Field(max_length=MAX_COLUMNS)
    profile_summary: str = Field(max_length=2_000)
    spec_brief: str = Field(max_length=4_000)
    change_request: str = Field(default="", max_length=MAX_CHANGE_REQUEST_CHARS)
    user_requests: list[UserRequest] = Field(default_factory=list, max_length=MAX_USER_REQUESTS)
    """The earlier change requests the plot carries out, oldest first: choices the review never turns into defects."""
    gate_notes: list[Note] = Field(default_factory=list, max_length=MAX_NOTES)
    plot_language: str = Field(default=DEFAULT_LANGUAGE, pattern=LANGUAGE_PATTERN)
    """The session language, against which VQ-06 judges the plot's own text."""
    dataset_context: str = Field(default="", max_length=MAX_DATASET_CONTEXT_CHARS)
    """The screened notes pasted with the data and the source of a computed table (`dataset_context.py`)."""
    file_name: str = Field(default="", max_length=MAX_FILE_NAME_CHARS)
    """The screened name of the dropped file, as for `AdaptRequest.file_name`."""


class Defect(_ModelOutput):
    """One reviewer finding with a fixed id, rendered into the pipeline's defect grammar."""

    id: DefectId
    theme: DefectTheme
    observed: DefectText
    target: DefectText
    likely_cause: DefectText

    @field_validator("observed", "target", "likely_cause", mode="before")
    @classmethod
    def _one_line(cls, value: Any, info: ValidationInfo) -> Any:
        """A defect line is one line: collapse every whitespace run to a single space.

        The first `→` separates observed from target, so an arrow inside `observed`
        becomes `->`. Both happen before the length check, so the limit bounds the
        stored text and therefore the rendered line.
        """
        return _defect_text(value, info.field_name or "") if isinstance(value, str) else value

    def as_line(self) -> str:
        """`<ID> (<theme>): <observed> → <target>. Likely cause: <likely_cause>.`

        The grammar of `DEFECT_RE` in automation/scripts/regen_gate.py and of the
        review prompt, so repair feedback reads the same as the catalogue pipeline's.
        """
        target = self.target.rstrip(". ")
        cause = self.likely_cause.rstrip(". ")
        return f"{self.id} ({self.theme}): {self.observed} → {target}. Likely cause: {cause}."


class Verdict(_ModelOutput):
    """The reviewer's answer: a pass with no defects, or a rejection with one to five.

    A contradictory verdict (`ok` with defects, or a rejection without any) is a
    validation error rather than a guess: a pass with defects could ship a defective
    render as `ok`, and a rejection without defects gives the repair nothing to fix.
    """

    ok: bool
    defects: list[Defect] = Field(default_factory=list, max_length=MAX_DEFECTS)

    @model_validator(mode="after")
    def _ok_matches_defects(self) -> Self:
        if self.ok and self.defects:
            raise ValueError("an ok verdict names no defects")
        if not self.ok and not self.defects:
            raise ValueError("a rejecting verdict names at least one defect")
        return self


# --- Formal repairs of model answers --------------------------------------------------

DEFECT_IDS: frozenset[str] = frozenset(get_args(DefectId))
DEFECT_THEMES: frozenset[str] = frozenset(get_args(DefectTheme))
DEFECT_TEXT_FIELDS = ("observed", "target", "likely_cause")


def _json_list(value: Any) -> Any:
    """A list the model sent as JSON text, parsed; anything else unchanged.

    An answer without constrained decoding (Claude's forced tool call before the
    answers moved to `output_config.format`, which now rules this out on Claude)
    sometimes carried a nested array as a string; the items are the model's own,
    only their wrapping differs.
    """
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return value
        if isinstance(parsed, list):
            return parsed
    return value


def _defect_id(item: Any) -> str:
    """The case-folded id of a defect the model sent, empty when it has none."""
    value = item.get("id") if isinstance(item, dict) else None
    return value.strip().upper() if isinstance(value, str) else ""


def _off_checklist(item: Any) -> bool:
    """Whether a defect names an id, but one outside the reviewer's checklist (such as VQ-05)."""
    defect_id = _defect_id(item)
    return bool(defect_id) and defect_id not in DEFECT_IDS


def _repair_defect(item: Any) -> dict[str, str] | None:
    """One defect with its formal misses mended, or None when it cannot be used.

    The id and theme are case-folded; a theme outside the set becomes `both`, which the
    pipeline files under the one theme the reviewer saw. Each text is put on one line
    and clipped to `MAX_DEFECT_TEXT_CHARS` with an ellipsis. A defect whose id is
    outside the checklist, or that lacks one of its three texts, cannot be used.
    """
    if not isinstance(item, dict):
        return None
    defect_id = _defect_id(item)
    if defect_id not in DEFECT_IDS:
        return None
    theme = item.get("theme")
    theme = theme.strip().lower() if isinstance(theme, str) else ""
    repaired = {"id": defect_id, "theme": theme if theme in DEFECT_THEMES else "both"}
    for name in DEFECT_TEXT_FIELDS:
        text = item.get(name)
        text = _defect_text(text, name) if isinstance(text, str) else ""
        if not text:
            return None
        repaired[name] = _clip(text, MAX_DEFECT_TEXT_CHARS)
    return repaired


def repair_verdict(data: Any) -> Any:
    """A reviewer answer with its formal misses mended; `data` unchanged when nothing can be mended.

    Every usable defect is kept (see `_repair_defect`), the first `MAX_DEFECTS` of
    them, and `ok` follows from them: a verdict that names a usable defect rejects,
    whatever its `ok` said. A pass (`ok` true) whose defects all name ids outside the
    checklist stays a pass without them: the reviewer passed the render, and its
    checklist leaves those criteria out. Any other verdict left without a usable
    defect keeps its own `ok` and defects, so it still fails validation: a rejection
    that names nothing usable gives the repair nothing to fix, and a checklist defect
    without its texts is a rejection the reviewer meant.
    """
    if not isinstance(data, dict):
        return data
    raw = _json_list(data.get("defects", []))
    if not isinstance(raw, list):
        return data
    defects = [defect for defect in map(_repair_defect, raw) if defect is not None][:MAX_DEFECTS]
    if defects:
        return {**data, "ok": False, "defects": defects}
    if data.get("ok") is True and raw and all(map(_off_checklist, raw)):
        return {**data, "defects": []}
    return data


def repair_plan(data: Any) -> Any:
    """An adapter answer with its formal misses mended; the edits are never changed.

    `changes` keeps its first `MAX_CHANGES` non-empty notes, each on one line and
    clipped to `MAX_CHANGE_CHARS`; `title` is clipped to `MAX_TITLE_CHARS` (a missing
    one is empty); a blank `full_code` means no full file. The edit contract stays
    strict: an edit list over `MAX_EDITS`, an empty `find`, or edits next to a full
    file still fail, because dropping or choosing hunks would change the plan.
    """
    if not isinstance(data, dict):
        return data
    repaired = dict(data)
    if "edits" in data:
        repaired["edits"] = _json_list(data["edits"])
    full_code = data.get("full_code")
    if isinstance(full_code, str) and not full_code.strip():
        repaired["full_code"] = None
    title = data.get("title")
    if title is None:
        repaired["title"] = ""
    elif isinstance(title, str):
        repaired["title"] = _clip(title.strip(), MAX_TITLE_CHARS)
    changes = _json_list(data.get("changes", []))
    if isinstance(changes, list):
        notes = [_WHITESPACE.sub(" ", note).strip() for note in changes if isinstance(note, str)]
        repaired["changes"] = [_clip(note, MAX_CHANGE_CHARS) for note in notes if note][:MAX_CHANGES]
    return repaired


# --- Result ----------------------------------------------------------------------------


RoundOutcome = Literal[
    "ok", "review", "measured", "render_failed", "check_failed", "answer_unusable", "unreviewed", "error"
]
"""How one pipeline round (an attempt) ended, in the page's vocabulary.

`ok`: the reviewer passed the render; `review`: it named findings; `measured`: the
render passed the blocking host gates, but its canvas, probe or adaptation findings
went to the repair; `render_failed`: the blocking host gates failed; `check_failed`:
an edit did not apply, the validator refused the code or the loader did not fit;
`answer_unusable`: the adapter's answer yielded no usable plan; `unreviewed`: the
render shipped without a review (every review used, the review unreadable, or a
limit reached); `error`: an exception.
"""


RoundStep = Literal["adapting", "repairing", "checking", "rendering", "reviewing"]
"""The pipeline steps the progress events name, the ones a round can end in."""
RubricId = Annotated[str, Field(pattern=r"^[A-Z]{2}-[0-9]{2}$")]
"""A rubric or auto-reject id (`VQ-05`, `AR-09`): a closed code, never text."""
MAX_ROUND_DEFECTS = 6


class Round(_ServerContract):
    """One pipeline round for the progress grid: its attempt, how it ended, and how many findings it passed on.

    `step` is the pipeline step the round was in when it ended (an unreadable review
    ends at `reviewing`, a limit before the review at `rendering`, an error anywhere).
    `shipped` marks the round whose render the result shipped, which is not always the
    last one: a repair round that fails its check leaves the earlier render shipped.
    `findings` counts the lines the round passed on as the next attempt reads them, and `defects`
    the rubric ids among them (`VQ-01`, `VQ-05`), which the page names in words for the repair
    round that follows (live round 9 of 2026-10-16: the repair was invisible on the page).
    """

    attempt: int = Field(ge=1, le=MAX_ATTEMPTS)
    outcome: RoundOutcome
    findings: int = Field(default=0, ge=0, le=99)
    step: RoundStep | None = None
    shipped: bool = False
    defects: list[RubricId] = Field(default_factory=list, max_length=MAX_ROUND_DEFECTS)


ShownGroup = Literal[
    "title",
    "x axis label",
    "y axis label",
    "z axis label",
    "other axis labels",
    "legend",
    "x tick labels",
    "y tick labels",
    "z tick labels",
    "annotations",
    "other texts",
]
"""The roles `PlotShows.texts` groups the drawn texts by (`grounding.plot_texts`)."""
ShownText = Annotated[str, Field(min_length=1, max_length=MAX_SHOWN_TEXT_CHARS)]
ReviewState = Literal["passed", "findings", "not_reviewed"]


class PlotShows(_ServerContract):
    """What the shipped render shows, built by the server: the root's closing reply is grounded in it.

    `texts` are the drawn texts by role, read from the render's probe (`grounding.plot_texts`);
    None when the renderer reported none (a renderer older than the `labels` probe field).
    `review` is the verdict on exactly this render (`passed`: it met the ship bar), `score`
    the catalogue review's score, `requested_not_found` the `expected_texts` the drawn
    texts do not show (`grounding.expected_misses`). The texts are written by the code under
    test, so the root reads them fenced, as data.
    """

    texts: dict[ShownGroup, list[ShownText]] | None = None
    review: ReviewState = "not_reviewed"
    score: int | None = Field(default=None, ge=0, le=100)
    requested_not_found: list[ExpectedText] = Field(default_factory=list, max_length=MAX_EXPECTED_TEXTS)


class PlotResult(_ServerContract):
    """The pipeline's final output; every path through `run_pipeline` yields one.

    `ok`: the reviewer passed exactly the shipped render and the canvas was not
    padded. `needs_attention`: a render shipped with residual defect lines.
    `failed`: no render passed the blocking host gates; `reason` says why.
    `not_ready`: no dataset, incomplete bindings or data the user has not confirmed yet,
    decided before any LLM call.

    `version` is the number the session's version store gave the shipped result
    (`ok` or `needs_attention`), the one the artifact and theme toggle routes take;
    it is set once the version is stored, and a `failed` or `not_ready` result has none.

    `rounds` lists how each attempt ended, in order (`Round`), for the page's progress
    grid; it is content-free (an outcome and a count) and empty for `not_ready`.

    `shows` is what the shipped render shows (`PlotShows`), on `ok` and `needs_attention`
    only; it goes to the root, never to the page's `plot` event (`stream.PLOT_FIELDS`).

    `request_kept` is `true` on a `not_ready` result whose own `change_request` or `expected_texts` the
    server keeps for the first plot (`pipeline.keep_pending_request`), so the root says the request is kept
    only when it is (live round 9 of 2026-10-16: the root said so without calling the tool). Root-only too.
    """

    status: PlotStatus
    reason: FailureReason | NotReadyReason | None = None
    attempts: int = Field(default=0, ge=0, le=MAX_ATTEMPTS)
    artifacts: list[ArtifactName] = Field(default_factory=list, max_length=4)
    changes: list[ChangeNote] = Field(default_factory=list, max_length=MAX_CHANGES)
    residual_defects: list[Line] = Field(default_factory=list, max_length=MAX_RESIDUAL_DEFECTS)
    version: int | None = Field(default=None, ge=1)
    rounds: list[Round] = Field(default_factory=list, max_length=MAX_ATTEMPTS)
    shows: PlotShows | None = None
    request_kept: bool | None = None

    @model_validator(mode="after")
    def _status_rules(self) -> Self:
        if self.request_kept is not None and self.status != "not_ready":
            raise ValueError("only a not_ready result keeps a request")
        if self.status in ("failed", "not_ready") and self.version is not None:
            raise ValueError(f"a {self.status!r} result stores no version")
        if self.status in ("failed", "not_ready") and self.shows is not None:
            raise ValueError(f"a {self.status!r} result shows no plot")
        if self.status == "failed":
            if self.reason not in FAILURE_REASONS:
                raise ValueError(f"a failed result needs a reason in {sorted(FAILURE_REASONS)}")
        elif self.status == "not_ready":
            if self.reason not in NOT_READY_REASONS:
                raise ValueError(f"a not_ready result needs a reason in {sorted(NOT_READY_REASONS)}")
            if self.attempts or self.artifacts:
                raise ValueError("a not_ready result has no attempts and no artifacts")
        else:
            if self.reason is not None:
                raise ValueError(f"a {self.status!r} result carries no reason")
            if self.attempts < 1:
                raise ValueError(f"a {self.status!r} result needs at least one attempt")
            if self.status == "ok" and self.residual_defects:
                raise ValueError("an ok result has no residual defects; that is needs_attention")
            if self.status == "needs_attention" and not self.residual_defects:
                raise ValueError("a needs_attention result names its residual defects")
        if len(set(self.artifacts)) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self

    @classmethod
    def not_ready(cls, reason: NotReadyReason, *, request_kept: bool = False) -> Self:
        """The result before any LLM call when the session lacks a dataset, bindings or the user's confirmation."""
        return cls(status="not_ready", reason=reason, request_kept=request_kept or None)
