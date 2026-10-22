"""Data roles from a spec's stored `## Data` bullets, and the data shape they imply.

The input is `Spec.data` (core/database/models.py): the `## Data` bullets as
`automation/scripts/sync_to_postgres.py` stores them, one string per `- ` or `* `
line with the marker stripped (nested bullets arrive flattened, continuation lines
are lost); `data_bullets` extracts the same list from a `specification.md`. The
parser never raises; a bullet it cannot read as a role is skipped.

The module is shared by the agent (bindings, session state) and the adaptability
checker (`core/adaptability.py`), and it uses the standard library only: the
checker's single-file mirror, `automation/scripts/adaptability_check.py`, carries
a verbatim copy of it for the workflow runner's system Python
(`core/adaptability_mirror.py` builds that file).

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

The data shape (`spec_shape`, docs/concepts/adaptable-code.md "Data shapes")
decides what the adaptable form of an implementation holds, in this order:

* `excluded`: the 13 map specs (`MAP_SPECS`), which fetch geometry over the network.
* An entry of `SHAPE_OVERRIDES`: a spec whose role bullets misfile it, with the reason.
* `network`: a role named `nodes` or `edges` (`STRUCTURE_ROLES`). `df` is the edge
  list, a second `nodes` table holds node attributes.
* `matrix`: a role whose name contains `matrix`. `df` is a labeled square DataFrame.
* `generated`: no role carries a numeric, categorical, datetime or boolean kind (only
  text or untyped roles: encoded text, puzzle grids). The block holds parameters.
* `table`, the default: every role is a column of one table.

The colour-driving role (`color_role`) is the first categorical or text role whose
name is one of `COLOR_ROLE_NAMES` or whose description names a colour encoding
(`COLOR_WORDS`). A spec without one is a single-series plot as far as the palette
rule is concerned. The rule favours precision: a pie's `category` ("category
labels") is not detected, so the palette rule stays lenient there.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


# A role is matched against the spec's `## Data` bullets later; the pattern only keeps
# arbitrary text out. Digits and capitals are allowed because 21 of 325 specs name
# roles such as `log2_fold_change`, `lower_95` or `temperature_K`.
ROLE_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]{0,31}$"

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
_DIGITS = frozenset("0123456789")
_OPTIONAL = re.compile(r"\boptional\b", re.IGNORECASE)
_WORD = re.compile(r"[a-z]+")
_BACKTICKED = re.compile(r"`[^`]*`")
_INVALID_NAME_CHARS = re.compile(r"[^A-Za-z0-9_]+")
_ROLE_NAME = re.compile(ROLE_PATTERN)
COMPUTED = re.compile(r"(?:computed|calculated|derived)\b", re.IGNORECASE)
"""A description that starts so names a value the plot computes from the other roles (`rolling_avg` of
`line-timeseries-rolling`: "Computed rolling average (e.g., 7-day, 30-day window)"). Only the start counts:
"values computed as x(t)" or "used to compute distances" describe data. A spec opts a role in by its wording."""


@dataclass(frozen=True)
class DataRole:
    """One data role a spec declares; `variadic` roles bind `<name>1`, `<name>2`, ..."""

    name: str
    kinds: tuple[RoleKind, ...]
    required: bool
    variadic: bool
    description: str
    non_negative: bool = False
    """Whether the role needs values of 0 or more: set per spec by `signs.mark_non_negative`, never parsed."""
    computed: bool = False
    """Whether the plot can compute the role from the data (`rolling_avg`: "Computed rolling average ...", by
    `COMPUTED`, or listed in `computed.COMPUTED_ROLES`): optional, bound when a column holds it, else the adapter
    computes it (owner decision of 2026-10-15, "both allowed")."""

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
    computed = bool(COMPUTED.match(description))

    def role(name: str, variadic: bool = False) -> DataRole | None:
        clean = _clean_name(name, MAX_VARIADIC_NAME_CHARS if variadic else MAX_ROLE_NAME_CHARS)
        if clean is None:
            return None
        return DataRole(
            name=clean, kinds=kinds, required=required, variadic=variadic, description=description, computed=computed
        )

    candidates: list[DataRole | None] = []
    if through and len(names) >= 2 and (family := _range_family(names[0])):
        candidates.append(role(family, variadic=True))
    elif more:
        families: list[str] = []
        for name in names:
            family = _without_last_digits(name)
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


def _without_last_digits(name: str) -> str:
    """`name` without its last ASCII digit run (`y12` is `y`, `a1b2c` is `a1bc`); unchanged without digits."""
    end = max((index for index, char in enumerate(name) if char in _DIGITS), default=-1) + 1
    if end == 0:
        return name
    start = end
    while start and name[start - 1] in _DIGITS:
        start -= 1
    return name[:start] + name[end:]


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


# --- the `## Data` section of a specification.md ------------------------------------------

_DATA_SECTION = re.compile(r"## Data\s*\n(.+?)(?=\n##|\Z)", re.DOTALL)


def data_bullets(spec_markdown: str) -> list[str]:
    """The `## Data` bullets of a `specification.md`, as `sync_to_postgres.py` stores them in `Spec.data`.

    One string per line that starts with `- ` or `* ` once stripped, the marker removed;
    an empty list when the spec has no `## Data` section.
    """
    match = _DATA_SECTION.search(spec_markdown)
    if not match:
        return []
    bullets: list[str] = []
    for line in match.group(1).strip().split("\n"):
        line = line.strip()
        if line.startswith(("- ", "* ")):
            bullets.append(line[2:].strip())
    return bullets


# --- data shape ------------------------------------------------------------------------------

Shape = Literal["table", "matrix", "network", "generated", "excluded"]
SHAPES: tuple[Shape, ...] = ("table", "matrix", "network", "generated", "excluded")

MAP_SPECS = frozenset(
    {
        "bubble-map-geographic",
        "cartogram-area-distortion",
        "choropleth-basic",
        "contour-map-geographic",
        "flowmap-origin-destination",
        "heatmap-geographic",
        "map-connection-lines",
        "map-marker-clustered",
        "map-projections",
        "map-route-path",
        "map-tile-background",
        "map-tilegrid",
        "scatter-map-geographic",
    }
)
"""The 13 map specs: tagged both `plot_type: map` and `data_type: geospatial`. Their implementations
pull basemaps, tiles or Natural Earth geometry over the network. `scatter-pitch-events` (a sports pitch
tagged `map`) and `hexbin-map-geographic` (drawn from inline coordinates) are not on the list."""

SHAPE_OVERRIDES: dict[str, tuple[Shape, str]] = {
    "learning-curve-basic": ("matrix", "train_scores and validation_scores are per-fold score matrices"),
    "pdp-basic": ("matrix", "the roles name a computed dependence and ICE curve matrix, not observations"),
    "network-transport-static": ("network", "stations and routes are the node and edge tables"),
    "upset-basic": ("table", "one row per element with its set memberships"),
    "venn-labeled-items": ("table", "one row per item with the zone it falls in"),
    "bifurcation-basic": ("generated", "a simulation of the logistic map over a parameter range"),
    "chessboard-basic": ("generated", "rows and columns are the board size, not data columns"),
    "curve-bias-variance-tradeoff": ("generated", "every curve follows from formulas over model complexity"),
    "heatmap-mandelbrot": ("generated", "the roles are the window and iteration parameters of a fractal"),
    "line-impurity-comparison": ("generated", "Gini and entropy curves computed from a probability grid"),
    "line-tanabe-sugano": ("generated", "term energies computed from ligand-field formulas"),
    "maze-circular": ("generated", "a maze generated from its ring count and seed"),
    "maze-printable": ("generated", "a maze generated from its size and seed"),
    "mohr-circle": ("generated", "three stress components define the circle"),
    "psychrometric-basic": ("generated", "the chart's curves follow from psychrometric formulas"),
    "tree-phylogenetic": ("generated", "the tree is encoded as a Newick string"),
}
"""Specs whose role bullets misfile them (docs/concepts/adaptable-code.md "Data shapes"), with the reason.
heatmap-correlation and heatmap-clustered need no entry: their `matrix` roles already make them matrices, the
lenient shape until a spec change retypes them as observations. An entry goes away when the spec pipeline
retypes the roles so that the rule below files the spec correctly."""

STRUCTURE_ROLES = frozenset({"nodes", "edges"})
"""Roles that name a network's node or edge table rather than a column."""

