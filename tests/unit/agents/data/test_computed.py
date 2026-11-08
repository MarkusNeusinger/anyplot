"""Tests for agents/anyplot/data/computed.py: the roles bound only by a clear name, computed or name-only."""

import re
from functools import cache
from pathlib import Path

import pytest

from agents.anyplot.briefs import describe_role, spec_brief
from agents.anyplot.data.bindings import carry_bindings, check_bindings, default_bindings, filled_bindings
from agents.anyplot.data.computed import (
    ALIASES,
    COMPANIONS,
    NAME_ONLY_ROLES,
    mark_name_only,
    name_match,
    open_window,
    window_line,
    window_rank,
)
from agents.anyplot.data.conversions import candidates
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.schemas import Binding
from agents.anyplot.session_state import CatalogueSnapshot, SessionView
from core.spec_roles import COMPUTED_ROLES, DataRole, data_bullets, parse_roles


PLOTS = Path(__file__).parents[4] / "plots"

DERIVED_WORDING = re.compile(
    r"\b(?:moving average|[se]ma|ewma|exponentially weighted|rolling (?:average|mean)|standard deviations"
    r"|\d+-(?:period|day|week)|plotted \d+ periods|computed as|calculated (?:via|as|from)|derived (?:via|from)"
    r"|rollback|median ranks?|plotting positions?|age-to-age|optimal solution)\b",
    re.IGNORECASE,
)
"""A role description worded like an indicator or a formula: a moving average or an EMA, a window (`20-period`),
bands of standard deviations, a line shifted by some periods, a value computed, calculated or derived, and the
named methods of the other listed roles (a rollback, median ranks, age-to-age factors, the optimal solution)."""
ARITHMETIC = re.compile(r"\b(?:sum|mean|average|total|minus|plus|difference|ratio|product)\b|\s[+−/]\s", re.IGNORECASE)
"""Arithmetic in a description that names another role of the spec: `sum of bias_squared + variance + ...`,
`Difference between MACD and signal line`, `Annual mean temperature`."""

DATA_ROLES: dict[tuple[str, str], str] = {
    ("burndown-sprint", "scope_change"): "the scope added or removed on a day is an event the data records",
    ("climograph-walter-lieth", "precipitation"): "the monthly totals are measurements; the 2:1 names the axis scale",
    ("funnel-meta-analysis", "effect_size"): "each study's estimate is reported; a mean difference is one kind of it",
    ("heatmap-rainflow", "count"): "the cycle counts come from a load history that no role of the spec carries",
    ("indicator-macd", "macd"): "the 12-day minus 26-day EMA needs closing prices, and the spec has no role for them",
    ("line-parametric", "x"): "the curve's coordinates are the data; 'computed as x(t)' says where they come from",
    ("line-parametric", "y"): "the curve's coordinates are the data; 'computed as y(t)' says where they come from",
}
"""Roles worded like a formula (`worded_as_derived`) that hold data the plot cannot compute, with the reason."""

PENDING_ROLES: dict[tuple[str, str], str] = {
    ("indicator-macd", "close"): "`close` (numeric, optional) - Closing price for each period",
    ("indicator-rsi", "close"): "`close` (numeric, optional) - Closing price for each period",
    ("spc-xbar-r", "subgroup_size"): (
        "`subgroup_size` (integer, optional) - Number of measurements in each sample (n), which selects the "
        "control chart constants A2, D3 and D4"
    ),
}
"""Name-only roles that the spec changes add (`NAME_ONLY_ROLES` lists them ahead), with the bullet each proposes.
An entry may go once its spec has the role; until then the spec may lack it."""


def roles_of(spec_id: str) -> list[DataRole]:
    return snapshot_from_repo(spec_id, "matplotlib").roles()


@cache
def catalogue_roles() -> dict[str, list[DataRole]]:
    """Every spec's roles as a session reads them: the `## Data` bullets the database stores, marked the same way."""
    roles: dict[str, list[DataRole]] = {}
    for path in sorted(PLOTS.glob("*/specification.md")):
        bullets = data_bullets(path.read_text(encoding="utf-8"))
        snapshot = CatalogueSnapshot(spec_id=path.parent.name, title=path.parent.name, data_roles=bullets, code="pass")
        roles[snapshot.spec_id] = snapshot.roles()
    return roles


