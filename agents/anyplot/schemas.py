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
from collections.abc import Iterable
from typing import Annotated, Any, Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, ValidationInfo, field_validator, model_validator


# Limits from the design doc, named once so the parser, the tools and the tests share them.
MAX_ROWS = 20_000
MAX_COLUMNS = 50
MAX_COLUMN_NAME_CHARS = 64
MAX_CELL_CHARS = 40
MAX_SAMPLE_ROWS = 5
MAX_TOP_VALUES = 5
MAX_CHANGE_REQUEST_CHARS = 600
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
MAX_RESIDUAL_DEFECTS = 16  # 5 reviewer lines, 4 advisory probe gates, canvas padding, adaptation findings
MAX_NOTE_CHARS = 300
MAX_CHANGE_CHARS = 200
MAX_DEFECT_TEXT_CHARS = 200
# Every rendered defect line is also a feedback or residual `Line`, so a `Line` must hold
# the longest `Defect.as_line()`: three texts of 200 characters plus 35 of grammar.
MAX_LINE_CHARS = 640

ColumnName = Annotated[str, Field(min_length=1, max_length=MAX_COLUMN_NAME_CHARS)]
Cell = Annotated[str, Field(max_length=MAX_CELL_CHARS)]
Note = Annotated[str, Field(min_length=1, max_length=MAX_NOTE_CHARS)]
Line = Annotated[str, Field(min_length=1, max_length=MAX_LINE_CHARS)]
ChangeNote = Annotated[str, Field(min_length=1, max_length=MAX_CHANGE_CHARS)]
DefectText = Annotated[str, Field(min_length=1, max_length=MAX_DEFECT_TEXT_CHARS)]

ColumnDtype = Literal["integer", "number", "datetime", "boolean", "text"]
SourceFormat = Literal["csv", "tsv", "semicolon", "pipe", "json_records", "json_columns", "json_pairs"]

# The reviewer's reduced checklist: the rubric criteria it scores plus AR-09 for clipping.
DefectId = Literal["VQ-01", "VQ-02", "VQ-03", "VQ-06", "VQ-07", "SC-01", "SC-03", "DQ-03", "AR-09"]
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
    """One column of the pasted dataset, as the deterministic parser profiled it."""

    name: ColumnName
    dtype: ColumnDtype
    missing: NonNegativeInt
    unique: NonNegativeInt
    min: float | Cell | None = None
    max: float | Cell | None = None
    top: list[Cell] = Field(default_factory=list, max_length=MAX_TOP_VALUES)


class DatasetProfile(_ServerContract):
    """What the root and the adapter learn about the dataset; never the raw data.

    The sample rows are rendered inside a `<user_data>` fence by the tool layer,
    which escapes the delimiters; the schema only bounds their size.
    """

    rows: int = Field(ge=1, le=MAX_ROWS)
    columns: list[ColumnProfile] = Field(min_length=1, max_length=MAX_COLUMNS)
    sample: list[Annotated[list[Cell], Field(max_length=MAX_COLUMNS)]] = Field(
        default_factory=list, max_length=MAX_SAMPLE_ROWS
    )
    source_format: SourceFormat
    decimal: Literal[".", ","] = "."
    warnings: list[Note] = Field(default_factory=list, max_length=MAX_WARNINGS)

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
    feedback: list[Line] = Field(default_factory=list, max_length=MAX_FEEDBACK)
    previous_plan: AdaptPlan | None = None
    allow_full: bool = False


# --- Review ----------------------------------------------------------------------------


class ReviewRequest(_ServerContract):
    """What the tool-less reviewer gets; the two PNGs are attached by `render_id`."""

    render_id: str = Field(pattern=RENDER_ID_PATTERN)
    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)
    bindings: list[Binding] = Field(max_length=MAX_COLUMNS)
    profile_summary: str = Field(max_length=2_000)
    spec_brief: str = Field(max_length=4_000)
    change_request: str = Field(default="", max_length=MAX_CHANGE_REQUEST_CHARS)
    gate_notes: list[Note] = Field(default_factory=list, max_length=MAX_NOTES)


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
    """

    status: PlotStatus
    reason: FailureReason | NotReadyReason | None = None
    attempts: int = Field(default=0, ge=0, le=MAX_ATTEMPTS)
    artifacts: list[ArtifactName] = Field(default_factory=list, max_length=4)
    changes: list[ChangeNote] = Field(default_factory=list, max_length=MAX_CHANGES)
    residual_defects: list[Line] = Field(default_factory=list, max_length=MAX_RESIDUAL_DEFECTS)
    version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _status_rules(self) -> Self:
        if self.status in ("failed", "not_ready") and self.version is not None:
            raise ValueError(f"a {self.status!r} result stores no version")
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
    def not_ready(cls, reason: NotReadyReason) -> Self:
        """The result before any LLM call when the session lacks a dataset, bindings or the user's confirmation."""
        return cls(status="not_ready", reason=reason)
