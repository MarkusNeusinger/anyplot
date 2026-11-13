"""Server-set session state: the catalogue snapshot, the dataset reference, the bindings and the language.

Only the service writes these keys: the `/v1` routes through
`session_service.append_event` with a `state_delta`, the `set_bindings` tool
after `apply_bindings` accepted the bindings, the `prepare_data` tool after
`apply_operations` produced the next dataset version (`dataset_versions.py`), the
root's before-agent callback after it made a paste's `certain` conversions
(`paste_conversions.py`), the scope guard, which records the languages it offered (`LANGUAGE_OFFERED`), and
the `set_language` tool (`LANGUAGE`, `LANGUAGE_SOURCE`, `PLOT_LANGUAGE`). No model output and no client body
ever becomes a state value unchecked, and `plot_pipeline` reads spec, library,
dataset, bindings and language from here, never from its arguments.

`CatalogueSnapshot` mirrors the body the BFF sends (`api/routers/agent.py`): what the
agents service knows about the catalogue pair, since it has no database access.
"""

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.spec_roles import DataRole, mark_computed, parse_roles

from .data.bindings import BindingCheck, check_bindings, resolve_role
from .data.computed import mark_name_only
from .data.fidelity import mark_keys
from .data.signs import mark_non_negative
from .language import DEFAULT_LANGUAGE, MAX_OFFERED, LanguageSource, is_valid, read_source
from .schemas import MAX_CODE_CHARS, Binding, DatasetProfile, LastRun


