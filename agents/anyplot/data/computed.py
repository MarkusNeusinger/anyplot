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
a column that clearly holds the value (`name_match`: its name, or every word of one entry of
`ALIASES`, such as `SMA 20`, `BBU_20_2.0` or `Fitness (CTL)`), the default bindings bind it
and the plot uses it; the user may bind any fitting column by hand; otherwise the role stays
unbound, is never missing, and the adapter computes the value from the bound data (the spec
brief says per role which of the two applies, `briefs.describe_role`).

The review of 2026-10-15 made the match strict: no bare word that also names something else
(`upper` needs a band word, `fitness` a training word), and words that rule a column out
(`EXCLUDES_ALL`: `Upper Shadow`, `Volume SMA`, `Fitness Age`, `Fatigue (RPE)`, a MACD). The
spec's window (`WINDOWS`: 20 for the Bollinger roles, 42 and 7 for CTL and ATL) breaks a tie
(`window_rank`), and a bound column of another window (`SMA 200`) is a binding warning
(`window_line`), so nothing changes silently.
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import replace

from core.spec_roles import DataRole


COMPUTED_ROLES: dict[str, frozenset[str]] = {
    "indicator-bollinger": frozenset({"sma", "upper_band", "lower_band"}),
    "line-training-load-pmc": frozenset({"ctl", "atl", "tsb"}),
}
"""Per spec, the roles the plot computes when no column holds them, beyond the bullets that say so."""

_MOVING_AVERAGE = (
    "sma",
    "ma",
    "moving average",
    "moving avg",
    "moving mean",
    "rolling average",
    "rolling avg",
    "rolling mean",
    "gleitender durchschnitt",
    "gleitender mittelwert",
    "moyenne mobile",
    "media movil",
    "media mobile",
    "day average",
    "day avg",
    "day mean",
    "d avg",
    "d mean",
    "tage mittel",
    "tage durchschnitt",
)
"""A moving average in a column name: `SMA 20`, `MA(20)`, `MA7`, `7-day average`, `avg_7d`, `7-Tage-Mittel`."""
_TRAINING = ("training", "load", "stress", "belastung", "trainingsbelastung")
"""The context a bare `fitness`, `fatigue` or `form` needs: alone it is a score, an age or a rating."""

ALIASES: dict[str, tuple[str, ...]] = {
    # Never a bare `rolling`: `rolling_std`, `rolling_sum` and `Rolling Variance` are other statistics.
    "rolling_avg": _MOVING_AVERAGE,
    "sma": (*_MOVING_AVERAGE, "middle band", "mittleres band", "bbm", "bollinger mitte", "bande mediane"),
    # A bare `upper` or `lower` is a candle's shadow, a circuit limit or a confidence bound: a band word comes along.
    "upper_band": (
        "upper band",
        "bb upper",
        "bollinger upper",
        "bbu",
        "bollinger oben",
        "oberes band",
        "obere band",
        "bande superieure",
        "banda superior",
        "banda superiore",
    ),
    "lower_band": (
        "lower band",
        "bb lower",
        "bollinger lower",
        "bbl",
        "bollinger unten",
        "unteres band",
        "untere band",
        "bande inferieure",
        "banda inferior",
        "banda inferiore",
    ),
    "ctl": (
        "ctl",
        "chronic training load",
        "chronic load",
        "chronische belastung",
        "chronische trainingsbelastung",
        *(f"fitness {word}" for word in _TRAINING),
    ),
    "atl": (
        "atl",
        "acute training load",
        "acute load",
        "akute belastung",
        "akute trainingsbelastung",
        *(f"fatigue {word}" for word in _TRAINING),
        *(f"ermudung {word}" for word in _TRAINING),
    ),
    "tsb": (
        "tsb",
        "training stress balance",
        "freshness",
        "frische",
        "trainingsstressbilanz",
        *(f"form {word}" for word in (*_TRAINING, "balance")),
    ),
}
"""Per role name, the words a column name holds when it clearly carries that value (all words of one entry,
compared without case and diacritics, in any order). The role's own name always counts too (`rolling_avg`,
`upper band`). Review of 2026-10-15: no bare word that also names something else (`upper`, `fitness`, `form`)."""

