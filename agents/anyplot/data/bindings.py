"""Default bindings of spec data roles to dataset columns, and their validation.

No ADK import. `bindings.apply`, which writes validated bindings into session
state and answers `409 run_active` during a run, belongs to the ADK session layer;
it calls `check_bindings`. `carry_bindings` is what a dataset version change
(`prepare_data`, undo) does to the bindings: the ones still valid stay, the roles
left without one get the defaults.

Compatibility of a role kind with a column dtype (`ACCEPTS`), with the tier that
ranks candidate columns for the default:

| Role kind     | Tier 1 (preferred) | Tier 2 (accepted)  |
|---------------|--------------------|--------------------|
| `numeric`     | number, integer    |                    |
| `categorical` | text, boolean      | integer            |
| `text`        | text               | boolean, integer   |
| `boolean`     | boolean            | integer (0/1 code) |
| `datetime`    | datetime (tier 0)  |                    |

A role with several kinds (`datetime/numeric`) accepts the union and takes the
best tier. A datetime column is tier 0 for every role that accepts datetime,
because no other kind can use it; that keeps `x (numeric/datetime)` on the date
column instead of the first number. A role without kinds accepts any column in
`check_bindings` but is never bound by default.

A role that needs values of 0 or more (`DataRole.non_negative`, set per spec by
`signs.py`) never takes a column with a negative value by default; it takes the next
candidate or stays unbound. Bound by hand, it is valid but warned about
(`BindingCheck.warnings`).
"""

import itertools
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from ..schemas import Binding, ColumnDtype, ColumnProfile, DatasetProfile
from .computed import name_match
from .parse import value_like
from .roles import DataRole, RoleKind
from .signs import has_negative, sign_line


# A variadic family binds at most this many columns by default (charts with more series stop
# being readable); the user can bind more in the UI, and `check_bindings` does not cap them.
MAX_VARIADIC_DEFAULT = 12
# Name similarity below this is noise and does not reorder candidates.
MIN_NAME_SIMILARITY = 0.6

ACCEPTS: dict[RoleKind, dict[ColumnDtype, int]] = {
    "numeric": {"number": 1, "integer": 1},
    "categorical": {"text": 1, "boolean": 1, "integer": 2},
    "text": {"text": 1, "boolean": 2, "integer": 2},
    "boolean": {"boolean": 1, "integer": 2},
    "datetime": {"datetime": 0},
}

GROUPING_KINDS: frozenset[RoleKind] = frozenset(("categorical", "text", "boolean"))
"""Role kinds whose column splits or labels the marks; a single-valued column ranks last for them."""

MIN_CONSTANT_ROWS = 5
"""The rows from which a number column with one distinct value is a constant, no measure (`weak_measures`)."""
MAX_CATEGORIES = 60
"""The distinct values up to which a text column is a plausible category (bars, groups, series) by default."""
YEAR_RANGE = (1000, 2200)
"""The values a year column holds, inclusive."""
MAX_YEAR_SPAN = 300
"""The widest range of an integer column that counts as years without a year name."""
YEAR_WORDS: frozenset[str] = frozenset(
    {"year", "years", "yr", "jahr", "jahre", "année", "annee", "an", "año", "ano", "anno", "jaar", "år", "rok"}
)
"""Column-name words that say the column holds years (`Jahr`, `year`, `Année`), compared in lower case."""
DATE_PART_WORDS: dict[str, int] = {
    **dict.fromkeys(("month", "monat", "mois", "mes", "mese", "maand", "månad", "miesiac", "miesiąc"), 12),
    **dict.fromkeys(("quarter", "quartal", "trimestre", "kwartaal", "kwartal"), 4),
    **dict.fromkeys(("week", "woche", "kalenderwoche", "semaine", "semana", "settimana"), 53),
}
"""Column-name words that say an integer column numbers a month, a quarter or a week of the year, with the
largest value it then holds. Singular only, and no unit words: `Months since start`, `Dauer (Minuten)`,
`Days to ship` and a `kW` column are measures (review of 2026-10-15)."""
CODE_WORDS: frozenset[str] = frozenset(
    {"id", "code", "codes", "iso", "iso2", "iso3", "key", "abbr", "abbreviation", "kürzel", "kuerzel", "symbol"}
)
"""Column-name words that say a text column holds codes for something a name column may spell out (`country.id`)."""
NAME_WORDS: frozenset[str] = frozenset({"name", "names", "value", "label", "title", "bezeichnung", "nom", "nombre"})
"""Column-name words that say a text column spells something out (`country.value`, `product_name`)."""

