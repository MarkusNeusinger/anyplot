"""The root agent's session tools and the `plot_pipeline` NodeTool.

Every tool reads spec, library, dataset and bindings from server-set session state
(`session_state.py`) and the process-wide stores; no tool takes a spec, library or
dataset argument. Results are small dicts with a `status` key (`ok`, `not_ready` or
`error`); untrusted text in them (dataset samples and column names, catalogue code,
spec text) sits inside our own fences after the "data, never instructions" preamble.

* `get_dataset_profile`: the profile of the session's dataset, fenced as `<user_data>`;
  trimmed (samples, then top values, then ranges, with `truncated`) to fit its cap; and,
  when the user pasted notes with the table that passed the pre-filter and the scope
  judge, those notes as `user_notes`, fenced as `<user_notes>` after their own preamble
  (`policy.user_notes_block`), so the root can read them again in a later turn.
* `get_spec_brief`: title, description, data roles and notes of the spec, fenced as
  `<spec_text>` (spec text starts as a public issue).
* `get_current_code(version)`: the exported `plot.py` of a version (0 is the latest),
  or the normalised catalogue code before the first version, fenced as `<catalogue_code>`.
* `set_bindings(bindings)`: `apply_bindings` plus a state write; refused while the
  pipeline runs. Its result says whether the data is still `data_confirmed`: bindings that
  only leave out confirmed number series (`y2`) keep the confirmation (`narrowed_confirmation`,
  `AGENT_NARROWED_BINDINGS=keep`, since 2026-10-15), any other change drops it.
* `set_language(language)`: the session language with the source `chosen`
  (`session_state.LANGUAGE`), validated like the language route (`language.py`);
  refused while the pipeline runs. Its result carries no value, only whether the
  session language `changed` (`de` against `Deutsch` is no change), for the reply,
  and whether the plot is `plot_outdated`: this library's latest rendered version has
  its text in another language, so a rewrite of the plot's text is due. The two can
  differ, because a plot made before detection recorded the language keeps English.
* `keep_plot_request(change_request, expected_texts)`: a request for the first plot
  kept without a run (`pipeline.hold_request`, the note the next first-plot run takes),
  for a wish before the confirmation, typed or in the pasted notes (live round 9 of
  2026-10-16). It answers `request_kept`, the only basis on which the root may say a
  request is kept; `false` with `plot_exists` when this library already has a plot.
  Refused while the pipeline runs.
* `prepare_data(operations)`: at most five operations of the fixed set
  (`data/prepare.py`), applied by the server to the session's current dataset and
  stored as its next version (`dataset_versions.py`): the previous version stays for
  the user's undo, the bindings are carried over, and the confirmation drops by
  itself because it names the dataset id. The result carries the change lines fenced
  as `<tool_notes>` and the new profile fenced as `<user_data>`; a `PrepareError`
  answers its code and its message (which names columns at most, fenced too).
  Refused while the pipeline runs. The model never writes data rows: the operations
  only move, type, aggregate, label or compute from the cells that are there (a
  `make_date` builds a date from the year and month columns of the same row).
* `query_data(operations, columns, limit)`: a question about the data answered from a copy
  (`data/query.py`, since 2026-10-15): zero to five operations of `prepare_data`'s set, then
  the first `limit` rows (at most 25) in at most eight columns, fenced as `<user_data>`, with
  the total row count and the change lines. Nothing is stored: the dataset, its version, the
  bindings and the confirmation stay as they are, so a question never mutates the user's data.
* `generate_data(variables, series)`: a table computed by the server from formulas
  (`data/generate.py`): one or two variables, each a range of evenly spaced points,
  and one to ten series, each an expression over them. The table is parsed like a
  paste and stored as the session's next dataset version (`push_version`, the
  previous data kept for undo) or, in a session without data, as version 1 the way
  the dataset route stores a paste. Either way the confirmation drops by itself, the
  bindings are the defaults for the new columns (`push_version(rebind=True)`: a
  binding made for the old data is not carried over, even where a column name such as
  `x` returns), and the turn's `done` carries the version with its change line. The result has `prepare_data`'s shape; a
  `GenerateError` answers its code and its message (fenced). Refused while the
  pipeline runs. The model writes no rows: it chooses the spec, NumPy computes it.
* `plot_pipeline`: the `Workflow` around `pipeline.run_pipeline`, which ADK exposes as
  a NodeTool with the input schema `PipelineArgs` (`change_request`, `base`, `theme`).
  The tool name is the workflow name, so it stays stable.
"""

