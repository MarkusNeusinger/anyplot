"""The root agent's session tools and the `plot_pipeline` NodeTool.

Every tool reads spec, library, dataset and bindings from server-set session state
(`session_state.py`) and the process-wide stores; no tool takes a spec, library or
dataset argument. Results are small dicts with a `status` key (`ok`, `not_ready` or
`error`); untrusted text in them (dataset samples and column names, catalogue code,
spec text) sits inside our own fences after the "data, never instructions" preamble.

* `get_dataset_profile`: the profile of the session's dataset, fenced as `<user_data>`;
  trimmed (samples, then top values, then ranges, with `truncated`) to fit its cap.
* `get_spec_brief`: title, description, data roles and notes of the spec, fenced as
  `<spec_text>` (spec text starts as a public issue).
* `get_current_code(version)`: the exported `plot.py` of a version (0 is the latest),
  or the normalised catalogue code before the first version, fenced as `<catalogue_code>`.
* `set_bindings(bindings)`: `apply_bindings` plus a state write; refused while the
  pipeline runs.
* `set_language(language)`: the session language with the source `chosen`
  (`session_state.LANGUAGE`), validated like the language route (`language.py`);
  refused while the pipeline runs. Its result carries no value, only whether the
  session language `changed` (`de` against `Deutsch` is no change), for the reply,
  and whether the plot is `plot_outdated`: this library's latest rendered version has
  its text in another language, so a rewrite of the plot's text is due. The two can
  differ, because a plot made before detection recorded the language keeps English.
* `prepare_data(operations)`: at most five operations of the fixed set
  (`data/prepare.py`), applied by the server to the session's current dataset and
  stored as its next version (`dataset_versions.py`): the previous version stays for
  the user's undo, the bindings are carried over, and the confirmation drops by
  itself because it names the dataset id. The result carries the change lines fenced
  as `<tool_notes>` and the new profile fenced as `<user_data>`; a `PrepareError`
  answers its code and its message (which names columns at most, fenced too).
  Refused while the pipeline runs. The model never writes data rows: the operations
  only move, type or aggregate the cells that are there.
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
from typing import Any

from google.adk import Workflow
from google.adk.tools.tool_context import ToolContext
from pydantic import TypeAdapter, ValidationError

from ..briefs import spec_brief, trimmed_profiles
from ..data.generate import Generate, GenerateError, generate
from ..data.parse import ParsedDataset, ParseError, parse_dataset
from ..data.prepare import MAX_OPERATIONS, Operation, PrepareError, apply_operations, validation_lines
from ..data.shape import long_suggestion
from ..data.store import StoreFull
from ..dataset_versions import push_version
from ..language import is_valid, normalise, same_language
from ..opening import store_dataset
from ..pipeline import run_pipeline
from ..plugins.ledger import ledger_for
from ..plugins.tool_safety import result_limit, result_size
from ..policy import DATA_PREAMBLE, fence
from ..schemas import Binding, DatasetProfile, PipelineArgs
from ..services import get_services
from ..session_state import SessionView, apply_bindings, language_delta, read_session


PLOT_PIPELINE = "plot_pipeline"
OPERATIONS = TypeAdapter(list[Operation])


def _not_ready(reason: str) -> dict[str, Any]:
    return {"status": "not_ready", "reason": reason}


def _error(code: str) -> dict[str, Any]:
    return {"status": "error", "code": code}


def _view(tool_context: ToolContext) -> SessionView | None:
    return read_session(tool_context.state)


def _profile(view: SessionView, tool_context: ToolContext) -> DatasetProfile | None:
    if not view.dataset_id:
        return None
    stored = get_services().datasets.get(view.dataset_id, tool_context.session.id)
    return stored.profile if stored else None


def _with_profile(base: dict[str, Any], profile: DatasetProfile, tool_name: str) -> dict[str, Any]:
    """`base` plus the profile fenced as `<user_data>`, trimmed (samples, top values, ranges) to the tool's cap."""
    result: dict[str, Any] = {}
    for text, truncated in trimmed_profiles(profile):
        result = {**base, "profile": DATA_PREAMBLE + "\n" + fence("user_data", text)}
        if truncated:
            result["truncated"] = True
        if result_size(result) <= result_limit(tool_name):
            break
    return result