_NOT_ALNUM = re.compile(r"[^0-9a-z]+")
_CODE_VALUE = re.compile(r"[A-Z][A-Z0-9]{1,3}")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_WORDS = re.compile(r"[^\W_]+")


@dataclass(frozen=True)
class BindingCheck:
    """The verdict on a set of bindings. `complete` needs no errors and every required role bound.

    `warnings` never refuse a binding: one line per role that needs values of 0 or more
    bound to a column with a negative value, or left open because every column that
    fits it has one (`signs.py`).
    """

    complete: bool
    errors: list[str]
    missing_roles: list[str]
    warnings: list[str] = field(default_factory=list)


def default_bindings(roles: list[DataRole], profile: DatasetProfile) -> list[Binding]:
    """Bind roles to columns: exact names first, then by kind tier and name similarity.

    1. A column whose normalised name equals a role's (or, for a variadic family
       `y`, matches `y<n>`) is bound to it when the dtypes are compatible.
    2. The remaining roles pick, in the order required single roles, required
       variadic families, optional single roles, optional variadic families (spec
       order within each group), the unused compatible column with the best
       (single-valued, weak measure, category rank, tier, name similarity, code rank,
       year rank, column position): for a categorical, text or boolean role a column with one distinct
       value ranks after every column with two or more (`_constant_group`), and a real
       category before a year column before a text column of numbers
       (`_category_rank`); a number role ranks year columns after the measures, a role
       that also takes dates before them (`_year_rank`, both since 2026-10-15). A measure role
       (`is_measure`) ranks a weak measure (`weak_measures`: a constant, years, a month) after
       every other column, and an optional one never takes it; an axis (`is_axis`, `x`) avoids
       only constants and ranks years first, so a scatter of `Month, Temperature` keeps the
       month on x; a grouping role ranks a column of codes after its name column
       (`_code_rank`; all since live test round 3 and its review of 2026-10-15). A variadic
       family takes every unused tier-0 or tier-1 column that is no weak measure in column
       order, up to `MAX_VARIADIC_DEFAULT`; a required family that would stay empty takes the
       first weak one. A role the plot can compute (`DataRole.computed`, `data/computed.py`) is
       bound only to a column whose name clearly holds it (`computed.name_match`, before any other
       role picks); otherwise it stays open and the plot computes it (owner decision of
       2026-10-15, "both allowed").
       A single role never falls back to a tier-2 column that a variadic family of
       the spec takes at tier 0 or 1: in wide data such as `month, Shoes, Hats`
       for `x`, `y1, y2, ...` and `category`, an integer series column stays a
       series instead of becoming the category; a column of years named so is no
       series, so the category may take it.

    Each column is bound at most once. Members of a family are numbered `<name>1`,
    `<name>2`, ... in column order. Roles without kinds stay unbound.
    """
    columns = profile.columns
    used: set[str] = set()
    single: dict[str, str] = {}
    family: dict[str, list[ColumnProfile]] = {role.name: [] for role in roles if role.variadic}
    families = [role for role in roles if role.variadic and role.kinds]
    weak = weak_measures(profile)
    # A column of years named so is a time key, never a series of a number family: a single role may take it.
    # A weak measure the family leaves out stays reserved too: `Dauer (Minuten)` or a constant `target` is no
    # series label (review of 2026-10-15).
    reserved = {
        column.name
        for column in columns
        for owner in families
        if (tier := _tier(owner, column)) is not None and tier <= 1 and year_score(column) < 2
    }

    # A constant is no measure even when named like the role (`y2`, `size`); a year or a month named so is meant.
    constants = {column.name for column in columns if profile.rows >= MIN_CONSTANT_ROWS and column.unique <= 1}

    for role in roles:
        if not role.kinds:
            continue
        named = [column for column in columns if not (is_measure(role) and column.name in constants)]
        if role.variadic:
            for column in named:
                if column.name not in used and _member_of(role, column.name) and _tier(role, column) is not None:
                    if len(family[role.name]) < MAX_VARIADIC_DEFAULT:
                        family[role.name].append(column)
                        used.add(column.name)
        else:
            for column in named:
                if (
                    column.name not in used
                    and _norm(column.name) == _norm(role.name)
                    and _tier(role, column) is not None
                ):
                    single[role.name] = column.name
                    used.add(column.name)
                    break

    # A role the plot can compute takes a column only on a clear name match (`SMA 20` for `sma`), before any
    # other role ranks the columns: otherwise it stays open and the plot computes it (`data/computed.py`).
    for role in roles:
        if not role.computed or not role.kinds or role.variadic or role.name in single:
            continue
        for column in columns:
            if (
                column.name not in used
                and column.name not in constants
                and _tier(role, column) is not None
                and name_match(role, column.name)
            ):
                single[role.name] = column.name
                used.add(column.name)
                break

    order = sorted(
        (role for role in roles if role.kinds and not role.computed),
        key=lambda role: (not role.required, role.variadic),  # stable: spec order inside each group
    )
    for role in order:
        if role.variadic:
            members = family[role.name]
            fitting = sorted(
                (tier, position)
                for position, column in enumerate(columns)
                if column.name not in used and (tier := _tier(role, column)) is not None and tier <= 1
            )
            ranked_members = [(tier, position) for tier, position in fitting if columns[position].name not in weak]
            if not members and not ranked_members and role.required:
                ranked_members = fitting[:1]  # one weak member rather than none for a required family
            for _, position in ranked_members[: max(0, MAX_VARIADIC_DEFAULT - len(members))]:
                members.append(columns[position])
                used.add(columns[position].name)
        elif role.name not in single:
            # An axis (`x`) only skips constants: a month, a rank or a year is a fine independent variable.
            avoid = (constants if is_axis(role) else weak) if is_measure(role) else set()
            ranked = sorted(
                (
                    _constant_group(role, column),
                    column.name in avoid,
                    _category_rank(role, column),
                    tier,
                    -_rounded_similarity(role.name, column.name),
                    _code_rank(role, column, columns),
                    _year_rank(role, column),
                    position,
                    column.name,
                )
                for position, column in enumerate(columns)
                if column.name not in used
                and (tier := _tier(role, column)) is not None
                and (tier <= 1 or column.name not in reserved)
                and (role.required or column.name not in avoid)
            )
            if ranked:
                single[role.name] = ranked[0][-1]
                used.add(ranked[0][-1])

    position_of = {column.name: position for position, column in enumerate(columns)}
    bindings: list[Binding] = []
    for role in roles:
        if role.variadic:
            members = sorted(family[role.name], key=lambda column: position_of[column.name])
            bindings.extend(Binding(role=role.member(n), column=column.name) for n, column in enumerate(members, 1))
        elif role.name in single:
            bindings.append(Binding(role=role.name, column=single[role.name]))
    return bindings


