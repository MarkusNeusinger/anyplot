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
  or the normalised catalogue code before the first version, fenced as `<catalogue_code>`;
  for a version also what its downloaded data holds (`version_data`: the rows in each file
  that carries the data, and the view of the plot it drew them through, as counts under
  keys that explain themselves, since the tool's description stays one sentence).
* `set_bindings(bindings)`: `apply_bindings` plus a state write; refused while the
  pipeline runs. Its result says whether the data is still `data_confirmed`: bindings that
  only leave out confirmed number series (`y2`) keep the confirmation (`narrowed_confirmation`,
  `AGENT_NARROWED_BINDINGS=keep`, since 2026-10-15), any other change drops it. In a turn whose own change of the
  data emptied a role, a binding that puts a column of the turn holding a date turned into numbers or the row
  numbers on a role is refused, the whole call, with `invalid_bindings` and a fixed `message` (`data/emptied.py`).
* `set_language(language, applies_to)`: the reply language (the session language,
  `session_state.LANGUAGE`, with the source `chosen`), the plot's text
  (`session_state.PLOT_LANGUAGE`) or both (the default), validated like the language
  route (`language.py`); refused while the pipeline runs. With a plot in the session,
  `replies` stores the plot language as it resolves at that moment, so the plot the user
  has keeps its language. Before the first plot it stores none: the first plot follows
  the new reply language, unless the user asked for the plot's text by itself. Since
  2026-11-01 the two are apart: the live test of that day had "Make
  the title German" turn the replies German too. Its result carries no value, only
  whether the reply language `changed` (`de` against `Deutsch` is no change), for the
  reply, and whether the plot is `plot_outdated`: this library's latest rendered
  version has its text in another language than the plot language, so a rewrite of
  the plot's text is due.
* `keep_plot_request(change_request, expected_texts, remember)`: a request for the first plot
  kept without a run (`pipeline.hold_request`, the note the next first-plot run takes),
  for a wish before the confirmation, typed or in the pasted notes (live round 9 of
  2026-10-16), with its lasting decisions for the plot memory, stored once that plot ships.
  It answers `request_kept`, the only basis on which the root may say a
  request is kept; `false` with `plot_exists` when this library already has a plot of
  the current data and the data is confirmed. While the data or the bindings wait for the
  user's check, a change of that plot is kept as one (`PENDING_BASE`, since 2026-11-11), and
  "plot the new data" draws it on the latest version. A plot of data a new paste replaced is none (`CodeVersion.earlier_data`,
  owner decision of 2026-11-08): the note pasted with the new data is kept for that data's
  first plot. Refused while the pipeline runs.
* `forget(entry_id)`: removes an entry of the user's plot memory (`memory.py`, since
  2026-11-02), the standing decisions the page shows and every later run hands the
  adapter and the reviewer, in any library. Entries come in with a run
  (`PipelineArgs.remember`), since the root cannot call a tool after a shipped plot.
  The result carries the count, never a text. Refused while the pipeline runs.
* `switch_plot(library, plot, spec_id)`: a library switch the user asked for in the chat
  ("make it in seaborn"). It writes nothing: the ledger keeps the request, the turn's `done`
  carries it as `switch`, and the page makes the switch with the route and, with `plot`, the
  carry run. Another spec (`plot_type_switch_unavailable`, until the plot-type switch), the
  current library (`same_library`) and a library the service does not serve
  (`library_unavailable`) are refused.
* `prepare_data(operations, from_version)`: at most five operations of the fixed set
  (`data/prepare.py`), applied by the server to the session's current dataset and
  stored as its next version (`dataset_versions.py`): the previous version stays for
  the user's undo, the bindings are carried over, and the confirmation drops by
  itself because it names the dataset id. The result carries the change lines fenced
  as `<tool_notes>` and the new profile fenced as `<user_data>`; a `PrepareError`
  answers its code and its message (which names columns at most, fenced too).
  Refused while the pipeline runs. The model never writes data rows: the operations
  only move, type, aggregate, label, empty or compute from the cells that are there (a
  `make_date` builds a date from the year and month columns of the same row, a `split`
  cuts `10–25` into 10 and 25 at a literal separator, a `compute` evaluates a checked
  expression over number columns). A change no operation can make is the `unsupported`
  operation with its `family`: the call changes nothing and answers `unsupported_operation`
  with the `family` and a fixed sentence in the session language (`refusals.yaml`,
  `unsupported_<family>`), which the root sends instead of pointing the user to their file,
  and the turn's `chat_turn` line counts the gap (`capability_gap`). With `from_version` (`original` or a
  version number the session block lists, since 2026-11-07) the operations start from that earlier version
  instead, none of them taking it as it was, and the result is stored on top all the same: the history is
  never rewritten, the change lines say where it started (`dataset_versions.rebuilt_changes`), and a number
  that is gone answers `other_paste` or `version_not_kept` (`dataset_versions.resolve_version`). Since
  2026-11-14 the `keep_rows` at the end of a call land in the view of the plot instead (`plot_view.route`,
  owner decision of 2026-11-13): which rows the plot draws, stored as session state with no data version,
  so the table and the confirmation stand and the plot may run in the same turn. The result then names
  `landed` (`view`, `table`, `table_and_view`), the view's lines fenced as `<tool_notes>` and, for a view
  alone, `plot_outdated`; `reset_view` clears the view, and a view that does not fit the table the call
  leaves refuses the whole call. A selection held from before that keeps every row of the table the call
  leaves is cleared with a line of its own (`plot_view.idle_selections`). Once a call of the turn has left a
  required role without the column it was bound to, a call that turns a date into numbers or makes the row
  numbers is refused before anything is stored, with `invalid_operation` and a fixed `message`, and counts
  against none of the turn's caps; a call that makes none but whose carry would put such a column of an
  earlier call on a role is stored with that column kept off every role (`data/emptied.py`, `_turn_columns`).
* `query_data(operations, columns, limit, from_version)`: a question about the data answered from a copy
  (`data/query.py`, since 2026-10-15): zero to five operations of `prepare_data`'s set, or of the two only a
  question takes (`prepare.QueryOperation`: an `aggregate` without `by`, a `fit`), then
  the first `limit` rows (at most 25) in at most eight columns, fenced as `<user_data>`, with
  the total row count and the change lines. Nothing is stored: the dataset, its version, the
  bindings and the confirmation stay as they are, so a question never mutates the user's data.
  `from_version` reads an earlier version as `prepare_data` does; a plot button's turn may still call it.
* `generate_data(variables, series)`: a table computed by the server from formulas
  (`data/generate.py`): one or two variables, each a range of evenly spaced points,
  and one to ten series, each an expression over them. The table is parsed like a
  paste and stored as the session's next dataset version (`push_version`, the
  previous data kept for undo) or, in a session without data, as the first version of
  new data the way the dataset route stores a paste, under the session's next number
  either way. The confirmation drops by itself, the
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
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from google.adk import Workflow
from google.adk.tools.tool_context import ToolContext
from pydantic import ValidationError

from core.spec_roles import DataRole

