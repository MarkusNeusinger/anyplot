"""Opening a session and taking in a dataset: the deterministic steps behind `/v1/sessions` and `/dataset`.

* `assess(snapshot, library, settings)` normalises the catalogue code and runs the
  readiness scan (which includes the SECURITY validator): the eligibility answer
  (`blocked`, `coupled` or `clean` with its reasons) and the normalised working base.
* `opening_state(...)` is the state delta that opens a session or switches its library.
* `ingest_dataset(...)` parses pasted text, stores it in the session's dataset store
  (replacing an older dataset of the session), and proposes default bindings.

Used by the `/v1` routes and by the development fixture seed, so a seeded session is
exactly what the routes would have built. No ADK import.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from .code.normalise import SUPPORTED_LIBRARIES as NORMALISED_LIBRARIES
from .code.normalise import normalise
from .code.readiness import ReadinessStatus, scan
from .data.bindings import default_bindings
from .data.parse import ParsedDataset, parse_dataset
from .data.store import DatasetStore
from .schemas import Binding
from .session_state import BINDINGS, DATASET_ID, CatalogueSnapshot, initial_state
from .settings import AgentSettings


@dataclass(frozen=True)
class Eligibility:
    """Whether a spec and library pair can be adapted, and why."""

    eligible: bool
    status: ReadinessStatus
    reasons: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)

    def public(self) -> dict[str, Any]:
        """The eligibility as the routes answer it (hints stay on the server)."""
        return {"eligible": self.eligible, "status": self.status, "reasons": list(self.reasons)}


def assess(snapshot: CatalogueSnapshot, library: str, settings: AgentSettings) -> tuple[Eligibility, str]:
    """Normalise and scan one catalogue pair: its eligibility and the normalised code."""
    code = snapshot.code
    normalised = normalise(code, library=library) if library in NORMALISED_LIBRARIES else code
    readiness = scan(normalised, spec_id=snapshot.spec_id, library=library, enabled_libraries=settings.libraries)
    eligibility = Eligibility(
        eligible=readiness.status != "blocked",
        status=readiness.status,
        reasons=list(readiness.reasons),
        hints=list(readiness.hints),
    )
    return eligibility, normalised


def opening_state(
    *, spec_id: str, library: str, locale: str, snapshot: CatalogueSnapshot, normalised: str, eligibility: Eligibility
) -> dict[str, Any]:
    """The state delta of an eligible session (`initial_state` with the readiness record)."""
    return initial_state(
        spec_id=spec_id,
        library=library,
        locale=locale,
        snapshot=snapshot,
        normalised=normalised,
        readiness={"status": eligibility.status, "reasons": eligibility.reasons, "hints": eligibility.hints},
    )


@dataclass
class IngestedDataset:
    """A parsed and stored dataset with its proposed bindings."""

    dataset_id: str
    parsed: ParsedDataset
    bindings: list[Binding]

    def state_delta(self) -> dict[str, Any]:
        return {DATASET_ID: self.dataset_id, BINDINGS: [binding.model_dump() for binding in self.bindings]}


def store_dataset(
    store: DatasetStore,
    session_id: str,
    parsed: ParsedDataset,
    snapshot: CatalogueSnapshot,
    previous_id: str | None = None,
) -> IngestedDataset:
    """Store a parsed dataset for a session, replacing its previous one; raises `StoreFull`."""
    dataset_id = store.put(session_id, parsed)
    if previous_id and previous_id != dataset_id:
        store.delete(previous_id, session_id)
    return IngestedDataset(dataset_id, parsed, default_bindings(snapshot.roles(), parsed.profile))


def ingest_dataset(
    store: DatasetStore, session_id: str, text: str, snapshot: CatalogueSnapshot, previous_id: str | None = None
) -> IngestedDataset:
    """Parse and store pasted data for a session; raises `ParseError` or `StoreFull`."""
    return store_dataset(store, session_id, parse_dataset(text), snapshot, previous_id)


MAX_JUDGE_SAMPLE_CHARS = 3_000


def dataset_judge_input(parsed: ParsedDataset) -> str:
    """What the dataset judge sees: headers, top values and sample cells, at most 3 KB, as JSON."""
    profile = parsed.profile
    payload: dict[str, Any] = {
        "columns": [column.name for column in profile.columns],
        "top_values": {column.name: column.top[:3] for column in profile.columns if column.top},
        "sample": profile.sample[:3],
    }
    text = json.dumps(payload, ensure_ascii=False)
    while len(text) > MAX_JUDGE_SAMPLE_CHARS and (payload["sample"] or payload["top_values"]):
        if payload["sample"]:
            payload["sample"] = payload["sample"][:-1]
        else:
            payload["top_values"] = dict(list(payload["top_values"].items())[:-1])
        text = json.dumps(payload, ensure_ascii=False)
    return text[:MAX_JUDGE_SAMPLE_CHARS]