def carry_bindings(
    bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile, previous: DatasetProfile | None = None
) -> list[Binding]:
    """The bindings after the dataset changed under them (`prepare_data`, undo): the valid ones stay.

    A binding stays when its column is still in `profile` with a dtype its role accepts
    (`check_bindings` on it alone finds no error). When every binding stayed, nothing
    changes, so a role the user left unbound stays unbound, with one exception: a date
    column the change made (`make_date`, or `set_type` to a date; a datetime column that
    `previous`, the version before, did not have) fills an open required role that takes
    dates (owner decision of 2026-10-15: the code binds it, not the model). When a binding
    went (its column dropped, renamed or re-typed), the roles without a binding are bound
    as `default_bindings` would bind them on the columns no kept binding uses: the
    defaults are computed on that reduced view, so a role whose first choice a kept
    binding holds takes its next candidate rather than staying open. A family keeps
    its members and gains the defaults' members under the next free numbers. The
    result is in the order the defaults list them.
    """
    kept = [binding for binding in bindings if not check_bindings([binding], roles, profile).errors]
    if len(kept) == len(bindings):
        dated = _new_dates(kept, roles, profile, previous)
        return _in_spec_order([*kept, *dated], roles, profile) if dated else list(bindings)
    used = {binding.column for binding in kept}
    taken = {binding.role for binding in kept}
    open_roles = [role for role in roles if role.variadic or role.name not in taken]
    free = profile.model_copy(update={"columns": [column for column in profile.columns if column.name not in used]})
    for binding in default_bindings(open_roles, free):
        role = resolve_role(binding.role, roles)
        if role is not None and role.variadic:
            number = next(n for n in itertools.count(1) if role.member(n) not in taken)
            binding = Binding(role=role.member(number), column=binding.column)
        taken.add(binding.role)
        kept.append(binding)
    return _in_spec_order(kept, roles, profile)


