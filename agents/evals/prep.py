"""Live prep eval: the root's step-1 data choices on short requests, through `/v1` in process with the real model.

Run it with the models from the settings (Claude Haiku 5.5 on Vertex AI `eu` by default):

    uv run --extra agents python -m agents.evals.prep
    uv run --extra agents python -m agents.evals.prep --provider gemini

Each case of `fixtures/prep/<id>.json` (`message`, `expected_operations`, `locale`, and
optionally `dataset_text`, `spec_id`, `library`, `tags`) opens a session on
`agents.main:app` through httpx's `ASGITransport`, as the matrix harness does, posts
the dataset when the case has one (the dataset judge runs for real), sends the message
as a free-text turn (the scope judge, then the root with its tools) and reads the
`prepare_data`, `generate_data` and `run_data_code` calls the root made from the
session's events. The pipeline never runs: no case confirms the data or asks for a
plot, so no adapter call happens; a `run_data_code` call runs its snippet on the
configured render backend (the remote renderer's `POST /run-data` by default).

A `run_data_code` call counts as the table it stored, `{"op": "run_data_code", "rows":
..., "columns": ...}`, read from its answer: the Python the root writes varies from run
to run, the table's size does not. With the default `AGENT_RENDERER=fake` no case
renders, but a data run is not the fake's fixture table: `HostDataBackend`
(`host_data.py`) runs the snippet under the real harness in data mode, with the
renderer's limits, and answers with the table it computed, as `POST /run-data` does.
The fake's fixed four-row table made the root (rightly) distrust its own run and call
`run_data_code` again, which scored the fake instead of the root. `AGENT_RENDERER=remote`
(with `AGENT_RENDER_URL`) or `local` sends the data runs to that renderer instead. A case with `refuse: true` (a snippet that reads a
file, a script with another purpose) passes when no data tool call of the turn stored a
version, whether the scope judge refused it, the validator did, or the root called
nothing.

A case passes by the table its turn leaves, since 2026-11-08 (`score_turn`): the session's current data version
after the turn, as the tools stored it, must equal the table the case's `expected_operations` make from the same
start through the same server code (`expected_result`: `apply_and_parse` for the `prepare_data` operations, five to
a call in their order, and `generate` with the tool's own parse for a `generate_data` item). The start is the
version the turn began on, or the one `expected_from_version` names, read from the session's store before the turn,
so the earlier versions (`before_operations`), the screened notes and the session language are the tools' own. Two
tables are equal when their columns in order, each column's dtype, their row count and every cell are
(`table_difference`): a text, date or boolean cell exactly, a number cell (`integer`, `number`) within
`TABLE_REL_TOL` relative or `TABLE_ABS_TOL` absolute, since `data.csv` writes a float in full and two sums of the
same values in another order differ in the last digit. Rows are compared in their order, which a line connects, a
bar chart keeps and a sort is about; a case with `row_order: "any"`, a request that leaves the order open, compares
both tables after a canonical sort of their rows. So a `drop_columns` of a notes column before an `aggregate` that
keeps only its keys and its values, and the `aggregate` alone, are the same answer (guard 2a of #12599, where
`de-hard-kette-gesamtzeile` read such a run as a miss). A named gap (`unsupported`) changes no table, so the gaps the
turn named must be the expected ones as well. Every `prepare_data`, `generate_data` and `run_data_code` call of the
turn must have succeeded all the same: a list the data refuses (a column named before its rename, a type its cells
cannot take) is a miss however the turn ends, and so is a formula the server cannot compute (`failed_calls`). An
`unsupported_operation` answer is no failure: the root named a change no operation can make (`{"op": "unsupported",
"family": ...}`), which a case expects as it expects any operation, since 2026-11-07.

The exact operation match is kept as a diagnostic beside the table (`ops_exact`, counted in the summary), and it
decides four kinds of case instead (`PrepCase.scored_by_table`): one with `expected_operations: []`, which passes when
the root made no data call (a scope refusal and a plain reply both pass, and the report lists every tool call and the
refusal, so a false refusal stays visible); one that expects a `run_data_code` call, whose code and values vary from
run to run, so it compares the size of the stored table; a `refuse` case (below); and one with `strict_operations:
true`, for a case where the operation itself is the point. `check_cases` refuses a case scored by its table whose
expected operations leave its table as it is, since the table cannot tell them from no call: such a case is strict.
The match is order-insensitive. A `compute` operation matches by the values it computes on invented rows, whatever
short names and form the expression has (`compute_key`). The operations of every `prepare_data` call of the turn
are taken together (one call with two operations and two calls with one each are the same) and each is normalised
through the `Operation` models (`canonical_operations`): a default the model left out and one it wrote are the same,
a `set_type` `decimal` equal to the dataset's own counts as left out, and the column list of `drop_columns` and
`pivot_longer` and the conditions of `drop_rows` are sets. A `generate_data` call is one item `{"op":
"generate_data", "variables": [...], "series": [...]}`, normalised through the `generate.Generate` model the same way
for the report (defaults left out, the whitespace of every expression and endpoint removed, the series a set; the
variables keep their order, which decides the grid's), and two calls match when they compute the same table
(`comparison_key`): the same names, points and values, so `-3.0` is `-3`, `tau` is `2*pi` and `x*x` is `x**2`. A
reply of the root that talks about its own instructions (ADK's instruction markers, a system instruction, the session
block; `INSTRUCTION_TALK`) is a miss whatever the data calls did, and the summary counts such cases under
`instruction_talk`. The gate is `--min-exact` (80 percent) matched cases of the answered ones; the flag and the
summary's `exact` keep their names from the time a match was the exact one.

A case may send the step-1 summary action instead of a message (`action: "summarize_data"`, as the page
does after a paste): it expects no data call, and only its reply is scored. Every root reply is also
measured for its shape (short, to the point, a question only when it matters): its words
(`MAX_REPLY_WORDS`), its questions, and whether it closes with one. A closing
question is a reply miss unless the turn is blocked: the case is tagged `ask_back` (a request that can
mean two different changes), a data call of the turn failed, or the turn left a required role of the spec
without a column (`roles_open`), unless the session block offered a date column for it, which the reply
states instead (`offered`, since 2026-11-04). A closing invitation to choose is a reply miss on the same
terms (`closes_with_invitation`: a last sentence or clause such as "Choose …", "Pick one …", "tell me which
…", "Wähle …"; never the instruction to press `.confirm()`). A reply over `MAX_REPLY_WORDS` words is a
reply miss too, and so is the reply of a summary turn (the summary action, or the note sent with the paste)
that names no row count in digits, neither the paste's nor that of the version the turn made (`names_count`):
a summary says how many rows the data has. The reply gate is `--max-reply-misses` (10 percent) of the
answered cases with a reply; the reply text itself never enters the report.

A summary case is also checked for the conversions it owes (`score_conversions`). Before the turn, the run
computes in code what the session block will list for the open roles (`conversions.candidates`); after it, each
`certain` line must be among the turn's operations. The server makes those lines itself before the root runs
(`paste_conversions.py`), so the operations of its record (`CONVERSIONS_MADE`) come first among the turn's, its
version is part of the table the turn leaves, and a fixture expects them as it expects the root's, first in its list:
a root that drops or renames its column leaves another table (one that makes it again leaves the same table when the
operation keeps what is there, as `row_number` does). A turn left without one is the
original failure of the live test of 2026-11-01,
where the root asked the user for a date column a conversion would have made, so the case is a miss whatever its
fixture expected, and any skip fails the run. The summary counts `conversions_owed` and `conversions_made`, and
each case its `server_operations`.

A case may change the data before its message (`before_operations`, since 2026-11-07): the server stores each list
of operations as the next data version, as the root's earlier turns would have, so the session block lists them and
the message can ask for what only an earlier version still has ("the first 20 after all" after a top 10). Its
`expected_from_version` (`original` or a number) is the version its expected table starts from, and it is scored
too (`score_from_version`): some `prepare_data` or
`query_data` call of the turn names it and no `prepare_data` call names another, or the case is a miss. The report
lists every call's `from_version` under `from_versions`, scored or not.

A case with `plot_request` asks for a change of the plot, alone or beside its data operations: an order of the
bars, a total in the title. Its turn must send that wish to the plot, a `keep_plot_request` or a `plot_pipeline`
call that carries a request, a text or a decision, and the plot must have it: the answer kept it for the next plot
(`request_kept`) or drew it (`score_plot_request`, `PLOT_TOOLS`). Otherwise the case is a miss; the summary counts
those under `plot_request_misses`. Its data is scored as in every case, so a table the turn sorted for the order misses by the
order of its rows, and a case whose message asks for the plot alone expects no data call (`expected_operations: []`).

A case is `unavailable` when its dataset could not be stored (`503 guard_unavailable`)
or its turn ended with an `error` event (the judge down, `capacity`); it counts in no
rate, and more than `--max-unavailable` (10 percent) of them exit 4. A dataset the
judge refuses (`403 data_refused`) is a miss, because the fixtures are synthetic
tables that must pass.

A case makes about five model calls: the dataset judge, the scope judge, and the root
two or three times (a profile read, the tool call, the reply). Under the Vertex quota
for Claude Haiku in `eu` (150 requests per minute since 2026-10-31, see `scope.py`),
`--calls-per-minute` (25 by default) spaces the starts of the cases `CALLS_PER_CASE`
times further apart than the scope eval spaces its judge calls: 12 seconds at the
default, so the 81 cases take about 16 minutes; the cases run one at a time. The cost
is the list price of every call the attribution log booked (`pricing.call_cost`,
`pricing.judge_cost`).

It writes `<out>/<date>-prep-<model>.json` (the stamp, the gates, the summary, every
case's canonical expected and found operations, `ops_exact`, what its table missed in
words that name columns at most (`table_miss`), its tool calls, refusal, cost and
latency; never a dataset, a cell or a message, which stay in the fixtures) and prints a table.
The exit code is 0 when the gate holds, 1 when it does not, 2 for a setup error (a
fixture that does not load or whose expected operations fail the `Operation` or
`Generate` models, an unpriced model) and 4 for an outage.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import itertools
import json
import logging
import math
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Collection, MutableMapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from agents.evals.matrix import (
    ATTRIBUTION_LOGGER,
    EVAL_GLOBAL_DAILY_TOKENS,
    MODEL_PROVIDERS,
    PROVIDER_DEFAULTS,
    AttributionCollector,
    parse_events,
    store_data_steps,
)
from agents.evals.pricing import LOCATION_SURCHARGE, UnknownPrice, call_cost, judge_cost, price_of
from agents.evals.scope import Pacer


if TYPE_CHECKING:  # importing agents.anyplot builds the agents, so the runtime imports wait for `configure`
    from agents.anyplot.data.parse import ParsedDataset
    from agents.anyplot.data.store import StoredDataset
    from agents.anyplot.render.contract import RenderBackend
    from agents.anyplot.schemas import FromVersion
    from agents.anyplot.services import Services
    from agents.anyplot.settings import AgentSettings
    from agents.main import Runtime


EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_CASES = EVALS_DIR / "fixtures" / "prep"
DEFAULT_OUT = EVALS_DIR / "reports"
REPORT_SCHEMA = 2
"""2 since 2026-11-08: a match is the table the turn left (`score_turn`), and each result has `ops_exact` and
`table_miss`."""
MAX_MESSAGE_CHARS = 2_000  # the /messages limit (agents/main.py)
MAX_DATASET_CHARS = 200 * 1024
CALLS_PER_CASE = 5
"""Model calls a case makes, about: the dataset judge, the scope judge, two or three root calls."""
DEFAULT_CALLS_PER_MINUTE = 25.0
DEFAULT_MIN_EXACT = 0.8
DEFAULT_MAX_UNAVAILABLE = 0.1
DEFAULT_MAX_REPLY_MISSES = 0.1
MAX_REPLY_WORDS = 100
"""The longest reply that is no reply miss, in words: about the five sentences `root.md` allows at most. A data
change with its counts, the confirmation and an open role fits; a reply padded with the request repeated back or a
list of what stayed the same does not (prep runs of 2026-11-01: on the main prompt a median of 69 words and 5 of 52
replies over 100, on the "Replies" rules 57 words and 2 of 52)."""
BLOCKED_TAGS = frozenset({"ask_back"})
"""A case with one of these tags cannot go on without the user's answer, so its reply may close with a question."""
QUESTION = re.compile(r"[?？؟]+")
INVITATION = re.compile(
    r"(?:choose|pick|select|decide|tell me|let me know|say which|name (?:the|a|one)|if you(?:'d)? (?:want|like)"
    r"|wähle|wählt|such dir|entscheide|sag mir|nenne|gib mir|wenn du (?:willst|möchtest))\b",
    re.IGNORECASE,
)
"""The start of a closing sentence or clause that asks the user to choose or to ask: an invitation as much as a
question (root.md, "Replies": never close with one, as a question or as a statement). The list is narrow on purpose:
the instruction to check the preview and press `.confirm()` is an imperative the replies must close with, and a
column named `Name` may start a sentence ("Name is bound to the category"). It came from the summary of the owner's
customers table of 2026-11-04, which closed with "Choose the y column in the data panel, or name the unit you
want." in 2 of 5 live runs."""
_SENTENCE_END = re.compile(r"(?<=[.!?。])\s+")
_CLAUSE_START = re.compile(r"[;—–]\s*|,\s+(?:or|oder)\s+")
EXIT_OK, EXIT_FAILED, EXIT_SETUP, EXIT_OUTAGE = 0, 1, 2, 4
PREPARE_TOOL = "prepare_data"
QUERY_TOOL = "query_data"
GENERATE_TOOL = "generate_data"
DATA_CODE_TOOL = "run_data_code"
MAX_BEFORE_VERSIONS = 5
"""Earlier changes a case may make before its message: the versions the undo history keeps."""
DATA_TOOLS = frozenset({PREPARE_TOOL, GENERATE_TOOL, DATA_CODE_TOOL})
PIPELINE_TOOL = "plot_pipeline"
PLOT_TOOLS = frozenset({"keep_plot_request", PIPELINE_TOOL})
"""The calls that send a wish to the plot: kept for the next plot, or run on the plot the session has."""
SHIPPED = frozenset({"ok", "needs_attention"})
"""The `plot_pipeline` results that drew a plot."""
"""The root's tools that store a dataset version; every call of them in a turn must succeed."""
GAP_CODE = "unsupported_operation"
"""`prepare_data`'s answer to the `unsupported` operation: the root named a change no operation can make."""
GAP_OP = "unsupported"
"""The operation that names such a gap: it changes no table, so a case compares the gaps apart (`gap_difference`)."""
SET_OPERATIONS: dict[str, str] = {
    "drop_columns": "columns",
    "pivot_longer": "columns",
    "drop_rows": "where",
    "blank": "columns",
    "aggregate": "columns",
}
"""Per operation, the list field whose order carries no meaning (compared as a set); a condition list is sorted by
`_sorted_conditions`, and an "any of" list of values in any condition is a set too. An `aggregate` names `columns`
only for two or more value columns, whose order is only the order of the result's columns."""
CONDITION_OPERATIONS = frozenset({"drop_rows", "blank", "keep_rows"})
"""The operations whose `where` is one list of conditions that must all hold."""
MAX_REPLY_NAMES = 6
"""The texts one case may ask its reply to contain (`PrepCase.reply_names`)."""
COMPUTE_PROBE_ROWS = 8
"""The rows of invented values two `compute` expressions are compared on (`comparison_key`)."""
COMPUTE_PROBES: tuple[tuple[float, float, float], ...] = ((150.5, 7.913, 21.7), (1.5, 0.913, 2.17))
"""The probe sets of `compute_key`, each `(start, step per row, step per column)`: large values first, so a shifted log
or root (`log(p - 100)`, `sqrt(t - 50)`) is defined on every row, then small ones for an expression the first set
leaves without any value (`log(100 - p)`)."""
TABLE_REL_TOL = 1e-9
"""How far apart, relative to the larger, two number cells may be and still be one value (`table_difference`):
`data.csv` writes a float in full (`repr`), so a sum taken in another order or a `compute` written in another form
differs in its last digits, while a real difference in the data is far larger."""
TABLE_ABS_TOL = 1e-12
"""The same for two number cells near zero, where a relative tolerance holds nothing: `sin(pi)` is about 1.2e-16."""
NUMBER_DTYPES = frozenset({"integer", "number"})
"""The column dtypes whose cells compare as numbers, within the tolerances; every other cell compares as its text."""
SORT_DIGITS = 9
"""The significant digits a number cell is sorted by under `row_order: "any"`, so two cells within the tolerances
take the same place among the rows."""
ROOT_AUTHOR = "anyplot"
INSTRUCTION_TALK = re.compile(
    # ADK's own markers (`flows/llm_flows/context/_fencing.py`), named or quoted.
    r"SYSTEM_INSTRUCTION|<<<ELIDED_MARKER>>>"
    # The root's instructions named as such: only after a determiner, so a column, a heredoc or
    # a data value with one of these words never counts.
    r"|\b(?:my|your|the|this|these|those|a|an|as)\s+(?:system[ -]?(?:instructions?|prompt)|session[ -]block)\b"
    r"|\b(?:meine[mnrs]?|deine[mnrs]?|die|der|den|dem|diese[mnrs]?|eine[mnrs]?|als)\s+"
    r"(?:System(?:anweisung|instruktion)(?:en)?|Systemprompts?|Sitzungsblocks?|Session-Blocks?)\b",
    re.IGNORECASE,
)
"""A reply that talks about the root's own instructions: ADK's markers, a system instruction, the session block.

Until 2026-10-15 ADK sent the session block inside the user's turn between
`<<<BEGIN_SYSTEM_INSTRUCTION>>>` markers, and the root once told the user that "the text with the
SYSTEM_INSTRUCTION markers in your message" changed nothing. Such a reply is a miss whatever the
data calls did. A bare `<<<` is no marker: a data-code reply may quote a heredoc (`<<<EOT`). The
plain words stay, behind a determiner ("your system instruction", "der Sitzungsblock"), because a
reply about the block need not quote a marker; a column or value that only contains such a word
does not count."""


