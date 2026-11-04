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
`set_type` refuses anyway. A column whose name or cells say ids, codes or spans of years
(`stays_text`) is none either: such cells may read as numbers or dates, and it would change
what they mean (owner's second opinion of 2026-11-02). For a role that takes dates, a column
of whole numbers is a candidate too, as years, only with a year header (`temporal.year_score`
2), because prices of 1149 to 3000 look like years, and only with one row per year: in
`Year, Month, Temperature` every month would fall on 1 January, and `make_date` builds those
dates. The session block shows the root one line per candidate (`Candidate.line`, at most
`MAX_CANDIDATES`), with the operations that make it:

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

A date column for the axis counts even when the axis is taken: the defaults fill the roles in
spec order, so `8 Nov 2026,3000` on a line plot has its one number column on `x` and `y`
open. The dates then take the axis, and the numbers move to `y` (`bindings.axis_slot`).

A lower and upper bound pair left open (`bounds.py`: both roles required and unbound, also when
the defaults left them open because two unrelated measures would have been inverted) takes a
text column of ranges first (`RangeSplit`): every cell two numbers around one dash, the first
never above the second (`prepare.range_run`: `10–25`, `-5–10`, `1,5–2,5` with decimal commas).
That is `certain` only, the one shape throughout; a column with one odd cell, an id (`A-12`), an
ISO date and a span of years are no candidate, and the user can still ask for the `split`. Its
operation is the `split` into two new columns named after the column with `min` and `max` in
the session language (`RANGE_WORDS`), which the service binds to the lower and the upper role
(`bindings.carry_bindings`).

Last comes the row number, when no column and no conversion can fill the open role
(`RowNumbers`, `bindings.row_slot`, the owner's live test of 2026-11-02: `1,3,5,4,6,2` on a
line plot). On a required axis it counts as `certain`: the column `index` holds 1 to n, the axis
takes it, and a number column that sat there moves to the open measure, with one line in
the reply. On a role that names each row (a bar chart without labels) it is `uncertain`: the
root offers it as its one question. A row-number column the paste already has is reused, and
nothing here runs for `/dataset/copy`, which copies confirmed data byte for byte.

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
from ..schemas import MAX_COLUMN_NAME_CHARS, Binding, ColumnProfile, DatasetProfile
from .bindings import RowSlot, axis_slot, check_bindings, code_like, row_number_columns, row_slot
from .bounds import BoundPair, bound_pairs
from .parse import ParsedDataset, id_like, span_like
from .prepare import ROW_NUMBER_NAME, DryRun, RangeRun, dry_run, range_run, read_frame, year_run
from .temporal import year_score


MAX_CANDIDATES = 3
"""The candidate lines the session block carries at most: one per open role is the usual case."""

Target = Literal["number", "datetime"]
Outcome = Literal["date", "number", "index"]

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

RANGE_WORDS: dict[str, tuple[str, str]] = {
    "en": ("min", "max"),
    "de": ("Min", "Max"),
    "fr": ("min", "max"),
    "es": ("mín", "máx"),
    "it": ("min", "max"),
    "pt": ("mín", "máx"),
    "nl": ("min", "max"),
    "pl": ("min", "maks"),
}
"""The words for the lower and the upper end of a range in the names of a `split`'s two columns, as `TYPE_WORDS`."""


@dataclass(frozen=True)
class Candidate:
    """A column that a conversion turns into what the open role `role` takes, with its dry run."""

    role: str
    dry: DryRun
    name: str
    """The new column's name (`new_name`)."""
    moved: Binding | None = None
    """What happens to the column on the axis the conversion takes (`bindings.axis_slot`)."""

    @property
    def certain(self) -> bool:
        return self.dry.certain

    @property
    def outcome(self) -> Outcome:
        return "date" if self.dry.type == "datetime" else "number"

    def operations(self) -> list[dict[str, Any]]:
        """The `prepare_data` operations that make the conversion: the new column, then a sort when it runs newest first."""
        conversion: dict[str, Any] = {"op": "set_type", "column": self.dry.column, "type": self.dry.type}
        if self.dry.date_format is not None:
            conversion["date_format"] = self.dry.date_format
        operations = [{**conversion, "name": self.name}]
        if self.dry.order == "descending":
            operations.append({"op": "sort", "column": self.name})
        return operations

    def line(self) -> str:
        """The session block's line: the role, the column, the counts, certain or why not, and the operations."""
        dry = self.dry
        kind = "text" if dry.date_format is None else "whole numbers"
        line = f"{self.role}: column '{dry.column}' ({kind}): {dry.read} of {dry.present} cells would be {dry.reading}"
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
        if self.moved is not None:
            line += f"; {self.moved.role} then takes '{self.moved.column}', which {self.role} holds now"
        return f"{line}; operations: {json.dumps(self.operations(), ensure_ascii=False)}"


@dataclass(frozen=True)
class RangeSplit:
    """A text column of ranges (`10–25`) that a `split` turns into the two columns a lower and upper bound pair takes."""

    pair: BoundPair
    run: RangeRun
    names: tuple[str, str]
    """The new columns' names (`range_names`): the lower end first."""

    @property
    def role(self) -> str:
        return self.pair.lower

    @property
    def certain(self) -> bool:
        return True  # only a column of one shape throughout is a candidate (`prepare.range_run`)

    @property
    def outcome(self) -> Outcome:
        return "number"

    def operations(self) -> list[dict[str, Any]]:
        return [{"op": "split", "column": self.run.column, "separator": self.run.separator, "names": list(self.names)}]

    def line(self) -> str:
        """The session block's line: the two roles, the column, the counts, certain, and the operations."""
        run, (low, high) = self.run, self.names
        line = (
            f"{self.pair.lower} and {self.pair.upper}: column '{run.column}' (text): {run.present} of {run.present} "
            f"cells would split at '{run.separator}' into two numbers, the first never above the second, and be "
            f"{run.reading}, as the new columns '{low}' ({self.pair.lower}) and '{high}' ({self.pair.upper}); "
            "certain: every cell reads and nothing is guessed"
        )
        return f"{line}; operations: {json.dumps(self.operations(), ensure_ascii=False)}"


@dataclass(frozen=True)
class RowNumbers:
    """The row numbers for a role that no column and no conversion can fill (`bindings.row_slot`)."""

    slot: RowSlot
    name: str
    rows: int

    @property
    def role(self) -> str:
        return self.slot.role

    @property
    def certain(self) -> bool:
        return self.slot.certain

    @property
    def outcome(self) -> Outcome:
        return "index"

    def operations(self) -> list[dict[str, Any]]:
        return [{"op": "row_number", "name": self.name}]

    def line(self) -> str:
        """The session block's line: the open role, what fills it, certain or why not, and the operations."""
        moved = self.slot.moved
        line = (
            f"{moved.role if moved else self.role}: no column or conversion fills it; a new column '{self.name}' with "
            f"the row numbers 1 to {self.rows} takes {self.role}"
        )
        if moved is not None:
            line += f", and {moved.role} takes '{moved.column}', which {self.role} holds now"
        if self.certain:
            line += "; certain: a list of values is drawn by position, and this is wanted, never a mistake"
        else:
            line += f"; uncertain: the table has no labels for {self.role}, and a row number says nothing as a label"
        return f"{line}; operations: {json.dumps(self.operations(), ensure_ascii=False)}"


def stays_text(column: ColumnProfile) -> bool:
    """A column no conversion touches: ids, codes or spans of years, by its name or its frequent cells."""
    return id_like(column.name) or span_like(column.name) or code_like(column)


def candidates(
    bindings: list[Binding],
    roles: list[DataRole],
    profile: DatasetProfile,
    parsed: ParsedDataset,
    *,
    language: str = DEFAULT_LANGUAGE,
    keep_text: Collection[str] = (),
    cache: MutableMapping[tuple[str, str], DryRun | RangeRun | None] | None = None,
) -> list[Candidate | RangeSplit | RowNumbers]:
    """The conversions that would fill the required roles `bindings` leave open, at most `MAX_CANDIDATES`.

    First an open lower and upper bound pair takes the first free column of ranges (`RangeSplit`);
    then the roles in spec order, each taking the first free column (in column order) whose dry
    run reads it as the role's type. A conversion is a suggestion, like the default bindings, so
    it takes only a column no binding holds and gives each column to one role: a column on
    several roles is the user's choice only (`bindings.check_bindings`). `keep_text` names the
    columns kept text on request, `cache` holds the dry runs by column and type
    (`StoredDataset.dry_runs`; `range` for the ranges); `parsed` is read into a frame only when a
    dry run is due. With no conversion at all, the row numbers (`RowNumbers`).
    """
    missing = set(check_bindings(bindings, roles, profile).missing_roles)
    if not missing:
        return []
    used = {binding.column for binding in bindings}
    columns = [column for column in profile.columns if column.name not in used]
    free = [
        column.name
        for column in columns
        if column.dtype == "text" and column.name not in keep_text and not stays_text(column)
    ]
    years = [
        column.name for column in columns if year_score(column) == 2 and column.unique == profile.rows - column.missing
    ]
    runs = cache if cache is not None else {}
    frame = None

    def run(column: str, target: Target) -> DryRun | None:
        nonlocal frame
        key = (column, target)
        if key not in runs:
            if frame is None:
                frame = read_frame(parsed)
            runs[key] = year_run(frame, column) if column in years else dry_run(frame, column, target, profile.decimal)
        result = runs[key]
        return result if isinstance(result, DryRun) else None

    def ranges(column: str) -> RangeRun | None:
        nonlocal frame
        key = (column, "range")
        if key not in runs:
            if frame is None:
                frame = read_frame(parsed)
            runs[key] = range_run(frame, column, profile.decimal)
        result = runs[key]
        return result if isinstance(result, RangeRun) else None

    slot = axis_slot(bindings, roles, profile)
    moved = slot.moved if slot is not None else None
    wanted = {role.name for role in roles if role.name in missing}
    if slot is not None and moved is not None and "datetime" in slot.role.kinds:
        wanted.add(slot.role.name)
    taken: set[str] = set()
    names = {column.name for column in profile.columns}
    found: list[Candidate | RangeSplit | RowNumbers] = []
    for pair in bound_pairs(roles):
        if pair.lower not in missing or pair.upper not in missing:
            continue
        column = next((column for column in free if column not in taken and ranges(column) is not None), None)
        ranged = ranges(column) if column is not None else None
        if column is None or ranged is None or len(found) == MAX_CANDIDATES:
            continue
        pair_names = range_names(column, language, names)
        names.update(pair_names)
        taken.add(column)
        wanted -= {pair.lower, pair.upper}
        found.append(RangeSplit(pair, ranged, pair_names))
    for role in roles:
        if role.name not in wanted or len(found) == MAX_CANDIDATES:
            continue
        if role.name in missing and found and moved is not None:
            continue  # the dates that take the axis leave this role the axis's column
        for column in [*free, *(years if "datetime" in role.kinds else [])]:
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
            on_axis = slot is not None and role.name == slot.role.name
            found.append(Candidate(role.name, dry, name, moved if on_axis else None))
            break
    return found or _row_numbers(bindings, roles, profile, used)


def _row_numbers(
    bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile, used: Collection[str]
) -> list[Candidate | RangeSplit | RowNumbers]:
    """The row numbers as the one candidate, when `bindings.row_slot` finds them a role."""
    slot = row_slot(bindings, roles, profile)
    if slot is None:
        return []
    names = {column.name for column in profile.columns}
    pasted = sorted(row_number_columns(profile) - set(used))
    name, number = (pasted[0] if pasted else ROW_NUMBER_NAME), 2
    while not pasted and name in names:
        name = f"{ROW_NUMBER_NAME}_{number}"
        number += 1
    return [RowNumbers(slot, name, profile.rows)]


def new_name(column: str, target: Target, language: str, taken: Collection[str]) -> str:
    """`<column> (<type word>)` within the column-name cap, `_2`, `_3`, ... before the bracket when it is taken."""
    return _with_word(column, TYPE_WORDS.get(canonical(language), TYPE_WORDS[DEFAULT_LANGUAGE])[target], taken)


def range_names(column: str, language: str, taken: Collection[str]) -> tuple[str, str]:
    """`<column> (min)` and `<column> (max)` in the session language (`RANGE_WORDS`), as `new_name` names them."""
    low, high = RANGE_WORDS.get(canonical(language), RANGE_WORDS[DEFAULT_LANGUAGE])
    first = _with_word(column, low, taken)
    return first, _with_word(column, high, {*taken, first})


def _with_word(column: str, word: str, taken: Collection[str]) -> str:
    suffix = f" ({word})"
    stem = column[: MAX_COLUMN_NAME_CHARS - len(suffix)].rstrip()
    name, number = stem + suffix, 2
    while name in taken:
        tail = f"_{number}"
        name = column[: MAX_COLUMN_NAME_CHARS - len(suffix) - len(tail)].rstrip() + tail + suffix
        number += 1
    return name
