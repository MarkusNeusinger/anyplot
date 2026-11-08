"""Roles bound only by a clear name: the ones the plot can compute, and the ones only a column named so holds.

No ADK import. A spec role is computed (`DataRole.computed`) when its `## Data` bullet
starts with "Computed", "Calculated" or "Derived" (`spec_roles.COMPUTED`, the rolling average of
`line-timeseries-rolling`), or when `spec_roles.COMPUTED_ROLES` lists it for its spec: values the
plot derives from the other roles although the spec's bullet reads like data (the Bollinger
bands from the closing price, the fitness, fatigue and form of a training-load chart from
the daily load, the moving averages and Ichimoku lines of a price table). The list lives in
`core/spec_roles.py`, not in the spec files, which only the spec pipeline writes, so the
pipeline's adaptability checker reads it too; `tests/unit/agents/data/test_computed.py` checks
that every listed role exists in its spec and audits the wording of every spec's roles, so a
new spec with such a role fails until it is listed there or named as data with the reason.

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

A name-only role (`DataRole.name_only`, listed in `NAME_ONLY_ROLES`) takes a column by the same
name match and by nothing else, but a required one stays required: no role of its spec carries
what the plot would compute it from. Unmarked, the MACD line of `indicator-macd` and the RSI of
`indicator-rsi` took a price table's `Open`, and the sample means, ranges and control limits of
`spc-xbar-r` took the raw measurements `X1` to `X5` of a wide subgroup table: complete bindings,
a wrong plot and no warning. Marked, such a role stays open and is missing, so the page and the
root ask for its column. No conversion, row number or date fills it either (`conversions.py`).
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import replace

from core.spec_roles import DataRole


NAME_ONLY_ROLES: dict[str, frozenset[str]] = {
    "indicator-macd": frozenset({"macd", "close"}),
    "indicator-rsi": frozenset({"rsi", "close"}),
    "spc-xbar-r": frozenset(
        {"sample_mean", "sample_range", "ucl", "lcl", "center_line", "upper_warning", "lower_warning", "subgroup_size"}
    ),
}
"""Per spec, the roles the default bindings fill only from a column whose name clearly holds them (`name_match`).