def spoken(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def worded_as_derived(role: DataRole, roles: list[DataRole]) -> bool:
    """Whether the role's description reads like a value computed from data: indicator wording, or arithmetic over
    another role of the spec that it names (`bias_squared`, `macd`, `temperature`; names of three letters or more)."""
    if DERIVED_WORDING.search(role.description):
        return True
    described = f" {spoken(role.description)} "
    names_another = any(
        len(other.name) > 2 and f" {spoken(other.name)} " in described for other in roles if other.name != role.name
    )
    return names_another and ARITHMETIC.search(role.description) is not None


def pairs(bindings: list[Binding]) -> list[tuple[str, str]]:
    return [(binding.role, binding.column) for binding in bindings]


def computed_role(name: str) -> DataRole:
    return DataRole(name=name, kinds=("numeric",), required=True, variadic=False, description="", computed=True)


def name_only_role(name: str) -> DataRole:
    return DataRole(name=name, kinds=("numeric",), required=True, variadic=False, description="", name_only=True)


def with_pending(spec_id: str) -> list[DataRole]:
    """The spec's roles with the bullets the pending spec changes add, marked as a session marks them."""
    bullets = data_bullets((PLOTS / spec_id / "specification.md").read_text(encoding="utf-8"))
    added = [bullet for (spec, _), bullet in PENDING_ROLES.items() if spec == spec_id]
    snapshot = CatalogueSnapshot(spec_id=spec_id, title=spec_id, data_roles=[*bullets, *added], code="pass")
    return snapshot.roles()


def table(header: str, rows: int = 3) -> str:
    """A table of `header` with dates in the first column and distinct numbers in the others."""
    names = header.split(",")
    lines = [header]
    for row in range(rows):
        cells = [f"2024-01-0{row + 1}"] + [f"{100 + 7 * index + row * 1.5:.1f}" for index in range(len(names) - 1)]
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


def stock(extra: str = "", rows: int = 5) -> str:
    """An invented daily price table (date, OHLC, volume) with the `extra` number columns after it."""
    names = extra.split(",") if extra else []
    lines = [",".join(["date", "Open", "High", "Low", "Close", "Volume", *names])]
    for row in range(rows):
        base = 50 + 0.8 * row
        cells = [f"2024-03-{row + 4:02d}", f"{base:.2f}", f"{base + 2.5:.2f}", f"{base - 1.5:.2f}", f"{base + 1:.2f}"]
        cells += [str(9000 + 37 * row)] + [f"{base + 0.3 * (index + 1):.2f}" for index in range(len(names))]
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


def sample_table(roles: list[DataRole], rows: int = 4) -> str:
    """A table with one column per role that takes one, named as the role, with cells of the role's first kind."""
    makers = {
        "numeric": lambda row: f"{10 + 3 * row}.5",
        "datetime": lambda row: f"2024-05-{row + 1:02d}",
        "boolean": lambda row: "true" if row % 2 else "false",
    }
    columns = [role.member(1) if role.variadic else role.name for role in roles if role.kinds]
    kinds = [role.kinds[0] for role in roles if role.kinds]
    lines = [",".join(columns)]
    for row in range(rows):
        lines.append(",".join(makers.get(kind, lambda row: f"item {row}")(row) for kind in kinds))
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("spec_id", sorted(COMPUTED_ROLES))
def test_every_listed_role_exists_in_its_spec_and_is_marked(spec_id: str) -> None:
    roles = {role.name: role for role in roles_of(spec_id)}

    assert COMPUTED_ROLES[spec_id] <= set(roles), spec_id
    assert {name for name, role in roles.items() if role.computed} == COMPUTED_ROLES[spec_id]


def test_the_bullet_prefix_still_marks_the_rolling_average() -> None:
    assert [role.name for role in roles_of("line-timeseries-rolling") if role.computed] == ["rolling_avg"]


def test_every_alias_names_a_computed_or_name_only_role() -> None:
    computed = {name for names in COMPUTED_ROLES.values() for name in names} | {"rolling_avg"}
    named = {name for names in NAME_ONLY_ROLES.values() for name in names}

    assert set(ALIASES) <= computed | named


@pytest.mark.parametrize("spec_id", sorted(NAME_ONLY_ROLES))
def test_every_name_only_role_exists_in_its_spec_and_is_marked(spec_id: str) -> None:
    roles = {role.name: role for role in roles_of(spec_id)}
    pending = {name for spec, name in PENDING_ROLES if spec == spec_id}

    assert NAME_ONLY_ROLES[spec_id] - pending <= set(roles), spec_id
    assert {name for name, role in roles.items() if role.name_only} == NAME_ONLY_ROLES[spec_id] & set(roles)
    assert not any(role.name_only and role.computed for role in roles.values())
    # The proposed bullets parse as the optional roles they are meant to be, and get the mark the day they land.
    marked = {role.name: role for role in with_pending(spec_id)}
    assert NAME_ONLY_ROLES[spec_id] <= {name for name, role in marked.items() if role.name_only}
    assert all(not marked[name].required for name in pending)


def test_a_variadic_role_is_never_name_only() -> None:
    family = parse_roles(["`rsi1, rsi2, ...` (numeric) - one RSI per series"])

    assert [role.name_only for role in mark_name_only(family, "indicator-rsi")] == [False]


def test_every_role_worded_as_a_formula_is_computed_or_named_as_data() -> None:
    """The audit over the catalogue: a role the plot can compute but nothing marks is required, and the default
    bindings fill it with any number column (`Open`, `High` and `Low` as the three SMAs of `indicator-sma`). A new
    spec worded so fails here until `COMPUTED_ROLES` lists the role or `DATA_ROLES` names it as data with the
    reason."""
    flagged = {
        (spec_id, role.name): role.computed
        for spec_id, roles in catalogue_roles().items()
        for role in roles
        if worded_as_derived(role, roles)
    }

    unmarked = sorted(key for key, computed in flagged.items() if not computed and key not in DATA_ROLES)
    assert unmarked == [], "list each in COMPUTED_ROLES (data/computed.py), or in DATA_ROLES here with the reason"
    assert sorted(key for key in DATA_ROLES if flagged.get(key) is not False) == []  # gone, renamed or now computed


def test_the_audit_finds_the_indicators_of_the_catalogue() -> None:
    """The wording check itself: every moving average, band, Ichimoku line and MACD part of the catalogue is found."""
    roles = catalogue_roles()
    found = {
        (spec_id, role.name) for spec_id in roles for role in roles[spec_id] if worded_as_derived(role, roles[spec_id])
    }

    for spec_id in ("indicator-sma", "indicator-ema", "indicator-ichimoku", "indicator-bollinger", "indicator-macd"):
        assert {(spec_id, name) for name in COMPUTED_ROLES[spec_id]} <= found, spec_id
    assert ("line-timeseries-rolling", "rolling_avg") in found
    listed = {(spec_id, name) for spec_id, names in COMPUTED_ROLES.items() for name in names}
    assert listed <= found  # every listed role is worded so that removing it from the list fails the audit


def test_the_adapter_prompt_knows_the_markers_of_the_brief() -> None:
    """The adapter computes an unbound computed role (from bound companions where given) and uses a bound one as it
    is: the prompt names the brief's exact markers, so "leave out what an unbound role needs" never drops it."""
    prompt = (Path(__file__).parents[4] / "agents" / "anyplot" / "prompts" / "adapter.md").read_text()
    role = computed_role("upper_band")

    assert "not bound: compute it in the plot code from the bound data" in describe_role(role)
    assert "bound: use its column as it is" in describe_role(role, bound=True)
    assert "build it on the bound sma" in describe_role(role, companions=["sma"])
    for marker in ("not bound: compute it in the plot code from the bound data", "bound: use its column as it is"):
        assert marker in prompt
    assert "build it on the bound ..." in prompt and "the spec:" in prompt


@pytest.mark.parametrize(
    ("role_name", "column"),
    [
        ("sma", "SMA 20"),
        ("sma", "sma20"),
        ("sma", "MA20"),
        ("sma", "MA(20)"),
        ("sma", "Gleitender Durchschnitt (20)"),
        ("sma", "Middle Band"),
        ("sma", "BBM_20_2.0"),
        ("sma", "Rolling Mean 20"),
        ("upper_band", "Upper Band"),
        ("upper_band", "BB Upper"),
        ("upper_band", "BBU_20_2.0"),
        ("upper_band", "Bollinger Oben"),
        ("upper_band", "Oberes Band"),
        ("upper_band", "Bande supérieure"),
        ("upper_band", "Banda superior"),
        ("upper_band", "Banda superiore"),
        ("lower_band", "BB Lower"),
        ("lower_band", "BBL_20_2.0"),
        ("lower_band", "Bollinger Unten"),
        ("lower_band", "Bande inférieure"),
        ("lower_band", "Banda inferior"),
        ("lower_band", "Banda inferiore"),
        ("ctl", "CTL"),
        ("ctl", "Fitness (CTL)"),
        ("ctl", "Chronic Load"),
        ("ctl", "Chronic Training Load"),
        ("ctl", "Chronische Trainingsbelastung"),
        ("atl", "Acute Load"),
        ("atl", "Fatigue (ATL)"),
        ("atl", "Ermüdung (Belastung)"),
        ("tsb", "Form (TSB)"),
        ("tsb", "Freshness"),
        ("tsb", "Frische"),
        ("tsb", "Training Stress Balance"),
        ("rolling_avg", "rollingAvg"),
        ("rolling_avg", "Rolling Mean"),
        ("rolling_avg", "MA7"),
        ("rolling_avg", "7-day average"),
        ("rolling_avg", "7d avg"),
        ("rolling_avg", "avg_7d"),
        ("rolling_avg", "7-Tage-Mittel"),
        ("sma_short", "SMA 20"),
        ("sma_short", "Short MA"),
        ("sma_medium", "MA(50)"),
        ("sma_long", "Long SMA"),
        ("sma_long", "200-day average"),
        ("ema_short", "EMA 12"),
        ("ema_short", "Fast EMA"),
        ("ema_long", "ewm_26"),
        ("ema_long", "Exponentieller Durchschnitt (26)"),
        ("tenkan_sen", "Tenkan-sen"),
        ("tenkan_sen", "Conversion Line"),
        ("kijun_sen", "Kijun"),
        ("kijun_sen", "Base Line"),
        ("senkou_span_a", "Senkou Span A"),
        ("senkou_span_a", "Leading Span A"),
        ("senkou_span_b", "SpanB"),
        ("chikou_span", "Lagging Span"),
        ("signal", "Signal Line"),
        ("signal", "MACD Signal"),
        ("signal", "MACDs_12_26_9"),
        ("histogram", "MACD Histogram"),
        ("histogram", "Hist"),
        ("histogram", "MACDh_12_26_9"),
        ("histogram", "MACD Oscillator"),
        ("ideal", "Ideal Burndown"),
        ("total_error", "Total Error"),
        ("temp_annual_mean", "Annual Mean Temperature"),
        ("precip_annual_total", "Annual Precipitation (mm)"),
        ("development_factor", "Age-to-Age Factor"),
        ("development_factor", "LDF"),
        ("cumulative_probability", "Median Rank"),
        ("cumulative_probability", "Unreliability F(t)"),
        ("final_value", "Prediction"),
        ("emv", "Expected Value"),
        ("pruned", "Pruned"),
    ],
)
def test_a_name_that_holds_the_value_matches(role_name: str, column: str) -> None:
    assert name_match(computed_role(role_name), column)


@pytest.mark.parametrize(
    ("role_name", "column"),
    [
        ("sma", "small"),
        ("sma", "Volume SMA"),
        ("sma", "Volume Moving Average"),
        ("sma", "SMA Upper Band"),
        ("sma", "Moving Average Convergence Divergence"),
        ("upper_band", "Upper"),
        ("upper_band", "Upper Shadow"),
        ("upper_band", "Upper Circuit Limit"),
        ("upper_band", "Upper_CI"),
        ("upper_band", "lower band"),
        ("lower_band", "Lower Shadow"),
        ("lower_band", "Lower Circuit Limit"),
        ("ctl", "Fitness"),
        ("ctl", "Fitness Age"),
        ("ctl", "Fitness Level"),
        ("atl", "Fatigue (RPE)"),
        ("atl", "Ermüdung"),
        ("tsb", "Form"),
        ("tsb", "Form Rating"),
        ("tsb", "Form_ID"),
        ("tsb", "tss"),
        ("rolling_avg", "Temperature"),
        ("rolling_avg", "rolling_std"),
        ("rolling_avg", "rolling_sum"),
        ("rolling_avg", "rolling_count"),
        ("rolling_avg", "Rolling Variance"),
        ("rolling_avg", "SMA Upper Band"),
        ("rolling_avg", "Moving Average Convergence Divergence"),
        ("rolling_avg", "Exponentially Weighted Moving Average"),
        ("sma", "Exponential Moving Average 20"),
        ("sma_short", "EMA 20"),
        ("sma_short", "Weighted Moving Average 20"),
        ("sma_short", "Long MA"),
        ("sma_medium", "SMA Upper Band"),
        ("sma_long", "Short SMA"),
        ("sma_long", "Open"),
        ("ema_short", "SMA 12"),
        ("ema_short", "Moving Average 12"),
        ("ema_long", "Fast EMA"),
        ("tenkan_sen", "Kijun-sen"),
        ("senkou_span_a", "Senkou Span B"),
        ("chikou_span", "Close"),
        ("signal", "MACD"),
        ("signal", "Buy Signal"),
        ("signal", "Trading Signal"),
        ("signal", "Bullish Signal"),
        ("signal", "MACD Histogram"),
        ("histogram", "MACD Signal"),
        ("development_factor", "Development Period"),
        ("development_factor", "Age"),
        ("cumulative_probability", "Survival Probability"),
        ("cumulative_probability", "Rank"),
        ("final_value", "Base Prediction"),
        ("final_value", "Expected Value"),
        ("emv", "Payoff"),
    ],
)
def test_a_name_that_holds_something_else_does_not(role_name: str, column: str) -> None:
    """Review of 2026-10-15: candle shadows, circuit limits, a volume average, a fitness age, an RPE, a MACD; and an
    EMA for an SMA, the other window's size word, a trade signal, a survival probability, a SHAP base value."""
    assert not name_match(computed_role(role_name), column)


@pytest.mark.parametrize(
    ("role_name", "column"),
    [
        ("macd", "MACD"),
        ("macd", "macd"),
        ("macd", "MACD_12_26_9"),
        ("macd", "MACD Line"),
        ("macd", "MACD (12, 26)"),
        ("rsi", "RSI"),
        ("rsi", "RSI_14"),
        ("rsi", "RSI (14)"),
        ("rsi", "Relative Strength Index"),
        ("close", "Close"),
        ("close", "Adj Close"),
        ("close", "Closing Price"),
        ("close", "Price"),
        ("close", "Schlusskurs"),
        ("sample_mean", "Mean"),
        ("sample_mean", "X-bar"),
        ("sample_mean", "Xbar"),
        ("sample_mean", "Average"),
        ("sample_mean", "Sample Mean"),
        ("sample_mean", "Mittelwert"),
        ("sample_range", "Range"),
        ("sample_range", "R"),
        ("sample_range", "Sample Range"),
        ("sample_range", "Spannweite"),
        ("ucl", "UCL"),
        ("ucl", "Upper Control Limit"),
        ("ucl", "Obere Eingriffsgrenze"),
        ("lcl", "LCL"),
        ("lcl", "Lower Limit"),
        ("center_line", "CL"),
        ("center_line", "Center"),
        ("center_line", "Centre Line"),
        ("center_line", "X-bar-bar"),
        ("center_line", "Grand Mean"),
        ("center_line", "R-bar"),
        ("upper_warning", "UWL"),
        ("upper_warning", "Upper Warning Limit"),
        ("lower_warning", "LWL"),
        ("subgroup_size", "n"),
        ("subgroup_size", "Subgroup Size"),
        ("subgroup_size", "Sample Size"),
    ],
)
def test_a_name_that_holds_a_name_only_value_matches(role_name: str, column: str) -> None:
    assert name_match(name_only_role(role_name), column)


@pytest.mark.parametrize(
    ("role_name", "column"),
    [
        ("macd", "Open"),
        ("macd", "MACD Signal"),
        ("macd", "MACD Histogram"),
        ("macd", "MACD Hist"),
        ("macd", "MACDs_12_26_9"),
        ("macd", "MACDh_12_26_9"),
        ("macd", "MACD Oscillator"),
        ("rsi", "Open"),
        ("rsi", "Value"),
        ("rsi", "Stoch RSI"),
        ("rsi", "StochRSI"),
        ("rsi", "RSI MA"),
        ("rsi", "RSI Signal"),
        ("rsi", "Relative Strength"),
        ("close", "Open"),
        ("close", "Open Price"),
        ("close", "Close SMA 20"),
        ("close", "Price Change"),
        ("close", "Volume"),
        ("sample_mean", "X1"),
        ("sample_mean", "Measurement"),
        ("sample_mean", "Mean Range"),
        ("sample_mean", "Average Range"),
        ("sample_mean", "Grand Mean"),
        ("sample_mean", "X-bar-bar"),
        ("sample_mean", "X-bar UCL"),
        ("sample_mean", "Moving Average"),
        ("sample_range", "Moving Range"),
        ("sample_range", "R-bar"),
        ("sample_range", "R UCL"),
        ("sample_range", "Range LCL"),
        ("ucl", "Upper Spec Limit"),
        ("ucl", "USL"),
        ("ucl", "Upper Warning Limit"),
        ("ucl", "LCL"),
        ("lcl", "Lower Spec Limit"),
        ("lcl", "Lower Warning Limit"),
        ("center_line", "UCL"),
        ("center_line", "X-bar"),
        ("center_line", "Upper Center"),
        ("upper_warning", "LWL"),
        ("lower_warning", "Upper Warning"),
        ("subgroup_size", "Sample"),
    ],
)
def test_a_name_that_holds_another_value_is_no_name_only_match(role_name: str, column: str) -> None:
    """A price is no MACD line or RSI, a raw measurement no sample mean, a tolerance no control limit, an R-chart
    center line no range."""
    assert not name_match(name_only_role(role_name), column)


class TestBollinger:
    def test_bands_in_the_data_are_bound(self) -> None:
        # `table` fills each column above the one before it: the lower band stands first, so it lies below the
        # upper one, as a band does (a lower band above the upper one is never bound, `bounds.py`).
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(table("date,close,SMA 20,Lower Band,Upper Band")).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [
            ("date", "date"),
            ("close", "close"),
            ("sma", "SMA 20"),
            ("upper_band", "Upper Band"),
            ("lower_band", "Lower Band"),
        ]
        check = check_bindings(bindings, roles, data)
        assert check.complete and check.warnings == []

    @pytest.mark.parametrize(
        ("upper", "lower"),
        [
            ("SMA Upper Band", "SMA Lower Band"),
            ("Moving Average Upper Band", "Moving Average Lower Band"),
            ("Gleitender Durchschnitt oberes Band", "Gleitender Durchschnitt unteres Band"),
            ("BBU_20_2.0", "BBL_20_2.0"),
        ],
    )
    def test_band_qualified_names_are_bands_not_the_average(self, upper: str, lower: str) -> None:
        """A band named after the average is a band: `sma` never takes it and stays computed."""
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(table(f"date,close,{lower},{upper}")).profile  # the lower band below the upper one

        assert pairs(default_bindings(roles, data)) == [
            ("date", "date"),
            ("close", "close"),
            ("upper_band", upper),
            ("lower_band", lower),
        ]

    def test_candle_columns_are_no_bands(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(table("date,close,Upper Shadow,Lower Shadow,Volume SMA")).profile

        assert pairs(default_bindings(roles, data)) == [("date", "date"), ("close", "close")]

    def test_only_prices_leave_the_bands_to_the_plot(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset("date,price\n2024-01-01,100.5\n2024-01-02,101.5\n2024-01-03,99.0\n").profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("close", "price")]
        check = check_bindings(bindings, roles, data)
        assert check.complete and check.missing_roles == []

    def test_a_matching_column_never_takes_the_only_price(self) -> None:
        """Review of 2026-10-15: `close` needs the one number column even when its name reads like an average."""
        roles = roles_of("indicator-bollinger")
        data = parse_dataset("date,SMA 20\n2024-01-01,100.5\n2024-01-02,101.5\n2024-01-03,99.0\n").profile

        assert pairs(default_bindings(roles, data)) == [("date", "date"), ("close", "SMA 20")]

    def test_the_required_role_takes_the_unclaimed_column_first(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(table("date,SMA 20,price")).profile

        assert pairs(default_bindings(roles, data)) == [("date", "date"), ("close", "price"), ("sma", "SMA 20")]

    def test_the_spec_window_wins_a_tie_and_another_window_is_a_warning(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(table("date,close,SMA 50,SMA 20")).profile

        bindings = default_bindings(roles, data)
        assert ("sma", "SMA 20") in pairs(bindings)
        assert check_bindings(bindings, roles, data).warnings == []

        only_200 = parse_dataset(table("date,close,SMA 200")).profile
        bound = default_bindings(roles, only_200)
        assert ("sma", "SMA 200") in pairs(bound)
        assert check_bindings(bound, roles, only_200).warnings == [
            "sma: column 'SMA 200' holds a 200-period value; the spec's convention is 20, "
            "so the plot shows the column's window"
        ]

    def test_window_lines(self) -> None:
        assert window_line("sma", "BBM_20_2.0") is None
        assert window_line("upper_band", "BBU_50_2.0") is not None
        assert window_line("sma", "SMA") is None  # no window named, nothing to say
        assert window_line("rolling_avg", "MA 200") is None  # the spec names no single window
        assert window_line("ema_short", "EMA 50") is None and window_line("ema_long", "EMA 200") is None
        assert window_line("ema_short", "EMA 20") == (
            "ema_short: column 'EMA 20' holds a 20-period value; the spec's convention is 12 or 50, "
            "so the plot shows the column's window"
        )

    def test_window_ranks_and_open_windows(self) -> None:
        ema_short = computed_role("ema_short")

        assert [window_rank(ema_short, name) for name in ("EMA 12", "EMA 50", "EMA", "EMA 20")] == [0, 1, 2, 3]
        assert [window_rank(computed_role("sma"), name) for name in ("SMA 20", "SMA", "SMA 50")] == [0, 1, 2]
        assert open_window("ema_long", {}) == 26 and open_window("ema_long", {"ema_short": "EMA 50"}) == 200
        assert open_window("ema_short", {"ema_long": "EMA 26"}) == 12 and open_window("ema_short", {}) == 12
        assert open_window("sma_long", {"sma_short": "SMA 10"}) == 200 and open_window("histogram", {}) is None


class TestTrainingLoad:
    def test_daily_load_alone_is_enough(self) -> None:
        roles = roles_of("line-training-load-pmc")
        data = parse_dataset("date,tss\n2024-01-01,80\n2024-01-02,0\n2024-01-03,120\n").profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("tss", "tss")]
        assert check_bindings(bindings, roles, data).complete

    def test_an_export_with_fitness_and_fatigue_binds_them(self) -> None:
        roles = roles_of("line-training-load-pmc")
        data = parse_dataset(table("date,TSS,Fitness (CTL),Fatigue (ATL),Form (TSB)")).profile

        assert pairs(default_bindings(roles, data)) == [
            ("date", "date"),
            ("tss", "TSS"),
            ("ctl", "Fitness (CTL)"),
            ("atl", "Fatigue (ATL)"),
            ("tsb", "Form (TSB)"),
        ]

    def test_scores_and_ratings_are_no_loads(self) -> None:
        roles = roles_of("line-training-load-pmc")
        data = parse_dataset(table("date,tss,Fitness Age,Fatigue (RPE),Form Rating")).profile

        assert pairs(default_bindings(roles, data)) == [("date", "date"), ("tss", "tss")]


class TestRollingAverage:
    def test_a_band_column_is_no_rolling_average(self) -> None:
        roles = roles_of("line-timeseries-rolling")
        data = parse_dataset(table("date,value,SMA Upper Band")).profile

        assert pairs(default_bindings(roles, data)) == [("date", "date"), ("value", "value")]

    def test_a_week_average_is_bound(self) -> None:
        roles = roles_of("line-timeseries-rolling")
        data = parse_dataset(table("date,value,7-day average")).profile

        assert pairs(default_bindings(roles, data)) == [
            ("date", "date"),
            ("value", "value"),
            ("rolling_avg", "7-day average"),
        ]


class TestMovingAverages:
    def test_a_price_table_binds_the_close_and_leaves_the_averages_to_the_plot(self) -> None:
        """`Open`, `High` and `Low` are prices, not the three SMAs: unmarked roles took them."""
        roles = roles_of("indicator-sma")
        data = parse_dataset(stock()).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("close", "Close")]
        check = check_bindings(bindings, roles, data)
        assert check.complete and check.missing_roles == [] and check.warnings == []

    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            ("SMA 20,SMA 50,SMA 200", {"sma_short": "SMA 20", "sma_medium": "SMA 50", "sma_long": "SMA 200"}),
            ("SMA 200,SMA 50,SMA 20", {"sma_short": "SMA 20", "sma_medium": "SMA 50", "sma_long": "SMA 200"}),
            ("MA50,MA20", {"sma_short": "MA20", "sma_medium": "MA50"}),
            ("Long MA,Short MA", {"sma_short": "Short MA", "sma_long": "Long MA"}),
            ("EMA 20,Weighted Moving Average", {}),
        ],
    )
    def test_each_average_takes_the_column_of_its_window(self, header: str, expected: dict[str, str]) -> None:
        roles = roles_of("indicator-sma")
        data = parse_dataset(stock(header)).profile

        bindings = default_bindings(roles, data)
        assert {role: column for role, column in pairs(bindings) if role.startswith("sma")} == expected
        assert check_bindings(bindings, roles, data).warnings == []

    def test_another_window_is_bound_with_a_warning(self) -> None:
        roles = roles_of("indicator-sma")
        data = parse_dataset(stock("SMA 10")).profile

        bindings = default_bindings(roles, data)
        assert ("sma_short", "SMA 10") in pairs(bindings)
        assert check_bindings(bindings, roles, data).warnings == [
            "sma_short: column 'SMA 10' holds a 10-period value; the spec's convention is 20, "
            "so the plot shows the column's window"
        ]


