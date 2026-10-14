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

_NOT_ALNUM = re.compile(r"[^0-9a-z]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


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
       (single-valued, tier, name similarity, column position): for a categorical,
       text or boolean role a column with one distinct value ranks after every
       column with two or more (`_constant_group`). A variadic family takes every
       unused tier-0 or tier-1 column in column order, up to `MAX_VARIADIC_DEFAULT`.
       A single role never falls back to a tier-2 column that a variadic family of
       the spec takes at tier 0 or 1: in wide data such as `month, Shoes, Hats`
       for `x`, `y1, y2, ...` and `category`, an integer series column stays a
       series instead of becoming the category.

    Each column is bound at most once. Members of a family are numbered `<name>1`,
    `<name>2`, ... in column order. Roles without kinds stay unbound.
    """
    columns = profile.columns
    used: set[str] = set()
    single: dict[str, str] = {}
    family: dict[str, list[ColumnProfile]] = {role.name: [] for role in roles if role.variadic}
    families = [role for role in roles if role.variadic and role.kinds]
    reserved = {
        column.name
        for column in columns
        for owner in families
        if (tier := _tier(owner, column)) is not None and tier <= 1
    }

    for role in roles:
        if not role.kinds:
            continue
        if role.variadic:
            for column in columns:
                if column.name not in used and _member_of(role, column.name) and _tier(role, column) is not None:
                    if len(family[role.name]) < MAX_VARIADIC_DEFAULT:
                        family[role.name].append(column)
                        used.add(column.name)
        else:
            for column in columns:
                if (
                    column.name not in used
                    and _norm(column.name) == _norm(role.name)
                    and _tier(role, column) is not None
                ):
                    single[role.name] = column.name
                    used.add(column.name)
                    break

    order = sorted(
        (role for role in roles if role.kinds),
        key=lambda role: (not role.required, role.variadic),  # stable: spec order inside each group
    )
    for role in order:
        if role.variadic:
            members = family[role.name]
            ranked_members = sorted(
                (tier, position)
                for position, column in enumerate(columns)
                if column.name not in used and (tier := _tier(role, column)) is not None and tier <= 1
            )
            for _, position in ranked_members[: max(0, MAX_VARIADIC_DEFAULT - len(members))]:
                members.append(columns[position])
                used.add(columns[position].name)
        elif role.name not in single:
            ranked = sorted(
                (
                    _constant_group(role, column),
                    tier,
                    -_rounded_similarity(role.name, column.name),
                    position,
                    column.name,
                )
                for position, column in enumerate(columns)
                if column.name not in used
                and (tier := _tier(role, column)) is not None
                and (tier <= 1 or column.name not in reserved)
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


def carry_bindings(bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile) -> list[Binding]:
    """The bindings after the dataset changed under them (`prepare_data`, undo): the valid ones stay.

    A binding stays when its column is still in `profile` with a dtype its role accepts
    (`check_bindings` on it alone finds no error). When every binding stayed, nothing
    changes, so a role the user left unbound stays unbound. When one went (its column
    dropped, renamed or re-typed), the roles without a binding are bound as
    `default_bindings` would bind them on the columns no kept binding uses: the
    defaults are computed on that reduced view, so a role whose first choice a kept
    binding holds takes its next candidate rather than staying open. A family keeps
    its members and gains the defaults' members under the next free numbers. The
    result is in the order the defaults list them.
    """
    kept = [binding for binding in bindings if not check_bindings([binding], roles, profile).errors]
    if len(kept) == len(bindings):
        return list(bindings)
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
    # In the order the defaults list them: the spec's roles, a family's members by column position.
    role_order = {role.name: position for position, role in enumerate(roles)}
    column_order = {column.name: position for position, column in enumerate(profile.columns)}

    def place(binding: Binding) -> tuple[int, int]:
        role = resolve_role(binding.role, roles)
        return role_order.get(role.name if role else "", len(roles)), column_order.get(binding.column, 0)

    return sorted(kept, key=place)


def check_bindings(bindings: list[Binding], roles: list[DataRole], profile: DatasetProfile) -> BindingCheck:
    """Validate bindings against the spec's roles and the dataset's columns.

    Errors: an unknown role (a variadic family is bound through its members
    `<name><n>`, never its bare name), a role bound twice, a column missing from the
    profile, a column bound twice, a dtype the role's kinds do not accept (see
    `ACCEPTS`). `missing_roles` lists the required roles without a binding; a
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
        if not role.non_negative or role.variadic or role.name in seen_roles:
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
    missing = [role.name for role in roles if role.required and role.name not in bound]
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


def _rounded_similarity(role_name: str, column_name: str) -> float:
    similarity = name_similarity(role_name, column_name)
    return round(similarity, 2) if similarity >= MIN_NAME_SIMILARITY else 0.0


def _norm(name: str) -> str:
    return _NOT_ALNUM.sub("", name.casefold())


def _tokens(name: str) -> set[str]:
    return {token for token in _NOT_ALNUM.split(_CAMEL.sub(" ", name).casefold()) if token}
