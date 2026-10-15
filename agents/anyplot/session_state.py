"""Server-set session state: the catalogue snapshot, the dataset reference, the bindings and the language.

Only the service writes these keys: the `/v1` routes through
`session_service.append_event` with a `state_delta`, the `set_bindings` tool
after `apply_bindings` accepted the bindings, the `prepare_data` tool after
`apply_operations` produced the next dataset version (`dataset_versions.py`), the
scope guard, which records the detected session language once (`LANGUAGE`,
`LANGUAGE_SOURCE`), and the `set_language` tool. No model output and no client body
ever becomes a state value unchecked, and `plot_pipeline` reads spec, library,
dataset, bindings and language from here, never from its arguments.

`CatalogueSnapshot` mirrors the body the BFF sends (`api/routers/agent.py`): what the
agents service knows about the catalogue pair, since it has no database access.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .data.bindings import BindingCheck, check_bindings, resolve_role
from .data.roles import DataRole, parse_roles
from .data.signs import mark_non_negative
from .language import DEFAULT_LANGUAGE, SOURCES, LanguageSource, is_valid
from .schemas import MAX_CODE_CHARS, Binding, DatasetProfile


PREFIX = "anyplot."
SPEC_ID = PREFIX + "spec_id"
LIBRARY = PREFIX + "library"
LOCALE = PREFIX + "locale"
"""The browser's locale the session opened with: metadata for the feedback case, never the session language."""
LANGUAGE = PREFIX + "language"
"""The session language: the replies and every text in the plot. A short language name or
code that matches `language.LANGUAGE_PATTERN` (`de`, `English`, `Swedish`). Absent means `en`."""
LANGUAGE_SOURCE = PREFIX + "language_source"
"""How it was set: `default` (nobody yet), `pasted` (the judges' code for the notes or the column
names of a paste before any typed message, `language.pasted_language`), `detected` (the scope
judge's code for the session's first in-scope typed message), `chosen` (the language route or the
root's `set_language`). Absent means `default`. Only `chosen` is final: detection writes only over
`default` and `pasted`, a paste only over `default` and `pasted`."""
SNAPSHOT = PREFIX + "snapshot"
NORMALISED = PREFIX + "normalised"
HINTS = PREFIX + "hints"
READINESS = PREFIX + "readiness"
DATASET_ID = PREFIX + "dataset_id"
DATASET_HISTORY = PREFIX + "dataset_history"
"""The ids of the dataset versions before the current one, oldest first, at most
`dataset_versions.MAX_DATASET_HISTORY`: what `POST .../dataset/undo` restores, newest first.
A new paste empties it."""
DATASET_VERSION = PREFIX + "dataset_version"
"""The number of the current dataset version: 1 for a paste, one more for every
`prepare_data`, one less for every undo. Above 1 there is a version to undo."""
BINDINGS = PREFIX + "bindings"
CONFIRMED = PREFIX + "confirmed"
"""The fingerprint of what the user confirmed (`.confirm()` in the data panel): the dataset
id and the bindings as they were (`confirmation_fingerprint`). The plot pipeline runs only
while the fingerprint of the current state equals it, so a new dataset (a paste, a
transcription's `.use()`) or any binding change, also one that lands between the
confirmation's read and its write, leaves the data unconfirmed without an explicit reset."""
PENDING_REQUEST = PREFIX + "pending_request"
"""The `change_request` of a first plot that stopped `not_ready` (`data_unconfirmed` or `incomplete_bindings`) or
got no queue slot: the user's note for the plot (a title, a label), joined to the next first-plot run's own request
(`pipeline.run_pipeline`), so a binding change the root made that asked for `.confirm()` again never loses it (live
test of 2026-10-15). It stays until a run ships a plot. Any later binding write, new data version (a paste,
`prepare_data`, `generate_data`, `run_data_code`, `.to_long()`, undo) or library switch drops it: it was written
for the data and bindings before (owner decision of 2026-10-15). The pipeline reads it defensively: a value that is
no text is ignored, and text is cut to `MAX_CHANGE_REQUEST_CHARS` (`pipeline.merged_request`)."""
PENDING_EXPECTED_TEXTS = PREFIX + "pending_expected_texts"
"""The `expected_texts` that came with `PENDING_REQUEST` (the title or number format the user asked to see), kept
and dropped with it, so the next `.create_plot()` checks the render for the same texts (`pipeline.merged_texts`)."""
PENDING_CLEARED: dict[str, Any] = {PENDING_REQUEST: None, PENDING_EXPECTED_TEXTS: None}
"""The state delta that drops a kept first-plot note and its texts: every binding write, new data version and
library switch carries it."""
LAST_STATUS = PREFIX + "last_status"
VERSIONS = PREFIX + "versions"

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
        """The spec's data roles, the ones that cannot be negative marked (`data/signs.py`)."""
        return mark_non_negative(parse_roles(self.data_roles), self.spec_id)


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
    versions: int = 0
    last_status: str | None = None
    confirmed: str | None = None
    """The confirmation fingerprint the state holds, if any (`CONFIRMED`)."""
    dataset_history: list[str] = field(default_factory=list)
    """The ids of the dataset versions before the current one, oldest first (`DATASET_HISTORY`)."""
    dataset_version: int = 1
    """The current dataset version's number (`DATASET_VERSION`); 1 without a dataset or for a paste."""
    language: str = DEFAULT_LANGUAGE
    """The session language (`LANGUAGE`), validated: a value outside the pattern reads as `en`."""
    language_source: LanguageSource = "default"
    """How the session language was set (`LANGUAGE_SOURCE`): `default`, `pasted`, `detected` or `chosen`."""

    @property
    def data_confirmed(self) -> bool:
        """Whether the user confirmed the current dataset with its current bindings (step 1 of two)."""
        return bool(self.dataset_id) and self.confirmed == confirmation_fingerprint(self.dataset_id, self.bindings)


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
    """The state delta of `.confirm()`: the current dataset with its current bindings counts as confirmed."""
    return {CONFIRMED: confirmation_fingerprint(view.dataset_id, view.bindings)}


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
    """The state delta that sets the session language (the language route, `set_language`, detection)."""
    return {LANGUAGE: language, LANGUAGE_SOURCE: source}