from .. import telemetry
from ..briefs import bindings_text, spec_brief, trimmed_profiles
from ..code.data_code import check_data_code
from ..data.bindings import carry_bindings, check_bindings, resolve_role
from ..data.emptied import Emptied, added_columns, emptied, held_bindings, made_columns, open_roles, renamed
from ..data.generate import Generate, GenerateError, generate
from ..data.parse import MAX_CANONICAL_BYTES, MAX_COMPUTED_BYTES, ParsedDataset, ParseError, parse_dataset
from ..data.prepare import (
    MAX_OPERATIONS,
    ApplyView,
    KeepRows,
    Operation,
    PrepareArgs,
    Prepared,
    PrepareError,
    QueryOperation,
    Unsupported,
    apply_and_parse,
    validation_lines,
)
from ..data.query import DEFAULT_QUERY_ROWS, QueryArgs, QueryResult, run_query
from ..data.shape import long_suggestion
from ..data.store import StoredDataset, StoreFull
from ..dataset_context import code_source, generated_source
from ..dataset_guard import DataRefused, GuardUnavailable, check_dataset
from ..dataset_versions import (
    VersionRefusal,
    VersionRefused,
    kept_versions,
    push_version,
    rebuilt_changes,
    resolve_version,
)
from ..language import LANGUAGE_TARGETS, is_valid, normalise, refusal_lang, same_language
from ..memory import ForgetArgs, MemoryRefused, memory_delta, read_memory
from ..memory import forget as memory_forget
from ..opening import store_dataset
from ..pipeline import (
    PENDING_REASONS,
    has_request,
    hold_request,
    in_users_words,
    load_inputs,
    plot_shows_replaced_data,
    run_pipeline,
)
from ..plot_view import (
    CLEARED_LINE,
    IDLE_SELECTION_LINE,
    Current,
    PlotView,
    Routed,
    Viewed,
    ViewRefused,
    breaks_bindings,
    current,
    idle_selections,
    merged,
    read_view,
    route,
    settled_delta,
    table_only,
    view_delta,
    view_of,
    without_selections,
)
from ..plugins.ledger import RequestLedger, attribution, ledger_for
from ..plugins.tool_safety import (
    DATA_CODE_TOOL,
    MAX_DATA_CODE_CHARS,
    MAX_FILE_NAME_RESULT_BYTES,
    MAX_NOTES_RESULT_BYTES,
    PREPARE_TOOL,
    QUERY_TOOL,
    changed_data,
    result_limit,
    result_size,
)
from ..policy import DATA_PREAMBLE, fence, file_name_block, refusal, user_notes_block
from ..render.contract import DataJob, DataOutput, RendererUnavailable
from ..render.gates import data_rows, error_summary
from ..render.harness import DATA_EXIT
from ..render.runtimes.python import DATA_FILE_NAME
from ..render.serial import RenderBusy
from ..schemas import (
    CURRENT_VERSION,
    MAX_COLUMNS,
    MAX_ROWS,
    PAGE_ARTIFACT,
    Binding,
    DatasetProfile,
    KeepRequestArgs,
    PipelineArgs,
    SwitchArgs,
)
from ..services import CodeVersion, get_services
from ..session_state import (
    PLOT_LANGUAGE,
    SessionView,
    apply_bindings,
    language_delta,
    narrowed_confirmation,
    plot_language,
    read_session,
)
from ..settings import get_settings


PLOT_PIPELINE = "plot_pipeline"
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
    # Versions of another library or spec (before a switch) are not this plot's code.
    stored = get_services().versions.get(tool_context.session.id, version or None, target=view.target)
    if stored is None and version:
        return _error("unknown_version")
    code = stored.export if stored is not None else view.normalised
    result: dict[str, Any] = {
        "status": "ok",
        "version": stored.number if stored is not None else 0,
        "code": DATA_PREAMBLE + "\n" + fence("catalogue_code", code),
    }
    if stored is not None:
        result["data"] = version_data(stored)
    return result


def version_data(stored: CodeVersion) -> dict[str, Any]:
    """What a version's downloaded data holds, counted from the version itself, as the `data` field of
    `get_current_code`'s result:

    * `rows_in_file`: the rows of `data.csv`, and for a JavaScript plot those of its `plot.html`, which embeds the
      typed table (`data_json`), keyed by file name. Counted as records, so a quoted cell with a line break is one row.
    * `view`: present when the version drew its rows through a view of the plot (`CodeVersion.view_rows`): it drew
      `rows` of the table's `of_rows` rows. `rows_in_file` is below `view.rows` when rows of the view that share the
      plot's key were combined for the run (`repeated_keys.combine_in_view`), which the run's change line says
      (`fidelity.combined_in_view_line`).

    The tool's description, which the root reads on every turn, stays one sentence: the root needs these facts only
    when it reads a version, so the keys carry their meaning and this docstring explains them. A longer description,
    with a prompt clause that sent the root here, tipped one routing case into adding a column nobody asked for.

    The version's own facts, never the session's: the session block names the view in force now, which a later
    change of the view, an undo or a switch of the library may have moved away from what this version drew. Integers
    and fixed file names only, so nothing in it needs a fence."""
    rows: dict[str, int] = {"data.csv": data_rows(stored.data_csv)}
    if PAGE_ARTIFACT in stored.artifacts() and stored.data_json is not None:
        rows[PAGE_ARTIFACT] = len(json.loads(stored.data_json)["data"])
    data: dict[str, Any] = {"rows_in_file": rows}
    if stored.view_rows is not None:
        data["view"] = {"rows": stored.view_rows.rows, "of_rows": stored.view_rows.of_rows}
    return data


async def set_bindings(bindings: list[dict[str, str]], tool_context: ToolContext) -> dict[str, Any]:
    """Bind spec data roles to dataset columns. Each binding is {"role": <role name>, "column": <column name>}."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    ledger = ledger_for(tool_context.invocation_id)
    if ledger.pipeline_active:
        return _error("run_active")
    profile = _profile(view, tool_context)
    if profile is None:
        return _not_ready("no_dataset")
    try:
        parsed = [Binding.model_validate(item) for item in bindings]
    except ValueError:
        return _error("invalid_bindings")
    landed = held_bindings(parsed, view.bindings, ledger.made_columns) if ledger.emptied_roles else []
    if landed:
        # A date turned into numbers or the row numbers, made in a turn whose change of the data emptied a role, take
        # no role in it (`data/emptied.py`).
        ledger.guard_held.append("set_bindings")
        columns = [binding.column for binding in landed]
        _note_held(
            ledger, "set_bindings", ledger.emptied_roles, [ledger.added_columns.get(name, "") for name in columns]
        )
        missing = check_bindings(view.bindings, view.snapshot.roles(), profile).missing_roles
        waiting = any(role in missing for role in ledger.emptied_roles)
        return _column_held(ledger.emptied_roles, {}, [], columns, "invalid_bindings", waiting=waiting)
    roles = view.snapshot.roles()
    check, delta = apply_bindings(parsed, roles, profile)
    if not delta:
        # The errors quote column names from the user's dataset.
        errors = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(check.errors[:10], ensure_ascii=False))
        return {"status": "error", "code": "invalid_bindings", "errors": errors}
    emptied_roles = ledger.emptied_roles
    _note_taken(
        ledger, "set_bindings", view.bindings, parsed, roles, emptied_roles, emptied_roles, ledger.added_columns
    )
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
    if check.warnings:  # valid, but a column that misfits its role, or a key the rows repeat; they name columns
        telemetry.note_binding_warnings(tool_context.session.id, check.warnings)  # closed codes for `chat_turn`
        result["warnings"] = DATA_PREAMBLE + "\n" + fence("user_data", json.dumps(check.warnings, ensure_ascii=False))
    return result


async def set_language(language: str, tool_context: ToolContext, applies_to: str = "both") -> dict[str, Any]:
    """Set the language of your replies, of the text in the plot (title, axis titles, legend entries, annotations), or of both. `language` is a short language name or code such as "de", "English" or "Swedish". `applies_to`: "plot" when the user asks for the plot's text in a language ("labels in English", "make the title German"), "replies" when they ask for your answers in one ("answer in French"), "both" when they ask for both or for the whole session in one. The next plot version uses the plot language; code, comments and column names stay as they are."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    if not isinstance(language, str):
        return _error("invalid_language")
    if applies_to not in LANGUAGE_TARGETS:
        return _error("invalid_arguments")
    value = normalise(language)
    if not is_valid(value):
        return _error("invalid_language")
    versions = get_services().versions
    replies = applies_to in ("both", "replies")
    plot: str | None = value
    if applies_to == "replies":
        # With a plot in the session, the plot keeps its language as it resolves now. Before the first plot nothing
        # is written for it: the first plot follows the new reply language (`plot_language`), unless the user asked
        # for the plot's text by itself before, a choice that stays as it is.
        drawn = versions.latest_language(tool_context.session.id)
        plot = plot_language(view, drawn) if drawn is not None else None
    changed = replies and not same_language(view.language, value)
    # The plot the user sees is this library's latest render; its text may be in another language than the
    # plot language (made before a choice in another library), so the rewrite is decided against it.
    latest = versions.latest_rendered(tool_context.session.id, target=view.target)
    plot_outdated = latest is not None and plot is not None and not same_language(latest.language, plot)
    # A request for the replies' language is a pick, final either way: no language is offered after it. One for the
    # plot's text alone leaves the replies and their source, so a German "Beschriftung auf Deutsch" in an English
    # session still offers German replies. Nothing but a pick writes the plot's language.
    delta = {**(language_delta(value, "chosen") if replies else {}), **({} if plot is None else {PLOT_LANGUAGE: plot})}
    for key, item in delta.items():
        tool_context.state[key] = item
    return {"status": "ok", "source": "chosen", "changed": changed, "plot_outdated": plot_outdated}


