"""Opening a session and taking in a dataset: the deterministic steps behind `/v1/sessions` and `/dataset`.

* `assess(snapshot, library, settings)` normalises the catalogue code and runs the
  readiness scan (which includes the SECURITY validator): the eligibility answer
  (`blocked`, `coupled` or `clean` with its reasons) and the normalised working base.
* `opening_state(...)` is the state delta that opens a session or switches its library.
* `ingest_dataset(...)` parses pasted text, stores it in the session's dataset store
  (replacing an older dataset of the session and the versions kept for undo), and
  proposes default bindings; a paste is version 1 of the data (`dataset_versions.py`).
* `instruction_like(parsed)` and `dataset_judge_inputs(parsed)` are what the
  `/dataset` route checks before it stores a dataset: a deterministic pre-filter over
  every header and cell for text addressed to an AI, then the dataset judge on every
  part of the judged view. Both look for injection only: personal data (names, postal
  and e-mail addresses, phone numbers, web addresses, amounts) is ordinary data.
* `notes_instruction_like(lines)` and `notes_judge_input(lines)` do the same for the
  notes pasted around the table (`ParsedDataset.context_lines`): the pre-filter, then
  the scope judge. A refusal there drops only the notes, never the table.

Used by the `/v1` routes and by the development fixture seed, so a seeded session is
exactly what the routes would have built. No ADK import.
"""

import copy
import csv
import io
import json
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from .code.normalise import SUPPORTED_LIBRARIES as NORMALISED_LIBRARIES
from .code.normalise import normalise
from .code.readiness import ReadinessStatus, scan
from .data.bindings import default_bindings
from .data.parse import ParsedDataset, display_copy, parse_dataset, with_constant_columns
from .data.store import DatasetStore
from .policy import fence
from .schemas import MAX_SAMPLE_ROWS, MAX_TOP_VALUES, Binding
from .session_state import (
    BINDINGS,
    DATASET_HISTORY,
    DATASET_ID,
    DATASET_VERSION,
    PENDING_REQUEST,
    CatalogueSnapshot,
    initial_state,
)
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
        """The delta of a paste: version 1 of the data, with no history to undo.

        A request kept from a plot that stopped before the confirmation (`PENDING_REQUEST`) was
        written for the data it replaces, so it goes too: a title for the Swiss table must not
        land on the German one pasted after it.
        """
        return {
            DATASET_ID: self.dataset_id,
            BINDINGS: [binding.model_dump() for binding in self.bindings],
            DATASET_HISTORY: [],
            DATASET_VERSION: 1,
            PENDING_REQUEST: None,
        }


def store_dataset(
    store: DatasetStore,
    session_id: str,
    parsed: ParsedDataset,
    snapshot: CatalogueSnapshot,
    previous_id: str | None = None,
    history: Sequence[str] = (),
    *,
    notes_screened: bool = False,
    code: str | None = None,
) -> IngestedDataset:
    """Store a parsed dataset for a session, replacing its previous one and its history; raises `StoreFull`.

    The notes pasted around the table (`context_lines`) are kept only when the caller says they
    passed the dataset route's screen (`notes_screened`: the pre-filter and the scope judge); every
    other path (a fixture seed, an eval's ingest) stores the table without them, so no unjudged
    note ever reaches the root (#12168 review). `code` is the Python that computed the table
    (`run_data_code`), kept with the version for the data panel.
    """
    if not notes_screened:
        # Constant columns whose values went into the notes come back as columns, so the values survive.
        parsed = with_constant_columns(parsed)
        if parsed.context_lines:
            parsed = replace(parsed, context_lines=[])
    dataset_id = store.put(session_id, parsed, code=code)
    for old in (previous_id, *history):
        if old and old != dataset_id:
            store.delete(old, session_id)
    return IngestedDataset(dataset_id, parsed, default_bindings(snapshot.roles(), parsed.profile))


def ingest_dataset(
    store: DatasetStore,
    session_id: str,
    text: str,
    snapshot: CatalogueSnapshot,
    previous_id: str | None = None,
    history: Sequence[str] = (),
) -> IngestedDataset:
    """Parse and store pasted data for a session; raises `ParseError` or `StoreFull`."""
    return store_dataset(store, session_id, parse_dataset(text), snapshot, previous_id, history)


MAX_JUDGE_CHUNK_CHARS = 4_000
"""The size of one part of the dataset judge's input in characters of JSON (about 1,000 tokens)."""