def initial_state(
    *, spec_id: str, library: str, locale: str, snapshot: CatalogueSnapshot, normalised: str, readiness: dict[str, Any]
) -> dict[str, Any]:
    """The state delta that opens a session (or switches its library).

    The session language is not part of it: ADK applies a delta key by key, so a library
    switch keeps `LANGUAGE` and `LANGUAGE_SOURCE`, and a new session reads them as `en`
    and `default` (`read_session`).
    """
    return {
        SPEC_ID: spec_id,
        LIBRARY: library,
        LOCALE: locale,
        SNAPSHOT: snapshot.model_dump(),
        NORMALISED: normalised,
        HINTS: list(readiness.get("hints", [])),
        READINESS: readiness,
        **PENDING_CLEARED,  # a note kept for another library's first plot does not carry over
    }


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
    raw_source = state.get(LANGUAGE_SOURCE)
    language_source: LanguageSource = "default"
    if raw_source in SOURCES and language == raw_language:
        language_source = raw_source
    return SessionView(
        spec_id=str(spec_id),
        library=str(library),
        locale=str(state.get(LOCALE) or "en"),
        snapshot=CatalogueSnapshot.model_validate(snapshot),
        normalised=str(state.get(NORMALISED) or ""),
        hints=[str(hint) for hint in state.get(HINTS) or []],
        dataset_id=state.get(DATASET_ID),
        bindings=[Binding.model_validate(item) for item in raw_bindings],
        versions=int(state.get(VERSIONS) or 0),
        last_status=state.get(LAST_STATUS),
        confirmed=state.get(CONFIRMED),
        dataset_history=[str(item) for item in state.get(DATASET_HISTORY) or []],
        dataset_version=max(1, int(state.get(DATASET_VERSION) or 1)),
        language=language,
        language_source=language_source,
    )


def apply_bindings(
    bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile
) -> tuple[BindingCheck, dict[str, Any]]:
    """`bindings.apply`: validate bindings against the spec roles and the profile.

    Returns the check and, when it has no errors, the state delta that stores the
    bindings (incomplete bindings are stored too; the pipeline answers `not_ready`).
    An empty delta means nothing may be written.
    """
    check = check_bindings(bindings, roles, profile)
    if check.errors:
        return check, {}
    # A kept plot note (`PENDING_REQUEST`) was written for the bindings before; any binding write drops it.
    return check, {BINDINGS: [binding.model_dump() for binding in bindings], **PENDING_CLEARED}