PREFIX = "anyplot."
SPEC_ID = PREFIX + "spec_id"
LIBRARY = PREFIX + "library"
LOCALE = PREFIX + "locale"
"""The browser's locale the session opened with: metadata for the feedback case, never the session language."""
LANGUAGE = PREFIX + "language"
"""The session language: the language of the replies, and of the first plot's text (`plot_language`). A short
language name or code that matches `language.LANGUAGE_PATTERN` (`de`, `English`, `Swedish`). Absent means `en`."""
LANGUAGE_SOURCE = PREFIX + "language_source"
"""How it was set: `default` (nobody yet, English), `chosen` (the chip through the language route, or the root's
`set_language`), `offer` (the user accepted an offer, the language route with `via: offer`). Absent means `default`,
and so do `pasted` and `detected`, which detection wrote before 2026-11-08 (`language.read_source`). Only `chosen` is
final: no offer comes after it (`language.offer`)."""
LANGUAGE_OFFERED = PREFIX + "language_offered"
"""The languages the page was offered, as stored forms, oldest first, at most `language.MAX_OFFERED`: each comes
once (`language.offer`). The scope guard appends a typed message's offer, the dataset route a paste's; a fan-out
copy takes the page session's. Absent means none."""
PLOT_LANGUAGE = PREFIX + "plot_language"
"""The language the user asked for the plot's text: the language route (the chip, which sets the session language
too) or the root's `set_language`, or the page session's plot language for a fan-out copy. Absent until then: the
plot then keeps the language its latest version is written in (`plot_language`). Owner decision of 2026-11-01."""
SNAPSHOT = PREFIX + "snapshot"
NORMALISED = PREFIX + "normalised"
HINTS = PREFIX + "hints"
READINESS = PREFIX + "readiness"
TELEMETRY_SOURCE = PREFIX + "telemetry_source"
"""`fanout` for a session the admin's "plot in all libraries" fan-out opened (`POST /v1/sessions` with
`source: fanout`), absent otherwise: every usage-telemetry line of the session carries that source (`telemetry.emit`).
Written once at the opening; a library switch keeps it."""
DATASET_ID = PREFIX + "dataset_id"
DATASET_HISTORY = PREFIX + "dataset_history"
"""The ids of the dataset versions before the current one, oldest first, at most
`dataset_versions.MAX_DATASET_HISTORY`: what `POST .../dataset/undo` restores, newest first.
A new paste empties it. There is a version to undo while it holds one (`SessionView.can_undo`)."""
DATASET_VERSION = PREFIX + "dataset_version"
"""The session's number of the current dataset version (`StoredDataset.number`). The session numbers every version it
stores once, the next number each time, never reused: a paste, an opened file, a copy or a computed table as much as a
change (`prepare_data`, `.to_long()`, a rebuild), and an undo makes the version it restores current again with its own
number (owner decision of 2026-11-07: "v2" names the same table to the user, whose card shows this number, and to the
root, whose session block lists it). Whether there is a version to undo is the history's, never this number's."""
DATASET_ORIGINAL = PREFIX + "dataset_original"
"""The id of the first version of the session's current data: the paste, the opened file, the copy or the table
computed in a session without data. The store keeps it also after the history cap pushed it out of `DATASET_HISTORY`,
so `prepare_data` and `query_data` can always start from it (`from_version` `original`); undo never reaches it there.
A new paste replaces it and deletes the old one (owner decision of 2026-11-06)."""
DATASET_TOP = PREFIX + "dataset_top"
"""The highest number the session gave a dataset version: the next version gets one more, a paste included. An undo
lowers `DATASET_VERSION` but never this; absent before the session's first data. The current data holds the numbers
from its original's up to this one, so a number below the original's is a version of earlier data, which a paste
replaced (`other_paste`), and one from it up that the session no longer keeps was undone or left the history
(`version_not_kept`)."""
DATASET_COPIED_FROM = PREFIX + "dataset_copied_from"
"""The number of the data version this session's data was copied from (`POST .../dataset/copy`, the admin fan-out's
copy of the page session's confirmed version), absent for data of the session's own. The copy is the session's first
version, with no history; this records where it came from, for the feedback bundle. A paste replaces it."""
SUMMARY_PENDING = PREFIX + "summary_pending"
"""The id of a pasted dataset the root has not summarized yet: the dataset route writes it with the paste (also a
transcription's `.use()`), and the messages route clears it once a root turn on that dataset ended without a
failure or a refusal; the confirm route clears it too, since the user who confirmed the data has seen it and the
next text is the plot's request, never a note. While it names the current dataset, a typed message is the note the
user sent with the paste: the route gives it the pasted notes and the file's name, and the session block says the
data was pasted just now. Data the root made, a copy of another session's data and a session from before the key
read as summarized. The version of the conversions the server makes on the summary turn (`CONVERSIONS_MADE`) takes
the paste's place here: it is still the paste the root has not summarized."""
CONVERSIONS_MADE = PREFIX + "conversions_made"
"""The `certain` conversions for open roles the server made on the summary turn of a paste (`paste_conversions.py`),
as `ConversionsMade`: the version they made, their session-block lines and their operations. The session block lists
the lines while that version is the summary turn's; a later version, a new paste or an undo leaves the record stale,
and nothing reads it then."""
BINDINGS = PREFIX + "bindings"
CONFIRMED = PREFIX + "confirmed"
"""The fingerprint of what the user confirmed (the confirm route `.create_plot()` calls first): the dataset
id and the bindings as they were (`confirmation_fingerprint`). The plot pipeline runs only
while the fingerprint of the current state equals it, so a new dataset (a paste, a
transcription's `.use()`) or any binding change, also one that lands between the
confirmation's read and its write, leaves the data unconfirmed without an explicit reset."""
PENDING_REQUEST = PREFIX + "pending_request"
"""The `change_request` of a first plot that stopped `not_ready` (`data_unconfirmed` or `incomplete_bindings`) or
got no queue slot: the user's note for the plot (a title, a label), joined to the next first-plot run's own request
(`pipeline.run_pipeline`), so a binding change the root made that asked for a confirmation again never loses it (live
test of 2026-10-15). It stays until a run ships a plot. A note written for other data or other bindings never applies
(owner decision of 2026-10-15): a new data version (a paste, `prepare_data`, `generate_data`, `run_data_code`,
`.to_long()`, undo) drops it at once, and the run that would take it drops it when a binding it was kept for no longer
stands (`pipeline.pending_fate`, `PENDING_BINDINGS`). The bindings are judged at the run, not at each write, so a
column the user unbinds and binds again on the way keeps the note, and the root's own `set_bindings` or
`prepare_data` in the turn that kept it never voids it (main's `_settle_kept_note`). A library switch keeps it, since
the data and bindings stay (owner decision of 2026-11-02). The pipeline reads it defensively: a value that is no text
is ignored, and text is cut to `MAX_CHANGE_REQUEST_CHARS` (`pipeline.merged_request`)."""
PENDING_EXPECTED_TEXTS = PREFIX + "pending_expected_texts"
"""The `expected_texts` that came with `PENDING_REQUEST` (the title or number format the user asked to see), kept
and dropped with it, so a bare `.create_plot()` checks the render for the same texts; a run that brings a request or
texts of its own checks only its own (`pipeline.chosen_texts`). Read through the `PipelineArgs` validator
(`pipeline.kept_texts`)."""
PENDING_BINDINGS = PREFIX + "pending_bindings"
"""The bindings the note was written for (`pipeline.hold_request`; the turn that kept it ends with them,
`_settle_kept_note` in `agents/main.py`): the run takes the note only while the bindings in force keep every one of
them, roles open then being free to fill (the step `incomplete_bindings` waits for); otherwise the user rebound a
column the note was written for, and the run drops it (`pipeline.pending_fate`)."""
PENDING_REMEMBER = PREFIX + "pending_remember"
"""The plot memory decisions that came with `PENDING_REQUEST` (`KeepRequestArgs.remember`), kept and dropped with it;
the first-plot run that takes the note stores them in the memory once it ships (`pipeline.take_pending_request`)."""
PENDING_BASE = PREFIX + "pending_base"
"""`previous` while the kept request is a change of the library's plot of the current data, not a first plot's note:
the library has that plot, and the request waited because the data or the bindings waited for the user's check
(`pipeline.hold_request`; persona round of 2026-11-11: "drop these rows and use a log scale" changed the data, and
the log scale reached no plot, because a change of an existing plot was never kept). The page's "plot the new data"
then draws it on the latest version together with the new data (`pipeline.take_pending_request`), where a first
plot's note makes that run a fresh start (`pipeline.new_data_base`). Unset for a first plot's note; kept and dropped
with `PENDING_REQUEST`."""
PENDING_CLEARED: dict[str, Any] = {
    PENDING_REQUEST: None,
    PENDING_EXPECTED_TEXTS: None,
    PENDING_BINDINGS: None,
    PENDING_REMEMBER: None,
    PENDING_BASE: None,
}
"""The state delta that drops a kept note, a first plot's or a change of the plot, and its texts: every new data
version carries it, except in the turn that kept it, which puts it back (`_settle_kept_note`) (a binding
write no longer does: the run judges the bindings, `pipeline.pending_fate`; a library switch no longer does either,
2026-11-02)."""
LAST_RUN = PREFIX + "last_run"
"""How the latest plot run ended (`schemas.LastRun`, content-free), written by every run that yields a result
(`pipeline.record_last_run`): the feedback bundle's `session.last_run`."""