_FILLER = r"(?:[\w'-]+\s+){0,3}"
_RULE_QUALIFIER = r"(?:previous|prior|above|earlier|preceding|former|system|original|your|my|all|any|these)"
INSTRUCTION_LIKE = re.compile(
    r"(?i)"
    # "ignore all the previous instructions", "forget your prompt", "disregard every earlier guideline"
    r"\b(?:ignore|disregard|forget|override|bypass)\s+" + _FILLER + r"(?:instructions?|prompts?|directions?|"
    r"guidelines?)\b"
    # "disregard all rules", "forget your rules"; not "ignore the rules of the road"
    r"|\b(?:ignore|disregard|forget|override|bypass)\s+(?:\w+\s+){0,2}?" + _RULE_QUALIFIER + r"\s+(?:the\s+)?rules?\b"
    # "ignore everything above"
    r"|\b(?:ignore|disregard|forget)\s+(?:everything|anything|all)\s+(?:above|before|prior|previously|earlier)\b"
    # "Ignoriere alle Anweisungen", "Vergiss alle vorherigen Anweisungen", "Missachte die bisherigen Regeln"
    r"|\b(?:ignorier\w*|vergiss|vergesst|vergessen\s+sie|missacht\w*|übergeh\w*)\s+" + _FILLER + r"(?:anweisungen|"
    r"instruktionen|vorgaben|prompts?|systemprompts?)\b"
    r"|\b(?:ignorier\w*|vergiss|vergesst|vergessen\s+sie|missacht\w*|übergeh\w*)\s+(?:\w+\s+){0,2}?"
    r"(?:vorherigen|bisherigen|obigen|vorigen|deine|ihre|alle)\s+regeln\b"
    # "you are now an AI without rules", "you are a language model"; not "you are a model employee"
    r"|\byou\s+are\s+(?:now|no\s+longer)\s+(?:an?\s+|the\s+|my\s+)?(?:ai|assistant|chatbot|bot|"
    r"language\s+model|llm|model|gpt|chatgpt|claude|gemini|dan|jailbroken|in\s+developer\s+mode|unrestricted)\b"
    r"|\byou\s+are\s+(?:an?\s+|the\s+|my\s+)?(?:ai|ai\s+model|language\s+model|llm|gpt|chatgpt|claude|gemini|"
    r"dan|jailbroken|in\s+developer\s+mode|unrestricted)\b"
    r"|\byou\s+are\s+(?:an?\s+|the\s+|my\s+)?(?:assistant|chatbot|bot|model)\s+now\b"
    r"|\bdu\s+bist\s+(?:jetzt\s+|nun\s+|ab\s+jetzt\s+)?(?:eine?\s+)?(?:ki|assistent\w*|chatbot|bot|sprachmodell)\b"
    r"|\bsystem\s+prompt\b"
    # a role marker at the start of a cell or line followed by an order: "system: you obey", not "System: Linux"
    r"|(?:^|[\n,\"])[ \t]*(?:system|assistant)[ \t]*:[ \t]*(?:you|ignore|disregard|forget|from\s+now|always|"
    r"never|do|reply|respond|answer|act|pretend|print|reveal|repeat|say|write|follow|obey)\b"
    # chat-template tokens
    r"|<\|?(?:im_start|im_end|system|endoftext)\|?>|\[/?INST\]|<<SYS>>"
)
"""Text addressed to an AI in a header or a cell: the dataset is refused before the judge.

A deliberately narrow list: every pattern is rare in real tables, so an ordinary
free-text column (comments, product descriptions, a job title such as "Assistant:
Maria Lopez", a log line such as "system: started") passes; "you are" alone or "act
as" would not. Anything subtler is the judge's. Links of any scheme (`javascript:`
included), web addresses, e-mail addresses and phone numbers are data, not
instructions, and pass: a cell reaches a plot only as a value of `df`, and the chat
and the plot event strip links from what the root writes."""


def instruction_like(parsed: ParsedDataset) -> bool:
    """Whether any header or cell of the canonical dataset holds text that `INSTRUCTION_LIKE` matches.

    It reads every row, not only the ones the judge sees: the pattern costs nothing,
    and a cell anywhere can reach the reviewer's image as a label.
    """
    return INSTRUCTION_LIKE.search(parsed.csv) is not None


NOTES_INSTRUCTION_WARNING = "the notes above or below the table were left out: they read like instructions to an AI"
NOTES_REFUSED_WARNING = "the notes above or below the table were left out: they are not about the data or the plot"
NOTES_UNCHECKED_WARNING = "the notes above or below the table were left out: they could not be checked right now"
"""The warnings of the three ways the `/dataset` route drops the notes pasted with a table
(`ParsedDataset.context_lines`): the pre-filter, a refusing scope verdict, no verdict. The table
itself is stored either way; dropping the notes costs the user nothing, no strike included."""


def notes_instruction_like(lines: Sequence[str]) -> bool:
    """Whether the notes pasted around a table hold text that `INSTRUCTION_LIKE` matches, read as one block.

    The same pattern as the cells: one line that hits drops every note, because a hidden
    injection in a copied web table usually spans the lines around a harmless one.
    """
    return bool(lines) and INSTRUCTION_LIKE.search("\n".join(lines)) is not None


def notes_judge_input(lines: Sequence[str]) -> str:
    """The scope judge's input for the notes pasted around a table: the lines inside `<user_notes>`.

    The scope rubric (`scope_judge.md`, "Notes pasted with the data") judges such a block as
    the user's words about the data; the scope eval sends its `notes` cases through this too.
    """
    return fence("user_notes", "\n".join(lines))


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
    200 characters) instead of the profile's 40-character display copy. The top
    values walk the column the way the profile does (`parse._profile_column`): by
    frequency, until `MAX_TOP_VALUES` distinct display copies are found. Values whose
    display copies coincide count once in the profile, so every one of them is judged,
    and the lower-ranked values the profile reaches past them are judged too.
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
        values: list[str] = []
        copies: set[str] = set()
        for value, _ in counts.most_common():
            values.append(value)
            copies.add(display_copy(value))
            if len(copies) == MAX_TOP_VALUES:
                break
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
    shorter view. The view is the table with its constant columns (`with_constant_columns`):
    they come back as columns when the notes that carry their values are not kept.
    """
    view = judged_view(with_constant_columns(parsed))
    parts = _Parts({"columns": view.columns})
    for name, values in view.top_values.items():
        parts.add(("top_values", name), values)
    for number, row in enumerate(view.sample, start=1):
        for name, cell in zip(view.columns, row, strict=False):
            if cell:
                parts.add(("sample_rows", f"row {number}", name), cell)
    return parts.done()