class TestExponentialAverages:
    def test_a_price_table_leaves_both_averages_to_the_plot(self) -> None:
        roles = roles_of("indicator-ema")
        data = parse_dataset(stock()).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("close", "Close")]
        assert check_bindings(bindings, roles, data).complete

    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            ("EMA 12,EMA 26", {"ema_short": "EMA 12", "ema_long": "EMA 26"}),
            ("EMA 26,EMA 12", {"ema_short": "EMA 12", "ema_long": "EMA 26"}),
            ("Slow EMA,Fast EMA", {"ema_short": "Fast EMA", "ema_long": "Slow EMA"}),
            ("SMA 12,Moving Average 26", {}),
            ("EMA 50,EMA 200", {"ema_short": "EMA 50", "ema_long": "EMA 200"}),
            ("EMA 200,EMA 50,EMA 26,EMA 12", {"ema_short": "EMA 12", "ema_long": "EMA 26"}),
        ],
    )
    def test_each_average_takes_its_column(self, header: str, expected: dict[str, str]) -> None:
        """Both pairs the spec names bind without a warning, the golden cross's 50 and 200 too (the spec's first
        application); with both pairs in the data, its example's 12 and 26 win."""
        roles = roles_of("indicator-ema")
        data = parse_dataset(stock(header)).profile

        bindings = default_bindings(roles, data)
        assert {role: column for role, column in pairs(bindings) if role.startswith("ema")} == expected
        assert check_bindings(bindings, roles, data).warnings == []


