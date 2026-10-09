"""Data roles from a spec's stored `## Data` bullets.

The input is `Spec.data` (core/database/models.py): the `## Data` bullets as
`automation/scripts/sync_to_postgres.py` stores them, one string per `- ` or `* `
line with the marker stripped (nested bullets arrive flattened, continuation lines
are lost). No ADK import. The parser never raises; a bullet it cannot read as a
role is skipped.

A role bullet starts with backticked names, optionally a parenthesised type, then
a separator (`-`, `–`, `—` or `:`) and a description:

    `x` (numeric) - Independent variable values
    `x` (datetime/numeric) - continuous axis values
    `start_name`, `end_name` (string) - two roles sharing type and description
    `price` or `value` (numeric) - alternatives: one role, named by the first name
    `y1, y2, y3, ...` (numeric) - a variadic family `y`: members `y1`, `y2`, ...
    `y_1`, `y_2`, ... (numeric) - a variadic family `y_`: members `y_1`, `y_2`, ...
    `variable_1` through `variable_n` (numeric) - a variadic family `variable_`
    `y1_lower, y1_upper, ...` (numeric) - two variadic families, `y_lower` and `y_upper`

A variadic family is named by its first member with the last run of digits (or the
trailing `n` after `through`) removed, so the members are always `<name><n>` with
n = 1, 2, ...; a family whose index sat mid-name (`y1_lower`) therefore numbers its
members at the end (`y_lower1`). Bullets that do not start with a backtick are not
roles: `Size:`, `Example:`, `Note:`, `Constraint:`, and `Derived `x`` (a value the
plot computes, not a column). The one exception is a bold label ending in
"variable" or "column" (`**X variable**: Continuous variable (often time)`), used
by three specs; it becomes the role `x`, and its kinds come from type words in the
label and the description.

Kinds come from the words inside the type parentheses (backticked text in them is
ignored): `TYPE_WORDS` maps a word to a `RoleKind`; words in `QUALIFIER_WORDS`
(`optional`, `array`, `list of`, ...) carry no type. When the parentheses hold no
type word but other words (`dict`, `list of tuples`, `geometry`), the role's kind
is `text`; when they hold nothing typed at all (`(2D array)`, `(list)`) or are
missing, the role has no kinds and default bindings leave it unbound.

A role is optional when the word "optional" appears in its type parentheses or its
description; otherwise it is required. Names are made to satisfy `ROLE_PATTERN`
(characters outside `[A-Za-z0-9_]` become `_`, at most 32 characters, 30 for a
variadic family so its members up to `<name>50` still fit, a leading `_` before a
digit); a name without a letter or digit, or one already taken by an earlier
bullet, is skipped, so names are unique.
"""

import re
from dataclasses import dataclass
from typing import Literal

from ..schemas import ROLE_PATTERN


RoleKind = Literal["numeric", "categorical", "datetime", "text", "boolean"]

MAX_ROLE_NAME_CHARS = 32
MAX_VARIADIC_NAME_CHARS = 30

TYPE_WORDS: dict[str, RoleKind] = {
    "numeric": "numeric",
    "numerical": "numeric",
    "number": "numeric",
    "numbers": "numeric",
    "float": "numeric",
    "floats": "numeric",
    "double": "numeric",
    "int": "numeric",
    "ints": "numeric",
    "integer": "numeric",
    "integers": "numeric",
    "continuous": "numeric",
    "count": "numeric",
    "counts": "numeric",
    "categorical": "categorical",
    "category": "categorical",
    "categories": "categorical",
    "ordinal": "categorical",
    "nominal": "categorical",
    "datetime": "datetime",
    "date": "datetime",
    "dates": "datetime",
    "time": "datetime",
    "timestamp": "datetime",
    "timestamps": "datetime",
    "string": "text",
    "strings": "text",
    "str": "text",
    "text": "text",
    "label": "text",
    "labels": "text",
    "boolean": "boolean",
    "bool": "boolean",
    "binary": "boolean",
}

QUALIFIER_WORDS: frozenset[str] = frozenset(
    {
        "optional",
        "required",
        "array",
        "arrays",
        "list",
        "lists",
        "of",
        "or",
        "and",
        "d",  # the letter left from "1D", "2D"
        "matrix",
        "pair",
        "pairs",
        "column",
        "columns",
        "metadata",
        "ordered",
    }
)

# Possessive quantifiers (`*+`, `++`) and the run-start lookbehinds keep every
# pattern linear in the bullet length: nothing after a whitespace or digit run
# can match inside that run, so there is never anything to backtrack into.
_HEAD_TOKEN = re.compile(
    r"\s*+(?:`(?P<code>[^`]++)`|(?P<more>\.\.\.|…)|(?P<range>through|to)\b|(?P<alt>or)\b|(?P<sep>,|/|and\b))",
    re.IGNORECASE,
)
_TAIL = re.compile(r"\s*+(?:\((?P<type>[^)]*+)\))?\s*+(?:[-–—:]++\s*+)?(?P<desc>.*)", re.DOTALL)
_BOLD = re.compile(r"\*\*(?P<label>[^*]++)\*\*\s*+[-–—:]?\s*+(?P<desc>.*)", re.DOTALL)
_BOLD_LABEL_END = re.compile(r"(?<!\s)\s++(?:variable|variables|column|columns)$", re.IGNORECASE)
_LAST_DIGITS = re.compile(r"[0-9]+(?=[^0-9]*$)")
_OPTIONAL = re.compile(r"\boptional\b", re.IGNORECASE)
_WORD = re.compile(r"[a-z]+")
_BACKTICKED = re.compile(r"`[^`]*`")
_INVALID_NAME_CHARS = re.compile(r"[^A-Za-z0-9_]+")
_ROLE_NAME = re.compile(ROLE_PATTERN)