import json
import math
import secrets
from typing import Any

from google.adk import Workflow
from google.adk.tools.tool_context import ToolContext
from pydantic import TypeAdapter, ValidationError

from .. import telemetry
from ..briefs import bindings_text, spec_brief, trimmed_profiles
from ..code.data_code import check_data_code
from ..data.generate import Generate, GenerateError, generate
from ..data.parse import MAX_CANONICAL_BYTES, MAX_COMPUTED_BYTES, ParsedDataset, ParseError, parse_dataset
from ..data.prepare import MAX_OPERATIONS, Operation, PrepareError, apply_operations, validation_lines, with_date_notes
from ..data.query import DEFAULT_QUERY_ROWS, QueryArgs, QueryResult, run_query
from ..data.shape import long_suggestion
from ..data.store import StoredDataset, StoreFull
from ..dataset_context import code_source, generated_source
from ..dataset_guard import DataRefused, GuardUnavailable, check_dataset
from ..dataset_versions import push_version
from ..language import is_valid, normalise, same_language
from ..opening import store_dataset
from ..pipeline import hold_request, run_pipeline
from ..plugins.ledger import attribution, ledger_for
from ..plugins.tool_safety import (
    DATA_CODE_TOOL,
    MAX_DATA_CODE_CHARS,
    MAX_FILE_NAME_RESULT_BYTES,
    MAX_NOTES_RESULT_BYTES,
    QUERY_TOOL,
    result_limit,
    result_size,
)
from ..policy import DATA_PREAMBLE, fence, file_name_block, user_notes_block
from ..render.contract import DataJob, DataOutput, RendererUnavailable
from ..render.gates import error_summary
from ..render.harness import DATA_EXIT
from ..render.runtimes.python import DATA_FILE_NAME
from ..render.serial import RenderBusy
from ..schemas import MAX_COLUMNS, MAX_ROWS, Binding, DatasetProfile, KeepRequestArgs, PipelineArgs
from ..services import get_services
from ..session_state import (
    PENDING_BINDINGS,
    SessionView,
    apply_bindings,
    language_delta,
    narrowed_confirmation,
    read_session,
)
from ..settings import get_settings


PLOT_PIPELINE = "plot_pipeline"
OPERATIONS = TypeAdapter(list[Operation])
PROFILE_RESULT_BYTES = result_limit("get_dataset_profile") - MAX_NOTES_RESULT_BYTES - MAX_FILE_NAME_RESULT_BYTES
"""What `get_dataset_profile`'s profile is trimmed to: its cap less the room kept for the pasted notes and a
dropped file's name."""


def _not_ready(reason: str) -> dict[str, Any]:
    return {"status": "not_ready", "reason": reason}


def _error(code: str) -> dict[str, Any]:
    return {"status": "error", "code": code}


def _view(tool_context: ToolContext) -> SessionView | None:
    return read_session(tool_context.state)


def _stored(view: SessionView, tool_context: ToolContext) -> StoredDataset | None:
    if not view.dataset_id:
        return None
    return get_services().datasets.get(view.dataset_id, tool_context.session.id)


def _profile(view: SessionView, tool_context: ToolContext) -> DatasetProfile | None:
    stored = _stored(view, tool_context)
    return stored.profile if stored else None


def _with_profile(
    base: dict[str, Any], profile: DatasetProfile, tool_name: str, *, limit: int | None = None
) -> dict[str, Any]:
    """`base` plus the profile fenced as `<user_data>`, trimmed (samples, top values, ranges) to the tool's cap,
    or to `limit` when given."""
    cap = result_limit(tool_name) if limit is None else limit
    result: dict[str, Any] = {}
    for text, truncated in trimmed_profiles(profile):
        result = {**base, "profile": DATA_PREAMBLE + "\n" + fence("user_data", text)}
        if truncated:
            result["truncated"] = True
        if result_size(result) <= cap:
            break
    return result