_BAND_SIDES = frozenset(
    {"upper", "lower", "obere", "oberes", "untere", "unteres", "oben", "unten", "bbu", "bbl"}
    | {"superieure", "inferieure", "superior", "inferior", "superiore", "inferiore"}
)
EXCLUDES_ALL = frozenset(
    {"shadow", "wick", "limit", "circuit", "volume", "vol", "age", "level", "rating", "rpe", "score", "id"}
    | {"ci", "confidence", "convergence", "divergence", "macd", "tier", "std", "sum", "count", "variance", "var"}
)
"""Words that rule a column out for every computed role: `Upper Shadow`, `Volume SMA`, `Fitness Age`, `Form_ID`,
`Fatigue (RPE)`, `Upper_CI`, `Moving Average Convergence Divergence` and other statistics name something else."""
EXCLUDES: dict[str, frozenset[str]] = {"sma": _BAND_SIDES, "rolling_avg": _BAND_SIDES | {"band", "bb", "bollinger"}}
"""Per role name, more such words: `SMA Upper Band` is a band, never the middle average or a rolling average."""

WINDOWS: dict[str, int] = {"sma": 20, "upper_band": 20, "lower_band": 20, "ctl": 42, "atl": 7}
"""The window the specs name for a role (`indicator-bollinger`: 20 periods; `line-training-load-pmc`: CTL over
42 days, ATL over 7). A column whose name carries another window (`SMA 200`) is still bound, with a warning."""
MAX_WINDOW = 999

_WORD = re.compile(r"[^\W_]+")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
_DIGIT_EDGE = re.compile(r"(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])")


def mark_computed(roles: Iterable[DataRole], spec_id: str) -> list[DataRole]:
    """The roles with `computed` set for the ones `COMPUTED_ROLES` lists for `spec_id`; a bullet's own mark stays."""
    listed = COMPUTED_ROLES.get(spec_id, frozenset())
    return [replace(role, computed=True) if role.name in listed else role for role in roles]


def name_match(role: DataRole, column_name: str) -> bool:
    """Whether the column's name clearly says it holds the role's value: every word of the role's name or of one alias."""
    return match_score(role, column_name) > 0


def match_score(role: DataRole, column_name: str) -> int:
    """How specific the match is: the words of the longest phrase the column's name holds (0: no match).

    `SMA Upper Band` holds `sma` (one word) and `upper band` (two): the more specific role takes
    the column, so the upper band is never read as the middle average (`bindings.default_bindings`).
    """
    words = set(_words(column_name))
    if words & (EXCLUDES_ALL | EXCLUDES.get(role.name, frozenset())):
        return 0
    phrases = (role.name.replace("_", " "), *ALIASES.get(role.name, ()))
    return max((len(wanted) for phrase in phrases if (wanted := _words(phrase)) and set(wanted) <= words), default=0)


def windows(column_name: str) -> list[int]:
    """The whole numbers from 2 to `MAX_WINDOW` in a column name, in order: `SMA 20` [20], `BBU_20_2.0` [20, 2]."""
    return [int(word) for word in _words(column_name) if word.isdigit() and 2 <= int(word) <= MAX_WINDOW]


def window_rank(role: DataRole, column_name: str) -> int:
    """0 when the column's name carries the spec's window for the role (or the role has none), 1 when it names none,
    2 when it names another: the tie-break between two columns that match as well (`SMA 20` before `SMA 50`)."""
    window = WINDOWS.get(role.name)
    found = windows(column_name)
    if window is None or window in found:
        return 0
    return 2 if found else 1


def window_line(role_name: str, column_name: str) -> str | None:
    """The warning for a column bound to a role whose spec names a window, when the column names another one.

    Owner rule: nothing changes silently. `SMA 200` on `sma` stays bound, and the session block,
    the `set_bindings` result and the page say that the plot shows a 200-period average where
    the spec's convention is 20 (review of 2026-10-15).
    """
    window = WINDOWS.get(role_name)
    found = windows(column_name)
    if window is None or not found or window in found:
        return None
    other = found[0]
    return (
        f"{role_name}: column '{column_name}' holds a {other}-period value; the spec's convention is {window}, "
        "so the plot shows the column's window"
    )


def _words(text: str) -> list[str]:
    """Lower-case words without diacritics, split at camel case and between letters and digits (`SMA20`)."""
    split = _DIGIT_EDGE.sub(" ", _CAMEL.sub(" ", text))
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", split.casefold()) if not unicodedata.combining(char)
    )
    return _WORD.findall(folded)