def _new_dates(
    kept: list[Binding], roles: list[DataRole], profile: DatasetProfile, previous: DatasetProfile | None
) -> list[Binding]:
    """Bindings of the open required roles that take dates to the date columns `previous` did not have."""
    if previous is None:
        return []
    before = {column.name for column in previous.columns if column.dtype == "datetime"}
    used = {binding.column for binding in kept}
    taken = {binding.role for binding in kept}
    fresh = [
        column
        for column in profile.columns
        if column.dtype == "datetime" and column.name not in before and column.name not in used
    ]
    added: list[Binding] = []
    for role in roles:
        if not fresh or not role.required or role.variadic or role.computed or role.name in taken:
            continue
        if "datetime" in role.kinds:
            column = max(fresh, key=lambda column: name_similarity(role.name, column.name))  # first on a tie
            fresh.remove(column)
            added.append(Binding(role=role.name, column=column.name))
    return added


def _in_spec_order(bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile) -> list[Binding]:
    """In the order the defaults list them: the spec's roles, a family's members by column position."""
    role_order = {role.name: position for position, role in enumerate(roles)}
    column_order = {column.name: position for position, column in enumerate(profile.columns)}

    def place(binding: Binding) -> tuple[int, int]:
        role = resolve_role(binding.role, roles)
        return role_order.get(role.name if role else "", len(roles)), column_order.get(binding.column, 0)

    return sorted(bindings, key=place)


def check_bindings(bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile) -> BindingCheck:
    """Validate bindings against the spec's roles and the dataset's columns.

    Errors: an unknown role (a variadic family is bound through its members
    `<name><n>`, never its bare name), a role bound twice, a column missing from the
    profile, a column bound twice, a dtype the role's kinds do not accept (see
    `ACCEPTS`). `missing_roles` lists the required roles without a binding, except a role
    the plot can compute (`DataRole.computed`: bound, the plot uses the column; open, it
    computes the value); a
    required variadic family needs at least one member. `warnings`: a valid binding of
    a non-negative role to a column with a negative value (`signs.sign_line`), and an
    unbound non-negative role whose every fitting column that no other role holds has one.
    """
    columns = {column.name: column for column in profile.columns}
    errors: list[str] = []
    warnings: list[str] = []
    seen_roles: set[str] = set()
    seen_columns: set[str] = set()
    bound: set[str] = set()
    for binding in bindings:
        role = resolve_role(binding.role, roles)
        if role is None:
            family = next((r for r in roles if r.variadic and r.name == binding.role), None)
            if family is not None:
                errors.append(f"role '{binding.role}' takes numbered members such as '{family.member(1)}'")
            else:
                errors.append(f"unknown role '{binding.role}'")
        if binding.role in seen_roles:
            errors.append(f"role '{binding.role}' is bound more than once")
        seen_roles.add(binding.role)
        column = columns.get(binding.column)
        if column is None:
            errors.append(f"column '{binding.column}' is not in the dataset")
        elif binding.column in seen_columns:
            errors.append(f"column '{binding.column}' is bound more than once")
        seen_columns.add(binding.column)
        if role is None or column is None:
            continue
        if not accepts(role, column.dtype):
            wanted = " or ".join(role.kinds)
            errors.append(f"role '{binding.role}' needs {wanted} data, but column '{column.name}' is {column.dtype}")
            continue
        bound.add(role.name)
        if role.non_negative and has_negative(column):
            warnings.append(sign_line(binding.role, column))
    # An open non-negative role whose only fitting free columns are negative says why it stayed open;
    # a column another role holds is no candidate, as in `default_bindings`.
    for role in roles:
        if not role.non_negative or role.variadic or role.computed or role.name in seen_roles:
            continue
        fitting = [
            column
            for column in profile.columns
            if column.name not in seen_columns and role.kinds and accepts(role, column.dtype)
        ]
        if fitting and all(has_negative(column) for column in fitting):
            names = ", ".join(f"'{column.name}'" for column in fitting[:3])
            warnings.append(
                f"{role.name}: not bound, because every column that fits it ({names}) has negative values; "
                "this role needs values of 0 or more"
            )
    missing = [role.name for role in roles if role.required and not role.computed and role.name not in bound]
    return BindingCheck(complete=not errors and not missing, errors=errors, missing_roles=missing, warnings=warnings)