async def get_dataset_profile(tool_context: ToolContext) -> dict[str, Any]:
    """Return the profile of the user's dataset: row count, typed columns and a few sample cells, and `to_long` when the table is wide for this plot."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    stored = _stored(view, tool_context)
    if stored is None:
        return _not_ready("no_dataset")
    profile = stored.profile
    base: dict[str, Any] = {"status": "ok", "rows": profile.rows}
    if view.bindings:
        # The bindings in force, so a summary names these rather than the ones the profile suggests (live tests of
        # 2026-10-14/15); the column names are the user's headers, so they are fenced as data.
        base["bindings"] = DATA_PREAMBLE + "\n" + fence("user_data", bindings_text(view.bindings))
    suggestion = long_suggestion(view.snapshot.roles(), profile, view.language)
    if suggestion is not None:
        # The page offers it as `.to_long()`; the column names are the user's, so fenced as data.
        base["to_long"] = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(suggestion.body(), ensure_ascii=False))
    # The profile keeps its own budget; the notes pasted with the data (judged at the paste) come on top, so the
    # root can read them again after the context filter dropped the summary turn that carried them.
    result = _with_profile(base, profile, "get_dataset_profile", limit=PROFILE_RESULT_BYTES)
    if stored.context_lines:
        result["user_notes"] = user_notes_block(stored.context_lines)
    if stored.file_name:
        # The dropped file's name, fenced as data under its own preamble: a name, never a request.
        result["file_name"] = file_name_block(stored.file_name)
    return result


async def get_spec_brief(tool_context: ToolContext) -> dict[str, Any]:
    """Return the chosen plot's title, description, data roles and notes."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    return {"status": "ok", "brief": DATA_PREAMBLE + "\n" + fence("spec_text", spec_brief(view))}


async def get_current_code(version: int, tool_context: ToolContext) -> dict[str, Any]:
    """Return the plot's code. version 0 is the latest version; before the first plot it is the catalogue code."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    # Versions of another library (before a library switch) are not this plot's code.
    stored = get_services().versions.get(tool_context.session.id, version or None, library=view.library)
    if stored is None and version:
        return _error("unknown_version")
    code = stored.export if stored is not None else view.normalised
    return {
        "status": "ok",
        "version": stored.number if stored is not None else 0,
        "code": DATA_PREAMBLE + "\n" + fence("catalogue_code", code),
    }


async def set_bindings(bindings: list[dict[str, str]], tool_context: ToolContext) -> dict[str, Any]:
    """Bind spec data roles to dataset columns. Each binding is {"role": <role name>, "column": <column name>}."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    profile = _profile(view, tool_context)
    if profile is None:
        return _not_ready("no_dataset")
    try:
        parsed = [Binding.model_validate(item) for item in bindings]
    except ValueError:
        return _error("invalid_bindings")
    roles = view.snapshot.roles()
    check, delta = apply_bindings(parsed, roles, profile, tool_context.state.get(PENDING_BINDINGS))
    if not delta:
        # The errors quote column names from the user's dataset.
        errors = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(check.errors[:10], ensure_ascii=False))
        return {"status": "error", "code": "invalid_bindings", "errors": errors}
    # Other bindings than the user confirmed leave the confirmation's fingerprint behind and the panel asks again,
    # unless they only leave out confirmed number series (`narrowed_confirmation`, `AGENT_NARROWED_BINDINGS`).
    if get_settings().narrowed_bindings == "keep":
        delta.update(narrowed_confirmation(view, parsed, check, roles))
    for key, value in delta.items():
        tool_context.state[key] = value
    confirmed = read_session(tool_context.state)
    result: dict[str, Any] = {
        "status": "ok",
        "complete": check.complete,
        "missing_roles": check.missing_roles,
        "data_confirmed": bool(confirmed and confirmed.data_confirmed),
    }
    if check.warnings:  # valid, but a role that needs values of 0 or more got negative ones; they name columns
        telemetry.note_binding_warnings(tool_context.session.id, check.warnings)  # closed codes for `chat_turn`
        result["warnings"] = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(check.warnings, ensure_ascii=False))
    return result