async def keep_plot_request(
    change_request: str,
    tool_context: ToolContext,
    expected_texts: list[str] | None = None,
    remember: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Keep a request for this library's next plot of the current data without starting a run: the user's next plot draws it. Use it while the data or the bindings wait for the user's check: for a plot wish before the first plot (a title, a scale), typed or in the pasted notes, also when the library has a plot of data pasted before, and for a change of the plot this library has when the data changed, also in the turn that changed it (after the data tool). `change_request` is a short English description (at most 600 characters); `expected_texts` lists the texts and number formats the user wrote out, verbatim; `remember` the request's lasting decisions, as for plot_pipeline. Returns request_kept: true when the server keeps it; false, with a reason, when this library has a plot of the current data and the data is confirmed (plot_exists: then call plot_pipeline with base "previous"), or when nothing is left to keep once the texts the user did not write are left out (nothing_to_keep)."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    try:
        args = KeepRequestArgs.model_validate(
            {"change_request": change_request, "expected_texts": expected_texts or [], "remember": remember or []}
        )
    except ValidationError:
        return _error("invalid_arguments")
    services = get_services()
    latest = services.versions.latest_rendered(tool_context.session.id, target=view.target)
    # A plot of data a new paste replaced is no plot of this data: the note pasted with the new data is for its first
    # plot (owner decision of 2026-11-08), which the fresh run of the plot button takes (`take_pending_request`).
    exists = latest is not None and not plot_shows_replaced_data(services, tool_context.session.id, view)
    ledger = ledger_for(tool_context.invocation_id)
    # A change of a plot of the current data runs at once while the data is confirmed: nothing to keep. While the
    # data or the bindings wait for the user's check, also after this turn's own change of the data, whose new
    # version is never confirmed in its turn, it is kept as that change (`PENDING_BASE`), and "plot the new data"
    # draws it on the latest version.
    waits = changed_data(ledger) or load_inputs(tool_context, services)[2] in PENDING_REASONS
    if exists and not waits:
        return {"status": "ok", "request_kept": False, "reason": "plot_exists"}
    kept = PipelineArgs(**args.model_dump(), base="previous") if exists else PipelineArgs(**args.model_dump())
    # A text the user never wrote is no text to check the plot for: only what stands in their words is kept.
    note = in_users_words(kept, ledger.user_words)
    if not has_request(note):
        return {"status": "ok", "request_kept": False, "reason": "nothing_to_keep"}
    hold_request(tool_context.state, note)
    ledger.kept_note = note  # held for the bindings and data this turn ends with (`_settle_kept_note`)
    return {"status": "ok", "request_kept": True}


async def forget(entry_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Remove a decision from the user's plot memory by its id, as the session block lists it, when the user takes it back ("no reference line after all") or asks you to forget it. The plot itself changes only through plot_pipeline. Returns the number of entries left."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    if ledger_for(tool_context.invocation_id).pipeline_active:
        return _error("run_active")
    try:
        args = ForgetArgs(entry_id=entry_id)
    except ValidationError:
        return _error("invalid_arguments")
    try:
        entries = memory_forget(read_memory(tool_context.state), args.entry_id)
    except MemoryRefused as exc:
        return _error(exc.code)
    for key, value in memory_delta(entries).items():
        tool_context.state[key] = value
    return {"status": "ok", "entries": len(entries)}


async def switch_plot(
    library: str, tool_context: ToolContext, plot: bool = True, spec_id: str | None = None
) -> dict[str, Any]:
    """Move the plot to another library when the user asks for it ("make it in seaborn", "zeig das in ggplot2"): after this turn the page switches the library and, with plot true, makes the plot there at once from that library's catalogue plot with the user's decisions (the plot memory). library: one of the libraries the session block lists to switch to. plot: false only when the user wants to switch without a plot yet. spec_id: leave it out; another plot type is not offered yet. Writes nothing and starts no run: call no plot_pipeline in the same turn. Returns switch_requested: true, or an error code."""
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    try:
        args = SwitchArgs.model_validate({"library": library, "plot": plot, "spec_id": spec_id})
    except ValidationError:
        return _error("invalid_arguments")
    if args.spec_id is not None and args.spec_id != view.spec_id:
        return _error("plot_type_switch_unavailable")  # the target is a pair already; the route refuses another spec
    if args.library not in get_settings().libraries:
        return _error("library_unavailable")
    if args.library == view.library:
        return _error("same_library")
    request: dict[str, Any] = {"library": args.library, "plot": args.plot}
    if args.spec_id is not None:
        request["spec_id"] = args.spec_id
    ledger_for(tool_context.invocation_id).switch_request = request
    return {"status": "ok", "switch_requested": True}


def _conversion_outcome(
    prepared: Prepared, profile: DatasetProfile, bindings: list[Binding]
) -> telemetry.ConversionOutcome | None:
    """What `prepare_data` made for an open role, as the `chat_turn` reports it (`telemetry.ConversionOutcome`).

    A column read in place (its own source in `converted`) counts only when a role took it: re-typing a column that
    fills no role is no conversion for an open role.
    """
    if prepared.row_numbers:
        return "index"
    dtypes = {column.name: column.dtype for column in profile.columns}
    bound = {binding.column for binding in bindings}
    made = [name for name, source in prepared.converted.items() if name != source or name in bound]
    if not made:
        return None
    return "date" if any(dtypes.get(name) == "datetime" for name in made) else "number"


def capability_gap(
    operations: Sequence[Operation | QueryOperation], view: SessionView, tool_context: ToolContext
) -> dict[str, Any] | None:
    """The answer to an `unsupported` operation among `operations`, None without one.

    A change no operation can make: the service's own sentence in the session language (`refusals.yaml`,
    `unsupported_<family>`), never a word of the request, and the gap counted by its family alone
    (`capability_gap`). Nothing runs and nothing changes. `prepare_data` and `query_data` answer it alike, so a gap
    named in a question reads the same as one named for a change.
    """
    gap = next((operation for operation in operations if isinstance(operation, Unsupported)), None)
    if gap is None:
        return None
    ledger_for(tool_context.invocation_id).capability_gaps.append(gap.family)
    message = refusal(f"unsupported_{gap.family}", refusal_lang(view.language))
    return {"status": "error", "code": "unsupported_operation", "family": gap.family, "message": message}


VERSION_MESSAGES: dict[VersionRefusal, str] = {
    "other_paste": (
        "no version of the current data has that number: it was a version of data the user pasted over, which is "
        "gone; the session block lists the versions of the current data"
    ),
    "version_not_kept": (
        "that version of the current data is gone (undone, or older than the history keeps); the session block lists "
        "the versions you can start from"
    ),
}
"""The fixed message of a `from_version` refusal (`dataset_versions.VersionRefusal`): server text, never the user's."""


def _version_refusal(code: VersionRefusal) -> dict[str, Any]:
    return {"status": "error", "code": code, "message": VERSION_MESSAGES[code]}


COLUMN_HELD_MESSAGE = (
    "Nothing changed. A change of this turn takes the column of {roles}, so in this turn no date is turned into "
    "numbers and no row number is made, and none takes a role. Make the rest of the change without that column. In "
    "the reply, name the role whose column the change takes and say that the next turn lists what can fill it; if the "
    "user asked for the column held here, say it can be made in the next turn."
)
"""The refusal of the guard on an emptied role (`data/emptied.py`): server text, the role names the spec's own; the
columns stand fenced beside it under `errors`. It names no operation the root could try instead, since a derived
column on the emptied axis would pass the guard (the known gap its log line counts), and it says why a conversion the
user did ask for waits a turn. It never says a role lost its column, since the call it refuses may be the one that
would have emptied it: the `errors` lines tell the two apart. It comes with the code the tool answers a call it cannot
make with (`invalid_operation`, `invalid_bindings`), as the refusal of a view that would break the bindings does."""
COLUMN_HELD_FILLED_MESSAGE = (
    "Nothing changed. A change of this turn took the column of {roles}, so in this turn no date is turned into "
    "numbers and no row number is made, and none takes a role. Make the rest of the change without that column; if "
    "the user asked for the column held here, say in the reply that it can be made in the next turn."
)
"""The same refusal once no role the turn emptied is open any more (the root bound a column that was there to it):
it says only what holds, and nothing about a role that waits or about what the next turn lists for it."""
LOST_LINE = "{role} lost its column '{column}' in an earlier change of this turn"
LOSING_LINE = "{role} would lose its column '{column}' with this call"
MADE_NOW_LINE = "'{name}' holds a date turned into numbers or the row numbers, and this call would make it"
MADE_BEFORE_LINE = "'{name}' holds a date turned into numbers or the row numbers, made earlier in this turn"
"""The `errors` lines of the guard's refusal, fenced since they name the user's columns: a role an earlier call of the
turn emptied, a role this call would empty, a column this call would make, a column an earlier call made."""


def _column_held(
    lost: Mapping[str, str],
    losing: Mapping[str, str],
    made_now: Sequence[str],
    made_before: Sequence[str],
    code: str,
    *,
    waiting: bool,
) -> dict[str, Any]:
    """The refusal with `code` of a call that would make or bind a date turned into numbers or the row numbers in a
    turn that emptied the roles of `lost`, or of `losing` with this very call (each role: the column it was bound to):
    the fixed message, `COLUMN_HELD_MESSAGE` while one of those roles is open (`waiting`) and
    `COLUMN_HELD_FILLED_MESSAGE` once none is, and the lines that name the columns, fenced."""
    lines = [
        *(LOST_LINE.format(role=role, column=column) for role, column in lost.items()),
        *(LOSING_LINE.format(role=role, column=column) for role, column in losing.items() if role not in lost),
        *(MADE_NOW_LINE.format(name=name) for name in dict.fromkeys(made_now)),
        *(MADE_BEFORE_LINE.format(name=name) for name in dict.fromkeys(made_before) if name not in made_now),
    ]
    roles = list(dict.fromkeys([*lost, *losing]))
    message = (COLUMN_HELD_MESSAGE if waiting else COLUMN_HELD_FILLED_MESSAGE).format(roles=", ".join(roles))
    return {"status": "error", "code": code, "message": message, "errors": _fenced_lines(lines)}


def _note_held(
    ledger: RequestLedger, tool: str, roles: Iterable[str], kinds: Iterable[str], *, outcome: str = "refused"
) -> None:
    """The guard's log line (hook `emptied_role`) for a call it held a column from: the tool, the outcome (`refused`,
    or `kept_off` for a change stored with an earlier call's fill kept off every role), the roles the turn's change
    takes the column of, and the names of the operations that made the held columns. Content-free: the spec's role
    names and closed operation names, never a column or a cell."""
    attribution(
        "emptied_role",
        ledger,
        tool=tool,
        outcome=outcome,
        roles=sorted(set(roles)),
        kinds=sorted({kind for kind in kinds if kind}),
    )


def _note_taken(
    ledger: RequestLedger,
    tool: str,
    before: Collection[Binding],
    after: Sequence[Binding],
    roles: list[DataRole],
    taken: Collection[str],
    emptied: Collection[str],
    added: Mapping[str, str],
) -> None:
    """The guard's log line for each new binding of `after` that fills a role the turn took the column of. Both
    count, neither judges: the line is written whether the user asked for the binding or not.

    * `bound`: a column an operation of the turn added (`added`, with the operation's name) on a role of `taken`, the
      roles whose column the turn took: the known gap, a derived column or a text conversion the guard lets through.
    * `refilled`: a column that was there before the turn (no operation of it added the column) on a role of
      `emptied`, the roles the turn left open (`RequestLedger.emptied_roles`), by `set_bindings` or by the carry of a
      later call, such as a column read as numbers in place that the carry puts on the open role. Only the role: the
      column is the user's. A role whose column a rename moved is not in `emptied`, so a rename is no refill."""
    for binding in after:
        role = resolve_role(binding.role, roles)
        name = role.name if role is not None else binding.role
        if binding in before:
            continue
        if binding.column in added and name in taken:
            attribution("emptied_role", ledger, tool=tool, outcome="bound", role=name, kind=added[binding.column])
        elif binding.column not in added and name in emptied:
            attribution("emptied_role", ledger, tool=tool, outcome="refilled", role=name)


@dataclass(frozen=True)
class _TurnColumns:
    """What one `prepare_data` call does to the guard on an emptied role: the roles it empties (`emptied`), the
    turn's columns of a date turned into numbers or the row numbers once it is stored (`made`) and the columns its
    operations added with their names (`added`), its refusal when it would make one of `made` or put one on a role in
    a turn that emptied a role, and `kept_off`, the earlier calls' fills its carry gives no role when the call is
    stored."""

    emptied: list[Emptied]
    made: list[str]
    added: dict[str, str]
    refusal: dict[str, Any] | None = None
    kept_off: list[str] = field(default_factory=list)


def _turn_columns(
    ledger: RequestLedger,
    bindings: list[Binding],
    roles: list[DataRole],
    current: DatasetProfile,
    start: DatasetProfile,
    parsed: ParsedDataset,
    prepared: Prepared | None,
    operations: Sequence[Operation],
) -> _TurnColumns:
    """The guard on an emptied role for one `prepare_data` call (`data/emptied.py`).

    `bindings` are the ones in force on `current`, the current version; `start` is the version the call's operations
    start from (another one for a rebuild); `parsed` is the table they leave. The turn's columns of a date turned into
    numbers or the row numbers (`emptied.made_columns`) are the earlier calls' under this call's renames and this
    call's own new ones, each while the table still has it. The call empties a role when it leaves one open that it
    found bound, judged with those columns hidden that no role held. Once the turn has emptied a role, the call is
    refused when it makes such a column, or when the carry that stores it (`push_version`, which computes the same
    bindings) would move one a role held. When the carry would only put an earlier call's fill on a role, the call is
    the user's change and is stored, with every such fill no role holds kept off the roles (`kept_off`).
    """
    names = {column.name for column in parsed.profile.columns}
    converted = prepared.converted if prepared is not None else {}
    row_numbers = prepared.row_numbers if prepared is not None else []
    splits = prepared.splits if prepared is not None else []
    date_numbers = prepared.date_numbers if prepared is not None else []
    before = {column.name for column in start.columns}
    new = [name for name in made_columns(date_numbers, row_numbers, before) if name in names]
    made = [name for name in dict.fromkeys([*renamed(ledger.made_columns, operations), *new]) if name in names]
    earlier = dict(zip(renamed(list(ledger.added_columns), operations), ledger.added_columns.values(), strict=True))
    added = {
        name: kind
        for name, kind in {**earlier, **added_columns(operations, before, names, new)}.items()
        if name in names
    }
    bound = {binding.column for binding in bindings}
    still_open = open_roles(bindings, roles, current, parsed.profile, set(made) - bound)
    now = {item.role: item.column for item in emptied(bindings, roles, current, still_open)}
    if not ledger.emptied_roles and not now:
        return _TurnColumns([], made, added)
    emptied_now = [Emptied(role, column) for role, column in now.items()]
    carried = carry_bindings(bindings, roles, parsed.profile, current, converted, row_numbers, splits)
    landed = [binding.column for binding in held_bindings(carried, bindings, made)]
    if not new and not landed:
        return _TurnColumns(emptied_now, made, added)
    emptying = [*ledger.emptied_roles, *now]
    kinds = [added.get(name, "") for name in [*new, *landed]]
    if not new and not bound & set(landed):
        # Fills an earlier call of the turn made, which this change's carry would put on a role: the change is the
        # user's and is stored, every such fill no role holds stays off every role, and the role waits for the user.
        _note_held(ledger, PREPARE_TOOL, emptying, kinds, outcome="kept_off")
        return _TurnColumns(emptied_now, made, added, kept_off=[name for name in made if name not in bound])
    _note_held(ledger, PREPARE_TOOL, emptying, kinds)
    waiting = any(role in still_open for role in emptying)
    refusal = _column_held(ledger.emptied_roles, now, new, landed, "invalid_operation", waiting=waiting)
    return _TurnColumns(emptied_now, made, added, refusal)


async def prepare_data(
    operations: list[dict[str, Any]], tool_context: ToolContext, from_version: str = CURRENT_VERSION
) -> dict[str, Any]:
    """Change the user's dataset with one to five operations, applied in order by the server; the result becomes the next version of the data, which the user then checks and confirms.

    from_version: the version the operations start from: "current" (the default), "original" (the first version, the
    table as the user pasted or opened it) or a version number the session block lists, such as "2"; the result is
    stored as the next version on top all the same, and the change lines say where it started. From an earlier
    version, operations may be empty: that version as it was becomes the next one.

    Each operation is an object with "op" and its fields, column names exactly as the profile lists them:
    rename (column, name); drop_columns (columns); drop_rows (where: conditions on single columns that must all hold,
    each {column, test, value}, or with values: a list of which any one may match, for test eq or contains; test is
    eq|ne|contains|is_missing|not_missing|gt|lt|ge|le);
    set_type (column, type number|datetime|text, date_format, decimal); aggregate (by, column or columns: several
    value columns, how sum|mean|count|min|max|first|last, period hour|day|week|month|quarter|year; first and last
    take a group's first and last value, by time within a period of a date key); sort (column, descending); pivot_longer
    (columns, names_to, values_to); pivot_wider
    (names_from, values_from, index); classify (name, rules: each where conditions and a label, otherwise: the optional
    label for rows no rule matches; adds the text column name, labelling each row by the first rule that holds); derive
    (name, how ratio|difference|sum|share|percent_change|cumsum|index, columns, within, order, percent; adds the number
    column name computed from number columns: columns[0] / columns[1], columns[0] - columns[1], a row sum, a share of
    the group's total, or, in the order of a number or date column order, the percent change from the previous row,
    the running total, or an index with the group's first row = 100); make_date (name, year, and month with an
    optional day, or quarter, or week; adds the date column name built from whole-number columns holding the parts of
    a date, a part left out being its first: year and month give the first day of each month); row_number (name; adds
    the whole-number column name, default index, the rows numbered 1 to n); date_number (column, unit
    year|days|timestamp|decimal_year, name; adds a number column from a date column: the calendar year, the whole days
    since the column's earliest date = 0, the Unix time in seconds in UTC, or the year plus the part of it gone by;
    name left out, the server names it after the column and the unit); and four text operations on the cells of
    column, each adding new columns typed by their cells (numbers, dates or text) and keeping column as it is: split
    (column, separator: a literal text such as - or –, names: 2 to 10 new columns; 10–25 gives 10 and 25), extract
    (column, keep number|digits|letters, name; number for an amount, CHF 1'200 gives 1200; digits for an id or a
    code), strip (column, prefix, suffix, name; takes a literal
    text off the start or the end of each cell) and replace (column, old, new, name; new empty removes old); compute
    (name, expression, inputs; adds the number column name from an expression over number columns, with the
    expression language of generate_data, inputs mapping each short name of the expression to its column, such as
    {"q": "Quantity", "p": "Price"} for q * p); diff (name, column, order, within, lag; adds the change of column from
    the row lag places before, default 1, in the order of a number or date column order); rolling (name, column, how
    mean|sum, window, order, within; adds the mean or sum over window rows, each row and the ones before it); blank
    (columns, where; empties the cells of columns in the rows where the conditions hold, the rows stay); keep_rows (n
    or where, one of the two, and target plot|table, default plot; n keeps the first n rows in their current order:
    the top 10 by revenue is a sort descending, then keep_rows 10; where keeps the rows for which the conditions
    hold: only some categories, only a period as ge its start and le its end; it lands in the view of the plot, which
    says which rows the plot draws and leaves the table, its version and the user's confirmation as they are; with
    target table the table itself loses the other rows); reset_view (no fields; first in a call, clears the view of
    the plot so every row is drawn again); apply_view (no fields; first in a call, puts the rows the view of the plot
    shows in place of the table's, so the operations after it work on those rows and no view is left);
    unsupported
    (family fill_values|edit_cells|add_rows|combine_tables|text_pattern|time_window|other; alone, for a change no
    operation can make: it changes nothing and answers unsupported_operation with a fixed message to send). Steps
    chain in one call: a later operation may name a column an earlier one made. Returns the change lines and the new
    profile, or an error with a code and a message. A call whose keep_rows landed in the view returns landed (view,
    or table_and_view), the view's lines with the rows the plot now draws, and for a view alone plot_outdated: true
    when the plot on the page still shows other rows, so a plot run in the same turn is due.
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
        if not isinstance(operations, list) or len(operations) > MAX_OPERATIONS:
            raise ValueError(f"operations is a list of 1 to {MAX_OPERATIONS} operations")
        args = PrepareArgs.model_validate({"operations": operations, "from_version": from_version})
    except ValidationError as exc:
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines(validation_lines(exc))}
    except ValueError as exc:
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines([str(exc)])}
    if (gap := capability_gap(args.operations, view, tool_context)) is not None:
        return gap
    try:
        start = resolve_version(kept_versions(services.datasets, session_id, view), args.from_version)
    except VersionRefused as exc:
        return _version_refusal(exc.code)
    if start.current and not args.operations:  # `from_version` named the current version by its number
        lines = ["from_version names the current version, and there is no operation: nothing would change"]
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines(lines)}
    try:
        # A call that names the version it starts from rebuilds the table, so everything in it is the table's: the
        # rows the user asks back are in no view. Also when that version is the current one, by its number or as the
        # original: the root said which table it means.
        rebuilds = args.from_version != CURRENT_VERSION
        routed = table_only(args.operations) if rebuilds else route(args.operations)
        # The view held from before, as it holds for the current table: one that no longer fits it (after an undo,
        # a change in the data panel) counts as none, so it never makes this call fail for a column that is gone.
        roles = view.snapshot.roles()
        now = current(tool_context.state, stored, view.language, bindings=view.bindings, roles=roles)
        held = now.view
        if routed.apply and held.empty:
            raise ViewRefused("there is no view of the plot to apply: the plot draws every row of the table")
        shown = merged(held, routed) if routed.view else held
    except ViewRefused as exc:
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines([str(exc)])}
    # Whether the call makes a data version: the table's operations, the view's rows put in the table's place
    # (`apply_view`), or an earlier version taken as it was.
    stores = bool(routed.table) or routed.apply or not start.current
    prepared: Prepared | None = None
    moved: list[str] = []
    try:
        parsed = start.stored.as_parsed()  # the version as it is: an earlier one as the next, or a view's table
        if routed.apply:
            # The view's own operations, as a step of the table: the rows it showed are the table the rest works on.
            applied, parsed = apply_and_parse(parsed, held.operations(), language=view.language)
            moved = list(applied.changes)
        if routed.table:
            prepared, parsed = apply_and_parse(parsed, routed.table, language=view.language)
    except PrepareError as exc:
        # The message names columns of the user's dataset at most, never a cell; fenced like every column name.
        return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
    except ParseError:  # the operations keep every parser cap (rows, columns, size), so a refusal here is a bug
        return _error("internal")
    turn: _TurnColumns | None = None
    if stores:
        # Checked on the table and the bindings the call would leave, before anything is stored (`data/emptied.py`).
        turn = _turn_columns(
            ledger, view.bindings, roles, stored.profile, start.stored.profile, parsed, prepared, routed.table
        )
        if turn.refusal is not None:
            ledger.guard_held.append(PREPARE_TOOL)
            return turn.refusal
    # The view is checked on the table the call leaves, before anything is stored: a view of this call that does not
    # fit refuses the whole call, a view held from before is cleared with a line.
    seen: Viewed | None = None
    cleared = now.cleared is not None  # a view that had stopped fitting before this call is written out with it
    if not shown.empty:
        try:
            seen = view_of(parsed, shown, view.language)
        except PrepareError as exc:
            if routed.view:
                return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
            shown, cleared = PlotView(), True
    if seen is not None:
        # The bindings the view has to hold on: the ones in force, or the ones the new version will carry
        # (`push_version` computes them the same way), so a call that changes the table is checked like any other.
        bound = view.bindings
        if stores:
            kept_off = set(turn.kept_off) if turn is not None else set()
            bound = carry_bindings(
                view.bindings,
                roles,
                parsed.profile.model_copy(
                    update={"columns": [column for column in parsed.profile.columns if column.name not in kept_off]}
                ),
                start.stored.profile,
                prepared.converted if prepared is not None else None,
                prepared.row_numbers if prepared is not None else (),
                prepared.splits if prepared is not None else (),
            )
        if breaks_bindings(bound, roles, parsed.profile, seen.parsed.profile):
            if routed.view:
                message = _fenced_lines([VIEW_BREAKS_BINDINGS])
                return {"status": "error", "code": "invalid_operation", "message": message}
            shown, seen, cleared = PlotView(), None, True
    idle: list[str] = []
    if stores and seen is not None:
        # A selection held from before that keeps every row the new table has: the change of the table did what it
        # did, so it is cleared with a line (`plot_view.idle_selections`). One the call named itself is its own word.
        before = (
            PlotView()
            if routed.reset
            else PlotView(selections=[w for w in held.selections if w not in routed.selections])
        )
        gone = idle_selections(shown, before, parsed, view.language)
        if gone:
            text = [name for name, dtype in parsed.column_dtypes.items() if dtype == "text"]
            idle = [IDLE_SELECTION_LINE.format(words=PlotView(selections=[where]).words(text)) for where in gone]
            shown = without_selections(shown, gone)
            seen = None if shown.empty else view_of(parsed, shown, view.language)
    if not stores:
        return _view_result(tool_context, view, start.stored, shown, seen, routed)
    changes = rebuilt_changes(start, [*moved, *(prepared.changes if prepared is not None else [])])
    # The view as stored before the call (also one that had stopped fitting) and the view the call leaves: kept with
    # the version, so its undo takes back what the step did to the view as well (`StoredDataset.view_change`).
    view_before, view_after = read_view(tool_context.state).stamp(), shown.stamp()
    try:
        # From an earlier version too, the result goes on top: the history is never rewritten, and `.undo()` steps
        # back to the version the turn began with.
        version = push_version(
            services.datasets,
            session_id,
            view,
            parsed,
            view.snapshot,
            converted=prepared.converted if prepared is not None else None,
            row_numbers=prepared.row_numbers if prepared is not None else (),
            splits=prepared.splits if prepared is not None else (),
            changes=changes,
            made_from=None if start.current else start.stored,
            kept_off=turn.kept_off if turn is not None else (),
            view_change=(view_before, view_after) if view_before != view_after else None,
        )
    except StoreFull:
        return _error("capacity")
    # The new dataset id leaves the confirmation's fingerprint behind: the user confirms the new version.
    for key, value in version.delta.items():
        tool_context.state[key] = value
    if prepared is not None and (outcome := _conversion_outcome(prepared, parsed.profile, version.bindings)):
        telemetry.note_conversion(session_id, outcome)
    ledger.dataset_changes.extend(changes)
    # The names only, for the telemetry; an applied view is the table's step, under its own name.
    ledger.prep_ops.extend([*(["apply_view"] if routed.apply else []), *(op.op for op in routed.table)])
    if not start.current:
        ledger.rebuilt_from.append(start.number)
    if turn is not None:
        ledger.made_columns, ledger.added_columns = turn.made, turn.added
        for item in turn.emptied:
            ledger.emptied_roles.setdefault(item.role, item.column)
        # The roles whose column this call took (gone, or no longer fitting the role), filled or not.
        took = {
            role.name
            for binding in view.bindings
            if check_bindings([binding], roles, parsed.profile).errors
            and (role := resolve_role(binding.role, roles)) is not None
        }
        taken = {*ledger.emptied_roles, *took}
        emptied_roles = ledger.emptied_roles
        _note_taken(ledger, PREPARE_TOOL, view.bindings, version.bindings, roles, taken, emptied_roles, turn.added)
    base = {
        "status": "ok",
        "rows": parsed.profile.rows,
        "columns": len(parsed.profile.columns),
        "version": version.version,
        "changes": DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(changes, ensure_ascii=False)),
    }
    if routed.view or cleared or idle:
        # The view of this call, or one held from before that the new table no longer fits or no longer needs all of:
        # stored with the version. Only a view the call itself named settles what a paste had set aside
        # (`settled_delta`).
        for key, value in (settled_delta(shown) if routed.view else view_delta(shown)).items():
            tool_context.state[key] = value
        ledger.view_ops.extend(view_op_names(routed))
        # An applied view that left none behind landed in the table alone.
        both = routed.view and not (routed.apply and shown.empty)
        base["landed"] = "table_and_view" if both else "table"
        base["view"] = _view_lines(
            shown, seen, version.version, parsed.profile.rows, cleared=cleared, applied=routed.apply, idle=idle
        )
    elif any(isinstance(operation, KeepRows) for operation in routed.table):
        base["landed"] = "table"  # a `keep_rows` the call's order or its `target` sent to the table
    if version.bindings != view.bindings:
        # The server moved them (`carry_bindings`): the reply names these, not the ones the turn started from (live
        # run of 2026-11-02: the root saw x on `value` and called the row numbers a mistake).
        base["bindings"] = DATA_PREAMBLE + "\n" + fence("user_data", bindings_text(version.bindings))
    return _with_profile(base, parsed.profile, "prepare_data")


VIEW_BREAKS_BINDINGS = (
    "with this view a column the plot is bound to would hold no usable value: the bindings would no longer hold, so "
    "the view was not set"
)
"""`prepare_data`'s refusal of a view whose rows leave a bound column the plot cannot read (every cell empty)."""
VIEW_CLEARED = "the view of the plot is cleared: the plot draws every row of the table again"
VIEW_APPLIED = "the view of the plot was applied to the table: the rows it showed are the table now, and no view is set"
"""`prepare_data`'s line for an `apply_view`: the table took the view's rows, as a data version the user checks."""
NO_VIEW_TO_ASK = "there is no view of the plot to apply: the plot draws every row of the table, so leave apply_view out"


def view_op_names(routed: Routed) -> list[str]:
    """The operation names of a call's view part, as the telemetry counts them: the names only. An applied view is
    the table's step and counts there (`RequestLedger.prep_ops`)."""
    names = ["reset_view"] if routed.reset and not routed.apply else []
    names += ["keep_rows"] * len(routed.selections)
    return [*names, "sort", "keep_rows"] if routed.top is not None else names


def _view_lines(
    shown: PlotView,
    seen: Viewed | None,
    data_version: int,
    table_rows: int,
    *,
    cleared: bool,
    applied: bool = False,
    idle: Sequence[str] = (),
) -> str:
    """The view as a tool result carries it, fenced: each step's line with its counts and the server's summary, or the
    one line of a view that is no more: applied to the table, cleared by the call, or no longer fitting. `idle` are
    the lines of the selections the call's change of the table cleared (`plot_view.idle_selections`), which say why
    on their own."""
    if seen is not None and not shown.empty:
        lines = [*([VIEW_APPLIED] if applied else []), *idle, *seen.changes, seen.summary(data_version)]
    else:
        gone = [VIEW_APPLIED] if applied else [CLEARED_LINE] if cleared else [] if idle else [VIEW_CLEARED]
        lines = [*gone, *idle, f"the plot draws all {table_rows} rows of data v{data_version}"]
    return DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(lines, ensure_ascii=False))


def _view_result(
    tool_context: ToolContext,
    view: SessionView,
    stored: StoredDataset,
    shown: PlotView,
    seen: Viewed | None,
    routed: Routed,
) -> dict[str, Any]:
    """`prepare_data`'s answer to a call that changed the view alone: the view is stored, the table, its version and
    the user's confirmation stay as they are.

    `plot_outdated` says that this library's latest plot of the data drew other rows than the view now shows, so a
    run is due: the root may start it in the same turn, since no data changed.
    """
    for key, value in settled_delta(shown).items():
        tool_context.state[key] = value
    ledger = ledger_for(tool_context.invocation_id)
    ledger.view_ops.extend(view_op_names(routed))
    services = get_services()
    latest = services.versions.latest_rendered(tool_context.session.id, target=view.target)
    # A run is due, and can start, only for a plot of this very table that the user confirmed: a plot of an earlier
    # version waits for the user's check of the new data, whatever the view says.
    drew_this = (
        latest is not None
        and view.data_confirmed
        and latest.drew(stored.number)
        and not plot_shows_replaced_data(services, tool_context.session.id, view)
    )
    return {
        "status": "ok",
        "landed": "view",
        "rows": seen.rows if seen is not None else stored.profile.rows,
        "of_rows": stored.profile.rows,
        "version": stored.number,
        "view": _view_lines(shown, seen, stored.number, stored.profile.rows, cleared=False),
        "plot_outdated": drew_this and latest is not None and latest.view != shown.stamp(),
    }


async def query_data(
    operations: list[dict[str, Any]],
    tool_context: ToolContext,
    columns: list[str] | None = None,
    limit: int = DEFAULT_QUERY_ROWS,
    from_version: str = CURRENT_VERSION,
) -> dict[str, Any]:
    """Answer a question about the user's data without changing it: the operations are applied to a copy and the first rows of the result come back as a small table; nothing is stored, and the data, its version and its confirmation stay as they are.

    operations: zero to five operations of the same set as prepare_data, plus fit, applied in order (keep only some
    rows with keep_rows and where, such as test eq on the year asked about; a top N is a sort with limit; a share, a
    percent change or an index is a derive, a change from the row before a diff, another formula a compute; a total
    or a mean per group an aggregate, and over all rows an aggregate without by; fit (x, y) is the least-squares line
    of the number column y on the number column x as one row of slope, intercept, r_squared and n, which a later
    compute can use; apply_view first asks the question of the rows the view of the plot shows instead of every row
    of the table). columns: the columns to return, at most 8
    (default: the first 8). limit: the rows to return, 1 to 25 (default 10). from_version: the version to read,
    "current" (the default), "original" (the first version, the table as the user pasted or opened it) or a version
    number the session block lists. Returns the table (columns and rows), the number of rows of the whole result,
    whether it was cut, and the change lines, which name a tie when the cut at limit falls among rows a sort ranked
    equal; while a view of the plot is in force, view says which rows the answer read. Or an error with a code and
    a message.
    """
    view = _view(tool_context)
    if view is None:
        return _error("session_not_open")
    stored = _stored(view, tool_context)
    if stored is None:
        return _not_ready("no_dataset")
    try:
        args = QueryArgs.model_validate(
            {"operations": operations, "columns": columns, "limit": limit, "from_version": from_version}
        )
    except ValidationError as exc:
        return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines(validation_lines(exc))}
    if (gap := capability_gap(args.operations, view, tool_context)) is not None:
        return gap
    try:
        start = resolve_version(
            kept_versions(get_services().datasets, tool_context.session.id, view), args.from_version
        )
    except VersionRefused as exc:
        return _version_refusal(exc.code)
    # The view of the plot in force, as every reader of it sees it. A question reads the whole table unless its
    # operations start with `apply_view`, which asks it of the rows the plot draws; either way the answer says which.
    held = current(tool_context.state, stored, view.language, bindings=view.bindings, roles=view.snapshot.roles())
    asked = list(args.operations)
    of_view = bool(asked) and isinstance(asked[0], ApplyView)
    source = start.stored.as_parsed()
    seen: list[str] = []
    if of_view:
        if not start.current:
            lines = ["apply_view works on the current table, whose rows the view shows: leave from_version out"]
            return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines(lines)}
        if held.viewed is None:
            return {"status": "error", "code": "invalid_operations", "errors": _fenced_lines([NO_VIEW_TO_ASK])}
        source, seen, asked = held.viewed.parsed, list(held.viewed.changes), asked[1:]
    try:
        answer = run_query(source, asked, args.columns, args.limit, language=view.language)
    except PrepareError as exc:
        # The message names columns of the user's dataset at most, never a cell; fenced like every column name.
        return {"status": "error", "code": exc.code, "message": _fenced_lines([exc.message])}
    # Said only of the current table: an earlier version has no view to tell the answer's rows from.
    told = asked_of(held, stored, of_view=of_view) if held.viewed is not None and start.current else None
    return query_result(replace(answer, changes=rebuilt_changes(start, [*seen, *answer.changes])), told)


