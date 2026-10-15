"""Roles the plot can compute from the data: bound when the data has the column, computed when it has not.

No ADK import. A spec role is computed (`DataRole.computed`) when its `## Data` bullet
starts with "Computed", "Calculated" or "Derived" (`roles.COMPUTED`, the rolling average of
`line-timeseries-rolling`), or when `COMPUTED_ROLES` lists it for its spec: indicators the
plot derives from the other roles although the spec's bullet reads like data (the Bollinger
bands from the closing price, the fitness, fatigue and form of a training-load chart from
the daily load). The list lives here, not in the spec files, which only the spec pipeline
writes; `tests/unit/agents/data/test_computed.py` checks that every listed role exists in
its spec.

Owner decision of 2026-10-15, "both allowed": a computed role is optional. When the data has
a column that clearly holds the value (`name_match`: its name, or a word of `ALIASES`, such
as `SMA 20` or `gleitender Durchschnitt` for a moving average), the default bindings bind it
and the plot uses it; the user may bind any fitting column by hand; otherwise the role stays
unbound, is never missing, and the adapter computes the value from the bound data (the spec
brief says per role which of the two applies, `briefs.describe_role`).
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import replace

from .roles import DataRole


COMPUTED_ROLES: dict[str, frozenset[str]] = {
    "indicator-bollinger": frozenset({"sma", "upper_band", "lower_band"}),
    "line-training-load-pmc": frozenset({"ctl", "atl", "tsb"}),
}
"""Per spec, the roles the plot computes when no column holds them, beyond the bullets that say so."""

ALIASES: dict[str, tuple[str, ...]] = {
    "rolling_avg": (
        "rolling",
        "moving average",
        "moving avg",
        "moving mean",
        "sma",
        "ema",
        "gleitender durchschnitt",
        "gleitender mittelwert",
        "moyenne mobile",
        "media movil",
        "media mobile",
    ),
    "sma": ("sma", "moving average", "moving avg", "gleitender durchschnitt", "middle band", "mittleres band"),
    "upper_band": ("upper", "oberes band", "obere", "bb upper"),
    "lower_band": ("lower", "unteres band", "untere", "bb lower"),
    "ctl": ("ctl", "fitness", "chronic training load"),
    "atl": ("atl", "fatigue", "acute training load", "ermudung"),
    "tsb": ("tsb", "form", "training stress balance"),
}
"""Per role name, the words a column name holds when it clearly carries that value (all words of one entry,
compared without case and diacritics). The role's own name always counts too (`rolling_avg`, `upper band`)."""

_WORD = re.compile(r"[^\W_]+")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
_DIGIT_EDGE = re.compile(r"(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])")


def mark_computed(roles: Iterable[DataRole], spec_id: str) -> list[DataRole]:
    """The roles with `computed` set for the ones `COMPUTED_ROLES` lists for `spec_id`; a bullet's own mark stays."""
    listed = COMPUTED_ROLES.get(spec_id, frozenset())
    return [replace(role, computed=True) if role.name in listed else role for role in roles]


def name_match(role: DataRole, column_name: str) -> bool:
    """Whether the column's name clearly says it holds the role's value: every word of the role's name or of one alias."""
    words = set(_words(column_name))
    phrases = (role.name.replace("_", " "), *ALIASES.get(role.name, ()))
    return any((wanted := _words(phrase)) and set(wanted) <= words for phrase in phrases)


def _words(text: str) -> list[str]:
    """Lower-case words without diacritics, split at camel case and between letters and digits (`SMA20`)."""
    split = _DIGIT_EDGE.sub(" ", _CAMEL.sub(" ", text))
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", split.casefold()) if not unicodedata.combining(char)
    )
    return _WORD.findall(folded)