async def set_language(language: str, tool_context: ToolContext) -> dict[str, Any]:
    """Set the session language: the language of your replies and of every text in the plot (title, axis titles, legend entries, annotations). `language` is a short language name or code such as "de", "English" or "Swedish". The next plot version uses it; code, comments and column names stay as they are."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    if not isinstance(language, str):
        return _error("invalid_language")
    value = normalise(language)
    if not is_valid(value):
        return _error("invalid_language")
    changed = not same_language(view.language, value)
    # The plot the user sees is this library's latest render; its text may be in another language than the
    # session's (a plot made before detection recorded the language), so the rewrite is decided against it.
    latest = get_services().versions.latest_rendered(tool_context.session.id, library=view.library)
    plot_outdated = latest is not None and not same_language(latest.language, value)
    # A choice is final either way: detection never writes over `chosen`.
    for key, item in language_delta(value, "chosen").items():
        tool_context.state[key] = item
    return {"status": "ok", "source": "chosen", "changed": changed, "plot_outdated": plot_outdated}


async def keep_plot_request(
    change_request: str, tool_context: ToolContext, expected_texts: list[str] | None = None
) -> dict[str, Any]:
    """Keep a request for the first plot of this library without starting a run: the next "Create plot" draws it. Use it for a plot wish before the data is confirmed (a title, a scale), typed or in the pasted notes. `change_request` is a short English description (at most 600 characters); `expected_texts` lists the texts and number formats the user wrote out, verbatim. Returns request_kept: true when the server keeps it; false, with a reason, when this library already has a plot (then call plot_pipeline with base "previous" once the data is confirmed)."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    try:
        args = KeepRequestArgs(change_request=change_request, expected_texts=expected_texts or [])
    except ValidationError:
        return _error("invalid_arguments")
    if get_services().versions.latest_rendered(tool_context.session.id, library=view.library) is not None:
        # A change of an existing plot is no first-plot note: the root repeats it once the data is confirmed.
        return {"status": "ok", "request_kept": False, "reason": "plot_exists"}
    hold_request(tool_context.state, PipelineArgs(**args.model_dump()))
    return {"status": "ok", "request_kept": True}


async def prepare_data(operations: list[dict[str, Any]], tool_context: ToolContext) -> dict[str, Any]:
    """Change the user's dataset with one to five operations, applied in order by the server; the result becomes the next version of the data, which the user then checks and confirms.

    Each operation is an object with "op" and its fields, column names exactly as the profile lists them:
    rename (column, name); drop_columns (columns); drop_rows (where: conditions on single columns that must all hold);
    set_type (column, type number|datetime|text, date_format, decimal); aggregate (by, column, how sum|mean|count|min|max,
    period hour|day|week|month|quarter|year); sort (column, descending); pivot_longer (columns, names_to, values_to); pivot_wider
    (names_from, values_from, index); classify (name, rules: each where conditions and a label, otherwise: the optional
    label for rows no rule matches; adds the text column name, labelling each row by the first rule that holds); derive
    (name, how ratio|difference|sum|share|percent_change|cumsum|index, columns, within, order, percent; adds the number
    column name computed from number columns: columns[0] / columns[1], columns[0] - columns[1], a row sum, a share of
    the group's total, or, in the order of a number or date column order, the percent change from the previous row,
    the running total, or an index with the group's first row = 100); make_date (name, year, and month with an
    optional day, or quarter, or week; adds the date column name built from whole-number columns holding the parts of
    a date, a part left out being its first: year and month give the first day of each month). Returns the change
    lines and the new profile, or an error with a code and a message.
    """
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    ledger = ledger_for(tool_context.invocation_id)
    if ledger.pipeline_active:
        return _error("run_active")
    services = get_services()
    session_id = tool_context.session.id
    stored = services.datasets.get(view.dataset_id, session_id) if view.dataset_id else None
    if stored is None:
        return _not_ready("no_dataset")
    try:
        if not isinstance(operations, list) or not 1 <= len(operations) <= MAX_OPERATIONS:
            raise ValueError(f"operations is a list of 1 to {MAX_OPERATIONS} operations")
        parsed_operations = OPERATIONS.validate_python(operations)
    except ValidationError as exc:
        lines = validation_lines(exc, prefix="operations")
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines(lines)}
    except ValueError as exc:
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines([str(exc)])}
    try:
        prepared = apply_operations(stored.as_parsed(), parsed_operations)
        # The columns `set_type text` made text stay text: the re-parse would type them by content again.
        # The CSV is the service's own: every row stays, also a `Total` category a sort moved to the end.
        parsed = parse_dataset(
            prepared.csv,
            text_columns=prepared.text_columns,
            find_table=False,
            max_bytes=MAX_COMPUTED_BYTES,
            canonical=True,
        )
        # A date column whose day and month order is still a guess keeps its note, so a later call can switch it.
        parsed = with_date_notes(parsed, prepared)
    except PrepareError as exc:
        # The message names columns of the user's dataset at most, never a cell; fenced like every column name.
        return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
    except ParseError:  # the operations keep every parser cap (rows, columns, size), so a refusal here is a bug
        return _error("internal")
    try:
        version = push_version(services.datasets, session_id, view, parsed, view.snapshot)
    except StoreFull:
        return _error("capacity")
    # The new dataset id leaves the confirmation's fingerprint behind: the user confirms the new version.
    for key, value in version.delta.items():
        tool_context.state[key] = value
    ledger.dataset_changes.extend(prepared.changes)
    ledger.prep_ops.extend(operation.op for operation in parsed_operations)  # the names only, for the telemetry
    base = {
        "status": "ok",
        "rows": parsed.profile.rows,
        "columns": len(parsed.profile.columns),
        "version": version.version,
        "changes": DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(prepared.changes, ensure_ascii=False)),
    }
    return _with_profile(base, parsed.profile, "prepare_data")


