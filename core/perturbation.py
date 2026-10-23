"""The perturbation smoke run's pure parts: perturbed tables and the mutated source.

The static checker (`core/adaptability.py`) tests proxies; the smoke run tests the
property itself (docs/concepts/adaptable-code.md, "Perturbation smoke run"): it
replaces the `# Data` block with other tables, rewrites the column constants through
their role comments, and runs the whole file. This module builds the tables from the
sample `df` and the source text for each run; the runner that executes the file in
the plotting environment, checks the PNGs on the canvas and looks for stale labels is
the pipeline's (PR 2).

`perturbations(df, columns, roles, shape)` returns, for a table, in this order:

* `renamed`: every column renamed, one of them with spaces, a unit and a dot
  (`"Value no. 1 (k EUR)"`), and every categorical column's values renamed
  (`"Group 1"`, ...). `renames` maps each old column name to its new one, so columns no
  spec role names (`# role: extra`) follow too; `retired` lists the old category values,
  so the runner can find a text artist that still shows one.
* `more_categories` and `fewer_categories`: one more value in every categorical column
  (the rows of its last value copied under a new label, numbers scaled by 1.1), and one
  fewer (the rows of its last value dropped), both within eight values and at least one;
  left out for a table without categorical columns. A colour-driving role whose group
  count the spec fixes (`fixed_group_count`: a split violin's two halves) keeps its groups.
* `single_group`: only the rows of the colour-driving role's first value, when the spec
  allows a single group (`single_group_allowed`).
* `fewer_rows`: per value of the colour-driving role (or overall), the first
  `max(2, ceil(n / 10))` rows.
* `more_rows`: ten copies; copy k continues every numeric column past the sample's range
  (k times the range plus one step), every datetime column past its last date, and
  suffixes the values of the categorical columns. The colour-driving role's column keeps
  its values, numeric codes included (groups 0 and 1 stay two groups).
* `scaled`: every numeric column times 1,000 plus 100,000.

A matrix (`df` a labeled square DataFrame) gets `renamed` (index and columns), `more`
and `fewer` (one label added or dropped on both axes) and `scaled`. Generated and
excluded specs have no table to perturb, and network specs are deferred: their block may
bind a `nodes` table beside the edge list, whose identifiers must follow the perturbed
endpoints, which comes with network eligibility (networks are not eligible for the agent in
phase 1). There is no nullable-dtype perturbation: the agent's loader hands over float64
with NaN (decision of 2026-10-23).

`smoke_source(source, perturbation, data_path)` is the source to run: the block replaced
by a `pandas.read_pickle` of the table and every column constant renamed through
`perturbation.renames`.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from core.adaptability import replace_block, rewrite_columns
from core.spec_roles import DataRole, Shape


MAX_GROUPS = 8
"""The palette's eight positions: no perturbation takes a categorical column past them."""
ROW_FACTOR = 10
SCALE = 1_000
SHIFT = 100_000
NEW_LABEL = "Added"
_SINGLE_GROUP_WORDS = ("binary", "two ", "pair", "split", "both", "left/right", "versus", " vs")


@dataclass(frozen=True)
class Perturbation:
    """One table to run the file on: the column each role binds in it, the column renames, the retired labels."""

    name: str
    description: str
    df: pd.DataFrame
    columns: dict[str, str | list[str]]
    retired: frozenset[str] = field(default_factory=frozenset)
    renames: dict[str, str] = field(default_factory=dict)
    """Old column name -> new one, for every renamed column (spec roles and extras alike)."""


def fixed_group_count(roles: Sequence[DataRole], color_role: str | None) -> bool:
    """The spec fixes how many groups its colour-driving role has.

    A boolean role, or one whose description says so ("binary", "two", "pair", "split", "both",
    "versus"): a split violin or a two-sample comparison needs exactly its two groups.
    """
    role = next((role for role in roles if role.name == color_role), None)
    if role is None:
        return False
    if "boolean" in role.kinds:
        return True
    text = f" {role.description.lower()} "
    return any(word in text for word in _SINGLE_GROUP_WORDS)


def single_group_allowed(roles: Sequence[DataRole], shape: Shape, color_role: str | None) -> bool:
    """The single-group perturbation runs on a table whose colour-driving role can hold one value."""
    return shape == "table" and color_role is not None and not fixed_group_count(roles, color_role)