class TestIchimoku:
    def test_a_price_table_binds_the_prices_and_leaves_the_lines_to_the_plot(self) -> None:
        roles = roles_of("indicator-ichimoku")
        data = parse_dataset(stock()).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [
            ("date", "date"),
            ("open", "Open"),
            ("high", "High"),
            ("low", "Low"),
            ("close", "Close"),
        ]
        check = check_bindings(bindings, roles, data)
        assert check.complete and check.missing_roles == []

    def test_an_export_with_the_lines_binds_them(self) -> None:
        roles = roles_of("indicator-ichimoku")
        data = parse_dataset(stock("Tenkan-sen,Kijun-sen,Senkou Span A,Senkou Span B,Chikou Span")).profile

        assert pairs(default_bindings(roles, data))[5:] == [
            ("tenkan_sen", "Tenkan-sen"),
            ("kijun_sen", "Kijun-sen"),
            ("senkou_span_a", "Senkou Span A"),
            ("senkou_span_b", "Senkou Span B"),
            ("chikou_span", "Chikou Span"),
        ]


class TestMacd:
    MACD = "date,{}\n2024-03-04,0.41,0.35,0.06\n2024-03-05,0.52,0.38,0.14\n2024-03-06,0.47,0.40,0.07\n"

    def test_the_macd_line_alone_is_enough(self) -> None:
        roles = roles_of("indicator-macd")
        data = parse_dataset("date,MACD\n2024-03-04,0.41\n2024-03-05,0.52\n2024-03-06,-0.12\n").profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("macd", "MACD")]
        check = check_bindings(bindings, roles, data)
        assert check.complete and check.missing_roles == []

    @pytest.mark.parametrize(
        "header", ["MACD,MACD Signal,MACD Hist", "MACD_12_26_9,MACDs_12_26_9,MACDh_12_26_9", "macd,signal,histogram"]
    )
    def test_an_export_binds_each_part(self, header: str) -> None:
        roles = roles_of("indicator-macd")
        macd, signal, histogram = header.split(",")

        assert pairs(default_bindings(roles, parse_dataset(self.MACD.format(header)).profile)) == [
            ("date", "date"),
            ("macd", macd),
            ("signal", signal),
            ("histogram", histogram),
        ]

    def test_a_trade_signal_is_no_signal_line(self) -> None:
        roles = roles_of("indicator-macd")
        data = parse_dataset("date,MACD,Buy Signal\n2024-03-04,0.41,1\n2024-03-05,0.52,0\n2024-03-06,0.47,1\n").profile

        assert pairs(default_bindings(roles, data)) == [("date", "date"), ("macd", "MACD")]

    # These hold before and after the spec change that adds an optional `close` (`PENDING_ROLES`): a spec PR
    # cannot change a test, so none of them pins what `close` binds.
    def test_a_price_table_leaves_the_macd_line_missing(self) -> None:
        """Before: `macd` took `Open`, the check was complete, and the plot drew the opening price as the MACD."""
        roles = roles_of("indicator-macd")
        data = parse_dataset(stock()).profile

        bindings = default_bindings(roles, data)
        assert {role for role, _ in pairs(bindings)} <= {"date", "close"}
        check = check_bindings(bindings, roles, data)
        assert not check.complete and check.missing_roles == ["macd"]

    def test_the_pandas_ta_line_alone_is_enough(self) -> None:
        roles = roles_of("indicator-macd")
        data = parse_dataset(table("date,MACD_12_26_9")).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("macd", "MACD_12_26_9")]
        assert check_bindings(bindings, roles, data).complete

    def test_a_signal_line_is_never_the_macd_line(self) -> None:
        roles = roles_of("indicator-macd")
        data = parse_dataset(table("date,Close,MACD Signal")).profile

        bindings = default_bindings(roles, data)
        assert ("signal", "MACD Signal") in pairs(bindings) and "macd" not in dict(pairs(bindings))
        assert check_bindings(bindings, roles, data).missing_roles == ["macd"]