MAX_SNAPSHOT_CHARS = 64 * 1024


class CatalogueSnapshot(BaseModel):
    """One spec and library of the catalogue, as the BFF loaded it (at most 64 KB)."""

    model_config = ConfigDict(extra="forbid")

    spec_id: str = Field(pattern=r"^[a-z0-9-]{1,100}$")
    title: str = Field(max_length=300)
    description: str = Field(default="", max_length=16_000)
    data_roles: list[str] = Field(default_factory=list, max_length=200)
    notes: list[str] = Field(default_factory=list, max_length=200)
    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)
    library_version: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def _bounded(self) -> Self:
        if len(self.model_dump_json()) > MAX_SNAPSHOT_CHARS:
            raise ValueError("the catalogue snapshot is larger than 64 KB")
        return self

    def roles(self) -> list[DataRole]:
        """The spec's data roles, with the ones that cannot be negative (`data/signs.py`), the ones the plot can
        compute (`spec_roles.COMPUTED_ROLES`), the ones bound only by name (`data/computed.py`) and the ones that
        key the marks (`data/fidelity.py`) marked."""
        roles = mark_computed(mark_non_negative(parse_roles(self.data_roles), self.spec_id), self.spec_id)
        return mark_keys(mark_name_only(roles, self.spec_id), self.spec_id)


