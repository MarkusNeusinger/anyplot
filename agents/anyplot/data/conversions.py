"""The conversions a required role left open could take: text columns that a `set_type` turns into its type.

No ADK import. Owner direction after the live test of 2026-11-01 ("it could suggest the
conversion, or directly create an extra column with the conversion; if anything required
can't be filled, it should at least check"): a price table whose months the parser kept as
text (`Nov 2026`) left a time series' date role open, and the root told the user that none
of the date formats it can apply read them. Now, when the bindings leave a required role
open (`check_bindings` lists it among `missing_roles`), the server checks in code which free
text columns a `set_type` would turn into the role's type, dates for a role that takes
dates and numbers for one that takes numbers, with a dry run of the conversion on the whole
column (`prepare.dry_run`) and its counts. A column that reads as dates is never a number
candidate (`Nov 26, 2026` is no 26.2026), a column kept text on request (`set_type text`) is
none at all, and neither is one where more than a tenth of the cells would fail, which
`set_type` refuses anyway. The session block shows the root one line per candidate
(`Candidate.line`, at most `MAX_CANDIDATES`), with the operations that make it:

* `certain`: every cell converts and the reading guesses nothing. The root makes the
  conversion in the summary turn without asking, as a new column beside the original
  (`set_type` with `name`), which the service binds to the role (`bindings.carry_bindings`),
  and says so in one sentence with the count; the user confirms the data as usual, and
  `.undo()` takes it back.
* `uncertain`: some cells would not read and would be missing, or the reading guesses the
  day and month order, the century of a two-digit year, the decimal mark or thousands
  separators (`prepare.Conversion.guess`). The root proposes the conversion with the counts,
  as its one question.

When the converted dates would run newest first, the operations end with a `sort` of the
new column: a time series is drawn in date order, so the root never asks about it.

The new column is named after its source with the type in the session language
(`Month (date)`, `Monat (Datum)`, `TYPE_WORDS`): the root takes the operations as given, so
the conversion is the same in every run. Each dry run is made once per dataset version
(`StoredDataset.dry_runs`).
"""

import json
from collections.abc import Collection, MutableMapping
from dataclasses import dataclass
from typing import Any, Literal

from core.spec_roles import DataRole

from ..language import DEFAULT_LANGUAGE, canonical
from ..schemas import MAX_COLUMN_NAME_CHARS, Binding, DatasetProfile
from .bindings import check_bindings
from .parse import ParsedDataset
from .prepare import DryRun, dry_run, read_frame


MAX_CANDIDATES = 3
"""The candidate lines the session block carries at most: one per open role is the usual case."""

Target = Literal["number", "datetime"]

TYPE_WORDS: dict[str, dict[Target, str]] = {
    "en": {"datetime": "date", "number": "number"},
    "de": {"datetime": "Datum", "number": "Zahl"},
    "fr": {"datetime": "date", "number": "nombre"},
    "es": {"datetime": "fecha", "number": "número"},
    "it": {"datetime": "data", "number": "numero"},
    "pt": {"datetime": "data", "number": "número"},
    "nl": {"datetime": "datum", "number": "getal"},
    "pl": {"datetime": "data", "number": "liczba"},
}
"""The word for the converted type in the new column's name, by session language (as `shape.LONG_NAMES`, owner rule:
generated text follows the session language, the user's own column names never change); English for any other."""


@dataclass(frozen=True)
class Candidate:
    """A text column that a conversion turns into what the open role `role` takes, with its dry run."""

    role: str
    dry: DryRun
    name: str
    """The new column's name (`new_name`)."""

    def operations(self) -> list[dict[str, Any]]:
        """The `prepare_data` operations that make the conversion: the new column, then a sort when it runs newest first."""
        operations: list[dict[str, Any]] = [
            {"op": "set_type", "column": self.dry.column, "type": self.dry.type, "name": self.name}
        ]
        if self.dry.order == "descending":
            operations.append({"op": "sort", "column": self.name})
        return operations

    def line(self) -> str:
        """The session block's line: the role, the column, the counts, certain or why not, and the operations."""
        dry = self.dry
        line = f"{self.role}: column '{dry.column}' (text): {dry.read} of {dry.present} cells would be {dry.reading}"
        if dry.certain:
            line += "; certain: every cell reads and nothing is guessed"
        else:
            reasons = []
            if dry.read < dry.present:
                missing = dry.present - dry.read
                reasons.append(f"{missing} {'cell' if missing == 1 else 'cells'} would not read and be missing")
            if dry.guess:
                reasons.append(f"the reading guesses {dry.guess}")
            line += f"; uncertain: {' and '.join(reasons)}"
        if dry.order == "descending":
            line += "; the dates run newest first, so the sort puts them oldest first"
        return f"{line}; operations: {json.dumps(self.operations(), ensure_ascii=False)}"


def candidates(
    bindings: list[Binding],
    roles: list[DataRole],
    profile: DatasetProfile,
    parsed: ParsedDataset,
    *,
    language: str = DEFAULT_LANGUAGE,
    keep_text: Collection[str] = (),
    cache: MutableMapping[tuple[str, str], DryRun | None] | None = None,
) -> list[Candidate]:
    """The conversions that would fill the required roles `bindings` leave open, at most `MAX_CANDIDATES`.

    The roles in spec order, each taking the first free text column (in column order) whose
    dry run reads it as the role's type; a column serves one role. `keep_text` names the
    columns kept text on request, `cache` holds the dry runs by column and type
    (`StoredDataset.dry_runs`); `parsed` is read into a frame only when a dry run is due.
    """
    missing = set(check_bindings(bindings, roles, profile).missing_roles)
    if not missing:
        return []
    used = {binding.column for binding in bindings}
    free = [column.name for column in profile.columns if column.dtype == "text" and column.name not in used]
    free = [name for name in free if name not in keep_text]
    if not free:
        return []
    runs = cache if cache is not None else {}
    frame = None

    def run(column: str, target: Target) -> DryRun | None:
        nonlocal frame
        key = (column, target)
        if key not in runs:
            if frame is None:
                frame = read_frame(parsed)
            runs[key] = dry_run(frame, column, target, profile.decimal)
        return runs[key]

    taken: set[str] = set()
    names = {column.name for column in profile.columns}
    found: list[Candidate] = []
    for role in roles:
        if role.name not in missing or len(found) == MAX_CANDIDATES:
            continue
        for column in free:
            if column in taken:
                continue
            dates = run(column, "datetime")
            dry = dates if "datetime" in role.kinds else None
            if dry is None and dates is None and "numeric" in role.kinds:
                dry = run(column, "number")
            if dry is None:
                continue
            name = new_name(column, dry.type, language, names)
            names.add(name)
            taken.add(column)
            found.append(Candidate(role.name, dry, name))
            break
    return found


def new_name(column: str, target: Target, language: str, taken: Collection[str]) -> str:
    """`<column> (<type word>)` within the column-name cap, `_2`, `_3`, ... before the bracket when it is taken."""
    word = TYPE_WORDS.get(canonical(language), TYPE_WORDS[DEFAULT_LANGUAGE])[target]
    suffix = f" ({word})"
    stem = column[: MAX_COLUMN_NAME_CHARS - len(suffix)].rstrip()
    name, number = stem + suffix, 2
    while name in taken:
        tail = f"_{number}"
        name = column[: MAX_COLUMN_NAME_CHARS - len(suffix) - len(tail)].rstrip() + tail + suffix
        number += 1
    return name