class TestRsi:
    @pytest.mark.parametrize(
        ("header", "column"), [("date,RSI", "RSI"), ("date,Close,RSI", "RSI"), ("date,RSI_14", "RSI_14")]
    )
    def test_an_rsi_column_binds(self, header: str, column: str) -> None:
        roles = roles_of("indicator-rsi")
        data = parse_dataset(table(header)).profile

        bindings = default_bindings(roles, data)
        assert dict(pairs(bindings))["rsi"] == column
        assert check_bindings(bindings, roles, data).complete

    @pytest.mark.parametrize("data", [stock(), table("date,Value"), table("date,Stoch RSI")])
    def test_a_column_not_named_so_leaves_the_rsi_missing(self, data: str) -> None:
        """A price, a bare value or a stochastic RSI is no RSI: before, `rsi` took the first number column."""
        roles = roles_of("indicator-rsi")
        profile = parse_dataset(data).profile

        bindings = default_bindings(roles, profile)
        assert {role for role, _ in pairs(bindings)} <= {"date", "close"}
        assert check_bindings(bindings, roles, profile).missing_roles == ["rsi"]

    def test_the_spec_window_wins_a_tie(self) -> None:
        roles = roles_of("indicator-rsi")
        data = parse_dataset(table("date,RSI 7,RSI 14")).profile

        bindings = default_bindings(roles, data)
        assert ("rsi", "RSI 14") in pairs(bindings)
        assert check_bindings(bindings, roles, data).warnings == []  # a name-only role carries no window warning


