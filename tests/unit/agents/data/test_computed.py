"""Tests for agents/anyplot/data/computed.py: the roles the plot can compute, bound when the data has them."""

from pathlib import Path

import pytest

from agents.anyplot.briefs import describe_role
from agents.anyplot.data.bindings import check_bindings, default_bindings
from agents.anyplot.data.computed import ALIASES, COMPUTED_ROLES, name_match, window_line
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.roles import DataRole
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.schemas import Binding


def roles_of(spec_id: str) -> list[DataRole]:
    return snapshot_from_repo(spec_id, "matplotlib").roles()


def pairs(bindings: list[Binding]) -> list[tuple[str, str]]:
    return [(binding.role, binding.column) for binding in bindings]


def computed_role(name: str) -> DataRole:
    return DataRole(name=name, kinds=("numeric",), required=True, variadic=False, description="", computed=True)


def table(header: str, rows: int = 3) -> str:
    """A table of `header` with dates in the first column and distinct numbers in the others."""
    names = header.split(",")
    lines = [header]
    for row in range(rows):
        cells = [f"2024-01-0{row + 1}"] + [f"{100 + 7 * index + row * 1.5:.1f}" for index in range(len(names) - 1)]
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("spec_id", sorted(COMPUTED_ROLES))
def test_every_listed_role_exists_in_its_spec_and_is_marked(spec_id: str) -> None:
    roles = {role.name: role for role in roles_of(spec_id)}

    assert COMPUTED_ROLES[spec_id] <= set(roles), spec_id
    assert {name for name, role in roles.items() if role.computed} == COMPUTED_ROLES[spec_id]


def test_the_bullet_prefix_still_marks_the_rolling_average() -> None:
    assert [role.name for role in roles_of("line-timeseries-rolling") if role.computed] == ["rolling_avg"]


def test_every_alias_names_a_computed_role() -> None:
    computed = {name for names in COMPUTED_ROLES.values() for name in names} | {"rolling_avg"}

    assert set(ALIASES) == computed


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
    ],
)
def test_a_name_that_holds_something_else_does_not(role_name: str, column: str) -> None:
    """Review of 2026-10-15: candle shadows, circuit limits, a volume average, a fitness age, an RPE, a MACD."""
    assert not name_match(computed_role(role_name), column)


class TestBollinger:
    def test_bands_in_the_data_are_bound(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(table("date,close,SMA 20,Upper Band,Lower Band")).profile

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
        data = parse_dataset(table(f"date,close,{upper},{lower}")).profile

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