class SetupError(Exception):
    """A run that cannot start: its message says what to change."""


class PrepCase(BaseModel):
    """One data request, on one small dataset or none, with the operations the root should choose."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]{1,64}$")
    dataset_text: str | None = Field(default=None, min_length=1, max_length=MAX_DATASET_CHARS)
    """Posted before the message; a formula case may leave it out (`generate_data` makes the first data)."""
    message: str | None = Field(default=None, min_length=1, max_length=MAX_MESSAGE_CHARS)
    action: Literal["summarize_data"] | None = None
    """The page's step-1 summary action, sent instead of a message; a case has exactly one of the two."""
    expected_operations: list[dict[str, Any]]
    locale: str = Field(pattern=r"^[a-z]{2}$")
    spec_id: str = Field(default="scatter-basic", pattern=r"^[a-z0-9-]{1,100}$")
    library: str = Field(default="matplotlib", pattern=r"^[a-z0-9]{1,32}$")
    tags: list[str] = Field(default_factory=list)
    refuse: bool = False
    """The case passes when no data tool call of the turn stored a version (a scope refusal, a validator refusal or
    no call at all): a snippet that reads a file or a script with another purpose than the plot's data."""
    first_turn: bool = False
    """The message is the note the user typed with the paste: the first turn on the data, which summarizes it and
    acts on the note in one reply (`SUMMARY_PENDING`). Without it, the harness marks the data summarized before the
    message, as after the page's summary turn, so a message case means what it meant before the note path."""
    before_operations: list[list[dict[str, Any]]] = Field(default_factory=list, max_length=MAX_BEFORE_VERSIONS)
    """Earlier changes of the data, one `prepare_data` call's operations each, which the server applies before the
    message as the root's earlier turns would have, each as a version of its own (`_make_versions`): the session block
    lists them, and the message can ask for what only an earlier version still has (since 2026-11-07)."""
    expected_from_version: Literal["current", "original"] | Annotated[int, Field(ge=1)] | None = None
    """The version the turn should start from (`from_version`, `original` being 1): some `prepare_data` or
    `query_data` call names it and no `prepare_data` call names another (`score_from_version`), and the expected table
    starts from it. None leaves the versions unscored, and the expected table starts from the current version; the
    report lists the versions all the same."""
    strict_operations: bool = False
    """Score the case by its operations (`same_operations`) instead of the table they make (`scored_by_table`): for a
    case whose operation itself is the point, such as one the table cannot show (since 2026-11-08)."""
    row_order: Literal["same", "any"] = "same"
    """`any` for a request that leaves the order of the rows open: the found and the expected table are compared after
    a canonical sort of their rows. `same`, the default, compares the rows in their order, which a line connects and a
    sort is about. Only for a case scored by its table."""
    plot_request: bool = False
    """The message asks for a change of the plot, alone or beside its data operations (an order of the bars, a total
    in the title): the turn must send it to the plot with one of `PLOT_TOOLS`, and the plot must keep or draw it
    (`score_plot_request`). The data operations are scored as in every case, so a table the turn sorted for such an
    order is a miss by its rows."""
    reply_names: list[str] = Field(default_factory=list, max_length=MAX_REPLY_NAMES)
    """Texts of the fixture's own data the reply has to contain, each as written: what the user must hear about and
    the table cannot show, such as the rows a top N left out of a tie. A reply without one of them is the reply miss
    `unnamed` (`measure_reply`)."""
    view: Literal["set", "none"] | None = None
    """Where the turn's choice of rows has to land (`score_view`): `set` for a view of the plot (a selection, a top
    N), which leaves the table as it is, `none` for a turn that must leave no view (a cleaning step, rows the user
    asks out of the table itself). The table a plot would draw is the same either way, so only this tells a turn
    that cut the table from one that set the view. None leaves it unscored."""

    @model_validator(mode="after")
    def _one_turn(self) -> PrepCase:
        if (self.message is None) == (self.action is None):
            raise ValueError("a case has either a message or an action")
        if self.action is not None and self.dataset_text is None:
            raise ValueError("a summary action needs a dataset")
        if self.first_turn and (self.message is None or self.dataset_text is None):
            raise ValueError("a first turn is a message sent with a dataset")
        if self.before_operations and (self.message is None or self.first_turn or self.dataset_text is None):
            raise ValueError("earlier changes come before a message on summarized data")
        if self.row_order == "any" and not self.scored_by_table:
            raise ValueError("row_order is for a case scored by its table")
        if self.row_order == "any" and self.plot_request:
            # The order of the rows is how such a case sees a table that was sorted for the plot's order.
            raise ValueError("a plot_request case compares the rows in their order")
        return self

    @property
    def scored_by_table(self) -> bool:
        """Whether the case passes by the table its turn leaves (`score_turn`), not by its operations.

        Every case does except four kinds, which keep the exact operation match: one that expects no data call
        (`expected_operations: []`), one that expects a `run_data_code` call (its code and values vary from run to
        run, so its stored table counts by its size), a `refuse` case (nothing may be stored) and a case with
        `strict_operations`.
        """
        if self.refuse or self.strict_operations or not self.expected_operations:
            return False
        return all(item.get("op") != DATA_CODE_TOOL for item in self.expected_operations)