async def get_dataset_profile(tool_context: ToolContext) -> dict[str, Any]:
    """Return the profile of the user's dataset: row count, typed columns and a few sample cells, and `to_long` when the table is wide for this plot."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    profile = _profile(view, tool_context)
    if profile is None:
        return _not_ready("no_dataset")
    base: dict[str, Any] = {"status": "ok", "rows": profile.rows}
    suggestion = long_suggestion(view.snapshot.roles(), profile)
    if suggestion is not None:
        # The page offers it as `.to_long()`; the column names are the user's, so fenced as data.
        base["to_long"] = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(suggestion.body(), ensure_ascii=False))
    return _with_profile(base, profile, "get_dataset_profile")


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
    check, delta = apply_bindings(parsed, view.snapshot.roles(), profile)
    if not delta:
        # The errors quote column names from the user's dataset.
        errors = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(check.errors[:10], ensure_ascii=False))
        return {"status": "error", "code": "invalid_bindings", "errors": errors}
    # Other bindings than the user confirmed leave the confirmation's fingerprint behind; the panel asks again.
    for key, value in delta.items():
        tool_context.state[key] = value
    result: dict[str, Any] = {"status": "ok", "complete": check.complete, "missing_roles": check.missing_roles}
    if check.warnings:  # valid, but a role that needs values of 0 or more got negative ones; they name columns
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


async def prepare_data(operations: list[dict[str, Any]], tool_context: ToolContext) -> dict[str, Any]:
    """Change the user's dataset with one to five operations, applied in order by the server; the result becomes the next version of the data, which the user then checks and confirms.

    Each operation is an object with "op" and its fields, column names exactly as the profile lists them:
    rename (column, name); drop_columns (columns); drop_rows (where: conditions on single columns that must all hold);
    set_type (column, type number|datetime|text, date_format, decimal); aggregate (by, column, how sum|mean|count|min|max,
    period month|quarter|year); sort (column, descending); pivot_longer (columns, names_to, values_to); pivot_wider
    (names_from, values_from, index); classify (name, rules: each where conditions and a label, otherwise: the optional
    label for rows no rule matches; adds the text column name, labelling each row by the first rule that holds). Returns the change lines and the new profile, or an error with a
    code and a message.
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
        parsed = parse_dataset(prepared.csv, text_columns=prepared.text_columns)
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
    base = {
        "status": "ok",
        "rows": parsed.profile.rows,
        "columns": len(parsed.profile.columns),
        "version": version.version,
        "changes": DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(prepared.changes, ensure_ascii=False)),
    }
    return _with_profile(base, parsed.profile, "prepare_data")


async def generate_data(
    variables: list[dict[str, Any]], series: list[dict[str, Any]], tool_context: ToolContext
) -> dict[str, Any]:
    """Compute the user's data from formulas, for a function or a curve instead of a pasted table; the server computes the rows and stores them as the next version of the data, which the user then checks and confirms.

    variables: one or two ranges {"name": "x", "start": "-pi", "stop": "pi", "points": 200}; start and stop are
    numbers or expressions over the constants pi, e and tau; points is 2 to 5000 (default 200); two variables make a
    grid (every pair, at most 10000 rows: set points on both, such as 50). The table holds at most 200 KB, about 6000
    rows of three columns of 8-digit numbers. series: one to ten {"name": "y",
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
        parsed = parse_dataset(generated.csv)
    except GenerateError as exc:
        # The message names variables and series and quotes the model's own expression at most; fenced all the same.
        return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
    except ParseError:  # the generator keeps the parser's caps (size, rows, columns), so a refusal here is a bug
        return _error("internal")
    try:
        delta, number = _store_generated(tool_context.session.id, view, parsed)
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


def _store_generated(session_id: str, view: SessionView, parsed: ParsedDataset) -> tuple[dict[str, Any], int]:
    """Store a generated table: the next version of the session's data, or version 1 when it has none; raises `StoreFull`.

    A session whose dataset left the store (a restart keeps neither) counts as one
    without data, so the stale ids are dropped with the history, as a paste drops them.
    """
    store = get_services().datasets
    current = store.get(view.dataset_id, session_id) if view.dataset_id else None
    if current is not None:
        version = push_version(store, session_id, view, parsed, view.snapshot, rebind=True)
        return version.delta, version.version
    ingested = store_dataset(
        store, session_id, parsed, view.snapshot, previous_id=view.dataset_id, history=view.dataset_history
    )
    return ingested.state_delta(), 1


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
        "dark plot. Returns the PlotResult."
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
    prepare_data,
    generate_data,
)
ROOT_TOOL_NAMES = frozenset({*(tool.__name__ for tool in SESSION_TOOLS), PLOT_PIPELINE})