A role belongs here when every number column fits its kind but only a column named so holds its value, and no
role of its spec can compute it: the MACD line and the RSI need closing prices, which neither spec carries, and
the X-bar/R chart's sample statistics and limits need the subgroups' measurements and size, which it carries
neither. The optional warning limits are here too, because an optional number role otherwise takes any free
number column. `close` and `subgroup_size` are not in the specs yet: they are the optional roles the spec changes
for these specs add, listed here so that they bind by name from the day they arrive.
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
    # The name-only roles (`NAME_ONLY_ROLES`): `MACD_12_26_9` and `RSI_14` hold their role's own name.
    "macd": ("macd line", "moving average convergence divergence"),
    "rsi": ("relative strength index",),
    "close": ("closing price", "closing", "price", "schlusskurs", "schluss", "kurs", "cierre", "chiusura", "cloture"),
    "sample_mean": ("mean", "average", "avg", "x bar", "xbar", "mittelwert", "moyenne"),
    "sample_range": ("range", "r", "spannweite"),
    "ucl": ("upper control limit", "upper limit", "obere eingriffsgrenze", "oeg"),
    "lcl": ("lower control limit", "lower limit", "untere eingriffsgrenze", "ueg"),
    "center_line": (
        *("cl", "center", "centre", "centerline", "centre line", "central line", "mittellinie"),
        *("x bar bar", "xbarbar", "grand mean", "process mean", "r bar", "rbar", "average range", "mean range"),
    ),
    "upper_warning": ("uwl", "upper warning limit", "obere warngrenze", "owg"),
    "lower_warning": ("lwl", "lower warning limit", "untere warngrenze", "uwg"),
    "subgroup_size": ("n", "subgroup n", "sample size", "group size", "stichprobenumfang", "stichprobengrosse"),
}
"""Per role name, the words a column name holds when it clearly carries that value (all words of one entry,
compared without case and diacritics, in any order). The role's own name always counts too (`rolling_avg`,
`upper band`, `ideal`), so a role whose name is all a column would say has no entry. No bare word that also
names something else (`upper`, `fitness`, `form`). A role name has one entry for every spec: `close` is
looked up only where it is name-only, since a required `close` of another spec takes any number column."""

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
_LIMIT_WORDS = frozenset(
    {"ucl", "lcl", "cl", "uwl", "lwl", "limit", "limits", "control", "warning", "upper", "lower", "sigma"}
    | {"center", "centre", "central", "centerline", "spec", "usl", "lsl", "tolerance"}
)
"""Words of a control chart's limits and center line: a column named so is no sample mean and no range."""
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
    "macd": frozenset({"signal", "hist", "histogram", "oscillator", "osc"}),
    "rsi": frozenset({"stoch", "stochastic", "stochrsi", "connors", "ma", "sma", "ema", "signal", "smoothed"}),
    "close": frozenset({"open", "high", "low", "ma", "sma", "ema", "rsi", "signal", "change", "return", "target"}),
    "sample_mean": _LIMIT_WORDS | {"range", "grand", "process", "overall", "moving"},
    "sample_range": _LIMIT_WORDS | {"mean", "average", "avg", "bar", "moving", "interquartile", "iqr"},
    "ucl": frozenset({"warning", "uwl", "lower", "lcl", "spec", "specification", "usl", "tolerance"}),
    "lcl": frozenset({"warning", "lwl", "upper", "ucl", "spec", "specification", "lsl", "tolerance"}),
    "center_line": frozenset({"upper", "lower", "ucl", "lcl", "uwl", "lwl", "warning"}),
    "upper_warning": frozenset({"lower", "lwl"}),
    "lower_warning": frozenset({"upper", "uwl"}),
}
"""Per role name, more such words: `SMA Upper Band` is a band, never the middle average or a rolling average;
`EMA 20` is no SMA; `Long MA` is not the short average; `Buy Signal` is a trade, not the MACD's signal line;
`Survival Probability` is the complement of the failure probability; `Expected Value` of a SHAP chart is its base;
`MACD Histogram` is no MACD line and `Stoch RSI` no RSI; `Close SMA` is an average, not the price; `X-bar UCL`,
`Average Range` and `Moving Range` are no sample mean or range; `Upper Spec Limit` is a tolerance, no control
limit."""

WINDOWS: dict[str, tuple[int, ...]] = {
    "sma": (20,),
    "upper_band": (20,),
    "lower_band": (20,),
    "ctl": (42,),
    "atl": (7,),
    "sma_short": (20,),
    "sma_medium": (50,),
    "sma_long": (200,),
    "ema_short": (12, 50),
    "ema_long": (26, 200),
    "tenkan_sen": (9,),
    "kijun_sen": (26,),
    "senkou_span_b": (52,),
    "rsi": (14,),
}
"""The windows the specs name for a role, the first one the convention (`indicator-bollinger`: 20 periods;
`line-training-load-pmc`: CTL over 42 days, ATL over 7; `indicator-sma`: 20, 50 and 200; `indicator-ichimoku`:
9 for the conversion line, 26 for the base line, 52 for leading span B; `indicator-rsi`: a 14-period lookback).
`indicator-ema` names two pairs, 12 and 26 (its example and the implementations) and 50 and 200 (its golden
cross), so `ema_short` takes 12 or 50 and `ema_long` 26 or 200, paired by position (`PAIRED_WINDOWS`). A column
whose name carries another window (`SMA 100`) is still bound, with a warning."""
PAIRED_WINDOWS: dict[str, str] = {"ema_short": "ema_long", "ema_long": "ema_short"}
"""Roles whose windows go together by their position in `WINDOWS`: an open long EMA beside a bound `EMA 50` is the
200-period one (`open_window`)."""
MAX_WINDOW = 999

_WORD = re.compile(r"[^\W_]+")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
_DIGIT_EDGE = re.compile(r"(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])")


