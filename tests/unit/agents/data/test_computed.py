"""Tests for agents/anyplot/data/computed.py: the roles the plot can compute, bound when the data has them."""

from pathlib import Path

import pytest

from agents.anyplot.briefs import describe_role
from agents.anyplot.data.bindings import check_bindings, default_bindings
from agents.anyplot.data.computed import ALIASES, COMPUTED_ROLES, name_match
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.roles import DataRole
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.schemas import Binding


def roles_of(spec_id: str) -> list[DataRole]:
    return snapshot_from_repo(spec_id, "matplotlib").roles()


def pairs(bindings: list[Binding]) -> list[tuple[str, str]]:
    return [(binding.role, binding.column) for binding in bindings]


@pytest.mark.parametrize("spec_id", sorted(COMPUTED_ROLES))
def test_every_listed_role_exists_in_its_spec_and_is_marked(spec_id: str) -> None:
    roles = {role.name: role for role in roles_of(spec_id)}

    assert COMPUTED_ROLES[spec_id] <= set(roles), spec_id
    assert {name for name, role in roles.items() if role.computed} == COMPUTED_ROLES[spec_id]


def test_the_bullet_prefix_still_marks_the_rolling_average() -> None:
    assert [role.name for role in roles_of("line-timeseries-rolling") if role.computed] == ["rolling_avg"]


def test_the_adapter_prompt_knows_both_markers_of_the_brief() -> None:
    """The adapter computes an unbound computed role and uses a bound one unchanged: the prompt names the brief's
    exact markers, so the general "leave out what an unbound role needs" rule does not drop the indicator."""
    role = DataRole(name="sma", kinds=("numeric",), required=True, variadic=False, description="", computed=True)
    prompt = (Path(__file__).parents[4] / "agents" / "anyplot" / "prompts" / "adapter.md").read_text()

    for bound in (False, True):
        marker = describe_role(role, bound).split(", ", 1)[1].rstrip(")")
        assert marker.split(":")[0] + ":" in prompt
    assert "not bound: compute it in the plot code from the bound data" in prompt
    assert "bound: use its column as it is" in prompt


def test_every_alias_names_a_computed_role() -> None:
    computed = {name for names in COMPUTED_ROLES.values() for name in names} | {"rolling_avg"}

    assert set(ALIASES) == computed


@pytest.mark.parametrize(
    ("role_name", "column", "matches"),
    [
        ("sma", "SMA 20", True),
        ("sma", "sma20", True),
        ("sma", "Gleitender Durchschnitt (20)", True),
        ("sma", "Middle Band", True),
        ("sma", "small", False),
        ("upper_band", "Upper", True),
        ("upper_band", "Oberes Band", True),
        ("upper_band", "lower", False),
        ("lower_band", "BB Lower", True),
        ("ctl", "CTL", True),
        ("ctl", "Fitness (CTL)", True),
        ("atl", "Ermüdung", True),
        ("tsb", "Form", True),
        ("tsb", "tss", False),
        ("rolling_avg", "rollingAvg", True),
        ("rolling_avg", "Rolling Mean", True),
        ("rolling_avg", "Temperature", False),
        # Other rolling statistics are no average (Copilot review of #12195).
        ("rolling_avg", "rolling_std", False),
        ("rolling_avg", "rolling_sum", False),
        ("rolling_avg", "rolling_count", False),
        ("rolling_avg", "Rolling Variance", False),
    ],
)
def test_name_match(role_name: str, column: str, matches: bool) -> None:
    role = DataRole(name=role_name, kinds=("numeric",), required=True, variadic=False, description="", computed=True)

    assert name_match(role, column) is matches


class TestBollinger:
    def test_bands_in_the_data_are_bound(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(
            "date,close,SMA 20,Upper,Lower\n"
            "2024-01-01,100.5,99.0,103.0,95.0\n2024-01-02,101.5,99.5,104.0,95.5\n2024-01-03,99.0,99.8,104.5,95.1\n"
        ).profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [
            ("date", "date"),
            ("close", "close"),
            ("sma", "SMA 20"),
            ("upper_band", "Upper"),
            ("lower_band", "Lower"),
        ]
        assert check_bindings(bindings, roles, data).complete

    @pytest.mark.parametrize(
        ("upper", "lower"),
        [
            ("SMA Upper Band", "SMA Lower Band"),
            ("Moving Average Upper Band", "Moving Average Lower Band"),
            ("Gleitender Durchschnitt oberes Band", "Gleitender Durchschnitt unteres Band"),
        ],
    )
    def test_band_qualified_names_are_bands_not_the_average(self, upper: str, lower: str) -> None:
        """A band named after the average is a band: `sma` never takes it and stays computed."""
        roles = roles_of("indicator-bollinger")
        data = parse_dataset(
            f"date,close,{upper},{lower}\n"
            "2024-01-01,100.5,103.0,95.0\n2024-01-02,101.5,104.0,95.5\n2024-01-03,99.0,104.5,95.1\n"
        ).profile

        assert pairs(default_bindings(roles, data)) == [
            ("date", "date"),
            ("close", "close"),
            ("upper_band", upper),
            ("lower_band", lower),
        ]

    def test_only_prices_leave_the_bands_to_the_plot(self) -> None:
        roles = roles_of("indicator-bollinger")
        data = parse_dataset("date,price\n2024-01-01,100.5\n2024-01-02,101.5\n2024-01-03,99.0\n").profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("close", "price")]
        check = check_bindings(bindings, roles, data)
        assert check.complete and check.missing_roles == []


class TestTrainingLoad:
    def test_daily_load_alone_is_enough(self) -> None:
        roles = roles_of("line-training-load-pmc")
        data = parse_dataset("date,tss\n2024-01-01,80\n2024-01-02,0\n2024-01-03,120\n").profile

        bindings = default_bindings(roles, data)
        assert pairs(bindings) == [("date", "date"), ("tss", "tss")]
        assert check_bindings(bindings, roles, data).complete

    def test_an_export_with_fitness_and_fatigue_binds_them(self) -> None:
        roles = roles_of("line-training-load-pmc")
        data = parse_dataset(
            "date,TSS,Fitness (CTL),Fatigue (ATL),Form (TSB)\n"
            "2024-01-01,80,50.1,60.2,-10.1\n2024-01-02,0,49.0,52.0,-3.0\n2024-01-03,120,51.5,66.0,-14.5\n"
        ).profile

        assert pairs(default_bindings(roles, data)) == [
            ("date", "date"),
            ("tss", "TSS"),
            ("ctl", "Fitness (CTL)"),
            ("atl", "Fatigue (ATL)"),
            ("tsb", "Form (TSB)"),
        ]