def resolve_role(name: str, roles: list[DataRole]) -> DataRole | None:
    """The role a binding name refers to: an exact single role, else the variadic family with the longest prefix."""
    for role in roles:
        if not role.variadic and role.name == name:
            return role
    families = [role for role in roles if role.variadic and _member_of(role, name)]
    return max(families, key=lambda role: len(role.name), default=None)


def accepts(role: DataRole, dtype: ColumnDtype) -> bool:
    """Whether a column of `dtype` may be bound to `role` (a role without kinds accepts any column)."""
    return not role.kinds or any(dtype in ACCEPTS[kind] for kind in role.kinds)


def name_similarity(role_name: str, column_name: str) -> float:
    """0 to 1: exact after normalising case and punctuation, containment, token overlap, or edit ratio."""
    a, b = _norm(role_name), _norm(column_name)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    contained = 0.8 if (len(a) >= 3 and a in b) or (len(b) >= 3 and b in a) else 0.0
    tokens_a, tokens_b = _tokens(role_name), _tokens(column_name)
    overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b) if tokens_a and tokens_b else 0.0
    ratio = SequenceMatcher(None, a, b).ratio() * 0.9
    return max(contained, overlap, ratio)


def _member_of(role: DataRole, name: str) -> bool:
    """`name` is `<role.name><n>` with n a positive integer without leading zeros."""
    if not role.variadic or not name.startswith(role.name):
        return False
    index = name[len(role.name) :]
    return index.isascii() and index.isdigit() and not index.startswith("0")


def _tier(role: DataRole, column: ColumnProfile) -> int | None:
    """The column's rank as a default for `role`, or None: an incompatible dtype, or a negative value for a non-negative role."""
    if role.non_negative and has_negative(column):
        return None
    tiers = [ACCEPTS[kind][column.dtype] for kind in role.kinds if column.dtype in ACCEPTS[kind]]
    return min(tiers) if tiers else None


def _constant_group(role: DataRole, column: ColumnProfile) -> bool:
    """Whether `column` holds at most one distinct value and `role` groups or labels by its values.

    A categorical, text or boolean role (a series, a category, a label) split by a column
    with one value draws one group, so such a column ranks after every column with two or
    more values: `Kanton` holding only "Schweiz" never becomes the series while
    `Staatsangehörigkeit` has two values. Number and date roles keep their order.
    """
    return column.unique <= 1 and any(kind in GROUPING_KINDS for kind in role.kinds)


def year_score(column: ColumnProfile) -> int:
    """2 for an integer column of years named so (`Jahr`, `year`), 1 for an unnamed run of whole years, else 0.

    Values count as years when all lie within `YEAR_RANGE` and span at most `MAX_YEAR_SPAN`.
    Without a year name that is not enough (review of 2026-10-15: prices, rents or calories of
    1000 to 2200 look the same): the column must also hold every year of its range, at least
    three (`unique == max - min + 1`), as a yearly series does, in a wide or a long table.
    """
    if column.dtype != "integer" or not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return 0
    low, high = YEAR_RANGE
    if not (low <= column.min and column.max <= high and column.max - column.min <= MAX_YEAR_SPAN):
        return 0
    if YEAR_WORDS & set(_WORDS.findall(column.name.casefold())):
        return 2
    return 1 if column.unique >= 3 and column.unique == int(column.max - column.min) + 1 else 0