Size = Annotated[int, Field(ge=1)]


class _CodeExpectation(BaseModel):
    """An expected `run_data_code` call: the table it should store, by its size (the code itself varies).

    `rows` or `columns` may be a list of two to four sizes when the user's code leaves the table's shape genuinely
    open, as a script that defines both the steps and the walk they add up to: a table of the walk alone and one that
    keeps the steps beside it are both the user's data. A call the root made always has one size.
    """

    model_config = ConfigDict(extra="forbid")
    op: str = Field(pattern=f"^{DATA_CODE_TOOL}$")
    rows: Size | list[Size]
    columns: Size | list[Size]

    @field_validator("rows", "columns")
    @classmethod
    def _choices(cls, value: int | list[int]) -> int | list[int]:
        if isinstance(value, int):
            return value
        choices = sorted(set(value))
        if not 2 <= len(choices) <= 4:
            raise ValueError("a list of sizes holds two to four different sizes")
        return choices


def canonical_code(item: dict[str, Any]) -> str:
    """A `run_data_code` call as a JSON line: the rows and columns of the table it stored, or the sizes an expected
    one may have (sorted); raises `ValidationError`."""
    data = _CodeExpectation.model_validate(item).model_dump()
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def _code_fits(found: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Whether a stored table's size is one the expected `run_data_code` call allows.

    A found item without a size (a `{"op": "run_data_code"}` the root put into `prepare_data`'s operations, which
    ToolSafety refused and the report keeps raw) fits nothing: a miss, never a crash of the run.
    """
    return all(
        isinstance(found.get(key), int)
        and found[key] in (expected[key] if isinstance(expected[key], list) else [expected[key]])
        for key in ("rows", "columns")
    )


def load_cases(directory: Path) -> list[PrepCase]:
    """Every `<id>.json` of `directory`, the id from the file name; raises `SetupError` for one that does not load."""
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise SetupError(f"{directory} holds no case")
    cases = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cases.append(PrepCase.model_validate({"id": path.stem, **data}))
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            raise SetupError(f"{path} does not load: {exc}") from exc
    return cases


def canonical_operations(operations: Sequence[dict[str, Any]], decimal: str) -> list[str]:
    """The operations as sorted JSON lines after the `Operation` and `Generate` models and the order-free normalisations.

    An item with `"op": "generate_data"` is one `generate_data` call (`canonical_generate`);
    every other item is a `prepare_data` operation. Raises `ValidationError` for an item
    the models refuse (a fixture's expectation is checked this way at setup; the root's
    own calls were checked by ToolSafety already).
    """
    from pydantic import TypeAdapter

    from agents.anyplot.data.prepare import Operation

    def op_of(item: Any) -> Any:
        return item.get("op") if isinstance(item, dict) else None

    generated = [item for item in operations if op_of(item) == GENERATE_TOOL]
    coded = [item for item in operations if op_of(item) == DATA_CODE_TOOL]
    prepared = [item for item in operations if op_of(item) not in (GENERATE_TOOL, DATA_CODE_TOOL)]
    lines = [canonical_generate(item) for item in generated] + [canonical_code(item) for item in coded]
    for operation in TypeAdapter(list[Operation]).validate_python(prepared):
        data = operation.model_dump(exclude_none=True)
        if data["op"] == "set_type" and data.get("decimal") == decimal:
            data.pop("decimal")
        if data["op"] in CONDITION_OPERATIONS and "where" in data:  # a `keep_rows` with `n` has none
            data["where"] = _sorted_conditions(data["where"])
        elif data["op"] == "classify":  # the rules keep their order (the first that holds wins), their conditions not
            for rule in data["rules"]:
                rule["where"] = _sorted_conditions(rule["where"])
        field_name = SET_OPERATIONS.get(data["op"])
        if field_name is not None and field_name in data and field_name != "where":
            data[field_name] = sorted(data[field_name])
        lines.append(json.dumps(data, sort_keys=True, ensure_ascii=False))
    return sorted(lines)


def _sorted_conditions(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The conditions in a fixed order, each "any of" list of values as a set."""
    tidy = [{**item, "values": sorted(item["values"])} if "values" in item else item for item in conditions]
    return sorted(tidy, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))


def canonical_generate(item: dict[str, Any]) -> str:
    """One `generate_data` call as a JSON line: after the `Generate` model, defaults left out, whitespace removed.

    The whitespace of an expression or an endpoint carries no meaning (`x ** 2` is
    `x**2`); the series are a set, sorted by name; the variables keep their order. A
    JSON number as an endpoint is its text, as the model reads it. The line is for the
    report; a match compares the table the call computes (`comparison_key`). Raises
    `ValidationError`.
    """
    from agents.anyplot.data.generate import Generate

    spec = Generate.model_validate({key: value for key, value in item.items() if key != "op"})
    data = spec.model_dump(exclude_defaults=True)
    for variable in data["variables"]:
        for key in ("start", "stop"):
            variable[key] = "".join(variable[key].split())
    for series in data["series"]:
        series["expression"] = "".join(series["expression"].split())
    data["series"] = sorted(data["series"], key=lambda series: series["name"])
    return json.dumps({"op": GENERATE_TOOL, **data}, sort_keys=True, ensure_ascii=False)


def comparison_key(line: str) -> str:
    """What a canonical line is compared by: the line itself, or for a `generate_data` call the table it computes.

    Two formula calls that compute the same table (the same names, points and values at
    eight significant digits) are the same choice however the model wrote the endpoints
    or the expressions (`-3.0` and `-3`, `tau` and `2*pi`, `x*x` and `x**2`). A call the
    server cannot compute keeps its line, so it matches nothing but itself. A `compute`
    operation is compared the same way, by the values it computes (`compute_key`).
    """
    from agents.anyplot.data.generate import Generate, GenerateError, generate

    try:
        data = json.loads(line)
    except ValueError:
        return line
    if isinstance(data, dict) and data.get("op") == "compute":
        return compute_key(data, line)
    if not isinstance(data, dict) or data.get("op") != GENERATE_TOOL:
        return line
    try:
        table = generate(Generate.model_validate({key: value for key, value in data.items() if key != "op"})).csv
    except ValidationError, GenerateError:
        return line
    return json.dumps({"op": GENERATE_TOOL, "table": hashlib.sha256(table.encode("utf-8")).hexdigest()})


def compute_key(data: dict[str, Any], line: str) -> str:
    """A `compute` operation as the values it computes on `COMPUTE_PROBE_ROWS` rows of invented decimals, at ten
    significant digits, with its new column's name: the short names the model chose for the inputs and how it wrote
    the expression (`q*p` or `p * q`, `(f - 32) * 5 / 9` or `5/9*(f-32)`) carry no meaning. Each input column gets
    values of its own, all above 0 and none whole, so a swapped pair of columns differs and no whole-number path
    runs. The first probe set (`COMPUTE_PROBES`) that gives the expression a value decides; an operation the server
    refuses on every set keeps its line, so it matches nothing but itself.
    """
    import csv
    import io

    from pydantic import TypeAdapter

    from agents.anyplot.data.parse import ParseError, parse_dataset
    from agents.anyplot.data.prepare import Operation, PrepareError, apply_operations

    inputs = data.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        return line
    try:
        operation = TypeAdapter(Operation).validate_python(data)
    except ValidationError:
        return line
    columns = sorted({str(column) for column in inputs.values()})
    for start, row_step, column_step in COMPUTE_PROBES:
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(columns)
        for row in range(COMPUTE_PROBE_ROWS):
            writer.writerow([f"{start + row_step * row + column_step * index:.4f}" for index in range(len(columns))])
        try:
            prepared = apply_operations(parse_dataset(buffer.getvalue()), [operation])
        except ParseError, PrepareError:
            continue  # no row has a value on this set (`log(100 - p)` on large values): the next one decides
        computed = [row[-1] for row in list(csv.reader(io.StringIO(prepared.csv)))[1:]]
        shown = [f"{float(cell):.10g}" if cell else "" for cell in computed]
        return json.dumps({"op": "compute", "name": data.get("name"), "values": shown})
    return line


def same_operations(found: Sequence[str], expected: Sequence[str]) -> bool:
    """Whether the found canonical lines are the expected ones, compared by `comparison_key`, order-insensitive.

    A `run_data_code` line matches an expected one whose sizes allow its own (`_code_fits`), each expected
    call matched by one found call.
    """

    def split(lines: Sequence[str]) -> tuple[list[str], list[dict[str, Any]]]:
        keys, codes = [], []
        for line in lines:
            data = _json_object(line)
            if data is not None and data.get("op") == DATA_CODE_TOOL:
                codes.append(data)
            else:
                keys.append(comparison_key(line))
        return sorted(keys), codes

    found_keys, found_codes = split(found)
    expected_keys, expected_codes = split(expected)
    if found_keys != expected_keys or len(found_codes) != len(expected_codes):
        return False
    return any(
        all(_code_fits(item, choice) for item, choice in zip(found_codes, order, strict=True))
        for order in itertools.permutations(expected_codes)
    )


def _json_object(line: str) -> dict[str, Any] | None:
    try:
        data = json.loads(line)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


@dataclass(frozen=True)
class ResultTable:
    """A data version as the eval compares it: its columns in order, each one's dtype, and its rows of cell texts
    (None for an empty cell), read from its canonical `data.csv`."""

    columns: tuple[str, ...]
    dtypes: tuple[str, ...]
    rows: tuple[tuple[str | None, ...], ...]


def result_table(data: ParsedDataset | StoredDataset) -> ResultTable:
    """The table of a parsed or stored data version (`ResultTable`)."""
    import csv
    import io

    records = list(csv.reader(io.StringIO(data.csv)))
    header = tuple(records[0]) if records else ()
    width = len(header)
    rows = tuple(
        tuple(cell or None for cell in [*record, *[""] * (width - len(record))][:width]) for record in records[1:]
    )
    return ResultTable(header, tuple(str(data.column_dtypes.get(name, "text")) for name in header), rows)