_DATA_KINDS = frozenset({"numeric", "categorical", "datetime", "boolean"})


def spec_shape(spec_id: str, roles: Sequence[DataRole]) -> Shape:
    """The data shape of `spec_id` with the parsed `roles` (the module docstring has the rule)."""
    if spec_id in MAP_SPECS:
        return "excluded"
    if spec_id in SHAPE_OVERRIDES:
        return SHAPE_OVERRIDES[spec_id][0]
    names = [role.name.lower() for role in roles]
    if any(name in STRUCTURE_ROLES for name in names):
        return "network"
    if any("matrix" in name for name in names):
        return "matrix"
    if roles and not any(kind in _DATA_KINDS for role in roles for kind in role.kinds):
        return "generated"
    return "table"


def is_structure_role(role: DataRole, shape: Shape) -> bool:
    """A role the shape satisfies without a column constant: a network's node or edge table, a matrix role."""
    name = role.name.lower()
    if shape == "network":
        return name in STRUCTURE_ROLES or name in {"stations", "routes"}
    if shape == "matrix":
        return True
    return False


# --- colour-driving role ---------------------------------------------------------------------

COLOR_ROLE_NAMES = frozenset(
    {
        "group",
        "series",
        "component",
        "subcategory",
        "split_group",
        "fill_category",
        "hue",
        "color",
        "colour",
        "cluster",
        "clusters",
        "compound",
        "branch",
        "term",
    }
)
"""Role names that colour the marks by their values: groups, series, stacked components, line identities. Not
`symbol` or `cohort`: heatmap-periodic-table's element symbol and heatmap-cohort-retention's cohort label
rows of a heatmap. Not `entity`: slope charts colour their lines by direction, not by entity."""
COLOR_WORDS = re.compile(r"\b(?:colou?r(?:s|ed|ing)?|hue|legend|series|stacked|stacking|segments?)\b", re.IGNORECASE)
"""Description words that name a colour encoding of a categorical role ("labels identifying each series",
"Group identifier for color coding curves", "shown as stacked segments")."""
_LABEL_KINDS = frozenset({"categorical", "text", "boolean"})


def color_role(roles: Sequence[DataRole]) -> DataRole | None:
    """The spec's colour-driving role, or None for a single-series plot (the module docstring has the rule)."""
    for role in roles:
        if not any(kind in _LABEL_KINDS for kind in role.kinds):
            continue
        if role.name.lower() in COLOR_ROLE_NAMES or COLOR_WORDS.search(role.description):
            return role
    return None
