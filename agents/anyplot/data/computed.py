"""Roles the plot can compute from the data: bound when the data has the column, computed when it has not.

No ADK import. A spec role is computed (`DataRole.computed`) when its `## Data` bullet
starts with "Computed", "Calculated" or "Derived" (`spec_roles.COMPUTED`, the rolling average of
`line-timeseries-rolling`), or when `COMPUTED_ROLES` lists it for its spec: values the
plot derives from the other roles although the spec's bullet reads like data (the Bollinger
bands from the closing price, the fitness, fatigue and form of a training-load chart from
the daily load, the moving averages and Ichimoku lines of a price table). The list lives
here, not in the spec files, which only the spec pipeline writes;
`tests/unit/agents/data/test_computed.py` checks that every listed role exists in its spec
and audits the wording of every spec's roles, so a new spec with such a role fails until it
is listed here or named as data there with the reason.

An unmarked role is required, and the default bindings fill a required number role with any
number column: unmarked, the three SMAs of `indicator-sma` take a stock table's `Open`,
`High` and `Low`, and the plot draws prices where its averages belong.

Owner decision of 2026-10-15, "both allowed": a computed role is optional. When the data has
a column that clearly holds the value (`name_match`: its name, or every word of one entry of
`ALIASES`, such as `SMA 20`, `BBU_20_2.0` or `Fitness (CTL)`), the default bindings bind it
and the plot uses it; the user may bind any fitting column by hand; otherwise the role stays
unbound, is never missing, and the adapter computes the value from the bound data (the spec
brief says per role which of the two applies, `briefs.describe_role`).

The match is strict: no bare word that also names something else
(`upper` needs a band word, `fitness` a training word), and words that rule a column out
(`EXCLUDES_ALL`: `Upper Shadow`, `Volume SMA`, `Fitness Age`, `Fatigue (RPE)`, a MACD),
unless the word belongs to one of the role's own phrases (`MACD Signal` is the MACD's signal
line). The spec's window (`WINDOWS`: 20 for the Bollinger roles, 42 and 7 for CTL and ATL)
breaks a tie (`window_rank`), and a bound column of another window (`SMA 200`) is a binding
warning (`window_line`), so nothing changes silently.
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import replace

from core.spec_roles import DataRole


COMPUTED_ROLES: dict[str, frozenset[str]] = {
    "burndown-sprint": frozenset({"ideal"}),
    "climograph-walter-lieth": frozenset({"temp_annual_mean", "precip_annual_total"}),
    "curve-bias-variance-tradeoff": frozenset({"total_error"}),
    "heatmap-loss-triangle": frozenset({"development_factor"}),
    "indicator-bollinger": frozenset({"sma", "upper_band", "lower_band"}),
    "indicator-ema": frozenset({"ema_short", "ema_long"}),
    "indicator-ichimoku": frozenset({"tenkan_sen", "kijun_sen", "senkou_span_a", "senkou_span_b", "chikou_span"}),
    "indicator-macd": frozenset({"signal", "histogram"}),
    "indicator-sma": frozenset({"sma_short", "sma_medium", "sma_long"}),
    "line-training-load-pmc": frozenset({"ctl", "atl", "tsb"}),
    "probability-weibull": frozenset({"cumulative_probability"}),
    "shap-waterfall": frozenset({"final_value"}),
    "tree-decision": frozenset({"emv", "pruned"}),
}
"""Per spec, the roles the plot computes when no column holds them, beyond the bullets that say so.