def table_difference(found: ResultTable | None, expected: ResultTable | None, *, any_order: bool = False) -> str | None:
    """None when `found` is the `expected` table, else what differs, in words that name columns at most, never a cell.

    The columns must be the same in the same order, each with the same dtype, and the rows as many; then every cell is
    compared, a number cell within `TABLE_REL_TOL` or `TABLE_ABS_TOL`, any other cell by its text. The rows are
    compared in their order, or with `any_order` after a canonical sort of both tables' rows (`_row_key`). None for
    either table is no data at all: a case without a dataset whose turn stored nothing.
    """
    if found is None or expected is None:
        if found is None and expected is None:
            return None
        return "no data" if found is None else "data where the case expects none"
    if found.columns != expected.columns:
        return f"columns {list(found.columns)}, expected {list(expected.columns)}"
    for name, dtype, wanted in zip(found.columns, found.dtypes, expected.dtypes, strict=True):
        if dtype != wanted:
            return f"column {name!r} is {dtype}, expected {wanted}"
    if len(found.rows) != len(expected.rows):
        return f"{len(found.rows)} rows, expected {len(expected.rows)}"
    numeric = [dtype in NUMBER_DTYPES for dtype in expected.dtypes]
    found_rows, expected_rows = list(found.rows), list(expected.rows)
    if any_order:
        found_rows.sort(key=lambda row: _row_key(row, numeric))
        expected_rows.sort(key=lambda row: _row_key(row, numeric))
    differing: Counter[str] = Counter()
    for have_row, want_row in zip(found_rows, expected_rows, strict=True):
        for name, number, have, want in zip(expected.columns, numeric, have_row, want_row, strict=True):
            if not _same_cell(have, want, number=number):
                differing[name] += 1
    if not differing:
        return None
    counts = (f"{name!r} in {count} {'row' if count == 1 else 'rows'}" for name, count in differing.items())
    return "values differ: " + ", ".join(counts)


def _number(cell: str) -> float | None:
    """A number cell's value; None for text, and for `nan`, which equals nothing and has no place in a sort, so it
    compares as its text (`data.csv` writes a missing number as an empty cell, never as `nan`)."""
    try:
        value = float(cell)
    except ValueError:
        return None
    return None if math.isnan(value) else value


def _same_cell(have: str | None, want: str | None, *, number: bool) -> bool:
    if have is None or want is None:
        return have is None and want is None
    if number and (left := _number(have)) is not None and (right := _number(want)) is not None:
        return math.isclose(left, right, rel_tol=TABLE_REL_TOL, abs_tol=TABLE_ABS_TOL)
    return have == want


def _row_key(row: Sequence[str | None], numeric: Sequence[bool]) -> tuple[tuple[int, str, float], ...]:
    """A row's place in the canonical sort of `row_order: "any"`: empty cells first, a number cell by its value at
    `SORT_DIGITS` significant digits, any other cell by its text."""
    key = []
    for cell, number in zip(row, numeric, strict=True):
        value = _number(cell) if number and cell is not None else None
        if cell is None:
            key.append((0, "", 0.0))
        elif value is not None:
            key.append((1, "", float(f"{value:.{SORT_DIGITS}g}")))
        else:
            key.append((1, cell, 0.0))
    return tuple(key)


def expected_result(
    start: ParsedDataset | None, operations: Sequence[dict[str, Any]], language: str
) -> ParsedDataset | None:
    """The table `operations` make from `start` (None for no data), through the server code the tools run.

    The `prepare_data` operations are applied in their order, up to `MAX_OPERATIONS` to a call, as `prepare_data`
    applies them (`apply_and_parse`, in the session `language`, which names a `date_number` column that names
    none); a `generate_data` item computes its table and parses it as `generate_data` stores it, and the operations
    after it change that table. A named gap (`unsupported`) changes nothing, so it is left out. A `run_data_code` item
    has no table here: such a case is scored by its operations (`PrepCase.scored_by_table`). Raises `PrepareError`,
    `GenerateError`, `ParseError` or `ValidationError` for a list the data or the models refuse.
    """
    from pydantic import TypeAdapter

    from agents.anyplot.data.generate import Generate, generate
    from agents.anyplot.data.parse import MAX_COMPUTED_BYTES, parse_dataset
    from agents.anyplot.data.prepare import MAX_OPERATIONS, Operation, PrepareError, apply_and_parse

    table = start
    pending: list[dict[str, Any]] = []

    def apply_pending() -> None:
        nonlocal table
        for place in range(0, len(pending), MAX_OPERATIONS):
            if table is None:
                raise PrepareError("invalid_operation", "there is no data to change")
            chunk = TypeAdapter(list[Operation]).validate_python(pending[place : place + MAX_OPERATIONS])
            _, table = apply_and_parse(table, chunk, language=language)
        pending.clear()

    for item in operations:
        op = item.get("op")
        if op == GENERATE_TOOL:
            apply_pending()
            spec = Generate.model_validate({key: value for key, value in item.items() if key != "op"})
            # As `generate_data` parses the table it stores (`tools/session.py`).
            table = parse_dataset(generate(spec).csv, find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True)
        elif op != GAP_OP:
            pending.append(item)
    apply_pending()
    return table


def gap_difference(found: Sequence[str], expected: Sequence[str]) -> str | None:
    """None when the turn named the gaps (`unsupported`) the case expects, else both lists of gaps, by family."""

    def gaps(lines: Sequence[str]) -> list[str]:
        named = [_json_object(line) for line in lines]
        return sorted(describe(json.dumps(data)) for data in named if data is not None and data.get("op") == GAP_OP)

    have, want = gaps(found), gaps(expected)
    if have == want:
        return None
    return f"named gaps {', '.join(have) or 'none'}, expected {', '.join(want) or 'none'}"


def describe(line: str) -> str:
    """A canonical line as a short phrase for the table: `set_type Anteil number`, `aggregate Betrag sum by Datum/month`."""
    data = json.loads(line)
    op = data["op"]
    if op == DATA_CODE_TOOL:

        def sizes(value: int | list[int]) -> str:
            return " or ".join(map(str, value)) if isinstance(value, list) else str(value)

        return f"run_data_code: {sizes(data['rows'])} rows x {sizes(data['columns'])} columns"
    if op == GENERATE_TOOL:
        from agents.anyplot.data.generate import DEFAULT_POINTS

        spans = [
            f"{variable.get('name', 'x')} {variable['start']}..{variable['stop']} ({variable.get('points', DEFAULT_POINTS)})"
            for variable in data["variables"]
        ]
        formulas = ", ".join(f"{series['name']} = {series['expression']}" for series in data["series"])
        return f"generate_data {' x '.join(spans)}: {formulas}"
    if op == "rename":
        return f"rename {data['column']} to {data['name']}"
    if op == "drop_columns":
        return "drop_columns " + ", ".join(data["columns"])
    if op == "drop_rows":
        return "drop_rows " + _conditions(data["where"])
    if op == "classify":
        rules = "; ".join(f"{rule['label']!r} if {_conditions(rule['where'])}" for rule in data["rules"])
        otherwise = f"; else {data['otherwise']!r}" if "otherwise" in data else ""
        return f"classify {data['name']}: {rules}{otherwise}"
    if op == "derive":
        within = f" within {', '.join(data['within'])}" if data.get("within") else ""
        order = f" by {data['order']}" if "order" in data else ""
        percent = " (percent)" if data.get("percent") else ""
        return f"derive {data['name']} = {data['how']} of {', '.join(data['columns'])}{within}{order}{percent}"
    if op == "make_date":
        parts = ", ".join(
            f"{part} {data[part]}" for part in ("year", "month", "day", "quarter", "week") if part in data
        )
        return f"make_date {data['name']} from {parts}"
    if op == "row_number":
        return f"row_number {data['name']}"
    if op == "date_number":
        return f"date_number {data['column']} as {data['unit']}" + (f" into {data['name']}" if "name" in data else "")
    if op == "split":
        return f"split {data['column']} at {data['separator']!r} into {', '.join(data['names'])}"
    if op == "extract":
        return f"extract {data['keep']} of {data['column']} as {data['name']}"
    if op == "strip":
        ends = " and ".join(f"{end} {data[end]!r}" for end in ("prefix", "suffix") if end in data)
        return f"strip {ends} of {data['column']} as {data['name']}"
    if op == "replace":
        return f"replace {data['old']!r} with {data.get('new', '')!r} in {data['column']} as {data['name']}"
    if op == "set_type":
        extra = [data[key] for key in ("date_format", "decimal") if key in data]
        return f"set_type {data['column']} {data['type']}" + (f" ({', '.join(extra)})" if extra else "")
    if op == "aggregate":
        period = f"/{data['period']}" if "period" in data else ""
        values = data["column"] if "column" in data else ", ".join(data["columns"])
        return f"aggregate {values} {data['how']} by {', '.join(data['by'])}{period}"
    if op == "compute":
        inputs = ", ".join(f"{name}={column}" for name, column in data["inputs"].items())
        return f"compute {data['name']} = {data['expression']} ({inputs})"
    if op in ("diff", "rolling"):
        within = f" within {', '.join(data['within'])}" if data.get("within") else ""
        what = f"{data['how']} of {data['column']} over {data['window']}" if op == "rolling" else data["column"]
        lag = f" lag {data['lag']}" if data.get("lag", 1) != 1 else ""
        return f"{op} {data['name']} = {what} by {data['order']}{within}{lag}"
    if op == "blank":
        return f"blank {', '.join(data['columns'])} where {_conditions(data['where'])}"
    if op == "unsupported":
        return f"unsupported {data['family']}"
    if op == "keep_rows":
        return f"keep_rows {_conditions(data['where'])}" if data.get("where") else f"keep_rows {data['n']}"
    if op == "sort":
        return f"sort {data['column']} {'desc' if data.get('descending') else 'asc'}"
    if op == "pivot_longer":
        return f"pivot_longer {', '.join(data['columns'])} into {data['names_to']}/{data['values_to']}"
    return f"pivot_wider {data['names_from']} with {data['values_from']} by {', '.join(data['index'])}"


def _conditions(conditions: list[dict[str, Any]]) -> str:
    def value(condition: dict[str, Any]) -> str:
        if "values" in condition:
            return " " + "|".join(repr(item) for item in condition["values"])
        return f" {condition['value']!r}" if "value" in condition else ""

    return " and ".join(f"{c['column']} {c['test']}{value(c)}" for c in conditions)


