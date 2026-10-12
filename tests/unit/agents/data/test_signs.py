"""Tests for agents/anyplot/data/signs.py and its use in bindings: roles that cannot be negative.

The fixtures are the owner's feedback cases of 2026-10-12, generalised: a sine table on
`polar-scatter` (a negative radius folded the circle into a cardioid) and on
`bar-feature-importance` (the defaults gave the signed `y` to `std`), and the control
cases whose `value` is signed by design (`waterfall-basic`, `bar-diverging`).
"""

import math
from pathlib import Path

import pytest

from agents.anyplot.data.bindings import check_bindings, default_bindings
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.roles import DataRole, parse_roles
from agents.anyplot.data.signs import NON_NEGATIVE_ROLES, has_negative, is_non_negative, mark_non_negative
from agents.anyplot.schemas import Binding, DatasetProfile


PLOTS = Path(__file__).resolve().parents[4] / "plots"
SINE = "x,y\n" + "\n".join(f"{x / 10:.2f},{math.sin(x / 10):.4f}" for x in range(-31, 32)) + "\n"


def spec_roles(spec_id: str) -> list[DataRole]:
    """The spec's roles as the session reads them: its `## Data` bullets, marked by `signs.py`."""
    text = (PLOTS / spec_id / "specification.md").read_text(encoding="utf-8")
    section = text.split("## Data", 1)[1].split("\n## ", 1)[0]
    bullets = [line.strip()[2:] for line in section.splitlines() if line.strip().startswith(("- ", "* "))]
    return mark_non_negative(parse_roles(bullets), spec_id)


def profile(csv: str) -> DatasetProfile:
    return parse_dataset(csv).profile


def pairs(bindings: list[Binding]) -> list[tuple[str, str]]:
    return [(binding.role, binding.column) for binding in bindings]


class TestTables:
    @pytest.mark.parametrize(
        ("role", "spec", "expected"),
        [
            ("radius", "polar-scatter", True),
            ("std", "bar-feature-importance", True),
            ("size", "bubble-basic", True),
            ("value", "pie-basic", True),
            ("value", "donut-nested", True),
            ("value", "treemap-basic", True),
            ("value", "sankey-basic", True),
            ("value", "funnel-basic", True),
            ("value", "waterfall-basic", False),
            ("value", "bar-diverging", False),
            ("importance", "bar-feature-importance", False),
            ("theta", "polar-scatter", False),
            ("effect_size", "funnel-meta-analysis", False),
        ],
    )
    def test_which_roles_need_values_of_zero_or_more(self, role: str, spec: str, expected: bool) -> None:
        assert is_non_negative(role, spec) is expected

    def test_every_spec_named_by_the_value_list_exists_and_has_a_value_role(self) -> None:
        """The table names real specs: a renamed spec would silently lose its check."""
        for spec in ("funnel-basic", "bubble-packed", "bubble-map-geographic", "pie-basic", "treemap-basic"):
            assert any(role.name == "value" and role.non_negative for role in spec_roles(spec)), spec

    def test_the_role_names_occur_in_the_catalogue(self) -> None:
        """Most names of the list are real roles; a list of names no spec uses would check nothing."""
        names = {
            role.name
            for spec in PLOTS.iterdir()
            if (spec / "specification.md").exists()
            for role in spec_roles(spec.name)
        }
        assert len(NON_NEGATIVE_ROLES & names) >= 15

    def test_has_negative_reads_number_columns_only(self) -> None:
        columns = {column.name: column for column in profile("a,b,c\n-1,x,2024-01-01\n2,y,2024-02-01\n").columns}
        assert has_negative(columns["a"]) is True
        assert has_negative(columns["b"]) is False
        assert has_negative(columns["c"]) is False


class TestDefaults:
    def test_a_negative_radius_is_never_the_default(self) -> None:
        roles = spec_roles("polar-scatter")

        bindings = default_bindings(roles, profile(SINE))

        assert pairs(bindings) == [("theta", "x")]
        check = check_bindings(bindings, roles, profile(SINE))
        assert check.missing_roles == ["radius"]
        assert check.warnings == [
            "radius: not bound, because every column that fits it ('y') has negative values; "
            "this role needs values of 0 or more"
        ]

    def test_the_reason_names_only_the_columns_still_free(self) -> None:
        """theta holds the only non-negative column; radius is left with the signed one and says so."""
        roles = spec_roles("polar-scatter")
        data = profile("angle,y\n0,-1\n90,1\n180,0.5\n")

        bindings = default_bindings(roles, data)

        assert pairs(bindings) == [("theta", "angle")]
        assert check_bindings(bindings, roles, data).warnings == [
            "radius: not bound, because every column that fits it ('y') has negative values; "
            "this role needs values of 0 or more"
        ]

    @pytest.mark.parametrize(
        ("spec", "role"),
        [("alluvial-basic", "flow"), ("frontier-efficient", "risk"), ("dot-matrix-proportional", "total")],
    )
    def test_magnitudes_of_the_catalogue_are_marked(self, spec: str, role: str) -> None:
        assert any(item.name == role and item.non_negative for item in spec_roles(spec))

    def test_a_non_negative_column_still_takes_the_role(self) -> None:
        roles = spec_roles("polar-scatter")
        data = profile("angle,speed,y\n0,1.5,-1\n90,2.5,1\n180,0,0\n")

        assert dict(pairs(default_bindings(roles, data)))["radius"] == "speed"
        assert check_bindings(default_bindings(roles, data), roles, data).warnings == []

    def test_std_skips_a_signed_column(self) -> None:
        roles = spec_roles("bar-feature-importance")
        data = profile("name,score,y\nA,0.5,-0.2\nB,0.3,0.1\n")

        bound = dict(pairs(default_bindings(roles, data)))

        assert "std" not in bound  # optional, so it stays open rather than take the signed y
        assert bound["feature"] == "name"

    def test_a_signed_value_stays_the_default_where_the_plot_is_signed(self) -> None:
        roles = spec_roles("waterfall-basic")
        data = profile("step,change\nStart,100\nCosts,-40\nEnd,60\n")

        bindings = default_bindings(roles, data)

        assert pairs(bindings) == [("category", "step"), ("value", "change")]
        assert check_bindings(bindings, roles, data).warnings == []


class TestWarnings:
    def test_a_binding_by_hand_is_valid_and_warned_about(self) -> None:
        roles = spec_roles("polar-scatter")
        data = profile(SINE)

        check = check_bindings([Binding(role="theta", column="x"), Binding(role="radius", column="y")], roles, data)

        assert check.complete and not check.errors
        assert check.warnings == [
            "radius: column 'y' has negative values (down to -0.9996); this role needs values of 0 or more"
        ]

    def test_a_pie_value_with_negatives_is_warned_about(self) -> None:
        roles = spec_roles("pie-basic")
        data = profile("segment,share\nA,40\nB,-5\nC,65\n")

        check = check_bindings(
            [Binding(role="category", column="segment"), Binding(role="value", column="share")], roles, data
        )

        assert [line.split(":")[0] for line in check.warnings] == ["value"]

    def test_the_snapshot_marks_its_roles(self) -> None:
        from agents.anyplot.session_state import CatalogueSnapshot

        bullets = ["`theta` (numeric) - angle", "`radius` (numeric) - distance"]
        snapshot = CatalogueSnapshot(spec_id="polar-scatter", title="t", data_roles=bullets, code="x = 1")

        assert [(role.name, role.non_negative) for role in snapshot.roles()] == [("theta", False), ("radius", True)]