@dataclass(frozen=True)
class DataRole:
    """One data role a spec declares; `variadic` roles bind `<name>1`, `<name>2`, ..."""

    name: str
    kinds: tuple[RoleKind, ...]
    required: bool
    variadic: bool
    description: str

    def member(self, index: int) -> str:
        """The binding role name of the `index`-th (1-based) column of a variadic family."""
        return f"{self.name}{index}"


def parse_roles(data_bullets: list[str]) -> list[DataRole]:
    """The roles declared by a spec's stored `## Data` bullets, in bullet order."""
    roles: list[DataRole] = []
    taken: set[str] = set()
    for bullet in data_bullets:
        for role in _parse_bullet(bullet.strip()):
            if role.name not in taken:
                taken.add(role.name)
                roles.append(role)
    return roles


def type_words(type_text: str) -> tuple[tuple[RoleKind, ...], list[str]]:
    """Kinds from the text inside a bullet's type parentheses, plus the unknown words that made it `text`."""
    words = _WORD.findall(_BACKTICKED.sub(" ", type_text).lower())
    kinds = _ordered_kinds(words)
    if kinds:
        return kinds, []
    unknown = [word for word in words if word not in QUALIFIER_WORDS]
    return (("text",), unknown) if unknown else ((), [])


def _ordered_kinds(words: list[str]) -> tuple[RoleKind, ...]:
    kinds: list[RoleKind] = []
    for word in words:
        kind = TYPE_WORDS.get(word)
        if kind is not None and kind not in kinds:
            kinds.append(kind)
    return tuple(kinds)


def _parse_bullet(bullet: str) -> list[DataRole]:
    if bullet.startswith("**"):
        return _parse_bold(bullet)
    if not bullet.startswith("`"):
        return []

    names: list[str] = []
    more = through = alternative = False
    position = end = 0
    while match := _HEAD_TOKEN.match(bullet, position):
        position = match.end()
        if match.group("code") is not None:
            for item in match.group("code").split(","):
                item = item.strip()
                if item in ("...", "…"):
                    more = True
                elif item:
                    names.append(item)
            end = position
        elif match.group("more"):
            more, end = True, position
        elif match.group("range"):
            through = True
        elif match.group("alt"):
            alternative = True
    tail = _TAIL.match(bullet, end)  # every group is optional, so it always matches
    type_text = (tail.group("type") or "") if tail else ""
    description = (tail.group("desc") if tail else "").strip()
    kinds, _ = type_words(type_text)
    required = not _OPTIONAL.search(f"{type_text} {description}")

    def role(name: str, variadic: bool = False) -> DataRole | None:
        clean = _clean_name(name, MAX_VARIADIC_NAME_CHARS if variadic else MAX_ROLE_NAME_CHARS)
        if clean is None:
            return None
        return DataRole(name=clean, kinds=kinds, required=required, variadic=variadic, description=description)

    candidates: list[DataRole | None] = []
    if through and len(names) >= 2 and (family := _range_family(names[0])):
        candidates.append(role(family, variadic=True))
    elif more:
        families: list[str] = []
        for name in names:
            family = _LAST_DIGITS.sub("", name, count=1)
            if family == name:
                candidates.append(role(name))
            elif family and family not in families:
                families.append(family)
        candidates.extend(role(family, variadic=True) for family in families)
    elif alternative and names:
        candidates.append(role(names[0]))
    else:
        candidates.extend(role(name) for name in names)
    return [candidate for candidate in candidates if candidate is not None]


def _range_family(name: str) -> str | None:
    """The family a range start such as `y1` or `yn` belongs to (`y`); None when the name has no index.

    A trailing digit run is the index, else a trailing `n`; an empty family (`1`, `n`)
    is no family. Plain string operations keep this linear in the name length.
    """
    family = name.rstrip("0123456789")
    if family == name:
        family = name[:-1] if name.endswith("n") else ""
    return family or None


def _parse_bold(bullet: str) -> list[DataRole]:
    match = _BOLD.fullmatch(bullet)
    if not match or not _BOLD_LABEL_END.search(match.group("label").strip()):
        return []
    label = _BOLD_LABEL_END.sub("", match.group("label").strip())
    description = match.group("desc").strip()
    name = _clean_name("_".join(_WORD.findall(label.lower())), MAX_ROLE_NAME_CHARS)
    if name is None:
        return []
    kinds = _ordered_kinds(_WORD.findall(f"{label} {description}".lower()))
    required = not _OPTIONAL.search(description)
    return [DataRole(name=name, kinds=kinds, required=required, variadic=False, description=description)]


def _clean_name(name: str, limit: int) -> str | None:
    clean = _INVALID_NAME_CHARS.sub("_", name.strip())
    if clean[:1].isdigit():
        clean = f"_{clean}"
    clean = clean[:limit]
    if not any(char.isalnum() for char in clean):
        return None
    return clean if _ROLE_NAME.fullmatch(clean) else None