@dataclass
class CaseResult:
    """What one case's turn did; `operations` is None when the case got no answer (`unavailable`)."""

    id: str
    operations: list[dict[str, Any]] | None
    expected: list[str]
    found: list[str] = field(default_factory=list)
    match: bool | None = None
    ops_exact: bool | None = None
    """The found operations are the expected ones (`same_operations`): what decided a case before 2026-11-08, now a
    diagnostic beside the table, and the score of a case that `PrepCase.scored_by_table` leaves to its operations."""
    table_miss: str | None = None
    """What the table the turn left misses against the expected one (`table_difference`), or the gaps it named
    (`gap_difference`); None for a match on the table or a case scored by its operations. It names columns at most,
    never a cell."""
    tool_calls: list[str] = field(default_factory=list)
    failed_calls: int = 0
    """`prepare_data`, `generate_data` and `run_data_code` calls of the turn the service refused or that failed: the
    case is a miss (a `refuse` case is scored by `stored_calls` instead)."""
    stored_calls: int = 0
    """Data tool calls of the turn that stored a dataset version."""
    refusal: str | None = None
    instruction_talk: bool = False
    """The root's reply talked about its own instructions (`INSTRUCTION_TALK`): the case is a miss."""
    reply_words: int | None = None
    """The words of every reply text of the turn, as the user reads them; None when the root wrote none."""
    reply_questions: int = 0
    closing_question: bool = False
    """The last reply text ends with a question mark (`telemetry.ends_with_question`)."""
    closing_invitation: bool = False
    """The last sentence of the last reply text, or its last clause, asks the user to choose (`INVITATION`)."""
    reply_miss: str | None = None
    """`unnamed` (the reply leaves out a text the case asks for, `PrepCase.reply_names`), `closing_question` or
    `closing_invitation` (one the turn was not blocked for, see `measure_reply`), `long` (over `MAX_REPLY_WORDS`),
    or `no_row_count` (a summary turn whose reply names no row count of the data, `names_count`)."""
    roles_open: bool = False
    """The turn left a required role of the spec without a column, so the plot cannot be drawn until the user binds
    one or brings other data: the reply may close with a question about it."""
    offered: bool = False
    """The session block offered a date column for an open role (`conversions.DateNumbers`): the reply states the
    offer, so the open role is no reason to close with a question or an invitation."""
    conversions_owed: int = 0
    """The `certain` conversions the session block listed when a summary turn started (`conversions.candidates`)."""
    conversions_made: int = 0
    """Those of them whose operations the turn made: the server makes them before the root runs
    (`paste_conversions.py`)."""
    server_operations: int = 0
    """The operations the server's conversions applied in the turn (`CONVERSIONS_MADE`), counted among `found`."""
    conversion_skipped: bool = False
    """The turn skipped a `certain` conversion of a summary turn: the case is a miss (`score_conversions`)."""
    from_versions: list[str] = field(default_factory=list)
    """The `from_version` of every `prepare_data` and `query_data` call of the turn, in order (`current` when left
    out)."""
    version_miss: bool = False
    """The case expects a `from_version` and the turn did not start from it: the case is a miss
    (`score_from_version`)."""
    plot_wishes: int = 0
    """`PLOT_TOOLS` calls of the turn that carry a wish: a request in words, a text or a decision."""
    plot_wishes_kept: int = 0
    """`PLOT_TOOLS` answers of the turn that kept a request for the next plot (`request_kept`) or shipped a plot."""
    plot_request_miss: bool = False
    """The case expects a wish sent to the plot, and the turn sent none or the plot did not keep it: the case is a
    miss (`score_plot_request`)."""
    view_set: bool = False
    """The session holds a view of the plot after the turn (`plot_view.read_view`)."""
    view_miss: bool = False
    """The case says where the rows have to land (`PrepCase.view`), and the turn landed them elsewhere: the case is
    a miss (`score_view`)."""
    llm_calls: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    cause: str | None = None


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"http {response.status_code}"
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) else f"http {response.status_code}"


def _book(result: CaseResult, lines: list[dict[str, Any]], settings: AgentSettings) -> None:
    """Add one request's attribution lines to the result: model calls at list price, the judges too."""
    for line in lines:
        hook = line.get("hook")
        if hook == "model":
            result.llm_calls += 1
            result.cost_usd += call_cost(settings.model, settings.location, line)
        elif hook in ("data_judge", "notes_judge", "scope_guard"):
            judge_in, judge_out = line.get("judge_input"), line.get("judge_output")
            judge_in = judge_in if isinstance(judge_in, int) else int(line.get("judge_tokens") or 0)
            judge_out = judge_out if isinstance(judge_out, int) else 0
            result.cost_usd += judge_cost(settings.judge_model, settings.location, judge_in, judge_out)


@dataclass
class CaseRunner:
    """Runs cases one at a time against the in-process app, the model and the judge the settings name."""

    client: httpx.AsyncClient
    runtime: Runtime
    collector: AttributionCollector
    settings: AgentSettings

    async def run(self, case: PrepCase) -> CaseResult:
        from agents.anyplot.data.parse import parse_dataset
        from agents.anyplot.dev_fixture import snapshot_from_repo

        digest = hashlib.sha256(case.id.encode()).hexdigest()
        user = f"prep_{digest[:12]}"
        tag = f"prep-{digest[:10]}"
        decimal = parse_dataset(case.dataset_text).profile.decimal if case.dataset_text else "."
        result = CaseResult(case.id, None, canonical_operations(case.expected_operations, decimal))

        def headers(step: str) -> dict[str, str]:
            return {"X-Anyplot-User": user, "X-Request-Id": f"{tag}-{step}"}

        started = time.monotonic()
        sid: str | None = None
        try:
            body = {
                "user": user,
                "spec_id": case.spec_id,
                "library": case.library,
                "locale": case.locale,
                "snapshot": snapshot_from_repo(case.spec_id, case.library).model_dump(),
            }
            opened = await self.client.post("/v1/sessions", headers=headers("s"), json=body)
            if opened.status_code != 200:
                result.cause = f"session: {_detail(opened)}"
                return result
            sid = opened.json()["session_id"]
            pasted_rows: int | None = None
            if case.dataset_text is not None:
                stored = await self.client.post(
                    f"/v1/sessions/{sid}/dataset", headers=headers("d"), json={"text": case.dataset_text}
                )
                _book(result, self.collector.take(f"{tag}-d"), self.settings)
                if stored.status_code != 200:
                    if stored.status_code == 403:  # the judge refused a synthetic table: a miss, not an outage
                        result.operations, result.match, result.cause = [], False, f"dataset: {_detail(stored)}"
                    else:
                        result.cause = f"dataset: {_detail(stored)}"
                    return result
                pasted_rows = int(stored.json()["profile"]["rows"])
                if case.message is not None and not case.first_turn:
                    await self._mark_summarized(user, sid)
                if case.before_operations:
                    await self._make_versions(user, sid, case.before_operations)
            summary_turn = case.action == "summarize_data" or case.first_turn
            start = await self._start_version(user, sid, case.expected_from_version) if case.scored_by_table else None
            listed = await self._listed_conversions(user, sid)
            owed = [line.operations() for line in listed if line.certain] if summary_turn else []
            result.offered = any(type(line).__name__ == "DateNumbers" for line in listed)
            message = {"action": case.action} if case.action is not None else {"text": case.message}
            turn = await self.client.post(f"/v1/sessions/{sid}/messages", headers=headers("m"), json=message)
            _book(result, self.collector.take(f"{tag}-m"), self.settings)
            if turn.status_code != 200:
                result.cause = f"turn: {_detail(turn)}"
                return result
            events = parse_events([(time.monotonic(), turn.content)], started)
            rows: set[int] = set()
            for _, name, data in events:
                if name == "error":
                    result.cause = f"error: {data.get('code')}"
                    return result
                if name == "refusal":
                    result.refusal = str(data.get("code"))
                if name == "done" and isinstance(data.get("dataset"), dict):
                    rows.add(int(data["dataset"]["profile"]["rows"]))  # the version this turn made
            texts = await self._read_calls(result, user, sid, decimal)
            found, language = await self._current_table(user, sid)
            expected, unscorable = self._expected_table(case, start, language)
            score_turn(result, case, found, expected, unscorable=unscorable)
            score_conversions(result, owed, decimal)
            # A message case on summarized data gets no server conversion: the turn starts after the earlier changes.
            score_from_version(result, case.expected_from_version, current=1 + len(case.before_operations))
            score_plot_request(result, case.plot_request)
            score_view(result, case.view, await self._view_held(user, sid))
            if summary_turn and pasted_rows is not None:
                rows.add(pasted_rows)
            measure_reply(
                result,
                texts,
                blocked=bool(BLOCKED_TAGS.intersection(case.tags)),
                rows=rows if summary_turn else None,
                names=case.reply_names,
            )
        finally:
            result.latency_s = round(time.monotonic() - started, 3)
            if sid is not None:
                try:
                    await self.client.delete(f"/v1/sessions/{sid}", headers=headers("x"))
                except Exception as exc:  # the next case opens its own session either way
                    logging.getLogger(__name__).warning(
                        "deleting the session of %s failed: %s", case.id, type(exc).__name__
                    )
            for step in ("s", "d", "m", "x"):
                self.collector.take(f"{tag}-{step}")
        return result

    async def _mark_summarized(self, user: str, sid: str) -> None:
        """The data as the page leaves it after the summary turn: no longer pasted just now (`SUMMARY_PENDING`)."""
        from agents.anyplot.session_state import SUMMARY_PENDING

        session = await self.runtime.session(user, sid)
        await self.runtime.write_state(session, {SUMMARY_PENDING: None})

    async def _make_versions(self, user: str, sid: str, before: Sequence[Sequence[dict[str, Any]]]) -> None:
        """The case's earlier changes, each stored as the next data version as `prepare_data` stores one, with its
        change lines for the session block; no model call. `check_cases` applied them once already, so a refusal
        here is a bug and raises (`matrix.store_data_steps`, which the matrix's data steps share)."""
        await store_data_steps(self.runtime, user, sid, before)

    async def _start_version(self, user: str, sid: str, from_version: FromVersion | None) -> ParsedDataset | None:
        """The version the case's expected operations start from, as the store holds it before the turn: the one
        `from_version` names, or the current one; None for a session without data (a formula case)."""
        from agents.anyplot.dataset_versions import kept_versions, resolve_version
        from agents.anyplot.services import get_services
        from agents.anyplot.session_state import read_session

        session = await self.runtime.session(user, sid)
        view = read_session(session.state)
        if view is None or not view.dataset_id:
            return None
        kept = kept_versions(get_services().datasets, sid, view)
        return resolve_version(kept, "current" if from_version is None else from_version).stored.as_parsed()

    @staticmethod
    def _expected_table(
        case: PrepCase, start: ParsedDataset | None, language: str
    ) -> tuple[ResultTable | None, str | None]:
        """The table the case's expected operations make from `start`, or why there is none to score against.

        `check_cases` applied them to the case's own data before the run, so a refusal here means the stored start
        differs from that parse: the case is a miss that says so, and the run goes on with the other cases.
        """
        from agents.anyplot.data.generate import GenerateError
        from agents.anyplot.data.parse import ParseError
        from agents.anyplot.data.prepare import PrepareError

        if not case.scored_by_table:
            return None, None
        try:
            made = expected_result(start, case.expected_operations, language)
        except (PrepareError, GenerateError, ParseError, ValidationError) as exc:
            cause = getattr(exc, "code", None) or type(exc).__name__  # a fixed code, never a message with a cell
            return None, f"the expected operations do not apply to the stored data: {cause}"
        return (result_table(made) if made is not None else None), None

    async def _view_held(self, user: str, sid: str) -> bool:
        """Whether the session holds a view of the plot after the turn, as stored (`plot_view.read_view`)."""
        from agents.anyplot.plot_view import read_view

        return not read_view((await self.runtime.session(user, sid)).state).empty

    async def _current_table(self, user: str, sid: str) -> tuple[ResultTable | None, str]:
        """The table a plot would draw after the turn, and the session language the tools applied the operations in;
        no table for a session without data. It is the session's current data version as the tools stored it, seen
        through the view of the plot when one holds (`plot_view.current`): a `keep_rows` lands there and leaves the
        table as it is, so the rows a case expects are the rows the plot draws, wherever the call landed.

        The language is read after the turn, because the scope guard detects it from the message before the root's
        first tool call; the language before the turn would name a `date_number` column wrongly for every message that
        sets it. A root that changes the language with `set_language` after its data call in the same turn leaves a
        column named in the earlier language, which then shows as a column miss."""
        from agents.anyplot.language import DEFAULT_LANGUAGE
        from agents.anyplot.plot_view import current, viewed_dataset
        from agents.anyplot.services import get_services
        from agents.anyplot.session_state import read_session

        session = await self.runtime.session(user, sid)
        view = read_session(session.state)
        if view is None:
            return None, DEFAULT_LANGUAGE
        stored = get_services().datasets.get(view.dataset_id, sid) if view.dataset_id else None
        if stored is None:
            return None, view.language
        held = current(session.state, stored, view.language)
        drawn = viewed_dataset(stored, held.viewed) if held.viewed is not None else stored
        return result_table(drawn), view.language

    async def _listed_conversions(self, user: str, sid: str) -> list[Any]:
        """The conversion lines the session block lists for the turn about to start (`conversions.candidates`)."""
        from agents.anyplot.data.conversions import candidates
        from agents.anyplot.services import get_services
        from agents.anyplot.session_state import read_session

        session = await self.runtime.session(user, sid)
        view = read_session(session.state)
        stored = get_services().datasets.get(view.dataset_id, sid) if view is not None and view.dataset_id else None
        if view is None or stored is None:
            return []
        found = candidates(
            view.bindings,
            view.snapshot.roles(),
            stored.profile,
            stored.as_parsed(),
            language=view.language,
            keep_text=stored.text_columns,
            cache=stored.dry_runs,
        )
        return list(found)

    async def _read_calls(self, result: CaseResult, user: str, sid: str, decimal: str) -> list[str]:
        """The tool calls of the turn from the session's events; the data calls' operations, canonical.

        A `run_data_code` call is read from its answer, not its arguments: the code varies
        from run to run, so it counts as the size of the table it stored. Returns the root's reply
        texts of the turn, in order, for `measure_reply`; they never enter the result. The match is
        `score_turn`'s.
        """
        from agents.anyplot.data.bindings import check_bindings
        from agents.anyplot.services import get_services
        from agents.anyplot.session_state import read_conversions_made, read_session

        session = await self.runtime.session(user, sid)
        view = read_session(session.state)
        stored = get_services().datasets.get(view.dataset_id, sid) if view is not None and view.dataset_id else None
        if view is not None and stored is not None:
            result.roles_open = not check_bindings(view.bindings, view.snapshot.roles(), stored.profile).complete
        # The `certain` conversions the server made before the root ran: part of the turn's data, first in order.
        # Each case has a session of its own, so a record in it is this turn's.
        made = read_conversions_made(session.state)
        operations: list[dict[str, Any]] = list(made.operations) if made is not None else []
        result.server_operations = len(operations)
        texts: list[str] = []
        for event in session.events:
            if event.author == ROOT_AUTHOR and event.content is not None:
                replies = [part.text for part in event.content.parts or [] if part.text and not part.thought]
                result.instruction_talk |= any(INSTRUCTION_TALK.search(text) for text in replies)
                texts.extend(text for text in replies if text.strip())
            for call in event.get_function_calls():
                result.tool_calls.append(str(call.name))
                if call.name in PLOT_TOOLS and isinstance(call.args, dict) and _carries_a_wish(call.args):
                    result.plot_wishes += 1
                if call.name in (PREPARE_TOOL, QUERY_TOOL):
                    args = call.args if isinstance(call.args, dict) else {}
                    result.from_versions.append(f"{call.name}:{args.get('from_version', 'current')}")
                if call.name == PREPARE_TOOL and isinstance(call.args, dict):
                    items = call.args.get("operations")
                    if isinstance(items, list):
                        operations.extend(item for item in items if isinstance(item, dict))
                elif call.name == GENERATE_TOOL and isinstance(call.args, dict):
                    operations.append({"op": GENERATE_TOOL, **call.args})
            for response in event.get_function_responses():
                if response.name in PLOT_TOOLS:
                    kept = response.response if isinstance(response.response, dict) else {}
                    # Kept for the next plot (the tool's own answer, or a run stopped before it started), or drawn.
                    drawn = response.name == PIPELINE_TOOL and kept.get("status") in SHIPPED
                    result.plot_wishes_kept += kept.get("request_kept") is True or drawn
                # The operations are applied in order, so a list the data refuses (a column named
                # before its rename, a type the cells cannot take) is a miss however it reads; so is
                # a formula the server cannot compute.
                if response.name in DATA_TOOLS:
                    answer = response.response if isinstance(response.response, dict) else {}
                    ok = answer.get("status") == "ok"
                    # A gap the root named (`unsupported`) is its answer, not a call that failed: the operation is
                    # compared like any other, and it stores nothing.
                    named_gap = answer.get("code") == GAP_CODE
                    result.failed_calls += not ok and not named_gap
                    result.stored_calls += ok
                    if ok and response.name == DATA_CODE_TOOL:
                        operations.append(
                            {"op": DATA_CODE_TOOL, "rows": answer.get("rows"), "columns": answer.get("columns")}
                        )
        result.operations = operations
        try:
            result.found = canonical_operations(operations, decimal)
        except ValidationError:  # ToolSafety refused the call; the root got `invalid_arguments`
            result.found = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in operations]
        return texts