@dataclass
class SessionView:
    """The server-set state of one session, read once per tool call or pipeline run."""

    spec_id: str
    library: str
    locale: str
    snapshot: CatalogueSnapshot
    normalised: str
    hints: list[str]
    dataset_id: str | None
    bindings: list[Binding] = field(default_factory=list)
    last_run: LastRun | None = None
    """How the latest plot run ended (`LAST_RUN`); None before the first run, or for a record that no longer reads."""
    confirmed: str | None = None
    """The confirmation fingerprint the state holds, if any (`CONFIRMED`)."""
    dataset_history: list[str] = field(default_factory=list)
    """The ids of the dataset versions before the current one, oldest first (`DATASET_HISTORY`)."""
    dataset_version: int = 1
    """The session's number of the current dataset version (`DATASET_VERSION`); 1 without a dataset."""
    dataset_original: str | None = None
    """The id of the first version of the current data (`DATASET_ORIGINAL`); None without data, or for a view built
    without the key, where `dataset_versions` takes the current version while nothing stands before it."""
    dataset_top: int = 0
    """The highest number the session gave a dataset version (`DATASET_TOP`); 0 before its first data."""
    language: str = DEFAULT_LANGUAGE
    """The session language (`LANGUAGE`), validated: a value outside the pattern reads as `en`."""
    language_source: LanguageSource = "default"
    """How the session language was set (`LANGUAGE_SOURCE`): `default`, `chosen` or `offer`."""
    language_offered: list[str] = field(default_factory=list)
    """The languages the page was offered (`LANGUAGE_OFFERED`), validated, oldest first."""
    plot_language_choice: str | None = None
    """The language the user asked for the plot's text (`PLOT_LANGUAGE`), validated; None when none was asked for
    (or the stored value is outside the pattern). `plot_language` resolves the language a run writes in."""
    readiness: str | None = None
    """The readiness status of the catalogue file the session's library opened with (`READINESS`), for the usage
    telemetry; None when the state holds none."""
    summary_pending: bool = False
    """Whether the current dataset is a paste the root has not summarized yet (`SUMMARY_PENDING`)."""

    @property
    def data_confirmed(self) -> bool:
        """Whether the user confirmed the current dataset with its current bindings (step 1 of two)."""
        return bool(self.dataset_id) and self.confirmed == confirmation_fingerprint(self.dataset_id, self.bindings)

    @property
    def can_undo(self) -> bool:
        """Whether `POST .../dataset/undo` has a version to restore: the history holds one (`DATASET_HISTORY`). The
        current number says nothing about it: a paste can carry any number, and past the history cap a version above
        the original's has nothing left to undo."""
        return bool(self.dataset_history)

    @property
    def next_version(self) -> int:
        """The number the session's next stored dataset version gets: one above every number it gave (`DATASET_TOP`),
        and so above the current one.

        It comes from the view, so it holds only while nothing stores a version between the view's read and the
        delta's write, as the history the delta writes does. Every writer keeps that: the data routes (undo,
        `.to_long()`, copy) read and write with no suspension between them (`InMemorySessionService.get_session` and
        `append_event` never yield), and a paste or a turn, which do suspend, exclude every other writer of the
        session while they run (`main._active`)."""
        return max(self.dataset_top, self.dataset_version if self.dataset_id else 0) + 1

    @property
    def earlier_datasets(self) -> list[str]:
        """The ids the session keeps besides the current version: the original kept past the history, then the
        history; what a new paste deletes (`opening.store_dataset`)."""
        original = self.dataset_original
        if original and original != self.dataset_id and original not in self.dataset_history:
            return [original, *self.dataset_history]
        return list(self.dataset_history)

    @property
    def target(self) -> tuple[str, str]:
        """The (spec, library) pair the session adapts now: what a switch changes, and what a version is filed under
        (`CodeVersion.target`)."""
        return (self.spec_id, self.library)