def perturbations(
    df: pd.DataFrame,
    columns: Mapping[str, str | Sequence[str]],
    roles: Sequence[DataRole],
    shape: Shape,
    color_role: str | None = None,
) -> list[Perturbation]:
    """The perturbed tables for the sample `df`, whose role columns `columns` names (role -> column).

    Empty for a generated, excluded or network spec (the module docstring says why networks wait).
    """
    if shape in ("generated", "excluded", "network"):
        return []
    if shape == "matrix":
        return _matrix_perturbations(df, columns)
    role_columns: dict[str, str | list[str]] = {
        role: name if isinstance(name, str) else list(name) for role, name in columns.items()
    }
    color_value = role_columns.get(color_role) if color_role else None
    color_column = color_value if isinstance(color_value, str) else None
    categorical = [name for name in df.columns if _is_categorical(df[name])]
    fixed = color_column if color_column is not None and fixed_group_count(roles, color_role) else None
    varied = [name for name in categorical if name != fixed]
    out = [_renamed(df, role_columns, categorical)]
    for changed in (_more_categories(df, role_columns, varied), _fewer_categories(df, role_columns, varied)):
        if len(changed.df) != len(df):  # a table without categorical columns has no categories to change
            out.append(changed)
    if color_column is not None and single_group_allowed(roles, shape, color_role):
        first = df[color_column].dropna().iloc[0] if df[color_column].notna().any() else None
        single = df[df[color_column] == first].reset_index(drop=True)
        out.append(
            Perturbation("single_group", f"only the {color_column!r} value {first!r}", single, dict(role_columns))
        )
    out.append(_fewer_rows(df, role_columns, color_column))
    out.append(_more_rows(df, role_columns, categorical, color_column))
    out.append(_scaled(df, role_columns))
    return out


def _is_categorical(series: pd.Series) -> bool:
    return bool(
        isinstance(series.dtype, pd.CategoricalDtype)
        or pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
        or pd.api.types.is_bool_dtype(series)
    )


def _numeric(df: pd.DataFrame) -> list[str]:
    return [
        name
        for name in df.columns
        if pd.api.types.is_numeric_dtype(df[name]) and not pd.api.types.is_bool_dtype(df[name])
    ]


def _renamed_columns(df: pd.DataFrame) -> dict[str, str]:
    """Every column renamed; the first numeric one gets spaces, a unit and a dot."""
    numeric = _numeric(df)
    unit_column = numeric[0] if numeric else (df.columns[0] if len(df.columns) else None)
    mapping: dict[str, str] = {}
    for index, name in enumerate(df.columns, start=1):
        if name == unit_column:
            mapping[name] = f"Value no. {index} (k EUR)"
        else:
            mapping[name] = f"Column {index} renamed"
    return mapping


def _remap(columns: Mapping[str, str | list[str]], mapping: Mapping[str, str]) -> dict[str, str | list[str]]:
    out: dict[str, str | list[str]] = {}
    for role, name in columns.items():
        out[role] = mapping.get(name, name) if isinstance(name, str) else [mapping.get(item, item) for item in name]
    return out


def _renamed(df: pd.DataFrame, columns: Mapping[str, str | list[str]], categorical: list[str]) -> Perturbation:
    table = df.copy()
    retired: set[str] = set()
    for name in categorical:
        if pd.api.types.is_bool_dtype(table[name]):
            continue
        values = list(dict.fromkeys(table[name].dropna().tolist()))
        taken = {str(value) for value in values}
        relabel: dict[object, str] = {}
        for position, value in enumerate(values, start=1):
            label = f"{str(name).split(' ')[0].title()} {position}"
            while label in taken:
                label += "·"
            relabel[value] = label
        retired |= {str(value) for value in values}
        table[name] = table[name].map(lambda value, relabel=relabel: relabel.get(value, value))
    mapping = _renamed_columns(table)
    return Perturbation(
        "renamed",
        "columns renamed (one with spaces, a unit and a dot) and category values renamed",
        table.rename(columns=mapping),
        _remap(columns, mapping),
        frozenset(retired),
        {str(old): new for old, new in mapping.items()},
    )


def _more_categories(df: pd.DataFrame, columns: Mapping[str, str | list[str]], categorical: list[str]) -> Perturbation:
    table = df.copy()
    for name in categorical:
        if pd.api.types.is_bool_dtype(table[name]):
            continue
        values = list(dict.fromkeys(table[name].dropna().tolist()))
        if not values or len(values) >= MAX_GROUPS:
            continue
        if isinstance(table[name].dtype, pd.CategoricalDtype):
            table[name] = table[name].astype(object)  # a new label is no category of the old dtype
        extra = table[table[name] == values[-1]].copy()
        extra[name] = f"{NEW_LABEL} {name}"
        for numeric in _numeric(extra):
            extra[numeric] = extra[numeric] * 1.1
        table = pd.concat([table, extra], ignore_index=True)
    return Perturbation("more_categories", "one more value in every categorical column", table, dict(columns))


def _fewer_categories(df: pd.DataFrame, columns: Mapping[str, str | list[str]], categorical: list[str]) -> Perturbation:
    table = df.copy()
    for name in categorical:
        values = list(dict.fromkeys(table[name].dropna().tolist()))
        if len(values) >= 2:
            table = table[table[name] != values[-1]]
    return Perturbation(
        "fewer_categories", "one fewer value in every categorical column", table.reset_index(drop=True), dict(columns)
    )


