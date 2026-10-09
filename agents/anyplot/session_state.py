"""Server-set session state: the catalogue snapshot, the dataset reference and the bindings.

Only the service writes these keys: the `/v1` routes through
`session_service.append_event` with a `state_delta`, and the `set_bindings` tool
after `apply_bindings` accepted the bindings. No model output and no client body
ever becomes a state value unchecked, and `plot_pipeline` reads spec, library,
dataset and bindings from here, never from its arguments.

`CatalogueSnapshot` mirrors the body the BFF sends (`api/routers/agent.py`): what the
agents service knows about the catalogue pair, since it has no database access.
"""

from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .data.bindings import BindingCheck, check_bindings
from .data.roles import DataRole, parse_roles
from .schemas import MAX_CODE_CHARS, Binding, DatasetProfile


PREFIX = "anyplot."
SPEC_ID = PREFIX + "spec_id"
LIBRARY = PREFIX + "library"
LOCALE = PREFIX + "locale"
SNAPSHOT = PREFIX + "snapshot"
NORMALISED = PREFIX + "normalised"
HINTS = PREFIX + "hints"
READINESS = PREFIX + "readiness"
DATASET_ID = PREFIX + "dataset_id"
BINDINGS = PREFIX + "bindings"
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
        return parse_roles(self.data_roles)


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

    @property
    def lang(self) -> str:
        return self.locale.lower()[:2] if self.locale else "en"


def initial_state(
    *, spec_id: str, library: str, locale: str, snapshot: CatalogueSnapshot, normalised: str, readiness: dict[str, Any]
) -> dict[str, Any]:
    """The state delta that opens a session (or switches its library)."""
    return {
        SPEC_ID: spec_id,
        LIBRARY: library,
        LOCALE: locale,
        SNAPSHOT: snapshot.model_dump(),
        NORMALISED: normalised,
        HINTS: list(readiness.get("hints", [])),
        READINESS: readiness,
    }


def read_session(state: Any) -> SessionView | None:
    """The session view from an ADK state mapping, or None when the session was never opened."""
    snapshot = state.get(SNAPSHOT)
    spec_id = state.get(SPEC_ID)
    library = state.get(LIBRARY)
    if not snapshot or not spec_id or not library:
        return None
    raw_bindings = state.get(BINDINGS) or []
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
    return check, {BINDINGS: [binding.model_dump() for binding in bindings]}
