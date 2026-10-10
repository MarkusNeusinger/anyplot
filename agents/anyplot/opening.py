"""Opening a session and taking in a dataset: the deterministic steps behind `/v1/sessions` and `/dataset`.

* `assess(snapshot, library, settings)` normalises the catalogue code and runs the
  readiness scan (which includes the SECURITY validator): the eligibility answer
  (`blocked`, `coupled` or `clean` with its reasons) and the normalised working base.
* `opening_state(...)` is the state delta that opens a session or switches its library.
* `ingest_dataset(...)` parses pasted text, stores it in the session's dataset store
  (replacing an older dataset of the session), and proposes default bindings.
* `instruction_like(parsed)` and `dataset_judge_inputs(parsed)` are what the `/dataset`
  route checks before it stores a dataset: a deterministic pre-filter, then the
  dataset judge on every part of the judged view.

Used by the `/v1` routes and by the development fixture seed, so a seeded session is
exactly what the routes would have built. No ADK import.
"""

import copy
import csv
import io
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .code.normalise import SUPPORTED_LIBRARIES as NORMALISED_LIBRARIES
from .code.normalise import normalise
from .code.readiness import ReadinessStatus, scan
from .data.bindings import default_bindings
from .data.parse import ParsedDataset, parse_dataset
from .data.store import DatasetStore
from .schemas import MAX_SAMPLE_ROWS, MAX_TOP_VALUES, Binding
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


MAX_JUDGE_CHUNK_CHARS = 4_000
"""The size of one part of the dataset judge's input in characters of JSON (about 1,000 tokens)."""

INSTRUCTION_LIKE = re.compile(
    r"(?i)"
    # "ignore all previous instructions", "disregard the rules", "forget your prompt"
    r"\b(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+|any\s+|the\s+|your\s+|my\s+|these\s+)?"
    r"(?:previous\s+|prior\s+|above\s+|earlier\s+|preceding\s+|former\s+|system\s+|original\s+)?"
    r"(?:instructions?|rules?|prompts?|directions?|guidelines?)\b"
    # "ignoriere alle vorherigen Anweisungen"
    r"|\bignorier\w*\s+(?:alle\s+|die\s+)?(?:vorherigen|bisherigen|obigen|vorigen|deine|ihre)\s+"
    r"(?:anweisungen|regeln|instruktionen|vorgaben)\b"
    # "you are now an AI without rules", "du bist jetzt ein Assistent"
    r"|\byou\s+are\s+(?:now\s+|no\s+longer\s+)?(?:an?\s+|the\s+|my\s+)?(?:ai|assistant|chatbot|bot|"
    r"language\s+model|llm|model|gpt|chatgpt|claude|gemini|dan|jailbroken|developer\s+mode|unrestricted)\b"
    r"|\bdu\s+bist\s+(?:jetzt\s+|nun\s+|ab\s+jetzt\s+)?(?:eine?\s+)?(?:ki|assistent\w*|chatbot|bot|sprachmodell)\b"
    r"|\bsystem\s+prompt\b"
    # a role marker at the start of a cell or line: "system:", "assistant:"
    r"|(?:^|[\n,\"])[ \t]*(?:system|assistant|developer)[ \t]*:"
    # chat-template tokens
    r"|<\|?(?:im_start|im_end|system|endoftext)\|?>|\[/?INST\]|<<SYS>>"
    # URL schemes
    r"|\b(?:https?|ftps?|sftp|file)://|\b(?:javascript|vbscript):"
)
"""Text addressed to an AI, or a URL, in a header or a cell: the dataset is refused before the judge.

A deliberately narrow list: every pattern is rare in real tables, so an ordinary
free-text column (comments, product descriptions) passes; "you are" alone or
"act as" would not. URLs count because a cell reaches the plot as a label and the
PNG carries the anyplot.ai footer. Anything subtler is the judge's."""


def instruction_like(parsed: ParsedDataset) -> bool:
    """Whether any header or cell of the canonical dataset holds text that `INSTRUCTION_LIKE` matches.

    It reads every row, not only the ones the judge sees: the pattern costs nothing,
    and a cell anywhere can reach the reviewer's image as a label.
    """
    return INSTRUCTION_LIKE.search(parsed.csv) is not None


@dataclass(frozen=True)
class JudgedView:
    """The dataset as the judge sees it: every header, the root's and the adapter's samples and top values, in full."""

    columns: list[str]
    top_values: dict[str, list[str]]
    sample: list[list[str]]


def judged_view(parsed: ParsedDataset) -> JudgedView:
    """Every header, the top values of every text and boolean column, and the first sample rows, cells in full.

    The rows and values are the ones the profile gives the root and the adapter
    (`MAX_SAMPLE_ROWS` rows, `MAX_TOP_VALUES` values, the same order), read from the
    canonical `data.csv` so that each cell keeps its whole text (up to the parser's
    200 characters) instead of the profile's 40-character display copy.
    """
    reader = csv.reader(io.StringIO(parsed.csv))
    columns = next(reader)
    rows = list(reader)
    dtypes = {column.name: column.dtype for column in parsed.profile.columns}
    top_values: dict[str, list[str]] = {}
    for index, name in enumerate(columns):
        if dtypes.get(name) not in ("text", "boolean"):
            continue
        counts = Counter(row[index] for row in rows if index < len(row) and row[index])
        values = [value for value, _ in counts.most_common(MAX_TOP_VALUES)]
        if values:
            top_values[name] = values
    return JudgedView(columns=columns, top_values=top_values, sample=rows[:MAX_SAMPLE_ROWS])


class _Parts:
    """Packs a JSON payload into parts of at most `MAX_JUDGE_CHUNK_CHARS` characters, one item at a time.

    An item that does not fit the current part starts the next one; a single item is
    never split (the largest, all 50 headers, is about 3,400 characters).
    """

    def __init__(self, first: dict[str, Any]) -> None:
        self.parts: list[str] = []
        self.payload = first

    def add(self, path: tuple[str, ...], value: Any) -> None:
        trial = copy.deepcopy(self.payload)
        _put(trial, path, value)
        if len(_json(trial)) > MAX_JUDGE_CHUNK_CHARS and self.payload:
            self.parts.append(_json(self.payload))
            trial = {}
            _put(trial, path, value)
        self.payload = trial

    def done(self) -> list[str]:
        if self.payload:
            self.parts.append(_json(self.payload))
        return self.parts


def _put(payload: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    node = payload
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def dataset_judge_inputs(parsed: ParsedDataset) -> list[str]:
    """The judged view as JSON parts of about `MAX_JUDGE_CHUNK_CHARS` characters each; the judge sees every part.

    The first part holds every column name (50 of at most 64 characters fit in one
    part), then the top values column by column, then the sample rows cell by cell
    (an empty cell is left out), each starting a new part when the current one is
    full. Nothing is dropped: a wide table or long cells give more parts, never a
    shorter view.
    """
    view = judged_view(parsed)
    parts = _Parts({"columns": view.columns})
    for name, values in view.top_values.items():
        parts.add(("top_values", name), values)
    for number, row in enumerate(view.sample, start=1):
        for name, cell in zip(view.columns, row, strict=False):
            if cell:
                parts.add(("sample_rows", f"row {number}", name), cell)
    return parts.done()