A role belongs here when its value follows from the spec's other roles by a fixed formula: the
one its bullet or the spec's notes give, or the standard definition of the indicator it names.
Moving averages and EMAs of `close`, the Ichimoku lines from `high`, `low` and `close`, the
MACD signal line and histogram from `macd`, the ideal burndown line from the first day's
scope, the annual mean and total of a climograph's months, a sum of error terms, chain-ladder
age-to-age factors, median-rank plotting positions, a SHAP prediction as base plus
contributions, and a decision tree's rollback. Not here: a value that needs a model fit
(`logistic-regression`'s probability, a forecast), an input no role carries (the MACD line
without prices, control limits without the subgroup size), or a stated value such as a target.
"""

_BOLLINGER = frozenset({"sma", "upper_band", "lower_band"})
_LOADS = frozenset({"ctl", "atl", "tsb"})
COMPANIONS: dict[str, dict[str, frozenset[str]]] = {
    "indicator-bollinger": {name: _BOLLINGER - {name} for name in _BOLLINGER},
    "line-training-load-pmc": {name: _LOADS - {name} for name in _LOADS},
    "indicator-ichimoku": {"senkou_span_a": frozenset({"tenkan_sen", "kijun_sen"})},
    "indicator-macd": {"signal": frozenset({"histogram"}), "histogram": frozenset({"signal"})},
    "tree-decision": {"pruned": frozenset({"emv"})},
}
"""Per spec and computed role, the other computed roles its formula relates it to: an open one is built on those
of them that are bound, so the parts agree (the bands around a bound middle band, a balance from the bound loads,
leading span A from the bound conversion and base lines, the histogram from a bound signal line). A role the spec
does not relate stays independent: the three SMAs of `indicator-sma` each come from `close`."""

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
_EXPONENTIAL = (
    "ema",
    "ewma",
    "ewm",
    "exponential moving average",
    "exponential average",
    "exponentially weighted",
    "exponentieller durchschnitt",
    "exponentiell gleitender durchschnitt",
    "moyenne mobile exponentielle",
    "media movil exponencial",
    "media mobile esponenziale",
)
"""An exponential moving average in a column name: `EMA 12`, `EMA(26)`, `ewm_12`, `Exponentieller Durchschnitt`."""
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
    # Three windows of one average: the window in the name (`SMA 50`) or a size word (`Long MA`) picks the role.
    "sma_short": _MOVING_AVERAGE,
    "sma_medium": _MOVING_AVERAGE,
    "sma_long": _MOVING_AVERAGE,
    "ema_short": _EXPONENTIAL,
    "ema_long": _EXPONENTIAL,
    "tenkan_sen": ("tenkan", "conversion line"),
    "kijun_sen": ("kijun", "base line"),
    "senkou_span_a": ("senkou a", "span a"),
    "senkou_span_b": ("senkou b", "span b"),
    "chikou_span": ("chikou", "lagging span", "lagging line"),
    "signal": ("macd signal", "macdsignal", "macds"),
    "histogram": ("hist", "macd hist", "macdhist", "macdh", "macd oscillator", "macd osc"),
    "development_factor": ("development factors", "age to age", "ldf", "link ratio", "ata"),
    "cumulative_probability": ("median rank", "unreliability", "failure probability", "cdf"),
    "temp_annual_mean": ("annual mean temperature", "annual temperature", "jahresmitteltemperatur"),
    "precip_annual_total": ("annual precipitation", "annual rainfall", "jahresniederschlag"),
    "final_value": ("prediction", "model output"),
    "emv": ("expected monetary value", "expected value"),
}
"""Per role name, the words a column name holds when it clearly carries that value (all words of one entry,
compared without case and diacritics, in any order). The role's own name always counts too (`rolling_avg`,
`upper band`, `ideal`), so a role whose name is all a column would say has no entry. No bare word that also
names something else (`upper`, `fitness`, `form`)."""

_BAND_SIDES = frozenset(
    {"upper", "lower", "obere", "oberes", "untere", "unteres", "oben", "unten", "bbu", "bbl"}
    | {"superieure", "inferieure", "superior", "inferior", "superiore", "inferiore"}
)
EXCLUDES_ALL = frozenset(
    {"shadow", "wick", "limit", "circuit", "volume", "vol", "age", "level", "rating", "rpe", "score", "id"}
    | {"ci", "confidence", "convergence", "divergence", "macd", "tier", "std", "sum", "count", "variance", "var"}
)
"""Words that rule a column out for every computed role: `Upper Shadow`, `Volume SMA`, `Fitness Age`, `Form_ID`,
`Fatigue (RPE)`, `Upper_CI`, `Moving Average Convergence Divergence` and other statistics name something else.
A word of the role's own name or aliases never rules it out (`MACD Signal`, `Age-to-Age Factor`)."""
_BAND_WORDS = _BAND_SIDES | {"band", "bb", "bollinger"}
_NOT_SIMPLE = frozenset(
    {"ema", "ewma", "ewm", "exponential", "exponentially", "exponentieller", "exponentiell", "exponentielle"}
    | {"exponencial", "esponenziale", "weighted", "wma", "vwap"}
)
"""Words of an average that is not a simple one: an EMA, a weighted average or a VWAP is no SMA and no rolling mean."""
_SHORT, _MEDIUM, _LONG = frozenset({"short", "fast"}), frozenset({"medium", "mid"}), frozenset({"long", "slow"})
EXCLUDES: dict[str, frozenset[str]] = {
    "sma": _BAND_SIDES | _NOT_SIMPLE,
    "rolling_avg": _BAND_WORDS | _NOT_SIMPLE,
    "sma_short": _BAND_WORDS | _NOT_SIMPLE | _MEDIUM | _LONG,
    "sma_medium": _BAND_WORDS | _NOT_SIMPLE | _SHORT | _LONG,
    "sma_long": _BAND_WORDS | _NOT_SIMPLE | _SHORT | _MEDIUM,
    "ema_short": _BAND_WORDS | {"sma", "simple"} | _MEDIUM | _LONG,
    "ema_long": _BAND_WORDS | {"sma", "simple"} | _SHORT | _MEDIUM,
    "signal": frozenset({"buy", "sell", "trade", "trades", "trading", "entry", "exit", "bullish", "bearish"}),
    "cumulative_probability": frozenset({"survival", "reliability"}),
    "final_value": frozenset({"base", "expected", "mean", "average"}),
}
"""Per role name, more such words: `SMA Upper Band` is a band, never the middle average or a rolling average;
`EMA 20` is no SMA; `Long MA` is not the short average; `Buy Signal` is a trade, not the MACD's signal line;
`Survival Probability` is the complement of the failure probability; `Expected Value` of a SHAP chart is its base."""