async def query_data(
    operations: list[dict[str, Any]],
    tool_context: ToolContext,
    columns: list[str] | None = None,
    limit: int = DEFAULT_QUERY_ROWS,
) -> dict[str, Any]:
    """Answer a question about the user's data without changing it: the operations are applied to a copy and the first rows of the result come back as a small table; nothing is stored, and the data, its version and its confirmation stay as they are.

    operations: zero to five operations of the same set as prepare_data, applied in order (keep only some rows with
    drop_rows on the others, such as test ne on the year asked about; a top N is a sort with limit; a share, a change
    or an index is a derive; a total or a mean per group an aggregate). columns: the columns to return, at most 8
    (default: the first 8). limit: the rows to return, 1 to 25 (default 10). Returns the table (columns and rows),
    the number of rows of the whole result, whether it was cut, and the change lines, or an error with a code and a
    message.
    """
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    stored = _stored(view, tool_context)
    if stored is None:
        return _not_ready("no_dataset")
    try:
        args = QueryArgs.model_validate({"operations": operations, "columns": columns, "limit": limit})
    except ValidationError as exc:
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines(validation_lines(exc))}
    try:
        answer = run_query(stored.as_parsed(), args.operations, args.columns, args.limit)
    except PrepareError as exc:
        # The message names columns of the user's dataset at most, never a cell; fenced like every column name.
        return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
    return query_result(answer)


def query_result(answer: QueryResult) -> dict[str, Any]:
    """The `query_data` result: the table fenced as `<user_data>`, cut by rows from the end to fit the tool's cap."""
    rows = list(answer.rows)
    while True:
        table = {"columns": answer.columns, "rows": rows}
        result: dict[str, Any] = {
            "status": "ok",
            "rows": answer.total_rows,
            "table": DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(table, ensure_ascii=False)),
            "truncated": answer.truncated or len(rows) < len(answer.rows),
        }
        if answer.changes:
            notes = json.dumps(answer.changes, ensure_ascii=False)
            result["changes"] = DATA_PREAMBLE + "\n" + fence("tool_notes", notes)
        if not rows or result_size(result) <= result_limit(QUERY_TOOL):
            return result
        rows.pop()


async def generate_data(
    variables: list[dict[str, Any]], series: list[dict[str, Any]], tool_context: ToolContext
) -> dict[str, Any]:
    """Compute the user's data from formulas, for a function or a curve instead of a pasted table; the server computes the rows and stores them as the next version of the data, which the user then checks and confirms.

    variables: one or two ranges {"name": "x", "start": "-pi", "stop": "pi", "points": 200}; start and stop are
    numbers or expressions over the constants pi, e and tau; points is 2 to 5000 (default 200); two variables make a
    grid (every pair, at most 10000 rows: set points on both, such as 50). The table holds at most 2 MB, more than any
    grid within these point limits needs. series: one to ten {"name": "y",
    "expression": "sin(x)"}, each an expression over the variables with numbers, pi, e, tau, + - * / ** % //,
    parentheses and the functions sin cos tan asin acos atan sinh cosh tanh exp log log10 log2 sqrt abs floor ceil
    round sign atan2 min max. Returns the change lines and the new profile, or an error with a code and a message.
    """
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    ledger = ledger_for(tool_context.invocation_id)
    if ledger.pipeline_active:
        return _error("run_active")
    try:
        spec = Generate.model_validate({"variables": variables, "series": series})
    except ValidationError as exc:
        return {"status": "error", "code": "invalid_arguments", "errors": _fenced_lines(validation_lines(exc))}
    try:
        generated = generate(spec)
        parsed = parse_dataset(generated.csv, find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True)
    except GenerateError as exc:
        # The message names variables and series and quotes the model's own expression at most; fenced all the same.
        return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
    except ParseError:  # the generator keeps the parser's caps (size, rows, columns), so a refusal here is a bug
        return _error("internal")
    try:
        delta, number = _store_generated(tool_context.session.id, view, parsed, source=generated_source(spec))
    except StoreFull:
        return _error("capacity")
    # A new dataset id leaves the confirmation's fingerprint behind: the user confirms the generated data.
    for key, value in delta.items():
        tool_context.state[key] = value
    changes = [*generated.changes, *generated.warnings]
    ledger.dataset_changes.extend(changes)
    base = {
        "status": "ok",
        "rows": parsed.profile.rows,
        "columns": len(parsed.profile.columns),
        "version": number,
        "changes": DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(changes, ensure_ascii=False)),
    }
    return _with_profile(base, parsed.profile, "generate_data")