LIMIT_VALUES = {"upper": 11.4, "ucl": 11.4, "uwl": 11.1, "lower": 9.6, "lcl": 9.6, "lwl": 9.9}
"""Invented control limits: the upper ones above the lower ones, as on a real chart."""


def spc(header: str, constant: tuple[str, ...] = (), rows: int = 6) -> str:
    """An invented subgroup table: the sample number first, then a number per column; `constant` columns (limits, a
    subgroup size) hold one value on every row, as a control chart's limits do."""
    names = header.split(",")
    lines = [header]
    for row in range(rows):
        cells = [str(row + 1)]
        for index, name in enumerate(names[1:]):
            if name in constant:
                words = name.lower().split()
                cells.append(str(next((LIMIT_VALUES[word] for word in words if word in LIMIT_VALUES), 10.5)))
            else:
                cells.append(f"{10 + 0.1 * row + 0.37 * index:.2f}")
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


class TestSpc:
    def test_raw_subgroup_measurements_leave_the_summary_roles_missing(self) -> None:
        """Before: `X1` to `X5` became the sample mean, the range, both limits and the center line, complete."""
        roles = roles_of("spc-xbar-r")
        data = parse_dataset(spc("Sample,X1,X2,X3,X4,X5")).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("sample_id", "Sample")]
        check = check_bindings(bindings, roles, data)
        assert check.missing_roles == ["sample_mean", "sample_range", "ucl", "lcl", "center_line"]

    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            (
                "Sample,Mean,Range,UCL,LCL,CL",
                {"sample_mean": "Mean", "sample_range": "Range", "ucl": "UCL", "lcl": "LCL", "center_line": "CL"},
            ),
            (
                "Sample,X-bar,R,UCL,LCL,Center",
                {"sample_mean": "X-bar", "sample_range": "R", "ucl": "UCL", "lcl": "LCL", "center_line": "Center"},
            ),
            (
                "Sample,Average,Range,X-bar-bar,Upper Control Limit,Lower Control Limit,UWL,LWL",
                {
                    "sample_mean": "Average",
                    "sample_range": "Range",
                    "ucl": "Upper Control Limit",
                    "lcl": "Lower Control Limit",
                    "center_line": "X-bar-bar",
                    "upper_warning": "UWL",
                    "lower_warning": "LWL",
                },
            ),
        ],
    )
    def test_a_summary_table_with_its_limits_binds_by_name(self, header: str, expected: dict[str, str]) -> None:
        """The limits are the same on every row: a name-only role takes such a constant column all the same."""
        roles = roles_of("spc-xbar-r")
        statistics = {expected["sample_mean"], expected["sample_range"]}
        limits = tuple(name for name in expected.values() if name not in statistics)
        data = parse_dataset(spc(header, constant=limits)).profile

        bindings = default_bindings(roles, data)
        assert dict(pairs(bindings)) == {"sample_id": "Sample", **expected}
        assert check_bindings(bindings, roles, data).complete

    def test_a_summary_table_without_limits_stalls_as_before(self) -> None:
        roles = roles_of("spc-xbar-r")
        data = parse_dataset(spc("Sample,Mean,Range")).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("sample_id", "Sample"), ("sample_mean", "Mean"), ("sample_range", "Range")]
        assert check_bindings(bindings, roles, data).missing_roles == ["ucl", "lcl", "center_line"]

    def test_tolerances_are_no_control_limits(self) -> None:
        roles = roles_of("spc-xbar-r")
        data = parse_dataset(spc("Sample,Mean,Range,USL,Upper Spec Limit,Target", constant=("USL", "Target"))).profile

        bound = dict(pairs(default_bindings(roles, data)))
        assert not {"ucl", "lcl", "center_line", "upper_warning", "lower_warning"} & set(bound)

    def test_the_names_of_the_spec_bind_by_their_names(self) -> None:
        roles = roles_of("spc-xbar-r")
        data = parse_dataset(sample_table([role for role in roles if role.required])).profile

        assert check_bindings(default_bindings(roles, data), roles, data).complete