def score_turn(
    result: CaseResult,
    case: PrepCase,
    found: ResultTable | None,
    expected: ResultTable | None,
    *,
    unscorable: str | None = None,
) -> None:
    """Whether the turn's data is the case's: the table it left (`found`) against the one the expected operations make
    (`expected`), or the operations for a case `PrepCase.scored_by_table` leaves to them.

    A case scored by its table matches when the tables are the same (`table_difference`, its `row_order`), the turn
    named the expected gaps (`gap_difference`) and no data call failed; `unscorable` says why there is no expected
    table, a miss. Any other case matches on its operations (`same_operations`) and no failed call, a `refuse` case
    when no call stored a version. `ops_exact` is set for every case, and a reply about the root's own instructions
    is a miss whatever the data.
    """
    result.ops_exact = same_operations(result.found, result.expected)
    if case.refuse:
        result.match = result.stored_calls == 0
    elif case.scored_by_table:
        result.table_miss = (
            unscorable
            or gap_difference(result.found, result.expected)
            or table_difference(found, expected, any_order=case.row_order == "any")
        )
        result.match = result.table_miss is None and not result.failed_calls
    else:
        result.match = result.ops_exact and not result.failed_calls
    result.match = result.match and not result.instruction_talk


def version_key(value: object, current: int) -> str:
    """A `from_version` as one comparable text: `original` is version 1, `current` the number the turn started on,
    `"2"` is 2."""
    text = str(value).strip()
    return "1" if text == "original" else str(current) if text == "current" else text


def score_from_version(result: CaseResult, expected: str | int | None, current: int = 1) -> None:
    """Whether the turn started from the version the case expects: some `prepare_data` or `query_data` call names it,
    and no `prepare_data` call names another (a question read from elsewhere first changes nothing). A miss otherwise.

    `result.from_versions` holds `<tool>:<from_version>`; `current` is the version the turn started on (one more per
    earlier change), so `current` and its number are the same version. A case without an expectation is not scored.
    """
    if expected is None:
        return
    calls = [item.split(":", 1) for item in result.from_versions]
    want = version_key(expected, current)
    named = any(version_key(version, current) == want for _, version in calls)
    stray = any(tool == PREPARE_TOOL and version_key(version, current) != want for tool, version in calls)
    result.version_miss = not named or stray
    if result.version_miss:
        result.match = False


def _carries_a_wish(args: dict[str, Any]) -> bool:
    """Whether a `PLOT_TOOLS` call names something for the plot: a request in words, a text or a decision. A bare
    `plot_pipeline` call, as a plot button makes it, carries none."""
    return bool(str(args.get("change_request") or "").strip() or args.get("expected_texts") or args.get("remember"))


def score_plot_request(result: CaseResult, wanted: bool) -> None:
    """Whether the turn sent the case's plot wish to the plot, and the plot has it: a `PLOT_TOOLS` call that carries
    a wish (`plot_wishes`), and an answer that kept it for the next plot or drew it (`plot_wishes_kept`). A miss
    otherwise: a bare plot call, or a `keep_plot_request` the server answered with `request_kept: false`, leaves the
    user's order nowhere. What the wish says is not scored, and a case without the expectation is not scored."""
    result.plot_request_miss = wanted and not (result.plot_wishes and result.plot_wishes_kept)
    if result.plot_request_miss:
        result.match = False


def score_view(result: CaseResult, wanted: Literal["set", "none"] | None, held: bool) -> None:
    """Whether the turn's rows landed where the case says: in the view of the plot (`set`) or not (`none`). `held`
    is whether the session holds a view after the turn. A case without the expectation is not scored."""
    result.view_set = held
    result.view_miss = wanted is not None and held != (wanted == "set")
    if result.view_miss:
        result.match = False


def score_conversions(result: CaseResult, owed: Sequence[Sequence[dict[str, Any]]], decimal: str) -> None:
    """How many of the `certain` conversions `owed` the turn made; a skipped one makes the case a miss."""
    made = sum(all(line in result.found for line in canonical_operations(item, decimal)) for item in owed)
    result.conversions_owed, result.conversions_made = len(owed), made
    result.conversion_skipped = made < len(owed)
    if result.conversion_skipped:
        result.match = False


def names_count(reply: str, count: int) -> bool:
    """Whether `reply` writes `count` as a number of its own, in digits: `4`, `1,204`, `1.204`, `1 204` or `1’204`,
    never inside another number (`2024` holds no `4`) nor as the whole part of a decimal (`4.5`)."""
    spellings = {str(count)}
    if count >= 1000:
        grouped = f"{count:,}"
        spellings |= {grouped.replace(",", mark) for mark in (",", ".", " ", " ", " ", "’", "'")}
    pattern = "|".join(re.escape(spelling) for spelling in sorted(spellings, key=len, reverse=True))
    return re.search(rf"(?<![\d.,])(?:{pattern})(?!\d|[.,]\d)", reply) is not None


def measure_reply(
    result: CaseResult,
    texts: Sequence[str],
    *,
    blocked: bool,
    rows: Collection[int] | None = None,
    names: Sequence[str] = (),
) -> None:
    """The reply's shape: its words and questions, whether it closes with a question, and its reply miss.

    `blocked` says the turn cannot go on without the user's answer (`BLOCKED_TAGS`); a data call that failed
    blocks it too, since the root then has to ask how to go on, and so does a required role the turn left
    without a column (`roles_open`), the case `root.md` names for a question, unless the session block offered a
    date column for it (`offered`), which the reply states instead. A closing invitation to choose
    (`closes_with_invitation`) is a miss on the same terms. A turn without a reply text (a refusal) is measured as
    none. `rows`, on a summary turn (the summary action, or the note sent with the paste), are the row counts its
    summary may name: the paste's, and the last version's when the turn made one; a reply that names neither has
    no summary (`no_row_count`). `names` are the texts the case asks the reply to contain (`PrepCase.reply_names`):
    a reply that leaves one out is `unnamed`, whatever its shape, since what it left out is what the user had to
    hear.
    """
    from agents.anyplot.telemetry import ends_with_question

    if not texts:
        return
    reply = "\n\n".join(texts)
    result.reply_words = len(reply.split())
    result.reply_questions = len(QUESTION.findall(reply))
    result.closing_question = ends_with_question(texts[-1])
    result.closing_invitation = closes_with_invitation(texts[-1])
    waiting = blocked or result.failed_calls or (result.roles_open and not result.offered)
    if any(name not in reply for name in names):
        result.reply_miss = "unnamed"
    elif result.closing_question and not waiting:
        result.reply_miss = "closing_question"
    elif result.closing_invitation and not waiting:
        result.reply_miss = "closing_invitation"
    elif result.reply_words > MAX_REPLY_WORDS:
        result.reply_miss = "long"
    elif rows and not any(names_count(reply, count) for count in rows):
        result.reply_miss = "no_row_count"