def numeric_text(column: ColumnProfile) -> bool:
    """A text column whose frequent values all read as numbers or dates (`7.184.003` the parse could not type)."""
    return column.dtype == "text" and bool(column.top) and all(value_like(value) for value in column.top)


def _category_rank(role: DataRole, column: ColumnProfile) -> int:
    """The rank of `column` as a category, group or label for a role of grouping kinds only; 0 for every other role.

    A live test of 2026-10-15 bound `Bevölkerung`, a text column of 24 numbers the parse had
    not typed, as the category of a bar chart and the year as its value. For a role that
    groups or labels (and accepts no number or date), the candidates rank:

    0. a real text or boolean column of 2 to `MAX_CATEGORIES` distinct values;
    1. an integer column of years named so, then 2. one whose values look like years;
    3. a text column with more distinct values;
    4. an ordinal integer column, every value of a short range (`Quartal` 1 to 4, `_ordinal`);
    5. another integer column of at most `MAX_CATEGORIES` distinct values;
    6. a text column of numbers (`numeric_text`), then 7. any other integer column (a measure).
    """
    if not role.kinds or any(kind not in GROUPING_KINDS for kind in role.kinds):
        return 0
    if column.dtype in ("text", "boolean") and not numeric_text(column):
        return 0 if column.unique <= MAX_CATEGORIES else 3
    if column.dtype == "integer":
        score = year_score(column)
        if score:
            return 3 - score
        if _ordinal(column):
            return 4
        return 5 if column.unique <= MAX_CATEGORIES else 7
    return 6


def _ordinal(column: ColumnProfile) -> bool:
    """An integer column that numbers steps (`Quartal` 1 to 4, `Monat` 1 to 12): every value of a short range."""
    if not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return False
    span = int(column.max - column.min) + 1
    return 2 <= column.unique == span <= MAX_CATEGORIES


def _year_rank(role: DataRole, column: ColumnProfile) -> int:
    """For a number role, years last: the value of a bar or a y is a measure, not the year (live test of 2026-10-15).

    A role that also takes dates (`x (datetime/numeric)`) is a time axis, and so is an axis
    role (`is_axis`, review of 2026-10-15): years rank first among the number columns
    there. Every other role keeps its order (0).
    """
    if "numeric" not in role.kinds:
        return 0
    score = year_score(column)
    return -score if "datetime" in role.kinds or is_axis(role) else score


def is_measure(role: DataRole) -> bool:
    """A role whose values are measured amounts (`y`, `value`, `size`): it takes numbers and no dates."""
    return "numeric" in role.kinds and "datetime" not in role.kinds


def is_axis(role: DataRole) -> bool:
    """The independent axis of a number plot (`x`, `x_values`): a month, a rank or a year is a fine x.

    It skips only constants by default, never a weak measure such as `Month` (scatter of
    `Month, Temperature`: x is the month, review of 2026-10-15).
    """
    return role.name == "x" or role.name.startswith("x_")


def date_part(column: ColumnProfile, *, has_year: bool) -> bool:
    """An integer column that numbers a month, a quarter or a week of the year.

    Named so (`Month`, `Monat`, `Quartal`, `Woche`, `DATE_PART_WORDS`) and within that
    part's range, or, beside a column of years (`has_year`), every value from 1 to 12 or
    from 1 to 4 (live test of 2026-10-15: the `Month` of a MeteoSwiss table of `Year`,
    `Month`, `Temperature` was bound as the value of a time series). Durations and units
    (`Months since start` up to 36, `Dauer (Minuten)`, a `kW` column) are measures.
    """
    if column.dtype != "integer" or not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return False
    words = _WORDS.findall(_CAMEL.sub(" ", column.name).casefold())
    highest = max((DATE_PART_WORDS.get(word, 0) for word in words), default=0)
    if highest and 1 <= column.min and column.max <= highest:
        return True
    return has_year and column.min == 1 and column.max in (4, 12) and column.unique == column.max