def confirmation_fingerprint(dataset_id: str | None, bindings: list[Binding]) -> str:
    """What a confirmation covers: the dataset id and the bindings, as one short digest.

    The bindings are a set of role-to-column assignments (`check_bindings` reads them
    unordered), so they are sorted before hashing: the same assignments in another order
    are the same confirmation.
    """
    assignments = sorted((binding.role, binding.column) for binding in bindings)
    payload = json.dumps({"dataset": dataset_id, "bindings": assignments})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def confirm_delta(view: SessionView) -> dict[str, Any]:
    """The state delta of the confirm route: the current dataset with its current bindings counts as confirmed, and
    as summarized (`SUMMARY_PENDING`): a `.create_plot()` after a note turn that failed plots, it summarizes nothing."""
    return {CONFIRMED: confirmation_fingerprint(view.dataset_id, view.bindings), SUMMARY_PENDING: None}


def narrows(confirmed: list[Binding], bindings: list[Binding], roles: list[DataRole]) -> bool:
    """Whether `bindings` only leave out series of `confirmed`: members of a number family such as `y2`.

    Owner decision of 2026-10-15 ("e.g. drops the 2nd line"): every kept binding is one the
    user confirmed, role and column as they were, and every one left out is a member of a
    variadic family of numbers. Leaving out a grouping, text or boolean role (`series`, which
    merged two countries into one line in the review) or any single role, or renumbering a
    member so that `y1` plots another column, is a change the user has not seen. Something
    must be left out: the same bindings narrow nothing.
    """
    kept = {(binding.role, binding.column) for binding in bindings}
    before = {(binding.role, binding.column) for binding in confirmed}
    if len(kept) != len(bindings) or not kept < before:
        return False
    for name, _ in before - kept:
        role = resolve_role(name, roles)
        if role is None or not role.variadic or set(role.kinds) != {"numeric"}:
            return False
    return True


def narrowed_confirmation(
    view: SessionView, bindings: list[Binding], check: BindingCheck, roles: list[DataRole]
) -> dict[str, Any]:
    """The state delta that moves the user's confirmation to `bindings`, or {} when it does not move.

    It moves only while the data is confirmed, the new bindings are complete, and they narrow
    the confirmed ones (`narrows`): the user saw every assignment they keep, so a step-2 note
    such as "only co2_per_capita" plots in the same turn instead of stopping on
    `data_unconfirmed` (live test of 2026-10-15). `AGENT_NARROWED_BINDINGS=reset` turns it off.
    """
    if not (view.data_confirmed and check.complete and narrows(view.bindings, bindings, roles)):
        return {}
    return {CONFIRMED: confirmation_fingerprint(view.dataset_id, bindings)}


def language_delta(language: str, source: LanguageSource) -> dict[str, Any]:
    """The state delta that sets the session language (the language route, `set_language`, a fan-out copy)."""
    return {LANGUAGE: language, LANGUAGE_SOURCE: source}


def offered_delta(offered: list[str], language: str) -> dict[str, Any]:
    """The state delta that records `language` as offered, after the ones `offered` holds."""
    return {LANGUAGE_OFFERED: [*offered, language][-MAX_OFFERED:]}