class TestPendingRoles:
    """`close` and `subgroup_size` as the spec changes add them: optional, and bound only by name."""

    def test_a_bare_value_is_no_closing_price(self) -> None:
        """An optional number role takes any free number column: unmarked, `Value` of an RSI export would be `close`."""
        roles = with_pending("indicator-rsi")
        data = parse_dataset(table("date,Value")).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date")]
        assert check_bindings(bindings, roles, data).missing_roles == ["rsi"]

    @pytest.mark.parametrize("spec_id", ["indicator-macd", "indicator-rsi"])
    def test_a_price_table_binds_the_close_and_still_misses_the_indicator(self, spec_id: str) -> None:
        roles = with_pending(spec_id)
        data = parse_dataset(stock()).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("close", "Close")]
        assert check_bindings(bindings, roles, data).missing_roles == ["macd" if spec_id == "indicator-macd" else "rsi"]

    def test_the_subgroup_size_binds_by_name_and_never_a_measurement(self) -> None:
        roles = with_pending("spc-xbar-r")

        wide = parse_dataset(spc("Sample,X1,X2,X3,X4,X5")).profile
        assert "subgroup_size" not in dict(pairs(default_bindings(roles, wide)))
        named = parse_dataset(spc("Sample,n,Mean,Range", constant=("n",))).profile
        assert dict(pairs(default_bindings(roles, named)))["subgroup_size"] == "n"


class TestNoOtherFill:
    """A name-only role left open takes no column the code adds by itself unless the column is named for it."""

    def test_a_conversion_is_offered_only_for_a_column_named_for_it(self) -> None:
        """Text columns of numbers (`$5`): the RSI's converts for `rsi`, a price's never does."""
        roles = roles_of("indicator-rsi")
        parsed = parse_dataset("date,Open,RSI\n2024-01-01,$5,$45\n2024-01-02,7,51\n2024-01-03,$12,$48\n")

        offered = candidates(default_bindings(roles, parsed.profile), roles, parsed.profile, parsed)
        assert [(candidate.role, getattr(candidate, "name", None)) for candidate in offered] == [
            ("rsi", "RSI (number)")
        ]
        price = parse_dataset("date,Open\n2024-01-01,$5\n2024-01-02,7\n2024-01-03,$12\n")
        assert candidates(default_bindings(roles, price.profile), roles, price.profile, price) == []

    def test_a_converted_column_fills_the_role_only_by_name(self) -> None:
        roles = roles_of("indicator-macd")
        date = [Binding(role="date", column="date")]
        data = parse_dataset(table("date,Open (number),MACD (number)")).profile

        carried = carry_bindings(date, roles, data, converted={"Open (number)": "Open", "MACD (number)": "MACD"})
        assert ("macd", "MACD (number)") in pairs(carried)
        price = parse_dataset(table("date,Open (number)")).profile
        assert pairs(carry_bindings(date, roles, price, converted={"Open (number)": "Open"})) == [("date", "date")]

    def test_the_filled_bindings_keep_the_rule(self) -> None:
        roles = roles_of("indicator-macd")
        data = parse_dataset(stock("MACD")).profile

        filled = filled_bindings([Binding(role="date", column="date")], roles, data)
        assert ("macd", "MACD") in pairs(filled)
        assert ("macd", "Open") not in pairs(filled_bindings([], roles, parse_dataset(stock()).profile))