def weak_measures(profile: DatasetProfile) -> set[str]:
    """The columns that are no measure, although they hold numbers: a constant, years, or a part of a date.

    A measure role (`is_measure`) ranks them after every other fitting column, an optional
    one never takes them, and a number family takes them only when it would otherwise stay
    empty: a column with one distinct value draws a flat line (live test of 2026-10-15:
    `decimal`, all 0, bound as `y2` of a World Bank table), and a year or a month is where
    a value sits, not the value. A column is constant only in a table of at least
    `MIN_CONSTANT_ROWS` rows: two equal values in a two-row table say little.
    """
    columns = profile.columns
    has_year = any(year_score(column) for column in columns)
    constant = profile.rows >= MIN_CONSTANT_ROWS
    return {
        column.name
        for column in columns
        if column.dtype in ("integer", "number")
        and ((constant and column.unique <= 1) or year_score(column) or date_part(column, has_year=has_year))
    }


def _code_like(column: ColumnProfile) -> bool:
    """A text column of codes: named so (`country.id`, `iso3code`), or its frequent values are short capitals (`AT`, `CHE`)."""
    if column.dtype != "text":
        return False
    words = set(_WORDS.findall(_CAMEL.sub(" ", column.name).casefold()))
    if words & CODE_WORDS or any(word.endswith("code") for word in words):
        return True
    return bool(column.top) and all(_CODE_VALUE.fullmatch(value) for value in column.top if isinstance(value, str))


def _code_rank(role: DataRole, column: ColumnProfile, columns: list[ColumnProfile]) -> int:
    """1 for a column of codes beside its name column; else 0.

    Only for a role of grouping kinds (a series, a category, a label): the legend and the
    axis read `Austria` better than `AT` (live test of 2026-10-15, a World Bank table with
    `country.id` and `country.value`). The name column must be related by its name, the
    same stem once the code and name words are taken off (`country.id` and `country.value`,
    `product_code` and `product_name`, `countryiso3code` and `country`), and partition the
    rows the same way, as far as the profile tells: the same number of distinct values and
    of missing cells. Equal counts alone are no relation (`Status` and `Line`, review of
    2026-10-15). The rank comes after name similarity, so a role named like the code column
    keeps it unless the name column is as similar.
    """
    if not role.kinds or any(kind not in GROUPING_KINDS for kind in role.kinds) or not _code_like(column):
        return 0
    stem = _stem(column.name, CODE_WORDS)
    twin = any(
        other.name != column.name
        and other.dtype == "text"
        and not numeric_text(other)
        and not _code_like(other)
        and other.unique == column.unique
        and other.missing == column.missing
        and _related(stem, _stem(other.name, NAME_WORDS))
        for other in columns
    )
    return 1 if twin else 0


def _stem(name: str, drop: frozenset[str]) -> str:
    """A column name without its code or name words, normalised: `country.id` is `country`, `iso3code` `iso3`."""
    words = _WORDS.findall(_CAMEL.sub(" ", name).casefold())
    kept = [word.removesuffix("code") for word in words if word not in drop]
    return _norm("".join(kept))


def _related(code_stem: str, name_stem: str) -> bool:
    """Two stems of at least three characters, one inside the other (`countryiso3` holds `country`)."""
    if len(code_stem) < 3 or len(name_stem) < 3:
        return False
    return code_stem in name_stem or name_stem in code_stem


def _rounded_similarity(role_name: str, column_name: str) -> float:
    similarity = name_similarity(role_name, column_name)
    return round(similarity, 2) if similarity >= MIN_NAME_SIMILARITY else 0.0


def _norm(name: str) -> str:
    return _NOT_ALNUM.sub("", name.casefold())


def _tokens(name: str) -> set[str]:
    return {token for token in _NOT_ALNUM.split(_CAMEL.sub(" ", name).casefold()) if token}