def plot_language(view: SessionView, latest: str | None) -> str:
    """The language the next plot version writes its text in (owner decision of 2026-11-01).

    The user's request for the plot's text (`PLOT_LANGUAGE`) comes first. Without one, the
    plot keeps `latest`, the language the session's latest rendered version is written in
    (`CodeVersion.language`, in any library), so a follow-up message in another language
    never rewrites the text of a plot the user already has: the live test of 2026-11-01
    had "Use a log scale on y" turn a German plot's title and numbers English, while its
    axes and months stayed German. Before the first plot, the session language decides: English
    until the user picks another (the chip, a request in the chat, an accepted offer).
    """
    if view.plot_language_choice is not None:
        return view.plot_language_choice
    if latest is not None and is_valid(latest):
        return latest
    return view.language


def initial_state(
    *, spec_id: str, library: str, locale: str, snapshot: CatalogueSnapshot, normalised: str, readiness: dict[str, Any]
) -> dict[str, Any]:
    """The state delta that opens a session (or switches its library).

    The session language is not part of it: ADK applies a delta key by key, so a library
    switch keeps `LANGUAGE`, `LANGUAGE_SOURCE`, `LANGUAGE_OFFERED` and `PLOT_LANGUAGE`, and a new session
    reads them as `en`, `default`, none offered and no choice for the plot (`read_session`). Nor is a kept
    first-plot note (`PENDING_REQUEST`, its texts and bindings): a switch keeps the data and
    the bindings it was written for, so the note waits for the first plot in the new library
    (owner decision of 2026-11-02). The plot memory (`memory.MEMORY`) stays the same way.
    """
    return {
        SPEC_ID: spec_id,
        LIBRARY: library,
        LOCALE: locale,
        SNAPSHOT: snapshot.model_dump(),
        NORMALISED: normalised,
        HINTS: list(readiness.get("hints", [])),
        READINESS: readiness,
    }


def _last_run(raw: Any) -> LastRun | None:
    """The stored `LAST_RUN` record, or None; one that no longer validates (a schema change) reads as none."""
    if not isinstance(raw, dict):
        return None
    try:
        return LastRun.model_validate(raw)
    except ValueError:
        return None


class ConversionsMade(BaseModel):
    """What the server's conversions on a paste made (`CONVERSIONS_MADE`), validated on every read."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1, max_length=64)
    """The data version the conversions made."""
    lines: list[str] = Field(min_length=1, max_length=8)
    """One line per conversion, for the session block (`conversions.Candidate.made`); they name the user's columns."""
    operations: list[dict[str, Any]] = Field(min_length=1, max_length=16)
    """The operations applied, in order, as the conversion lines listed them."""


USER_BOUND = PREFIX + "user_bound"
"""The bindings the user set by hand in the data panel since the root's last turn that ended well, as `{role, column}`
pairs (`PUT /bindings` adds a pair whenever it changes one; the turn's end drops them, `agents/main.py`). The session
block lists the ones still in force (`user_bound`), so the root reads a binding that differs from what it said as the
user's choice: in the persona round of 2026-11-11 it wrote "I was wrong earlier" after the user had rebound a role
by a click."""


def user_bound(state: Any, bindings: Sequence[Binding]) -> list[Binding]:
    """The bindings in force that the user set by hand since the root's last turn (`USER_BOUND`), in the order of
    `bindings`. A pair the root or a new paste has since replaced is no longer the user's, and a stored value that
    is no list of pairs counts as none."""
    raw = state.get(USER_BOUND)
    if not isinstance(raw, list):
        return []
    noted = {(item.get("role"), item.get("column")) for item in raw if isinstance(item, dict)}
    return [binding for binding in bindings if (binding.role, binding.column) in noted]


def read_conversions_made(state: Any) -> ConversionsMade | None:
    """The record of the server's conversions on a paste, or None when there is none or it does not validate."""
    raw = state.get(CONVERSIONS_MADE)
    if not isinstance(raw, dict):
        return None
    try:
        return ConversionsMade.model_validate(raw)
    except ValueError:
        return None