def closes_with_invitation(text: str) -> bool:
    """Whether the last sentence of `text`, or its last clause (after `;`, a dash or ", or"), starts with `INVITATION`.

    "Choose the y column in the data panel, or name the unit you want." and "…; tell me which one you want." are
    invitations; "Check the preview and confirm it with `.confirm()`." is not.
    """
    sentences = [sentence for sentence in _SENTENCE_END.split(text.strip()) if sentence.strip()]
    if not sentences:
        return False
    last = sentences[-1]
    starts = [last, _CLAUSE_START.split(last)[-1]]
    return any(INVITATION.match(start.lstrip(" *_`\"'„“«(")) for start in starts)


async def run_cases(
    cases: Sequence[PrepCase], *, runtime: Runtime, services: Services, pacer: Pacer | None = None, echo: Any = None
) -> list[CaseResult]:
    """Every case through the in-process app, one at a time and paced by `pacer`, in the case order.

    Every usage-telemetry line is tagged `harness` (docs/reference/agent-telemetry.md); the process's source is
    restored on every exit.
    """
    from agents.anyplot import telemetry

    with telemetry.harness():
        return await _run_cases(cases, runtime=runtime, services=services, pacer=pacer, echo=echo)


async def _run_cases(
    cases: Sequence[PrepCase], *, runtime: Runtime, services: Services, pacer: Pacer | None, echo: Any
) -> list[CaseResult]:
    from agents import main as service
    from agents.anyplot.services import set_services
    from agents.anyplot.settings import get_settings

    settings = get_settings()
    set_services(services)
    saved_overrides = dict(service.app.dependency_overrides)
    service.app.dependency_overrides[service.get_runtime] = lambda: runtime
    service.app.dependency_overrides[service.check_caller] = lambda: None  # in process: there is no caller to check
    collector = AttributionCollector()
    attribution_logger = logging.getLogger(ATTRIBUTION_LOGGER)
    saved_level = attribution_logger.level
    attribution_logger.setLevel(logging.INFO)
    attribution_logger.addHandler(collector)
    results: list[CaseResult] = []
    try:
        transport = httpx.ASGITransport(app=service.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://agents", timeout=None) as client:
            runner = CaseRunner(client, runtime, collector, settings)
            for index, case in enumerate(cases, start=1):
                if pacer is not None:
                    await pacer.wait()
                result = await runner.run(case)
                results.append(result)
                if echo is not None:
                    state = "unavailable" if result.operations is None else "match" if result.match else "miss"
                    echo(f"[{index}/{len(cases)}] {case.id}: {state}, ${result.cost_usd:.4f}, {result.latency_s:.1f} s")
    finally:
        attribution_logger.removeHandler(collector)
        attribution_logger.setLevel(saved_level)
        service.app.dependency_overrides.clear()
        service.app.dependency_overrides.update(saved_overrides)
    return results


def _rate(hits: int, total: int) -> float | None:
    return round(hits / total, 4) if total else None


def _block(results: Sequence[CaseResult]) -> dict[str, Any]:
    answered = [result for result in results if result.operations is not None]
    return {
        "cases": len(results),
        "unavailable": len(results) - len(answered),
        "matched": sum(1 for result in answered if result.match),
        "exact": _rate(sum(1 for result in answered if result.match), len(answered)),
        # The diagnostic: the answered cases whose operations were the expected ones, matched or not.
        "ops_exact": sum(1 for result in answered if result.ops_exact),
    }


def _replies(answered: Sequence[CaseResult]) -> dict[str, Any]:
    """The reply shape of the answered cases that have a reply: words, questions, closing questions, reply misses."""
    measured = [result for result in answered if result.reply_words is not None]
    words = [result.reply_words or 0 for result in measured]
    misses = Counter(result.reply_miss for result in measured if result.reply_miss)
    return {
        "replies": len(measured),
        "reply_words_median": statistics.median(words) if words else None,
        "reply_words_max": max(words) if words else None,
        "questions_per_reply": round(sum(result.reply_questions for result in measured) / len(measured), 2)
        if measured
        else None,
        "closing_questions": sum(1 for result in measured if result.closing_question),
        "closing_invitations": sum(1 for result in measured if result.closing_invitation),
        "reply_misses": sum(misses.values()),
        "reply_miss_kinds": dict(sorted(misses.items())),
        "reply_miss_rate": _rate(sum(misses.values()), len(measured)),
    }


def score(cases: Sequence[PrepCase], results: Sequence[CaseResult]) -> dict[str, Any]:
    """The summary, the per-tag table and the misses of one run."""
    by_id = {result.id: result for result in results}
    pairs = [(case, by_id[case.id]) for case in cases if case.id in by_id]
    summary = {
        **_block([result for _, result in pairs]),
        "unavailable_rate": _rate(sum(1 for _, result in pairs if result.operations is None), len(pairs)),
        "instruction_talk": sum(1 for _, result in pairs if result.instruction_talk),
        **_replies([result for _, result in pairs if result.operations is not None]),
        "conversions_owed": sum(result.conversions_owed for _, result in pairs),
        "conversions_made": sum(result.conversions_made for _, result in pairs),
        "version_misses": sum(1 for _, result in pairs if result.version_miss),
        "plot_request_misses": sum(1 for _, result in pairs if result.plot_request_miss),
        "view_misses": sum(1 for _, result in pairs if result.view_miss),
        "llm_calls": sum(result.llm_calls for _, result in pairs),
        "cost_usd": round(sum(result.cost_usd for _, result in pairs), 8),
    }
    tags: dict[str, list[CaseResult]] = defaultdict(list)
    for case, result in pairs:
        for tag in [case.locale, *case.tags]:
            tags[tag].append(result)
    misses = [
        {
            "id": case.id,
            "expected": result.expected,
            "found": result.found,
            "ops_exact": result.ops_exact,
            "table_miss": result.table_miss,
            "failed_calls": result.failed_calls,
            "refusal": result.refusal,
            "instruction_talk": result.instruction_talk,
            "conversion_skipped": result.conversion_skipped,
            "server_operations": result.server_operations,
            "from_versions": result.from_versions,
            "version_miss": result.version_miss,
            "plot_request_miss": result.plot_request_miss,
            "view_set": result.view_set,
            "view_miss": result.view_miss,
            "plot_wishes": result.plot_wishes,
            "plot_wishes_kept": result.plot_wishes_kept,
            "tool_calls": result.tool_calls,
        }
        for case, result in pairs
        if result.operations is not None and not result.match
    ]
    reply_misses = [
        {"id": case.id, "reply_miss": result.reply_miss, "words": result.reply_words}
        for case, result in pairs
        if result.operations is not None and result.reply_miss
    ]
    causes = Counter(result.cause or "unknown" for _, result in pairs if result.operations is None)
    return {
        "summary": summary,
        "per_tag": {tag: _block(items) for tag, items in sorted(tags.items())},
        "misses": misses,
        "reply_misses": reply_misses,
        "unavailable_causes": dict(causes.most_common()),
    }


@dataclass(frozen=True)
class Gates:
    min_exact: float = DEFAULT_MIN_EXACT
    max_unavailable: float = DEFAULT_MAX_UNAVAILABLE
    max_reply_misses: float = DEFAULT_MAX_REPLY_MISSES


def verdict_of(summary: dict[str, Any], gates: Gates) -> tuple[int, list[str]]:
    """The exit code and the reasons for it: an outage first, then the exact-match gate and the reply gate."""
    if (summary["unavailable_rate"] or 0.0) > gates.max_unavailable:
        return EXIT_OUTAGE, [f"{summary['unavailable']} cases got no answer (more than {gates.max_unavailable:.0%})"]
    reasons = []
    exact = summary["exact"]
    if exact is None or exact < gates.min_exact:
        reasons.append(f"the match rate {exact} is below {gates.min_exact}")
    if (summary["reply_miss_rate"] or 0.0) > gates.max_reply_misses:
        reasons.append(
            f"{summary['reply_misses']} of {summary['replies']} replies close with a question or an invitation the "
            f"turn was not blocked for, run over {MAX_REPLY_WORDS} words or summarize without a row count "
            f"(more than {gates.max_reply_misses:.0%})"
        )
    skipped = summary.get("conversions_owed", 0) - summary.get("conversions_made", 0)
    if skipped:
        reasons.append(f"the turns skipped {skipped} certain conversions of {summary['conversions_owed']}")
    return (EXIT_FAILED, reasons) if reasons else (EXIT_OK, [])


def table(cases: Sequence[PrepCase], results: Sequence[CaseResult]) -> str:
    """One line per case: the id, the expected operations, the found ones, the outcome."""
    by_id = {result.id: result for result in results}
    rows = [("case", "expected", "found", "result")]
    for case in cases:
        result = by_id.get(case.id)
        if result is None:
            continue
        expected = "; ".join(describe(line) for line in result.expected) or "no operation"
        if result.operations is None:
            found, outcome = result.cause or "unavailable", "unavailable"
        else:
            found = "; ".join(_safe_describe(line) for line in result.found) or (
                f"no operation (refusal {result.refusal})" if result.refusal else "no operation"
            )
            outcome = "match" if result.match else "miss (instruction talk)" if result.instruction_talk else "miss"
            if result.match and result.ops_exact is False:
                outcome += " (other operations, same table)"
            # Before the table's difference, which may run past the cell's 60 characters.
            if result.failed_calls and not result.match:
                outcome += f", {result.failed_calls} failed data {'call' if result.failed_calls == 1 else 'calls'}"
            if result.table_miss:
                outcome += f": {result.table_miss}"
            if result.version_miss:
                outcome += f", from {', '.join(result.from_versions) or 'no call'}"
            if result.plot_request_miss:
                outcome += ", no plot request"
            if result.view_miss:
                outcome += ", the table was cut, not the view" if case.view == "set" else ", a view was set"
            if result.reply_miss:
                outcome += f", reply: {result.reply_miss.replace('_', ' ')}"
        rows.append((case.id, expected, found, outcome))
    widths = [min(60, max(len(row[column]) for row in rows)) for column in range(4)]
    return "\n".join("  ".join(cell[: widths[i]].ljust(widths[i]) for i, cell in enumerate(row)) for row in rows)


def _safe_describe(line: str) -> str:
    try:
        return describe(line)
    except KeyError, TypeError, ValueError:
        return line


def summary_text(scored: dict[str, Any], reasons: list[str]) -> str:
    summary = scored["summary"]
    exact = "n/a" if summary["exact"] is None else f"{summary['exact']:.1%}"
    lines = [
        f"cases {summary['cases']}, unavailable {summary['unavailable']}, matched {summary['matched']}, "
        f"exact {exact}, the expected operations exactly {summary['ops_exact']}, llm calls {summary['llm_calls']}, "
        f"cost ${summary['cost_usd']:.4f}",
        "per tag: "
        + ", ".join(
            f"{tag} {block['matched']}/{block['cases'] - block['unavailable']}"
            for tag, block in scored["per_tag"].items()
        ),
    ]
    if summary["instruction_talk"]:
        lines.append(f"replies about the root's own instructions: {summary['instruction_talk']}")
    if summary["replies"]:
        lines.append(
            f"replies {summary['replies']}: median {summary['reply_words_median']} words (max "
            f"{summary['reply_words_max']}), {summary['questions_per_reply']} questions per reply, "
            f"{summary['closing_questions']} close with a question, {summary['closing_invitations']} with an "
            f"invitation, {summary['reply_misses']} reply misses"
        )
    if summary["conversions_owed"]:
        lines.append(f"certain conversions made: {summary['conversions_made']} of {summary['conversions_owed']}")
    if scored["unavailable_causes"]:
        lines.append(
            "unavailable: " + ", ".join(f"{count} x {cause}" for cause, count in scored["unavailable_causes"].items())
        )
    lines.append("PASS" if not reasons else "FAIL: " + "; ".join(reasons))
    return "\n".join(lines)


# --- Command line -----------------------------------------------------------------------------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m agents.evals.prep",
        description="Score the root's prepare_data and generate_data choices on the prep cases.",
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="case directory (default fixtures/prep)")
    parser.add_argument("--tags", help="only the cases with any of these comma-separated tags (a locale is a tag)")
    parser.add_argument("--provider", choices=sorted(PROVIDER_DEFAULTS), help="model family (default: the settings)")
    parser.add_argument("--model", help="the root's model; the provider's default when only --provider")
    parser.add_argument("--judge-model", help="the judges' model; the provider's default when only --provider")
    parser.add_argument("--location", choices=sorted(LOCATION_SURCHARGE), help="Vertex AI location (default eu)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (default agents/evals/reports)")
    parser.add_argument(
        "--calls-per-minute",
        type=float,
        default=DEFAULT_CALLS_PER_MINUTE,
        help=f"model-call starts per minute (25; a case makes about {CALLS_PER_CASE}, so cases start 60 x {CALLS_PER_CASE} / N "
        "seconds apart; 0: unpaced)",
    )
    parser.add_argument("--min-exact", type=float, default=DEFAULT_MIN_EXACT)
    parser.add_argument("--max-unavailable", type=float, default=DEFAULT_MAX_UNAVAILABLE)
    parser.add_argument(
        "--max-reply-misses",
        type=float,
        default=DEFAULT_MAX_REPLY_MISSES,
        help=(
            "replies that close with a question or an invitation the turn was not blocked for, run over "
            f"{MAX_REPLY_WORDS} words, or summarize without a row count"
        ),
    )
    args = parser.parse_args(argv)
    if args.calls_per_minute < 0:
        parser.error("--calls-per-minute must be 0 (unpaced) or more")
    for name in ("min_exact", "max_unavailable", "max_reply_misses"):
        if not 0 <= getattr(args, name) <= 1:
            parser.error(f"--{name.replace('_', '-')} is a fraction between 0 and 1")
    return args