def _fewer_rows(df: pd.DataFrame, columns: Mapping[str, str | list[str]], color_column: str | None) -> Perturbation:
    keep = max(2, math.ceil(len(df) / ROW_FACTOR))
    if color_column is not None and color_column in df.columns:
        per_group = max(2, math.ceil(keep / max(1, df[color_column].nunique())))
        table = df.groupby(color_column, sort=False, dropna=False).head(per_group)
    else:
        table = df.head(keep)
    return Perturbation(
        "fewer_rows",
        f"about a tenth of the rows ({len(table)} of {len(df)})",
        table.reset_index(drop=True),
        dict(columns),
    )


def _more_rows(
    df: pd.DataFrame, columns: Mapping[str, str | list[str]], categorical: list[str], color_column: str | None
) -> Perturbation:
    # the colour-driving column keeps its values: numeric group codes (0 and 1) must stay two groups
    numeric = [name for name in _numeric(df) if name != color_column]
    datetimes = [name for name in df.columns if pd.api.types.is_datetime64_any_dtype(df[name]) and name != color_column]
    copies = [df.copy()]
    for k in range(1, ROW_FACTOR):
        part = df.copy()
        for name in numeric:
            values = part[name].astype(float)
            span = float(values.max() - values.min()) if values.notna().any() else 0.0
            step = float(np.nanmedian(np.diff(np.sort(values.dropna().unique())))) if values.nunique() > 1 else 1.0
            part[name] = values + k * (span + step)
        for name in datetimes:
            stamps = part[name]
            ordered = stamps.dropna().sort_values().unique()
            gap = pd.Series(ordered).diff().median() if len(ordered) > 1 else pd.Timedelta(days=1)
            part[name] = stamps + k * ((stamps.max() - stamps.min()) + gap)
        for name in categorical:
            if name == color_column or pd.api.types.is_bool_dtype(part[name]):
                continue
            part[name] = part[name].map(lambda value, k=k: value if pd.isna(value) else f"{value} {k + 1}")
        copies.append(part)
    table = pd.concat(copies, ignore_index=True)
    return Perturbation("more_rows", f"{ROW_FACTOR} times the rows ({len(table)})", table, dict(columns))


def _scaled(df: pd.DataFrame, columns: Mapping[str, str | list[str]]) -> Perturbation:
    table = df.copy()
    for name in _numeric(table):
        table[name] = table[name].astype(float) * SCALE + SHIFT
    return Perturbation("scaled", f"numbers times {SCALE:,} plus {SHIFT:,}", table, dict(columns))


def _matrix_perturbations(df: pd.DataFrame, columns: Mapping[str, str | Sequence[str]]) -> list[Perturbation]:
    roles = {role: name if isinstance(name, str) else list(name) for role, name in columns.items()}
    labels = [str(label) for label in df.index]
    relabel = {label: f"Item {position}" for position, label in enumerate(df.index, start=1)}
    relabel.update(
        {label: f"Item {position}" for position, label in enumerate(df.columns, start=1) if label not in relabel}
    )
    renamed = df.rename(index=relabel, columns=relabel)
    # the column labels are the matrix's columns: a constant that names one (`# role: extra`) follows it
    renames = {str(label): relabel[label] for label in df.columns}
    out = [
        Perturbation("renamed", "matrix labels renamed", renamed, _remap(roles, renames), frozenset(labels), renames)
    ]
    if len(df.index) < MAX_GROUPS and len(df.index) == len(df.columns):
        bigger = df.copy().astype(float)
        bigger.loc[NEW_LABEL] = bigger.iloc[-1] * 0.9
        bigger[NEW_LABEL] = bigger.loc[:, bigger.columns[-1]] * 0.9
        out.append(Perturbation("more_categories", "one more label on both axes", bigger, dict(roles)))
    if len(df.index) > 2 and len(df.index) == len(df.columns):
        out.append(
            Perturbation("fewer_categories", "one fewer label on both axes", df.iloc[:-1, :-1].copy(), dict(roles))
        )
    out.append(
        Perturbation("scaled", f"numbers times {SCALE:,} plus {SHIFT:,}", df.astype(float) * SCALE + SHIFT, dict(roles))
    )
    return out


def smoke_source(source: str, perturbation: Perturbation, data_path: str) -> str:
    """The source with its block replaced by a read of `data_path` (a pickle) and its column constants renamed.

    Every column constant, `# role: extra` included, follows `perturbation.renames`.
    """
    block = f"import pandas as pd\n\ndf = pd.read_pickle({data_path!r})"
    return rewrite_columns(replace_block(source, block), perturbation.renames)