def asked_of(held: Current, stored: StoredDataset, *, of_view: bool) -> str:
    """Which rows a `query_data` answer read while a view of the plot is in force: the ones the plot draws, or
    every row of the table, with the counts and the view's words, and for the table the way to ask of the view. The
    root's reply says which, since a total over 248 rows is no total of the 12 the user is looking at."""
    assert held.viewed is not None
    text = [name for name, dtype in stored.column_dtypes.items() if dtype == "text"]
    drawn = f"{held.viewed.rows} of the table's {held.viewed.of_rows} rows (view: {held.view.words(text)})"
    if of_view:
        return f"this answer reads the rows the plot draws, {drawn}"
    return (
        f"this answer reads every row of the table; the plot draws {drawn}. To ask about the rows the plot draws, "
        "start the operations with apply_view"
    )


def query_result(answer: QueryResult, view: str | None = None) -> dict[str, Any]:
    """The `query_data` result: the table fenced as `<user_data>`, cut by rows from the end to fit the tool's cap.
    `view` is the line that says which rows the answer read while a view of the plot is in force (`asked_of`): it is
    part of the result before the cut, so the rows give way to it and the result never passes the cap for it."""
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
        if view is not None:
            result["view"] = DATA_PREAMBLE + "\n" + fence("tool_notes", view)
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
    changes = [*generated.changes, *generated.warnings]
    try:
        delta, number = _store_generated(
            tool_context.session.id, view, parsed, source=generated_source(spec), changes=changes
        )
    except StoreFull:
        return _error("capacity")
    # A new dataset id leaves the confirmation's fingerprint behind: the user confirms the generated data.
    for key, value in delta.items():
        tool_context.state[key] = value
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
    session_id: str,
    view: SessionView,
    parsed: ParsedDataset,
    *,
    code: str | None = None,
    source: str,
    changes: list[str],
) -> tuple[dict[str, Any], int]:
    """Store a generated table: the next version of the session's data, or the first of new data when it has none,
    under the session's next number either way; raises `StoreFull`.

    A session whose dataset left the store (a restart keeps neither) counts as one
    without data, so the stale ids are dropped with the history, as a paste drops them.
    `code` is the Python that computed the table (`run_data_code`), kept with the version;
    `source` says where it comes from (`dataset_context`), for the adapter and the reviewer;
    `changes` are its change lines, which the session block lists for a version after the first.
    """
    store = get_services().datasets
    current = store.get(view.dataset_id, session_id) if view.dataset_id else None
    if current is not None:
        version = push_version(
            store, session_id, view, parsed, view.snapshot, rebind=True, code=code, source=source, changes=changes
        )
        return version.delta, version.version
    ingested = store_dataset(
        store,
        session_id,
        parsed,
        view.snapshot,
        previous_id=view.dataset_id,
        history=view.earlier_datasets,
        code=code,
        source=source,
        number=view.next_version,
    )
    return ingested.state_delta(), ingested.number