def read_session(state: Any) -> SessionView | None:
    """The session view from an ADK state mapping, or None when the session was never opened."""
    snapshot = state.get(SNAPSHOT)
    spec_id = state.get(SPEC_ID)
    library = state.get(LIBRARY)
    if not snapshot or not spec_id or not library:
        return None
    raw_bindings = state.get(BINDINGS) or []
    # Validated on every read, so a corrupt value can never reach a prompt.
    raw_language = state.get(LANGUAGE)
    language = raw_language if isinstance(raw_language, str) and is_valid(raw_language) else DEFAULT_LANGUAGE
    # A source is the stored language's: a value the pattern refused reads as the default, from nobody.
    language_source = read_source(state.get(LANGUAGE_SOURCE) if language == raw_language else None)
    raw_offered = state.get(LANGUAGE_OFFERED)
    language_offered = (
        [item for item in raw_offered if isinstance(item, str) and is_valid(item)][-MAX_OFFERED:]
        if isinstance(raw_offered, list)
        else []
    )
    raw_plot_language = state.get(PLOT_LANGUAGE)
    plot_language_choice = (
        raw_plot_language if isinstance(raw_plot_language, str) and is_valid(raw_plot_language) else None
    )
    raw_readiness = state.get(READINESS)
    status = raw_readiness.get("status") if isinstance(raw_readiness, dict) else None
    dataset_version = max(1, int(state.get(DATASET_VERSION) or 1))
    raw_original = state.get(DATASET_ORIGINAL)
    return SessionView(
        spec_id=str(spec_id),
        library=str(library),
        locale=str(state.get(LOCALE) or "en"),
        snapshot=CatalogueSnapshot.model_validate(snapshot),
        normalised=str(state.get(NORMALISED) or ""),
        hints=[str(hint) for hint in state.get(HINTS) or []],
        dataset_id=state.get(DATASET_ID),
        bindings=[Binding.model_validate(item) for item in raw_bindings],
        last_run=_last_run(state.get(LAST_RUN)),
        confirmed=state.get(CONFIRMED),
        dataset_history=[str(item) for item in state.get(DATASET_HISTORY) or []],
        dataset_version=dataset_version,
        dataset_original=raw_original if isinstance(raw_original, str) and raw_original else None,
        dataset_top=max(int(state.get(DATASET_TOP) or 0), dataset_version if state.get(DATASET_ID) else 0),
        language=language,
        language_source=language_source,
        language_offered=language_offered,
        plot_language_choice=plot_language_choice,
        readiness=status if isinstance(status, str) else None,
        summary_pending=bool(state.get(DATASET_ID)) and state.get(SUMMARY_PENDING) == state.get(DATASET_ID),
    )


def apply_bindings(
    bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile
) -> tuple[BindingCheck, dict[str, Any]]:
    """`bindings.apply`: validate bindings against the spec roles and the profile.

    Returns the check and, when it has no errors, the state delta that stores the
    bindings (incomplete bindings are stored too; the pipeline answers `not_ready`).
    An empty delta means nothing may be written.

    A kept plot note (`PENDING_REQUEST`) is left to the run that would take it, which judges the
    bindings in force then against the ones it was kept for (`pipeline.pending_fate`): a write
    on the way, such as a column unbound and bound again, decides nothing.
    """
    check = check_bindings(bindings, roles, profile)
    if check.errors:
        return check, {}
    return check, {BINDINGS: [binding.model_dump() for binding in bindings]}


def fills_open_roles(held: object, bindings: list[Binding]) -> bool:
    """Whether `bindings` keep every binding of `held` (stored bindings) and only add roles `held` left open."""
    if not isinstance(held, list):
        return False
    try:
        before = {(binding.role, binding.column) for binding in (Binding.model_validate(item) for item in held)}
    except ValueError:
        return False
    after = {(binding.role, binding.column) for binding in bindings}
    return before <= after
