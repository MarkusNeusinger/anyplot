"""Lower and upper bound pairs among a spec's roles, and the check that their columns are not swapped around.

No ADK import. A range plot draws each row from a lower to an upper value: `min_value` and
`max_value` of `range-interval`, `ci_lower` and `ci_upper` of a forest plot, `low` and `high`
of a candlestick. When the default bindings put two unrelated measures on such a pair, such as
a count of games on `min_value` and an average score on `max_value`, every row's minimum lies
above its maximum and the plot draws nonsense. Nothing noticed: the bindings were complete, so
the conversion check for open roles (`conversions.py`) never ran, and the text column that held
the ranges (`10–25`) stayed unused.

A pair (`bound_pairs`) is two single number roles whose names differ in one word only, the
lower word of `BOUND_WORDS` in one and its upper partner in the other: `min_value` and
`max_value`, `ci_lower` and `ci_upper`, `lower_80` and `upper_80`, `low` and `high`, `lcl` and
`ucl`. The rule reads the role names the specs declare; `NOT_BOUNDS` names the pairs it finds
that are no bounds, from the specs' own descriptions: `error_lower` and `error_upper` are the
magnitudes of an error below and above a point (`errorbar-asymmetric`), which may be of any
size each, and `low_value` and `high_value` are the outcomes of a low and a high scenario of a
tornado chart, where the low scenario can give the larger outcome. A variadic family
(`y_lower1`, `y_upper1`, ...) is no pair here: its members take columns in column order.

A pair is inverted (`inverted`) when the smallest value of the lower column lies above the
largest value of the upper column, so every row's lower bound would lie above its upper bound;
the profile's minimum and maximum say so without reading the rows. The default bindings never
bind such a pair, which leaves both roles open. A pair bound so by hand is the user's choice: it
stays valid, nothing blocks `.confirm()`, every change of the data keeps it, and it carries one
neutral warning line (`inverted_line`, `bindings.check_bindings`).
"""

from dataclasses import dataclass

from core.spec_roles import DataRole

from ..schemas import ColumnProfile


BOUND_WORDS: tuple[tuple[str, str], ...] = (("lower", "upper"), ("low", "high"), ("min", "max"), ("lcl", "ucl"))
"""The word of a lower bound in a role name, and the word of its upper partner."""

NOT_BOUNDS: frozenset[frozenset[str]] = frozenset(
    {frozenset({"error_lower", "error_upper"}), frozenset({"low_value", "high_value"})}
)
"""Pairs of role names that `BOUND_WORDS` matches but whose values are no lower and upper bound of one range."""


@dataclass(frozen=True)
class BoundPair:
    """Two roles of one spec: `lower` holds the lower end of each row's range, `upper` the upper end."""

    lower: str
    upper: str


def bound_pairs(roles: list[DataRole]) -> list[BoundPair]:
    """The lower and upper bound pairs among `roles`, in the order of the lower role."""
    singles = {role.name.casefold(): role.name for role in roles if not role.variadic and "numeric" in role.kinds}
    pairs: list[BoundPair] = []
    for key, name in singles.items():
        words = key.split("_")
        for position, word in enumerate(words):
            for low, high in BOUND_WORDS:
                if word != low:
                    continue
                partner = singles.get("_".join([*words[:position], high, *words[position + 1 :]]))
                if partner is not None and frozenset({key, partner.casefold()}) not in NOT_BOUNDS:
                    pairs.append(BoundPair(name, partner))
    return pairs


def inverted(lower: ColumnProfile, upper: ColumnProfile) -> bool:
    """Whether every value of the number column `lower` lies above every value of the number column `upper`."""
    numbers = ("number", "integer")
    if lower.dtype not in numbers or upper.dtype not in numbers:
        return False
    low, high = lower.min, upper.max
    return isinstance(low, int | float) and isinstance(high, int | float) and low > high


def ordered(lower: ColumnProfile, upper: ColumnProfile) -> bool:
    """Whether two number columns can be a range's ends in this order: `lower` neither starts nor ends above `upper`.

    Where every row's lower end lies at or below its upper end, both the smallest and the largest value of
    `lower` lie at or below those of `upper`. The test is stricter than `inverted` and is for the two parts of
    one `split`, whose rows belong together: `22-18` and `17-12` (a high before a low) fail it, although the
    parts overlap.
    """
    numbers = ("number", "integer")
    if lower.dtype not in numbers or upper.dtype not in numbers:
        return False
    low_min, high_min, low_max, high_max = lower.min, upper.min, lower.max, upper.max
    if not (
        isinstance(low_min, int | float)
        and isinstance(high_min, int | float)
        and isinstance(low_max, int | float)
        and isinstance(high_max, int | float)
    ):
        return False
    return low_min <= high_min and low_max <= high_max


def inverted_line(pair: BoundPair, lower: ColumnProfile, upper: ColumnProfile) -> str:
    """The binding warning of an inverted pair (`inverted`): one neutral line that says what the plot will show.

    It never asks for another binding: a person may bind a range high to low on purpose, and the binding stays
    valid and is drawn as bound.
    """
    return (
        f"{pair.lower} and {pair.upper}: every value of '{lower.name}' (from {_shown(lower.min)}) lies above every "
        f"value of '{upper.name}' (up to {_shown(upper.max)}), so each row's lower bound is above its upper bound"
    )


def _shown(value: object) -> str:
    """A profile's minimum or maximum as the profile writes it: a whole number without `.0`."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