@pytest.mark.parametrize("spec_id", sorted(COMPUTED_ROLES))
def test_without_the_computed_columns_the_bindings_are_complete(spec_id: str) -> None:
    """Every listed spec: a table with a column for each other role binds them, leaves every computed role to the
    plot and misses nothing, so the run starts and the adapter computes the rest."""
    roles = roles_of(spec_id)
    data = parse_dataset(sample_table([role for role in roles if not role.computed])).profile

    bindings = default_bindings(roles, data)
    assert not {binding.role for binding in bindings} & COMPUTED_ROLES[spec_id]
    check = check_bindings(bindings, roles, data)
    assert check.missing_roles == [] and check.complete, check


class TestBrief:
    def test_a_computed_role_keeps_its_formula_and_window(self) -> None:
        sma = next(role for role in roles_of("indicator-bollinger") if role.name == "sma")

        assert "the spec: Simple moving average (middle band), typically 20-period" in describe_role(sma)

    def test_open_bands_are_built_on_the_bound_middle_band(self) -> None:
        upper = next(role for role in roles_of("indicator-bollinger") if role.name == "upper_band")
        line = describe_role(upper, companions=["sma"])

        assert line.startswith(
            "upper_band (numeric, not bound: compute it in the plot code from the bound data; "
            "build it on the bound sma where the spec relates them, not independently; the spec: "
        )

    def test_the_adapter_is_told_to_compute_the_open_averages(self) -> None:
        """The adapter's spec brief (`pipeline`, `spec_brief(view)`) for a price table: the close is bound, and each
        SMA is computed in the plot code with the spec's window, so the plot draws all three lines."""
        snapshot = snapshot_from_repo("indicator-sma", "matplotlib")
        bindings = default_bindings(snapshot.roles(), parse_dataset(stock()).profile)
        brief = spec_brief(SessionView("indicator-sma", "matplotlib", "en", snapshot, "code", [], None, bindings))

        assert "date (datetime, required); close (numeric, required)" in brief
        for name, window, spec in (
            ("sma_short", 20, "Short-term SMA (e.g., 20-period)"),
            ("sma_medium", 50, "Medium-term SMA (e.g., 50-period)"),
            ("sma_long", 200, "Long-term SMA (e.g., 200-period)"),
        ):
            assert (
                f"{name} (numeric, not bound: compute it in the plot code from the bound data with a {window}-period "
                f"window; the spec: {spec})"
            ) in brief

    @pytest.mark.parametrize(
        ("header", "windows"),
        [("", {"ema_short": 12, "ema_long": 26}), ("EMA 50", {"ema_long": 200}), ("EMA 26", {"ema_short": 12})],
    )
    def test_an_open_ema_names_the_window_of_its_pair(self, header: str, windows: dict[str, int]) -> None:
        """The long EMA's bullet says "e.g., 50-day" while the example and the code say 26: the brief names the
        window, and a bound `EMA 50` makes the open long EMA the golden cross's 200."""
        snapshot = snapshot_from_repo("indicator-ema", "matplotlib")
        bindings = default_bindings(snapshot.roles(), parse_dataset(stock(header)).profile)
        brief = spec_brief(SessionView("indicator-ema", "matplotlib", "en", snapshot, "code", [], None, bindings))

        for name, window in windows.items():
            assert f"{name} (numeric, not bound: compute it in the plot code from the bound data with a {window}-" in (
                brief
            )

    def test_an_open_band_beside_its_bound_middle_band_names_no_window(self) -> None:
        """The bands follow the bound average's window, whatever it is: the companions say so, not a number."""
        upper = next(role for role in roles_of("indicator-bollinger") if role.name == "upper_band")

        assert "-period window" not in describe_role(upper, companions=["sma"], window=20)
        assert "with a 20-period window; the spec: " in describe_role(upper, window=20)

    def test_open_ichimoku_spans_are_built_on_the_bound_lines(self) -> None:
        snapshot = snapshot_from_repo("indicator-ichimoku", "matplotlib")
        bindings = default_bindings(snapshot.roles(), parse_dataset(stock("Tenkan-sen,Kijun-sen")).profile)
        brief = spec_brief(SessionView("indicator-ichimoku", "matplotlib", "en", snapshot, "code", [], None, bindings))

        assert "tenkan_sen (numeric, bound: use its column as it is, do not compute it; the spec: " in brief
        assert (
            "senkou_span_a (numeric, not bound: compute it in the plot code from the bound data; build it on the "
            "bound tenkan_sen, kijun_sen where the spec relates them, not independently; the spec: Leading Span A"
        ) in brief
        assert "chikou_span (numeric, not bound: compute it in the plot code from the bound data; the spec: " in brief

    def test_independent_averages_are_not_built_on_each_other(self) -> None:
        """A bound `SMA 20` says nothing about the 50- and 200-period averages: each is computed from `close`."""
        snapshot = snapshot_from_repo("indicator-sma", "matplotlib")
        bindings = default_bindings(snapshot.roles(), parse_dataset(stock("SMA 20")).profile)
        brief = spec_brief(SessionView("indicator-sma", "matplotlib", "en", snapshot, "code", [], None, bindings))

        assert "sma_short (numeric, bound: use its column as it is" in brief
        assert "build it on the bound" not in brief

    def test_a_bound_signal_line_builds_the_histogram(self) -> None:
        snapshot = snapshot_from_repo("indicator-macd", "matplotlib")
        data = parse_dataset("date,MACD,Signal\n2024-03-04,0.41,0.35\n2024-03-05,0.52,0.38\n").profile
        brief = spec_brief(
            SessionView(
                "indicator-macd",
                "matplotlib",
                "en",
                snapshot,
                "code",
                [],
                None,
                default_bindings(snapshot.roles(), data),
            )
        )

        assert (
            "histogram (numeric, not bound: compute it in the plot code from the bound data; build it on the bound signal"
            in (brief)
        )


@pytest.mark.parametrize("spec_id", sorted(COMPANIONS))
def test_companions_relate_computed_roles_of_their_spec(spec_id: str) -> None:
    listed = COMPUTED_ROLES[spec_id]

    for role_name, related in COMPANIONS[spec_id].items():
        assert role_name in listed and related <= listed - {role_name}, (spec_id, role_name)