def _store_generated(
    session_id: str, view: SessionView, parsed: ParsedDataset, *, code: str | None = None, source: str
) -> tuple[dict[str, Any], int]:
    """Store a generated table: the next version of the session's data, or version 1 when it has none; raises `StoreFull`.

    A session whose dataset left the store (a restart keeps neither) counts as one
    without data, so the stale ids are dropped with the history, as a paste drops them.
    `code` is the Python that computed the table (`run_data_code`), kept with the version;
    `source` says where it comes from (`dataset_context`), for the adapter and the reviewer.
    """
    store = get_services().datasets
    current = store.get(view.dataset_id, session_id) if view.dataset_id else None
    if current is not None:
        version = push_version(store, session_id, view, parsed, view.snapshot, rebind=True, code=code, source=source)
        return version.delta, version.version
    ingested = store_dataset(
        store,
        session_id,
        parsed,
        view.snapshot,
        previous_id=view.dataset_id,
        history=view.dataset_history,
        code=code,
        source=source,
    )
    return ingested.state_delta(), 1


DATA_CODE_CHANGE = "computed from your code"
"""The change line of a `run_data_code` version; the rows and columns follow it."""
SOURCE_LANGUAGES = frozenset({"python", "javascript", "r", "math", "other"})
"""`run_data_code`'s `source_language`: what the user wrote before the root's translation, for attribution only."""
RUN_FAILURES: dict[str, str] = {
    "no_frame": "the code defined no table: assign a pandas DataFrame to df at the top level",
    "frame_shape": "df has nested column headers (a MultiIndex) or an index that cannot become columns: flatten it",
    "too_many_rows": f"df has more than {MAX_ROWS:,} rows: compute fewer points",
    "too_many_columns": f"df has more than {MAX_COLUMNS} columns: keep only the columns the plot needs",
    "too_large": "df's CSV is over 2 MB: compute fewer rows or round the values",
    "blocked": "the code tried to reach native code, files, processes or the network, which the sandbox refuses",
    "usage": "the sandbox could not start the code",
    "exec_deny": (
        "the sandbox could not set up its protection against program starts, so it ran no code: this is no fault of "
        "the code, and no change to it helps; tell the user that computing data is unavailable right now"
    ),
}
"""Fixed messages for the harness's data-mode exit codes (`harness.DATA_EXIT`) other than `ok` and `error`."""
CANONICAL_TOO_LARGE = (
    "df fits the 2 MB cap, but written out the way the plot reads it (ISO dates, full numbers) it is over "
    f"{MAX_CANONICAL_BYTES // (1024 * 1024)} MB: keep fewer rows or columns, or shorten long text and number cells"
)
"""The refusal of a table whose canonical CSV passes `parse.MAX_CANONICAL_BYTES` although df's own CSV fit."""
DATA_RUN_SLOT_WAIT_S = 120.0
"""How long `run_data_code` waits for the instance's render slot before it answers `busy`."""


def _error_lines(code: str, lines: list[str]) -> dict[str, Any]:
    """A `run_data_code` refusal with its lines fenced as `<tool_notes>`: they come from the server, never from the
    snippet's own output, but they name the model's own code."""
    notes = DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(lines, ensure_ascii=False))
    return {"status": "error", "code": code, "message": notes}