def mark_name_only(roles: Iterable[DataRole], spec_id: str) -> list[DataRole]:
    """The roles with `name_only` set for the single roles `NAME_ONLY_ROLES` lists for `spec_id`."""
    listed = NAME_ONLY_ROLES.get(spec_id, frozenset())
    return [replace(role, name_only=True) if role.name in listed and not role.variadic else role for role in roles]


def binds_by_name(role: DataRole) -> bool:
    """Whether the defaults bind the role only to a column whose name holds it: a computed or a name-only role."""
    return (role.computed or role.name_only) and not role.variadic


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
    every other role, not from the MACD's signal line (`MACD Signal`). A word a phrase repeats
    must be repeated in the name: `X-bar` holds `x bar` (the sample mean) but not `x bar bar`
    (the grand mean), which `X-bar-bar` holds.
    """
    words = Counter(_words(column_name))
    phrases = [
        wanted for phrase in (role.name.replace("_", " "), *ALIASES.get(role.name, ())) if (wanted := _words(phrase))
    ]
    own = {word for wanted in phrases for word in wanted}
    if words.keys() & ((EXCLUDES_ALL | EXCLUDES.get(role.name, frozenset())) - own):
        return 0
    return max((len(wanted) for wanted in phrases if not Counter(wanted) - words), default=0)


def windows(column_name: str) -> list[int]:
    """The whole numbers from 2 to `MAX_WINDOW` in a column name, in order: `SMA 20` [20], `BBU_20_2.0` [20, 2]."""
    return [int(word) for word in _words(column_name) if word.isdigit() and 2 <= int(word) <= MAX_WINDOW]


def window_rank(role: DataRole, column_name: str) -> int:
    """The tie-break between two columns that match as well (`SMA 20` before `SMA 50`): the position of the window
    the column's name carries among the role's `WINDOWS` (0 for a role without one), then one past the last for a
    name that names none, and one more for a name that names another window."""
    accepted = WINDOWS.get(role.name, ())
    if not accepted:
        return 0
    found = windows(column_name)
    for position, window in enumerate(accepted):
        if window in found:
            return position
    return len(accepted) + 1 if found else len(accepted)


def window_line(role_name: str, column_name: str) -> str | None:
    """The warning for a column bound to a role whose spec names a window, when the column names another one.

    Owner rule: nothing changes silently. `SMA 200` on `sma` stays bound, and the session block,
    the `set_bindings` result and the page say that the plot shows a 200-period average where
    the spec's convention is 20 (review of 2026-10-15). `EMA 50` and `EMA 200` are a pair the
    EMA spec names, so they carry no warning.
    """
    accepted = WINDOWS.get(role_name, ())
    found = windows(column_name)
    if not accepted or not found or set(accepted) & set(found):
        return None
    convention = " or ".join(str(window) for window in accepted)
    return (
        f"{role_name}: column '{column_name}' holds a {found[0]}-period value; the spec's convention is "
        f"{convention}, so the plot shows the column's window"
    )


def open_window(role_name: str, bound: Mapping[str, str]) -> int | None:
    """The window the plot computes an open role with: the role's first in `WINDOWS`, or, when its partner in
    `PAIRED_WINDOWS` is bound (`bound`: role name to column) to a column that names one of the partner's windows,
    the window at the same position (`EMA 50` bound to the short EMA: the open long one takes 200). None for a role
    without a window."""
    accepted = WINDOWS.get(role_name, ())
    if not accepted:
        return None
    partner = PAIRED_WINDOWS.get(role_name)
    if partner is not None and partner in bound:
        found = windows(bound[partner])
        for position, window in enumerate(WINDOWS.get(partner, ())):
            if window in found and position < len(accepted):
                return accepted[position]
    return accepted[0]


def _words(text: str) -> list[str]:
    """Lower-case words without diacritics, split at camel case and between letters and digits (`SMA20`)."""
    split = _DIGIT_EDGE.sub(" ", _CAMEL.sub(" ", text))
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", split.casefold()) if not unicodedata.combining(char)
    )
    return _WORD.findall(folded)