WINDOWS: dict[str, int] = {
    "sma": 20,
    "upper_band": 20,
    "lower_band": 20,
    "ctl": 42,
    "atl": 7,
    "sma_short": 20,
    "sma_medium": 50,
    "sma_long": 200,
    "ema_short": 12,
    "ema_long": 26,
    "tenkan_sen": 9,
    "kijun_sen": 26,
    "senkou_span_b": 52,
}
"""The window the specs name for a role (`indicator-bollinger`: 20 periods; `line-training-load-pmc`: CTL over
42 days, ATL over 7; `indicator-sma`: 20, 50 and 200; `indicator-ema`: 12 and 26, its example and every
implementation; `indicator-ichimoku`: 9 for the conversion line, 26 for the base line, 52 for leading span B).
A column whose name
carries another window (`SMA 100`) is still bound, with a warning."""
MAX_WINDOW = 999

_WORD = re.compile(r"[^\W_]+")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
_DIGIT_EDGE = re.compile(r"(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])")


def mark_computed(roles: Iterable[DataRole], spec_id: str) -> list[DataRole]:
    """The roles with `computed` set for the ones `COMPUTED_ROLES` lists for `spec_id`; a bullet's own mark stays."""
    listed = COMPUTED_ROLES.get(spec_id, frozenset())
    return [replace(role, computed=True) if role.name in listed else role for role in roles]


def companions(spec_id: str, role_name: str, bound: Iterable[str]) -> list[str]:
    """The roles of `bound`, in its order, that `COMPANIONS` relates `role_name` to in `spec_id`."""
    related = COMPANIONS.get(spec_id, {}).get(role_name, frozenset())
    return [name for name in bound if name in related]


def name_match(role: DataRole, column_name: str) -> bool:
    """Whether the column's name clearly says it holds the role's value: every word of the role's name or of one alias."""
    return match_score(role, column_name) > 0


def match_score(role: DataRole, column_name: str) -> int:
    """How specific the match is: the words of the longest phrase the column's name holds (0: no match).

    `SMA Upper Band` holds `sma` (one word) and `upper band` (two): the more specific role takes
    the column, so the upper band is never read as the middle average (`bindings.default_bindings`).
    A word the role's own phrases hold rules nothing out: `macd` excludes a MACD column from
    every other role, not from the MACD's signal line (`MACD Signal`).
    """
    words = set(_words(column_name))
    phrases = [
        wanted for phrase in (role.name.replace("_", " "), *ALIASES.get(role.name, ())) if (wanted := _words(phrase))
    ]
    own = {word for wanted in phrases for word in wanted}
    if words & ((EXCLUDES_ALL | EXCLUDES.get(role.name, frozenset())) - own):
        return 0
    return max((len(wanted) for wanted in phrases if set(wanted) <= words), default=0)


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