async def run_data_code(code: str, source_language: str, tool_context: ToolContext) -> dict[str, Any]:
    """Run Python that generates the data for the plot (a snippet the user pasted or typed, translated by you to Python if it was JavaScript, R, a formula or anything else); the server validates it, runs it in a sandbox without network or files, and stores the table it computed in df as the next version of the data, which the user then checks and confirms.

    code: Python of at most 6,000 characters using only numpy, pandas, math, random, statistics or scipy.stats (and
    the other scipy computing modules); it must assign the final table to df at the top level as a pandas DataFrame
    (at most 20,000 rows, 50 columns and 2 MB as CSV: 10,000 rows of about 10 float columns at full precision fit;
    for a wider table round floats to the decimal places that still keep their values distinct, such as
    df.round(3) for values between -50 and 50, or keep every k-th row), read no file, call no network and
    draw nothing (no matplotlib, no plot(),
    no hist()). Never write data values from memory: more than 20 numbers or 20 text values written out in one list,
    tuple or dict (a list repeated with * counts every copy), or 40 in the code, are refused. source_language:
    what the user wrote, one of python, javascript, r, math or other. Returns the change lines and the new profile,
    or an error with a code and a message.
    """
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    ledger = ledger_for(tool_context.invocation_id)
    if ledger.pipeline_active:
        return _error("run_active")
    settings = get_settings()
    if not settings.data_code:
        return _error("unavailable")
    if not isinstance(code, str) or not 0 < len(code) <= MAX_DATA_CODE_CHARS:  # ToolSafety checks it first
        return _error("invalid_arguments")
    language = source_language if source_language in SOURCE_LANGUAGES else "other"
    prepared, findings = check_data_code(code)
    if findings:
        attribution("data_code", ledger, outcome="invalid_code", language=language, rules=[f.rule for f in findings])
        lines = [f"line {f.line}: {f.message}" if f.line else f.message for f in findings[:MAX_FINDING_LINES]]
        return _error_lines("invalid_code", lines)
    services = get_services()
    user = ledger.user_id or "anonymous"
    # Checked before the queue wait and counted after it, so a run that never starts is never counted; the user's
    # runs waiting in their other sessions at the same time (at most `AGENT_USER_MAX_RUNS` - 1) can each pass this
    # check and overshoot the day's count by as many, a small overshoot accepted with the parallel windows (2026-10-21).
    if not services.usage.data_runs_ok(user, settings):
        attribution("data_code", ledger, outcome="daily_limit", language=language)
        return _error("daily_limit")
    if ledger.run_slot is not None and not await ledger.run_slot():  # the run queue's slot and the turn's start
        # The route failed the turn with `run_limit` (the user's runs in other sessions fill their share) or
        # `capacity` (a full queue, an expired wait), or the wait was cancelled; the turn is aborted either way.
        code = "run_limit" if ledger.error == "run_limit" else "capacity"
        attribution("data_code", ledger, outcome=code, language=language)
        return _error(code)
    services.usage.add_data_run(user)
    job = DataJob(job_id=f"d{secrets.token_hex(8)}", source=prepared, timeout_s=settings.data_run_timeout_s)
    try:
        output = await services.backend.run_data(job, wait_s=DATA_RUN_SLOT_WAIT_S)
    except RenderBusy:
        attribution("data_code", ledger, outcome="busy", language=language)
        return _error("busy")
    except RendererUnavailable, NotImplementedError:  # `DataRunUnsupported` among them: a renderer without the route
        attribution("data_code", ledger, outcome="unavailable", language=language)
        return _error("unavailable")
    failure = _run_failure(output)
    attribution(
        "data_code",
        ledger,
        outcome=failure[0] if failure else "ran",
        language=language,
        exit_code=output.exit_code,
        wall_s=round(output.wall_s, 3),
    )
    if failure is not None:
        return _error_lines(*failure)
    assert output.csv_text is not None  # `_run_failure` refuses a run without a table
    try:
        parsed = parse_dataset(output.csv_text, find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True)
    except ParseError as exc:
        if exc.code == "too_long":  # its canonical copy outgrew `MAX_CANONICAL_BYTES` (wide dates, long text)
            return _error_lines("run_failed", [CANONICAL_TOO_LARGE])
        return _error_lines("unparseable", [f"the table df holds cannot be read as data: {exc.message}"])
    if not any(column.dtype in ("integer", "number", "datetime") for column in parsed.profile.columns):
        return _error_lines("no_numbers", ["df has no number or date column: a plot needs values to draw"])
    try:
        await check_dataset(services, ledger, parsed)
    except DataRefused:
        return _error("data_refused")
    except GuardUnavailable:
        return _error("guard_unavailable")
    try:
        delta, number = _store_generated(
            tool_context.session.id, view, parsed, code=prepared, source=code_source(prepared, language)
        )
    except StoreFull:
        return _error("capacity")
    for key, value in delta.items():
        tool_context.state[key] = value
    changes = [f"{DATA_CODE_CHANGE}: {parsed.profile.rows} rows, {len(parsed.profile.columns)} columns"]
    ledger.dataset_changes.extend(changes)
    base = {
        "status": "ok",
        "rows": parsed.profile.rows,
        "columns": len(parsed.profile.columns),
        "version": number,
        "changes": DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(changes, ensure_ascii=False)),
    }
    return _with_profile(base, parsed.profile, DATA_CODE_TOOL)