def configure(args: argparse.Namespace, environ: MutableMapping[str, str]) -> None:
    """Write the flags into the `AGENT_*` environment; runs before any `agents.anyplot` import (as in scope.py)."""
    environ["PYTHON_DOTENV_DISABLED"] = "1"
    environ["ADK_DISABLE_LOAD_DOTENV"] = "1"
    environ.pop("AGENT_DEV_FIXTURE", None)
    environ.setdefault("ENVIRONMENT", "development")
    # No case renders, so the fake backend needs no service; its data runs execute the snippet (`eval_backend`).
    environ.setdefault("AGENT_RENDERER", "fake")
    environ["AGENT_RUNS_PER_MINUTE"] = "60"  # the pacer spaces the cases; the queue's own rate would double the wait
    environ["AGENT_GLOBAL_DAILY_TOKEN_BUDGET"] = str(EVAL_GLOBAL_DAILY_TOKENS)
    provider = args.provider
    if provider is None and args.model:
        provider = next((name for prefix, name in MODEL_PROVIDERS.items() if args.model.startswith(prefix)), None)
        if provider is None:
            raise SetupError(f"cannot tell the provider of {args.model!r}; pass --provider")
    if provider is not None:
        default_model, default_judge = PROVIDER_DEFAULTS[provider]
        environ["AGENT_PROVIDER"] = provider
        environ["AGENT_MODEL"] = args.model or default_model
        environ["AGENT_JUDGE_MODEL"] = args.judge_model or default_judge
    elif args.judge_model:
        environ["AGENT_JUDGE_MODEL"] = args.judge_model
    if args.location:
        environ["AGENT_LOCATION"] = args.location


def eval_backend(settings: AgentSettings) -> RenderBackend:
    """The renderer the settings name; for `fake`, the fake whose data runs execute the snippet (`HostDataBackend`)."""
    from agents.anyplot.render import make_backend
    from agents.evals.host_data import HostDataBackend

    if settings.renderer != "fake":
        return make_backend(settings)
    return HostDataBackend(cpu_seconds=settings.render_timeout_s, environment=settings.environment)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def stamp(settings: AgentSettings, cases: Sequence[PrepCase]) -> dict[str, Any]:
    from agents.anyplot.policy import root_instruction

    return {
        "schema": REPORT_SCHEMA,
        "date": datetime.now(UTC).date().isoformat(),
        "provider": settings.provider,
        "model": settings.model,
        "judge_model": settings.judge_model,
        "location": settings.location,
        "root_prompt_hash": _sha(root_instruction()),
        "cases_hash": _sha(json.dumps([case.model_dump() for case in cases], sort_keys=True, ensure_ascii=False)),
        "cases": len(cases),
    }


def check_cases(cases: Sequence[PrepCase]) -> None:
    """Every expected operation list passes the `Operation` and `Generate` models, a case's earlier changes apply to
    its dataset one after the other, and a case scored by its table gets one: its expected operations apply to the
    version they start from (`expected_result`) and change its table as the scoring compares it (`table_difference`,
    the case's `row_order`), since a table they leave as it is cannot tell them from no data call (such a case is
    `strict_operations`). Raises `SetupError` otherwise."""
    from agents.anyplot.data.generate import GenerateError
    from agents.anyplot.data.parse import ParseError, parse_dataset
    from agents.anyplot.data.prepare import PrepareArgs, PrepareError, apply_and_parse

    for case in cases:
        try:
            canonical_operations(case.expected_operations, ".")
        except ValidationError as exc:
            raise SetupError(f"case {case.id}: expected_operations do not validate: {exc}") from exc
        try:
            versions = [parse_dataset(case.dataset_text)] if case.dataset_text is not None else []
        except ParseError as exc:
            raise SetupError(f"case {case.id}: dataset_text does not parse: {exc}") from exc
        for place, operations in enumerate(case.before_operations):
            try:
                args = PrepareArgs.model_validate({"operations": operations})
                # In the case's language, as the session names a column the operations leave unnamed (`date_number`).
                _, parsed = apply_and_parse(versions[-1], args.operations, language=case.locale)
            except (ValidationError, PrepareError) as exc:
                raise SetupError(f"case {case.id}: before_operations[{place}] does not apply: {exc}") from exc
            versions.append(parsed)
        if not case.scored_by_table:
            continue
        start = _offline_start(case, versions)
        try:
            made = expected_result(start, case.expected_operations, case.locale)
        except (ValidationError, PrepareError, GenerateError, ParseError) as exc:
            raise SetupError(f"case {case.id}: expected_operations do not apply to its data: {exc}") from exc
        changes = any(item.get("op") != GAP_OP for item in case.expected_operations)
        # The scoring's own equality: a sort under `row_order: "any"`, or a change within the tolerances, is none.
        unchanged = (
            made is not None
            and start is not None
            and table_difference(result_table(start), result_table(made), any_order=case.row_order == "any") is None
        )
        if changes and unchanged:
            raise SetupError(
                f"case {case.id}: expected_operations leave its table as it is, so the table cannot tell them from no "
                "data call; set strict_operations"
            )


def _offline_start(case: PrepCase, versions: Sequence[ParsedDataset]) -> ParsedDataset | None:
    """The version among a case's `versions` (the paste, then one per earlier change) that its expected operations
    start from: the one `expected_from_version` names, or the last; raises `SetupError` for a number it does not
    have."""
    wanted = case.expected_from_version
    if not versions:
        return None
    if wanted is None or wanted == "current":
        return versions[-1]
    number = 1 if wanted == "original" else int(wanted)
    if not 1 <= number <= len(versions):
        raise SetupError(f"case {case.id}: expected_from_version {wanted} names no version of its data")
    return versions[number - 1]


def main(argv: list[str] | None = None, *, runtime: Runtime | None = None, services: Services | None = None) -> int:
    """Run the eval; `runtime` and `services` replace the service's own (tests)."""
    args = parse_args(argv)
    try:
        configure(args, os.environ)
        cases = load_cases(args.cases)
        wanted: set[str] = set()
        if args.tags:
            wanted = {tag.strip() for tag in args.tags.split(",") if tag.strip()}
            cases = [case for case in cases if wanted & {case.locale, *case.tags}]
            if not cases:
                raise SetupError(f"no case carries any of the tags {', '.join(sorted(wanted))}")
        from agents import main as service
        from agents.anyplot.services import Services
        from agents.anyplot.settings import get_settings

        get_settings.cache_clear()
        settings = get_settings()
        price_of(settings.model)
        price_of(settings.judge_model)
        check_cases(cases)
        if services is None:
            # Built here, not on the first data run: a backend the settings cannot have (the host data runs outside
            # development or test, a remote renderer without its URL) is a setup error, not a run of misses.
            from agents.anyplot.render.contract import RendererUnavailable

            try:
                backend = eval_backend(settings)
            except RendererUnavailable as exc:
                raise SetupError(str(exc)) from exc
            services = Services(backend_factory=lambda: backend)
    except (SetupError, UnknownPrice, ValidationError) as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return EXIT_SETUP
    pacer = Pacer(args.calls_per_minute / CALLS_PER_CASE) if args.calls_per_minute else None
    results = asyncio.run(
        run_cases(
            cases,
            runtime=runtime or service.Runtime(),
            services=services,
            pacer=pacer,
            echo=lambda text: print(text, file=sys.stderr, flush=True),
        )
    )
    scored = score(cases, results)
    gates = Gates(args.min_exact, args.max_unavailable, args.max_reply_misses)
    code, reasons = verdict_of(scored["summary"], gates)
    report = {
        "stamp": stamp(settings, cases),
        "calls_per_minute": args.calls_per_minute,
        "gates": asdict(gates),
        "passed": code == EXIT_OK,
        "reasons": reasons,
        **scored,
        "results": [asdict(result) for result in results],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    suffix = "-" + "-".join(sorted(wanted)) if wanted else ""
    path = args.out / f"{report['stamp']['date']}-prep-{settings.model}{suffix}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(table(cases, results))
    print(summary_text(scored, reasons))
    print(f"report: {path}")
    return code


if __name__ == "__main__":
    sys.exit(main())