DATA_CODE_CHANGE = "computed from your code"
"""The change line of a `run_data_code` version; the rows and columns follow it."""
EXAMPLE_DATA_CHANGE = "generated example data"
"""The change line of a `run_data_code` version the root wrote for a request for example data (`source_language`
`example`): the data panel says plainly that the table is made up, not the user's."""
SOURCE_LANGUAGES = frozenset({"python", "javascript", "r", "math", "other", "example"})
"""`run_data_code`'s `source_language`: what the user wrote before the root's translation, for attribution, or
`example` for example data the user asked for, which also sets the change line and the source line."""
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
    """Run Python that generates the data for the plot (a snippet the user pasted or typed, translated by you to Python if it was JavaScript, R, a formula or anything else, or code you write for example data the user asked for); the server validates it, runs it in a sandbox without network or files, and stores the table it computed in df as the next version of the data, which the user then checks and confirms.

    code: Python of at most 6,000 characters using only numpy, pandas, math, random, statistics or scipy.stats (and
    the other scipy computing modules); it must assign the final table to df at the top level as a pandas DataFrame
    (at most 20,000 rows, 50 columns and 2 MB as CSV: 10,000 rows of about 10 float columns at full precision fit;
    for a wider table round floats to the decimal places that still keep their values distinct, such as
    df.round(3) for values between -50 and 50, or keep every k-th row), read no file, call no network and
    draw nothing (no matplotlib, no plot(),
    no hist()). Never write data values from memory: more than 20 numbers or 20 text values written out in one list,
    tuple or dict (a list repeated with * counts every copy), or 40 in the code, are refused. source_language:
    what the user wrote, one of python, javascript, r, math or other, or example when the user asked for example data
    and wrote no code. Returns the change lines and the new profile, or an error with a code and a message.
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
    if not services.usage.data_runs_ok(user, settings, ledger.tier):
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
    example = language == "example"
    change = EXAMPLE_DATA_CHANGE if example else DATA_CODE_CHANGE
    changes = [f"{change}: {parsed.profile.rows} rows, {len(parsed.profile.columns)} columns"]
    # The queue, the run and the judge suspended this call: a data call of the same turn may have stored a version
    # meanwhile, so the table goes on top of the session as it is now, under the number after that one
    # (`SessionView.next_version`), never on the view read before the run, which would number it twice.
    current = _view(tool_context)
    if current is None:
        return _error("session_not_open")
    try:
        delta, number = _store_generated(
            tool_context.session.id,
            current,
            parsed,
            code=prepared,
            source=code_source(prepared, language),
            changes=changes,
        )
    except StoreFull:
        return _error("capacity")
    for key, value in delta.items():
        tool_context.state[key] = value
    ledger.example_data = ledger.example_data or example
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
        "at most 600 characters) and base='previous'. Leave theme out unless the user asks for a theme: the plot "
        "then follows the theme of the user's page, and a change keeps a theme the user asked for; pass "
        "theme='dark' only when the user asks for a dark plot, and theme='light' only when they ask for a light "
        "one. Pass expected_texts (at most five) with the texts and number formats the user wrote out for "
        "the plot, verbatim. Pass remember (at most five) with the change's lasting decisions for the user's plot "
        "memory, each {kind, text, target, expected_text}, stored once the plot ships. Returns the PlotResult, with "
        "what the shipped plot shows under shows."
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
    forget,
    switch_plot,
    prepare_data,
    query_data,
    generate_data,
    run_data_code,
)
ROOT_TOOL_NAMES = frozenset({*(tool.__name__ for tool in SESSION_TOOLS), PLOT_PIPELINE})