MAX_FINDING_LINES = 10
"""Validator findings a refusal lists; the rest are the same kind of fix."""


def _run_failure(output: DataOutput) -> tuple[str, list[str]] | None:
    """The error code and fixed lines of a data run that left no table; None for one that did.

    Nothing the snippet printed is passed on: an exception is named by its class and the
    line of `snippet.py` it was raised on (`gates.error_summary`), never its message.
    """
    if output.timed_out:
        return "timeout", ["the code ran longer than the sandbox allows: compute fewer points or simplify it"]
    if output.reason is not None:
        return "run_failed", [f"the sandbox stopped the code ({output.reason}): write no files and compute less"]
    if output.exit_code == DATA_EXIT["error"]:
        summary = error_summary(output.stderr_tail, code_file=DATA_FILE_NAME)
        return "code_error", [f"the code raised {summary}"]
    for name, exit_code in DATA_EXIT.items():
        if output.exit_code == exit_code and name in RUN_FAILURES:
            return "run_failed", [cap_failure(name, output.measured, output.limit) or RUN_FAILURES[name]]
    if output.exit_code is not None and output.exit_code < 0:
        # A launcher that died of a signal and left no `status.json`: the harness's own code is lost.
        return "run_failed", [f"the sandbox ended the run without naming why (signal {-output.exit_code})"]
    if output.exit_code != 0:
        return "run_failed", ["the code ended with an error the sandbox does not name"]
    if output.csv_text is None:
        return "run_failed", ["the sandbox returned no table"]
    return None


CAP_HEADROOM = 0.9
"""The share of a cap a suggested thinning aims at, so the retry lands under it, not on it."""


def cap_failure(name: str, measured: int | None, limit: int | None) -> str | None:
    """The refusal line of a broken row, column or size cap with the harness's numbers and a fix; None without them.

    A live run of 2026-10-14 (a 10,000-step ODE at full float precision, about 800 KB of
    CSV) failed twice with no reason given. With the size and the cap the model can thin
    and round on the first retry: the step `k` keeps the table under the cap as it is.
    """
    if measured is None or limit is None or limit <= 0 or measured <= limit:
        return None
    k = math.ceil(measured / (limit * CAP_HEADROOM))
    nth = _ordinal(k)
    if name == "too_large":
        return (
            f"df's CSV is {math.ceil(measured / 1024):,} KB, over the {limit // 1024:,} KB cap: keep every {nth} row "
            f"(df = df.iloc[::{k}]) or compute about 1/{k} of the points, and round the floats to the decimal "
            "places that still keep the values distinct (df = df.round(3) for values between -50 and 50; never so "
            "few that close values become equal), which roughly halves the size and lets you keep more rows; a line "
            "needs no more than a few thousand points"
        )
    if name == "too_many_rows":
        return (
            f"df has {measured:,} rows, more than the {limit:,} the data takes: keep every {nth} row "
            f"(df = df.iloc[::{k}]) or compute fewer points"
        )
    if name == "too_many_columns":
        return f"df has {measured} columns, more than the {limit} the data takes: keep only the columns the plot needs"
    return None


def _ordinal(number: int) -> str:
    """`2nd`, `3rd`, `4th`, `11th`, `21st`: the step in "keep every 2nd row"."""
    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _fenced_lines(lines: list[str]) -> str:
    """Lines that quote the user's column names (or the model's own values), fenced as data."""
    return DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(lines, ensure_ascii=False))


plot_pipeline = Workflow(
    name=PLOT_PIPELINE,
    description=(
        "Adapt the plot to the user's dataset and bindings, render it in one theme, review it, and repair it "
        "once if needed. Call it with no arguments for 'Create plot'; for a change, pass change_request (English, "
        "at most 600 characters) and base='previous'. Leave theme out unless the user asks for a theme: a new plot "
        "is light and a change keeps the latest version's theme; pass theme='dark' only when the user asks for a "
        "dark plot. Pass expected_texts (at most five) with the texts and number formats the user wrote out for "
        "the plot, verbatim. Returns the PlotResult, with what the shipped plot shows under shows."
    ),
    input_schema=PipelineArgs,
    edges=[("START", run_pipeline)],
)

SESSION_TOOLS = (
    get_dataset_profile,
    get_spec_brief,
    get_current_code,
    set_bindings,
    set_language,
    keep_plot_request,
    prepare_data,
    query_data,
    generate_data,
    run_data_code,
)
ROOT_TOOL_NAMES = frozenset({*(tool.__name__ for tool in SESSION_TOOLS), PLOT_PIPELINE})
